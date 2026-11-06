"""Diacritic-free lower-case normalisation shared by alias writes and search (FR-002).

``place_aliases.alias_normalized`` is written with :func:`normalize_search_text` and queries are
normalised the same way, so "Chùa Linh Ứng", "chua linh ung" and "CHUA LINH UNG" all match.
"""

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
# đ/Đ are base letters in Unicode, not d + combining mark, so NFD does not split them.
_LETTER_MAP = str.maketrans({"đ": "d", "Đ": "d"})


def normalize_search_text(value: str) -> str:
    """Lower-case, strip combining marks (NFD), map đ→d and collapse whitespace."""
    decomposed = unicodedata.normalize("NFD", value.translate(_LETTER_MAP))
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return _WHITESPACE.sub(" ", stripped.lower()).strip()
