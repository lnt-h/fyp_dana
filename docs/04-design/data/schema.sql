-- =============================================================================
-- Gonarra physical schema — GONARRA-DATA v0.1 (Draft)
-- DBMS:      PostgreSQL 16 + PostGIS + pgvector (+ pgcrypto, pg_trgm), AWS RDS db.t4g.micro
-- Owner:     Lê Ngọc Tấn Hiền · Approver: trantrongminh (Pending) · Date: 2026-11-04
-- Prompt:    design/databaseDesign_SQL_prompt.md v2.0 + design/databaseDesign_VectorDB_prompt.md v2.0
--            (adapted copies in docs/00-governance/prompt-templates/design/, kit commit 6996dae)
-- Narrative: docs/04-design/data/data-model.md (section numbers below refer to it)
--
-- This file is the design contract. Alembic revisions in apps/api/migrations/versions
-- implement it (model.md §9). It applies cleanly to an EMPTY database:
--   * Section 0 reproduces what migration 20261102_0001_foundation ALREADY creates
--     (marked "EXISTS"). Migration 0002+ must NOT re-create those objects.
--   * Sections 1-9 are NEW objects (migrations 0002_catalog, 0003_planning, 0004_study).
-- Enumerations are TEXT + CHECK (not CREATE TYPE) so Alembic can extend them with a
-- plain constraint swap instead of ALTER TYPE.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Section 0 — EXISTS in 20261102_0001_foundation (apps/api/app/models/account.py)
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- EXISTS: gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS postgis;    -- EXISTS: geography(Point,4326), GIST
CREATE EXTENSION IF NOT EXISTS vector;     -- EXISTS: pgvector

CREATE TABLE IF NOT EXISTS accounts (      -- EXISTS: identity mapping Clerk subject -> account UUID
    id            uuid         NOT NULL DEFAULT gen_random_uuid(),
    clerk_user_id varchar(255) NOT NULL,
    created_at    timestamptz  NOT NULL DEFAULT now(),
    updated_at    timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT accounts_pkey PRIMARY KEY (id),
    CONSTRAINT accounts_clerk_user_id_key UNIQUE (clerk_user_id)
);
-- EXISTS: redundant with accounts_clerk_user_id_key; proposed for removal (OQ-020).
CREATE UNIQUE INDEX IF NOT EXISTS ix_accounts_clerk_user_id ON accounts (clerk_user_id);

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
COMMENT ON TABLE cities IS 'Five launch cities (BRU-007). boundary is optional and, when present, gates publication (OUTSIDE_CITY).';

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
        ('OPEN_DATASET', 'RUNTIME_API', 'OFFICIAL_SOURCE', 'MEDIA_LIBRARY', 'AI_SERVICE'))
);
COMMENT ON TABLE data_providers IS 'Every external data or service provider that can reach a persistence boundary (BRU-004).';

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
COMMENT ON TABLE places IS 'Stable Gonarra place identity (candidate until published). location = place position for map and routing fallback (FR-003, FR-054).';

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
    name_is_source_fallback boolean    NOT NULL DEFAULT false,  -- migration 0007
    review_state           text        NOT NULL DEFAULT 'DRAFT',
    reviewed_at            timestamptz,
    created_at             timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_place_localizations PRIMARY KEY (id),
    CONSTRAINT fk_place_localizations_place_id FOREIGN KEY (place_id) REFERENCES places (id) ON DELETE CASCADE,
    CONSTRAINT uq_place_localizations_place_id_locale_localization_revision UNIQUE (place_id, locale, localization_revision),
    CONSTRAINT ck_place_localizations_locale CHECK (locale IN ('vi', 'en')),
    CONSTRAINT ck_place_localizations_localization_revision CHECK (localization_revision > 0),
    CONSTRAINT ck_place_localizations_translation_origin CHECK (translation_origin IN ('ORIGINAL', 'HUMAN_TRANSLATION', 'AI_DRAFT', 'AI_SUMMARY')),
    CONSTRAINT ck_place_localizations_review_state CHECK (review_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED')),
    CONSTRAINT ck_place_localizations_approved_complete CHECK (
        review_state NOT IN ('APPROVED', 'SUPERSEDED') OR (reviewed_at IS NOT NULL AND description IS NOT NULL))
);
-- Q-C2: at most one approved revision per place and locale.
CREATE UNIQUE INDEX uq_place_localizations_place_id_locale_approved
    ON place_localizations (place_id, locale) WHERE review_state = 'APPROVED';
