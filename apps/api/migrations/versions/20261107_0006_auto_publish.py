# ruff: noqa: E501
"""Automated content pipeline (DEC-022): CHECK values and alias uniqueness per locale.

* ``catalog_audit_events.action`` gains AUTO_APPROVE, AUTO_PUBLISH and AUTO_REJECT (the
  deterministic publication gate replaces curator review).
* ``data_providers.provider_kind`` gains OPERATOR_DATA (the owner's place sheet).
* ``idempotency_records.operation`` gains TRIP_CREATE, PREVIEW_EDIT and PUBLISH.
* ``account_deletion_jobs.clerk_subject_sha256`` (nullable, hex SHA-256, partial index on COMPLETED).
* ``place_aliases`` uniqueness becomes (place_id, locale, alias_normalized): a VI and an EN
  search name that fold to the same text (e.g. "Bà Nà Hills" / "Ba Na Hills") are both kept,
  so the gate's per-locale MISSING_SEARCH_NAME check can pass.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261107_0006"
down_revision: str | None = "20261106_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute_script(sql: str) -> None:
    # Colons are escaped so that literals in comments are not read as bind parameters.
    op.execute(sa.text(sql.replace(":", "\\:")))


AUTO_PUBLISH_SQL = """
ALTER TABLE catalog_audit_events DROP CONSTRAINT ck_catalog_audit_events_action;
ALTER TABLE catalog_audit_events ADD CONSTRAINT ck_catalog_audit_events_action CHECK (action IN
    ('IMPORT', 'MATCH_REVIEW', 'CONTENT_REVIEW', 'FACT_REVIEW', 'MEDIA_REVIEW', 'PUBLISH', 'WITHDRAW', 'POLICY_CHANGE',
     'WEB_PROMOTE', 'WEB_REJECT', 'AUTO_APPROVE', 'AUTO_PUBLISH', 'AUTO_REJECT'));

ALTER TABLE data_providers DROP CONSTRAINT ck_data_providers_provider_kind;
ALTER TABLE data_providers ADD CONSTRAINT ck_data_providers_provider_kind CHECK (provider_kind IN
    ('OPEN_DATASET', 'RUNTIME_API', 'OFFICIAL_SOURCE', 'MEDIA_LIBRARY', 'AI_SERVICE', 'WEB_SEARCH', 'WEB_CONTENT',
     'OPERATOR_DATA'));

ALTER TABLE idempotency_records DROP CONSTRAINT ck_idempotency_records_operation;
ALTER TABLE idempotency_records ADD CONSTRAINT ck_idempotency_records_operation CHECK (operation IN
    ('TRIP_SAVE', 'PREVIEW_CREATE', 'DAY_REGENERATE', 'ACCOUNT_DELETE', 'TRIP_CREATE', 'PREVIEW_EDIT', 'PUBLISH'));

ALTER TABLE place_aliases DROP CONSTRAINT uq_place_aliases_place_id_alias_normalized;
ALTER TABLE place_aliases ADD CONSTRAINT uq_place_aliases_place_id_locale_alias_normalized
    UNIQUE (place_id, locale, alias_normalized);

-- Deleted-account tombstone (FR-071): hash of the Clerk subject of a COMPLETED deletion job.
ALTER TABLE account_deletion_jobs ADD COLUMN clerk_subject_sha256 char(64);
ALTER TABLE account_deletion_jobs ADD CONSTRAINT ck_account_deletion_jobs_clerk_subject_sha256_format
    CHECK (clerk_subject_sha256 ~ '^[0-9a-f]{64}$');
CREATE INDEX ix_account_deletion_jobs_clerk_subject_sha256_completed
    ON account_deletion_jobs (clerk_subject_sha256) WHERE status = 'COMPLETED';
