"""Wikimedia Commons client: licence filter, metadata cleaning, batching (recorded payloads)."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.ingestion.common import USER_AGENT
from app.ingestion.commons import (
    API_URL,
    CommonsFile,
    Rejected,
    classify_license,
    fetch_files,
    file_title,
    parse_imageinfo,
    strip_html,
)
from app.ingestion.wikidata import parse_bindings


@pytest.mark.parametrize(
    ("code", "short", "expected"),
    [
        ("cc0", "CC0", "CC0-1.0"),
        ("pd", "Public domain", "PUBLIC-DOMAIN"),
        (None, "Public domain", "PUBLIC-DOMAIN"),
        ("cc-by-4.0", "CC BY 4.0", "CC-BY-4.0"),
        ("cc-by-sa-4.0", "CC BY-SA 4.0", "CC-BY-SA-4.0"),
        ("cc-by-sa-3.0-de", "CC BY-SA 3.0 de", "CC-BY-SA-3.0"),
        ("cc-by-2", "CC BY 2.0", "CC-BY-2.0"),
        (None, "CC BY-SA 2.5", "CC-BY-SA-2.5"),
        ("cc-by-nc-sa-4.0", "CC BY-NC-SA 4.0", None),
        ("cc-by-nd-4.0", "CC BY-ND 4.0", None),
        ("gfdl", "GFDL", None),
        (None, "Fair use", None),
        (None, None, None),
    ],
)
def test_license_filter(code: str | None, short: str | None, expected: str | None) -> None:
    assert classify_license(code, short) == expected


def test_strip_html_removes_tags_and_entities() -> None:
    artist = '<a href="//commons.wikimedia.org/wiki/User:X" title="User:X">Nguyễn&nbsp;Văn A</a>\n'
    assert strip_html(artist) == "Nguyễn Văn A"
    assert strip_html(None) == ""


def test_file_title_normalises_like_mediawiki() -> None:
    assert file_title("chua_cau.jpg") == "File:Chua cau.jpg"
    assert file_title("File:Hoi An  old town.JPG") == "File:Hoi An old town.JPG"
    assert file_title("") == ""


def _page(
    title: str,
    *,
    license_code: str = "cc-by-sa-4.0",
    short: str = "CC BY-SA 4.0",
    artist: str | None = '<span class="fn">Photographer</span>',
    thumbmime: str = "image/jpeg",
    attribution: str | None = None,
    nonfree: str | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "License": {"value": license_code},
        "LicenseShortName": {"value": short},
    }
    if artist is not None:
        meta["Artist"] = {"value": artist}
    if attribution is not None:
        meta["Attribution"] = {"value": attribution}
    if nonfree is not None:
        meta["NonFree"] = {"value": nonfree}
    name = title.removeprefix("File:").replace(" ", "_")
    return {
        "title": title,
        "imageinfo": [
            {
                "url": f"https://upload.wikimedia.org/wikipedia/commons/a/ab/{name}",
                "descriptionurl": f"https://commons.wikimedia.org/wiki/{title.replace(' ', '_')}",
                "width": 4000,
                "height": 3000,
                "mime": "image/jpeg",
                "thumburl": f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/{name}/1280px-{name}",
                "thumbwidth": 1280,
                "thumbheight": 960,
                "thumbmime": thumbmime,
                "sha1": "a" * 40,
                "extmetadata": meta,
            }
        ],
    }


def test_parse_imageinfo_accepts_free_licence_with_author() -> None:
    result = parse_imageinfo(_page("File:Chua Cau.jpg"))
    assert isinstance(result, CommonsFile)
    assert result.license_code == "CC-BY-SA-4.0"
    assert result.creator == "Photographer"
    assert result.attribution == "Photographer, CC BY-SA 4.0, via Wikimedia Commons"
    assert result.file_url.endswith("/1280px-Chua_Cau.jpg") and result.width == 1280
    assert len(result.sha256) == 64


def test_parse_imageinfo_prefers_the_required_attribution_text() -> None:
    result = parse_imageinfo(_page("File:A.jpg", attribution="<b>Studio Hội An</b>"))
    assert isinstance(result, CommonsFile)
    assert result.attribution == "Studio Hội An, CC BY-SA 4.0, via Wikimedia Commons"


@pytest.mark.parametrize(
    ("page", "reason"),
    [
        (
            _page("File:A.jpg", license_code="cc-by-nc-4.0", short="CC BY-NC 4.0"),
            "LICENSE_NOT_ALLOWED",
        ),
        (_page("File:A.jpg", nonfree="true"), "LICENSE_NOT_ALLOWED"),
        (_page("File:A.jpg", artist=None), "NO_AUTHOR"),
        (_page("File:A.gif", thumbmime="image/gif"), "UNSUPPORTED_MIME"),
        ({"title": "File:Gone.jpg", "missing": True}, "MISSING_FILE"),
    ],
)
def test_parse_imageinfo_rejections(page: dict[str, Any], reason: str) -> None:
    result = parse_imageinfo(page)
    assert isinstance(result, Rejected) and result.reason == reason


def test_public_domain_without_author_is_accepted_as_unknown_author() -> None:
    result = parse_imageinfo(
        _page("File:Old.jpg", license_code="pd", short="Public domain", artist=None)
    )
    assert isinstance(result, CommonsFile)
    assert result.creator == "Unknown author"
    assert result.license_code == "PUBLIC-DOMAIN"


async def test_fetch_files_batches_and_follows_normalisation() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        titles = request.url.params["titles"].split("|")
        normalized = [
            {"from": title, "to": title.replace("_", " ")} for title in titles if "_" in title
        ]
        pages = [_page(title.replace("_", " ")) for title in titles if "Missing" not in title]
        pages += [{"title": t, "missing": True} for t in titles if "Missing" in t]
        return httpx.Response(200, json={"query": {"normalized": normalized, "pages": pages}})

    titles = ["File:A_b.jpg", "File:C.jpg", "File:Missing.jpg"]
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        results = await fetch_files(client, titles, delay_s=0, batch_size=2)
    assert len(requests) == 2
    assert all(str(request.url).startswith(API_URL) for request in requests)
    assert all(request.headers["user-agent"] == USER_AGENT for request in requests)
    params = requests[0].url.params
    assert params["prop"] == "imageinfo" and "extmetadata" in params["iiprop"]
    assert isinstance(results["File:A_b.jpg"], CommonsFile)
    assert results["File:A_b.jpg"].title == "File:A b.jpg"  # type: ignore[union-attr]
    assert isinstance(results["File:C.jpg"], CommonsFile)
    missing = results["File:Missing.jpg"]
    assert isinstance(missing, Rejected) and missing.reason == "MISSING_FILE"


def test_wikidata_binding_images_become_commons_file_names() -> None:
    binding = {
        "item": {"value": "http://www.wikidata.org/entity/Q1091054"},
        "coord": {"value": "Point(108.32624 15.87713)"},
        "labelEn": {"value": "Japanese Covered Bridge"},
        "classLabels": {"value": "covered bridge"},
        "images": {
            "value": "http://commons.wikimedia.org/wiki/Special:FilePath/Chua%20Cau.jpg|"
            "http://commons.wikimedia.org/wiki/Special:FilePath/A_bridge.jpg"
        },
    }
    (item,) = parse_bindings([binding])
    assert item.images == ("A bridge.jpg", "Chua Cau.jpg")
    assert item.payload()["image"] == ["A bridge.jpg", "Chua Cau.jpg"]
