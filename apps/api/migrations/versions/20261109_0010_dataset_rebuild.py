# ruff: noqa: E501
"""Dataset rebuild without AI-generated catalog content (DEC-031..DEC-033, 2026-11-09).

* ``places.is_area`` and ``catalog_publications.is_area`` (boolean, default false): the place is
  an area (bay, peninsula, mountain range, old town …). It is published for the map and the
  Guide but is never a planner stop; ``fn_publish_place`` copies it into the snapshot and
  ``vw_published_places`` exposes it (appended column).
* ``place_localizations.description_source_revision_id`` (nullable FK): the source revision the
  displayed description comes from (Wikipedia, Wikivoyage, owner sheet), so the API can show
  attribution, licence and link next to the text.
* ``ck_place_localizations_approved_complete`` no longer requires a description: under DEC-033
  option A a place may be published with names but no description ("No description yet"). The
  code gate (``REQUIRE_DESCRIPTION`` in ``app/curation/auto_publish.py``) decides; option B is a
  one-line switch there.
* ``knowledge_chunks``: the (city, place, locale, corpus revision, section) uniqueness applies to
  PLACE chunks only (partial unique index), so a city-level corpus revision can hold several
  CITY chunks of one section (Wikivoyage "Understand", "Get around" … split ≤ 1 200 chars).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261109_0010"
down_revision: str | None = "20261108_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute_script(sql: str) -> None:
    # Colons are escaped so that literals in comments are not read as bind parameters.
    op.execute(sa.text(sql.replace(":", "\\:")))


PUBLISH_FUNCTION = """
CREATE OR REPLACE FUNCTION fn_publish_place(p_place_id uuid, p_actor_account_id uuid)
RETURNS uuid
LANGUAGE plpgsql AS $$
DECLARE
    v_violations      text;
    v_revision        integer;
    v_entrance        jsonb;
    v_corpus          integer;
    v_publication_id  uuid;
BEGIN
    PERFORM 1 FROM places WHERE id = p_place_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'place % not found', p_place_id USING ERRCODE = 'no_data_found';
    END IF;

    SELECT string_agg(g.violation_code || coalesce(':' || g.detail, ''), ', ')
      INTO v_violations
      FROM fn_publication_gate_violations(p_place_id) AS g;
    IF v_violations IS NOT NULL THEN
        RAISE EXCEPTION 'publication gate failed for place %: %', p_place_id, v_violations
            USING ERRCODE = 'check_violation';
    END IF;

    UPDATE catalog_publications
       SET state = 'SUPERSEDED', state_changed_at = now(), state_reason = 'superseded by a newer publication'
     WHERE place_id = p_place_id AND state = 'PUBLISHED';

    SELECT coalesce(max(publication_revision), 0) + 1 INTO v_revision
      FROM catalog_publications WHERE place_id = p_place_id;

    SELECT f.value INTO v_entrance
      FROM place_facts f
     WHERE f.place_id = p_place_id AND f.field_code = 'ENTRANCE_LOCATION'
       AND f.review_state = 'APPROVED' AND f.knowledge_state = 'KNOWN';

    SELECT max(kc.corpus_revision) INTO v_corpus
      FROM knowledge_chunks kc
     WHERE kc.place_id = p_place_id AND kc.scope = 'PLACE' AND kc.review_state = 'APPROVED';

    INSERT INTO catalog_publications (
        place_id, city_id, publication_revision, state, category_code, area_code, location, entrance_location,
        visit_minutes_min, visit_minutes_suggested, visit_minutes_max,
        localization_vi_id, localization_en_id, corpus_revision, published_by_account_id, is_area)
    SELECT p.id, p.city_id, v_revision, 'PUBLISHED', p.category_code, p.area_code, p.location,
           CASE WHEN v_entrance IS NULL THEN NULL
                ELSE ST_SetSRID(ST_MakePoint((v_entrance ->> 'lng')::float8, (v_entrance ->> 'lat')::float8), 4326)::geography
           END,
           p.visit_minutes_min, p.visit_minutes_suggested, p.visit_minutes_max,
           (SELECT pl.id FROM place_localizations pl
             WHERE pl.place_id = p.id AND pl.locale = 'vi' AND pl.review_state = 'APPROVED'),
           (SELECT pl.id FROM place_localizations pl
             WHERE pl.place_id = p.id AND pl.locale = 'en' AND pl.review_state = 'APPROVED'),
           v_corpus, p_actor_account_id, p.is_area
      FROM places p
     WHERE p.id = p_place_id
    RETURNING id INTO v_publication_id;

    INSERT INTO publication_facts (catalog_publication_id, place_fact_id)
    SELECT v_publication_id, f.id
      FROM place_facts f
     WHERE f.place_id = p_place_id AND f.review_state = 'APPROVED';

    INSERT INTO publication_media (catalog_publication_id, media_asset_id, ordinal)
    SELECT v_publication_id, pm.media_asset_id, pm.ordinal
      FROM place_media pm
      JOIN media_assets m ON m.id = pm.media_asset_id
     WHERE pm.place_id = p_place_id AND m.rights_state = 'CLEARED'
       AND (m.rights_expires_on IS NULL OR m.rights_expires_on > current_date);

    UPDATE places
       SET workflow_state = 'PUBLISHED', content_revision = content_revision + 1
     WHERE id = p_place_id;

    INSERT INTO catalog_audit_events (actor_account_id, entity_table, entity_id, action, to_state, detail)
    VALUES (p_actor_account_id, 'catalog_publications', v_publication_id, 'PUBLISH', 'PUBLISHED',
            jsonb_build_object('place_id', p_place_id, 'publication_revision', v_revision));

    RETURN v_publication_id;
