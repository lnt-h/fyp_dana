"""HTTP behaviour of trips, previews, Save and deletion against the in-memory store."""

import json
import uuid
from datetime import time
from typing import Any

from httpx import AsyncClient
from trip_fakes import World, day, verified_stop, web_stop

from app.config import Settings, get_settings
from app.planning.workflows import NotImplementedWorkflow, get_planning_workflow


def _two_revision_preview(world: World) -> tuple[Any, Any, dict[str, Any]]:
    """Revision 1: two verified stops. Revision 2 adds a WEB_UNVERIFIED stop."""
    store = world.store
    trip = store.make_trip(world.account_id, world.city.id)
    museum = store.make_publication("Museum")
    bridge = store.make_publication("Bridge")
    cafe = store.make_candidate("Cafe on the web")
    first = [verified_stop(museum, 1, time(9, 0)), verified_stop(bridge, 2, time(11, 0))]
    rev1 = {"days": [day(1, first)]}
    rev2 = {"days": [day(1, [*first, web_stop(cafe, 3, time(13, 0))])]}
    preview = store.make_preview(trip, [rev1, rev2])
    return trip, preview, rev2


def _accept_body(preview: Any, trip: Any, **extra: Any) -> dict[str, Any]:
    return {
        "expected_preview_revision": preview.head_revision,
        "expected_trip_revision": trip.revision,
        **extra,
    }


# ---- ownership -------------------------------------------------------------------------------


async def test_foreign_trip_and_preview_are_not_found(world: World, client: AsyncClient) -> None:
    other = uuid.uuid4()
    trip = world.store.make_trip(other, world.city.id)
    pub = world.store.make_publication("Museum")
    preview = world.store.make_preview(trip, [{"days": [day(1, [verified_stop(pub, 1, time(9))])]}])
    key = {"Idempotency-Key": str(uuid.uuid4())}

    responses = [
        await client.get(f"/v1/trips/{trip.id}"),
        await client.patch(f"/v1/trips/{trip.id}", json={"expected_revision": 0, "title": "x"}),
        await client.delete(f"/v1/trips/{trip.id}?expected_revision=0"),
        await client.get(f"/v1/trips/{trip.id}/stops/{uuid.uuid4()}/place-card"),
        await client.get(f"/v1/trips/{trip.id}/handoff-links?kind=STAY"),
        await client.get(f"/v1/plan-previews/{preview.id}"),
        await client.patch(
            f"/v1/plan-previews/{preview.id}",
            json={
                "expected_revision": 1,
                "edits": [{"op": "LOCK_STOP", "stop_id": str(uuid.uuid4())}],
            },
        ),
        await client.post(
            f"/v1/plan-previews/{preview.id}/accept",
            json=_accept_body(preview, trip),
            headers=key,
        ),
        await client.post(
            f"/v1/trips/{trip.id}/plan-previews",
            json={"source": "GENERATE", "expected_trip_revision": 0, "locale": "vi"},
        ),
    ]
    for response in responses:
        assert response.status_code == 404, response.text
        assert response.json()["error"]["code"] == "resource_not_found"
    assert world.store.saves == 0
    assert trip.id in world.store.trips


