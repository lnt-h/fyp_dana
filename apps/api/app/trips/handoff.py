"""Deterministic booking-partner deep links (FR-064, DEC-002). No provider call, nothing stored.

URL shapes are partner public search URLs with the city, trip dates and (for activities) the stop
name filled in. They are not affiliate links and have not been verified against partner
documentation; adjust :data:`PARTNERS` when a partner changes its query parameters.
"""

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final
from urllib.parse import quote, urlencode

from app.errors import validation_failed
from app.schemas.trips import HandoffKind, HandoffLink, Locale, PartnerKey


@dataclass(frozen=True)
class Partner:
    key: PartnerKey
    display_name: str
    kind: HandoffKind


PARTNERS: Final[dict[PartnerKey, Partner]] = {
    "agoda": Partner("agoda", "Agoda", "STAY"),
    "booking_com": Partner("booking_com", "Booking.com", "STAY"),
    "klook": Partner("klook", "Klook", "ACTIVITY"),
    "twelve_go": Partner("twelve_go", "12Go", "TRANSPORT"),
}
DEFAULT_PARTNER: Final[dict[HandoffKind, PartnerKey]] = {
    "STAY": "agoda",
    "ACTIVITY": "klook",
    "TRANSPORT": "twelve_go",
}


@dataclass(frozen=True)
class HandoffTrip:
    city_id: uuid.UUID
    city_name_en: str
    city_code: str
    start_date: date
    day_count: int


def stay_dates(start: date, day_count: int) -> tuple[date, date]:
    """(check-in, check-out): a trip of N days spans N-1 nights, at least one night."""
    return start, start + timedelta(days=max(day_count - 1, 1))


def build_handoff_link(
    *,
    kind: HandoffKind,
    partner_key: PartnerKey | None,
    trip: HandoffTrip,
    locale: Locale,
    activity_name: str | None = None,
) -> HandoffLink:
    key = partner_key or DEFAULT_PARTNER[kind]
    partner = PARTNERS[key]
    if partner.kind != kind:
        raise validation_failed(
            "validation_error",
            f"Partner {key} does not serve {kind}",
            fields=[{"location": ["query", "partner"]}],
        )
    end_date = trip.start_date + timedelta(days=trip.day_count - 1)
    check_in, check_out = stay_dates(trip.start_date, trip.day_count)
    city = trip.city_name_en
    if key == "agoda":
        query = urlencode(
            {
                "textToSearch": city,
                "checkIn": check_in.isoformat(),
                "checkOut": check_out.isoformat(),
                "rooms": 1,
                "adults": 2,
                "locale": "vi-vn" if locale == "vi" else "en-us",
            }
        )
        url = f"https://www.agoda.com/search?{query}"
    elif key == "booking_com":
        query = urlencode(
            {
                "ss": city,
                "checkin": check_in.isoformat(),
                "checkout": check_out.isoformat(),
                "group_adults": 2,
                "no_rooms": 1,
                "lang": "vi" if locale == "vi" else "en-gb",
            }
        )
        url = f"https://www.booking.com/searchresults.html?{query}"
    elif key == "klook":
        if not activity_name:
            raise validation_failed(
                "validation_error",
                "stop_id is required for ACTIVITY",
                fields=[{"location": ["query", "stop_id"]}],
            )
        prefix = "vi" if locale == "vi" else "en-US"
        url = (
            f"https://www.klook.com/{prefix}/search/result/?"
            f"{urlencode({'query': f'{activity_name} {city}'})}"
        )
    else:
        lang = "vi" if locale == "vi" else "en"
        url = (
            f"https://12go.asia/{lang}/travel/{quote(trip.city_code)}"
            f"?{urlencode({'date': trip.start_date.isoformat()})}"
        )
    return HandoffLink(
        kind=kind,
        partner_key=key,
        partner_display_name=partner.display_name,
        url=url,
        city_id=trip.city_id,
        start_date=trip.start_date,
        end_date=end_date,
    )
