"""AI-extracted facts (DEC-028): relaxed validator, value parsing and composition."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest

from app.agents.fact_validation import (
    grounding,
    has_contact_data,
    parse_hours,
    parse_price,
    validate_fact_extraction,
)
from app.agents.schemas import FactEvidenceItem, FactExtractionDraft, HoursRule
from app.agents.writer import build_fact_prompt
from app.curation.auto_publish import Contributions, SourceInfo, compose, gate_reasons
from app.curation.fact_extract import (
    build_osm_query,
    osm_evidence_text,
    wikidata_evidence_text,
)
from app.ingestion.areas import load_areas
from app.ingestion.common import PROVENANCE_KEY
from app.models.catalog import Place
from app.models.reference import FactField

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "fact_evidence_phuoc_lam.json").read_text("utf-8")
)
EVIDENCE = [
    FactEvidenceItem(item["id"], item["text"], None, item["kind"]) for item in FIXTURE["evidence"]
]


def _draft(**overrides: Any) -> FactExtractionDraft:
    return FactExtractionDraft.model_validate({**FIXTURE["model_output"], **overrides})


def test_recorded_output_is_accepted_with_strong_grounding() -> None:
    check = validate_fact_extraction(_draft(), EVIDENCE)
    assert check.issues == []
    facts = {fact.field_code: fact for fact in check.extraction.facts}
    assert facts["ADDRESS_VI"].value == {"text": "46 Nguyễn Trường Tộ, Cẩm Phô, Hội An"}
    assert facts["ADDRESS_VI"].grounding == "STRONG"
    assert facts["OPENING_HOURS"].value["text"] == "Mo-Su 07:00-17:00"
    assert facts["ADMISSION_PRICE"].value == {"free": True}
    assert check.extraction.short_description == {
        "vi": ("Ngôi chùa cổ từ thế kỷ 17 ở Hội An.", "desc:vi"),
        "en": ("A 17th-century pagoda in Hoi An.", "desc:en"),
    }


def test_quote_not_in_evidence_only_downgrades_to_weak() -> None:
    address = {**FIXTURE["model_output"]["address_vi"], "quote": "toạ lạc bên bờ sông Thu Bồn"}
    check = validate_fact_extraction(_draft(address_vi=address), EVIDENCE)
    fact = next(f for f in check.extraction.facts if f.field_code == "ADDRESS_VI")
    assert fact.grounding == "WEAK" and check.issues == []


def test_unknown_evidence_id_rejects_the_field() -> None:
    hours = {**FIXTURE["model_output"]["opening_hours"], "evidence_id": "web9"}
    check = validate_fact_extraction(_draft(opening_hours=hours), EVIDENCE)
    assert "OPENING_HOURS" not in {f.field_code for f in check.extraction.facts}
    assert check.issues == ["unknown_evidence:OPENING_HOURS"]


def test_contact_data_rejects_the_field() -> None:
    address = {
        **FIXTURE["model_output"]["address_vi"],
        "text": "46 Nguyễn Trường Tộ, ĐT 0905 123 456",
    }
    check = validate_fact_extraction(_draft(address_vi=address), EVIDENCE)
    assert "ADDRESS_VI" not in {f.field_code for f in check.extraction.facts}
    assert check.issues == ["contact_data:ADDRESS_VI"]
    assert has_contact_data("xem www.example.vn") and has_contact_data("a@b.vn")
    assert not has_contact_data("Mo-Su 07:00-17:00")


@pytest.mark.parametrize(
    ("rules", "text"),
    [
        ([HoursRule(days=[1, 2, 3, 4, 5, 6, 7], open="7:00", close="17:30")], "Mo-Su 07:00-17:30"),
        (
            [
                HoursRule(days=[1, 2, 3, 4, 5], open="08:00", close="11:30"),
                HoursRule(days=[1, 2, 3, 4, 5], open="13:30", close="17:00"),
                HoursRule(days=[6, 7], open="08:00", close="12:00"),
            ],
            "Mo-Fr 08:00-11:30,13:30-17:00; Sa-Su 08:00-12:00",
        ),
        ([HoursRule(days=[1, 3, 5], open="06:00", close="24:00")], "Mo,We,Fr 06:00-24:00"),
    ],
)
def test_hours_are_parsed_by_code(rules: list[HoursRule], text: str) -> None:
    value = parse_hours(rules)
    assert value is not None and value["text"] == text


@pytest.mark.parametrize(
    "rules",
    [
        [HoursRule(days=[1], open="17:00", close="08:00")],  # closes before it opens
        [HoursRule(days=[1], open="25:00", close="26:00")],
        [
            HoursRule(days=[1], open="08:00", close="12:00"),
            HoursRule(days=[1], open="11:00", close="13:00"),
        ],
    ],
)
def test_invalid_hours_are_rejected(rules: list[HoursRule]) -> None:
    assert parse_hours(rules) is None


def test_prices_are_parsed_by_code() -> None:
    assert parse_price(True, None, None) == {"free": True}
    assert parse_price(False, 120000, 60000) == {
        "free": False,
        "currency": "VND",
        "adult": 120000,
        "child": 60000,
        "amount": "120000",
    }
    assert parse_price(False, None, 20000) is None  # no adult price
    assert parse_price(False, 120, None) is None  # "120k" not converted: implausible
    assert parse_price(True, 40000, None) is None  # free and a price at once


def test_unparsable_price_rejects_only_that_field() -> None:
    price = {"free": False, "adult_vnd": 50, "child_vnd": None, "evidence_id": "web2", "quote": "x"}
    check = validate_fact_extraction(_draft(admission_price=price), EVIDENCE)
    assert check.issues == ["unparsable:ADMISSION_PRICE"]
    assert {f.field_code for f in check.extraction.facts} == {"ADDRESS_VI", "OPENING_HOURS"}


def test_grounding_ignores_case_and_diacritics() -> None:
    assert grounding("CHÙA MỞ CỬA TỪ 7H00", "Chùa mở cửa từ 7h00 đến 17h00") == "STRONG"
    assert grounding("open daily", "Chùa mở cửa từ 7h00") == "WEAK"


def test_prompt_redacts_contact_data_and_sends_no_urls() -> None:
    items = [FactEvidenceItem("web2", FIXTURE["evidence"][2]["text"], "https://x.vn/a", "WEB")]
    prompt, supplied = build_fact_prompt(
        name_vi="Chùa Phước Lâm", name_en=None, category=None, area=None, evidence=items
    )
    assert "0905" not in prompt and "[PHONE]" in prompt
    assert "https://x.vn" not in prompt and supplied[0].evidence_id == "web2"


def test_structured_evidence_texts() -> None:
    tags = {
        "addr:housenumber": "46",
        "addr:street": "Nguyễn Trường Tộ",
        "addr:city": "Hội An",
        "opening_hours": "Mo-Su 07:00-17:00",
        "phone": "+84 905 123 456",
        "website": "https://example.vn",
        "fee": "no",
    }
    text = osm_evidence_text(tags)
    assert "address: 46, Nguyễn Trường Tộ, Hội An" in text and "fee: no" in text
    assert "905" not in text and "example" not in text
    entity = {
        "claims": {
            "P6375": [{"mainsnak": {"datavalue": {"value": {"text": "46 Nguyễn Trường Tộ"}}}}],
            "P2555": [
                {
                    "mainsnak": {
                        "datavalue": {
                            "value": {
                                "amount": "+40000",
                                "unit": "http://www.wikidata.org/entity/Q192090",
                            }
                        }
                    }
                }
            ],
        }
    }
    assert wikidata_evidence_text(entity) == "street address: 46 Nguyễn Trường Tộ\nfee: 40000 VND"
    assert build_osm_query(["node/1", "way/2", "node/3", "bad"]) == (
        "[out:json][timeout:60];(node(id:1,3);way(id:2););out tags;"
    )


def _place() -> Place:
    return Place(
        id=uuid.uuid4(), slug="p", location="SRID=4326;POINT(108.3262 15.8771)", category_code=None
    )


FIELDS = [
    FactField(code=code, value_kind=kind, required_for_publication=True, is_operational=True)
    for code, kind in (
        ("ADDRESS_VI", "TEXT"),
        ("ADMISSION_PRICE", "MONEY"),
        ("OPENING_HOURS", "HOURS"),
    )
]


def test_compose_uses_ai_facts_only_where_no_source_value_and_gate_checks_link() -> None:
    osm_rev, facts_rev, web_rev, hours_rev = (uuid.uuid4() for _ in range(4))
    osm = {
        "name": {"vi": "Chùa Phước Lâm", "en": "Phuoc Lam Pagoda"},
        "location": {"lat": 15.8771, "lng": 108.3262},
        "category": "RELIGIOUS_SITE",
        "facts": {"OPENING_HOURS": {"value": {"weekly": {}, "text": "Mo-Su 07:00-17:00"}}},
        PROVENANCE_KEY: {
            "source_revision_id": str(osm_rev),
            "fact_source_revision_ids": {"OPENING_HOURS": str(hours_rev)},
        },
    }
    ai_facts = {
        "facts": {
            "ADDRESS_VI": {"value": {"text": "46 Nguyễn Trường Tộ"}, "grounding": "STRONG"},
            "OPENING_HOURS": {"value": {"text": "Mo-Su 06:00-18:00"}, "grounding": "WEAK"},
        },
        "short_description": {"vi": "Ngôi chùa cổ.", "en": "An old pagoda."},
        PROVENANCE_KEY: {
            "source_revision_id": str(facts_rev),
            "fact_source_revision_ids": {"ADDRESS_VI": str(web_rev), "OPENING_HOURS": str(web_rev)},
        },
    }
    desired = compose(
        _place(),
        Contributions(osm=osm, ai_facts=ai_facts),
        area_codes=load_areas("da-nang"),
        categories={"RELIGIOUS_SITE"},
        fact_fields=FIELDS,
    )
    by_code = {fact.field_code: fact for fact in desired.facts}
    assert (by_code["ADDRESS_VI"].origin, by_code["ADDRESS_VI"].grounding) == (
        "AI_EXTRACTED",
        "STRONG",
    )
    assert by_code["OPENING_HOURS"].origin == "SOURCE"  # OSM wins over the extraction
    assert by_code["ADMISSION_PRICE"].knowledge_state == "UNKNOWN"
    assert desired.localizations["vi"].short_description == "Ngôi chùa cổ."
    licensed = SourceInfo("OpenStreetMap", "ODbL-1.0", "© OpenStreetMap contributors")
    gonarra = SourceInfo("Gonarra", "GONARRA-AI-FACTS", "Facts extracted by Gonarra")
    web = SourceInfo("example.vn", "UNKNOWN", "example.vn")
    sources = {osm_rev: licensed, hours_rev: licensed, facts_rev: gonarra, web_rev: web}
    reasons = gate_reasons(desired, inside=True, sources=sources)
    # The cited web page has no licence: allowed for AI-extracted facts (a link, not content).
    assert not [r for r in reasons if r.startswith(("FACT_WITHOUT_SOURCE", "MISSING_LICENCE"))]
    del sources[web_rev]
    reasons = gate_reasons(desired, inside=True, sources=sources)
    assert "FACT_WITHOUT_SOURCE:ADDRESS_VI" in reasons
