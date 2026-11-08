from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from typing import Any

import pytest
from pytest_httpx import HTTPXMock
from research_fakes import FakeLedger, MemoryStore, private_resolver, public_resolver

from app.agents.schemas import WebCandidate
from app.ai.quota import Bucket
from app.research.candidates_repo import store_candidates
from app.research.extract import build_scoped_query, excerpt_for_model, query_key
from app.research.fetch import USER_AGENT, FetchStatus, PageFetcher
from app.research.places_check import SEARCH_TEXT_URL, PlacesChecker, PlacesOutcome
from app.research.tavily import SearchStatus, TavilySearch
from app.research.toolbox import ResearchToolbox

TAVILY_URL = "https://api.tavily.com/search"
PAGE_URL = "https://example.vn/an-bang"
HTML = (
    "<html><head><title>An Bàng beach guide</title></head><body><article>"
    "<h1>Bãi biển An Bàng</h1>"
    "<p>Bãi biển An Bàng nằm cách phố cổ Hội An khoảng 4 km về phía biển, rất yên bình.</p>"
    "<p>Liên hệ đặt chỗ: 0905 123 456 hoặc demo@example.vn để biết thêm chi tiết nhé.</p>"
    "<p>Bãi biển mở cửa tự do cả ngày, không thu vé vào cổng cho du khách tham quan.</p>"
    "</article></body></html>"
)


def tavily(store: MemoryStore, ledger: FakeLedger, key: str | None = "tvly-test") -> TavilySearch:
    return TavilySearch(api_key=key, ledger=ledger, store=store)  # type: ignore[arg-type]


# --- extract --------------------------------------------------------------------------------


def test_scoped_query_names_city_and_redacts() -> None:
    assert build_scoped_query("rooftop bar  river view") == "rooftop bar river view Đà Nẵng"
    assert build_scoped_query("night market Hội An") == "night market Hội An"
    assert "0905" not in build_scoped_query("quán gần 0905 123 456")
    assert query_key("Night  Market") == query_key("night market")


def test_excerpt_prefers_relevant_paragraphs_and_redacts() -> None:
    text = "Intro line.\n" + "\n".join(f"Filler paragraph {i} " * 5 for i in range(50))
    text += "\nThe vegetarian restaurant Minh Hien serves chay food. Call 0905 123 456."
    out = excerpt_for_model(text, focus="vegetarian chay Hội An", limit=400)
    assert out.startswith("Intro line.") and "Minh Hien" in out
    assert "0905" not in out and "[PHONE]" in out and len(out) <= 400


# --- tavily ---------------------------------------------------------------------------------


async def test_tavily_search_caches_and_books_both_buckets(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=TAVILY_URL,
        method="POST",
        json={"results": [{"url": PAGE_URL + "/", "title": "An Bàng", "content": "beach"}]},
    )
    store, ledger = MemoryStore(), FakeLedger()
    search = tavily(store, ledger)
    first = await search.search("quiet beach")
    assert first.status is SearchStatus.OK and first.hits[0].url == PAGE_URL
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["query"] == "quiet beach Đà Nẵng" and body["max_results"] == 5
    again = await search.search("Quiet  beach")
    assert again.status is SearchStatus.CACHED and again.hits == first.hits
    assert ledger.used[Bucket.TAVILY_DAY] == 1 and ledger.used[Bucket.TAVILY_MONTH] == 1


async def test_tavily_quota_and_missing_key_skip_the_call() -> None:
    store = MemoryStore()
    capped = FakeLedger({Bucket.TAVILY_MONTH: 0})
    out = await tavily(store, capped).search("x")
    assert out.status is SearchStatus.QUOTA_EXCEEDED and capped.reserved[Bucket.TAVILY_DAY] == 0
    assert (await tavily(store, FakeLedger(), key=None).search("x")).status is SearchStatus.DISABLED


async def test_tavily_provider_error_degrades(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TAVILY_URL, method="POST", status_code=500, json={})
    ledger = FakeLedger()
    out = await tavily(MemoryStore(), ledger).search("x")
    assert out.status is SearchStatus.PROVIDER_ERROR and not out.hits
    assert ledger.used[Bucket.TAVILY_DAY] == 1


# --- fetch ----------------------------------------------------------------------------------


