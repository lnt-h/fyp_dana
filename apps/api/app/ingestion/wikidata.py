"""Wikidata importer (ADR-012, DEC-022): tourism-relevant items inside the city bounding box.

One SPARQL query (``wikibase:box`` over the seeded city boundary's envelope) returns every item
with coordinates, its ``P31`` classes, VI/EN labels, descriptions, aliases and VI/EN Wikipedia
sitelinks. Classes are mapped to Gonarra categories in code (``categories.py``); unmapped items
are skipped. Wikidata data is CC0; the item URL is recorded as a source revision.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.areas import assign_area, load_areas
from app.ingestion.categories import map_category
from app.ingestion.common import (
    PROVENANCE_KEY,
    USER_AGENT,
    RunReport,
    add_record,
    canonical_json,
    create_place,
    finish_run,
    free_slug,
    get_or_create_revision,
    get_or_create_source,
    inside_city,
    link_identity,
    load_city,
    place_for_identity,
    require_active_policy,
    sha256_hex,
    start_run,
)

logger = logging.getLogger("gonarra.ingestion")

PROVIDER_KEY = "wikidata"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
API_URL = "https://www.wikidata.org/w/api.php"
HUMAN_QID = "Q5"
ENTITY_BATCH = 50
IMPORTER_VERSION = "wikidata-1"
RELEASE_ID = "wdqs-live"
ENTITY_URL = "https://www.wikidata.org/wiki/{qid}"
LICENSE_CODE = "CC0-1.0"
SPARQL_TIMEOUT_S = 90.0
MAX_ATTEMPTS = 4

_POINT = re.compile(r"Point\(\s*(-?[0-9.eE+-]+)\s+(-?[0-9.eE+-]+)\s*\)")
_QID = re.compile(r"Q[0-9]+$")

SPARQL_TEMPLATE = """
SELECT ?item (SAMPLE(?c) AS ?coord) (SAMPLE(?lv) AS ?labelVi) (SAMPLE(?le) AS ?labelEn)
  (SAMPLE(?dv) AS ?descVi) (SAMPLE(?de) AS ?descEn)
  (SAMPLE(?av) AS ?articleVi) (SAMPLE(?ae) AS ?articleEn)
  (GROUP_CONCAT(DISTINCT ?cl; separator="|") AS ?classLabels)
  (GROUP_CONCAT(DISTINCT ?aliasVi; separator="|") AS ?aliasesVi)
  (GROUP_CONCAT(DISTINCT ?aliasEn; separator="|") AS ?aliasesEn)
  (GROUP_CONCAT(DISTINCT ?img; separator="|") AS ?images)
