"""Google Routes client against pytest-httpx mocks only — no live Google call is ever made."""

from __future__ import annotations

import json

import httpx
import pytest
from pytest_httpx import HTTPXMock
from routing_fakes import matrix_callback

from app.config import Settings
from app.routing.estimate import EstimateProvider
from app.routing.google_routes import (
    COMPUTE_ROUTE_MATRIX_URL,
    FIELD_MASK,
    GoogleRoutesProvider,
)
from app.routing.provider import (
    EstimateNotAllowedError,
    LatLng,
    NoRoutesProvider,
    select_provider,
)

KEY = "test-key-not-real"


def _pts(n: int) -> list[LatLng]:
    return [LatLng(round(16.0 + i * 0.001, 6), round(108.2 + i * 0.001, 6)) for i in range(n)]


async def test_request_shape_and_parsing(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_callback(matrix_callback(no_route={(1, 0)}), url=COMPUTE_ROUTE_MATRIX_URL)
    provider = GoogleRoutesProvider(KEY)
    elements = await provider.compute_matrix(_pts(2), _pts(2), "DRIVE")

    request = httpx_mock.get_requests()[0]
    assert request.method == "POST"
    assert request.headers["X-Goog-Api-Key"] == KEY
    assert request.headers["X-Goog-FieldMask"] == FIELD_MASK
    assert FIELD_MASK == "originIndex,destinationIndex,distanceMeters,duration,condition"
    body = json.loads(request.content)
    assert body["travelMode"] == "DRIVE"
    assert body["routingPreference"] == "TRAFFIC_UNAWARE"
    assert body["origins"][1] == {
        "waypoint": {"location": {"latLng": {"latitude": 16.001, "longitude": 108.201}}}
    }

    by_pair = {(e.origin_index, e.destination_index): e for e in elements}
    assert len(by_pair) == 4
    assert by_pair[(0, 0)].available and by_pair[(0, 0)].duration_s == 60  # omitted indexes = 0
    assert by_pair[(0, 1)].distance_m == 1001 and by_pair[(0, 1)].duration_s == 120
    assert not by_pair[(1, 0)].available and not by_pair[(1, 0)].error  # ROUTE_NOT_FOUND


async def test_walk_omits_routing_preference(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_callback(matrix_callback(), url=COMPUTE_ROUTE_MATRIX_URL)
    await GoogleRoutesProvider(KEY).compute_matrix(_pts(1), _pts(2), "WALK")
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["travelMode"] == "WALK"
    assert "routingPreference" not in body


async def test_batches_at_25_by_25(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_callback(matrix_callback(), url=COMPUTE_ROUTE_MATRIX_URL, is_reusable=True)
    elements = await GoogleRoutesProvider(KEY).compute_matrix(_pts(30), _pts(27), "DRIVE")
    requests = httpx_mock.get_requests()
    shapes = sorted(
        (len(json.loads(r.content)["origins"]), len(json.loads(r.content)["destinations"]))
        for r in requests
    )
    assert shapes == [(5, 2), (5, 25), (25, 2), (25, 25)]
    assert len(elements) == 30 * 27
    assert {(e.origin_index, e.destination_index) for e in elements} == {
        (o, d) for o in range(30) for d in range(27)
    }
    # Global indexes are re-based: origin 29 / destination 26 came from the last block.
    last = next(e for e in elements if e.origin_index == 29 and e.destination_index == 26)
    assert last.distance_m == 1000 + 10 * 4 + 1


async def test_http_error_degrades_to_error_elements(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=COMPUTE_ROUTE_MATRIX_URL, status_code=429)
    elements = await GoogleRoutesProvider(KEY).compute_matrix(_pts(2), _pts(2), "DRIVE")
    assert len(elements) == 4
    assert all(not e.available and e.error for e in elements)


async def test_timeout_degrades(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ReadTimeout("slow"), url=COMPUTE_ROUTE_MATRIX_URL)
    elements = await GoogleRoutesProvider(KEY).compute_matrix(_pts(1), _pts(1), "DRIVE")
    assert elements[0].error


async def test_missing_and_malformed_elements_are_errors(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=COMPUTE_ROUTE_MATRIX_URL,
        json=[
            {"condition": "ROUTE_EXISTS", "distanceMeters": 5, "duration": "bad"},
            {"destinationIndex": 1, "condition": "ROUTE_MATRIX_ELEMENT_CONDITION_UNSPECIFIED"},
        ],
    )
    elements = await GoogleRoutesProvider(KEY).compute_matrix(_pts(2), _pts(2), "DRIVE")
    assert all(not e.available and e.error for e in elements)


async def test_key_not_logged(httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture) -> None:
    httpx_mock.add_response(url=COMPUTE_ROUTE_MATRIX_URL, status_code=500)
    await GoogleRoutesProvider(KEY).compute_matrix(_pts(1), _pts(1), "DRIVE")
    assert KEY not in caplog.text
    assert "16.0" not in caplog.text  # no coordinates in logs


def test_select_provider() -> None:
    assert isinstance(select_provider(Settings(google_maps_api_key=None)), NoRoutesProvider)
    google = select_provider(Settings(google_maps_api_key=KEY, environment="production"))
    assert isinstance(google, GoogleRoutesProvider)
    dev = select_provider(Settings(environment="development"), estimate_enabled=True)
    assert isinstance(dev, EstimateProvider)
    # A configured key wins over the dev estimate.
    assert isinstance(
        select_provider(Settings(google_maps_api_key=KEY), estimate_enabled=True),
        GoogleRoutesProvider,
    )


def test_estimate_impossible_in_production() -> None:
    prod = Settings(environment="production")
    with pytest.raises(EstimateNotAllowedError):
        select_provider(prod, estimate_enabled=True)
    with pytest.raises(EstimateNotAllowedError):
        select_provider(
            Settings(environment="production", google_maps_api_key=KEY), estimate_enabled=True
        )
    with pytest.raises(EstimateNotAllowedError):
        EstimateProvider(prod)


async def test_estimate_provider_is_unmetered_and_not_persistable() -> None:
    provider = EstimateProvider(Settings(environment="test"))
    assert not provider.metered and not provider.persistable
    (element,) = await provider.compute_matrix(
        [LatLng(16.0610, 108.2272)], [LatLng(16.0602, 108.2468)], "DRIVE"
    )
    assert element.available and element.distance_m and 2_000 < element.distance_m < 3_500
