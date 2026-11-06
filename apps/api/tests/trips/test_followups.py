"""Deletion guard and TRIP_CREATE / PREVIEW_EDIT idempotency against the in-memory store."""

import uuid
from datetime import time
from typing import Any

import pytest
from httpx import AsyncClient
from trip_fakes import World, day, verified_stop

from app.config import Settings

# ---- deletion guard ---------------------------------------------------------------------------


async def test_open_deletion_job_blocks_every_route_except_deletion(
    world: World, client: AsyncClient
) -> None:
    trip = world.store.make_trip(world.account_id, world.city.id)
    assert (await client.get("/v1/trips")).status_code == 200
    first = await client.post("/v1/me/deletion", json={"confirm": True})
    assert first.status_code == 202

    for method, path in [
        ("GET", "/v1/trips"),
        ("GET", f"/v1/trips/{trip.id}"),
        ("GET", "/v1/me/preferences"),
        ("DELETE", f"/v1/trips/{trip.id}?expected_revision=0"),
    ]:
        blocked = await client.request(method, path)
        assert blocked.status_code == 409, (method, path, blocked.text)
        assert blocked.json()["error"]["code"] == "deletion_in_progress"
    created = await client.post(
        "/v1/trips", json={"city_id": str(world.city.id), "day_count": 1, "start_date": None}
    )
    assert created.status_code == 409
    assert len(world.store.trips) == 1

    # The two deletion routes stay available: POST returns the open job, GET its status.
    again = await client.post("/v1/me/deletion", json={"confirm": True})
    assert again.status_code == 202 and again.json()["id"] == first.json()["id"]
    status = await client.get("/v1/me/deletion")
    assert status.status_code == 200 and status.json()["status"] == "REQUESTED"


@pytest.mark.parametrize("state", ["IN_PROGRESS", "FAILED"])
async def test_guard_covers_in_progress_and_failed(
    world: World, client: AsyncClient, state: str
) -> None:
    job = await world.store.add_deletion_job(world.account_id)
    job.status = state
    assert (await client.get("/v1/trips")).status_code == 409
    job.status = "COMPLETED"
    job.account_id = None
    assert (await client.get("/v1/trips")).status_code == 200


# ---- TRIP_CREATE ------------------------------------------------------------------------------


async def test_create_trip_replays_with_same_key(world: World, client: AsyncClient) -> None:
    body = {"city_id": str(world.city.id), "start_date": "2026-12-01", "day_count": 2}
    key = {"Idempotency-Key": str(uuid.uuid4())}
    first = await client.post("/v1/trips", json=body, headers=key)
    second = await client.post("/v1/trips", json=body, headers=key)
    assert first.status_code == second.status_code == 201
    assert first.headers["idempotent-replayed"] == "false"
    assert second.headers["idempotent-replayed"] == "true"
    assert second.json() == first.json()
    assert second.headers["location"] == f"/v1/trips/{first.json()['id']}"
    assert len(world.store.trips) == 1

    reused = await client.post("/v1/trips", json={**body, "day_count": 3}, headers=key)
    assert reused.status_code == 409
    assert reused.json()["error"]["code"] == "idempotency_key_reused"

    plain = await client.post("/v1/trips", json=body)
    assert plain.status_code == 201 and "idempotent-replayed" not in plain.headers
    assert len(world.store.trips) == 2

    bad = await client.post("/v1/trips", json=body, headers={"Idempotency-Key": "nope"})
    assert bad.status_code == 422


async def test_failed_create_leaves_no_record(world: World, client: AsyncClient) -> None:
    disabled = world.store.add_city(enabled=False)
    key = {"Idempotency-Key": str(uuid.uuid4())}
    body: dict[str, Any] = {"city_id": str(disabled.id), "day_count": 1, "start_date": None}
    assert (await client.post("/v1/trips", json=body, headers=key)).status_code == 422
    assert world.store.idem == {}


# ---- PREVIEW_EDIT -----------------------------------------------------------------------------


async def test_edit_preview_replays_instead_of_revision_conflict(
    world: World, client: AsyncClient
) -> None:
    store = world.store
    trip = store.make_trip(world.account_id, world.city.id)
    museum = store.make_publication("Museum")
    stops = [verified_stop(museum, 1, time(9, 0))]
    preview = store.make_preview(trip, [{"days": [day(1, stops)]}])
    body = {"expected_revision": 1, "edits": [{"op": "LOCK_STOP", "stop_id": stops[0]["id"]}]}
    key = {"Idempotency-Key": str(uuid.uuid4())}

    first = await client.patch(f"/v1/plan-previews/{preview.id}", json=body, headers=key)
    assert first.status_code == 200, first.text
    assert first.headers["idempotent-replayed"] == "false"
    assert first.json()["preview_revision"] == 2

    retry = await client.patch(f"/v1/plan-previews/{preview.id}", json=body, headers=key)
    assert retry.status_code == 200
    assert retry.headers["idempotent-replayed"] == "true"
    assert retry.json() == first.json()

    unkeyed = await client.patch(f"/v1/plan-previews/{preview.id}", json=body)
    assert unkeyed.status_code == 409
    assert unkeyed.json()["error"]["code"] == "revision_conflict"

    other = {**body, "expected_revision": 2}
    reused = await client.patch(f"/v1/plan-previews/{preview.id}", json=other, headers=key)
    assert reused.status_code == 409
    assert reused.json()["error"]["code"] == "idempotency_key_reused"


async def test_edit_replay_still_checks_owner(world: World, client: AsyncClient) -> None:
    store = world.store
    trip = store.make_trip(uuid.uuid4(), world.city.id)
    preview = store.make_preview(trip, [{"days": [day(1, [])]}])
    response = await client.patch(
        f"/v1/plan-previews/{preview.id}",
        json={
            "expected_revision": 1,
            "edits": [{"op": "LOCK_STOP", "stop_id": str(uuid.uuid4())}],
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 404
    assert store.pending_idem == {} and store.idem == {}


# ---- settings ---------------------------------------------------------------------------------


def test_clerk_secret_blank_is_unset_and_routes_default() -> None:
    settings = Settings(_env_file=None, clerk_secret_key="  ")  # type: ignore[call-arg]
    assert settings.clerk_secret_key is None
    assert Settings(_env_file=None).quota_routes_elements_per_day == 300  # type: ignore[call-arg]
