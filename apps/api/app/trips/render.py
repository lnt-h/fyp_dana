"""Render stored snapshots into API ``ItineraryDay`` / ``Stop`` / ``Leg`` with trust labels.

Names and coordinates come from the pinned publication (VERIFIED) or the web candidate
(WEB_UNVERIFIED); nothing is invented. Local planned times become ``date-time`` in the city's time
zone from the trip start date (unknown start date → null times).
"""

import re
import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.schemas.trips import GeoPoint, ItineraryDay, Leg, Locale, Stop, Trip, WebSource
from app.trips.repository import CandidateInfo, PublicationInfo, TripStore
from app.trips.snapshot import PlanSnapshot

_POINT = re.compile(r"POINT\s*\(\s*(-?[0-9.eE+-]+)\s+(-?[0-9.eE+-]+)\s*\)")
DEFAULT_TIME_ZONE = "Asia/Ho_Chi_Minh"


def parse_point(ewkt: str | None) -> GeoPoint | None:
    """``SRID=4326;POINT(lng lat)`` → GeoPoint (PostGIS order is longitude first)."""
    if not ewkt:
        return None
    match = _POINT.search(ewkt)
    if match is None:
        return None
    return GeoPoint(longitude=float(match.group(1)), latitude=float(match.group(2)))


def local_time(value: time) -> str:
    return value.strftime("%H:%M")


def _at(start: date | None, day_index: int, value: time, zone: ZoneInfo) -> datetime | None:
    if start is None:
        return None
    return datetime.combine(start + timedelta(days=day_index - 1), value, tzinfo=zone)


def trip_schema(trip: object) -> Trip:
    return Trip.model_validate(trip, from_attributes=True)


async def render_days(
    store: TripStore,
    snapshot: PlanSnapshot,
    *,
    locale: Locale,
    start_date: date | None,
    time_zone: str = DEFAULT_TIME_ZONE,
    trip_day_ids: dict[int, uuid.UUID] | None = None,
) -> list[ItineraryDay]:
    stops = snapshot.all_stops()
    publications = await store.publications(
        {s.catalog_publication_id for s in stops if s.catalog_publication_id is not None}
    )
    candidates = await store.candidates(
        {s.web_place_candidate_id for s in stops if s.web_place_candidate_id is not None}
    )
    zone = ZoneInfo(time_zone)
    days: list[ItineraryDay] = []
    for day in snapshot.days:
        rendered: list[Stop] = []
        for stop in day.stops:
            common: dict[str, object] = {
                "id": stop.id,
                "trust_level": stop.trust_level,
                "ordinal": stop.ordinal,
                "planned_arrival": _at(start_date, day.day_index, stop.planned_arrival, zone),
                "planned_departure": _at(start_date, day.day_index, stop.planned_departure, zone),
                "visit_minutes": stop.visit_minutes,
                "is_locked": stop.is_locked,
                "rationale": stop.rationale,
                "conflicts": stop.conflicts,
            }
            if stop.trust_level == "VERIFIED":
                assert stop.catalog_publication_id is not None
                publication = publications.get(stop.catalog_publication_id)
                rendered.append(_verified_stop(common, stop.place_id, publication, locale))
            else:
                assert stop.web_place_candidate_id is not None
                candidate = candidates.get(stop.web_place_candidate_id)
                rendered.append(_web_stop(common, stop.web_place_candidate_id, candidate, locale))
        legs = [
            Leg(
                from_stop_id=leg.from_stop_id,
                to_stop_id=leg.to_stop_id,
                travel_mode=leg.travel_mode,
                availability=leg.availability,
                distance_m=leg.distance_m,
                duration_s=leg.duration_s,
                measured_at=leg.measured_at,
                estimated=leg.estimated,
                conflicts=leg.conflicts,
            )
            for leg in day.legs
        ]
        days.append(
            ItineraryDay(
                trip_day_id=(trip_day_ids or {}).get(day.day_index),
                day_index=day.day_index,
                day_window_start=local_time(day.day_window_start),
                day_window_end=local_time(day.day_window_end),
                stops=rendered,
                legs=legs,
            )
        )
    return days


def _verified_stop(
    common: dict[str, object],
    place_id: uuid.UUID | None,
    publication: PublicationInfo | None,
    locale: Locale,
) -> Stop:
    if publication is None:
        # The FK pins the publication, so this only happens for a dangling preview snapshot.
        return Stop.model_validate(
            {
                **common,
                "place_id": place_id,
                "catalog_publication_id": None,
                "name_vi": "",
                "name": "",
                "location": None,
            }
        )
    return Stop.model_validate(
        {
            **common,
            "place_id": publication.place_id,
            "catalog_publication_id": publication.id,
            "name_vi": publication.name_vi,
            "name": publication.name_en if locale == "en" else publication.name_vi,
            "location": parse_point(publication.location),
        }
    )


def candidate_names(candidate: CandidateInfo, locale: Locale) -> tuple[str, str, str]:
    """(name_vi, name_en, name for locale); falls back to the extracted ``name``."""
    name_vi = candidate.name_vi or candidate.name
    name_en = candidate.name_en or candidate.name
    return name_vi, name_en, name_en if locale == "en" else name_vi


def _web_stop(
    common: dict[str, object],
    candidate_id: uuid.UUID,
    candidate: CandidateInfo | None,
    locale: Locale,
) -> Stop:
    if candidate is None:
        return Stop.model_validate(
            {
                **common,
                "place_id": None,
                "catalog_publication_id": None,
                "name_vi": "",
                "name": "",
                "location": None,
            }
        )
    name_vi, _, name = candidate_names(candidate, locale)
    return Stop.model_validate(
        {
            **common,
            "place_id": None,
            "catalog_publication_id": None,
            "web_source": WebSource(
                url=candidate.source_url,
                fetched_at=candidate.fetched_at,
                candidate_id=candidate_id,
            ),
            "name_vi": name_vi,
            "name": name,
            "location": parse_point(candidate.location),
        }
    )
