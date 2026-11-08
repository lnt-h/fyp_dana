"""Wikidata linking for OSM-only places and the human (P31=Q5) check (recorded payloads)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.ingestion.common import USER_AGENT
from app.ingestion.wikidata import API_URL, fetch_human_qids, human_qids_from, parse_bindings
from app.ingestion.wikidata_link import (
    LinkCandidate,
    LinkReport,
    distance_m,
    find_backfills,
    find_links,
    is_place_item,
    link_payload,
    match_key,
    radius_for,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _json(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return data


ITEMS = {
    item.qid: item
    for item in parse_bindings(_json("sparql_link_sample.json")["results"]["bindings"])
}


def _candidate(
    slug: str, lng: float, lat: float, *names: str, category: str = "HERITAGE"
) -> LinkCandidate:
    return LinkCandidate(uuid.uuid5(uuid.NAMESPACE_DNS, slug), slug, category, lng, lat, set(names))


def test_match_key_ignores_case_diacritics_punctuation_parentheses_and_city() -> None:
    assert match_key("Chùa Cầu (Hội An)") == "chua cau"
    assert match_key("Minh Huong Temple of Literature, Hoi An") == "minh huong temple of literature"
    assert match_key("NGŨ HÀNH SƠN – Đà Nẵng") == "ngu hanh son"


def test_place_type_check_on_recorded_items() -> None:
    assert is_place_item(ITEMS["Q6755207"])  # mountain range
    assert is_place_item(ITEMS["Q1091054"])  # covered bridge | Buddhist temple in Vietnam
    assert not is_place_item(ITEMS["Q7022659"])  # ward of Vietnam
    assert not is_place_item(ITEMS["Q183421"])  # massacre, war crime: an event


def test_radius_depends_on_category() -> None:
    assert radius_for("NATURE") == 1000.0 and radius_for("BEACH") == 1000.0
    assert radius_for("RELIGIOUS_SITE") == 300.0


def test_links_need_name_distance_and_place_type() -> None:
    marble = _candidate("ngu-hanh-son", 108.2596, 16.0017, "Ngũ Hành Sơn", category="NATURE")
    near_bridge = _candidate("chua-cau-osm", 108.3262, 15.8771, "Chùa Cầu")
    far_pagoda = _candidate("chua-linh-ung-2", 107.9941, 15.9972, "Chùa Linh Ứng")
    other_name = _candidate("hoi-an-x", 108.3262, 15.8771, "Hội quán X")
    links = find_links(
        [marble, near_bridge, far_pagoda, other_name], list(ITEMS.values()), linked_elsewhere={}
    )
    by_slug = {link.slug: link.item.qid for link in links}
    # The ward Q7022659 has the same name but is an administrative unit.
    assert by_slug == {"ngu-hanh-son": "Q6755207", "chua-cau-osm": "Q1091054"}
    # 300 m radius for a non-large category: an item 600 m away is not linked.
    museum = _candidate("ngu-hanh-son-museum", 108.2596, 16.0071, "Ngũ Hành Sơn", category="MUSEUM")
    assert find_links([museum], list(ITEMS.values()), linked_elsewhere={}) == []


def test_qid_on_another_place_is_a_duplicate_and_one_item_one_place() -> None:
    a = _candidate("chua-cau-a", 108.3262, 15.8771, "Chùa Cầu")
    b = _candidate("chua-cau-b", 108.3270, 15.8775, "Japanese Bridge")
    report = LinkReport(provider_key="wikidata")
    links = find_links([a, b], list(ITEMS.values()), linked_elsewhere={}, report=report)
    assert [link.slug for link in links] == ["chua-cau-a"]
    assert report.contested == [("chua-cau-b", "Q1091054")]
    report = LinkReport(provider_key="wikidata")
    owner = uuid.uuid4()
    links = find_links(
        [a], list(ITEMS.values()), linked_elsewhere={"Q1091054": owner}, report=report
    )
    assert links == [] and report.duplicates == [("chua-cau-a", "Q1091054")]


def test_backfill_known_qids_skips_humans_events_and_far_items() -> None:
    temple = _candidate("van-chi-minh-huong", 108.3305, 15.8787, "Văn chỉ Minh Hương")
    mountain = _candidate("ngu-hanh-son", 108.2596, 16.0017, "Ngũ Hành Sơn", category="NATURE")
    vestige = _candidate("son-my-vestige-site", 108.8700, 15.1800, "Khu chứng tích Sơn Mỹ")
    statue = _candidate("kazimierz-kwiatkowski", 108.3290, 15.8780, "Kazimierz Kwiatkowski")
    far = _candidate("far-bridge", 108.40, 15.95, "Chùa Cầu")
    report = LinkReport(provider_key="wikidata")
    links = find_backfills(
        [
            (temple, "Q132483343"),
            (mountain, "Q6755207"),
            (vestige, "Q183421"),
            (statue, "Q11738068"),
            (far, "Q1091054"),
        ],
        list(ITEMS.values()),
        humans={"Q11738068"},
        report=report,
    )
    assert [(link.slug, link.item.qid, link.method) for link in links] == [
        ("ngu-hanh-son", "Q6755207", "OSM_WIKIDATA_TAG"),
        ("van-chi-minh-huong", "Q132483343", "OSM_WIKIDATA_TAG"),
    ]
    assert report.humans == [("kazimierz-kwiatkowski", "Q11738068")]


def test_link_payload_keeps_the_osm_point_and_category() -> None:
    payload = link_payload(ITEMS["Q6755207"])
    assert "location" not in payload and "category" not in payload
    assert payload["id"] == "Q6755207"
    assert payload["sitelinks"] == {"vi": "Ngũ Hành Sơn", "en": "Ngũ Hành Sơn"}
    assert payload["image"] == ["Marble Mountains View 3.JPG"]


def test_human_qids_from_recorded_wbgetentities() -> None:
    assert human_qids_from(_json("wikidata_wbgetentities_p31.json")) == {"Q11738068"}


async def test_fetch_human_qids_batches_and_tolerates_errors() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        ids = request.url.params["ids"].split("|")
        if "Q11738068" in ids:
            return httpx.Response(200, json=_json("wikidata_wbgetentities_p31.json"))
        return httpx.Response(200, json={"error": {"code": "no-such-entity"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        humans = await fetch_human_qids(
            client, ["Q6755207", "Q11738068", "bad", "Q99999999999"], batch_size=2
        )
    assert humans == {"Q11738068"}
    assert len(requests) == 2
    assert all(str(r.url).startswith(API_URL) for r in requests)
    assert all(r.headers["user-agent"] == USER_AGENT for r in requests)
    assert requests[0].url.params["props"] == "claims"


@pytest.mark.parametrize(("a", "b"), [((108.26, 16.0), (108.2596, 16.0017))])
def test_distance_is_metres(a: tuple[float, float], b: tuple[float, float]) -> None:
    assert 150 < distance_m(*a, *b) < 250
