"""Wikipedia summaries (DEC-022): VI/EN lead extracts for places with a Wikidata sitelink.

Uses the REST summary endpoint (``/api/rest_v1/page/summary/{title}``). The extract becomes the
place description and the Guide OVERVIEW chunk of that locale. Wikipedia text is CC BY-SA 4.0:
each page is recorded as a ``source_revisions`` row (locator = page URL, retrieved_at,
content_sha256 of the extract) under the source "Wikipedia (vi|en)" with the attribution text.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import parse_point
from app.ingestion.common import (
    PROVENANCE_KEY,
    USER_AGENT,
    RunReport,
    add_record,
    canonical_json,
    finish_run,
    get_or_create_revision,
    get_or_create_source,
    link_identity,
    load_city,
    provider_id_for,
    require_active_policy,
    sha256_hex,
    start_run,
)
from app.ingestion.wikidata import PROVIDER_KEY as WIKIDATA_KEY
from app.ingestion.wikidata import get_with_retries
from app.models.catalog import Place
from app.models.providers import ImportRecord, ImportRun

logger = logging.getLogger("gonarra.ingestion")

PROVIDER_KEY = "wikipedia"
IMPORTER_VERSION = "wikipedia-2"  # 2: records the article's own wikibase_item
RELEASE_ID = "rest-v1-summary"
SUMMARY_URL = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
LICENSE_CODE = "CC-BY-SA-4.0"
ATTRIBUTION = "Text from Wikipedia ({lang}), by Wikipedia contributors, licensed CC BY-SA 4.0"
REQUEST_DELAY_S = 0.2
MAX_EXTRACT_CHARS = 3500


@dataclass(frozen=True)
class PageRequest:
    place_id: uuid.UUID
    locale: str
    title: str


@dataclass(frozen=True)
class PageSummary:
    place_id: uuid.UUID
    locale: str
    title: str
    page_url: str
    summary: str
    revision: str | None
    # The article's own Wikidata item (DEC-031): an extract describes the place only when this
    # equals the place's QID (a sitelink may redirect to an article about another subject).
    wikibase_item: str | None = None

    @property
    def upstream_id(self) -> str:
        return f"{self.locale}:{self.title}"

    def payload(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "page_url": self.page_url,
            "summary": self.summary,
            "wikibase_item": self.wikibase_item,
        }


def trim_extract(text: str, limit: int = MAX_EXTRACT_CHARS) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind(". "))
    return cut[: end + 1] if end > limit // 2 else cut.rstrip() + "…"


def parse_summary(request: PageRequest, body: dict[str, Any]) -> PageSummary | None:
    if body.get("type") not in (None, "standard"):
        return None  # disambiguation pages and the like carry no usable description
    extract = trim_extract(str(body.get("extract") or ""))
    if not extract:
        return None
    page_url = ((body.get("content_urls") or {}).get("desktop") or {}).get(
        "page"
    ) or f"https://{request.locale}.wikipedia.org/wiki/{quote(request.title.replace(' ', '_'))}"
    revision = body.get("revision")
    return PageSummary(
        place_id=request.place_id,
        locale=request.locale,
        title=str(body.get("title") or request.title),
        page_url=str(page_url),
        summary=extract,
        revision=str(revision) if revision is not None else None,
        wikibase_item=str(body["wikibase_item"]) if body.get("wikibase_item") else None,
    )


async def sitelink_requests(session: AsyncSession, city_id: uuid.UUID) -> list[PageRequest]:
    """VI/EN titles from each place's latest accepted Wikidata record."""
    provider_id = await provider_id_for(session, WIKIDATA_KEY)
    if provider_id is None:
        return []
    rows = (
        await session.execute(
            select(ImportRecord.place_id, ImportRecord.allowed_payload)
            .join(ImportRun, ImportRun.id == ImportRecord.import_run_id)
            .join(Place, Place.id == ImportRecord.place_id)
            .where(
                ImportRun.data_provider_id == provider_id,
                ImportRun.status == "SUCCEEDED",
                ImportRecord.validation_status == "ACCEPTED",
                Place.city_id == city_id,
            )
            .order_by(ImportRecord.place_id, ImportRun.started_at.desc())
            .distinct(ImportRecord.place_id)
        )
    ).all()
    requests: list[PageRequest] = []
    for row in rows:
        place_id: uuid.UUID | None = row[0]
        payload: dict[str, Any] = dict(row[1] or {})
        sitelinks = payload.get("sitelinks") or {}
        for locale in ("vi", "en"):
            title = sitelinks.get(locale)
            if place_id is not None and title:
                requests.append(PageRequest(place_id=place_id, locale=locale, title=str(title)))
    return requests


