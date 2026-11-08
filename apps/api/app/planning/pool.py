"""Planner candidate pool: published places of one city with what scheduling needs (§3.2 step 3).

Reads go through ``vw_published_places`` / ``vw_published_place_facts`` (published snapshot only,
FR-004). Opening hours come from the ``OPENING_HOURS`` fact when it is KNOWN and parses; anything
else stays unknown (never invented). Coordinates stay server-side: they feed routing only and are
never part of a model prompt (BR-046).
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import bindparam, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.places import vw_published_place_facts, vw_published_places
from app.models.catalog import CatalogPublication, PlaceClosureRule
from app.planning.calendar.rules import ClosureRule, describe_rule_error
from app.planning.calendar.windows import OpeningHours

logger = logging.getLogger("gonarra.planning")


@dataclass(frozen=True, slots=True)
class PoolPlace:
    place_id: uuid.UUID
    catalog_publication_id: uuid.UUID
    category_code: str
    area_code: str | None
    name_vi: str
    name_en: str
    summary_vi: str | None
    summary_en: str | None
    lat: float
    lng: float
    visit_minutes: int
    famous: bool  # has a Wikipedia article in the published corpus: proxy for "well known"
    hours: OpeningHours | None
    fact_verified_at: date | None  # oldest verification of a KNOWN operational fact
    corpus_revision: int | None = None

    @property
    def key(self) -> str:
        return f"place:{self.place_id}"

    def name(self, locale: str) -> str:
        return self.name_en if locale == "en" else self.name_vi

    def summary(self, locale: str) -> str | None:
        return self.summary_en if locale == "en" else self.summary_vi


# "Famous" = the published corpus holds a Wikipedia lead for the place (an approved chunk of the
# current corpus revision sourced from the ``wikipedia`` provider, i.e. a Wikidata sitelink with an
# article). Any description is NOT a signal: short descriptions and grounded AI_SUMMARY texts exist
# for most places since 2026-11-08 and would make everything famous.
WIKIPEDIA_PROVIDER_KEY = "wikipedia"
_FAMOUS_SQL = text(
    """
    SELECT DISTINCT cp.id
      FROM catalog_publications cp
      JOIN knowledge_chunks kc
        ON kc.place_id = cp.place_id
       AND kc.corpus_revision = cp.corpus_revision
       AND kc.review_state = 'APPROVED'
      JOIN knowledge_chunk_sources kcs ON kcs.knowledge_chunk_id = kc.id
      JOIN source_revisions sr ON sr.id = kcs.source_revision_id
      JOIN sources s ON s.id = sr.source_id
      JOIN data_providers dp ON dp.id = s.data_provider_id
     WHERE cp.id IN :publication_ids
       AND dp.provider_key = :provider_key
    """
).bindparams(bindparam("publication_ids", expanding=True))


def parse_hours(value: Any) -> OpeningHours | None:
    if not isinstance(value, dict) or not value:
        return None
    try:
        return OpeningHours.from_value(value)
    except (ValueError, TypeError, KeyError):
        return None


async def load_pool(session: AsyncSession, city_id: uuid.UUID) -> list[PoolPlace]:
    vw = vw_published_places
    rows = (
        await session.execute(
            select(
                vw.c.place_id,
                vw.c.catalog_publication_id,
                vw.c.category_code,
                CatalogPublication.area_code,
                vw.c.name_vi,
                vw.c.name_en,
                vw.c.short_description_vi,
                vw.c.short_description_en,
                func.ST_Y(func.geometry(vw.c.location)).label("lat"),
                func.ST_X(func.geometry(vw.c.location)).label("lng"),
                vw.c.visit_minutes_suggested,
                vw.c.corpus_revision,
            )
            .select_from(vw)
            .join(CatalogPublication, CatalogPublication.id == vw.c.catalog_publication_id)
            .where(vw.c.city_id == city_id)
            .order_by(vw.c.place_id)
        )
    ).all()
    if not rows:
        return []
    publication_ids = [row.catalog_publication_id for row in rows]
    vf = vw_published_place_facts
    facts = (
        await session.execute(
            select(
                vf.c.catalog_publication_id, vf.c.field_code, vf.c.value, vf.c.verified_at
            ).where(
                vf.c.catalog_publication_id.in_(publication_ids),
                vf.c.knowledge_state == "KNOWN",
                or_(vf.c.is_operational.is_(True), vf.c.field_code == "OPENING_HOURS"),
            )
        )
    ).all()
    famous: set[uuid.UUID] = set(
        (
            await session.execute(
                _FAMOUS_SQL,
                {"publication_ids": publication_ids, "provider_key": WIKIPEDIA_PROVIDER_KEY},
            )
        ).scalars()
    )
    hours: dict[uuid.UUID, OpeningHours | None] = {}
    verified: dict[uuid.UUID, date] = {}
    for fact in facts:
        if fact.field_code == "OPENING_HOURS":
            hours[fact.catalog_publication_id] = parse_hours(fact.value)
        if fact.verified_at is not None:
            day = fact.verified_at.date()
            current = verified.get(fact.catalog_publication_id)
            verified[fact.catalog_publication_id] = day if current is None else min(current, day)
    return [
        PoolPlace(
            place_id=row.place_id,
            catalog_publication_id=row.catalog_publication_id,
            category_code=row.category_code,
            area_code=row.area_code,
            name_vi=row.name_vi,
            name_en=row.name_en,
            summary_vi=row.short_description_vi,
            summary_en=row.short_description_en,
            lat=float(row.lat),
            lng=float(row.lng),
            visit_minutes=int(row.visit_minutes_suggested),
            famous=row.catalog_publication_id in famous,
            hours=hours.get(row.catalog_publication_id),
            fact_verified_at=verified.get(row.catalog_publication_id),
            corpus_revision=row.corpus_revision,
        )
        for row in rows
    ]


async def load_rules(session: AsyncSession, city_id: uuid.UUID) -> list[ClosureRule]:
    """Approved, not yet ended closure rules of the city (place, area and city scope)."""
    rule = PlaceClosureRule
    rows = (
        await session.execute(
            select(rule).where(
                rule.city_id == city_id,
                rule.review_state == "APPROVED",
                or_(rule.effective_to.is_(None), rule.effective_to >= func.current_date()),
            )
        )
    ).scalars()
    parsed: list[ClosureRule] = []
    for row in rows:
        try:
            parsed.append(ClosureRule.from_row(row))
        except ValueError as exc:
            # Never silently drop a rule: log why (field paths and expected shapes, no rule text).
            logger.warning(
                "planning closure_rule_unparsable rule_id=%s rule_kind=%s reason=%s",
                row.id,
                row.rule_kind,
                describe_rule_error(exc),
            )
    return parsed


def by_id(pool: Sequence[PoolPlace]) -> dict[uuid.UUID, PoolPlace]:
    return {place.place_id: place for place in pool}
