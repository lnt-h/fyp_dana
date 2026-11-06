"""Place fact value rules (BR-024, FR-012).

Facts are written by the automated publication gate (``app.curation.auto_publish``): each change
is a new ``fact_revision`` that supersedes the previous APPROVED one (approved rows are immutable,
enforced by a trigger), and operational facts carry claim-level evidence (``fact_evidence``).
"""

from __future__ import annotations

from typing import Any

from app.errors import invalid
from app.models.reference import FactField


def validate_fact_value(
    field: FactField, knowledge_state: str, value: dict[str, Any] | None
) -> None:
    """Domain shape rules (mirrors ck_place_facts_* plus value_kind expectations)."""
    if knowledge_state == "KNOWN":
        if not value:
            raise invalid("fact_value_required", "A KNOWN fact needs a value object")
    elif value is not None:
        raise invalid("fact_value_forbidden", "Only KNOWN facts carry a value")
    if value is None:
        return
    if field.value_kind == "LOCATION":
        lat, lng = value.get("lat"), value.get("lng")
        if not (
            isinstance(lat, int | float)
            and isinstance(lng, int | float)
            and -90 <= lat <= 90
            and -180 <= lng <= 180
        ):
            raise invalid(
                "fact_value_invalid", "LOCATION facts need numeric lat/lng", field=field.code
            )


def validate_conflict(conflict_state: str, conflict_note: str | None) -> None:
    if conflict_state != "NONE" and not conflict_note:
        raise invalid("conflict_note_required", "An OPEN or RESOLVED conflict needs a note")
