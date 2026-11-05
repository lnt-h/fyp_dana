-- -----------------------------------------------------------------------------
-- Section 8A — NEW (migration 0004): free-tier quota ledger and provider caches (DEC-018, ADR-006)
-- Implemented by apps/api/migrations/versions/20261106_0004_caches.py. Paste into docs/data/schema.sql
-- after Section 7 (the 1.0 contract lacks this section). Depends on Sections 0-7.
-- Every cache row names the provider policy it is stored under (ADR-006 "every cache row has a policy");
-- expires_at is bounded by the policy retention in a CHECK so an over-long TTL cannot be written.
-- Cache keys never contain traveler GPS, account IDs or question text (BR-046): routes keys are
-- catalog/candidate/anchor IDs, research and embedding keys are SHA-256 hashes of redacted text.
-- -----------------------------------------------------------------------------
CREATE TABLE ai_quota_ledger (
    id            uuid        NOT NULL DEFAULT gen_random_uuid(),
    scope         text        NOT NULL,
    account_id    uuid,
    bucket        text        NOT NULL,
    period_start  date        NOT NULL,
    cap           integer     NOT NULL,
    used          integer     NOT NULL DEFAULT 0,
    reserved      integer     NOT NULL DEFAULT 0,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_ai_quota_ledger PRIMARY KEY (id),
    CONSTRAINT fk_ai_quota_ledger_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    -- NULLS NOT DISTINCT: GLOBAL rows (account_id NULL) are unique per bucket and period too.
    CONSTRAINT uq_ai_quota_ledger_scope_account_id_bucket_period_start
        UNIQUE NULLS NOT DISTINCT (scope, account_id, bucket, period_start),
    CONSTRAINT ck_ai_quota_ledger_scope CHECK (scope IN ('GLOBAL', 'ACCOUNT')),
    CONSTRAINT ck_ai_quota_ledger_scope_account CHECK ((scope = 'ACCOUNT') = (account_id IS NOT NULL)),
    CONSTRAINT ck_ai_quota_ledger_bucket CHECK (bucket IN
        ('GEMINI_FLASH', 'GEMINI_FLASH_LITE', 'GEMINI_EMBED', 'GROQ', 'TAVILY_DAY', 'TAVILY_MONTH',
         'PLACES', 'ROUTES_ELEMENTS', 'ACCOUNT_PROPOSALS', 'ACCOUNT_QUESTIONS')),
    CONSTRAINT ck_ai_quota_ledger_bucket_scope CHECK (
        (scope = 'ACCOUNT') = (bucket IN ('ACCOUNT_PROPOSALS', 'ACCOUNT_QUESTIONS'))),
    CONSTRAINT ck_ai_quota_ledger_month_start CHECK (
        bucket <> 'TAVILY_MONTH' OR extract(day FROM period_start) = 1),
    CONSTRAINT ck_ai_quota_ledger_counters CHECK (cap >= 0 AND used >= 0 AND reserved >= 0)
);
CREATE INDEX ix_ai_quota_ledger_account_id ON ai_quota_ledger (account_id);
-- Q-L2: retention sweep of old periods.
CREATE INDEX ix_ai_quota_ledger_period_start ON ai_quota_ledger (period_start);
COMMENT ON TABLE ai_quota_ledger IS 'Free-tier budget per bucket and period (DEC-018, architecture §3.3). period_start is the local date in Asia/Ho_Chi_Minh (first day of the month for TAVILY_MONTH). Reserve: INSERT ... ON CONFLICT DO NOTHING to open the row with cap from settings, then UPDATE ... SET reserved = reserved + :n, cap = :cap WHERE <key, account_id IS NOT DISTINCT FROM :aid> AND used + reserved + :n <= :cap RETURNING; zero rows = exhausted, the caller degrades. Commit moves the actual units from reserved to used (used may exceed cap when the actual count is larger; no CHECK blocks the record); release returns reserved units. GLOBAL buckets have account_id NULL.';
COMMENT ON COLUMN ai_quota_ledger.cap IS 'Copied from settings GONARRA_QUOTA_* when the row is opened; may be raised later, never used to reject a commit.';

