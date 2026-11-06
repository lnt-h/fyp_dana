"""``Idempotency-Key`` handling (ADR-009, FR-041, ASM-071).

Scope: ``(account_id, operation, idempotency_key)`` — the primary key of ``idempotency_records``.
The request fingerprint is the SHA-256 of the canonical JSON of the operation's target id (the
preview for Save/edit, the account for trip creation) and body,
so the same key reused for a different preview or body answers 409 ``idempotency_key_reused``.
Records live 24 h. Only successful responses are stored; a failed attempt rolls its claim back so a
retry re-evaluates.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from app.errors import AppError
from app.models.planning import IdempotencyRecord

IDEMPOTENCY_HEADER: Final = "Idempotency-Key"
REPLAYED_HEADER: Final = "Idempotent-Replayed"
RETENTION: Final = timedelta(hours=24)

OP_TRIP_SAVE: Final = "TRIP_SAVE"
OP_PREVIEW_CREATE: Final = "PREVIEW_CREATE"
OP_DAY_REGENERATE: Final = "DAY_REGENERATE"
OP_ACCOUNT_DELETE: Final = "ACCOUNT_DELETE"
# Allowed by ck_idempotency_records_operation from migration 0006 on (optional key on
# POST /v1/trips and PATCH /v1/plan-previews/{id}).
OP_TRIP_CREATE: Final = "TRIP_CREATE"
OP_PREVIEW_EDIT: Final = "PREVIEW_EDIT"


@dataclass(frozen=True)
class StoredResponse:
    status: int
    body: dict[str, Any]


def normalize_key(raw: str | None, *, required: bool) -> str | None:
    """Validate the header: a UUID per the contract (stored canonical, lower-case)."""
    if raw is None or not raw.strip():
        if required:
            raise AppError(
                422,
                "validation_error",
                "Idempotency-Key header is required",
                context={"fields": [{"location": ["header", IDEMPOTENCY_HEADER]}]},
            )
        return None
    try:
        return str(uuid.UUID(raw.strip()))
    except ValueError as exc:
        raise AppError(
            422,
            "validation_error",
            "Idempotency-Key must be a UUID",
            context={"fields": [{"location": ["header", IDEMPOTENCY_HEADER]}]},
        ) from exc


def request_fingerprint(target_id: uuid.UUID, body: dict[str, Any]) -> str:
    canonical = json.dumps(
        {"target": str(target_id), "body": body}, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def expires_at(now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + RETENTION


def replay_or_raise(record: IdempotencyRecord, fingerprint: str) -> StoredResponse:
    """Decide what an existing record means for this request."""
    if record.request_sha256 != fingerprint:
        raise AppError(
            409,
            "idempotency_key_reused",
            "This Idempotency-Key was already used for a different request",
        )
    if record.state != "COMPLETED" or record.response_status is None:
        raise AppError(
            409,
            "idempotency_in_progress",
            "A request with this Idempotency-Key is still in progress",
            retryable=True,
        )
    return StoredResponse(status=record.response_status, body=dict(record.response_body or {}))
