"""One multi-day OR-Tools routing model per proposal (ADR-011).

* Vehicle ``d`` = trip day ``d``, starting and ending at that day's fixed anchors, its time
  window being the day window.
* Node ``(stop, d)`` for every day on whose date the stop has an effective window that fits the
  visit; the copy may only be served by vehicle ``d`` and its cumul domain is that date's
  windows (start no earlier than opening, finish no later than closing). A stop closed on a date
  simply has no copy for that day.
* One disjunction over a stop's copies (at most one visit) with a drop penalty decreasing with
  the selector rank; must-sees are prohibitively expensive to drop; locked stops keep only the
  copy of their day, with an even larger penalty, and are ordered by ``position``.
* Arcs whose leg is unavailable (``durations`` returns ``None``) are removed — never estimated.
* Travel-mode restrictions (ADR-011 amendment 2026-11-09): ``SolverInput.day_durations`` replaces
  a pair's duration on a date (the walking leg inside a car-free zone) and
  ``SolverInput.departure_bans`` forbids departing along an arc inside a restricted window, so a
  plan never contains a restricted leg.
* Optional lunch break per day (OR-Tools break interval on the time dimension).
* Day balance: a hard per-day capacity of stops (fair share, raised for stops servable only that
  day, capped by the pace ``DaySpec.max_stops``) plus a soft floor share, so a multi-day trip is
  not packed into day 1 and no day stays empty while candidates exist.
* Variety: ``SolverInput.category_day_caps`` caps stops per ``StopSpec.category`` per day
  (raised to the category's fair share over the days).
* Same-day tickets: stops with a ``StopSpec.ticket_group`` (a ticket valid only on its day of
  purchase, e.g. the Hội An Old Town ticket) are pinned to one day when the first solution
  spreads them, so a plan does not buy the same ticket twice (TICKET_VALIDITY).
* Fixed first-solution strategy, guided local search, a solution limit as the deterministic
  work bound and a time limit as safety cap: same input ⇒ same output.

``regenerate_day`` solves one day as a single-vehicle model with the other days' stops removed.
"""

from __future__ import annotations

import time as _time
from collections import Counter
from collections.abc import Collection, Sequence
from dataclasses import dataclass, replace
from typing import Any

from ortools.constraint_solver import (  # type: ignore[import-untyped]  # OR-Tools ships no stubs
    pywrapcp,
    routing_enums_pb2,
)

from app.planning.solver.model import (
    SECONDS_PER_DAY,
    BreakSlot,
    DayPlan,
    DaySpec,
    DroppedStop,
    DropReason,
    Lock,
    ScheduledStop,
    SolverInput,
    SolverParams,
    SolverResult,
    SolveStatus,
    StopSpec,
)

_FORBIDDEN = SECONDS_PER_DAY  # transit for removed arcs; never chosen
_BIG_M = 4 * SECONDS_PER_DAY


@dataclass(frozen=True, slots=True)
class _Node:
    key: str
    day: int
    stop: StopSpec | None  # None for anchors
    domain: tuple[tuple[int, int], ...]  # allowed service-start ranges


def stop_count(node: _Node) -> int:
    return 1 if node.stop is not None else 0


def add_count_dimension(routing: Any, name: str, counts: list[int], capacity: list[int]) -> Any:
    """A dimension counting nodes (``counts`` per node) with a hard capacity per vehicle."""
    callback = routing.RegisterUnaryTransitVector(counts)
    routing.AddDimensionWithVehicleCapacity(callback, 0, capacity, True, name)
    return routing.GetDimensionOrDie(name)


def _category_of(node: _Node) -> str | None:
    return node.stop.category if node.stop is not None else None


def _copy_domain(stop: StopSpec, day: DaySpec) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    for interval in sorted(stop.windows.get(day.date, ()), key=lambda i: (i.start_s, i.end_s)):
        lo = max(interval.start_s, day.start_s)
        hi = min(interval.end_s, day.end_s) - stop.visit_s
        if hi >= lo:
            ranges.append((lo, hi))
    merged: list[tuple[int, int]] = []
    for lo, hi in ranges:
        if merged and lo <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return tuple(merged)


# Plan Health compares whole minutes (a departure is rounded up to the minute), so a departure
# that must precede a banned span ends at least one minute before it.
_BAN_MARGIN_S = 60


