# ruff: noqa: E501
"""Content origin labels and grounded description enrichment (2026-11-08, D3).

* ``place_localizations.translation_origin`` gains ``AI_SUMMARY``: the description was written by
  the grounded writer from cited source revisions (``enrich descriptions``), so the API can
  label AI-summarised text (schema.sql 1.2).
* ``place_localizations.name_is_source_fallback`` (boolean, default false): the name in this
  locale is the original Vietnamese proper name, unchanged; never a machine translation.
* ``ai_invocations.purpose`` gains ``CONTENT_SUMMARY`` (offline description enrichment, no
  traveler account behind it).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261108_0007"
down_revision: str | None = "20261107_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute_script(sql: str) -> None:
    # Colons are escaped so that literals in comments are not read as bind parameters.
    op.execute(sa.text(sql.replace(":", "\\:")))


CONTENT_ORIGIN_SQL = """
ALTER TABLE place_localizations DROP CONSTRAINT ck_place_localizations_translation_origin;
ALTER TABLE place_localizations ADD CONSTRAINT ck_place_localizations_translation_origin CHECK (translation_origin IN
    ('ORIGINAL', 'HUMAN_TRANSLATION', 'AI_DRAFT', 'AI_SUMMARY'));
ALTER TABLE place_localizations ADD COLUMN name_is_source_fallback boolean NOT NULL DEFAULT false;
COMMENT ON COLUMN place_localizations.translation_origin IS 'ORIGINAL | HUMAN_TRANSLATION | AI_DRAFT | AI_SUMMARY (migration 0007; the description was written by the grounded writer from cited source revisions; label it in the UI).';
COMMENT ON COLUMN place_localizations.name_is_source_fallback IS 'true = this locale has no source name; the original Vietnamese proper name is reused unchanged (never translated).';

ALTER TABLE ai_invocations DROP CONSTRAINT ck_ai_invocations_purpose;
ALTER TABLE ai_invocations ADD CONSTRAINT ck_ai_invocations_purpose CHECK (purpose IN
    ('PLAN_GENERATE', 'PLAN_REPAIR', 'DAY_REGENERATE', 'RESEARCH', 'GUIDE_ANSWER', 'PHOTO_IDENTIFY', 'CORPUS_EMBED', 'QUERY_EMBED', 'TRANSLATION_DRAFT', 'CONTENT_SUMMARY'));
ALTER TABLE ai_invocations DROP CONSTRAINT ck_ai_invocations_traveler_purpose;
ALTER TABLE ai_invocations ADD CONSTRAINT ck_ai_invocations_traveler_purpose CHECK (
    account_id IS NOT NULL OR purpose IN ('CORPUS_EMBED', 'TRANSLATION_DRAFT', 'CONTENT_SUMMARY'));
"""

DOWNGRADE_SQL = """
DELETE FROM ai_invocations WHERE purpose = 'CONTENT_SUMMARY';
ALTER TABLE ai_invocations DROP CONSTRAINT ck_ai_invocations_traveler_purpose;
ALTER TABLE ai_invocations ADD CONSTRAINT ck_ai_invocations_traveler_purpose CHECK (
    account_id IS NOT NULL OR purpose IN ('CORPUS_EMBED', 'TRANSLATION_DRAFT'));
ALTER TABLE ai_invocations DROP CONSTRAINT ck_ai_invocations_purpose;
ALTER TABLE ai_invocations ADD CONSTRAINT ck_ai_invocations_purpose CHECK (purpose IN
    ('PLAN_GENERATE', 'PLAN_REPAIR', 'DAY_REGENERATE', 'RESEARCH', 'GUIDE_ANSWER', 'PHOTO_IDENTIFY', 'CORPUS_EMBED', 'QUERY_EMBED', 'TRANSLATION_DRAFT'));

ALTER TABLE place_localizations DROP COLUMN name_is_source_fallback;
UPDATE place_localizations SET translation_origin = 'AI_DRAFT' WHERE translation_origin = 'AI_SUMMARY';
ALTER TABLE place_localizations DROP CONSTRAINT ck_place_localizations_translation_origin;
ALTER TABLE place_localizations ADD CONSTRAINT ck_place_localizations_translation_origin CHECK (translation_origin IN
    ('ORIGINAL', 'HUMAN_TRANSLATION', 'AI_DRAFT'));
"""


def upgrade() -> None:
    _execute_script(CONTENT_ORIGIN_SQL)


def downgrade() -> None:
    _execute_script(DOWNGRADE_SQL)
