"""Catalog and preferences routes with dependency overrides and stubbed repositories (no DB)."""

import dataclasses
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time
from typing import Any

import jwt
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from app.api.routes import catalog as catalog_routes
from app.catalog.places import (
    FactRecord,
    FactSourceRecord,
    MediaRecord,
    PlaceDetailRecord,
    PlacesRepository,
    PlaceSummaryRecord,
)
from app.catalog.preferences import PreferencesRecord, PreferencesRepository, PreferencesUpdate
from app.catalog.reference import AreaRecord, CategoryRecord, CityRecord, ReferenceRepository
from app.catalog.search import InvalidCursorError, SearchPage
from app.db.session import get_db_session
from app.main import create_app
from app.models.account import Account
from app.security import clerk
from app.security.clerk import (
    AuthenticatedUser,
    get_current_account,
    get_current_user,
    get_optional_account,
)

CITY_ID = uuid.uuid4()
PLACE_ID = uuid.uuid4()
PUBLICATION_ID = uuid.uuid4()
ACCOUNT_ID = uuid.uuid4()

AREA = AreaRecord("hoi-an-old-town", CITY_ID, "Phố cổ Hội An", "Hoi An Ancient Town", 5)
CITY = CityRecord(
    CITY_ID, "da-nang", "Đà Nẵng", "Da Nang", "Asia/Ho_Chi_Minh", 15.6, 108.1, (AREA,)
)
SUMMARY = PlaceSummaryRecord(
    place_id=PLACE_ID,
    catalog_publication_id=PUBLICATION_ID,
    city_id=CITY_ID,
    slug="chua-linh-ung",
    category_code="RELIGIOUS_SITE",
    area_code=None,
    name_vi="Chùa Linh Ứng",
    name_en="Linh Ung Pagoda",
    short_description_vi="Chùa trên bán đảo Sơn Trà",
    short_description_en="Pagoda on Son Tra",
    lat=16.1,
    lng=108.27,
    visit_minutes_suggested=60,
    thumbnail=MediaRecord(
        uuid.uuid4(),
        "places/linh-ung.jpg",
        800,
        600,
        "Jane",
        "CC-BY-4.0",
        "© Jane",
        "Chùa",
        "Pagoda",
        1,
    ),
)
VERIFIED_AT = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
SOURCE = FactSourceRecord(
    uuid.uuid4(),
    "Sở Du lịch",
    "Giờ mở cửa",
    "https://example.invalid/a",
    VERIFIED_AT,
    "CC-BY-4.0",
    "© Sở Du lịch Đà Nẵng",
    None,
)
DETAIL = PlaceDetailRecord(
    summary=SUMMARY,
    publication_revision=2,
    published_at=VERIFIED_AT,
    description_vi="Mô tả",
    description_en="Description",
    visit_minutes_min=30,
    visit_minutes_max=90,
    entrance_lat=None,
    entrance_lng=None,
    area=None,
    facts=(
        FactRecord(
            uuid.uuid4(),
            "OPENING_HOURS",
            True,
            "KNOWN",
            {"text": "06:00-21:00"},
            VERIFIED_AT,
            None,
            False,
            (SOURCE,),
        ),
        FactRecord(
            uuid.uuid4(),
            "ADMISSION_PRICE",
            True,
            "UNKNOWN",
            None,
            VERIFIED_AT,
            None,
            True,
            (SOURCE,),
        ),
    ),
    media=(SUMMARY.thumbnail,),  # type: ignore[arg-type]
    closure_rules=(),
)


async def _fake_session() -> AsyncIterator[object]:
    yield object()


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_current_user] = lambda: AuthenticatedUser("u", None)
    application.dependency_overrides[get_current_account] = lambda: Account(
        id=ACCOUNT_ID, clerk_user_id="u"
    )
    application.dependency_overrides[get_optional_account] = lambda: Account(
        id=ACCOUNT_ID, clerk_user_id="u"
    )
    application.dependency_overrides[get_db_session] = _fake_session

    async def cities(self: Any) -> list[CityRecord]:
        return [CITY]

    async def categories(self: Any) -> list[CategoryRecord]:
        return [CategoryRecord("HERITAGE", "Di sản", "Heritage", 1)]

    async def no_locale(self: Any, account_id: uuid.UUID) -> str | None:
        return None

    monkeypatch.setattr(ReferenceRepository, "list_enabled_cities", cities)
    monkeypatch.setattr(ReferenceRepository, "list_categories", categories)
    monkeypatch.setattr(PreferencesRepository, "get_locale", no_locale)
    return application