WHERE {{
  SERVICE wikibase:box {{
    ?item wdt:P625 ?c .
    bd:serviceParam wikibase:cornerSouthWest "Point({min_lng} {min_lat})"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerNorthEast "Point({max_lng} {max_lat})"^^geo:wktLiteral .
  }}
  ?item wdt:P31 ?class .
  OPTIONAL {{ ?class rdfs:label ?cl FILTER(LANG(?cl) = "en") }}
  OPTIONAL {{ ?item rdfs:label ?lv FILTER(LANG(?lv) = "vi") }}
  OPTIONAL {{ ?item rdfs:label ?le FILTER(LANG(?le) = "en") }}
  OPTIONAL {{ ?item schema:description ?dv FILTER(LANG(?dv) = "vi") }}
  OPTIONAL {{ ?item schema:description ?de FILTER(LANG(?de) = "en") }}
  OPTIONAL {{ ?item skos:altLabel ?aliasVi FILTER(LANG(?aliasVi) = "vi") }}
  OPTIONAL {{ ?item skos:altLabel ?aliasEn FILTER(LANG(?aliasEn) = "en") }}
  OPTIONAL {{ ?av schema:about ?item ; schema:isPartOf <https://vi.wikipedia.org/> }}
  OPTIONAL {{ ?ae schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }}
  OPTIONAL {{ ?item wdt:P18 ?img }}
}}
GROUP BY ?item
"""


@dataclass(frozen=True)
class WikidataItem:
    qid: str
    lng: float
    lat: float
    labels: dict[str, str]
    descriptions: dict[str, str]
    aliases: dict[str, list[str]]
    sitelinks: dict[str, str]  # locale -> Wikipedia page title
    class_labels: tuple[str, ...]
    category: str | None = None
    # Wikimedia Commons file names from P18 ("File:" prefix stripped), sorted; see commons.py.
    images: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        """Provider fields as named in the policy's field rules (filtered before storage)."""
        return {
            "id": self.qid,
            "name": self.labels,
            "location": {"lat": self.lat, "lng": self.lng},
            "category": self.category,
            "description": self.descriptions,
            "aliases": self.aliases,
            "sitelinks": self.sitelinks,
            "image": list(self.images),
        }


@dataclass
class WikidataReport(RunReport):
    unmapped: int = 0
    by_category: dict[str, int] = field(default_factory=dict)


def build_query(bbox: tuple[float, float, float, float]) -> str:
    min_lng, min_lat, max_lng, max_lat = bbox
    return SPARQL_TEMPLATE.format(
        min_lng=min_lng, min_lat=min_lat, max_lng=max_lng, max_lat=max_lat
    )


def _value(binding: dict[str, Any], key: str) -> str | None:
    cell = binding.get(key)
    if not cell:
        return None
    value = str(cell.get("value", "")).strip()
    return value or None


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return sorted({part.strip() for part in value.split("|") if part.strip()})


def _title_from_article(url: str | None) -> str | None:
    if not url:
        return None
    return unquote(url.rsplit("/wiki/", 1)[-1]).replace("_", " ") or None


def _commons_file(value: str) -> str | None:
    """``http://commons.wikimedia.org/wiki/Special:FilePath/A%20b.jpg`` → ``A b.jpg``."""
    name = unquote(value.rsplit("/", 1)[-1]).replace("_", " ").strip()
    return name or None


def parse_bindings(bindings: Sequence[dict[str, Any]]) -> list[WikidataItem]:
    """SPARQL JSON bindings → items with a mapped category (unmapped ones are dropped)."""
    items: dict[str, WikidataItem] = {}
    for binding in bindings:
        uri = _value(binding, "item") or ""
        qid = uri.rsplit("/", 1)[-1]
        coord = _POINT.search(_value(binding, "coord") or "")
        if not _QID.match(qid) or coord is None:
            continue
        class_labels = tuple(_split(_value(binding, "classLabels")))
        labels = {
            locale: label
            for locale, label in (
                ("vi", _value(binding, "labelVi")),
                ("en", _value(binding, "labelEn")),
            )
            if label
        }
        descriptions = {
            locale: text
            for locale, text in (
                ("vi", _value(binding, "descVi")),
                ("en", _value(binding, "descEn")),
            )
            if text
        }
        sitelinks = {
            locale: title
            for locale, title in (
                ("vi", _title_from_article(_value(binding, "articleVi"))),
                ("en", _title_from_article(_value(binding, "articleEn"))),
            )
            if title
        }
        aliases = {
            locale: values
            for locale, values in (
                ("vi", _split(_value(binding, "aliasesVi"))),
                ("en", _split(_value(binding, "aliasesEn"))),
            )
            if values
        }
        items[qid] = WikidataItem(
            qid=qid,
            lng=round(float(coord.group(1)), 7),
            lat=round(float(coord.group(2)), 7),
            labels=labels,
            descriptions=descriptions,
            aliases=aliases,
            sitelinks=sitelinks,
            class_labels=class_labels,
            category=map_category(class_labels),
            images=tuple(
                sorted(
                    {
                        name
                        for name in (_commons_file(v) for v in _split(_value(binding, "images")))
                        if name
                    }
                )
            ),
        )
    return [items[qid] for qid in sorted(items, key=lambda q: int(q[1:]))]


async def get_with_retries(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    max_attempts: int = MAX_ATTEMPTS,
    backoff_s: float = 2.0,
) -> httpx.Response:
    """GET with polite retries on 429/5xx and transport errors (honours Retry-After)."""
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = await client.get(url, params=params, headers=headers)
        except httpx.TransportError as exc:
            last_error = exc
        else:
            if response.status_code < 500 and response.status_code != 429:
                return response
            last_error = httpx.HTTPStatusError(
                f"HTTP {response.status_code}", request=response.request, response=response
            )
            retry_after = response.headers.get("retry-after", "")
            if retry_after.isdigit():
                await asyncio.sleep(min(float(retry_after), 60.0))
                continue
        if attempt < max_attempts:
            await asyncio.sleep(backoff_s * attempt)
    assert last_error is not None
    raise last_error


async def fetch_items(
    client: httpx.AsyncClient, bbox: tuple[float, float, float, float]
) -> list[WikidataItem]:
    response = await get_with_retries(
        client,
        SPARQL_ENDPOINT,
        params={"query": build_query(bbox), "format": "json"},
        headers={"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return parse_bindings(response.json()["results"]["bindings"])


def human_qids_from(body: dict[str, Any]) -> set[str]:
    """``wbgetentities`` (props=claims) response → QIDs whose P31 includes Q5 (human)."""
    humans: set[str] = set()
    for qid, entity in (body.get("entities") or {}).items():
        for claim in ((entity or {}).get("claims") or {}).get("P31") or []:
            value = (((claim or {}).get("mainsnak") or {}).get("datavalue") or {}).get("value")
            if isinstance(value, dict) and value.get("id") == HUMAN_QID:
                humans.add(str(qid))
    return humans


async def fetch_human_qids(
    client: httpx.AsyncClient, qids: Sequence[str], *, batch_size: int = ENTITY_BATCH
) -> set[str]:
    """Which of ``qids`` are humans (P31=Q5); one ``wbgetentities`` request per 50 QIDs.
    A failed batch is logged and treated as "not known to be human"."""
    unique = sorted({q for q in qids if _QID.match(q)}, key=lambda q: int(q[1:]))
    humans: set[str] = set()
    for start in range(0, len(unique), batch_size):
        batch = unique[start : start + batch_size]
        params = {
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "claims",
            "format": "json",
        }
        try:
            response = await get_with_retries(
                client, API_URL, params=params, headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("wikidata wbgetentities failed batch=%d error=%s", start, exc)
            continue
        if "error" in body:
            logger.warning("wikidata wbgetentities error batch=%d", start)
            continue
        humans |= human_qids_from(body)
    return humans


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=SPARQL_TIMEOUT_S, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    )


async def import_wikidata(
    session: AsyncSession,
    *,
    city_code: str,
    client: httpx.AsyncClient | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> WikidataReport:
    """Fetch and stage Wikidata items as DRAFT (IMPORTED) places. Commits once at the end."""
    await require_active_policy(session, PROVIDER_KEY)  # refuse before any network call
    city = await load_city(session, city_code)
    box = bbox or city.bbox
    if box is None:
        raise ValueError(f"city {city_code} has no boundary to query inside")
    own_client = client is None
    http = client or make_client()
    try:
        all_items = await fetch_items(http, box)
    finally:
        if own_client:
            await http.aclose()
    return await stage_items(session, city_code=city_code, items=all_items, policy_key=PROVIDER_KEY)


async def stage_items(
    session: AsyncSession, *, city_code: str, items: Sequence[WikidataItem], policy_key: str
) -> WikidataReport:
    policy = await require_active_policy(session, policy_key)
    city = await load_city(session, city_code)
    areas = load_areas(city_code)
    report = WikidataReport(provider_key=policy_key)
    mapped = [item for item in items if item.category is not None]
    report.unmapped = len(items) - len(mapped)
    checksum = sha256_hex(canonical_json([item.payload() for item in mapped]))
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
    source = await get_or_create_source(
        session,
        data_provider_id=policy.provider_id,
        publisher="Wikidata",
        source_kind="OPEN_DATA",
        license_code=LICENSE_CODE,
        attribution_text=policy.attribution_text or "Wikidata (CC0)",
        homepage_url="https://www.wikidata.org/",
    )
    for item in mapped:
        report.record_count += 1
        payload = policy.filter_payload(item.payload())
        name = item.labels.get("en") or item.labels.get("vi") or ""
        reason: str | None = None
        if not item.labels:
            reason = "NO_LABEL"
        elif not await inside_city(session, city.id, item.lng, item.lat):
            reason = "OUTSIDE_CITY"
        if reason is not None:
            report.reject(reason)
            add_record(
                session,
                run,
                upstream_id=item.qid,
                raw_name=name,
                upstream_category=item.category,
                lng=item.lng,
                lat=item.lat,
                payload=payload,
                rejection_reason=reason,
            )
            continue
        place_id = await place_for_identity(session, policy.provider_id, item.qid)
        match_state = "MATCHED"
        if place_id is None:
            place = await create_place(
                session,
                city_id=city.id,
                slug=await free_slug(session, city.id, name),
                lng=item.lng,
                lat=item.lat,
                category_code=item.category,
                area_code=assign_area(areas, item.lng, item.lat),
            )
            place_id = place.id
            match_state = "NEW_CANDIDATE"
            report.created_places += 1
        await link_identity(
            session,
            place_id=place_id,
            provider_id=policy.provider_id,
            upstream_id=item.qid,
            release=RELEASE_ID,
        )
        revision = await get_or_create_revision(
            session,
            source_id=source.id,
            locator=ENTITY_URL.format(qid=item.qid),
            content_sha256=sha256_hex(canonical_json(payload)),
            title=name,
        )
        payload[PROVENANCE_KEY] = {"source_revision_id": str(revision.id)}
        add_record(
            session,
            run,
            upstream_id=item.qid,
            raw_name=name,
            upstream_category=item.category,
            lng=item.lng,
            lat=item.lat,
            payload=payload,
            place_id=place_id,
            match_state=match_state,
        )
        report.accepted += 1
        assert item.category is not None
        report.by_category[item.category] = report.by_category.get(item.category, 0) + 1
    finish_run(run, report)
    await session.commit()
    logger.info(
        "wikidata import accepted=%d rejected=%d unmapped=%d",
        report.accepted,
        report.rejected,
        report.unmapped,
    )
    return report
