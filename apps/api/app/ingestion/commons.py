"""Wikimedia Commons place photos (DEC-022): licensed media for imported places.

File names come from each place's latest Wikidata record (``P18``, curated main image, first)
and OSM records (``wikimedia_commons`` / ``image`` pointing at Commons). The MediaWiki API
(``prop=imageinfo``, up to 50 titles per request) returns the thumbnail URL, size, MIME type and
``extmetadata``. Only free licences are accepted: CC0, public domain, CC BY *, CC BY-SA *
(no NC/ND, no "non-free", no unknown licence). A CC BY/BY-SA file without an author is rejected.

Accepted files become ``media_assets`` (rights CLEARED, per-file licence, creator and
attribution with HTML stripped; ``object_key`` is the absolute Commons thumbnail URL) linked to
the place through ``place_media`` in a deterministic order (Wikidata P18 first, then OSM, at
most ``MAX_PER_PLACE``). The file page is recorded as a source revision of the source
"Wikimedia Commons". ``auto_publish`` then sees licensed media for the place.

Images are hot-linked, not downloaded: ``media_assets.sha256`` holds the SHA-256 of
``commons:<title>:<sha1>`` (the Commons SHA-1 of the original file), a stable content-derived key.
"""

from __future__ import annotations

import asyncio
import html
import logging
import re
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import distinct_on
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
    load_city,
    provider_id_for,
    require_active_policy,
    sha256_hex,
    start_run,
)
from app.ingestion.osm import PROVIDER_KEY as OSM_KEY
from app.ingestion.osm import commons_file_name
from app.ingestion.wikidata import PROVIDER_KEY as WIKIDATA_KEY
from app.ingestion.wikidata import get_with_retries
from app.models.catalog import MediaAsset, Place, PlaceMedia, Source, SourceRevision
from app.models.providers import ImportRecord, ImportRun

logger = logging.getLogger("gonarra.ingestion")

PROVIDER_KEY = "wikimedia_commons"
IMPORTER_VERSION = "commons-1"
RELEASE_ID = "commons-api-live"
API_URL = "https://commons.wikimedia.org/w/api.php"
THUMB_WIDTH = 1280
BATCH_SIZE = 50
MAX_PER_PLACE = 3
REQUEST_DELAY_S = 0.5
ALLOWED_MIME = frozenset({"image/jpeg", "image/png", "image/webp"})
SOURCE_ATTRIBUTION = "Wikimedia Commons contributors (per-file licence and author)"
EXTMETADATA_FIELDS = (
    "LicenseShortName",
    "License",
    "UsageTerms",
    "Artist",
    "Credit",
    "Attribution",
    "AttributionRequired",
    "NonFree",
    "Copyrighted",
)

_TAG = re.compile(r"<[^>]+>")
_CC = re.compile(r"^cc[- ]by(?P<sa>[- ]sa)?[- ](?P<version>[0-9](?:\.[0-9])?)(?:[- ].*)?$")


# ---- Licences and metadata ----------------------------------------------------------------


def strip_html(value: str | None) -> str:
    """Commons extmetadata is HTML: tags removed, entities decoded, whitespace collapsed."""
    if not value:
        return ""
    text = html.unescape(_TAG.sub(" ", str(value)))
    return " ".join(text.split())


def classify_license(license_code: str | None, short_name: str | None) -> str | None:
    """Commons licence → Gonarra licence code, or None when not acceptable.

    Accepted: ``CC0-1.0``, ``PUBLIC-DOMAIN``, ``CC-BY-<v>`` and ``CC-BY-SA-<v>`` (ported
    variants such as ``cc-by-sa-3.0-de`` keep the version). NC/ND, GFDL-only and anything
    unknown are rejected.
    """
    for raw in (license_code, short_name):
        value = " ".join((raw or "").strip().lower().split())
        if not value:
            continue
        if "nc" in re.split(r"[- ]", value) or "nd" in re.split(r"[- ]", value):
            return None
        if value in ("cc0", "cc0 1.0", "cc0-1.0", "cc-zero") or value.startswith("cc0"):
            return "CC0-1.0"
        if value in ("pd", "public domain") or value.startswith(("pd-", "public domain")):
            return "PUBLIC-DOMAIN"
        match = _CC.match(value)
        if match is not None:
            version = match.group("version")
            version = version if "." in version else f"{version}.0"
            return f"CC-BY-SA-{version}" if match.group("sa") else f"CC-BY-{version}"
    return None


