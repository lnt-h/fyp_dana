"""Owner accuracy audit (2026-11-08): a CSV of a random sample of published places.

``python -m app.cli publish audit-sample [--fraction 0.1] [--seed N] [--out file.csv]`` writes,
for each sampled current publication, the published VI/EN names (with the proper-name fallback
flag), descriptions with their origin (``ORIGINAL`` / ``AI_SUMMARY``) and source locators, the
cited URLs of an AI summary, every published fact with its value and evidence locators, and the
image credit. The last two columns are empty for the owner to fill in (accurate? notes).
"""

from __future__ import annotations

import csv
import math
import random
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.auto_publish import AI_SUMMARY_PROVIDER_KEY
from app.models.catalog import (
    CatalogAuditEvent,
    CatalogPublication,
    FactEvidence,
    MediaAsset,
    Place,
    PlaceFact,
    PlaceLocalization,
    PublicationFact,
    PublicationMedia,
    SourceRevision,
)
from app.models.providers import DataProvider, ImportRecord, ImportRun

COLUMNS: tuple[str, ...] = (
    "slug",
    "area_code",
    "category_code",
    "name_vi",
    "name_en",
    "name_en_is_vi_fallback",
    "description_vi",
    "description_vi_origin",
    "description_en",
    "description_en_origin",
    "description_sources",
    "ai_cited_urls",
    "facts",
    "image_credit",
    "owner_accurate_yes_no",
    "owner_notes",
)


def sample_size(total: int, fraction: float) -> int:
    """``ceil(total × fraction)``, at least 1 when anything is published."""
    if total <= 0:
        return 0
    return min(total, max(1, math.ceil(total * fraction)))


def choose(items: Sequence[Any], *, fraction: float, seed: int | None) -> list[Any]:
    return random.Random(seed).sample(list(items), sample_size(len(items), fraction))


async def _locators(session: AsyncSession, ids: Sequence[str | uuid.UUID]) -> list[str]:
    wanted = [uuid.UUID(str(value)) for value in ids]
    if not wanted:
        return []
    rows = (
        await session.scalars(select(SourceRevision.locator).where(SourceRevision.id.in_(wanted)))
    ).all()
    return sorted(set(rows))


async def audit_rows(
    session: AsyncSession, *, fraction: float = 0.1, seed: int | None = None
) -> list[dict[str, str]]:
    publications = (
        await session.scalars(
            select(CatalogPublication)
            .where(CatalogPublication.state == "PUBLISHED")
            .order_by(CatalogPublication.id)
        )
    ).all()
    rows: list[dict[str, str]] = []
    for publication in choose(publications, fraction=fraction, seed=seed):
        place = await session.get(Place, publication.place_id)
        vi = await session.get(PlaceLocalization, publication.localization_vi_id)
        en = await session.get(PlaceLocalization, publication.localization_en_id)
        assert place is not None and vi is not None and en is not None
        detail = await session.scalar(
            select(CatalogAuditEvent.detail)
            .where(
                CatalogAuditEvent.entity_id == place.id,
                CatalogAuditEvent.action == "AUTO_PUBLISH",
            )
            .order_by(CatalogAuditEvent.id.desc())
            .limit(1)
        )
        source_ids: list[str] = []
        for values in ((detail or {}).get("sources") or {}).values():
            source_ids.extend(values)
        ai_payload = await session.scalar(
            select(ImportRecord.allowed_payload)
            .join(ImportRun, ImportRun.id == ImportRecord.import_run_id)
            .join(DataProvider, DataProvider.id == ImportRun.data_provider_id)
            .where(
                ImportRecord.place_id == place.id,
                ImportRecord.validation_status == "ACCEPTED",
                ImportRun.status == "SUCCEEDED",
                DataProvider.provider_key == AI_SUMMARY_PROVIDER_KEY,
            )
            .order_by(ImportRun.started_at.desc())
            .limit(1)
        )
        uses_ai = "AI_SUMMARY" in (vi.translation_origin, en.translation_origin)
        cited = list((ai_payload or {}).get("cited_urls") or []) if uses_ai else []
        facts: list[str] = []
        fact_rows = (
            await session.scalars(
                select(PlaceFact)
                .join(PublicationFact, PublicationFact.place_fact_id == PlaceFact.id)
                .where(PublicationFact.catalog_publication_id == publication.id)
                .order_by(PlaceFact.field_code)
            )
        ).all()
        for fact in fact_rows:
            evidence = (
                await session.scalars(
                    select(FactEvidence.source_revision_id).where(
                        FactEvidence.place_fact_id == fact.id
                    )
                )
            ).all()
            value = (fact.value or {}).get("text") if isinstance(fact.value, dict) else None
            shown = value or (fact.value if fact.value is not None else "")
            locators = await _locators(session, list(evidence))
            facts.append(
                f"{fact.field_code}={fact.knowledge_state}:{shown} [{' | '.join(locators)}]"
            )
        media = (
            await session.execute(
                select(MediaAsset.attribution_text, MediaAsset.license_code, MediaAsset.creator)
                .join(PublicationMedia, PublicationMedia.media_asset_id == MediaAsset.id)
                .where(PublicationMedia.catalog_publication_id == publication.id)
                .order_by(PublicationMedia.ordinal)
            )
        ).all()
        rows.append(
            {
                "slug": place.slug,
                "area_code": publication.area_code or "",
                "category_code": publication.category_code,
                "name_vi": vi.name,
                "name_en": en.name,
                "name_en_is_vi_fallback": "yes" if en.name_is_source_fallback else "no",
                "description_vi": vi.description or "",
                "description_vi_origin": vi.translation_origin,
                "description_en": en.description or "",
                "description_en_origin": en.translation_origin,
                "description_sources": " | ".join(await _locators(session, source_ids)),
                "ai_cited_urls": " | ".join(cited),
                "facts": " ; ".join(facts),
                "image_credit": " ; ".join(f"{m[0]} ({m[1]})" for m in media),
                "owner_accurate_yes_no": "",
                "owner_notes": "",
            }
        )
    rows.sort(key=lambda row: row["slug"])
    return rows


def write_csv(rows: Sequence[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