def _banned_all_day(spans: Sequence[tuple[int, int]]) -> bool:
    return any(lo <= 0 and hi >= SECONDS_PER_DAY for lo, hi in spans)


def _ban_departures(
    routing: Any,
    time_dim: Any,
    from_index: int,
    to_index: int,
    visit_s: int,
    spans: Sequence[tuple[int, int]],
) -> None:
    """If ``from → to`` is used, its departure (service start + visit) lies outside ``spans``."""
    solver = routing.solver()
    cumul = time_dim.CumulVar(from_index)
    used = solver.IsEqualCstVar(routing.NextVar(from_index), to_index)
    for lo, hi in spans:
        before = solver.IsLessOrEqualCstVar(cumul, lo - _BAN_MARGIN_S - visit_s)
        after = solver.IsGreaterOrEqualCstVar(cumul, hi - visit_s)
        solver.Add(before + after >= used)


def _validate(inp: SolverInput) -> None:
    if not inp.days:
        raise ValueError("at least one day is required")
    keys = [s.key for s in inp.stops]
    if len(keys) != len(set(keys)):
        raise ValueError("stop keys must be unique")
    anchor_keys = {d.start_key for d in inp.days} | {d.end_key for d in inp.days}
    if anchor_keys & set(keys):
        raise ValueError("a stop key may not equal an anchor key")
    for stop in inp.stops:
        if stop.lock is not None and not 0 <= stop.lock.day_index < len(inp.days):
            raise ValueError(f"lock day out of range for {stop.key}")


def solve(inp: SolverInput) -> SolverResult:
    """Solve, then make sure no day is left empty while a stop could be served on it.

    The insertion heuristic may put a stop that is servable on several days onto a busy day and
    local search rarely moves it (that means swapping its day copies). For each empty day that
    some stop could serve, the stop is pinned to that day — a dropped one first (best rank),
    else the lowest-ranked stop of the fullest other day — and the model is solved again. At
    most one re-solve per day; the result is kept only if it schedules at least as many stops.
    """
    _validate(inp)
    result, servable = _solve(inp, {})
    result, servable, pins = _group_tickets(inp, result, servable, {})
    by_key = {stop.key: stop for stop in inp.stops}
    for _ in range(len(inp.days) - 1):
        if result.status is not SolveStatus.SOLVED:
            break
        empty = [plan.day_index for plan in result.days if not plan.stops]
        day_of = {s.key: plan.day_index for plan in result.days for s in plan.stops}
        movable = [
            key
            for key, ds in servable.items()
            if key not in pins and by_key[key].lock is None and any(v in ds for v in empty)
        ]
        if not empty or not movable:
            break
        dropped = sorted((k for k in movable if k not in day_of), key=lambda k: by_key[k].rank)
        if dropped:
            key = dropped[0]
        else:
            load = {v: sum(1 for d in day_of.values() if d == v) for v in set(day_of.values())}
            key = max(
                (k for k in movable if load.get(day_of[k], 0) > 1),
                key=lambda k: (load[day_of[k]], by_key[k].rank, k),
                default="",
            )
            if not key:
                break
        target = next(v for v in empty if v in servable[key])
        candidate, servable = _solve(inp, {**pins, key: target})
        if candidate.status is not SolveStatus.SOLVED or _count(candidate) < _count(result):
            break
        pins[key] = target
        result = candidate
    return result


def _count(result: SolverResult) -> int:
    return sum(len(plan.stops) for plan in result.days)


def _scheduled_days(result: SolverResult) -> dict[str, int]:
    return {stop.key: plan.day_index for plan in result.days for stop in plan.stops}


