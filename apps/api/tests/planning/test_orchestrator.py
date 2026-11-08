"""Orchestrator pipeline with fakes: rule-based selector, validator fallback, routing modes.

No database, no keys, no live providers. The DB-backed flow (preview persistence, SSE route) is
covered by ``tests/integration/test_planning_orchestrator.py``.
"""

from __future__ import annotations

import json
import random
import uuid
from collections import Counter
from collections.abc import Sequence
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, time
from typing import Any

from agno.agent import Agent
from agno.models.message import Message
from agno.run.agent import RunOutput

from app.ai.invocations import Purpose
from app.ai.quota import Bucket, QuotaBudget, QuotaDecision, QuotaReservation
from app.config import Settings
from app.planning.assemble import DayFrame, ProviderIds
from app.planning.calendar.windows import OpeningHours
from app.planning.orchestrator import (
    EffectivePreferences,
    PlanningOrchestrator,
    RunTrace,
    _Progress,
    choose_anchor,
    merge_preferences,
    planning_preferences_of,
)
from app.planning.pool import PoolPlace
from app.planning.rule_selector import (
    RuleCandidate,
    fame_preference,
    interests_from_text,
    select_rule_based,
)
from app.routing.matrix_cache import CachedLeg
from app.routing.provider import NoRoutesProvider, TravelMode

NOW = datetime(2026, 11, 8, 2, 0, tzinfo=UTC)
CITY = uuid.UUID(int=0xC1)
ACCOUNT = uuid.UUID(int=0xACC)
GOOGLE_ID = uuid.UUID(int=0x600)
ESTIMATE_ID = uuid.UUID(int=0xE57)
TUE = date(2026, 11, 10)

# (category, area, famous, lat, lng)
SPECS = [
    ("HERITAGE", "hai-chau", True, 16.0610, 108.2240),
    ("MUSEUM", "hai-chau", True, 16.0600, 108.2230),
    ("BEACH", "son-tra", True, 16.0640, 108.2460),
    ("FOOD", "hai-chau", False, 16.0680, 108.2200),
    ("FOOD", "son-tra", False, 16.0700, 108.2400),
    ("CAFE", "hai-chau", False, 16.0650, 108.2220),
    ("MARKET", "hai-chau", True, 16.0680, 108.2250),
    ("RELIGIOUS_SITE", "ngu-hanh-son", False, 16.0030, 108.2630),
    ("VIEWPOINT", "son-tra", False, 16.1000, 108.2700),
    ("NATURE", "son-tra", False, 16.1100, 108.2800),
]


def place(i: int, category: str, area: str, famous: bool, lat: float, lng: float) -> PoolPlace:
    return PoolPlace(
        place_id=uuid.UUID(int=0x1000 + i, version=4),
        catalog_publication_id=uuid.UUID(int=0x2000 + i, version=4),
        category_code=category,
        area_code=area,
        name_vi=f"Điểm {i}",
        name_en=f"Place {i}",
        summary_vi=None,
        summary_en=None,
        lat=lat,
        lng=lng,
        visit_minutes=60,
        famous=famous,
        hours=OpeningHours.every_day("07:00", "22:00"),
        fact_verified_at=date(2026, 10, 1),
    )


POOL = [place(i, *spec) for i, spec in enumerate(SPECS)]
CANDIDATES = [RuleCandidate(p.place_id, p.category_code, p.area_code, p.famous) for p in POOL]


# ---- fakes --------------------------------------------------------------------------------


class FakeLedger:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.used: Counter[Bucket] = Counter()

    async def reserve(
        self, *, bucket: Bucket, amount: int = 1, account_id: uuid.UUID | None = None
    ) -> QuotaDecision:
        res = QuotaReservation(uuid.uuid4(), bucket, amount, account_id, date(2026, 11, 8))
        return QuotaDecision(True, bucket, 100, res)

    async def commit(self, reservation: QuotaReservation) -> None:
        self.used[reservation.bucket] += reservation.amount

    async def release(self, reservation: QuotaReservation) -> None:
        return None


class FakeCache:
    def __init__(self) -> None:
        self.writes: list[CachedLeg] = []

    async def read(
        self, keys: Sequence[str], mode: TravelMode, *, now: datetime
    ) -> dict[tuple[str, str], CachedLeg]:
        return {}

    async def write(self, legs: Any, mode: TravelMode, *, now: datetime) -> int:
        self.writes.extend(legs)
        return len(self.writes)


class _Session:
    async def execute(self, *args: Any, **kwargs: Any) -> None:
        return None

    async def commit(self) -> None:
        return None