async def test_fetch_extracts_text_records_revision_and_caches(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="https://example.vn/robots.txt", text="User-agent: *\nAllow: /")
    httpx_mock.add_response(url=PAGE_URL, html=HTML)
    store = MemoryStore()
    fetcher = PageFetcher(store=store, resolver=public_resolver)  # type: ignore[arg-type]
    page = await fetcher.fetch(PAGE_URL + "#top")
    assert page.status is FetchStatus.OK and page.title == "An Bàng beach guide"
    assert "phố cổ Hội An" in page.text
    assert store.revisions[0]["url"] == PAGE_URL and len(store.revisions[0]["sha"]) == 64
    assert page.source_revision_id == store.revisions[0]["id"]
    assert httpx_mock.get_requests()[1].headers["user-agent"] == USER_AGENT
    cached = await fetcher.fetch(PAGE_URL)
    assert cached.status is FetchStatus.CACHED and cached.text == page.text
    assert len(store.revisions) == 1


async def test_fetch_respects_robots(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://example.vn/robots.txt", text="User-agent: GonarraBot\nDisallow: /"
    )
    fetcher = PageFetcher(store=MemoryStore(), resolver=public_resolver)  # type: ignore[arg-type]
    assert (await fetcher.fetch(PAGE_URL)).status is FetchStatus.ROBOTS_DISALLOWED


@pytest.mark.parametrize(
    "url", ["http://example.vn/x", "https://user:pw@example.vn/x", "https://example.vn:8443/x"]
)
async def test_fetch_ssrf_guard_refuses_bad_urls(url: str) -> None:
    fetcher = PageFetcher(store=MemoryStore(), resolver=public_resolver)  # type: ignore[arg-type]
    assert (await fetcher.fetch(url)).status is FetchStatus.BLOCKED_URL


async def test_fetch_refuses_private_addresses() -> None:
    fetcher = PageFetcher(store=MemoryStore(), resolver=private_resolver)  # type: ignore[arg-type]
    assert (await fetcher.fetch(PAGE_URL)).status is FetchStatus.BLOCKED_URL


async def test_fetch_rechecks_redirect_targets(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="https://example.vn/robots.txt", status_code=404)
    httpx_mock.add_response(
        url=PAGE_URL, status_code=302, headers={"location": "http://169.254.169.254/latest"}
    )
    fetcher = PageFetcher(store=MemoryStore(), resolver=public_resolver)  # type: ignore[arg-type]
    assert (await fetcher.fetch(PAGE_URL)).status is FetchStatus.BLOCKED_URL


async def test_fetch_size_and_type_limits(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="https://example.vn/robots.txt", status_code=404)
    httpx_mock.add_response(url=PAGE_URL, content=b"x" * (2 * 1024 * 1024 + 10))
    httpx_mock.add_response(
        url=PAGE_URL + "/pdf", content=b"%PDF", headers={"content-type": "application/pdf"}
    )
    fetcher = PageFetcher(store=MemoryStore(), resolver=public_resolver)  # type: ignore[arg-type]
    assert (await fetcher.fetch(PAGE_URL)).status is FetchStatus.TOO_LARGE
    assert (await fetcher.fetch(PAGE_URL + "/pdf")).status is FetchStatus.UNSUPPORTED_TYPE


# --- places ---------------------------------------------------------------------------------


async def test_places_check_skipped_without_key() -> None:
    checker = PlacesChecker(api_key=None, ledger=FakeLedger(), store=MemoryStore())  # type: ignore[arg-type]
    result = await checker.check("Chợ Hàn")
    assert result.outcome is PlacesOutcome.SKIPPED and result.checked_at is None


@pytest.mark.parametrize(
    ("payload", "inside", "expected"),
    [
        (
            {
                "places": [
                    {
                        "id": "g1",
                        "businessStatus": "OPERATIONAL",
                        "location": {"latitude": 16.06, "longitude": 108.22},
                    }
                ]
            },
            True,
            PlacesOutcome.EXISTS_OPERATIONAL,
        ),
        (
            {
                "places": [
                    {
                        "id": "g1",
                        "businessStatus": "CLOSED_PERMANENTLY",
                        "location": {"latitude": 16.06, "longitude": 108.22},
                    }
                ]
            },
            True,
            PlacesOutcome.EXISTS_CLOSED,
        ),
        (
            {"places": [{"id": "g1", "location": {"latitude": 21.0, "longitude": 105.8}}]},
            False,
            PlacesOutcome.OUTSIDE_CITY,
        ),
        ({}, True, PlacesOutcome.NOT_FOUND),
    ],
)
async def test_places_check_verdicts(
    httpx_mock: HTTPXMock, payload: dict[str, Any], inside: bool, expected: PlacesOutcome
) -> None:
    httpx_mock.add_response(url=SEARCH_TEXT_URL, method="POST", json=payload)
    store, ledger = MemoryStore(inside_city=inside), FakeLedger()
    checker = PlacesChecker(api_key="g-key", ledger=ledger, store=store)  # type: ignore[arg-type]
    result = await checker.check("Chợ Hàn")
    assert result.outcome is expected and result.checked_at is not None
    request = httpx_mock.get_requests()[0]
    assert request.headers["x-goog-fieldmask"] == "places.id,places.businessStatus,places.location"
    assert ledger.used[Bucket.PLACES] == 1
    cached = await checker.check("Chợ Hàn")
    assert cached.cached and cached.outcome is expected


