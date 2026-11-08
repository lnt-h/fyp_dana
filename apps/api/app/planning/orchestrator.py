"""``propose_trip`` / ``regenerate_day`` orchestrator (architecture §3.2, ADR-011, ADR-013).

Deterministic Gonarra code drives every step; models only rank IDs and write rationales:

1. ``VALIDATING_REQUEST`` — owner-scoped trip load (ownership before any model or provider call),
   expected trip revision, effective preferences, idempotency claim, per-account quota.
2. ``SELECTING_PLACES`` — published Đà Nẵng pool, pre-ranked by the rule selector; the
   ``selector`` model re-ranks it when a key and quota exist. Output is Pydantic + domain
   validated (unknown IDs ⇒ failure) and falls back to the rule-based selector.
3. ``RESEARCHING`` — only with ``research_enabled`` and a thin pool, under a hard timeout. Web
   candidates are stored for the curator queue; they carry no coordinates yet (ADR-006), so they
   are not scheduled.
4. ``ROUTING`` — one leg matrix over the pool + the day anchor (Google Routes, demo estimate, or
   nothing: legs UNAVAILABLE).
5. ``SCHEDULING`` — one OR-Tools multi-day model with per-date windows (calendar rules).
6. ``CHECKING_HEALTH`` — Plan Health (code).
7. ``WRITING`` — ``grounded_writer`` rationales; null when no key/quota; never blocks.
8. Persist an ACTIVE preview (revision 1) and emit ``preview_ready``.

Nothing here logs prompts, request text, place names or coordinates (AGENTS.md).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Literal

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runtime import AgentContext, AgentRunner, default_runner, load_instructions
from app.agents.schemas import RationaleStop, RationaleTraveller, ResultSource, TimeOfDay
from app.agents.selector import MAX_CANDIDATES, select_places
from app.agents.validators import validate_selection
from app.agents.writer import RATIONALE_AGENT, trim_text, write_rationales
from app.ai.invocations import Purpose
from app.ai.providers import Role, provider_configured, role_chain
from app.ai.quota import (
    PROPOSE_BUDGET,
    REGENERATE_DAY_BUDGET,
    Bucket,
    QuotaBudget,
    QuotaLedger,
)
from app.ai.redaction import CandidateDto
from app.catalog.preferences import PreferencesRepository
from app.config import Settings
from app.errors import AppError
from app.models.planning import IdempotencyRecord, PlanPreview, PreviewRevision, Trip
from app.models.providers import DataProvider
from app.observability import error_payload, log_failure
from app.planning.assemble import (
    DayFrame,
    LockedStop,
    ProviderIds,
    ScheduleInput,
    attach_conflicts,
    build_days,
    health_plan,
    schedule,
)
from app.planning.calendar.windows import PlaceRef, effective_windows
from app.planning.health import evaluate
from app.planning.leg_modes import LegModePlan, plan_leg_modes, restricted_keys, restricted_pairs
from app.planning.pool import PoolPlace, by_id, load_pool, load_rules
from app.planning.rule_selector import (
    RuleCandidate,
    category_day_cap,
    diversify,
    pool_size,
    rank_candidates,
    select_rule_based,
    stops_per_day,
    wanted_interests,
)
from app.planning.solver import DropReason
from app.planning.workflows import EventSink, ProposeTripCommand, RegenerateDayCommand
from app.routing.anchors import DA_NANG_ANCHORS, Anchor
from app.routing.matrix import RouteMatrix, get_matrix
from app.routing.matrix_cache import ROUTES_PROVIDER_KEY, MatrixCache
from app.routing.provider import (
    EstimateNotAllowedError,
    LatLng,
    NoRoutesProvider,
    RoutesProvider,
    haversine_m,
    select_provider,
)
from app.schemas.trips import PlanningPreferences
from app.trips import idempotency
from app.trips.assumptions import (
    ESTIMATED_LEGS,
    NO_ROUTES,
    RESEARCH_SKIPPED,
    STOPS_LEFT_OUT,
    WALK_IN_RESTRICTED_ZONE,
    unique_keys,
)
from app.trips.repository import ROUTES_ESTIMATE_PROVIDER_KEY, SQLAlchemyTripStore
from app.trips.snapshot import PlanSnapshot, SnapshotDay, SnapshotStop, evaluate_health

logger = logging.getLogger("gonarra.planning")

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]
Stage = Literal[
    "VALIDATING_REQUEST",
    "SELECTING_PLACES",
    "RESEARCHING",
    "VERIFYING_WEB_PLACES",
    "ROUTING",
    "SCHEDULING",
    "CHECKING_HEALTH",
    "WRITING",
]

PREVIEW_TTL = timedelta(hours=24)
# ``preview_revisions.model_version`` is required for generated revisions
# (ck_preview_revisions_model_recorded); this marks a pool chosen by the rule-based selector.
RULE_BASED_VERSION = "gonarra:rule-based-selector@1"
DEFAULT_DAY_START = time(8, 0)
DEFAULT_DAY_END = time(20, 0)
VN_OFFSET = timedelta(hours=7)
# Drops the traveler is told about: the place cannot be visited on the trip dates at all.
LEFT_OUT_REASONS = frozenset(
    {DropReason.CLOSED_ON_ALL_DATES, DropReason.LOCKED_DAY_CLOSED, DropReason.UNREACHABLE}
)


class PlanningAbort(Exception):
    """A typed, user-facing terminal error (mapped to the ``error`` stream event)."""

    def __init__(self, code: str, message: str, *, retryable: bool = False, **context: Any):
        super().__init__(code)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.context = context


@dataclass(slots=True)
class EffectivePreferences:
    pace: str | None
    interests: tuple[str, ...]
    modes: tuple[str, ...]
    day_start: time
    day_end: time
    must_see: tuple[uuid.UUID, ...]


@dataclass(slots=True)
class RunTrace:
    """Metadata of one run (versions for the preview revision); never user text."""

    model_version: str | None = None
    prompt_versions: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)  # app.trips.assumptions keys
    research_used: bool = False


def _parse_time(value: Any) -> time | None:
    if isinstance(value, time):
        return value
    if isinstance(value, str) and value:
        try:
            return time.fromisoformat(value)
        except ValueError:
            return None
    return None


def merge_preferences(
    request: PlanningPreferences | None,
    trip: Mapping[str, Any] | None,
    account: Any,
) -> EffectivePreferences:
    """Request preferences win over the trip's stored ones, which win over account defaults."""
    req = request.model_dump(exclude_none=True) if request is not None else {}
    stored = dict(trip or {})

    def pick(name: str) -> Any:
        if req.get(name) not in (None, [], ""):
            return req[name]
        if stored.get(name) not in (None, [], ""):
            return stored[name]
        return getattr(account, name, None)

    modes = tuple(pick("allowed_modes") or ("WALK", "DRIVE"))
    start = _parse_time(pick("day_start_time")) or DEFAULT_DAY_START
    end = _parse_time(pick("day_end_time")) or DEFAULT_DAY_END
    if end <= start:
        start, end = DEFAULT_DAY_START, DEFAULT_DAY_END
    must = req.get("must_see_place_ids") or stored.get("must_see_place_ids") or []
    return EffectivePreferences(
        pace=pick("pace"),
        interests=tuple(str(code).upper() for code in (pick("interest_category_codes") or ())),
        modes=modes,
        day_start=start,
        day_end=end,
        must_see=tuple(uuid.UUID(str(pid)) for pid in must),
    )