@dataclass(frozen=True)
class CommonsFile:
    title: str  # "File:..."
    file_url: str  # thumbnail URL (hot-linked), absolute https
    description_url: str
    width: int
    height: int
    mime: str
    sha1: str
    license_code: str
    license_name: str
    creator: str
    attribution: str

    @property
    def sha256(self) -> str:
        return sha256_hex(f"commons:{self.title}:{self.sha1}")

    def payload(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "file_url": self.file_url,
            "description_url": self.description_url,
            "width": self.width,
            "height": self.height,
            "mime": self.mime,
            "license": self.license_code,
            "creator": self.creator,
            "attribution": self.attribution,
        }


@dataclass(frozen=True)
class Rejected:
    title: str
    reason: str


def file_title(name: str) -> str:
    """``foo_bar.jpg`` / ``File:foo bar.jpg`` → ``File:Foo bar.jpg`` (MediaWiki normalisation)."""
    text = name.strip()
    for prefix in ("File:", "Image:", "file:", "image:"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    text = " ".join(text.replace("_", " ").split())
    return f"File:{text[:1].upper()}{text[1:]}" if text else ""


def parse_imageinfo(page: Mapping[str, Any]) -> CommonsFile | Rejected:
    title = str(page.get("title") or "")
    if page.get("missing") or page.get("invalid") or not page.get("imageinfo"):
        return Rejected(title, "MISSING_FILE")
    info = page["imageinfo"][0]
    meta = {
        key: (value or {}).get("value") for key, value in (info.get("extmetadata") or {}).items()
    }
    if str(meta.get("NonFree") or "").strip().lower() in ("true", "1", "yes"):
        return Rejected(title, "LICENSE_NOT_ALLOWED")
    short_name = strip_html(meta.get("LicenseShortName"))
    license_code = classify_license(strip_html(meta.get("License")), short_name)
    if license_code is None:
        return Rejected(title, "LICENSE_NOT_ALLOWED")
    mime = str(info.get("thumbmime") or info.get("mime") or "")
    if mime not in ALLOWED_MIME:
        return Rejected(title, "UNSUPPORTED_MIME")
    url = str(info.get("thumburl") or info.get("url") or "")
    width = int(info.get("thumbwidth") or info.get("width") or 0)
    height = int(info.get("thumbheight") or info.get("height") or 0)
    if not url.startswith("https://") or width <= 0 or height <= 0:
        return Rejected(title, "MISSING_FILE")
    creator = strip_html(meta.get("Artist"))[:300]
    free = license_code in ("CC0-1.0", "PUBLIC-DOMAIN")
    if not creator:
        if not free:
            return Rejected(title, "NO_AUTHOR")
        creator = "Unknown author"
    licence_label = short_name or (
        "Public domain" if license_code == "PUBLIC-DOMAIN" else license_code
    )
    custom = strip_html(meta.get("Attribution"))[:300]
    attribution = f"{custom or creator}, {licence_label}, via Wikimedia Commons"
    return CommonsFile(
        title=title,
        file_url=url,
        description_url=str(info.get("descriptionurl") or ""),
        width=width,
        height=height,
        mime=mime,
        sha1=str(info.get("sha1") or ""),
        license_code=license_code,
        license_name=licence_label,
        creator=creator,
        attribution=attribution,
    )


# ---- Fetching -----------------------------------------------------------------------------


async def fetch_files(
    client: httpx.AsyncClient,
    titles: Sequence[str],
    *,
    delay_s: float = REQUEST_DELAY_S,
    batch_size: int = BATCH_SIZE,
) -> dict[str, CommonsFile | Rejected]:
    """Requested title → parsed file or rejection (normalisations and redirects followed)."""
    results: dict[str, CommonsFile | Rejected] = {}
    unique = sorted(set(titles))
    for start in range(0, len(unique), batch_size):
        if start and delay_s:
            await asyncio.sleep(delay_s)
        batch = unique[start : start + batch_size]
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|thumbmime|sha1|extmetadata",
            "iiurlwidth": str(THUMB_WIDTH),
            "iiextmetadatafilter": "|".join(EXTMETADATA_FIELDS),
            "iiextmetadatalanguage": "en",
            "redirects": "1",
            "titles": "|".join(batch),
        }
        try:
            response = await get_with_retries(
                client, API_URL, params=params, headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            query = response.json().get("query") or {}
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("commons imageinfo failed batch=%d error=%s", start, exc)
            continue
        alias: dict[str, str] = {}
        for item in (query.get("normalized") or []) + (query.get("redirects") or []):
            alias[str(item.get("from"))] = str(item.get("to"))
        pages = {str(page.get("title")): page for page in query.get("pages") or []}
        for requested in batch:
            resolved = requested
            for _ in range(3):
                if resolved in pages or resolved not in alias:
                    break
                resolved = alias[resolved]
            page = pages.get(resolved)
            results[requested] = (
                parse_imageinfo(page) if page is not None else Rejected(requested, "MISSING_FILE")
            )
    return results


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=60.0, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    )


