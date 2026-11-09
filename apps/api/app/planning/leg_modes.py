"""Travel-mode restrictions handled in scheduling (ADR-011 amendment 2026-11-09).

A calendar rule may forbid travel modes between two stops it both covers on a date, optionally
only for legs departing inside its ``from``/``to`` window (e.g. the Hội An Old Town is car-free
15:00–22:00; :class:`app.planning.calendar.windows.ModeRestriction`). Plan Health reports such a
leg as ``LEG_MODE_RESTRICTED`` (BLOCKING), so the planner builds plans that never contain one:

- **Walk instead.** When the plan's mode is restricted for a pair, WALK is allowed by the
  traveler and not restricted itself, and the provider's walking leg is short enough
  (≤ :data:`WALK_MAX_DISTANCE_M` and ≤ :data:`WALK_MAX_DURATION_S`), the pair uses WALK on that
  date: the solver schedules with the walking duration and the snapshot shows a WALK leg with the
  provider's walking distance and duration. Walking is used for the whole date, not only inside
  the window: a short walk is always allowed, and the timeline then matches the solver exactly.
- **Otherwise avoid it.** The pair keeps the plan's mode, but the solver may not depart along it
  inside the restricted window (a whole-day restriction removes the arc). The solver then orders
  the stops differently or drops one.

Durations and distances always come from a routing matrix (Google Routes, or the labelled
estimate provider in demo); nothing here invents a value (BRU-006). Zone geometry is not modelled:
a leg is restricted when both stops are covered by the rule, which is what Plan Health checks.
"""

from __future__ import annotations

import uuid
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

from app.planning.calendar.windows import DAY_MINUTES, DayWindow, Interval
from app.routing.matrix import RouteMatrix

WALK_MAX_DISTANCE_M = 1_500
WALK_MAX_DURATION_S = 20 * 60

Pair = tuple[str, str]

__all__ = [
    "WALK_MAX_DISTANCE_M",
    "WALK_MAX_DURATION_S",
    "LegModePlan",
    "Pair",
    "plan_leg_modes",
    "restricted_keys",
    "restricted_pairs",
]


@dataclass(frozen=True, slots=True)
class LegModePlan:
    """Per-date leg decisions for pairs whose planned mode a rule restricts.

    ``walk[date]`` holds the pairs that use WALK on that date (durations from ``walk_matrix``);
    ``bans[date][pair]`` holds the minute spans in which the pair may not be departed in the
    plan's mode (``(0, 1440)`` = never).
    """

    walk_matrix: RouteMatrix | None = None
    walk: Mapping[date, frozenset[Pair]] = field(default_factory=dict)
    bans: Mapping[date, Mapping[Pair, tuple[Interval, ...]]] = field(default_factory=dict)

    def walks(self, day: date, pair: Pair) -> bool:
        return pair in self.walk.get(day, frozenset())

    def walk_durations_s(self) -> dict[date, dict[Pair, int]]:
        """Solver overrides: the walking duration of each WALK pair, per date."""
        out: dict[date, dict[Pair, int]] = {}
        if self.walk_matrix is None:
            return out
        for day, pairs in self.walk.items():
            for a, b in pairs:
                seconds = self.walk_matrix.duration_s(a, b)
                if seconds is not None:
                    out.setdefault(day, {})[(a, b)] = seconds
        return out

    def bans_s(self) -> dict[date, dict[Pair, tuple[tuple[int, int], ...]]]:
        """Solver departure bans in seconds since local midnight."""
        return {
            day: {pair: tuple((lo * 60, hi * 60) for lo, hi in spans) for pair, spans in by.items()}
            for day, by in self.bans.items()
            if by
        }


def _merge(spans: Sequence[Interval]) -> tuple[Interval, ...]:
    merged: list[Interval] = []
    for lo, hi in sorted(spans):
        if merged and lo <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return tuple(merged)


def restricted_pairs(
    places: Sequence[tuple[str, uuid.UUID]],
    dates: Sequence[date],
    windows: Mapping[tuple[uuid.UUID, date], DayWindow],
    mode: str,
) -> dict[date, dict[Pair, tuple[Interval, ...]]]:
    """Ordered pairs (by key) whose ``mode`` a rule covering both places restricts, per date,
    with the departure spans (minutes) in which the restriction holds.

    Mirrors :func:`app.planning.health._restricting_rules`: a rule restricts a leg when it lists
    ``mode``, covers both ends on the date and the departure lies in its window (no window = all
    day).
    """
    out: dict[date, dict[Pair, tuple[Interval, ...]]] = {}
    for day in dates:
        rules: dict[str, dict[uuid.UUID, Interval]] = {}
        for key, place_id in places:
            window = windows.get((place_id, day))
            if window is None:
                continue
            for restriction in window.mode_restrictions:
                if mode in restriction.modes:
                    span = restriction.interval or (0, DAY_MINUTES)
                    rules.setdefault(key, {})[restriction.rule_id] = span
        by_pair: dict[Pair, tuple[Interval, ...]] = {}
        for a, rules_a in rules.items():
            for b, rules_b in rules.items():
                if a == b:
                    continue
                shared = [span for rule_id, span in rules_a.items() if rule_id in rules_b]
                if shared:
                    by_pair[(a, b)] = _merge(shared)
        if by_pair:
            out[day] = by_pair
    return out


def restricted_keys(restricted: Mapping[date, Mapping[Pair, object]]) -> list[str]:
    """Every key that appears in a restricted pair (stable order)."""
    keys: dict[str, None] = {}
    for by_pair in restricted.values():
        for a, b in by_pair:
            keys.setdefault(a)
            keys.setdefault(b)
    return list(keys)


def plan_leg_modes(
    restricted: Mapping[date, Mapping[Pair, tuple[Interval, ...]]],
    *,
    mode: str,
    allowed_modes: Collection[str],
    walk_matrix: RouteMatrix | None,
    walk_restricted: Mapping[date, Collection[Pair]] | None = None,
) -> LegModePlan:
    """Choose WALK for each restricted pair where a reasonable walking leg exists, else ban.

    ``walk_restricted`` lists pairs where a rule also restricts WALK on that date (never walked).
    """
    walk: dict[date, set[Pair]] = {}
    bans: dict[date, dict[Pair, tuple[Interval, ...]]] = {}
    can_walk = mode != "WALK" and "WALK" in allowed_modes and walk_matrix is not None
    for day, by_pair in restricted.items():
        no_walk = set((walk_restricted or {}).get(day, ()))
        for pair, spans in by_pair.items():
            if can_walk and pair not in no_walk and walk_matrix is not None:
                leg = walk_matrix.legs.get(pair)
                if (
                    leg is not None
                    and leg.available
                    and leg.distance_m is not None
                    and leg.duration_s is not None
                    and leg.distance_m <= WALK_MAX_DISTANCE_M
                    and leg.duration_s <= WALK_MAX_DURATION_S
                ):
                    walk.setdefault(day, set()).add(pair)
                    continue
            bans.setdefault(day, {})[pair] = spans
    return LegModePlan(
        walk_matrix=walk_matrix if walk else None,
        walk={day: frozenset(pairs) for day, pairs in walk.items()},
        bans=bans,
    )
