"""Wikidata linking for places without a QID (2026-11-08, DEC-022, ADR-012).

Most OSM-only places have a Wikidata item that the Wikidata importer skipped because its
``P31`` class is not mapped to a Gonarra category (e.g. "mountain range", "Chinese temple").
This step links such places to their item so the rest of the pipeline (Wikipedia summaries,
Commons P18 and page images, auto-publish) can use it.

* One SPARQL request: the importer's own city-box query (``wikidata.fetch_items``), which returns
  every item with a coordinate, its class labels, VI/EN labels, aliases, sitelinks and P18.
* A place (not RETIRED, not FOOD/CAFE, no Wikidata identity yet) is linked to an item only when
  all hold:
  - a VI or EN name of the place equals a VI or EN label/alias of the item after normalisation
    (case, diacritics, punctuation, parentheticals and a trailing city name ignored);
  - the item's P625 is within ``RADIUS_M`` (300 m), or ``LARGE_RADIUS_M`` (1 km) for large sites
    (beaches, nature, theme parks, viewpoints);
  - the item is a place: no class is a human, an administrative unit, a settlement or a road
    (``NOT_A_PLACE``);
  - the QID is not already linked to another place (a duplicate place: reported, not merged);
  - no other candidate place claims the same item (closest wins, the others are reported).
  When several items match one place, the closest is taken.
* Backfill: a place that already has a Wikidata identity (from an OSM ``wikidata=Q…`` tag) but no
  accepted Wikidata record (its class was unmapped, so the importer skipped it) gets the record
  too, when the item is a place (as above) within ``BACKFILL_RADIUS_M``. An item that is a human
  (OSM tags on memorials sometimes point at the person) is reported, never used.
* The match is stored where Wikidata records live: an accepted ``import_records`` row of the
  Wikidata provider (release ``wdqs-link``) with ``match_state`` MATCHED, an
  ``external_place_identities`` row (``NAME_AND_DISTANCE``) and a source
  revision of the source "Wikidata" (locator = item URL). The payload carries no ``location``
  and no ``category``: the place keeps its OSM point and category; labels, descriptions, aliases,
  sitelinks and P18 come from Wikidata like for imported items.
"""

from __future__ import annotations