def _group_tickets(
    inp: SolverInput,
    result: SolverResult,
    servable: dict[str, set[int]],
    pins: dict[str, int],
) -> tuple[SolverResult, dict[str, set[int]], dict[str, int]]:
    """Pin a same-ticket group to one day when the first solution split it (ADR-011).

    A ticket valid only on its day of purchase (``StopSpec.ticket_group``, e.g. the Hội An Old
    Town ticket) costs twice when its places are spread over two days. Each group is moved to
    the day that already serves most of it, and the move is kept only when every stop of the
    group can be served that day and no stop is lost. Locks are never overridden.
    """
    if len(inp.days) < 2:
        return result, servable, pins
    groups: dict[str, list[str]] = {}
    for stop in inp.stops:
        if stop.ticket_group is not None and stop.lock is None:
            groups.setdefault(stop.ticket_group, []).append(stop.key)
    for group in sorted(groups):
        keys = groups[group]
        if len(keys) < 2:
            continue
        day_of = _scheduled_days(result)
        used = [day_of[key] for key in keys if key in day_of]
        counts = Counter(used)
        if len(counts) < 2:
            continue
        target = min(counts, key=lambda day: (-counts[day], day))
        if any(target not in servable.get(key, set()) for key in keys):
            continue
        candidate_pins = {**pins, **dict.fromkeys(keys, target)}
        candidate, candidate_servable = _solve(inp, candidate_pins)
        if candidate.status is not SolveStatus.SOLVED or _count(candidate) < _count(result):
            continue
        result, servable, pins = candidate, candidate_servable, candidate_pins
    return result, servable, pins


