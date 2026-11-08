"""Domain validators for model output (architecture §3.1, AGENTS.md implementation rules).

Pure functions, no I/O. Pydantic checks the shape; these check the meaning: catalog IDs are a
subset of the supplied candidates, citations point at supplied evidence, and every quote a
researcher reports is verbatim text of a page fetched in the same run (DEC-022).
"""

from __future__ import annotations

import json
import re
import unicodedata
import uuid
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ValidationError

from app.agents.schemas import (
    AnswerStatus,
    Claim,
    GroundedAnswer,
    Pick,
    RationaleSet,
    ResearchReport,
    ResearchTools,
    SelectionResult,
    WebCandidate,
)

# ---------------------------------------------------------------------------------------------
# Text helpers (shared with app.research)
# ---------------------------------------------------------------------------------------------

_WS_RE = re.compile(r"\s+")
_PUNCT_MAP = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "−": "-",
        " ": " ",
        "…": "...",
    }
)


def normalise_text(value: str) -> str:
    """NFC, unified quotes/dashes, collapsed whitespace, case-folded. Accents are kept."""
    value = unicodedata.normalize("NFC", value).translate(_PUNCT_MAP)
    return _WS_RE.sub(" ", value).strip().casefold()


def fold(value: str) -> str:
    """Accent-insensitive form for name matching (``Hội An`` → ``hoi an``)."""
    decomposed = unicodedata.normalize("NFD", normalise_text(value)).replace("đ", "d")
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return _WS_RE.sub(" ", re.sub(r"[^\w\s]", " ", stripped)).strip()


def quote_in_text(quote: str, text: str) -> bool:
    """True when ``quote`` occurs verbatim in ``text`` modulo whitespace, case and typography."""
    needle = normalise_text(quote).strip(" .\"'")
    return len(needle) >= 4 and needle in normalise_text(text)


def normalise_url(url: str) -> str:
    """Scheme/host lower-cased, fragment dropped, default port and trailing slash removed."""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    netloc = (
        host
        if port is None or (scheme, port) in {("https", 443), ("http", 80)}
        else (f"{host}:{port}")
    )
    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parts.query, ""))


# ---------------------------------------------------------------------------------------------
# Parsing model content
# ---------------------------------------------------------------------------------------------


