"""Owner place sheet importer (CSV, DEC-022). Columns: ``apps/api/data/README.md``.

Each row is one place with VI/EN names and short descriptions, a row source (URL, publisher,
licence) and optional facts, each with its own source URL. Rows are validated in code; invalid
rows are staged as REJECTED import records with a reason. A row may name ``wikidata_id`` to
enrich the place already imported from Wikidata instead of creating a new one.
"""

from __future__ import annotations

import asyncio
import csv
import io
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.areas import assign_area, load_areas
from app.ingestion.common import (
    PROVENANCE_KEY,
    RunReport,
    add_record,
    canonical_json,
    create_place,
    finish_run,
    free_slug,
    get_or_create_revision,
    get_or_create_source,
    inside_city,
    link_identity,
    load_city,
    place_for_identity,
    provider_id_for,
    require_active_policy,
    sha256_hex,
    start_run,
)
from app.ingestion.wikidata import PROVIDER_KEY as WIKIDATA_KEY
from app.models.reference import Area, Category

PROVIDER_KEY = "gonarra_sheet"
IMPORTER_VERSION = "sheet-1"
SOURCE_KINDS = ("OFFICIAL", "OPEN_DATA", "REFERENCE", "OWN_OBSERVATION", "WEB")
UNKNOWN_LICENCE = "UNKNOWN"

REQUIRED_COLUMNS = (
    "slug",
    "category_code",
    "area_code",
    "lat",
    "lng",
    "name_vi",
    "name_en",
    "short_description_vi",
    "short_description_en",
    "source_url",
    "source_publisher",
    "licence",
)

# Sheet fact column -> fact_fields code. Each needs "<column>_source_url" when filled.
TEXT_FACTS: dict[str, str] = {
    "opening_hours": "OPENING_HOURS",
    "ticket_price": "ADMISSION_PRICE",
    "address_vi": "ADDRESS_VI",
    "payment_methods": "PAYMENT_METHODS",
    "dress_code": "DRESS_CODE",
    "access_rules": "ACCESS_RULES",
}

_DAYS = {"mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6, "sun": 7}
_RANGE = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]-(([01][0-9]|2[0-3]):[0-5][0-9]|24:00)$")


def parse_opening_hours(text: str) -> dict[str, list[list[str]]]:
    """``"mon-fri 08:00-11:30,13:30-17:00; sat-sun 07:00-17:00"`` → the OPENING_HOURS shape
    ``{"1": [["08:00", "11:30"], ["13:30", "17:00"]], ...}`` (ISO weekday keys, Mon = 1).
    ``daily`` means mon-sun; ``closed`` gives an empty list. Days not named are absent
    (unknown), never assumed closed. Raises ``ValueError("INVALID_OPENING_HOURS")``."""
    weekly: dict[str, list[list[str]]] = {}
    for clause in (part.strip() for part in text.split(";")):
        if not clause:
            continue
        pieces = clause.split(None, 1)
        if len(pieces) != 2:
            raise ValueError("INVALID_OPENING_HOURS")
        day_spec, hours = pieces[0].lower(), pieces[1].strip().lower()
        if day_spec == "daily":
            days = list(range(1, 8))
        else:
            days = []
            for token in day_spec.split(","):
                ends = token.split("-")
                if len(ends) == 1 and ends[0] in _DAYS:
                    days.append(_DAYS[ends[0]])
                elif len(ends) == 2 and ends[0] in _DAYS and ends[1] in _DAYS:
                    start, end = _DAYS[ends[0]], _DAYS[ends[1]]
                    if start > end:
                        raise ValueError("INVALID_OPENING_HOURS")
                    days.extend(range(start, end + 1))
                else:
                    raise ValueError("INVALID_OPENING_HOURS")
        if hours == "closed":
            ranges: list[list[str]] = []
        else:
            ranges = []
            for item in (piece.strip() for piece in hours.split(",")):
                if not _RANGE.match(item):
                    raise ValueError("INVALID_OPENING_HOURS")
                opens, closes = item.split("-")
                if closes != "24:00" and closes <= opens:
                    raise ValueError("INVALID_OPENING_HOURS")
                ranges.append([opens, closes])
        for day in days:
            if str(day) in weekly:
                raise ValueError("INVALID_OPENING_HOURS")
            weekly[str(day)] = ranges
    if not weekly:
        raise ValueError("INVALID_OPENING_HOURS")
    return dict(sorted(weekly.items()))


