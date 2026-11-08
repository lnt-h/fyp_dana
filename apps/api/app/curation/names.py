"""English-name fallback for Vietnamese proper names (owner decision 2026-11-08, D3 item 3).

A place with no English name keeps its original Vietnamese name in the EN localization when the
name is a proper noun: always for FOOD, CAFE, MARKET, RELIGIOUS_SITE and CRAFT_VILLAGE (venue,
market, pagoda and village names), and for other categories only when the name does not start
with a generic Vietnamese place word ("Bãi biển", "Bảo tàng", "Núi" …) that an English reader
would need translated. The name is reused unchanged and flagged
(``place_localizations.name_is_source_fallback``); names are never machine-translated.
"""

from __future__ import annotations

import re
import unicodedata

PROPER_NAME_CATEGORIES = frozenset({"FOOD", "CAFE", "MARKET", "RELIGIOUS_SITE", "CRAFT_VILLAGE"})

# Accent-folded generic leading words, matched on whole words.
GENERIC_PREFIXES: tuple[str, ...] = (
    "bai bien",
    "bai tam",
    "bai",
    "bien",
    "bao tang",
    "nui",
    "deo",
    "cau",
    "ho",
    "suoi",
    "thac",
    "dao",
    "hon",
    "ban dao",
    "cong vien",
    "khu du lich",
    "khu",
    "di tich",
    "nha tho",
    "nha co",
    "nha",
    "chua",
    "dinh",
    "den",
    "mieu",
    "lang",
    "thap",
    "thanh",
    "doi",
    "hang",
    "dong",
    "mui",
    "vinh",
    "pho",
    "duong",
    "quang truong",
    "tuong",
    "tuong dai",
    "nghia trang",
    "rung",
    "song",
    "dam",
    "cua",
    "vuon",
    "cho",
    "hoi quan",
    "truong",
    "ga",
)


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold()).replace("đ", "d")
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return " ".join(re.sub(r"[^\w\s]", " ", stripped).split())


def has_generic_prefix(name: str) -> bool:
    folded = _fold(name)
    return any(folded == p or folded.startswith(p + " ") for p in GENERIC_PREFIXES)


def proper_name_fallback(category: str | None, vi_name: str | None) -> str | None:
    """The EN name to use when no source gives one: the VI name unchanged, or None."""
    name = " ".join((vi_name or "").split())
    if not name or category is None:
        return None
    if category in PROPER_NAME_CATEGORIES:
        return name
    return None if has_generic_prefix(name) else name
