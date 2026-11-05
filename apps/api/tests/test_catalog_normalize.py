import unicodedata
import uuid

import pytest

from app.catalog.normalize import normalize_search_text
from app.catalog.reference import normalize_category_code
from app.catalog.search import InvalidCursorError, decode_cursor, encode_cursor


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Chùa Linh Ứng", "chua linh ung"),
        ("Mỹ Khê", "my khe"),
        ("Đà Nẵng", "da nang"),
        ("ĐÈO HẢI VÂN", "deo hai van"),
        ("  Phố cổ   Hội An ", "pho co hoi an"),
        ("Bà Nà Hills", "ba na hills"),
        ("Ngũ Hành Sơn", "ngu hanh son"),
        ("Cù Lao Chàm", "cu lao cham"),
        ("Chợ Hàn", "cho han"),
        ("chua linh ung", "chua linh ung"),
        # Precomposed and decomposed input normalise identically.
        (unicodedata.normalize("NFD", "Mỹ Khê"), "my khe"),
        ("Mỹ Khê", "my khe"),
    ],
)
def test_normalize_search_text(raw: str, expected: str) -> None:
    assert normalize_search_text(raw) == expected


def test_normalized_value_satisfies_alias_check() -> None:
    value = normalize_search_text("Cầu Rồng")
    assert value == value.lower() and value == "cau rong"


@pytest.mark.parametrize("raw", ["heritage", "HERITAGE", " Heritage "])
def test_category_codes_are_upper_case(raw: str) -> None:
    assert normalize_category_code(raw) == "HERITAGE"


def test_cursor_round_trip() -> None:
    place_id = uuid.uuid4()
    for key, key_type in ((2.718281828, float), ("chùa linh ứng", str)):
        cursor = encode_cursor("abc", key, place_id)
        assert "=" not in cursor
        assert decode_cursor(cursor, "abc", key_type) == (key, place_id)


@pytest.mark.parametrize("cursor", ["not-base64!!", "e30", "eyJ2IjoyfQ", ""])
def test_malformed_cursor_is_rejected(cursor: str) -> None:
    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor, "abc", float)


def test_cursor_from_other_filters_is_rejected() -> None:
    cursor = encode_cursor("abc", 1.0, uuid.uuid4())
    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor, "other", float)
    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor, "abc", str)
