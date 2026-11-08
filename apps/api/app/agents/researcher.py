"""``researcher`` role: catalog-first web research (architecture §3.1, §3.4, ADR-014).

Groq only (never Gemini). Tools are injected (:class:`app.agents.schemas.ResearchTools`,
implemented by ``app.research.toolbox``) so this package stays free of provider adapters and
repositories. The adapters enforce the per-run caps (≤ 2 searches, ≤ 3 fetches, ≤ 3 Places
checks); ``tool_call_limit`` bounds the loop. Whatever the model reports is kept only if the
fetched pages support it verbatim (:func:`app.agents.validators.validate_research`).

The model proposes; it never publishes. The orchestrator stores surviving candidates as
``web_place_candidates`` rows (``app.research.candidates_repo``), shown as ``WEB_UNVERIFIED``.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from agno.tools import tool

from app.agents.runtime import AgentContext, load_instructions, run_chain
from app.agents.schemas import (
    Locale,
    ResearchOutcome,
    ResearchReport,
    ResearchTools,
    ResultSource,
)
from app.agents.validators import parse_output, validate_research
from app.ai.providers import Role
from app.ai.redaction import redact_text

AGENT_NAME = "researcher"
# 6 research tool calls (architecture §3.1) + 1 submit_report call that ends the run.
TOOL_CALL_LIMIT = 7
# Whole tool loop (several Groq round-trips plus searches and fetches).
RUN_TIMEOUT_S = 120.0
MAX_KNOWN_NAMES = 40
# Groq rejects ``response_format=json_object`` together with tool calling, so the researcher
# runs without Agno's output_schema and the report is parsed and re-validated from the final
# message (the JSON shape is spelled out in the instructions).
STRUCTURED_OUTPUT = False


def research_tool_functions(tools: ResearchTools) -> list[Any]:
    """Plain async functions with docstrings: Agno derives the tool schema from them."""

    async def tavily_search(query: str) -> str:
        """Search the web for places in Đà Nẵng or Hội An. Returns up to 5 results with url,
        title and snippet.

        Args:
            query: Short search query in Vietnamese or English.
        """
        return await tools.tavily_search(query)

    async def fetch_page(url: str) -> str:
        """Fetch a search result page and return its readable text (truncated).

        Args:
            url: A URL returned by tavily_search.
        """
        return await tools.fetch_page(url)

    async def places_check(name: str) -> str:
        """Check whether a named place exists in Đà Nẵng and is operating.

        Args:
            name: Place name as written on the page.
        """
        return await tools.places_check(name)

    @tool(stop_after_tool_call=True)
    async def submit_report(
        candidates: list[dict[str, Any]], evidence: list[dict[str, Any]]
    ) -> str:
        """Submit the final research report. Call exactly once, at the end; this ends the task.

        Args:
            candidates: Proposed places, each with name, name_vi, name_en, category_guess,
                source_url, google_place_id, name_quote and facts (field, value, quote).
            evidence: Verbatim quotes that answer the request, each with source_url, quote, note.
        """
        # The run stops here and this string becomes the run content; it is parsed and
        # validated like a plain-text answer (gpt-oss tends to answer through a tool call).
        return json.dumps({"candidates": candidates, "evidence": evidence}, ensure_ascii=False)

    return [tavily_search, fetch_page, places_check, submit_report]


def build_research_prompt(*, request_text: str, locale: Locale, known_names: Sequence[str]) -> str:
    payload = {
        "request": redact_text(request_text),
        "answer_language": locale,
        "already_in_catalog": [redact_text(n) for n in known_names[:MAX_KNOWN_NAMES]],
    }
    return json.dumps(payload, ensure_ascii=False)


async def run_research(
    ctx: AgentContext,
    *,
    request_text: str,
    locale: Locale,
    tools: ResearchTools,
    known_names: Sequence[str] = (),
) -> ResearchOutcome:
    """Run the researcher once. Never raises for model, quota or validation failures: an empty
    ``DEGRADED`` report means research was skipped or failed."""
    first_attempt = len(ctx.attempts)
    instructions, version = load_instructions(AGENT_NAME, locale)
    prompt = build_research_prompt(
        request_text=request_text, locale=locale, known_names=known_names
    )
    dropped: list[str] = []

    def validate(report: ResearchReport) -> tuple[ResearchReport | None, list[str]]:
        check = validate_research(report, tools=tools, known_names=known_names)
        dropped.extend(check.dropped)
        return check.report, check.dropped

    call = await run_chain(
        ctx,
        Role.RESEARCHER,
        agent_name=AGENT_NAME,
        instructions=instructions,
        prompt_version=version,
        prompt=prompt,
        output_schema=ResearchReport if STRUCTURED_OUTPUT else None,
        parse=lambda content: parse_output(content, ResearchReport),
        validate=validate,
        tools_factory=lambda: research_tool_functions(tools),
        tool_call_limit=TOOL_CALL_LIMIT,
        timeout_s=RUN_TIMEOUT_S,
    )
    attempts = tuple(ctx.attempts[first_attempt:])
    if call.value is None:
        return ResearchOutcome(
            ResearchReport(), ResultSource.DEGRADED, attempts, tuple(call.issues)
        )
    return ResearchOutcome(call.value, ResultSource.MODEL, attempts, tuple(dropped))