async def fetch_summaries(
    client: httpx.AsyncClient, requests: Sequence[PageRequest], *, delay_s: float = REQUEST_DELAY_S
) -> list[PageSummary]:
    summaries: list[PageSummary] = []
    for index, request in enumerate(requests):
        if index and delay_s:
            await asyncio.sleep(delay_s)
        url = SUMMARY_URL.format(
            lang=request.locale, title=quote(request.title.replace(" ", "_"), safe="")
        )
        try:
            response = await get_with_retries(
                client, url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
            )
        except httpx.HTTPError as exc:
            logger.warning("wikipedia summary failed locale=%s error=%s", request.locale, exc)
            continue
        if response.status_code != 200:
            continue
        summary = parse_summary(request, response.json())
        if summary is not None:
            summaries.append(summary)
    return summaries


async def import_wikipedia(
    session: AsyncSession, *, city_code: str, client: httpx.AsyncClient | None = None
) -> RunReport:
    await require_active_policy(session, PROVIDER_KEY)  # refuse before any network call
    city = await load_city(session, city_code)
    requests = await sitelink_requests(session, city.id)
    own_client = client is None
    http = client or httpx.AsyncClient(
        timeout=30.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    )
    try:
        summaries = await fetch_summaries(http, requests)
    finally:
        if own_client:
            await http.aclose()
    return await stage_summaries(session, city_code=city_code, summaries=summaries)


async def stage_summaries(
    session: AsyncSession, *, city_code: str, summaries: Sequence[PageSummary]
) -> RunReport:
    policy = await require_active_policy(session, PROVIDER_KEY)
    city = await load_city(session, city_code)
    report = RunReport(provider_key=PROVIDER_KEY)
    ordered = sorted(summaries, key=lambda s: (str(s.place_id), s.locale))
    checksum = sha256_hex(
        canonical_json([[str(s.place_id), s.upstream_id, s.payload()] for s in ordered])
    )
    run = await start_run(
        session,
        policy,
        city.id,
        release_id=RELEASE_ID,
        checksum=checksum,
        importer_version=IMPORTER_VERSION,
    )
    if run is None:
        report.skipped_unchanged = True
        return report
    report.import_run_id = run.id
    sources = {
        locale: await get_or_create_source(
            session,
            data_provider_id=policy.provider_id,
            publisher=f"Wikipedia ({locale})",
            source_kind="REFERENCE",
            license_code=LICENSE_CODE,
            attribution_text=ATTRIBUTION.format(lang=locale),
            homepage_url=f"https://{locale}.wikipedia.org/",
        )
        for locale in ("vi", "en")
    }
    for summary in ordered:
        place = await session.get(Place, summary.place_id)
        if place is None:
            continue
        report.record_count += 1
        payload = policy.filter_payload(summary.payload())
        title = (
            summary.title
            if summary.revision is None
            else (f"{summary.title} (revision {summary.revision})")
        )
        revision = await get_or_create_revision(
            session,
            source_id=sources[summary.locale].id,
            locator=summary.page_url,
            content_sha256=sha256_hex(summary.summary),
            title=title,
        )
        payload[PROVENANCE_KEY] = {
            "source_revision_id": str(revision.id),
            "locale": summary.locale,
        }
        await link_identity(
            session,
            place_id=place.id,
            provider_id=policy.provider_id,
            upstream_id=summary.upstream_id,
            release=summary.revision,
        )
        lng, lat = _point(place.location)
        add_record(
            session,
            run,
            upstream_id=summary.upstream_id,
            raw_name=summary.title,
            upstream_category=None,
            lng=lng,
            lat=lat,
            payload=payload,
            place_id=place.id,
            match_state="MATCHED",
        )
        report.accepted += 1
    finish_run(run, report)
    await session.commit()
    return report


def _point(ewkt: str) -> tuple[float, float]:
    point = parse_point(ewkt)
    if point is None:
        raise ValueError("place has no point location")
    return point.longitude, point.latitude
