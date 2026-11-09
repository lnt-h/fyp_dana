import uuid

import pytest

from app.agents.schemas import Pick, Rationale, RationaleSet, SelectionResult
from app.agents.validators import (
    extract_json_object,
    fact_like,
    fold,
    normalise_url,
    quote_in_text,
    rule_based_selection,
    validate_rationales,
    validate_selection,
)

A, B, C = (uuid.UUID(int=i, version=4) for i in (1, 2, 3))


def test_quote_matching_tolerates_whitespace_case_and_typography() -> None:
    text = "Giờ mở cửa:  7h – 17h\nhằng ngày. “Đẹp” lắm."
    assert quote_in_text("giờ mở cửa: 7h - 17h hằng ngày.", text)
    assert quote_in_text('"Đẹp" lắm', text)
    assert not quote_in_text("Giờ mở cửa: 8h - 17h", text)
    assert not quote_in_text("ab", text)  # too short to count as a quote


def test_fold_and_url_normalisation() -> None:
    assert fold("Hội An – Đà Nẵng!") == "hoi an da nang"
    assert normalise_url("HTTPS://Example.VN:443/a/#frag") == "https://example.vn/a"


def test_extract_json_object_from_fenced_or_prose() -> None:
    assert extract_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json_object('Here you go: {"a": {"b": 2}} done') == {"a": {"b": 2}}


def test_selection_validation_rules() -> None:
    result = SelectionResult(
        picks=[
            Pick(place_id=str(B), rank=2),
            Pick(place_id=str(A), rank=1, day_hint=3),
            Pick(place_id="nope", rank=3),
        ]
    )
    check = validate_selection(result, candidate_ids=[A, B], must_see=[C], days=2)
    assert not check.ok
    assert {i.split(":")[0] for i in check.issues} == {
        "unknown_place_id",
        "day_hint_out_of_range",
        "must_see_missing",
    }
    ok = validate_selection(
        SelectionResult(picks=[Pick(place_id=str(B), rank=5), Pick(place_id=str(A), rank=2)]),
        candidate_ids=[A, B],
    )
    assert ok.ok and ok.result is not None
    assert [(p.place_id, p.rank) for p in ok.result.picks] == [(str(A), 1), (str(B), 2)]


def test_rule_based_selection_is_deterministic_and_capped() -> None:
    ids = [uuid.UUID(int=i, version=4) for i in range(1, 30)]
    first = rule_based_selection(ids, must_see=[ids[5]], max_picks=10)
    assert first == rule_based_selection(ids, must_see=[ids[5]], max_picks=10)
    assert len(first.picks) == 10 and first.picks[0].place_id == str(ids[5])


@pytest.mark.parametrize(
    "text",
    [
        "Đèo cao năm trăm mét, nhìn ra cả vịnh.",  # the live VI note (DEC-030 check)
        "A five hundred metres climb to the summit.",
        "It is about two kilometres from the old town.",
        "Mười lăm phút đi bộ là tới chợ.",
        "Chỉ mất hai tiếng để tham quan.",
        "Vé khoảng hai trăm nghìn đồng.",
        "Allow twenty-five minutes for the walk.",
        "Half an hour is enough here.",
        "Entry is fifty thousand dong.",
        "Cách trung tâm ba cây số.",
        "Đường lên dài 500 mét.",  # digits are still caught
    ],
)
def test_rationale_with_spelled_out_number_and_unit_is_fact_like(text: str) -> None:
    assert fact_like(text)


@pytest.mark.parametrize(
    "text",
    [
        "Ngũ Hành Sơn có năm ngọn núi đá vôi.",  # "năm" without a unit
        "Một trong những cây cầu đẹp nhất thành phố.",
        "A quiet pagoda with three carved gates.",
        "One of the oldest bridges in the city.",
        "Bảy Mẫu Coconut Forest is rowed in round basket boats.",
        "Năm 1990 ngôi chùa được trùng tu.",
    ],
)
def test_counts_and_names_without_units_are_allowed(text: str) -> None:
    assert not fact_like(text)


def test_validate_rationales_drops_spelled_out_measurements() -> None:
    result = RationaleSet(
        rationales=[
            Rationale(place_id=str(A), text="Con đèo cao năm trăm mét nhìn ra biển."),
            Rationale(place_id=str(B), text="Five hundred metres of white sand."),
            Rationale(place_id=str(C), text="Một ngôi chùa yên tĩnh trên núi."),
        ]
    )
    mapping, issues = validate_rationales(result, stop_ids=[A, B, C])
    assert mapping[A] is None and mapping[B] is None
    assert mapping[C] == "Một ngôi chùa yên tĩnh trên núi."
    assert sorted(issues) == sorted([f"fact_like_text:{A}", f"fact_like_text:{B}"])