import logging
import math
import re
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import normalize_search_text, parse_point
from app.ingestion.common import (
    PROVENANCE_KEY,
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
from app.ingestion.osm import PROVIDER_KEY as OSM_KEY
from app.ingestion.wikidata import (
    ENTITY_URL,
    LICENSE_CODE,
    PROVIDER_KEY,
    WikidataItem,
    fetch_human_qids,
    fetch_items,
    make_client,
)
from app.models.catalog import Place, PlaceLocalization
from app.models.providers import ExternalPlaceIdentity, ImportRecord, ImportRun

logger = logging.getLogger("gonarra.ingestion")

RELEASE_ID = "wdqs-link"
IMPORTER_VERSION = "wikidata-link-1"
RADIUS_M = 300.0
LARGE_RADIUS_M = 1000.0
BACKFILL_RADIUS_M = 2000.0
LARGE_CATEGORIES = frozenset({"BEACH", "NATURE", "THEME_PARK", "VIEWPOINT"})
SKIP_CATEGORIES = frozenset({"FOOD", "CAFE"})

# Class labels (English, lower case, whole label) that make an item something other than a
# visitable place. Whole-label matching keeps "war memorial", "town hall", "city gate" as places.
_NOT_A_PLACE = re.compile(
    r"human|person|family|given name|family name|surname"
    r"|.*\badministrative\b.*|.*\belectoral\b.*|.*\bconstituency\b.*"
    r"|(ward|commune|district|province|municipality|county|city|town|township|village|hamlet"
    r"|country|quarter|neighbou?rhood|urban district|rural district)( of .*| in .*)?"
    r"|(.* )?(human )?settlement|street|road|highway|route|(.* )?(street|road)"
    r"|massacre|war crime.*|(.* )?battle|(.* )?event|(.* )?festival|election|(.* )?disaster"
    r"|incident|wartime .*|military operation|(.* )?trial|wikimedia .*"
)
_PAREN = re.compile(r"\([^)]*\)")
_PUNCT = re.compile(r"[^\w\s]")
_CITY_SUFFIX = re.compile(r"\s+(hoi an|da nang|quang nam|viet nam|vietnam)$")


def match_key(name: str) -> str:
    """Comparable form of a name: normalised, no parentheticals/punctuation/trailing city."""
    text = normalize_search_text(_PAREN.sub(" ", name or ""))
    text = " ".join(_PUNCT.sub(" ", text).split())
    previous = None
    while previous != text:
        previous = text
        text = _CITY_SUFFIX.sub("", text)
    return text


def distance_m(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """Great-circle distance in metres (haversine)."""
    radius = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def is_place_item(item: WikidataItem) -> bool:
    """False for humans, administrative units, settlements, roads (and items without a class)."""
    labels = [label.lower() for label in item.class_labels]
    return bool(labels) and not any(_NOT_A_PLACE.fullmatch(label) for label in labels)


def is_human(item: WikidataItem) -> bool:
    return any(label.lower() in ("human", "person") for label in item.class_labels)


def item_keys(item: WikidataItem) -> set[str]:
    names: list[str] = list(item.labels.values())
    for values in item.aliases.values():
        names.extend(values)
    return {key for key in (match_key(name) for name in names) if len(key) >= 3}


def radius_for(category: str | None) -> float:
    return LARGE_RADIUS_M if category in LARGE_CATEGORIES else RADIUS_M


@dataclass
class LinkCandidate:
    place_id: uuid.UUID
    slug: str
    category: str | None
    lng: float
    lat: float
    names: set[str] = field(default_factory=set)

    def keys(self) -> set[str]:
        return {key for key in (match_key(name) for name in self.names) if len(key) >= 3}


@dataclass(frozen=True)
class Link:
    place_id: uuid.UUID
    slug: str
    item: WikidataItem
    distance_m: float
    method: str = "NAME_AND_DISTANCE"  # or OSM_WIKIDATA_TAG (backfill of a known identity)


@dataclass
class LinkReport(RunReport):
    candidates: int = 0
    items: int = 0
    linked: int = 0
    not_a_place: int = 0
    backfilled: int = 0
    humans: list[tuple[str, str]] = field(default_factory=list)  # (slug, QID)
    duplicates: list[tuple[str, str]] = field(default_factory=list)  # (slug, QID)
    contested: list[tuple[str, str]] = field(default_factory=list)  # (slug, QID)


def find_links(
    candidates: Sequence[LinkCandidate],
    items: Sequence[WikidataItem],
    *,
    linked_elsewhere: Mapping[str, uuid.UUID],
    report: LinkReport | None = None,
) -> list[Link]:
    """Pure matching (see module docstring); deterministic for the same input."""
    report = report or LinkReport(provider_key=PROVIDER_KEY)
    by_key: dict[str, list[WikidataItem]] = {}
    rejected_types: set[str] = set()
    for item in items:
        for key in item_keys(item):
            by_key.setdefault(key, []).append(item)
    best: dict[uuid.UUID, Link] = {}
    for candidate in sorted(candidates, key=lambda c: c.slug):
        radius = radius_for(candidate.category)
        options: dict[str, tuple[float, WikidataItem]] = {}
        for key in candidate.keys():
            for item in by_key.get(key, ()):
                distance = distance_m(candidate.lng, candidate.lat, item.lng, item.lat)
                if distance > radius:
                    continue
                if not is_place_item(item):
                    rejected_types.add(item.qid)
                    continue
                options[item.qid] = (distance, item)
        if not options:
            continue
        distance, item = min(options.values(), key=lambda pair: (pair[0], int(pair[1].qid[1:])))
        owner = linked_elsewhere.get(item.qid)
        if owner is not None and owner != candidate.place_id:
            report.duplicates.append((candidate.slug, item.qid))
            continue
        best[candidate.place_id] = Link(candidate.place_id, candidate.slug, item, distance)
    # One item, one place: the closest candidate wins.
    by_item: dict[str, list[Link]] = {}
    for link in best.values():
        by_item.setdefault(link.item.qid, []).append(link)
    links: list[Link] = []
    for qid, claims in sorted(by_item.items()):
        claims.sort(key=lambda link: (link.distance_m, link.slug))
        links.append(claims[0])
        report.contested.extend((link.slug, qid) for link in claims[1:])
    report.not_a_place = len(rejected_types)
    return sorted(links, key=lambda link: link.slug)


def find_backfills(
    known: Sequence[tuple[LinkCandidate, str]],
    items: Sequence[WikidataItem],
    *,
    humans: Iterable[str] = (),
    report: LinkReport | None = None,
) -> list[Link]:
    """Places with a known QID but no Wikidata record → that item, when it is a nearby place.
    ``humans``: QIDs known to be people (checked separately; people have no coordinate)."""
    report = report or LinkReport(provider_key=PROVIDER_KEY)
    by_qid = {item.qid: item for item in items}
    human_set = set(humans)
    links: list[Link] = []
    for candidate, qid in sorted(known, key=lambda pair: pair[0].slug):
        item = by_qid.get(qid)
        if qid in human_set or (item is not None and is_human(item)):
            report.humans.append((candidate.slug, qid))
            continue
        if item is None:
            continue
        distance = distance_m(candidate.lng, candidate.lat, item.lng, item.lat)
        if not is_place_item(item) or distance > BACKFILL_RADIUS_M:
            continue
        links.append(Link(candidate.place_id, candidate.slug, item, distance, "OSM_WIKIDATA_TAG"))
    return links


def link_payload(item: WikidataItem) -> dict[str, Any]:
    """The Wikidata record of a linked place: no location, no category (OSM keeps those)."""
    payload = item.payload()
    payload.pop("location", None)
    payload.pop("category", None)
    return payload


async def link_candidates(
    session: AsyncSession, city_id: uuid.UUID, *, place_ids: Iterable[uuid.UUID] | None = None
) -> list[LinkCandidate]:
    """Places without a Wikidata identity (or exactly ``place_ids``) with their VI/EN names
    (localizations and OSM records)."""
    wikidata_id = await provider_id_for(session, PROVIDER_KEY)
    query = select(Place).where(
        Place.city_id == city_id,
        Place.workflow_state != "RETIRED",
        Place.category_code.not_in(SKIP_CATEGORIES),
    )
    if place_ids is not None:
        query = query.where(Place.id.in_(list(place_ids) or [uuid.uuid4()]))
    elif wikidata_id is not None:
        query = query.where(
            Place.id.not_in(
                select(ExternalPlaceIdentity.place_id).where(
                    ExternalPlaceIdentity.data_provider_id == wikidata_id
                )
            )
        )
    places = (await session.scalars(query)).all()
    result: dict[uuid.UUID, LinkCandidate] = {}
    for place in places:
        point = parse_point(place.location)
        if point is None:
            continue
        result[place.id] = LinkCandidate(
            place.id, place.slug, place.category_code, point.longitude, point.latitude
        )
    if not result:
        return []
    names = await session.execute(
        select(PlaceLocalization.place_id, PlaceLocalization.name).where(
            PlaceLocalization.place_id.in_(result)
        )
    )
    for place_id, name in names.all():
        result[place_id].names.add(str(name))
    osm_id = await provider_id_for(session, OSM_KEY)
    if osm_id is not None:
        rows = await session.execute(
            select(ImportRecord.place_id, ImportRecord.allowed_payload)
            .join(ImportRun, ImportRun.id == ImportRecord.import_run_id)
            .where(
                ImportRun.data_provider_id == osm_id,
                ImportRun.status == "SUCCEEDED",
                ImportRecord.validation_status == "ACCEPTED",
                ImportRecord.place_id.in_(result),
            )
        )
        for row in rows.all():
            payload: dict[str, Any] = dict(row[1] or {})
            for value in _names(payload.get("name")):
                result[row[0]].names.add(value)
    return [entry for _, entry in sorted(result.items(), key=lambda kv: kv[1].slug)]


def _names(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        return [str(v) for v in value.values() if isinstance(v, str) and v.strip()]
    return []


async def identities_without_record(
    session: AsyncSession, city_id: uuid.UUID
) -> list[tuple[LinkCandidate, str]]:
    """(place, QID) for places whose Wikidata identity has no accepted Wikidata record."""
    provider_id = await provider_id_for(session, PROVIDER_KEY)
    if provider_id is None:
        return []
    with_record = (
        select(ImportRecord.place_id)
        .join(ImportRun, ImportRun.id == ImportRecord.import_run_id)
        .where(
            ImportRun.data_provider_id == provider_id,
            ImportRun.status == "SUCCEEDED",
            ImportRecord.validation_status == "ACCEPTED",
            ImportRecord.place_id.is_not(None),
        )
    )
    rows = (
        await session.execute(
            select(ExternalPlaceIdentity.place_id, ExternalPlaceIdentity.upstream_id)
            .join(Place, Place.id == ExternalPlaceIdentity.place_id)
            .where(
                ExternalPlaceIdentity.data_provider_id == provider_id,
                Place.city_id == city_id,
                Place.id.not_in(with_record),
            )
        )
    ).all()
    qids = {row[0]: str(row[1]) for row in rows}
    candidates = await link_candidates(session, city_id, place_ids=qids)
    return [(candidate, qids[candidate.place_id]) for candidate in candidates]


async def linked_qids(session: AsyncSession) -> dict[str, uuid.UUID]:
    provider_id = await provider_id_for(session, PROVIDER_KEY)
    if provider_id is None:
        return {}
    rows = await session.execute(
        select(ExternalPlaceIdentity.upstream_id, ExternalPlaceIdentity.place_id).where(
            ExternalPlaceIdentity.data_provider_id == provider_id
        )
    )
    return {str(qid): place_id for qid, place_id in rows.all()}


async def import_wikidata_links(
    session: AsyncSession,
    *,
    city_code: str,
    client: httpx.AsyncClient | None = None,
    items: Sequence[WikidataItem] | None = None,
) -> LinkReport:
    """Fetch the city's Wikidata items (one SPARQL request) unless given, check identity-only
    QIDs missing from them for P31=Q5 (one ``wbgetentities`` per 50), then link places."""
    await require_active_policy(session, PROVIDER_KEY)  # refuse before any network call
    city = await load_city(session, city_code)
    if city.bbox is None and items is None:
        raise ValueError(f"city {city_code} has no boundary to query inside")
    known = await identities_without_record(session, city.id)
    own_client = client is None
    http = client or make_client()
    try:
        if items is None:
            assert city.bbox is not None
            items = await fetch_items(http, city.bbox)
        present = {item.qid for item in items}
        missing = [qid for _candidate, qid in known if qid not in present]
        humans = await fetch_human_qids(http, missing) if missing else set()
    finally:
        if own_client:
            await http.aclose()
    return await stage_links(session, city_code=city_code, items=items, humans=humans)


async def stage_links(
    session: AsyncSession,
    *,
    city_code: str,
    items: Sequence[WikidataItem],
    humans: set[str] | None = None,
) -> LinkReport:
    policy = await require_active_policy(session, PROVIDER_KEY)
    city = await load_city(session, city_code)
    report = LinkReport(provider_key=PROVIDER_KEY)
    candidates = await link_candidates(session, city.id)
    report.candidates = len(candidates)
    report.items = len(items)
    links = find_links(
        candidates, items, linked_elsewhere=await linked_qids(session), report=report
    )
    known = await identities_without_record(session, city.id)
    backfills = find_backfills(known, items, humans=humans or set(), report=report)
    links = sorted([*links, *backfills], key=lambda link: link.slug)
    checksum = sha256_hex(
        canonical_json(
            [[str(link.place_id), link.item.qid, link_payload(link.item)] for link in links]
        )
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
    source = await get_or_create_source(
        session,
        data_provider_id=policy.provider_id,
        publisher="Wikidata",
        source_kind="OPEN_DATA",
        license_code=LICENSE_CODE,
        attribution_text=policy.attribution_text or "Wikidata (CC0)",
        homepage_url="https://www.wikidata.org/",
    )
    points = {c.place_id: c for c in candidates}
    points.update({candidate.place_id: candidate for candidate, _qid in known})
    for link in links:
        item = link.item
        report.record_count += 1
        payload = policy.filter_payload(link_payload(item))
        name = item.labels.get("en") or item.labels.get("vi") or item.qid
        revision = await get_or_create_revision(
            session,
            source_id=source.id,
            locator=ENTITY_URL.format(qid=item.qid),
            content_sha256=sha256_hex(canonical_json(payload)),
            title=name,
        )
        payload[PROVENANCE_KEY] = {
            "source_revision_id": str(revision.id),
            "match": {
                "method": link.method,
                "distance_m": round(link.distance_m, 1),
                "radius_m": (
                    BACKFILL_RADIUS_M
                    if link.method == "OSM_WIKIDATA_TAG"
                    else radius_for(points[link.place_id].category)
                ),
                "classes": list(item.class_labels),
            },
        }
        if link.method == "NAME_AND_DISTANCE":
            await link_identity(
                session,
                place_id=link.place_id,
                provider_id=policy.provider_id,
                upstream_id=item.qid,
                release=RELEASE_ID,
                match_method="NAME_AND_DISTANCE",
            )
        else:
            report.backfilled += 1
        candidate = points[link.place_id]
        add_record(
            session,
            run,
            upstream_id=item.qid,
            raw_name=name,
            upstream_category=item.category,
            lng=candidate.lng,
            lat=candidate.lat,
            payload=payload,
            place_id=link.place_id,
            match_state="MATCHED",
        )
        report.accepted += 1
    report.linked = len(links) - report.backfilled
    finish_run(run, report)
    await session.commit()
    logger.info(
        "wikidata link candidates=%d items=%d linked=%d duplicates=%d contested=%d",
        report.candidates,
        report.items,
        report.linked,
        len(report.duplicates),
        len(report.contested),
    )
    return report
