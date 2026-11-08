"""OpenStreetMap importer: opening_hours parser, tag mapping, element parsing, Overpass client."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from app.ingestion.categories import map_osm_tags
from app.ingestion.common import USER_AGENT
from app.ingestion.osm import (
    OVERPASS_ENDPOINTS,
    build_query,
    commons_file_name,
    fetch_elements,
    parse_elements,
    parse_osm_opening_hours,
)

BBOX = (107.2, 14.9, 108.95, 16.35)
ALL_DAYS = [str(day) for day in range(1, 8)]


def _weekly(raw: str) -> dict[str, list[list[str]]] | None:
    parsed = parse_osm_opening_hours(raw)
    if parsed is None:
        return None
    assert parsed["text"] == raw.strip()
    return parsed["weekly"]  # type: ignore[no-any-return]


def test_opening_hours_weekday_and_weekend_rules() -> None:
    weekly = _weekly("Mo-Fr 08:00-17:00; Sa,Su 07:00-18:00")
    assert weekly == {
        **{str(day): [["08:00", "17:00"]] for day in range(1, 6)},
        "6": [["07:00", "18:00"]],
        "7": [["07:00", "18:00"]],
    }


def test_opening_hours_24_7_and_whole_week() -> None:
    assert _weekly("24/7") == {day: [["00:00", "24:00"]] for day in ALL_DAYS}
    assert _weekly("Mo-Su 07:00-22:00") == {day: [["07:00", "22:00"]] for day in ALL_DAYS}
    assert _weekly("07:00-22:30") == {day: [["07:00", "22:30"]] for day in ALL_DAYS}
    assert _weekly("Mo-Su 06:00-24:00") == {day: [["06:00", "24:00"]] for day in ALL_DAYS}


def test_opening_hours_day_lists_intervals_and_off() -> None:
    assert _weekly("Mo,We,Fr 08:00-11:30,13:30-17:00; Tu off; Th closed") == {
        "1": [["08:00", "11:30"], ["13:30", "17:00"]],
        "2": [],
        "3": [["08:00", "11:30"], ["13:30", "17:00"]],
        "4": [],
        "5": [["08:00", "11:30"], ["13:30", "17:00"]],
    }
    # Spaces around separators and single-digit hours are tolerated.
    assert _weekly("Mo - Fr 8:00 - 17:00") == {str(d): [["08:00", "17:00"]] for d in range(1, 6)}


def test_opening_hours_later_rule_overrides_and_wraps() -> None:
    weekly = _weekly("Mo-Su 08:00-22:00; Tu off")
    assert weekly is not None and weekly["2"] == [] and weekly["1"] == [["08:00", "22:00"]]
    assert set(_weekly("Fr-Mo 09:00-17:00") or {}) == {"1", "5", "6", "7"}


def test_opening_hours_days_not_named_stay_unknown() -> None:
    assert set(_weekly("Mo-Fr 08:00-17:00") or {}) == {"1", "2", "3", "4", "5"}


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "PH off",
        "Mo-Fr 08:00-17:00; PH off",
        "Mo-Su sunrise-sunset",
        "Jan-Mar Mo-Fr 08:00-17:00",
        "week 1-20 Mo-Fr 08:00-17:00",
        "Mo-Su 10:00-02:00",  # overnight: not representable, never guessed
        "Mo-Fr 08:00+",
        'Mo-Fr 08:00-17:00 "by appointment"',
        "Mo-Fr",
        "Mo-Fr 08:00-12:00,11:00-17:00",  # overlapping
        "Mo-Fr 17:00-08:00",
        "open daily",
        "Mo-Fr 08:00-17:00 || PH off",
    ],
)
def test_opening_hours_unsupported_gives_no_fact(raw: str) -> None:
    assert parse_osm_opening_hours(raw) is None


@pytest.mark.parametrize(
    ("tags", "category"),
    [
        ({"tourism": "museum"}, "MUSEUM"),
        ({"tourism": "gallery"}, "MUSEUM"),
        ({"tourism": "viewpoint"}, "VIEWPOINT"),
        ({"tourism": "theme_park"}, "THEME_PARK"),
        ({"leisure": "water_park"}, "THEME_PARK"),
        ({"historic": "temple", "amenity": "place_of_worship"}, "RELIGIOUS_SITE"),
        ({"historic": "ruins"}, "HERITAGE"),
        ({"historic": "boundary_stone"}, None),
        ({"amenity": "restaurant", "religion": "buddhist"}, "FOOD"),
        ({"amenity": "cafe"}, "CAFE"),
        ({"amenity": "marketplace"}, "MARKET"),
        ({"shop": "mall"}, "MARKET"),
        ({"leisure": "park"}, "NATURE"),
        ({"natural": "beach"}, "BEACH"),
        ({"natural": "peak"}, "NATURE"),
        ({"natural": "cave_entrance"}, "NATURE"),
        ({"tourism": "attraction"}, None),  # ambiguous on its own: skipped
        ({"tourism": "attraction", "man_made": "bridge"}, "VIEWPOINT"),
        ({"tourism": "attraction", "religion": "buddhist"}, "RELIGIOUS_SITE"),
        ({"tourism": "hotel"}, None),
        ({"religion": "buddhist"}, None),  # qualifier alone never imports
    ],
)
def test_osm_category_mapping(tags: dict[str, str], category: str | None) -> None:
    assert map_osm_tags(tags) == category


def test_build_query_uses_south_west_north_east_and_requires_names() -> None:
    query = build_query(BBOX)
    assert query.startswith("[out:json][timeout:180];")
    assert "(14.9,107.2,16.35,108.95)" in query
    assert query.endswith("out center tags;")
    assert query.count('["name"]') == 7
    assert 'nwr["amenity"="place_of_worship"]' in query


def test_commons_file_name_from_osm_tags() -> None:
    assert commons_file_name("File:Chua_Cau.jpg") == "Chua Cau.jpg"
    assert commons_file_name("https://commons.wikimedia.org/wiki/File:A%20b.jpg") == "A b.jpg"
    assert (
        commons_file_name(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Foo.jpg/320px-Foo.jpg"
        )
        == "Foo.jpg"
    )
    assert commons_file_name("https://upload.wikimedia.org/wikipedia/commons/a/ab/Bar.png") == (
        "Bar.png"
    )
    assert commons_file_name("Category:Hoi An") is None
    assert commons_file_name("https://example.com/photo.jpg") is None
    assert commons_file_name(None) is None


OVERPASS_BODY: dict[str, Any] = {
    "elements": [
        {
            "type": "node",
            "id": 2,
            "lat": 15.8771,
            "lon": 108.3262,
            "tags": {
                "name": "Chùa Cầu",
                "name:en": "Japanese Covered Bridge",
                "historic": "monument",
                "wikidata": "Q1091054",
                "opening_hours": "Mo-Su 07:00-21:30",
                "website": "https://hoianworldheritage.org.vn/",
                "wikimedia_commons": "File:Chua Cau.jpg",
            },
        },
        {
            "type": "way",
            "id": 1,
            "center": {"lat": 16.1003, "lon": 108.2779},
            "tags": {
                "name": "Chùa Linh Ứng",
                "amenity": "place_of_worship",
                "religion": "buddhist",
            },
        },
        {"type": "node", "id": 3, "lat": 16.0, "lon": 108.2, "tags": {"amenity": "cafe"}},
        {"type": "way", "id": 4, "tags": {"name": "No centre", "tourism": "museum"}},
        {"type": "node", "id": 5, "lat": 16.0, "lon": 108.2, "tags": {"name": "Hotel X"}},
    ]
}


def test_parse_elements_keeps_named_points_and_maps_fields() -> None:
    elements = parse_elements(OVERPASS_BODY["elements"])
    assert [element.upstream_id for element in elements] == ["node/2", "node/5", "way/1"]
    bridge, hotel, pagoda = elements
    assert bridge.category == "HERITAGE" and hotel.category is None
    assert pagoda.category == "RELIGIOUS_SITE" and (pagoda.lng, pagoda.lat) == (108.2779, 16.1003)
    assert bridge.names == {"vi": "Chùa Cầu", "en": "Japanese Covered Bridge"}
    assert pagoda.names == {"vi": "Chùa Linh Ứng"}  # no name:en → no English name (no translation)
    payload = bridge.payload()
    assert payload["wikidata"] == "Q1091054"
    assert payload["website"] == "https://hoianworldheritage.org.vn/"
    assert payload["wikimedia_commons"] == "File:Chua Cau.jpg"
    assert payload["facts"]["OPENING_HOURS"] == {
        "value": {
            "weekly": {day: [["07:00", "21:30"]] for day in ALL_DAYS},
            "text": "Mo-Su 07:00-21:30",
        },
        "source_url": "https://www.openstreetmap.org/node/2",
    }
    assert pagoda.payload()["facts"] == {}


async def test_fetch_elements_falls_back_to_the_mirror() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.host == "overpass-api.de":
            return httpx.Response(504)
        return httpx.Response(200, json=OVERPASS_BODY)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        elements = await fetch_elements(client, BBOX, backoff_s=0)
    assert len(elements) == 3
    assert [request.url.host for request in seen] == [
        "overpass-api.de",
        "overpass-api.de",
        httpx.URL(OVERPASS_ENDPOINTS[1]).host,
    ]
    assert all(request.headers["user-agent"] == USER_AGENT for request in seen)
    assert "out center tags" in seen[0].url.params["data"]


async def test_fetch_elements_rejects_partial_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = {"remark": "runtime error: Query timed out", "elements": []}
        return httpx.Response(200, content=json.dumps(body).encode())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(RuntimeError):
            await fetch_elements(client, BBOX, backoff_s=0)
