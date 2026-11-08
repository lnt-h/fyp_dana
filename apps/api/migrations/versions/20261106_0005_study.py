# ruff: noqa: E501
"""User-study records (FR-077). Implements docs/04-design/data/schema.sql 1.0 Section 8."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0005"
down_revision: str | None = "20261106_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute_script(sql: str) -> None:
    # Colons are escaped so that JSON/time literals in comments are not read as bind parameters.
    op.execute(sa.text(sql.replace(":", "\\:")))


SECTION_8_SQL = """
-- -----------------------------------------------------------------------------
-- Section 8 — NEW (migration 0005): user-study records (FR-077; retention ASM-010, NFR-018)
-- -----------------------------------------------------------------------------
CREATE TABLE study_participants (
    id                uuid        NOT NULL DEFAULT gen_random_uuid(),
    account_id        uuid,
    participant_code  text        NOT NULL,
    enrolled_at       timestamptz NOT NULL DEFAULT now(),
    withdrawn_at      timestamptz,
    CONSTRAINT pk_study_participants PRIMARY KEY (id),
    CONSTRAINT fk_study_participants_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE SET NULL,
    CONSTRAINT uq_study_participants_account_id UNIQUE (account_id),
    CONSTRAINT uq_study_participants_participant_code UNIQUE (participant_code),
    CONSTRAINT ck_study_participants_participant_code_format CHECK (participant_code ~ '^[A-Z0-9-]{2,16}$')
);
COMMENT ON TABLE study_participants IS 'Flags study accounts with a pseudonymous code. Link to the account is cut on account deletion (OQ-017).';

CREATE TABLE study_session_logs (
    id                           uuid        NOT NULL DEFAULT gen_random_uuid(),
    study_participant_id         uuid        NOT NULL,
    interface_locale             text        NOT NULL,
    request_submitted_at         timestamptz NOT NULL,
    first_proposal_displayed_at  timestamptz,
    save_outcome                 text        NOT NULL,
    created_at                   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_study_session_logs PRIMARY KEY (id),
    CONSTRAINT fk_study_session_logs_study_participant_id FOREIGN KEY (study_participant_id)
        REFERENCES study_participants (id) ON DELETE CASCADE,
    CONSTRAINT ck_study_session_logs_interface_locale CHECK (interface_locale IN ('vi', 'en')),
    CONSTRAINT ck_study_session_logs_save_outcome CHECK (save_outcome IN ('SAVED', 'NOT_SAVED', 'SAVE_REFUSED')),
    CONSTRAINT ck_study_session_logs_order CHECK (
        first_proposal_displayed_at IS NULL OR first_proposal_displayed_at >= request_submitted_at)
);
CREATE INDEX ix_study_session_logs_study_participant_id ON study_session_logs (study_participant_id);  -- Q-Y1 report
COMMENT ON TABLE study_session_logs IS 'FR-077 five fields only; no request or question text. Deleted by 2027-06-30 (NFR-018).';
"""

DOWNGRADE_SQL = """
DROP TABLE IF EXISTS study_session_logs, study_participants;
"""


def upgrade() -> None:
    _execute_script(SECTION_8_SQL)


def downgrade() -> None:
    _execute_script(DOWNGRADE_SQL)
