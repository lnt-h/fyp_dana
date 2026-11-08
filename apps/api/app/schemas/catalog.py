"""Catalog response schemas (openapi.yaml 0.4.0 §Catalog, plus the 1.0 trust-label additions of
architecture §5). Field names are the contract's snake_case names."""

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Locale = Literal["vi", "en"]
TrustLevel = Literal["VERIFIED", "WEB_UNVERIFIED"]
KnowledgeState = Literal["KNOWN", "UNKNOWN", "NOT_APPLICABLE"]
Freshness = Literal["CURRENT", "STALE"]
SearchSort = Literal["relevance", "name"]


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class PageInfo(BaseModel):
    next_cursor: str | None = Field(description="Null on the last page.")


class Area(BaseModel):
    """Travel area of a city (DEC-013), e.g. ``hoi-an-old-town``; a filter, not a city."""

    code: str
    name_vi: str
    name_en: str
    sort_order: int


class City(BaseModel):
    id: uuid.UUID
    code: str
    name_vi: str
    name_en: str
    time_zone: str
    centre: GeoPoint | None = None
    areas: list[Area] = Field(default_factory=list)


class CityList(BaseModel):
    items: list[City]


class Category(BaseModel):
    code: str = Field(description="UPPER_CASE category code; lower-case is accepted on input.")
    name_vi: str
    name_en: str
    sort_order: int


class CategoryList(BaseModel):
    items: list[Category]


class Media(BaseModel):
    media_asset_id: uuid.UUID
    url: str
    width_px: int | None = None
    height_px: int | None = None
    alt_text: str | None = None
    creator: str | None = None
    license_code: str
    attribution_text: str


class Attribution(BaseModel):
    publisher: str
    attribution_text: str
    license_code: str | None = None
    homepage_url: str | None = None


class Citation(BaseModel):
    source_revision_id: uuid.UUID
    knowledge_chunk_id: uuid.UUID | None = None
    section: str | None = None
    place_fact_id: uuid.UUID | None = None
    publisher: str
    title: str | None = None
    locator: str | None = None
    verified_at: date
    trust_level: TrustLevel = "VERIFIED"


class PlaceFact(BaseModel):
    """One operational fact. UNKNOWN is never collapsed into an empty value (FR-005)."""

    place_fact_id: uuid.UUID | None = None
    field_code: str
    knowledge_state: KnowledgeState
    value: dict[str, Any] | str | None = None
    verified_at: date | None = None
    valid_until: date | None = None
    freshness: Freshness
    source: Citation | None = Field(
        default=None, description="Most recent supporting source (1.0); also listed in sources."
    )
    sources: list[Citation]


class ClosureRule(BaseModel):
    """Approved calendar rule applying to the place, its area or the city (ADR-011)."""

    id: uuid.UUID
    applies_to: Literal["PLACE", "AREA", "CITY"]
    rule_kind: str
    effect: str
    severity: Literal["BLOCKING", "WARNING"]
    params: dict[str, Any]
    note: str = Field(description="Note in the requested locale.")
    effective_from: date | None = None
    effective_to: date | None = None
    verified_at: date | None = None


DescriptionOrigin = Literal["SOURCE", "AI_SUMMARY"]


class PlaceSummary(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    slug: str
    category_code: str
    area_code: str | None = None
    name_vi: str = Field(description="Vietnamese name, always present (FR-076).")
    name: str = Field(description="Name in the requested locale.")
    name_is_source_fallback: bool = Field(
        default=False,
        description=(
            "1.0.3. True when `name` (EN locale) is the original Vietnamese proper name reused "
            "unchanged because no source gives an English name; never a machine translation."
        ),
    )
    short_description: str | None = None
    location: GeoPoint
    visit_minutes_suggested: int | None = None
    catalog_publication_id: uuid.UUID
    thumbnail: Media | None = None
    trust_level: TrustLevel = Field(
        default="VERIFIED", description="Published catalog places are always VERIFIED."
    )


class PlaceSummaryPage(PageInfo):
    items: list[PlaceSummary]


class PlaceDetail(PlaceSummary):
    name_en: str
    description: str | None = None
    description_origin: DescriptionOrigin | None = Field(
        default=None,
        description=(
            "1.0.3. SOURCE = text from a cited source (Wikipedia lead, operator sheet, Wikidata); "
            "AI_SUMMARY = summarised by Gonarra's grounded writer from the listed sources (label "
            "it in the UI). Null when there is no description."
        ),
    )
    visit_minutes_min: int | None = None
    visit_minutes_max: int | None = None
    entrance_location: GeoPoint | None = None
    area: Area | None = None
    publication_revision: int
    published_at: datetime
    facts: list[PlaceFact]
    media: list[Media] = Field(default_factory=list)
    closure_rules: list[ClosureRule] = Field(default_factory=list)
    attributions: list[Attribution] = Field(description="Every source whose data is shown.")