COMMENT ON TABLE place_localizations IS 'Reviewed VI/EN names and original descriptions (BR-004, FR-011). AI_DRAFT needs curator approval (FR-019).';
COMMENT ON COLUMN place_localizations.translation_origin IS 'ORIGINAL | HUMAN_TRANSLATION | AI_DRAFT | AI_SUMMARY (migration 0007; the description was written by the grounded writer from cited source revisions; label it in the UI).';
COMMENT ON COLUMN place_localizations.name_is_source_fallback IS 'true = this locale has no source name; the original Vietnamese proper name is reused unchanged (never translated).';

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
    CONSTRAINT ck_sources_source_kind CHECK (source_kind IN ('OFFICIAL', 'OPEN_DATA', 'REFERENCE', 'OWN_OBSERVATION'))
);
CREATE INDEX ix_sources_data_provider_id ON sources (data_provider_id);
COMMENT ON TABLE sources IS 'Publisher with licence and required attribution text (FR-008, FR-016). NULL attribution blocks publication.';

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
COMMENT ON TABLE source_revisions IS 'Immutable capture of one URL/document as consulted; private_evidence_key points to an access-controlled S3 object.';

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
    origin         text        NOT NULL DEFAULT 'SOURCE',  -- migration 0009, DEC-028
    grounding      text,                                   -- migration 0009, DEC-028
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
    CONSTRAINT ck_place_facts_conflict_note CHECK (conflict_state = 'NONE' OR conflict_note IS NOT NULL),
    CONSTRAINT ck_place_facts_origin CHECK (origin IN ('SOURCE', 'OWNER', 'AI_EXTRACTED')),
    CONSTRAINT ck_place_facts_grounding CHECK (grounding IN ('STRONG', 'WEAK')),
    CONSTRAINT ck_place_facts_grounding_origin CHECK (grounding IS NULL OR origin = 'AI_EXTRACTED')
);
-- Q-C3: the single current approved fact per place and field.
CREATE UNIQUE INDEX uq_place_facts_place_id_field_code_approved
    ON place_facts (place_id, field_code) WHERE review_state = 'APPROVED';
CREATE INDEX ix_place_facts_field_code ON place_facts (field_code);
COMMENT ON TABLE place_facts IS 'Versioned operational/structured facts with explicit KNOWN/UNKNOWN/NOT_APPLICABLE (BR-024, FR-006, FR-012). AI never invents facts; AI_EXTRACTED rows are extracted from a cited evidence revision by the grounded writer and parsed by code (DEC-028, revises BRU-002).';
COMMENT ON COLUMN place_facts.origin IS 'SOURCE | OWNER | AI_EXTRACTED (migration 0009, DEC-028): AI_EXTRACTED = extracted by the grounded writer from the cited evidence revision, never invented; label it in the UI.';
COMMENT ON COLUMN place_facts.grounding IS 'STRONG | WEAK for AI_EXTRACTED facts: the model quote overlaps the cited evidence text by >= 0.5 of its tokens (STRONG) or not (WEAK); NULL otherwise.';

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
-- Section 5 — NEW (migration 0002): Guide corpus (pgvector), model.md §4.3
-- -----------------------------------------------------------------------------
CREATE TABLE knowledge_chunks (
    id               uuid        NOT NULL DEFAULT gen_random_uuid(),
    place_id         uuid        NOT NULL,
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
    CONSTRAINT fk_knowledge_chunks_place_id FOREIGN KEY (place_id) REFERENCES places (id) ON DELETE CASCADE,
    CONSTRAINT uq_knowledge_chunks_place_id_locale_corpus_revision_chunk_index
        UNIQUE (place_id, locale, corpus_revision, chunk_index),
    CONSTRAINT uq_knowledge_chunks_place_id_locale_corpus_revision_section
        UNIQUE (place_id, locale, corpus_revision, section),
    CONSTRAINT ck_knowledge_chunks_locale CHECK (locale IN ('vi', 'en')),
    CONSTRAINT ck_knowledge_chunks_section CHECK (
        section IN ('OVERVIEW', 'HISTORY', 'HIGHLIGHTS', 'VISIT_TIPS', 'ETIQUETTE', 'ACCESS')),
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
-- Tier 2 (roadmap, ADR-010 0.3) lexical leg of hybrid retrieval over NFC-normalised, diacritic-folded content.
CREATE INDEX ix_knowledge_chunks_content_trgm
    ON knowledge_chunks USING gin (lower(content) gin_trgm_ops)
    WHERE review_state = 'APPROVED';
COMMENT ON TABLE knowledge_chunks IS 'Approved original narrative chunks for the Guide (FR-056..FR-058), one per section per locale and corpus revision; embedded on write by the curation API (ADR-012). Never a source of operational facts.';
COMMENT ON COLUMN knowledge_chunks.section IS 'Citation unit: OVERVIEW, HISTORY, HIGHLIGHTS, VISIT_TIPS, ETIQUETTE or ACCESS (ADR-010 0.3).';

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
        ('IMPORT', 'MATCH_REVIEW', 'CONTENT_REVIEW', 'FACT_REVIEW', 'MEDIA_REVIEW', 'PUBLISH', 'WITHDRAW', 'POLICY_CHANGE')),
    CONSTRAINT ck_catalog_audit_events_detail_object CHECK (jsonb_typeof(detail) = 'object')
);
CREATE INDEX ix_catalog_audit_events_entity_table_entity_id_occurred_at
    ON catalog_audit_events (entity_table, entity_id, occurred_at);                       -- Q-A1
