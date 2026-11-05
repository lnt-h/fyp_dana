"""The ``preview_revisions.snapshot`` document and the M2 manual-edit engine.

The snapshot is the stored, immutable shape of one preview revision. It holds identifiers and
planned local times only; display names, coordinates and web provenance are resolved at read time
from the pinned publication or the ``web_place_candidates`` row, so a snapshot never authors facts.

Manual edits (API-020) run no selection, routing or solver (that is M3, architecture §3.2). The M2
re-timing rule is **sequential shift within the day**: the first stop keeps its arrival (a new first
stop starts at the day window), every later stop arrives at the previous departure plus the leg
duration when that leg is measured (0 otherwise) and departs ``visit_minutes`` later. Legs whose
endpoints or mode changed lose their measurement (``EXPIRED``, null distance/duration) until M3
re-measures them.
"""

import uuid
from datetime import datetime, time
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.errors import AppError, validation_failed
from app.schemas.trips import Conflict, PlanHealth, PreviewEditOperation, TravelMode, TrustLevel

LegAvailability = Literal["AVAILABLE", "UNAVAILABLE", "EXPIRED"]


class _Snap(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SnapshotStop(_Snap):
    id: uuid.UUID
    trust_level: TrustLevel = "VERIFIED"
    place_id: uuid.UUID | None = None
    catalog_publication_id: uuid.UUID | None = None
    web_place_candidate_id: uuid.UUID | None = None
    ordinal: int = Field(ge=1)
    planned_arrival: time
    planned_departure: time
    visit_minutes: int = Field(ge=1, le=600)
    is_locked: bool = False
    rationale: str | None = None
    conflicts: list[Conflict] = Field(default_factory=list)

    @model_validator(mode="after")
    def _shape(self) -> Self:
        # Mirrors ck_trip_stops_shape: exactly one of (published place + publication) or candidate.
        if self.trust_level == "VERIFIED":
            ok = (
                self.place_id is not None
                and self.catalog_publication_id is not None
                and self.web_place_candidate_id is None
            )
        else:
            ok = (
                self.web_place_candidate_id is not None
                and self.place_id is None
                and self.catalog_publication_id is None
            )
        if not ok:
            raise ValueError("stop shape does not match its trust_level")
        if self.planned_arrival >= self.planned_departure:
            raise ValueError("planned_arrival must be before planned_departure")
        return self


class SnapshotLeg(_Snap):
    from_stop_id: uuid.UUID
    to_stop_id: uuid.UUID
    travel_mode: TravelMode
    availability: LegAvailability
    distance_m: int | None = Field(default=None, ge=0)
    duration_s: int | None = Field(default=None, ge=0)
    data_provider_id: uuid.UUID | None = None
    measured_at: datetime | None = None
    expires_at: datetime | None = None
    conflicts: list[Conflict] = Field(default_factory=list)

    @model_validator(mode="after")
    def _measurement(self) -> Self:
        # Mirrors ck_route_legs_measurement.
        measured = (
            self.distance_m is not None
            and self.duration_s is not None
            and self.data_provider_id is not None
            and self.measured_at is not None
        )
        if (self.availability == "AVAILABLE") != measured:
            raise ValueError("AVAILABLE legs, and only they, carry a full measurement")
        return self


class SnapshotDay(_Snap):
    day_index: int = Field(ge=1, le=3)
    day_window_start: time
    day_window_end: time
    stops: list[SnapshotStop] = Field(default_factory=list)
    legs: list[SnapshotLeg] = Field(default_factory=list)


class PlanSnapshot(_Snap):
    days: list[SnapshotDay]
    health_reasons: list[Conflict] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    research_used: bool = False
    agent_run_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _unique(self) -> Self:
        stop_ids = [stop.id for day in self.days for stop in day.stops]
        if len(stop_ids) != len(set(stop_ids)):
            raise ValueError("stop ids must be unique")
        indices = [day.day_index for day in self.days]
        if len(indices) != len(set(indices)):
            raise ValueError("day_index must be unique")
        return self

    def all_stops(self) -> list[SnapshotStop]:
        return [stop for day in self.days for stop in day.stops]

    def has_web_unverified(self) -> bool:
        return any(stop.trust_level == "WEB_UNVERIFIED" for stop in self.all_stops())


class PublishedPlace(BaseModel):
    """Current publication of a place, as needed by ADD_STOP / REPLACE_STOP."""

    place_id: uuid.UUID
    catalog_publication_id: uuid.UUID
    visit_minutes_min: int
    visit_minutes_suggested: int
    visit_minutes_max: int


SEVERITY_HEALTH: dict[str, PlanHealth] = {"BLOCKING": "BLOCKED", "WARNING": "WARNING"}


def evaluate_health(snapshot: PlanSnapshot) -> tuple[PlanHealth, list[Conflict]]:
    """M2 Plan Health for a manual edit: worst severity among carried conflicts.

    ``snapshot.health_reasons`` holds plan-level reasons only; stop and leg conflicts are folded in
    here, so the returned list is what ``PlanPreview.health_reasons`` shows.

    A ``WEB_UNVERIFIED`` stop caps the plan at WARNING (ADR-011) and an unmeasured leg is reported
    as WARNING too (its duration was taken as 0 by the sequential re-timing). The calendar-rule
    engine replaces this in M3.
    """
    reasons: list[Conflict] = [
        reason for reason in snapshot.health_reasons if reason.type != "WEB_PLACE_UNVERIFIED"
    ]
    for day in snapshot.days:
        for stop in day.stops:
            reasons.extend(stop.conflicts)
        for leg in day.legs:
            reasons.extend(leg.conflicts)
    if snapshot.has_web_unverified():
        reasons.append(
            Conflict(
                type="WEB_PLACE_UNVERIFIED",
                severity="WARNING",
                message="The plan contains a place found on the web that is not verified.",
            )
        )
    health: PlanHealth = "GOOD"
    for reason in reasons:
        level = SEVERITY_HEALTH[reason.severity]
        if level == "BLOCKED":
            health = "BLOCKED"
        elif health == "GOOD":
            health = "WARNING"
    if health == "GOOD" and any(
        leg.availability != "AVAILABLE" for day in snapshot.days for leg in day.legs
    ):
        health = "WARNING"
    # Health reasons at plan level are de-duplicated by (type, message).
    unique: dict[tuple[str, str | None], Conflict] = {}
    for reason in reasons:
        unique.setdefault((reason.type, reason.message), reason)
    return health, list(unique.values())


def _add_minutes(value: time, minutes: float) -> time:
    total = value.hour * 60 + value.minute + value.second / 60 + minutes
    if total >= 24 * 60:
        raise validation_failed(
            "day_overflow", "The edited day runs past midnight; remove or shorten a stop."
        )
    whole = int(total)
    return time(whole // 60, whole % 60)


class _Editor:
    def __init__(
        self,
        snapshot: PlanSnapshot,
        *,
        day_count: int,
        default_mode: TravelMode,
        publications: dict[uuid.UUID, PublishedPlace],
    ) -> None:
        self.day_count = day_count
        self.default_mode: TravelMode = default_mode
        self.publications = publications
        self.days: dict[int, list[SnapshotStop]] = {
            day.day_index: [stop.model_copy(deep=True) for stop in day.stops]
            for day in snapshot.days
        }
        self.windows = {
            day.day_index: (day.day_window_start, day.day_window_end) for day in snapshot.days
        }
        self.original_legs = {
            (leg.from_stop_id, leg.to_stop_id): leg for day in snapshot.days for leg in day.legs
        }
        self.mode_overrides: dict[tuple[uuid.UUID, uuid.UUID], TravelMode] = {}
        self.original_first_arrival = {
            day.day_index: (day.stops[0].id, day.stops[0].planned_arrival)
            for day in snapshot.days
            if day.stops
        }
        self.snapshot = snapshot

    # -- lookups -------------------------------------------------------------------------------

    def _locate(self, stop_id: uuid.UUID | None, index: int) -> tuple[int, int]:
        if stop_id is None:
            raise validation_failed(
                "validation_failed", "stop_id is required", edit_index=index, field="stop_id"
            )
        for day_index, stops in self.days.items():
            for position, stop in enumerate(stops):
                if stop.id == stop_id:
                    return day_index, position
        raise validation_failed(
            "unknown_stop", "stop_id is not part of this preview revision", edit_index=index
        )

    def _publication(self, place_id: uuid.UUID | None, index: int) -> PublishedPlace:
        if place_id is None:
            raise validation_failed(
                "validation_failed", "place_id is required", edit_index=index, field="place_id"
            )
        published = self.publications.get(place_id)
        if published is None:
            raise validation_failed(
                "place_not_in_city",
                "The place is not published in this trip's city",
                edit_index=index,
            )
        if any(stop.place_id == place_id for stops in self.days.values() for stop in stops):
            raise validation_failed(
                "duplicate_place", "The place is already part of this plan", edit_index=index
            )
        return published

    def _day(self, day_index: int | None, index: int) -> list[SnapshotStop]:
        if day_index is None:
            raise validation_failed(
                "validation_failed", "day_index is required", edit_index=index, field="day_index"
            )
        if day_index > self.day_count:
            raise validation_failed(
                "validation_failed",
                "day_index exceeds the trip's day_count",
                edit_index=index,
                day_count=self.day_count,
            )
        if day_index not in self.days:
            raise validation_failed(
                "validation_failed", "day_index is not part of this preview", edit_index=index
            )
        return self.days[day_index]

    @staticmethod
    def _insert(stops: list[SnapshotStop], stop: SnapshotStop, to_ordinal: int | None) -> None:
        position = len(stops) if to_ordinal is None else min(to_ordinal - 1, len(stops))
        stops.insert(position, stop)

    def _new_stop(self, published: PublishedPlace, visit_minutes: int | None) -> SnapshotStop:
        minutes = visit_minutes or published.visit_minutes_suggested
        placeholder = time(0, 0)
        return SnapshotStop.model_construct(
            id=uuid.uuid4(),
            trust_level="VERIFIED",
            place_id=published.place_id,
            catalog_publication_id=published.catalog_publication_id,
            web_place_candidate_id=None,
            ordinal=1,
            planned_arrival=placeholder,
            planned_departure=placeholder,
            visit_minutes=minutes,
            is_locked=False,
            rationale=None,
            conflicts=[],
        )

    # -- operations ----------------------------------------------------------------------------

    def apply(self, index: int, edit: PreviewEditOperation) -> None:
        op = edit.op
        if op == "MOVE_STOP":
            day_index, position = self._locate(edit.stop_id, index)
            target = self._day(edit.day_index if edit.day_index is not None else day_index, index)
            stop = self.days[day_index].pop(position)
            self._insert(target, stop, edit.to_ordinal)
        elif op == "ADD_STOP":
            target = self._day(edit.day_index, index)
            published = self._publication(edit.place_id, index)
            self._insert(target, self._new_stop(published, edit.visit_minutes), edit.to_ordinal)
        elif op == "REMOVE_STOP":
            day_index, position = self._locate(edit.stop_id, index)
            self.days[day_index].pop(position)
        elif op == "REPLACE_STOP":
            day_index, position = self._locate(edit.stop_id, index)
            published = self._publication(edit.place_id, index)
            self.days[day_index][position] = self._new_stop(published, edit.visit_minutes)
        elif op == "SET_VISIT_MINUTES":
            if edit.visit_minutes is None:
                raise validation_failed(
                    "validation_failed",
                    "visit_minutes is required",
                    edit_index=index,
                    field="visit_minutes",
                )
            day_index, position = self._locate(edit.stop_id, index)
            stop = self.days[day_index][position]
            stop.visit_minutes = edit.visit_minutes
        elif op == "SET_LEG_MODE":
            if edit.from_stop_id is None or edit.to_stop_id is None or edit.travel_mode is None:
                raise validation_failed(
                    "validation_failed",
                    "from_stop_id, to_stop_id and travel_mode are required",
                    edit_index=index,
                )
            if not self._consecutive(edit.from_stop_id, edit.to_stop_id):
                raise validation_failed(
                    "unknown_leg", "The two stops are not consecutive in one day", edit_index=index
                )
            self.mode_overrides[(edit.from_stop_id, edit.to_stop_id)] = edit.travel_mode
        elif op in ("LOCK_STOP", "UNLOCK_STOP"):
            day_index, position = self._locate(edit.stop_id, index)
            self.days[day_index][position].is_locked = op == "LOCK_STOP"
        else:  # pragma: no cover - guarded by the schema Literal
            raise AppError(422, "validation_failed", f"Unsupported edit {op}")

    def _consecutive(self, first: uuid.UUID, second: uuid.UUID) -> bool:
        for stops in self.days.values():
            for before, after in zip(stops, stops[1:], strict=False):
                if before.id == first and after.id == second:
                    return True
        return False

    # -- rebuild -------------------------------------------------------------------------------

    def _leg(self, before: SnapshotStop, after: SnapshotStop) -> SnapshotLeg:
        key = (before.id, after.id)
        original = self.original_legs.get(key)
        override = self.mode_overrides.get(key)
        if original is not None and (override is None or override == original.travel_mode):
            return original.model_copy(deep=True)
        mode: TravelMode = override or (
            original.travel_mode if original is not None else self.default_mode
        )
        return SnapshotLeg(
            from_stop_id=before.id,
            to_stop_id=after.id,
            travel_mode=mode,
            availability="EXPIRED",
        )

    def build(self) -> PlanSnapshot:
        days: list[SnapshotDay] = []
        for day_index in sorted(self.days):
            stops = self.days[day_index]
            window_start, window_end = self.windows[day_index]
            legs = [self._leg(a, b) for a, b in zip(stops, stops[1:], strict=False)]
            first = self.original_first_arrival.get(day_index)
            cursor = (
                first[1]
                if first is not None and stops and stops[0].id == first[0]
                else window_start
            )
            rebuilt: list[SnapshotStop] = []
            for position, stop in enumerate(stops):
                if position > 0:
                    leg = legs[position - 1]
                    cursor = _add_minutes(cursor, (leg.duration_s or 0) / 60)
                departure = _add_minutes(cursor, stop.visit_minutes)
                conflicts = [c for c in stop.conflicts if c.type != "DAY_WINDOW_EXCEEDED"]
                if departure > window_end:
                    conflicts.append(
                        Conflict(
                            type="DAY_WINDOW_EXCEEDED",
                            severity="WARNING",
                            message="This stop ends after the day window.",
                        )
                    )
                rebuilt.append(
                    SnapshotStop.model_validate(
                        {
                            **stop.model_dump(),
                            "ordinal": position + 1,
                            "planned_arrival": cursor,
                            "planned_departure": departure,
                            "conflicts": [c.model_dump() for c in conflicts],
                        }
                    )
                )
                cursor = departure
            days.append(
                SnapshotDay(
                    day_index=day_index,
                    day_window_start=window_start,
                    day_window_end=window_end,
                    stops=rebuilt,
                    legs=legs,
                )
            )
        reasons = [
            reason
            for reason in self.snapshot.health_reasons
            if reason.type not in ("DAY_WINDOW_EXCEEDED", "WEB_PLACE_UNVERIFIED")
        ]
        return PlanSnapshot(
            days=days,
            health_reasons=reasons,
            assumptions=list(self.snapshot.assumptions),
            research_used=self.snapshot.research_used,
            agent_run_id=self.snapshot.agent_run_id,
        )


def apply_edits(
    snapshot: PlanSnapshot,
    edits: list[PreviewEditOperation],
    *,
    day_count: int,
    default_mode: TravelMode,
    publications: dict[uuid.UUID, PublishedPlace],
) -> tuple[PlanSnapshot, PlanHealth]:
    """Apply ``edits`` in order and return the new snapshot and its Plan Health.

    ``publications`` maps each ``place_id`` named by ADD_STOP/REPLACE_STOP to its current
    publication in the trip's city (missing = not published there → 422 ``place_not_in_city``).
    """
    editor = _Editor(
        snapshot, day_count=day_count, default_mode=default_mode, publications=publications
    )
    for index, edit in enumerate(edits):
        editor.apply(index, edit)
    rebuilt = editor.build()
    health, _ = evaluate_health(rebuilt)
    return rebuilt, health