# ---- Candidates ---------------------------------------------------------------------------


@dataclass
class PlaceImages:
    place_id: uuid.UUID
    names: dict[str, str] = field(default_factory=dict)
    titles: list[str] = field(default_factory=list)

    def add(self, name: str | None) -> None:
        title = file_title(name) if name else ""
        if title and title not in self.titles:
            self.titles.append(title)


async def _latest_payloads(
    session: AsyncSession, city_id: uuid.UUID, provider_key: str
) -> list[tuple[uuid.UUID, str, dict[str, Any]]]:
    """(place_id, upstream_id, payload) of the latest accepted record per place and element."""
    provider_id = await provider_id_for(session, provider_key)
    if provider_id is None:
        return []
    rows = (
        await session.execute(
            select(ImportRecord.place_id, ImportRecord.upstream_id, ImportRecord.allowed_payload)
            .join(ImportRun, ImportRun.id == ImportRecord.import_run_id)
            .join(Place, Place.id == ImportRecord.place_id)
            .where(
                ImportRun.data_provider_id == provider_id,
                ImportRun.status == "SUCCEEDED",
                ImportRecord.validation_status == "ACCEPTED",
                Place.city_id == city_id,
                Place.workflow_state != "RETIRED",
            )
            .order_by(
                ImportRecord.place_id,
                ImportRecord.upstream_id,
                ImportRun.started_at.desc(),
                ImportRecord.created_at.desc(),
            )
            .ext(distinct_on(ImportRecord.place_id, ImportRecord.upstream_id))
        )
    ).all()
    return [(row[0], str(row[1]), dict(row[2] or {})) for row in rows if row[0] is not None]


async def place_images(session: AsyncSession, city_id: uuid.UUID) -> list[PlaceImages]:
    """Per place, ordered Commons titles: Wikidata P18 (sorted) first, then OSM tags."""
    places: dict[uuid.UUID, PlaceImages] = {}
    for place_id, _upstream, payload in await _latest_payloads(session, city_id, WIKIDATA_KEY):
        entry = places.setdefault(place_id, PlaceImages(place_id))
        entry.names = {**dict(payload.get("name") or {}), **entry.names}
        for name in payload.get("image") or []:
            entry.add(str(name))
    osm = sorted(
        await _latest_payloads(session, city_id, OSM_KEY), key=lambda row: (str(row[0]), row[1])
    )
    for place_id, _upstream, payload in osm:
        entry = places.setdefault(place_id, PlaceImages(place_id))
        for locale, value in dict(payload.get("name") or {}).items():
            entry.names.setdefault(locale, value)
        entry.add(commons_file_name(payload.get("wikimedia_commons")))
        entry.add(commons_file_name(payload.get("image")))
    return [
        entry for _, entry in sorted(places.items(), key=lambda item: str(item[0])) if entry.titles
    ]


# ---- Staging ------------------------------------------------------------------------------


@dataclass
class CommonsReport(RunReport):
    places_with_media: int = 0
    media_assets: int = 0
    by_license: dict[str, int] = field(default_factory=dict)