CREATE INDEX ix_catalog_audit_events_actor_account_id ON catalog_audit_events (actor_account_id);
COMMENT ON TABLE catalog_audit_events IS 'Append-only curator audit trail (FR-015, NFR-015). App role has INSERT/SELECT only.';

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
      FROM knowledge_chunks kc WHERE kc.place_id = p_place_id AND kc.review_state = 'APPROVED';

    INSERT INTO catalog_publications (
        place_id, city_id, publication_revision, state, category_code, location, entrance_location,
        visit_minutes_min, visit_minutes_suggested, visit_minutes_max,
        localization_vi_id, localization_en_id, corpus_revision, published_by_account_id)
    SELECT p.id, p.city_id, v_revision, 'PUBLISHED', p.category_code, p.location,
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

-- -----------------------------------------------------------------------------
-- Section 7 — NEW (migration 0003): private planning data (owner-scoped)
-- -----------------------------------------------------------------------------
CREATE TABLE account_preferences (
    account_id                   uuid        NOT NULL,
    locale                       text        NOT NULL DEFAULT 'vi',
    pace                         text,
    interest_category_codes      text[]      NOT NULL DEFAULT '{}',
    allowed_modes                text[]      NOT NULL DEFAULT '{WALK,DRIVE}',
    day_start_time               time,
    day_end_time                 time,
    ai_notice_acknowledged_at    timestamptz,
    created_at                   timestamptz NOT NULL DEFAULT now(),
    updated_at                   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_account_preferences PRIMARY KEY (account_id),
    CONSTRAINT fk_account_preferences_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    CONSTRAINT ck_account_preferences_locale CHECK (locale IN ('vi', 'en')),
    CONSTRAINT ck_account_preferences_pace CHECK (pace IS NULL OR pace IN ('RELAXED', 'BALANCED', 'PACKED')),
    CONSTRAINT ck_account_preferences_allowed_modes CHECK (
        cardinality(allowed_modes) > 0 AND allowed_modes <@ ARRAY['WALK', 'DRIVE']::text[]),
    CONSTRAINT ck_account_preferences_interest_count CHECK (cardinality(interest_category_codes) <= 20),
    CONSTRAINT ck_account_preferences_day_window CHECK (
        day_start_time IS NULL OR day_end_time IS NULL OR day_start_time < day_end_time)
);
COMMENT ON TABLE account_preferences IS 'Explicitly saved language, preferences (FR-073, FR-075) and AI-notice acknowledgement (FR-074). No free-text memory.';

CREATE TABLE trips (
    id                    uuid        NOT NULL DEFAULT gen_random_uuid(),
    account_id            uuid        NOT NULL,
    city_id               uuid        NOT NULL,
    title                 text,
    start_date            date,
    day_count             smallint    NOT NULL,
    status                text        NOT NULL DEFAULT 'DRAFT',
    revision              integer     NOT NULL DEFAULT 0,
    planning_preferences  jsonb       NOT NULL DEFAULT '{}'::jsonb,
    saved_at              timestamptz,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_trips PRIMARY KEY (id),
    CONSTRAINT fk_trips_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    CONSTRAINT fk_trips_city_id FOREIGN KEY (city_id) REFERENCES cities (id) ON DELETE RESTRICT,
    CONSTRAINT uq_trips_id_city_id UNIQUE (id, city_id),
    CONSTRAINT uq_trips_id_account_id UNIQUE (id, account_id),
    CONSTRAINT ck_trips_day_count CHECK (day_count BETWEEN 1 AND 3),
    CONSTRAINT ck_trips_status CHECK (status IN ('DRAFT', 'SAVED')),
    CONSTRAINT ck_trips_revision CHECK (revision >= 0),
    CONSTRAINT ck_trips_saved_revision CHECK ((status = 'SAVED') = (revision > 0 AND saved_at IS NOT NULL)),
    CONSTRAINT ck_trips_title_length CHECK (title IS NULL OR length(title) <= 120),
    CONSTRAINT ck_trips_planning_preferences_object CHECK (jsonb_typeof(planning_preferences) = 'object')
);
-- Q-T1: list my trips, most recent first (FR-045).
CREATE INDEX ix_trips_account_id_updated_at ON trips (account_id, updated_at DESC);
CREATE INDEX ix_trips_city_id ON trips (city_id);
COMMENT ON TABLE trips IS 'Trip header; revision = accepted (saved) version, advanced only by explicit Save (BR-011, FR-040..FR-042). One city, 1-3 days (BRU-007).';