_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_QID = re.compile(r"^Q[0-9]+$")
_URL = re.compile(r"^https?://\S+$")


@dataclass(frozen=True)
class SheetFact:
    field_code: str
    value: dict[str, Any]
    source_url: str


@dataclass(frozen=True)
class SheetRow:
    line: int
    slug: str
    category_code: str
    area_code: str | None
    lat: float
    lng: float
    names: dict[str, str]
    short_descriptions: dict[str, str]
    descriptions: dict[str, str]
    source_url: str
    source_publisher: str
    source_kind: str
    licence: str
    attribution: str | None
    wikidata_id: str | None
    facts: tuple[SheetFact, ...]
    visit_minutes: tuple[int, int, int] | None

    def payload(self) -> dict[str, Any]:
        return {
            "id": self.slug,
            "wikidata_id": self.wikidata_id,
            "name": self.names,
            "location": {"lat": self.lat, "lng": self.lng},
            "category": self.category_code,
            "area": self.area_code,
            "short_description": self.short_descriptions,
            "description": self.descriptions,
            "source": {
                "url": self.source_url,
                "publisher": self.source_publisher,
                "kind": self.source_kind,
                "licence": self.licence,
                "attribution": self.attribution,
            },
            "facts": {
                fact.field_code: {"value": fact.value, "source_url": fact.source_url}
                for fact in self.facts
            },
            "visit_minutes": list(self.visit_minutes) if self.visit_minutes else None,
        }


@dataclass(frozen=True)
class RowError:
    line: int
    slug: str
    reason: str


def _cell(row: Mapping[str, str | None], key: str) -> str:
    return (row.get(key) or "").strip()


def parse_rows(text: str) -> tuple[list[SheetRow], list[RowError]]:
    """Structural validation only (reference data is checked against the database later)."""
    reader = csv.DictReader(io.StringIO(text))
    missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"sheet is missing columns: {', '.join(missing)}")
    rows: list[SheetRow] = []
    errors: list[RowError] = []
    for line, raw in enumerate(reader, start=2):
        slug = _cell(raw, "slug")
        try:
            rows.append(_parse_row(line, raw))
        except ValueError as exc:
            errors.append(RowError(line=line, slug=slug, reason=str(exc)))
    return rows, errors


