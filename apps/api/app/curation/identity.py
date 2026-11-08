"""Description identity check (DEC-031, data-fix spec §4.2 ``DESCRIPTION_IDENTITY``).

A description must be about *this* place. Beyond the source-level rules (Wikipedia only through
the place's own Wikidata sitelink, Wikivoyage only through a matched listing), a cheap text check
rejects a description that names another catalog place but none of this place's own names — it
caught "art-gallery" described as "Art In Paradise", "nha-tho-toc" as "Nhà thờ tộc Trần" and the
Réhahn biography on the Precious Heritage museum. Pure functions, accent-folded word matching.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from app.catalog.normalize import fold_words
from app.curation.names import name_core

MIN_OTHER_NAME_CHARS = 10


def _contains(text: str, phrase: str) -> bool:
    return bool(phrase) and f" {phrase} " in text


def mentions_own_name(text: str, own_names: Iterable[str]) -> bool:
    folded = f" {fold_words(text)} "
    for name in own_names:
        full = fold_words(name)
        core = name_core(name)
        if _contains(folded, full) or (len(core) >= 4 and _contains(folded, core)):
            return True
    return False


def other_place_index(names_by_slug: Mapping[str, Iterable[str]]) -> dict[str, str]:
    """``{folded full name: slug}`` of names specific enough to identify a place in free text:
    at least two words left after the class word and at least ``MIN_OTHER_NAME_CHARS`` long."""
    index: dict[str, str] = {}
    ambiguous: set[str] = set()
    for slug, names in names_by_slug.items():
        for name in names:
            full = fold_words(name)
            if len(full) < MIN_OTHER_NAME_CHARS or len(name_core(name).split()) < 2:
                continue
            if full in index and index[full] != slug:
                ambiguous.add(full)
            index.setdefault(full, slug)
    return {name: slug for name, slug in index.items() if name not in ambiguous}


def description_mentions_other_place(
    text: str | None, *, slug: str, own_names: Iterable[str], index: Mapping[str, str]
) -> str | None:
    """The slug of another catalog place the text names, when it names none of ``own_names``."""
    if not text:
        return None
    own = list(own_names)
    if mentions_own_name(text, own):
        return None
    folded = f" {fold_words(text)} "
    own_folded = {fold_words(name) for name in own}
    for name, other in sorted(index.items(), key=lambda item: (-len(item[0]), item[0])):
        if other != slug and name not in own_folded and _contains(folded, name):
            return other
    return None
