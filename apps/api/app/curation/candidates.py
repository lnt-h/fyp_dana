"""Candidate places: list, detail, manual draft, review (API-033..035), publish/unpublish.

Places are written only by curators through this service; publication goes exclusively
through ``fn_publish_place`` / ``fn_withdraw_place`` (which write their own audit rows).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy import Text, case, exists, func, literal, or_, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.chunks import ChunkService
from app.curation.common import (
    audit,
    clamp_limit,
    commit,
    constraint_error,
    decode_cursor,
    default_city_id,
    flush,
    get_place,
    normalize_search_text,
    page_slice,
    parse_point,
    require_city,
    to_ewkt,
)
from app.curation.embedding import ChunkEmbedder
from app.curation.facts import FactService
from app.errors import AppError, conflict, invalid
from app.models.catalog import (
    CatalogPublication,
    Place,
    PlaceAlias,
    PlaceFact,
    PlaceLocalization,
)
from app.models.knowledge import KnowledgeChunk as KnowledgeChunkRow
from app.models.providers import DataProvider, ImportRecord, ImportRun
from app.schemas.admin import (
    Alias,
    AliasInput,
    CandidateCreate,
    CandidateDetail,
    CandidatePage,
    CandidateReview,
    CandidateSummary,
    GateViolation,
    GeoPoint,
    Localization,
    LocalizationInput,
    PublishRequest,
    ReviewWarning,
    UnpublishRequest,
)
from app.schemas.admin import (
    CatalogPublication as CatalogPublicationSchema,
)

CandidateSort = Literal["-updated_at", "name"]

_GATE_SQL = text(
    "SELECT violation_code, detail FROM fn_publication_gate_violations(:place_id) "
    "ORDER BY violation_code, detail"
)


async def gate_violations(session: AsyncSession, place_id: uuid.UUID) -> list[GateViolation]:
    rows = (await session.execute(_GATE_SQL, {"place_id": place_id})).all()
    return [GateViolation(code=row[0], detail=row[1]) for row in rows]


def _name_subquery(locale: str) -> Any:
    preference = case((PlaceLocalization.review_state == "APPROVED", 0), else_=1)
    return (
        select(PlaceLocalization.name)
        .where(
            PlaceLocalization.place_id == Place.id,
            PlaceLocalization.locale == locale,
            PlaceLocalization.review_state != "REJECTED",
        )
        .order_by(preference, PlaceLocalization.localization_revision.desc())
        .limit(1)
        .correlate(Place)
        .scalar_subquery()
    )


def _summary_columns() -> list[Any]:
    has_ai_draft = (
        exists()
        .where(
            PlaceLocalization.place_id == Place.id,
            PlaceLocalization.translation_origin == "AI_DRAFT",
            PlaceLocalization.review_state == "DRAFT",
        )
        .correlate(Place)
    )
    provider_release = (
        select(DataProvider.provider_key + literal(" ", Text) + ImportRun.release_id)
        .select_from(ImportRecord)
        .join(ImportRun, ImportRun.id == ImportRecord.import_run_id)
        .join(DataProvider, DataProvider.id == ImportRun.data_provider_id)
        .where(ImportRecord.place_id == Place.id)
        .order_by(ImportRun.started_at.desc())
        .limit(1)
        .correlate(Place)
        .scalar_subquery()
    )
    violations = func.fn_publication_gate_violations(Place.id).table_valued(
        "violation_code", "detail"
    )
    gate_count = select(func.count()).select_from(violations).correlate(Place).scalar_subquery()
    return [
        _name_subquery("vi").label("name_vi"),
        _name_subquery("en").label("name_en"),
        has_ai_draft.label("has_ai_draft"),
        provider_release.label("provider_release"),
        gate_count.label("gate_missing_count"),
    ]


def _summary(place: Place, extra: Any) -> CandidateSummary:
    return CandidateSummary(
        id=place.id,
        city_id=place.city_id,
        slug=place.slug,
        category_code=place.category_code,
        area_code=place.area_code,
        workflow_state=place.workflow_state,
        name_vi=extra.name_vi,
        name_en=extra.name_en,
        content_revision=place.content_revision,
        has_ai_draft=bool(extra.has_ai_draft),
        provider_release=extra.provider_release,
        gate_missing_count=int(extra.gate_missing_count or 0),
        updated_at=place.updated_at,
    )


def publication_schema(row: CatalogPublication) -> CatalogPublicationSchema:
    return CatalogPublicationSchema.model_validate(row, from_attributes=True)


class CandidateService:
    def __init__(
        self, session: AsyncSession, embedder: ChunkEmbedder, *, default_city_code: str
    ) -> None:
        self._session = session
        self._embedder = embedder
        self._default_city_code = default_city_code
        self._chunks = ChunkService(session, embedder)
        self._facts = FactService(session)

    # ---- reads --------------------------------------------------------------------------

    async def list_candidates(
        self,
        *,
        city_id: uuid.UUID | None = None,
        workflow_state: str | None = None,
        import_run_id: uuid.UUID | None = None,
        q: str | None = None,
        sort: CandidateSort = "-updated_at",
        cursor: str | None = None,
        limit: int | None = None,
    ) -> CandidatePage:
        offset = decode_cursor(cursor)
        size = clamp_limit(limit)
        columns = _summary_columns()
        statement = select(Place, *columns).execution_options(populate_existing=True)
        if city_id is not None:
            statement = statement.where(Place.city_id == city_id)
        if workflow_state is not None:
            statement = statement.where(Place.workflow_state == workflow_state)
        if import_run_id is not None:
            statement = statement.where(
                exists().where(
                    ImportRecord.place_id == Place.id, ImportRecord.import_run_id == import_run_id
                )
            )
        if q:
            needle = f"%{normalize_search_text(q)}%"
            raw = f"%{q.strip()}%"
            statement = statement.where(
                or_(
                    Place.slug.ilike(needle),
                    exists().where(
                        PlaceAlias.place_id == Place.id, PlaceAlias.alias_normalized.like(needle)
                    ),
                    exists().where(
                        PlaceLocalization.place_id == Place.id, PlaceLocalization.name.ilike(raw)
                    ),
                )
            )
        if sort == "name":
            name = func.coalesce(columns[0], columns[1], Place.slug)
            statement = statement.order_by(name.asc(), Place.id)
        else:
            statement = statement.order_by(Place.updated_at.desc(), Place.id)
        rows = (await self._session.execute(statement.offset(offset).limit(size + 1))).all()
        page, next_cursor = page_slice(rows, offset, size)
        return CandidatePage(next_cursor=next_cursor, items=[_summary(row[0], row) for row in page])

    async def get_candidate(
        self, place_id: uuid.UUID, *, warnings: Sequence[ReviewWarning] = ()
    ) -> CandidateDetail:
        place = await get_place(self._session, place_id)
        await self._session.refresh(place)
        extra = (
            await self._session.execute(select(*_summary_columns()).where(Place.id == place_id))
        ).one()
        summary = _summary(place, extra)
        localizations = (
            await self._session.scalars(
                select(PlaceLocalization)
                .where(PlaceLocalization.place_id == place_id)
                .order_by(PlaceLocalization.locale, PlaceLocalization.localization_revision.desc())
            )
        ).all()
        aliases = (
            await self._session.scalars(
                select(PlaceAlias)
                .where(PlaceAlias.place_id == place_id)
                .order_by(PlaceAlias.locale, PlaceAlias.alias_kind, PlaceAlias.alias)
            )
        ).all()
        facts = (
            await self._session.scalars(
                select(PlaceFact)
                .where(PlaceFact.place_id == place_id)
                .order_by(PlaceFact.field_code, PlaceFact.fact_revision.desc())
            )
        ).all()
        working_revision = await self._session.scalar(
            select(func.max(KnowledgeChunkRow.corpus_revision)).where(
                KnowledgeChunkRow.place_id == place_id
            )
        )
        chunk_rows: Sequence[KnowledgeChunkRow] = []
        if working_revision is not None:
            chunk_rows = (
                await self._session.scalars(
                    select(KnowledgeChunkRow)
                    .where(
                        KnowledgeChunkRow.place_id == place_id,
                        KnowledgeChunkRow.corpus_revision == working_revision,
                    )
                    .order_by(KnowledgeChunkRow.locale, KnowledgeChunkRow.chunk_index)
                )
            ).all()
        chunks = await self._chunks.to_schema_many(chunk_rows)
        all_warnings = list(warnings)
        for chunk in chunks:
            already = any(
                w.knowledge_chunk_id == chunk.id and w.code == "CHUNK_EMBEDDING_PENDING"
                for w in all_warnings
            )
            if (
                chunk.embedding_state == "PENDING"
                and chunk.review_state != "RETIRED"
                and not already
            ):
                all_warnings.append(
                    ReviewWarning(code="CHUNK_EMBEDDING_PENDING", knowledge_chunk_id=chunk.id)
                )
        publications = (
            await self._session.scalars(
                select(CatalogPublication)
                .where(CatalogPublication.place_id == place_id)
                .order_by(CatalogPublication.publication_revision.desc())
            )
        ).all()
        location = parse_point(place.location) or GeoPoint(latitude=0, longitude=0)
        return CandidateDetail(
            **summary.model_dump(),
            location=location,
            visit_minutes_min=place.visit_minutes_min,
            visit_minutes_suggested=place.visit_minutes_suggested,
            visit_minutes_max=place.visit_minutes_max,
            has_no_media=place.has_no_media,
            localizations=[
                Localization.model_validate(row, from_attributes=True) for row in localizations
            ],
            aliases=[Alias.model_validate(row, from_attributes=True) for row in aliases],
            facts=await self._facts.to_schema_many(facts),
            chunks=chunks,
            gate_violations=await gate_violations(self._session, place_id),
            warnings=all_warnings,
            publications=[publication_schema(row) for row in publications],
        )

    # ---- writes -------------------------------------------------------------------------

    async def create_candidate(
        self, data: CandidateCreate, actor_account_id: uuid.UUID
    ) -> CandidateDetail:
        city_id = data.city_id or await default_city_id(self._session, self._default_city_code)
        await require_city(self._session, city_id)
        _check_visit_minutes(
            data.visit_minutes_min, data.visit_minutes_suggested, data.visit_minutes_max
        )
        place = Place(
            city_id=city_id,
            slug=data.slug,
            area_code=data.area_code,
            category_code=data.category_code,
            workflow_state="CONTENT_REVIEW",
            location=to_ewkt(data.location),
            visit_minutes_min=data.visit_minutes_min,
            visit_minutes_suggested=data.visit_minutes_suggested,
            visit_minutes_max=data.visit_minutes_max,
            has_no_media=bool(data.has_no_media),
        )
        self._session.add(place)
        await flush(self._session)
        localization_log = await apply_localizations(
            self._session, place.id, data.localizations, []
        )
        alias_log = await apply_aliases(self._session, place.id, data.aliases)
        await flush(self._session)
        audit(
            self._session,
            actor_account_id=actor_account_id,
            entity_table="places",
            entity_id=place.id,
            action="CONTENT_REVIEW",
            to_state=place.workflow_state,
            detail={
                "operation": "create",
                "slug": place.slug,
                "localizations": localization_log,
                "aliases": alias_log,
            },
        )
        await commit(self._session)
        return await self.get_candidate(place.id)

    async def review_candidate(
        self, place_id: uuid.UUID, data: CandidateReview, actor_account_id: uuid.UUID
    ) -> CandidateDetail:
        place = await get_place(self._session, place_id, lock=True)
        await self._session.refresh(place)
        if place.content_revision != data.expected_content_revision:
            raise conflict(
                "revision_conflict",
                "The candidate changed since it was opened",
                expected_content_revision=data.expected_content_revision,
                current_revision=place.content_revision,
            )
        provided = data.model_fields_set
        from_state = place.workflow_state
        changed: list[str] = []
        for name in (
            "category_code",
            "area_code",
            "visit_minutes_min",
            "visit_minutes_suggested",
            "visit_minutes_max",
        ):
            if name in provided:
                setattr(place, name, getattr(data, name))
                changed.append(name)
        if "location" in provided and data.location is not None:
            place.location = to_ewkt(data.location)
            changed.append("location")
        if "has_no_media" in provided and data.has_no_media is not None:
            place.has_no_media = data.has_no_media
            changed.append("has_no_media")
        _check_visit_minutes(
            place.visit_minutes_min, place.visit_minutes_suggested, place.visit_minutes_max
        )
        if data.workflow_state is not None and data.workflow_state != place.workflow_state:
            if place.workflow_state == "PUBLISHED":
                raise conflict(
                    "place_published",
                    "Unpublish the place before changing its workflow state",
                )
            if data.workflow_state == "READY_TO_PUBLISH":
                missing = [
                    name
                    for name in (
                        "category_code",
                        "visit_minutes_min",
                        "visit_minutes_suggested",
                        "visit_minutes_max",
                    )
                    if getattr(place, name) is None
                ]
                if missing:
                    raise invalid(
                        "place_incomplete",
                        "Category and visit minutes are required before READY_TO_PUBLISH",
                        missing=missing,
                    )
            place.workflow_state = data.workflow_state
        await flush(self._session)
        localization_log = await apply_localizations(
            self._session, place_id, data.localizations or [], data.confirm_ai_draft_locales
        )
        alias_log = await apply_aliases(self._session, place_id, data.aliases or [])
        warnings: list[ReviewWarning] = []
        chunk_ids: list[str] = []
        for chunk in data.chunks or []:
            row = await self._chunks.apply_input(place_id, chunk, actor_account_id, warnings)
            chunk_ids.append(str(row.id))
        place.content_revision = place.content_revision + 1
        await flush(self._session)
        audit(
            self._session,
            actor_account_id=actor_account_id,
            entity_table="places",
            entity_id=place_id,
            action="CONTENT_REVIEW",
            from_state=from_state,
            to_state=place.workflow_state,
            detail={
                "operation": "review",
                "content_revision": place.content_revision,
                "fields": changed,
                "localizations": localization_log,
                "aliases": alias_log,
                "chunks": chunk_ids,
            },
        )
        await commit(self._session)
        return await self.get_candidate(place_id, warnings=warnings)

    async def publish(
        self, place_id: uuid.UUID, data: PublishRequest, actor_account_id: uuid.UUID
    ) -> CatalogPublicationSchema:
        place = await get_place(self._session, place_id, lock=True)
        await self._session.refresh(place)
        if place.content_revision != data.expected_content_revision:
            raise conflict(
                "revision_conflict",
                "The candidate changed since it was opened",
                expected_content_revision=data.expected_content_revision,
                current_revision=place.content_revision,
            )
        violations = await gate_violations(self._session, place_id)
        if violations:
            raise _publication_incomplete(violations)
        try:
            publication_id = await self._session.scalar(
                select(func.fn_publish_place(place_id, actor_account_id))
            )
        except DBAPIError as exc:
            await self._session.rollback()
            if getattr(exc.orig, "sqlstate", None) == "23514":
                raise _publication_incomplete(
                    await gate_violations(self._session, place_id)
                ) from exc
            raise constraint_error(exc) from exc
        await commit(self._session)
        row = await self._session.get(CatalogPublication, publication_id, populate_existing=True)
        if row is None:  # pragma: no cover - the function returned this id in our transaction
            raise AppError(500, "publication_missing", "Publication was not recorded")
        return publication_schema(row)

    async def unpublish(
        self, place_id: uuid.UUID, data: UnpublishRequest, actor_account_id: uuid.UUID
    ) -> CatalogPublicationSchema:
        await get_place(self._session, place_id, lock=True)
        current = await self._session.scalar(
            select(CatalogPublication).where(
                CatalogPublication.place_id == place_id, CatalogPublication.state == "PUBLISHED"
            )
        )
        if current is None:
            raise conflict("not_published", "The place has no current publication")
        await self._session.execute(
            select(func.fn_withdraw_place(place_id, actor_account_id, data.state_reason))
        )
        await commit(self._session)
        row = await self._session.get(CatalogPublication, current.id, populate_existing=True)
        assert row is not None
        return publication_schema(row)


def _publication_incomplete(violations: list[GateViolation]) -> AppError:
    return invalid(
        "publication_incomplete",
        "The candidate does not pass the publication gate",
        missing=[violation.model_dump() for violation in violations],
    )


def _check_visit_minutes(low: int | None, suggested: int | None, high: int | None) -> None:
    ordered = [value for value in (low, suggested, high) if value is not None]
    if ordered != sorted(ordered):
        raise invalid(
            "invalid_visit_minutes",
            "visit_minutes_min <= visit_minutes_suggested <= visit_minutes_max",
        )


# ---- Localizations and aliases (shared with web-candidate promotion) ---------------------


async def apply_localizations(
    session: AsyncSession,
    place_id: uuid.UUID,
    items: Sequence[LocalizationInput],
    confirm_ai_draft_locales: Sequence[str],
) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    for item in items:
        if item.id is not None:
            row = await session.scalar(
                select(PlaceLocalization).where(
                    PlaceLocalization.id == item.id, PlaceLocalization.place_id == place_id
                )
            )
            if row is None:
                raise invalid("unknown_localization", "Unknown localization", id=str(item.id))
            if row.locale != item.locale:
                raise invalid(
                    "localization_locale_mismatch", "Locale does not match", id=str(row.id)
                )
        else:
            latest = await session.scalar(
                select(func.max(PlaceLocalization.localization_revision)).where(
                    PlaceLocalization.place_id == place_id,
                    PlaceLocalization.locale == item.locale,
                )
            )
            assert item.name is not None  # enforced by LocalizationInput
            row = PlaceLocalization(
                place_id=place_id,
                locale=item.locale,
                localization_revision=(latest or 0) + 1,
                name=item.name,
                short_description=item.short_description,
                description=item.description,
                translation_origin=item.translation_origin,
                review_state="DRAFT",
            )
            session.add(row)
            await flush(session)
        await _review_localization(session, row, item.review_state, confirm_ai_draft_locales)
        log.append(
            {
                "id": str(row.id),
                "locale": row.locale,
                "revision": row.localization_revision,
                "review_state": row.review_state,
            }
        )
    return log


async def _review_localization(
    session: AsyncSession,
    row: PlaceLocalization,
    requested: str,
    confirm_ai_draft_locales: Sequence[str],
) -> None:
    if requested == row.review_state:
        return
    if row.review_state != "DRAFT":
        raise conflict(
            "localization_already_reviewed",
            "Only DRAFT localizations can be reviewed; add a new revision",
            id=str(row.id),
            review_state=row.review_state,
        )
    now = datetime.now(UTC)
    if requested == "REJECTED":
        row.review_state, row.reviewed_at = "REJECTED", now
        return
    if requested != "APPROVED":
        return
    if row.translation_origin == "AI_DRAFT" and row.locale not in confirm_ai_draft_locales:
        raise invalid(
            "ai_draft_unconfirmed",
            "Confirm the AI draft locale explicitly before approval (FR-019)",
            locale=row.locale,
        )
    if not row.description:
        raise invalid(
            "localization_incomplete",
            "An approved localization needs a description",
            locale=row.locale,
        )
    await session.execute(
        update(PlaceLocalization)
        .where(
            PlaceLocalization.place_id == row.place_id,
            PlaceLocalization.locale == row.locale,
            PlaceLocalization.review_state == "APPROVED",
            PlaceLocalization.id != row.id,
        )
        .values(review_state="SUPERSEDED")
    )
    row.review_state, row.reviewed_at = "APPROVED", now
    await flush(session)


async def apply_aliases(
    session: AsyncSession, place_id: uuid.UUID, items: Sequence[AliasInput]
) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    for item in items:
        normalized = normalize_search_text(item.alias)
        if not normalized:
            raise invalid("invalid_alias", "Alias is empty after normalisation")
        row = await session.scalar(
            select(PlaceAlias).where(
                PlaceAlias.place_id == place_id, PlaceAlias.alias_normalized == normalized
            )
        )
        if row is None:
            row = PlaceAlias(place_id=place_id, alias_normalized=normalized)
            session.add(row)
        row.locale = item.locale
        row.alias = item.alias.strip()
        row.alias_kind = item.alias_kind
        row.review_state = item.review_state
        await flush(session)
        log.append(
            {"id": str(row.id), "alias_kind": row.alias_kind, "review_state": row.review_state}
        )
    return log
