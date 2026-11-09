from __future__ import annotations

import json
import uuid
from typing import Any

import pytest
from agent_fakes import (
    FakeLedger,
    InvocationSink,
    ScriptedRunner,
    make_settings,
    output,
)
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.run.base import RunStatus

from app.agents.researcher import run_research
from app.agents.runtime import AgentContext, build_agent, load_instructions
from app.agents.schemas import (
    AnswerStatus,
    EvidenceItem,
    Pick,
    RationaleStop,
    RationaleTraveller,
    ResultSource,
    SelectionResult,
)
from app.agents.selector import select_places
from app.agents.writer import (
    build_rationale_prompt,
    trim_text,
    write_guide_answer,
    write_rationales,
)
from app.ai.invocations import Purpose
from app.ai.providers import GEMINI_FLASH, GEMINI_FLASH_LITE, GROQ_DEFAULT, Role, role_chain
from app.ai.quota import Bucket
from app.ai.redaction import CandidateDto

ACCOUNT = uuid.UUID("11111111-1111-4111-8111-111111111111")
IDS = [uuid.UUID(int=i + 1, version=4) for i in range(6)]
CATS = ["BEACH", "FOOD", "FOOD", "MUSEUM", "CAFE", "BEACH"]
CANDIDATES = [
    CandidateDto(place_id=pid, name_vi=f"Điểm {i}", name_en=f"Place {i}", category_code=cat)
    for i, (pid, cat) in enumerate(zip(IDS, CATS, strict=True))
]


def ctx_for(
    runner: ScriptedRunner, caps: dict[Bucket, int] | None = None, **settings: Any
) -> tuple[AgentContext, FakeLedger, InvocationSink]:
    s = make_settings(**settings)
    ledger = FakeLedger(s, caps)
    sink = InvocationSink()
    ctx = AgentContext(
        settings=s,
        ledger=ledger,  # type: ignore[arg-type]
        session_factory=sink.factory(),
        purpose=Purpose.PLAN_GENERATE,
        account_id=ACCOUNT,
        runner=runner,
    )
    return ctx, ledger, sink


def picks(*ids: uuid.UUID | str) -> dict[str, Any]:
    return {"picks": [{"place_id": str(p), "rank": i} for i, p in enumerate(ids, 1)]}


# --- runtime --------------------------------------------------------------------------------


def test_build_agent_shared_settings_hide_key() -> None:
    settings = make_settings()
    groq = build_agent(
        role_chain(Role.SELECTOR)[2], settings, name="s", instructions="x", output_schema=None
    )
    assert groq.telemetry is False and groq.retries == 0 and groq.db is None
    assert groq.add_history_to_context is False and groq.markdown is False
    assert "groq-test-SECRET" not in repr(groq.model)
    from app.agents.schemas import SelectionResult

    gem = build_agent(
        role_chain(Role.SELECTOR)[0],
        settings,
        name="s",
        instructions="x",
        output_schema=SelectionResult,
    )
    assert gem.use_json_mode is False
    groq2 = build_agent(
        role_chain(Role.SELECTOR)[2],
        settings,
        name="s",
        instructions="x",
        output_schema=SelectionResult,
    )
    assert groq2.use_json_mode is True


def test_instructions_exist_for_every_role_and_locale() -> None:
    for name in ("selector", "researcher", "writer_rationale", "writer_guide"):
        for locale in ("vi", "en"):
            text, version = load_instructions(name, locale)  # type: ignore[arg-type]
            assert text and version.startswith(f"{name}.{locale}@")


# --- selector -------------------------------------------------------------------------------


async def test_selector_happy_path_records_metadata_only() -> None:
    runner = ScriptedRunner([picks(IDS[2], IDS[0])])
    ctx, ledger, sink = ctx_for(runner)
    out = await select_places(
        ctx,
        request_text="beach and seafood, mail me at a@b.com",
        candidates=CANDIDATES,
        days=2,
        locale="en",
    )
    assert out.source is ResultSource.MODEL
    assert [p.place_id for p in out.result.picks] == [str(IDS[2]), str(IDS[0])]
    assert ledger.used[Bucket.GEMINI_FLASH] == 1
    model_id, prompt, _ = runner.calls[0]
    assert model_id.startswith("gemini") and "a@b.com" not in prompt and "[EMAIL]" in prompt
    assert len(sink.rows) == 1
    row = sink.rows[0]
    assert row["outcome"] == "OK" and row["account_id"] == ACCOUNT
    assert not any(isinstance(v, str) and "beach" in v for v in row.values())


