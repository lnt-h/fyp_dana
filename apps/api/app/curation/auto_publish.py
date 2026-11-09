"""Automated publication gate and auto-publish (DEC-022, DEC-031..DEC-033). No human review.

For every candidate place of a city this module

1. **composes** the content it would publish from the staged import records, deterministically
   and from human-written open sources only (DEC-031): names from the owner sheet > Wikidata >
   OpenStreetMap > Wikivoyage > promoted web candidate; the description per locale from the
   owner sheet > the matched Wikivoyage listing > the Wikipedia lead reached through the place's
   own Wikidata sitelink > none (never translated, never AI-written; Wikidata descriptions are
   short descriptions only); facts from the sheet > OpenStreetMap > Wikivoyage (``lastedit`` ≥
   2023), each with its own source revision, otherwise UNKNOWN;
2. runs the **gate** in code (``GATE_RULES``): both names, an editorial source, location inside
   the city boundary, category and area, licences and attribution, name quality (generic, not
   Vietnamese, format), not a non-stop, not a duplicate or part of another place, and — only
   when ``REQUIRE_DESCRIPTION`` (DEC-033 option B) — a description in both locales;
3. on pass, **approves** localizations, aliases, facts, chunks and identities as the system
   account and publishes through ``fn_publish_place`` (which re-checks the SQL gate), inside a
   savepoint per place. City-level Wikivoyage chunks are approved after the places.

AI-generated catalog content (``AI_SUMMARY`` descriptions, ``AI_EXTRACTED`` facts, DEC-025/
DEC-028) is retired by DEC-031: it is read only when ``allow_ai_content`` is passed **and** the
provider policy is ACTIVE (the documented restore path), and the ``AI_CONTENT`` rule rejects
it otherwise.

Idempotent: approved rows are reused while their content is unchanged, and a place is
re-published only when the publication snapshot would differ. A place whose last publication was
WITHDRAWN (owner takedown) is never re-published automatically unless ``include_withdrawn``.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, null, or_, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.normalize import fold_words
from app.curation.chunks import content_sha256
from app.curation.city_chunks import CityChunkReport, publish_city_chunks
from app.curation.common import audit, normalize_search_text, parse_point
from app.curation.dedupe import Candidate, find_duplicates
from app.curation.embedding import ChunkEmbedder
from app.curation.identity import description_mentions_other_place, other_place_index
from app.curation.names import (
    has_vietnamese_diacritics,
    is_generic_name,
    is_not_a_stop_name,
    normalise_display_name,
    prefer_diacritic_alias,
    proper_name_fallback,
    swapped_vi_en,
    venue_name_needs_editorial,
    vi_name_problem,
)
from app.curation.overrides import CurationOverrides, load_overrides
from app.curation.system import system_account_id
from app.db.types import ewkt_point
from app.ingestion.areas import AreaPolygon, assign_area, load_areas
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
from app.models.providers import (
    DataProvider,
    ExternalPlaceIdentity,
    ImportRecord,
    ImportRun,
    ProviderPolicy,
)
from app.models.reference import Category, FactField

logger = logging.getLogger("gonarra.curation")

LOCALES: tuple[str, ...] = ("vi", "en")
PROPER_NAME_CATEGORIES = frozenset({"MARKET", "CRAFT_VILLAGE", "RELIGIOUS_SITE"})
# Retired AI providers (DEC-031): grounded AI descriptions (DEC-025) and AI-extracted facts and
# short descriptions (DEC-028). Their import records stay as an audit trail.
AI_SUMMARY_PROVIDER_KEY = "gonarra_ai_summary"
AI_FACTS_PROVIDER_KEY = "gonarra_ai_facts"
AI_PROVIDER_KEYS = (AI_SUMMARY_PROVIDER_KEY, AI_FACTS_PROVIDER_KEY)
SHEET_PROVIDER_KEY = "gonarra_sheet"
WIKIVOYAGE_PROVIDER_KEY = "wikivoyage"
UNUSABLE_LICENCES = frozenset({"", "UNKNOWN", "NONE"})
AI_ORIGINS = frozenset({"AI_SUMMARY", "AI_DRAFT"})

# DEC-033 — the ONE switch for the description requirement. False = option A (description
# optional; the card shows "No description yet"); True = option B (VI and EN descriptions
# mandatory, the owner writes the missing ones in the sheet).
REQUIRE_DESCRIPTION = False
# A description shorter than this is a stub ("bridge in Vietnam") and is treated as absent.
MIN_DESCRIPTION_CHARS = 80
# Wikivoyage facts older than this are dropped (prices like "US$1 (Jan 2018)" are stale).
WIKIVOYAGE_FACTS_SINCE = date(2023, 1, 1)

# Wikidata classes (English labels, lower case) that make a NATURE/HERITAGE/VIEWPOINT place an
# area: published for the map and the Guide, never a planner stop (``places.is_area``).
AREA_CLASS_WORDS: tuple[str, ...] = (
    "bay",
    "gulf",
    "peninsula",
    "island group",
    "archipelago",
    "mountain range",
    "historic district",
    "old town",
    "city district",
    "urban district",
    "protected area",
    "nature reserve",
    "national park",
    "mountain pass",
    "river",
    "lagoon",
)
AREA_CATEGORIES = frozenset({"NATURE", "HERITAGE", "VIEWPOINT", "BEACH"})
# Venues need an editorial source (owner sheet, Wikivoyage listing, Wikidata item): an OSM
# restaurant or café alone is not a recommendation.
CURATED_ONLY_CATEGORIES = frozenset({"FOOD", "CAFE", "NIGHTLIFE"})
VENUE_NAME_CATEGORIES = CURATED_ONLY_CATEGORIES


def osm_has_tourist_signal(osm: Mapping[str, Any] | None) -> bool:
    """An OSM element mappers made visitor-ready: its own English name (``name:en`` different
    from the Vietnamese name), a website or parsed opening hours."""
    if not osm:
        return False
    names = osm.get("name") or {}
    en, vi = names.get("en"), names.get("vi")
    if en and (not vi or fold_words(str(en)) != fold_words(str(vi))):
        return True
    return bool(osm.get("website")) or bool((osm.get("facts") or {}).get("OPENING_HOURS"))


# Human-readable gate rules (reported by the CLI and documented in apps/api/data/README.md).
GATE_RULES: dict[str, str] = {
    "NO_SOURCE": "the place has no staged record with a recorded source revision",
    "NO_EDITORIAL_SOURCE": (
        "no Wikidata item, Wikivoyage listing, Wikipedia article or owner-sheet row, and (non-"
        "venue categories) no OSM name:en, website or opening hours; FOOD/CAFE/NIGHTLIFE always "
        "need an editorial source, and a generic English venue description ('... stall') never "
        "counts OSM alone as editorial"
    ),
    "OUTSIDE_CITY": "location is outside the city boundary",
    "MISSING_CATEGORY": "no category could be set (sheet or mapped Wikidata class)",
    "MISSING_AREA": "location is outside every travel-area polygon and the sheet names no area",
    "MISSING_NAME": "no name in this locale (sheet, Wikidata, OSM or Wikivoyage)",
    "MISSING_DESCRIPTION": (
        "no human-written description in this locale (sheet, Wikivoyage, Wikipedia); "
        "enforced only when REQUIRE_DESCRIPTION is on (DEC-033 option B)"
    ),
    "AI_CONTENT": "AI-generated description or fact (retired by DEC-031)",
    "GENERIC_NAME": "the name is only a class word (Chùa, Museum, Produce …)",
    "VI_NAME_NOT_VIETNAMESE": (
        "the VI name has no Vietnamese diacritics and is not an allow-listed brand; "
        "owner adds the spelling to the sheet, code never guesses diacritics"
    ),
    "NAME_SWAPPED": (
        "the VI name is plain Latin while the EN name carries Vietnamese diacritics "
        "(locales exchanged); owner fixes the order in the sheet"
    ),
    "NAME_FORMAT": "the name is in a non-Latin script",
    "NOT_A_STOP": "hotel, bank, tailor, office, supermarket or mall, or listed as not a stop",
    "DUPLICATE_OF": "another candidate is the same place (same item, or name and radius)",
    "PART_OF": "part of another catalog place (folded into the parent, not a stop)",
    "MISSING_LICENCE": "a source used by shown content has no licence or no attribution text",
    "FACT_WITHOUT_SOURCE": "a KNOWN fact has no attributed source revision",
    "SQL_GATE": "fn_publication_gate_violations reported a violation",
}
# Reported per place but never a rejection: the description candidate was dropped.
DESCRIPTION_NOTES: dict[str, str] = {
    "DESCRIPTION_TOO_SHORT": f"description under {MIN_DESCRIPTION_CHARS} characters (stub)",
    "DESCRIPTION_IDENTITY": "description names another catalog place and not this one",
    "DESCRIPTION_OTHER_ENTITY": "Wikipedia article belongs to another Wikidata item",
    "DESCRIPTION_BLOCKED": "description listed as wrong entity in data/curation",
}


# ---- Composition --------------------------------------------------------------------------


@dataclass(frozen=True)
class DescriptionCandidate:
    text: str
    revision_id: uuid.UUID
    source: str  # sheet | wikivoyage | wikipedia | ai


@dataclass
class DesiredLocalization:
    name: str | None
    short_description: str | None
    description: str | None
    source_revision_ids: set[uuid.UUID] = field(default_factory=set)
    # ORIGINAL; AI_SUMMARY only on the restore path (allow_ai_content, DEC-031).
    translation_origin: str = "ORIGINAL"
    name_is_source_fallback: bool = False
    # Pages an AI summary was written from (restore path only).
    cited_revision_ids: set[uuid.UUID] = field(default_factory=set)
    description_source_revision_id: uuid.UUID | None = None
    name_revision_id: uuid.UUID | None = None
    description_candidates: list[DescriptionCandidate] = field(default_factory=list)
    vi_name_aliases: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DesiredFact:
    field_code: str
    knowledge_state: str
    value: dict[str, Any] | None
    evidence: tuple[tuple[uuid.UUID, str], ...]  # (source_revision_id, supported_claim)
    origin: str = "SOURCE"  # SOURCE | OWNER | AI_EXTRACTED (restore path only)
    grounding: str | None = None  # STRONG | WEAK for AI_EXTRACTED
    verified_on: date | None = None  # source date (Wikivoyage lastedit); default: today


@dataclass(frozen=True)
class DesiredChunk:
    locale: str
    content: str
    source_revision_id: uuid.UUID
    section: str = "OVERVIEW"


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
    is_area: bool = False
    qid: str | None = None
    osm_ids: frozenset[str] = frozenset()
    editorial: bool = False
    source_count: int = 0
    # Name and cross-place findings (gate reasons) and dropped-description notes.
    name_reasons: list[str] = field(default_factory=list)
    cross_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class Contributions:
    sheet: dict[str, Any] | None = None
    wikidata: dict[str, Any] | None = None
    wikipedia: dict[str, dict[str, Any]] = field(default_factory=dict)
    osm: dict[str, Any] | None = None
    osm_ids: tuple[str, ...] = ()
    wikivoyage: dict[str, Any] | None = None
    web: WebPlaceCandidate | None = None
    ai_summary: dict[str, Any] | None = None
    ai_facts: dict[str, Any] | None = None
    qid: str | None = None


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
    """A staged fact with its own source revision id (sheet, OSM and Wikivoyage records)."""
    fact = ((payload or {}).get("facts") or {}).get(code)
    revision = (
        ((payload or {}).get(PROVENANCE_KEY) or {}).get("fact_source_revision_ids") or {}
    ).get(code)
    if fact and revision and fact.get("value"):
        return fact, str(revision)
    return None


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def is_area_place(
    slug: str,
    category: str | None,
    wikidata: dict[str, Any] | None,
    overrides: CurationOverrides,
) -> bool:
    """Owner list first; otherwise a Wikidata class naming an area (bay, peninsula, old town …)."""
    if slug in overrides.schedulable:
        return False
    if slug in overrides.areas:
        return True
    if category not in AREA_CATEGORIES:
        return False
    classes = [str(c).lower() for c in ((wikidata or {}).get("classes") or [])]
    return any(word == c or c.endswith(" " + word) for c in classes for word in AREA_CLASS_WORDS)


def _wikipedia_candidate(
    place_slug: str,
    locale: str,
    wiki: dict[str, Any] | None,
    qid: str | None,
    overrides: CurationOverrides,
    notes: list[str],
) -> DescriptionCandidate | None:
    text_value = _clean((wiki or {}).get("summary"))
    revision = _provenance_id(wiki)
    if not text_value or revision is None:
        return None
    item = (wiki or {}).get("wikibase_item")
    if item and qid and item != qid:
        notes.append(f"DESCRIPTION_OTHER_ENTITY:{locale}")
        return None
    if (place_slug, locale, "wikipedia") in overrides.blocked_descriptions:
        notes.append(f"DESCRIPTION_BLOCKED:{locale}")
        return None
    return DescriptionCandidate(text_value, revision, "wikipedia")


def compose(
    place: Place,
    contributions: Contributions,
    *,
    area_codes: Sequence[Any],
    categories: set[str],
    fact_fields: Sequence[FactField],
    overrides: CurationOverrides | None = None,
    allow_ai_content: bool = False,
    identity_index: Mapping[str, str] | None = None,
) -> Desired:
    overrides = overrides or CurationOverrides()
    sheet, wikidata, web = contributions.sheet, contributions.wikidata, contributions.web
    osm, wikivoyage = contributions.osm, contributions.wikivoyage
    ai_summary = contributions.ai_summary if allow_ai_content else None
    ai_facts = contributions.ai_facts if allow_ai_content else None
    ai_facts_rev = _provenance_id(ai_facts)
    point = parse_point(place.location)
    lng, lat = (point.longitude, point.latitude) if point else (0.0, 0.0)
    for payload in (sheet, wikidata, osm, wikivoyage):
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
        or (wikivoyage or {}).get("category")
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
    wv_rev = _provenance_id(wikivoyage)
    web_rev = web.source_revision_id if web is not None else None
    primary = sheet_rev or wikidata_rev or osm_rev or wv_rev or web_rev
    qid = contributions.qid
    notes: list[str] = []
    name_reasons: list[str] = []

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
        wv_name = _clean(((wikivoyage or {}).get("name") or {}).get(locale))
        web_name = _clean(getattr(web, f"name_{locale}", None)) if web is not None else None
        wd_aliases = [
            a
            for a in (_clean(x) for x in ((wikidata or {}).get("aliases") or {}).get(locale) or [])
            if a
        ]
        wv_aliases = [
            a
            for a in (
                _clean(x) for x in ((wikivoyage or {}).get("aliases") or {}).get(locale) or []
            )
            if a
        ]
        name_rev: uuid.UUID | None = None
        ordered = [
            (sheet_name, sheet_rev),
            (wd_name, wikidata_rev),
            (osm_name, osm_rev),
            (wv_name, wv_rev),
            (web_name, web_rev),
        ]
        if category in CURATED_ONLY_CATEGORIES:
            # Venue names: the travel guide's spelling beats free-form OSM tags
            # ("Phở Tùng" over "Pho Tung- so good!").
            ordered[2], ordered[3] = ordered[3], ordered[2]
        for candidate_name, revision in ordered:
            if candidate_name:
                loc.name, name_rev = candidate_name, revision
                break
        _add(loc, name_rev)
        loc.name_revision_id = name_rev
        if locale == "vi" and loc.name:
            # "Tan Ky" with a sourced alias "Tấn Ký": the spelling with diacritics wins.
            better = prefer_diacritic_alias(
                loc.name, [n for n in (osm_name, wv_name, *wd_aliases, *wv_aliases) if n]
            )
            if better:
                loc.name = better
        if loc.name:
            fixed = normalise_display_name(loc.name)
            if fixed is None:
                name_reasons.append(f"NAME_FORMAT:{locale}")
            else:
                loc.name = fixed
        if locale == "vi":
            vi_name_rev = name_rev
        elif not loc.name and "vi" in localizations:
            # Proper-name fallback (D3, DEC-031): the Vietnamese name unchanged, never translated.
            fallback = proper_name_fallback(category, localizations["vi"].name)
            if fallback is not None:
                loc.name = fallback
                loc.name_is_source_fallback = True
                _add(loc, vi_name_rev)

        sheet_short = _clean(((sheet or {}).get("short_description") or {}).get(locale))
        wd_desc = _clean(((wikidata or {}).get("description") or {}).get(locale))
        ai_short = _clean(((ai_facts or {}).get("short_description") or {}).get(locale))
        if sheet_short:
            loc.short_description = sheet_short
            _add(loc, sheet_rev)
        elif wd_desc:
            # A Wikidata description is a short label ("bridge in Vietnam"), never the
            # description itself (DEC-031).
            loc.short_description = wd_desc
            _add(loc, wikidata_rev)
        elif ai_short and ai_facts_rev:
            loc.short_description = ai_short
            _add(loc, ai_facts_rev)

        # Description priority (DEC-031): sheet > Wikivoyage listing > own-sitelink Wikipedia.
        candidates: list[DescriptionCandidate] = []
        sheet_desc = _clean(((sheet or {}).get("description") or {}).get(locale))
        if sheet_desc and sheet_rev:
            candidates.append(DescriptionCandidate(sheet_desc, sheet_rev, "sheet"))
        wv_desc = _clean(((wikivoyage or {}).get("description") or {}).get(locale))
        if wv_desc and wv_rev:
            if (place.slug, locale, "wikivoyage") in overrides.blocked_descriptions:
                notes.append(f"DESCRIPTION_BLOCKED:{locale}")
            else:
                candidates.append(DescriptionCandidate(wv_desc, wv_rev, "wikivoyage"))
        wiki = _wikipedia_candidate(
            place.slug, locale, contributions.wikipedia.get(locale), qid, overrides, notes
        )
        if wiki is not None:
            candidates.append(wiki)
        ai_text = _clean(((ai_summary or {}).get("description") or {}).get(locale))
        if ai_text and ai_rev:
            candidates.append(DescriptionCandidate(ai_text, ai_rev, "ai"))
        own_names = [
            n
            for n in (loc.name, sheet_name, wd_name, osm_name, wv_name, *wd_aliases, *wv_aliases)
            if n
        ]
        for candidate in candidates:
            if len(candidate.text) < MIN_DESCRIPTION_CHARS:
                notes.append(f"DESCRIPTION_TOO_SHORT:{locale}:{candidate.source}")
                continue
            if identity_index is not None and candidate.source != "sheet":
                other = description_mentions_other_place(
                    candidate.text, slug=place.slug, own_names=own_names, index=identity_index
                )
                if other is not None:
                    notes.append(f"DESCRIPTION_IDENTITY:{locale}:{candidate.source}:{other}")
                    continue
            loc.description = candidate.text
            loc.description_source_revision_id = candidate.revision_id
            loc.source_revision_ids.add(candidate.revision_id)
            if candidate.source == "ai":
                loc.translation_origin = "AI_SUMMARY"
                loc.cited_revision_ids |= ai_cited
            break
        loc.description_candidates = candidates
        # Guide chunks: human text only — the accepted Wikipedia lead (OVERVIEW) and the
        # Wikivoyage listing (VISIT_TIPS), each verbatim with its own source revision.
        for candidate in candidates:
            if candidate.source not in ("wikipedia", "wikivoyage"):
                continue
            flagged = f"DESCRIPTION_IDENTITY:{locale}:{candidate.source}"
            if len(candidate.text) < MIN_DESCRIPTION_CHARS or any(
                n.startswith(flagged) for n in notes
            ):
                continue
            section = "OVERVIEW" if candidate.source == "wikipedia" else "VISIT_TIPS"
            chunks.append(DesiredChunk(locale, candidate.text, candidate.revision_id, section))
        localizations[locale] = loc

        names: list[str] = []
        for candidate_name in (
            loc.name,
            wd_name,
            sheet_name,
            osm_name,
            wv_name,
            *wd_aliases,
            *wv_aliases,
        ):
            cleaned = _clean(candidate_name)
            if cleaned and cleaned not in names:
                names.append(cleaned)
        aliases[locale] = names

    facts: list[DesiredFact] = []
    wv_lastedit = _parse_date((wikivoyage or {}).get("lastedit"))
    for fact_field in fact_fields:
        code = fact_field.code
        owner = _sourced_fact(sheet, code)
        sourced = owner or _sourced_fact(osm, code)
        verified_on: date | None = None
        if sourced is None and wv_lastedit is not None and wv_lastedit >= WIKIVOYAGE_FACTS_SINCE:
            sourced = _sourced_fact(wikivoyage, code)
            verified_on = wv_lastedit if sourced is not None else None
        ai = _sourced_fact(ai_facts, code) if sourced is None else None
        if sourced is not None:
            staged, fact_rev = sourced
            value = dict(staged["value"])
            claim = f"{code}: {value.get('text') or value}"[:500]
            origin = "OWNER" if owner is not None else "SOURCE"
            facts.append(
                DesiredFact(
                    code,
                    "KNOWN",
                    value,
                    ((uuid.UUID(fact_rev), claim),),
                    origin,
                    verified_on=verified_on,
                )
            )
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

    vi_loc, en_loc = localizations["vi"], localizations["en"]
    if not vi_loc.name and en_loc.name and not en_loc.name_is_source_fallback:
        # The reverse proper-name rule (DEC-031): a name that is already Vietnamese ("Cơm Nhà
        # Linh") or a venue brand ("Golden Pine") is the same in both locales; never translated.
        if category in VENUE_NAME_CATEGORIES or (
            category in PROPER_NAME_CATEGORIES and has_vietnamese_diacritics(en_loc.name)
        ):
            vi_loc.name = en_loc.name
            vi_loc.name_is_source_fallback = True
            _add(vi_loc, en_loc.name_revision_id)
            aliases["vi"] = [en_loc.name, *[a for a in aliases["vi"] if a != en_loc.name]]
    vi_name = localizations["vi"].name
    en_name = localizations["en"].name
    for locale in LOCALES:
        name = localizations[locale].name
        if name and is_generic_name(name, has_qid=bool(qid)):
            name_reasons.append(f"GENERIC_NAME:{locale}")
    if vi_name and vi_name_problem(vi_name, category):
        name_reasons.append("VI_NAME_NOT_VIETNAMESE")
    if swapped_vi_en(vi_name, en_name):
        name_reasons.append("NAME_SWAPPED")

    editorial = bool(
        qid
        or sheet is not None
        or wikivoyage is not None
        or any(_provenance_id(w) for w in contributions.wikipedia.values())
        or (
            category not in CURATED_ONLY_CATEGORIES
            and not venue_name_needs_editorial(
                localizations["vi"].name, localizations["en"].name
            )
            and osm_has_tourist_signal(osm)
        )
    )
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
        is_area=is_area_place(place.slug, category, wikidata, overrides),
        qid=qid,
        osm_ids=frozenset(contributions.osm_ids),
        editorial=editorial,
        source_count=sum(
            1
            for present in (
                sheet,
                wikidata,
                osm,
                wikivoyage,
                web,
                contributions.wikipedia.get("vi"),
                contributions.wikipedia.get("en"),
            )
            if present
        ),
        name_reasons=name_reasons,
        notes=notes,
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
    desired: Desired,
    *,
    inside: bool,
    sources: dict[uuid.UUID, SourceInfo],
    allow_ai_content: bool = False,
    require_description: bool | None = None,
    not_a_stop: str | None = None,
) -> list[str]:
    require = REQUIRE_DESCRIPTION if require_description is None else require_description
    reasons: list[str] = []
    if desired.primary_revision_id is None:
        reasons.append("NO_SOURCE")
    elif not desired.editorial:
        reasons.append("NO_EDITORIAL_SOURCE")
    if not inside:
        reasons.append("OUTSIDE_CITY")
    if desired.category_code is None:
        reasons.append("MISSING_CATEGORY")
    if desired.area_code is None:
        reasons.append("MISSING_AREA")
    used: set[uuid.UUID] = set()
    ai_content = False
    for locale in LOCALES:
        loc = desired.localizations[locale]
        if not loc.name:
            reasons.append(f"MISSING_NAME:{locale}")
        if require and not loc.description:
            reasons.append(f"MISSING_DESCRIPTION:{locale}")
        if loc.translation_origin in AI_ORIGINS:
            ai_content = True
            if allow_ai_content and not any(
                revision_id in sources for revision_id in loc.cited_revision_ids
            ):
                reasons.append(f"FACT_WITHOUT_SOURCE:description:{locale}")
        used |= loc.source_revision_ids
    reasons.extend(desired.name_reasons)
    if not_a_stop is not None or any(
        is_not_a_stop_name(loc.name) for loc in desired.localizations.values()
    ):
        reasons.append("NOT_A_STOP")
    for fact in desired.facts:
        evidence_ids = {revision_id for revision_id, _ in fact.evidence}
        if fact.origin == "AI_EXTRACTED":
            ai_content = True
            if not any(revision_id in sources for revision_id in evidence_ids):
                reasons.append(f"FACT_WITHOUT_SOURCE:{fact.field_code}")
            continue
        if fact.knowledge_state == "KNOWN" and not any(
            revision_id in sources and sources[revision_id].usable for revision_id in evidence_ids
        ):
            reasons.append(f"FACT_WITHOUT_SOURCE:{fact.field_code}")
        used |= evidence_ids
    if ai_content and not allow_ai_content:
        reasons.append("AI_CONTENT")
    used |= {chunk.source_revision_id for chunk in desired.chunks}
    bad = sorted(
        {sources[r].publisher for r in used if r in sources and not sources[r].usable}
        | ({"<missing source revision>"} if any(r not in sources for r in used) else set())
    )
    reasons.extend(f"MISSING_LICENCE:{publisher}" for publisher in bad)
    reasons.extend(desired.cross_reasons)
    return reasons


# ---- Cross-place rules (duplicates, parts, shared display names) ---------------------------


@dataclass
class PlaceDraft:
    """One composed candidate of a run (``auto_publish`` composes every place first)."""

    place: Place
    contributions: Contributions
    desired: Desired


def _names(desired: Desired) -> list[str]:
    return [name for names in desired.aliases.values() for name in names]


def identity_index_for(drafts: Iterable[PlaceDraft]) -> dict[str, str]:
    return other_place_index({d.place.slug: _names(d.desired) for d in drafts})


def apply_cross_place_rules(
    drafts: Sequence[PlaceDraft],
    overrides: CurationOverrides,
    eligible: set[str] | None = None,
) -> None:
    """Adds ``DUPLICATE_OF:<slug>`` and ``PART_OF:<slug>`` to ``desired.cross_reasons``.
    ``eligible`` (slugs passing every other rule) are preferred as duplicate keepers."""
    by_slug = {d.place.slug: d for d in drafts}
    candidates = [
        Candidate(
            slug=d.place.slug,
            category=d.desired.category_code,
            lat=d.desired.lat,
            lng=d.desired.lng,
            names=tuple(_names(d.desired)),
            qid=d.desired.qid,
            osm_ids=d.desired.osm_ids,
            source_count=d.desired.source_count,
            created_at=d.place.created_at,
            vi_name=d.desired.localizations["vi"].name,
            eligible=eligible is None or d.place.slug in eligible,
        )
        for d in drafts
        if not d.desired.is_area
    ]
    for duplicate, keeper in find_duplicates(candidates).items():
        by_slug[duplicate].desired.cross_reasons.append(f"DUPLICATE_OF:{keeper}")
    by_qid = {d.desired.qid: d for d in drafts if d.desired.qid}
    for draft in drafts:
        parent_slug = overrides.part_of.get(draft.place.slug)
        if parent_slug is None:
            for parent_qid in (draft.contributions.wikidata or {}).get("part_of") or []:
                parent = by_qid.get(str(parent_qid))
                if parent is not None and parent is not draft:
                    parent_slug = parent.place.slug
                    break
        if parent_slug is None and draft.desired.qid:
            for other in drafts:
                has_part = (other.contributions.wikidata or {}).get("has_part") or []
                if other is not draft and draft.desired.qid in has_part:
                    parent_slug = other.place.slug
                    break
        if parent_slug is None or parent_slug == draft.place.slug:
            continue
        parent_draft = by_slug.get(parent_slug)
        # Children of an area (Hội An Ancient Town, Sơn Trà) stay stops.
        if parent_draft is not None and parent_draft.desired.is_area:
            continue
        draft.desired.cross_reasons.append(f"PART_OF:{parent_slug}")


def disambiguate_names(drafts: Sequence[PlaceDraft], areas: Sequence[AreaPolygon]) -> None:
    """Places that will be published under one shared name get the area's short name appended
    ("Chùa Linh Ứng (Bãi Bụt)"); the plain name stays a search alias. Display only."""
    short = {a.code: {"vi": a.short_vi, "en": a.short_en} for a in areas}
    for locale in LOCALES:
        groups: dict[str, list[PlaceDraft]] = {}
        for draft in drafts:
            name = draft.desired.localizations[locale].name
            if name:
                groups.setdefault(fold_words(name), []).append(draft)
        for members in groups.values():
            if len(members) < 2:
                continue
            suffixes = [short.get(m.desired.area_code or "", {}).get(locale) for m in members]
            if None in suffixes or len(set(suffixes)) != len(suffixes):
                continue  # two in one area, or an area without a short name: leave as is
            for member, suffix in zip(members, suffixes, strict=True):
                loc = member.desired.localizations[locale]
                loc.name = f"{loc.name} ({suffix})"
                names = [n for n in member.desired.aliases[locale] if n != loc.name]
                member.desired.aliases[locale] = [loc.name, *names]


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
    category_code: str | None = None
    is_area: bool = False
    has_description: dict[str, bool] = field(default_factory=dict)
    description_sources: dict[str, str | None] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    name_vi: str | None = None
    name_en: str | None = None


@dataclass
class PublishReport:
    dry_run: bool
    outcomes: list[PlaceOutcome] = field(default_factory=list)
    city_chunks: CityChunkReport | None = None

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

    def publishable(self) -> list[PlaceOutcome]:
        return [o for o in self.outcomes if o.status in ("published", "unchanged", "would_publish")]

    def published_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for outcome in self.publishable():
            key = outcome.category_code or "-"
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def note_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for outcome in self.outcomes:
            for code in {note.split(":", 1)[0] for note in outcome.notes}:
                counts[code] = counts.get(code, 0) + 1
        return dict(sorted(counts.items()))

    def published_by_area(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for outcome in self.outcomes:
            if outcome.status in ("published", "unchanged", "would_publish"):
                key = outcome.area_code or "-"
                counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))


# ---- Loading ------------------------------------------------------------------------------


async def _latest_payloads(
    session: AsyncSession,
    place_id: uuid.UUID,
    provider_key: str,
    *,
    latest_run_only: bool = False,
) -> list[tuple[str, dict[str, Any]]]:
    """Accepted payloads of one place, newest first. ``latest_run_only``: only the provider's
    newest SUCCEEDED run counts (a full-snapshot importer such as Wikivoyage: a listing no
    longer matched to this place must not keep feeding it)."""
    statement = (
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
    if latest_run_only:
        latest = (
            select(ImportRun.id)
            .join(DataProvider, DataProvider.id == ImportRun.data_provider_id)
            .where(DataProvider.provider_key == provider_key, ImportRun.status == "SUCCEEDED")
            .order_by(ImportRun.started_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        statement = statement.where(ImportRun.id == latest)
    rows = (await session.execute(statement)).all()
    return [(str(row[0]), dict(row[1] or {})) for row in rows]


async def policy_active(session: AsyncSession, provider_key: str) -> bool:
    """True when the provider has an ACTIVE policy (``require_active_policy`` without raising)."""
    found = await session.scalar(
        select(ProviderPolicy.id)
        .join(DataProvider, DataProvider.id == ProviderPolicy.data_provider_id)
        .where(DataProvider.provider_key == provider_key, ProviderPolicy.status == "ACTIVE")
        .limit(1)
    )
    return found is not None


async def gather(
    session: AsyncSession, place: Place, *, ai_providers: Iterable[str] = ()
) -> Contributions:
    """Staged payloads of one place. AI providers are read only when listed in ``ai_providers``
    (the restore path: ``allow_ai_content`` and an ACTIVE policy, DEC-031)."""
    contributions = Contributions()
    sheet = await _latest_payloads(session, place.id, SHEET_PROVIDER_KEY)
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
        contributions.osm_ids = tuple(sorted(latest_osm))
    for upstream_id, payload in await _latest_payloads(session, place.id, "wikipedia"):
        locale = upstream_id.split(":", 1)[0]
        if locale in LOCALES and locale not in contributions.wikipedia:
            contributions.wikipedia[locale] = payload
    wikivoyage = await _latest_payloads(
        session, place.id, WIKIVOYAGE_PROVIDER_KEY, latest_run_only=True
    )
    contributions.wikivoyage = wikivoyage[0][1] if wikivoyage else None
    if AI_SUMMARY_PROVIDER_KEY in ai_providers:
        ai_summary = await _latest_payloads(session, place.id, AI_SUMMARY_PROVIDER_KEY)
        contributions.ai_summary = ai_summary[0][1] if ai_summary else None
    if AI_FACTS_PROVIDER_KEY in ai_providers:
        ai_facts = await _latest_payloads(session, place.id, AI_FACTS_PROVIDER_KEY)
        contributions.ai_facts = ai_facts[0][1] if ai_facts else None
    contributions.web = await session.scalar(
        select(WebPlaceCandidate)
        .where(WebPlaceCandidate.promoted_place_id == place.id)
        .order_by(WebPlaceCandidate.updated_at.desc())
        .limit(1)
    )
    qid = (contributions.wikidata or {}).get("id") or (contributions.osm or {}).get("wikidata")
    if not qid:
        qid = await session.scalar(
            select(ExternalPlaceIdentity.upstream_id)
            .join(DataProvider, DataProvider.id == ExternalPlaceIdentity.data_provider_id)
            .where(
                ExternalPlaceIdentity.place_id == place.id,
                DataProvider.provider_key == "wikidata",
                ExternalPlaceIdentity.review_state != "REJECTED",
            )
            .order_by(ExternalPlaceIdentity.upstream_id)
            .limit(1)
        )
    contributions.qid = str(qid) if qid else None
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
        if place.is_area != desired.is_area:
            place.is_area = desired.is_area
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
                current.description_source_revision_id,
            ) == (
                loc.name,
                loc.short_description,
                loc.description,
                loc.translation_origin,
                loc.name_is_source_fallback,
                loc.description_source_revision_id,
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
                    description_source_revision_id=loc.description_source_revision_id,
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
            verified_at = (
                datetime(
                    fact.verified_on.year, fact.verified_on.month, fact.verified_on.day, tzinfo=UTC
                )
                if fact.verified_on is not None
                else self.now
            )
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
                    and (fact.verified_on is None or current.verified_at == verified_at)
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
                verified_at=verified_at,
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
        current = {(row.locale, row.section, row.content_sha256) for row in approved}
        wanted = {
            (chunk.locale, chunk.section, content_sha256(chunk.content)) for chunk in desired.chunks
        }
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
        next_index: dict[str, int] = {}
        for chunk in desired.chunks:
            sha = content_sha256(chunk.content)
            vector, model = vectors[sha]
            index = next_index.get(chunk.locale, 0)
            next_index[chunk.locale] = index + 1
            row = KnowledgeChunk(
                city_id=self.place.city_id,
                place_id=place_id,
                scope="PLACE",
                locale=chunk.locale,
                section=chunk.section,
                corpus_revision=revision,
                chunk_index=index,
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
            "AND p.is_area = cp.is_area "
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
    allow_ai_content: bool = False,
    require_description: bool | None = None,
) -> PublishReport:
    """Compose every candidate of the city, apply the cross-place rules, gate and publish.

    ``place_ids`` limits what is written; every candidate is still composed so duplicates,
    parts and shared names are judged against the whole city. ``allow_ai_content`` is the
    DEC-031 restore path (AI payloads are read only while their policy is ACTIVE)."""
    city = await load_city(session, city_code)
    actor = await system_account_id(session)
    await session.commit()
    areas = load_areas(city_code)
    overrides = load_overrides(city_code)
    categories = set((await session.scalars(select(Category.code))).all())
    fact_fields = (await session.scalars(select(FactField).order_by(FactField.code))).all()
    ai_providers = [
        key for key in AI_PROVIDER_KEYS if allow_ai_content and await policy_active(session, key)
    ]
    ids = (
        await session.scalars(
            select(Place.id)
            .where(Place.city_id == city.id, Place.workflow_state != "RETIRED")
            .order_by(Place.slug)
        )
    ).all()

    def build(
        place: Place, contributions: Contributions, index: Mapping[str, str] | None
    ) -> Desired:
        return compose(
            place,
            contributions,
            area_codes=areas,
            categories=categories,
            fact_fields=fact_fields,
            overrides=overrides,
            allow_ai_content=allow_ai_content,
            identity_index=index,
        )

    drafts: list[PlaceDraft] = []
    for place_id in ids:
        place = await session.get(Place, place_id)
        assert place is not None
        contributions = await gather(session, place, ai_providers=ai_providers)
        drafts.append(PlaceDraft(place, contributions, build(place, contributions, None)))
    index = identity_index_for(drafts)
    for draft in drafts:
        draft.desired = build(draft.place, draft.contributions, index)
    evaluated: list[tuple[PlaceDraft, list[str]]] = []
    for draft in drafts:
        sources = await _sources(session, _revision_ids(draft.desired))
        inside = await inside_city(session, city.id, draft.desired.lng, draft.desired.lat)
        reasons = gate_reasons(
            draft.desired,
            inside=inside,
            sources=sources,
            allow_ai_content=allow_ai_content,
            require_description=require_description,
            not_a_stop=overrides.not_a_stop.get(draft.place.slug),
        )
        evaluated.append((draft, reasons))
    apply_cross_place_rules(
        drafts, overrides, eligible={d.place.slug for d, reasons in evaluated if not reasons}
    )
    evaluated = [(d, [*reasons, *d.desired.cross_reasons]) for d, reasons in evaluated]
    disambiguate_names([d for d, reasons in evaluated if not reasons], areas)

    wanted = set(place_ids) if place_ids is not None else None
    report = PublishReport(dry_run=dry_run)
    for draft, reasons in evaluated:
        if wanted is not None and draft.place.id not in wanted:
            continue
        report.outcomes.append(
            await _process(
                session,
                draft,
                reasons,
                actor=actor,
                embedder=embedder,
                dry_run=dry_run,
                include_withdrawn=include_withdrawn,
            )
        )
    if place_ids is None:
        report.city_chunks = await publish_city_chunks(
            session, city_id=city.id, embedder=embedder, dry_run=dry_run
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
    draft: PlaceDraft,
    reasons: list[str],
    *,
    actor: uuid.UUID,
    embedder: ChunkEmbedder,
    dry_run: bool,
    include_withdrawn: bool,
) -> PlaceOutcome:
    place = await session.get(Place, draft.place.id, populate_existing=True)
    assert place is not None
    desired = draft.desired
    outcome = PlaceOutcome(
        place_id=place.id,
        slug=place.slug,
        area_code=desired.area_code,
        status="",
        category_code=desired.category_code,
        is_area=desired.is_area,
        has_description={
            locale: bool(loc.description) for locale, loc in desired.localizations.items()
        },
        description_sources={
            locale: next(
                (
                    c.source
                    for c in loc.description_candidates
                    if c.revision_id == loc.description_source_revision_id
                ),
                None,
            )
            for locale, loc in desired.localizations.items()
        },
        notes=list(desired.notes),
        name_vi=desired.localizations["vi"].name,
        name_en=desired.localizations["en"].name,
    )
    if not include_withdrawn and await _owner_withdrawn(session, place.id):
        outcome.status = "withdrawn"
        return outcome
    outcome.reasons = list(reasons)
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