def planning_preferences_of(prefs: EffectivePreferences) -> PlanningPreferences:
    """The effective preferences in contract shape, stored on the preview snapshot."""
    return PlanningPreferences.model_validate(
        {
            "pace": prefs.pace,
            "interest_category_codes": list(prefs.interests)[:20] or None,
            "allowed_modes": list(prefs.modes) or None,
            "day_start_time": prefs.day_start.strftime("%H:%M"),
            "day_end_time": prefs.day_end.strftime("%H:%M"),
            "must_see_place_ids": [str(pid) for pid in prefs.must_see][:10] or None,
        }
    )


def vn_today(now: datetime) -> date:
    return (now.astimezone(UTC) + VN_OFFSET).date()


def choose_anchor(places: Sequence[PoolPlace]) -> Anchor:
    """Public anchor (never traveler GPS) nearest to the pool centroid; airport excluded."""
    options = [a for a in DA_NANG_ANCHORS if a.code != "dn-airport"]
    if not places:
        return options[0]
    lat = sum(p.lat for p in places) / len(places)
    lng = sum(p.lng for p in places) / len(places)
    centre = LatLng(lat, lng)
    return min(options, key=lambda a: (haversine_m(a.location, centre), a.code))


def primary_mode(modes: Sequence[str]) -> Literal["WALK", "DRIVE"]:
    return "DRIVE" if "DRIVE" in modes or not modes else "WALK"


class _Progress:
    def __init__(self, sink: EventSink) -> None:
        self._sink = sink

    def stage(self, stage: Stage, agent: str | None = None, **detail: int) -> None:
        event: dict[str, Any] = {"type": "progress", "stage": stage, "agent": agent}
        if detail:
            event["detail"] = detail
        self._sink.emit(event)


def _error_event(request_id: str, abort: PlanningAbort) -> dict[str, Any]:
    detail = error_payload(
        abort.code,
        abort.message,
        request_id,
        retryable=abort.retryable,
        context=abort.context or None,
    )["error"]
    return {"type": "error", "error": detail}


_PACE_LABELS: Mapping[str, Mapping[str, str]] = {
    "en": {"RELAXED": "relaxed", "BALANCED": "balanced", "PACKED": "packed"},
    "vi": {"RELAXED": "thong thả", "BALANCED": "cân bằng", "PACKED": "dày đặc"},
}


def time_of_day(arrival: time) -> TimeOfDay:
    """Day part of a planned arrival, the only schedule detail the rationale writer sees."""
    if arrival < time(11, 0):
        return "morning"
    if arrival < time(14, 0):
        return "midday"
    if arrival < time(17, 0):
        return "afternoon"
    return "evening"


def rationale_stop(
    place: PoolPlace, stop: SnapshotStop, locale: Literal["vi", "en"]
) -> RationaleStop:
    """Published, localized catalog text for one stop; no coordinates, hours or prices (BR-046)."""
    return RationaleStop(
        place_id=place.place_id,
        name=place.name(locale)[:200],
        category_code=place.category_code,
        category_label=(place.category_label(locale) or "")[:200] or None,
        area=(place.area_name(locale) or "")[:200] or None,
        summary=(place.summary(locale) or "")[:600] or None,
        description=trim_text(place.description(locale)),
        time_of_day=time_of_day(stop.planned_arrival),
    )