async def get(app: FastAPI, path: str, **kwargs: Any) -> Response:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path, **kwargs)


async def put(app: FastAPI, path: str, body: Any) -> Response:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.put(path, json=body)


@pytest.mark.parametrize("path", ["/v1/me/preferences", "/v1/trips"])
async def test_private_routes_require_authentication(path: str) -> None:
    response = await get(create_app(), path)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


PUBLIC_PATHS = ["/v1/cities", "/v1/categories", "/v1/places", f"/v1/places/{PLACE_ID}"]


@pytest.fixture
def public_app(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    """The catalog app without the auth overrides: real optional-auth dependencies."""
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_account, None)
    app.dependency_overrides.pop(get_optional_account, None)

    async def fake_search(session: Any, **kwargs: Any) -> SearchPage:
        return SearchPage(items=[SUMMARY], next_cursor=None)

    async def fake_detail(self: Any, place_id: uuid.UUID) -> PlaceDetailRecord | None:
        return DETAIL

    monkeypatch.setattr(catalog_routes, "search_catalog", fake_search)
    monkeypatch.setattr(PlacesRepository, "get_published_detail", fake_detail)
    return app


@pytest.mark.parametrize("path", PUBLIC_PATHS)
async def test_public_catalog_reads_work_for_guests(public_app: FastAPI, path: str) -> None:
    response = await get(public_app, path)
    assert response.status_code == 200, response.text


class _Verifier:
    def __init__(self, valid: bool) -> None:
        self.valid = valid

    def verify(self, token: str) -> AuthenticatedUser:
        if not self.valid:
            raise jwt.InvalidTokenError("bad token")
        return AuthenticatedUser("user_1", None)


