# ruff: noqa: E501
"""City-level Guide sessions and Guide idempotency (DEC-017, API-024/028).

* ``guide_sessions`` drops ``ck_guide_sessions_context``: a scope CITY session has neither a
  place nor (necessarily) a trip. Scope is derived (place_id NULL = CITY); the city of a CITY
  session without a trip is the enabled release city (Đà Nẵng only, DEC-013).
* ``idempotency_records.operation`` gains ``GUIDE_ASK`` (API-028 ``Idempotency-Key``).
* ``guide_messages.answer_status`` gains ``ANSWERED_WEB_UNVERIFIED`` (contract 1.0 enum; the web
  fallback itself is not implemented yet).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261108_0008"
down_revision: str | None = "20261108_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPGRADE_SQL = """
ALTER TABLE guide_sessions DROP CONSTRAINT ck_guide_sessions_context;
COMMENT ON TABLE guide_sessions IS 'Private Guide conversation: city-level (place_id NULL), or one published place; optionally linked to an owned trip (FR-056, FR-069, DEC-017).';

ALTER TABLE idempotency_records DROP CONSTRAINT ck_idempotency_records_operation;
ALTER TABLE idempotency_records ADD CONSTRAINT ck_idempotency_records_operation CHECK (operation IN
    ('TRIP_SAVE', 'PREVIEW_CREATE', 'DAY_REGENERATE', 'ACCOUNT_DELETE', 'TRIP_CREATE', 'PREVIEW_EDIT', 'PUBLISH', 'GUIDE_ASK'));

ALTER TABLE guide_messages DROP CONSTRAINT ck_guide_messages_answer_status;
ALTER TABLE guide_messages ADD CONSTRAINT ck_guide_messages_answer_status CHECK (
    (role = 'ASSISTANT' AND answer_status IN ('ANSWERED', 'ANSWERED_WEB_UNVERIFIED', 'INSUFFICIENT_EVIDENCE', 'NOT_RECOGNISED'))
    OR (role = 'TRAVELER' AND answer_status IS NULL));
"""

DOWNGRADE_SQL = """
DELETE FROM guide_messages WHERE answer_status = 'ANSWERED_WEB_UNVERIFIED';
ALTER TABLE guide_messages DROP CONSTRAINT ck_guide_messages_answer_status;
ALTER TABLE guide_messages ADD CONSTRAINT ck_guide_messages_answer_status CHECK (
    (role = 'ASSISTANT' AND answer_status IN ('ANSWERED', 'INSUFFICIENT_EVIDENCE', 'NOT_RECOGNISED'))
    OR (role = 'TRAVELER' AND answer_status IS NULL));

DELETE FROM idempotency_records WHERE operation = 'GUIDE_ASK';
ALTER TABLE idempotency_records DROP CONSTRAINT ck_idempotency_records_operation;
ALTER TABLE idempotency_records ADD CONSTRAINT ck_idempotency_records_operation CHECK (operation IN
    ('TRIP_SAVE', 'PREVIEW_CREATE', 'DAY_REGENERATE', 'ACCOUNT_DELETE', 'TRIP_CREATE', 'PREVIEW_EDIT', 'PUBLISH'));

DELETE FROM guide_sessions WHERE trip_id IS NULL AND place_id IS NULL;
ALTER TABLE guide_sessions ADD CONSTRAINT ck_guide_sessions_context CHECK (trip_id IS NOT NULL OR place_id IS NOT NULL);
COMMENT ON TABLE guide_sessions IS 'Private Guide conversation scoped to a published place or an owned trip (FR-056, FR-069).';
"""


def _execute_script(sql: str) -> None:
    op.execute(sa.text(sql.replace(":", "\\:")))


def upgrade() -> None:
    _execute_script(UPGRADE_SQL)


def downgrade() -> None:
    _execute_script(DOWNGRADE_SQL)
