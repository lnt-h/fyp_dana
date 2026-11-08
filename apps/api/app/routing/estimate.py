"""Haversine estimate provider — TESTS, LOCAL DEVELOPMENT AND OWNER DEMO ONLY.

BRU-006: no straight-line or model value is ever accepted as a measured leg. This provider exists
so the planner can be exercised without a Google Maps key. It refuses to be constructed outside
``development``, ``test`` and ``demo`` (``Settings.estimates_allowed``), is not metered and is
never persisted to ``routes_matrix_cache``; legs from it are marked ``estimated`` by the matrix
service and carry ``estimated=true`` plus a ``LEG_ESTIMATED`` notice in the API.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.config import Settings
from app.routing.provider import (
    Element,
    EstimateNotAllowedError,
    LatLng,
    ProviderKind,
    ProviderTravelMode,
    haversine_m,
)

# Urban Đà Nẵng: road distance ≈ 1.35 × straight line; conservative mode speeds.
DETOUR_FACTOR = 1.35
SPEED_M_PER_S: dict[str, float] = {
    "DRIVE": 25_000 / 3600,
    "TWO_WHEELER": 22_000 / 3600,
    "WALK": 4_500 / 3600,
}


class EstimateProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.estimates_allowed:
            raise EstimateNotAllowedError(
                f"routes estimate provider cannot run in {settings.environment}"
            )

    @property
    def kind(self) -> ProviderKind:
        return "ESTIMATE"

    @property
    def metered(self) -> bool:
        return False

    @property
    def persistable(self) -> bool:
        return False

    async def compute_matrix(
        self,
        origins: Sequence[LatLng],
        destinations: Sequence[LatLng],
        mode: ProviderTravelMode,
    ) -> list[Element]:
        speed = SPEED_M_PER_S[mode]
        elements: list[Element] = []
        for oi, origin in enumerate(origins):
            for di, destination in enumerate(destinations):
                distance = round(haversine_m(origin, destination) * DETOUR_FACTOR)
                elements.append(Element(oi, di, distance, round(distance / speed), available=True))
        return elements