def extract_json_object(text: str) -> Any:
    """First top-level JSON object in ``text`` (tolerates ``json`` fences and leading prose)."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    while start != -1:
        try:
            value, _ = json.JSONDecoder().raw_decode(stripped[start:])
            return value
        except json.JSONDecodeError:
            start = stripped.find("{", start + 1)
    raise ValueError("no JSON object in model output")


def parse_output[M: BaseModel](content: Any, schema: type[M]) -> M:
    """Re-validate model content with ``schema`` (``extra="forbid"``). Raises ``ValueError``."""
    try:
        if isinstance(content, schema):
            return schema.model_validate(content.model_dump())
        if isinstance(content, BaseModel):
            return schema.model_validate(content.model_dump())
        if isinstance(content, dict):
            return schema.model_validate(content)
        if isinstance(content, str):
            return schema.model_validate(extract_json_object(content))
    except ValidationError as exc:
        raise ValueError(f"schema: {exc.error_count()} error(s)") from exc
    raise ValueError("empty model output")


# ---------------------------------------------------------------------------------------------
# selector
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SelectionCheck:
    issues: tuple[str, ...]
    result: SelectionResult | None  # normalised (ranks 1..n), set only when valid

    @property
    def ok(self) -> bool:
        return not self.issues


def validate_selection(
    result: SelectionResult,
    *,
    candidate_ids: Collection[uuid.UUID],
    must_see: Collection[uuid.UUID] = (),
    days: int = 3,
    max_picks: int = 24,
) -> SelectionCheck:
    """IDs ⊆ candidates, no duplicates, must-sees present, day hints within the trip."""
    allowed = {str(item) for item in candidate_ids}
    issues: list[str] = []
    seen: set[str] = set()
    picks: list[Pick] = []
    for pick in sorted(result.picks, key=lambda p: p.rank):
        try:
            key = str(uuid.UUID(pick.place_id))
        except ValueError:
            issues.append(f"unknown_place_id:{pick.place_id[:40]}")
            continue
        if key not in allowed:
            issues.append(f"unknown_place_id:{key}")
            continue
        if key in seen:
            issues.append(f"duplicate_place_id:{key}")
            continue
        if pick.day_hint is not None and pick.day_hint > days:
            issues.append(f"day_hint_out_of_range:{key}")
            continue
        seen.add(key)
        picks.append(pick.model_copy(update={"place_id": key}))
    missing = sorted(str(item) for item in must_see if str(item) not in seen)
    issues.extend(f"must_see_missing:{key}" for key in missing)
    if len(picks) > max_picks:
        issues.append(f"too_many_picks:{len(picks)}")
    if not picks:
        issues.append("no_picks")
    if issues:
        return SelectionCheck(tuple(issues), None)
    ranked = [p.model_copy(update={"rank": i}) for i, p in enumerate(picks, start=1)]
    return SelectionCheck((), SelectionResult(picks=ranked, unmet_requests=result.unmet_requests))


def rule_based_selection(
    candidate_ids: Sequence[uuid.UUID],
    *,
    categories: Mapping[uuid.UUID, str] | None = None,
    must_see: Sequence[uuid.UUID] = (),
    max_picks: int = 24,
) -> SelectionResult:
    """Deterministic fallback: must-sees first, then candidates round-robin by category in the
    orchestrator's order (which is already relevance-ranked), so planning completes without AI."""
    ordered: list[uuid.UUID] = [pid for pid in must_see if pid in set(candidate_ids)]
    buckets: dict[str, list[uuid.UUID]] = {}
    for pid in candidate_ids:
        if pid in ordered:
            continue
        buckets.setdefault((categories or {}).get(pid, ""), []).append(pid)
    queues = list(buckets.values())
    while queues and len(ordered) < max_picks:
        for queue in list(queues):
            if queue:
                ordered.append(queue.pop(0))
            if not queue:
                queues.remove(queue)
            if len(ordered) >= max_picks:
                break
    picks = [Pick(place_id=str(pid), rank=i) for i, pid in enumerate(ordered[:max_picks], 1)]
    return SelectionResult(picks=picks, unmet_requests=[])


# ---------------------------------------------------------------------------------------------
# grounded_writer
# ---------------------------------------------------------------------------------------------

# Rationales must not author displayed facts (hours, prices, distances, durations, phones).
_FACTLIKE_RE = re.compile(
    r"\d{1,2}\s*(?:[:h]\s*\d{2}|h\b|giờ|am\b|pm\b)"
    r"|\d[\d.,]*\s*(?:đ|₫|vnd|vnđ|usd|\$|k\b|nghìn|ngàn|triệu)"
    r"|\d[\d.,]*\s*(?:km|m\b|mét|phút|minutes?|mins?|hours?|tiếng)",
    re.IGNORECASE,
)


def validate_rationales(
    result: RationaleSet, *, stop_ids: Collection[uuid.UUID]
) -> tuple[dict[uuid.UUID, str | None], list[str]]:
    """Map every stop to a rationale or ``None``; unknown IDs, duplicates and fact-like text are
    dropped (the stop then shows no rationale rather than an unsupported claim)."""
    allowed = {str(item): item for item in stop_ids}
    out: dict[uuid.UUID, str | None] = dict.fromkeys(stop_ids)
    issues: list[str] = []
    for item in result.rationales:
        try:
            key = str(uuid.UUID(item.place_id))
        except ValueError:
            issues.append("unknown_place_id")
            continue
        if key not in allowed:
            issues.append(f"unknown_place_id:{key}")
            continue
        pid = allowed[key]
        if out[pid] is not None:
            issues.append(f"duplicate_place_id:{key}")
            continue
        if _FACTLIKE_RE.search(item.text):
            issues.append(f"fact_like_text:{key}")
            continue
        out[pid] = item.text
    return out, issues


