"""grounded_writer DESCRIPTION profile: validator rules and the role chain (D3, 2026-11-08)."""

from __future__ import annotations

from typing import Any

import pytest
from agent_fakes import FakeLedger, InvocationSink, ScriptedRunner, make_settings

from app.agents.runtime import AgentContext
from app.agents.schemas import DescriptionSource, PlaceDescriptionDraft, ResultSource
from app.agents.validators import fact_kinds, validate_description
from app.agents.writer import write_place_description
from app.ai.invocations import Purpose
from app.ai.providers import GROQ_DEFAULT, Provider, Role, role_chain

WIKI = "https://vi.wikipedia.org/wiki/Chùa_Cầu"
SITE = "https://example.vn/chua-cau"
SOURCE_TEXT = (
    "Chùa Cầu là cây cầu cổ có mái che ở Hội An, do thương nhân Nhật Bản xây dựng vào thế kỷ 17. "
    "Năm 1719 cầu được chúa Nguyễn Phúc Chu đặt tên Lai Viễn Kiều. "
    "The bridge is a symbol of Hoi An and appears on the 20,000 dong banknote."
)
VI = (
    "Chùa Cầu là cây cầu cổ có mái che bắc qua một con lạch nhỏ ở Hội An. "
    "Cầu do thương nhân Nhật Bản dựng vào thế kỷ 17 và được đặt tên Lai Viễn Kiều năm 1719."
)
EN = (
    "The Japanese Covered Bridge is a roofed 17th-century bridge in Hoi An, built by Japanese "
    "merchants. It was named Lai Vien Kieu in 1719 and remains the town's best-known symbol."
)


def draft(**overrides: Any) -> PlaceDescriptionDraft:
    base: dict[str, Any] = {
        "insufficient_evidence": False,
        "description_vi": VI,
        "description_en": EN,
        "cited_urls": [WIKI],
    }
    base.update(overrides)
    return PlaceDescriptionDraft.model_validate(base)


def check(value: PlaceDescriptionDraft) -> Any:
    return validate_description(value, supplied_urls=[WIKI, SITE], source_text=SOURCE_TEXT)


def test_valid_draft_is_normalised() -> None:
    result = check(draft(cited_urls=[WIKI + "/", WIKI]))
    assert result.ok and result.issues == ()
    assert result.description is not None
    assert result.description.cited_urls == (WIKI,)


def test_unsupplied_url_rejects_the_draft() -> None:
    result = check(draft(cited_urls=[WIKI, "https://other.example/made-up"]))
    assert not result.ok and "cited_url_not_supplied" in result.issues


def test_no_citation_rejects_the_draft() -> None:
    result = check(draft(cited_urls=[]))
    assert not result.ok and "no_supplied_citation" in result.issues


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("Vé vào cửa là 120.000 đồng cho người lớn. Cầu rất đẹp vào buổi tối.", "price"),
        ("Tickets cost 120,000 VND. The bridge is lovely at night.", "price"),
        ("The bridge is open daily from 7:00 to 21:30. It is lovely at night.", "hours"),
        ("Cầu mở cửa từ 7h30 mỗi ngày. Cầu rất đẹp vào buổi tối.", "hours"),
        ("Call 0905 123 456 to book a guide. The bridge is lovely at night.", "phone"),
        ("It is rated 4.5/5 by visitors. The bridge is lovely at night.", "rating"),
        ("Xem thêm tại https://example.vn. Cầu rất đẹp vào buổi tối.", "contact"),
    ],
)
def test_facts_in_text_reject_the_draft(text: str, kind: str) -> None:
    assert kind in fact_kinds(text)
    english = text.startswith(("Tickets", "The", "Call", "It"))
    result = check(draft(description_en=text) if english else draft(description_vi=text))
    assert not result.ok
    assert any(issue.startswith("fact_in_text") and issue.endswith(kind) for issue in result.issues)


def test_years_and_history_are_not_facts() -> None:
    assert fact_kinds(EN) == [] and fact_kinds(VI) == []


def test_number_missing_from_sources_rejects_the_draft() -> None:
    text = "The bridge was built in 1593 by Japanese merchants. It is the symbol of Hoi An."
    result = check(draft(description_en=text))
    assert not result.ok and "unsupported_number:en:1593" in result.issues


def test_sentence_count_and_missing_locale() -> None:
    result = check(
        draft(description_vi="Chùa Cầu là cây cầu cổ có mái che rất nổi tiếng ở Hội An.")
    )
    assert "sentence_count:vi:1" in result.issues
    result = check(draft(description_en=None))
    assert "missing_description:en" in result.issues


def test_insufficient_evidence_is_valid_and_stores_nothing() -> None:
    result = check(draft(insufficient_evidence=True, description_vi=None, description_en=None))
    assert result.ok and result.insufficient_evidence and result.description is None


# --- writer chain ---------------------------------------------------------------------------


def ctx_for(runner: ScriptedRunner) -> AgentContext:
    settings = make_settings()
    return AgentContext(
        settings=settings,
        ledger=FakeLedger(settings),  # type: ignore[arg-type]
        session_factory=InvocationSink().factory(),
        purpose=Purpose.CONTENT_SUMMARY,
        runner=runner,
    )


SOURCES = [
    DescriptionSource(url=WIKI, title="Chùa Cầu", text=SOURCE_TEXT, kind="WIKIPEDIA"),
    DescriptionSource(
        url=SITE, title="Site", text="Liên hệ 0905 123 456 hoặc a@b.vn.", kind="OFFICIAL_SITE"
    ),
]


def test_description_chain_is_flash_lite_then_groq() -> None:
    chain = role_chain(Role.WRITER_DESCRIPTION)
    assert [(s.provider, s.model_id) for s in chain] == [
        (Provider.GEMINI, "gemini-3.5-flash-lite"),
        (Provider.GROQ, GROQ_DEFAULT),
    ]


async def test_writer_returns_validated_description_and_redacts_sources() -> None:
    runner = ScriptedRunner([draft().model_dump()])
    out = await write_place_description(
        ctx_for(runner),
        name_vi="Chùa Cầu",
        name_en=None,
        category="HERITAGE",
        area="hoi-an-old-town",
        sources=SOURCES,
    )
    assert out.source is ResultSource.MODEL and out.description is not None
    prompt = runner.calls[0][1]
    assert "0905 123 456" not in prompt and "a@b.vn" not in prompt
    assert WIKI in prompt


async def test_writer_repairs_once_then_gives_up() -> None:
    bad = draft(cited_urls=["https://invented.example/x"]).model_dump()
    runner = ScriptedRunner([bad, bad])
    out = await write_place_description(
        ctx_for(runner),
        name_vi="Chùa Cầu",
        name_en=None,
        category="HERITAGE",
        area=None,
        sources=SOURCES,
    )
    assert out.description is None and out.source is ResultSource.DEGRADED
    assert len(runner.calls) == 2
    assert "previous_answer_rejected" in runner.calls[1][1]


async def test_writer_insufficient_evidence() -> None:
    content = {"insufficient_evidence": True, "description_vi": None, "description_en": None}
    out = await write_place_description(
        ctx_for(ScriptedRunner([content])),
        name_vi="Quán X",
        name_en=None,
        category="FOOD",
        area=None,
        sources=SOURCES,
    )
    assert out.description is None and out.insufficient_evidence


async def test_writer_without_sources_makes_no_call() -> None:
    runner = ScriptedRunner([])
    out = await write_place_description(
        ctx_for(runner), name_vi="X", name_en=None, category=None, area=None, sources=[]
    )
    assert out.description is None and not runner.calls
