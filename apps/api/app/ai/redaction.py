"""BR-046 redactor: no account IDs, contact data or precise location reach any provider.

Deterministic regex rules, applied to free text (user prompts, questions, notes) and to
candidate DTOs before they are serialised into a model prompt. :func:`ensure_clean` is the
fail-closed gate for an assembled prompt: it raises instead of sending.

Do not run :func:`redact_text` over a serialised candidate list: catalog place IDs are UUIDs
and would be replaced. Pass them to :func:`ensure_clean` as ``allowed_ids`` instead.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

EMAIL = "[EMAIL]"
PHONE = "[PHONE]"
URL = "[URL]"
ACCOUNT = "[ACCOUNT_ID]"
ID = "[ID]"
COORDS = "[COORDINATES]"

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
# Clerk identifiers: user_…, sess_…, org_…, client_… and friends.
_CLERK_RE = re.compile(r"\b(?:user|sess|org|client|sms|idn|inv|orginv)_[A-Za-z0-9]{8,}\b")
# URL whose query string or fragment carries a credential-like parameter.
_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_SECRET_PARAM_RE = re.compile(
    r"[?&#](?:[A-Za-z_]*token|key|api_key|apikey|sig|signature|auth|session|sessionid|code|"
    r"secret|password|pwd|jwt|__clerk_[a-z_]*)=",
    re.IGNORECASE,
)
# "16.0544, 108.2022" style pairs. ≥ 3 decimals so ratings like "4.5, 3.0" survive; see
# _is_coordinate_pair for the VN thousands-separator guard ("50.000, 100.000" đồng).
_COORD_PAIR_RE = re.compile(
    r"(?<![\d.])(-?\d{1,3})\.(\d{3,})\s*[,;/ ]\s*(-?\d{1,3})\.(\d{3,})(?![\d.])"
)
# "lat: 16.05", "lng=108.2", "vĩ độ 16,05" …
_COORD_KEY_RE = re.compile(
    r"\b(?:lat|lng|lon|latitude|longitude|vĩ độ|kinh độ|vi do|kinh do)\b\s*[:=]?\s*"
    r"-?\d{1,3}[.,]\d+",
    re.IGNORECASE,
)
# Google Maps "@16.05,108.2,17z" fragments.
_MAPS_AT_RE = re.compile(r"@-?\d{1,3}\.\d+,-?\d{1,3}\.\d+(?:,\d+(?:\.\d+)?z)?")
# Vietnamese phone numbers: +84 / 0084 / (+84) / 0 prefix then 8–10 digits with optional
# space, dot or dash separators: 0905 123 456, 0236.3822.123, +84 905-123-456.
_PHONE_RE = re.compile(r"(?<![\w+])(?:\(?\+84\)?|0084|0)(?:[\s.\-]?\d){8,10}(?![\w])")


def _is_coordinate_pair(match: re.Match[str]) -> bool:
    lat_int, lat_dec, lng_int, lng_dec = match.groups()
    if lat_dec == "000" and lng_dec == "000":
        return False  # "50.000, 100.000" is a VN price range, not a location
    return abs(int(lat_int)) <= 90 and abs(int(lng_int)) <= 180


def _coord_pair_sub(match: re.Match[str]) -> str:
    return COORDS if _is_coordinate_pair(match) else match.group(0)


_RULES: tuple[tuple[re.Pattern[str], str | Callable[[re.Match[str]], str]], ...] = (
    (_EMAIL_RE, EMAIL),
    (_CLERK_RE, ACCOUNT),
    (_UUID_RE, ID),
    (_MAPS_AT_RE, COORDS),
    (_COORD_KEY_RE, COORDS),
    (_COORD_PAIR_RE, _coord_pair_sub),
    (_PHONE_RE, PHONE),
)


class RedactionError(ValueError):
    """An assembled prompt still contains personal data; the call must not be made."""

    def __init__(self, kinds: Iterable[str]) -> None:
        self.kinds = tuple(sorted(set(kinds)))
        super().__init__(f"prompt contains redactable data: {', '.join(self.kinds)}")


def _redact_url(match: re.Match[str]) -> str:
    url = match.group(0)
    if _SECRET_PARAM_RE.search(url) or _MAPS_AT_RE.search(url):
        return URL
    return url


def redact_text(value: str) -> str:
    """Replace e-mails, VN phone numbers, credential URLs, Clerk IDs, UUIDs and coordinates."""
    result = _URL_RE.sub(_redact_url, value)
    for pattern, placeholder in _RULES:
        result = pattern.sub(placeholder, result)
    return result


def find_sensitive(value: str, *, allowed_ids: Iterable[str | uuid.UUID] = ()) -> list[str]:
    """Kinds of personal data present in ``value``; UUIDs in ``allowed_ids`` are tolerated."""
    allowed = {str(item).lower() for item in allowed_ids}
    kinds: list[str] = []
    if any(_SECRET_PARAM_RE.search(m.group(0)) for m in _URL_RE.finditer(value)):
        kinds.append("url")
    if _EMAIL_RE.search(value):
        kinds.append("email")
    if _CLERK_RE.search(value):
        kinds.append("account_id")
    if any(m.group(0).lower() not in allowed for m in _UUID_RE.finditer(value)):
        kinds.append("uuid")
    if (
        _MAPS_AT_RE.search(value)
        or _COORD_KEY_RE.search(value)
        or any(_is_coordinate_pair(m) for m in _COORD_PAIR_RE.finditer(value))
    ):
        kinds.append("coordinates")
    if _PHONE_RE.search(value):
        kinds.append("phone")
    return kinds


def ensure_clean(value: str, *, allowed_ids: Iterable[str | uuid.UUID] = ()) -> str:
    """Fail closed: return ``value`` unchanged or raise :class:`RedactionError`."""
    kinds = find_sensitive(value, allowed_ids=allowed_ids)
    if kinds:
        raise RedactionError(kinds)
    return value


class CandidateDto(BaseModel):
    """Provider-safe view of a planner candidate (published place). No coordinates,
    addresses, contact data or account data; ``extra="forbid"`` keeps it that way."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    place_id: uuid.UUID
    name_vi: str
    name_en: str
    category_code: str
    area_code: str | None = None
    summary: str | None = None
    open_windows: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


_CANDIDATE_FIELDS = frozenset(CandidateDto.model_fields)
_FREE_TEXT_FIELDS = ("name_vi", "name_en", "summary")


def redact_candidate(candidate: CandidateDto | Mapping[str, Any]) -> CandidateDto:
    """Allow-list the DTO fields (dropping account_id, lat/lng/location, phone, email,
    website, address, …) and redact free text inside the remaining ones."""
    raw: Mapping[str, Any] = (
        candidate.model_dump() if isinstance(candidate, CandidateDto) else candidate
    )
    data = {key: raw[key] for key in _CANDIDATE_FIELDS if key in raw}
    for key in _FREE_TEXT_FIELDS:
        if isinstance(data.get(key), str):
            data[key] = redact_text(data[key])
    data["tags"] = [redact_text(str(tag)) for tag in data.get("tags") or []]
    return CandidateDto.model_validate(data)


def redact_candidates(
    candidates: Iterable[CandidateDto | Mapping[str, Any]],
) -> list[CandidateDto]:
    return [redact_candidate(candidate) for candidate in candidates]
