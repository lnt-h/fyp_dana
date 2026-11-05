# ruff: noqa: E501
"""Catalog schema: reference data through publications (schema.sql 1.0 Sections 1-6).

Reference data, providers and policies, places, content, provenance, media, web candidates,
closure rules, Guide corpus, publications and audit. Implements docs/data/schema.sql 1.0 Sections 1-6 plus the Section 9 triggers and views that belong
to these tables. Reference rows are seeded by `python -m app.cli seed`, not by this migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0002"
down_revision: str | None = "20261102_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute_script(sql: str) -> None:
    # Colons are escaped so that JSON/time literals in comments are not read as bind parameters.
    op.execute(sa.text(sql.replace(":", "\\:")))


SECTION_1_SQL = """
-- -----------------------------------------------------------------------------
-- Section 1 — NEW (migration 0002): extension and shared trigger functions
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- NEW: trigram index for diacritic-free alias search (Q-S1)

-- Keeps updated_at correct for writes that bypass the ORM (SQL scripts, functions).
CREATE OR REPLACE FUNCTION fn_set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END
$$;

-- Immutable rows: reject any UPDATE (DELETE stays possible so owner cascades work).
CREATE OR REPLACE FUNCTION fn_reject_update() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'rows of % are immutable; append a new revision instead', TG_TABLE_NAME
        USING ERRCODE = 'integrity_constraint_violation';
END
$$;

-- NEW (migration 0002): the existing accounts table gains only this trigger.
CREATE TRIGGER trg_accounts_set_updated_at_before
    BEFORE UPDATE ON accounts FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();


