"""Operator (``/v1/admin``) request and response schemas.

DEC-022 withdrew the curator review surfaces: content is published by the automated gate
(``app.curation.auto_publish``). What remains is the owner's emergency takedown (API-037) and the
release-gate summary (API-042), mirroring ``docs/04-design/api/openapi.yaml`` 1.0.1.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PublicationState = Literal["PUBLISHED", "SUPERSEDED", "WITHDRAWN"]


class _Write(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CatalogPublication(BaseModel):
    id: uuid.UUID
    place_id: uuid.UUID
    city_id: uuid.UUID
    publication_revision: int
    state: PublicationState
    published_by_account_id: uuid.UUID | None
    published_at: datetime
    state_changed_at: datetime | None
    state_reason: str | None
    corpus_revision: int | None = None


class UnpublishRequest(_Write):
    state_reason: str = Field(min_length=1, max_length=500)


class AreaCount(BaseModel):
    area_code: str
    published_count: int = Field(ge=0)


class CitySummary(BaseModel):
    city_id: uuid.UUID
    code: str
    is_enabled: bool
    published_count: int = Field(ge=0)
    candidate_count: int = Field(ge=0)
    pending_web_candidate_count: int = Field(ge=0)
    published_by_area: list[AreaCount]


class CitySummaryList(BaseModel):
    items: list[CitySummary]
