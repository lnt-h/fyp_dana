"""Wikidata and Wikipedia clients with recorded fixtures (no network: pytest-httpx)."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

import httpx
import pytest
from pytest_httpx import HTTPXMock

from app.ingestion.categories import map_category
from app.ingestion.common import USER_AGENT
from app.ingestion.wikidata import build_query, fetch_items, get_with_retries, parse_bindings
from app.ingestion.wikipedia import (
    PageRequest,
    fetch_summaries,
    parse_summary,
    trim_extract,
)

FIXTURES = Path(__file__).parent / "fixtures"
SPARQL = re.compile(r"https://query\.wikidata\.org/sparql\?.*")
BBOX = (107.2, 14.9, 108.95, 16.35)


def _fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_category_mapping_is_deterministic_and_most_specific() -> None:
    assert map_category(["covered bridge", "tourist attraction"]) == "HERITAGE"
    assert map_category(["Buddhist temple", "mountain"]) == "RELIGIOUS_SITE"
    assert map_category(["Beach"]) == "BEACH"
    assert map_category(["hotel", "commune of Vietnam"]) is None
    assert map_category([]) is None


def test_build_query_uses_the_bbox() -> None:
    query = build_query(BBOX)
    assert '"Point(107.2 14.9)"' in query and '"Point(108.95 16.35)"' in query
    assert "wikibase:box" in query and "skos:altLabel" in query


def test_parse_bindings_maps_classes_and_sitelinks() -> None:
    items = parse_bindings(_fixture("sparql_da_nang.json")["results"]["bindings"])
    by_id = {item.qid: item for item in items}
    assert set(by_id) == {"Q1091054", "Q18277260", "Q55555555"}  # lexeme L123 dropped
    bridge = by_id["Q1091054"]
    assert bridge.category == "HERITAGE"
    assert (bridge.lng, bridge.lat) == (108.32624, 15.87713)
    assert bridge.labels == {"vi": "Chùa Cầu", "en": "Japanese Covered Bridge"}
    assert bridge.sitelinks == {"vi": "Chùa Cầu", "en": "Japanese Covered Bridge"}
    assert bridge.aliases == {"vi": ["Cầu Nhật Bản", "Lai Viễn Kiều"], "en": ["Chua Cau"]}
    assert by_id["Q18277260"].category == "RELIGIOUS_SITE"
    assert by_id["Q18277260"].labels == {"vi": "Chùa Linh Ứng (Sơn Trà)"}
    assert by_id["Q55555555"].category is None  # hotel: unmapped, skipped by the importer


async def test_fetch_items_sends_user_agent_and_parses(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=SPARQL, json=_fixture("sparql_da_nang.json"))
    async with httpx.AsyncClient() as client:
        items = await fetch_items(client, BBOX)
    assert len(items) == 3
    request = httpx_mock.get_requests()[0]
    assert request.headers["user-agent"] == USER_AGENT
    assert "email" not in USER_AGENT.lower() and "@" not in USER_AGENT


async def test_retries_on_429_then_succeeds(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="https://example.test/x", status_code=429)
    httpx_mock.add_response(url="https://example.test/x", status_code=503)
    httpx_mock.add_response(url="https://example.test/x", json={"ok": True})
    async with httpx.AsyncClient() as client:
        response = await get_with_retries(client, "https://example.test/x", backoff_s=0)
    assert response.json() == {"ok": True}
    assert len(httpx_mock.get_requests()) == 3


async def test_retries_give_up(httpx_mock: HTTPXMock) -> None:
    for _ in range(2):
        httpx_mock.add_response(url="https://example.test/y", status_code=500)
    async with httpx.AsyncClient() as client:
        with pytest.raises(httpx.HTTPStatusError):
            await get_with_retries(client, "https://example.test/y", max_attempts=2, backoff_s=0)


def test_parse_summary_and_skip_disambiguation() -> None:
    request = PageRequest(place_id=uuid.uuid4(), locale="en", title="Japanese Covered Bridge")
    summary = parse_summary(request, _fixture("wikipedia_summary_en.json"))
    assert summary is not None
    assert summary.page_url == "https://en.wikipedia.org/wiki/Japanese_Covered_Bridge"
    assert summary.revision == "1250000000"
    assert summary.summary.startswith("The Japanese Covered Bridge")
    assert summary.upstream_id == "en:Japanese Covered Bridge"
    assert parse_summary(request, {"type": "disambiguation", "extract": "x"}) is None
    assert parse_summary(request, {"type": "standard", "extract": ""}) is None


def test_trim_extract_cuts_at_a_sentence() -> None:
    text = "One sentence here. " * 400
    trimmed = trim_extract(text, limit=100)
    assert len(trimmed) <= 100 and trimmed.endswith(".")


async def test_fetch_summaries(httpx_mock: HTTPXMock) -> None:
    place_id = uuid.uuid4()
    httpx_mock.add_response(
        url="https://en.wikipedia.org/api/rest_v1/page/summary/Japanese_Covered_Bridge",
        json=_fixture("wikipedia_summary_en.json"),
    )
    httpx_mock.add_response(
        url="https://vi.wikipedia.org/api/rest_v1/page/summary/Ch%C3%B9a_C%E1%BA%A7u",
        status_code=404,
    )
    requests = [
        PageRequest(place_id, "en", "Japanese Covered Bridge"),
        PageRequest(place_id, "vi", "Chùa Cầu"),
    ]
    async with httpx.AsyncClient() as client:
        summaries = await fetch_summaries(client, requests, delay_s=0)
    assert [s.locale for s in summaries] == ["en"]