CREATE TABLE trip_days (
    id                uuid     NOT NULL DEFAULT gen_random_uuid(),
    trip_id           uuid     NOT NULL,
    day_index         smallint NOT NULL,
    day_window_start  time     NOT NULL,
    day_window_end    time     NOT NULL,
    CONSTRAINT pk_trip_days PRIMARY KEY (id),
    CONSTRAINT fk_trip_days_trip_id FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE CASCADE,
    CONSTRAINT uq_trip_days_trip_id_day_index UNIQUE (trip_id, day_index),
    CONSTRAINT uq_trip_days_id_trip_id UNIQUE (id, trip_id),
    CONSTRAINT ck_trip_days_day_index CHECK (day_index BETWEEN 1 AND 3),
    CONSTRAINT ck_trip_days_window CHECK (day_window_start < day_window_end)
);

CREATE OR REPLACE FUNCTION fn_check_trip_day_index() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_day_count smallint;
BEGIN
    SELECT day_count INTO v_day_count FROM trips WHERE id = NEW.trip_id;
    IF NEW.day_index > v_day_count THEN
        RAISE EXCEPTION 'day_index % exceeds trip day_count %', NEW.day_index, v_day_count
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END
$$;
CREATE TRIGGER trg_trip_days_check_day_index_before
    BEFORE INSERT OR UPDATE OF day_index, trip_id ON trip_days
    FOR EACH ROW EXECUTE FUNCTION fn_check_trip_day_index();

CREATE TABLE trip_stops (
    id                      uuid     NOT NULL,
    trip_id                 uuid     NOT NULL,
    trip_day_id             uuid     NOT NULL,
    city_id                 uuid     NOT NULL,
    place_id                uuid     NOT NULL,
    catalog_publication_id  uuid     NOT NULL,
    ordinal                 smallint NOT NULL,
    planned_arrival         time     NOT NULL,
    planned_departure       time     NOT NULL,
    visit_minutes           smallint NOT NULL,
    is_locked               boolean  NOT NULL DEFAULT false,
    CONSTRAINT pk_trip_stops PRIMARY KEY (id),
    CONSTRAINT fk_trip_stops_trip_day_id_trip_id FOREIGN KEY (trip_day_id, trip_id)
        REFERENCES trip_days (id, trip_id) ON DELETE CASCADE,
    CONSTRAINT fk_trip_stops_trip_id_city_id FOREIGN KEY (trip_id, city_id)
        REFERENCES trips (id, city_id) ON DELETE CASCADE,
    CONSTRAINT fk_trip_stops_place_id_city_id FOREIGN KEY (place_id, city_id)
        REFERENCES places (id, city_id) ON DELETE RESTRICT,
    CONSTRAINT fk_trip_stops_catalog_publication_id_place_id FOREIGN KEY (catalog_publication_id, place_id)
        REFERENCES catalog_publications (id, place_id) ON DELETE RESTRICT,
    CONSTRAINT uq_trip_stops_trip_day_id_ordinal UNIQUE (trip_day_id, ordinal) DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT uq_trip_stops_trip_id_place_id UNIQUE (trip_id, place_id),
    CONSTRAINT uq_trip_stops_id_trip_day_id UNIQUE (id, trip_day_id),
    CONSTRAINT ck_trip_stops_ordinal CHECK (ordinal > 0),
    CONSTRAINT ck_trip_stops_times CHECK (planned_arrival < planned_departure),
    CONSTRAINT ck_trip_stops_visit_minutes CHECK (visit_minutes BETWEEN 1 AND 600)
);
CREATE INDEX ix_trip_stops_place_id_city_id ON trip_stops (place_id, city_id);
CREATE INDEX ix_trip_stops_catalog_publication_id ON trip_stops (catalog_publication_id);
COMMENT ON TABLE trip_stops IS 'Saved stops with stable IDs from the preview; composite FKs enforce same-city membership (BR-006) and the catalog revision used.';

