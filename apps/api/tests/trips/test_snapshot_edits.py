"""Pure tests of the M2 manual-edit engine (no solver, sequential re-timing)."""

import uuid
from datetime import time

import pytest
from trip_fakes import FakeStore, day, verified_stop, web_stop

from app.errors import AppError
from app.schemas.trips import PreviewEditOperation
from app.trips.snapshot import PlanSnapshot, apply_edits, evaluate_health


def _plan() -> tuple[FakeStore, PlanSnapshot]:
    store = FakeStore()
    a, b, c = (store.make_publication(n) for n in ("A", "B", "C"))
    stops = [
        verified_stop(a, 1, time(9)),
        verified_stop(b, 2, time(11)),
        verified_stop(c, 3, time(13)),
    ]
    return store, PlanSnapshot.model_validate({"days": [day(1, stops)]})


def _edit(snapshot: PlanSnapshot, store: FakeStore, *ops: dict[str, object]) -> PlanSnapshot:
    result, _ = apply_edits(
        snapshot,
        [PreviewEditOperation.model_validate(op) for op in ops],
        day_count=2,
        default_mode="WALK",
        publications=store.published,
    )
    return result


def test_remove_and_resize_shift_following_stops() -> None:
    store, plan = _plan()
    first, second, third = plan.days[0].stops
    result = _edit(
        plan,
        store,
        {"op": "REMOVE_STOP", "stop_id": str(second.id)},
        {"op": "SET_VISIT_MINUTES", "stop_id": str(first.id), "visit_minutes": 30},
    )
    stops = result.days[0].stops
    assert [s.id for s in stops] == [first.id, third.id]
    assert (stops[0].planned_arrival, stops[0].planned_departure) == (time(9), time(9, 30))
    # The new A→C leg is unmeasured (EXPIRED), so C follows A directly.
    assert stops[1].planned_arrival == time(9, 30)
    assert result.days[0].legs[0].availability == "EXPIRED"
    assert result.days[0].legs[0].distance_m is None


def test_leg_mode_change_drops_measurement_and_warns() -> None:
    store, plan = _plan()
    first, second, _ = plan.days[0].stops
    result, health = apply_edits(
        plan,
        [
            PreviewEditOperation(
                op="SET_LEG_MODE", from_stop_id=first.id, to_stop_id=second.id, travel_mode="DRIVE"
            )
        ],
        day_count=1,
        default_mode="WALK",
        publications={},
    )
    leg = result.days[0].legs[0]
    assert (leg.travel_mode, leg.availability, leg.duration_s) == ("DRIVE", "EXPIRED", None)
    assert health == "WARNING"


def test_invalid_edits_are_rejected() -> None:
    store, plan = _plan()
    first, _, third = plan.days[0].stops
    with pytest.raises(AppError) as unknown:
        _edit(plan, store, {"op": "LOCK_STOP", "stop_id": str(uuid.uuid4())})
    assert unknown.value.code == "unknown_stop"
    with pytest.raises(AppError) as not_consecutive:
        _edit(
            plan,
            store,
            {
                "op": "SET_LEG_MODE",
                "from_stop_id": str(first.id),
                "to_stop_id": str(third.id),
                "travel_mode": "DRIVE",
            },
        )
    assert not_consecutive.value.code == "unknown_leg"
    with pytest.raises(AppError) as duplicate:
        _edit(plan, store, {"op": "ADD_STOP", "day_index": 1, "place_id": str(first.place_id)})
    assert duplicate.value.code == "duplicate_place"
    with pytest.raises(AppError) as overflow:
        _edit(
            plan,
            store,
            *[
                {"op": "SET_VISIT_MINUTES", "stop_id": str(s.id), "visit_minutes": 600}
                for s in plan.days[0].stops
            ],
        )
    assert overflow.value.code == "day_overflow"


def test_day_window_exceeded_is_a_warning() -> None:
    store, plan = _plan()
    third = plan.days[0].stops[2]
    result, health = apply_edits(
        plan,
        [PreviewEditOperation(op="SET_VISIT_MINUTES", stop_id=third.id, visit_minutes=480)],
        day_count=1,
        default_mode="WALK",
        publications={},
    )
    assert health == "WARNING"
    assert [c.type for c in result.days[0].stops[2].conflicts] == ["DAY_WINDOW_EXCEEDED"]


def test_web_stop_caps_health_at_warning() -> None:
    store = FakeStore()
    cand = store.make_candidate("Cafe")
    plan = PlanSnapshot.model_validate({"days": [day(1, [web_stop(cand, 1, time(9))])]})
    health, reasons = evaluate_health(plan)
    assert health == "WARNING"
    assert [r.type for r in reasons] == ["WEB_PLACE_UNVERIFIED"]


def test_snapshot_rejects_mixed_stop_shape() -> None:
    store = FakeStore()
    pub = store.make_publication("A")
    stop = verified_stop(pub, 1, time(9))
    stop["web_place_candidate_id"] = str(uuid.uuid4())
    with pytest.raises(ValueError):
        PlanSnapshot.model_validate({"days": [day(1, [stop])]})
