"""Guide corpus chunk helpers (ADR-010, ADR-012). Chunks are written by the automated
publication gate (``app.curation.auto_publish``) with their embedding computed on write.
"""

from __future__ import annotations

import hashlib

PLACE_SECTIONS: tuple[str, ...] = (
    "OVERVIEW",
    "HISTORY",
    "HIGHLIGHTS",
    "VISIT_TIPS",
    "ETIQUETTE",
    "ACCESS",
)


def content_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def chunk_index(section: str) -> int:
    return PLACE_SECTIONS.index(section)
