"""Curator-reviewed place facts (BR-024, FR-012). The only writer of ``place_facts``.

Each change is a new DRAFT ``fact_revision``; approval supersedes the previous APPROVED
revision of the same field (approved rows are immutable, enforced by a trigger). Operational
facts need claim-level evidence (``fact_evidence``) before approval.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import (
    audit,
    bump_content_revision,
    commit,
    flush,
    get_place,
    require_source_revisions,
)
from app.errors import conflict, invalid, not_found
from app.models.catalog import FactEvidence as FactEvidenceRow
from app.models.catalog import PlaceFact
from app.models.reference import FactField
from app.schemas.admin import (
    AdminPlaceFact,
    AdminPlaceFactList,
    FactCreate,
    FactEvidence,
    FactEvidenceInput,
    FactReview,
    FactUpdate,
)


def validate_fact_value(
    field: FactField, knowledge_state: str, value: dict[str, Any] | None
) -> None:
    """Domain shape rules (mirrors ck_place_facts_* plus value_kind expectations)."""
    if knowledge_state == "KNOWN":
        if not value:
            raise invalid("fact_value_required", "A KNOWN fact needs a value object")
    elif value is not None:
        raise invalid("fact_value_forbidden", "Only KNOWN facts carry a value")
    if value is None:
        return
    if field.value_kind == "LOCATION":
        lat, lng = value.get("lat"), value.get("lng")
        if not (
            isinstance(lat, int | float)
            and isinstance(lng, int | float)
            and -90 <= lat <= 90
            and -180 <= lng <= 180
        ):
            raise invalid(
                "fact_value_invalid", "LOCATION facts need numeric lat/lng", field=field.code
            )


def validate_conflict(conflict_state: str, conflict_note: str | None) -> None:
    if conflict_state != "NONE" and not conflict_note:
        raise invalid("conflict_note_required", "An OPEN or RESOLVED conflict needs a note")


class FactService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_facts(
        self,
        place_id: uuid.UUID,
        *,
        field_code: str | None = None,
        include_history: bool = True,
    ) -> AdminPlaceFactList:
        await get_place(self._session, place_id)
        statement = select(PlaceFact).where(PlaceFact.place_id == place_id)
        if field_code is not None:
            statement = statement.where(PlaceFact.field_code == field_code)
        if not include_history:
            statement = statement.where(PlaceFact.review_state.in_(("DRAFT", "APPROVED")))
        rows = (
            await self._session.scalars(
                statement.order_by(PlaceFact.field_code, PlaceFact.fact_revision.desc())
            )
        ).all()
        return AdminPlaceFactList(items=await self.to_schema_many(rows))

    async def to_schema_many(self, rows: Sequence[PlaceFact]) -> list[AdminPlaceFact]:
        ids = [row.id for row in rows]
        evidence: dict[uuid.UUID, list[FactEvidence]] = {fact_id: [] for fact_id in ids}
        if ids:
            links = (
                await self._session.scalars(
                    select(FactEvidenceRow).where(FactEvidenceRow.place_fact_id.in_(ids))
                )
            ).all()
            for link in links:
                evidence[link.place_fact_id].append(
                    FactEvidence(
                        source_revision_id=link.source_revision_id,
                        supported_claim=link.supported_claim,
                    )
                )
        return [_to_schema(row, evidence[row.id]) for row in rows]

    async def create_fact(
        self, place_id: uuid.UUID, data: FactCreate, actor_account_id: uuid.UUID
    ) -> AdminPlaceFact:
        await get_place(self._session, place_id, lock=True)
        field = await self._field(data.field_code)
        validate_fact_value(field, data.knowledge_state, data.value)
        validate_conflict(data.conflict_state, data.conflict_note)
        await require_source_revisions(
            self._session, [item.source_revision_id for item in data.evidence]
        )
        latest = await self._session.scalar(
            select(func.max(PlaceFact.fact_revision)).where(
                PlaceFact.place_id == place_id, PlaceFact.field_code == data.field_code
            )
        )
        row = PlaceFact(
            place_id=place_id,
            field_code=data.field_code,
            fact_revision=(latest or 0) + 1,
            knowledge_state=data.knowledge_state,
            value=data.value,
            valid_until=data.valid_until,
            review_state="DRAFT",
            conflict_state=data.conflict_state,
            conflict_note=data.conflict_note,
        )
        self._session.add(row)
        await flush(self._session)
        await self._replace_evidence(row.id, data.evidence)
        self._audit(actor_account_id, row, "create", None, "DRAFT")
        await bump_content_revision(self._session, place_id)
        await commit(self._session)
        return await self._one(row)

    async def update_fact(
        self,
        place_id: uuid.UUID,
        fact_id: uuid.UUID,
        data: FactUpdate,
        actor_account_id: uuid.UUID,
    ) -> AdminPlaceFact:
        await get_place(self._session, place_id, lock=True)
        row = await self._fact(place_id, fact_id)
        if row.review_state != "DRAFT":
            raise conflict(
                "fact_not_editable",
                "Only DRAFT fact revisions can be edited; create a new revision",
                review_state=row.review_state,
            )
        provided = data.model_fields_set
        if "knowledge_state" in provided and data.knowledge_state is not None:
            row.knowledge_state = data.knowledge_state
        if "value" in provided:
            row.value = data.value
        if "valid_until" in provided:
            row.valid_until = data.valid_until
        if "conflict_state" in provided and data.conflict_state is not None:
            row.conflict_state = data.conflict_state
        if "conflict_note" in provided:
            row.conflict_note = data.conflict_note
        field = await self._field(row.field_code)
        validate_fact_value(field, row.knowledge_state, row.value)
        validate_conflict(row.conflict_state, row.conflict_note)
        if data.evidence is not None:
            await require_source_revisions(
                self._session, [item.source_revision_id for item in data.evidence]
            )
            await self._replace_evidence(row.id, data.evidence)
        await flush(self._session)
        self._audit(actor_account_id, row, "update", "DRAFT", "DRAFT")
        await bump_content_revision(self._session, place_id)
        await commit(self._session)
        return await self._one(row)

    async def review_fact(
        self,
        place_id: uuid.UUID,
        fact_id: uuid.UUID,
        data: FactReview,
        actor_account_id: uuid.UUID,
    ) -> AdminPlaceFact:
        await get_place(self._session, place_id, lock=True)
        row = await self._fact(place_id, fact_id)
        if row.review_state != "DRAFT":
            raise conflict(
                "fact_already_reviewed",
                "Only DRAFT fact revisions can be reviewed",
                review_state=row.review_state,
            )
        if data.decision == "REJECT":
            row.review_state = "REJECTED"
            await flush(self._session)
            self._audit(actor_account_id, row, "reject", "DRAFT", "REJECTED")
        else:
            field = await self._field(row.field_code)
            if row.conflict_state == "OPEN":
                raise invalid("fact_conflict_open", "Resolve the conflict before approval")
            evidence_count = await self._session.scalar(
                select(func.count())
                .select_from(FactEvidenceRow)
                .where(FactEvidenceRow.place_fact_id == row.id)
            )
            if field.is_operational and not evidence_count:
                raise invalid(
                    "fact_evidence_required",
                    "Operational facts need at least one source before approval",
                    field_code=row.field_code,
                )
            superseded = (
                await self._session.scalars(
                    update(PlaceFact)
                    .where(
                        PlaceFact.place_id == place_id,
                        PlaceFact.field_code == row.field_code,
                        PlaceFact.review_state == "APPROVED",
                    )
                    .values(review_state="SUPERSEDED")
                    .returning(PlaceFact.id)
                )
            ).all()
            row.review_state = "APPROVED"
            row.verified_at = data.verified_at or datetime.now(UTC)
            await flush(self._session)
            self._audit(
                actor_account_id,
                row,
                "approve",
                "DRAFT",
                "APPROVED",
                superseded=[str(value) for value in superseded],
            )
        await bump_content_revision(self._session, place_id)
        await commit(self._session)
        return await self._one(row)

    # ---- internals ----------------------------------------------------------------------

    async def _field(self, code: str) -> FactField:
        field = await self._session.get(FactField, code)
        if field is None:
            raise invalid("unknown_field_code", "Unknown fact field", field_code=code)
        return field

    async def _fact(self, place_id: uuid.UUID, fact_id: uuid.UUID) -> PlaceFact:
        row = await self._session.scalar(
            select(PlaceFact).where(PlaceFact.id == fact_id, PlaceFact.place_id == place_id)
        )
        if row is None:
            raise not_found("Fact not found", code="not_found")
        return row

    async def _replace_evidence(
        self, fact_id: uuid.UUID, evidence: Sequence[FactEvidenceInput]
    ) -> None:
        await self._session.execute(
            delete(FactEvidenceRow).where(FactEvidenceRow.place_fact_id == fact_id)
        )
        seen: set[uuid.UUID] = set()
        for item in evidence:
            if item.source_revision_id in seen:
                continue
            seen.add(item.source_revision_id)
            self._session.add(
                FactEvidenceRow(
                    place_fact_id=fact_id,
                    source_revision_id=item.source_revision_id,
                    supported_claim=item.supported_claim,
                )
            )

    def _audit(
        self,
        actor_account_id: uuid.UUID,
        row: PlaceFact,
        operation: str,
        from_state: str | None,
        to_state: str,
        **extra: Any,
    ) -> None:
        audit(
            self._session,
            actor_account_id=actor_account_id,
            entity_table="place_facts",
            entity_id=row.id,
            action="FACT_REVIEW",
            from_state=from_state,
            to_state=to_state,
            detail={
                "operation": operation,
                "place_id": str(row.place_id),
                "field_code": row.field_code,
                "fact_revision": row.fact_revision,
                **extra,
            },
        )

    async def _one(self, row: PlaceFact) -> AdminPlaceFact:
        await self._session.refresh(row)
        [schema] = await self.to_schema_many([row])
        return schema


def _to_schema(row: PlaceFact, evidence: list[FactEvidence]) -> AdminPlaceFact:
    return AdminPlaceFact(
        id=row.id,
        place_id=row.place_id,
        field_code=row.field_code,
        fact_revision=row.fact_revision,
        knowledge_state=row.knowledge_state,
        value=row.value,
        verified_at=row.verified_at,
        valid_until=row.valid_until,
        review_state=row.review_state,
        conflict_state=row.conflict_state,
        conflict_note=row.conflict_note,
        evidence=evidence,
        source_revision_ids=[item.source_revision_id for item in evidence],
        created_at=row.created_at,
    )
