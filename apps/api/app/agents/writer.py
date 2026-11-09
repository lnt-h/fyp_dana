"""``grounded_writer`` role, two profiles (architecture §3.1, ADR-010, DEC-031).

* ``RATIONALE`` (Gemini Flash-Lite → Groq): one batched call per preview; any failure gives
  ``None`` rationales, never an error.
* ``GUIDE_ANSWER`` (Gemini Flash → Groq): claims must cite supplied ``evidence_ids``; claims
  citing anything else are dropped and zero claims means ``INSUFFICIENT_EVIDENCE``.

Catalog content is never written by a model (DEC-031): the offline ``enrich descriptions`` and
``enrich facts`` profiles were removed with their commands.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Sequence

from app.agents.runtime import AgentContext, load_instructions, run_chain
from app.agents.schemas import (
    AnswerStatus,
    EvidenceItem,
    GroundedAnswer,
    GuideAnswerOutcome,
    Locale,
    RationaleOutcome,
    RationaleSet,
    RationaleStop,
    RationaleTraveller,
    ResultSource,
)
from app.agents.validators import parse_output, validate_citations, validate_rationales
from app.ai.providers import Role
from app.ai.redaction import redact_text

RATIONALE_AGENT = "writer_rationale"
GUIDE_AGENT = "writer_guide"
MAX_EVIDENCE = 24
MAX_HISTORY_TURNS = 4
RATIONALE_DESCRIPTION_CHARS = 600

_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}")


def _ids_in(evidence_ids: Sequence[str]) -> list[str]:
    """UUIDs embedded in evidence ids (``fact:<uuid>``) are legitimate prompt content."""
    return [m.group(0) for eid in evidence_ids for m in _UUID_RE.finditer(eid)]


def trim_text(value: str | None, limit: int = RATIONALE_DESCRIPTION_CHARS) -> str | None:
    """Whitespace-collapsed text cut to ``limit`` characters at a sentence or word boundary."""
    if not value:
        return None
    text = " ".join(value.split())
    if len(text) <= limit:
        return text or None
    cut = text[:limit]
    sentence = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if sentence >= limit // 2:
        return cut[: sentence + 1]
    space = cut.rfind(" ")
    return (cut[:space] if space > 0 else cut).rstrip(",;:") + "…"


def build_rationale_prompt(
    *,
    request_text: str,
    stops: Sequence[RationaleStop],
    traveller: RationaleTraveller | None = None,
) -> str:
    """Request, structured preferences and per-stop catalog text, redacted (BR-046)."""

    def red(value: str | None) -> str | None:
        return redact_text(value) if value else None

    payload = {
        "request": redact_text(request_text),
        "traveller": (
            {
                "interests": [redact_text(item) for item in traveller.interests],
                "pace": red(traveller.pace),
            }
            if traveller is not None
            else None
        ),
        "stops": [
            {
                "place_id": str(stop.place_id),
                "name": redact_text(stop.name),
                "category": red(stop.category_label) or stop.category_code,
                "area": red(stop.area),
                "time_of_day": stop.time_of_day,
                "summary": red(stop.summary),
                "description": red(stop.description),
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
    traveller: RationaleTraveller | None = None,
) -> RationaleOutcome:
    """One rationale (or ``None``) per stop. Never raises for model or quota failures."""
    first_attempt = len(ctx.attempts)
    stop_ids = [stop.place_id for stop in stops]
    empty: dict[uuid.UUID, str | None] = dict.fromkeys(stop_ids)
    if not stops:
        return RationaleOutcome(empty, ResultSource.DEGRADED)
    instructions, version = load_instructions(RATIONALE_AGENT, locale)
    prompt = build_rationale_prompt(request_text=request_text, stops=stops, traveller=traveller)
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
