"""Duplicate detection for the publication gate (DEC-031, data-fix spec §4.2 ``DUPLICATE_OF``).

Two candidate places are duplicates when they share a Wikidata item or an OpenStreetMap element,
or when their categories are compatible, they lie within the category radius and their name
cores (generic class words stripped, accent-folded) are at least 0.85 similar. FOOD, CAFE and
NIGHTLIFE branches of one name anywhere in the city collapse to one stop (``BRANCH_RADIUS_M``).
The keeper is deterministic: passes the other gate rules > own Wikidata item > Vietnamese
name with diacritics > more sources > older record > slug. Pure functions; the gate supplies
the candidates.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher

from app.curation.names import has_vietnamese_diacritics, name_core

NAME_SIMILARITY = 0.85
BRANCH_RADIUS_M = 15_000.0

RADIUS_M: dict[str, float] = {
    "FOOD": 75.0,
    "CAFE": 75.0,
    "NIGHTLIFE": 75.0,
    "MARKET": 150.0,
    "MUSEUM": 150.0,
    "RELIGIOUS_SITE": 150.0,
    "HERITAGE": 150.0,
    "VIEWPOINT": 150.0,
    "THEME_PARK": 400.0,
    "BEACH": 2_000.0,
    "NATURE": 2_000.0,
    "CRAFT_VILLAGE": 2_000.0,
}
DEFAULT_RADIUS_M = 150.0

# Categories that may describe the same real place (an OSM café vs a Wikidata restaurant).
_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"FOOD", "CAFE", "NIGHTLIFE", "MARKET"}),
    frozenset({"MUSEUM", "HERITAGE", "RELIGIOUS_SITE", "VIEWPOINT"}),
    frozenset({"BEACH", "NATURE", "VIEWPOINT"}),
    frozenset({"THEME_PARK", "NATURE"}),
    frozenset({"CRAFT_VILLAGE", "MARKET", "HERITAGE"}),
)
_BRANCH_CATEGORIES = frozenset({"FOOD", "CAFE", "NIGHTLIFE"})


@dataclass(frozen=True)
class Candidate:
    slug: str
    category: str | None
    lat: float
    lng: float
    names: tuple[str, ...]  # display names and aliases, any locale
    qid: str | None = None
    osm_ids: frozenset[str] = field(default_factory=frozenset)
    source_count: int = 0
    created_at: datetime | None = None
    vi_name: str | None = None
    eligible: bool = True  # passes every other gate rule: preferred as the keeper


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def compatible(a: str | None, b: str | None) -> bool:
    if a is None or b is None:
        return False
    return a == b or any(a in group and b in group for group in _GROUPS)


def radius_for(a: str | None, b: str | None) -> float:
    return max(RADIUS_M.get(a or "", DEFAULT_RADIUS_M), RADIUS_M.get(b or "", DEFAULT_RADIUS_M))


def name_similarity(a: Candidate, b: Candidate) -> float:
    best = 0.0
    cores_a = {core for core in (name_core(n) for n in a.names) if core}
    cores_b = {core for core in (name_core(n) for n in b.names) if core}
    for left in cores_a:
        for right in cores_b:
            if left == right:
                return 1.0
            best = max(best, SequenceMatcher(None, left, right).ratio())
    return best


def same_place(a: Candidate, b: Candidate) -> bool:
    if a.qid and b.qid:
        if a.qid == b.qid:
            return True
    if a.osm_ids & b.osm_ids:
        return True
    if not compatible(a.category, b.category):
        return False
    distance = distance_m(a.lat, a.lng, b.lat, b.lng)
    similarity = name_similarity(a, b)
    # Two different Wikidata items need the same name core ("My Son B1" vs "B3" are two towers).
    if similarity < (1.0 if a.qid and b.qid else NAME_SIMILARITY):
        return False
    if distance <= radius_for(a.category, b.category):
        return True
    return (
        a.category in _BRANCH_CATEGORIES
        and b.category in _BRANCH_CATEGORIES
        and distance <= BRANCH_RADIUS_M
    )


def keeper_key(c: Candidate) -> tuple[int, int, int, int, float, str]:
    """Sort key: the first candidate is kept."""
    created = c.created_at.timestamp() if c.created_at else float("inf")
    return (
        0 if c.eligible else 1,
        0 if c.qid else 1,
        0 if c.vi_name and has_vietnamese_diacritics(c.vi_name) else 1,
        -c.source_count,
        created,
        c.slug,
    )


def find_duplicates(candidates: Sequence[Candidate]) -> dict[str, str]:
    """``{duplicate slug: keeper slug}`` over connected groups of :func:`same_place` pairs."""
    parent: dict[str, str] = {c.slug: c.slug for c in candidates}

    def root(slug: str) -> str:
        while parent[slug] != slug:
            parent[slug] = parent[parent[slug]]
            slug = parent[slug]
        return slug

    ordered = sorted(candidates, key=lambda c: c.lat)
    # Sweep by latitude: pairs farther apart than the largest radius are skipped cheaply.
    max_deg = BRANCH_RADIUS_M / 111_000.0
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if right.lat - left.lat > max_deg:
                break
            if same_place(left, right):
                parent[root(left.slug)] = root(right.slug)
    groups: dict[str, list[Candidate]] = {}
    for c in candidates:
        groups.setdefault(root(c.slug), []).append(c)
    result: dict[str, str] = {}
    for members in groups.values():
        if len(members) < 2:
            continue
        keeper = min(members, key=keeper_key)
        for member in members:
            if member.slug != keeper.slug:
                result[member.slug] = keeper.slug
    return result


def find_duplicate(desired: Candidate, others: Sequence[Candidate]) -> str | None:
    """The keeper slug when ``desired`` duplicates one of ``others`` and is not the keeper."""
    return find_duplicates([desired, *others]).get(desired.slug)
