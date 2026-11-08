"""From retrieved evidence to the writer's input, and from its validated output to the stored
answer (ADR-010 1.0).

Evidence ids sent to the model are short positional ids (``E1``..``En``), so no catalog UUID
reaches the provider. After the writer's own validation, every claim is checked again against
the id map built here; a citation that does not resolve to supplied evidence drops the claim, and
an answer left without a valid citation is ``INSUFFICIENT_EVIDENCE``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.agents.schemas import AnswerStatus, EvidenceItem, GroundedAnswer
from app.guide.evidence import Evidence, citation_section
from app.schemas.guide import Citation

MAX_ANSWER_CHARS = 4000  # ck_guide_messages_content_length
MAX_EVIDENCE_TEXT = 2000  # EvidenceItem.text

INSUFFICIENT_TEXT = {
    "vi": (
        "Mình chưa tìm thấy thông tin đã kiểm chứng về câu hỏi này trong dữ liệu Đà Nẵng "
        "của Gonarra."
    ),
    "en": "I couldn't find source-checked information about this in Gonarra's Đà Nẵng catalog.",
}


@dataclass(frozen=True, slots=True)
class ComposedAnswer:
    status: str  # ANSWERED | INSUFFICIENT_EVIDENCE
    content: str
    citations: list[tuple[Evidence, Citation]]
    claims: list[str]


def evidence_items(evidence: Sequence[Evidence]) -> tuple[list[EvidenceItem], dict[str, Evidence]]:
    items: list[EvidenceItem] = []
    by_id: dict[str, Evidence] = {}
    for index, item in enumerate(evidence, start=1):
        evidence_id = f"E{index}"
        by_id[evidence_id] = item
        items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                text=item.text[:MAX_EVIDENCE_TEXT],
                label=item.label[:200] if item.label else None,
            )
        )
    return items, by_id


def to_citation(item: Evidence) -> Citation:
    return Citation(
        source_revision_id=item.source_revision_id,
        trust_level="VERIFIED",
        evidence_kind=item.kind,
        url=None,
        fetched_at=None,
        knowledge_chunk_id=item.knowledge_chunk_id,
        section=citation_section(item.section) if item.kind == "CHUNK" else None,
        place_fact_id=item.place_fact_id,
        publisher=item.publisher,
        title=item.title,
        locator=item.locator,
        verified_at=item.verified_at,
    )


def insufficient(locale: str) -> ComposedAnswer:
    text = INSUFFICIENT_TEXT.get(locale, INSUFFICIENT_TEXT["vi"])
    return ComposedAnswer("INSUFFICIENT_EVIDENCE", text, [], [])


def compose(answer: GroundedAnswer, by_id: dict[str, Evidence], locale: str) -> ComposedAnswer:
    """Keep claims whose every evidence id resolves; cite each source revision once (the
    citation table's key is (message, source_revision))."""
    if answer.status is not AnswerStatus.ANSWERED:
        return insufficient(locale)
    claims: list[str] = []
    cited: dict[str, Evidence] = {}
    length = 0
    for claim in answer.claims:
        if not claim.evidence_ids or any(eid not in by_id for eid in claim.evidence_ids):
            continue
        extra = len(claim.text) + (1 if claims else 0)
        if length + extra > MAX_ANSWER_CHARS:
            break
        claims.append(claim.text)
        length += extra
        for eid in claim.evidence_ids:
            cited.setdefault(eid, by_id[eid])
    if not claims or not cited:
        return insufficient(locale)
    citations: list[tuple[Evidence, Citation]] = []
    seen_revisions: set[str] = set()
    for item in cited.values():
        revision = str(item.source_revision_id)
        if revision in seen_revisions:
            continue
        seen_revisions.add(revision)
        citations.append((item, to_citation(item)))
    return ComposedAnswer("ANSWERED", " ".join(claims), citations, claims)