def _parse_row(line: int, raw: Mapping[str, str | None]) -> SheetRow:
    slug = _cell(raw, "slug")
    if not _SLUG.match(slug):
        raise ValueError("INVALID_SLUG")
    try:
        lat, lng = float(_cell(raw, "lat")), float(_cell(raw, "lng"))
    except ValueError as exc:
        raise ValueError("INVALID_COORDINATES") from exc
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValueError("INVALID_COORDINATES")
    names = {loc: _cell(raw, f"name_{loc}") for loc in ("vi", "en") if _cell(raw, f"name_{loc}")}
    if not names:
        raise ValueError("NO_NAME")
    source_url = _cell(raw, "source_url")
    publisher = _cell(raw, "source_publisher")
    if not _URL.match(source_url) or not publisher:
        raise ValueError("NO_SOURCE")
    source_kind = _cell(raw, "source_kind").upper() or "REFERENCE"
    if source_kind not in SOURCE_KINDS:
        raise ValueError("INVALID_SOURCE_KIND")
    wikidata_id = _cell(raw, "wikidata_id") or None
    if wikidata_id is not None and not _QID.match(wikidata_id):
        raise ValueError("INVALID_WIKIDATA_ID")
    facts: list[SheetFact] = []
    for column, field_code in TEXT_FACTS.items():
        value = _cell(raw, column)
        if not value:
            continue
        fact_source = _cell(raw, f"{column}_source_url")
        if not _URL.match(fact_source):
            raise ValueError(f"FACT_WITHOUT_SOURCE:{field_code}")
        if field_code == "OPENING_HOURS":
            fact_value: dict[str, Any] = {"weekly": parse_opening_hours(value), "text": value}
        else:
            fact_value = {"text": value}
        facts.append(SheetFact(field_code, fact_value, fact_source))
    entrance_lat, entrance_lng = _cell(raw, "entrance_lat"), _cell(raw, "entrance_lng")
    if entrance_lat or entrance_lng:
        fact_source = _cell(raw, "entrance_source_url")
        if not _URL.match(fact_source):
            raise ValueError("FACT_WITHOUT_SOURCE:ENTRANCE_LOCATION")
        try:
            point = {"lat": float(entrance_lat), "lng": float(entrance_lng)}
        except ValueError as exc:
            raise ValueError("INVALID_COORDINATES") from exc
        facts.append(SheetFact("ENTRANCE_LOCATION", point, fact_source))
    visit: tuple[int, int, int] | None = None
    visit_cells = [_cell(raw, f"visit_minutes_{k}") for k in ("min", "suggested", "max")]
    if any(visit_cells):
        try:
            low, mid, high = (int(value) for value in visit_cells)
        except ValueError as exc:
            raise ValueError("INVALID_VISIT_MINUTES") from exc
        if not (0 < low <= mid <= high <= 600):
            raise ValueError("INVALID_VISIT_MINUTES")
        visit = (low, mid, high)
    return SheetRow(
        line=line,
        slug=slug,
        category_code=_cell(raw, "category_code").upper(),
        area_code=_cell(raw, "area_code") or None,
        lat=lat,
        lng=lng,
        names=names,
        short_descriptions={
            loc: _cell(raw, f"short_description_{loc}")
            for loc in ("vi", "en")
            if _cell(raw, f"short_description_{loc}")
        },
        descriptions={
            loc: _cell(raw, f"description_{loc}")
            for loc in ("vi", "en")
            if _cell(raw, f"description_{loc}")
        },
        source_url=source_url,
        source_publisher=publisher,
        source_kind=source_kind,
        licence=_cell(raw, "licence") or UNKNOWN_LICENCE,
        attribution=_cell(raw, "attribution") or (publisher if _cell(raw, "licence") else None),
        wikidata_id=wikidata_id,
        facts=tuple(facts),
        visit_minutes=visit,
    )


async def import_sheet(session: AsyncSession, *, city_code: str, path: Path) -> RunReport:
    text = await asyncio.to_thread(path.read_text, encoding="utf-8-sig")
    return await import_sheet_text(session, city_code=city_code, text=text, release_id=path.name)


