"""Matrix service: cache first, misses only, quota per element, WALK gate (ADR-011, DEC-018)."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from pytest_httpx import HTTPXMock
from routing_fakes import NOW, FakeCache, FakeLedger, matrix_callback

from app.config import Settings
from app.routing.estimate import EstimateProvider
from app.routing.google_routes import COMPUTE_ROUTE_MATRIX_URL, GoogleRoutesProvider
from app.routing.matrix import LegSource, get_matrix
from app.routing.matrix_cache import CachedLeg
from app.routing.provider import LatLng, NoRoutesProvider
from app.routing.warm import warm_routes

GOOGLE = GoogleRoutesProvider("test-key-not-real")

# Đà Nẵng-like points: A, B, C within ~1.5 km of each other; D (Hội An) ~25 km away.
POINTS = {
    "anchor:dn-dragon-bridge": LatLng(16.0610, 108.2272),
    "place:aaaaaaaa-0000-0000-0000-000000000001": LatLng(16.0680, 108.2240),
    "place:aaaaaaaa-0000-0000-0000-000000000002": LatLng(16.0560, 108.2330),
    "web:bbbbbbbb-0000-0000-0000-000000000003": LatLng(15.8771, 108.3260),
}
KEYS = list(POINTS)


def _clock():  # type: ignore[no-untyped-def]
    return NOW


async def _matrix(provider, ledger, cache, mode="DRIVE", points=POINTS):  # type: ignore[no-untyped-def]
    return await get_matrix(
        None,
        keys_with_coords=points,
        mode=mode,
        ledger=ledger,
        provider=provider,
        cache=cache,
        clock=_clock,
    )


async def test_cold_matrix_fetches_all_pairs_once(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    httpx_mock.add_callback(matrix_callback(), url=COMPUTE_ROUTE_MATRIX_URL, is_reusable=True)
    matrix = await _matrix(GOOGLE, ledger, cache)
    assert len(matrix.legs) == 12
    assert all(leg.available and leg.source is LegSource.PROVIDER for leg in matrix.legs.values())
    assert matrix.duration_s(KEYS[0], KEYS[0]) == 0
    # One 4×4 rectangle: 12 legs plus 4 billed self pairs (discarded), one request.
    assert ledger.reserve_calls == [16]
    assert ledger.used == 16 and ledger.reserved == 0
    assert len(cache.writes) == 12
    assert matrix.stats.requested_elements == 16 and matrix.stats.cache_hits == 0


async def test_cache_hits_avoid_provider_calls(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    for o in KEYS:
        for d in KEYS:
            if o != d:
                cache.put(CachedLeg(o, d, True, 900, 300), "DRIVE", NOW + timedelta(days=3))
    matrix = await _matrix(GOOGLE, ledger, cache)
    assert httpx_mock.get_requests() == []
    assert ledger.reserve_calls == []
    assert matrix.duration_s(KEYS[1], KEYS[2]) == 300
    assert {leg.source for leg in matrix.legs.values()} == {LegSource.CACHE}


async def test_only_misses_are_requested(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    httpx_mock.add_callback(matrix_callback(), url=COMPUTE_ROUTE_MATRIX_URL, is_reusable=True)
    missing = {(KEYS[3], KEYS[0]), (KEYS[3], KEYS[1])}
    for o in KEYS:
        for d in KEYS:
            if o != d and (o, d) not in missing:
                cache.put(CachedLeg(o, d, True, 900, 300), "DRIVE", NOW + timedelta(days=3))
    matrix = await _matrix(GOOGLE, ledger, cache)
    (request,) = httpx_mock.get_requests()
    body = json.loads(request.content)
    assert len(body["origins"]) == 1 and len(body["destinations"]) == 2
    assert ledger.reserve_calls == [2]
    assert matrix.leg(KEYS[3], KEYS[0]).source is LegSource.PROVIDER
    assert matrix.stats.cache_hits == 10


async def test_expired_cache_rows_are_refetched(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    httpx_mock.add_callback(matrix_callback(), url=COMPUTE_ROUTE_MATRIX_URL, is_reusable=True)
    for o in KEYS:
        for d in KEYS:
            if o != d:
                cache.put(CachedLeg(o, d, True, 900, 300), "DRIVE", NOW - timedelta(seconds=1))
    matrix = await _matrix(GOOGLE, ledger, cache)
    assert matrix.stats.cache_hits == 0
    assert ledger.reserve_calls == [16]
    assert all(leg.source is LegSource.PROVIDER for leg in matrix.legs.values())


async def test_cached_no_route_is_unavailable_not_refetched(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    for o in KEYS:
        for d in KEYS:
            if o != d:
                cache.put(CachedLeg(o, d, False, None, None), "DRIVE", NOW + timedelta(days=1))
    matrix = await _matrix(GOOGLE, ledger, cache)
    assert httpx_mock.get_requests() == []
    assert matrix.duration_s(KEYS[0], KEYS[1]) is None
    assert matrix.leg(KEYS[0], KEYS[1]).source is LegSource.NO_ROUTE


async def test_quota_exhaustion_degrades_to_unavailable(
    httpx_mock: HTTPXMock, cache: FakeCache
) -> None:
    ledger = FakeLedger(cap=5)
    matrix = await _matrix(GOOGLE, ledger, cache)
    assert httpx_mock.get_requests() == []  # never called without a reservation
    assert len(matrix.legs) == 12
    assert all(
        not leg.available and leg.source is LegSource.QUOTA_EXHAUSTED
        for leg in matrix.legs.values()
    )
    assert matrix.stats.quota_denied_elements == 12  # legs, not billed elements
    assert cache.writes == []  # a denial is never cached


async def test_provider_error_committed_but_not_cached(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    httpx_mock.add_response(url=COMPUTE_ROUTE_MATRIX_URL, status_code=503)
    matrix = await _matrix(GOOGLE, ledger, cache)
    assert all(leg.source is LegSource.PROVIDER_ERROR for leg in matrix.legs.values())
    assert ledger.used == 16  # attempted ⇒ consumed (quota accounting rule)
    assert cache.writes == []
    assert matrix.stats.failed_elements == 12


async def test_no_route_from_google_is_cached_as_unavailable(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    httpx_mock.add_callback(
        matrix_callback(no_route={(1, 0)}), url=COMPUTE_ROUTE_MATRIX_URL, is_reusable=True
    )
    matrix = await _matrix(GOOGLE, ledger, cache)
    no_route = [p for p, leg in matrix.legs.items() if leg.source is LegSource.NO_ROUTE]
    assert len(no_route) == 1
    assert any(not w.available for w in cache.writes)


async def test_walk_only_for_pairs_within_2_5_km(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    httpx_mock.add_callback(matrix_callback(), url=COMPUTE_ROUTE_MATRIX_URL, is_reusable=True)
    matrix = await _matrix(GOOGLE, ledger, cache, mode="WALK")
    far = KEYS[3]
    for other in KEYS[:3]:
        assert matrix.leg(far, other).source is LegSource.WALK_TOO_FAR
        assert matrix.leg(other, far).source is LegSource.WALK_TOO_FAR
    assert sum(ledger.reserve_calls) == 9  # 3 near points: 6 legs + 3 self pairs
    for request in httpx_mock.get_requests():
        body = json.loads(request.content)
        assert body["travelMode"] == "WALK"
        coords = [o["waypoint"]["location"]["latLng"]["latitude"] for o in body["origins"]]
        assert 15.8771 not in coords


async def test_no_provider_configured_is_unavailable_without_quota(
    ledger: FakeLedger, cache: FakeCache
) -> None:
    matrix = await _matrix(NoRoutesProvider(), ledger, cache)
    assert all(leg.source is LegSource.NOT_CONFIGURED for leg in matrix.legs.values())
    assert ledger.reserve_calls == [] and cache.writes == []


async def test_estimates_are_marked_and_never_cached(ledger: FakeLedger, cache: FakeCache) -> None:
    matrix = await _matrix(EstimateProvider(Settings(environment="test")), ledger, cache)
    assert matrix.has_estimates
    assert all(leg.estimated for leg in matrix.legs.values())
    assert ledger.reserve_calls == [] and cache.writes == []


async def test_invalid_keys_rejected(ledger: FakeLedger, cache: FakeCache) -> None:
    with pytest.raises(ValueError):
        await _matrix(GOOGLE, ledger, cache, points={"gps:16.0,108.2": LatLng(16.0, 108.2)})


async def test_large_matrix_batches_and_reserves_per_request(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    httpx_mock.add_callback(matrix_callback(), url=COMPUTE_ROUTE_MATRIX_URL, is_reusable=True)
    points = {
        f"place:p{i:02d}": LatLng(16.0 + i * 0.002, 108.2 + (i % 5) * 0.002) for i in range(30)
    }
    matrix = await _matrix(GOOGLE, ledger, cache, points=points)
    assert len(matrix.legs) == 30 * 29
    assert all(leg.available for leg in matrix.legs.values())
    assert sum(ledger.reserve_calls) == 30 * 30  # needed legs + 30 self pairs
    for request in httpx_mock.get_requests():
        body = json.loads(request.content)
        assert len(body["origins"]) <= 25 and len(body["destinations"]) <= 25
        assert len(body["origins"]) * len(body["destinations"]) <= 625


async def test_warm_routes_fills_anchors_and_places(
    httpx_mock: HTTPXMock, ledger: FakeLedger, cache: FakeCache
) -> None:
    httpx_mock.add_callback(matrix_callback(), url=COMPUTE_ROUTE_MATRIX_URL, is_reusable=True)
    places = {k: v for k, v in POINTS.items() if not k.startswith("anchor:")}
    report = await warm_routes(
        None,  # points given ⇒ no catalog query
        ledger=ledger,
        provider=GOOGLE,
        points=places,
        cache=cache,
        clock=_clock,
    )
    assert report.points == 4 + 3  # 4 fixed anchors + 3 places
    assert report.by_mode["DRIVE"].requested_elements == 7 * 7
    assert report.by_mode["WALK"].requested_elements < 7 * 7
    # Second run is fully cached.
    before = len(httpx_mock.get_requests())
    again = await warm_routes(
        None,
        ledger=ledger,
        provider=GOOGLE,
        points=places,
        cache=cache,
        clock=_clock,
    )
    assert len(httpx_mock.get_requests()) == before
    assert again.by_mode["DRIVE"].cache_hits == 42
