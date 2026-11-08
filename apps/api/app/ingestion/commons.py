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

Second source, Wikipedia page images (2026-11-08): a place that still has no media after P18
and OSM, and whose latest Wikidata record (sitelinks) or Wikipedia record names a VI or EN
article, gets that article's *free* lead image (``prop=pageimages|pageprops``:
``page_image_free`` only, never the non-free ``page_image``; SVGs, maps, logos, flags and seals
are NOT_A_PHOTO). The file then goes through the same Commons ``imageinfo`` + ``extmetadata``
licence path (a local, non-Commons file is MISSING_FILE). Wrong-subject guards: a redirect to a
section (``tofragment``) is rejected, and when the place has a known Wikidata QID the article's
``wikibase_item`` must be that QID. The P18 of a parent / part-of item is never used. The
article revision is recorded as a source revision of "Wikipedia (vi|en)" and linked from the
import record provenance (``via_source_revision_id``).

Third and fourth sources (2026-11-08, phase 3), only for PUBLISHED places still without media
after the sources above, within ``EXTRA_REQUEST_BUDGET`` Commons requests per run:

* **Geosearch** (``list=geosearch``, namespace File) at the place point within ``GEO_RADIUS_M``
  (150 m; ``GEO_LARGE_RADIUS_M`` 500 m for beaches, nature, theme parks, viewpoints), ranked by
  distance then image size, at most ``GEO_MAX_PER_PLACE`` files.
* **Full-text search** (``list=search``, namespace File) for the VI and EN names in quotes; a
  file is accepted only when its title, description or categories contain the normalised place
  name and it is in the area (GPS within ``SEARCH_MAX_DISTANCE_M`` or, without GPS, a city/area
  name in its text), so a same-named pagoda elsewhere in Vietnam is never used.

Both go through the same licence/author/MIME checks and NOT_A_PHOTO; a file whose title or
categories name a *different* published place (and not this one) is skipped (``OTHER_PLACE``).
The import record provenance carries ``via`` (``commons_geosearch`` / ``commons_search``) and the
distance or query.

