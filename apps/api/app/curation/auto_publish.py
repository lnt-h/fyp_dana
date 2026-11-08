"""Automated publication gate and auto-publish (DEC-022). No human review.

For every candidate place of a city this module

1. **composes** the content it would publish from the staged import records (owner sheet >
   Wikidata/Wikipedia > OpenStreetMap > promoted web candidate), deterministically; facts come
   from the sheet, else from OpenStreetMap (OPENING_HOURS), else from the grounded writer's
   extraction (``enrich facts``, DEC-028: ``origin = AI_EXTRACTED`` with its grounding flag and
   the cited evidence revision), each with its own source revision;
2. runs the **gate** in code (``GATE_RULES``): both locales complete, location inside the city
   boundary, category and area set, every source licensed and attributed, every KNOWN fact
   backed by an attributed source revision (otherwise it is UNKNOWN, never invented), no media
   unless licensed media exists;
3. on pass, **approves** localizations, aliases, facts, chunks and identities as the system
   account and publishes through ``fn_publish_place`` (which re-checks the SQL gate), inside a
   savepoint per place.

Idempotent: approved rows are reused while their content is unchanged, and a place is
re-published only when the publication snapshot would differ. A place whose last publication was
WITHDRAWN (owner takedown) is never re-published automatically unless ``include_withdrawn``.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, null, or_, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.chunks import content_sha256
from app.curation.common import audit, normalize_search_text, parse_point
from app.curation.embedding import ChunkEmbedder
from app.curation.names import proper_name_fallback
from app.curation.system import system_account_id
from app.db.types import ewkt_point
from app.ingestion.areas import assign_area, load_areas
from app.ingestion.categories import VISIT_MINUTES
from app.ingestion.common import PROVENANCE_KEY, inside_city, load_city
from app.models.catalog import (
    CatalogAuditEvent,
    CatalogPublication,
    FactEvidence,
    MediaAsset,
    Place,
    PlaceAlias,
    PlaceFact,
    PlaceLocalization,
    PlaceMedia,
    PublicationFact,
    PublicationMedia,
    Source,
    SourceRevision,
    WebPlaceCandidate,
)
from app.models.knowledge import KnowledgeChunk, KnowledgeChunkSource
from app.models.providers import DataProvider, ExternalPlaceIdentity, ImportRecord, ImportRun
from app.models.reference import Category, FactField

logger = logging.getLogger("gonarra.curation")

LOCALES: tuple[str, ...] = ("vi", "en")
# Grounded AI descriptions (app.research.enrich): one import record per place under this provider.
AI_SUMMARY_PROVIDER_KEY = "gonarra_ai_summary"
# AI-extracted facts and short descriptions (app.curation.fact_extract, DEC-028).
AI_FACTS_PROVIDER_KEY = "gonarra_ai_facts"
UNUSABLE_LICENCES = frozenset({"", "UNKNOWN", "NONE"})

# Human-readable gate rules (reported by the CLI and documented in apps/api/data/README.md).
GATE_RULES: dict[str, str] = {
    "NO_SOURCE": "the place has no staged record with a recorded source revision",
    "OUTSIDE_CITY": "location is outside the city boundary",
    "MISSING_CATEGORY": "no category could be set (sheet or mapped Wikidata class)",
    "MISSING_AREA": "location is outside every travel-area polygon and the sheet names no area",
    "MISSING_NAME": "no name in this locale (sheet name or Wikidata label)",
    "MISSING_DESCRIPTION": (
        "no description in this locale (Wikipedia, sheet, AI summary of cited sources or Wikidata)"
    ),
    "AI_SUMMARY_UNCITED": "an AI-summarised description has no recorded cited source revision",
    "MISSING_LICENCE": "a source used by shown content has no licence or no attribution text",
    "FACT_WITHOUT_SOURCE": "a KNOWN fact has no attributed source revision",
    "SQL_GATE": "fn_publication_gate_violations reported a violation",
}


# ---- Composition --------------------------------------------------------------------------


@dataclass
class DesiredLocalization:
    name: str | None
    short_description: str | None
    description: str | None
    source_revision_ids: set[uuid.UUID] = field(default_factory=set)
    # ORIGINAL, or AI_SUMMARY when the description comes from the grounded writer (0007).
    translation_origin: str = "ORIGINAL"
    name_is_source_fallback: bool = False
    # Pages the AI summary was written from (provenance; checked by AI_SUMMARY_UNCITED).
    cited_revision_ids: set[uuid.UUID] = field(default_factory=set)


@dataclass(frozen=True)
class DesiredFact:
    field_code: str
    knowledge_state: str
    value: dict[str, Any] | None
    evidence: tuple[tuple[uuid.UUID, str], ...]  # (source_revision_id, supported_claim)
    origin: str = "SOURCE"  # SOURCE | OWNER | AI_EXTRACTED (0009, DEC-028)
    grounding: str | None = None  # STRONG | WEAK for AI_EXTRACTED


@dataclass(frozen=True)
class DesiredChunk:
    locale: str
    content: str
    source_revision_id: uuid.UUID


@dataclass
class Desired:
    lng: float
    lat: float
    category_code: str | None
    area_code: str | None
    visit_minutes: tuple[int, int, int] | None
    localizations: dict[str, DesiredLocalization]
    aliases: dict[str, list[str]]
    facts: list[DesiredFact]
    chunks: list[DesiredChunk]
    primary_revision_id: uuid.UUID | None


@dataclass
class Contributions:
    sheet: dict[str, Any] | None = None
    wikidata: dict[str, Any] | None = None
    wikipedia: dict[str, dict[str, Any]] = field(default_factory=dict)
    osm: dict[str, Any] | None = None
    web: WebPlaceCandidate | None = None
    ai_summary: dict[str, Any] | None = None
    ai_facts: dict[str, Any] | None = None


def _provenance_id(
    payload: dict[str, Any] | None, key: str = "source_revision_id"
) -> uuid.UUID | None:
    value = ((payload or {}).get(PROVENANCE_KEY) or {}).get(key)
    return uuid.UUID(str(value)) if value else None


def _add(loc: DesiredLocalization, revision_id: uuid.UUID | None) -> None:
    if revision_id is not None:
        loc.source_revision_ids.add(revision_id)


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text_value = " ".join(str(value).split())
    return text_value or None


def _sourced_fact(payload: dict[str, Any] | None, code: str) -> tuple[dict[str, Any], str] | None:
    """A staged fact with its own source revision id (sheet and OSM records share the shape)."""
    fact = ((payload or {}).get("facts") or {}).get(code)
    revision = (
        ((payload or {}).get(PROVENANCE_KEY) or {}).get("fact_source_revision_ids") or {}
    ).get(code)
    if fact and revision and fact.get("value"):
        return fact, str(revision)
    return None


def compose(
    place: Place,
    contributions: Contributions,
    *,
    area_codes: Sequence[Any],
    categories: set[str],
    fact_fields: Sequence[FactField],
) -> Desired:
    sheet, wikidata, web = contributions.sheet, contributions.wikidata, contributions.web
    osm, ai_summary = contributions.osm, contributions.ai_summary
    ai_facts = contributions.ai_facts
    ai_facts_rev = _provenance_id(ai_facts)
    point = parse_point(place.location)
    lng, lat = (point.longitude, point.latitude) if point else (0.0, 0.0)
    for payload in (sheet, wikidata, osm):
        location = (payload or {}).get("location")
        if location:
            lng, lat = float(location["lng"]), float(location["lat"])
            break
    else:
        web_point = parse_point(web.location) if web is not None and web.location else None
        if web_point is not None:
            lng, lat = web_point.longitude, web_point.latitude

    category = (
        (sheet or {}).get("category")
        or (wikidata or {}).get("category")
        or (osm or {}).get("category")
    )
    if category is None and web is not None and web.category_guess:
        category = web.category_guess.strip().upper()
    if category is None:
        category = place.category_code
    if category not in categories:
        category = None

    area = (sheet or {}).get("area") or assign_area(area_codes, lng, lat)

    visit: tuple[int, int, int] | None = None
    sheet_visit = (sheet or {}).get("visit_minutes")
    if sheet_visit:
        visit = (int(sheet_visit[0]), int(sheet_visit[1]), int(sheet_visit[2]))
    elif category is not None:
        visit = VISIT_MINUTES.get(category)

    sheet_rev = _provenance_id(sheet)
    wikidata_rev = _provenance_id(wikidata)
    osm_rev = _provenance_id(osm)
    web_rev = web.source_revision_id if web is not None else None
    primary = sheet_rev or wikidata_rev or osm_rev or web_rev

    ai_rev = _provenance_id(ai_summary)
    ai_cited = {
        uuid.UUID(str(value))
        for value in ((ai_summary or {}).get(PROVENANCE_KEY) or {}).get("cited_source_revision_ids")
        or []
    }
    localizations: dict[str, DesiredLocalization] = {}
    aliases: dict[str, list[str]] = {}
    chunks: list[DesiredChunk] = []
    vi_name_rev: uuid.UUID | None = None
    for locale in LOCALES:
        loc = DesiredLocalization(name=None, short_description=None, description=None)
        sheet_name = _clean(((sheet or {}).get("name") or {}).get(locale))
        wd_name = _clean(((wikidata or {}).get("name") or {}).get(locale))
        osm_name = _clean(((osm or {}).get("name") or {}).get(locale))
        web_name = _clean(getattr(web, f"name_{locale}", None)) if web is not None else None
        if sheet_name:
            loc.name = sheet_name
            _add(loc, sheet_rev)
        elif wd_name:
            loc.name = wd_name
            _add(loc, wikidata_rev)
        elif osm_name:
            loc.name = osm_name
            _add(loc, osm_rev)
        elif web_name:
            loc.name = web_name
            _add(loc, web_rev)
        name_rev = (
            (sheet_rev if sheet_name else None)
            or (wikidata_rev if wd_name else None)
            or (osm_rev if osm_name else None)
            or (web_rev if web_name else None)
        )
        if locale == "vi":
            vi_name_rev = name_rev
        elif not loc.name and "vi" in localizations:
            # Proper-name fallback (D3): the Vietnamese name unchanged, never a translation.
            fallback = proper_name_fallback(category, localizations["vi"].name)
            if fallback is not None:
                loc.name = fallback
                loc.name_is_source_fallback = True
                _add(loc, vi_name_rev)

        sheet_short = _clean(((sheet or {}).get("short_description") or {}).get(locale))
        sheet_desc = _clean(((sheet or {}).get("description") or {}).get(locale))
        wd_desc = _clean(((wikidata or {}).get("description") or {}).get(locale))
        wiki = contributions.wikipedia.get(locale)
        wiki_text = _clean((wiki or {}).get("summary"))
        wiki_rev = _provenance_id(wiki)
        ai_text = _clean(((ai_summary or {}).get("description") or {}).get(locale))

        ai_short = _clean(((ai_facts or {}).get("short_description") or {}).get(locale))
        if sheet_short:
            loc.short_description = sheet_short
            _add(loc, sheet_rev)
        elif wd_desc:
            loc.short_description = wd_desc
            _add(loc, wikidata_rev)
        elif ai_short and ai_facts_rev:
            loc.short_description = ai_short
            _add(loc, ai_facts_rev)

        if wiki_text and wiki_rev:
            loc.description = wiki_text
            loc.source_revision_ids.add(wiki_rev)
            chunks.append(DesiredChunk(locale, wiki_text, wiki_rev))
        elif sheet_desc:
            loc.description = sheet_desc
            _add(loc, sheet_rev)
        elif ai_text and ai_rev:
            loc.description = ai_text
            loc.translation_origin = "AI_SUMMARY"
            loc.source_revision_ids.add(ai_rev)
            loc.cited_revision_ids |= ai_cited
        elif sheet_short:
            loc.description = sheet_short
        elif wd_desc:
            loc.description = wd_desc
            _add(loc, wikidata_rev)
        localizations[locale] = loc

        names: list[str] = []
        for candidate in (
            loc.name,
            wd_name,
            sheet_name,
            osm_name,
            *(((wikidata or {}).get("aliases") or {}).get(locale) or []),
        ):
            cleaned = _clean(candidate)
            if cleaned and cleaned not in names:
                names.append(cleaned)
        aliases[locale] = names

    facts: list[DesiredFact] = []
    for fact_field in fact_fields:
        code = fact_field.code
        owner = _sourced_fact(sheet, code)
        sourced = owner or _sourced_fact(osm, code)
        ai = _sourced_fact(ai_facts, code) if sourced is None else None
        if sourced is not None:
            staged, fact_rev = sourced
            value = dict(staged["value"])
            claim = f"{code}: {value.get('text') or value}"[:500]
            origin = "OWNER" if owner is not None else "SOURCE"
            facts.append(DesiredFact(code, "KNOWN", value, ((uuid.UUID(fact_rev), claim),), origin))
        elif ai is not None:
            staged, fact_rev = ai
            value = dict(staged["value"])
            claim = f"{code} (AI-extracted): {staged.get('quote') or value}"[:500]
            facts.append(
                DesiredFact(
                    code,
                    "KNOWN",
                    value,
                    ((uuid.UUID(fact_rev), claim),),
                    "AI_EXTRACTED",
                    staged.get("grounding")
                    if staged.get("grounding") in ("STRONG", "WEAK")
                    else "WEAK",
                )
            )
        elif fact_field.required_for_publication:
            evidence: tuple[tuple[uuid.UUID, str], ...] = ()
            if primary is not None:
                claim = f"No value for {code} in this source; shown as unknown."
                evidence = ((primary, claim),)
            facts.append(DesiredFact(code, "UNKNOWN", None, evidence))

    return Desired(
        lng=lng,
        lat=lat,
        category_code=category,
        area_code=area,
        visit_minutes=visit,
        localizations=localizations,
        aliases=aliases,
        facts=facts,
        chunks=chunks,
        primary_revision_id=primary,
    )


# ---- Gate ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceInfo:
    publisher: str
    license_code: str
    attribution_text: str | None

    @property
    def usable(self) -> bool:
        return self.license_code.strip().upper() not in UNUSABLE_LICENCES and bool(
            (self.attribution_text or "").strip()
        )


def gate_reasons(
    desired: Desired, *, inside: bool, sources: dict[uuid.UUID, SourceInfo]
) -> list[str]:
    reasons: list[str] = []
    if desired.primary_revision_id is None:
        reasons.append("NO_SOURCE")
    if not inside:
        reasons.append("OUTSIDE_CITY")
    if desired.category_code is None:
        reasons.append("MISSING_CATEGORY")
    if desired.area_code is None:
        reasons.append("MISSING_AREA")
    used: set[uuid.UUID] = set()
    for locale in LOCALES:
        loc = desired.localizations[locale]
        if not loc.name:
            reasons.append(f"MISSING_NAME:{locale}")
        if not loc.description:
            reasons.append(f"MISSING_DESCRIPTION:{locale}")
        if loc.translation_origin == "AI_SUMMARY" and not any(
            revision_id in sources for revision_id in loc.cited_revision_ids
        ):
            reasons.append(f"AI_SUMMARY_UNCITED:{locale}")
        used |= loc.source_revision_ids
    for fact in desired.facts:
        evidence_ids = {revision_id for revision_id, _ in fact.evidence}
        if fact.origin == "AI_EXTRACTED":
            # DEC-028: the cited evidence is a link, not copied content; it must exist (like the
            # cited pages of an AI summary) but its licence is not required.
            if not any(revision_id in sources for revision_id in evidence_ids):
                reasons.append(f"FACT_WITHOUT_SOURCE:{fact.field_code}")
            continue
        if fact.knowledge_state == "KNOWN" and not any(
            revision_id in sources and sources[revision_id].usable for revision_id in evidence_ids
        ):
            reasons.append(f"FACT_WITHOUT_SOURCE:{fact.field_code}")
        used |= evidence_ids
    used |= {chunk.source_revision_id for chunk in desired.chunks}
    bad = sorted(
        {sources[r].publisher for r in used if r in sources and not sources[r].usable}
        | ({"<missing source revision>"} if any(r not in sources for r in used) else set())
    )
    reasons.extend(f"MISSING_LICENCE:{publisher}" for publisher in bad)
    return reasons


# ---- Report -------------------------------------------------------------------------------


@dataclass
class PlaceOutcome:
    place_id: uuid.UUID
    slug: str
    area_code: str | None
    # published | unchanged | rejected | withdrawn (by the owner, skipped) |
    # withdrawn_by_gate (was published, now fails the gate) | would_publish (dry run)
    status: str
    reasons: list[str] = field(default_factory=list)
    chunks_pending: int = 0


@dataclass
class PublishReport:
    dry_run: bool
    outcomes: list[PlaceOutcome] = field(default_factory=list)

    def count(self, status: str) -> int:
        return sum(1 for outcome in self.outcomes if outcome.status == status)

    def rejection_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for outcome in self.outcomes:
            if outcome.status not in ("rejected", "withdrawn_by_gate"):
                continue
            for code in {reason.split(":", 1)[0] for reason in outcome.reasons}:
                counts[code] = counts.get(code, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    def published_by_area(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for outcome in self.outcomes:
            if outcome.status in ("published", "unchanged", "would_publish"):
                key = outcome.area_code or "-"
                counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))


# ---- Loading ------------------------------------------------------------------------------


async def _latest_payloads(
    session: AsyncSession, place_id: uuid.UUID, provider_key: str
) -> list[tuple[str, dict[str, Any]]]:
    rows = (
        await session.execute(
            select(ImportRecord.upstream_id, ImportRecord.allowed_payload)
            .join(ImportRun, ImportRun.id == ImportRecord.import_run_id)
            .join(DataProvider, DataProvider.id == ImportRun.data_provider_id)
            .where(
                ImportRecord.place_id == place_id,
                ImportRecord.validation_status == "ACCEPTED",
                ImportRun.status == "SUCCEEDED",
                DataProvider.provider_key == provider_key,
            )
            .order_by(ImportRun.started_at.desc(), ImportRecord.created_at.desc())
        )
    ).all()
    return [(str(row[0]), dict(row[1] or {})) for row in rows]


async def gather(session: AsyncSession, place: Place) -> Contributions:
    contributions = Contributions()
    sheet = await _latest_payloads(session, place.id, "gonarra_sheet")
    contributions.sheet = sheet[0][1] if sheet else None
    wikidata = await _latest_payloads(session, place.id, "wikidata")
    contributions.wikidata = wikidata[0][1] if wikidata else None
    osm = await _latest_payloads(session, place.id, "openstreetmap")
    latest_osm: dict[str, dict[str, Any]] = {}
    for upstream_id, payload in osm:
        latest_osm.setdefault(upstream_id, payload)
    if latest_osm:
        # Several OSM elements may describe one place (node + building): prefer one with facts,
        # then the lowest element id, so the choice is deterministic.
        contributions.osm = sorted(
            latest_osm.items(), key=lambda item: (not (item[1].get("facts") or {}), item[0])
        )[0][1]
    for upstream_id, payload in await _latest_payloads(session, place.id, "wikipedia"):
        locale = upstream_id.split(":", 1)[0]
        if locale in LOCALES and locale not in contributions.wikipedia:
            contributions.wikipedia[locale] = payload
    ai_summary = await _latest_payloads(session, place.id, AI_SUMMARY_PROVIDER_KEY)
    contributions.ai_summary = ai_summary[0][1] if ai_summary else None
    ai_facts = await _latest_payloads(session, place.id, AI_FACTS_PROVIDER_KEY)
    contributions.ai_facts = ai_facts[0][1] if ai_facts else None
    contributions.web = await session.scalar(
        select(WebPlaceCandidate)
        .where(WebPlaceCandidate.promoted_place_id == place.id)
        .order_by(WebPlaceCandidate.updated_at.desc())
        .limit(1)
    )
    return contributions


async def _sources(
    session: AsyncSession, revision_ids: Iterable[uuid.UUID]
) -> dict[uuid.UUID, SourceInfo]:
    ids = set(revision_ids)
    if not ids:
        return {}
    rows = (
        await session.execute(
            select(
                SourceRevision.id, Source.publisher, Source.license_code, Source.attribution_text
            )
            .join(Source, Source.id == SourceRevision.source_id)
            .where(SourceRevision.id.in_(ids))
        )
    ).all()
    return {row[0]: SourceInfo(row[1], row[2], row[3]) for row in rows}


def _revision_ids(desired: Desired) -> set[uuid.UUID]:
    ids: set[uuid.UUID] = set()
    for loc in desired.localizations.values():
        ids |= loc.source_revision_ids | loc.cited_revision_ids
    for fact in desired.facts:
        ids |= {revision_id for revision_id, _ in fact.evidence}
    ids |= {chunk.source_revision_id for chunk in desired.chunks}
    if desired.primary_revision_id:
        ids.add(desired.primary_revision_id)
    return ids


# ---- Applying -----------------------------------------------------------------------------


@dataclass
class _Apply:
    session: AsyncSession
    place: Place
    actor: uuid.UUID
    now: datetime
    embedder: ChunkEmbedder
    chunks_pending: int = 0

    async def place_attributes(self, desired: Desired) -> None:
        place = self.place
        point = parse_point(place.location)
        if point is None or (
            round(point.longitude, 7),
            round(point.latitude, 7),
        ) != (round(desired.lng, 7), round(desired.lat, 7)):
            place.location = ewkt_point(desired.lng, desired.lat)
        if place.category_code != desired.category_code:
            place.category_code = desired.category_code
        if place.area_code != desired.area_code:
            place.area_code = desired.area_code
        assert desired.visit_minutes is not None
        low, mid, high = desired.visit_minutes
        if (place.visit_minutes_min, place.visit_minutes_suggested, place.visit_minutes_max) != (
            low,
            mid,
            high,
        ):
            place.visit_minutes_min = low
            place.visit_minutes_suggested = mid
            place.visit_minutes_max = high
        has_media = await self.session.scalar(
            select(func.count())
            .select_from(PlaceMedia)
            .join(MediaAsset, MediaAsset.id == PlaceMedia.media_asset_id)
            .where(PlaceMedia.place_id == place.id, MediaAsset.rights_state == "CLEARED")
        )
        if place.has_no_media != (not has_media):
            place.has_no_media = not has_media
        if place.workflow_state not in ("READY_TO_PUBLISH", "PUBLISHED"):
            place.workflow_state = "READY_TO_PUBLISH"
        await self.session.flush()

    async def localizations(self, desired: Desired) -> None:
        for locale, loc in desired.localizations.items():
            current = await self.session.scalar(
                select(PlaceLocalization).where(
                    PlaceLocalization.place_id == self.place.id,
                    PlaceLocalization.locale == locale,
                    PlaceLocalization.review_state == "APPROVED",
                )
            )
            if current is not None and (
                current.name,
                current.short_description,
                current.description,
                current.translation_origin,
                current.name_is_source_fallback,
            ) == (
                loc.name,
                loc.short_description,
                loc.description,
                loc.translation_origin,
                loc.name_is_source_fallback,
            ):
                continue
            if current is not None:
                await self.session.execute(
                    update(PlaceLocalization)
                    .where(PlaceLocalization.id == current.id)
                    .values(review_state="SUPERSEDED")
                )
            latest = await self.session.scalar(
                select(func.max(PlaceLocalization.localization_revision)).where(
                    PlaceLocalization.place_id == self.place.id,
                    PlaceLocalization.locale == locale,
                )
            )
            assert loc.name is not None
            self.session.add(
                PlaceLocalization(
                    place_id=self.place.id,
                    locale=locale,
                    localization_revision=(latest or 0) + 1,
                    name=loc.name,
                    short_description=loc.short_description,
                    description=loc.description,
                    translation_origin=loc.translation_origin,
                    name_is_source_fallback=loc.name_is_source_fallback,
                    review_state="APPROVED",
                    reviewed_at=self.now,
                )
            )
            await self.session.flush()

    async def aliases(self, desired: Desired) -> None:
        rows = (
            await self.session.scalars(
                select(PlaceAlias).where(PlaceAlias.place_id == self.place.id)
            )
        ).all()
        existing = {(row.locale, row.alias_normalized): row for row in rows}
        wanted: dict[tuple[str, str], tuple[str, str]] = {}
        for locale, names in desired.aliases.items():
            for index, name in enumerate(names):
                normalized = normalize_search_text(name)
                if normalized and (locale, normalized) not in wanted:
                    wanted[(locale, normalized)] = (name, "NAME" if index == 0 else "ALIAS")
        for key, (alias, kind) in wanted.items():
            row = existing.get(key)
            if row is None:
                self.session.add(
                    PlaceAlias(
                        place_id=self.place.id,
                        locale=key[0],
                        alias_kind=kind,
                        alias=alias,
                        alias_normalized=key[1],
                        review_state="APPROVED",
                    )
                )
            elif (row.alias_kind, row.alias, row.review_state) != (kind, alias, "APPROVED"):
                row.alias_kind, row.alias, row.review_state = kind, alias, "APPROVED"
        for key, row in existing.items():
            if key not in wanted and row.review_state == "APPROVED":
                row.review_state = "REJECTED"
        await self.session.flush()

    async def facts(self, desired: Desired) -> None:
        for fact in desired.facts:
            current = await self.session.scalar(
                select(PlaceFact).where(
                    PlaceFact.place_id == self.place.id,
                    PlaceFact.field_code == fact.field_code,
                    PlaceFact.review_state == "APPROVED",
                )
            )
            wanted_evidence = {(rev, claim) for rev, claim in fact.evidence}
            if current is not None:
                links = (
                    await self.session.execute(
                        select(FactEvidence.source_revision_id, FactEvidence.supported_claim).where(
                            FactEvidence.place_fact_id == current.id
                        )
                    )
                ).all()
                if (
                    current.knowledge_state == fact.knowledge_state
                    and current.value == fact.value
                    and current.origin == fact.origin
                    and current.grounding == fact.grounding
                    and current.conflict_state == "NONE"
                    and {(row[0], row[1]) for row in links} == wanted_evidence
                ):
                    continue
                await self.session.execute(
                    update(PlaceFact)
                    .where(PlaceFact.id == current.id)
                    .values(review_state="SUPERSEDED")
                )
            latest = await self.session.scalar(
                select(func.max(PlaceFact.fact_revision)).where(
                    PlaceFact.place_id == self.place.id,
                    PlaceFact.field_code == fact.field_code,
                )
            )
            row = PlaceFact(
                place_id=self.place.id,
                field_code=fact.field_code,
                fact_revision=(latest or 0) + 1,
                knowledge_state=fact.knowledge_state,
                value=fact.value if fact.value is not None else null(),  # SQL NULL, not JSON null
                verified_at=self.now,
                review_state="APPROVED",
                conflict_state="NONE",
                origin=fact.origin,
                grounding=fact.grounding,
            )
            self.session.add(row)
            await self.session.flush()
            for revision_id, claim in sorted(wanted_evidence, key=lambda item: str(item[0])):
                self.session.add(
                    FactEvidence(
                        place_fact_id=row.id, source_revision_id=revision_id, supported_claim=claim
                    )
                )
            await self.session.flush()

    async def chunks(self, desired: Desired) -> None:
        place_id = self.place.id
        approved = (
            await self.session.scalars(
                select(KnowledgeChunk).where(
                    KnowledgeChunk.place_id == place_id,
                    KnowledgeChunk.scope == "PLACE",
                    KnowledgeChunk.review_state == "APPROVED",
                )
            )
        ).all()
        current = {(row.locale, row.content_sha256) for row in approved}
        wanted = {(chunk.locale, content_sha256(chunk.content)) for chunk in desired.chunks}
        if current == wanted:
            return
        vectors: dict[str, tuple[Any, str]] = {}
        reusable = (
            await self.session.execute(
                select(
                    KnowledgeChunk.content_sha256,
                    KnowledgeChunk.embedding,
                    KnowledgeChunk.embedding_model,
                ).where(
                    KnowledgeChunk.place_id == place_id,
                    KnowledgeChunk.embedding.is_not(None),
                )
            )
        ).all()
        for hit in reusable:
            if hit[2]:
                vectors[str(hit[0])] = (hit[1], str(hit[2]))
        for chunk in desired.chunks:
            sha = content_sha256(chunk.content)
            if sha in vectors:
                continue
            embedding = await self.embedder.embed(chunk.content)
            if embedding is not None:
                vectors[sha] = (embedding.vector, embedding.model)
        pending = [c for c in desired.chunks if content_sha256(c.content) not in vectors]
        if pending:
            # Keep the previous approved corpus until every new chunk has a vector.
            self.chunks_pending = len(pending)
            return
        for row in approved:
            row.review_state = "RETIRED"
            row.retired_at = self.now
        await self.session.flush()
        revision = (
            await self.session.scalar(
                select(func.max(KnowledgeChunk.corpus_revision)).where(
                    KnowledgeChunk.place_id == place_id
                )
            )
            or 0
        ) + 1
        for chunk in desired.chunks:
            sha = content_sha256(chunk.content)
            vector, model = vectors[sha]
            row = KnowledgeChunk(
                city_id=self.place.city_id,
                place_id=place_id,
                scope="PLACE",
                locale=chunk.locale,
                section="OVERVIEW",
                corpus_revision=revision,
                chunk_index=0,
                content=chunk.content,
                content_sha256=sha,
                embedding=vector,
                embedding_model=model,
                review_state="APPROVED",
            )
            self.session.add(row)
            await self.session.flush()
            self.session.add(
                KnowledgeChunkSource(
                    knowledge_chunk_id=row.id, source_revision_id=chunk.source_revision_id
                )
            )
        await self.session.flush()

    async def identities(self) -> None:
        await self.session.execute(
            update(ExternalPlaceIdentity)
            .where(
                ExternalPlaceIdentity.place_id == self.place.id,
                ExternalPlaceIdentity.review_state == "PENDING",
            )
            .values(review_state="APPROVED", reviewed_at=self.now)
        )


async def needs_publication(session: AsyncSession, place_id: uuid.UUID) -> bool:
    """True when ``fn_publish_place`` would produce a snapshot different from the current one."""
    current = await session.scalar(
        select(CatalogPublication).where(
            CatalogPublication.place_id == place_id, CatalogPublication.state == "PUBLISHED"
        )
    )
    if current is None:
        return True
    same_place = await session.scalar(
        text(
            "SELECT p.category_code IS NOT DISTINCT FROM cp.category_code "
            "AND p.area_code IS NOT DISTINCT FROM cp.area_code "
            "AND ST_Equals(p.location::geometry, cp.location::geometry) "
            "AND p.visit_minutes_min = cp.visit_minutes_min "
            "AND p.visit_minutes_suggested = cp.visit_minutes_suggested "
            "AND p.visit_minutes_max = cp.visit_minutes_max "
            "FROM places p JOIN catalog_publications cp ON cp.place_id = p.id "
            "WHERE cp.id = :publication_id"
        ),
        {"publication_id": current.id},
    )
    if not same_place:
        return True
    approved = {
        row.locale: row.id
        for row in (
            await session.scalars(
                select(PlaceLocalization).where(
                    PlaceLocalization.place_id == place_id,
                    PlaceLocalization.review_state == "APPROVED",
                )
            )
        ).all()
    }
    if (approved.get("vi"), approved.get("en")) != (
        current.localization_vi_id,
        current.localization_en_id,
    ):
        return True
    approved_facts = set(
        (
            await session.scalars(
                select(PlaceFact.id).where(
                    PlaceFact.place_id == place_id, PlaceFact.review_state == "APPROVED"
                )
            )
        ).all()
    )
    published_facts = set(
        (
            await session.scalars(
                select(PublicationFact.place_fact_id).where(
                    PublicationFact.catalog_publication_id == current.id
                )
            )
        ).all()
    )
    if approved_facts != published_facts:
        return True
    cleared_media = set(
        (
            await session.execute(
                select(PlaceMedia.media_asset_id, PlaceMedia.ordinal)
                .join(MediaAsset, MediaAsset.id == PlaceMedia.media_asset_id)
                .where(
                    PlaceMedia.place_id == place_id,
                    MediaAsset.rights_state == "CLEARED",
                    or_(
                        MediaAsset.rights_expires_on.is_(None),
                        MediaAsset.rights_expires_on > func.current_date(),
                    ),
                )
            )
        ).all()
    )
    published_media = set(
        (
            await session.execute(
                select(PublicationMedia.media_asset_id, PublicationMedia.ordinal).where(
                    PublicationMedia.catalog_publication_id == current.id
                )
            )
        ).all()
    )
    if {tuple(row) for row in cleared_media} != {tuple(row) for row in published_media}:
        return True
    corpus = await session.scalar(
        select(func.max(KnowledgeChunk.corpus_revision)).where(
            KnowledgeChunk.place_id == place_id,
            KnowledgeChunk.scope == "PLACE",
            KnowledgeChunk.review_state == "APPROVED",
        )
    )
    return corpus != current.corpus_revision


AUTO_WITHDRAW_PREFIX = "auto-gate: "


async def _owner_withdrawn(session: AsyncSession, place_id: uuid.UUID) -> bool:
    """True when the latest publication was WITHDRAWN by the owner (not by this gate)."""
    row = (
        await session.execute(
            select(CatalogPublication.state, CatalogPublication.state_reason)
            .where(CatalogPublication.place_id == place_id)
            .order_by(CatalogPublication.publication_revision.desc())
            .limit(1)
        )
    ).first()
    return (
        row is not None
        and row[0] == "WITHDRAWN"
        and not str(row[1] or "").startswith(AUTO_WITHDRAW_PREFIX)
    )


async def _last_rejection(session: AsyncSession, place_id: uuid.UUID) -> list[str] | None:
    detail = await session.scalar(
        select(CatalogAuditEvent.detail)
        .where(
            CatalogAuditEvent.entity_table == "places",
            CatalogAuditEvent.entity_id == place_id,
            CatalogAuditEvent.action.in_(("AUTO_REJECT", "AUTO_PUBLISH")),
        )
        .order_by(CatalogAuditEvent.id.desc())
        .limit(1)
    )
    if detail is None:
        return None
    reasons = detail.get("reasons")
    return list(reasons) if isinstance(reasons, list) else None


def _sql_gate_reasons(exc: DBAPIError) -> list[str]:
    message = str(getattr(exc, "orig", exc))
    tail = message.split(": ", 2)[-1].splitlines()[0] if ": " in message else message
    return [f"SQL_GATE:{part.strip()}" for part in tail.split(",") if part.strip()]


# ---- Entry point --------------------------------------------------------------------------


async def auto_publish(
    session: AsyncSession,
    *,
    city_code: str,
    embedder: ChunkEmbedder,
    dry_run: bool = False,
    include_withdrawn: bool = False,
    place_ids: Sequence[uuid.UUID] | None = None,
) -> PublishReport:
    city = await load_city(session, city_code)
    actor = await system_account_id(session)
    await session.commit()
    areas = load_areas(city_code)
    categories = set((await session.scalars(select(Category.code))).all())
    fact_fields = (await session.scalars(select(FactField).order_by(FactField.code))).all()
    statement = select(Place.id).where(Place.city_id == city.id, Place.workflow_state != "RETIRED")
    if place_ids is not None:
        statement = statement.where(Place.id.in_(list(place_ids)))
    ids = (await session.scalars(statement.order_by(Place.slug))).all()
    report = PublishReport(dry_run=dry_run)
    for place_id in ids:
        report.outcomes.append(
            await _process(
                session,
                place_id,
                city_id=city.id,
                actor=actor,
                areas=areas,
                categories=categories,
                fact_fields=fact_fields,
                embedder=embedder,
                dry_run=dry_run,
                include_withdrawn=include_withdrawn,
            )
        )
    logger.info(
        "auto-publish published=%d unchanged=%d rejected=%d",
        report.count("published"),
        report.count("unchanged"),
        report.count("rejected"),
    )
    return report


async def _process(
    session: AsyncSession,
    place_id: uuid.UUID,
    *,
    city_id: uuid.UUID,
    actor: uuid.UUID,
    areas: Sequence[Any],
    categories: set[str],
    fact_fields: Sequence[FactField],
    embedder: ChunkEmbedder,
    dry_run: bool,
    include_withdrawn: bool,
) -> PlaceOutcome:
    place = await session.get(Place, place_id, populate_existing=True)
    assert place is not None
    contributions = await gather(session, place)
    desired = compose(
        place, contributions, area_codes=areas, categories=categories, fact_fields=fact_fields
    )
    outcome = PlaceOutcome(
        place_id=place.id, slug=place.slug, area_code=desired.area_code, status=""
    )
    if not include_withdrawn and await _owner_withdrawn(session, place.id):
        outcome.status = "withdrawn"
        return outcome
    sources = await _sources(session, _revision_ids(desired))
    inside = await inside_city(session, city_id, desired.lng, desired.lat)
    outcome.reasons = gate_reasons(desired, inside=inside, sources=sources)
    if outcome.reasons:
        outcome.status = "rejected"
        if dry_run:
            return outcome
        published = await session.scalar(
            select(CatalogPublication.id).where(
                CatalogPublication.place_id == place.id, CatalogPublication.state == "PUBLISHED"
            )
        )
        if published is not None:
            # Content that no longer passes the gate is taken down, not left stale.
            reason = AUTO_WITHDRAW_PREFIX + ", ".join(outcome.reasons)
            await session.execute(select(func.fn_withdraw_place(place.id, actor, reason[:500])))
            outcome.status = "withdrawn_by_gate"
        if await _last_rejection(session, place.id) != outcome.reasons:
            audit(
                session,
                actor_account_id=actor,
                entity_table="places",
                entity_id=place.id,
                action="AUTO_REJECT",
                to_state=place.workflow_state,
                detail={"reasons": outcome.reasons},
            )
        await session.commit()
        return outcome
    if dry_run:
        outcome.status = "would_publish"
        return outcome

    now = datetime.now(UTC)
    apply = _Apply(session=session, place=place, actor=actor, now=now, embedder=embedder)
    try:
        async with session.begin_nested():
            await apply.place_attributes(desired)
            await apply.localizations(desired)
            await apply.aliases(desired)
            await apply.facts(desired)
            await apply.chunks(desired)
            await apply.identities()
            await session.flush()
            if await needs_publication(session, place.id):
                publication_id = await session.scalar(
                    select(func.fn_publish_place(place.id, actor))
                )
                audit(
                    session,
                    actor_account_id=actor,
                    entity_table="places",
                    entity_id=place.id,
                    action="AUTO_PUBLISH",
                    to_state="PUBLISHED",
                    detail={
                        "reasons": [],
                        "publication_id": str(publication_id),
                        "sources": {
                            locale: sorted(str(r) for r in loc.source_revision_ids)
                            for locale, loc in desired.localizations.items()
                        },
                    },
                )
                outcome.status = "published"
            else:
                outcome.status = "unchanged"
        await session.commit()
    except DBAPIError as exc:
        await session.rollback()
        outcome.status = "rejected"
        outcome.reasons = _sql_gate_reasons(exc)
        logger.warning("auto-publish sql gate rejected place=%s", place.id)
    outcome.chunks_pending = apply.chunks_pending
    return outcome
