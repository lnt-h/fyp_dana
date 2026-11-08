"""Text helpers for research adapters: Đà Nẵng query scoping, page text extraction and the
model-facing excerpt.

The excerpt is what the researcher sees and what quotes are verified against, so it is built
deterministically (paragraphs ranked by overlap with the request) and redacted (BR-046: page
contact data and coordinates never travel to a model).
"""

from __future__ import annotations

import hashlib
import re

import trafilatura

from app.agents.validators import fold, normalise_text
from app.ai.redaction import ensure_clean, redact_text

MAX_QUERY_CHARS = 200
MAX_EXCERPT_CHARS = 1800
MAX_STORED_TEXT_CHARS = 60_000  # research_cache payload ≤ 256 KiB

_CITY_MARKERS = ("da nang", "danang", "hoi an", "hoian", "son tra", "ngu hanh son", "cu lao cham")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_WS_RE = re.compile(r"[ \t\r\f\v]+")


def build_scoped_query(query: str) -> str:
    """Redacted, whitespace-normalised query that always names the city (Đà Nẵng scope).

    Raises :class:`app.ai.redaction.RedactionError` if personal data survives redaction.
    """
    cleaned = " ".join(redact_text(query).split())[:MAX_QUERY_CHARS].strip()
    folded = fold(cleaned)
    if not any(marker in folded for marker in _CITY_MARKERS):
        cleaned = f"{cleaned} Đà Nẵng".strip()
    return ensure_clean(cleaned)


def query_key(query: str) -> str:
    """``research_cache.key_sha256`` for a Tavily query: SHA-256 of the normalised query."""
    return hashlib.sha256(normalise_text(query).encode("utf-8")).hexdigest()


def url_key(normalised_url: str) -> str:
    return hashlib.sha256(normalised_url.encode("utf-8")).hexdigest()


def content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def html_title(html: str) -> str | None:
    match = _TITLE_RE.search(html[:200_000])
    if not match:
        return None
    title = " ".join(match.group(1).split())
    return title[:300] or None


def html_to_text(html: str, *, url: str | None = None) -> str:
    """Main text of an HTML page (trafilatura; no comments, no links, tables kept)."""
    extracted = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_links=False,
        include_images=False,
        include_tables=True,
        favor_recall=True,
        deduplicate=True,
    )
    return clean_text(extracted or "")


def clean_text(value: str) -> str:
    lines = [_WS_RE.sub(" ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)[:MAX_STORED_TEXT_CHARS]


def _terms(value: str) -> set[str]:
    return {tok for tok in fold(value).split() if len(tok) >= 3}


def excerpt_for_model(text: str, *, focus: str = "", limit: int = MAX_EXCERPT_CHARS) -> str:
    """Redacted excerpt ≤ ``limit`` chars: the opening paragraph plus the paragraphs sharing
    the most terms with ``focus`` (the request and queries), kept in page order."""
    paragraphs = [p for p in redact_text(text).split("\n") if p.strip()]
    if not paragraphs:
        return ""
    wanted = _terms(focus)
    scored = sorted(
        range(len(paragraphs)),
        key=lambda i: (-(len(_terms(paragraphs[i]) & wanted)), i),
    )
    chosen: set[int] = {0}
    size = len(paragraphs[0])
    for index in scored:
        if index in chosen:
            continue
        cost = len(paragraphs[index]) + 1
        if size + cost > limit:
            continue
        chosen.add(index)
        size += cost
    excerpt = "\n".join(paragraphs[i] for i in sorted(chosen))
    return excerpt[:limit]
