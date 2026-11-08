# ruff: noqa: E501
"""Fact origin and grounding (DEC-028, 2026-11-08): AI-extracted facts from supplied sources.

* ``place_facts.origin`` (text, NOT NULL, default ``SOURCE``): ``SOURCE`` (taken from an open
  data / official source record), ``OWNER`` (the owner's place sheet), ``AI_EXTRACTED`` (the
  grounded writer extracted it from cited evidence; ``enrich facts``). Existing rows backed by an
  owner-sheet source revision become ``OWNER``; every other existing row stays ``SOURCE``.
* ``place_facts.grounding`` (text, NULL): ``STRONG`` / ``WEAK`` for AI-extracted facts only (the
  model's quote overlaps the cited evidence text by at least half of its tokens, or not).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261108_0009"
down_revision: str | None = "20261108_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute_script(sql: str) -> None:
    # Colons are escaped so that literals in comments are not read as bind parameters.
    op.execute(sa.text(sql.replace(":", "\\:")))


UPGRADE_SQL = """
ALTER TABLE place_facts ADD COLUMN origin text NOT NULL DEFAULT 'SOURCE';
ALTER TABLE place_facts ADD CONSTRAINT ck_place_facts_origin CHECK (origin IN ('SOURCE', 'OWNER', 'AI_EXTRACTED'));
ALTER TABLE place_facts ADD COLUMN grounding text;
ALTER TABLE place_facts ADD CONSTRAINT ck_place_facts_grounding CHECK (grounding IN ('STRONG', 'WEAK'));
ALTER TABLE place_facts ADD CONSTRAINT ck_place_facts_grounding_origin CHECK (grounding IS NULL OR origin = 'AI_EXTRACTED');
UPDATE place_facts SET origin = 'OWNER'
 WHERE id IN (
    SELECT fe.place_fact_id
      FROM fact_evidence fe
      JOIN source_revisions sr ON sr.id = fe.source_revision_id
      JOIN sources s ON s.id = sr.source_id
      JOIN data_providers dp ON dp.id = s.data_provider_id
     WHERE dp.provider_key = 'gonarra_sheet');
COMMENT ON COLUMN place_facts.origin IS 'SOURCE | OWNER | AI_EXTRACTED (migration 0009, DEC-028): AI_EXTRACTED = extracted by the grounded writer from the cited evidence revision, never invented; label it in the UI.';
COMMENT ON COLUMN place_facts.grounding IS 'STRONG | WEAK for AI_EXTRACTED facts: the model quote overlaps the cited evidence text by >= 0.5 of its tokens (STRONG) or not (WEAK); NULL otherwise.';
"""

DOWNGRADE_SQL = """
ALTER TABLE place_facts DROP CONSTRAINT ck_place_facts_grounding_origin;
ALTER TABLE place_facts DROP CONSTRAINT ck_place_facts_grounding;
ALTER TABLE place_facts DROP COLUMN grounding;
ALTER TABLE place_facts DROP CONSTRAINT ck_place_facts_origin;
ALTER TABLE place_facts DROP COLUMN origin;
"""


def upgrade() -> None:
    _execute_script(UPGRADE_SQL)


def downgrade() -> None:
    _execute_script(DOWNGRADE_SQL)
