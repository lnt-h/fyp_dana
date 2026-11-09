"""Commons geosearch and full-text search as third/fourth photo sources (recorded payloads)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import httpx

from app.catalog.places import commons_thumb_url
from app.ingestion.commons import (
    CommonsFile,
    PublishedPlace,
    Rejected,
    choose_found,
    geo_match,
    geosearch,
    names_other_place,
    parse_geosearch,
    parse_imageinfo,
    parse_search,
    search_files,
    search_match,
    search_query,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _json(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return data


def _files() -> dict[str, CommonsFile | Rejected]:
    pages = _json("commons_imageinfo_categories.json")["query"]["pages"]
    return {str(page["title"]): parse_imageinfo(page) for page in pages}


def _place(
    slug: str, vi: str, en: str, lng: float, lat: float, category: str = "RELIGIOUS_SITE"
) -> PublishedPlace:
    return PublishedPlace(
        uuid.uuid5(uuid.NAMESPACE_DNS, slug), slug, category, lng, lat, {"vi": vi, "en": en}
    )


PHUOC_LAM = _place("chua-phuoc-lam", "Chùa Phước Lâm", "Phuoc Lam Pagoda", 108.3335, 15.8869)
BRIDGE = _place(
    "japanese-bridge", "Chùa Cầu", "Japanese Covered Bridge", 108.3262, 15.8771, "HERITAGE"
)
NEAR_BRIDGE = _place("nha-co-x", "Nhà cổ Thử", "Test Old House", 108.3262, 15.8771, "MUSEUM")


def test_parse_recorded_geosearch_and_search() -> None:
    geo = parse_geosearch(_json("commons_geosearch.json"))
    assert geo[0] == ("File:Hội An, Chùa Cầu, 2020-01 CN-04.jpg", 0.4)
    assert all(title.startswith("File:") for title, _ in geo)
    assert parse_search(_json("commons_search.json"))[0] == "File:Phuoc Lam Pagoda 3.jpg"


def test_imageinfo_keeps_description_categories_and_gps_for_matching() -> None:
    files = _files()
    phuoc = files["File:Phuoc Lam Pagoda 3.jpg"]
    assert isinstance(phuoc, CommonsFile)
    assert phuoc.categories == ("Phuoc Lam Pagoda",)
    assert "hoi an" in phuoc.match_text()
    bridge = files["File:Hội An, Chùa Cầu, 2020-01 CN-04.jpg"]
    assert isinstance(bridge, CommonsFile) and bridge.lat is not None and bridge.lng is not None
    assert "description" not in phuoc.payload()  # matching data is never stored


def test_search_query_quotes_both_names() -> None:
    assert search_query(PHUOC_LAM) == '"Chùa Phước Lâm" OR "Phuoc Lam Pagoda"'
    one_word = _place("x", "Chùa", "Chùa", 108.3, 15.8)
    assert search_query(one_word) is None


def test_search_match_needs_the_name_and_the_area() -> None:
    files = _files()
    phuoc = files["File:Phuoc Lam Pagoda 3.jpg"]
    assert isinstance(phuoc, CommonsFile)
    assert search_match(phuoc, PHUOC_LAM)  # category names it; "Hoi An" in description
    elsewhere = _place("chua-phuoc-lam-hn", "Chùa Phước Lâm", "Phuoc Lam Pagoda", 105.85, 21.03)
    far = CommonsFile(**{**phuoc.__dict__, "lat": 21.03, "lng": 105.85 + 0.5})
    assert not search_match(far, elsewhere)  # GPS more than 2 km from the place
    tiles = files["File:Raffi kojian-hoi an-155621875.jpg"]
    assert isinstance(tiles, CommonsFile) and not search_match(tiles, PHUOC_LAM)


def test_file_naming_another_published_place_is_skipped() -> None:
    files = _files()
    bridge_photo = files["File:Hội An, Chùa Cầu, 2020-01 CN-04.jpg"]
    assert isinstance(bridge_photo, CommonsFile)
    assert names_other_place(bridge_photo, NEAR_BRIDGE, [BRIDGE, NEAR_BRIDGE])
    assert not names_other_place(bridge_photo, BRIDGE, [BRIDGE, NEAR_BRIDGE])


def test_choose_found_orders_search_then_nearest_geosearch_and_caps() -> None:
    files = _files()
    geo = parse_geosearch(_json("commons_geosearch.json"))
    chosen = choose_found(
        NEAR_BRIDGE,
        geo_hits=geo,
        search_hits=[],
        query=None,
        files=files,
        others=[BRIDGE, NEAR_BRIDGE],
    )
    # Geosearch is proximity only: the bridge photo names another published place and the
    # tile photo (11.3 m) does not name this place, so neither is auto-accepted.
    assert chosen == []
    chosen = choose_found(
        PHUOC_LAM,
        geo_hits=[],
        search_hits=parse_search(_json("commons_search.json")),
        query=search_query(PHUOC_LAM),
        files=files,
        others=[BRIDGE, PHUOC_LAM],
    )
    assert [title for title, _ in chosen] == ["File:Phuoc Lam Pagoda 3.jpg"]
    assert chosen[0][1]["via"] == "commons_search"


def test_geo_match_requires_the_place_name() -> None:
    files = _files()
    bridge_photo = files["File:Hội An, Chùa Cầu, 2020-01 CN-04.jpg"]
    assert isinstance(bridge_photo, CommonsFile)
    assert geo_match(bridge_photo, BRIDGE)
    assert not geo_match(bridge_photo, NEAR_BRIDGE)
    tiles = files["File:Raffi kojian-hoi an-155621875.jpg"]
    assert isinstance(tiles, CommonsFile) and not geo_match(tiles, NEAR_BRIDGE)


def test_choose_found_accepts_name_matching_geosearch() -> None:
    files = _files()
    chosen = choose_found(
        BRIDGE,
        geo_hits=[("File:Hội An, Chùa Cầu, 2020-01 CN-04.jpg", 0.4)],
        search_hits=[],
        query=None,
        files=files,
        others=[BRIDGE, NEAR_BRIDGE],
    )
    assert chosen == [
        (
            "File:Hội An, Chùa Cầu, 2020-01 CN-04.jpg",
            {"via": "commons_geosearch", "distance_m": 0.4},
        )
    ]


def test_commons_thumb_url_rewrites_sized_thumbnails() -> None:
    hero = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Foo.jpg/1280px-Foo.jpg"
    assert (
        commons_thumb_url(hero)
        == "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Foo.jpg/330px-Foo.jpg"
    )
    assert commons_thumb_url("places/linh-ung.jpg") is None
    assert commons_thumb_url("https://upload.wikimedia.org/wikipedia/commons/a/ab/Foo.jpg") is None


async def test_geosearch_and_search_requests() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        name = (
            "commons_geosearch.json"
            if request.url.params["list"] == "geosearch"
            else "commons_search.json"
        )
        return httpx.Response(200, json=_json(name))

    beach = _place("bai-x", "Bãi biển Thử", "Test Beach", 108.25, 16.05, "BEACH")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        geo = await geosearch(client, beach)
        hits = await search_files(client, '"Chùa Phước Lâm"')
    assert geo and hits
    params = requests[0].url.params
    assert (params["gsradius"], params["gsnamespace"]) == ("500", "6")
    assert params["gscoord"] == "16.05|108.25"
    assert requests[1].url.params["srnamespace"] == "6"