CREATE TABLE routes_matrix_cache (
    origin_key          text        NOT NULL,
    destination_key     text        NOT NULL,
    travel_mode         text        NOT NULL,
    availability        text        NOT NULL,
    distance_m          integer,
    duration_s          integer,
    provider_policy_id  uuid        NOT NULL,
    fetched_at          timestamptz NOT NULL DEFAULT now(),
    expires_at          timestamptz NOT NULL,
    CONSTRAINT pk_routes_matrix_cache PRIMARY KEY (origin_key, destination_key, travel_mode),
    CONSTRAINT fk_routes_matrix_cache_provider_policy_id FOREIGN KEY (provider_policy_id)
        REFERENCES provider_policies (id) ON DELETE RESTRICT,
    CONSTRAINT ck_routes_matrix_cache_origin_key_format CHECK (origin_key ~ '^(place|web|anchor):[a-z0-9-]{1,64}$'),
    CONSTRAINT ck_routes_matrix_cache_destination_key_format CHECK (destination_key ~ '^(place|web|anchor):[a-z0-9-]{1,64}$'),
    CONSTRAINT ck_routes_matrix_cache_distinct_keys CHECK (origin_key <> destination_key),
    CONSTRAINT ck_routes_matrix_cache_travel_mode CHECK (travel_mode IN ('WALK', 'DRIVE')),
    CONSTRAINT ck_routes_matrix_cache_availability CHECK (availability IN ('AVAILABLE', 'UNAVAILABLE')),
    CONSTRAINT ck_routes_matrix_cache_measurement CHECK (
        (availability = 'AVAILABLE') = (distance_m IS NOT NULL AND duration_s IS NOT NULL)),
    CONSTRAINT ck_routes_matrix_cache_measurement_values CHECK (
        (distance_m IS NULL OR distance_m >= 0) AND (duration_s IS NULL OR duration_s >= 0)),
    CONSTRAINT ck_routes_matrix_cache_expiry CHECK (
        expires_at > fetched_at AND expires_at <= fetched_at + interval '30 days')
);
CREATE INDEX ix_routes_matrix_cache_provider_policy_id ON routes_matrix_cache (provider_policy_id);
CREATE INDEX ix_routes_matrix_cache_expires_at ON routes_matrix_cache (expires_at);              -- Q-X1 sweep
COMMENT ON TABLE routes_matrix_cache IS 'Pairwise Google Routes measurements (ADR-011, ADR-006 google_routes EPHEMERAL <= 30 d). Keys: place:<places.id>, web:<web_place_candidates.id>, anchor:<fixed day-start anchor code>; never traveler GPS. WALK is requested only for pairs <= 2.5 km. UNAVAILABLE pairs are cached as unavailable, never estimated (BRU-006).';