async def import_commons(
    session: AsyncSession, *, city_code: str, client: httpx.AsyncClient | None = None
) -> CommonsReport:
    await require_active_policy(session, PROVIDER_KEY)  # refuse before any network call
    city = await load_city(session, city_code)
    candidates = await place_images(session, city.id)
    titles = [title for entry in candidates for title in entry.titles]
    own_client = client is None
    http = client or make_client()
    try:
        files = await fetch_files(http, titles)
    finally:
        if own_client:
            await http.aclose()
    return await stage_files(session, city_code=city_code, candidates=candidates, files=files)


def _alt_texts(names: Mapping[str, str]) -> tuple[str, str]:
    vi = names.get("vi") or names.get("en") or ""
    en = names.get("en") or names.get("vi") or ""
    return f"Ảnh: {vi}".strip(), f"Photo: {en}".strip()


async def _upsert_asset(
    session: AsyncSession, item: CommonsFile, source_revision_id: uuid.UUID
) -> MediaAsset:
    asset = await session.scalar(
        select(MediaAsset).where(
            (MediaAsset.object_key == item.file_url) | (MediaAsset.sha256 == item.sha256)
        )
    )
    values = {
        "object_key": item.file_url,
        "content_type": item.mime,
        "width_px": item.width,
        "height_px": item.height,
        "sha256": item.sha256,
        "creator": item.creator,
        "source_revision_id": source_revision_id,
        "license_code": item.license_code,
        "attribution_text": item.attribution,
        "rights_proof_key": item.description_url or None,
        "rights_state": "CLEARED",
    }
    if asset is None:
        asset = MediaAsset(**values)
        session.add(asset)
    else:
        for key, value in values.items():
            if getattr(asset, key) != value:
                setattr(asset, key, value)
    await session.flush()
    return asset


async def _sync_place_media(
    session: AsyncSession,
    *,
    place_id: uuid.UUID,
    wanted: Sequence[uuid.UUID],
    commons_assets: set[uuid.UUID],
    alt: tuple[str, str],
) -> None:
    """Make the place's Commons media exactly ``wanted`` (in order) after any other media."""
    rows = (await session.scalars(select(PlaceMedia).where(PlaceMedia.place_id == place_id))).all()
    current = [
        (row.ordinal, row.media_asset_id, row.alt_text_vi, row.alt_text_en)
        for row in sorted(rows, key=lambda r: r.ordinal)
        if row.media_asset_id in commons_assets
    ]
    other = [row.ordinal for row in rows if row.media_asset_id not in commons_assets]
    base = max(other, default=0)
    desired = [(base + index, asset_id, *alt) for index, asset_id in enumerate(wanted, start=1)]
    if current == desired:
        return
    await session.execute(
        delete(PlaceMedia).where(
            PlaceMedia.place_id == place_id,
            PlaceMedia.media_asset_id.in_([row[1] for row in current] or [uuid.uuid4()]),
        )
    )
    await session.flush()
    for ordinal, asset_id, alt_vi, alt_en in desired:
        session.add(
            PlaceMedia(
                place_id=place_id,
                media_asset_id=asset_id,
                ordinal=ordinal,
                alt_text_vi=alt_vi,
                alt_text_en=alt_en,
            )
        )
    await session.flush()


async def _commons_asset_ids(session: AsyncSession, provider_id: uuid.UUID) -> set[uuid.UUID]:
    rows = await session.scalars(
        select(MediaAsset.id)
        .join(SourceRevision, SourceRevision.id == MediaAsset.source_revision_id)
        .join(Source, Source.id == SourceRevision.source_id)
        .where(Source.data_provider_id == provider_id)
    )
    return set(rows.all())


def _snapshot(result: CommonsFile | Rejected | None) -> Any:
    if isinstance(result, CommonsFile):
        return result.payload()
    return result.reason if result is not None else "UNFETCHED"