Images are hot-linked, not downloaded: ``media_assets.sha256`` holds the SHA-256 of
``commons:<title>:<sha1>`` (the Commons SHA-1 of the original file), a stable content-derived key.
"""

from __future__ import annotations

import asyncio
import html
import logging
import math
import re
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import normalize_search_text, parse_point
from app.ingestion.common import (
    PROVENANCE_KEY,
    USER_AGENT,
    PolicyNotActiveError,
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
WIKIPEDIA_KEY = "wikipedia"
IMPORTER_VERSION = "commons-2"  # commons-2: Wikipedia page images as a second source
RELEASE_ID = "commons-api-live"
API_URL = "https://commons.wikimedia.org/w/api.php"
WIKIPEDIA_API_URL = "https://{lang}.wikipedia.org/w/api.php"
WIKIPEDIA_LICENSE = "CC-BY-SA-4.0"
WIKIPEDIA_ATTRIBUTION = (
    "Text from Wikipedia ({lang}), by Wikipedia contributors, licensed CC BY-SA 4.0"
)
ARTICLE_LOCALES = ("vi", "en")
# Geosearch / full-text search (third and fourth sources; published places only).
GEO_RADIUS_M = 150
GEO_LARGE_RADIUS_M = 500
LARGE_CATEGORIES = frozenset({"BEACH", "NATURE", "THEME_PARK", "VIEWPOINT"})
GEO_LIMIT = 10
GEO_MAX_PER_PLACE = 2
SEARCH_LIMIT = 10
SEARCH_MAX_DISTANCE_M = 2000.0
EXTRA_REQUEST_BUDGET = 300
# Without GPS, a full-text hit must name the city or an area (normalised, no diacritics).
AREA_WORDS = (
    "da nang",
    "danang",
    "hoi an",
    "quang nam",
    "son tra",
    "ngu hanh son",
    "my son",
    "ba na",
    "cu lao cham",
    "tam ky",
    "dien ban",
)
# Lead images of small articles are often locator maps, logos, flags or seals: not a photo.
_NOT_A_PHOTO = re.compile(
    r"(\.svg$|\bmap\b|\blocator\b|\blocation\b|\blogo\b|\bflag\b|\bseal\b|"
    r"coat of arms|bản đồ|\bcờ\b|\bhuy hiệu\b)",
    re.IGNORECASE,
)
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
    "ImageDescription",
    "ObjectName",
    "GPSLatitude",
    "GPSLongitude",
)

_TAG = re.compile(r"<[^>]+>")
_PUNCT = re.compile(r"[^\w\s]")
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
    """A licensed Commons file. ``description``, ``categories`` and the GPS point are used for
    matching only (geosearch / search); they are not part of the stored payload."""

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
    description: str = ""
    categories: tuple[str, ...] = ()
    lat: float | None = None
    lng: float | None = None

    @property
    def area_px(self) -> int:
        return self.width * self.height

    def match_text(self) -> str:
        """Title, description and categories, normalised (for name checks)."""
        parts = [self.title.removeprefix("File:"), self.description, *self.categories]
        return _norm(" ".join(parts))

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
    description = " ".join(
        part
        for part in (strip_html(meta.get("ObjectName")), strip_html(meta.get("ImageDescription")))
        if part
    )[:2000]
    categories = tuple(
        str(category.get("title") or "").removeprefix("Category:")
        for category in page.get("categories") or []
        if category.get("title")
    )
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
        description=description,
        categories=categories,
        lat=_float(meta.get("GPSLatitude")),
        lng=_float(meta.get("GPSLongitude")),
    )


def _float(value: Any) -> float | None:
    try:
        return float(strip_html(str(value))) if value not in (None, "") else None
    except ValueError:
        return None


def _norm(text: str) -> str:
    """Lower case, no diacritics/punctuation, single spaces (for name containment checks)."""
    return " ".join(_PUNCT.sub(" ", normalize_search_text(text.replace("_", " "))).split())


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
            "prop": "imageinfo|categories",
            "iiprop": "url|size|mime|thumbmime|sha1|extmetadata",
            "cllimit": "max",
            "clshow": "!hidden",
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


# ---- Wikipedia page images ----------------------------------------------------------------


@dataclass(frozen=True)
class Article:
    locale: str  # vi | en
    title: str  # as stored in the Wikidata sitelink / Wikipedia record


@dataclass(frozen=True)
class PageImage:
    locale: str
    article: str  # resolved article title
    page_url: str
    revision: str | None
    qid: str | None  # the article's own Wikidata item
    file: str  # "File:..." (Commons title, MediaWiki-normalised)

    def payload(self) -> dict[str, Any]:
        return {
            "locale": self.locale,
            "article": self.article,
            "page_url": self.page_url,
            "revision": self.revision,
            "wikibase_item": self.qid,
            "file": self.file,
        }


def parse_pageimages(
    locale: str, body: Mapping[str, Any], requested: Sequence[str]
) -> dict[str, PageImage | Rejected]:
    """One ``prop=pageimages|pageprops|info`` response → requested article title → result."""
    query = body.get("query") or {}
    alias: dict[str, str] = {}
    fragments: set[str] = set()
    for item in query.get("normalized") or []:
        alias[str(item.get("from"))] = str(item.get("to"))
    for item in query.get("redirects") or []:
        alias[str(item.get("from"))] = str(item.get("to"))
        if item.get("tofragment"):
            fragments.add(str(item.get("from")))
    pages = {str(page.get("title")): page for page in query.get("pages") or []}
    results: dict[str, PageImage | Rejected] = {}
    for title in requested:
        resolved, section = title, False
        for _ in range(4):
            section = section or resolved in fragments
            if resolved in pages or resolved not in alias:
                break
            resolved = alias[resolved]
        page = pages.get(resolved)
        if section:
            results[title] = Rejected(title, "SECTION_REDIRECT")
            continue
        if page is None or page.get("missing") or page.get("invalid"):
            results[title] = Rejected(title, "MISSING_ARTICLE")
            continue
        props = page.get("pageprops") or {}
        free = str(props.get("page_image_free") or "").strip()
        if not free:
            results[title] = Rejected(title, "NO_FREE_PAGE_IMAGE")
            continue
        if _NOT_A_PHOTO.search(free.replace("_", " ")):
            results[title] = Rejected(title, "NOT_A_PHOTO")
            continue
        revision = page.get("lastrevid")
        results[title] = PageImage(
            locale=locale,
            article=resolved,
            page_url=str(
                page.get("canonicalurl")
                or page.get("fullurl")
                or f"https://{locale}.wikipedia.org/wiki/{resolved.replace(' ', '_')}"
            ),
            revision=str(revision) if revision is not None else None,
            qid=str(props.get("wikibase_item") or "") or None,
            file=file_title(free),
        )
    return results


def same_subject(image: PageImage, qid: str | None) -> bool:
    """A place with a known QID only takes the image of the article about that QID."""
    return qid is None or image.qid == qid


async def fetch_page_images(
    client: httpx.AsyncClient,
    articles: Sequence[Article],
    *,
    delay_s: float = REQUEST_DELAY_S,
    batch_size: int = BATCH_SIZE,
) -> dict[Article, PageImage | Rejected]:
    """Article → its free lead image (or a rejection). One request per 50 titles per locale."""
    results: dict[Article, PageImage | Rejected] = {}
    calls = 0
    for locale in ARTICLE_LOCALES:
        titles = sorted({a.title for a in articles if a.locale == locale})
        for start in range(0, len(titles), batch_size):
            if calls and delay_s:
                await asyncio.sleep(delay_s)
            calls += 1
            batch = titles[start : start + batch_size]
            params = {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "prop": "pageimages|pageprops|info",
                "piprop": "name",
                "ppprop": "page_image_free|wikibase_item",
                "inprop": "url",
                "redirects": "1",
                "titles": "|".join(batch),
            }
            try:
                response = await get_with_retries(
                    client,
                    WIKIPEDIA_API_URL.format(lang=locale),
                    params=params,
                    headers={"User-Agent": USER_AGENT},
                )
                response.raise_for_status()
                body = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning("wikipedia pageimages failed locale=%s error=%s", locale, exc)
                continue
            for title, result in parse_pageimages(locale, body, batch).items():
                results[Article(locale, title)] = result
    return results


# ---- Commons geosearch and full-text search ------------------------------------------------


@dataclass(frozen=True)
class PublishedPlace:
    place_id: uuid.UUID
    slug: str
    category: str | None
    lng: float
    lat: float
    names: dict[str, str]

    def keys(self) -> set[str]:
        """Normalised names specific enough to match on (two words or more)."""
        return {key for key in (_norm(n) for n in self.names.values()) if len(key.split()) >= 2}

    @property
    def geo_radius(self) -> int:
        return GEO_LARGE_RADIUS_M if self.category in LARGE_CATEGORIES else GEO_RADIUS_M


def _contains(text_value: str, key: str) -> bool:
    return f" {key} " in f" {text_value} "


def distance_m(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    radius = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def names_other_place(
    item: CommonsFile, place: PublishedPlace, others: Sequence[PublishedPlace]
) -> bool:
    """True when the file's title/categories name another published place and not this one."""
    haystack = _norm(" ".join([item.title.removeprefix("File:"), *item.categories]))
    if any(_contains(haystack, key) for key in place.keys()):
        return False
    return any(
        other.place_id != place.place_id and any(_contains(haystack, key) for key in other.keys())
        for other in others
    )