CREATE TABLE route_legs (
    id                uuid        NOT NULL DEFAULT gen_random_uuid(),
    trip_day_id       uuid        NOT NULL,
    from_stop_id      uuid        NOT NULL,
    to_stop_id        uuid        NOT NULL,
    travel_mode       text        NOT NULL,
    availability      text        NOT NULL,
    distance_m        integer,
    duration_s        integer,
    data_provider_id  uuid,
    measured_at       timestamptz,
    expires_at        timestamptz,
    CONSTRAINT pk_route_legs PRIMARY KEY (id),
    CONSTRAINT fk_route_legs_trip_day_id FOREIGN KEY (trip_day_id) REFERENCES trip_days (id) ON DELETE CASCADE,
    CONSTRAINT fk_route_legs_from_stop_id_trip_day_id FOREIGN KEY (from_stop_id, trip_day_id)
        REFERENCES trip_stops (id, trip_day_id) ON DELETE CASCADE,
    CONSTRAINT fk_route_legs_to_stop_id_trip_day_id FOREIGN KEY (to_stop_id, trip_day_id)
        REFERENCES trip_stops (id, trip_day_id) ON DELETE CASCADE,
    CONSTRAINT fk_route_legs_data_provider_id FOREIGN KEY (data_provider_id) REFERENCES data_providers (id) ON DELETE RESTRICT,
    CONSTRAINT uq_route_legs_from_stop_id UNIQUE (from_stop_id),
    CONSTRAINT uq_route_legs_to_stop_id UNIQUE (to_stop_id),
    CONSTRAINT ck_route_legs_distinct_stops CHECK (from_stop_id <> to_stop_id),
    CONSTRAINT ck_route_legs_travel_mode CHECK (travel_mode IN ('WALK', 'DRIVE')),
    CONSTRAINT ck_route_legs_availability CHECK (availability IN ('AVAILABLE', 'UNAVAILABLE', 'EXPIRED')),
    CONSTRAINT ck_route_legs_measurement CHECK (
        (availability = 'AVAILABLE') = (distance_m IS NOT NULL AND duration_s IS NOT NULL
                                        AND data_provider_id IS NOT NULL AND measured_at IS NOT NULL)),
    CONSTRAINT ck_route_legs_measurement_values CHECK (
        (distance_m IS NULL OR distance_m >= 0) AND (duration_s IS NULL OR duration_s >= 0)),
    CONSTRAINT ck_route_legs_expiry CHECK (expires_at IS NULL OR measured_at IS NULL OR expires_at > measured_at)
);
CREATE INDEX ix_route_legs_trip_day_id ON route_legs (trip_day_id);
CREATE INDEX ix_route_legs_data_provider_id ON route_legs (data_provider_id);
-- Q-R1: expiry sweep of retained route measurements (provider policy, OQ-016).
CREATE INDEX ix_route_legs_expires_at_available ON route_legs (expires_at) WHERE availability = 'AVAILABLE';
COMMENT ON TABLE route_legs IS 'Directed leg between consecutive saved stops. Distance/duration only from the routing provider (BRU-006); NULL when unavailable or expired.';

CREATE TABLE plan_previews (
    id                  uuid        NOT NULL DEFAULT gen_random_uuid(),
    account_id          uuid        NOT NULL,
    trip_id             uuid        NOT NULL,
    base_trip_revision  integer     NOT NULL,
    head_revision       integer     NOT NULL DEFAULT 0,
    status              text        NOT NULL DEFAULT 'ACTIVE',
    expires_at          timestamptz NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_plan_previews PRIMARY KEY (id),
    CONSTRAINT fk_plan_previews_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    CONSTRAINT fk_plan_previews_trip_id_account_id FOREIGN KEY (trip_id, account_id)
        REFERENCES trips (id, account_id) ON DELETE CASCADE,
    CONSTRAINT ck_plan_previews_base_trip_revision CHECK (base_trip_revision >= 0),
    CONSTRAINT ck_plan_previews_head_revision CHECK (head_revision >= 0),
    CONSTRAINT ck_plan_previews_status CHECK (status IN ('ACTIVE', 'SAVED', 'DISCARDED', 'EXPIRED'))
);
-- Q-V1: the one active (unsaved) proposal of a trip (FR-040, FR-044).
CREATE UNIQUE INDEX uq_plan_previews_trip_id_active ON plan_previews (trip_id) WHERE status = 'ACTIVE';
CREATE INDEX ix_plan_previews_trip_id_account_id ON plan_previews (trip_id, account_id);
CREATE INDEX ix_plan_previews_account_id ON plan_previews (account_id);
-- Q-V3: expiry sweep.
CREATE INDEX ix_plan_previews_expires_at_active ON plan_previews (expires_at) WHERE status = 'ACTIVE';
COMMENT ON TABLE plan_previews IS 'Unsaved proposal identity bound to owner, trip and base revision; survives provider failures (BR-033).';

CREATE TABLE preview_revisions (
    plan_preview_id   uuid        NOT NULL,
    preview_revision  integer     NOT NULL,
    parent_revision   integer,
    origin            text        NOT NULL,
    plan_health       text        NOT NULL,
    snapshot          jsonb       NOT NULL,
    model_version     text,
    prompt_version    text,
    corpus_revision   integer,
    created_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_preview_revisions PRIMARY KEY (plan_preview_id, preview_revision),
    CONSTRAINT fk_preview_revisions_plan_preview_id FOREIGN KEY (plan_preview_id) REFERENCES plan_previews (id) ON DELETE CASCADE,
    CONSTRAINT ck_preview_revisions_preview_revision CHECK (preview_revision > 0),
    CONSTRAINT ck_preview_revisions_parent CHECK (parent_revision IS NULL OR (parent_revision > 0 AND parent_revision < preview_revision)),
    CONSTRAINT ck_preview_revisions_origin CHECK (origin IN ('GENERATED', 'MANUAL_EDIT', 'DAY_REGENERATED', 'REPAIRED')),
    CONSTRAINT ck_preview_revisions_plan_health CHECK (plan_health IN ('GOOD', 'WARNING', 'BLOCKED')),
    CONSTRAINT ck_preview_revisions_snapshot_object CHECK (jsonb_typeof(snapshot) = 'object' AND snapshot ? 'days'),
    CONSTRAINT ck_preview_revisions_model_recorded CHECK (origin = 'MANUAL_EDIT' OR model_version IS NOT NULL)
);
CREATE TRIGGER trg_preview_revisions_reject_update_before
    BEFORE UPDATE ON preview_revisions FOR EACH ROW EXECUTE FUNCTION fn_reject_update();