@pytest.mark.parametrize("path", PUBLIC_PATHS)
async def test_public_catalog_reads_reject_an_invalid_token(
    public_app: FastAPI, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    monkeypatch.setattr(clerk, "get_token_verifier", lambda: _Verifier(valid=False))
    response = await get(public_app, path, headers={"Authorization": "Bearer nope"})
    assert response.status_code == 401


@pytest.mark.parametrize("path", PUBLIC_PATHS)
async def test_public_catalog_reads_accept_a_valid_token(
    public_app: FastAPI, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    seen: list[uuid.UUID] = []

    async def account(user: Any, session: Any) -> Account:
        assert user.subject == "user_1"
        return Account(id=ACCOUNT_ID, clerk_user_id="user_1")

    async def no_job(session: Any, account_id: uuid.UUID) -> bool:
        seen.append(account_id)
        return False

    monkeypatch.setattr(clerk, "get_account_allowing_deletion", account)
    monkeypatch.setattr(clerk, "has_open_deletion_job", no_job)
    monkeypatch.setattr(clerk, "get_token_verifier", lambda: _Verifier(valid=True))
    response = await get(public_app, path, headers={"Authorization": "Bearer ok"})
    assert response.status_code == 200, response.text
    assert seen == [ACCOUNT_ID]


async def test_cities_lists_enabled_city_with_areas(app: FastAPI) -> None:
    body = (await get(app, "/v1/cities")).json()
    assert body == {
        "items": [
            {
                "id": str(CITY_ID),
                "code": "da-nang",
                "name_vi": "Đà Nẵng",
                "name_en": "Da Nang",
                "time_zone": "Asia/Ho_Chi_Minh",
                "centre": {"latitude": 15.6, "longitude": 108.1},
                "areas": [
                    {
                        "code": "hoi-an-old-town",
                        "name_vi": "Phố cổ Hội An",
                        "name_en": "Hoi An Ancient Town",
                        "sort_order": 5,
                    }
                ],
            }
        ]
    }


async def test_categories_shape(app: FastAPI) -> None:
    body = (await get(app, "/v1/categories")).json()
    assert body["items"] == [
        {"code": "HERITAGE", "name_vi": "Di sản", "name_en": "Heritage", "sort_order": 1}
    ]


async def test_search_returns_verified_summaries(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []

    async def fake_search(session: Any, **kwargs: Any) -> SearchPage:
        calls.append(kwargs)
        return SearchPage(items=[SUMMARY], next_cursor="next")

    monkeypatch.setattr(catalog_routes, "search_catalog", fake_search)
    response = await get(
        app,
        "/v1/places",
        params={"q": "linh ung", "category_code": "religious_site", "locale": "en", "limit": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["next_cursor"] == "next"
    item = body["items"][0]
    assert item["trust_level"] == "VERIFIED"
    assert item["name"] == "Linh Ung Pagoda"
    assert item["name_vi"] == "Chùa Linh Ứng"
    assert item["location"] == {"latitude": 16.1, "longitude": 108.27}
    assert item["thumbnail"]["url"].endswith("/places/linh-ung.jpg")
    assert item["thumbnail"]["alt_text"] == "Pagoda"
    assert calls[0]["city_id"] == CITY_ID
    assert calls[0]["category_code"] == "religious_site"  # upper-cased inside search_catalog
    assert calls[0]["limit"] == 5 and calls[0]["locale"] == "en"


async def test_search_defaults_to_vi_and_account_locale(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_search(session: Any, **kwargs: Any) -> SearchPage:
        return SearchPage(items=[SUMMARY], next_cursor=None)

    monkeypatch.setattr(catalog_routes, "search_catalog", fake_search)
    assert (await get(app, "/v1/places")).json()["items"][0]["name"] == "Chùa Linh Ứng"

    async def en_locale(self: Any, account_id: uuid.UUID) -> str | None:
        return "en"

    monkeypatch.setattr(PreferencesRepository, "get_locale", en_locale)
    assert (await get(app, "/v1/places")).json()["items"][0]["name"] == "Linh Ung Pagoda"


async def test_invalid_cursor_is_400(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search(session: Any, **kwargs: Any) -> SearchPage:
        raise InvalidCursorError("malformed cursor")

    monkeypatch.setattr(catalog_routes, "search_catalog", fake_search)
    response = await get(app, "/v1/places", params={"cursor": "zzz"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_cursor"


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"city_id": str(uuid.uuid4())}, "city_id"),
        ({"city_code": "hoi-an"}, "city_code"),
        ({"area_code": "old-quarter"}, "area_code"),
        ({"bbox": "1,2,3"}, "bbox"),
        ({"bbox": "108.3,16.0,108.1,16.1"}, "bbox"),
        ({"near": "16.0"}, "near"),
        ({"near": "95,108"}, "near"),
    ],
)
async def test_search_filter_validation(app: FastAPI, params: dict[str, str], field: str) -> None:
    response = await get(app, "/v1/places", params=params)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["context"]["fields"][0]["location"] == ["query", field]


@pytest.mark.parametrize(
    "params", [{"limit": 0}, {"limit": 51}, {"q": ""}, {"sort": "distance"}, {"locale": "fr"}]
)
async def test_search_parameter_validation(app: FastAPI, params: dict[str, Any]) -> None:
    response = await get(app, "/v1/places", params=params)
    assert response.status_code == 422


async def test_place_detail_keeps_unknown_facts(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_detail(self: Any, place_id: uuid.UUID) -> PlaceDetailRecord | None:
        return DETAIL if place_id == PLACE_ID else None

    monkeypatch.setattr(PlacesRepository, "get_published_detail", fake_detail)
    response = await get(app, f"/v1/places/{PLACE_ID}", params={"locale": "en"})
    assert response.status_code == 200
    body = response.json()
    assert body["trust_level"] == "VERIFIED"
    assert body["name"] == "Linh Ung Pagoda" and body["name_vi"] == "Chùa Linh Ứng"
    assert body["description"] == "Description"
    assert body["entrance_location"] is None
    hours, price = body["facts"]
    assert hours["value"] == {"text": "06:00-21:00"} and hours["freshness"] == "CURRENT"
    assert hours["verified_at"] == "2026-10-01"
    assert hours["source"]["publisher"] == "Sở Du lịch"
    assert hours["source"]["trust_level"] == "VERIFIED"
    assert price["knowledge_state"] == "UNKNOWN" and price["value"] is None
    assert price["freshness"] == "STALE"
    assert {a["attribution_text"] for a in body["attributions"]} == {
        "© Sở Du lịch Đà Nẵng",
        "© Jane",
    }

    missing = await get(app, f"/v1/places/{uuid.uuid4()}")
    assert missing.status_code == 404


async def test_place_detail_exposes_description_origin_and_name_fallback(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    summary = dataclasses.replace(SUMMARY, name_en="Chùa Linh Ứng", name_en_is_source_fallback=True)
    detail = dataclasses.replace(
        DETAIL, summary=summary, translation_origin_en="AI_SUMMARY", description_vi=None
    )

    async def fake_detail(self: Any, place_id: uuid.UUID) -> PlaceDetailRecord | None:
        return detail

    monkeypatch.setattr(PlacesRepository, "get_published_detail", fake_detail)
    en = (await get(app, f"/v1/places/{PLACE_ID}", params={"locale": "en"})).json()
    assert en["description_origin"] == "AI_SUMMARY"
    assert en["name_is_source_fallback"] is True and en["name"] == "Chùa Linh Ứng"
    vi = (await get(app, f"/v1/places/{PLACE_ID}", params={"locale": "vi"})).json()
    assert vi["description"] is None and vi["description_origin"] is None
    assert vi["name_is_source_fallback"] is False  # the VI name is the source name
    monkeypatch.setattr(
        PlacesRepository,
        "get_published_detail",
        lambda self, place_id: _async(DETAIL),
    )
    plain = (await get(app, f"/v1/places/{PLACE_ID}", params={"locale": "vi"})).json()
    assert plain["description_origin"] == "SOURCE"


async def _async(value: Any) -> Any:
    return value


async def test_preferences_defaults(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    async def none(self: Any, account_id: uuid.UUID) -> PreferencesRecord | None:
        return None

    monkeypatch.setattr(PreferencesRepository, "get", none)
    body = (await get(app, "/v1/me/preferences")).json()
    assert body == {
        "locale": "vi",
        "pace": None,
        "interest_category_codes": [],
        "allowed_modes": ["WALK", "DRIVE"],
        "day_start_time": None,
        "day_end_time": None,
        "ai_notice_acknowledged_at": None,
        "updated_at": None,
    }


async def test_put_preferences_normalises_interests(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    saved: list[tuple[uuid.UUID, PreferencesUpdate]] = []

    async def upsert(
        self: Any, account_id: uuid.UUID, update: PreferencesUpdate
    ) -> PreferencesRecord:
        saved.append((account_id, update))
        return PreferencesRecord(
            locale=update.locale,
            interest_category_codes=update.interest_category_codes,
            allowed_modes=update.allowed_modes,
            day_start_time=update.day_start_time,
            day_end_time=update.day_end_time,
        )

    monkeypatch.setattr(PreferencesRepository, "upsert", upsert)
    response = await put(
        app,
        "/v1/me/preferences",
        {
            "locale": "en",
            "interest_category_codes": ["heritage", "HERITAGE"],
            "allowed_modes": ["WALK"],
            "day_start_time": "08:30",
            "day_end_time": "20:00",
            "ai_notice_acknowledged": True,
        },
    )
    assert response.status_code == 200
    account_id, update = saved[0]
    assert account_id == ACCOUNT_ID
    assert update.interest_category_codes == ("HERITAGE",)
    assert update.day_start_time == time(8, 30) and update.ai_notice_acknowledged
    body = response.json()
    assert body["interest_category_codes"] == ["HERITAGE"]
    assert body["day_start_time"] == "08:30"


@pytest.mark.parametrize(
    "body",
    [
        {"locale": "vi", "interest_category_codes": [], "allowed_modes": []},
        {"locale": "vi", "interest_category_codes": [], "allowed_modes": ["WALK", "WALK"]},
        {"locale": "vi", "interest_category_codes": [], "allowed_modes": ["BIKE"]},
        {"locale": "fr", "interest_category_codes": [], "allowed_modes": ["WALK"]},
        {"locale": "vi", "interest_category_codes": [], "allowed_modes": ["WALK"], "x": 1},
        {
            "locale": "vi",
            "interest_category_codes": [],
            "allowed_modes": ["WALK"],
            "day_start_time": "8:00",
        },
        {
            "locale": "vi",
            "interest_category_codes": [],
            "allowed_modes": ["WALK"],
            "day_start_time": "20:00",
            "day_end_time": "08:00",
        },
        {"locale": "vi", "interest_category_codes": ["x"] * 21, "allowed_modes": ["WALK"]},
        {"locale": "vi", "interest_category_codes": ["SPA"], "allowed_modes": ["WALK"]},
        {"locale": "vi", "pace": "FAST", "interest_category_codes": [], "allowed_modes": ["WALK"]},
    ],
)
async def test_put_preferences_validation(app: FastAPI, body: dict[str, Any]) -> None:
    response = await put(app, "/v1/me/preferences", body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
