"""Code validation of the grounded writer's FACT_EXTRACT output (DEC-028, relaxed rule).

A field is **accepted** when it cites an evidence id that exists in the supplied set; its quote
is compared with the cited evidence text only to set ``grounding``:

* ``STRONG`` when at least ``GROUNDING_MIN_OVERLAP`` (0.5) of the quote's tokens occur in the
  cited evidence text (case, diacritics and punctuation ignored);
* ``WEAK`` otherwise. The quote never rejects a field.

A field is **rejected** (stays UNKNOWN) only when it cites no supplied evidence id, its value fails
code parsing (opening hours and price shapes) or its value contains contact data (phone, e-mail,
URL, coordinates). Values are converted by code into the stored fact shapes:

* OPENING_HOURS → ``{"weekly": {"1": [["07:00", "17:00"]], …}, "text": "Mo-Su 07:00-17:00"}``
  (the OSM-like ``text`` is generated here, never copied from the model);
* ADMISSION_PRICE → ``{"free": true}`` or ``{"currency": "VND", "adult": 40000, "child": 20000,
  "amount": "40000"}`` (``amount`` keeps the 1.0 MONEY rendering working);
* ADDRESS_VI → ``{"text": "…"}``.

ENTRANCE_LOCATION is never extracted (its LOCATION shape needs coordinates; models never give
coordinates).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

from app.agents.schemas import (
    FactEvidenceItem,
    FactExtraction,
    FactExtractionDraft,
    HoursRule,
    ValidatedFact,
)
from app.ai.redaction import find_sensitive

GROUNDING_MIN_OVERLAP = 0.5
MIN_PRICE_VND = 1_000
MAX_PRICE_VND = 5_000_000
DAY_CODES = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
_TIME = re.compile(r"^(\d{1,2}):(\d{2})$")
_URL = re.compile(r"https?://|www\.", re.IGNORECASE)
_TOKEN = re.compile(r"\w+")


def tokens(value: str) -> list[str]:
    """Lower-case tokens without diacritics (đ → d)."""
    lowered = value.lower().replace("đ", "d")
    stripped = "".join(
        ch for ch in unicodedata.normalize("NFD", lowered) if unicodedata.category(ch) != "Mn"
    )
    return _TOKEN.findall(stripped)


def grounding(quote: str, evidence_text: str) -> Literal["STRONG", "WEAK"]:
    """STRONG when ≥ 0.5 of the quote's tokens occur in the evidence text, else WEAK."""
    quote_tokens = tokens(quote)
    if not quote_tokens:
        return "WEAK"
    available = set(tokens(evidence_text))
    hits = sum(1 for token in quote_tokens if token in available)
    return "STRONG" if hits / len(quote_tokens) >= GROUNDING_MIN_OVERLAP else "WEAK"


def has_contact_data(value: str) -> bool:
    """Phone numbers, e-mail addresses, URLs or coordinates (never shown as a fact value)."""
    if _URL.search(value):
        return True
    return any(kind in ("phone", "email", "coordinates", "url") for kind in find_sensitive(value))


def _minutes(value: str) -> int | None:
    match = _TIME.match(value.strip())
    if match is None:
        return None
    hours, minutes = int(match.group(1)), int(match.group(2))
    if minutes > 59 or hours > 24 or (hours == 24 and minutes):
        return None
    return hours * 60 + minutes


