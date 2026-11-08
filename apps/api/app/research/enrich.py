"""Grounded AI place descriptions (owner decision 2026-11-08, D3): ``enrich descriptions``.

Offline, operator-run. For a prioritised set of draft places that lack a sourced description
in at least one locale it

1. gathers source text: the place's Wikipedia extracts (already staged), its official website
   from OpenStreetMap (fetched by :class:`PageFetcher`: SSRF guard, robots.txt, trafilatura),
   else a Tavily search for the place name in Đà Nẵng / Hội An and up to two result pages.
   Every fetched page is a ``source_revisions`` row (provenance); search snippets alone are
   never used as a source;
2. calls the ``grounded_writer`` DESCRIPTION profile (Gemini Flash-Lite → Groq) and validates
   the draft (:func:`app.agents.validators.validate_description`): cited URLs ⊆ supplied URLs,
   no prices / hours / phone numbers / ratings, numbers must occur in the sources;
3. stages a valid draft as an import record of provider ``gonarra_ai_summary`` with its own
   source revision (publisher "Gonarra", AI-summary licence) and the cited revisions in the
   provenance; the gate (``publish auto``) then uses it as the description of a locale that has
   no Wikipedia or sheet description, labelled ``translation_origin = 'AI_SUMMARY'``.

``insufficient_evidence`` stores no description: only a REJECTED marker record, so a re-run does
not spend budget on the same place again (``--retry-insufficient`` overrides).

Budget: Tavily ≈ 1 000 searches / month on the free tier, so at most ``limit`` places (default
150) are processed, in priority order (:func:`prioritise`), FOOD + CAFE capped at 40. Every
provider call goes through the quota ledger; the run stops gracefully when the writer chain or
Tavily is exhausted and reports what it did. Places already enriched are skipped (idempotent).
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runtime import AgentContext
from app.agents.schemas import DescriptionSource, PlaceDescription
from app.agents.validators import normalise_url
from app.agents.writer import write_place_description
from app.ai.invocations import Purpose
from app.ai.quota import QuotaLedger, SessionFactory
from app.config import Settings
from app.curation.auto_publish import (
    AI_SUMMARY_PROVIDER_KEY,
    LOCALES,
    Contributions,
    compose,
    gather,
)
from app.curation.common import parse_point
from app.ingestion.areas import hoi_an_area_codes, load_areas
from app.ingestion.common import (
    PROVENANCE_KEY,
    ActivePolicy,
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
from app.models.catalog import Place
from app.models.providers import DataProvider, ImportRecord, ImportRun
from app.models.reference import Category
from app.research.fetch import PageFetcher
from app.research.store import SqlResearchStore
from app.research.tavily import SearchStatus, TavilySearch

logger = logging.getLogger("gonarra.research")

IMPORTER_VERSION = "enrich-1"
DEFAULT_LIMIT = 150
FOOD_CAFE_CAP = 40
MIN_SOURCE_CHARS = 400  # below this, a web search is added
MAX_SEARCH_PAGES = 2
STOP_AFTER_EXHAUSTED = 3  # consecutive writer-chain exhaustions → stop
INSUFFICIENT = "INSUFFICIENT_EVIDENCE"

SUMMARY_PUBLISHER = "Gonarra"
SUMMARY_LICENCE = "GONARRA-AI-SUMMARY"
SUMMARY_ATTRIBUTION = (
    "Short description written by Gonarra with AI assistance, only from the cited sources"
)

TOURISM_CATEGORIES = frozenset(
    {
        "HERITAGE",
        "MUSEUM",
        "RELIGIOUS_SITE",
        "VIEWPOINT",
        "BEACH",
        "NATURE",
        "THEME_PARK",
        "CRAFT_VILLAGE",
    }
)
FOOD_CAFE = frozenset({"FOOD", "CAFE"})
EATING_CATEGORIES = frozenset({"FOOD", "CAFE", "MARKET"})
# Search results from these hosts are not used as description sources (social posts, booking
# and review aggregators: little descriptive text, mostly prices and ratings).
SKIPPED_HOSTS: tuple[str, ...] = (
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com",
    "booking.com",
    "agoda.com",
    "traveloka.com",
    "tripadvisor.",
    "foody.vn",
    "google.",
    "klook.com",
    "expedia.",
)


# ---- Candidates and priority --------------------------------------------------------------


@dataclass(frozen=True)
class EnrichCandidate:
    place_id: uuid.UUID
    slug: str
    category: str | None
    area_code: str | None
    name_vi: str
    name_en: str | None
    hoi_an: bool
    wikidata: bool  # has a Wikidata record
    osm_signal: bool  # OSM element tagged wikidata / website / opening_hours
    website: str | None
    has_hours: bool
    wikipedia: tuple[DescriptionSource, ...] = ()
    wikipedia_revisions: tuple[uuid.UUID, ...] = ()

    @property
    def tier(self) -> int | None:
        """1 = Wikidata place in an area; 2 = OSM place with signal tags or a tourism category;
        3 = FOOD/CAFE/MARKET with a website or hours and an EN name or in the Hội An area;
        None = not enriched."""
        if self.area_code is None:
            return None
        if self.wikidata and self.category not in EATING_CATEGORIES:
            return 1
        if self.category in EATING_CATEGORIES:
            if (self.website or self.has_hours) and (self.name_en or self.hoi_an):
                return 3
            return None
        if self.osm_signal or self.category in TOURISM_CATEGORIES:
            return 2
        return None


def prioritise(
    candidates: Sequence[EnrichCandidate], *, limit: int, food_cafe_cap: int = FOOD_CAFE_CAP
) -> list[EnrichCandidate]:
    """At most ``limit`` candidates in priority order, FOOD + CAFE capped at ``food_cafe_cap``.

    Order: tier; then Hội An area first (release gate ≥ 30); then places with a Wikipedia
    extract or a website (cheapest evidence, no search); then non-religious tourism categories
    before small shrines; then slug (deterministic).
    """

    def key(item: EnrichCandidate) -> tuple[int, int, int, int, str]:
        return (
            item.tier or 9,
            0 if item.hoi_an else 1,
            0 if (item.wikipedia or item.website) else 1,
            0 if item.category not in ("RELIGIOUS_SITE", "NATURE") else 1,
            item.slug,
        )

    chosen: list[EnrichCandidate] = []
    food_cafe = 0
    for item in sorted((c for c in candidates if c.tier is not None), key=key):
        if len(chosen) >= limit:
            break
        if item.category in FOOD_CAFE:
            if food_cafe >= food_cafe_cap:
                continue
            food_cafe += 1
        chosen.append(item)
    return chosen


def needs_description(contributions: Contributions) -> bool:
    """True when some locale has neither a Wikipedia extract nor a sheet description."""
    for locale in LOCALES:
        wiki = contributions.wikipedia.get(locale) or {}
        sheet_desc = ((contributions.sheet or {}).get("description") or {}).get(locale)
        if not (str(wiki.get("summary") or "").strip() or str(sheet_desc or "").strip()):
            return True
    return False


def _https(url: str | None) -> str | None:
    if not url:
        return None
    value = url.strip().split(";", 1)[0].strip()
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    parts = urlsplit(value)
    if not parts.hostname:
        return None
    return urlunsplit(("https", parts.netloc, parts.path or "/", parts.query, ""))


def _skipped_host(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(marker in host for marker in SKIPPED_HOSTS)


async def load_candidates(
    session: AsyncSession, *, city_code: str, place_ids: Sequence[uuid.UUID] | None = None
) -> list[EnrichCandidate]:
    """Draft places that need a description, with what is already known about them."""
    city = await load_city(session, city_code)
    areas = load_areas(city_code)
    hoi_an = hoi_an_area_codes(areas)
    categories = set((await session.scalars(select(Category.code))).all())
    enriched = await _already_enriched(session)
    statement = select(Place).where(
        Place.city_id == city.id, Place.workflow_state.not_in(("RETIRED", "PUBLISHED"))
    )
    if place_ids is not None:
        statement = statement.where(Place.id.in_(list(place_ids)))
    places = (await session.scalars(statement.order_by(Place.slug))).all()
    result: list[EnrichCandidate] = []
    for place in places:
        if place.id in enriched:
            continue
        contributions = await gather(session, place)
        if not needs_description(contributions):
            continue
        desired = compose(
            place, contributions, area_codes=areas, categories=categories, fact_fields=()
        )
        name_vi = desired.localizations["vi"].name
        if not name_vi:
            continue
        en = desired.localizations["en"]
        osm = contributions.osm or {}
        wiki_sources: list[DescriptionSource] = []
        wiki_revisions: list[uuid.UUID] = []
        for locale in LOCALES:
            page = contributions.wikipedia.get(locale)
            revision = ((page or {}).get(PROVENANCE_KEY) or {}).get("source_revision_id")
            if page and page.get("summary") and page.get("page_url") and revision:
                wiki_sources.append(
                    DescriptionSource(
                        url=str(page["page_url"]),
                        title=str(page.get("title") or "") or None,
                        text=str(page["summary"]),
                        kind="WIKIPEDIA",
                    )
                )
                wiki_revisions.append(uuid.UUID(str(revision)))
        result.append(
            EnrichCandidate(
                place_id=place.id,
                slug=place.slug,
                category=desired.category_code,
                area_code=desired.area_code,
                name_vi=name_vi,
                name_en=None if en.name_is_source_fallback else en.name,
                hoi_an=desired.area_code in hoi_an,
                wikidata=contributions.wikidata is not None,
                osm_signal=bool(osm.get("wikidata") or osm.get("website") or osm.get("facts")),
                website=_https(osm.get("website")),
                has_hours=bool(osm.get("opening_hours")),
                wikipedia=tuple(wiki_sources),
                wikipedia_revisions=tuple(wiki_revisions),
            )
        )
    return result


async def _already_enriched(
    session: AsyncSession, *, include_insufficient: bool = True
) -> set[uuid.UUID]:
    statement = (
        select(ImportRecord.place_id)
        .join(ImportRun, ImportRun.id == ImportRecord.import_run_id)
        .join(DataProvider, DataProvider.id == ImportRun.data_provider_id)
        .where(
            DataProvider.provider_key == AI_SUMMARY_PROVIDER_KEY,
            ImportRun.status == "SUCCEEDED",
            ImportRecord.place_id.is_not(None),
        )
    )
    if not include_insufficient:
        statement = statement.where(ImportRecord.validation_status == "ACCEPTED")
    return {row for row in (await session.scalars(statement)).all() if row is not None}


# ---- Run ----------------------------------------------------------------------------------


@dataclass
class EnrichedSample:
    slug: str
    name_vi: str
    description_vi: str
    description_en: str
    cited_urls: tuple[str, ...]


@dataclass
class EnrichReport(RunReport):
    selected: int = 0
    enriched: int = 0
    insufficient: int = 0
    failed: int = 0
    no_sources: int = 0
    tavily_calls: int = 0
    tavily_cached: int = 0
    pages_fetched: int = 0
    model_calls: Counter[str] = field(default_factory=Counter)
    stopped: str | None = None
    issues: Counter[str] = field(default_factory=Counter)
    samples: list[EnrichedSample] = field(default_factory=list)
    hoi_an_enriched: int = 0


@dataclass(frozen=True)
class _Gathered:
    sources: tuple[DescriptionSource, ...]
    revisions: dict[str, uuid.UUID]  # normalised URL → source revision id


class Enricher:
    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: SessionFactory,
        ctx: AgentContext,
        fetcher: PageFetcher,
        search: TavilySearch,
    ) -> None:
        self._settings = settings
        self._sf = session_factory
        self._ctx = ctx
        self._fetcher = fetcher
        self._search = search
        self.tavily_exhausted = False

    async def gather_sources(self, candidate: EnrichCandidate, report: EnrichReport) -> _Gathered:
        sources: list[DescriptionSource] = list(candidate.wikipedia)
        revisions = {
            normalise_url(source.url): revision
            for source, revision in zip(
                candidate.wikipedia, candidate.wikipedia_revisions, strict=True
            )
        }

        async def add_page(url: str, kind: str) -> None:
            page = await self._fetcher.fetch(url)
            if not page.ok or page.source_revision_id is None:
                return
            report.pages_fetched += 1
            key = normalise_url(page.url)
            if key in revisions:
                return
            revisions[key] = page.source_revision_id
            sources.append(DescriptionSource(url=key, title=page.title, text=page.text, kind=kind))

        if candidate.website and not _skipped_host(candidate.website):
            await add_page(candidate.website, "OFFICIAL_SITE")
        if sum(len(s.text) for s in sources) < MIN_SOURCE_CHARS and not self.tavily_exhausted:
            town = "Hội An" if candidate.hoi_an else "Đà Nẵng"
            response = await self._search.search(f"{candidate.name_vi} {town}")
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
                if _skipped_host(hit.url) or normalise_url(hit.url) in revisions:
                    continue
                before = len(sources)
                await add_page(hit.url, "WEB_SEARCH")
                fetched += 1 if len(sources) > before else 0
        return _Gathered(tuple(sources), revisions)

    async def run(
        self,
        session: AsyncSession,
        *,
        city_code: str,
        limit: int,
        food_cafe_cap: int = FOOD_CAFE_CAP,
        retry_insufficient: bool = False,
        place_ids: Sequence[uuid.UUID] | None = None,
    ) -> EnrichReport:
        report = EnrichReport(provider_key=AI_SUMMARY_PROVIDER_KEY)
        policy = await require_active_policy(session, AI_SUMMARY_PROVIDER_KEY)
        candidates = await load_candidates(session, city_code=city_code, place_ids=place_ids)
        if retry_insufficient:
            accepted = await _already_enriched(session, include_insufficient=False)
            candidates = [c for c in candidates if c.place_id not in accepted]
        chosen = prioritise(candidates, limit=limit, food_cafe_cap=food_cafe_cap)
        report.selected = len(chosen)
        city = await load_city(session, city_code)
        now = datetime.now(UTC)
        run = await start_run(
            session,
            policy,
            city.id,
            release_id=f"enrich-{now.strftime('%Y%m%dT%H%M%SZ')}",
            checksum=sha256_hex(f"{now.isoformat()}:{uuid.uuid4()}"),
            importer_version=IMPORTER_VERSION,
        )
        assert run is not None
        report.import_run_id = run.id
        source = await get_or_create_source(
            session,
            data_provider_id=policy.provider_id,
            publisher=SUMMARY_PUBLISHER,
            source_kind="REFERENCE",
            license_code=SUMMARY_LICENCE,
            attribution_text=SUMMARY_ATTRIBUTION,
        )
        await session.commit()
        exhausted_in_row = 0
        try:
            for candidate in chosen:
                if exhausted_in_row >= STOP_AFTER_EXHAUSTED:
                    report.stopped = "writer model chain exhausted (quota or provider errors)"
                    break
                gathered = await self.gather_sources(candidate, report)
                if not gathered.sources:
                    report.no_sources += 1
                    await self._stage(session, run, policy, source.id, candidate, None, gathered)
                    continue
                first = len(self._ctx.attempts)
                outcome = await write_place_description(
                    self._ctx,
                    name_vi=candidate.name_vi,
                    name_en=candidate.name_en,
                    category=candidate.category,
                    area=candidate.area_code,
                    sources=gathered.sources,
                )
                for attempt in self._ctx.attempts[first:]:
                    report.model_calls[attempt.provider_model] += 1
                report.issues.update(issue.split(":", 1)[0] for issue in outcome.issues)
                if outcome.description is not None:
                    exhausted_in_row = 0
                    report.enriched += 1
                    report.hoi_an_enriched += 1 if candidate.hoi_an else 0
                    await self._stage(
                        session, run, policy, source.id, candidate, outcome.description, gathered
                    )
                    report.samples.append(
                        EnrichedSample(
                            slug=candidate.slug,
                            name_vi=candidate.name_vi,
                            description_vi=outcome.description.description_vi,
                            description_en=outcome.description.description_en,
                            cited_urls=outcome.description.cited_urls,
                        )
                    )
                elif outcome.insufficient_evidence:
                    exhausted_in_row = 0
                    report.insufficient += 1
                    await self._stage(session, run, policy, source.id, candidate, None, gathered)
                else:
                    report.failed += 1
                    exhausted_in_row = exhausted_in_row + 1 if outcome.exhausted else 0
                if self.tavily_exhausted and report.stopped is None:
                    logger.info("enrich tavily quota exhausted; continuing without search")
            if self.tavily_exhausted:
                report.stopped = (report.stopped + "; " if report.stopped else "") + (
                    "Tavily quota exhausted (places after that used Wikipedia/websites only)"
                )
        finally:
            run_row = await session.get(ImportRun, run.id)
            if run_row is not None:
                finish_run(run_row, report)
                await session.commit()
        return report

    async def _stage(
        self,
        session: AsyncSession,
        run: ImportRun,
        policy: ActivePolicy,
        source_id: uuid.UUID,
        candidate: EnrichCandidate,
        description: PlaceDescription | None,
        gathered: _Gathered,
    ) -> None:
        """One import record per processed place; a REJECTED marker when nothing is stored."""
        place = await session.get(Place, candidate.place_id)
        assert place is not None
        point = parse_point(place.location)
        lng, lat = (point.longitude, point.latitude) if point else (0.0, 0.0)
        if description is None:
            add_record(
                session,
                run,
                upstream_id=f"ai-summary:{place.id}",
                raw_name=candidate.name_vi,
                upstream_category=candidate.category,
                lng=lng,
                lat=lat,
                payload={"description": {}, "cited_urls": []},
                rejection_reason=INSUFFICIENT if gathered.sources else "NO_SOURCES",
                place_id=place.id,
                match_state="MATCHED",
            )
            await session.commit()
            return
        cited_revisions = [
            str(gathered.revisions[url])
            for url in description.cited_urls
            if normalise_url(url) in gathered.revisions
        ]
        content = {
            "vi": description.description_vi,
            "en": description.description_en,
            "cited_urls": list(description.cited_urls),
        }
        revision = await get_or_create_revision(
            session,
            source_id=source_id,
            locator=f"gonarra:ai-summary:{place.slug}",
            content_sha256=sha256_hex(canonical_json(content)),
            title=f"AI summary of {candidate.name_vi}"[:300],
        )
        attempts = [a for a in self._ctx.attempts if a.outcome == "OK"]
        payload = policy.filter_payload(
            {
                "description": {"vi": description.description_vi, "en": description.description_en},
                "cited_urls": list(description.cited_urls),
                "model": attempts[-1].provider_model if attempts else None,
            }
        )
        payload[PROVENANCE_KEY] = {
            "source_revision_id": str(revision.id),
            "cited_source_revision_ids": cited_revisions,
        }
        add_record(
            session,
            run,
            upstream_id=f"ai-summary:{place.id}",
            raw_name=candidate.name_vi,
            upstream_category=candidate.category,
            lng=lng,
            lat=lat,
            payload=payload,
            place_id=place.id,
            match_state="MATCHED",
        )
        await session.commit()


def build_enricher(settings: Settings, session_factory: SessionFactory) -> tuple[Enricher, Any]:
    """Wire the production adapters; returns the enricher and an async closer."""
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
    enricher = Enricher(
        settings=settings, session_factory=session_factory, ctx=ctx, fetcher=fetcher, search=search
    )
    return enricher, fetcher.aclose
