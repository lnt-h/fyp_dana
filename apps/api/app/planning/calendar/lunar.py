"""Pure-Python Vietnamese lunisolar calendar (ADR-011 0.3, FR-102, OQ-125).

Implements the astronomical algorithm published by Hồ Ngọc Đức ("Âm lịch Việt Nam"): new moons
from Meeus' series, the winter-solstice month (month 11) as anchor, and the leap month as the
first month without a major solar term. All day boundaries use UTC+7 (Vietnam), which is why the
result differs from the Chinese calendar (UTC+8) in some years (e.g. Tết 1985, 2007).

No I/O, no third-party dependencies; deterministic for identical inputs (NFR-032).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

VN_TIMEZONE_HOURS = 7.0
"""Vietnam standard time offset used for every lunar day boundary."""

_JDN_ORDINAL_OFFSET = 1_721_425  # date(2000, 1, 1).toordinal() + offset == JDN 2451545
_SYNODIC_MONTH = 29.530588853
_EPOCH_NEW_MOON = 2_415_021.076998695  # JD of the new moon of 1900-01-01
_DR = math.pi / 180.0

__all__ = [
    "VN_TIMEZONE_HOURS",
    "LunarDate",
    "leap_month_of",
    "lunar_to_solar",
    "solar_to_lunar",
]


@dataclass(frozen=True, order=True, slots=True)
class LunarDate:
    """A Vietnamese lunar date. ``leap`` is true for a day in the intercalary (nhuận) month."""

    year: int
    month: int
    day: int
    leap: bool = False


def _jdn(day: date) -> int:
    return day.toordinal() + _JDN_ORDINAL_OFFSET


def _from_jdn(jdn: int) -> date:
    return date.fromordinal(jdn - _JDN_ORDINAL_OFFSET)


def _new_moon(k: int) -> float:
    """Julian date (UT) of the k-th new moon after 1900-01-01 (Meeus, low precision)."""
    t = k / 1236.85
    t2 = t * t
    t3 = t2 * t
    jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * t2 - 0.000000155 * t3
    jd1 += 0.00033 * math.sin((166.56 + 132.87 * t - 0.009173 * t2) * _DR)
    m = 359.2242 + 29.10535608 * k - 0.0000333 * t2 - 0.00000347 * t3
    mpr = 306.0253 + 385.81691806 * k + 0.0107306 * t2 + 0.00001236 * t3
    f = 21.2964 + 390.67050646 * k - 0.0016528 * t2 - 0.00000239 * t3
    c1 = (0.1734 - 0.000393 * t) * math.sin(m * _DR) + 0.0021 * math.sin(2 * _DR * m)
    c1 = c1 - 0.4068 * math.sin(mpr * _DR) + 0.0161 * math.sin(_DR * 2 * mpr)
    c1 = c1 - 0.0004 * math.sin(_DR * 3 * mpr)
    c1 = c1 + 0.0104 * math.sin(_DR * 2 * f) - 0.0051 * math.sin(_DR * (m + mpr))
    c1 = c1 - 0.0074 * math.sin(_DR * (m - mpr)) + 0.0004 * math.sin(_DR * (2 * f + m))
    c1 = c1 - 0.0004 * math.sin(_DR * (2 * f - m)) - 0.0006 * math.sin(_DR * (2 * f + mpr))
    c1 = c1 + 0.0010 * math.sin(_DR * (2 * f - mpr)) + 0.0005 * math.sin(_DR * (2 * mpr + m))
    if t < -11:
        delta_t = 0.001 + 0.000839 * t + 0.0002261 * t2 - 0.00000845 * t3 - 0.000000081 * t * t3
    else:
        delta_t = -0.000278 + 0.000265 * t + 0.000262 * t2
    return jd1 + c1 - delta_t


def _sun_longitude(jdn: float) -> float:
    """Apparent solar longitude in radians, normalised to [0, 2π)."""
    t = (jdn - 2451545.0) / 36525
    t2 = t * t
    m = 357.52910 + 35999.05030 * t - 0.0001559 * t2 - 0.00000048 * t * t2
    l0 = 280.46645 + 36000.76983 * t + 0.0003032 * t2
    dl = (1.914600 - 0.004817 * t - 0.000014 * t2) * math.sin(_DR * m)
    dl += (0.019993 - 0.000101 * t) * math.sin(_DR * 2 * m) + 0.000290 * math.sin(_DR * 3 * m)
    longitude = (l0 + dl) * _DR
    return longitude - math.pi * 2 * math.floor(longitude / (math.pi * 2))


def _new_moon_day(k: int, tz: float) -> int:
    """Local day number (JDN) on which the k-th new moon falls."""
    return math.floor(_new_moon(k) + 0.5 + tz / 24)


def _sun_sector(day_number: int, tz: float) -> int:
    """Major solar term sector (0..11) at the start of the local day."""
    return math.floor(_sun_longitude(day_number - 0.5 - tz / 24) / math.pi * 6)


def _lunar_month_11(year: int, tz: float) -> int:
    """Day number of the start of lunar month 11 (the month containing the winter solstice)."""
    offset = _jdn(date(year, 12, 31)) - 2415021
    k = math.floor(offset / _SYNODIC_MONTH)
    new_moon = _new_moon_day(k, tz)
    if _sun_sector(new_moon, tz) >= 9:
        new_moon = _new_moon_day(k - 1, tz)
    return new_moon


def _leap_month_offset(a11: int, tz: float) -> int:
    """Offset (in months after month 11) of the leap month in a 13-month lunar year."""
    k = math.floor((a11 - _EPOCH_NEW_MOON) / _SYNODIC_MONTH + 0.5)
    i = 1
    arc = _sun_sector(_new_moon_day(k + i, tz), tz)
    while True:
        last = arc
        i += 1
        arc = _sun_sector(_new_moon_day(k + i, tz), tz)
        if arc == last or i >= 14:
            break
    return i - 1


def _leap_month_number(leap_offset: int) -> int:
    """Lunar month number repeated by the leap month ``leap_offset`` months after month 11."""
    return (leap_offset + 9) % 12 + 1


def solar_to_lunar(day: date, *, tz: float = VN_TIMEZONE_HOURS) -> LunarDate:
    """Convert a Gregorian date to the Vietnamese lunar date."""
    day_number = _jdn(day)
    k = math.floor((day_number - _EPOCH_NEW_MOON) / _SYNODIC_MONTH)
    month_start = _new_moon_day(k + 1, tz)
    if month_start > day_number:
        month_start = _new_moon_day(k, tz)
    a11 = _lunar_month_11(day.year, tz)
    b11 = a11
    if a11 >= month_start:
        lunar_year = day.year
        a11 = _lunar_month_11(day.year - 1, tz)
    else:
        lunar_year = day.year + 1
        b11 = _lunar_month_11(day.year + 1, tz)
    lunar_day = day_number - month_start + 1
    diff = math.floor((month_start - a11) / 29)
    leap = False
    lunar_month = diff + 11
    if b11 - a11 > 365:
        leap_diff = _leap_month_offset(a11, tz)
        if diff >= leap_diff:
            lunar_month = diff + 10
            leap = diff == leap_diff
    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and diff < 4:
        lunar_year -= 1
    return LunarDate(year=lunar_year, month=lunar_month, day=lunar_day, leap=leap)


def leap_month_of(lunar_year: int, *, tz: float = VN_TIMEZONE_HOURS) -> int | None:
    """Number of the month repeated as a leap month in ``lunar_year``, or ``None``."""
    for a11_year in (lunar_year - 1, lunar_year):
        a11 = _lunar_month_11(a11_year, tz)
        b11 = _lunar_month_11(a11_year + 1, tz)
        if b11 - a11 <= 365:
            continue
        offset = _leap_month_offset(a11, tz)
        month = _leap_month_number(offset)
        # Months 11 and 12 (offset ≤ 2) belong to the lunar year that starts after a11's year.
        owner_year = a11_year if month >= 11 else a11_year + 1
        if owner_year == lunar_year:
            return month
    return None


def lunar_to_solar(lunar: LunarDate, *, tz: float = VN_TIMEZONE_HOURS) -> date:
    """Convert a Vietnamese lunar date to the Gregorian date.

    Raises ``ValueError`` when the lunar date does not exist (a leap flag on a month that is not
    the year's leap month, or day 30 of a 29-day month).
    """
    if not 1 <= lunar.month <= 12 or not 1 <= lunar.day <= 30:
        raise ValueError(f"invalid lunar date {lunar}")
    if lunar.month < 11:
        a11 = _lunar_month_11(lunar.year - 1, tz)
        b11 = _lunar_month_11(lunar.year, tz)
    else:
        a11 = _lunar_month_11(lunar.year, tz)
        b11 = _lunar_month_11(lunar.year + 1, tz)
    offset = lunar.month - 11
    if offset < 0:
        offset += 12
    if b11 - a11 > 365:
        leap_offset = _leap_month_offset(a11, tz)
        leap_month = _leap_month_number(leap_offset)
        if lunar.leap and lunar.month != leap_month:
            raise ValueError(f"lunar year {lunar.year} has no leap month {lunar.month}")
        if lunar.leap or offset >= leap_offset:
            offset += 1
    elif lunar.leap:
        raise ValueError(f"lunar year {lunar.year} has no leap month")
    k = math.floor(0.5 + (a11 - _EPOCH_NEW_MOON) / _SYNODIC_MONTH)
    month_start = _new_moon_day(k + offset, tz)
    result = _from_jdn(month_start + lunar.day - 1)
    if solar_to_lunar(result, tz=tz) != lunar:
        raise ValueError(f"lunar month of {lunar} has fewer than {lunar.day} days")
    return result
