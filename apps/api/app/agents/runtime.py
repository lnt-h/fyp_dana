"""Shared agent runtime: build an Agno ``Agent`` for one ``ModelSpec`` and walk a role chain.

This is the only place an Agno ``Agent`` is constructed (architecture §2). Every call:

1. picks the next configured model with budget (:func:`app.ai.quota.select_model`);
2. fails closed on BR-046 (:func:`app.ai.redaction.ensure_clean`) before anything is sent;
3. commits the reservation once the call was attempted, plus extra units for tool round-trips;
4. records metadata only (:func:`app.ai.invocations.record_invocation`), never prompt text;
5. re-validates the output with the role's Pydantic schema and domain validator; at most one
   repair call, then the caller's fallback.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from collections.abc import Awaitable, Callable, Collection, Sequence
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.run.base import RunStatus

from app.agents.schemas import Attempt
from app.ai.invocations import Outcome, Purpose, provider_model, record_invocation, timed
from app.ai.providers import ModelSpec, ProviderNotConfigured, Role, make_model, role_chain
from app.ai.quota import (
    QuotaBudget,
    QuotaLedger,
    SessionFactory,
    bucket_for_spec,
    select_model,
)
from app.ai.redaction import ensure_clean

if TYPE_CHECKING:
    from pydantic import BaseModel

    from app.config import Settings

logger = logging.getLogger("gonarra.agents")

PROMPTS_DIR = Path(__file__).parent / "prompts"
PromptLocale = Literal["vi", "en"]

AgentRunner = Callable[[Agent, str], Awaitable[RunOutput]]


async def default_runner(agent: Agent, prompt: str) -> RunOutput:
    output = await agent.arun(prompt, stream=False)
    if not isinstance(output, RunOutput):  # pragma: no cover - stream=False returns RunOutput
        raise TypeError("unexpected streaming response")
    return output


@cache
def load_instructions(name: str, locale: PromptLocale) -> tuple[str, str]:
    """Instruction text of ``prompts/<locale>/<name>.md`` and its version ``name.locale@sha8``."""
    text = (PROMPTS_DIR / locale / f"{name}.md").read_text(encoding="utf-8").strip()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return text, f"{name}.{locale}@{digest}"


@dataclass(slots=True)
class AgentContext:
    """Per-operation dependencies, owned by the orchestrator.

    ``account_id`` is required for traveler purposes (``ck_ai_invocations_traveler_purpose``);
    it is used for metadata rows only and never placed in a prompt.
    """

    settings: Settings
    ledger: QuotaLedger
    session_factory: SessionFactory
    purpose: Purpose
    account_id: uuid.UUID | None = None
    budget: QuotaBudget | None = None
    agent_run_id: uuid.UUID | None = None
    runner: AgentRunner = default_runner
    attempts: list[Attempt] = field(default_factory=list)


def build_agent(
    spec: ModelSpec,
    settings: Settings,
    *,
    name: str,
    instructions: str,
    output_schema: type[BaseModel] | None = None,
    tools: Sequence[Callable[..., Any]] | None = None,
    tool_call_limit: int | None = None,
) -> Agent:
    """Agno ``Agent`` with the shared settings of architecture §3.1.

    ``retries=0``: the role chain is the retry policy, so every provider request is reserved in
    the quota ledger first (Agno's own retry would bypass the ledger). Telemetry is off so no
    run metadata leaves the server.
    """
    return Agent(
        model=make_model(spec, settings),
        name=name,
        instructions=instructions,
        output_schema=output_schema,
        use_json_mode=spec.json_mode and output_schema is not None,
        tools=list(tools) if tools else None,
        tool_call_limit=tool_call_limit if tools else None,
        retries=0,
        markdown=False,
        add_history_to_context=False,
        add_datetime_to_context=False,
        add_location_to_context=False,
        db=None,
        telemetry=False,
        store_media=False,
        store_tool_messages=False,
        store_history_messages=False,
    )


def _error_code(content: Any) -> str:
    text = str(content or "").lower()
    if "429" in text or "rate limit" in text or "rate_limit" in text or "quota" in text:
        return "rate_limited"
    if "tool_use_failed" in text or "tool call validation failed" in text:
        return "tool_use_failed"
    if "404" in text or "model_not_found" in text or "no longer available" in text:
        return "model_unavailable"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "401" in text or "403" in text or "api key" in text or "permission" in text:
        return "auth"
    if "400" in text or "invalid" in text:
        return "bad_request"
    return "provider_error"


def _model_requests(output: RunOutput) -> int:
    messages = output.messages or []
    return max(1, sum(1 for message in messages if getattr(message, "role", None) == "assistant"))


RETRY_SAME_MODEL = frozenset({"tool_use_failed"})


@dataclass(slots=True)
class CallResult[T]:
    value: T | None
    issues: list[str] = field(default_factory=list)
    repaired: bool = False
    exhausted: bool = False  # chain exhausted (no model, quota or all providers failed)
    provider_model: str | None = None


async def run_chain[P, T](
    ctx: AgentContext,
    role: Role,
    *,
    agent_name: str,
    instructions: str,
    prompt_version: str,
    prompt: str,
    allowed_ids: Collection[str | uuid.UUID] = (),
    output_schema: type[BaseModel] | None,
    parse: Callable[[Any], P],
    validate: Callable[[P], tuple[T | None, list[str]]],
    repair_prompt: Callable[[list[str]], str] | None = None,
    tools_factory: Callable[[], Sequence[Callable[..., Any]]] | None = None,
    tool_call_limit: int | None = None,
    timeout_s: float | None = None,
    next_model_on_invalid: bool = False,
    next_model_after_repair: bool = False,
) -> CallResult[T]:
    """Walk ``role_chain(role)`` until a valid result, the repair budget or the chain runs out.

    ``parse`` raises ``ValueError`` on schema failure; ``validate`` returns ``(value, issues)``
    where ``value is None`` means invalid. A provider error or unparsable (e.g. truncated) output
    moves to the next model; an invalid result triggers one repair (if ``repair_prompt``) on the
    same model. ``next_model_on_invalid`` moves an invalid result without a repair to the next
    model; with ``next_model_after_repair`` too, a failed repair also moves on, so every model
    in the chain is tried before the caller's fallback. Every attempt is recorded with its
    ``error_code``.
    """
    chain = role_chain(role)
    ensure_clean(prompt, allowed_ids=allowed_ids)
    start = 0
    current_prompt = prompt
    repaired = False
    retried = False
    last_issues: list[str] = []
    while start < len(chain):
        selection = await select_model(chain[start:], ctx.ledger, budget=ctx.budget)
        if selection is None:
            return CallResult(None, last_issues or ["chain_exhausted"], repaired, exhausted=True)
        spec = selection.spec
        index = start + selection.index
        try:
            agent = build_agent(
                spec,
                ctx.settings,
                name=agent_name,
                instructions=instructions,
                output_schema=output_schema,
                tools=tools_factory() if tools_factory else None,
                tool_call_limit=tool_call_limit,
            )
        except ProviderNotConfigured:
            await ctx.ledger.release(selection.reservation)
            start = index + 1
            continue

        ensure_clean(current_prompt, allowed_ids=allowed_ids)
        outcome = Outcome.OK
        error_code: str | None = None
        output: RunOutput | None = None
        with timed() as timer:
            try:
                output = await asyncio.wait_for(
                    ctx.runner(agent, current_prompt), timeout=timeout_s or spec.timeout_s + 5
                )
            except TimeoutError:
                outcome, error_code = Outcome.TIMEOUT, "timeout"
            except Exception as exc:  # provider SDKs raise many types; never log the message
                outcome, error_code = Outcome.PROVIDER_ERROR, type(exc).__name__
        await ctx.ledger.commit(selection.reservation)
        if output is not None and output.status == RunStatus.error:
            error_code = _error_code(output.content)
            outcome = Outcome.TIMEOUT if error_code == "timeout" else Outcome.PROVIDER_ERROR
        extra = _model_requests(output) - 1 if output is not None else 0
        if extra > 0:
            await _account_extra(ctx, spec, extra)

        value: T | None = None
        issues: list[str] = []
        malformed = False
        if outcome is Outcome.OK and output is not None:
            try:
                parsed = parse(output.content)
            except ValueError as exc:
                # Agno leaves ``content`` as the raw string when it cannot build the output
                # schema from it: truncated JSON (output budget spent, e.g. on Gemini thinking)
                # or no JSON at all. A repair prompt on the same model would hit the same limit,
                # so this attempt fails and the chain moves on.
                malformed = output_schema is not None and isinstance(output.content, str)
                value, issues = None, ["malformed_output" if malformed else str(exc)[:200]]
            else:
                try:
                    value, issues = validate(parsed)
                except ValueError as exc:
                    value, issues = None, [str(exc)[:200]]
            if value is None:
                outcome = Outcome.VALIDATION_FAILED
                error_code = "malformed_output" if malformed else "validation_failed"

        metrics = output.metrics if output is not None else None
        attempt = Attempt(
            provider_model=provider_model(spec.provider, spec.model_id),
            outcome=outcome.value,
            latency_ms=timer.elapsed_ms,
            input_tokens=metrics.input_tokens if metrics else None,
            output_tokens=metrics.output_tokens if metrics else None,
            error_code=error_code,
            tool_calls=len(output.tools or []) if output is not None else 0,
        )
        ctx.attempts.append(attempt)
        await record_invocation(
            ctx.session_factory,
            purpose=ctx.purpose,
            role=role,
            provider=spec.provider,
            model_id=spec.model_id,
            outcome=outcome,
            latency_ms=attempt.latency_ms,
            input_tokens=attempt.input_tokens,
            output_tokens=attempt.output_tokens,
            account_id=ctx.account_id,
            agent_run_id=ctx.agent_run_id,
            error_code=error_code,
            prompt_version=prompt_version,
        )

        if outcome is Outcome.OK:
            return CallResult(value, issues, repaired, provider_model=attempt.provider_model)
        if outcome is Outcome.VALIDATION_FAILED:
            last_issues = issues
            if malformed:
                start = index + 1  # unparsable output: next model, the repair stays unused
                continue
            if repair_prompt is not None and not repaired:
                repaired = True
                current_prompt = repair_prompt(issues)
                start = index  # repair on the same model first
                continue
            if next_model_on_invalid and (not repaired or next_model_after_repair):
                start = index + 1  # later models get a try (after a repair: with its note)
                continue
            return CallResult(None, issues, repaired, provider_model=attempt.provider_model)
        last_issues = [error_code or "provider_error"]
        if error_code in RETRY_SAME_MODEL and not retried:
            # Malformed tool call (gpt-oss on Groq sometimes leaks channel tokens into the tool
            # name): one fresh attempt on the same model; tool results are cached per run.
            retried = True
            start = index
            continue
        start = index + 1
    return CallResult(None, last_issues or ["chain_exhausted"], repaired, exhausted=True)


async def _account_extra(ctx: AgentContext, spec: ModelSpec, amount: int) -> None:
    """Book tool round-trips (one provider request each) against the model's bucket."""
    bucket = bucket_for_spec(spec)
    decision = await ctx.ledger.reserve(bucket=bucket, amount=amount)
    if decision.reservation is not None:
        await ctx.ledger.commit(decision.reservation)
    else:
        logger.warning("quota bucket=%s extra=%d not_booked", bucket.value, amount)