COMMENT ON TABLE preview_revisions IS 'Immutable proposal snapshots (days, stops, legs, health, warnings). Intentional JSONB document; see model.md §2.4.';

CREATE TABLE guide_sessions (
    id          uuid        NOT NULL DEFAULT gen_random_uuid(),
    account_id  uuid        NOT NULL,
    trip_id     uuid,
    place_id    uuid,
    locale      text        NOT NULL,
    expires_at  timestamptz NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_guide_sessions PRIMARY KEY (id),
    CONSTRAINT fk_guide_sessions_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    CONSTRAINT fk_guide_sessions_trip_id_account_id FOREIGN KEY (trip_id, account_id)
        REFERENCES trips (id, account_id) ON DELETE CASCADE,
    CONSTRAINT fk_guide_sessions_place_id FOREIGN KEY (place_id) REFERENCES places (id) ON DELETE RESTRICT,
    CONSTRAINT ck_guide_sessions_locale CHECK (locale IN ('vi', 'en'))
    -- Migration 0008: no context CHECK; place_id NULL = city-level session (DEC-017, API-024).
);
-- Q-Q1: my recent Guide sessions.
CREATE INDEX ix_guide_sessions_account_id_created_at ON guide_sessions (account_id, created_at DESC);
CREATE INDEX ix_guide_sessions_trip_id_account_id ON guide_sessions (trip_id, account_id);
CREATE INDEX ix_guide_sessions_place_id ON guide_sessions (place_id);
CREATE INDEX ix_guide_sessions_expires_at ON guide_sessions (expires_at);                -- Q-Q3 retention sweep
COMMENT ON TABLE guide_sessions IS 'Private Guide conversation: city-level (place_id NULL), or one published place; optionally linked to an owned trip (FR-056, FR-069, DEC-017).';

CREATE TABLE guide_messages (
    id                uuid        NOT NULL DEFAULT gen_random_uuid(),
    guide_session_id  uuid        NOT NULL,
    seq               integer     NOT NULL,
    role              text        NOT NULL,
    input_mode        text,
    content           text        NOT NULL,
    answer_status     text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_guide_messages PRIMARY KEY (id),
    CONSTRAINT fk_guide_messages_guide_session_id FOREIGN KEY (guide_session_id) REFERENCES guide_sessions (id) ON DELETE CASCADE,
    CONSTRAINT uq_guide_messages_guide_session_id_seq UNIQUE (guide_session_id, seq),
    CONSTRAINT ck_guide_messages_seq CHECK (seq > 0),
    CONSTRAINT ck_guide_messages_role CHECK (role IN ('TRAVELER', 'ASSISTANT')),
    CONSTRAINT ck_guide_messages_input_mode CHECK (
        (role = 'TRAVELER' AND input_mode IN ('TEXT', 'VOICE_TRANSCRIPT', 'PHOTO'))
        OR (role = 'ASSISTANT' AND input_mode IS NULL)),
    CONSTRAINT ck_guide_messages_answer_status CHECK (
        (role = 'ASSISTANT' AND answer_status IN ('ANSWERED', 'ANSWERED_WEB_UNVERIFIED', 'INSUFFICIENT_EVIDENCE', 'NOT_RECOGNISED'))
        OR (role = 'TRAVELER' AND answer_status IS NULL)),
    CONSTRAINT ck_guide_messages_content_length CHECK (length(content) BETWEEN 1 AND 4000)
);
COMMENT ON TABLE guide_messages IS 'Question/answer text only. Photos, audio and traveler coordinates are never stored.';

