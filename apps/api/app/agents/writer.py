"""``grounded_writer`` role, two profiles (architecture §3.1, ADR-010).

* ``RATIONALE`` (Gemini Flash-Lite → Groq): one batched call per preview; any failure gives
  ``None`` rationales, never an error.
* ``GUIDE_ANSWER`` (Gemini Flash → Groq): claims must cite supplied ``evidence_ids``; claims
  citing anything else are dropped and zero claims means ``INSUFFICIENT_EVIDENCE``.
* ``DESCRIPTION`` (Gemini Flash-Lite → Groq; offline ``enrich descriptions``, D3): a VI and an
  EN description written only from supplied source texts, citing supplied URLs only, with no
  prices, hours, phone numbers or ratings (:func:`validate_description`). One repair call, then
  the next model; ``insufficient_evidence`` stores nothing.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Sequence

from app.agents.runtime import AgentContext, load_instructions, run_chain
from app.agents.schemas import (
    MAX_DESCRIPTION_SOURCES,
    AnswerStatus,
    DescriptionOutcome,
    DescriptionSource,
    EvidenceItem,
    GroundedAnswer,
    GuideAnswerOutcome,
    Locale,
    PlaceDescription,
    PlaceDescriptionDraft,
    RationaleOutcome,
    RationaleSet,
    RationaleStop,
    ResultSource,
)
from app.agents.validators import (
    DescriptionCheck,
    parse_output,
    validate_citations,
    validate_description,
    validate_rationales,
)
from app.ai.providers import Role
from app.ai.redaction import URL as REDACTED_URL
from app.ai.redaction import redact_text

RATIONALE_AGENT = "writer_rationale"
GUIDE_AGENT = "writer_guide"
DESCRIPTION_AGENT = "writer_description"
MAX_SOURCE_CHARS = 3000
MAX_EVIDENCE = 24
MAX_HISTORY_TURNS = 4

_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}")


def _ids_in(evidence_ids: Sequence[str]) -> list[str]:
    """UUIDs embedded in evidence ids (``fact:<uuid>``) are legitimate prompt content."""
    return [m.group(0) for eid in evidence_ids for m in _UUID_RE.finditer(eid)]


def build_rationale_prompt(*, request_text: str, stops: Sequence[RationaleStop]) -> str:
    payload = {
        "request": redact_text(request_text),
        "stops": [
            {
                "place_id": str(stop.place_id),
                "name": redact_text(stop.name),
                "category": stop.category_code,
                "summary": redact_text(stop.summary) if stop.summary else None,
                "tags": [redact_text(tag) for tag in stop.tags],
            }
            for stop in stops
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


async def write_rationales(
    ctx: AgentContext,
    *,
    request_text: str,
    stops: Sequence[RationaleStop],
    locale: Locale,
) -> RationaleOutcome:
    """One rationale (or ``None``) per stop. Never raises for model or quota failures."""
    first_attempt = len(ctx.attempts)
    stop_ids = [stop.place_id for stop in stops]
    empty: dict[uuid.UUID, str | None] = dict.fromkeys(stop_ids)
    if not stops:
        return RationaleOutcome(empty, ResultSource.DEGRADED)
    instructions, version = load_instructions(RATIONALE_AGENT, locale)
    prompt = build_rationale_prompt(request_text=request_text, stops=stops)
    issues_seen: list[str] = []

    def validate(
        result: RationaleSet,
    ) -> tuple[dict[uuid.UUID, str | None] | None, list[str]]:
        mapping, issues = validate_rationales(result, stop_ids=stop_ids)
        issues_seen.extend(issues)
        return mapping, issues

    call = await run_chain(
        ctx,
        Role.WRITER_RATIONALE,
        agent_name=RATIONALE_AGENT,
        instructions=instructions,
        prompt_version=version,
        prompt=prompt,
        allowed_ids=stop_ids,
        output_schema=RationaleSet,
        parse=lambda content: parse_output(content, RationaleSet),
        validate=validate,
        next_model_on_invalid=True,
    )
    attempts = tuple(ctx.attempts[first_attempt:])
    if call.value is None:
        return RationaleOutcome(empty, ResultSource.DEGRADED, attempts, tuple(call.issues))
    return RationaleOutcome(call.value, ResultSource.MODEL, attempts, tuple(issues_seen))


def build_guide_prompt(
    *,
    question: str,
    evidence: Sequence[EvidenceItem],
    history: Sequence[tuple[str, str]],
) -> str:
    payload = {
        "question": redact_text(question),
        "recent_turns": [
            {"role": role, "text": redact_text(text)} for role, text in history[-MAX_HISTORY_TURNS:]
        ],
        "evidence": [
            {
                "evidence_id": item.evidence_id,
                "label": redact_text(item.label) if item.label else None,
                "text": redact_text(item.text),
            }
            for item in evidence
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


async def write_guide_answer(
    ctx: AgentContext,
    *,
    question: str,
    evidence: Sequence[EvidenceItem],
    locale: Locale,
    history: Sequence[tuple[str, str]] = (),
) -> GuideAnswerOutcome:
    """Grounded answer from ``evidence`` only. ``INSUFFICIENT_EVIDENCE`` when there is no
    evidence, the chain is exhausted or no claim survives citation validation."""
    first_attempt = len(ctx.attempts)
    insufficient = GroundedAnswer(status=AnswerStatus.INSUFFICIENT_EVIDENCE, claims=[])
    items = list(evidence[:MAX_EVIDENCE])
    if not items:
        return GuideAnswerOutcome(insufficient, ResultSource.DEGRADED, issues=("no_evidence",))
    evidence_ids = [item.evidence_id for item in items]
    instructions, version = load_instructions(GUIDE_AGENT, locale)
    prompt = build_guide_prompt(question=question, evidence=items, history=history)
    dropped_total = 0

    def validate(answer: GroundedAnswer) -> tuple[GroundedAnswer | None, list[str]]:
        nonlocal dropped_total
        cleaned, dropped = validate_citations(answer, evidence_ids=evidence_ids)
        dropped_total += dropped
        return cleaned, ([f"dropped_claims:{dropped}"] if dropped else [])

    call = await run_chain(
        ctx,
        Role.WRITER_GUIDE,
        agent_name=GUIDE_AGENT,
        instructions=instructions,
        prompt_version=version,
        prompt=prompt,
        allowed_ids=_ids_in(evidence_ids),
        output_schema=GroundedAnswer,
        parse=lambda content: parse_output(content, GroundedAnswer),
        validate=validate,
        next_model_on_invalid=True,
    )
    attempts = tuple(ctx.attempts[first_attempt:])
    if call.value is None:
        return GuideAnswerOutcome(
            insufficient, ResultSource.DEGRADED, attempts, dropped_total, tuple(call.issues)
        )
    return GuideAnswerOutcome(
        call.value, ResultSource.MODEL, attempts, dropped_total, tuple(call.issues)
    )


def build_description_prompt(
    *,
    name_vi: str,
    name_en: str | None,
    category: str | None,
    area: str | None,
    sources: Sequence[DescriptionSource],
) -> tuple[str, list[str], str]:
    """``(prompt, supplied_urls, source_text)``; every text is redacted (BR-046) and capped.

    A source whose URL would be redacted (credential parameters) is not supplied.
    """
    supplied: list[str] = []
    items: list[dict[str, str | None]] = []
    texts: list[str] = []
    for source in sources[:MAX_DESCRIPTION_SOURCES]:
        url = redact_text(source.url)
        if REDACTED_URL in url or url in supplied:
            continue
        text = redact_text(source.text)[:MAX_SOURCE_CHARS]
        if not text.strip():
            continue
        supplied.append(url)
        texts.append(text)
        items.append(
            {
                "url": url,
                "kind": source.kind,
                "title": redact_text(source.title)[:200] if source.title else None,
                "text": text,
            }
        )
    payload = {
        "place": {
            "name_vi": redact_text(name_vi),
            "name_en": redact_text(name_en) if name_en else None,
            "category": category,
            "area": area,
        },
        "sources": items,
    }
    return json.dumps(payload, ensure_ascii=False), supplied, "\n".join(texts)


async def write_place_description(
    ctx: AgentContext,
    *,
    name_vi: str,
    name_en: str | None,
    category: str | None,
    area: str | None,
    sources: Sequence[DescriptionSource],
) -> DescriptionOutcome:
    """Validated bilingual description, or ``None`` (insufficient evidence / degraded).

    Never raises for model, validation or quota failures.
    """
    first_attempt = len(ctx.attempts)
    prompt, supplied, source_text = build_description_prompt(
        name_vi=name_vi, name_en=name_en, category=category, area=area, sources=sources
    )
    if not supplied:
        return DescriptionOutcome(
            None, ResultSource.DEGRADED, insufficient_evidence=True, issues=("no_sources",)
        )
    instructions, version = load_instructions(DESCRIPTION_AGENT, "en")
    insufficient = False

    def validate(draft: PlaceDescriptionDraft) -> tuple[PlaceDescription | None, list[str]]:
        nonlocal insufficient
        check: DescriptionCheck = validate_description(
            draft, supplied_urls=supplied, source_text=source_text
        )
        if check.insufficient_evidence:
            insufficient = True
            # A sentinel value stops the chain; the caller stores nothing.
            return PlaceDescription("", "", ()), []
        return check.description, list(check.issues)

    def repair(issues: list[str]) -> str:
        return json.dumps(
            {
                "previous_answer_rejected": issues[:10],
                "request": json.loads(prompt),
            },
            ensure_ascii=False,
        )

    call = await run_chain(
        ctx,
        Role.WRITER_DESCRIPTION,
        agent_name=DESCRIPTION_AGENT,
        instructions=instructions,
        prompt_version=version,
        prompt=prompt,
        output_schema=PlaceDescriptionDraft,
        parse=lambda content: parse_output(content, PlaceDescriptionDraft),
        validate=validate,
        repair_prompt=repair,
        next_model_on_invalid=True,
    )
    attempts = tuple(ctx.attempts[first_attempt:])
    if call.value is None:
        return DescriptionOutcome(
            None, ResultSource.DEGRADED, False, attempts, tuple(call.issues), call.exhausted
        )
    if insufficient:
        return DescriptionOutcome(None, ResultSource.MODEL, True, attempts, tuple(call.issues))
    source = ResultSource.REPAIRED if call.repaired else ResultSource.MODEL
    return DescriptionOutcome(call.value, source, False, attempts, tuple(call.issues))
