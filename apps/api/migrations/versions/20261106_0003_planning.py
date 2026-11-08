# ruff: noqa: E501
"""Planning schema: trips, previews, Guide sessions, AI usage (schema.sql 1.0 Section 7).

Preferences, trips, days, stops, legs, previews, Guide sessions, AI usage, idempotency and
account deletion jobs. Implements docs/04-design/data/schema.sql 1.0 Section 7 plus its Section 9 updated_at triggers.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0003"
down_revision: str | None = "20261106_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute_script(sql: str) -> None:
    # Colons are escaped so that JSON/time literals in comments are not read as bind parameters.
    op.execute(sa.text(sql.replace(":", "\\:")))


SECTION_7_SQL = """
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
COMMENT ON TABLE trips IS 'Trip header; revision = accepted (saved) version, advanced only by explicit Save (BR-011, FR-040..FR-042). One enabled city, 1-3 days (BRU-007 rev. 1).';

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
    id                       uuid     NOT NULL,
    trip_id                  uuid     NOT NULL,
    trip_day_id              uuid     NOT NULL,
    city_id                  uuid     NOT NULL,
    trust_level              text     NOT NULL DEFAULT 'VERIFIED',
    place_id                 uuid,
    catalog_publication_id   uuid,
    web_place_candidate_id   uuid,
    ordinal                  smallint NOT NULL,
    planned_arrival          time     NOT NULL,
    planned_departure        time     NOT NULL,
    visit_minutes            smallint NOT NULL,
    is_locked                boolean  NOT NULL DEFAULT false,
    CONSTRAINT pk_trip_stops PRIMARY KEY (id),
    CONSTRAINT fk_trip_stops_trip_day_id_trip_id FOREIGN KEY (trip_day_id, trip_id)
        REFERENCES trip_days (id, trip_id) ON DELETE CASCADE,
    CONSTRAINT fk_trip_stops_trip_id_city_id FOREIGN KEY (trip_id, city_id)
        REFERENCES trips (id, city_id) ON DELETE CASCADE,
    CONSTRAINT fk_trip_stops_place_id_city_id FOREIGN KEY (place_id, city_id)
        REFERENCES places (id, city_id) ON DELETE RESTRICT,
    CONSTRAINT fk_trip_stops_catalog_publication_id_place_id FOREIGN KEY (catalog_publication_id, place_id)
        REFERENCES catalog_publications (id, place_id) ON DELETE RESTRICT,
    CONSTRAINT fk_trip_stops_web_place_candidate_id_city_id FOREIGN KEY (web_place_candidate_id, city_id)
        REFERENCES web_place_candidates (id, city_id) ON DELETE RESTRICT,
    CONSTRAINT uq_trip_stops_trip_day_id_ordinal UNIQUE (trip_day_id, ordinal) DEFERRABLE INITIALLY IMMEDIATE,
    CONSTRAINT uq_trip_stops_trip_id_place_id UNIQUE (trip_id, place_id),
    CONSTRAINT uq_trip_stops_id_trip_day_id UNIQUE (id, trip_day_id),
    CONSTRAINT ck_trip_stops_trust_level CHECK (trust_level IN ('VERIFIED', 'WEB_UNVERIFIED')),
    -- Exactly one shape: a VERIFIED stop pins a published place; a WEB_UNVERIFIED stop references a candidate.
    CONSTRAINT ck_trip_stops_shape CHECK (
        (trust_level = 'VERIFIED' AND place_id IS NOT NULL AND catalog_publication_id IS NOT NULL
            AND web_place_candidate_id IS NULL)
        OR (trust_level = 'WEB_UNVERIFIED' AND web_place_candidate_id IS NOT NULL
            AND place_id IS NULL AND catalog_publication_id IS NULL)),
    CONSTRAINT ck_trip_stops_ordinal CHECK (ordinal > 0),
    CONSTRAINT ck_trip_stops_times CHECK (planned_arrival < planned_departure),
    CONSTRAINT ck_trip_stops_visit_minutes CHECK (visit_minutes BETWEEN 1 AND 600)
);
CREATE UNIQUE INDEX uq_trip_stops_trip_id_web_place_candidate_id
    ON trip_stops (trip_id, web_place_candidate_id) WHERE web_place_candidate_id IS NOT NULL;
CREATE INDEX ix_trip_stops_place_id_city_id ON trip_stops (place_id, city_id);
CREATE INDEX ix_trip_stops_catalog_publication_id ON trip_stops (catalog_publication_id);
CREATE INDEX ix_trip_stops_web_place_candidate_id ON trip_stops (web_place_candidate_id);
COMMENT ON TABLE trip_stops IS 'Saved stops with stable IDs from the preview; composite FKs enforce same-city membership (BR-006) and the catalog revision used. trust_level (DEC-015): VERIFIED pins a publication; WEB_UNVERIFIED references a web_place_candidates row and is shown with its source URL and fetched date. The stored level never changes; vw_trip_stop_trust derives the effective level.';
COMMENT ON COLUMN trip_stops.trust_level IS 'VERIFIED or WEB_UNVERIFIED (canonical TrustLevel values, shared with the API).';