async def test_selector_repairs_once_then_succeeds() -> None:
    bad = picks(IDS[0], uuid.uuid4(), IDS[0])
    runner = ScriptedRunner([bad, picks(IDS[0], IDS[3])])
    ctx, _, sink = ctx_for(runner)
    out = await select_places(
        ctx, request_text="x", candidates=CANDIDATES, days=1, locale="vi", must_see=[IDS[3]]
    )
    assert out.source is ResultSource.REPAIRED
    assert "previous_answer_rejected" in runner.calls[1][1]
    assert [r["outcome"] for r in sink.rows] == ["VALIDATION_FAILED", "OK"]


async def test_selector_falls_back_to_rule_based_after_whole_chain() -> None:
    # Flash invalid → Flash repair unparsable → Flash-Lite invalid → Groq invalid → rule-based.
    runner = ScriptedRunner([picks(IDS[0]), "not json at all", picks(IDS[0]), picks(IDS[1])])
    ctx, ledger, sink = ctx_for(runner)
    out = await select_places(
        ctx, request_text="x", candidates=CANDIDATES, days=1, locale="en", must_see=[IDS[4]]
    )
    assert out.source is ResultSource.RULE_BASED
    assert out.result.picks[0].place_id == str(IDS[4])
    # round-robin across categories after the must-see
    assert [p.place_id for p in out.result.picks[1:4]] == [str(IDS[0]), str(IDS[1]), str(IDS[3])]
    assert [c[0] for c in runner.calls] == [
        GEMINI_FLASH,
        GEMINI_FLASH,
        GEMINI_FLASH_LITE,
        GROQ_DEFAULT,
    ]
    assert [a.error_code for a in out.attempts] == [
        "validation_failed",
        "malformed_output",
        "validation_failed",
        "validation_failed",
    ]
    assert [r["error_code"] for r in sink.rows] == [a.error_code for a in out.attempts]
    assert ledger.used[Bucket.GROQ] == 1


TRUNCATED = '{"picks":[{"place_id":"' + str(IDS[0]) + '","rank":1,"day_hint":1},{"place_id":"0000'


async def test_selector_truncated_output_moves_to_next_model_without_repair() -> None:
    # Gemini thinking tokens used the output budget: Agno leaves the cut-off JSON as a string.
    runner = ScriptedRunner([TRUNCATED, picks(IDS[1], IDS[0])])
    ctx, _, sink = ctx_for(runner)
    out = await select_places(ctx, request_text="x", candidates=CANDIDATES, days=1, locale="en")
    assert out.source is ResultSource.MODEL
    assert [c[0] for c in runner.calls] == [GEMINI_FLASH, GEMINI_FLASH_LITE]
    assert "previous_answer_rejected" not in runner.calls[1][1]
    assert [r["outcome"] for r in sink.rows] == ["VALIDATION_FAILED", "OK"]
    assert [r["error_code"] for r in sink.rows] == ["malformed_output", None]
    assert out.issues == ()


async def test_selector_truncated_everywhere_degrades_to_rule_based() -> None:
    runner = ScriptedRunner([TRUNCATED, TRUNCATED, TRUNCATED])
    ctx, _, sink = ctx_for(runner)
    out = await select_places(ctx, request_text="x", candidates=CANDIDATES, days=1, locale="en")
    assert out.source is ResultSource.RULE_BASED and out.result.picks
    assert len(runner.calls) == 3
    assert {r["error_code"] for r in sink.rows} == {"malformed_output"}


def test_selector_specs_leave_room_for_output() -> None:
    # SelectionResult for MAX_PICKS picks is ~1k tokens; Gemini 3 thinking tokens count
    # against max_output_tokens, so Flash runs with low thinking and a larger budget.
    for spec in role_chain(Role.SELECTOR):
        assert spec.max_output_tokens is not None and spec.max_output_tokens >= 4096
        if spec.model_id == GEMINI_FLASH:
            assert spec.thinking_level == "low"
    assert set(SelectionResult.model_fields) == {"picks"}
    assert set(Pick.model_fields) == {"place_id", "rank", "day_hint"}


