"""Golden vectors and round-trip properties for the Vietnamese lunar calendar (FR-102, OQ-125)."""

from datetime import date, timedelta

import pytest

from app.planning.calendar.lunar import LunarDate, leap_month_of, lunar_to_solar, solar_to_lunar

# Tết (lunar 1/1) in Vietnam. 2030 differs from the Chinese New Year (2030-02-03) because the new
# moon falls at 23:07 UTC+7 on 2 February.
TET = {
    2020: date(2020, 1, 25),
    2021: date(2021, 2, 12),
    2022: date(2022, 2, 1),
    2023: date(2023, 1, 22),
    2024: date(2024, 2, 10),
    2025: date(2025, 1, 29),
    2026: date(2026, 2, 17),
    2027: date(2027, 2, 6),
    2028: date(2028, 1, 26),
    2029: date(2029, 2, 13),
    2030: date(2030, 2, 2),
}

# Hội An lantern nights = lunar 14th (OQ-125 pending), 2026–2027 (no leap month either year).
LANTERN_NIGHTS = {
    (2026, 1): date(2026, 3, 2),
    (2026, 2): date(2026, 4, 1),
    (2026, 3): date(2026, 4, 30),
    (2026, 4): date(2026, 5, 30),
    (2026, 5): date(2026, 6, 28),
    (2026, 6): date(2026, 7, 27),
    (2026, 7): date(2026, 8, 26),
    (2026, 8): date(2026, 9, 24),
    (2026, 9): date(2026, 10, 23),
    (2026, 10): date(2026, 11, 22),
    (2026, 11): date(2026, 12, 22),
    (2026, 12): date(2027, 1, 21),
    (2027, 1): date(2027, 2, 19),
    (2027, 2): date(2027, 3, 21),
    (2027, 3): date(2027, 4, 20),
    (2027, 4): date(2027, 5, 19),
    (2027, 5): date(2027, 6, 18),
    (2027, 6): date(2027, 7, 17),
    (2027, 7): date(2027, 8, 15),
    (2027, 8): date(2027, 9, 14),
    (2027, 9): date(2027, 10, 13),
    (2027, 10): date(2027, 11, 11),
    (2027, 11): date(2027, 12, 11),
    (2027, 12): date(2028, 1, 10),
}


@pytest.mark.parametrize(("year", "solar"), sorted(TET.items()))
def test_tet_golden(year: int, solar: date) -> None:
    assert lunar_to_solar(LunarDate(year, 1, 1)) == solar
    assert solar_to_lunar(solar) == LunarDate(year, 1, 1)
    assert solar_to_lunar(solar - timedelta(days=1)).year == year - 1


def test_tet_2026_and_2027_release_gate_vectors() -> None:
    assert lunar_to_solar(LunarDate(2026, 1, 1)) == date(2026, 2, 17)
    assert lunar_to_solar(LunarDate(2027, 1, 1)) == date(2027, 2, 6)


@pytest.mark.parametrize(("lunar_month", "solar"), sorted(LANTERN_NIGHTS.items()))
def test_lantern_night_lunar_14th(lunar_month: tuple[int, int], solar: date) -> None:
    year, month = lunar_month
    assert lunar_to_solar(LunarDate(year, month, 14)) == solar
    assert solar_to_lunar(solar) == LunarDate(year, month, 14)


@pytest.mark.parametrize(
    ("lunar", "solar"),
    [
        (LunarDate(2026, 8, 15), date(2026, 9, 25)),  # Trung Thu 2026
        (LunarDate(2027, 8, 15), date(2027, 9, 15)),  # Trung Thu 2027
        (LunarDate(2026, 1, 15), date(2026, 3, 3)),  # Rằm tháng Giêng 2026
        (LunarDate(2025, 7, 15), date(2025, 9, 6)),  # Vu Lan 2025 (after leap 6th month)
        (LunarDate(2025, 6, 1, leap=True), date(2025, 7, 25)),  # first day of leap 6th, 2025
        (LunarDate(2025, 6, 1), date(2025, 6, 25)),
        (LunarDate(2026, 3, 10), date(2026, 4, 26)),  # Giỗ Tổ Hùng Vương 2026
    ],
)
def test_known_dates(lunar: LunarDate, solar: date) -> None:
    assert lunar_to_solar(lunar) == solar
    assert solar_to_lunar(solar) == lunar


def test_vietnam_differs_from_china_by_time_zone() -> None:
    # UTC+7 vs UTC+8: well-known divergent years.
    for year, vn, cn in [
        (1985, date(1985, 1, 21), date(1985, 2, 20)),
        (2007, date(2007, 2, 17), date(2007, 2, 18)),
        (2030, date(2030, 2, 2), date(2030, 2, 3)),
    ]:
        assert lunar_to_solar(LunarDate(year, 1, 1)) == vn
        assert lunar_to_solar(LunarDate(year, 1, 1), tz=8) == cn


@pytest.mark.parametrize(
    ("year", "leap"),
    [(2020, 4), (2023, 2), (2025, 6), (2026, None), (2027, None), (2028, 5), (2033, 11)],
)
def test_leap_months(year: int, leap: int | None) -> None:
    assert leap_month_of(year) == leap


def test_invalid_lunar_dates_raise() -> None:
    with pytest.raises(ValueError):
        lunar_to_solar(LunarDate(2026, 5, 1, leap=True))  # 2026 has no leap month
    with pytest.raises(ValueError):
        lunar_to_solar(LunarDate(2025, 5, 1, leap=True))  # 2025 leap month is 6
    with pytest.raises(ValueError):
        lunar_to_solar(LunarDate(2026, 13, 1))
    short = next(
        m
        for m in range(1, 13)
        if lunar_to_solar(LunarDate(2026, m, 29)) + timedelta(days=1)
        == lunar_to_solar(LunarDate(2026, m + 1, 1) if m < 12 else LunarDate(2027, 1, 1))
    )
    with pytest.raises(ValueError):
        lunar_to_solar(LunarDate(2026, short, 30))


def test_round_trip_every_day_2020_to_2035() -> None:
    day = date(2020, 1, 1)
    previous = solar_to_lunar(day - timedelta(days=1))
    while day <= date(2035, 12, 31):
        lunar = solar_to_lunar(day)
        assert lunar_to_solar(lunar) == day
        assert 1 <= lunar.day <= 30 and 1 <= lunar.month <= 12
        # Consecutive days: day + 1 within a month, or day 1 of the next month (29/30-day months).
        if lunar.day == 1:
            assert previous.day in (29, 30)
        else:
            assert lunar.day == previous.day + 1 and lunar.month == previous.month
        previous = lunar
        day += timedelta(days=1)


def test_lunar_years_have_12_or_13_months() -> None:
    for year in range(2020, 2036):
        length = (
            lunar_to_solar(LunarDate(year + 1, 1, 1)) - lunar_to_solar(LunarDate(year, 1, 1))
        ).days
        expected = range(383, 386) if leap_month_of(year) else range(353, 356)
        assert length in expected, (year, length)
