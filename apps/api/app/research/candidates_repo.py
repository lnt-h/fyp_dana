"""``web_place_candidates`` writer (DEC-015, DEC-022, ADR-014).

Stores the validated research candidates, nothing else: no ``places`` rows, no
``place_facts``, no publications. Facts extracted from a page are kept only inside
``extraction`` together with their verified verbatim quote. Promotion is a separate step
(``promote_web_candidate_if_eligible`` in the content pipeline).

* ``source_revision_id`` is the ``source_revisions`` row of the fetched page (required);
* ``google_place_id`` and ``places_checked_at`` come from this run's places check only;
* ``coordinate_source`` / ``location`` stay NULL: Google coordinates are never stored here
  (ADR-006) and no page coordinates are extracted yet;
* a re-proposal (same Google place, or same name in the city while pending) bumps
  ``times_proposed`` instead of inserting a duplicate.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError

from app.agents.schemas import WebCandidate
from app.ai.quota import SessionFactory
from app.research.places_check import PlacesOutcome
from app.research.toolbox import ResearchToolbox

logger = logging.getLogger("gonarra.research")

EXTRACTION_SCHEMA = "gonarra.research.v1"

_CITY = text("/* research:city */ SELECT id FROM cities WHERE code = :code")
_BY_GOOGLE_ID = text(
    "/* research:cand_by_gid */ SELECT id FROM web_place_candidates WHERE google_place_id = :gid"
)
_BY_NAME = text(
    "/* research:cand_by_name */ SELECT id FROM web_place_candidates "
    "WHERE city_id = :city_id AND lower(name) = lower(:name) AND review_state = 'PENDING' "
    "ORDER BY created_at LIMIT 1"
)
_BUMP = text(
    "/* research:cand_bump */ UPDATE web_place_candidates "
    "SET times_proposed = times_proposed + 1, updated_at = now() WHERE id = :id"
)
_INSERT = text(
    "/* research:cand_insert */ INSERT INTO web_place_candidates "
    "(city_id, name, name_vi, name_en, category_guess, location, coordinate_source, "
    "google_place_id, places_check_outcome, places_checked_at, source_revision_id, fetched_at, "
    "tavily_query, extraction, extraction_model) VALUES (:city_id, :name, :name_vi, :name_en, "
    ":category_guess, NULL, NULL, :gid, :outcome, :checked_at, :rev, :fetched_at, :query, "
    ":extraction, :model) RETURNING id"
).bindparams(bindparam("extraction", type_=JSONB))


@dataclass(frozen=True, slots=True)
class StoredCandidate:
    id: uuid.UUID
    name: str
    source_url: str
    places_check_outcome: str
    created: bool  # False when an existing row was re-proposed


def extraction_payload(candidate: WebCandidate, *, page_title: str | None) -> dict[str, Any]:
    return {
        "schema": EXTRACTION_SCHEMA,
        "source_url": candidate.source_url,
        "page_title": page_title,
        "name_quote": candidate.name_quote,
        "facts": [fact.model_dump() for fact in candidate.facts],
        "quotes_verified": True,
    }


async def store_candidates(
    session_factory: SessionFactory,
    *,
    candidates: Sequence[WebCandidate],
    toolbox: ResearchToolbox,
    extraction_model: str | None,
    city_code: str = "da-nang",
) -> list[StoredCandidate]:
    """Write one row per validated candidate (see module docstring). Candidates whose page has
    no ``source_revisions`` row are skipped (provenance is mandatory)."""
    stored: list[StoredCandidate] = []
    query = "; ".join(toolbox.queries)[:500] or None
    try:
        async with session_factory() as session:
            city_id = (await session.execute(_CITY, {"code": city_code})).scalar()
            if city_id is None:
                raise LookupError(f"city {city_code} not seeded")
            for cand in candidates:
                page = toolbox.page(cand.source_url)
                if page is None or page.source_revision_id is None:
                    logger.info("research candidate skipped reason=no_source_revision")
                    continue
                check = toolbox.places_for(cand.name, cand.google_place_id)
                outcome = check.outcome
                gid = (
                    check.google_place_id
                    if outcome not in {PlacesOutcome.SKIPPED, PlacesOutcome.NOT_FOUND}
                    else None
                )
                existing = None
                if gid is not None:
                    existing = (await session.execute(_BY_GOOGLE_ID, {"gid": gid})).scalar()
                if existing is None:
                    existing = (
                        await session.execute(_BY_NAME, {"city_id": city_id, "name": cand.name})
                    ).scalar()
                if existing is not None:
                    await session.execute(_BUMP, {"id": existing})
                    stored.append(
                        StoredCandidate(existing, cand.name, cand.source_url, outcome.value, False)
                    )
                    continue
                new_id: uuid.UUID = (
                    await session.execute(
                        _INSERT,
                        {
                            "city_id": city_id,
                            "name": cand.name,
                            "name_vi": cand.name_vi,
                            "name_en": cand.name_en,
                            "category_guess": cand.category_guess,
                            "gid": gid,
                            "outcome": outcome.value,
                            "checked_at": (
                                None if outcome is PlacesOutcome.SKIPPED else check.checked_at
                            ),
                            "rev": page.source_revision_id,
                            "fetched_at": page.retrieved_at or datetime.now(UTC),
                            "query": query,
                            "extraction": extraction_payload(cand, page_title=page.title),
                            "model": extraction_model,
                        },
                    )
                ).scalar_one()
                stored.append(
                    StoredCandidate(new_id, cand.name, cand.source_url, outcome.value, True)
                )
            await session.commit()
    except SQLAlchemyError:
        logger.warning("research candidates not stored count=%d", len(candidates))
        return []
    return stored
