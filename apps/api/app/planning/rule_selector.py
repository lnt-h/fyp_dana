"""Deterministic rule-based selector (architecture §3.2 step 4 fallback, ADR-004).

Used whenever the ``selector`` model is unavailable (no key, quota exhausted, provider failure,
invalid output) so planning always completes without AI. Pure code, no I/O: the same input gives
the same ranked pool.

Scoring per candidate (higher first):

* category matches an interest (explicit ``interest_category_codes`` or a keyword in the request
  text) → +100;
* famous-vs-hidden: a place with a curated long description (Wikipedia lead) counts as *famous*.
  Default and "famous" requests favour famous places; "hidden gem / local" requests favour the
  others;
* greedy diversity while picking: −30 per already picked place of the same category, +8 for a
  travel area not yet covered on multi-day trips (area spread);
* meal slots: FOOD gets up to two picks per day (lunch, dinner) and CAFE one, ranked by the same
  score, so every day has a meal candidate when the catalog has one.

Must-sees always come first, in the order given. Ties break on the place id string.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

Pace = Literal["RELAXED", "BALANCED", "PACKED"]
FamePreference = Literal["FAMOUS", "HIDDEN"]

PICKS_PER_DAY: dict[str, int] = {"RELAXED": 4, "BALANCED": 6, "PACKED": 8}
MAX_POOL = 24
MEAL_CATEGORIES = frozenset({"FOOD", "CAFE"})
FOOD_PER_DAY = 2
CAFE_PER_DAY = 1

INTEREST_BONUS = 100
FAME_BONUS = 20
DEFAULT_FAME_BONUS = 10
CATEGORY_REPEAT_PENALTY = 30
NEW_AREA_BONUS = 8

# Accent-folded keywords (VI and EN) → category codes.
_KEYWORDS: dict[str, tuple[str, ...]] = {
    "BEACH": ("beach", "bien", "swim", "tam bien", "bai"),
    "FOOD": ("food", "eat", "an uong", "mon an", "dac san", "quan an", "restaurant", "street food"),
    "CAFE": ("cafe", "coffee", "ca phe"),
    "MUSEUM": ("museum", "bao tang", "history", "lich su"),
    "RELIGIOUS_SITE": ("temple", "pagoda", "chua", "church", "nha tho", "den", "spiritual"),
    "MARKET": ("market", "cho", "shopping", "mua sam"),
    "NIGHTLIFE": ("night", "bar", "pub", "ve dem", "buoi toi", "nightlife"),
    "NATURE": ("nature", "thien nhien", "hike", "trek", "forest", "rung", "nui", "mountain"),
    "VIEWPOINT": ("view", "sunset", "hoang hon", "ngam canh", "panorama"),
    "HERITAGE": ("heritage", "di san", "old town", "pho co", "ancient", "co kinh"),
    "THEME_PARK": ("theme park", "amusement", "cong vien", "kids", "tre em", "family"),
    "CRAFT_VILLAGE": ("craft", "lang nghe", "pottery", "gom", "handicraft", "thu cong"),
}
_HIDDEN = (
    "hidden",
    "local",
    "off the beaten",
    "less touristy",
    "it nguoi",
    "an khach",
    "dia phuong",
)
_FAMOUS = ("famous", "must see", "iconic", "highlight", "noi tieng", "noi bat", "biet tieng")


def fold(text: str) -> str:
    """Lower-case, accent-free, ``đ`` → ``d``, punctuation as spaces."""
    decomposed = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return " " + re.sub(r"[^\w]+", " ", stripped).strip() + " "


def _has(folded: str, phrase: str) -> bool:
    return f" {phrase} " in folded


def interests_from_text(text: str | None) -> frozenset[str]:
    if not text:
        return frozenset()
    folded = fold(text)
    return frozenset(
        code for code, words in _KEYWORDS.items() if any(_has(folded, w) for w in words)
    )


def fame_preference(text: str | None) -> FamePreference | None:
    if not text:
        return None
    folded = fold(text)
    if any(_has(folded, w) for w in _HIDDEN):
        return "HIDDEN"
    if any(_has(folded, w) for w in _FAMOUS):
        return "FAMOUS"
    return None


def pool_size(days: int, pace: str | None) -> int:
    """Pool for the solver: picks per day for the pace plus one spare per day, capped."""
    per_day = PICKS_PER_DAY.get(pace or "BALANCED", PICKS_PER_DAY["BALANCED"])
    return min(MAX_POOL, (per_day + 1) * max(1, days))


@dataclass(frozen=True, slots=True)
class RuleCandidate:
    place_id: uuid.UUID
    category_code: str
    area_code: str | None = None
    famous: bool = False


def base_score(
    candidate: RuleCandidate, interests: Collection[str], fame: FamePreference | None
) -> int:
    score = INTEREST_BONUS if candidate.category_code in interests else 0
    if fame == "HIDDEN":
        score += -FAME_BONUS // 2 if candidate.famous else FAME_BONUS
    elif fame == "FAMOUS":
        score += FAME_BONUS if candidate.famous else 0
    else:
        score += DEFAULT_FAME_BONUS if candidate.famous else 0
    return score


def rank_candidates(
    candidates: Iterable[RuleCandidate],
    *,
    interests: Collection[str] = (),
    request_text: str | None = None,
) -> list[RuleCandidate]:
    """Static relevance order (used to pre-rank the pool sent to the model)."""
    wanted = frozenset(interests) | interests_from_text(request_text)
    fame = fame_preference(request_text)
    return sorted(candidates, key=lambda c: (-base_score(c, wanted, fame), str(c.place_id)))


def select_rule_based(
    candidates: Sequence[RuleCandidate],
    *,
    days: int,
    pace: str | None = None,
    interests: Collection[str] = (),
    request_text: str | None = None,
    must_see: Sequence[uuid.UUID] = (),
    exclude: Collection[uuid.UUID] = (),
    limit: int | None = None,
) -> list[uuid.UUID]:
    """Ranked place ids (best first) for a ``days``-day trip. Deterministic."""
    target = limit if limit is not None else pool_size(days, pace)
    wanted = frozenset(interests) | interests_from_text(request_text)
    fame = fame_preference(request_text)
    excluded = set(exclude)
    pool = {c.place_id: c for c in candidates if c.place_id not in excluded}

    picked: list[uuid.UUID] = [pid for pid in dict.fromkeys(must_see) if pid in pool]
    category_count: dict[str, int] = {}
    areas: set[str] = set()
    for pid in picked:
        cand = pool[pid]
        category_count[cand.category_code] = category_count.get(cand.category_code, 0) + 1
        if cand.area_code:
            areas.add(cand.area_code)

    meal_caps = {"FOOD": FOOD_PER_DAY * days, "CAFE": CAFE_PER_DAY * days}
    # Meal slots are reserved whatever the interests: every day needs lunch and dinner.
    reserved = {
        code: min(cap, sum(1 for c in pool.values() if c.category_code == code))
        for code, cap in meal_caps.items()
    }

    def dynamic(cand: RuleCandidate) -> int:
        score = base_score(cand, wanted, fame)
        score -= CATEGORY_REPEAT_PENALTY * category_count.get(cand.category_code, 0)
        if days > 1 and cand.area_code and cand.area_code not in areas:
            score += NEW_AREA_BONUS
        return score

    def take(cand: RuleCandidate) -> None:
        picked.append(cand.place_id)
        category_count[cand.category_code] = category_count.get(cand.category_code, 0) + 1
        if cand.area_code:
            areas.add(cand.area_code)

    # 1. Meal slots (scored without the repeat penalty inside their own category).
    for code in ("FOOD", "CAFE"):
        need = reserved[code] - category_count.get(code, 0)
        options = sorted(
            (c for c in pool.values() if c.category_code == code and c.place_id not in picked),
            key=lambda c: (-base_score(c, wanted, fame), str(c.place_id)),
        )
        for cand in options[: max(0, need)]:
            if len(picked) >= target:
                break
            take(cand)

    # 2. Everything else, greedily with diversity; meal categories only beyond their cap.
    while len(picked) < target:
        chosen = set(picked)
        options = [
            c
            for c in pool.values()
            if c.place_id not in chosen
            and (
                c.category_code not in MEAL_CATEGORIES
                or category_count.get(c.category_code, 0) < meal_caps[c.category_code]
            )
        ]
        if not options:
            break
        best = min(options, key=lambda c: (-dynamic(c), str(c.place_id)))
        take(best)
    return picked  # must-sees are never cut, even beyond the target