def validate_citations(
    answer: GroundedAnswer, *, evidence_ids: Collection[str]
) -> tuple[GroundedAnswer, int]:
    """Drop claims citing anything outside the supplied evidence; zero claims left →
    ``INSUFFICIENT_EVIDENCE``. Returns the cleaned answer and the number of dropped claims."""
    allowed = set(evidence_ids)
    kept: list[Claim] = []
    dropped = 0
    for claim in answer.claims:
        if claim.evidence_ids and all(eid in allowed for eid in claim.evidence_ids):
            kept.append(claim)
        else:
            dropped += 1
    if answer.status is AnswerStatus.INSUFFICIENT_EVIDENCE or not kept:
        return GroundedAnswer(status=AnswerStatus.INSUFFICIENT_EVIDENCE, claims=[]), dropped
    return GroundedAnswer(status=AnswerStatus.ANSWERED, claims=kept), dropped


# ---------------------------------------------------------------------------------------------
# researcher
# ---------------------------------------------------------------------------------------------


@dataclass(slots=True)
class ResearchCheck:
    report: ResearchReport
    dropped: list[str] = field(default_factory=list)


def _name_in_quote(name: str, quote: str) -> bool:
    tokens = [tok for tok in fold(name).split() if len(tok) >= 2]
    haystack = f" {fold(quote)} "
    return bool(tokens) and all(f" {tok} " in haystack for tok in tokens)


def validate_research(
    report: ResearchReport,
    *,
    tools: ResearchTools,
    known_names: Iterable[str] = (),
) -> ResearchCheck:
    """Keep only what the fetched pages support.

    * candidate ``source_url`` must be a page fetched in this run;
    * ``name_quote`` must be verbatim page text and contain the candidate name;
    * each fact's ``quote`` must be verbatim page text, else the fact is dropped;
    * ``google_place_id`` must come from a places_check of this run, else it is cleared;
    * duplicates and names already in the catalog (``known_names``) are dropped;
    * evidence must quote a fetched page verbatim.
    """
    dropped: list[str] = []
    known = {fold(name) for name in known_names}
    seen: set[str] = set()
    candidates: list[WebCandidate] = []
    for cand in report.candidates:
        url = normalise_url(cand.source_url)
        text = tools.page_text(url)
        label = cand.name[:60]
        if text is None:
            dropped.append(f"candidate_source_not_fetched:{label}")
            continue
        if not quote_in_text(cand.name_quote, text):
            dropped.append(f"candidate_name_quote_not_found:{label}")
            continue
        if not _name_in_quote(cand.name, cand.name_quote):
            dropped.append(f"candidate_name_not_in_quote:{label}")
            continue
        key = fold(cand.name)
        if key in seen:
            dropped.append(f"candidate_duplicate:{label}")
            continue
        if key in known:
            dropped.append(f"candidate_already_in_catalog:{label}")
            continue
        facts = []
        for fact in cand.facts:
            if quote_in_text(fact.quote, text):
                facts.append(fact)
            else:
                dropped.append(f"fact_quote_not_found:{label}:{fact.field}")
        place_id = cand.google_place_id
        if place_id is not None and tools.places_result(place_id) is None:
            dropped.append(f"google_place_id_unverified:{label}")
            place_id = None
        seen.add(key)
        candidates.append(
            cand.model_copy(update={"source_url": url, "facts": facts, "google_place_id": place_id})
        )
    evidence = []
    for item in report.evidence:
        url = normalise_url(item.source_url)
        text = tools.page_text(url)
        if text is None or not quote_in_text(item.quote, text):
            dropped.append(f"evidence_quote_not_found:{url[:80]}")
            continue
        evidence.append(item.model_copy(update={"source_url": url}))
    return ResearchCheck(ResearchReport(candidates=candidates, evidence=evidence), dropped)
