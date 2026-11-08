"""Wikipedia page images as the second Commons source (recorded ``pageimages`` payloads)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import httpx

from app.ingestion.common import USER_AGENT
from app.ingestion.commons import (
    Article,
    PageImage,
    PlaceArticles,
    PlaceImages,
    Rejected,
    add_page_images,
    fetch_page_images,
    parse_pageimages,
    same_subject,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(locale: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (FIXTURES / f"wikipedia_pageimages_{locale}.json").read_text(encoding="utf-8")
    )
    return data


EN_TITLES = [
    "Japanese_Covered_Bridge",
    "My Son Sanctuary",
    "Nonexistent Page Xyz",
    "Avatar (2009 film)",
]
VI_TITLES = ["Chùa Cầu", "Bảo tàng Điêu khắc Chăm Đà Nẵng"]


def test_parse_recorded_en_response_follows_normalisation_and_redirects() -> None:
    results = parse_pageimages("en", _fixture("en"), EN_TITLES)
    bridge = results["Japanese_Covered_Bridge"]
    assert isinstance(bridge, PageImage)
    assert bridge.article == "Japanese Bridge"
    assert bridge.qid == "Q1091054"
    assert bridge.file.startswith("File:2024 Hội An - Japanese Covered Bridge")
    assert bridge.page_url == "https://en.wikipedia.org/wiki/Japanese_Bridge"
    assert bridge.revision == "1366907918"
    my_son = results["My Son Sanctuary"]
    assert isinstance(my_son, PageImage) and my_son.qid == "Q391406"
    missing = results["Nonexistent Page Xyz"]
    assert isinstance(missing, Rejected) and missing.reason == "MISSING_ARTICLE"
    # Non-free lead image (film poster): only ``page_image`` is set, never used.
    poster = results["Avatar (2009 film)"]
    assert isinstance(poster, Rejected) and poster.reason == "NO_FREE_PAGE_IMAGE"


def test_parse_recorded_vi_response() -> None:
    results = parse_pageimages("vi", _fixture("vi"), VI_TITLES)
    bridge = results["Chùa Cầu"]
    assert isinstance(bridge, PageImage)
    assert (bridge.locale, bridge.file, bridge.qid) == ("vi", "File:Cau Nhat Ban.jpg", "Q1091054")
    museum = results["Bảo tàng Điêu khắc Chăm Đà Nẵng"]
    assert isinstance(museum, PageImage) and museum.file == "File:Museum of Cham Sculpture.jpg"


def test_section_redirect_is_another_subject() -> None:
    body = {
        "query": {
            "redirects": [{"from": "Tháp A1", "to": "Mỹ Sơn", "tofragment": "Nhóm A"}],
            "pages": [
                {
                    "title": "Mỹ Sơn",
                    "pageprops": {"page_image_free": "My_Son.jpg", "wikibase_item": "Q391406"},
                }
            ],
        }
    }
    result = parse_pageimages("vi", body, ["Tháp A1"])["Tháp A1"]
    assert isinstance(result, Rejected) and result.reason == "SECTION_REDIRECT"


def _image(qid: str | None, file: str = "File:X.jpg") -> PageImage:
    return PageImage("en", "X", "https://en.wikipedia.org/wiki/X", "1", qid, file)


def test_subject_guard_requires_the_place_qid_when_known() -> None:
    assert same_subject(_image("Q1"), "Q1")
    assert same_subject(_image("Q1"), None)
    assert not same_subject(_image("Q2"), "Q1")  # e.g. the parent / part-of article
    assert not same_subject(_image(None), "Q1")


async def test_fetch_page_images_one_request_per_locale_batch() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        locale = request.url.host.split(".", 1)[0]
        return httpx.Response(200, json=_fixture(locale))

    articles = [Article("en", t) for t in EN_TITLES] + [Article("vi", t) for t in VI_TITLES]
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        results = await fetch_page_images(client, articles, delay_s=0)
    assert [r.url.host for r in requests] == ["vi.wikipedia.org", "en.wikipedia.org"]
    assert all(r.headers["user-agent"] == USER_AGENT for r in requests)
    params = requests[0].url.params
    assert params["prop"] == "pageimages|pageprops|info"
    assert "page_image_free" in params["ppprop"] and "original" not in params.get("piprop", "")
    assert isinstance(results[Article("vi", "Chùa Cầu")], PageImage)
    assert isinstance(results[Article("en", "Avatar (2009 film)")], Rejected)


async def test_failed_request_yields_no_images() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        results = await fetch_page_images(client, [Article("vi", "Chùa Cầu")], delay_s=0)
    assert results == {}


def test_add_page_images_only_for_places_without_media_and_same_subject() -> None:
    vi = parse_pageimages("vi", _fixture("vi"), VI_TITLES)
    en = parse_pageimages("en", _fixture("en"), EN_TITLES)
    images = {Article("vi", t): r for t, r in vi.items()} | {
        Article("en", t): r for t, r in en.items()
    }
    bridge, museum, parent, done = (uuid.UUID(int=i) for i in range(1, 5))
    articles = [
        PlaceArticles(
            bridge,
            qid="Q1091054",
            names={"vi": "Chùa Cầu", "en": "Japanese Bridge"},
            articles=[Article("vi", "Chùa Cầu"), Article("en", "Japanese_Covered_Bridge")],
        ),
        PlaceArticles(museum, qid=None, articles=[Article("vi", VI_TITLES[1])]),
        # A tower whose record points at the whole sanctuary article: wrong subject.
        PlaceArticles(parent, qid="Q999", articles=[Article("en", "My Son Sanctuary")]),
        PlaceArticles(done, qid=None, articles=[Article("vi", "Chùa Cầu")]),
    ]
    existing = [PlaceImages(done, titles=["File:Owner.jpg"])]
    result, wrong = add_page_images(existing, articles, images, skip={done})
    by_place = {entry.place_id: entry for entry in result}
    assert wrong == 1 and parent not in by_place
    assert by_place[done].titles == ["File:Owner.jpg"] and not by_place[done].via
    assert by_place[bridge].titles[0] == "File:Cau Nhat Ban.jpg"  # VI article first
    assert len(by_place[bridge].titles) == 2
    assert set(by_place[bridge].via) == set(by_place[bridge].titles)
    assert by_place[bridge].names == {"vi": "Chùa Cầu", "en": "Japanese Bridge"}
    assert by_place[museum].names == {"vi": VI_TITLES[1]}
    assert (
        by_place[museum]
        .via["File:Museum of Cham Sculpture.jpg"]
        .page_url.startswith("https://vi.wikipedia.org/")
    )


def test_maps_logos_and_svgs_are_not_photos() -> None:
    names = [
        "Vietnam_location_map.svg",
        "Da Nang locator map.png",
        "Logo Bảo tàng.png",
        "Flag of Vietnam.png",
        "Bản đồ Hội An.jpg",
    ]
    pages = [
        {"title": f"P{i}", "pageprops": {"page_image_free": name}} for i, name in enumerate(names)
    ]
    pages.append({"title": "Photo", "pageprops": {"page_image_free": "Cau_Nhat_Ban.jpg"}})
    titles = [str(page["title"]) for page in pages]
    results = parse_pageimages("vi", {"query": {"pages": pages}}, titles)
    for title in titles[:-1]:
        result = results[title]
        assert isinstance(result, Rejected) and result.reason == "NOT_A_PHOTO", title
    assert isinstance(results["Photo"], PageImage)