# --- toolbox --------------------------------------------------------------------------------


async def test_toolbox_caps_and_url_allow_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=TAVILY_URL,
        method="POST",
        json={"results": [{"url": PAGE_URL, "title": "t", "content": "Call 0905 123 456"}]},
        is_reusable=True,
    )
    httpx_mock.add_response(url="https://example.vn/robots.txt", status_code=404)
    httpx_mock.add_response(url=PAGE_URL, html=HTML)
    store, ledger = MemoryStore(), FakeLedger()
    box = ResearchToolbox(
        search=tavily(store, ledger),
        fetcher=PageFetcher(store=store, resolver=public_resolver),  # type: ignore[arg-type]
        places=PlacesChecker(api_key=None, ledger=ledger, store=store),  # type: ignore[arg-type]
        focus="beach",
    )
    first = json.loads(await box.tavily_search("beach one"))
    assert "0905" not in json.dumps(first, ensure_ascii=False)
    await box.tavily_search("beach two")
    assert "limit" in json.loads(await box.tavily_search("beach three"))["error"]
    assert "only URLs" in json.loads(await box.fetch_page("https://evil.example/x"))["error"]
    page = json.loads(await box.fetch_page(PAGE_URL))
    assert "An Bàng" in page["text"] and "demo@example.vn" not in page["text"]
    assert box.page_text(PAGE_URL) == page["text"]
    assert json.loads(await box.places_check("An Bàng"))["outcome"] == "SKIPPED"
    assert box.stats.searches == 2 and box.stats.fetches == 1 and box.stats.places_checks == 1


# --- candidates repository ------------------------------------------------------------------


class RecordingSession:
    def __init__(self) -> None:
        self.statements: list[tuple[str, dict[str, Any]]] = []
        self.committed = False

    async def execute(self, stmt: Any, params: dict[str, Any]) -> Any:
        tag = str(stmt).split("*/")[0].replace("/*", "").strip()
        self.statements.append((tag, params))
        value: Any = None
        if tag == "research:city":
            value = uuid.UUID(int=7)
        elif tag == "research:cand_insert":
            value = uuid.UUID(int=9)

        class _R:
            def scalar(self) -> Any:
                return value

            def scalar_one(self) -> Any:
                return value

        return _R()

    async def commit(self) -> None:
        self.committed = True


async def test_store_candidates_writes_pending_row_with_provenance(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=TAVILY_URL, method="POST", json={"results": [{"url": PAGE_URL, "title": "t"}]}
    )
    httpx_mock.add_response(url="https://example.vn/robots.txt", status_code=404)
    httpx_mock.add_response(url=PAGE_URL, html=HTML)
    store, ledger = MemoryStore(), FakeLedger()
    box = ResearchToolbox(
        search=tavily(store, ledger),
        fetcher=PageFetcher(store=store, resolver=public_resolver),  # type: ignore[arg-type]
        places=PlacesChecker(api_key=None, ledger=ledger, store=store),  # type: ignore[arg-type]
    )
    await box.tavily_search("An Bàng")
    await box.fetch_page(PAGE_URL)
    cand = WebCandidate(
        name="Bãi biển An Bàng",
        category_guess="BEACH",
        source_url=PAGE_URL,
        name_quote="Bãi biển An Bàng nằm cách phố cổ Hội An",
    )
    session = RecordingSession()

    @asynccontextmanager
    async def factory() -> Any:
        yield session

    stored = await store_candidates(
        factory, candidates=[cand], toolbox=box, extraction_model="GROQ:x"
    )
    assert stored and stored[0].created and stored[0].places_check_outcome == "SKIPPED"
    insert = dict(session.statements)["research:cand_insert"]
    assert insert["outcome"] == "SKIPPED" and insert["checked_at"] is None and insert["gid"] is None
    assert insert["rev"] == store.revisions[0]["id"]
    assert insert["extraction"]["name_quote"].startswith("Bãi biển An Bàng")
    assert insert["query"] == "An Bàng Đà Nẵng"
    assert session.committed