async def stage_files(
    session: AsyncSession,
    *,
    city_code: str,
    candidates: Sequence[PlaceImages],
    files: Mapping[str, CommonsFile | Rejected],
) -> CommonsReport:
    policy = await require_active_policy(session, PROVIDER_KEY)
    city = await load_city(session, city_code)
    report = CommonsReport(provider_key=PROVIDER_KEY)
    snapshot = [
        [str(entry.place_id), entry.names, [_snapshot(files.get(t)) for t in entry.titles]]
        for entry in candidates
    ]
    run = await start_run(
        session,
        policy,
        city.id,
        release_id=RELEASE_ID,
        checksum=sha256_hex(canonical_json(snapshot)),
        importer_version=IMPORTER_VERSION,
    )
    if run is None:
        report.skipped_unchanged = True
        return report
    report.import_run_id = run.id
    sources: dict[str, Source] = {}
    commons_assets = await _commons_asset_ids(session, policy.provider_id)
    wanted_by_place: dict[uuid.UUID, list[uuid.UUID]] = {}
    alt_by_place: dict[uuid.UUID, tuple[str, str]] = {}
    for entry in candidates:
        place = await session.get(Place, entry.place_id)
        if place is None:
            continue
        point = parse_point(place.location)
        lng, lat = (point.longitude, point.latitude) if point else (0.0, 0.0)
        wanted: list[uuid.UUID] = []
        for title in entry.titles:
            result = files.get(title)
            upstream_id = f"{title}#{place.id}"
            report.record_count += 1
            if isinstance(result, CommonsFile) and len(wanted) >= MAX_PER_PLACE:
                report.skipped += 1
                continue
            if not isinstance(result, CommonsFile):
                reason = result.reason if result is not None else "UNFETCHED"
                report.reject(reason)
                add_record(
                    session,
                    run,
                    upstream_id=upstream_id,
                    raw_name=title,
                    upstream_category=None,
                    lng=lng,
                    lat=lat,
                    payload={"title": title},
                    rejection_reason=reason,
                    place_id=place.id,
                )
                continue
            source = sources.get(result.license_code)
            if source is None:
                source = await get_or_create_source(
                    session,
                    data_provider_id=policy.provider_id,
                    publisher="Wikimedia Commons",
                    source_kind="OPEN_DATA",
                    license_code=result.license_code,
                    attribution_text=policy.attribution_text or SOURCE_ATTRIBUTION,
                    homepage_url="https://commons.wikimedia.org/",
                )
                sources[result.license_code] = source
            payload = policy.filter_payload(result.payload())
            revision = await get_or_create_revision(
                session,
                source_id=source.id,
                locator=result.description_url or result.file_url,
                content_sha256=sha256_hex(canonical_json(result.payload())),
                title=result.title,
            )
            asset = await _upsert_asset(session, result, revision.id)
            commons_assets.add(asset.id)
            if asset.id not in wanted:
                wanted.append(asset.id)
            payload[PROVENANCE_KEY] = {
                "source_revision_id": str(revision.id),
                "media_asset_id": str(asset.id),
            }
            add_record(
                session,
                run,
                upstream_id=upstream_id,
                raw_name=title,
                upstream_category=None,
                lng=lng,
                lat=lat,
                payload=payload,
                place_id=place.id,
                match_state="MATCHED",
            )
            report.accepted += 1
            report.by_license[result.license_code] = (
                report.by_license.get(result.license_code, 0) + 1
            )
        wanted_by_place[place.id] = wanted
        alt_by_place[place.id] = _alt_texts(entry.names)
    # Places that had Commons media but no longer have any wanted file lose it.
    stale = await session.scalars(
        select(PlaceMedia.place_id)
        .join(Place, Place.id == PlaceMedia.place_id)
        .where(
            Place.city_id == city.id,
            PlaceMedia.media_asset_id.in_(commons_assets or {uuid.uuid4()}),
        )
        .distinct()
    )
    for place_id in stale.all():
        wanted_by_place.setdefault(place_id, [])
        alt_by_place.setdefault(place_id, ("", ""))
    for place_id in sorted(wanted_by_place, key=str):
        await _sync_place_media(
            session,
            place_id=place_id,
            wanted=wanted_by_place[place_id],
            commons_assets=commons_assets,
            alt=alt_by_place[place_id],
        )
        if wanted_by_place[place_id]:
            report.places_with_media += 1
    report.media_assets = len({a for ids in wanted_by_place.values() for a in ids})
    finish_run(run, report)
    await session.commit()
    logger.info(
        "commons import accepted=%d rejected=%d places_with_media=%d",
        report.accepted,
        report.rejected,
        report.places_with_media,
    )
    return report