def rationale_traveller(
    prefs: EffectivePreferences, pool: Iterable[PoolPlace], locale: Literal["vi", "en"]
) -> RationaleTraveller | None:
    """Interests as localized category labels and the pace; ``None`` when neither is set."""
    labels = {p.category_code: p.category_label(locale) for p in pool if p.category_label(locale)}
    interests = [
        (labels.get(code) or code.replace("_", " ").lower())[:200] for code in prefs.interests[:20]
    ]
    pace = _PACE_LABELS[locale].get(prefs.pace or "") if prefs.pace else None
    if not interests and pace is None:
        return None
    return RationaleTraveller(interests=interests, pace=pace)


class PlanningOrchestrator:
    """The production :class:`app.planning.workflows.PlanningWorkflow`."""

    def __init__(
        self,
        session_factory: SessionFactory,
        settings: Settings,
        *,
        routes_provider: RoutesProvider | None = None,
        matrix_cache: MatrixCache | None = None,
        agent_runner: AgentRunner = default_runner,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._sf = session_factory
        self._settings = settings
        self._provider = routes_provider
        self._matrix_cache = matrix_cache
        self._runner = agent_runner
        self._clock = clock or (lambda: datetime.now(UTC))

    # ---- workflow entry points ---------------------------------------------------------------

    async def propose_trip(self, command: ProposeTripCommand, sink: EventSink) -> None:
        await self._guarded(command.request_id, sink, self._propose(command, sink))

    async def regenerate_day(self, command: RegenerateDayCommand, sink: EventSink) -> None:
        await self._guarded(command.request_id, sink, self._regenerate(command, sink))

    async def _guarded(self, request_id: str, sink: EventSink, run: Any) -> None:
        try:
            await run
        except PlanningAbort as abort:
            sink.emit(_error_event(request_id, abort))
        except AppError as exc:
            sink.emit(
                _error_event(
                    request_id,
                    PlanningAbort(exc.code, exc.message, retryable=exc.retryable),
                )
            )
        except Exception as exc:  # noqa: BLE001 - reported as an error event
            log_failure(logger, "planning_run_failed", exc, request_id=request_id)
            sink.emit(
                _error_event(
                    request_id,
                    PlanningAbort(
                        "internal_error", "The plan could not be created", retryable=True
                    ),
                )
            )
        finally:
            sink.close()

    # ---- propose_trip ------------------------------------------------------------------------

    async def _propose(self, command: ProposeTripCommand, sink: EventSink) -> None:
        progress = _Progress(sink)
        progress.stage("VALIDATING_REQUEST")
        body = command.request
        now = self._clock()
        fingerprint = idempotency.request_fingerprint(command.trip_id, body.model_dump(mode="json"))
        claimed = False
        # Everything after the claim commit runs inside this try, so a failure at any step
        # releases the IN_PROGRESS claim and a retry with the same key re-evaluates.
        try:
            async with self._sf() as session:
                trip = await self._owned_trip(session, command.account_id, command.trip_id)
                if body.expected_trip_revision != trip.revision:
                    raise PlanningAbort(
                        "revision_conflict",
                        "The trip changed since it was loaded.",
                        expected_trip_revision=body.expected_trip_revision,
                        current_revision=trip.revision,
                    )
                if command.idempotency_key is not None:
                    replay = await self._claim(
                        session,
                        command.account_id,
                        idempotency.OP_PREVIEW_CREATE,
                        command.idempotency_key,
                        fingerprint,
                        now,
                    )
                    if replay is not None:
                        sink.emit(replay)
                        return
                    claimed = True
                account_prefs = await PreferencesRepository(session).get_or_default(
                    command.account_id
                )
                prefs = merge_preferences(
                    body.preferences, trip.planning_preferences, account_prefs
                )
                city_id, trip_revision, day_count = trip.city_id, trip.revision, trip.day_count
                start_date = trip.start_date
                trip_prefs = dict(trip.planning_preferences or {})
                saved = (
                    await SQLAlchemyTripStore(session).saved_itinerary(trip.id)
                    if body.source == "SAVED_ITINERARY"
                    else None
                )
                pool = await load_pool(session, city_id) if saved is None else []
                rules = await load_rules(session, city_id) if saved is None else []
                providers = await self._provider_ids(session)
                await session.commit()

            if saved is not None:
                # Edit the saved itinerary: no AI, no routing (the saved legs are kept).
                snapshot = saved.snapshot.model_copy(deep=True)
                if not snapshot.days:
                    raise PlanningAbort("trip_not_saved", "The trip has no saved itinerary.")
                if trip_prefs:
                    snapshot.preferences = PlanningPreferences.model_validate(trip_prefs)
                health, _ = evaluate_health(snapshot)
                preview_id, revision, plan_health = await self._persist_new(
                    command, trip_revision, snapshot, health, RunTrace(), now
                )
            else:
                ledger = QuotaLedger(self._sf, self._settings, clock=self._clock)
                async with QuotaBudget(ledger, account_id=command.account_id) as budget:
                    decision = await budget.acquire(PROPOSE_BUDGET)
                    if not decision.allowed:
                        raise PlanningAbort(
                            "quota_exceeded",
                            "Daily planning limit reached; try again tomorrow.",
                            retryable=True,
                        )
                    frames = self._frames(day_count, start_date, prefs, now)
                    trace = RunTrace()
                    stored_prefs = planning_preferences_of(prefs)
                    snapshot, plan_health = await self._plan(
                        progress=progress,
                        ledger=ledger,
                        budget=budget,
                        account_id=command.account_id,
                        purpose=Purpose.PLAN_GENERATE,
                        locale=body.locale,
                        request_text=body.request_text or "",
                        prefs=prefs,
                        pool=pool,
                        rules=rules,
                        city_id=city_id,
                        frames=frames,
                        providers=providers,
                        trace=trace,
                        now=now,
                    )
                    snapshot.preferences = stored_prefs
                    preview_id, revision, plan_health = await self._persist_new(
                        command, trip_revision, snapshot, plan_health, trace, now
                    )
                    await budget.commit(Bucket.ACCOUNT_PROPOSALS)
        except BaseException:
            if claimed and command.idempotency_key is not None:
                await self._release_claim(
                    command.account_id, idempotency.OP_PREVIEW_CREATE, command.idempotency_key
                )
            raise
        sink.emit(
            {
                "type": "preview_ready",
                "preview_id": str(preview_id),
                "preview_revision": revision,
                "plan_health": plan_health,
            }
        )

    # ---- regenerate_day ----------------------------------------------------------------------

    async def _regenerate(self, command: RegenerateDayCommand, sink: EventSink) -> None:
        progress = _Progress(sink)
        progress.stage("VALIDATING_REQUEST")
        body = command.request
        now = self._clock()
        fingerprint = idempotency.request_fingerprint(
            command.preview_id, body.model_dump(mode="json")
        )
        claimed = False
        try:
            async with self._sf() as session:
                preview = await session.scalar(
                    select(PlanPreview).where(
                        PlanPreview.id == command.preview_id,
                        PlanPreview.account_id == command.account_id,
                    )
                )
                if preview is None:
                    raise PlanningAbort("resource_not_found", "Preview not found")
                if command.idempotency_key is not None:
                    # Before the head-revision check: a retry of a completed regeneration sees a
                    # moved head and must replay, not answer revision_conflict.
                    replay = await self._claim(
                        session,
                        command.account_id,
                        idempotency.OP_DAY_REGENERATE,
                        command.idempotency_key,
                        fingerprint,
                        now,
                    )
                    if replay is not None:
                        sink.emit(replay)
                        return
                    claimed = True
                if preview.status != "ACTIVE" or preview.expires_at <= now:
                    raise PlanningAbort("preview_closed", "This preview is no longer available")
                if body.expected_revision != preview.head_revision:
                    raise PlanningAbort(
                        "revision_conflict",
                        "The preview changed since it was loaded.",
                        expected_revision=body.expected_revision,
                        current_revision=preview.head_revision,
                    )
                trip = await self._owned_trip(session, command.account_id, preview.trip_id)
                if body.day_index > trip.day_count:
                    raise PlanningAbort("validation_error", "day_index is outside the trip")
                head = await session.get(PreviewRevision, (preview.id, preview.head_revision))
                if head is None:
                    raise PlanningAbort("resource_not_found", "Preview revision not found")
                parent = PlanSnapshot.model_validate(head.snapshot)
                account_prefs = await PreferencesRepository(session).get_or_default(
                    command.account_id
                )
                # The preferences the preview was generated with win over the trip's stored ones.
                stored = (
                    parent.preferences.model_dump(mode="json", exclude_none=True)
                    if parent.preferences is not None
                    else trip.planning_preferences
                )
                prefs = merge_preferences(None, stored, account_prefs)
                snapshot_prefs = parent.preferences or planning_preferences_of(prefs)
                city_id, day_count, start_date = trip.city_id, trip.day_count, trip.start_date
                pool = await load_pool(session, city_id)
                rules = await load_rules(session, city_id)
                providers = await self._provider_ids(session)
                await session.commit()

            ledger = QuotaLedger(self._sf, self._settings, clock=self._clock)
            async with QuotaBudget(ledger, account_id=command.account_id) as budget:
                decision = await budget.acquire(REGENERATE_DAY_BUDGET)
                if not decision.allowed:
                    raise PlanningAbort(
                        "quota_exceeded", "Daily planning limit reached; try again tomorrow."
                    )
                frames = self._frames(day_count, start_date, prefs, now)
                target = next(f for f in frames if f.day_index == body.day_index)
                old_day = next((d for d in parent.days if d.day_index == body.day_index), None)
                other = [d for d in parent.days if d.day_index != body.day_index]
                used = {s.place_id for d in other for s in d.stops if s.place_id is not None}
                requested_locks = set(body.locked_stop_ids or ())
                locks: dict[uuid.UUID, LockedStop] = {}
                stop_ids: dict[uuid.UUID, uuid.UUID] = {}
                if old_day is not None:
                    position = 0
                    for stop in old_day.stops:
                        if stop.place_id is None:
                            continue
                        stop_ids[stop.place_id] = stop.id
                        if stop.is_locked or stop.id in requested_locks:
                            locks[stop.place_id] = LockedStop(
                                stop.id, body.day_index, position, stop.visit_minutes
                            )
                            position += 1
                remaining = [p for p in pool if p.place_id not in used]
                prefs.must_see = tuple(locks) + tuple(
                    pid for pid in prefs.must_see if pid not in used and pid not in locks
                )
                trace = RunTrace()
                day_snapshot, _ = await self._plan(
                    progress=progress,
                    ledger=ledger,
                    budget=budget,
                    account_id=command.account_id,
                    purpose=Purpose.DAY_REGENERATE,
                    locale=body.locale or "vi",
                    request_text=body.instruction or "",
                    prefs=prefs,
                    pool=remaining,
                    rules=rules,
                    city_id=city_id,
                    frames=[target],
                    providers=providers,
                    trace=trace,
                    now=now,
                    locks=locks,
                    stop_ids=stop_ids,
                    evaluate_health=False,
                )
                days = sorted([*other, *day_snapshot.days], key=lambda d: d.day_index)
                dates = {f.day_index: f.date for f in frames}
                result = evaluate(
                    health_plan(days, dates, pool=by_id(pool), must_see=prefs.must_see),
                    self._windows(pool, rules, city_id, frames),
                    today=vn_today(now),
                )
                snapshot = PlanSnapshot(
                    days=days,
                    health_reasons=attach_conflicts(days, result),
                    assumptions=unique_keys([*parent.assumptions, *trace.assumptions]),
                    research_used=parent.research_used or trace.research_used,
                    preferences=snapshot_prefs,
                )
                revision = await self._append_revision(command, snapshot, result.plan_health, trace)
                await budget.commit(Bucket.ACCOUNT_PROPOSALS)
        except BaseException:
            if claimed and command.idempotency_key is not None:
                await self._release_claim(
                    command.account_id, idempotency.OP_DAY_REGENERATE, command.idempotency_key
                )
            raise
        sink.emit(
            {
                "type": "preview_ready",
                "preview_id": str(command.preview_id),
                "preview_revision": revision,
                "plan_health": result.plan_health,
            }
        )

    # ---- the pipeline ------------------------------------------------------------------------

    async def _plan(
        self,
        *,
        progress: _Progress,
        ledger: QuotaLedger,
        budget: QuotaBudget,
        account_id: uuid.UUID,
        purpose: Purpose,
        locale: Literal["vi", "en"],
        request_text: str,
        prefs: EffectivePreferences,
        pool: Sequence[PoolPlace],
        rules: Sequence[Any],
        city_id: uuid.UUID,
        frames: Sequence[DayFrame],
        providers: ProviderIds,
        trace: RunTrace,
        now: datetime,
        locks: Mapping[uuid.UUID, LockedStop] | None = None,
        stop_ids: Mapping[uuid.UUID, uuid.UUID] | None = None,
        evaluate_health: bool = True,
    ) -> tuple[PlanSnapshot, str]:
        if not pool:
            raise PlanningAbort(
                "unsupported_request", "No published places are available for this city yet."
            )
        ctx = AgentContext(
            settings=self._settings,
            ledger=ledger,
            session_factory=self._sf,
            purpose=purpose,
            account_id=account_id,
            budget=budget,
            runner=self._runner,
        )
        places = by_id(pool)
        must_see = tuple(pid for pid in prefs.must_see if pid in places)

        # 2. selection
        use_model = self._chain_configured(Role.SELECTOR)
        progress.stage(
            "SELECTING_PLACES", "selector" if use_model else None, catalog_candidates=len(pool)
        )
        picked = await self._select(
            ctx, pool, prefs, must_see, request_text, len(frames), locale, use_model, trace
        )

        # 3. research (off by default)
        if self._settings.research_enabled and len(pool) < pool_size(len(frames), prefs.pace):
            progress.stage("RESEARCHING", "researcher")
            await self._research(ctx, request_text, locale, pool, trace)

        # 4. routing
        selected = [places[pid] for pid in picked]
        anchor = choose_anchor(selected)
        mode = primary_mode(prefs.modes)
        progress.stage("ROUTING")
        matrix = await self._matrix(selected, anchor, mode, ledger)
        windows = self._windows(selected, rules, city_id, frames)
        leg_modes = await self._leg_modes(selected, frames, windows, mode, prefs.modes, ledger)

        # 5. scheduling
        progress.stage("SCHEDULING")
        wanted = wanted_interests(prefs.interests, request_text)
        inp = ScheduleInput(
            frames=frames,
            places=selected,
            windows=windows,
            matrix=matrix,
            anchor_key=anchor.key,
            mode=mode,
            must_see=frozenset(must_see),
            locks=locks or {},
            # Day balance: the pace caps stops per day and every day gets a fair share
            # (a 2-day plan once put all 10 stops on day 1); per-category caps keep variety.
            max_stops_per_day=stops_per_day(prefs.pace),
            category_day_caps={
                p.category_code: cap
                for p in selected
                if (cap := category_day_cap(p.category_code, wanted)) is not None
            },
            leg_modes=leg_modes,
        )
        output = await asyncio.to_thread(schedule, inp)
        days = build_days(inp, output, provider_ids=providers, now=now, stop_ids=stop_ids)
        if output.buffered:
            trace.assumptions.append(NO_ROUTES)
        if any(leg.estimated for day in days for leg in day.legs):
            trace.assumptions.append(ESTIMATED_LEGS)
        if mode != "WALK" and any(leg.travel_mode == "WALK" for day in days for leg in day.legs):
            trace.assumptions.append(WALK_IN_RESTRICTED_ZONE)
        if any(drop.reason in LEFT_OUT_REASONS for drop in output.result.dropped):
            trace.assumptions.append(STOPS_LEFT_OUT)

        # 6. Plan Health
        plan_health = "GOOD"
        reasons: list[Any] = []
        if evaluate_health:
            progress.stage("CHECKING_HEALTH")
            dates = {f.day_index: f.date for f in frames}
            result = evaluate(
                health_plan(days, dates, pool=places, must_see=must_see),
                windows,
                today=vn_today(now),
            )
            reasons = attach_conflicts(days, result)
            plan_health = result.plan_health

        # 7. rationales (never block)
        stops = [s for d in days for s in d.stops if s.place_id is not None]
        if stops and self._chain_configured(Role.WRITER_RATIONALE):
            progress.stage("WRITING", "grounded_writer")
            await self._rationales(ctx, request_text, locale, days, places, prefs, trace)

        snapshot = PlanSnapshot(
            days=days,
            health_reasons=reasons,
            assumptions=unique_keys(trace.assumptions),
            research_used=trace.research_used,
        )
        return snapshot, plan_health

    def _chain_configured(self, role: Role) -> bool:
        return any(provider_configured(s.provider, self._settings) for s in role_chain(role))

    async def _select(
        self,
        ctx: AgentContext,
        pool: Sequence[PoolPlace],
        prefs: EffectivePreferences,
        must_see: Sequence[uuid.UUID],
        request_text: str,
        days: int,
        locale: Literal["vi", "en"],
        use_model: bool,
        trace: RunTrace,
    ) -> list[uuid.UUID]:
        candidates = [
            RuleCandidate(p.place_id, p.category_code, p.area_code, p.famous) for p in pool
        ]
        target = pool_size(days, prefs.pace)
        wanted = wanted_interests(prefs.interests, request_text)
        ranked = rank_candidates(candidates, interests=prefs.interests, request_text=request_text)
        category = {c.place_id: c.category_code for c in candidates}

        def varied(picks: Sequence[uuid.UUID], fallback: Sequence[uuid.UUID]) -> list[uuid.UUID]:
            return diversify(
                picks,
                category.__getitem__,
                days=days,
                wanted=wanted,
                target=target,
                must_see=must_see,
                fallback=fallback,
            )

        rule_pick = varied(
            select_rule_based(
                candidates,
                days=days,
                pace=prefs.pace,
                interests=prefs.interests,
                request_text=request_text,
                must_see=must_see,
            ),
            [c.place_id for c in ranked],
        )
        if not use_model:
            return rule_pick
        shortlist_ids = list(dict.fromkeys([*must_see, *rule_pick, *(c.place_id for c in ranked)]))
        shortlist_ids = shortlist_ids[: max(MAX_CANDIDATES, len(must_see))]
        places = by_id(pool)
        dtos = [
            CandidateDto(
                place_id=pid,
                name_vi=places[pid].name_vi,
                name_en=places[pid].name_en,
                category_code=places[pid].category_code,
                area_code=places[pid].area_code,
                summary=places[pid].summary(locale),
                open_windows=[],
            )
            for pid in shortlist_ids
        ]
        outcome = await select_places(
            ctx,
            request_text=request_text,
            candidates=dtos,
            days=days,
            locale=locale,
            must_see=must_see,
            preferences={
                "pace": prefs.pace or "BALANCED",
                "interests": ",".join(prefs.interests),
                "picks_wanted": str(target),
            },
            max_picks=max(target, len(must_see)),
        )
        if outcome.source not in (ResultSource.MODEL, ResultSource.REPAIRED):
            return rule_pick
        # Defence in depth: re-check against the whole pool (unknown IDs ⇒ rule-based).
        check = validate_selection(
            outcome.result,
            candidate_ids=list(places),
            must_see=must_see,
            days=days,
            max_picks=max(target, len(must_see)),
        )
        if check.result is None:
            return rule_pick
        model_pick = [uuid.UUID(p.place_id) for p in check.result.picks]
        if outcome.attempts:
            trace.model_version = outcome.attempts[-1].provider_model
        trace.prompt_versions.append(load_instructions("selector", locale)[1])
        # Category variety (at most N per category per day unless it is the only interest), then
        # top up with rule-based picks when the model returned a short list.
        return varied(model_pick, rule_pick)

    async def _research(
        self,
        ctx: AgentContext,
        request_text: str,
        locale: Literal["vi", "en"],
        pool: Sequence[PoolPlace],
        trace: RunTrace,
    ) -> None:
        """Run the researcher under a hard timeout; on timeout or failure the plan proceeds."""
        from app.agents.researcher import run_research
        from app.research.candidates_repo import store_candidates
        from app.research.fetch import PageFetcher
        from app.research.places_check import PlacesChecker
        from app.research.store import SqlResearchStore
        from app.research.tavily import TavilySearch
        from app.research.toolbox import ResearchToolbox

        settings = self._settings
        if not request_text.strip() or not self._chain_configured(Role.RESEARCHER):
            return
        tavily = settings.tavily_api_key.get_secret_value() if settings.tavily_api_key else None
        maps = (
            settings.google_maps_api_key.get_secret_value()
            if settings.google_maps_api_key
            else None
        )
        # DRAFT provider policies only in development/test/demo; staging needs ACTIVE ones.
        store = SqlResearchStore(self._sf, allow_draft_policies=settings.draft_policies_allowed)
        fetcher = PageFetcher(store=store)
        try:
            box = ResearchToolbox(
                search=TavilySearch(api_key=tavily, ledger=ctx.ledger, store=store),
                fetcher=fetcher,
                places=PlacesChecker(api_key=maps, ledger=ctx.ledger, store=store),
            )
            outcome = await asyncio.wait_for(
                run_research(
                    ctx,
                    request_text=request_text,
                    locale=locale,
                    tools=box,
                    known_names=[p.name(locale) for p in pool],
                ),
                timeout=settings.research_timeout_s,
            )
            if outcome.report.candidates:
                model = outcome.attempts[-1].provider_model if outcome.attempts else None
                await store_candidates(
                    self._sf,
                    candidates=outcome.report.candidates,
                    toolbox=box,
                    extraction_model=model,
                )
                trace.research_used = True
        except TimeoutError:
            logger.info("planning research_timeout")
            trace.assumptions.append(RESEARCH_SKIPPED)
        except Exception:  # noqa: BLE001 - research must never fail the plan
            logger.warning("planning research_failed")
            trace.assumptions.append(RESEARCH_SKIPPED)
        finally:
            await fetcher.aclose()

    async def _matrix(
        self,
        selected: Sequence[PoolPlace],
        anchor: Anchor | None,
        mode: Literal["WALK", "DRIVE"],
        ledger: QuotaLedger,
    ) -> RouteMatrix:
        provider = self._provider
        if provider is None:
            try:
                provider = select_provider(
                    self._settings, estimate_enabled=self._settings.routes_estimate_enabled
                )
            except EstimateNotAllowedError:
                logger.warning(
                    "planning routes_estimate_refused env=%s", self._settings.environment
                )
                provider = NoRoutesProvider()
        coords = {anchor.key: anchor.location} if anchor is not None else {}
        coords.update({p.key: LatLng(p.lat, p.lng) for p in selected})
        return await get_matrix(
            self._sf,
            keys_with_coords=coords,
            mode=mode,
            ledger=ledger,
            provider=provider,
            cache=self._matrix_cache,
        )

    async def _leg_modes(
        self,
        selected: Sequence[PoolPlace],
        frames: Sequence[DayFrame],
        windows: Mapping[Any, Any],
        mode: Literal["WALK", "DRIVE"],
        allowed_modes: Sequence[str],
        ledger: QuotaLedger,
    ) -> LegModePlan:
        """Restricted travel modes (car-free zones): walk where reasonable, else ban (ADR-011
        amendment 2026-11-09). Walking legs are measured only between the restricted places."""
        places = [(p.key, p.place_id) for p in selected]
        dates = [f.date for f in frames]
        restricted = restricted_pairs(places, dates, windows, mode)
        if not restricted:
            return LegModePlan()
        walk_matrix: RouteMatrix | None = None
        if mode != "WALK" and "WALK" in allowed_modes:
            keys = set(restricted_keys(restricted))
            walk_matrix = await self._matrix(
                [p for p in selected if p.key in keys], None, "WALK", ledger
            )
        return plan_leg_modes(
            restricted,
            mode=mode,
            allowed_modes=allowed_modes,
            walk_matrix=walk_matrix,
            walk_restricted=restricted_pairs(places, dates, windows, "WALK"),
        )

    def _windows(
        self,
        places: Sequence[PoolPlace],
        rules: Sequence[Any],
        city_id: uuid.UUID,
        frames: Sequence[DayFrame],
    ) -> dict[Any, Any]:
        return effective_windows(
            base_hours={p.place_id: p.hours for p in places},
            rules=rules,
            places=[PlaceRef(p.place_id, p.area_code, city_id) for p in places],
            dates=[f.date for f in frames],
        )

    async def _rationales(
        self,
        ctx: AgentContext,
        request_text: str,
        locale: Literal["vi", "en"],
        days: Sequence[SnapshotDay],
        places: Mapping[uuid.UUID, PoolPlace],
        prefs: EffectivePreferences,
        trace: RunTrace,
    ) -> None:
        stops = [s for d in days for s in d.stops if s.place_id in places]
        try:
            outcome = await write_rationales(
                ctx,
                request_text=request_text,
                stops=[rationale_stop(places[s.place_id], s, locale) for s in stops if s.place_id],
                locale=locale,
                traveller=rationale_traveller(prefs, places.values(), locale),
            )
        except Exception:  # noqa: BLE001 - rationales never block a plan
            logger.warning("planning rationale_failed")
            return
        if outcome.source is not ResultSource.MODEL:
            return
        for stop in stops:
            if stop.place_id is not None:
                stop.rationale = outcome.rationales.get(stop.place_id)
        trace.prompt_versions.append(load_instructions(RATIONALE_AGENT, locale)[1])

    # ---- helpers: DB -------------------------------------------------------------------------

    async def _owned_trip(
        self, session: AsyncSession, account_id: uuid.UUID, trip_id: uuid.UUID
    ) -> Trip:
        trip = await session.scalar(
            select(Trip).where(Trip.id == trip_id, Trip.account_id == account_id)
        )
        if trip is None:
            raise PlanningAbort("resource_not_found", "Trip not found")
        return trip

    def _frames(
        self, day_count: int, start: date | None, prefs: EffectivePreferences, now: datetime
    ) -> list[DayFrame]:
        first = start or vn_today(now)
        start_min = prefs.day_start.hour * 60 + prefs.day_start.minute
        end_min = prefs.day_end.hour * 60 + prefs.day_end.minute
        return [
            DayFrame(i + 1, first + timedelta(days=i), start_min, end_min)
            for i in range(max(1, min(3, day_count)))
        ]

    async def _provider_ids(self, session: AsyncSession) -> ProviderIds:
        """``data_providers`` rows behind leg measurements; created on first use if missing."""
        google = await _ensure_provider(session, ROUTES_PROVIDER_KEY, "Google Routes API")
        estimate = await _ensure_provider(
            session, ROUTES_ESTIMATE_PROVIDER_KEY, "Gonarra straight-line estimate (demo only)"
        )
        return ProviderIds(google_routes=google, estimate=estimate)

    async def _claim(
        self,
        session: AsyncSession,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        fingerprint: str,
        now: datetime,
    ) -> dict[str, Any] | None:
        store = SQLAlchemyTripStore(session)
        existing = await store.claim_idempotency(
            account_id,
            operation,
            key,
            fingerprint,
            idempotency.expires_at(now),
        )
        if existing is None:
            await session.commit()  # the claim must be visible while the run is in flight
            return None
        stored = idempotency.replay_or_raise(existing, fingerprint)
        await session.rollback()
        return {
            "type": "preview_ready",
            "preview_id": stored.body.get("preview_id"),
            "preview_revision": stored.body.get("preview_revision"),
            "plan_health": stored.body.get("plan_health"),
        }

    async def _release_claim(self, account_id: uuid.UUID, operation: str, key: str) -> None:
        try:
            async with self._sf() as session:
                await session.execute(
                    delete(IdempotencyRecord).where(
                        IdempotencyRecord.account_id == account_id,
                        IdempotencyRecord.operation == operation,
                        IdempotencyRecord.idempotency_key == key,
                        IdempotencyRecord.state == "IN_PROGRESS",
                    )
                )
                await session.commit()
        except Exception:  # noqa: BLE001 - the record expires on its own
            logger.warning("planning idempotency_release_failed")

    async def _persist_new(
        self,
        command: ProposeTripCommand,
        base_revision: int,
        snapshot: PlanSnapshot,
        plan_health: str,
        trace: RunTrace,
        now: datetime,
    ) -> tuple[uuid.UUID, int, str]:
        """New ACTIVE preview with revision 1. A newer trip revision (Save elsewhere) wins: the
        late result is not written (ADR-009). Any older ACTIVE preview of the trip is discarded
        (one ACTIVE preview per trip)."""
        async with self._sf() as session:
            trip = await session.scalar(
                select(Trip)
                .where(Trip.id == command.trip_id, Trip.account_id == command.account_id)
                .with_for_update()
            )
            if trip is None:
                raise PlanningAbort("resource_not_found", "Trip not found")
            if trip.revision != base_revision:
                raise PlanningAbort(
                    "revision_conflict",
                    "The trip changed while the plan was being created.",
                    current_revision=trip.revision,
                )
            await session.execute(
                update(PlanPreview)
                .where(PlanPreview.trip_id == trip.id, PlanPreview.status == "ACTIVE")
                .values(status="DISCARDED", updated_at=now)
            )
            preview = PlanPreview(
                id=uuid.uuid4(),
                account_id=command.account_id,
                trip_id=trip.id,
                base_trip_revision=base_revision,
                head_revision=1,
                status="ACTIVE",
                expires_at=now + PREVIEW_TTL,
            )
            session.add(preview)
            await session.flush()
            session.add(
                PreviewRevision(
                    plan_preview_id=preview.id,
                    preview_revision=1,
                    parent_revision=None,
                    origin="GENERATED",
                    plan_health=plan_health,
                    snapshot=snapshot.model_dump(mode="json"),
                    model_version=trace.model_version or RULE_BASED_VERSION,
                    prompt_version=",".join(trace.prompt_versions) or None,
                    corpus_revision=None,
                )
            )
            await session.flush()
            if command.idempotency_key is not None:
                await SQLAlchemyTripStore(session).complete_idempotency(
                    command.account_id,
                    idempotency.OP_PREVIEW_CREATE,
                    command.idempotency_key,
                    status=201,
                    body={
                        "preview_id": str(preview.id),
                        "preview_revision": 1,
                        "plan_health": plan_health,
                    },
                    resource_id=preview.id,
                )
            await session.commit()
            return preview.id, 1, plan_health

    async def _append_revision(
        self,
        command: RegenerateDayCommand,
        snapshot: PlanSnapshot,
        plan_health: str,
        trace: RunTrace,
    ) -> int:
        """Append a DAY_REGENERATED revision if the head did not move meanwhile (ADR-009)."""
        async with self._sf() as session:
            preview = await session.scalar(
                select(PlanPreview)
                .where(
                    PlanPreview.id == command.preview_id,
                    PlanPreview.account_id == command.account_id,
                )
                .with_for_update()
            )
            expected = command.request.expected_revision
            if preview is None or preview.status != "ACTIVE":
                raise PlanningAbort("preview_closed", "This preview is no longer available")
            if preview.head_revision != expected:
                raise PlanningAbort(
                    "revision_conflict",
                    "The preview changed while the day was being regenerated.",
                    current_revision=preview.head_revision,
                )
            number = expected + 1
            session.add(
                PreviewRevision(
                    plan_preview_id=preview.id,
                    preview_revision=number,
                    parent_revision=expected,
                    origin="DAY_REGENERATED",
                    plan_health=plan_health,
                    snapshot=snapshot.model_dump(mode="json"),
                    model_version=trace.model_version or RULE_BASED_VERSION,
                    prompt_version=",".join(trace.prompt_versions) or None,
                )
            )
            await session.flush()
            await session.execute(
                update(PlanPreview).where(PlanPreview.id == preview.id).values(head_revision=number)
            )
            if command.idempotency_key is not None:
                await SQLAlchemyTripStore(session).complete_idempotency(
                    command.account_id,
                    idempotency.OP_DAY_REGENERATE,
                    command.idempotency_key,
                    status=201,
                    body={
                        "preview_id": str(preview.id),
                        "preview_revision": number,
                        "plan_health": plan_health,
                    },
                    resource_id=preview.id,
                )
            await session.commit()
            return number


async def _ensure_provider(session: AsyncSession, key: str, display_name: str) -> uuid.UUID:
    await session.execute(
        insert(DataProvider)
        .values(provider_key=key, display_name=display_name, provider_kind="RUNTIME_API")
        .on_conflict_do_nothing(index_elements=[DataProvider.provider_key])
    )
    provider_id = await session.scalar(
        select(DataProvider.id).where(DataProvider.provider_key == key)
    )
    if provider_id is None:  # pragma: no cover - the upsert above guarantees a row
        raise RuntimeError("data provider missing")
    return provider_id
