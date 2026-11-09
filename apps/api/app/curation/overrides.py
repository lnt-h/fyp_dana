"""Owner-maintained curation decisions (``data/curation/<city>.yaml``, DEC-031).

Facts about *what a place is* that no open source states reliably, recorded by the owner and
applied by the gate in code: areas (published for map and Guide, never a planner stop), parts of
another place (folded into the parent, not a stop), records that are not trip stops, descriptions
of the wrong entity, and display-name suffixes. Keys are place slugs. The file never carries
descriptions or facts; those come from sources (sheet, Wikivoyage, Wikipedia, OSM).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.ingestion.areas import DATA_DIR

CURATION_DIR = DATA_DIR / "curation"


@dataclass(frozen=True)
class CurationOverrides:
    areas: frozenset[str] = frozenset()
    schedulable: frozenset[str] = frozenset()  # never an area even if a source class says so
    part_of: dict[str, str] = field(default_factory=dict)  # child slug -> parent slug
    not_a_stop: dict[str, str] = field(default_factory=dict)  # slug -> reason
    blocked_descriptions: frozenset[tuple[str, str, str]] = frozenset()  # (slug, locale, source)


def parse_overrides(document: dict[str, Any] | None) -> CurationOverrides:
    doc = document or {}

    def slugs(key: str) -> frozenset[str]:
        return frozenset(str(item["slug"]) for item in doc.get(key) or [])

    return CurationOverrides(
        areas=slugs("areas"),
        schedulable=slugs("schedulable"),
        part_of={str(item["slug"]): str(item["parent"]) for item in doc.get("part_of") or []},
        not_a_stop={
            str(item["slug"]): str(item.get("reason") or "not a trip stop")
            for item in doc.get("not_a_stop") or []
        },
        blocked_descriptions=frozenset(
            (str(item["slug"]), str(item["locale"]), str(item["source"]))
            for item in doc.get("blocked_descriptions") or []
        ),
    )


@lru_cache(maxsize=8)
def load_overrides(city_code: str, path: Path | None = None) -> CurationOverrides:
    file = path or CURATION_DIR / f"{city_code}.yaml"
    if not file.exists():
        return CurationOverrides()
    with file.open(encoding="utf-8") as handle:
        return parse_overrides(yaml.safe_load(handle))
