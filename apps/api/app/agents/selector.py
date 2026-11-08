"""``selector`` role: rank a pool of published place IDs (architecture §3.1, ADR-013).

Gemini Flash → Flash-Lite → Groq (``app.ai.providers``), no tools. IDs ⊆ candidates, no
duplicates, must-sees present; one repair, then the deterministic fallback so planning always
completes without AI (the orchestrator then uses ``app.planning.rule_selector``).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from typing import Any

from app.agents.runtime import AgentContext, load_instructions, run_chain
from app.agents.schemas import (
    MAX_PICKS,
    Locale,
    ResultSource,
    SelectionOutcome,
    SelectionResult,
)
from app.agents.validators import parse_output, rule_based_selection, validate_selection
from app.ai.providers import Role
from app.ai.redaction import CandidateDto, redact_candidates, redact_text

AGENT_NAME = "selector"
# SPK-004: 30 candidates already pushed a thinking model past 28 s; the orchestrator pre-ranks.
MAX_CANDIDATES = 24


def build_selector_prompt(
    *,
    request_text: str,
    candidates: Sequence[CandidateDto],
    days: int,
    must_see: Sequence[uuid.UUID],
    preferences: Mapping[str, Any] | None,
) -> str:
    """User message: redacted request, structured preferences and redacted candidate DTOs."""
    payload = {
        "request": redact_text(request_text),
        "trip_days": days,
        "must_see": [str(pid) for pid in must_see],
        "preferences": {k: redact_text(str(v)) for k, v in (preferences or {}).items()},
        "candidates": [c.model_dump(mode="json", exclude_none=True) for c in candidates],
    }
    return json.dumps(payload, ensure_ascii=False)


async def select_places(
    ctx: AgentContext,
    *,
    request_text: str,
    candidates: Sequence[CandidateDto],
    days: int,
    locale: Locale,
    must_see: Sequence[uuid.UUID] = (),
    preferences: Mapping[str, Any] | None = None,
    max_picks: int = MAX_PICKS,
) -> SelectionOutcome:
    """Rank ``candidates`` for the request. Never raises for model, quota or validation
    failures: the result then comes from :func:`rule_based_selection` (``RULE_BASED``)."""
    pool = redact_candidates(candidates[:MAX_CANDIDATES])
    ids = [c.place_id for c in pool]
    categories = {c.place_id: c.category_code for c in pool}
    must = [pid for pid in must_see if pid in set(ids)]
    first_attempt = len(ctx.attempts)

    def fallback(issues: list[str]) -> SelectionOutcome:
        result = rule_based_selection(
            ids, categories=categories, must_see=must, max_picks=max_picks
        )
        return SelectionOutcome(
            result, ResultSource.RULE_BASED, tuple(ctx.attempts[first_attempt:]), tuple(issues)
        )

    if not pool:
        return fallback(["empty_pool"])

    instructions, version = load_instructions(AGENT_NAME, locale)
    prompt = build_selector_prompt(
        request_text=request_text,
        candidates=pool,
        days=days,
        must_see=must,
        preferences=preferences,
    )

    def validate(result: SelectionResult) -> tuple[SelectionResult | None, list[str]]:
        check = validate_selection(
            result, candidate_ids=ids, must_see=must, days=days, max_picks=max_picks
        )
        return check.result, list(check.issues)

    def repair(issues: list[str]) -> str:
        # Echo only kinds and *listed* IDs: an invented ID must never be sent back (BR-046).
        allowed = {str(pid) for pid in ids}
        safe = [i if i.split(":", 1)[-1] in allowed else i.split(":", 1)[0] for i in issues]
        note = {
            "previous_answer_rejected": sorted(set(safe))[:10],
            "fix": "Use only listed place_id values, no duplicates, include every must_see.",
        }
        return prompt + "\n" + json.dumps(note, ensure_ascii=False)

    call = await run_chain(
        ctx,
        Role.SELECTOR,
        agent_name=AGENT_NAME,
        instructions=instructions,
        prompt_version=version,
        prompt=prompt,
        allowed_ids=ids,
        output_schema=SelectionResult,
        parse=lambda content: parse_output(content, SelectionResult),
        validate=validate,
        repair_prompt=repair,
        # DEC-026: Flash → Flash-Lite → Groq are all tried before the rule-based selector.
        next_model_on_invalid=True,
        next_model_after_repair=True,
    )
    if call.value is None:
        return fallback(call.issues)
    source = ResultSource.REPAIRED if call.repaired else ResultSource.MODEL
    return SelectionOutcome(
        call.value, source, tuple(ctx.attempts[first_attempt:]), tuple(call.issues)
    )
