"""Traveler preference schemas (openapi.yaml 0.4.0 ``Preferences`` / ``PreferencesWrite``)."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Locale = Literal["vi", "en"]
Pace = Literal["RELAXED", "BALANCED", "PACKED"]
TravelMode = Literal["WALK", "DRIVE"]
LocalTime = Annotated[
    str, Field(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$", examples=["08:00"])
]


class Preferences(BaseModel):
    locale: Locale
    pace: Pace | None = None
    interest_category_codes: list[str]
    allowed_modes: list[TravelMode]
    day_start_time: LocalTime | None = None
    day_end_time: LocalTime | None = None
    ai_notice_acknowledged_at: datetime | None = None
    updated_at: datetime | None = None


class PreferencesWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locale: Locale
    pace: Pace | None = None
    interest_category_codes: list[str] = Field(max_length=20)
    allowed_modes: list[TravelMode] = Field(min_length=1)
    day_start_time: LocalTime | None = None
    day_end_time: LocalTime | None = None
    ai_notice_acknowledged: bool = Field(
        default=False,
        description="Set true once the FR-074 notice is shown; the server stamps the time.",
    )

    @model_validator(mode="after")
    def _check(self) -> "PreferencesWrite":
        if len(set(self.allowed_modes)) != len(self.allowed_modes):
            raise ValueError("allowed_modes must not repeat a mode")
        if (
            self.day_start_time is not None
            and self.day_end_time is not None
            and self.day_start_time >= self.day_end_time
        ):
            raise ValueError("day_start_time must be before day_end_time")
        return self