async def import_sheet_text(
    session: AsyncSession, *, city_code: str, text: str, release_id: str
) -> RunReport:
    policy = await require_active_policy(session, PROVIDER_KEY)
    city = await load_city(session, city_code)
    rows, errors = parse_rows(text)
    report = RunReport(provider_key=PROVIDER_KEY)
    run = await start_run(
        session,
        policy,
        city.id,
        release_id=release_id,
        checksum=sha256_hex(text),
        importer_version=IMPORTER_VERSION,
    )
    if run is None:
        report.skipped_unchanged = True
        return report
    report.import_run_id = run.id
    for error in errors:
        report.record_count += 1
        report.reject(error.reason.split(":", 1)[0])
        add_record(
            session,
            run,
            upstream_id=f"line-{error.line}",
            raw_name=error.slug or f"line {error.line}",
            upstream_category=None,
            lng=0.0,
            lat=0.0,
            payload={},
            rejection_reason=error.reason,
        )
    categories = set((await session.scalars(select(Category.code))).all())
    areas_known = set(
        (await session.scalars(select(Area.code).where(Area.city_id == city.id))).all()
    )
    polygons = load_areas(city_code)
    wikidata_provider = await provider_id_for(session, WIKIDATA_KEY)
    seen: set[str] = set()
    for row in rows:
        report.record_count += 1
        payload = policy.filter_payload(row.payload())
        reason: str | None = None
        if row.slug in seen:
            reason = "DUPLICATE_SLUG"
        elif row.category_code not in categories:
            reason = "UNKNOWN_CATEGORY"
        elif row.area_code is not None and row.area_code not in areas_known:
            reason = "UNKNOWN_AREA"
        elif not await inside_city(session, city.id, row.lng, row.lat):
            reason = "OUTSIDE_CITY"
        seen.add(row.slug)
        name = row.names.get("en") or row.names.get("vi") or row.slug
        if reason is not None:
            report.reject(reason)
            add_record(
                session,
                run,
                upstream_id=row.slug if reason != "DUPLICATE_SLUG" else f"line-{row.line}",
                raw_name=name,
                upstream_category=row.category_code,
                lng=row.lng,
                lat=row.lat,
                payload=payload,
                rejection_reason=reason,
            )
            continue
        provenance = await _record_sources(session, policy.provider_id, row)
        payload[PROVENANCE_KEY] = provenance
        place_id = await place_for_identity(session, policy.provider_id, row.slug)
        if place_id is None and row.wikidata_id and wikidata_provider is not None:
            place_id = await place_for_identity(session, wikidata_provider, row.wikidata_id)
        match_state = "MATCHED"
        if place_id is None:
            place = await create_place(
                session,
                city_id=city.id,
                slug=await free_slug(session, city.id, row.slug),
                lng=row.lng,
                lat=row.lat,
                category_code=row.category_code,
                area_code=row.area_code or assign_area(polygons, row.lng, row.lat),
            )
            place_id = place.id
            match_state = "NEW_CANDIDATE"
            report.created_places += 1
        await link_identity(
            session,
            place_id=place_id,
            provider_id=policy.provider_id,
            upstream_id=row.slug,
            release=release_id,
        )
        if (
            row.wikidata_id
            and wikidata_provider is not None
            and await place_for_identity(session, wikidata_provider, row.wikidata_id) is None
        ):
            # A later Wikidata import then enriches this place instead of duplicating it.
            await link_identity(
                session,
                place_id=place_id,
                provider_id=wikidata_provider,
                upstream_id=row.wikidata_id,
                release=None,
            )
        add_record(
            session,
            run,
            upstream_id=row.slug,
            raw_name=name,
            upstream_category=row.category_code,
            lng=row.lng,
            lat=row.lat,
            payload=payload,
            place_id=place_id,
            match_state=match_state,
        )
        report.accepted += 1
    finish_run(run, report)
    await session.commit()
    return report


async def _record_sources(session: AsyncSession, provider_id: Any, row: SheetRow) -> dict[str, Any]:
    """Source + revision for the row and each fact; returns their ids for the record."""
    source = await get_or_create_source(
        session,
        data_provider_id=provider_id,
        publisher=row.source_publisher,
        source_kind=row.source_kind,
        license_code=row.licence,
        attribution_text=row.attribution,
    )
    content = {
        "name": row.names,
        "short_description": row.short_descriptions,
        "description": row.descriptions,
    }
    revision = await get_or_create_revision(
        session,
        source_id=source.id,
        locator=row.source_url,
        content_sha256=sha256_hex(canonical_json(content)),
        title=row.names.get("vi") or row.names.get("en"),
    )
    facts: dict[str, str] = {}
    for fact in row.facts:
        fact_revision = await get_or_create_revision(
            session,
            source_id=source.id,
            locator=fact.source_url,
            content_sha256=sha256_hex(canonical_json({fact.field_code: fact.value})),
            title=f"{fact.field_code} for {row.slug}",
        )
        facts[fact.field_code] = str(fact_revision.id)
    return {"source_revision_id": str(revision.id), "fact_source_revision_ids": facts}


def rejected_lines(errors: Sequence[RowError]) -> list[str]:
    return [f"line {error.line} ({error.slug or '-'}): {error.reason}" for error in errors]