@asynccontextmanager
async def fake_session() -> Any:
    yield _Session()


class Sink:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event: Any) -> None:
        self.events.append(dict(event))

    def close(self) -> None:
        return None


class Runner:
    """Scripted model answers (JSON strings); records which model was called."""

    def __init__(self, answers: list[Any]) -> None:
        self.answers = list(answers)
        self.models: list[str] = []
        self.prompts: list[str] = []

    async def __call__(self, agent: Agent, prompt: str) -> RunOutput:
        assert agent.model is not None
        self.models.append(str(agent.model.id))
        self.prompts.append(prompt)
        answer = self.answers.pop(0)
        content = answer if isinstance(answer, str) else json.dumps(answer)
        return RunOutput(content=content, messages=[Message(role="assistant", content="x")])


def settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {"environment": "test"}
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


def prefs(**overrides: Any) -> EffectivePreferences:
    base: dict[str, Any] = {
        "pace": "BALANCED",
        "interests": (),
        "modes": ("WALK", "DRIVE"),
        "day_start": time(8, 0),
        "day_end": time(20, 0),
        "must_see": (),
    }
    base.update(overrides)
    return EffectivePreferences(**base)


async def run_plan(
    orchestrator: PlanningOrchestrator,
    cfg: Settings,
    *,
    days: int = 1,
    request_text: str = "",
    pref: EffectivePreferences | None = None,
) -> tuple[Any, str, Sink, RunTrace]:
    ledger = FakeLedger(cfg)
    sink = Sink()
    trace = RunTrace()
    frames = [DayFrame(i + 1, date(2026, 11, 10 + i), 8 * 60, 20 * 60) for i in range(days)]
    async with QuotaBudget(ledger, account_id=ACCOUNT) as budget:  # type: ignore[arg-type]
        snapshot, health = await orchestrator._plan(
            progress=_Progress(sink),
            ledger=ledger,  # type: ignore[arg-type]
            budget=budget,
            account_id=ACCOUNT,
            purpose=Purpose.PLAN_GENERATE,
            locale="en",
            request_text=request_text,
            prefs=pref or prefs(),
            pool=POOL,
            rules=[],
            city_id=CITY,
            frames=frames,
            providers=ProviderIds(GOOGLE_ID, ESTIMATE_ID),
            trace=trace,
            now=NOW,
        )
    return snapshot, health, sink, trace


# ---- rule-based selector ------------------------------------------------------------------


def test_rule_selector_is_deterministic_and_order_independent() -> None:
    first = select_rule_based(CANDIDATES, days=2, pace="BALANCED")
    shuffled = list(CANDIDATES)
    random.Random(7).shuffle(shuffled)
    assert select_rule_based(shuffled, days=2, pace="BALANCED") == first
    assert len(first) == len(set(first)) == len(POOL)  # (6+1)*2 = 14 > 10 → everything


def test_rule_selector_meals_interests_must_see_and_fame() -> None:
    by_cat = {p.category_code: p.place_id for p in reversed(POOL)}
    must = POOL[9].place_id
    picked = select_rule_based(
        CANDIDATES, days=1, pace="RELAXED", interests=("BEACH",), must_see=(must,)
    )
    assert picked[0] == must  # must-sees first
    assert len(picked) == 5  # (4+1) * 1 day
    cats = [next(p.category_code for p in POOL if p.place_id == pid) for pid in picked]
    assert cats.count("FOOD") == 2 and cats.count("CAFE") == 1  # meal slots
    assert by_cat["BEACH"] in picked  # interest match

    hidden = select_rule_based(
        CANDIDATES, days=1, pace="RELAXED", request_text="hidden local spots, no food"
    )
    famous = select_rule_based(CANDIDATES, days=1, pace="RELAXED", request_text="famous sights")
    famous_ids = {p.place_id for p in POOL if p.famous}
    assert sum(pid in famous_ids for pid in famous) > sum(pid in famous_ids for pid in hidden)


def test_keyword_and_fame_parsing_vi_en() -> None:
    assert {"BEACH", "FOOD"} <= interests_from_text("Tắm biển và ăn uống đặc sản")
    assert "CAFE" in interests_from_text("cà phê sáng")
    assert fame_preference("chỗ ít người, địa phương") == "HIDDEN"
    assert fame_preference("những nơi nổi tiếng") == "FAMOUS"
    assert fame_preference(None) is None