CREATE TABLE guide_message_citations (
    guide_message_id    uuid NOT NULL,
    source_revision_id  uuid NOT NULL,
    knowledge_chunk_id  uuid,
    place_fact_id       uuid,
    CONSTRAINT pk_guide_message_citations PRIMARY KEY (guide_message_id, source_revision_id),
    CONSTRAINT fk_guide_message_citations_guide_message_id FOREIGN KEY (guide_message_id) REFERENCES guide_messages (id) ON DELETE CASCADE,
    CONSTRAINT fk_guide_message_citations_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES source_revisions (id) ON DELETE RESTRICT,
    CONSTRAINT fk_guide_message_citations_knowledge_chunk_id FOREIGN KEY (knowledge_chunk_id) REFERENCES knowledge_chunks (id) ON DELETE SET NULL,
    CONSTRAINT fk_guide_message_citations_place_fact_id FOREIGN KEY (place_fact_id) REFERENCES place_facts (id) ON DELETE SET NULL
);
CREATE INDEX ix_guide_message_citations_source_revision_id ON guide_message_citations (source_revision_id);
CREATE INDEX ix_guide_message_citations_knowledge_chunk_id ON guide_message_citations (knowledge_chunk_id);
CREATE INDEX ix_guide_message_citations_place_fact_id ON guide_message_citations (place_fact_id);

CREATE TABLE ai_invocations (
    id                uuid        NOT NULL DEFAULT gen_random_uuid(),
    account_id        uuid,
    purpose           text        NOT NULL,
    provider_model    text        NOT NULL,
    prompt_version    text,
    corpus_revision   integer,
    outcome           text        NOT NULL,
    latency_ms        integer     NOT NULL,
    input_tokens      integer,
    output_tokens     integer,
    created_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_ai_invocations PRIMARY KEY (id),
    CONSTRAINT fk_ai_invocations_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    CONSTRAINT ck_ai_invocations_purpose CHECK (purpose IN
        ('PLAN_GENERATE', 'PLAN_REPAIR', 'DAY_REGENERATE', 'RESEARCH', 'GUIDE_ANSWER', 'PHOTO_IDENTIFY', 'CORPUS_EMBED', 'QUERY_EMBED', 'TRANSLATION_DRAFT', 'CONTENT_SUMMARY')),
    CONSTRAINT ck_ai_invocations_outcome CHECK (outcome IN
        ('OK', 'VALIDATION_FAILED', 'PROVIDER_ERROR', 'TIMEOUT', 'QUOTA_EXCEEDED', 'REFUSED_BY_CAP')),
    CONSTRAINT ck_ai_invocations_traveler_purpose CHECK (
        account_id IS NOT NULL OR purpose IN ('CORPUS_EMBED', 'TRANSLATION_DRAFT', 'CONTENT_SUMMARY')),
    CONSTRAINT ck_ai_invocations_numbers CHECK (
        latency_ms >= 0 AND (input_tokens IS NULL OR input_tokens >= 0) AND (output_tokens IS NULL OR output_tokens >= 0))
);
-- Q-U1: per-traveler daily cap (NFR-036): count today's traveler invocations.
CREATE INDEX ix_ai_invocations_account_id_created_at ON ai_invocations (account_id, created_at);
-- Q-U2: retention sweep.
CREATE INDEX ix_ai_invocations_created_at ON ai_invocations (created_at);
COMMENT ON TABLE ai_invocations IS 'Safe AI usage metadata (plan.md §8): model, prompt, corpus, outcome, latency, tokens. Never prompt or answer text.';

CREATE TABLE idempotency_records (
    account_id       uuid        NOT NULL,
    operation        text        NOT NULL,
    idempotency_key  text        NOT NULL,
    request_sha256   char(64)    NOT NULL,
    state            text        NOT NULL DEFAULT 'IN_PROGRESS',
    response_status  smallint,
    response_body    jsonb,
    resource_id      uuid,
    created_at       timestamptz NOT NULL DEFAULT now(),
    expires_at       timestamptz NOT NULL,
    CONSTRAINT pk_idempotency_records PRIMARY KEY (account_id, operation, idempotency_key),
    CONSTRAINT fk_idempotency_records_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    CONSTRAINT ck_idempotency_records_operation CHECK (operation IN
        ('TRIP_SAVE', 'PREVIEW_CREATE', 'DAY_REGENERATE', 'ACCOUNT_DELETE', 'TRIP_CREATE', 'PREVIEW_EDIT', 'PUBLISH',
         'GUIDE_ASK')),
    CONSTRAINT ck_idempotency_records_key_length CHECK (length(idempotency_key) BETWEEN 8 AND 128),
    CONSTRAINT ck_idempotency_records_request_sha256_format CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_idempotency_records_state CHECK (state IN ('IN_PROGRESS', 'COMPLETED')),
    CONSTRAINT ck_idempotency_records_completed CHECK ((state = 'COMPLETED') = (response_status IS NOT NULL)),
    CONSTRAINT ck_idempotency_records_expiry CHECK (expires_at > created_at)
);
CREATE INDEX ix_idempotency_records_expires_at ON idempotency_records (expires_at);   -- Q-K2 sweep
COMMENT ON TABLE idempotency_records IS 'Replay protection for Save and other replayable writes (FR-041). Same key + different request hash = rejected.';