def _solve(inp: SolverInput, pins: dict[str, int]) -> tuple[SolverResult, dict[str, set[int]]]:
    """One OR-Tools solve; ``pins`` restricts a stop to one day without a lock's penalty.
    Also returns the days on which each candidate stop can be served."""
    params = inp.params
    days = inp.days
    n_days = len(days)

    nodes: list[_Node] = []
    for v, day in enumerate(days):
        nodes.append(_Node(day.start_key, v, None, ((day.start_s, day.end_s),)))
    for v, day in enumerate(days):
        nodes.append(_Node(day.end_key, v, None, ((day.start_s, day.end_s),)))
    copies: dict[str, list[int]] = {}
    pre_dropped: dict[str, DropReason] = {}
    for stop in inp.stops:
        if stop.lock is not None:
            allowed_days: Sequence[int] = [stop.lock.day_index]
        elif stop.key in pins:
            allowed_days = [pins[stop.key]]
        else:
            allowed_days = range(n_days)
        stop_copies: list[int] = []
        for v in allowed_days:
            domain = _copy_domain(stop, days[v])
            if domain:
                stop_copies.append(len(nodes))
                nodes.append(_Node(stop.key, v, stop, domain))
        if stop_copies:
            copies[stop.key] = stop_copies
        else:
            pre_dropped[stop.key] = (
                DropReason.LOCKED_DAY_CLOSED
                if stop.lock is not None and any(_copy_domain(stop, d) for d in days)
                else DropReason.CLOSED_ON_ALL_DATES
            )

    by_key_pre = {stop.key: stop for stop in inp.stops}

    # Leg lookup memo over keys (the accessor may be a cache-backed matrix).
    leg_memo: dict[tuple[str, str], int | None] = {}

    def base_leg(a: str, b: str) -> int | None:
        pair = (a, b)
        if pair not in leg_memo:
            value = inp.durations(a, b)
            leg_memo[pair] = None if value is None else max(0, int(value))
        return leg_memo[pair]

    def leg(a: str, b: str, v: int) -> int | None:
        """Duration of ``a → b`` on day ``v``: the date's override (another mode) first; an arc
        banned for the whole day is unavailable (ADR-011 amendment 2026-11-09)."""
        if a == b:
            return 0
        when = days[v].date
        if _banned_all_day(inp.departure_bans.get(when, {}).get((a, b), ())):
            return None
        override = inp.day_durations.get(when, {}).get((a, b))
        if override is not None:
            return max(0, int(override))
        return base_leg(a, b)

    # Unreachable copies: no usable in-arc or out-arc within their day.
    for key, idxs in list(copies.items()):
        reachable: list[int] = []
        for i in idxs:
            node = nodes[i]
            day = days[node.day]
            peers = [
                nodes[j].key for j in range(2 * n_days, len(nodes)) if nodes[j].day == node.day
            ]
            v = node.day
            has_in = leg(day.start_key, key, v) is not None or any(
                leg(p, key, v) is not None for p in peers if p != key
            )
            has_out = leg(key, day.end_key, v) is not None or any(
                leg(key, p, v) is not None for p in peers if p != key
            )
            if has_in and has_out:
                reachable.append(i)
        if not reachable:
            del copies[key]
            pre_dropped[key] = DropReason.UNREACHABLE
        else:
            copies[key] = reachable

    active_nodes = list(range(2 * n_days)) + sorted(i for idxs in copies.values() for i in idxs)
    # Re-index so the OR-Tools model only contains live nodes.
    live = [nodes[i] for i in active_nodes]
    remap = {old: new for new, old in enumerate(active_nodes)}
    copies = {k: [remap[i] for i in idxs] for k, idxs in copies.items()}

    manager = pywrapcp.RoutingIndexManager(
        len(live), n_days, list(range(n_days)), list(range(n_days, 2 * n_days))
    )
    routing = pywrapcp.RoutingModel(manager)

    def node_of(index: int) -> int:
        return int(manager.IndexToNode(index))

    def service(node: int) -> int:
        stop = live[node].stop
        return stop.visit_s if stop is not None else 0

    def travel(from_node: int, to_node: int) -> int:
        a, b = live[from_node], live[to_node]
        if a.day != b.day:
            return _FORBIDDEN  # arcs across days are removed below
        if a.stop is None and b.stop is None:
            return leg(a.key, b.key, a.day) or 0  # empty day: start → end
        value = leg(a.key, b.key, a.day)
        return _FORBIDDEN if value is None else value

    # Node-indexed matrices are evaluated in C++ (no Python callback per arc evaluation).
    n_live = len(live)
    travel_matrix = [[travel(f, t) for t in range(n_live)] for f in range(n_live)]
    time_matrix = [[service(f) + travel_matrix[f][t] for t in range(n_live)] for f in range(n_live)]
    travel_idx = routing.RegisterTransitMatrix(travel_matrix)
    time_idx = routing.RegisterTransitMatrix(time_matrix)
    routing.SetArcCostEvaluatorOfAllVehicles(travel_idx)
    routing.AddDimension(time_idx, SECONDS_PER_DAY, SECONDS_PER_DAY, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    solver = routing.solver()

    # Day windows on the anchors.
    for v, day in enumerate(days):
        time_dim.CumulVar(routing.Start(v)).SetRange(day.start_s, day.end_s)
        time_dim.CumulVar(routing.End(v)).SetRange(day.start_s, day.end_s)
        routing.AddVariableMinimizedByFinalizer(time_dim.CumulVar(routing.Start(v)))
        routing.AddVariableMinimizedByFinalizer(time_dim.CumulVar(routing.End(v)))

    # Stop copies: vehicle restriction, per-date windows, forbidden arcs.
    for node_id in range(2 * n_days, len(live)):
        node = live[node_id]
        index = manager.NodeToIndex(node_id)
        # Only vehicle `day` may serve this copy (-1 = unperformed). Equivalent to
        # SetAllowedVehiclesForIndex, whose SWIG binding rejects Python lists in OR-Tools 9.15.
        routing.VehicleVar(index).SetValues([-1, node.day])
        cumul = time_dim.CumulVar(index)
        cumul.SetRange(node.domain[0][0], node.domain[-1][1])
        for (_, prev_hi), (next_lo, _) in zip(node.domain, node.domain[1:], strict=False):
            if next_lo - 1 >= prev_hi + 1:
                cumul.RemoveInterval(prev_hi + 1, next_lo - 1)
        routing.AddVariableMinimizedByFinalizer(cumul)

    starts = {routing.Start(v): v for v in range(n_days)}
    ends = {routing.End(v): v for v in range(n_days)}
    for from_node in [*range(n_days), *range(2 * n_days, len(live))]:
        from_index = (
            routing.Start(from_node) if from_node < n_days else manager.NodeToIndex(from_node)
        )
        a = live[from_node]
        for to_node in range(n_days, len(live)):
            b = live[to_node]
            to_index = (
                routing.End(to_node - n_days)
                if to_node < 2 * n_days
                else manager.NodeToIndex(to_node)
            )
            if from_index == to_index:
                continue
            if a.day != b.day:
                if not (from_index in starts and to_index in ends):
                    routing.NextVar(from_index).RemoveValue(to_index)
                continue
            if a.stop is None and b.stop is None:
                continue  # empty day is always allowed
            if leg(a.key, b.key, a.day) is None:
                routing.NextVar(from_index).RemoveValue(to_index)
                continue
            spans = inp.departure_bans.get(days[a.day].date, {}).get((a.key, b.key), ())
            if spans:
                _ban_departures(routing, time_dim, from_index, to_index, service(from_node), spans)

    # Day balance. Travel cost alone packs every stop into the first day whenever the day window
    # is long enough (a 2-day plan once put all 10 stops on day 1), and local search can hardly
    # move a stop between days (that means swapping its day copies). So the balance is a hard
    # per-day capacity on a Stops dimension: the fair share ceil(stops ÷ days), raised to the
    # stops that can only be served that day (closures, locks), and never above the pace cap
    # ``max_stops``. A soft lower bound (the floor share) also makes an empty day cost more
    # than dropping a low-ranked stop, so no requested day stays empty while candidates exist.
    servable_days = {key: {live[i].day for i in idxs} for key, idxs in copies.items()}
    n_candidates = len(servable_days)
    capacities: list[int] = []
    for v, day in enumerate(days):
        only_here = sum(1 for ds in servable_days.values() if ds == {v})
        cap = max(-(-n_candidates // n_days), only_here)
        if day.max_stops is not None:
            cap = min(cap, day.max_stops)
        capacities.append(cap)
    if n_days > 1 or any(day.max_stops is not None for day in days):
        stops_dim = add_count_dimension(
            routing, "Stops", [stop_count(live[n]) for n in range(len(live))], capacities
        )
        for v in range(n_days):
            servable = sum(1 for ds in servable_days.values() if v in ds)
            lower = min(n_candidates // n_days, capacities[v], servable)
            if n_days > 1 and lower > 0:
                # An empty route is "unused" and OR-Tools would skip its soft-bound cost.
                routing.SetVehicleUsedWhenEmpty(True, v)
                stops_dim.SetCumulVarSoftLowerBound(
                    routing.End(v), lower, params.day_balance_penalty
                )

    # Variety: per-day cap per category, raised to the category's fair share over the days so
    # a capped category never forces a drop that spreading could avoid.
    category_counts: dict[str, int] = {}
    for key in copies:
        category = by_key_pre[key].category
        if category is not None:
            category_counts[category] = category_counts.get(category, 0) + 1
    for category in sorted(category_counts):
        category_cap = inp.category_day_caps.get(category)
        if category_cap is None or category_counts[category] <= category_cap:
            continue
        add_count_dimension(
            routing,
            f"Category:{category}",
            [1 if _category_of(live[n]) == category else 0 for n in range(len(live))],
            [max(category_cap, -(-category_counts[category] // n_days))] * n_days,
        )

    # Disjunctions (optional / must-see / locked).
    by_key = {stop.key: stop for stop in inp.stops}
    for key in sorted(copies):
        indices = [manager.NodeToIndex(n) for n in copies[key]]
        routing.AddDisjunction(indices, params.drop_penalty(by_key[key]), 1)

    # Locked stops keep their relative order within their day.
    locked_by_day: dict[int, list[StopSpec]] = {}
    for stop in inp.stops:
        if stop.lock is not None and stop.key in copies:
            locked_by_day.setdefault(stop.lock.day_index, []).append(stop)
    for group in locked_by_day.values():
        group.sort(key=lambda s: (s.lock.position if s.lock else 0, s.key))
        for first, second in zip(group, group[1:], strict=False):
            ia = manager.NodeToIndex(copies[first.key][0])
            ib = manager.NodeToIndex(copies[second.key][0])
            ca, cb = time_dim.CumulVar(ia), time_dim.CumulVar(ib)
            aa, ab = routing.ActiveVar(ia), routing.ActiveVar(ib)
            solver.Add(cb + 2 * _BIG_M >= ca + first.visit_s + _BIG_M * aa + _BIG_M * ab)

    # Lunch breaks.
    breaks: dict[int, Any] = {}
    if any(day.lunch is not None for day in days):
        node_visit_transit = [0] * routing.Size()
        for index in range(routing.Size()):
            node_visit_transit[index] = service(node_of(index))
        for v, day in enumerate(days):
            if day.lunch is None:
                continue
            interval = solver.FixedDurationIntervalVar(
                day.lunch.earliest_start_s,
                day.lunch.latest_start_s,
                day.lunch.duration_s,
                False,
                f"lunch-{v}",
            )
            time_dim.SetBreakIntervalsOfVehicle([interval], v, node_visit_transit)
            breaks[v] = interval

    search = pywrapcp.DefaultRoutingSearchParameters()
    search.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    )
    search.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search.solution_limit = params.solution_limit
    search.time_limit.FromMilliseconds(max(1, int(params.time_limit_s * 1000)))
    search.log_search = False

    began = _time.monotonic()
    solution = routing.SolveWithParameters(search)
    elapsed = _time.monotonic() - began
    time_limit_reached = elapsed >= params.time_limit_s * 0.98

    pre = tuple(
        DroppedStop(key, reason, by_key[key].must_see, by_key[key].lock is not None)
        for key, reason in sorted(pre_dropped.items())
    )
    if solution is None:
        all_dropped = pre + tuple(
            DroppedStop(k, DropReason.NOT_SCHEDULED, by_key[k].must_see, by_key[k].lock is not None)
            for k in sorted(copies)
        )
        no_solution = SolverResult(
            SolveStatus.NO_SOLUTION, (), all_dropped, None, time_limit_reached
        )
        return no_solution, servable_days

    def value(var: Any) -> int:
        return int(solution.Value(var))

    break_starts: dict[int, int] = {}
    if breaks:
        names = {f"lunch-{v}": v for v in breaks}
        container = solution.IntervalVarContainer()
        for i in range(container.Size()):
            element = container.Element(i)
            name = element.Var().Name()
            if name in names and element.PerformedValue():
                break_starts[names[name]] = int(element.StartValue())

    plans: list[DayPlan] = []
    visited: set[str] = set()
    for v, day in enumerate(days):
        index = routing.Start(v)
        start_cumul = value(time_dim.CumulVar(index))
        prev_node = node_of(index)
        prev_departure = start_cumul
        stops: list[ScheduledStop] = []
        index = value(routing.NextVar(index))
        while not routing.IsEnd(index):
            node_id = node_of(index)
            node = live[node_id]
            travel_s = travel(prev_node, node_id)
            start = value(time_dim.CumulVar(index))
            arrival = min(prev_departure + travel_s, start)
            departure = start + service(node_id)
            stops.append(ScheduledStop(node.key, arrival, start, departure, travel_s))
            visited.add(node.key)
            prev_node, prev_departure = node_id, departure
            index = value(routing.NextVar(index))
        to_end = (
            travel(prev_node, node_of(index))
            if stops
            else (leg(day.start_key, day.end_key, v) or 0)
        )
        lunch: BreakSlot | None = None
        if day.lunch is not None and v in break_starts:
            lunch = BreakSlot(break_starts[v], break_starts[v] + day.lunch.duration_s)
        plans.append(
            DayPlan(
                day_index=v,
                date=day.date,
                stops=tuple(stops),
                start_departure_s=start_cumul,
                end_arrival_s=prev_departure + to_end,
                travel_to_end_s=to_end,
                lunch=lunch,
            )
        )

    solver_dropped = tuple(
        DroppedStop(k, DropReason.NOT_SCHEDULED, by_key[k].must_see, by_key[k].lock is not None)
        for k in sorted(copies)
        if k not in visited
    )
    solved = SolverResult(
        status=SolveStatus.SOLVED,
        days=tuple(plans),
        dropped=pre + solver_dropped,
        objective=int(solution.ObjectiveValue()),
        time_limit_reached=time_limit_reached,
    )
    return solved, servable_days


def regenerate_day(
    inp: SolverInput,
    *,
    day_index: int,
    exclude_keys: Collection[str] = (),
    params: SolverParams | None = None,
) -> SolverResult:
    """Re-solve one day alone (ADR-011): single vehicle, stops used on other days excluded.

    Stops locked to ``day_index`` stay mandatory; stops locked to other days are excluded. The
    returned :class:`DayPlan` carries the original ``day_index``.
    """
    if not 0 <= day_index < len(inp.days):
        raise ValueError("day_index out of range")
    excluded = set(exclude_keys)
    stops: list[StopSpec] = []
    for stop in inp.stops:
        if stop.key in excluded:
            continue
        if stop.lock is not None:
            if stop.lock.day_index != day_index:
                continue
            stop = replace(stop, lock=Lock(0, stop.lock.position))
        stops.append(stop)
    single = SolverInput(
        days=(inp.days[day_index],),
        stops=tuple(stops),
        durations=inp.durations,
        params=params or inp.params,
        day_durations=inp.day_durations,
        departure_bans=inp.departure_bans,
    )
    result = solve(single)
    return replace(result, days=tuple(replace(plan, day_index=day_index) for plan in result.days))