def test_keywords_do_not_collide_with_common_vietnamese_words() -> None:
    # "đến" (go to) is not "đền" (temple), "cho" (for) is not "chợ" (market), "gia đình" is
    # not a beach; folded single syllables must not trigger interests.
    assert interests_from_text("Tôi muốn đến Hội An, gợi ý cho gia đình") == frozenset()
    assert interests_from_text("toi muon den hoi an, goi y cho gia dinh") == frozenset()
    assert interests_from_text("bài viết hay") == frozenset()
    assert fame_preference("Tôi muốn nói tiếng Anh") is None
    # Diacritic-aware and multi-word folded keywords still match.
    assert "RELIGIOUS_SITE" in interests_from_text("thăm đền và chùa")
    assert "MARKET" in interests_from_text("đi chợ Hàn")
    assert "BEACH" in interests_from_text("bai bien My Khe")
    assert "MUSEUM" in interests_from_text("bao tang Cham")
    assert "MUSEUM" not in interests_from_text("nhân viên lịch sự")


def test_merge_preferences_request_wins() -> None:
    class Account:
        pace = "RELAXED"
        interest_category_codes = ("MUSEUM",)
        allowed_modes = ("WALK",)
        day_start_time = time(9, 0)
        day_end_time = time(18, 0)

    merged = merge_preferences(None, {"pace": "PACKED"}, Account())
    assert merged.pace == "PACKED" and merged.interests == ("MUSEUM",)
    assert merged.modes == ("WALK",) and merged.day_start == time(9, 0)


def test_anchor_is_public_and_near_pool() -> None:
    hoi_an = [place(99, "HERITAGE", "hoi-an-old-town", True, 15.877, 108.326)]
    assert choose_anchor(hoi_an).code == "hoi-an-old-town"
    assert choose_anchor(POOL[:3]).code != "dn-airport"


# ---- pipeline with fakes ------------------------------------------------------------------


async def test_plan_without_keys_uses_rules_and_estimates() -> None:
    cfg = settings(routes_estimate_enabled=True)
    cache = FakeCache()
    orch = PlanningOrchestrator(fake_session, cfg, matrix_cache=cache, clock=lambda: NOW)
    snapshot, health, sink, trace = await run_plan(orch, cfg, days=2)

    stages = [(e["stage"], e["agent"]) for e in sink.events]
    assert stages == [
        ("SELECTING_PLACES", None),
        ("ROUTING", None),
        ("SCHEDULING", None),
        ("CHECKING_HEALTH", None),
    ]  # no WRITING without a writer key
    assert [d.day_index for d in snapshot.days] == [1, 2]
    stops = [s for d in snapshot.days for s in d.stops]
    assert stops and {s.place_id for s in stops} <= {p.place_id for p in POOL}
    assert all(s.rationale is None for s in stops)
    legs = [leg for d in snapshot.days for leg in d.legs]
    assert legs and all(leg.estimated and leg.availability == "AVAILABLE" for leg in legs)
    assert all(leg.data_provider_id == ESTIMATE_ID and leg.expires_at is None for leg in legs)
    for leg in legs:
        assert [(c.type, c.severity) for c in leg.conflicts] == [("LEG_ESTIMATED", "INFO")]
    assert health == "GOOD"  # INFO notices never downgrade the plan
    assert cache.writes == []  # estimates are never cached
    assert trace.model_version is None and trace.assumptions

    # Same input → same plan (stop ids aside).
    again, *_ = await run_plan(orch, cfg, days=2)
    assert [[s.place_id for s in d.stops] for d in again.days] == [
        [s.place_id for s in d.stops] for d in snapshot.days
    ]


async def test_plan_without_routing_provider_still_returns_blocked_plan() -> None:
    cfg = settings()
    orch = PlanningOrchestrator(
        fake_session,
        cfg,
        routes_provider=NoRoutesProvider(),
        matrix_cache=FakeCache(),
        clock=lambda: NOW,
    )
    snapshot, health, _, trace = await run_plan(orch, cfg)
    stops = snapshot.days[0].stops
    assert len(stops) >= 2
    legs = snapshot.days[0].legs
    assert legs and all(
        leg.availability == "UNAVAILABLE" and leg.duration_s is None for leg in legs
    )
    assert health == "BLOCKED"
    assert any(c.type == "LEG_UNAVAILABLE" for leg in legs for c in leg.conflicts)
    assert "no_routes" in trace.assumptions  # a stable key, localized at response time


async def test_estimate_refused_in_production_degrades_to_unavailable() -> None:
    cfg = settings(environment="production", routes_estimate_enabled=True)
    orch = PlanningOrchestrator(fake_session, cfg, matrix_cache=FakeCache(), clock=lambda: NOW)
    snapshot, health, _, _ = await run_plan(orch, cfg)
    assert all(not leg.estimated for d in snapshot.days for leg in d.legs)
    assert health == "BLOCKED"