CREATE TABLE account_deletion_jobs (
    id              uuid        NOT NULL DEFAULT gen_random_uuid(),
    account_id      uuid,
    status          text        NOT NULL DEFAULT 'REQUESTED',
    attempt_count   smallint    NOT NULL DEFAULT 0,
    failure_reason  text,
    requested_at    timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    completed_at    timestamptz,
    CONSTRAINT pk_account_deletion_jobs PRIMARY KEY (id),
    CONSTRAINT fk_account_deletion_jobs_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE SET NULL,
    CONSTRAINT ck_account_deletion_jobs_status CHECK (status IN ('REQUESTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED')),
    CONSTRAINT ck_account_deletion_jobs_completed CHECK ((status = 'COMPLETED') = (completed_at IS NOT NULL)),
    CONSTRAINT ck_account_deletion_jobs_completed_unlinked CHECK (status <> 'COMPLETED' OR account_id IS NULL),
    CONSTRAINT ck_account_deletion_jobs_failure_reason CHECK (status <> 'FAILED' OR failure_reason IS NOT NULL),
    CONSTRAINT ck_account_deletion_jobs_attempt_count CHECK (attempt_count >= 0)
);
-- Q-D1: one open deletion job per account; also serves FK lookups on account delete.
CREATE UNIQUE INDEX uq_account_deletion_jobs_account_id_open
    ON account_deletion_jobs (account_id) WHERE status IN ('REQUESTED', 'IN_PROGRESS', 'FAILED');
CREATE INDEX ix_account_deletion_jobs_account_id ON account_deletion_jobs (account_id);
-- Q-D2: worker picks due jobs; 24 h deadline monitor (BR-021).
CREATE INDEX ix_account_deletion_jobs_status_requested_at ON account_deletion_jobs (status, requested_at);
COMMENT ON TABLE account_deletion_jobs IS 'Retryable deletion workflow and visible status (BR-021, BR-044, FR-071, FR-072). Keeps no personal data after completion.';

-- -----------------------------------------------------------------------------
-- Section 8 — NEW (migration 0004): user-study records (FR-077; retention ASM-010, NFR-018)
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

-- -----------------------------------------------------------------------------
-- Section 9 — NEW: updated_at triggers, views, reference seed
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_cities_set_updated_at_before BEFORE UPDATE ON cities FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_categories_set_updated_at_before BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_data_providers_set_updated_at_before BEFORE UPDATE ON data_providers FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_places_set_updated_at_before BEFORE UPDATE ON places FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_external_place_identities_set_updated_at_before BEFORE UPDATE ON external_place_identities FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_place_aliases_set_updated_at_before BEFORE UPDATE ON place_aliases FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_sources_set_updated_at_before BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_media_assets_set_updated_at_before BEFORE UPDATE ON media_assets FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_account_preferences_set_updated_at_before BEFORE UPDATE ON account_preferences FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_trips_set_updated_at_before BEFORE UPDATE ON trips FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_plan_previews_set_updated_at_before BEFORE UPDATE ON plan_previews FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_account_deletion_jobs_set_updated_at_before BEFORE UPDATE ON account_deletion_jobs FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

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

-- Reference seed. Gonarra covers Đà Nẵng only (owner 2026-11-08); Hội An is an area of Đà Nẵng
-- (2025 merger), not a city. Other cities were removed (`app.cli seed` deletes unreferenced rows).
INSERT INTO cities (code, name_vi, name_en) VALUES
    ('da-nang',           'Đà Nẵng',              'Da Nang');

-- Operational fact vocabulary; 180-day staleness from ASM-008.
INSERT INTO fact_fields (code, is_operational, required_for_publication, value_kind, stale_after_days) VALUES
    ('OPENING_HOURS',     true, true,  'HOURS',    180),
    ('ADMISSION_PRICE',   true, true,  'MONEY',    180),
    ('ADDRESS_VI',        true, true,  'TEXT',     180),
    ('ENTRANCE_LOCATION', true, true,  'LOCATION', 180),
    ('PAYMENT_METHODS',   true, false, 'TEXT',     180),
    ('DRESS_CODE',        true, false, 'TEXT',     180),
    ('ACCESS_RULES',      true, false, 'TEXT',     180);

-- Providers named in SRC-104 / DEC-007. Policies are NOT seeded: terms versions must be recorded by the owner (OQ-016).
INSERT INTO data_providers (provider_key, display_name, provider_kind) VALUES
    ('overture_places',      'Overture Maps Places',          'OPEN_DATASET'),
    ('foursquare_os_places', 'Foursquare Open Source Places', 'OPEN_DATASET'),
    ('wikidata',             'Wikidata',                      'OPEN_DATASET'),
    ('wikimedia_commons',    'Wikimedia Commons',             'MEDIA_LIBRARY'),
    ('google_places',        'Google Places API',             'RUNTIME_API'),
    ('google_routes',        'Google Routes API',             'RUNTIME_API'),
    ('liteapi',              'LiteAPI',                       'RUNTIME_API'),
    ('gemini',               'Google Gemini API',             'AI_SERVICE');