async def test_selector_provider_error_falls_through_to_groq() -> None:
    runner = ScriptedRunner(
        [output("Error code: 404 model not found", status=RunStatus.error), picks(IDS[1])]
    )
    ctx, ledger, sink = ctx_for(runner, caps={Bucket.GEMINI_FLASH_LITE: 0})
    out = await select_places(ctx, request_text="x", candidates=CANDIDATES, days=1, locale="en")
    assert out.source is ResultSource.MODEL
    assert runner.calls[1][0] == GROQ_DEFAULT
    assert ledger.used[Bucket.GEMINI_FLASH] == 1 and ledger.used[Bucket.GROQ] == 1
    assert sink.rows[0]["outcome"] == "PROVIDER_ERROR"
    assert out.attempts[0].error_code == "model_unavailable"


async def test_selector_quota_exhausted_degrades_without_calls() -> None:
    runner = ScriptedRunner([])
    ctx, _, sink = ctx_for(
        runner, caps={Bucket.GEMINI_FLASH: 0, Bucket.GEMINI_FLASH_LITE: 0, Bucket.GROQ: 0}
    )
    out = await select_places(ctx, request_text="x", candidates=CANDIDATES, days=1, locale="en")
    assert out.source is ResultSource.RULE_BASED and not runner.calls and not sink.rows


async def test_selector_exception_is_provider_error_and_message_not_kept() -> None:
    runner = ScriptedRunner([RuntimeError("secret body"), picks(IDS[0])])
    ctx, _, _ = ctx_for(runner)
    out = await select_places(ctx, request_text="x", candidates=CANDIDATES, days=1, locale="en")
    assert out.attempts[0].outcome == "PROVIDER_ERROR"
    assert out.attempts[0].error_code == "RuntimeError"


# --- writer ---------------------------------------------------------------------------------


async def test_rationales_drop_unknown_and_fact_like_text() -> None:
    stops = [
        RationaleStop(place_id=IDS[0], name="Mỹ Khê", category_code="BEACH"),
        RationaleStop(place_id=IDS[1], name="Chợ Hàn", category_code="MARKET"),
    ]
    content = {
        "rationales": [
            {"place_id": str(IDS[0]), "text": "A calm beach that matches your wish to swim."},
            {"place_id": str(IDS[1]), "text": "Opens at 6:00 and costs 50.000đ."},
            {"place_id": str(uuid.uuid4()), "text": "Invented."},
        ]
    }
    ctx, ledger, _ = ctx_for(ScriptedRunner([content]))
    out = await write_rationales(ctx, request_text="beach", stops=stops, locale="en")
    assert out.rationales[IDS[0]] and out.rationales[IDS[1]] is None
    assert ledger.used[Bucket.GEMINI_FLASH_LITE] == 1
    assert any(i.startswith("fact_like_text") for i in out.issues)


def test_rationale_prompt_carries_description_area_time_and_traveller_redacted() -> None:
    stop = RationaleStop(
        place_id=IDS[0],
        name="Cầu Rồng",
        category_code="VIEWPOINT",
        category_label="Viewpoint",
        area="Hải Châu",
        summary="bridge in Vietnam",
        description="A dragon-shaped bridge that breathes fire and water. Call 0905 123 456.",
        time_of_day="evening",
    )
    prompt = build_rationale_prompt(
        request_text="mail me at a@b.com",
        stops=[stop],
        traveller=RationaleTraveller(interests=["Viewpoint", "Food"], pace="relaxed"),
    )
    payload = json.loads(prompt)
    (item,) = payload["stops"]
    assert item["category"] == "Viewpoint" and item["area"] == "Hải Châu"
    assert item["time_of_day"] == "evening"
    assert "breathes fire" in item["description"]
    assert payload["traveller"] == {"interests": ["Viewpoint", "Food"], "pace": "relaxed"}
    # BR-046: contact data never reaches the provider.
    assert "0905 123 456" not in prompt and "a@b.com" not in prompt


def test_trim_text_cuts_at_sentence_or_word() -> None:
    sentence = "First sentence here. " * 40
    out = trim_text(sentence)
    assert out is not None and len(out) <= 600 and out.endswith(".")
    words = "word " * 200
    out = trim_text(words)
    assert out is not None and len(out) <= 601 and out.endswith("…") and "  " not in out
    assert trim_text("  short   text ") == "short text"
    assert trim_text(None) is None and trim_text("") is None


async def test_rationale_left_out_by_model_is_null() -> None:
    stops = [
        RationaleStop(place_id=IDS[0], name="A", category_code="BEACH", description="Fine sand."),
        RationaleStop(place_id=IDS[1], name="B", category_code="VIEWPOINT"),
    ]
    content = {"rationales": [{"place_id": str(IDS[0]), "text": "Fine sand for a slow morning."}]}
    ctx, _, _ = ctx_for(ScriptedRunner([content]))
    out = await write_rationales(ctx, request_text="", stops=stops, locale="en")
    assert out.source is ResultSource.MODEL
    assert out.rationales == {IDS[0]: "Fine sand for a slow morning.", IDS[1]: None}


