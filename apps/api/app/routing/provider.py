"""Routes provider seam (ADR-011, ADR-006, BRU-006).

Every distance/duration shown to a traveler comes from Google Routes. This module defines the
provider Protocol and the two non-Google implementations that are safe to construct anywhere:

* :class:`NoRoutesProvider` — no key configured: every element is UNAVAILABLE (Plan Health then
  reports ``LEG_UNAVAILABLE``). Production-safe; nothing is estimated.
* :class:`app.routing.estimate.EstimateProvider` — haversine estimate for tests and local
  development only; refuses to exist when ``Settings.environment == "production"``.

:func:`select_provider` is the only place that decides which one the app uses.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

from app.config import Settings

if TYPE_CHECKING:
    import httpx

# Contract modes (cache CHECK allows WALK and DRIVE). TWO_WHEELER is accepted by the Google client
# only; the matrix service and cache never use it.
TravelMode = Literal["DRIVE", "WALK"]
ProviderTravelMode = Literal["DRIVE", "WALK", "TWO_WHEELER"]

ProviderKind = Literal["GOOGLE", "NONE", "ESTIMATE"]


@dataclass(frozen=True, slots=True)
class LatLng:
    lat: float
    lng: float

    def __post_init__(self) -> None:
        if not (-90.0 <= self.lat <= 90.0 and -180.0 <= self.lng <= 180.0):
            raise ValueError("coordinates out of range")


@dataclass(frozen=True, slots=True)
class Element:
    """One origin→destination measurement.

    ``available`` is False when no route exists *or* the element could not be measured. ``error``
    distinguishes the latter (HTTP failure, provider not configured): such elements are never
    cached, so a transient fault does not poison the 30-day cache.
    """

    origin_index: int
    destination_index: int
    distance_m: int | None
    duration_s: int | None
    available: bool
    error: bool = False


class RoutesProvider(Protocol):
    """Computes a distance/duration matrix. Implementations never raise on provider faults;
    failed elements come back ``available=False, error=True``."""

    @property
    def kind(self) -> ProviderKind: ...

    @property
    def metered(self) -> bool:
        """True when calls consume the ``ROUTES_ELEMENTS`` quota."""
        ...

    @property
    def persistable(self) -> bool:
        """True when results may be written to ``routes_matrix_cache`` (Google data only)."""
        ...

    async def compute_matrix(
        self,
        origins: Sequence[LatLng],
        destinations: Sequence[LatLng],
        mode: ProviderTravelMode,
    ) -> list[Element]: ...


class NoRoutesProvider:
    """No routing provider configured: every leg is UNAVAILABLE (never estimated)."""

    @property
    def kind(self) -> ProviderKind:
        return "NONE"

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
        return [
            Element(o, d, None, None, available=False, error=True)
            for o in range(len(origins))
            for d in range(len(destinations))
        ]


EARTH_RADIUS_M = 6_371_008.8


def haversine_m(a: LatLng, b: LatLng) -> float:
    """Great-circle distance in metres. Used to gate WALK requests and by the dev estimator;
    never shown to travelers."""
    phi1, phi2 = math.radians(a.lat), math.radians(b.lat)
    dphi = phi2 - phi1
    dlmb = math.radians(b.lng - a.lng)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(h)))


class EstimateNotAllowedError(RuntimeError):
    """Raised when the estimate provider is requested in production."""


def select_provider(
    settings: Settings,
    *,
    estimate_enabled: bool = False,
    client: httpx.AsyncClient | None = None,
) -> RoutesProvider:
    """Pick the Routes provider for this process.

    1. Google Routes when ``google_maps_api_key`` is configured.
    2. Otherwise, when ``estimate_enabled`` (setting ``routes_estimate_enabled`` /
       ``GONARRA_ROUTES_ESTIMATE_ENABLED``) and the environment is not production, the haversine
       :class:`EstimateProvider` for local development.
    3. Otherwise :class:`NoRoutesProvider` (all legs UNAVAILABLE).

    Asking for estimates in production is a misconfiguration and raises, so it cannot ship.
    """
    if estimate_enabled and settings.environment == "production":
        raise EstimateNotAllowedError("routes estimate provider cannot be enabled in production")
    if settings.google_maps_api_key is not None:
        from app.routing.google_routes import GoogleRoutesProvider

        return GoogleRoutesProvider(settings.google_maps_api_key, client=client)
    if estimate_enabled:
        from app.routing.estimate import EstimateProvider

        return EstimateProvider(settings)
    return NoRoutesProvider()
