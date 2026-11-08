"""Guide retrieval and answer composition: pure helpers and the hybrid retriever (fake source)."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import date
from typing import Any

import pytest

from app.agents.schemas import AnswerStatus, Claim, GroundedAnswer
from app.guide.answer import MAX_ANSWER_CHARS, compose, evidence_items
from app.guide.evidence import Evidence, PlaceName, citation_section, fact_text
from app.guide.retrieval import (
    HybridRetriever,
    QueryVector,
    fact_intents,
    lexical_patterns,
    match_entities,
    place_scope_evidence,
    reciprocal_rank_fusion,
)

CITY = uuid.uuid4()
ACCOUNT = uuid.uuid4()


def place(vi: str, en: str, *aliases: str) -> PlaceName:
    return PlaceName(uuid.uuid4(), (vi, en, *aliases), vi, en)


def ev(
    kind: str = "CHUNK",
    *,
    place_id: uuid.UUID | None = None,
    locale: str | None = "en",
    field_code: str | None = None,
    revision: uuid.UUID | None = None,
) -> Evidence:
    item_id = uuid.uuid4()
    return Evidence(
        key=f"{kind.lower()}:{item_id}",
        kind=kind,  # type: ignore[arg-type]
        place_id=place_id,
        text="text",
        source_revision_id=revision or uuid.uuid4(),
        publisher="p",
        title=None,
        locator=None,
        verified_at=date(2026, 11, 1),
        knowledge_chunk_id=item_id if kind == "CHUNK" else None,
        place_fact_id=item_id if kind == "FACT" else None,
        section="OVERVIEW" if kind == "CHUNK" else None,
        locale=locale if kind == "CHUNK" else None,
        field_code=field_code,
    )


# ---- pure helpers -------------------------------------------------------------------------------


def test_entities_match_folded_names_and_prefer_longer() -> None:
    linh_ung = place("Chùa Linh Ứng", "Linh Ung Pagoda")
    bai_but = place("Chùa Linh Ứng Bãi Bụt", "Linh Ung Pagoda Bai But")
    my_khe = place("Bãi biển Mỹ Khê", "My Khe Beach", "Mỹ Khê")
    short = place("Ba", "Ba")
    places = [linh_ung, bai_but, my_khe, short]
    assert match_entities("chua linh ung bai but mo cua may gio?", places)[0] == bai_but.place_id
    assert match_entities("Is MY KHE nice at sunset?", places) == [my_khe.place_id]
    assert match_entities("ba ngày ở đây", places) == []  # names under 4 chars are ignored
    assert match_entities("Linh Ungx", places) == []  # whole words only


def test_lexical_patterns_keep_phrases_drop_stopwords_and_escape() -> None:
    patterns = lexical_patterns("Giờ mở cửa của bảo tàng 100% là gì?")
    assert "%mở cửa%" in patterns and "%bảo tàng%" in patterns
    assert "%của%" not in patterns and "%là%" not in patterns
    assert all(p.startswith("%") and p.endswith("%") for p in patterns)
    assert lexical_patterns("a_b%c") == ["%a\\_b c%", "%a\\_b%"]  # LIKE wildcards escaped
    assert lexical_patterns("the is a") == []
    assert len(lexical_patterns(" ".join(f"word{i}" for i in range(40)))) == 12


def test_fact_intents() -> None:
    assert fact_intents("What time does it open?") >= {"OPENING_HOURS"}
    assert "ADMISSION_PRICE" in fact_intents("giá vé bao nhiêu")
    assert fact_intents("tell me the history") == set()


def test_reciprocal_rank_fusion_rewards_agreement() -> None:
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["c", "a"], ["c"]])
    assert fused[0] == "c" and fused[1] == "a" and fused[-1] == "b"
    assert reciprocal_rank_fusion([]) == []


def test_place_scope_falls_back_to_other_locale_chunks() -> None:
    vi_chunk, fact = ev(locale="vi"), ev("FACT")
    assert place_scope_evidence([vi_chunk, fact], "en") == [vi_chunk, fact]
    en_chunk = ev(locale="en")
    assert place_scope_evidence([vi_chunk, en_chunk, fact], "en") == [en_chunk, fact]


def test_fact_text_quotes_value_and_marks_stale() -> None:
    assert fact_text("ADMISSION_PRICE", {"text": "40.000 VND"}, is_stale=False) == (
        "Admission price: 40.000 VND"
    )
    stale = fact_text("OPENING_HOURS", {"mon": ["07:00-17:00"]}, is_stale=True)
    assert stale.startswith('Opening hours: {"mon":["07:00-17:00"]}') and "outdated" in stale
    assert citation_section("CITY_OVERVIEW") is None and citation_section("HISTORY") == "HISTORY"


# ---- composition --------------------------------------------------------------------------------


def test_compose_validates_ids_dedupes_revisions_and_caps_length() -> None:
    shared = uuid.uuid4()
    items = [ev(revision=shared), ev("FACT", revision=shared), ev()]
    _, by_id = evidence_items(items)
    assert list(by_id) == ["E1", "E2", "E3"]
    answer = GroundedAnswer(
        status=AnswerStatus.ANSWERED,
        claims=[
            Claim(text="one", evidence_ids=["E1", "E2"]),
            Claim(text="bad", evidence_ids=["E1", "E4"]),
            Claim(text="three", evidence_ids=["E3"]),
        ],
    )
    composed = compose(answer, by_id, "en")
    assert composed.status == "ANSWERED" and composed.content == "one three"
    revisions = [citation.source_revision_id for _, citation in composed.citations]
    assert revisions == [shared, items[2].source_revision_id]

    long_claims = [Claim(text="x" * 600, evidence_ids=["E3"]) for _ in range(8)]
    capped = compose(GroundedAnswer(status=AnswerStatus.ANSWERED, claims=long_claims), by_id, "vi")
    assert len(capped.content) <= MAX_ANSWER_CHARS and len(capped.claims) == 6

    none_valid = GroundedAnswer(
        status=AnswerStatus.ANSWERED, claims=[Claim(text="x", evidence_ids=["E9"])]
    )
    refused = compose(none_valid, by_id, "vi")
    assert refused.status == "INSUFFICIENT_EVIDENCE" and not refused.citations
    assert refused.content


# ---- hybrid retriever ---------------------------------------------------------------------------


class Source:
    def __init__(
        self,
        names: list[PlaceName],
        evidence: dict[uuid.UUID, list[Evidence]],
        lexical: list[Evidence],
        vector: list[Evidence],
        models: set[str],
    ) -> None:
        self.names, self.evidence, self.lexical, self.vector, self.models = (
            names,
            evidence,
            lexical,
            vector,
            models,
        )
        self.calls: list[str] = []
        self.patterns: Sequence[str] = ()

    async def place_names(self, city_id: uuid.UUID) -> list[PlaceName]:
        return self.names

    async def place_evidence(self, place_ids: Sequence[uuid.UUID], locales: Any) -> list[Evidence]:
        self.calls.append("place")
        return [e for pid in place_ids for e in self.evidence.get(pid, [])]

    async def lexical_chunks(
        self, city_id: uuid.UUID, patterns: Sequence[str], locales: Any, limit: int
    ) -> list[Evidence]:
        self.calls.append("lexical")
        self.patterns = patterns
        return self.lexical

    async def embedding_models(self, city_id: uuid.UUID) -> set[str]:
        return self.models

    async def vector_chunks(self, *args: Any) -> list[Evidence]:
        self.calls.append("vector")
        return self.vector


class Embedder:
    def __init__(self, model: str = "gemini-embedding-001") -> None:
        self.model = model
        self.calls = 0

    async def embed(self, question: str, *, account_id: uuid.UUID) -> QueryVector | None:
        self.calls += 1
        return QueryVector([1.0] + [0.0] * 767, self.model)


async def test_city_retrieval_fuses_entity_lexical_and_vector() -> None:
    cau_rong = place("Cầu Rồng", "Dragon Bridge")
    hours = ev("FACT", place_id=cau_rong.place_id, field_code="OPENING_HOURS")
    overview = ev(place_id=cau_rong.place_id)
    both = ev()
    vector_only = ev()
    source = Source(
        [cau_rong],
        {cau_rong.place_id: [overview, hours]},
        lexical=[both],
        vector=[both, vector_only],
        models={"gemini-embedding-001"},
    )
    embedder = Embedder()
    result = await HybridRetriever(embedder).for_city(
        source,
        city_id=CITY,
        question="When does Dragon Bridge open for fire show?",
        locale="en",
        account_id=ACCOUNT,
    )
    keys = [item.key for item in result.evidence]
    assert keys[0] == both.key  # found by two channels
    assert keys.index(hours.key) < keys.index(overview.key)  # the asked-about fact first
    assert set(keys) == {hours.key, overview.key, both.key, vector_only.key}
    assert result.channels == {"entity": 2, "lexical": 1, "vector": 2}
    assert embedder.calls == 1


async def test_city_retrieval_without_embeddings_skips_vector_and_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    source = Source([], {}, lexical=[ev()], vector=[ev()], models=set())
    embedder = Embedder()
    with caplog.at_level(logging.INFO, logger="gonarra.guide"):
        result = await HybridRetriever(embedder).for_city(
            source, city_id=CITY, question="secret beach question", locale="vi", account_id=ACCOUNT
        )
    assert "vector" not in source.calls and embedder.calls == 0
    assert len(result.evidence) == 1
    assert "vector=skipped reason=no_embeddings" in caplog.text
    assert "secret beach" not in caplog.text  # the question is never logged


async def test_vector_model_mismatch_is_skipped() -> None:
    source = Source([], {}, lexical=[], vector=[ev()], models={"other-model"})
    result = await HybridRetriever(Embedder()).for_city(
        source, city_id=CITY, question="anything", locale="en", account_id=ACCOUNT
    )
    assert result.evidence == [] and "vector" not in source.calls


async def test_place_retrieval_reads_only_the_pinned_place() -> None:
    target = place("Bảo tàng Chăm", "Museum of Cham Sculpture")
    chunk, other = ev(place_id=target.place_id, locale="vi"), ev()
    source = Source([], {target.place_id: [chunk]}, lexical=[other], vector=[], models=set())
    result = await HybridRetriever(Embedder()).for_place(source, target.place_id, "en")
    assert result.evidence == [chunk] and source.calls == ["place"]