def _hhmm(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"


def _day_ranges(days: Sequence[int]) -> str:
    """[1,2,3,5] → "Mo-We,Fr" (OSM-like)."""
    ordered = sorted(set(days))
    parts: list[str] = []
    start = previous = ordered[0]
    for day in [*ordered[1:], None]:
        if day is not None and day == previous + 1:
            previous = day
            continue
        if start == previous:
            parts.append(DAY_CODES[start - 1])
        else:
            parts.append(f"{DAY_CODES[start - 1]}-{DAY_CODES[previous - 1]}")
        if day is not None:
            start = previous = day
    return ",".join(parts)


def parse_hours(rules: Sequence[HoursRule]) -> dict[str, object] | None:
    """Structured rules → the OPENING_HOURS fact shape, or None when a rule is invalid."""
    weekly: dict[str, list[list[str]]] = {}
    for rule in rules:
        opens, closes = _minutes(rule.open), _minutes(rule.close)
        if opens is None or closes is None or closes <= opens or opens >= 24 * 60:
            return None
        for day in sorted(set(rule.days)):
            if not 1 <= day <= 7:
                return None
            weekly.setdefault(str(day), []).append([_hhmm(opens), _hhmm(closes)])
    if not weekly:
        return None
    for ranges in weekly.values():
        ranges.sort()
        for (_, end), (start, _) in zip(ranges, ranges[1:], strict=False):
            if start < end:
                return None  # overlapping ranges on one day
    # Group days with identical ranges into "Mo-Fr 07:00-17:00; Sa,Su 08:00-12:00".
    groups: dict[tuple[tuple[str, str], ...], list[int]] = {}
    for day_key, day_ranges in weekly.items():
        groups.setdefault(tuple((a, b) for a, b in day_ranges), []).append(int(day_key))
    text = "; ".join(
        f"{_day_ranges(days)} " + ",".join(f"{a}-{b}" for a, b in group)
        for group, days in sorted(groups.items(), key=lambda item: min(item[1]))
    )
    return {"weekly": dict(sorted(weekly.items())), "text": text}


def parse_price(free: bool, adult: int | None, child: int | None) -> dict[str, object] | None:
    """Price draft → the ADMISSION_PRICE fact shape, or None when it is not a plausible price."""
    if free:
        return None if (adult or child) else {"free": True}
    if adult is None:
        return None
    for amount in (adult, child):
        if amount is not None and not MIN_PRICE_VND <= amount <= MAX_PRICE_VND:
            return None
    value: dict[str, object] = {
        "free": False,
        "currency": "VND",
        "adult": adult,
        "amount": str(adult),
    }
    if child is not None:
        value["child"] = child
    return value


@dataclass
class FactCheck:
    extraction: FactExtraction
    issues: list[str] = field(default_factory=list)


def validate_fact_extraction(
    draft: FactExtractionDraft, evidence: Sequence[FactEvidenceItem]
) -> FactCheck:
    """Apply the relaxed DEC-028 rule; rejected fields are listed in ``issues`` and dropped."""
    by_id: Mapping[str, FactEvidenceItem] = {item.evidence_id: item for item in evidence}
    issues: list[str] = []
    facts: list[ValidatedFact] = []

    def cited(code: str, evidence_id: str) -> FactEvidenceItem | None:
        item = by_id.get(evidence_id)
        if item is None:
            issues.append(f"unknown_evidence:{code}")
        return item

    if draft.address_vi is not None:
        item = cited("ADDRESS_VI", draft.address_vi.evidence_id)
        text = " ".join(draft.address_vi.text.split())
        if item is not None:
            if has_contact_data(text):
                issues.append("contact_data:ADDRESS_VI")
            else:
                facts.append(
                    ValidatedFact(
                        "ADDRESS_VI",
                        {"text": text},
                        item.evidence_id,
                        draft.address_vi.quote,
                        grounding(draft.address_vi.quote, item.text),
                    )
                )
    if draft.opening_hours is not None:
        item = cited("OPENING_HOURS", draft.opening_hours.evidence_id)
        if item is not None:
            hours = parse_hours(draft.opening_hours.rules)
            if hours is None:
                issues.append("unparsable:OPENING_HOURS")
            else:
                facts.append(
                    ValidatedFact(
                        "OPENING_HOURS",
                        hours,
                        item.evidence_id,
                        draft.opening_hours.quote,
                        grounding(draft.opening_hours.quote, item.text),
                    )
                )
    if draft.admission_price is not None:
        price_draft = draft.admission_price
        item = cited("ADMISSION_PRICE", price_draft.evidence_id)
        if item is not None:
            price = parse_price(price_draft.free, price_draft.adult_vnd, price_draft.child_vnd)
            if price is None:
                issues.append("unparsable:ADMISSION_PRICE")
            else:
                facts.append(
                    ValidatedFact(
                        "ADMISSION_PRICE",
                        price,
                        item.evidence_id,
                        price_draft.quote,
                        grounding(price_draft.quote, item.text),
                    )
                )
    short: dict[str, tuple[str, str]] = {}
    for locale, short_draft in (
        ("vi", draft.short_description_vi),
        ("en", draft.short_description_en),
    ):
        if short_draft is None:
            continue
        item = cited(f"SHORT_DESCRIPTION_{locale.upper()}", short_draft.evidence_id)
        text = " ".join(short_draft.text.split())
        if item is None:
            continue
        if has_contact_data(text):
            issues.append(f"contact_data:SHORT_DESCRIPTION_{locale.upper()}")
            continue
        short[locale] = (text, item.evidence_id)
    return FactCheck(FactExtraction(tuple(facts), short), issues)
