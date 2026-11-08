"""AI-extracted facts and short descriptions from supplied sources (DEC-028): ``enrich facts``.

Offline, operator-run, for PUBLISHED places whose ADDRESS_VI, OPENING_HOURS or ADMISSION_PRICE is
UNKNOWN or whose short description is missing in a locale:

1. **Evidence**, each item with an id and (for fact evidence) a source revision:
   * ``osm``: the element's current OSM tags (one Overpass request for all places; ``addr:*``,
     ``opening_hours``, ``fee``, ``charge``; phone, e-mail and website tags are never sent);
     revision = the element's stored OSM source revision;
   * ``wikidata``: P6375 street address, P2555 fee (VND), P856 website of the place's own item
     (``wbgetentities``, 50 per request); revision = the item's Wikidata source revision;
   * ``wiki:vi`` / ``wiki:en``: stored Wikipedia extracts;
   * ``web1``…: the official site (OSM ``website``) and up to two pages of a Tavily search
     "<name VI> giờ mở cửa giá vé địa chỉ" (aggregator hosts skipped), fetched by the research
     ``PageFetcher`` (each page a source revision);
   * ``desc:vi`` / ``desc:en``: the stored descriptions, for the short descriptions only.
2. The ``grounded_writer`` FACT_EXTRACT profile extracts the fields; code validation
   (:mod:`app.agents.fact_validation`, relaxed rule) keeps a field when it cites a supplied id,
   parses hours and prices, rejects contact data and sets STRONG/WEAK grounding. A fact citing an
   item without a source revision (a description) is dropped.
3. Accepted facts and short descriptions are staged as one import record per place of provider
   ``gonarra_ai_facts`` (own source revision, licence ``GONARRA-AI-FACTS``); the fact provenance
   maps each field to its cited evidence revision. ``publish auto`` then publishes them as
   ``origin = AI_EXTRACTED`` facts (only where no sheet or OSM value exists).

Every provider call goes through the quota ledger and the run's own caps (``max_searches``,
``max_model_calls``). Logs carry counts only, never fact text, evidence or prompts.
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runtime import AgentContext
from app.agents.schemas import FactEvidenceItem
from app.agents.writer import extract_place_facts
from app.ai.invocations import Purpose
from app.ai.quota import QuotaLedger, SessionFactory
from app.config import Settings
from app.curation.auto_publish import AI_FACTS_PROVIDER_KEY, LOCALES, compose, gather
from app.ingestion.areas import load_areas
from app.ingestion.common import (
    PROVENANCE_KEY,
    USER_AGENT,
    RunReport,
    add_record,
    canonical_json,
    finish_run,
    get_or_create_revision,
    get_or_create_source,
    load_city,
    require_active_policy,
    sha256_hex,
    start_run,
)
from app.ingestion.osm import OVERPASS_ENDPOINTS
from app.ingestion.wikidata import API_URL as WIKIDATA_API_URL
from app.ingestion.wikidata import ENTITY_URL, get_with_retries
from app.ingestion.wikidata import LICENSE_CODE as WIKIDATA_LICENCE
from app.models.catalog import Place
from app.models.providers import DataProvider, ImportRecord, ImportRun
from app.models.reference import Category, FactField
from app.research.enrich import QUERY_TOWN, _https, _skipped_host
from app.research.fetch import PageFetcher
from app.research.store import SqlResearchStore
from app.research.tavily import SearchStatus, TavilySearch

logger = logging.getLogger("gonarra.curation")

IMPORTER_VERSION = "facts-1"
FACT_FIELDS = ("ADDRESS_VI", "OPENING_HOURS", "ADMISSION_PRICE")
FACTS_PUBLISHER = "Gonarra"
FACTS_LICENCE = "GONARRA-AI-FACTS"
FACTS_ATTRIBUTION = "Facts extracted by Gonarra with AI assistance, only from the cited sources"
MAX_SEARCH_PAGES = 2
MAX_WIKI_CHARS = 2500
NO_FACTS = "NO_FACTS"
# OSM tags that may be sent as evidence (never phone, e-mail, website or contact:* tags).
OSM_EVIDENCE_TAGS = ("opening_hours", "fee", "charge", "fee:conditional", "description")
VND_QIDS = frozenset({"Q192090"})  # Vietnamese đồng
WIKIDATA_BATCH = 50


@dataclass
class FactCandidate:
    place_id: uuid.UUID
    slug: str
    name_vi: str
    name_en: str | None
    category: str | None
    area_code: str | None
    unknown: tuple[str, ...]
    short_missing: tuple[str, ...]
    descriptions: dict[str, str] = field(default_factory=dict)
    wikipedia: list[tuple[str, str, str, uuid.UUID]] = field(default_factory=list)
    osm_id: str | None = None  # node/123
    osm_revision: uuid.UUID | None = None
    qid: str | None = None
    website: str | None = None


@dataclass
class FactsReport(RunReport):
    selected: int = 0
    extracted_places: int = 0
    no_facts: int = 0
    failed: int = 0
    tavily_calls: int = 0
    tavily_cached: int = 0
    pages_fetched: int = 0
    wikimedia_requests: int = 0
    overpass_requests: int = 0
    by_field: Counter[str] = field(default_factory=Counter)
    by_grounding: Counter[str] = field(default_factory=Counter)
    issues: Counter[str] = field(default_factory=Counter)
    model_calls: Counter[str] = field(default_factory=Counter)
    stopped: str = ""


# ---- Candidates ---------------------------------------------------------------------------


async def _already_done(session: AsyncSession) -> set[uuid.UUID]:
    rows = await session.scalars(
        select(ImportRecord.place_id)
        .join(ImportRun, ImportRun.id == ImportRecord.import_run_id)
        .join(DataProvider, DataProvider.id == ImportRun.data_provider_id)
        .where(
            DataProvider.provider_key == AI_FACTS_PROVIDER_KEY,
            ImportRun.status == "SUCCEEDED",
            ImportRecord.place_id.is_not(None),
        )
    )
    return {row for row in rows.all() if row is not None}


async def load_fact_candidates(
    session: AsyncSession, *, city_code: str, retry: bool = False
) -> list[FactCandidate]:
    city = await load_city(session, city_code)
    areas = load_areas(city_code)
    categories = set((await session.scalars(select(Category.code))).all())
    fact_fields = (await session.scalars(select(FactField))).all()
    done = set() if retry else await _already_done(session)
    published = (
        await session.scalars(
            select(Place)
            .where(Place.city_id == city.id, Place.workflow_state == "PUBLISHED")
            .order_by(Place.slug)
        )
    ).all()
    result: list[FactCandidate] = []
    for place in published:
        if place.id in done:
            continue
        contributions = await gather(session, place)
        desired = compose(
            place,
            contributions,
            area_codes=areas,
            categories=categories,
            fact_fields=fact_fields,
        )
        unknown = tuple(
            fact.field_code
            for fact in desired.facts
            if fact.field_code in FACT_FIELDS and fact.knowledge_state != "KNOWN"
        )
        short_missing = tuple(
            locale for locale in LOCALES if not desired.localizations[locale].short_description
        )
        if not unknown and not short_missing:
            continue
        name_vi = desired.localizations["vi"].name
        if not name_vi:
            continue
        en = desired.localizations["en"]
        osm = contributions.osm or {}
        osm_rev = (osm.get(PROVENANCE_KEY) or {}).get("source_revision_id")
        wikidata = contributions.wikidata or {}
        candidate = FactCandidate(
            place_id=place.id,
            slug=place.slug,
            name_vi=name_vi,
            name_en=None if en.name_is_source_fallback else en.name,
            category=desired.category_code,
            area_code=desired.area_code,
            unknown=unknown,
            short_missing=short_missing,
            descriptions={
                locale: loc.description
                for locale, loc in desired.localizations.items()
                if loc.description
            },
            osm_id=str(osm.get("id")) if osm.get("id") else None,
            osm_revision=uuid.UUID(str(osm_rev)) if osm_rev else None,
            qid=str(wikidata.get("id")) if wikidata.get("id") else (osm.get("wikidata") or None),
            website=_https(osm.get("website")),
        )
        for locale in LOCALES:
            page = contributions.wikipedia.get(locale) or {}
            revision = (page.get(PROVENANCE_KEY) or {}).get("source_revision_id")
            if page.get("summary") and revision:
                candidate.wikipedia.append(
                    (
                        locale,
                        str(page.get("page_url") or ""),
                        str(page["summary"])[:MAX_WIKI_CHARS],
                        uuid.UUID(str(revision)),
                    )
                )
        result.append(candidate)
    return result


# ---- Structured evidence (OSM tags, Wikidata claims) ----------------------------------------


def osm_evidence_text(tags: dict[str, str]) -> str:
    """Address and visitor tags only; contact data is never sent."""
    lines: list[str] = []
    address = [
        tags.get(key, "").strip()
        for key in (
            "addr:housenumber",
            "addr:street",
            "addr:quarter",
            "addr:subdistrict",
            "addr:district",
            "addr:city",
        )
    ]
    if any(address):
        lines.append("address: " + ", ".join(part for part in address if part))
    if tags.get("addr:full"):
        lines.append(f"address: {tags['addr:full'].strip()}")
    for key in OSM_EVIDENCE_TAGS:
        if tags.get(key):
            lines.append(f"{key}: {tags[key].strip()}")
    return "\n".join(lines)


def build_osm_query(element_ids: Sequence[str]) -> str:
    by_type: dict[str, list[str]] = {"node": [], "way": [], "relation": []}
    for element in element_ids:
        kind, _, number = element.partition("/")
        if kind in by_type and number.isdigit():
            by_type[kind].append(number)
    parts = "".join(f"{kind}(id:{','.join(ids)});" for kind, ids in by_type.items() if ids)
    return f"[out:json][timeout:60];({parts});out tags;"


async def fetch_osm_tags(
    client: httpx.AsyncClient, element_ids: Sequence[str]
) -> dict[str, dict[str, str]]:
    """One Overpass request: element id → tags (empty on failure)."""
    if not element_ids:
        return {}
    query = build_osm_query(element_ids)
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            response = await get_with_retries(
                client,
                endpoint,
                params={"data": query},
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                max_attempts=2,
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("overpass tags failed endpoint=%s error=%s", endpoint, exc)
            continue
        return {
            f"{element.get('type')}/{element.get('id')}": dict(element.get("tags") or {})
            for element in body.get("elements") or []
        }
    return {}


def wikidata_evidence_text(entity: dict[str, Any]) -> str:
    """P6375 street address, P2555 fee (VND only) and P856 website presence."""
    claims = entity.get("claims") or {}
    lines: list[str] = []
    for claim in claims.get("P6375") or []:
        value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
        if isinstance(value, dict) and value.get("text"):
            lines.append(f"street address: {value['text']}")
    for claim in claims.get("P2555") or []:
        value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
        unit = str((value or {}).get("unit") or "").rsplit("/", 1)[-1]
        amount = str((value or {}).get("amount") or "").lstrip("+")
        if amount and unit in VND_QIDS:
            lines.append(f"fee: {amount} VND")
    if claims.get("P856"):
        lines.append("official website: listed")
    return "\n".join(lines)


async def fetch_wikidata_entities(
    client: httpx.AsyncClient, qids: Sequence[str]
) -> tuple[dict[str, dict[str, Any]], int]:
    """QID → entity (claims only); returns the entities and the number of requests made."""
    unique = sorted({q for q in qids if q and q.startswith("Q") and q[1:].isdigit()})
    entities: dict[str, dict[str, Any]] = {}
    requests = 0
    for start in range(0, len(unique), WIKIDATA_BATCH):
        batch = unique[start : start + WIKIDATA_BATCH]
        requests += 1
        try:
            response = await get_with_retries(
                client,
                WIKIDATA_API_URL,
                params={
                    "action": "wbgetentities",
                    "ids": "|".join(batch),
                    "props": "claims",
                    "format": "json",
                },
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("wikidata claims failed batch=%d error=%s", start, exc)
            continue
        entities.update({str(k): v for k, v in (body.get("entities") or {}).items()})
    return entities, requests


# ---- Extraction -----------------------------------------------------------------------------


@dataclass
class _Evidence:
    items: list[FactEvidenceItem] = field(default_factory=list)
    revisions: dict[str, uuid.UUID] = field(default_factory=dict)  # evidence id → revision
    urls: dict[str, str] = field(default_factory=dict)  # evidence id → URL

    def add(
        self,
        evidence_id: str,
        text_value: str,
        *,
        kind: str,
        revision: uuid.UUID | None = None,
        url: str | None = None,
    ) -> None:
        if (
            not text_value.strip()
            or evidence_id in self.revisions
            or any(item.evidence_id == evidence_id for item in self.items)
        ):
            return
        self.items.append(FactEvidenceItem(evidence_id, text_value, url, kind))
        if revision is not None:
            self.revisions[evidence_id] = revision
        if url:
            self.urls[evidence_id] = url


def search_query(candidate: FactCandidate) -> str:
    town = QUERY_TOWN.get(candidate.area_code or "", "Đà Nẵng")
    return f"{candidate.name_vi} {town} giờ mở cửa giá vé địa chỉ"


class FactExtractor:
    def __init__(
        self,
        *,
        ctx: AgentContext,
        fetcher: PageFetcher,
        search: TavilySearch,
        http: httpx.AsyncClient,
    ) -> None:
        self._ctx = ctx
        self._fetcher = fetcher
        self._search = search
        self._http = http
        self.tavily_exhausted = False

    async def _add_page(self, evidence: _Evidence, url: str, report: FactsReport) -> None:
        if _skipped_host(url):
            return
        page = await self._fetcher.fetch(url)
        if not page.ok or page.source_revision_id is None:
            return
        if _skipped_host(page.final_url or page.url):
            return
        report.pages_fetched += 1
        if page.source_revision_id in evidence.revisions.values():
            return
        evidence_id = f"web{sum(1 for i in evidence.items if i.evidence_id.startswith('web')) + 1}"
        evidence.add(
            evidence_id,
            page.text,
            kind="WEB",
            revision=page.source_revision_id,
            url=page.final_url or page.url,
        )

    async def gather(
        self,
        session: AsyncSession,
        candidate: FactCandidate,
        *,
        osm_tags: dict[str, dict[str, str]],
        entities: dict[str, dict[str, Any]],
        wikidata_source_id: uuid.UUID | None,
        report: FactsReport,
        max_searches: int,
    ) -> _Evidence:
        evidence = _Evidence()
        if candidate.osm_id and candidate.osm_revision:
            text_value = osm_evidence_text(osm_tags.get(candidate.osm_id, {}))
            evidence.add(
                "osm",
                text_value,
                kind="OSM",
                revision=candidate.osm_revision,
                url=f"https://www.openstreetmap.org/{candidate.osm_id}",
            )
        entity = entities.get(candidate.qid or "")
        if entity and wikidata_source_id is not None and candidate.qid:
            text_value = wikidata_evidence_text(entity)
            if text_value:
                revision = await get_or_create_revision(
                    session,
                    source_id=wikidata_source_id,
                    locator=ENTITY_URL.format(qid=candidate.qid),
                    content_sha256=sha256_hex(text_value),
                    title=candidate.qid,
                )
                evidence.add(
                    "wikidata",
                    text_value,
                    kind="WIKIDATA",
                    revision=revision.id,
                    url=ENTITY_URL.format(qid=candidate.qid),
                )
        for locale, url, summary, revision_id in candidate.wikipedia:
            evidence.add(f"wiki:{locale}", summary, kind="WIKIPEDIA", revision=revision_id, url=url)
        if candidate.unknown:
            if candidate.website:
                await self._add_page(evidence, candidate.website, report)
            if not self.tavily_exhausted and report.tavily_calls < max_searches:
                response = await self._search.search(search_query(candidate))
                if response.status is SearchStatus.QUOTA_EXCEEDED:
                    self.tavily_exhausted = True
                elif response.status is SearchStatus.CACHED:
                    report.tavily_cached += 1
                if response.provider_called:
                    report.tavily_calls += 1
                fetched = 0
                for hit in response.hits:
                    if fetched >= MAX_SEARCH_PAGES:
                        break
                    before = len(evidence.items)
                    await self._add_page(evidence, hit.url, report)
                    fetched += 1 if len(evidence.items) > before else 0
        for locale in candidate.short_missing:
            description = candidate.descriptions.get(locale)
            if description:
                evidence.add(f"desc:{locale}", description, kind="DESCRIPTION")
        return evidence

    async def run(
        self,
        session: AsyncSession,
        *,
        city_code: str,
        limit: int,
        max_searches: int,
        max_model_calls: int,
        retry: bool = False,
    ) -> FactsReport:
        report = FactsReport(provider_key=AI_FACTS_PROVIDER_KEY)
        policy = await require_active_policy(session, AI_FACTS_PROVIDER_KEY)
        candidates = (await load_fact_candidates(session, city_code=city_code, retry=retry))[:limit]
        report.selected = len(candidates)
        city = await load_city(session, city_code)
        source = await get_or_create_source(
            session,
            data_provider_id=policy.provider_id,
            publisher=FACTS_PUBLISHER,
            source_kind="REFERENCE",
            license_code=FACTS_LICENCE,
            attribution_text=FACTS_ATTRIBUTION,
        )
        wikidata_source = await session.scalar(
            text(
                "SELECT s.id FROM sources s JOIN data_providers d ON d.id = s.data_provider_id "
                "WHERE d.provider_key = 'wikidata' AND s.license_code = :licence "
                "ORDER BY s.created_at LIMIT 1"
            ),
            {"licence": WIKIDATA_LICENCE},
        )
        await session.commit()
        osm_ids = [c.osm_id for c in candidates if c.osm_id and c.unknown]
        osm_tags = await fetch_osm_tags(self._http, osm_ids) if osm_ids else {}
        report.overpass_requests = 1 if osm_ids else 0
        entities, requests = await fetch_wikidata_entities(
            self._http, [c.qid for c in candidates if c.qid and c.unknown]
        )
        report.wikimedia_requests += requests
        for candidate in candidates:
            used = sum(report.model_calls.values())
            if used >= max_model_calls:
                report.stopped = f"model call cap {max_model_calls} reached"
                break
            evidence = await self.gather(
                session,
                candidate,
                osm_tags=osm_tags,
                entities=entities,
                wikidata_source_id=wikidata_source,
                report=report,
                max_searches=max_searches,
            )
            if not evidence.items:
                report.no_facts += 1
                await self._stage(session, policy, city.id, source.id, candidate, None, evidence)
                continue
            first = len(self._ctx.attempts)
            outcome = await extract_place_facts(
                self._ctx,
                name_vi=candidate.name_vi,
                name_en=candidate.name_en,
                category=candidate.category,
                area=candidate.area_code,
                evidence=evidence.items,
            )
            model = ""
            for attempt in self._ctx.attempts[first:]:
                report.model_calls[attempt.provider_model] += 1
                model = attempt.provider_model
            report.issues.update(issue.split(":", 1)[0] for issue in outcome.issues)
            if outcome.extraction is None:
                report.failed += 1
                if outcome.exhausted:
                    report.stopped = "writer model chain exhausted (quota or provider errors)"
                    break
                continue
            staged = await self._stage(
                session,
                policy,
                city.id,
                source.id,
                candidate,
                outcome.extraction,
                evidence,
                model=model,
                report=report,
            )
            if staged:
                report.extracted_places += 1
            else:
                report.no_facts += 1
        if self.tavily_exhausted:
            report.stopped = (report.stopped + "; " if report.stopped else "") + (
                "Tavily quota exhausted"
            )
        logger.info(
            "enrich facts selected=%d extracted=%d no_facts=%d failed=%d",
            report.selected,
            report.extracted_places,
            report.no_facts,
            report.failed,
        )
        return report

    async def _stage(
        self,
        session: AsyncSession,
        policy: Any,
        city_id: uuid.UUID,
        source_id: uuid.UUID,
        candidate: FactCandidate,
        extraction: Any,
        evidence: _Evidence,
        *,
        model: str = "",
        report: FactsReport | None = None,
    ) -> bool:
        """One import run per place; True when something was staged as ACCEPTED."""
        facts: dict[str, dict[str, Any]] = {}
        fact_revisions: dict[str, str] = {}
        short: dict[str, str] = {}
        if extraction is not None:
            for fact in extraction.facts:
                revision = evidence.revisions.get(fact.evidence_id)
                if fact.field_code not in candidate.unknown or revision is None:
                    continue  # already known, or cites a description (no source revision)
                facts[fact.field_code] = {
                    "value": fact.value,
                    "grounding": fact.grounding,
                    "quote": fact.quote[:300],
                    "source_url": evidence.urls.get(fact.evidence_id),
                }
                fact_revisions[fact.field_code] = str(revision)
                if report is not None:
                    report.by_field[fact.field_code] += 1
                    report.by_grounding[fact.grounding] += 1
            for locale, (text_value, evidence_id) in extraction.short_description.items():
                if locale in candidate.short_missing and evidence_id == f"desc:{locale}":
                    short[locale] = text_value
                    if report is not None:
                        report.by_field[f"SHORT_DESCRIPTION_{locale.upper()}"] += 1
        now = datetime.now(UTC)
        run = await start_run(
            session,
            policy,
            city_id,
            release_id=f"facts-{candidate.place_id}-{now.strftime('%Y%m%dT%H%M%SZ')}",
            checksum=sha256_hex(f"{candidate.place_id}:{now.isoformat()}:{uuid.uuid4()}"),
            importer_version=IMPORTER_VERSION,
        )
        assert run is not None
        place_report = RunReport(provider_key=AI_FACTS_PROVIDER_KEY, record_count=1)
        point = await session.scalar(
            text(
                "SELECT ST_X(location::geometry) || ' ' || ST_Y(location::geometry) "
                "FROM places WHERE id = :id"
            ),
            {"id": candidate.place_id},
        )
        lng, lat = (float(part) for part in str(point).split())
        if not facts and not short:
            place_report.reject(NO_FACTS)
            add_record(
                session,
                run,
                upstream_id=f"ai-facts:{candidate.place_id}",
                raw_name=candidate.name_vi,
                upstream_category=None,
                lng=lng,
                lat=lat,
                payload={},
                rejection_reason=NO_FACTS,
                place_id=candidate.place_id,
            )
        else:
            payload = policy.filter_payload(
                {"facts": facts, "short_description": short, "model": model}
            )
            facts_revision = await get_or_create_revision(
                session,
                source_id=source_id,
                locator=f"gonarra:ai-facts:{candidate.place_id}",
                content_sha256=sha256_hex(canonical_json(payload)),
                title=f"AI-extracted facts: {candidate.slug}",
            )
            payload[PROVENANCE_KEY] = {
                "source_revision_id": str(facts_revision.id),
                "fact_source_revision_ids": fact_revisions,
            }
            add_record(
                session,
                run,
                upstream_id=f"ai-facts:{candidate.place_id}",
                raw_name=candidate.name_vi,
                upstream_category=None,
                lng=lng,
                lat=lat,
                payload=payload,
                place_id=candidate.place_id,
                match_state="MATCHED",
            )
            place_report.accepted = 1
        finish_run(run, place_report)
        await session.commit()
        return place_report.accepted == 1


def build_fact_extractor(
    settings: Settings, session_factory: SessionFactory
) -> tuple[FactExtractor, Any]:
    """Wire the production adapters; returns the extractor and an async closer."""
    ledger = QuotaLedger(session_factory, settings)
    store = SqlResearchStore(session_factory, allow_draft_policies=False)
    fetcher = PageFetcher(store=store)
    key = settings.tavily_api_key.get_secret_value() if settings.tavily_api_key else None
    search = TavilySearch(api_key=key, ledger=ledger, store=store)
    ctx = AgentContext(
        settings=settings,
        ledger=ledger,
        session_factory=session_factory,
        purpose=Purpose.CONTENT_SUMMARY,
    )
    http = httpx.AsyncClient(timeout=90.0, headers={"User-Agent": USER_AGENT})
    extractor = FactExtractor(ctx=ctx, fetcher=fetcher, search=search, http=http)

    async def close() -> None:
        await fetcher.aclose()
        await http.aclose()

    return extractor, close
