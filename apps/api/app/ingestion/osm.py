"""OpenStreetMap importer via Overpass (DEC-022, ADR-012): POIs, names and opening hours.

One Overpass query over the seeded city envelope returns named tourism, heritage, religious,
food, market, park and nature elements (``out center tags``). Tags are mapped to Gonarra
categories in code (``categories.map_osm_tags``); unmapped elements are skipped.

* ``opening_hours`` is converted to the OPENING_HOURS fact shape the owner sheet uses
  (``{"weekly": {...}, "text": raw}``) for the common subset of the OSM syntax only. Anything
  else (public holidays, sunrise, months, week numbers, overnight ranges, comments) gives no
  fact: the value stays UNKNOWN, never guessed.
* Dedupe: an element already linked to a place keeps that place; else an element tagged
  ``wikidata=Q…`` whose item is already a place enriches it; else a place with the same
  normalized name (diacritic-insensitive) within ``MATCH_RADIUS_M`` is enriched; otherwise a new
  DRAFT (IMPORTED) place is created, exactly like the Wikidata importer.
* OSM data is ODbL: every element is recorded as a source revision (locator = element URL) under
  the source "OpenStreetMap" with the attribution "© OpenStreetMap contributors".
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote, urlparse

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import normalize_search_text
from app.db.types import ewkt_point
from app.ingestion.areas import assign_area, load_areas
from app.ingestion.categories import map_osm_tags
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
    provider_id_for,
    require_active_policy,
    sha256_hex,
    start_run,
)
from app.ingestion.wikidata import PROVIDER_KEY as WIKIDATA_KEY
from app.ingestion.wikidata import get_with_retries
from app.models.catalog import Place
from app.models.providers import ImportRecord

logger = logging.getLogger("gonarra.ingestion")

PROVIDER_KEY = "openstreetmap"
IMPORTER_VERSION = "osm-1"
RELEASE_ID = "overpass-live"
LICENSE_CODE = "ODbL-1.0"
ATTRIBUTION = "© OpenStreetMap contributors"
ELEMENT_URL = "https://www.openstreetmap.org/{osm_type}/{osm_id}"
OVERPASS_ENDPOINTS: tuple[str, ...] = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
OVERPASS_TIMEOUT_S = 180
MATCH_RADIUS_M = 100.0

# Overpass selectors; every one also requires a name. Order is irrelevant (union).
SELECTORS: tuple[str, ...] = (
    '["tourism"~"^(attraction|museum|viewpoint|gallery|theme_park|zoo|aquarium)$"]',
    '["historic"]',
    '["amenity"="place_of_worship"]',
    '["amenity"~"^(restaurant|cafe|marketplace)$"]',
    '["leisure"~"^(park|beach_resort|water_park)$"]',
    '["natural"~"^(beach|peak|cave_entrance)$"]',
    '["shop"~"^(mall|marketplace)$"]',
)

_QID = re.compile(r"^Q[0-9]+$")


def build_query(bbox: tuple[float, float, float, float]) -> str:
    """Overpass QL over the envelope (south, west, north, east)."""
    min_lng, min_lat, max_lng, max_lat = bbox
    box = f"{min_lat},{min_lng},{max_lat},{max_lng}"
    body = "".join(f'nwr{selector}["name"]({box});' for selector in SELECTORS)
    return f"[out:json][timeout:{OVERPASS_TIMEOUT_S}];({body});out center tags;"


# ---- opening_hours ------------------------------------------------------------------------

_OSM_DAYS = {"mo": 1, "tu": 2, "we": 3, "th": 4, "fr": 5, "sa": 6, "su": 7}
_DAY = r"(?:Mo|Tu|We|Th|Fr|Sa|Su)"
_DAY_SELECTOR = re.compile(rf"^({_DAY}(?:-{_DAY})?(?:,{_DAY}(?:-{_DAY})?)*)(?: (.*))?$")
_TIME_RANGE = re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])-([01]?[0-9]|2[0-4]):([0-5][0-9])$")
_ALL_DAY = [["00:00", "24:00"]]


def _expand_days(selector: str) -> list[int]:
    days: list[int] = []
    for part in selector.split(","):
        ends = part.split("-")
        start = _OSM_DAYS[ends[0].lower()]
        end = _OSM_DAYS[ends[-1].lower()]
        span = range(start, end + 1) if start <= end else [*range(start, 8), *range(1, end + 1)]
        days.extend(day for day in span if day not in days)
    return days


def _time_ranges(text: str) -> list[list[str]] | None:
    ranges: list[list[str]] = []
    for item in text.split(","):
        match = _TIME_RANGE.match(item)
        if match is None:
            return None
        oh, om, ch, cm = match.groups()
        opens, closes = f"{int(oh):02d}:{om}", f"{int(ch):02d}:{cm}"
        if closes != "24:00" and (int(ch) == 24 or closes <= opens):
            return None  # overnight or empty interval: not representable in the weekly shape
        ranges.append([opens, closes])
    ranges.sort()
    for previous, current in zip(ranges, ranges[1:], strict=False):
        if current[0] < previous[1]:
            return None  # overlapping intervals
    return ranges


def parse_osm_opening_hours(raw: str) -> dict[str, Any] | None:
    """OSM ``opening_hours`` → ``{"weekly": {"1": [["08:00", "17:00"]], ...}, "text": raw}``.

    Supported: ``24/7``; rules separated by ``;``; day selectors ``Mo-Fr``, ``Sa,Su``,
    ``Mo-We,Fr``, wrapping ``Fr-Mo``; a rule without days applies to every day; several time
    ranges ``08:00-12:00,13:30-17:00``; ``off`` / ``closed``. A later rule replaces the days it
    names (OSM semantics). Days never named are absent (unknown), never assumed closed.
    Everything else returns None (UNKNOWN), including overnight ranges such as ``18:00-02:00``.
    """
    text = (raw or "").strip()
    if not text:
        return None
    weekly: dict[str, list[list[str]]] = {}
    for rule in text.split(";"):
        # Collapse spaces around separators: "Mo - Fr 08:00 - 17:00" == "Mo-Fr 08:00-17:00".
        rule = re.sub(r"\s*([-,])\s*", r"\1", " ".join(rule.split()))
        if not rule:
            continue
        match = _DAY_SELECTOR.match(rule)
        if match is not None:
            days = _expand_days(match.group(1))
            rest = (match.group(2) or "").strip()
            if not rest:
                return None  # "Mo-Fr" alone: unusual, not supported
        else:
            days, rest = list(range(1, 8)), rule
        lowered = rest.lower()
        if lowered in ("off", "closed"):
            ranges: list[list[str]] | None = []
        elif lowered == "24/7" and match is None:
            ranges = [list(item) for item in _ALL_DAY]
        else:
            ranges = _time_ranges(rest)
        if ranges is None:
            return None
        for day in days:
            weekly[str(day)] = [list(item) for item in ranges]
    if not weekly:
        return None
    return {"weekly": dict(sorted(weekly.items())), "text": text}


# ---- Elements -----------------------------------------------------------------------------


def commons_file_name(value: str | None) -> str | None:
    """A Commons file name from an OSM ``wikimedia_commons`` / ``image`` value, else None."""
    if not value:
        return None
    text = value.strip().split(";", 1)[0].strip()
    if text.startswith(("http://", "https://")):
        parsed = urlparse(text)
        path = unquote(parsed.path)
        if parsed.netloc == "commons.wikimedia.org" and "/wiki/" in path:
            text = path.split("/wiki/", 1)[1]
        elif parsed.netloc == "upload.wikimedia.org" and "/commons/" in path:
            parts = [part for part in path.split("/") if part]
            if "thumb" in parts:
                index = parts.index("thumb")
                text = parts[index + 3] if len(parts) > index + 3 else ""
            else:
                text = parts[-1]
            text = f"File:{text}" if text else ""
        else:
            return None
    for prefix in ("File:", "Image:"):
        if text.startswith(prefix):
            name = text[len(prefix) :].replace("_", " ").strip()
            return name or None
    return None


@dataclass(frozen=True)
class OsmElement:
    osm_type: str  # node | way | relation
    osm_id: int
    lng: float
    lat: float
    tags: Mapping[str, str]
    category: str | None

    @property
    def upstream_id(self) -> str:
        return f"{self.osm_type}/{self.osm_id}"

    @property
    def url(self) -> str:
        return ELEMENT_URL.format(osm_type=self.osm_type, osm_id=self.osm_id)

    @property
    def names(self) -> dict[str, str]:
        """``name:vi`` (else ``name``, the local name) and ``name:en``; never translated."""
        vi = (self.tags.get("name:vi") or self.tags.get("name") or "").strip()
        en = (self.tags.get("name:en") or "").strip()
        return {locale: value for locale, value in (("vi", vi), ("en", en)) if value}

    @property
    def wikidata_id(self) -> str | None:
        value = (self.tags.get("wikidata") or "").strip()
        return value if _QID.match(value) else None

    @property
    def opening_hours(self) -> dict[str, Any] | None:
        return parse_osm_opening_hours(self.tags.get("opening_hours") or "")

    def payload(self) -> dict[str, Any]:
        facts: dict[str, Any] = {}
        hours = self.opening_hours
        if hours is not None:
            facts["OPENING_HOURS"] = {"value": hours, "source_url": self.url}
        return {
            "id": self.upstream_id,
            "name": self.names,
            "location": {"lat": self.lat, "lng": self.lng},
            "category": self.category,
            "opening_hours": self.tags.get("opening_hours"),
            "facts": facts,
            "website": self.tags.get("website") or self.tags.get("contact:website"),
            "wikidata": self.wikidata_id,
            "image": self.tags.get("image"),
            "wikimedia_commons": self.tags.get("wikimedia_commons"),
        }


def parse_elements(elements: Sequence[Mapping[str, Any]]) -> list[OsmElement]:
    """Overpass JSON elements → named elements with a point (``center`` for ways/relations)."""
    parsed: dict[str, OsmElement] = {}
    for element in elements:
        osm_type = str(element.get("type") or "")
        if osm_type not in ("node", "way", "relation"):
            continue
        tags = {str(k): str(v) for k, v in (element.get("tags") or {}).items()}
        if not (tags.get("name") or "").strip():
            continue
        point = element if osm_type == "node" else element.get("center") or {}
        if point.get("lat") is None or point.get("lon") is None:
            continue
        item = OsmElement(
            osm_type=osm_type,
            osm_id=int(element["id"]),
            lng=round(float(point["lon"]), 7),
            lat=round(float(point["lat"]), 7),
            tags=tags,
            category=map_osm_tags(tags),
        )
        parsed[item.upstream_id] = item
    order = {"node": 0, "way": 1, "relation": 2}
    return sorted(parsed.values(), key=lambda e: (order[e.osm_type], e.osm_id))


# ---- Fetching -----------------------------------------------------------------------------


async def fetch_elements(
    client: httpx.AsyncClient,
    bbox: tuple[float, float, float, float],
    *,
    endpoints: Sequence[str] = OVERPASS_ENDPOINTS,
    backoff_s: float = 5.0,
) -> list[OsmElement]:
    """One Overpass query; the next endpoint is tried only when one fails."""
    query = build_query(bbox)
    last_error: Exception | None = None
    for endpoint in endpoints:
        try:
            response = await get_with_retries(
                client,
                endpoint,
                params={"data": query},
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                max_attempts=2,
                backoff_s=backoff_s,
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("overpass endpoint failed endpoint=%s error=%s", endpoint, exc)
            last_error = exc
            continue
        remark = str(body.get("remark") or "")
        if "runtime error" in remark.lower():
            # Overpass reports timeouts/out-of-memory as HTTP 200 with a partial result.
            last_error = RuntimeError(f"overpass incomplete result: {remark[:200]}")
            logger.warning("overpass incomplete endpoint=%s", endpoint)
            continue
        return parse_elements(body.get("elements") or [])
    assert last_error is not None
    raise last_error


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=OVERPASS_TIMEOUT_S + 30.0,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )


# ---- Staging ------------------------------------------------------------------------------


@dataclass
class OsmReport(RunReport):
    unmapped: int = 0
    matched_wikidata: int = 0
    matched_name: int = 0
    with_opening_hours: int = 0
    by_category: dict[str, int] = field(default_factory=dict)


async def import_osm(
    session: AsyncSession,
    *,
    city_code: str,
    client: httpx.AsyncClient | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> OsmReport:
    """Fetch and stage OSM elements. Commits once at the end."""
    await require_active_policy(session, PROVIDER_KEY)  # refuse before any network call
    city = await load_city(session, city_code)
    box = bbox or city.bbox
    if box is None:
        raise ValueError(f"city {city_code} has no boundary to query inside")
    own_client = client is None
    http = client or make_client()
    try:
        elements = await fetch_elements(http, box)
    finally:
        if own_client:
            await http.aclose()
    return await stage_elements(session, city_code=city_code, elements=elements)


def _names_of(raw_name: str | None, payload: Mapping[str, Any]) -> set[str]:
    names = {normalize_search_text(raw_name or "")}
    for value in (payload.get("name") or {}).values():
        if isinstance(value, str):
            names.add(normalize_search_text(value))
    names.discard("")
    return names


async def match_by_name(
    session: AsyncSession,
    *,
    city_id: uuid.UUID,
    names: set[str],
    lng: float,
    lat: float,
    radius_m: float = MATCH_RADIUS_M,
) -> uuid.UUID | None:
    """Closest place with an accepted record of the same normalized name within ``radius_m``."""
    if not names:
        return None
    point = func.ST_GeogFromText(ewkt_point(lng, lat))
    rows = (
        await session.execute(
            select(
                ImportRecord.place_id,
                ImportRecord.raw_name,
                ImportRecord.allowed_payload,
                func.ST_Distance(ImportRecord.location, point).label("distance"),
            )
            .join(Place, Place.id == ImportRecord.place_id)
            .where(
                Place.city_id == city_id,
                Place.workflow_state != "RETIRED",
                ImportRecord.validation_status == "ACCEPTED",
                func.ST_DWithin(ImportRecord.location, point, radius_m),
            )
            .order_by("distance", ImportRecord.place_id)
        )
    ).all()
    for row in rows:
        if row.place_id is not None and names & _names_of(row.raw_name, row.allowed_payload or {}):
            return uuid.UUID(str(row.place_id))
    return None


async def stage_elements(
    session: AsyncSession, *, city_code: str, elements: Sequence[OsmElement]
) -> OsmReport:
    policy = await require_active_policy(session, PROVIDER_KEY)
    city = await load_city(session, city_code)
    areas = load_areas(city_code)
    report = OsmReport(provider_key=PROVIDER_KEY)
    mapped = [element for element in elements if element.category is not None]
    report.unmapped = len(elements) - len(mapped)
    checksum = sha256_hex(canonical_json([element.payload() for element in mapped]))
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
        publisher="OpenStreetMap",
        source_kind="OPEN_DATA",
        license_code=LICENSE_CODE,
        attribution_text=policy.attribution_text or ATTRIBUTION,
        homepage_url="https://www.openstreetmap.org/copyright",
    )
    wikidata_provider = await provider_id_for(session, WIKIDATA_KEY)
    for element in mapped:
        report.record_count += 1
        payload = policy.filter_payload(element.payload())
        names = element.names
        name = names.get("vi") or names.get("en") or element.upstream_id
        if not await inside_city(session, city.id, element.lng, element.lat):
            report.reject("OUTSIDE_CITY")
            add_record(
                session,
                run,
                upstream_id=element.upstream_id,
                raw_name=name,
                upstream_category=element.category,
                lng=element.lng,
                lat=element.lat,
                payload=payload,
                rejection_reason="OUTSIDE_CITY",
            )
            continue
        place_id = await place_for_identity(session, policy.provider_id, element.upstream_id)
        match_state = "MATCHED"
        match_method = "EXACT_ID"
        qid = element.wikidata_id
        if place_id is None and qid and wikidata_provider is not None:
            place_id = await place_for_identity(session, wikidata_provider, qid)
            if place_id is not None:
                report.matched_wikidata += 1
        if place_id is None:
            place_id = await match_by_name(
                session,
                city_id=city.id,
                names={normalize_search_text(value) for value in names.values()},
                lng=element.lng,
                lat=element.lat,
            )
            if place_id is not None:
                match_method = "NAME_AND_DISTANCE"
                report.matched_name += 1
        if place_id is None:
            place = await create_place(
                session,
                city_id=city.id,
                slug=await free_slug(session, city.id, name),
                lng=element.lng,
                lat=element.lat,
                category_code=element.category,
                area_code=assign_area(areas, element.lng, element.lat),
            )
            place_id = place.id
            match_state = "NEW_CANDIDATE"
            report.created_places += 1
            if qid and wikidata_provider is not None:
                # A later Wikidata import then enriches this place instead of duplicating it.
                await link_identity(
                    session,
                    place_id=place_id,
                    provider_id=wikidata_provider,
                    upstream_id=qid,
                    release=None,
                )
        await link_identity(
            session,
            place_id=place_id,
            provider_id=policy.provider_id,
            upstream_id=element.upstream_id,
            release=RELEASE_ID,
            match_method=match_method,
        )
        revision = await get_or_create_revision(
            session,
            source_id=source.id,
            locator=element.url,
            content_sha256=sha256_hex(canonical_json(payload)),
            title=name,
        )
        provenance: dict[str, Any] = {"source_revision_id": str(revision.id)}
        facts = payload.get("facts") or {}
        if facts:
            # The element revision is the evidence of each fact it carries (sheet.py shape).
            provenance["fact_source_revision_ids"] = {code: str(revision.id) for code in facts}
            report.with_opening_hours += 1 if "OPENING_HOURS" in facts else 0
        payload[PROVENANCE_KEY] = provenance
        add_record(
            session,
            run,
            upstream_id=element.upstream_id,
            raw_name=name,
            upstream_category=element.category,
            lng=element.lng,
            lat=element.lat,
            payload=payload,
            place_id=place_id,
            match_state=match_state,
        )
        report.accepted += 1
        assert element.category is not None
        report.by_category[element.category] = report.by_category.get(element.category, 0) + 1
    finish_run(run, report)
    await session.commit()
    logger.info(
        "osm import accepted=%d rejected=%d unmapped=%d created=%d",
        report.accepted,
        report.rejected,
        report.unmapped,
        report.created_places,
    )
    return report