async def test_selector_unknown_ids_fall_back_to_rule_based() -> None:
    cfg = settings(gemini_api_key="gem-test", routes_estimate_enabled=True)
    bogus = {"picks": [{"place_id": str(uuid.uuid4()), "rank": 1}]}
    runner = Runner([bogus, bogus, bogus, bogus])
    orch = PlanningOrchestrator(
        fake_session, cfg, matrix_cache=FakeCache(), agent_runner=runner, clock=lambda: NOW
    )
    snapshot, _, sink, trace = await run_plan(orch, cfg)
    assert runner.models  # the model was asked
    assert sink.events[0] == {
        "type": "progress",
        "stage": "SELECTING_PLACES",
        "agent": "selector",
        "detail": {"catalog_candidates": len(POOL)},
    }
    rule = select_rule_based(CANDIDATES, days=1, pace="BALANCED")
    scheduled = {s.place_id for s in snapshot.days[0].stops}
    assert scheduled and scheduled <= set(rule)
    assert trace.model_version is None  # fallback: no model version recorded


async def test_selector_valid_pick_is_used_and_rationales_written() -> None:
    cfg = settings(gemini_api_key="gem-test", routes_estimate_enabled=True)
    chosen = [POOL[2].place_id, POOL[6].place_id]
    answers: list[Any] = [
        {"picks": [{"place_id": str(pid), "rank": i} for i, pid in enumerate(chosen, 1)]},
    ]
    orch_runner = Runner(answers)

    async def rationale_answer(agent: Agent, prompt: str) -> RunOutput:
        stops = json.loads(prompt)["stops"]
        body = {"rationales": [{"place_id": s["place_id"], "text": "Fits you."} for s in stops]}
        return RunOutput(
            content=json.dumps(body), messages=[Message(role="assistant", content="x")]
        )

    async def runner(agent: Agent, prompt: str) -> RunOutput:
        if orch_runner.answers:
            return await orch_runner(agent, prompt)
        return await rationale_answer(agent, prompt)

    orch = PlanningOrchestrator(
        fake_session, cfg, matrix_cache=FakeCache(), agent_runner=runner, clock=lambda: NOW
    )
    snapshot, _, sink, trace = await run_plan(orch, cfg, request_text="beach and market")
    scheduled = [s.place_id for s in snapshot.days[0].stops]
    assert set(chosen) <= set(scheduled)  # the model's picks lead; rule picks top up
    assert trace.model_version == "GEMINI:gemini-3.6-flash"
    assert ("WRITING", "grounded_writer") in [(e["stage"], e["agent"]) for e in sink.events]
    assert all(s.rationale == "Fits you." for s in snapshot.days[0].stops)
    # BR-046: the selector prompt carries ids, names and categories, never coordinates.
    assert orch_runner.prompts and all("108.2" not in p for p in orch_runner.prompts)


async def test_selector_accepts_more_must_sees_than_the_pace_target() -> None:
    # RELAXED, 1 day → target 5 picks; 6 must-sees must not make the model output invalid.
    cfg = settings(gemini_api_key="gem-test", routes_estimate_enabled=True)
    must = tuple(p.place_id for p in POOL[:6])
    answer = {"picks": [{"place_id": str(pid), "rank": i} for i, pid in enumerate(must, 1)]}
    runner = Runner([answer])

    async def run(agent: Agent, prompt: str) -> RunOutput:
        if runner.answers:
            return await runner(agent, prompt)
        return RunOutput(content="{}", messages=[Message(role="assistant", content="x")])

    orch = PlanningOrchestrator(
        fake_session, cfg, matrix_cache=FakeCache(), agent_runner=run, clock=lambda: NOW
    )
    _, _, _, trace = await run_plan(orch, cfg, pref=prefs(pace="RELAXED", must_see=must))
    assert len(runner.models) == 1  # accepted on the first attempt, no repair
    assert trace.model_version == "GEMINI:gemini-3.6-flash"


def test_planning_preferences_round_trip_through_the_snapshot() -> None:
    effective = prefs(pace="PACKED", modes=("WALK",), day_start=time(9, 30))
    stored = planning_preferences_of(effective)
    assert stored.allowed_modes == ["WALK"] and stored.day_start_time == "09:30"
    again = merge_preferences(None, stored.model_dump(mode="json", exclude_none=True), None)
    assert again.modes == ("WALK",) and again.pace == "PACKED"
    assert again.day_start == time(9, 30) and again.day_end == time(20, 0)