async def test_create_and_list_trips(world: World, client: AsyncClient) -> None:
    response = await client.post(
        "/v1/trips",
        json={"city_id": str(world.city.id), "start_date": "2026-12-01", "day_count": 3},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "DRAFT" and body["revision"] == 0
    assert response.headers["location"] == f"/v1/trips/{body['id']}"

    listing = await client.get("/v1/trips")
    assert [item["id"] for item in listing.json()["items"]] == [body["id"]]

    disabled = world.store.add_city(enabled=False)
    refused = await client.post(
        "/v1/trips",
        json={"city_id": str(disabled.id), "start_date": "2026-12-01", "day_count": 1},
    )
    assert refused.status_code == 422
    assert refused.json()["error"]["code"] == "unsupported_request"


async def test_trip_patch_checks_revision_without_advancing_it(
    world: World, client: AsyncClient
) -> None:
    trip = world.store.make_trip(world.account_id, world.city.id, status="SAVED", revision=2)
    stale = await client.patch(f"/v1/trips/{trip.id}", json={"expected_revision": 1, "title": "A"})
    assert stale.status_code == 409
    assert stale.json()["error"]["context"] == {"expected_revision": 1, "current_revision": 2}
    ok = await client.patch(f"/v1/trips/{trip.id}", json={"expected_revision": 2, "title": "A"})
    assert ok.status_code == 200
    assert ok.json()["title"] == "A" and ok.json()["revision"] == 2


# ---- Save ------------------------------------------------------------------------------------


async def test_accept_requires_acknowledgement_for_web_stop(
    world: World, client: AsyncClient
) -> None:
    trip, preview, _ = _two_revision_preview(world)
    headers = {"Idempotency-Key": str(uuid.uuid4())}
    refused = await client.post(
        f"/v1/plan-previews/{preview.id}/accept", json=_accept_body(preview, trip), headers=headers
    )
    assert refused.status_code == 422
    error = refused.json()["error"]
    assert error["code"] == "web_unverified_acknowledgement_required"
    assert len(error["context"]["stop_ids"]) == 1
    assert world.store.saves == 0 and trip.revision == 0

    # The failed attempt left no idempotency record, so the same key can carry the corrected body.
    saved = await client.post(
        f"/v1/plan-previews/{preview.id}/accept",
        json=_accept_body(preview, trip, acknowledge_web_unverified=True),
        headers=headers,
    )
    assert saved.status_code == 200, saved.text
    assert saved.headers["idempotent-replayed"] == "false"
    body = saved.json()
    assert body["status"] == "SAVED" and body["revision"] == 1
    stops = body["days"][0]["stops"]
    web = [stop for stop in stops if stop["trust_level"] == "WEB_UNVERIFIED"]
    assert len(web) == 1
    assert web[0]["place_id"] is None and web[0]["catalog_publication_id"] is None
    assert web[0]["web_source"]["url"] == "https://example.com/cafe"
    assert stops[0]["trust_level"] == "VERIFIED" and stops[0]["name"] == "Museum VI"
    assert stops[0]["planned_arrival"] == "2026-12-01T09:00:00+07:00"
    assert world.store.previews[preview.id].status == "SAVED"


async def test_accept_replay_returns_stored_response(world: World, client: AsyncClient) -> None:
    trip, preview, _ = _two_revision_preview(world)
    headers = {"Idempotency-Key": str(uuid.uuid4())}
    body = _accept_body(preview, trip, acknowledge_web_unverified=True)
    first = await client.post(f"/v1/plan-previews/{preview.id}/accept", json=body, headers=headers)
    second = await client.post(f"/v1/plan-previews/{preview.id}/accept", json=body, headers=headers)
    assert first.status_code == second.status_code == 200
    assert second.headers["idempotent-replayed"] == "true"
    assert second.json() == first.json()
    assert world.store.saves == 1 and trip.revision == 1

    reused = await client.post(
        f"/v1/plan-previews/{preview.id}/accept",
        json={**body, "expected_trip_revision": 1},
        headers=headers,
    )
    assert reused.status_code == 409
    assert reused.json()["error"]["code"] == "idempotency_key_reused"

    # A new key after Save: the preview is closed.
    closed = await client.post(
        f"/v1/plan-previews/{preview.id}/accept",
        json={**body, "expected_trip_revision": 1},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert closed.status_code == 410
    assert world.store.saves == 1


async def test_accept_revision_conflicts(world: World, client: AsyncClient) -> None:
    trip, preview, _ = _two_revision_preview(world)
    stale_preview = await client.post(
        f"/v1/plan-previews/{preview.id}/accept",
        json={"expected_preview_revision": 1, "expected_trip_revision": 0},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert stale_preview.status_code == 409
    error = stale_preview.json()["error"]
    assert error["code"] == "revision_conflict"
    assert error["context"] == {"expected_preview_revision": 1, "current_revision": 2}

    trip.revision, trip.status = 3, "SAVED"
    stale_trip = await client.post(
        f"/v1/plan-previews/{preview.id}/accept",
        json={"expected_preview_revision": 2, "expected_trip_revision": 0},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert stale_trip.status_code == 409
    assert stale_trip.json()["error"]["context"]["current_revision"] == 3

    # Matching the trip's current revision is not enough when the preview was based on an older one.
    based_on_old = await client.post(
        f"/v1/plan-previews/{preview.id}/accept",
        json={"expected_preview_revision": 2, "expected_trip_revision": 3},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert based_on_old.status_code == 409
    assert world.store.saves == 0 and world.store.idem == {}


async def test_accept_refuses_blocked_plan_and_missing_key(
    world: World, client: AsyncClient
) -> None:
    trip = world.store.make_trip(world.account_id, world.city.id)
    pub = world.store.make_publication("Museum")
    preview = world.store.make_preview(
        trip, [{"days": [day(1, [verified_stop(pub, 1, time(9))])]}], health="BLOCKED"
    )
    missing = await client.post(
        f"/v1/plan-previews/{preview.id}/accept", json=_accept_body(preview, trip)
    )
    assert missing.status_code == 422
    blocked = await client.post(
        f"/v1/plan-previews/{preview.id}/accept",
        json=_accept_body(preview, trip),
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "plan_blocked"


async def test_accept_refuses_withdrawn_publication(world: World, client: AsyncClient) -> None:
    trip = world.store.make_trip(world.account_id, world.city.id)
    pub = world.store.make_publication("Museum")
    preview = world.store.make_preview(trip, [{"days": [day(1, [verified_stop(pub, 1, time(9))])]}])
    world.store.pubs[pub.id] = type(pub)(**{**pub.__dict__, "state": "WITHDRAWN"})
    response = await client.post(
        f"/v1/plan-previews/{preview.id}/accept",
        json=_accept_body(preview, trip),
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "publication_incomplete"


# ---- Manual edits ----------------------------------------------------------------------------


async def test_edit_appends_manual_revision_and_checks_expected_revision(
    world: World, client: AsyncClient
) -> None:
    trip, preview, rev2 = _two_revision_preview(world)
    stops = rev2["days"][0]["stops"]
    stale = await client.patch(
        f"/v1/plan-previews/{preview.id}",
        json={"expected_revision": 1, "edits": [{"op": "LOCK_STOP", "stop_id": stops[0]["id"]}]},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["context"]["current_revision"] == 2

    edited = await client.patch(
        f"/v1/plan-previews/{preview.id}",
        json={
            "expected_revision": 2,
            "edits": [
                {"op": "MOVE_STOP", "stop_id": stops[2]["id"], "day_index": 1, "to_ordinal": 1},
                {"op": "LOCK_STOP", "stop_id": stops[1]["id"]},
            ],
        },
    )
    assert edited.status_code == 200, edited.text
    body = edited.json()
    assert body["preview_revision"] == 3 and body["parent_revision"] == 2
    assert body["origin"] == "MANUAL_EDIT" and body["plan_health"] == "WARNING"
    new_stops = body["days"][0]["stops"]
    assert [s["id"] for s in new_stops] == [stops[2]["id"], stops[0]["id"], stops[1]["id"]]
    # Sequential shift: the new first stop starts at the day window, no measured legs before the
    # kept museum→bridge leg, which keeps its 10-minute duration.
    assert [s["planned_arrival"][11:16] for s in new_stops] == ["08:00", "09:00", "10:10"]
    assert new_stops[2]["is_locked"] is True
    assert any(r["type"] == "WEB_PLACE_UNVERIFIED" for r in body["health_reasons"])


async def test_edit_rejects_place_outside_catalog(world: World, client: AsyncClient) -> None:
    trip, preview, _ = _two_revision_preview(world)
    response = await client.patch(
        f"/v1/plan-previews/{preview.id}",
        json={
            "expected_revision": 2,
            "edits": [{"op": "ADD_STOP", "day_index": 1, "place_id": str(uuid.uuid4())}],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "place_not_in_city"
    assert preview.head_revision == 2


# ---- Planning shells -------------------------------------------------------------------------


def _events(body: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in body.split("\n\n"):
        if not block or block.startswith(":"):
            continue
        name, data = block.split("\n")
        events.append((name.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return events


async def test_plan_preview_stream_ends_with_not_implemented(
    world: World, client: AsyncClient
) -> None:
    trip = world.store.make_trip(world.account_id, world.city.id)
    # Route plumbing with the stub workflow (the orchestrator itself is tested in tests/planning).
    world.app.dependency_overrides[get_planning_workflow] = NotImplementedWorkflow
    async with client.stream(
        "POST",
        f"/v1/trips/{trip.id}/plan-previews",
        json={"source": "GENERATE", "expected_trip_revision": 0, "locale": "vi"},
        headers={"Accept": "text/event-stream", "X-Request-ID": "req-plan"},
    ) as response:
        body = "".join([chunk async for chunk in response.aiter_text()])
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _events(body)
    assert len(events) == 1
    name, data = events[0]
    assert name == "error"
    assert data["error"]["code"] == "not_implemented"
    assert data["error"]["retryable"] is False
    assert data["error"]["request_id"] == "req-plan"

    json_mode = await client.post(
        f"/v1/trips/{trip.id}/plan-previews",
        json={"source": "GENERATE", "expected_trip_revision": 0, "locale": "vi"},
    )
    assert json_mode.status_code == 501
    assert json_mode.json()["error"]["code"] == "not_implemented"

    invalid = await client.post(
        f"/v1/trips/{trip.id}/plan-previews", json={"source": "GENERATE", "locale": "vi"}
    )
    assert invalid.status_code == 422


async def test_regenerate_uses_injected_workflow(world: World, client: AsyncClient) -> None:
    trip, preview, _ = _two_revision_preview(world)
    calls: list[Any] = []

    class Recorder:
        async def propose_trip(self, command: Any, sink: Any) -> None:  # pragma: no cover
            raise AssertionError

        async def regenerate_day(self, command: Any, sink: Any) -> None:
            calls.append(command)
            sink.emit({"type": "progress", "stage": "SCHEDULING"})
            sink.emit({"type": "error", "error": {"code": "quota_exceeded", "message": "x"}})
            sink.close()

    world.app.dependency_overrides[get_planning_workflow] = Recorder
    response = await client.post(
        f"/v1/plan-previews/{preview.id}/regenerate",
        json={"expected_revision": 2, "day_index": 1},
    )
    assert response.status_code == 429
    assert calls[0].preview_id == preview.id and calls[0].trip_id == trip.id


# ---- Stays and deletion ----------------------------------------------------------------------


async def test_stay_prices_flag(world: World, client: AsyncClient) -> None:
    trip = world.store.make_trip(world.account_id, world.city.id)
    off = await client.get(f"/v1/trips/{trip.id}/stay-prices")
    assert off.status_code == 404 and off.json()["error"]["code"] == "feature_disabled"
    world.app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,  # type: ignore[call-arg]
        stay_prices_enabled=True,
    )
    on = await client.get(f"/v1/trips/{trip.id}/stay-prices")
    assert on.status_code == 501 and on.json()["error"]["code"] == "not_implemented"
    assert on.headers["cache-control"] == "no-store"


async def test_handoff_links(world: World, client: AsyncClient) -> None:
    draft = world.store.make_trip(world.account_id, world.city.id)
    refused = await client.get(f"/v1/trips/{draft.id}/handoff-links?kind=STAY")
    assert refused.status_code == 409
    assert refused.json()["error"]["code"] == "trip_not_saved"

    trip, preview, _ = _two_revision_preview(world)
    await client.post(
        f"/v1/plan-previews/{preview.id}/accept",
        json=_accept_body(preview, trip, acknowledge_web_unverified=True),
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    stay = (await client.get(f"/v1/trips/{trip.id}/handoff-links?kind=STAY")).json()
    assert stay["partner_key"] == "agoda"
    assert "checkIn=2026-12-01" in stay["url"] and "checkOut=2026-12-02" in stay["url"]
    assert stay["end_date"] == "2026-12-02"
    booking = (
        await client.get(f"/v1/trips/{trip.id}/handoff-links?kind=STAY&partner=booking_com")
    ).json()
    assert booking["url"].startswith("https://www.booking.com/searchresults.html?ss=Da+Nang")
    transport = (await client.get(f"/v1/trips/{trip.id}/handoff-links?kind=TRANSPORT")).json()
    assert transport["partner_key"] == "twelve_go" and "date=2026-12-01" in transport["url"]
    no_stop = await client.get(f"/v1/trips/{trip.id}/handoff-links?kind=ACTIVITY")
    assert no_stop.status_code == 422
    stop_id = world.store.saved[trip.id].days[0].stops[0].id
    activity = (
        await client.get(f"/v1/trips/{trip.id}/handoff-links?kind=ACTIVITY&stop_id={stop_id}")
    ).json()
    assert activity["partner_key"] == "klook" and "Museum+EN" in activity["url"]
    wrong = await client.get(f"/v1/trips/{trip.id}/handoff-links?kind=STAY&partner=klook")
    assert wrong.status_code == 422


async def test_deletion_request_is_idempotent_by_state(world: World, client: AsyncClient) -> None:
    assert (await client.get("/v1/me/deletion")).status_code == 404
    refused = await client.post("/v1/me/deletion", json={"confirm": False})
    assert refused.status_code == 422
    first = await client.post("/v1/me/deletion", json={"confirm": True})
    second = await client.post("/v1/me/deletion", json={"confirm": True})
    assert first.status_code == second.status_code == 202
    assert first.headers["location"] == "/v1/me/deletion"
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["status"] == "REQUESTED"
    status = await client.get("/v1/me/deletion")
    assert status.status_code == 200 and status.json()["id"] == first.json()["id"]
    assert len(world.store.jobs) == 1
