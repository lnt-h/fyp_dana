"""Leg matrix service: cache first, fetch misses only (architecture §3.2 step 5, ADR-011).

``get_matrix`` returns a complete ``keys × keys`` matrix for one mode. Every ordered pair has a
:class:`Leg`; pairs that could not be measured are ``UNAVAILABLE`` with a reason — never
estimated in production (BRU-006). Provider calls reserve ``ROUTES_ELEMENTS`` first (one unit per
element); a denied reservation degrades those legs to ``UNAVAILABLE / QUOTA_EXHAUSTED``.
WALK is only requested for pairs within 2.5 km (straight line).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from sqlalchemy.exc import SQLAlchemyError

from app.ai.quota import Bucket, QuotaDecision, QuotaReservation
from app.observability import log_failure
from app.routing.google_routes import MAX_DESTINATIONS_PER_REQUEST, MAX_ORIGINS_PER_REQUEST
from app.routing.matrix_cache import (
    CachedLeg,
    MatrixCache,
    SessionFactory,
    SqlMatrixCache,
    validate_cache_key,
)
from app.routing.provider import Element, LatLng, RoutesProvider, TravelMode, haversine_m

logger = logging.getLogger("gonarra.routing")

WALK_MAX_STRAIGHT_LINE_M = 2_500.0


class LegSource(StrEnum):
    CACHE = "CACHE"
    PROVIDER = "PROVIDER"
    ESTIMATE = "ESTIMATE"  # dev/test only; never shown to travelers
    NO_ROUTE = "NO_ROUTE"  # Google reported no route (cached as UNAVAILABLE)
    WALK_TOO_FAR = "WALK_TOO_FAR"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    NOT_CONFIGURED = "NOT_CONFIGURED"


@dataclass(frozen=True, slots=True)
class Leg:
    available: bool
    distance_m: int | None
    duration_s: int | None
    source: LegSource

    @property
    def estimated(self) -> bool:
        return self.source is LegSource.ESTIMATE


@dataclass(frozen=True, slots=True)
class MatrixStats:
    pairs: int = 0
    cache_hits: int = 0
    requested_elements: int = 0
    quota_denied_elements: int = 0
    failed_elements: int = 0
    cached_writes: int = 0


@dataclass(frozen=True, slots=True)
class RouteMatrix:
    mode: TravelMode
    keys: tuple[str, ...]
    legs: Mapping[tuple[str, str], Leg]
    stats: MatrixStats = field(default_factory=MatrixStats)

    def leg(self, origin_key: str, destination_key: str) -> Leg:
        if origin_key == destination_key:
            return Leg(True, 0, 0, LegSource.CACHE)
        return self.legs[(origin_key, destination_key)]

    def duration_s(self, origin_key: str, destination_key: str) -> int | None:
        """Seconds, or ``None`` when the leg is unavailable (solver: forbidden arc)."""
        leg = self.leg(origin_key, destination_key)
        return leg.duration_s if leg.available else None

    def distance_m(self, origin_key: str, destination_key: str) -> int | None:
        leg = self.leg(origin_key, destination_key)
        return leg.distance_m if leg.available else None

    @property
    def has_estimates(self) -> bool:
        return any(leg.estimated for leg in self.legs.values())


class QuotaGate(Protocol):
    """The subset of :class:`app.ai.quota.QuotaLedger` the routing layer uses."""

    async def reserve(self, *, bucket: Bucket, amount: int = 1) -> QuotaDecision: ...

    async def commit(self, reservation: QuotaReservation) -> None: ...

    async def release(self, reservation: QuotaReservation) -> None: ...


@dataclass(frozen=True, slots=True)
class _Batch:
    origins: tuple[str, ...]
    destinations: tuple[str, ...]

    def pairs(self) -> list[tuple[str, str]]:
        return [(o, d) for o in self.origins for d in self.destinations if o != d]


def _plan_batches(misses: Sequence[tuple[str, str]], order: Mapping[str, int]) -> list[_Batch]:
    """Group missing pairs into rectangles of ≤ 25 × 25 elements.

    Origins with an identical set of missing destinations share a rectangle. An origin that is
    itself a missing destination joins with its own key added, so a cold ``n × n`` matrix is one
    rectangle (in 25 × 25 blocks) instead of ``n`` single-origin requests; the only extra billed
    elements are those self pairs (≤ one per origin), which are discarded.
    """
    by_origin: dict[str, set[str]] = {}
    for origin, destination in misses:
        by_origin.setdefault(origin, set()).add(destination)
    missing_destinations = {destination for _, destination in misses}
    groups: dict[tuple[str, ...], list[str]] = {}
    for origin in sorted(by_origin, key=order.__getitem__):
        dest_set = set(by_origin[origin])
        if origin in missing_destinations:
            dest_set.add(origin)
        dests = tuple(sorted(dest_set, key=order.__getitem__))
        groups.setdefault(dests, []).append(origin)
    batches: list[_Batch] = []
    for dests, origins in groups.items():
        for o0 in range(0, len(origins), MAX_ORIGINS_PER_REQUEST):
            for d0 in range(0, len(dests), MAX_DESTINATIONS_PER_REQUEST):
                batches.append(
                    _Batch(
                        tuple(origins[o0 : o0 + MAX_ORIGINS_PER_REQUEST]),
                        dests[d0 : d0 + MAX_DESTINATIONS_PER_REQUEST],
                    )
                )
    return batches


def _leg_from_element(element: Element, provider: RoutesProvider) -> Leg:
    if element.available:
        source = LegSource.ESTIMATE if provider.kind == "ESTIMATE" else LegSource.PROVIDER
        return Leg(True, element.distance_m, element.duration_s, source)
    if element.error:
        source = LegSource.NOT_CONFIGURED if provider.kind == "NONE" else LegSource.PROVIDER_ERROR
        return Leg(False, None, None, source)
    return Leg(False, None, None, LegSource.NO_ROUTE)


async def get_matrix(
    session_factory: SessionFactory | None,
    *,
    keys_with_coords: Mapping[str, LatLng],
    mode: TravelMode,
    ledger: QuotaGate,
    provider: RoutesProvider,
    cache: MatrixCache | None = None,
    clock: Callable[[], datetime] | None = None,
) -> RouteMatrix:
    """Complete matrix over ``keys_with_coords`` (insertion order kept) for ``mode``.

    ``cache`` defaults to :class:`SqlMatrixCache` over ``session_factory``. Never raises on
    provider, quota or cache faults; affected legs are ``UNAVAILABLE`` with a reason.
    """
    if mode not in ("DRIVE", "WALK"):
        raise ValueError(f"unsupported travel mode {mode!r}")
    keys = tuple(dict.fromkeys(validate_cache_key(k) for k in keys_with_coords))
    if cache is None:
        if session_factory is None:
            raise ValueError("session_factory or cache is required")
        cache = SqlMatrixCache(session_factory)
    now = (clock or (lambda: datetime.now(UTC)))()
    order = {key: index for index, key in enumerate(keys)}

    legs: dict[tuple[str, str], Leg] = {}
    wanted: list[tuple[str, str]] = []
    for origin in keys:
        for destination in keys:
            if origin == destination:
                continue
            if (
                mode == "WALK"
                and haversine_m(keys_with_coords[origin], keys_with_coords[destination])
                > WALK_MAX_STRAIGHT_LINE_M
            ):
                legs[(origin, destination)] = Leg(False, None, None, LegSource.WALK_TOO_FAR)
            else:
                wanted.append((origin, destination))

    cached: dict[tuple[str, str], CachedLeg] = {}
    if wanted:
        try:
            cached = await cache.read(keys, mode, now=now)
        except SQLAlchemyError:
            logger.warning("routes cache_read_failed mode=%s", mode)
    hits = 0
    misses: list[tuple[str, str]] = []
    for pair in wanted:
        hit = cached.get(pair)
        if hit is None:
            misses.append(pair)
            continue
        hits += 1
        legs[pair] = (
            Leg(True, hit.distance_m, hit.duration_s, LegSource.CACHE)
            if hit.available
            else Leg(False, None, None, LegSource.NO_ROUTE)
        )

    requested = denied = failed = written = 0
    for batch in _plan_batches(misses, order):
        n_elements = len(batch.origins) * len(batch.destinations)
        reservation: QuotaReservation | None = None
        if provider.metered:
            decision = await ledger.reserve(bucket=Bucket.ROUTES_ELEMENTS, amount=n_elements)
            if not decision.allowed or decision.reservation is None:
                for pair in batch.pairs():
                    denied += 1
                    legs[pair] = Leg(False, None, None, LegSource.QUOTA_EXHAUSTED)
                continue
            reservation = decision.reservation
        requested += n_elements
        try:
            elements = await provider.compute_matrix(
                [keys_with_coords[k] for k in batch.origins],
                [keys_with_coords[k] for k in batch.destinations],
                mode,
            )
        except Exception as exc:  # noqa: BLE001 — a provider bug must degrade, not fail the plan
            # No exception text: it may carry coordinates (precise locations are never logged).
            log_failure(logger, "routes_provider_raised", exc, mode=str(mode))
            elements = []
        finally:
            if reservation is not None:
                await ledger.commit(reservation)  # attempted ⇒ consumed

        to_cache: list[CachedLeg] = []
        for element in elements:
            if not (
                0 <= element.origin_index < len(batch.origins)
                and 0 <= element.destination_index < len(batch.destinations)
            ):
                continue
            origin = batch.origins[element.origin_index]
            destination = batch.destinations[element.destination_index]
            if origin == destination:
                continue  # self pair billed as rectangle filler; not a leg
            legs[(origin, destination)] = _leg_from_element(element, provider)
            if provider.persistable and not element.error:
                to_cache.append(
                    CachedLeg(
                        origin,
                        destination,
                        element.available,
                        element.distance_m,
                        element.duration_s,
                    )
                )
        for pair in batch.pairs():
            if pair not in legs:
                legs[pair] = Leg(False, None, None, LegSource.PROVIDER_ERROR)
            if legs[pair].source in (LegSource.PROVIDER_ERROR, LegSource.NOT_CONFIGURED):
                failed += 1
        if to_cache:
            try:
                written += await cache.write(to_cache, mode, now=now)
            except SQLAlchemyError:
                logger.warning("routes cache_write_failed mode=%s elements=%d", mode, len(to_cache))

    stats = MatrixStats(
        pairs=len(keys) * (len(keys) - 1),
        cache_hits=hits,
        requested_elements=requested,
        quota_denied_elements=denied,
        failed_elements=failed,
        cached_writes=written,
    )
    logger.info(
        "routes matrix mode=%s provider=%s pairs=%d hits=%d requested=%d denied=%d failed=%d",
        mode,
        provider.kind,
        stats.pairs,
        hits,
        requested,
        denied,
        failed,
    )
    return RouteMatrix(mode=mode, keys=keys, legs=legs, stats=stats)
