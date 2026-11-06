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
* Optional lunch break per day (OR-Tools break interval on the time dimension).
* Fixed first-solution strategy, guided local search, a solution limit as the deterministic
  work bound and a time limit as safety cap: same input ⇒ same output.

``regenerate_day`` solves one day as a single-vehicle model with the other days' stops removed.
"""

from __future__ import annotations

import time as _time
from collections.abc import Collection
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
    _validate(inp)
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
        allowed_days = [stop.lock.day_index] if stop.lock is not None else range(n_days)
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

    # Leg lookup memo over keys (the accessor may be a cache-backed matrix).
    leg_memo: dict[tuple[str, str], int | None] = {}

    def leg(a: str, b: str) -> int | None:
        if a == b:
            return 0
        pair = (a, b)
        if pair not in leg_memo:
            value = inp.durations(a, b)
            leg_memo[pair] = None if value is None else max(0, int(value))
        return leg_memo[pair]

    # Unreachable copies: no usable in-arc or out-arc within their day.
    for key, idxs in list(copies.items()):
        reachable: list[int] = []
        for i in idxs:
            node = nodes[i]
            day = days[node.day]
            peers = [
                nodes[j].key for j in range(2 * n_days, len(nodes)) if nodes[j].day == node.day
            ]
            has_in = leg(day.start_key, key) is not None or any(
                leg(p, key) is not None for p in peers if p != key
            )
            has_out = leg(key, day.end_key) is not None or any(
                leg(key, p) is not None for p in peers if p != key
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
        if a.stop is None and b.stop is None:
            return leg(a.key, b.key) or 0  # empty day: start → end
        value = leg(a.key, b.key)
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
            if leg(a.key, b.key) is None:
                routing.NextVar(from_index).RemoveValue(to_index)

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
        return SolverResult(SolveStatus.NO_SOLUTION, (), all_dropped, None, time_limit_reached)

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
            travel(prev_node, node_of(index)) if stops else (leg(day.start_key, day.end_key) or 0)
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
    return SolverResult(
        status=SolveStatus.SOLVED,
        days=tuple(plans),
        dropped=pre + solver_dropped,
        objective=int(solution.ObjectiveValue()),
        time_limit_reached=time_limit_reached,
    )


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
    )
    result = solve(single)
    return replace(result, days=tuple(replace(plan, day_index=day_index) for plan in result.days))
