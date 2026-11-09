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

from app.catalog.normalize import fold_words

PROPER_NAME_CATEGORIES = frozenset(
    {"FOOD", "CAFE", "NIGHTLIFE", "MARKET", "RELIGIOUS_SITE", "CRAFT_VILLAGE"}
)

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


def has_generic_prefix(name: str) -> bool:
    folded = fold_words(name)
    return any(folded == p or folded.startswith(p + " ") for p in GENERIC_PREFIXES)


def proper_name_fallback(category: str | None, vi_name: str | None) -> str | None:
    """The EN name to use when no source gives one: the VI name unchanged, or None."""
    name = " ".join((vi_name or "").split())
    if not name or category is None:
        return None
    if category in PROPER_NAME_CATEGORIES:
        return name
    return None if has_generic_prefix(name) else name


# ---- Name rules of the publication gate (DEC-031, data-fix spec §4.2) ----------------------

# A name that is only a class word is not a place name (iD validator / NSI behaviour). Folded,
# whole name. Exempt when the place has its own Wikidata item (the item names the place).
GENERIC_NAMES = frozenset(
    fold_words(name)
    for name in (
        "nhà thờ tộc",
        "nhà thờ",
        "chùa",
        "đình",
        "miếu",
        "lăng",
        "nhà bia",
        "quan âm",
        "tượng phật",
        "art gallery",
        "gallery",
        "museum",
        "bảo tàng",
        "café",
        "cafe",
        "coffee",
        "cà phê",
        "restaurant",
        "nhà hàng",
        "quán ăn",
        "chợ",
        "market",
        "bãi biển",
        "beach",
        "park",
        "công viên",
        "produce",
        "fruits and vegetables",
        "đền",
        "tháp",
        "temple",
        "pagoda",
        "church",
        "viewpoint",
        "bar",
        "pub",
        "nhà thờ tin lành",
        "protestant church",
        "protestantic church",
        "catholic church",
        "thánh thất cao đài",
        "rào chắn",
        "roadblock",
    )
)
_NSI_GENERIC = re.compile(r"^(fixme|n/?a|no ?name|none|null|unknown|test|untitled)$")

# Latin-script names that are correct in Vietnamese too (brands, foreign proper nouns). Folded.
# Owner-maintained: add a brand here when VI_NAME_NOT_VIETNAMESE holds a real place back.
LATIN_BRAND_ALLOWLIST = frozenset(
    fold_words(name)
    for name in (
        "Art in Paradise",
        "Art In Paradise Danang",
        "Hoi An Memories Land",
        "Mini-Golf Hoi An",
        "CSO Gallery",
        "Sun World Ba Na Hills",
        "Asia Park",
        "Sun World Danang Wonders",
        "Helio Center",
        "Golden Bridge",
        "Precious Heritage Art Gallery Museum",
        "Vinpearl Land Nam Hoi An",
        "VinWonders Nam Hoi An",
    )
)

# Venue categories whose names are often Latin brand names ("Rosie's Cafe", "Morning Glory").
VENUE_CATEGORIES = frozenset({"FOOD", "CAFE", "NIGHTLIFE"})

# Vietnamese-specific letters (after NFD the tone marks are combining characters).
_VI_LETTERS = set("ăâđêôơưĂÂĐÊÔƠƯ")


def has_vietnamese_diacritics(name: str) -> bool:
    if any(ch in _VI_LETTERS for ch in name):
        return True
    return any(unicodedata.combining(ch) for ch in unicodedata.normalize("NFD", name))


def is_latin_script(name: str) -> bool:
    """Latin letters (with Vietnamese diacritics), digits and punctuation only."""
    for ch in name:
        if ch.isalpha():
            base = unicodedata.normalize("NFD", ch)[0]
            if not ("a" <= base.lower() <= "z") and ch not in "đĐ":
                return False
    return True


def is_generic_name(name: str | None, *, has_qid: bool = False) -> bool:
    """True when the name is only a class word ("Chùa", "Museum", "Produce") or a placeholder."""
    if not name:
        return True
    folded = fold_words(name)
    if _NSI_GENERIC.match(folded):
        return True
    return not has_qid and folded in GENERIC_NAMES


def vi_name_problem(vi_name: str | None, category: str | None) -> bool:
    """True when the VI name is not Vietnamese: no diacritics, not a venue brand, not allow-listed.

    Catches "Tan Ky", "Diep Dong Nguyen", "Cua Dai", "Military blockhouse ruins". Venue
    categories (FOOD, CAFE, NIGHTLIFE) keep Latin brand names.
    """
    if not vi_name or has_vietnamese_diacritics(vi_name):
        return False
    if category in VENUE_CATEGORIES:
        return False
    return fold_words(vi_name) not in LATIN_BRAND_ALLOWLIST


def prefer_diacritic_alias(name: str | None, aliases: list[str]) -> str | None:
    """A VI alias spelling the same name with diacritics ("Tan Ky" -> "Tấn Ký"), else None."""
    if not name or has_vietnamese_diacritics(name):
        return None
    folded = fold_words(name)
    for alias in aliases:
        if has_vietnamese_diacritics(alias) and fold_words(alias) == folded:
            return " ".join(alias.split())
    return None


def normalise_display_name(name: str | None) -> str | None:
    """Deterministic display fixes: drop an address tail (", Trà Quế, Cẩm Hà, Hội An") when the
    head is a real name, and capitalise the first letter. Returns None for a non-Latin script."""
    if not name:
        return None
    text = " ".join(name.split())
    if not is_latin_script(text):
        return None
    if "," in text:
        head = text.split(",", 1)[0].strip()
        if len(head) >= 3 and not is_generic_name(head):
            text = head
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


_NOT_A_STOP = re.compile(
    r"\b(hotel|resort|homestay|hostel|villa|apartment|bat dong san|ngan hang|bank|atm|tailor|"
    r"may do|sieu thi|supermarket|mall|mega market|lotte mart|big c|co\.? ?ltd|cong ty|office|"
    r"van phong|pmu|phu kien|the thao)\b"
)


def is_not_a_stop_name(name: str | None) -> bool:
    """Hotels, banks, tailors, supermarkets, malls and offices are not trip stops."""
    return bool(name) and bool(_NOT_A_STOP.search(fold_words(name or "")))


_CORE_STOPWORDS = frozenset(
    {"the", "of", "and", "da nang", "hoi an", "danang", "hoian", "viet nam", "vietnam"}
)
_CORE_WORDS = frozenset(
    {
        "beach",
        "pagoda",
        "temple",
        "museum",
        "bridge",
        "market",
        "church",
        "hall",
        "assembly",
        "house",
        "old",
        "mountain",
        "restaurant",
        "cafe",
        "coffee",
        "the",
        "of",
        "and",
    }
)


def name_core(name: str | None) -> str:
    """Folded name without generic class words ("Bãi tắm Non Nước" -> "non nuoc")."""
    folded = fold_words(name or "")
    for prefix in sorted(GENERIC_PREFIXES, key=len, reverse=True):
        if folded == prefix:
            return ""
        if folded.startswith(prefix + " "):
            folded = folded[len(prefix) + 1 :]
            break
    text = " " + " ".join(w for w in folded.split() if w not in _CORE_WORDS) + " "
    kept = text
    for stop in _CORE_STOPWORDS:
        text = text.replace(f" {stop} ", " ")
    if not text.strip():
        text = kept  # "Chợ Hội An": the town name is the whole identity
    # Common spelling variants of one dish word ("Mỳ Quảng" / "Mì Quảng").
    text = text.replace(" my quang ", " mi quang ")
    return " ".join(text.split())