async def test_rationales_degrade_to_null_when_chain_exhausted() -> None:
    stops = [RationaleStop(place_id=IDS[0], name="A", category_code="BEACH")]
    ctx, _, _ = ctx_for(ScriptedRunner([]), caps={Bucket.GEMINI_FLASH_LITE: 0, Bucket.GROQ: 0})
    out = await write_rationales(ctx, request_text="x", stops=stops, locale="vi")
    assert out.source is ResultSource.DEGRADED and out.rationales == {IDS[0]: None}


async def test_guide_answer_drops_uncited_claims() -> None:
    evidence = [
        EvidenceItem(evidence_id=f"fact:{IDS[0]}", text="Open 07:00-17:00 daily."),
        EvidenceItem(evidence_id="chunk:2", text="Phone 0905 123 456 for bookings."),
    ]
    content = {
        "status": "ANSWERED",
        "claims": [
            {"text": "It opens at 7am.", "evidence_ids": [f"fact:{IDS[0]}"]},
            {"text": "Made up.", "evidence_ids": ["chunk:99"]},
        ],
    }
    runner = ScriptedRunner([content])
    ctx, _, _ = ctx_for(runner)
    out = await write_guide_answer(ctx, question="When open?", evidence=evidence, locale="en")
    assert out.answer.status is AnswerStatus.ANSWERED and len(out.answer.claims) == 1
    assert out.dropped_claims == 1
    assert "0905 123 456" not in runner.calls[0][1]


async def test_guide_answer_zero_valid_claims_is_insufficient() -> None:
    evidence = [EvidenceItem(evidence_id="e1", text="Something.")]
    content = {"status": "ANSWERED", "claims": [{"text": "x", "evidence_ids": ["e9"]}]}
    ctx, _, _ = ctx_for(ScriptedRunner([content]))
    out = await write_guide_answer(ctx, question="q", evidence=evidence, locale="vi")
    assert out.answer.status is AnswerStatus.INSUFFICIENT_EVIDENCE and not out.answer.claims


async def test_guide_without_evidence_makes_no_call() -> None:
    runner = ScriptedRunner([])
    ctx, _, _ = ctx_for(runner)
    out = await write_guide_answer(ctx, question="q", evidence=[], locale="en")
    assert out.answer.status is AnswerStatus.INSUFFICIENT_EVIDENCE and not runner.calls


# --- researcher -----------------------------------------------------------------------------

PAGE = (
    "Bánh xèo Bà Dưỡng là quán bánh xèo nổi tiếng gần chợ Hàn.\nQuán mở cửa từ 9h đến 21h mỗi ngày."
)
URL = "https://example.vn/banh-xeo"


class FakeTools:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.pages: dict[str, str] = {}

    async def tavily_search(self, query: str) -> str:
        self.calls.append("search")
        return json.dumps({"results": [{"url": URL, "title": "t", "snippet": "s"}]})

    async def fetch_page(self, url: str) -> str:
        self.calls.append("fetch")
        self.pages[url] = PAGE
        return json.dumps({"url": url, "text": PAGE})

    async def places_check(self, name: str) -> str:
        self.calls.append("places")
        return json.dumps({"outcome": "SKIPPED", "place_id": None})

    def page_text(self, url: str) -> str | None:
        return self.pages.get(url)

    def search_urls(self) -> frozenset[str]:
        return frozenset({URL})

    def places_result(self, google_place_id: str) -> str | None:
        return None