COMMENT ON COLUMN account_deletion_jobs.clerk_subject_sha256 IS 'SHA-256 (hex) of the deleted Clerk subject; lets the API refuse a re-used token of a deleted account without storing the subject.';
COMMENT ON COLUMN place_closure_rules.params IS 'Shape by rule_kind; every kind also accepts optional {"from":"HH:MM","to":"HH:MM"} (window within the day) and {"restricted_modes":["WALK"|"DRIVE"|"TWO_WHEELER"]} (migration 0006). WEEKLY {"weekdays":[1..7]} (ISO, 1 = Monday) with optional {"from":"HH:MM","to":"HH:MM"}; DATE {"dates":["YYYY-MM-DD"]} or {"month_day":["MM-DD"]} (yearly); LUNAR_DATE {"lunar_days":[1,14,15],"lunar_months":[...]|null} resolved by the pure-Python VN lunar algorithm, UTC+7 (OQ-125); SEASON {"from_month_day":"MM-DD","to_month_day":"MM-DD"}; TICKET_VALIDITY {"valid_same_day":true} or {"valid_hours":24}.';
"""

DOWNGRADE_SQL = """
COMMENT ON COLUMN place_closure_rules.params IS 'Shape by rule_kind. WEEKLY {"weekdays":[1..7]} (ISO, 1 = Monday) with optional {"from":"HH:MM","to":"HH:MM"}; DATE {"dates":["YYYY-MM-DD"]} or {"month_day":["MM-DD"]} (yearly); LUNAR_DATE {"lunar_days":[1,14,15],"lunar_months":[...]|null} resolved by the pure-Python VN lunar algorithm, UTC+7 (OQ-125); SEASON {"from_month_day":"MM-DD","to_month_day":"MM-DD"}; TICKET_VALIDITY {"valid_same_day":true} or {"valid_hours":24}.';
DROP INDEX IF EXISTS ix_account_deletion_jobs_clerk_subject_sha256_completed;
ALTER TABLE account_deletion_jobs DROP COLUMN IF EXISTS clerk_subject_sha256;

-- Keep one alias per (place, folded text) before the narrower unique constraint returns.
DELETE FROM place_aliases a
 USING place_aliases b
 WHERE a.place_id = b.place_id AND a.alias_normalized = b.alias_normalized
   AND a.id <> b.id AND (a.locale, a.id::text) > (b.locale, b.id::text);
ALTER TABLE place_aliases DROP CONSTRAINT uq_place_aliases_place_id_locale_alias_normalized;
ALTER TABLE place_aliases ADD CONSTRAINT uq_place_aliases_place_id_alias_normalized
    UNIQUE (place_id, alias_normalized);

DELETE FROM idempotency_records WHERE operation IN ('TRIP_CREATE', 'PREVIEW_EDIT', 'PUBLISH');
ALTER TABLE idempotency_records DROP CONSTRAINT ck_idempotency_records_operation;
ALTER TABLE idempotency_records ADD CONSTRAINT ck_idempotency_records_operation CHECK (operation IN
    ('TRIP_SAVE', 'PREVIEW_CREATE', 'DAY_REGENERATE', 'ACCOUNT_DELETE'));

UPDATE data_providers SET provider_kind = 'OFFICIAL_SOURCE' WHERE provider_kind = 'OPERATOR_DATA';
ALTER TABLE data_providers DROP CONSTRAINT ck_data_providers_provider_kind;
ALTER TABLE data_providers ADD CONSTRAINT ck_data_providers_provider_kind CHECK (provider_kind IN
    ('OPEN_DATASET', 'RUNTIME_API', 'OFFICIAL_SOURCE', 'MEDIA_LIBRARY', 'AI_SERVICE', 'WEB_SEARCH', 'WEB_CONTENT'));

UPDATE catalog_audit_events SET action = 'PUBLISH' WHERE action = 'AUTO_PUBLISH';
UPDATE catalog_audit_events SET action = 'CONTENT_REVIEW' WHERE action IN ('AUTO_APPROVE', 'AUTO_REJECT');
ALTER TABLE catalog_audit_events DROP CONSTRAINT ck_catalog_audit_events_action;
ALTER TABLE catalog_audit_events ADD CONSTRAINT ck_catalog_audit_events_action CHECK (action IN
    ('IMPORT', 'MATCH_REVIEW', 'CONTENT_REVIEW', 'FACT_REVIEW', 'MEDIA_REVIEW', 'PUBLISH', 'WITHDRAW', 'POLICY_CHANGE',
     'WEB_PROMOTE', 'WEB_REJECT'));
"""


def upgrade() -> None:
    _execute_script(AUTO_PUBLISH_SQL)


def downgrade() -> None:
    _execute_script(DOWNGRADE_SQL)
