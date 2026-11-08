"""Wikivoyage importer (DEC-032): listings and city sections, human-written, CC BY-SA 4.0.

Pages of Đà Nẵng and the Hội An area are fetched through the MediaWiki API (``action=parse``,
wikitext + revision id), at most one request every ``REQUEST_DELAY_S`` seconds with ``maxlag``
and back-off on HTTP 429, and cached on disk (``--cache-dir``, 7 days) so re-runs do not hit the
servers. Each page revision is one ``source_revisions`` row (locator = ``…&oldid=<revid>``).

* **Listings** (``{{see|do|eat|drink|buy|listing}}``; vi ``{{địa điểm|tên=|địa chỉ=}}``) are
  matched to existing places — by the listing's ``wikidata`` QID, else by name core within the
  category radius (or a unique exact name core near the page's town when the listing has no
  coordinates) — and staged as import records: EN name, VI alias/name only when the ``alt``
  carries Vietnamese diacritics, the listing ``content`` verbatim as the EN description (markup
  removed, the only change), hours/price facts only when ``lastedit`` ≥ 2023-01-01, and the
  listing ``lastedit`` as the verification date. A listing that matches nothing becomes a new
  IMPORTED draft only with coordinates inside the city, a mapped category and ≥ 60 characters of
  content. Lodging, transport, tailors, banks and supermarkets are skipped (not trip stops).
* **City sections** (intro, Understand, Get around, Stay safe …; vi Giới thiệu/Tổng quan, Đi
  trong thành phố, An ninh …) become DRAFT CITY-scope Guide chunks (≤ 1 200 characters each)
  approved by ``publish auto`` (``app.curation.city_chunks``).

Attribution: "Wikivoyage contributors, '<page>'" with the page link, licence CC BY-SA 4.0, and
"markup removed" as the indicated change. Our adapted text stays CC BY-SA 4.0 (share-alike).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.normalize import fold_words
from app.curation.city_chunks import CityChunk, CityChunkReport, stage_city_chunks
from app.curation.common import parse_point
from app.curation.dedupe import RADIUS_M, distance_m
from app.curation.names import has_vietnamese_diacritics, is_not_a_stop_name, name_core
from app.ingestion.areas import assign_area, load_areas
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
from app.ingestion.osm import parse_osm_opening_hours
from app.models.catalog import Place
from app.models.providers import ExternalPlaceIdentity, ImportRecord

logger = logging.getLogger("gonarra.ingestion")

PROVIDER_KEY = "wikivoyage"
IMPORTER_VERSION = "wv-4"  # 2: type-compatible matching, activities only by QID
RELEASE_ID = "mediawiki-parse"
LICENSE_CODE = "CC-BY-SA-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
ATTRIBUTION = (
    "Text from Wikivoyage ({lang}), by Wikivoyage contributors, licensed CC BY-SA 4.0; "
    "markup removed"
)
API_URL = "https://{lang}.wikivoyage.org/w/api.php"
PAGE_URL = "https://{lang}.wikivoyage.org/wiki/{title}"
REVISION_URL = "https://{lang}.wikivoyage.org/w/index.php?title={title}&oldid={revid}"
REQUEST_DELAY_S = 5.0
MAX_ATTEMPTS = 5
CACHE_TTL_S = 7 * 24 * 3600
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "gonarra" / "wikivoyage"
MIN_NEW_CONTENT_CHARS = 60
MAX_CHUNK_CHARS = 1200
NO_COORD_MATCH_RADIUS_M = 20_000.0
# Listing coordinates are often approximate: an exact name core matches within this distance.
EXACT_NAME_RADIUS_M = 1_000.0
WIKIDATA_KEY = "wikidata"

# Titles verified 2026-11-09. Marble Mountains, Ba Na Hills, Son Tra and Hai Van Pass have no
# en.wikivoyage page; they are listings inside "Da Nang".
PAGES: dict[str, tuple[str, ...]] = {
    "en": ("Da Nang", "Hoi An", "My Son", "Chàm Islands", "Tam Kỳ"),
    "vi": ("Đà Nẵng", "Hội An", "Thánh địa Mỹ Sơn"),
}
# Reference point of each page's town (lat, lng): listings without coordinates match only near it.
PAGE_CENTRES: dict[str, tuple[float, float]] = {
    "Da Nang": (16.054, 108.202),
    "Đà Nẵng": (16.054, 108.202),
    "Hoi An": (15.880, 108.335),
    "Hội An": (15.880, 108.335),
    "My Son": (15.764, 108.124),
    "Thánh địa Mỹ Sơn": (15.764, 108.124),
    "Chàm Islands": (15.950, 108.510),
    "Tam Kỳ": (15.570, 108.470),
}
# Pages whose sections become city-level Guide chunks.
CITY_CHUNK_PAGES = frozenset({"Da Nang", "Hoi An", "Chàm Islands", "My Son", "Đà Nẵng", "Hội An"})
SECTION_MAP: dict[str, str] = {
    "understand": "CITY_OVERVIEW",
    "get around": "GETTING_AROUND",
    "stay safe": "PRACTICAL",
    "stay healthy": "PRACTICAL",
    "respect": "PRACTICAL",
    "cope": "PRACTICAL",
    "connect": "PRACTICAL",
    "fees and permits": "PRACTICAL",
    "gioi thieu": "CITY_OVERVIEW",
    "tong quan": "CITY_OVERVIEW",
    "di trong thanh pho": "GETTING_AROUND",
    "di lai": "GETTING_AROUND",
    "an ninh": "PRACTICAL",
    "an toan": "PRACTICAL",
    "y te": "PRACTICAL",
    "luu y": "PRACTICAL",
}

LISTING_TYPES: dict[str, str] = {
    "see": "see",
    "do": "do",
    "eat": "eat",
    "drink": "drink",
    "buy": "buy",
    "listing": "listing",
    "địa điểm": "listing",
    "xem": "see",
    "làm": "do",
    "ăn": "eat",
    "uống": "drink",
    "mua": "buy",
}
SKIPPED_TYPES = frozenset({"sleep", "go", "marker", "city", "vicinity"})
_VI_PARAMS = {"tên": "name", "địa chỉ": "address", "điện thoại": "phone", "giờ": "hours"}

_MARKET = re.compile(r"\b(market|cho|night market|cho dem)\b")
_VILLAGE = re.compile(r"\b(village|lang)\b")
_CAFE = re.compile(r"\b(caf|cafe|coffee|ca phe|tea|teahouse|tra)\b")
_SKIP_BUY = re.compile(
    r"\b(tailor|tailors|bank|atm|supermarket|big c|lotte|mega market|mall|aeon|vincom|pharmacy|"
    r"bookshop|book store|shoe|shoes|optician|laundry|massage|spa|motorbike|rental|goods|"
    r"store|shop)\b"
)
_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("museum|bao tang|gallery", "MUSEUM"),
    (
        "pagoda|temple|chua|den|mieu|church|cathedral|nha tho|assembly hall|hoi quan|shrine|"
        "tower|thap",
        "RELIGIOUS_SITE",
    ),
    ("beach|bai bien|bai tam", "BEACH"),
    ("bridge|cau|house|nha co|old town|ruins|citadel|fort|tomb|well", "HERITAGE"),
    ("mountain|mountains|nui|peninsula|island|islands|cave|waterfall|forest|river", "NATURE"),
    ("park|world|land|hills|wonders|aquarium", "THEME_PARK"),
    ("pass|viewpoint|lookout|deo", "VIEWPOINT"),
)
_KEYWORD_CATEGORY = tuple((re.compile(rf"\b({words})\b"), code) for words, code in _KEYWORDS)
_CRAFT = re.compile(r"\b(pottery|silk|gom|lua|carpentry|moc|craft|nghe)\b")


# ---- Parsing ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Listing:
    lang: str
    page: str
    type: str
    name: str
    section: str
    params: Mapping[str, str]

    def get(self, key: str) -> str:
        return str(self.params.get(key) or "").strip()

    @property
    def lat_lng(self) -> tuple[float, float] | None:
        try:
            lat, lng = float(self.get("lat")), float(self.get("long"))
        except ValueError:
            return None
        if not (-90 <= lat <= 90 and -180 <= lng <= 180) or (lat == 0 and lng == 0):
            return None
        return lat, lng

    @property
    def lastedit(self) -> date | None:
        try:
            return date.fromisoformat(self.get("lastedit")[:10])
        except ValueError:
            return None

    @property
    def content(self) -> str:
        return wikitext_to_plain(self.get("content"))

    @property
    def plain_name(self) -> str:
        return wikitext_to_plain(self.name)

    @property
    def plain_alt(self) -> str:
        return wikitext_to_plain(self.get("alt"))

    @property
    def key(self) -> str:
        return f"{self.lang}:{self.page}#{fold_words(self.plain_name)}"


@dataclass(frozen=True)
class WikivoyagePage:
    lang: str
    title: str
    revid: int
    wikitext: str

    @property
    def url(self) -> str:
        return PAGE_URL.format(lang=self.lang, title=quote(self.title.replace(" ", "_")))

    @property
    def revision_url(self) -> str:
        return REVISION_URL.format(
            lang=self.lang, title=quote(self.title.replace(" ", "_")), revid=self.revid
        )


def _split_params(body: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    index = 0
    while index < len(body):
        pair = body[index : index + 2]
        if pair in ("{{", "[["):
            depth += 1
            current.append(pair)
            index += 2
            continue
        if pair in ("}}", "]]"):
            depth -= 1
            current.append(pair)
            index += 2
            continue
        char = body[index]
        if char == "|" and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
        index += 1
    parts.append("".join(current))
    return parts


def _template_end(text: str, start: int) -> int:
    """Index just after the ``}}`` closing the template opened at ``start`` (brace depth)."""
    depth = 0
    index = start
    while index < len(text):
        if text.startswith("{{", index):
            depth += 1
            index += 2
        elif text.startswith("}}", index):
            depth -= 1
            index += 2
            if depth == 0:
                return index
        else:
            index += 1
    return len(text)


_TEMPLATE_START = re.compile(r"\{\{\s*([^|{}]+?)\s*\|", re.UNICODE)
_HEADING = re.compile(r"^(==+)\s*(.*?)\s*\1\s*$", re.MULTILINE)


def parse_listings(wikitext: str, *, lang: str = "en", page: str = "") -> list[Listing]:
    """Listing templates with their parameters and the nearest heading above them."""
    headings = [(m.start(), m.group(2)) for m in _HEADING.finditer(wikitext)]
    listings: list[Listing] = []
    position = 0
    while True:
        match = _TEMPLATE_START.search(wikitext, position)
        if match is None:
            break
        start = match.start()
        end = _template_end(wikitext, start)
        position = max(end, match.end())
        kind = LISTING_TYPES.get(match.group(1).strip().lower())
        if kind is None:
            if match.group(1).strip().lower() in SKIPPED_TYPES:
                continue
            position = match.end()  # not a listing: look inside it too
            continue
        params: dict[str, str] = {}
        for part in _split_params(wikitext[start + 2 : end - 2])[1:]:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip().lower()
            params[_VI_PARAMS.get(key, key)] = value.strip()
        name = params.get("name", "")
        if not wikitext_to_plain(name):
            continue
        section = ""
        for offset, heading in headings:
            if offset < start:
                section = heading
        listings.append(Listing(lang, page, kind, name, section, params))
    return listings


_REF = re.compile(r"<ref[^>]*?/>|<ref[^>]*>.*?</ref>", re.DOTALL | re.IGNORECASE)
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML = re.compile(r"<[^>]+>")
_FILE_LINK = re.compile(
    r"\[\[(?:File|Image|Tập tin|Hình):[^\[\]]*(?:\[\[[^\]]*\]\][^\[\]]*)*\]\]", re.IGNORECASE
)
_WIKI_LINK = re.compile(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]")
_EXT_LINK = re.compile(r"\[(?:https?:)?//[^\s\]]+\s*([^\]]*)\]")
_ENTITIES = {"&nbsp;": " ", "&amp;": "&", "&ndash;": "–", "&mdash;": "—", "&quot;": '"'}


def _strip_templates(text: str) -> str:
    out: list[str] = []
    index = 0
    while True:
        start = text.find("{{", index)
        if start < 0:
            out.append(text[index:])
            break
        out.append(text[index:start])
        index = _template_end(text, start)
    return "".join(out)


def wikitext_to_plain(text: str) -> str:
    """Strip wiki markup: links → their label, bold/italic, templates, refs, HTML; collapse
    whitespace. The words are unchanged (the only adaptation of CC BY-SA text)."""
    value = _COMMENT.sub("", text or "")
    value = _REF.sub("", value)
    value = _FILE_LINK.sub("", value)
    value = _strip_templates(value)
    value = _WIKI_LINK.sub(r"\1", value)
    value = _EXT_LINK.sub(r"\1", value)
    value = value.replace("'''", "").replace("''", "")
    value = _HTML.sub("", value)
    for entity, replacement in _ENTITIES.items():
        value = value.replace(entity, replacement)
    return " ".join(value.split())


def category_for(listing: Listing) -> str | None:
    """Gonarra category of a listing, or None when it is not a trip stop."""
    name = fold_words(f"{listing.plain_name} {listing.plain_alt}")
    content = fold_words(listing.content)
    if is_not_a_stop_name(listing.plain_name):
        return None
    if _VILLAGE.search(name) and listing.type in ("see", "do", "buy", "listing"):
        return "CRAFT_VILLAGE" if _CRAFT.search(name) else None
    if listing.type == "eat":
        return "MARKET" if _MARKET.search(name) else "FOOD"
    if listing.type == "drink":
        return "CAFE" if _CAFE.search(name) or _CAFE.search(content[:80]) else "NIGHTLIFE"
    if listing.type == "buy":
        if _SKIP_BUY.search(name):
            return None
        return "MARKET" if _MARKET.search(name) else None
    if listing.type in ("see", "do", "listing"):
        if _MARKET.search(name):
            return "MARKET"
        for pattern, category in _KEYWORD_CATEGORY:
            if pattern.search(name):
                return category
    return None


_DAILY_RANGE = re.compile(
    r"(?:daily|every ?day|hằng ngày|mo-su)?[:,]?\s*"
    r"(\d{1,2})[:.h](\d{2})\s*(?:-|–|to)\s*(\d{1,2})[:.h](\d{2})",
    re.IGNORECASE,
)


def parse_hours(raw: str) -> dict[str, Any] | None:
    """A conservative subset: one daily time range ("06:00-21:00", "daily 7:30–17:00"), or an
    OSM-syntax value. Everything else is UNKNOWN."""
    text = wikitext_to_plain(raw).strip()
    if not text:
        return None
    simple = _DAILY_RANGE.fullmatch(text)
    if simple:
        opens = f"{int(simple.group(1)):02d}:{simple.group(2)}"
        closes = f"{int(simple.group(3)):02d}:{simple.group(4)}"
        parsed = parse_osm_opening_hours(f"Mo-Su {opens}-{closes}")
    else:
        parsed = parse_osm_opening_hours(text)
    if parsed is None:
        return None
    parsed["text"] = text
    return parsed


def section_chunks(page: WikivoyagePage) -> list[tuple[str, str, str]]:
    """``(section code, heading, text)`` for the intro and the mapped level-2 sections, split
    at paragraph and sentence boundaries into pieces of at most ``MAX_CHUNK_CHARS``."""
    text = page.wikitext
    pieces: list[tuple[str, str, str]] = []
    heads = [m for m in _HEADING.finditer(text) if len(m.group(1)) == 2]
    blocks: list[tuple[str, str, str]] = []
    intro_end = heads[0].start() if heads else len(text)
    blocks.append(("CITY_OVERVIEW", "", text[:intro_end]))
    for index, head in enumerate(heads):
        code = SECTION_MAP.get(fold_words(head.group(2)))
        if code is None:
            continue
        end = heads[index + 1].start() if index + 1 < len(heads) else len(text)
        blocks.append((code, head.group(2), text[head.end() : end]))
    for code, heading, body in blocks:
        body = _HEADING.sub("\n\n", body)
        paragraphs = [wikitext_to_plain(p) for p in re.split(r"\n\s*\n|\n(?=[*#])", body)]
        paragraphs = [p.lstrip("*# ").strip() for p in paragraphs]
        current = ""
        for paragraph in (p for p in paragraphs if len(p) >= 40):
            for sentence in _sentences(paragraph):
                if current and len(current) + 1 + len(sentence) > MAX_CHUNK_CHARS:
                    pieces.append((code, heading, current))
                    current = ""
                current = f"{current} {sentence}".strip()
        if len(current) >= 80:
            pieces.append((code, heading, current))
    return pieces


def _sentences(paragraph: str) -> list[str]:
    if len(paragraph) <= MAX_CHUNK_CHARS:
        return [paragraph]
    parts = re.split(r"(?<=[.!?])\s+", paragraph)
    out: list[str] = []
    for part in parts:
        while len(part) > MAX_CHUNK_CHARS:
            out.append(part[:MAX_CHUNK_CHARS])
            part = part[MAX_CHUNK_CHARS:]
        if part:
            out.append(part)
    return out


# ---- Fetching -----------------------------------------------------------------------------


class _Throttle:
    def __init__(self, delay_s: float) -> None:
        self.delay_s = delay_s
        self._last = 0.0

    async def wait(self) -> None:
        pause = self._last + self.delay_s - time.monotonic()
        if pause > 0:
            await asyncio.sleep(pause)
        self._last = time.monotonic()


def _cache_path(cache_dir: Path, lang: str, title: str) -> Path:
    return cache_dir / f"{lang}-{title.replace(' ', '_').replace('/', '_')}.json"


def page_from_body(lang: str, body: Mapping[str, Any]) -> WikivoyagePage | None:
    parse = body.get("parse")
    if not isinstance(parse, Mapping):
        return None
    wikitext = parse.get("wikitext")
    if isinstance(wikitext, Mapping):  # formatversion=1
        wikitext = wikitext.get("*")
    if not wikitext or parse.get("revid") is None:
        return None
    return WikivoyagePage(lang, str(parse.get("title")), int(parse["revid"]), str(wikitext))


async def fetch_page(
    client: httpx.AsyncClient,
    lang: str,
    title: str,
    *,
    throttle: _Throttle,
    cache_dir: Path | None = DEFAULT_CACHE_DIR,
    refresh: bool = False,
) -> WikivoyagePage | None:
    """One page (cached ``CACHE_TTL_S``); None when it does not exist."""
    cached = _cache_path(cache_dir, lang, title) if cache_dir is not None else None
    if cached is not None and cached.exists() and not refresh:
        if time.time() - cached.stat().st_mtime < CACHE_TTL_S:
            return page_from_body(lang, json.loads(cached.read_text(encoding="utf-8")))
    params = {
        "action": "parse",
        "page": title,
        "prop": "wikitext|revid",
        "redirects": "1",
        "format": "json",
        "formatversion": "2",
        "maxlag": "5",
    }
    for attempt in range(MAX_ATTEMPTS):
        await throttle.wait()
        response = await client.get(
            API_URL.format(lang=lang), params=params, headers={"User-Agent": USER_AGENT}
        )
        busy = (
            response.status_code in (429, 503) or "too many requests" in response.text[:500].lower()
        )
        if busy or '"code":"maxlag"' in response.text[:200]:
            await asyncio.sleep(throttle.delay_s * (2**attempt))
            continue
        response.raise_for_status()
        body = response.json()
        if "error" in body:
            return None
        if cached is not None:
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        return page_from_body(lang, body)
    raise httpx.HTTPError(f"wikivoyage {lang}:{title} still rate-limited after retries")


async def fetch_pages(
    *,
    client: httpx.AsyncClient | None = None,
    cache_dir: Path | None = DEFAULT_CACHE_DIR,
    refresh: bool = False,
    delay_s: float = REQUEST_DELAY_S,
    pages: Mapping[str, Sequence[str]] = PAGES,
) -> list[WikivoyagePage]:
    own = client is None
    http = client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    throttle = _Throttle(delay_s)
    result: list[WikivoyagePage] = []
    try:
        for lang, titles in pages.items():
            for title in titles:
                try:
                    page = await fetch_page(
                        http, lang, title, throttle=throttle, cache_dir=cache_dir, refresh=refresh
                    )
                except httpx.HTTPError as exc:
                    logger.warning("wikivoyage fetch failed lang=%s error=%s", lang, exc)
                    continue
                if page is not None:
                    result.append(page)
    finally:
        if own:
            await http.aclose()
    return result


# ---- Matching -----------------------------------------------------------------------------


@dataclass
class KnownPlace:
    place_id: uuid.UUID
    category: str | None
    lat: float
    lng: float
    cores: set[str] = field(default_factory=set)
    qid: str | None = None


async def known_places(session: AsyncSession, city_id: uuid.UUID) -> list[KnownPlace]:
    places: dict[uuid.UUID, KnownPlace] = {}
    for place in (
        await session.scalars(
            select(Place).where(Place.city_id == city_id, Place.workflow_state != "RETIRED")
        )
    ).all():
        point = parse_point(place.location)
        if point is None:
            continue
        places[place.id] = KnownPlace(
            place.id, place.category_code, point.latitude, point.longitude
        )
    rows = (
        await session.execute(
            select(
                ImportRecord.place_id, ImportRecord.raw_name, ImportRecord.allowed_payload
            ).where(
                ImportRecord.place_id.in_(list(places)),
                ImportRecord.validation_status == "ACCEPTED",
            )
        )
    ).all()
    for row in rows:
        known = places[row[0]]
        names: list[Any] = [row[1], *(dict(row[2] or {}).get("name") or {}).values()]
        for name in names:
            core = name_core(str(name)) if name else ""
            if core:
                known.cores.add(core)
    wikidata_id = await provider_id_for(session, WIKIDATA_KEY)
    if wikidata_id is not None:
        for place_id, upstream in (
            await session.execute(
                select(ExternalPlaceIdentity.place_id, ExternalPlaceIdentity.upstream_id).where(
                    ExternalPlaceIdentity.data_provider_id == wikidata_id,
                    ExternalPlaceIdentity.review_state != "REJECTED",
                )
            )
        ).all():
            if place_id in places:
                places[place_id].qid = str(upstream)
    return list(places.values())


def _similar(a: str, b: str) -> float:
    from difflib import SequenceMatcher

    return 1.0 if a == b else SequenceMatcher(None, a, b).ratio()


_MATCH_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"FOOD", "CAFE", "NIGHTLIFE", "MARKET"}),
    frozenset({"MUSEUM", "HERITAGE", "RELIGIOUS_SITE"}),
    frozenset({"BEACH", "NATURE", "VIEWPOINT", "THEME_PARK"}),
    frozenset({"CRAFT_VILLAGE"}),
)


def _match_compatible(listing_category: str | None, place_category: str | None) -> bool:
    """A name match must not cross place types ("Cam Pho Communal House" is not "Chợ Cẩm Phô")."""
    if listing_category is None or place_category is None:
        return True
    return any(listing_category in g and place_category in g for g in _MATCH_GROUPS)


def match_listing(
    listing: Listing, places: Sequence[KnownPlace], category: str | None
) -> KnownPlace | None:
    qid = listing.get("wikidata")
    if qid:
        for place in places:
            if place.qid == qid:
                return place
    alt = listing.plain_alt
    names = (listing.plain_name, alt, vietnamese_alt(alt) if alt else None)
    cores = {c for c in (name_core(n) for n in names if n) if c}
    if not cores:
        return None
    # An activity ("Ride a motorbike up the Hai Van Pass") describes a place only through its QID.
    if listing.type == "do":
        return None
    threshold = 0.85
    places = [p for p in places if _match_compatible(category, p.category)]
    point = listing.lat_lng
    if point is not None:
        radius = max(RADIUS_M.get(category or "", 150.0), 150.0)
        best: tuple[float, KnownPlace] | None = None
        for place in places:
            distance = distance_m(point[0], point[1], place.lat, place.lng)
            if distance > max(radius, EXACT_NAME_RADIUS_M):
                continue
            score = max((_similar(a, b) for a in cores for b in place.cores), default=0.0)
            if distance > radius and score < 1.0:
                continue
            if score >= threshold and (best is None or score > best[0]):
                best = (score, place)
        return best[1] if best else None
    centre = PAGE_CENTRES.get(listing.page)
    if centre is None:
        return None
    hits = [
        place
        for place in places
        if cores & place.cores
        and distance_m(centre[0], centre[1], place.lat, place.lng) <= NO_COORD_MATCH_RADIUS_M
    ]
    return hits[0] if len(hits) == 1 else None


async def _created_by_wikivoyage(
    session: AsyncSession, place_id: uuid.UUID, provider_id: uuid.UUID
) -> bool:
    """True when every identity of the place is a Wikivoyage listing (a draft we created)."""
    other = await session.scalar(
        select(ExternalPlaceIdentity.id)
        .where(
            ExternalPlaceIdentity.place_id == place_id,
            ExternalPlaceIdentity.data_provider_id != provider_id,
        )
        .limit(1)
    )
    return other is None


# ---- Staging ------------------------------------------------------------------------------


@dataclass
class WikivoyageReport(RunReport):
    pages: int = 0
    listings: int = 0
    matched: int = 0
    new_drafts: int = 0
    skipped_not_a_stop: int = 0
    skipped_no_text_or_coords: int = 0
    facts_dropped_stale: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    city_chunks: CityChunkReport | None = None


def vietnamese_alt(alt: str) -> str | None:
    """The Vietnamese part of an ``alt`` ("Hoi An Market (Chợ Hội An)" -> "Chợ Hội An")."""
    for part in re.split(r"[()/;,]| or ", alt):
        part = " ".join(part.split())
        if part and has_vietnamese_diacritics(part):
            return part
    return None


def _payload(listing: Listing, category: str | None) -> dict[str, Any]:
    name = listing.plain_name
    alt = listing.plain_alt
    vi_alt = vietnamese_alt(alt) if alt else None
    names: dict[str, str] = {}
    aliases: dict[str, list[str]] = {}
    if listing.type == "do" and category != "CRAFT_VILLAGE":
        pass  # an activity title ("Ride a motorbike up …") is not the place's name
    elif listing.lang == "en":
        names["en"] = name
        if vi_alt:
            names["vi"] = vi_alt
            aliases["vi"] = [vi_alt]
        elif alt and fold_words(alt) != fold_words(name):
            aliases["en"] = [alt]
    elif has_vietnamese_diacritics(name):
        names["vi"] = name
        aliases["vi"] = [name]
    payload: dict[str, Any] = {
        "id": listing.key,
        "name": names,
        "aliases": aliases,
        "category": category,
        "listing_type": listing.type,
        "lastedit": listing.lastedit.isoformat() if listing.lastedit else None,
        "website": listing.get("url") or None,
    }
    point = listing.lat_lng
    if point is not None:
        payload["location"] = {"lat": point[0], "lng": point[1]}
    if listing.lang == "en" and listing.content:
        payload["description"] = {"en": listing.content}
    facts: dict[str, Any] = {}
    fresh = listing.lastedit is not None and listing.lastedit >= date(2023, 1, 1)
    if fresh:
        hours = parse_hours(listing.get("hours"))
        if hours is not None:
            facts["OPENING_HOURS"] = {"value": hours}
        price = wikitext_to_plain(listing.get("price"))
        if price and listing.type in ("see", "do"):
            facts["ADMISSION_PRICE"] = {"value": {"text": price}}
        address = wikitext_to_plain(listing.get("address"))
        if address and has_vietnamese_diacritics(address):
            facts["ADDRESS_VI"] = {"value": {"text": address}}
    payload["facts"] = facts
    return payload


def _merge(primary: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    """Merge a second listing of the same place (e.g. a market in "Buy" and "Eat")."""
    merged = dict(primary)
    for key in ("name", "aliases"):
        combined = dict(other.get(key) or {})
        combined.update(primary.get(key) or {})
        merged[key] = combined
    if not merged.get("description") and other.get("description"):
        merged["description"] = other["description"]
    facts = dict(other.get("facts") or {})
    facts.update(primary.get("facts") or {})
    merged["facts"] = facts
    if not merged.get("location") and other.get("location"):
        merged["location"] = other["location"]
    return merged


async def import_wikivoyage(
    session: AsyncSession,
    *,
    city_code: str,
    city_chunks: bool = True,
    dry_run: bool = False,
    cache_dir: Path | None = DEFAULT_CACHE_DIR,
    refresh: bool = False,
    client: httpx.AsyncClient | None = None,
) -> WikivoyageReport:
    await require_active_policy(session, PROVIDER_KEY)  # refuse before any network call
    pages = await fetch_pages(client=client, cache_dir=cache_dir, refresh=refresh)
    return await stage_pages(
        session, city_code=city_code, pages=pages, city_chunks=city_chunks, dry_run=dry_run
    )


async def stage_pages(
    session: AsyncSession,
    *,
    city_code: str,
    pages: Sequence[WikivoyagePage],
    city_chunks: bool = True,
    dry_run: bool = False,
) -> WikivoyageReport:
    policy = await require_active_policy(session, PROVIDER_KEY)
    city = await load_city(session, city_code)
    report = WikivoyageReport(provider_key=PROVIDER_KEY, pages=len(pages))
    checksum = sha256_hex(
        canonical_json(sorted([p.lang, p.title, p.revid, IMPORTER_VERSION] for p in pages))
    )
    places = await known_places(session, city.id)
    areas = load_areas(city_code)

    # Group listings per matched place (or per listing for new drafts).
    staged: dict[str, tuple[Listing, KnownPlace | None, dict[str, Any], WikivoyagePage]] = {}
    for page in pages:
        for listing in parse_listings(page.wikitext, lang=page.lang, page=page.title):
            report.listings += 1
            category = category_for(listing)
            matched = match_listing(listing, places, category)
            if matched is None and category is None:
                report.skipped_not_a_stop += 1
                continue
            payload = _payload(listing, category or (matched.category if matched else None))
            if listing.get("hours") and listing.lastedit and listing.lastedit < date(2023, 1, 1):
                report.facts_dropped_stale += 1
            if matched is not None:
                key = f"place:{matched.place_id}"
            else:
                point = listing.lat_lng
                if (
                    listing.lang != "en"
                    or (listing.type == "do" and category != "CRAFT_VILLAGE")
                    or point is None
                    or len(listing.content) < MIN_NEW_CONTENT_CHARS
                    or not await inside_city(session, city.id, point[1], point[0])
                ):
                    report.skipped_no_text_or_coords += 1
                    continue
                key = listing.key
            previous = staged.get(key)
            if previous is None:
                staged[key] = (listing, matched, payload, page)
            else:
                first = previous[2]
                longer = len((payload.get("description") or {}).get("en", "")) > len(
                    (first.get("description") or {}).get("en", "")
                )
                primary, other = (payload, first) if longer else (first, payload)
                keep = (listing, matched, primary, page) if longer else previous
                staged[key] = (keep[0], keep[1], _merge(primary, other), keep[3])

    if dry_run:
        for _listing, matched, payload, _page in staged.values():
            report.record_count += 1
            report.matched += matched is not None
            report.new_drafts += matched is None
            category = payload.get("category") or "-"
            report.by_category[category] = report.by_category.get(category, 0) + 1
        return report

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
        lang: await get_or_create_source(
            session,
            data_provider_id=policy.provider_id,
            publisher=f"Wikivoyage ({lang})",
            source_kind="REFERENCE",
            license_code=LICENSE_CODE,
            attribution_text=ATTRIBUTION.format(lang=lang),
            homepage_url=f"https://{lang}.wikivoyage.org/",
        )
        for lang in sorted({p.lang for p in pages} | {"en"})
    }
    revisions = {
        (page.lang, page.title): await get_or_create_revision(
            session,
            source_id=sources[page.lang].id,
            locator=page.revision_url,
            content_sha256=sha256_hex(page.wikitext),
            title=f"Wikivoyage contributors, '{page.title}' (revision {page.revid})",
        )
        for page in pages
    }
    used_upstream_ids: set[str] = set()
    for _key, (listing, matched, payload, page) in sorted(staged.items()):
        revision = revisions[(page.lang, page.title)]
        point = listing.lat_lng
        place_id: uuid.UUID | None = matched.place_id if matched else None
        upstream_id = listing.key
        if upstream_id in used_upstream_ids:  # one name listed twice on a page, two places
            upstream_id = f"{upstream_id}@{listing.get('lat')},{listing.get('long')}"
        used_upstream_ids.add(upstream_id)
        if place_id is None:
            existing = await place_for_identity(session, policy.provider_id, upstream_id)
            if existing is not None and not await _created_by_wikivoyage(
                session, existing, policy.provider_id
            ):
                existing = None  # an old name match that no longer holds: start a new draft
            if existing is None:
                assert point is not None
                category = payload.get("category")
                place = await create_place(
                    session,
                    city_id=city.id,
                    slug=await free_slug(session, city.id, listing.plain_name),
                    lng=point[1],
                    lat=point[0],
                    category_code=category,
                    area_code=assign_area(areas, point[1], point[0]),
                )
                existing = place.id
                report.created_places += 1
                report.new_drafts += 1
            place_id = existing
        else:
            report.matched += 1
        filtered = policy.filter_payload(payload)
        filtered[PROVENANCE_KEY] = {
            "source_revision_id": str(revision.id),
            "fact_source_revision_ids": {code: str(revision.id) for code in payload["facts"]},
            "page_url": page.url,
            "locale": page.lang,
        }
        await link_identity(
            session,
            place_id=place_id,
            provider_id=policy.provider_id,
            upstream_id=upstream_id,
            release=str(page.revid),
            match_method="EXACT_ID" if listing.get("wikidata") else "NAME_AND_DISTANCE",
        )
        lat, lng = point if point is not None else (matched.lat, matched.lng) if matched else (0, 0)
        add_record(
            session,
            run,
            upstream_id=upstream_id,
            raw_name=listing.plain_name,
            upstream_category=payload.get("category"),
            lng=lng,
            lat=lat,
            payload=filtered,
            place_id=place_id,
            match_state="MATCHED",
        )
        report.record_count += 1
        report.accepted += 1
        category = payload.get("category") or "-"
        report.by_category[category] = report.by_category.get(category, 0) + 1

    # Identities of listings no longer matched to that place are removed (re-matched each run).
    for identity in (
        await session.scalars(
            select(ExternalPlaceIdentity).where(
                ExternalPlaceIdentity.data_provider_id == policy.provider_id
            )
        )
    ).all():
        if identity.upstream_id not in used_upstream_ids:
            await session.delete(identity)
    await session.flush()
    if city_chunks:
        chunks = [
            CityChunk(
                locale=page.lang,
                section=code,
                content=f"{page.title}{' — ' + heading if heading else ''}: {text}"[:4000],
                source_revision_id=revisions[(page.lang, page.title)].id,
            )
            for page in pages
            if page.title in CITY_CHUNK_PAGES
            for code, heading, text in section_chunks(page)
        ]
        report.city_chunks = await stage_city_chunks(session, city.id, chunks)
    finish_run(run, report)
    await session.commit()
    return report