CREATE TABLE research_cache (
    provider            text        NOT NULL,
    key_sha256          char(64)    NOT NULL,
    payload             jsonb       NOT NULL,
    source_revision_id  uuid,
    provider_policy_id  uuid        NOT NULL,
    fetched_at          timestamptz NOT NULL DEFAULT now(),
    expires_at          timestamptz NOT NULL,
    CONSTRAINT pk_research_cache PRIMARY KEY (provider, key_sha256),
    CONSTRAINT fk_research_cache_source_revision_id FOREIGN KEY (source_revision_id)
        REFERENCES source_revisions (id) ON DELETE SET NULL,
    CONSTRAINT fk_research_cache_provider_policy_id FOREIGN KEY (provider_policy_id)
        REFERENCES provider_policies (id) ON DELETE RESTRICT,
    CONSTRAINT ck_research_cache_provider CHECK (provider IN ('TAVILY', 'WEB_PAGE')),
    CONSTRAINT ck_research_cache_key_sha256_format CHECK (key_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_research_cache_payload_object CHECK (jsonb_typeof(payload) = 'object'),
    CONSTRAINT ck_research_cache_payload_size CHECK (octet_length(payload::text) <= 262144),
    CONSTRAINT ck_research_cache_source_revision CHECK (provider = 'WEB_PAGE' OR source_revision_id IS NULL),
    CONSTRAINT ck_research_cache_expiry CHECK (
        expires_at > fetched_at AND expires_at <= fetched_at + interval '7 days')
);
CREATE INDEX ix_research_cache_source_revision_id ON research_cache (source_revision_id);
CREATE INDEX ix_research_cache_provider_policy_id ON research_cache (provider_policy_id);
CREATE INDEX ix_research_cache_expires_at ON research_cache (expires_at);                        -- Q-X1 sweep
COMMENT ON TABLE research_cache IS 'Ephemeral research inputs (ADR-006 tavily / web_page EPHEMERAL 7 d, OQ-122). TAVILY: key = SHA-256 of the redacted, normalised query; payload = results (url, title, snippet). WEB_PAGE: key = SHA-256 of the normalised URL; payload = extracted text; the canonical provenance is the linked source_revisions row. Never shown as a fact and never copied into catalog tables.';

CREATE TABLE places_lookup_cache (
    id                   uuid        NOT NULL DEFAULT gen_random_uuid(),
    query_sha256         char(64),
    google_place_id      text,
    outcome              text        NOT NULL,
    location             geography(Point, 4326),
    location_expires_at  timestamptz,
    provider_policy_id   uuid        NOT NULL,
    fetched_at           timestamptz NOT NULL DEFAULT now(),
    outcome_expires_at   timestamptz NOT NULL,
    CONSTRAINT pk_places_lookup_cache PRIMARY KEY (id),
    CONSTRAINT fk_places_lookup_cache_provider_policy_id FOREIGN KEY (provider_policy_id)
        REFERENCES provider_policies (id) ON DELETE RESTRICT,
    CONSTRAINT uq_places_lookup_cache_query_sha256 UNIQUE (query_sha256),
    CONSTRAINT uq_places_lookup_cache_google_place_id UNIQUE (google_place_id),
    CONSTRAINT ck_places_lookup_cache_key CHECK (query_sha256 IS NOT NULL OR google_place_id IS NOT NULL),
    CONSTRAINT ck_places_lookup_cache_query_sha256_format CHECK (query_sha256 IS NULL OR query_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_places_lookup_cache_outcome CHECK (outcome IN
        ('EXISTS_OPERATIONAL', 'EXISTS_CLOSED', 'NOT_FOUND', 'OUTSIDE_CITY')),
    CONSTRAINT ck_places_lookup_cache_outcome_identity CHECK ((outcome = 'NOT_FOUND') = (google_place_id IS NULL)),
    CONSTRAINT ck_places_lookup_cache_location_expiry CHECK (
        (location IS NULL) = (location_expires_at IS NULL)
        AND (location_expires_at IS NULL OR location_expires_at <= fetched_at + interval '30 days')),
    CONSTRAINT ck_places_lookup_cache_outcome_expiry CHECK (
        outcome_expires_at > fetched_at AND outcome_expires_at <= fetched_at + interval '24 hours')
);
CREATE INDEX ix_places_lookup_cache_provider_policy_id ON places_lookup_cache (provider_policy_id);
CREATE INDEX ix_places_lookup_cache_outcome_expires_at ON places_lookup_cache (outcome_expires_at);   -- Q-X1 sweep
CREATE INDEX ix_places_lookup_cache_location_expires_at ON places_lookup_cache (location_expires_at)
    WHERE location_expires_at IS NOT NULL;                                                          -- Q-X1 sweep
COMMENT ON TABLE places_lookup_cache IS 'Google Places existence/status check results (ADR-006, ADR-014). Stores the place_id (IDENTIFIER_ONLY), Gonarra''s own verdict outcome (24 h) and an ephemeral lat/lng copy (<= 30 d, OQ-124; never copied into places or web_place_candidates). Google business_status and opening hours are DENY (runtime only) and have no column. query_sha256 = SHA-256 of the redacted text-search query (name + city), so repeated lookups of the same candidate hit the cache. The sweep nulls location after location_expires_at and deletes the row after outcome_expires_at.';

CREATE TABLE query_embedding_cache (
    text_sha256         char(64)    NOT NULL,
    locale              text        NOT NULL,
    embedding_model     text        NOT NULL,
    embedding           vector(768) NOT NULL,
    provider_policy_id  uuid        NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    expires_at          timestamptz NOT NULL,
    CONSTRAINT pk_query_embedding_cache PRIMARY KEY (text_sha256, locale, embedding_model),
    CONSTRAINT fk_query_embedding_cache_provider_policy_id FOREIGN KEY (provider_policy_id)
        REFERENCES provider_policies (id) ON DELETE RESTRICT,
    CONSTRAINT ck_query_embedding_cache_text_sha256_format CHECK (text_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_query_embedding_cache_locale CHECK (locale IN ('vi', 'en')),
    CONSTRAINT ck_query_embedding_cache_expiry CHECK (
        expires_at > created_at AND expires_at <= created_at + interval '90 days')
);
CREATE INDEX ix_query_embedding_cache_provider_policy_id ON query_embedding_cache (provider_policy_id);
CREATE INDEX ix_query_embedding_cache_expires_at ON query_embedding_cache (expires_at);          -- Q-X1 sweep
COMMENT ON TABLE query_embedding_cache IS 'Guide question embeddings (ADR-010 1.0, 90 d). Key = SHA-256 of the normalised, redacted question; the question text is never stored. embedding_model must equal the chunks'' embedding_model (vector(768), OQ-126).';

CREATE TRIGGER trg_ai_quota_ledger_set_updated_at_before
    BEFORE UPDATE ON ai_quota_ledger FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
