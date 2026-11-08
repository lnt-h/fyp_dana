"""Google Routes API v2 ``computeRouteMatrix`` client (ADR-011, ADR-006).

Only coordinates of catalog places, web candidates and fixed anchors are sent — never traveler
GPS, account IDs or free text (BR-046). The API key travels in ``X-Goog-Api-Key`` and is never
logged. Requests are split into blocks of at most 25 origins × 25 destinations (625 elements,
the TRAFFIC_UNAWARE limit, 50 waypoints). A failed block yields ``error=True`` elements instead
of raising; the caller decides how to degrade.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from typing import Any

import httpx
from pydantic import SecretStr

from app.routing.provider import Element, LatLng, ProviderKind, ProviderTravelMode

logger = logging.getLogger("gonarra.routing")

COMPUTE_ROUTE_MATRIX_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
FIELD_MASK = "originIndex,destinationIndex,distanceMeters,duration,condition"
MAX_ORIGINS_PER_REQUEST = 25
MAX_DESTINATIONS_PER_REQUEST = 25
DEFAULT_TIMEOUT_S = 10.0

_DURATION_RE = re.compile(r"^(\d+)(?:\.\d+)?s$")


def _waypoint(point: LatLng) -> dict[str, Any]:
    return {"waypoint": {"location": {"latLng": {"latitude": point.lat, "longitude": point.lng}}}}


def _parse_duration(value: object) -> int | None:
    if value is None:
        return 0  # proto3 omits zero values
    if not isinstance(value, str):
        return None
    match = _DURATION_RE.match(value)
    return int(match.group(1)) if match else None


def build_request_body(
    origins: Sequence[LatLng], destinations: Sequence[LatLng], mode: ProviderTravelMode
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "origins": [_waypoint(p) for p in origins],
        "destinations": [_waypoint(p) for p in destinations],
        "travelMode": mode,
    }
    # routingPreference is only valid for DRIVE and TWO_WHEELER; WALK rejects it.
    if mode != "WALK":
        body["routingPreference"] = "TRAFFIC_UNAWARE"
    return body


class GoogleRoutesProvider:
    def __init__(
        self,
        api_key: SecretStr | str,
        *,
        client: httpx.AsyncClient | None = None,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._api_key = api_key if isinstance(api_key, SecretStr) else SecretStr(api_key)
        self._client = client
        self._timeout_s = timeout_s

    @property
    def kind(self) -> ProviderKind:
        return "GOOGLE"

    @property
    def metered(self) -> bool:
        return True

    @property
    def persistable(self) -> bool:
        return True

    async def compute_matrix(
        self,
        origins: Sequence[LatLng],
        destinations: Sequence[LatLng],
        mode: ProviderTravelMode,
    ) -> list[Element]:
        if not origins or not destinations:
            return []
        if self._client is not None:
            return await self._compute_all(self._client, origins, destinations, mode)
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            return await self._compute_all(client, origins, destinations, mode)

    async def _compute_all(
        self,
        client: httpx.AsyncClient,
        origins: Sequence[LatLng],
        destinations: Sequence[LatLng],
        mode: ProviderTravelMode,
    ) -> list[Element]:
        elements: list[Element] = []
        denied = False
        for o0 in range(0, len(origins), MAX_ORIGINS_PER_REQUEST):
            block_o = origins[o0 : o0 + MAX_ORIGINS_PER_REQUEST]
            for d0 in range(0, len(destinations), MAX_DESTINATIONS_PER_REQUEST):
                block_d = destinations[d0 : d0 + MAX_DESTINATIONS_PER_REQUEST]
                if denied:
                    # 401/403 (key, API not enabled, billing): every further block would fail
                    # the same way, so skip the requests and the repeated warning.
                    block = _all_failed(len(block_o), len(block_d))
                else:
                    block, denied = await self._compute_block(client, block_o, block_d, mode)
                for element in block:
                    elements.append(
                        Element(
                            origin_index=element.origin_index + o0,
                            destination_index=element.destination_index + d0,
                            distance_m=element.distance_m,
                            duration_s=element.duration_s,
                            available=element.available,
                            error=element.error,
                        )
                    )
        return elements

    async def _compute_block(
        self,
        client: httpx.AsyncClient,
        origins: Sequence[LatLng],
        destinations: Sequence[LatLng],
        mode: ProviderTravelMode,
    ) -> tuple[list[Element], bool]:
        """Elements of one block and whether the key was refused (HTTP 401/403)."""
        headers = {
            "X-Goog-Api-Key": self._api_key.get_secret_value(),
            "X-Goog-FieldMask": FIELD_MASK,
            "Content-Type": "application/json",
        }
        try:
            response = await client.post(
                COMPUTE_ROUTE_MATRIX_URL,
                json=build_request_body(origins, destinations, mode),
                headers=headers,
                timeout=self._timeout_s,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # Never log the key or coordinates; status/class only.
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            logger.warning(
                "routes matrix_failed mode=%s elements=%d error=%s status=%s",
                mode,
                len(origins) * len(destinations),
                type(exc).__name__,
                status,
            )
            return _all_failed(len(origins), len(destinations)), status in (401, 403)
        if not isinstance(payload, list):
            logger.warning("routes matrix_failed mode=%s error=unexpected_payload", mode)
            return _all_failed(len(origins), len(destinations)), False
        return _parse_elements(payload, len(origins), len(destinations)), False


def _all_failed(n_origins: int, n_destinations: int) -> list[Element]:
    return [
        Element(o, d, None, None, available=False, error=True)
        for o in range(n_origins)
        for d in range(n_destinations)
    ]


def _parse_elements(payload: list[Any], n_origins: int, n_destinations: int) -> list[Element]:
    """Map the response onto a complete block; missing or malformed elements are errors."""
    found: dict[tuple[int, int], Element] = {}
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        # proto3 omits zero-valued indexes.
        o = raw.get("originIndex", 0)
        d = raw.get("destinationIndex", 0)
        if not (isinstance(o, int) and isinstance(d, int)):
            continue
        if not (0 <= o < n_origins and 0 <= d < n_destinations):
            continue
        condition = raw.get("condition")
        if condition == "ROUTE_EXISTS":
            distance = raw.get("distanceMeters", 0)
            duration = _parse_duration(raw.get("duration"))
            if isinstance(distance, int) and distance >= 0 and duration is not None:
                found[(o, d)] = Element(o, d, distance, duration, available=True)
            else:
                found[(o, d)] = Element(o, d, None, None, available=False, error=True)
        elif condition == "ROUTE_NOT_FOUND":
            found[(o, d)] = Element(o, d, None, None, available=False)
        else:
            # ROUTE_MATRIX_ELEMENT_CONDITION_UNSPECIFIED or a per-element error status.
            found[(o, d)] = Element(o, d, None, None, available=False, error=True)
    return [
        found.get((o, d), Element(o, d, None, None, available=False, error=True))
        for o in range(n_origins)
        for d in range(n_destinations)
    ]