def search_query(place: PublishedPlace) -> str | None:
    names: list[str] = []
    for locale in ARTICLE_LOCALES:
        name = " ".join((place.names.get(locale) or "").replace('"', " ").split())
        if name and name not in names and len(_norm(name).split()) >= 2:
            names.append(name)
    return " OR ".join(f'"{name}"' for name in names) or None


def search_match(item: CommonsFile, place: PublishedPlace) -> bool:
    """A full-text hit names this place and is in the area (GPS, else a city/area word)."""
    haystack = item.match_text()
    if not any(_contains(haystack, key) for key in place.keys()):
        return False
    if item.lat is not None and item.lng is not None:
        return distance_m(place.lng, place.lat, item.lng, item.lat) <= SEARCH_MAX_DISTANCE_M
    return any(_contains(haystack, word) for word in AREA_WORDS)


def parse_geosearch(body: Mapping[str, Any]) -> list[tuple[str, float]]:
    hits = ((body.get("query") or {}).get("geosearch")) or []
    return [
        (file_title(str(hit.get("title") or "")), float(hit.get("dist") or 0.0))
        for hit in hits
        if str(hit.get("title") or "").startswith("File:")
    ]


def parse_search(body: Mapping[str, Any]) -> list[str]:
    hits = ((body.get("query") or {}).get("search")) or []
    return [
        file_title(str(hit.get("title") or ""))
        for hit in hits
        if str(hit.get("title") or "").startswith("File:")
    ]