-- OQ-020: accounts_clerk_user_id_key already enforces uniqueness; the extra index from 0001 is redundant.
DROP INDEX IF EXISTS ix_accounts_clerk_user_id;
"""

SECTIONS_2_TO_4_SQL = """
-- -----------------------------------------------------------------------------
-- Section 2 — NEW (migration 0002): reference data
-- -----------------------------------------------------------------------------
CREATE TABLE cities (
    id          uuid        NOT NULL DEFAULT gen_random_uuid(),
    code        text        NOT NULL,
    name_vi     text        NOT NULL,
    name_en     text        NOT NULL,
    time_zone   text        NOT NULL DEFAULT 'Asia/Ho_Chi_Minh',
    boundary    geography(MultiPolygon, 4326),
    is_enabled  boolean     NOT NULL DEFAULT false,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_cities PRIMARY KEY (id),
    CONSTRAINT uq_cities_code UNIQUE (code),
    CONSTRAINT ck_cities_code_format CHECK (code ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
    CONSTRAINT ck_cities_time_zone CHECK (time_zone = 'Asia/Ho_Chi_Minh')
);
COMMENT ON TABLE cities IS 'Supported cities (BRU-007 rev. 1, DEC-013): only da-nang is enabled for the FYP; ha-noi, ho-chi-minh-city and hue stay disabled on the roadmap. Hội An is an area of Đà Nẵng (2025 merger), not a city. boundary is the post-merger polygon (OQ-121); optional and, when present, gates publication (OUTSIDE_CITY).';

CREATE TABLE areas (
    code        text        NOT NULL,
    city_id     uuid        NOT NULL,
    name_vi     text        NOT NULL,
    name_en     text        NOT NULL,
    boundary    geography(MultiPolygon, 4326),
    sort_order  smallint    NOT NULL DEFAULT 0,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_areas PRIMARY KEY (code),
    CONSTRAINT fk_areas_city_id FOREIGN KEY (city_id) REFERENCES cities (id) ON DELETE RESTRICT,
    CONSTRAINT uq_areas_code_city_id UNIQUE (code, city_id),
    CONSTRAINT ck_areas_code_format CHECK (code ~ '^[a-z0-9]+(-[a-z0-9]+)*$')
);
CREATE INDEX ix_areas_city_id_sort_order ON areas (city_id, sort_order);
COMMENT ON TABLE areas IS 'Travel areas of a city (DEC-013, OQ-121): curator-defined, not administrative wards. Used for the Hội An-area release gate (MET-011 rev. 1), area-scoped closure rules and the area label on places and stops. boundary is optional.';

CREATE TABLE categories (
    code        text        NOT NULL,
    name_vi     text        NOT NULL,
    name_en     text        NOT NULL,
    sort_order  smallint    NOT NULL DEFAULT 0,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_categories PRIMARY KEY (code),
    CONSTRAINT ck_categories_code_format CHECK (code ~ '^[A-Z][A-Z0-9_]*$')
);
COMMENT ON TABLE categories IS 'Curator-maintained place taxonomy shown on details (FR-003) and used for interest matching (FR-021).';

CREATE TABLE fact_fields (
    code                      text     NOT NULL,
    is_operational            boolean  NOT NULL,
    required_for_publication  boolean  NOT NULL DEFAULT false,
    value_kind                text     NOT NULL,
    stale_after_days          smallint,
    CONSTRAINT pk_fact_fields PRIMARY KEY (code),
    CONSTRAINT ck_fact_fields_code_format CHECK (code ~ '^[A-Z][A-Z0-9_]*$'),
    CONSTRAINT ck_fact_fields_value_kind CHECK (value_kind IN ('HOURS', 'MONEY', 'TEXT', 'LOCATION')),
    CONSTRAINT ck_fact_fields_stale_after_days CHECK (stale_after_days IS NULL OR stale_after_days > 0),
    CONSTRAINT ck_fact_fields_operational_staleness CHECK (NOT is_operational OR stale_after_days IS NOT NULL)
);
COMMENT ON TABLE fact_fields IS 'Fact vocabulary: which fields are operational, which gate publication (BR-004) and when they turn stale (BR-025, ASM-008).';

-- -----------------------------------------------------------------------------
-- Section 3 — NEW (migration 0002): providers, policies, staging, identities
-- -----------------------------------------------------------------------------
CREATE TABLE data_providers (
    id             uuid        NOT NULL DEFAULT gen_random_uuid(),
    provider_key   text        NOT NULL,
    display_name   text        NOT NULL,
    provider_kind  text        NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_data_providers PRIMARY KEY (id),
    CONSTRAINT uq_data_providers_provider_key UNIQUE (provider_key),
    CONSTRAINT ck_data_providers_provider_key_format CHECK (provider_key ~ '^[a-z0-9_]+$'),
    CONSTRAINT ck_data_providers_provider_kind CHECK (provider_kind IN
        ('OPEN_DATASET', 'RUNTIME_API', 'OFFICIAL_SOURCE', 'MEDIA_LIBRARY', 'AI_SERVICE', 'WEB_SEARCH', 'WEB_CONTENT'))
);
COMMENT ON TABLE data_providers IS 'Every external data or service provider that can reach a persistence boundary (BRU-004). WEB_SEARCH (Tavily) and WEB_CONTENT (fetched web pages) feed the research agent (DEC-015).';

CREATE TABLE provider_policies (
    id                uuid        NOT NULL DEFAULT gen_random_uuid(),
    data_provider_id  uuid        NOT NULL,
    policy_revision   integer     NOT NULL,
    terms_version     text        NOT NULL,
    terms_url         text        NOT NULL,
    purpose           text        NOT NULL,
    attribution_text  text,
    status            text        NOT NULL DEFAULT 'DRAFT',
    approved_at       timestamptz,
    next_review_on    date,
    created_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_provider_policies PRIMARY KEY (id),
    CONSTRAINT fk_provider_policies_data_provider_id FOREIGN KEY (data_provider_id)
        REFERENCES data_providers (id) ON DELETE RESTRICT,
    CONSTRAINT uq_provider_policies_data_provider_id_policy_revision UNIQUE (data_provider_id, policy_revision),
    CONSTRAINT ck_provider_policies_policy_revision CHECK (policy_revision > 0),
    CONSTRAINT ck_provider_policies_status CHECK (status IN ('DRAFT', 'ACTIVE', 'RETIRED')),
    CONSTRAINT ck_provider_policies_active_approved CHECK (status <> 'ACTIVE' OR approved_at IS NOT NULL)
);
CREATE UNIQUE INDEX uq_provider_policies_data_provider_id_active
    ON provider_policies (data_provider_id) WHERE status = 'ACTIVE';
COMMENT ON TABLE provider_policies IS 'Immutable policy revisions: terms, purpose, attribution, review date. One ACTIVE per provider.';

CREATE TABLE provider_field_rules (
    provider_policy_id  uuid     NOT NULL,
    field_name          text     NOT NULL,
    persistence_class   text     NOT NULL,
    max_retention       interval,
    CONSTRAINT pk_provider_field_rules PRIMARY KEY (provider_policy_id, field_name),
    CONSTRAINT fk_provider_field_rules_provider_policy_id FOREIGN KEY (provider_policy_id)
        REFERENCES provider_policies (id) ON DELETE CASCADE,
    CONSTRAINT ck_provider_field_rules_persistence_class CHECK (persistence_class IN
        ('ALLOW_CANONICAL', 'ALLOW_EPHEMERAL', 'ALLOW_IDENTIFIER_ONLY', 'DENY')),
    CONSTRAINT ck_provider_field_rules_ephemeral_retention CHECK
        (persistence_class <> 'ALLOW_EPHEMERAL' OR max_retention IS NOT NULL)
);
COMMENT ON TABLE provider_field_rules IS 'Field allowlist per policy revision. A field without a row is DENY (default deny, BRU-004).';

CREATE TABLE places (
    id                       uuid        NOT NULL DEFAULT gen_random_uuid(),
    city_id                  uuid        NOT NULL,
    area_code                text,
    slug                     text        NOT NULL,
    category_code            text,
    workflow_state           text        NOT NULL DEFAULT 'IMPORTED',
    location                 geography(Point, 4326) NOT NULL,
    visit_minutes_min        smallint,
    visit_minutes_suggested  smallint,
    visit_minutes_max        smallint,
    has_no_media             boolean     NOT NULL DEFAULT false,
    content_revision         integer     NOT NULL DEFAULT 1,
    created_at               timestamptz NOT NULL DEFAULT now(),
    updated_at               timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_places PRIMARY KEY (id),
    CONSTRAINT fk_places_city_id FOREIGN KEY (city_id) REFERENCES cities (id) ON DELETE RESTRICT,
    CONSTRAINT fk_places_category_code FOREIGN KEY (category_code) REFERENCES categories (code) ON DELETE RESTRICT,
    CONSTRAINT fk_places_area_code_city_id FOREIGN KEY (area_code, city_id)
        REFERENCES areas (code, city_id) ON DELETE RESTRICT,
    CONSTRAINT uq_places_city_id_slug UNIQUE (city_id, slug),
    CONSTRAINT uq_places_id_city_id UNIQUE (id, city_id),
    CONSTRAINT ck_places_slug_format CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
    CONSTRAINT ck_places_workflow_state CHECK (workflow_state IN
        ('IMPORTED', 'MATCH_REVIEW', 'CONTENT_REVIEW', 'READY_TO_PUBLISH', 'PUBLISHED', 'RETIRED')),
    CONSTRAINT ck_places_visit_minutes CHECK (
        (visit_minutes_min IS NULL OR visit_minutes_min > 0)
        AND (visit_minutes_min IS NULL OR visit_minutes_suggested IS NULL OR visit_minutes_min <= visit_minutes_suggested)
        AND (visit_minutes_suggested IS NULL OR visit_minutes_max IS NULL OR visit_minutes_suggested <= visit_minutes_max)
        AND (visit_minutes_max IS NULL OR visit_minutes_max <= 600)),
    CONSTRAINT ck_places_ready_complete CHECK (
        workflow_state NOT IN ('READY_TO_PUBLISH', 'PUBLISHED')
        OR (category_code IS NOT NULL AND visit_minutes_min IS NOT NULL
            AND visit_minutes_suggested IS NOT NULL AND visit_minutes_max IS NOT NULL)),
    CONSTRAINT ck_places_content_revision CHECK (content_revision > 0)
);
-- Q-I4: existing places within N m of a staging record (identity resolution).
CREATE INDEX ix_places_location_gist ON places USING gist (location);
CREATE INDEX ix_places_category_code ON places (category_code);
CREATE INDEX ix_places_area_code ON places (area_code);
COMMENT ON TABLE places IS 'Stable Gonarra place identity (candidate until published). location = place position for map and routing fallback (FR-003, FR-054). area_code = travel area within the city (DEC-013); the composite FK keeps area and place in the same city.';

CREATE TABLE import_runs (
    id                  uuid        NOT NULL DEFAULT gen_random_uuid(),
    data_provider_id    uuid        NOT NULL,
    provider_policy_id  uuid        NOT NULL,
    city_id             uuid        NOT NULL,
    release_id          text        NOT NULL,
    checksum_sha256     char(64)    NOT NULL,
    importer_version    text        NOT NULL,
    status              text        NOT NULL DEFAULT 'RUNNING',
    record_count        integer,
    accepted_count      integer,
    rejected_count      integer,
    duplicate_count     integer,
    failure_code        text,
    started_at          timestamptz NOT NULL DEFAULT now(),
    completed_at        timestamptz,
    CONSTRAINT pk_import_runs PRIMARY KEY (id),
    CONSTRAINT fk_import_runs_data_provider_id FOREIGN KEY (data_provider_id) REFERENCES data_providers (id) ON DELETE RESTRICT,
    CONSTRAINT fk_import_runs_provider_policy_id FOREIGN KEY (provider_policy_id) REFERENCES provider_policies (id) ON DELETE RESTRICT,
    CONSTRAINT fk_import_runs_city_id FOREIGN KEY (city_id) REFERENCES cities (id) ON DELETE RESTRICT,
    CONSTRAINT ck_import_runs_checksum_format CHECK (checksum_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_import_runs_status CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED')),
    CONSTRAINT ck_import_runs_completion CHECK ((status = 'RUNNING') = (completed_at IS NULL)),
    CONSTRAINT ck_import_runs_counts CHECK (
        (record_count IS NULL OR record_count >= 0) AND (accepted_count IS NULL OR accepted_count >= 0)
        AND (rejected_count IS NULL OR rejected_count >= 0) AND (duplicate_count IS NULL OR duplicate_count >= 0)),
    CONSTRAINT ck_import_runs_failure_code CHECK ((status = 'FAILED') = (failure_code IS NOT NULL))
);
-- Q-I1: replaying the same release is a no-op (FR-010).
CREATE UNIQUE INDEX uq_import_runs_succeeded_release
    ON import_runs (data_provider_id, city_id, release_id, checksum_sha256, importer_version)
    WHERE status = 'SUCCEEDED';
CREATE INDEX ix_import_runs_provider_policy_id ON import_runs (provider_policy_id);
CREATE INDEX ix_import_runs_city_id ON import_runs (city_id);
COMMENT ON TABLE import_runs IS 'One bounded open-data import (FR-009). A FAILED run never touches published rows.';

CREATE TABLE import_records (
    id                 uuid        NOT NULL DEFAULT gen_random_uuid(),
    import_run_id      uuid        NOT NULL,
    upstream_id        text        NOT NULL,
    raw_name           text        NOT NULL,
    normalized_name    text        NOT NULL,
    upstream_category  text,
    location           geography(Point, 4326) NOT NULL,
    allowed_payload    jsonb       NOT NULL DEFAULT '{}'::jsonb,
    validation_status  text        NOT NULL,
    rejection_reason   text,
    match_state        text        NOT NULL DEFAULT 'UNMATCHED',
    place_id           uuid,
    created_at         timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_import_records PRIMARY KEY (id),
    CONSTRAINT fk_import_records_import_run_id FOREIGN KEY (import_run_id) REFERENCES import_runs (id) ON DELETE CASCADE,
    CONSTRAINT fk_import_records_place_id FOREIGN KEY (place_id) REFERENCES places (id) ON DELETE SET NULL,
    CONSTRAINT uq_import_records_import_run_id_upstream_id UNIQUE (import_run_id, upstream_id),
    CONSTRAINT ck_import_records_allowed_payload_object CHECK (jsonb_typeof(allowed_payload) = 'object'),
    CONSTRAINT ck_import_records_validation_status CHECK (validation_status IN ('ACCEPTED', 'REJECTED')),
    CONSTRAINT ck_import_records_rejection_reason CHECK ((validation_status = 'REJECTED') = (rejection_reason IS NOT NULL)),
    CONSTRAINT ck_import_records_match_state CHECK (match_state IN ('UNMATCHED', 'MATCHED', 'AMBIGUOUS', 'NEW_CANDIDATE')),
    CONSTRAINT ck_import_records_normalized_lower CHECK (normalized_name = lower(normalized_name))
);
CREATE INDEX ix_import_records_place_id ON import_records (place_id);
CREATE INDEX ix_import_records_location_gist ON import_records USING gist (location);   -- Q-I3
COMMENT ON TABLE import_records IS 'Staging rows. allowed_payload holds only fields allowed by provider_field_rules of the run policy.';

CREATE TABLE external_place_identities (
    id                uuid         NOT NULL DEFAULT gen_random_uuid(),
    place_id          uuid         NOT NULL,
    data_provider_id  uuid         NOT NULL,
    upstream_id       text         NOT NULL,
    upstream_release  text,
    match_method      text         NOT NULL,
    match_confidence  numeric(4,3),
    review_state      text         NOT NULL DEFAULT 'PENDING',
    reviewed_at       timestamptz,
    created_at        timestamptz  NOT NULL DEFAULT now(),
    updated_at        timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT pk_external_place_identities PRIMARY KEY (id),
    CONSTRAINT fk_external_place_identities_place_id FOREIGN KEY (place_id) REFERENCES places (id) ON DELETE CASCADE,
    CONSTRAINT fk_external_place_identities_data_provider_id FOREIGN KEY (data_provider_id) REFERENCES data_providers (id) ON DELETE RESTRICT,
    CONSTRAINT uq_external_place_identities_data_provider_id_upstream_id UNIQUE (data_provider_id, upstream_id),
    CONSTRAINT ck_external_place_identities_match_method CHECK (match_method IN ('EXACT_ID', 'NAME_AND_DISTANCE', 'MANUAL')),
    CONSTRAINT ck_external_place_identities_match_confidence CHECK (match_confidence IS NULL OR match_confidence BETWEEN 0 AND 1),
    CONSTRAINT ck_external_place_identities_review_state CHECK (review_state IN ('PENDING', 'APPROVED', 'REJECTED')),
    CONSTRAINT ck_external_place_identities_reviewed CHECK (review_state = 'PENDING' OR reviewed_at IS NOT NULL)
);
CREATE INDEX ix_external_place_identities_place_id ON external_place_identities (place_id);
COMMENT ON TABLE external_place_identities IS 'Upstream IDs (Overture, Foursquare OS, Wikidata, Google place_id as identifier only). Prevents duplicate candidates (FR-010).';

-- -----------------------------------------------------------------------------
-- Section 4 — NEW (migration 0002): catalog content, provenance, media
-- -----------------------------------------------------------------------------
CREATE TABLE place_localizations (
    id                     uuid        NOT NULL DEFAULT gen_random_uuid(),
    place_id               uuid        NOT NULL,
    locale                 text        NOT NULL,
    localization_revision  integer     NOT NULL,
    name                   text        NOT NULL,
    short_description      text,
    description            text,
    translation_origin     text        NOT NULL,
    review_state           text        NOT NULL DEFAULT 'DRAFT',
    reviewed_at            timestamptz,
    created_at             timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_place_localizations PRIMARY KEY (id),
    CONSTRAINT fk_place_localizations_place_id FOREIGN KEY (place_id) REFERENCES places (id) ON DELETE CASCADE,
    CONSTRAINT uq_place_localizations_place_id_locale_localization_revision UNIQUE (place_id, locale, localization_revision),
    CONSTRAINT ck_place_localizations_locale CHECK (locale IN ('vi', 'en')),
    CONSTRAINT ck_place_localizations_localization_revision CHECK (localization_revision > 0),
    CONSTRAINT ck_place_localizations_translation_origin CHECK (translation_origin IN ('ORIGINAL', 'HUMAN_TRANSLATION', 'AI_DRAFT')),
    CONSTRAINT ck_place_localizations_review_state CHECK (review_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED')),
    CONSTRAINT ck_place_localizations_approved_complete CHECK (
        review_state NOT IN ('APPROVED', 'SUPERSEDED') OR (reviewed_at IS NOT NULL AND description IS NOT NULL))
);
-- Q-C2: at most one approved revision per place and locale.
CREATE UNIQUE INDEX uq_place_localizations_place_id_locale_approved
    ON place_localizations (place_id, locale) WHERE review_state = 'APPROVED';
COMMENT ON TABLE place_localizations IS 'Reviewed VI/EN names and original descriptions (BR-004, FR-011). AI_DRAFT needs curator approval (FR-019).';

CREATE TABLE place_aliases (
    id                uuid        NOT NULL DEFAULT gen_random_uuid(),
    place_id          uuid        NOT NULL,
    locale            text        NOT NULL,
    alias_kind        text        NOT NULL,
    alias             text        NOT NULL,
    alias_normalized  text        NOT NULL,
    review_state      text        NOT NULL DEFAULT 'DRAFT',
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_place_aliases PRIMARY KEY (id),
    CONSTRAINT fk_place_aliases_place_id FOREIGN KEY (place_id) REFERENCES places (id) ON DELETE CASCADE,
    CONSTRAINT uq_place_aliases_place_id_alias_normalized UNIQUE (place_id, alias_normalized),
    CONSTRAINT ck_place_aliases_locale CHECK (locale IN ('vi', 'en')),
    CONSTRAINT ck_place_aliases_alias_kind CHECK (alias_kind IN ('NAME', 'ALIAS')),
    CONSTRAINT ck_place_aliases_review_state CHECK (review_state IN ('DRAFT', 'APPROVED', 'REJECTED')),
    CONSTRAINT ck_place_aliases_normalized_lower CHECK (alias_normalized = lower(alias_normalized) AND length(alias_normalized) > 0)
);
CREATE INDEX ix_place_aliases_alias_normalized_trgm ON place_aliases USING gin (alias_normalized gin_trgm_ops);  -- Q-S1
COMMENT ON TABLE place_aliases IS 'Search forms: reviewed names and aliases, normalized by the API (lower case, diacritics removed, đ->d) for FR-002.';

CREATE TABLE sources (
    id                uuid        NOT NULL DEFAULT gen_random_uuid(),
    data_provider_id  uuid,
    publisher         text        NOT NULL,
    source_kind       text        NOT NULL,
    homepage_url      text,
    license_code      text        NOT NULL,
    attribution_text  text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_sources PRIMARY KEY (id),
    CONSTRAINT fk_sources_data_provider_id FOREIGN KEY (data_provider_id) REFERENCES data_providers (id) ON DELETE SET NULL,
    CONSTRAINT ck_sources_source_kind CHECK (source_kind IN ('OFFICIAL', 'OPEN_DATA', 'REFERENCE', 'OWN_OBSERVATION', 'WEB'))
);
CREATE INDEX ix_sources_data_provider_id ON sources (data_provider_id);
COMMENT ON TABLE sources IS 'Publisher with licence and required attribution text (FR-008, FR-016). NULL attribution blocks publication. WEB = a web site reached by the research agent (DEC-015); one source per host, one source_revisions row per fetched URL.';

CREATE TABLE source_revisions (
    id                   uuid        NOT NULL DEFAULT gen_random_uuid(),
    source_id            uuid        NOT NULL,
    locator              text        NOT NULL,
    title                text,
    retrieved_at         timestamptz NOT NULL,
    content_sha256       char(64),
    private_evidence_key text,
    created_at           timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_source_revisions PRIMARY KEY (id),
    CONSTRAINT fk_source_revisions_source_id FOREIGN KEY (source_id) REFERENCES sources (id) ON DELETE RESTRICT,
    CONSTRAINT uq_source_revisions_source_id_locator_retrieved_at UNIQUE (source_id, locator, retrieved_at),
    CONSTRAINT ck_source_revisions_content_sha256_format CHECK (content_sha256 IS NULL OR content_sha256 ~ '^[0-9a-f]{64}$')
);
CREATE TRIGGER trg_source_revisions_reject_update_before
    BEFORE UPDATE ON source_revisions FOR EACH ROW EXECUTE FUNCTION fn_reject_update();
COMMENT ON TABLE source_revisions IS 'Immutable capture of one URL/document as consulted; private_evidence_key points to an access-controlled object store key. The research agent appends one row per fetched URL (locator = URL, retrieved_at = fetched_at, content_sha256 of the page text; the text itself is EPHEMERAL in research_cache under the web_page policy).';

CREATE TABLE place_facts (
    id             uuid        NOT NULL DEFAULT gen_random_uuid(),
    place_id       uuid        NOT NULL,
    field_code     text        NOT NULL,
    fact_revision  integer     NOT NULL,
    knowledge_state text       NOT NULL,
    value          jsonb,
    verified_at    timestamptz,
    valid_until    date,
    review_state   text        NOT NULL DEFAULT 'DRAFT',
    conflict_state text        NOT NULL DEFAULT 'NONE',
    conflict_note  text,
    created_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_place_facts PRIMARY KEY (id),
    CONSTRAINT fk_place_facts_place_id FOREIGN KEY (place_id) REFERENCES places (id) ON DELETE CASCADE,
    CONSTRAINT fk_place_facts_field_code FOREIGN KEY (field_code) REFERENCES fact_fields (code) ON DELETE RESTRICT,
    CONSTRAINT uq_place_facts_place_id_field_code_fact_revision UNIQUE (place_id, field_code, fact_revision),
    CONSTRAINT ck_place_facts_fact_revision CHECK (fact_revision > 0),
    CONSTRAINT ck_place_facts_knowledge_state CHECK (knowledge_state IN ('KNOWN', 'UNKNOWN', 'NOT_APPLICABLE')),
    CONSTRAINT ck_place_facts_value_presence CHECK ((knowledge_state = 'KNOWN') = (value IS NOT NULL)),
    CONSTRAINT ck_place_facts_value_object CHECK (value IS NULL OR jsonb_typeof(value) = 'object'),
    CONSTRAINT ck_place_facts_entrance_shape CHECK (
        field_code <> 'ENTRANCE_LOCATION' OR value IS NULL
        OR (value ? 'lat' AND value ? 'lng'
            AND (value ->> 'lat')::numeric BETWEEN -90 AND 90 AND (value ->> 'lng')::numeric BETWEEN -180 AND 180)),
    CONSTRAINT ck_place_facts_review_state CHECK (review_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED')),
    CONSTRAINT ck_place_facts_approved_verified CHECK (review_state NOT IN ('APPROVED', 'SUPERSEDED') OR verified_at IS NOT NULL),
    CONSTRAINT ck_place_facts_conflict_state CHECK (conflict_state IN ('NONE', 'OPEN', 'RESOLVED')),
    CONSTRAINT ck_place_facts_conflict_note CHECK (conflict_state = 'NONE' OR conflict_note IS NOT NULL)
);
-- Q-C3: the single current approved fact per place and field.
CREATE UNIQUE INDEX uq_place_facts_place_id_field_code_approved
    ON place_facts (place_id, field_code) WHERE review_state = 'APPROVED';
CREATE INDEX ix_place_facts_field_code ON place_facts (field_code);
COMMENT ON TABLE place_facts IS 'Versioned operational/structured facts with explicit KNOWN/UNKNOWN/NOT_APPLICABLE (BR-024, FR-006, FR-012). AI never writes here (BRU-002).';

-- Approved/superseded facts are frozen except for review_state (APPROVED -> SUPERSEDED).
CREATE OR REPLACE FUNCTION fn_guard_place_fact_update() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.review_state IN ('APPROVED', 'SUPERSEDED')
       AND (to_jsonb(NEW) - 'review_state') IS DISTINCT FROM (to_jsonb(OLD) - 'review_state') THEN
        RAISE EXCEPTION 'approved fact % is immutable; create a new fact_revision', OLD.id
            USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    IF OLD.review_state = 'SUPERSEDED' AND NEW.review_state <> 'SUPERSEDED' THEN
        RAISE EXCEPTION 'superseded fact % cannot be reactivated', OLD.id
            USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER trg_place_facts_guard_update_before
    BEFORE UPDATE ON place_facts FOR EACH ROW EXECUTE FUNCTION fn_guard_place_fact_update();

CREATE TABLE fact_evidence (
    place_fact_id       uuid NOT NULL,
    source_revision_id  uuid NOT NULL,
    supported_claim     text NOT NULL,
    CONSTRAINT pk_fact_evidence PRIMARY KEY (place_fact_id, source_revision_id),
    CONSTRAINT fk_fact_evidence_place_fact_id FOREIGN KEY (place_fact_id) REFERENCES place_facts (id) ON DELETE CASCADE,
    CONSTRAINT fk_fact_evidence_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES source_revisions (id) ON DELETE RESTRICT,
    CONSTRAINT ck_fact_evidence_supported_claim CHECK (length(supported_claim) > 0)
);
CREATE INDEX ix_fact_evidence_source_revision_id ON fact_evidence (source_revision_id);
COMMENT ON TABLE fact_evidence IS 'Claim-level link fact revision -> source revision (BR-003, FR-005, FR-012).';

CREATE TABLE media_assets (
    id                  uuid        NOT NULL DEFAULT gen_random_uuid(),
    object_key          text        NOT NULL,
    content_type        text        NOT NULL,
    width_px            integer     NOT NULL,
    height_px           integer     NOT NULL,
    sha256              char(64)    NOT NULL,
    creator             text        NOT NULL,
    source_revision_id  uuid,
    license_code        text        NOT NULL,
    attribution_text    text        NOT NULL,
    rights_proof_key    text,
    rights_state        text        NOT NULL DEFAULT 'PENDING',
    rights_expires_on   date,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_media_assets PRIMARY KEY (id),
    CONSTRAINT fk_media_assets_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES source_revisions (id) ON DELETE RESTRICT,
    CONSTRAINT uq_media_assets_object_key UNIQUE (object_key),
    CONSTRAINT uq_media_assets_sha256 UNIQUE (sha256),
    CONSTRAINT ck_media_assets_content_type CHECK (content_type IN ('image/jpeg', 'image/png', 'image/webp')),
    CONSTRAINT ck_media_assets_dimensions CHECK (width_px > 0 AND height_px > 0),
    CONSTRAINT ck_media_assets_sha256_format CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_media_assets_rights_state CHECK (rights_state IN ('PENDING', 'CLEARED', 'REVOKED'))
);
CREATE INDEX ix_media_assets_source_revision_id ON media_assets (source_revision_id);
COMMENT ON TABLE media_assets IS 'S3 object reference with per-file licence, creator and attribution (own photos, Wikimedia Commons).';

CREATE TABLE place_media (
    place_id        uuid     NOT NULL,
    media_asset_id  uuid     NOT NULL,
    ordinal         smallint NOT NULL,
    alt_text_vi     text     NOT NULL,
    alt_text_en     text     NOT NULL,
    CONSTRAINT pk_place_media PRIMARY KEY (place_id, media_asset_id),
    CONSTRAINT fk_place_media_place_id FOREIGN KEY (place_id) REFERENCES places (id) ON DELETE CASCADE,
    CONSTRAINT fk_place_media_media_asset_id FOREIGN KEY (media_asset_id) REFERENCES media_assets (id) ON DELETE RESTRICT,
    CONSTRAINT uq_place_media_place_id_ordinal UNIQUE (place_id, ordinal),
    CONSTRAINT ck_place_media_ordinal CHECK (ordinal > 0)
);
CREATE INDEX ix_place_media_media_asset_id ON place_media (media_asset_id);

-- -----------------------------------------------------------------------------
-- Section 4A — NEW (migration 0002): research candidates (curator queue) and calendar rules
-- DEC-015, DEC-016. Both are curator-reviewed; the AI may propose a candidate, never publish it.
-- -----------------------------------------------------------------------------
CREATE TABLE web_place_candidates (
    id                      uuid        NOT NULL DEFAULT gen_random_uuid(),
    city_id                 uuid        NOT NULL,
    name                    text        NOT NULL,
    name_vi                 text,
    name_en                 text,
    category_guess          text,
    location                geography(Point, 4326),
    coordinate_source       text,
    google_place_id         text,
    places_check_outcome    text        NOT NULL DEFAULT 'SKIPPED',
    places_checked_at       timestamptz,
    source_revision_id      uuid        NOT NULL,
    fetched_at              timestamptz NOT NULL,
    tavily_query            text,
    extraction              jsonb       NOT NULL DEFAULT '{}'::jsonb,
    extraction_model        text,
    review_state            text        NOT NULL DEFAULT 'PENDING',
    promoted_place_id       uuid,
    reviewed_by_account_id  uuid,
    reviewed_at             timestamptz,
    review_note             text,
    times_proposed          integer     NOT NULL DEFAULT 1,
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_web_place_candidates PRIMARY KEY (id),
    CONSTRAINT fk_web_place_candidates_city_id FOREIGN KEY (city_id) REFERENCES cities (id) ON DELETE RESTRICT,
    CONSTRAINT fk_web_place_candidates_source_revision_id FOREIGN KEY (source_revision_id)
        REFERENCES source_revisions (id) ON DELETE RESTRICT,
    CONSTRAINT fk_web_place_candidates_promoted_place_id_city_id FOREIGN KEY (promoted_place_id, city_id)
        REFERENCES places (id, city_id) ON DELETE RESTRICT,
    CONSTRAINT fk_web_place_candidates_reviewed_by_account_id FOREIGN KEY (reviewed_by_account_id)
        REFERENCES accounts (id) ON DELETE SET NULL,
    CONSTRAINT uq_web_place_candidates_id_city_id UNIQUE (id, city_id),
    CONSTRAINT ck_web_place_candidates_name_length CHECK (length(name) BETWEEN 1 AND 200),
    CONSTRAINT ck_web_place_candidates_coordinate_source CHECK (
        coordinate_source IS NULL OR coordinate_source IN ('WEB_PAGE', 'TAVILY', 'OSM_NOMINATIM', 'CURATOR')),
    CONSTRAINT ck_web_place_candidates_location_source CHECK ((location IS NULL) = (coordinate_source IS NULL)),
    CONSTRAINT ck_web_place_candidates_places_check_outcome CHECK (places_check_outcome IN
        ('EXISTS_OPERATIONAL', 'EXISTS_CLOSED', 'NOT_FOUND', 'OUTSIDE_CITY', 'SKIPPED')),
    CONSTRAINT ck_web_place_candidates_places_checked CHECK (
        (places_check_outcome = 'SKIPPED') = (places_checked_at IS NULL)),
    CONSTRAINT ck_web_place_candidates_places_check_identity CHECK (
        places_check_outcome IN ('SKIPPED', 'NOT_FOUND') OR google_place_id IS NOT NULL),
    CONSTRAINT ck_web_place_candidates_extraction_object CHECK (jsonb_typeof(extraction) = 'object'),
    CONSTRAINT ck_web_place_candidates_review_state CHECK (review_state IN ('PENDING', 'PROMOTED', 'REJECTED', 'EXPIRED')),
    CONSTRAINT ck_web_place_candidates_promoted CHECK ((review_state = 'PROMOTED') = (promoted_place_id IS NOT NULL)),
    CONSTRAINT ck_web_place_candidates_reviewed CHECK (
        review_state IN ('PENDING', 'EXPIRED') OR reviewed_at IS NOT NULL),
    CONSTRAINT ck_web_place_candidates_times_proposed CHECK (times_proposed >= 1)
);
-- Google place_id is an identifier only (ADR-006); one candidate row per Google place, re-proposals bump times_proposed.
CREATE UNIQUE INDEX uq_web_place_candidates_google_place_id
    ON web_place_candidates (google_place_id) WHERE google_place_id IS NOT NULL;
-- Q-W1: curator queue, newest pending first (API-046).
CREATE INDEX ix_web_place_candidates_city_id_review_state_created_at
    ON web_place_candidates (city_id, review_state, created_at DESC);
-- Q-W2: dedupe a candidate against places and other candidates within N m before queueing.
CREATE INDEX ix_web_place_candidates_location_gist ON web_place_candidates USING gist (location);
CREATE INDEX ix_web_place_candidates_source_revision_id ON web_place_candidates (source_revision_id);
CREATE INDEX ix_web_place_candidates_promoted_place_id ON web_place_candidates (promoted_place_id);
CREATE INDEX ix_web_place_candidates_reviewed_by_account_id ON web_place_candidates (reviewed_by_account_id);
COMMENT ON TABLE web_place_candidates IS 'Curator queue of places found by the research agent (DEC-015, FR-101). Every row is WEB_UNVERIFIED until a curator promotes it: promotion creates a places row (IMPORTED), an external_place_identities row and a localization draft, then the ordinary publication gate applies. The EXPIRED sweep skips rows referenced by trip_stops.';
COMMENT ON COLUMN web_place_candidates.coordinate_source IS 'Where location came from: WEB_PAGE, TAVILY, OSM_NOMINATIM or CURATOR. Google coordinates are never stored canonically (ADR-006; ephemeral copy only in places_lookup_cache).';
COMMENT ON COLUMN web_place_candidates.places_check_outcome IS 'Gonarra verdict from the Google Places existence/status check (FR-100), not the raw Google string: EXISTS_OPERATIONAL, EXISTS_CLOSED, NOT_FOUND, OUTSIDE_CITY (outside cities.boundary) or SKIPPED (quota or check disabled).';
COMMENT ON COLUMN web_place_candidates.extraction IS 'Validated structured output of the extraction model (Pydantic-checked JSON object): hours/price/address claims as text with the supporting quote. Never copied into place_facts without curator review.';

CREATE TABLE place_closure_rules (
    id                      uuid        NOT NULL DEFAULT gen_random_uuid(),
    city_id                 uuid        NOT NULL,
    applies_to              text        NOT NULL,
    place_id                uuid,
    area_code               text,
    rule_kind               text        NOT NULL,
    effect                  text        NOT NULL,
    params                  jsonb       NOT NULL DEFAULT '{}'::jsonb,
    severity                text        NOT NULL,
    note_vi                 text        NOT NULL,
    note_en                 text        NOT NULL,
    effective_from          date,
    effective_to            date,
    source_revision_id      uuid,
    review_state            text        NOT NULL DEFAULT 'DRAFT',
    verified_at             timestamptz,
    reviewed_by_account_id  uuid,
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_place_closure_rules PRIMARY KEY (id),
    CONSTRAINT fk_place_closure_rules_city_id FOREIGN KEY (city_id) REFERENCES cities (id) ON DELETE RESTRICT,
    CONSTRAINT fk_place_closure_rules_place_id_city_id FOREIGN KEY (place_id, city_id)
        REFERENCES places (id, city_id) ON DELETE CASCADE,
    CONSTRAINT fk_place_closure_rules_area_code_city_id FOREIGN KEY (area_code, city_id)
        REFERENCES areas (code, city_id) ON DELETE RESTRICT,
    CONSTRAINT fk_place_closure_rules_source_revision_id FOREIGN KEY (source_revision_id)
        REFERENCES source_revisions (id) ON DELETE RESTRICT,
    CONSTRAINT fk_place_closure_rules_reviewed_by_account_id FOREIGN KEY (reviewed_by_account_id)
        REFERENCES accounts (id) ON DELETE SET NULL,
    CONSTRAINT ck_place_closure_rules_applies_to CHECK (applies_to IN ('PLACE', 'AREA', 'CITY')),
    CONSTRAINT ck_place_closure_rules_target CHECK (
        (applies_to = 'PLACE' AND place_id IS NOT NULL AND area_code IS NULL)
        OR (applies_to = 'AREA' AND area_code IS NOT NULL AND place_id IS NULL)
        OR (applies_to = 'CITY' AND place_id IS NULL AND area_code IS NULL)),
    CONSTRAINT ck_place_closure_rules_rule_kind CHECK (rule_kind IN
        ('WEEKLY', 'DATE', 'LUNAR_DATE', 'SEASON', 'TICKET_VALIDITY')),
    CONSTRAINT ck_place_closure_rules_effect CHECK (effect IN ('CLOSED', 'PARTIAL', 'EVENT', 'NOTICE')),
    CONSTRAINT ck_place_closure_rules_params_object CHECK (jsonb_typeof(params) = 'object'),
    CONSTRAINT ck_place_closure_rules_severity CHECK (severity IN ('BLOCKING', 'WARNING')),
    CONSTRAINT ck_place_closure_rules_notes CHECK (length(note_vi) BETWEEN 1 AND 500 AND length(note_en) BETWEEN 1 AND 500),
    CONSTRAINT ck_place_closure_rules_effective_range CHECK (
        effective_from IS NULL OR effective_to IS NULL OR effective_from <= effective_to),
    CONSTRAINT ck_place_closure_rules_review_state CHECK (review_state IN ('DRAFT', 'APPROVED', 'RETIRED')),
    CONSTRAINT ck_place_closure_rules_approved_verified CHECK (
        review_state <> 'APPROVED' OR (verified_at IS NOT NULL AND source_revision_id IS NOT NULL))
);
-- Q-H1: Plan Health loads every approved rule of the trip's city once per evaluation (FR-102).
CREATE INDEX ix_place_closure_rules_city_id_review_state ON place_closure_rules (city_id, review_state);
CREATE INDEX ix_place_closure_rules_place_id ON place_closure_rules (place_id);
CREATE INDEX ix_place_closure_rules_area_code ON place_closure_rules (area_code);
CREATE INDEX ix_place_closure_rules_source_revision_id ON place_closure_rules (source_revision_id);
CREATE INDEX ix_place_closure_rules_reviewed_by_account_id ON place_closure_rules (reviewed_by_account_id);
COMMENT ON TABLE place_closure_rules IS 'Curator-reviewed calendar rules evaluated by deterministic Plan Health code (DEC-016, FR-102, FR-107): weekly closures, fixed dates, lunar dates (Tết, Hội An lantern nights), seasons and ticket validity. AI never writes here. Only APPROVED rules are evaluated; an approved rule needs verified_at and a source.';
COMMENT ON COLUMN place_closure_rules.params IS 'Shape by rule_kind. WEEKLY {"weekdays":[1..7]} (ISO, 1 = Monday) with optional {"from":"HH:MM","to":"HH:MM"}; DATE {"dates":["YYYY-MM-DD"]} or {"month_day":["MM-DD"]} (yearly); LUNAR_DATE {"lunar_days":[1,14,15],"lunar_months":[...]|null} resolved by the pure-Python VN lunar algorithm, UTC+7 (OQ-125); SEASON {"from_month_day":"MM-DD","to_month_day":"MM-DD"}; TICKET_VALIDITY {"valid_same_day":true} or {"valid_hours":24}.';
COMMENT ON COLUMN place_closure_rules.effect IS 'CLOSED = place/area closed (BLOCKING by default); PARTIAL = reduced hours or access; EVENT = special event (e.g. lantern night, Tết); NOTICE = advisory text only.';

-- -----------------------------------------------------------------------------
"""

SECTIONS_5_TO_6_SQL = """
-- Section 5 — NEW (migration 0002): Guide corpus (pgvector), model.md §4.3
-- Place-scoped chunks (scope PLACE) and city-scoped chunks (scope CITY, DEC-017) share one table.
-- -----------------------------------------------------------------------------
CREATE TABLE knowledge_chunks (
    id               uuid        NOT NULL DEFAULT gen_random_uuid(),
    city_id          uuid        NOT NULL,
    place_id         uuid,
    scope            text        NOT NULL DEFAULT 'PLACE',
    locale           text        NOT NULL,
    section          text        NOT NULL,
    corpus_revision  integer     NOT NULL,
    chunk_index      smallint    NOT NULL,
    content          text        NOT NULL,
    content_sha256   char(64)    NOT NULL,
    embedding        vector(768),
    embedding_model  text,
    review_state     text        NOT NULL DEFAULT 'DRAFT',
    retired_at       timestamptz,
    created_at       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_knowledge_chunks PRIMARY KEY (id),
    CONSTRAINT fk_knowledge_chunks_city_id FOREIGN KEY (city_id) REFERENCES cities (id) ON DELETE RESTRICT,
    CONSTRAINT fk_knowledge_chunks_place_id_city_id FOREIGN KEY (place_id, city_id)
        REFERENCES places (id, city_id) ON DELETE CASCADE,
    -- NULLS NOT DISTINCT (PostgreSQL 15+): city-scoped rows have place_id NULL and must still be unique.
    CONSTRAINT uq_knowledge_chunks_city_id_place_id_locale_corpus_revision_chunk_index
        UNIQUE NULLS NOT DISTINCT (city_id, place_id, locale, corpus_revision, chunk_index),
    CONSTRAINT uq_knowledge_chunks_city_id_place_id_locale_corpus_revision_section
        UNIQUE NULLS NOT DISTINCT (city_id, place_id, locale, corpus_revision, section),
    CONSTRAINT ck_knowledge_chunks_scope CHECK (scope IN ('PLACE', 'CITY')),
    CONSTRAINT ck_knowledge_chunks_scope_place CHECK ((scope = 'PLACE') = (place_id IS NOT NULL)),
    CONSTRAINT ck_knowledge_chunks_locale CHECK (locale IN ('vi', 'en')),
    CONSTRAINT ck_knowledge_chunks_section CHECK (
        section IN ('OVERVIEW', 'HISTORY', 'HIGHLIGHTS', 'VISIT_TIPS', 'ETIQUETTE', 'ACCESS',
                    'CITY_OVERVIEW', 'GETTING_AROUND', 'EVENTS_CALENDAR', 'PRACTICAL')),
    CONSTRAINT ck_knowledge_chunks_section_scope CHECK (
        (scope = 'CITY') = (section IN ('CITY_OVERVIEW', 'GETTING_AROUND', 'EVENTS_CALENDAR', 'PRACTICAL'))),
    CONSTRAINT ck_knowledge_chunks_corpus_revision CHECK (corpus_revision > 0),
    CONSTRAINT ck_knowledge_chunks_chunk_index CHECK (chunk_index >= 0),
    CONSTRAINT ck_knowledge_chunks_content_length CHECK (length(content) BETWEEN 1 AND 4000),
    CONSTRAINT ck_knowledge_chunks_content_sha256_format CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_knowledge_chunks_review_state CHECK (review_state IN ('DRAFT', 'APPROVED', 'RETIRED')),
    CONSTRAINT ck_knowledge_chunks_approved_embedded CHECK (
        review_state <> 'APPROVED' OR (embedding IS NOT NULL AND embedding_model IS NOT NULL)),
    CONSTRAINT ck_knowledge_chunks_retired CHECK ((review_state = 'RETIRED') = (retired_at IS NOT NULL))
);
-- Q-G1 (ANN path): cosine HNSW over approved chunks only. Reason for HNSW over IVFFlat: model.md §4.3.
CREATE INDEX ix_knowledge_chunks_embedding_hnsw
    ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
    WHERE review_state = 'APPROVED';
-- Q-G2 (lexical leg of hybrid retrieval, ADR-010 1.0 / DEC-017) over lower-cased content; the API folds diacritics before matching.
CREATE INDEX ix_knowledge_chunks_content_trgm
    ON knowledge_chunks USING gin (lower(content) gin_trgm_ops)
    WHERE review_state = 'APPROVED';
-- Q-G3: city-scoped approved chunks of one city and locale (city Guide, DEC-017).
CREATE INDEX ix_knowledge_chunks_city_id_scope_locale_approved
    ON knowledge_chunks (city_id, scope, locale) WHERE review_state = 'APPROVED';
COMMENT ON TABLE knowledge_chunks IS 'Approved original narrative chunks for the Guide (FR-056..FR-058, FR-104), one per section per locale and corpus revision; embedded on write by the curation API (ADR-012). scope PLACE rows belong to a place; scope CITY rows (DEC-017) belong to the city only. Never a source of operational facts.';
COMMENT ON COLUMN knowledge_chunks.section IS 'Citation unit. PLACE scope: OVERVIEW, HISTORY, HIGHLIGHTS, VISIT_TIPS, ETIQUETTE, ACCESS. CITY scope: CITY_OVERVIEW, GETTING_AROUND, EVENTS_CALENDAR, PRACTICAL (ADR-010 1.0).';
COMMENT ON COLUMN knowledge_chunks.embedding IS 'gemini-embedding-001 with output_dimensionality=768, L2-normalised before storage (OQ-126); vector(768) is pinned to that model.';

CREATE TABLE knowledge_chunk_sources (
    knowledge_chunk_id  uuid NOT NULL,
    source_revision_id  uuid NOT NULL,
    CONSTRAINT pk_knowledge_chunk_sources PRIMARY KEY (knowledge_chunk_id, source_revision_id),
    CONSTRAINT fk_knowledge_chunk_sources_knowledge_chunk_id FOREIGN KEY (knowledge_chunk_id) REFERENCES knowledge_chunks (id) ON DELETE CASCADE,
    CONSTRAINT fk_knowledge_chunk_sources_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES source_revisions (id) ON DELETE RESTRICT
);
CREATE INDEX ix_knowledge_chunk_sources_source_revision_id ON knowledge_chunk_sources (source_revision_id);

-- -----------------------------------------------------------------------------
-- Section 6 — NEW (migration 0002): publication workflow and curator audit
-- -----------------------------------------------------------------------------
CREATE TABLE catalog_publications (
    id                       uuid        NOT NULL DEFAULT gen_random_uuid(),
    place_id                 uuid        NOT NULL,
    city_id                  uuid        NOT NULL,
    publication_revision     integer     NOT NULL,
    state                    text        NOT NULL DEFAULT 'PUBLISHED',
    category_code            text        NOT NULL,
    area_code                text,
    location                 geography(Point, 4326) NOT NULL,
    entrance_location        geography(Point, 4326),
    visit_minutes_min        smallint    NOT NULL,
    visit_minutes_suggested  smallint    NOT NULL,
    visit_minutes_max        smallint    NOT NULL,
    localization_vi_id       uuid        NOT NULL,
    localization_en_id       uuid        NOT NULL,
    corpus_revision          integer,
    published_by_account_id  uuid,
    published_at             timestamptz NOT NULL DEFAULT now(),
    state_changed_at         timestamptz,
    state_reason             text,
    CONSTRAINT pk_catalog_publications PRIMARY KEY (id),
    CONSTRAINT fk_catalog_publications_place_id_city_id FOREIGN KEY (place_id, city_id)
        REFERENCES places (id, city_id) ON DELETE RESTRICT,
    CONSTRAINT fk_catalog_publications_category_code FOREIGN KEY (category_code) REFERENCES categories (code) ON DELETE RESTRICT,
    CONSTRAINT fk_catalog_publications_area_code_city_id FOREIGN KEY (area_code, city_id)
        REFERENCES areas (code, city_id) ON DELETE RESTRICT,
    CONSTRAINT fk_catalog_publications_localization_vi_id FOREIGN KEY (localization_vi_id) REFERENCES place_localizations (id) ON DELETE RESTRICT,
    CONSTRAINT fk_catalog_publications_localization_en_id FOREIGN KEY (localization_en_id) REFERENCES place_localizations (id) ON DELETE RESTRICT,
    CONSTRAINT fk_catalog_publications_published_by_account_id FOREIGN KEY (published_by_account_id) REFERENCES accounts (id) ON DELETE SET NULL,
    CONSTRAINT uq_catalog_publications_place_id_publication_revision UNIQUE (place_id, publication_revision),
    CONSTRAINT uq_catalog_publications_id_place_id UNIQUE (id, place_id),
    CONSTRAINT ck_catalog_publications_publication_revision CHECK (publication_revision > 0),
    CONSTRAINT ck_catalog_publications_state CHECK (state IN ('PUBLISHED', 'SUPERSEDED', 'WITHDRAWN')),
    CONSTRAINT ck_catalog_publications_state_change CHECK ((state = 'PUBLISHED') = (state_changed_at IS NULL)),
    CONSTRAINT ck_catalog_publications_visit_minutes CHECK (
        visit_minutes_min > 0 AND visit_minutes_min <= visit_minutes_suggested
        AND visit_minutes_suggested <= visit_minutes_max AND visit_minutes_max <= 600)
);
-- Q-C1: exactly one current publication per place.
CREATE UNIQUE INDEX uq_catalog_publications_place_id_published ON catalog_publications (place_id) WHERE state = 'PUBLISHED';
-- Q-P1 / Q-E1 / Q-C4: published places of a city (planner candidates, Explore list, per-city counts FR-018).
CREATE INDEX ix_catalog_publications_city_id_category_code_published
    ON catalog_publications (city_id, category_code) WHERE state = 'PUBLISHED';
-- Q-N1: published places within 300 m of the traveler (FR-061, ASM-009).
CREATE INDEX ix_catalog_publications_location_gist_published
    ON catalog_publications USING gist (location) WHERE state = 'PUBLISHED';
CREATE INDEX ix_catalog_publications_category_code ON catalog_publications (category_code);
-- Q-C5: published places per area (Hội An-area gate, MET-011 rev. 1).
CREATE INDEX ix_catalog_publications_city_id_area_code_published
    ON catalog_publications (city_id, area_code) WHERE state = 'PUBLISHED';
CREATE INDEX ix_catalog_publications_localization_vi_id ON catalog_publications (localization_vi_id);
CREATE INDEX ix_catalog_publications_localization_en_id ON catalog_publications (localization_en_id);
CREATE INDEX ix_catalog_publications_published_by_account_id ON catalog_publications (published_by_account_id);
COMMENT ON TABLE catalog_publications IS 'Immutable publication manifest (snapshot of place attributes + exact revisions). Only state columns change.';

CREATE OR REPLACE FUNCTION fn_guard_catalog_publication_update() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    mutable_columns text[] := ARRAY['state', 'state_changed_at', 'state_reason', 'published_by_account_id'];
BEGIN
    IF (to_jsonb(NEW) - mutable_columns) IS DISTINCT FROM (to_jsonb(OLD) - mutable_columns) THEN
        RAISE EXCEPTION 'publication % is immutable except for its state', OLD.id
            USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    IF NEW.published_by_account_id IS DISTINCT FROM OLD.published_by_account_id
       AND NEW.published_by_account_id IS NOT NULL THEN
        RAISE EXCEPTION 'publication % reviewer can only be cleared by account deletion', OLD.id
            USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    IF NEW.state <> OLD.state AND OLD.state <> 'PUBLISHED' THEN
        RAISE EXCEPTION 'publication % in state % is final', OLD.id, OLD.state
            USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER trg_catalog_publications_guard_update_before
    BEFORE UPDATE ON catalog_publications FOR EACH ROW EXECUTE FUNCTION fn_guard_catalog_publication_update();

CREATE TABLE publication_facts (
    catalog_publication_id  uuid NOT NULL,
    place_fact_id           uuid NOT NULL,
    CONSTRAINT pk_publication_facts PRIMARY KEY (catalog_publication_id, place_fact_id),
    CONSTRAINT fk_publication_facts_catalog_publication_id FOREIGN KEY (catalog_publication_id) REFERENCES catalog_publications (id) ON DELETE RESTRICT,
    CONSTRAINT fk_publication_facts_place_fact_id FOREIGN KEY (place_fact_id) REFERENCES place_facts (id) ON DELETE RESTRICT
);
CREATE INDEX ix_publication_facts_place_fact_id ON publication_facts (place_fact_id);

CREATE TABLE publication_media (
    catalog_publication_id  uuid     NOT NULL,
    media_asset_id          uuid     NOT NULL,
    ordinal                 smallint NOT NULL,
    CONSTRAINT pk_publication_media PRIMARY KEY (catalog_publication_id, media_asset_id),
    CONSTRAINT fk_publication_media_catalog_publication_id FOREIGN KEY (catalog_publication_id) REFERENCES catalog_publications (id) ON DELETE RESTRICT,
    CONSTRAINT fk_publication_media_media_asset_id FOREIGN KEY (media_asset_id) REFERENCES media_assets (id) ON DELETE RESTRICT,
    CONSTRAINT ck_publication_media_ordinal CHECK (ordinal > 0)
);
CREATE INDEX ix_publication_media_media_asset_id ON publication_media (media_asset_id);

CREATE TABLE catalog_audit_events (
    id                bigint      GENERATED ALWAYS AS IDENTITY,
    actor_account_id  uuid,
    entity_table      text        NOT NULL,
    entity_id         uuid        NOT NULL,
    action            text        NOT NULL,
    from_state        text,
    to_state          text,
    detail            jsonb       NOT NULL DEFAULT '{}'::jsonb,
    occurred_at       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_catalog_audit_events PRIMARY KEY (id),
    CONSTRAINT fk_catalog_audit_events_actor_account_id FOREIGN KEY (actor_account_id) REFERENCES accounts (id) ON DELETE SET NULL,
    CONSTRAINT ck_catalog_audit_events_action CHECK (action IN
        ('IMPORT', 'MATCH_REVIEW', 'CONTENT_REVIEW', 'FACT_REVIEW', 'MEDIA_REVIEW', 'PUBLISH', 'WITHDRAW', 'POLICY_CHANGE',
         'WEB_PROMOTE', 'WEB_REJECT')),
    CONSTRAINT ck_catalog_audit_events_detail_object CHECK (jsonb_typeof(detail) = 'object')
);
CREATE INDEX ix_catalog_audit_events_entity_table_entity_id_occurred_at
    ON catalog_audit_events (entity_table, entity_id, occurred_at);                       -- Q-A1
CREATE INDEX ix_catalog_audit_events_actor_account_id ON catalog_audit_events (actor_account_id);
COMMENT ON TABLE catalog_audit_events IS 'Append-only curator audit trail (FR-015, NFR-015). App role has INSERT/SELECT only. WEB_PROMOTE / WEB_REJECT record curator decisions on web_place_candidates (FR-101); closure-rule reviews are recorded with entity_table = place_closure_rules and FACT_REVIEW.';

-- Publication gate (BR-004, BRU-003, FR-013, FR-016): returns one row per violation; empty = publishable.
CREATE OR REPLACE FUNCTION fn_publication_gate_violations(p_place_id uuid)
RETURNS TABLE (violation_code text, detail text)
LANGUAGE sql STABLE AS $$
    SELECT 'PLACE_NOT_READY', p.workflow_state
      FROM places p
     WHERE p.id = p_place_id AND p.workflow_state NOT IN ('READY_TO_PUBLISH', 'PUBLISHED')
    UNION ALL
    SELECT 'MISSING_LOCALIZATION', l.locale
      FROM (VALUES ('vi'), ('en')) AS l(locale)
     WHERE NOT EXISTS (SELECT 1 FROM place_localizations pl
                        WHERE pl.place_id = p_place_id AND pl.locale = l.locale AND pl.review_state = 'APPROVED')
    UNION ALL
    SELECT 'MISSING_SEARCH_NAME', l.locale
      FROM (VALUES ('vi'), ('en')) AS l(locale)
     WHERE NOT EXISTS (SELECT 1 FROM place_aliases a
                        WHERE a.place_id = p_place_id AND a.locale = l.locale
                          AND a.alias_kind = 'NAME' AND a.review_state = 'APPROVED')
    UNION ALL
    SELECT 'MISSING_REQUIRED_FACT', ff.code
      FROM fact_fields ff
     WHERE ff.required_for_publication
       AND NOT EXISTS (SELECT 1 FROM place_facts f
                        WHERE f.place_id = p_place_id AND f.field_code = ff.code AND f.review_state = 'APPROVED')
    UNION ALL
    SELECT 'FACT_WITHOUT_SOURCE', f.field_code
      FROM place_facts f
      JOIN fact_fields ff ON ff.code = f.field_code
     WHERE f.place_id = p_place_id AND f.review_state = 'APPROVED' AND ff.is_operational
       AND NOT EXISTS (SELECT 1 FROM fact_evidence e WHERE e.place_fact_id = f.id)
    UNION ALL
    SELECT 'FACT_CONFLICT_OPEN', f.field_code
      FROM place_facts f
     WHERE f.place_id = p_place_id AND f.review_state IN ('DRAFT', 'APPROVED') AND f.conflict_state = 'OPEN'
    UNION ALL
    SELECT DISTINCT 'SOURCE_WITHOUT_ATTRIBUTION', s.publisher
      FROM sources s
      JOIN source_revisions sr ON sr.source_id = s.id
     WHERE s.attribution_text IS NULL
       AND (EXISTS (SELECT 1 FROM fact_evidence e JOIN place_facts f ON f.id = e.place_fact_id
                     WHERE e.source_revision_id = sr.id AND f.place_id = p_place_id AND f.review_state = 'APPROVED')
            OR EXISTS (SELECT 1 FROM knowledge_chunk_sources ks JOIN knowledge_chunks kc ON kc.id = ks.knowledge_chunk_id
                        WHERE ks.source_revision_id = sr.id AND kc.place_id = p_place_id AND kc.review_state = 'APPROVED'))
    UNION ALL
    SELECT 'CHUNK_WITHOUT_SOURCE', kc.id::text
      FROM knowledge_chunks kc
     WHERE kc.place_id = p_place_id AND kc.review_state = 'APPROVED'
       AND NOT EXISTS (SELECT 1 FROM knowledge_chunk_sources ks WHERE ks.knowledge_chunk_id = kc.id)
    UNION ALL
    SELECT 'MEDIA_RIGHTS_MISSING', NULL
      FROM places p
     WHERE p.id = p_place_id AND NOT p.has_no_media
       AND NOT EXISTS (SELECT 1 FROM place_media pm JOIN media_assets m ON m.id = pm.media_asset_id
                        WHERE pm.place_id = p.id AND m.rights_state = 'CLEARED'
                          AND (m.rights_expires_on IS NULL OR m.rights_expires_on > current_date))
    UNION ALL
    SELECT 'IDENTITY_UNREVIEWED', i.upstream_id
      FROM external_place_identities i
     WHERE i.place_id = p_place_id AND i.review_state = 'PENDING'
    UNION ALL
    SELECT 'OUTSIDE_CITY', c.code
      FROM places p
      JOIN cities c ON c.id = p.city_id
     WHERE p.id = p_place_id AND c.boundary IS NOT NULL AND NOT ST_Covers(c.boundary, p.location)
$$;

-- The only publish path (FR-014): gate, supersede, snapshot, audit — one transaction.
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
        localization_vi_id, localization_en_id, corpus_revision, published_by_account_id)
    SELECT p.id, p.city_id, v_revision, 'PUBLISHED', p.category_code, p.area_code, p.location,
           CASE WHEN v_entrance IS NULL THEN NULL
                ELSE ST_SetSRID(ST_MakePoint((v_entrance ->> 'lng')::float8, (v_entrance ->> 'lat')::float8), 4326)::geography
           END,
           p.visit_minutes_min, p.visit_minutes_suggested, p.visit_minutes_max,
           (SELECT pl.id FROM place_localizations pl
             WHERE pl.place_id = p.id AND pl.locale = 'vi' AND pl.review_state = 'APPROVED'),
           (SELECT pl.id FROM place_localizations pl
             WHERE pl.place_id = p.id AND pl.locale = 'en' AND pl.review_state = 'APPROVED'),
           v_corpus, p_actor_account_id
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

-- Unpublish (FR-017): withdraw the current publication and return the place to the candidate set.
CREATE OR REPLACE FUNCTION fn_withdraw_place(p_place_id uuid, p_actor_account_id uuid, p_reason text)
RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    v_publication_id uuid;
BEGIN
    IF p_reason IS NULL OR length(p_reason) = 0 THEN
        RAISE EXCEPTION 'a withdrawal reason is required' USING ERRCODE = 'check_violation';
    END IF;
    PERFORM 1 FROM places WHERE id = p_place_id FOR UPDATE;
    UPDATE catalog_publications
       SET state = 'WITHDRAWN', state_changed_at = now(), state_reason = p_reason
     WHERE place_id = p_place_id AND state = 'PUBLISHED'
    RETURNING id INTO v_publication_id;
    IF v_publication_id IS NULL THEN
        RAISE EXCEPTION 'place % has no current publication', p_place_id USING ERRCODE = 'no_data_found';
    END IF;
    UPDATE places SET workflow_state = 'CONTENT_REVIEW' WHERE id = p_place_id;
    INSERT INTO catalog_audit_events (actor_account_id, entity_table, entity_id, action, from_state, to_state, detail)
    VALUES (p_actor_account_id, 'catalog_publications', v_publication_id, 'WITHDRAW', 'PUBLISHED', 'WITHDRAWN',
            jsonb_build_object('place_id', p_place_id, 'reason', p_reason));
END
$$;
"""

SECTION_9_SQL = """
CREATE TRIGGER trg_cities_set_updated_at_before BEFORE UPDATE ON cities FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_categories_set_updated_at_before BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_data_providers_set_updated_at_before BEFORE UPDATE ON data_providers FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_places_set_updated_at_before BEFORE UPDATE ON places FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_external_place_identities_set_updated_at_before BEFORE UPDATE ON external_place_identities FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_place_aliases_set_updated_at_before BEFORE UPDATE ON place_aliases FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_sources_set_updated_at_before BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_media_assets_set_updated_at_before BEFORE UPDATE ON media_assets FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Not in schema.sql 1.0 Section 9 but these tables carry updated_at (contract gap, see T-02 report).
CREATE TRIGGER trg_areas_set_updated_at_before BEFORE UPDATE ON areas FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_web_place_candidates_set_updated_at_before BEFORE UPDATE ON web_place_candidates FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_place_closure_rules_set_updated_at_before BEFORE UPDATE ON place_closure_rules FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Published places with both localizations (Explore FR-003, planner candidates Q-P1). Excludes candidates (BR-002).
CREATE VIEW vw_published_places AS
SELECT cp.id                       AS catalog_publication_id,
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
       cp.published_at
  FROM catalog_publications cp
  JOIN place_localizations lv ON lv.id = cp.localization_vi_id
  JOIN place_localizations le ON le.id = cp.localization_en_id
 WHERE cp.state = 'PUBLISHED';

-- Facts of the current publication with source, verification date and stale flag (FR-005..FR-008, BR-025).
CREATE VIEW vw_published_place_facts AS
SELECT cp.place_id,
       cp.id                AS catalog_publication_id,
       f.id                 AS place_fact_id,
       f.field_code,
       ff.is_operational,
       f.knowledge_state,
       f.value,
       f.verified_at,
       f.valid_until,
       (ff.is_operational
        AND (f.verified_at < now() - make_interval(days => ff.stale_after_days)
             OR (f.valid_until IS NOT NULL AND f.valid_until < current_date))) AS is_stale,
       (SELECT jsonb_agg(jsonb_build_object(
                   'source_revision_id', sr.id, 'publisher', s.publisher, 'locator', sr.locator,
                   'retrieved_at', sr.retrieved_at, 'license_code', s.license_code,
                   'attribution_text', s.attribution_text) ORDER BY sr.retrieved_at DESC)
          FROM fact_evidence e
          JOIN source_revisions sr ON sr.id = e.source_revision_id
          JOIN sources s ON s.id = sr.source_id
         WHERE e.place_fact_id = f.id) AS sources
  FROM catalog_publications cp
  JOIN publication_facts pf ON pf.catalog_publication_id = cp.id
  JOIN place_facts f ON f.id = pf.place_fact_id
  JOIN fact_fields ff ON ff.code = f.field_code
 WHERE cp.state = 'PUBLISHED';

-- Guide evidence corpus: approved chunks of the corpus revision pinned by each current publication (FR-058).
-- Tier 1 reads one place's chunks exactly; Tier 2 (roadmap) searches the whole view (ADR-010 0.3).
CREATE VIEW vw_guide_chunks AS
SELECT kc.id AS knowledge_chunk_id,
       kc.place_id,
       cp.city_id,
       kc.locale,
       kc.section,
       kc.corpus_revision,
       kc.content,
       kc.embedding,
       kc.embedding_model
  FROM knowledge_chunks kc
  JOIN catalog_publications cp
    ON cp.place_id = kc.place_id AND cp.state = 'PUBLISHED' AND cp.corpus_revision = kc.corpus_revision
 WHERE kc.review_state = 'APPROVED';
"""

DOWNGRADE_SQL = """
DROP VIEW IF EXISTS vw_guide_chunks;
DROP VIEW IF EXISTS vw_published_place_facts;
DROP VIEW IF EXISTS vw_published_places;
DROP FUNCTION IF EXISTS fn_withdraw_place(uuid, uuid, text);
DROP FUNCTION IF EXISTS fn_publish_place(uuid, uuid);
DROP FUNCTION IF EXISTS fn_publication_gate_violations(uuid);
DROP TABLE IF EXISTS
    catalog_audit_events, publication_media, publication_facts, catalog_publications,
    knowledge_chunk_sources, knowledge_chunks, place_closure_rules, web_place_candidates,
    place_media, media_assets, fact_evidence, place_facts, source_revisions, sources,
    place_aliases, place_localizations, external_place_identities, import_records, import_runs,
    places, provider_field_rules, provider_policies, data_providers,
    fact_fields, categories, areas, cities;
DROP FUNCTION IF EXISTS fn_guard_catalog_publication_update();
DROP FUNCTION IF EXISTS fn_guard_place_fact_update();
DROP TRIGGER IF EXISTS trg_accounts_set_updated_at_before ON accounts;
DROP FUNCTION IF EXISTS fn_reject_update();
DROP FUNCTION IF EXISTS fn_set_updated_at();
DROP EXTENSION IF EXISTS pg_trgm;
CREATE UNIQUE INDEX IF NOT EXISTS ix_accounts_clerk_user_id ON accounts (clerk_user_id);
"""


def upgrade() -> None:
    _execute_script(SECTION_1_SQL)
    _execute_script(SECTIONS_2_TO_4_SQL)
    _execute_script(SECTIONS_5_TO_6_SQL)
    _execute_script(SECTION_9_SQL)


def downgrade() -> None:
    _execute_script(DOWNGRADE_SQL)