-- Effective trust of a saved stop: a WEB_UNVERIFIED stop reads as VERIFIED once its candidate is promoted
-- and the promoted place has a current publication (DEC-015). Read path for API-014 / API-017 trust labels.
CREATE VIEW vw_trip_stop_trust AS
SELECT ts.id                                    AS trip_stop_id,
       ts.trip_id,
       ts.trip_day_id,
       ts.city_id,
       ts.trust_level                           AS stored_trust_level,
       CASE WHEN ts.trust_level = 'VERIFIED' THEN 'VERIFIED'
            WHEN wpc.review_state = 'PROMOTED' AND cp.id IS NOT NULL THEN 'VERIFIED'
            ELSE 'WEB_UNVERIFIED' END            AS effective_trust_level,
       coalesce(ts.place_id, CASE WHEN cp.id IS NOT NULL THEN wpc.promoted_place_id END)  AS effective_place_id,
       coalesce(ts.catalog_publication_id, cp.id)                                         AS effective_catalog_publication_id,
       ts.web_place_candidate_id,
       wpc.review_state                         AS candidate_review_state,
       wpc.places_check_outcome,
       sr.locator                               AS source_url,
       wpc.fetched_at
  FROM trip_stops ts
  LEFT JOIN web_place_candidates wpc ON wpc.id = ts.web_place_candidate_id
  LEFT JOIN catalog_publications cp ON cp.place_id = wpc.promoted_place_id AND cp.state = 'PUBLISHED'
  LEFT JOIN source_revisions sr ON sr.id = wpc.source_revision_id;
COMMENT ON VIEW vw_trip_stop_trust IS 'Per saved stop: stored and effective trust_level, resolved place/publication, candidate state, source URL and fetched_at (DEC-015, FR-098).';

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
    CONSTRAINT ck_guide_sessions_locale CHECK (locale IN ('vi', 'en')),
    CONSTRAINT ck_guide_sessions_context CHECK (trip_id IS NOT NULL OR place_id IS NOT NULL)
);
-- Q-Q1: my recent Guide sessions.
CREATE INDEX ix_guide_sessions_account_id_created_at ON guide_sessions (account_id, created_at DESC);
CREATE INDEX ix_guide_sessions_trip_id_account_id ON guide_sessions (trip_id, account_id);
CREATE INDEX ix_guide_sessions_place_id ON guide_sessions (place_id);
CREATE INDEX ix_guide_sessions_expires_at ON guide_sessions (expires_at);                -- Q-Q3 retention sweep
COMMENT ON TABLE guide_sessions IS 'Private Guide conversation scoped to a published place or an owned trip (FR-056, FR-069).';

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
        (role = 'ASSISTANT' AND answer_status IN ('ANSWERED', 'INSUFFICIENT_EVIDENCE', 'NOT_RECOGNISED'))
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
    agent_run_id      uuid,          -- T-02 addition (T-03): Agno run correlation, architecture §6
    error_code        text,          -- T-02 addition (T-03): machine-readable failure code, never provider text
    created_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_ai_invocations PRIMARY KEY (id),
    CONSTRAINT fk_ai_invocations_account_id FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
    CONSTRAINT ck_ai_invocations_purpose CHECK (purpose IN
        ('PLAN_GENERATE', 'PLAN_REPAIR', 'DAY_REGENERATE', 'RESEARCH', 'GUIDE_ANSWER', 'PHOTO_IDENTIFY', 'CORPUS_EMBED', 'QUERY_EMBED', 'TRANSLATION_DRAFT')),  -- RESEARCH: T-02 addition (T-03)
    CONSTRAINT ck_ai_invocations_outcome CHECK (outcome IN
        ('OK', 'VALIDATION_FAILED', 'PROVIDER_ERROR', 'TIMEOUT', 'QUOTA_EXCEEDED', 'REFUSED_BY_CAP')),
    CONSTRAINT ck_ai_invocations_traveler_purpose CHECK (
        account_id IS NOT NULL OR purpose IN ('CORPUS_EMBED', 'TRANSLATION_DRAFT')),
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
        ('TRIP_SAVE', 'PREVIEW_CREATE', 'DAY_REGENERATE', 'ACCOUNT_DELETE')),
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
"""

SECTION_9_SQL = """
CREATE TRIGGER trg_account_preferences_set_updated_at_before BEFORE UPDATE ON account_preferences FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_trips_set_updated_at_before BEFORE UPDATE ON trips FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_plan_previews_set_updated_at_before BEFORE UPDATE ON plan_previews FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_account_deletion_jobs_set_updated_at_before BEFORE UPDATE ON account_deletion_jobs FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
"""

DOWNGRADE_SQL = """
DROP VIEW IF EXISTS vw_trip_stop_trust;
DROP TABLE IF EXISTS
    account_deletion_jobs, idempotency_records, ai_invocations, guide_message_citations,
    guide_messages, guide_sessions, preview_revisions, plan_previews, route_legs,
    trip_stops, trip_days, trips, account_preferences;
DROP FUNCTION IF EXISTS fn_check_trip_day_index();
"""


def upgrade() -> None:
    _execute_script(SECTION_7_SQL)
    _execute_script(SECTION_9_SQL)


def downgrade() -> None:
    _execute_script(DOWNGRADE_SQL)
