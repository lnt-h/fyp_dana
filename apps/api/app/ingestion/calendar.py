"""Operator calendar loader: ``data/closure_rules/<city>.yaml`` → APPROVED closure rules.

DEC-016 rules are owner-maintained (DEC-022: no curator review). The load is a sync keyed by the
rule's full content: identical rules are kept, new or changed ones are inserted APPROVED (verified
now, reviewed by the system account, source "Gonarra operator calendar"), and approved rules from
this calendar source that the file no longer lists are RETIRED. ``params`` are validated with the
same per-kind validators Plan Health relies on.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.closure_rules import default_severity, validate_params
from app.curation.common import audit
from app.curation.system import system_account_id
from app.errors import AppError
from app.ingestion.areas import DATA_DIR
from app.ingestion.common import (
    canonical_json,
    get_or_create_revision,
    get_or_create_source,
    load_city,
    sha256_hex,
)
from app.models.catalog import Place, PlaceClosureRule, SourceRevision
from app.models.constants import CLOSURE_APPLIES_TO, CLOSURE_EFFECTS, CLOSURE_SEVERITIES
from app.models.reference import Area

CALENDAR_DIR = DATA_DIR / "closure_rules"
DEFAULT_PUBLISHER = "Gonarra operator calendar"


@dataclass(frozen=True)
class RuleSpec:
    applies_to: str
    place_slug: str | None
    area_code: str | None
    rule_kind: str
    effect: str
    severity: str
    params: dict[str, Any]
    note_vi: str
    note_en: str
    effective_from: date | None
    effective_to: date | None

    def key(self, place_id: uuid.UUID | None) -> str:
        return canonical_json(
            [
                self.applies_to,
                str(place_id) if place_id else None,
                self.area_code,
                self.rule_kind,
                self.effect,
                self.severity,
                self.params,
                self.note_vi,
                self.note_en,
                self.effective_from.isoformat() if self.effective_from else None,
                self.effective_to.isoformat() if self.effective_to else None,
            ]
        )


@dataclass
class CalendarReport:
    loaded: int = 0
    unchanged: int = 0
    inserted: int = 0
    retired: int = 0
    errors: list[str] = field(default_factory=list)


def _date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def parse_rules(document: dict[str, Any]) -> list[RuleSpec]:
    """Validate the YAML document; raises ``ValueError`` naming the first bad rule."""
    specs: list[RuleSpec] = []
    for index, item in enumerate(document.get("rules") or [], start=1):
        where = f"rule {index}"
        applies_to = str(item.get("applies_to", "")).upper()
        if applies_to not in CLOSURE_APPLIES_TO:
            raise ValueError(f"{where}: applies_to must be one of {CLOSURE_APPLIES_TO}")
        place_slug = item.get("place_slug")
        area_code = item.get("area_code")
        if (applies_to == "PLACE") != bool(place_slug) or (applies_to == "AREA") != bool(area_code):
            raise ValueError(f"{where}: PLACE needs place_slug, AREA needs area_code, CITY neither")
        rule_kind = str(item.get("rule_kind", "")).upper()
        effect = str(item.get("effect", "")).upper()
        if effect not in CLOSURE_EFFECTS:
            raise ValueError(f"{where}: effect must be one of {CLOSURE_EFFECTS}")
        severity = str(item.get("severity") or default_severity(effect)).upper()
        if severity not in CLOSURE_SEVERITIES:
            raise ValueError(f"{where}: severity must be one of {CLOSURE_SEVERITIES}")
        try:
            params = validate_params(rule_kind, dict(item.get("params") or {}))
        except KeyError as exc:
            raise ValueError(f"{where}: unknown rule_kind {rule_kind!r}") from exc
        except AppError as exc:
            raise ValueError(f"{where}: {exc.message} {exc.context}") from exc
        note_vi, note_en = str(item.get("note_vi") or ""), str(item.get("note_en") or "")
        if not (1 <= len(note_vi) <= 500 and 1 <= len(note_en) <= 500):
            raise ValueError(f"{where}: note_vi and note_en are required (1..500 chars)")
        effective_from, effective_to = (
            _date(item.get("effective_from")),
            _date(item.get("effective_to")),
        )
        if effective_from and effective_to and effective_from > effective_to:
            raise ValueError(f"{where}: effective_from is after effective_to")
        specs.append(
            RuleSpec(
                applies_to=applies_to,
                place_slug=str(place_slug) if place_slug else None,
                area_code=str(area_code) if area_code else None,
                rule_kind=rule_kind,
                effect=effect,
                severity=severity,
                params=params,
                note_vi=note_vi,
                note_en=note_en,
                effective_from=effective_from,
                effective_to=effective_to,
            )
        )
    return specs


async def load_calendar(
    session: AsyncSession, *, city_code: str, path: Path | None = None
) -> CalendarReport:
    file_path = path or CALENDAR_DIR / f"{city_code}.yaml"
    raw = file_path.read_text(encoding="utf-8")
    document = yaml.safe_load(raw) or {}
    specs = parse_rules(document)
    city = await load_city(session, city_code)
    actor = await system_account_id(session)
    source_meta = document.get("source") or {}
    source = await get_or_create_source(
        session,
        data_provider_id=None,
        publisher=str(source_meta.get("publisher") or DEFAULT_PUBLISHER),
        source_kind="OWN_OBSERVATION",
        license_code=str(source_meta.get("licence") or "Gonarra-internal"),
        attribution_text=str(source_meta.get("attribution") or DEFAULT_PUBLISHER),
    )
    revision = await get_or_create_revision(
        session,
        source_id=source.id,
        locator=f"gonarra:data/closure_rules/{file_path.name}",
        content_sha256=sha256_hex(raw),
        title=f"Operator calendar {city_code}",
    )
    report = CalendarReport(loaded=len(specs))
    existing = (
        await session.scalars(
            select(PlaceClosureRule).where(
                PlaceClosureRule.city_id == city.id,
                PlaceClosureRule.review_state == "APPROVED",
            )
        )
    ).all()
    own_revisions = set(
        (
            await session.scalars(
                select(SourceRevision.id).where(SourceRevision.source_id == source.id)
            )
        ).all()
    )
    by_key: dict[str, PlaceClosureRule] = {}
    for row in existing:
        if row.source_revision_id in own_revisions:
            by_key[_row_key(row)] = row
    areas = set((await session.scalars(select(Area.code).where(Area.city_id == city.id))).all())
    wanted: set[str] = set()
    now = datetime.now(UTC)
    for spec in specs:
        place_id: uuid.UUID | None = None
        if spec.applies_to == "PLACE":
            place_id = await session.scalar(
                select(Place.id).where(Place.city_id == city.id, Place.slug == spec.place_slug)
            )
            if place_id is None:
                report.errors.append(f"unknown place_slug {spec.place_slug!r}; rule skipped")
                continue
        if spec.applies_to == "AREA" and spec.area_code not in areas:
            report.errors.append(f"unknown area_code {spec.area_code!r}; rule skipped")
            continue
        key = spec.key(place_id)
        wanted.add(key)
        if key in by_key:
            report.unchanged += 1
            continue
        row = PlaceClosureRule(
            city_id=city.id,
            applies_to=spec.applies_to,
            place_id=place_id,
            area_code=spec.area_code if spec.applies_to == "AREA" else None,
            rule_kind=spec.rule_kind,
            effect=spec.effect,
            params=spec.params,
            severity=spec.severity,
            note_vi=spec.note_vi,
            note_en=spec.note_en,
            effective_from=spec.effective_from,
            effective_to=spec.effective_to,
            source_revision_id=revision.id,
            review_state="APPROVED",
            verified_at=now,
            reviewed_by_account_id=actor,
        )
        session.add(row)
        await session.flush()
        by_key[key] = row
        report.inserted += 1
        audit(
            session,
            actor_account_id=actor,
            entity_table="place_closure_rules",
            entity_id=row.id,
            action="AUTO_APPROVE",
            to_state="APPROVED",
            detail={"rule_kind": row.rule_kind, "applies_to": row.applies_to},
        )
    for key, row in by_key.items():
        if key not in wanted and row.review_state == "APPROVED":
            row.review_state = "RETIRED"
            report.retired += 1
            audit(
                session,
                actor_account_id=actor,
                entity_table="place_closure_rules",
                entity_id=row.id,
                action="AUTO_APPROVE",
                from_state="APPROVED",
                to_state="RETIRED",
                detail={"reason": "no longer in the operator calendar"},
            )
    await session.commit()
    return report


def _row_key(row: PlaceClosureRule) -> str:
    spec = RuleSpec(
        applies_to=row.applies_to,
        place_slug=None,
        area_code=row.area_code,
        rule_kind=row.rule_kind,
        effect=row.effect,
        severity=row.severity,
        params=dict(row.params),
        note_vi=row.note_vi,
        note_en=row.note_en,
        effective_from=row.effective_from,
        effective_to=row.effective_to,
    )
    return spec.key(row.place_id)