END
$$;
"""

VIEW_COLUMNS = """
       cp.id                       AS catalog_publication_id,
       cp.place_id,
       cp.city_id,
       cp.publication_revision,
       cp.category_code,
       lv.name                     AS name_vi,
       le.name                     AS name_en,
       lv.short_description        AS short_description_vi,
       le.short_description        AS short_description_en,
       lv.description              AS description_vi,
       le.description              AS description_en,
       cp.location,
       cp.entrance_location,
       cp.visit_minutes_min,
       cp.visit_minutes_suggested,
       cp.visit_minutes_max,
       cp.corpus_revision,
       cp.published_at"""

VIEW_FROM = """
  FROM catalog_publications cp
  JOIN place_localizations lv ON lv.id = cp.localization_vi_id
  JOIN place_localizations le ON le.id = cp.localization_en_id
 WHERE cp.state = 'PUBLISHED';
"""

UPGRADE_SQL = (
    """
ALTER TABLE places ADD COLUMN is_area boolean NOT NULL DEFAULT false;
COMMENT ON COLUMN places.is_area IS 'true = an area (bay, peninsula, mountain range, old town …): published for the map and the Guide, never a planner stop (migration 0010, DEC-031).';
ALTER TABLE catalog_publications ADD COLUMN is_area boolean NOT NULL DEFAULT false;
COMMENT ON COLUMN catalog_publications.is_area IS 'Snapshot of places.is_area at publication (migration 0010); planner pools exclude true.';

ALTER TABLE place_localizations ADD COLUMN description_source_revision_id uuid;
ALTER TABLE place_localizations ADD CONSTRAINT fk_place_localizations_description_source_revision_id
    FOREIGN KEY (description_source_revision_id) REFERENCES source_revisions (id) ON DELETE RESTRICT;
CREATE INDEX ix_place_localizations_description_source_revision_id
    ON place_localizations (description_source_revision_id);
COMMENT ON COLUMN place_localizations.description_source_revision_id IS 'Source revision of the displayed description (Wikipedia, Wikivoyage, owner sheet) for attribution and licence (migration 0010, DEC-031/DEC-032). NULL when there is no description.';

ALTER TABLE place_localizations DROP CONSTRAINT ck_place_localizations_approved_complete;
ALTER TABLE place_localizations ADD CONSTRAINT ck_place_localizations_approved_complete CHECK (
    review_state NOT IN ('APPROVED', 'SUPERSEDED') OR reviewed_at IS NOT NULL);

ALTER TABLE knowledge_chunks DROP CONSTRAINT uq_knowledge_chunks_city_id_place_id_locale_corpus_revision_sec;
CREATE UNIQUE INDEX uq_knowledge_chunks_place_section
    ON knowledge_chunks (city_id, place_id, locale, corpus_revision, section) WHERE scope = 'PLACE';
"""
    + PUBLISH_FUNCTION
    + "\nCREATE OR REPLACE VIEW vw_published_places AS\nSELECT"
    + VIEW_COLUMNS
    + ",\n       cp.is_area"
    + VIEW_FROM
)

DOWNGRADE_SQL = (
    "DROP VIEW vw_published_places;\nCREATE VIEW vw_published_places AS\nSELECT"
    + VIEW_COLUMNS
    + VIEW_FROM
    + PUBLISH_FUNCTION.replace(
        ", published_by_account_id, is_area)", ", published_by_account_id)"
    ).replace("v_corpus, p_actor_account_id, p.is_area", "v_corpus, p_actor_account_id")
    + """
DROP INDEX IF EXISTS uq_knowledge_chunks_place_section;
DELETE FROM knowledge_chunks WHERE scope = 'CITY' AND chunk_index > 0;
ALTER TABLE knowledge_chunks ADD CONSTRAINT uq_knowledge_chunks_city_id_place_id_locale_corpus_revision_sec
    UNIQUE NULLS NOT DISTINCT (city_id, place_id, locale, corpus_revision, section);

UPDATE place_localizations SET description = name WHERE description IS NULL AND review_state IN ('APPROVED', 'SUPERSEDED');
ALTER TABLE place_localizations DROP CONSTRAINT ck_place_localizations_approved_complete;
ALTER TABLE place_localizations ADD CONSTRAINT ck_place_localizations_approved_complete CHECK (
    review_state NOT IN ('APPROVED', 'SUPERSEDED') OR (reviewed_at IS NOT NULL AND description IS NOT NULL));

DROP INDEX IF EXISTS ix_place_localizations_description_source_revision_id;
ALTER TABLE place_localizations DROP COLUMN description_source_revision_id;
ALTER TABLE catalog_publications DROP COLUMN is_area;
ALTER TABLE places DROP COLUMN is_area;
"""
)


def upgrade() -> None:
    _execute_script(UPGRADE_SQL)


def downgrade() -> None:
    _execute_script(DOWNGRADE_SQL)