async def _query(client: httpx.AsyncClient, params: dict[str, str]) -> dict[str, Any] | None:
    try:
        response = await get_with_retries(
            client,
            API_URL,
            params={"action": "query", "format": "json", "formatversion": "2", **params},
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        return body
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("commons %s failed error=%s", params.get("list"), exc)
        return None


async def geosearch(client: httpx.AsyncClient, place: PublishedPlace) -> list[tuple[str, float]]:
    body = await _query(
        client,
        {
            "list": "geosearch",
            "gscoord": f"{place.lat}|{place.lng}",
            "gsradius": str(place.geo_radius),
            "gsnamespace": "6",
            "gslimit": str(GEO_LIMIT),
        },
    )
    return parse_geosearch(body) if body else []


async def search_files(client: httpx.AsyncClient, query: str) -> list[str]:
    body = await _query(
        client,
        {"list": "search", "srsearch": query, "srnamespace": "6", "srlimit": str(SEARCH_LIMIT)},
    )
    return parse_search(body) if body else []


def choose_found(
    place: PublishedPlace,
    *,
    geo_hits: Sequence[tuple[str, float]],
    search_hits: Sequence[str],
    query: str | None,
    files: Mapping[str, CommonsFile | Rejected],
    others: Sequence[PublishedPlace],
) -> list[tuple[str, dict[str, Any]]]:
    """Accepted (title, provenance) for one place: search matches first, then the nearest
    geosearch photos (largest first at equal distance); at most ``MAX_PER_PLACE``."""

    def usable(title: str) -> CommonsFile | None:
        item = files.get(title)
        if not isinstance(item, CommonsFile) or _NOT_A_PHOTO.search(title):
            return None
        return None if names_other_place(item, place, others) else item

    chosen: list[tuple[str, dict[str, Any]]] = []
    for title in search_hits:
        item = usable(title)
        if item is not None and search_match(item, place):
            chosen.append((title, {"via": "commons_search", "query": query}))
    geo: list[tuple[float, int, str]] = []
    for title, dist in geo_hits:
        item = usable(title)
        if item is not None:
            geo.append((dist, -item.area_px, title))
    for dist, _area, title in sorted(geo)[:GEO_MAX_PER_PLACE]:
        chosen.append((title, {"via": "commons_geosearch", "distance_m": round(dist, 1)}))
    unique: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for title, how in chosen:
        if title not in seen:
            seen.add(title)
            unique.append((title, how))
    return unique[:MAX_PER_PLACE]


async def published_places(session: AsyncSession, city_id: uuid.UUID) -> list[PublishedPlace]:
    """Published places with their published VI/EN names and point."""
    rows = (
        await session.execute(
            text(
                "SELECT p.id, p.slug, cp.category_code, ST_X(cp.location::geometry) AS lng, "
                "ST_Y(cp.location::geometry) AS lat, lv.name AS name_vi, le.name AS name_en "
                "FROM catalog_publications cp JOIN places p ON p.id = cp.place_id "
                "JOIN place_localizations lv ON lv.id = cp.localization_vi_id "
                "JOIN place_localizations le ON le.id = cp.localization_en_id "
                "WHERE cp.state = 'PUBLISHED' AND cp.city_id = :city ORDER BY p.slug"
            ),
            {"city": city_id},
        )
    ).all()
    return [
        PublishedPlace(
            place_id=row.id,
            slug=row.slug,
            category=row.category_code,
            lng=float(row.lng),
            lat=float(row.lat),
            names={k: v for k, v in (("vi", row.name_vi), ("en", row.name_en)) if v},
        )
        for row in rows
    ]


# ---- Candidates ---------------------------------------------------------------------------


@dataclass
class PlaceImages:
    place_id: uuid.UUID
    names: dict[str, str] = field(default_factory=dict)
    titles: list[str] = field(default_factory=list)
    # File title → the Wikipedia article it came from (second source only).
    via: dict[str, PageImage] = field(default_factory=dict)
    # File title → how geosearch / full-text search found it (third and fourth sources).
    found: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add(self, name: str | None) -> None:
        title = file_title(name) if name else ""
        if title and title not in self.titles:
            self.titles.append(title)

    def add_page_image(self, image: PageImage) -> None:
        if image.file and image.file not in self.titles:
            self.titles.append(image.file)
            self.via[image.file] = image

    def add_found(self, title: str, how: dict[str, Any]) -> None:
        if title and title not in self.titles:
            self.titles.append(title)
            self.found[title] = how


@dataclass
class PlaceArticles:
    place_id: uuid.UUID
    qid: str | None = None
    names: dict[str, str] = field(default_factory=dict)
    articles: list[Article] = field(default_factory=list)

    def add(self, locale: str, title: Any) -> None:
        text = " ".join(str(title or "").replace("_", " ").split())
        article = Article(locale, text)
        if text and locale in ARTICLE_LOCALES and article not in self.articles:
            self.articles.append(article)


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


async def place_articles(session: AsyncSession, city_id: uuid.UUID) -> list[PlaceArticles]:
    """Per place, its own VI/EN Wikipedia articles (Wikidata sitelinks, then Wikipedia records)
    and its own QID (Wikidata record, else OSM ``wikidata`` tag) for the subject check."""
    places: dict[uuid.UUID, PlaceArticles] = {}
    for place_id, upstream, payload in await _latest_payloads(session, city_id, WIKIDATA_KEY):
        entry = places.setdefault(place_id, PlaceArticles(place_id))
        entry.qid = entry.qid or upstream
        entry.names = {**dict(payload.get("name") or {}), **entry.names}
        sitelinks = dict(payload.get("sitelinks") or {})
        for locale in ARTICLE_LOCALES:
            entry.add(locale, sitelinks.get(locale))
    for place_id, upstream, payload in await _latest_payloads(session, city_id, WIKIPEDIA_KEY):
        locale = upstream.split(":", 1)[0]
        entry = places.setdefault(place_id, PlaceArticles(place_id))
        entry.add(locale, payload.get("title") or upstream.split(":", 1)[-1])
    for place_id, _upstream, payload in await _latest_payloads(session, city_id, OSM_KEY):
        known = places.get(place_id)
        if known is None:
            continue
        known.qid = known.qid or (str(payload.get("wikidata") or "") or None)
        for locale, value in dict(payload.get("name") or {}).items():
            known.names.setdefault(locale, value)
    for entry in places.values():
        entry.articles.sort(key=lambda a: ARTICLE_LOCALES.index(a.locale))
    return [
        entry
        for _, entry in sorted(places.items(), key=lambda item: str(item[0]))
        if entry.articles
    ]


async def _places_with_other_media(session: AsyncSession, city_id: uuid.UUID) -> set[uuid.UUID]:
    """Places with media that did not come from Commons (owner photos): left alone."""
    commons_id = await provider_id_for(session, PROVIDER_KEY)
    commons = await _commons_asset_ids(session, commons_id) if commons_id else set()
    rows = await session.scalars(
        select(PlaceMedia.place_id)
        .join(Place, Place.id == PlaceMedia.place_id)
        .where(
            Place.city_id == city_id,
            PlaceMedia.media_asset_id.not_in(commons or {uuid.uuid4()}),
        )
        .distinct()
    )
    return set(rows.all())


def add_page_images(
    candidates: Sequence[PlaceImages],
    articles: Sequence[PlaceArticles],
    images: Mapping[Article, PageImage | Rejected],
    *,
    skip: set[uuid.UUID],
) -> tuple[list[PlaceImages], int]:
    """Candidates plus page images for places in ``articles`` not in ``skip`` (those that
    already have media). Returns the new candidate list and the number of wrong-subject
    articles dropped."""
    by_place = {entry.place_id: entry for entry in candidates}
    wrong_subject = 0
    for entry in articles:
        if entry.place_id in skip:
            continue
        for article in entry.articles:
            image = images.get(article)
            if not isinstance(image, PageImage):
                continue
            if not same_subject(image, entry.qid):
                wrong_subject += 1
                continue
            target = by_place.get(entry.place_id)
            if target is None:
                names = dict(entry.names)
                if not names:
                    names = {a.locale: a.title for a in reversed(entry.articles)}
                target = by_place[entry.place_id] = PlaceImages(entry.place_id, names=names)
            target.add_page_image(image)
    ordered = [entry for _, entry in sorted(by_place.items(), key=lambda item: str(item[0]))]
    return [entry for entry in ordered if entry.titles], wrong_subject


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
    places_with_page_image: int = 0
    page_image_articles: int = 0
    page_image_wrong_subject: int = 0
    extra_requests: int = 0
    places_with_geosearch: int = 0
    places_with_search: int = 0
    media_assets: int = 0
    by_license: dict[str, int] = field(default_factory=dict)


async def import_commons(
    session: AsyncSession,
    *,
    city_code: str,
    client: httpx.AsyncClient | None = None,
    page_images: bool = True,
    extra_sources: bool = True,
    request_budget: int = EXTRA_REQUEST_BUDGET,
) -> CommonsReport:
    await require_active_policy(session, PROVIDER_KEY)  # refuse before any network call
    city = await load_city(session, city_code)
    candidates = await place_images(session, city.id)
    titles = [title for entry in candidates for title in entry.titles]
    articles: list[PlaceArticles] = []
    if page_images:
        try:
            await require_active_policy(session, WIKIPEDIA_KEY)
            articles = await place_articles(session, city.id)
        except PolicyNotActiveError:
            logger.info("wikipedia policy not active: page images skipped")
    looked_up = 0
    wrong_subject = 0
    own_client = client is None
    http = client or make_client()
    try:
        files = await fetch_files(http, titles)
        if articles:
            skip = await _places_with_other_media(session, city.id)
            skip |= {
                entry.place_id
                for entry in candidates
                if any(isinstance(files.get(t), CommonsFile) for t in entry.titles)
            }
            wanted = [a for a in articles if a.place_id not in skip]
            looked_up = sum(len(a.articles) for a in wanted)
            images = await fetch_page_images(http, [x for a in wanted for x in a.articles])
            candidates, wrong_subject = add_page_images(candidates, wanted, images, skip=skip)
            extra = [t for e in candidates for t in e.via if t not in files]
            if extra:
                files = {**files, **await fetch_files(http, extra)}
        extra_requests = 0
        if extra_sources:
            candidates, files, extra_requests = await _add_search_sources(
                session, http, city.id, candidates, files, budget=request_budget
            )
    finally:
        if own_client:
            await http.aclose()
    report = await stage_files(session, city_code=city_code, candidates=candidates, files=files)
    report.page_image_articles = looked_up
    report.page_image_wrong_subject = wrong_subject
    report.extra_requests = extra_requests
    return report


async def _add_search_sources(
    session: AsyncSession,
    http: httpx.AsyncClient,
    city_id: uuid.UUID,
    candidates: list[PlaceImages],
    files: dict[str, CommonsFile | Rejected],
    *,
    budget: int,
) -> tuple[list[PlaceImages], dict[str, CommonsFile | Rejected], int]:
    """Geosearch + full-text search for published places that still have no accepted file."""
    published = await published_places(session, city_id)
    have = await _places_with_other_media(session, city_id)
    have |= {
        entry.place_id
        for entry in candidates
        if any(isinstance(files.get(t), CommonsFile) for t in entry.titles)
    }
    need = [place for place in published if place.place_id not in have]
    used = 0
    geo: dict[uuid.UUID, list[tuple[str, float]]] = {}
    found: dict[uuid.UUID, list[str]] = {}
    queries: dict[uuid.UUID, str | None] = {}
    # Keep roughly one imageinfo batch per 5 places for the files found.
    reserve = len(need) // 5 + 1
    for place in need:
        if used + reserve >= budget:
            break
        geo[place.place_id] = await geosearch(http, place)
        used += 1
        await asyncio.sleep(REQUEST_DELAY_S)
    for place in need:
        query = search_query(place)
        queries[place.place_id] = query
        if query is None or used + reserve >= budget:
            continue
        found[place.place_id] = await search_files(http, query)
        used += 1
        await asyncio.sleep(REQUEST_DELAY_S)
    titles = {
        title
        for place in need
        for title in [
            *(t for t, _ in geo.get(place.place_id, [])),
            *found.get(place.place_id, []),
        ]
    }
    missing = sorted(t for t in titles if t not in files)
    room = max(0, budget - used) * BATCH_SIZE
    if missing:
        used += (min(len(missing), room) + BATCH_SIZE - 1) // BATCH_SIZE
        files = {**files, **await fetch_files(http, missing[:room])}
    by_place = {entry.place_id: entry for entry in candidates}
    for place in need:
        chosen = choose_found(
            place,
            geo_hits=geo.get(place.place_id, []),
            search_hits=found.get(place.place_id, []),
            query=queries.get(place.place_id),
            files=files,
            others=published,
        )
        if not chosen:
            continue
        entry = by_place.get(place.place_id)
        if entry is None:
            entry = by_place[place.place_id] = PlaceImages(place.place_id, names=dict(place.names))
        for title, how in chosen:
            entry.add_found(title, how)
    ordered = [entry for _, entry in sorted(by_place.items(), key=lambda item: str(item[0]))]
    return [entry for entry in ordered if entry.titles], files, used


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


async def _page_revision(
    session: AsyncSession, image: PageImage, cache: dict[str, Source]
) -> SourceRevision:
    """The Wikipedia article (revision) that chose the image, as a provenance source revision."""
    source = cache.get(image.locale)
    if source is None:
        provider_id = await provider_id_for(session, WIKIPEDIA_KEY)
        source = await get_or_create_source(
            session,
            data_provider_id=provider_id,
            publisher=f"Wikipedia ({image.locale})",
            source_kind="REFERENCE",
            license_code=WIKIPEDIA_LICENSE,
            attribution_text=WIKIPEDIA_ATTRIBUTION.format(lang=image.locale),
            homepage_url=f"https://{image.locale}.wikipedia.org/",
        )
        cache[image.locale] = source
    title = (
        image.article if image.revision is None else f"{image.article} (revision {image.revision})"
    )
    return await get_or_create_revision(
        session,
        source_id=source.id,
        locator=image.page_url,
        content_sha256=sha256_hex(canonical_json(image.payload())),
        title=title,
    )


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
        [
            str(entry.place_id),
            entry.names,
            [_snapshot(files.get(t)) for t in entry.titles],
            {t: image.payload() for t, image in sorted(entry.via.items())},
            dict(sorted(entry.found.items())),
        ]
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
    wikipedia_sources: dict[str, Source] = {}
    page_image_places: set[uuid.UUID] = set()
    geo_places: set[uuid.UUID] = set()
    search_places: set[uuid.UUID] = set()
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
            image = entry.via.get(title)
            if image is not None:
                via = await _page_revision(session, image, wikipedia_sources)
                payload[PROVENANCE_KEY]["via"] = "wikipedia_page_image"
                payload[PROVENANCE_KEY]["via_source_revision_id"] = str(via.id)
                page_image_places.add(place.id)
            how = entry.found.get(title)
            if how is not None:
                payload[PROVENANCE_KEY].update(how)
                if how["via"] == "commons_geosearch":
                    geo_places.add(place.id)
                else:
                    search_places.add(place.id)
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
    report.places_with_page_image = len({p for p in page_image_places if wanted_by_place.get(p)})
    report.places_with_geosearch = len({p for p in geo_places if wanted_by_place.get(p)})
    report.places_with_search = len({p for p in search_places if wanted_by_place.get(p)})
    finish_run(run, report)
    await session.commit()
    logger.info(
        "commons import accepted=%d rejected=%d places_with_media=%d",
        report.accepted,
        report.rejected,
        report.places_with_media,
    )
    return report
