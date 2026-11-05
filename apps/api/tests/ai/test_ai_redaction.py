import uuid

import pytest
from pydantic import ValidationError

from app.ai.redaction import (
    CandidateDto,
    RedactionError,
    ensure_clean,
    find_sensitive,
    redact_candidates,
    redact_text,
)

PLACE_ID = uuid.UUID("2f6c1c9e-3c1a-4d55-9b7e-0a1b2c3d4e5f")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Liên hệ tôi qua lan.nguyen@gmail.com nhé", "Liên hệ tôi qua [EMAIL] nhé"),
        ("Gọi 0905 123 456 khi tới", "Gọi [PHONE] khi tới"),
        ("SĐT: +84 905-123-456", "SĐT: [PHONE]"),
        ("Khách sạn (+84) 236 3822 123", "Khách sạn [PHONE]"),
        ("số bàn 0236.3822.123", "số bàn [PHONE]"),
        (
            "tài khoản user_2abcDEF123ghi và sess_9XyZ12345678",
            "tài khoản [ACCOUNT_ID] và [ACCOUNT_ID]",
        ),
        ("id 2f6c1c9e-3c1a-4d55-9b7e-0a1b2c3d4e5f", "id [ID]"),
        ("Tôi đang ở 16.0544, 108.2022 gần cầu Rồng", "Tôi đang ở [COORDINATES] gần cầu Rồng"),
        ("vị trí lat: 15.8801 lng=108.338", "vị trí [COORDINATES] [COORDINATES]"),
        ("vĩ độ 16,0544", "[COORDINATES]"),
        (
            "xem https://maps.google.com/@16.0544,108.2022,17z",
            "xem [URL]",
        ),
        (
            "link https://example.com/cb?access_token=abc123&x=1 ok",
            "link [URL] ok",
        ),
    ],
)
def test_redact_text(raw: str, expected: str) -> None:
    assert redact_text(raw) == expected
    assert find_sensitive(expected) == []


@pytest.mark.parametrize(
    "safe",
    [
        "Đi Hội An 2 ngày, thích ẩm thực và chùa, ngân sách 1.500.000 đồng",
        "Vé 50.000, 100.000 đồng; đánh giá 4.5, 3.0",
        "Mở cửa 08:00-17:00 ngày 2026-11-10",
        "https://vi.wikipedia.org/wiki/Ch%C3%B9a_Linh_%E1%BB%A8ng?lang=vi",
        "Đi bộ một đoạn long 2.5 km dọc sông Hàn",
    ],
)
def test_redact_text_keeps_ordinary_travel_text(safe: str) -> None:
    assert redact_text(safe) == safe
    assert find_sensitive(safe) == []


def test_redaction_is_deterministic_and_idempotent() -> None:
    raw = "email a@b.vn, gọi 0912345678, ở 16.0611, 108.2233"
    once = redact_text(raw)
    assert once == redact_text(raw) == redact_text(once)


def test_ensure_clean_fails_closed_but_allows_catalog_ids() -> None:
    prompt = f'{{"place_id": "{PLACE_ID}", "name_vi": "Chùa Linh Ứng"}}'
    assert ensure_clean(prompt, allowed_ids=[PLACE_ID]) == prompt
    with pytest.raises(RedactionError) as excinfo:
        ensure_clean(prompt + " account 0905123456 " + str(uuid.uuid4()), allowed_ids=[PLACE_ID])
    assert excinfo.value.kinds == ("phone", "uuid")


def test_redact_candidates_strips_location_contact_and_account() -> None:
    raw = {
        "place_id": str(PLACE_ID),
        "name_vi": "Chùa Linh Ứng Bãi Bụt",
        "name_en": "Linh Ung Pagoda",
        "category_code": "TEMPLE",
        "area_code": "son-tra",
        "summary": "Tượng Quán Thế Âm cao 67 m. Hotline 0236 3843 999.",
        "open_windows": ["2026-11-10 06:00-21:00"],
        "tags": ["view", "lienhe@chua.vn"],
        "account_id": str(uuid.uuid4()),
        "lat": 16.1003,
        "lng": 108.2778,
        "location": "POINT(108.2778 16.1003)",
        "address": "Hoàng Sa, Thọ Quang, Sơn Trà, Đà Nẵng",
        "phone": "0236 3843 999",
        "email": "lienhe@chua.vn",
        "website": "https://chualinhung.vn",
    }
    (dto,) = redact_candidates([raw])
    dumped = dto.model_dump()
    assert set(dumped) == {
        "place_id",
        "name_vi",
        "name_en",
        "category_code",
        "area_code",
        "summary",
        "open_windows",
        "tags",
    }
    assert dto.place_id == PLACE_ID
    assert dto.summary == "Tượng Quán Thế Âm cao 67 m. Hotline [PHONE]."
    assert dto.tags == ["view", "[EMAIL]"]
    assert dto.open_windows == ["2026-11-10 06:00-21:00"]
    assert find_sensitive(dto.model_dump_json(), allowed_ids=[PLACE_ID]) == []


def test_candidate_dto_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        CandidateDto(  # type: ignore[call-arg]
            place_id=PLACE_ID,
            name_vi="Cầu Rồng",
            name_en="Dragon Bridge",
            category_code="LANDMARK",
            lat=16.06,
        )
    dto = CandidateDto(
        place_id=PLACE_ID, name_vi="Cầu Rồng", name_en="Dragon Bridge", category_code="LANDMARK"
    )
    assert redact_candidates([dto])[0] == dto