async def test_researcher_runs_tools_and_keeps_only_verbatim_quotes() -> None:
    tools = FakeTools()
    report = {
        "candidates": [
            {
                "name": "Bánh xèo Bà Dưỡng",
                "category_guess": "FOOD",
                "source_url": URL,
                "google_place_id": "ChIJfake",
                "name_quote": "Bánh xèo Bà Dưỡng là quán bánh xèo nổi tiếng gần chợ Hàn.",
                "facts": [
                    {
                        "field": "OPENING_HOURS",
                        "value": "9-21",
                        "quote": "Quán mở cửa từ 9h đến 21h mỗi ngày.",
                    },
                    {
                        "field": "ADMISSION_PRICE",
                        "value": "30k",
                        "quote": "Giá 30.000 đồng một phần.",
                    },
                ],
            },
            {
                "name": "Quán Ma",
                "source_url": "https://never-fetched.vn/x",
                "name_quote": "Quán Ma ngon",
            },
        ],
        "evidence": [{"source_url": URL, "quote": "gần chợ Hàn", "note": None}],
    }

    async def loop(agent: Agent, prompt: str) -> RunOutput:
        fns = {getattr(f, "name", None) or f.__name__: f for f in agent.tools or []}  # type: ignore[union-attr]
        await fns["tavily_search"]("bánh xèo chợ Hàn")
        await fns["fetch_page"](URL)
        await fns["places_check"]("Bánh xèo Bà Dưỡng")
        assert agent.tool_call_limit == 7 and agent.output_schema is None
        return output(
            "```json\n" + json.dumps(report, ensure_ascii=False) + "\n```", assistant_msgs=4
        )

    runner = ScriptedRunner([loop])
    ctx, ledger, sink = ctx_for(runner)
    out = await run_research(
        ctx, request_text="quán bánh xèo gần chợ Hàn, call 0905123456", locale="vi", tools=tools
    )
    assert out.source is ResultSource.MODEL
    assert [c.name for c in out.report.candidates] == ["Bánh xèo Bà Dưỡng"]
    cand = out.report.candidates[0]
    assert [f.field for f in cand.facts] == ["OPENING_HOURS"]
    assert cand.google_place_id is None  # not returned by this run's places_check
    assert len(out.report.evidence) == 1
    assert any(d.startswith("fact_quote_not_found") for d in out.dropped)
    assert any(d.startswith("candidate_source_not_fetched") for d in out.dropped)
    assert runner.calls[0][0] == GROQ_DEFAULT
    assert "0905123456" not in runner.calls[0][1]
    assert ledger.used[Bucket.GROQ] == 4  # one reserved call + three tool round-trips
    assert len(sink.rows) == 1


async def test_researcher_unparseable_output_degrades() -> None:
    ctx, _, sink = ctx_for(ScriptedRunner(["I found nothing"]))
    out = await run_research(ctx, request_text="x", locale="en", tools=FakeTools())
    assert out.source is ResultSource.DEGRADED and not out.report.candidates
    assert sink.rows[0]["outcome"] == "VALIDATION_FAILED"


async def test_researcher_never_uses_gemini_and_skips_without_groq() -> None:
    runner = ScriptedRunner([])
    ctx, _, _ = ctx_for(runner, groq_api_key=None)
    out = await run_research(ctx, request_text="x", locale="en", tools=FakeTools())
    assert out.source is ResultSource.DEGRADED and not runner.calls


@pytest.mark.parametrize("bad", ["user_2abcdefghijkl", "lat: 16.05"])
async def test_redaction_gate_never_sends_identifiers(bad: str) -> None:
    runner = ScriptedRunner([picks(IDS[0])])
    ctx, _, _ = ctx_for(runner)
    await select_places(ctx, request_text=f"trip {bad}", candidates=CANDIDATES, days=1, locale="en")
    assert bad not in runner.calls[0][1]


async def test_tool_use_failed_retries_same_model_once() -> None:
    bad = output('{"error": {"code": "tool_use_failed"}}', status=RunStatus.error)
    runner = ScriptedRunner([bad, '{"candidates": [], "evidence": []}'])
    ctx, _, sink = ctx_for(runner)
    out = await run_research(ctx, request_text="x", locale="en", tools=FakeTools())
    assert out.source is ResultSource.MODEL and len(runner.calls) == 2
    assert [r["outcome"] for r in sink.rows] == ["PROVIDER_ERROR", "OK"]


async def test_researcher_accepts_report_submitted_through_tool() -> None:
    tools = FakeTools()

    async def loop(agent: Agent, prompt: str) -> RunOutput:
        fns = {getattr(f, "name", None) or f.__name__: f for f in agent.tools or []}  # type: ignore[union-attr]
        await fns["fetch_page"](URL)
        submit = fns["submit_report"]
        assert submit.stop_after_tool_call is True
        content = await submit.entrypoint(
            candidates=[
                {
                    "name": "Bánh xèo Bà Dưỡng",
                    "source_url": URL,
                    "name_quote": "Bánh xèo Bà Dưỡng là quán bánh xèo",
                }
            ],
            evidence=[],
        )
        return output(content)

    ctx, _, _ = ctx_for(ScriptedRunner([loop]))
    out = await run_research(ctx, request_text="bánh xèo", locale="vi", tools=tools)
    assert [c.name for c in out.report.candidates] == ["Bánh xèo Bà Dưỡng"]
