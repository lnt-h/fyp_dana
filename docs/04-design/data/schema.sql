-- =============================================================================
-- Gonarra physical schema (PostgreSQL 16 + PostGIS + pgvector + pgcrypto + pg_trgm)
-- GENERATED from the Alembic migrations at head 20261108_0009 on 2026-11-09. Do not edit by hand:
-- the migrations in apps/api/migrations/versions/ are the source of truth (DEC-029).
-- Narrative and rationale: docs/04-design/data/data-model.md.
-- Regenerate after every migration (from the repository root, Compose DB running):
--   docker compose exec -T db psql -U gonarra -d postgres -c "CREATE DATABASE gonarra_schema"
--   (cd apps/api && GONARRA_DATABASE_URL=postgresql+psycopg://gonarra:gonarra@localhost:5432/gonarra_schema \
--      uv run alembic upgrade head)
--   docker compose exec -T db pg_dump -U gonarra -d gonarra_schema --schema-only --no-owner \
--      --no-privileges --exclude-table=alembic_version | sed '/^\\\(un\)\?restrict /d'   # body below
--   docker compose exec -T db psql -U gonarra -d postgres -c "DROP DATABASE gonarra_schema"
-- =============================================================================

--
-- PostgreSQL database dump
--

\restrict MCSzH36Do0ebXGp4YcFXLtnQuLSrUj0AHmKTQJqBkCHKCzjeWPW7UzDGQLichQI

-- Dumped from database version 16.15 (Debian 16.15-1.pgdg13+2)
-- Dumped by pg_dump version 16.15 (Debian 16.15-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: fn_check_trip_day_index(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_check_trip_day_index() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: fn_guard_catalog_publication_update(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_guard_catalog_publication_update() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: fn_guard_place_fact_update(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_guard_place_fact_update() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: fn_publication_gate_violations(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_publication_gate_violations(p_place_id uuid) RETURNS TABLE(violation_code text, detail text)
    LANGUAGE sql STABLE
    AS $$
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


--
-- Name: fn_publish_place(uuid, uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_publish_place(p_place_id uuid, p_actor_account_id uuid) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: fn_reject_update(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_reject_update() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'rows of % are immutable; append a new revision instead', TG_TABLE_NAME
        USING ERRCODE = 'integrity_constraint_violation';
END
$$;


--
-- Name: fn_set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END
$$;


--
-- Name: fn_withdraw_place(uuid, uuid, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_withdraw_place(p_place_id uuid, p_actor_account_id uuid, p_reason text) RETURNS void
    LANGUAGE plpgsql
    AS $$
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


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account_deletion_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.account_deletion_jobs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    account_id uuid,
    status text DEFAULT 'REQUESTED'::text NOT NULL,
    attempt_count smallint DEFAULT 0 NOT NULL,
    failure_reason text,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    clerk_subject_sha256 character(64),
    CONSTRAINT ck_account_deletion_jobs_attempt_count CHECK ((attempt_count >= 0)),
    CONSTRAINT ck_account_deletion_jobs_clerk_subject_sha256_format CHECK ((clerk_subject_sha256 ~ '^[0-9a-f]{64}$'::text)),
    CONSTRAINT ck_account_deletion_jobs_completed CHECK (((status = 'COMPLETED'::text) = (completed_at IS NOT NULL))),
    CONSTRAINT ck_account_deletion_jobs_completed_unlinked CHECK (((status <> 'COMPLETED'::text) OR (account_id IS NULL))),
    CONSTRAINT ck_account_deletion_jobs_failure_reason CHECK (((status <> 'FAILED'::text) OR (failure_reason IS NOT NULL))),
    CONSTRAINT ck_account_deletion_jobs_status CHECK ((status = ANY (ARRAY['REQUESTED'::text, 'IN_PROGRESS'::text, 'COMPLETED'::text, 'FAILED'::text])))
);


--
-- Name: TABLE account_deletion_jobs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.account_deletion_jobs IS 'Retryable deletion workflow and visible status (BR-021, BR-044, FR-071, FR-072). Keeps no personal data after completion.';


--
-- Name: COLUMN account_deletion_jobs.clerk_subject_sha256; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.account_deletion_jobs.clerk_subject_sha256 IS 'SHA-256 (hex) of the deleted Clerk subject; lets the API refuse a re-used token of a deleted account without storing the subject.';


--
-- Name: account_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.account_preferences (
    account_id uuid NOT NULL,
    locale text DEFAULT 'vi'::text NOT NULL,
    pace text,
    interest_category_codes text[] DEFAULT '{}'::text[] NOT NULL,
    allowed_modes text[] DEFAULT '{WALK,DRIVE}'::text[] NOT NULL,
    day_start_time time without time zone,
    day_end_time time without time zone,
    ai_notice_acknowledged_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_account_preferences_allowed_modes CHECK (((cardinality(allowed_modes) > 0) AND (allowed_modes <@ ARRAY['WALK'::text, 'DRIVE'::text]))),
    CONSTRAINT ck_account_preferences_day_window CHECK (((day_start_time IS NULL) OR (day_end_time IS NULL) OR (day_start_time < day_end_time))),
    CONSTRAINT ck_account_preferences_interest_count CHECK ((cardinality(interest_category_codes) <= 20)),
    CONSTRAINT ck_account_preferences_locale CHECK ((locale = ANY (ARRAY['vi'::text, 'en'::text]))),
    CONSTRAINT ck_account_preferences_pace CHECK (((pace IS NULL) OR (pace = ANY (ARRAY['RELAXED'::text, 'BALANCED'::text, 'PACKED'::text]))))
);


--
-- Name: TABLE account_preferences; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.account_preferences IS 'Explicitly saved language, preferences (FR-073, FR-075) and AI-notice acknowledgement (FR-074). No free-text memory.';


--
-- Name: accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accounts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    clerk_user_id character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: ai_invocations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_invocations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    account_id uuid,
    purpose text NOT NULL,
    provider_model text NOT NULL,
    prompt_version text,
    corpus_revision integer,
    outcome text NOT NULL,
    latency_ms integer NOT NULL,
    input_tokens integer,
    output_tokens integer,
    agent_run_id uuid,
    error_code text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_ai_invocations_numbers CHECK (((latency_ms >= 0) AND ((input_tokens IS NULL) OR (input_tokens >= 0)) AND ((output_tokens IS NULL) OR (output_tokens >= 0)))),
    CONSTRAINT ck_ai_invocations_outcome CHECK ((outcome = ANY (ARRAY['OK'::text, 'VALIDATION_FAILED'::text, 'PROVIDER_ERROR'::text, 'TIMEOUT'::text, 'QUOTA_EXCEEDED'::text, 'REFUSED_BY_CAP'::text]))),
    CONSTRAINT ck_ai_invocations_purpose CHECK ((purpose = ANY (ARRAY['PLAN_GENERATE'::text, 'PLAN_REPAIR'::text, 'DAY_REGENERATE'::text, 'RESEARCH'::text, 'GUIDE_ANSWER'::text, 'PHOTO_IDENTIFY'::text, 'CORPUS_EMBED'::text, 'QUERY_EMBED'::text, 'TRANSLATION_DRAFT'::text, 'CONTENT_SUMMARY'::text]))),
    CONSTRAINT ck_ai_invocations_traveler_purpose CHECK (((account_id IS NOT NULL) OR (purpose = ANY (ARRAY['CORPUS_EMBED'::text, 'TRANSLATION_DRAFT'::text, 'CONTENT_SUMMARY'::text]))))
);


--
-- Name: TABLE ai_invocations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.ai_invocations IS 'Safe AI usage metadata (plan.md §8): model, prompt, corpus, outcome, latency, tokens. Never prompt or answer text.';


--
-- Name: ai_quota_ledger; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_quota_ledger (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    scope text NOT NULL,
    account_id uuid,
    bucket text NOT NULL,
    period_start date NOT NULL,
    cap integer NOT NULL,
    used integer DEFAULT 0 NOT NULL,
    reserved integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_ai_quota_ledger_bucket CHECK ((bucket = ANY (ARRAY['GEMINI_FLASH'::text, 'GEMINI_FLASH_LITE'::text, 'GEMINI_EMBED'::text, 'GROQ'::text, 'TAVILY_DAY'::text, 'TAVILY_MONTH'::text, 'PLACES'::text, 'ROUTES_ELEMENTS'::text, 'ACCOUNT_PROPOSALS'::text, 'ACCOUNT_QUESTIONS'::text]))),
    CONSTRAINT ck_ai_quota_ledger_bucket_scope CHECK (((scope = 'ACCOUNT'::text) = (bucket = ANY (ARRAY['ACCOUNT_PROPOSALS'::text, 'ACCOUNT_QUESTIONS'::text])))),
    CONSTRAINT ck_ai_quota_ledger_counters CHECK (((cap >= 0) AND (used >= 0) AND (reserved >= 0))),
    CONSTRAINT ck_ai_quota_ledger_month_start CHECK (((bucket <> 'TAVILY_MONTH'::text) OR (EXTRACT(day FROM period_start) = (1)::numeric))),
    CONSTRAINT ck_ai_quota_ledger_scope CHECK ((scope = ANY (ARRAY['GLOBAL'::text, 'ACCOUNT'::text]))),
    CONSTRAINT ck_ai_quota_ledger_scope_account CHECK (((scope = 'ACCOUNT'::text) = (account_id IS NOT NULL)))
);


--
-- Name: TABLE ai_quota_ledger; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.ai_quota_ledger IS 'Free-tier budget per bucket and period (DEC-018, architecture §3.3). period_start is the local date in Asia/Ho_Chi_Minh (first day of the month for TAVILY_MONTH). Reserve: INSERT ... ON CONFLICT DO NOTHING to open the row with cap from settings, then UPDATE ... SET reserved = reserved + :n, cap = :cap WHERE <key, account_id IS NOT DISTINCT FROM :aid> AND used + reserved + :n <= :cap RETURNING; zero rows = exhausted, the caller degrades. Commit moves the actual units from reserved to used (used may exceed cap when the actual count is larger; no CHECK blocks the record); release returns reserved units. GLOBAL buckets have account_id NULL.';


--
-- Name: COLUMN ai_quota_ledger.cap; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ai_quota_ledger.cap IS 'Copied from settings GONARRA_QUOTA_* when the row is opened; may be raised later, never used to reject a commit.';


--
-- Name: areas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.areas (
    code text NOT NULL,
    city_id uuid NOT NULL,
    name_vi text NOT NULL,
    name_en text NOT NULL,
    boundary public.geography(MultiPolygon,4326),
    sort_order smallint DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_areas_code_format CHECK ((code ~ '^[a-z0-9]+(-[a-z0-9]+)*$'::text))
);


--
-- Name: TABLE areas; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.areas IS 'Travel areas of a city (DEC-013, OQ-121): curator-defined, not administrative wards. Used for the Hội An-area release gate (MET-011 rev. 1), area-scoped closure rules and the area label on places and stops. boundary is optional.';


--
-- Name: catalog_audit_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalog_audit_events (
    id bigint NOT NULL,
    actor_account_id uuid,
    entity_table text NOT NULL,
    entity_id uuid NOT NULL,
    action text NOT NULL,
    from_state text,
    to_state text,
    detail jsonb DEFAULT '{}'::jsonb NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_catalog_audit_events_action CHECK ((action = ANY (ARRAY['IMPORT'::text, 'MATCH_REVIEW'::text, 'CONTENT_REVIEW'::text, 'FACT_REVIEW'::text, 'MEDIA_REVIEW'::text, 'PUBLISH'::text, 'WITHDRAW'::text, 'POLICY_CHANGE'::text, 'WEB_PROMOTE'::text, 'WEB_REJECT'::text, 'AUTO_APPROVE'::text, 'AUTO_PUBLISH'::text, 'AUTO_REJECT'::text]))),
    CONSTRAINT ck_catalog_audit_events_detail_object CHECK ((jsonb_typeof(detail) = 'object'::text))
);


--
-- Name: TABLE catalog_audit_events; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.catalog_audit_events IS 'Append-only curator audit trail (FR-015, NFR-015). App role has INSERT/SELECT only. WEB_PROMOTE / WEB_REJECT record curator decisions on web_place_candidates (FR-101); closure-rule reviews are recorded with entity_table = place_closure_rules and FACT_REVIEW.';


--
-- Name: catalog_audit_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.catalog_audit_events ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.catalog_audit_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: catalog_publications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalog_publications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    place_id uuid NOT NULL,
    city_id uuid NOT NULL,
    publication_revision integer NOT NULL,
    state text DEFAULT 'PUBLISHED'::text NOT NULL,
    category_code text NOT NULL,
    area_code text,
    location public.geography(Point,4326) NOT NULL,
    entrance_location public.geography(Point,4326),
    visit_minutes_min smallint NOT NULL,
    visit_minutes_suggested smallint NOT NULL,
    visit_minutes_max smallint NOT NULL,
    localization_vi_id uuid NOT NULL,
    localization_en_id uuid NOT NULL,
    corpus_revision integer,
    published_by_account_id uuid,
    published_at timestamp with time zone DEFAULT now() NOT NULL,
    state_changed_at timestamp with time zone,
    state_reason text,
    CONSTRAINT ck_catalog_publications_publication_revision CHECK ((publication_revision > 0)),
    CONSTRAINT ck_catalog_publications_state CHECK ((state = ANY (ARRAY['PUBLISHED'::text, 'SUPERSEDED'::text, 'WITHDRAWN'::text]))),
    CONSTRAINT ck_catalog_publications_state_change CHECK (((state = 'PUBLISHED'::text) = (state_changed_at IS NULL))),
    CONSTRAINT ck_catalog_publications_visit_minutes CHECK (((visit_minutes_min > 0) AND (visit_minutes_min <= visit_minutes_suggested) AND (visit_minutes_suggested <= visit_minutes_max) AND (visit_minutes_max <= 600)))
);


--
-- Name: TABLE catalog_publications; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.catalog_publications IS 'Immutable publication manifest (snapshot of place attributes + exact revisions). Only state columns change.';


--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    code text NOT NULL,
    name_vi text NOT NULL,
    name_en text NOT NULL,
    sort_order smallint DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_categories_code_format CHECK ((code ~ '^[A-Z][A-Z0-9_]*$'::text))
);


--
-- Name: TABLE categories; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.categories IS 'Curator-maintained place taxonomy shown on details (FR-003) and used for interest matching (FR-021).';


--
-- Name: cities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cities (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code text NOT NULL,
    name_vi text NOT NULL,
    name_en text NOT NULL,
    time_zone text DEFAULT 'Asia/Ho_Chi_Minh'::text NOT NULL,
    boundary public.geography(MultiPolygon,4326),
    is_enabled boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_cities_code_format CHECK ((code ~ '^[a-z0-9]+(-[a-z0-9]+)*$'::text)),
    CONSTRAINT ck_cities_time_zone CHECK ((time_zone = 'Asia/Ho_Chi_Minh'::text))
);


--
-- Name: TABLE cities; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cities IS 'Supported cities (BRU-007 rev. 1, DEC-013): only da-nang is enabled for the FYP; ha-noi, ho-chi-minh-city and hue stay disabled on the roadmap. Hội An is an area of Đà Nẵng (2025 merger), not a city. boundary is the post-merger polygon (OQ-121); optional and, when present, gates publication (OUTSIDE_CITY).';


--
-- Name: data_providers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_providers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    provider_key text NOT NULL,
    display_name text NOT NULL,
    provider_kind text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_data_providers_provider_key_format CHECK ((provider_key ~ '^[a-z0-9_]+$'::text)),
    CONSTRAINT ck_data_providers_provider_kind CHECK ((provider_kind = ANY (ARRAY['OPEN_DATASET'::text, 'RUNTIME_API'::text, 'OFFICIAL_SOURCE'::text, 'MEDIA_LIBRARY'::text, 'AI_SERVICE'::text, 'WEB_SEARCH'::text, 'WEB_CONTENT'::text, 'OPERATOR_DATA'::text])))
);


--
-- Name: TABLE data_providers; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.data_providers IS 'Every external data or service provider that can reach a persistence boundary (BRU-004). WEB_SEARCH (Tavily) and WEB_CONTENT (fetched web pages) feed the research agent (DEC-015).';


--
-- Name: external_place_identities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.external_place_identities (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    place_id uuid NOT NULL,
    data_provider_id uuid NOT NULL,
    upstream_id text NOT NULL,
    upstream_release text,
    match_method text NOT NULL,
    match_confidence numeric(4,3),
    review_state text DEFAULT 'PENDING'::text NOT NULL,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_external_place_identities_match_confidence CHECK (((match_confidence IS NULL) OR ((match_confidence >= (0)::numeric) AND (match_confidence <= (1)::numeric)))),
    CONSTRAINT ck_external_place_identities_match_method CHECK ((match_method = ANY (ARRAY['EXACT_ID'::text, 'NAME_AND_DISTANCE'::text, 'MANUAL'::text]))),
    CONSTRAINT ck_external_place_identities_review_state CHECK ((review_state = ANY (ARRAY['PENDING'::text, 'APPROVED'::text, 'REJECTED'::text]))),
    CONSTRAINT ck_external_place_identities_reviewed CHECK (((review_state = 'PENDING'::text) OR (reviewed_at IS NOT NULL)))
);


--
-- Name: TABLE external_place_identities; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.external_place_identities IS 'Upstream IDs (Overture, Foursquare OS, Wikidata, Google place_id as identifier only). Prevents duplicate candidates (FR-010).';


--
-- Name: fact_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_evidence (
    place_fact_id uuid NOT NULL,
    source_revision_id uuid NOT NULL,
    supported_claim text NOT NULL,
    CONSTRAINT ck_fact_evidence_supported_claim CHECK ((length(supported_claim) > 0))
);


--
-- Name: TABLE fact_evidence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.fact_evidence IS 'Claim-level link fact revision -> source revision (BR-003, FR-005, FR-012).';


--
-- Name: fact_fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_fields (
    code text NOT NULL,
    is_operational boolean NOT NULL,
    required_for_publication boolean DEFAULT false NOT NULL,
    value_kind text NOT NULL,
    stale_after_days smallint,
    CONSTRAINT ck_fact_fields_code_format CHECK ((code ~ '^[A-Z][A-Z0-9_]*$'::text)),
    CONSTRAINT ck_fact_fields_operational_staleness CHECK (((NOT is_operational) OR (stale_after_days IS NOT NULL))),
    CONSTRAINT ck_fact_fields_stale_after_days CHECK (((stale_after_days IS NULL) OR (stale_after_days > 0))),
    CONSTRAINT ck_fact_fields_value_kind CHECK ((value_kind = ANY (ARRAY['HOURS'::text, 'MONEY'::text, 'TEXT'::text, 'LOCATION'::text])))
);


--
-- Name: TABLE fact_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.fact_fields IS 'Fact vocabulary: which fields are operational, which gate publication (BR-004) and when they turn stale (BR-025, ASM-008).';


--
-- Name: guide_message_citations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.guide_message_citations (
    guide_message_id uuid NOT NULL,
    source_revision_id uuid NOT NULL,
    knowledge_chunk_id uuid,
    place_fact_id uuid
);


--
-- Name: guide_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.guide_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    guide_session_id uuid NOT NULL,
    seq integer NOT NULL,
    role text NOT NULL,
    input_mode text,
    content text NOT NULL,
    answer_status text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_guide_messages_answer_status CHECK ((((role = 'ASSISTANT'::text) AND (answer_status = ANY (ARRAY['ANSWERED'::text, 'ANSWERED_WEB_UNVERIFIED'::text, 'INSUFFICIENT_EVIDENCE'::text, 'NOT_RECOGNISED'::text]))) OR ((role = 'TRAVELER'::text) AND (answer_status IS NULL)))),
    CONSTRAINT ck_guide_messages_content_length CHECK (((length(content) >= 1) AND (length(content) <= 4000))),
    CONSTRAINT ck_guide_messages_input_mode CHECK ((((role = 'TRAVELER'::text) AND (input_mode = ANY (ARRAY['TEXT'::text, 'VOICE_TRANSCRIPT'::text, 'PHOTO'::text]))) OR ((role = 'ASSISTANT'::text) AND (input_mode IS NULL)))),
    CONSTRAINT ck_guide_messages_role CHECK ((role = ANY (ARRAY['TRAVELER'::text, 'ASSISTANT'::text]))),
    CONSTRAINT ck_guide_messages_seq CHECK ((seq > 0))
);


--
-- Name: TABLE guide_messages; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.guide_messages IS 'Question/answer text only. Photos, audio and traveler coordinates are never stored.';


--
-- Name: guide_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.guide_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    account_id uuid NOT NULL,
    trip_id uuid,
    place_id uuid,
    locale text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_guide_sessions_locale CHECK ((locale = ANY (ARRAY['vi'::text, 'en'::text])))
);


--
-- Name: TABLE guide_sessions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.guide_sessions IS 'Private Guide conversation: city-level (place_id NULL), or one published place; optionally linked to an owned trip (FR-056, FR-069, DEC-017).';


--
-- Name: idempotency_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.idempotency_records (
    account_id uuid NOT NULL,
    operation text NOT NULL,
    idempotency_key text NOT NULL,
    request_sha256 character(64) NOT NULL,
    state text DEFAULT 'IN_PROGRESS'::text NOT NULL,
    response_status smallint,
    response_body jsonb,
    resource_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    CONSTRAINT ck_idempotency_records_completed CHECK (((state = 'COMPLETED'::text) = (response_status IS NOT NULL))),
    CONSTRAINT ck_idempotency_records_expiry CHECK ((expires_at > created_at)),
    CONSTRAINT ck_idempotency_records_key_length CHECK (((length(idempotency_key) >= 8) AND (length(idempotency_key) <= 128))),
    CONSTRAINT ck_idempotency_records_operation CHECK ((operation = ANY (ARRAY['TRIP_SAVE'::text, 'PREVIEW_CREATE'::text, 'DAY_REGENERATE'::text, 'ACCOUNT_DELETE'::text, 'TRIP_CREATE'::text, 'PREVIEW_EDIT'::text, 'PUBLISH'::text, 'GUIDE_ASK'::text]))),
    CONSTRAINT ck_idempotency_records_request_sha256_format CHECK ((request_sha256 ~ '^[0-9a-f]{64}$'::text)),
    CONSTRAINT ck_idempotency_records_state CHECK ((state = ANY (ARRAY['IN_PROGRESS'::text, 'COMPLETED'::text])))
);


--
-- Name: TABLE idempotency_records; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.idempotency_records IS 'Replay protection for Save and other replayable writes (FR-041). Same key + different request hash = rejected.';


--
-- Name: import_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.import_records (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    import_run_id uuid NOT NULL,
    upstream_id text NOT NULL,
    raw_name text NOT NULL,
    normalized_name text NOT NULL,
    upstream_category text,
    location public.geography(Point,4326) NOT NULL,
    allowed_payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    validation_status text NOT NULL,
    rejection_reason text,
    match_state text DEFAULT 'UNMATCHED'::text NOT NULL,
    place_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_import_records_allowed_payload_object CHECK ((jsonb_typeof(allowed_payload) = 'object'::text)),
    CONSTRAINT ck_import_records_match_state CHECK ((match_state = ANY (ARRAY['UNMATCHED'::text, 'MATCHED'::text, 'AMBIGUOUS'::text, 'NEW_CANDIDATE'::text]))),
    CONSTRAINT ck_import_records_normalized_lower CHECK ((normalized_name = lower(normalized_name))),
    CONSTRAINT ck_import_records_rejection_reason CHECK (((validation_status = 'REJECTED'::text) = (rejection_reason IS NOT NULL))),
    CONSTRAINT ck_import_records_validation_status CHECK ((validation_status = ANY (ARRAY['ACCEPTED'::text, 'REJECTED'::text])))
);


--
-- Name: TABLE import_records; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.import_records IS 'Staging rows. allowed_payload holds only fields allowed by provider_field_rules of the run policy.';


--
-- Name: import_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.import_runs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    data_provider_id uuid NOT NULL,
    provider_policy_id uuid NOT NULL,
    city_id uuid NOT NULL,
    release_id text NOT NULL,
    checksum_sha256 character(64) NOT NULL,
    importer_version text NOT NULL,
    status text DEFAULT 'RUNNING'::text NOT NULL,
    record_count integer,
    accepted_count integer,
    rejected_count integer,
    duplicate_count integer,
    failure_code text,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    CONSTRAINT ck_import_runs_checksum_format CHECK ((checksum_sha256 ~ '^[0-9a-f]{64}$'::text)),
    CONSTRAINT ck_import_runs_completion CHECK (((status = 'RUNNING'::text) = (completed_at IS NULL))),
    CONSTRAINT ck_import_runs_counts CHECK ((((record_count IS NULL) OR (record_count >= 0)) AND ((accepted_count IS NULL) OR (accepted_count >= 0)) AND ((rejected_count IS NULL) OR (rejected_count >= 0)) AND ((duplicate_count IS NULL) OR (duplicate_count >= 0)))),
    CONSTRAINT ck_import_runs_failure_code CHECK (((status = 'FAILED'::text) = (failure_code IS NOT NULL))),
    CONSTRAINT ck_import_runs_status CHECK ((status = ANY (ARRAY['RUNNING'::text, 'SUCCEEDED'::text, 'FAILED'::text])))
);


--
-- Name: TABLE import_runs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.import_runs IS 'One bounded open-data import (FR-009). A FAILED run never touches published rows.';


--
-- Name: knowledge_chunk_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_chunk_sources (
    knowledge_chunk_id uuid NOT NULL,
    source_revision_id uuid NOT NULL
);


--
-- Name: knowledge_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_chunks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    city_id uuid NOT NULL,
    place_id uuid,
    scope text DEFAULT 'PLACE'::text NOT NULL,
    locale text NOT NULL,
    section text NOT NULL,
    corpus_revision integer NOT NULL,
    chunk_index smallint NOT NULL,
    content text NOT NULL,
    content_sha256 character(64) NOT NULL,
    embedding public.vector(768),
    embedding_model text,
    review_state text DEFAULT 'DRAFT'::text NOT NULL,
    retired_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_knowledge_chunks_approved_embedded CHECK (((review_state <> 'APPROVED'::text) OR ((embedding IS NOT NULL) AND (embedding_model IS NOT NULL)))),
    CONSTRAINT ck_knowledge_chunks_chunk_index CHECK ((chunk_index >= 0)),
    CONSTRAINT ck_knowledge_chunks_content_length CHECK (((length(content) >= 1) AND (length(content) <= 4000))),
    CONSTRAINT ck_knowledge_chunks_content_sha256_format CHECK ((content_sha256 ~ '^[0-9a-f]{64}$'::text)),
    CONSTRAINT ck_knowledge_chunks_corpus_revision CHECK ((corpus_revision > 0)),
    CONSTRAINT ck_knowledge_chunks_locale CHECK ((locale = ANY (ARRAY['vi'::text, 'en'::text]))),
    CONSTRAINT ck_knowledge_chunks_retired CHECK (((review_state = 'RETIRED'::text) = (retired_at IS NOT NULL))),
    CONSTRAINT ck_knowledge_chunks_review_state CHECK ((review_state = ANY (ARRAY['DRAFT'::text, 'APPROVED'::text, 'RETIRED'::text]))),
    CONSTRAINT ck_knowledge_chunks_scope CHECK ((scope = ANY (ARRAY['PLACE'::text, 'CITY'::text]))),
    CONSTRAINT ck_knowledge_chunks_scope_place CHECK (((scope = 'PLACE'::text) = (place_id IS NOT NULL))),
    CONSTRAINT ck_knowledge_chunks_section CHECK ((section = ANY (ARRAY['OVERVIEW'::text, 'HISTORY'::text, 'HIGHLIGHTS'::text, 'VISIT_TIPS'::text, 'ETIQUETTE'::text, 'ACCESS'::text, 'CITY_OVERVIEW'::text, 'GETTING_AROUND'::text, 'EVENTS_CALENDAR'::text, 'PRACTICAL'::text]))),
    CONSTRAINT ck_knowledge_chunks_section_scope CHECK (((scope = 'CITY'::text) = (section = ANY (ARRAY['CITY_OVERVIEW'::text, 'GETTING_AROUND'::text, 'EVENTS_CALENDAR'::text, 'PRACTICAL'::text]))))
);


--
-- Name: TABLE knowledge_chunks; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.knowledge_chunks IS 'Approved original narrative chunks for the Guide (FR-056..FR-058, FR-104), one per section per locale and corpus revision; embedded on write by the curation API (ADR-012). scope PLACE rows belong to a place; scope CITY rows (DEC-017) belong to the city only. Never a source of operational facts.';


--
-- Name: COLUMN knowledge_chunks.section; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.knowledge_chunks.section IS 'Citation unit. PLACE scope: OVERVIEW, HISTORY, HIGHLIGHTS, VISIT_TIPS, ETIQUETTE, ACCESS. CITY scope: CITY_OVERVIEW, GETTING_AROUND, EVENTS_CALENDAR, PRACTICAL (ADR-010 1.0).';


--
-- Name: COLUMN knowledge_chunks.embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.knowledge_chunks.embedding IS 'gemini-embedding-001 with output_dimensionality=768, L2-normalised before storage (OQ-126); vector(768) is pinned to that model.';


--
-- Name: media_assets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.media_assets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    object_key text NOT NULL,
    content_type text NOT NULL,
    width_px integer NOT NULL,
    height_px integer NOT NULL,
    sha256 character(64) NOT NULL,
    creator text NOT NULL,
    source_revision_id uuid,
    license_code text NOT NULL,
    attribution_text text NOT NULL,
    rights_proof_key text,
    rights_state text DEFAULT 'PENDING'::text NOT NULL,
    rights_expires_on date,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_media_assets_content_type CHECK ((content_type = ANY (ARRAY['image/jpeg'::text, 'image/png'::text, 'image/webp'::text]))),
    CONSTRAINT ck_media_assets_dimensions CHECK (((width_px > 0) AND (height_px > 0))),
    CONSTRAINT ck_media_assets_rights_state CHECK ((rights_state = ANY (ARRAY['PENDING'::text, 'CLEARED'::text, 'REVOKED'::text]))),
    CONSTRAINT ck_media_assets_sha256_format CHECK ((sha256 ~ '^[0-9a-f]{64}$'::text))
);


--
-- Name: TABLE media_assets; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.media_assets IS 'S3 object reference with per-file licence, creator and attribution (own photos, Wikimedia Commons).';


--
-- Name: place_aliases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.place_aliases (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    place_id uuid NOT NULL,
    locale text NOT NULL,
    alias_kind text NOT NULL,
    alias text NOT NULL,
    alias_normalized text NOT NULL,
    review_state text DEFAULT 'DRAFT'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_place_aliases_alias_kind CHECK ((alias_kind = ANY (ARRAY['NAME'::text, 'ALIAS'::text]))),
    CONSTRAINT ck_place_aliases_locale CHECK ((locale = ANY (ARRAY['vi'::text, 'en'::text]))),
    CONSTRAINT ck_place_aliases_normalized_lower CHECK (((alias_normalized = lower(alias_normalized)) AND (length(alias_normalized) > 0))),
    CONSTRAINT ck_place_aliases_review_state CHECK ((review_state = ANY (ARRAY['DRAFT'::text, 'APPROVED'::text, 'REJECTED'::text])))
);


--
-- Name: TABLE place_aliases; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.place_aliases IS 'Search forms: reviewed names and aliases, normalized by the API (lower case, diacritics removed, đ->d) for FR-002.';


--
-- Name: place_closure_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.place_closure_rules (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    city_id uuid NOT NULL,
    applies_to text NOT NULL,
    place_id uuid,
    area_code text,
    rule_kind text NOT NULL,
    effect text NOT NULL,
    params jsonb DEFAULT '{}'::jsonb NOT NULL,
    severity text NOT NULL,
    note_vi text NOT NULL,
    note_en text NOT NULL,
    effective_from date,
    effective_to date,
    source_revision_id uuid,
    review_state text DEFAULT 'DRAFT'::text NOT NULL,
    verified_at timestamp with time zone,
    reviewed_by_account_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_place_closure_rules_applies_to CHECK ((applies_to = ANY (ARRAY['PLACE'::text, 'AREA'::text, 'CITY'::text]))),
    CONSTRAINT ck_place_closure_rules_approved_verified CHECK (((review_state <> 'APPROVED'::text) OR ((verified_at IS NOT NULL) AND (source_revision_id IS NOT NULL)))),
    CONSTRAINT ck_place_closure_rules_effect CHECK ((effect = ANY (ARRAY['CLOSED'::text, 'PARTIAL'::text, 'EVENT'::text, 'NOTICE'::text]))),
    CONSTRAINT ck_place_closure_rules_effective_range CHECK (((effective_from IS NULL) OR (effective_to IS NULL) OR (effective_from <= effective_to))),
    CONSTRAINT ck_place_closure_rules_notes CHECK ((((length(note_vi) >= 1) AND (length(note_vi) <= 500)) AND ((length(note_en) >= 1) AND (length(note_en) <= 500)))),
    CONSTRAINT ck_place_closure_rules_params_object CHECK ((jsonb_typeof(params) = 'object'::text)),
    CONSTRAINT ck_place_closure_rules_review_state CHECK ((review_state = ANY (ARRAY['DRAFT'::text, 'APPROVED'::text, 'RETIRED'::text]))),
    CONSTRAINT ck_place_closure_rules_rule_kind CHECK ((rule_kind = ANY (ARRAY['WEEKLY'::text, 'DATE'::text, 'LUNAR_DATE'::text, 'SEASON'::text, 'TICKET_VALIDITY'::text]))),
    CONSTRAINT ck_place_closure_rules_severity CHECK ((severity = ANY (ARRAY['BLOCKING'::text, 'WARNING'::text]))),
    CONSTRAINT ck_place_closure_rules_target CHECK ((((applies_to = 'PLACE'::text) AND (place_id IS NOT NULL) AND (area_code IS NULL)) OR ((applies_to = 'AREA'::text) AND (area_code IS NOT NULL) AND (place_id IS NULL)) OR ((applies_to = 'CITY'::text) AND (place_id IS NULL) AND (area_code IS NULL))))
);


--
-- Name: TABLE place_closure_rules; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.place_closure_rules IS 'Curator-reviewed calendar rules evaluated by deterministic Plan Health code (DEC-016, FR-102, FR-107): weekly closures, fixed dates, lunar dates (Tết, Hội An lantern nights), seasons and ticket validity. AI never writes here. Only APPROVED rules are evaluated; an approved rule needs verified_at and a source.';


--
-- Name: COLUMN place_closure_rules.effect; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.place_closure_rules.effect IS 'CLOSED = place/area closed (BLOCKING by default); PARTIAL = reduced hours or access; EVENT = special event (e.g. lantern night, Tết); NOTICE = advisory text only.';


--
-- Name: COLUMN place_closure_rules.params; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.place_closure_rules.params IS 'Shape by rule_kind; every kind also accepts optional {"from":"HH:MM","to":"HH:MM"} (window within the day) and {"restricted_modes":["WALK"|"DRIVE"|"TWO_WHEELER"]} (migration 0006). WEEKLY {"weekdays":[1..7]} (ISO, 1 = Monday) with optional {"from":"HH:MM","to":"HH:MM"}; DATE {"dates":["YYYY-MM-DD"]} or {"month_day":["MM-DD"]} (yearly); LUNAR_DATE {"lunar_days":[1,14,15],"lunar_months":[...]|null} resolved by the pure-Python VN lunar algorithm, UTC+7 (OQ-125); SEASON {"from_month_day":"MM-DD","to_month_day":"MM-DD"}; TICKET_VALIDITY {"valid_same_day":true} or {"valid_hours":24}.';


--
-- Name: place_facts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.place_facts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    place_id uuid NOT NULL,
    field_code text NOT NULL,
    fact_revision integer NOT NULL,
    knowledge_state text NOT NULL,
    value jsonb,
    verified_at timestamp with time zone,
    valid_until date,
    review_state text DEFAULT 'DRAFT'::text NOT NULL,
    conflict_state text DEFAULT 'NONE'::text NOT NULL,
    conflict_note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    origin text DEFAULT 'SOURCE'::text NOT NULL,
    grounding text,
    CONSTRAINT ck_place_facts_approved_verified CHECK (((review_state <> ALL (ARRAY['APPROVED'::text, 'SUPERSEDED'::text])) OR (verified_at IS NOT NULL))),
    CONSTRAINT ck_place_facts_conflict_note CHECK (((conflict_state = 'NONE'::text) OR (conflict_note IS NOT NULL))),
    CONSTRAINT ck_place_facts_conflict_state CHECK ((conflict_state = ANY (ARRAY['NONE'::text, 'OPEN'::text, 'RESOLVED'::text]))),
    CONSTRAINT ck_place_facts_entrance_shape CHECK (((field_code <> 'ENTRANCE_LOCATION'::text) OR (value IS NULL) OR ((value ? 'lat'::text) AND (value ? 'lng'::text) AND ((((value ->> 'lat'::text))::numeric >= ('-90'::integer)::numeric) AND (((value ->> 'lat'::text))::numeric <= (90)::numeric)) AND ((((value ->> 'lng'::text))::numeric >= ('-180'::integer)::numeric) AND (((value ->> 'lng'::text))::numeric <= (180)::numeric))))),
    CONSTRAINT ck_place_facts_fact_revision CHECK ((fact_revision > 0)),
    CONSTRAINT ck_place_facts_grounding CHECK ((grounding = ANY (ARRAY['STRONG'::text, 'WEAK'::text]))),
    CONSTRAINT ck_place_facts_grounding_origin CHECK (((grounding IS NULL) OR (origin = 'AI_EXTRACTED'::text))),
    CONSTRAINT ck_place_facts_knowledge_state CHECK ((knowledge_state = ANY (ARRAY['KNOWN'::text, 'UNKNOWN'::text, 'NOT_APPLICABLE'::text]))),
    CONSTRAINT ck_place_facts_origin CHECK ((origin = ANY (ARRAY['SOURCE'::text, 'OWNER'::text, 'AI_EXTRACTED'::text]))),
    CONSTRAINT ck_place_facts_review_state CHECK ((review_state = ANY (ARRAY['DRAFT'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUPERSEDED'::text]))),
    CONSTRAINT ck_place_facts_value_object CHECK (((value IS NULL) OR (jsonb_typeof(value) = 'object'::text))),
    CONSTRAINT ck_place_facts_value_presence CHECK (((knowledge_state = 'KNOWN'::text) = (value IS NOT NULL)))
);


--
-- Name: TABLE place_facts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.place_facts IS 'Versioned operational/structured facts with explicit KNOWN/UNKNOWN/NOT_APPLICABLE (BR-024, FR-006, FR-012). AI never writes here (BRU-002).';


--
-- Name: COLUMN place_facts.origin; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.place_facts.origin IS 'SOURCE | OWNER | AI_EXTRACTED (migration 0009, DEC-028): AI_EXTRACTED = extracted by the grounded writer from the cited evidence revision, never invented; label it in the UI.';


--
-- Name: COLUMN place_facts.grounding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.place_facts.grounding IS 'STRONG | WEAK for AI_EXTRACTED facts: the model quote overlaps the cited evidence text by >= 0.5 of its tokens (STRONG) or not (WEAK); NULL otherwise.';


--
-- Name: place_localizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.place_localizations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    place_id uuid NOT NULL,
    locale text NOT NULL,
    localization_revision integer NOT NULL,
    name text NOT NULL,
    short_description text,
    description text,
    translation_origin text NOT NULL,
    review_state text DEFAULT 'DRAFT'::text NOT NULL,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    name_is_source_fallback boolean DEFAULT false NOT NULL,
    CONSTRAINT ck_place_localizations_approved_complete CHECK (((review_state <> ALL (ARRAY['APPROVED'::text, 'SUPERSEDED'::text])) OR ((reviewed_at IS NOT NULL) AND (description IS NOT NULL)))),
    CONSTRAINT ck_place_localizations_locale CHECK ((locale = ANY (ARRAY['vi'::text, 'en'::text]))),
    CONSTRAINT ck_place_localizations_localization_revision CHECK ((localization_revision > 0)),
    CONSTRAINT ck_place_localizations_review_state CHECK ((review_state = ANY (ARRAY['DRAFT'::text, 'APPROVED'::text, 'REJECTED'::text, 'SUPERSEDED'::text]))),
    CONSTRAINT ck_place_localizations_translation_origin CHECK ((translation_origin = ANY (ARRAY['ORIGINAL'::text, 'HUMAN_TRANSLATION'::text, 'AI_DRAFT'::text, 'AI_SUMMARY'::text])))
);


--
-- Name: TABLE place_localizations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.place_localizations IS 'Reviewed VI/EN names and original descriptions (BR-004, FR-011). AI_DRAFT needs curator approval (FR-019).';


--
-- Name: COLUMN place_localizations.translation_origin; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.place_localizations.translation_origin IS 'ORIGINAL | HUMAN_TRANSLATION | AI_DRAFT | AI_SUMMARY (migration 0007; the description was written by the grounded writer from cited source revisions; label it in the UI).';


--
-- Name: COLUMN place_localizations.name_is_source_fallback; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.place_localizations.name_is_source_fallback IS 'true = this locale has no source name; the original Vietnamese proper name is reused unchanged (never translated).';


--
-- Name: place_media; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.place_media (
    place_id uuid NOT NULL,
    media_asset_id uuid NOT NULL,
    ordinal smallint NOT NULL,
    alt_text_vi text NOT NULL,
    alt_text_en text NOT NULL,
    CONSTRAINT ck_place_media_ordinal CHECK ((ordinal > 0))
);


--
-- Name: places; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.places (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    city_id uuid NOT NULL,
    area_code text,
    slug text NOT NULL,
    category_code text,
    workflow_state text DEFAULT 'IMPORTED'::text NOT NULL,
    location public.geography(Point,4326) NOT NULL,
    visit_minutes_min smallint,
    visit_minutes_suggested smallint,
    visit_minutes_max smallint,
    has_no_media boolean DEFAULT false NOT NULL,
    content_revision integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_places_content_revision CHECK ((content_revision > 0)),
    CONSTRAINT ck_places_ready_complete CHECK (((workflow_state <> ALL (ARRAY['READY_TO_PUBLISH'::text, 'PUBLISHED'::text])) OR ((category_code IS NOT NULL) AND (visit_minutes_min IS NOT NULL) AND (visit_minutes_suggested IS NOT NULL) AND (visit_minutes_max IS NOT NULL)))),
    CONSTRAINT ck_places_slug_format CHECK ((slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'::text)),
    CONSTRAINT ck_places_visit_minutes CHECK ((((visit_minutes_min IS NULL) OR (visit_minutes_min > 0)) AND ((visit_minutes_min IS NULL) OR (visit_minutes_suggested IS NULL) OR (visit_minutes_min <= visit_minutes_suggested)) AND ((visit_minutes_suggested IS NULL) OR (visit_minutes_max IS NULL) OR (visit_minutes_suggested <= visit_minutes_max)) AND ((visit_minutes_max IS NULL) OR (visit_minutes_max <= 600)))),
    CONSTRAINT ck_places_workflow_state CHECK ((workflow_state = ANY (ARRAY['IMPORTED'::text, 'MATCH_REVIEW'::text, 'CONTENT_REVIEW'::text, 'READY_TO_PUBLISH'::text, 'PUBLISHED'::text, 'RETIRED'::text])))
);


--
-- Name: TABLE places; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.places IS 'Stable Gonarra place identity (candidate until published). location = place position for map and routing fallback (FR-003, FR-054). area_code = travel area within the city (DEC-013); the composite FK keeps area and place in the same city.';


--
-- Name: places_lookup_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.places_lookup_cache (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_sha256 character(64),
    google_place_id text,
    outcome text NOT NULL,
    location public.geography(Point,4326),
    location_expires_at timestamp with time zone,
    provider_policy_id uuid NOT NULL,
    fetched_at timestamp with time zone DEFAULT now() NOT NULL,
    outcome_expires_at timestamp with time zone NOT NULL,
    CONSTRAINT ck_places_lookup_cache_key CHECK (((query_sha256 IS NOT NULL) OR (google_place_id IS NOT NULL))),
    CONSTRAINT ck_places_lookup_cache_location_expiry CHECK ((((location IS NULL) = (location_expires_at IS NULL)) AND ((location_expires_at IS NULL) OR (location_expires_at <= (fetched_at + '30 days'::interval))))),
    CONSTRAINT ck_places_lookup_cache_outcome CHECK ((outcome = ANY (ARRAY['EXISTS_OPERATIONAL'::text, 'EXISTS_CLOSED'::text, 'NOT_FOUND'::text, 'OUTSIDE_CITY'::text]))),
    CONSTRAINT ck_places_lookup_cache_outcome_expiry CHECK (((outcome_expires_at > fetched_at) AND (outcome_expires_at <= (fetched_at + '24:00:00'::interval)))),
    CONSTRAINT ck_places_lookup_cache_outcome_identity CHECK (((outcome = 'NOT_FOUND'::text) = (google_place_id IS NULL))),
    CONSTRAINT ck_places_lookup_cache_query_sha256_format CHECK (((query_sha256 IS NULL) OR (query_sha256 ~ '^[0-9a-f]{64}$'::text)))
);


--
-- Name: TABLE places_lookup_cache; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.places_lookup_cache IS 'Google Places existence/status check results (ADR-006, ADR-014). Stores the place_id (IDENTIFIER_ONLY), Gonarra''s own verdict outcome (24 h) and an ephemeral lat/lng copy (<= 30 d, OQ-124; never copied into places or web_place_candidates). Google business_status and opening hours are DENY (runtime only) and have no column. query_sha256 = SHA-256 of the redacted text-search query (name + city), so repeated lookups of the same candidate hit the cache. The sweep nulls location after location_expires_at and deletes the row after outcome_expires_at.';


--
-- Name: plan_previews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plan_previews (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    account_id uuid NOT NULL,
    trip_id uuid NOT NULL,
    base_trip_revision integer NOT NULL,
    head_revision integer DEFAULT 0 NOT NULL,
    status text DEFAULT 'ACTIVE'::text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_plan_previews_base_trip_revision CHECK ((base_trip_revision >= 0)),
    CONSTRAINT ck_plan_previews_head_revision CHECK ((head_revision >= 0)),
    CONSTRAINT ck_plan_previews_status CHECK ((status = ANY (ARRAY['ACTIVE'::text, 'SAVED'::text, 'DISCARDED'::text, 'EXPIRED'::text])))
);


--
-- Name: TABLE plan_previews; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.plan_previews IS 'Unsaved proposal identity bound to owner, trip and base revision; survives provider failures (BR-033).';


--
-- Name: preview_revisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.preview_revisions (
    plan_preview_id uuid NOT NULL,
    preview_revision integer NOT NULL,
    parent_revision integer,
    origin text NOT NULL,
    plan_health text NOT NULL,
    snapshot jsonb NOT NULL,
    model_version text,
    prompt_version text,
    corpus_revision integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_preview_revisions_model_recorded CHECK (((origin = 'MANUAL_EDIT'::text) OR (model_version IS NOT NULL))),
    CONSTRAINT ck_preview_revisions_origin CHECK ((origin = ANY (ARRAY['GENERATED'::text, 'MANUAL_EDIT'::text, 'DAY_REGENERATED'::text, 'REPAIRED'::text]))),
    CONSTRAINT ck_preview_revisions_parent CHECK (((parent_revision IS NULL) OR ((parent_revision > 0) AND (parent_revision < preview_revision)))),
    CONSTRAINT ck_preview_revisions_plan_health CHECK ((plan_health = ANY (ARRAY['GOOD'::text, 'WARNING'::text, 'BLOCKED'::text]))),
    CONSTRAINT ck_preview_revisions_preview_revision CHECK ((preview_revision > 0)),
    CONSTRAINT ck_preview_revisions_snapshot_object CHECK (((jsonb_typeof(snapshot) = 'object'::text) AND (snapshot ? 'days'::text)))
);


--
-- Name: TABLE preview_revisions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.preview_revisions IS 'Immutable proposal snapshots (days, stops, legs, health, warnings). Intentional JSONB document; see model.md §2.4.';


--
-- Name: provider_field_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.provider_field_rules (
    provider_policy_id uuid NOT NULL,
    field_name text NOT NULL,
    persistence_class text NOT NULL,
    max_retention interval,
    CONSTRAINT ck_provider_field_rules_ephemeral_retention CHECK (((persistence_class <> 'ALLOW_EPHEMERAL'::text) OR (max_retention IS NOT NULL))),
    CONSTRAINT ck_provider_field_rules_persistence_class CHECK ((persistence_class = ANY (ARRAY['ALLOW_CANONICAL'::text, 'ALLOW_EPHEMERAL'::text, 'ALLOW_IDENTIFIER_ONLY'::text, 'DENY'::text])))
);


--
-- Name: TABLE provider_field_rules; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.provider_field_rules IS 'Field allowlist per policy revision. A field without a row is DENY (default deny, BRU-004).';


--
-- Name: provider_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.provider_policies (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    data_provider_id uuid NOT NULL,
    policy_revision integer NOT NULL,
    terms_version text NOT NULL,
    terms_url text NOT NULL,
    purpose text NOT NULL,
    attribution_text text,
    status text DEFAULT 'DRAFT'::text NOT NULL,
    approved_at timestamp with time zone,
    next_review_on date,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_provider_policies_active_approved CHECK (((status <> 'ACTIVE'::text) OR (approved_at IS NOT NULL))),
    CONSTRAINT ck_provider_policies_policy_revision CHECK ((policy_revision > 0)),
    CONSTRAINT ck_provider_policies_status CHECK ((status = ANY (ARRAY['DRAFT'::text, 'ACTIVE'::text, 'RETIRED'::text])))
);


--
-- Name: TABLE provider_policies; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.provider_policies IS 'Immutable policy revisions: terms, purpose, attribution, review date. One ACTIVE per provider.';


--
-- Name: publication_facts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.publication_facts (
    catalog_publication_id uuid NOT NULL,
    place_fact_id uuid NOT NULL
);


--
-- Name: publication_media; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.publication_media (
    catalog_publication_id uuid NOT NULL,
    media_asset_id uuid NOT NULL,
    ordinal smallint NOT NULL,
    CONSTRAINT ck_publication_media_ordinal CHECK ((ordinal > 0))
);


--
-- Name: query_embedding_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.query_embedding_cache (
    text_sha256 character(64) NOT NULL,
    locale text NOT NULL,
    embedding_model text NOT NULL,
    embedding public.vector(768) NOT NULL,
    provider_policy_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    CONSTRAINT ck_query_embedding_cache_expiry CHECK (((expires_at > created_at) AND (expires_at <= (created_at + '90 days'::interval)))),
    CONSTRAINT ck_query_embedding_cache_locale CHECK ((locale = ANY (ARRAY['vi'::text, 'en'::text]))),
    CONSTRAINT ck_query_embedding_cache_text_sha256_format CHECK ((text_sha256 ~ '^[0-9a-f]{64}$'::text))
);


--
-- Name: TABLE query_embedding_cache; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.query_embedding_cache IS 'Guide question embeddings (ADR-010 1.0, 90 d). Key = SHA-256 of the normalised, redacted question; the question text is never stored. embedding_model must equal the chunks'' embedding_model (vector(768), OQ-126).';


--
-- Name: research_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.research_cache (
    provider text NOT NULL,
    key_sha256 character(64) NOT NULL,
    payload jsonb NOT NULL,
    source_revision_id uuid,
    provider_policy_id uuid NOT NULL,
    fetched_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    CONSTRAINT ck_research_cache_expiry CHECK (((expires_at > fetched_at) AND (expires_at <= (fetched_at + '7 days'::interval)))),
    CONSTRAINT ck_research_cache_key_sha256_format CHECK ((key_sha256 ~ '^[0-9a-f]{64}$'::text)),
    CONSTRAINT ck_research_cache_payload_object CHECK ((jsonb_typeof(payload) = 'object'::text)),
    CONSTRAINT ck_research_cache_payload_size CHECK ((octet_length((payload)::text) <= 262144)),
    CONSTRAINT ck_research_cache_provider CHECK ((provider = ANY (ARRAY['TAVILY'::text, 'WEB_PAGE'::text]))),
    CONSTRAINT ck_research_cache_source_revision CHECK (((provider = 'WEB_PAGE'::text) OR (source_revision_id IS NULL)))
);


--
-- Name: TABLE research_cache; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.research_cache IS 'Ephemeral research inputs (ADR-006 tavily / web_page EPHEMERAL 7 d, OQ-122). TAVILY: key = SHA-256 of the redacted, normalised query; payload = results (url, title, snippet). WEB_PAGE: key = SHA-256 of the normalised URL; payload = extracted text; the canonical provenance is the linked source_revisions row. Never shown as a fact and never copied into catalog tables.';


--
-- Name: route_legs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.route_legs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    trip_day_id uuid NOT NULL,
    from_stop_id uuid NOT NULL,
    to_stop_id uuid NOT NULL,
    travel_mode text NOT NULL,
    availability text NOT NULL,
    distance_m integer,
    duration_s integer,
    data_provider_id uuid,
    measured_at timestamp with time zone,
    expires_at timestamp with time zone,
    CONSTRAINT ck_route_legs_availability CHECK ((availability = ANY (ARRAY['AVAILABLE'::text, 'UNAVAILABLE'::text, 'EXPIRED'::text]))),
    CONSTRAINT ck_route_legs_distinct_stops CHECK ((from_stop_id <> to_stop_id)),
    CONSTRAINT ck_route_legs_expiry CHECK (((expires_at IS NULL) OR (measured_at IS NULL) OR (expires_at > measured_at))),
    CONSTRAINT ck_route_legs_measurement CHECK (((availability = 'AVAILABLE'::text) = ((distance_m IS NOT NULL) AND (duration_s IS NOT NULL) AND (data_provider_id IS NOT NULL) AND (measured_at IS NOT NULL)))),
    CONSTRAINT ck_route_legs_measurement_values CHECK ((((distance_m IS NULL) OR (distance_m >= 0)) AND ((duration_s IS NULL) OR (duration_s >= 0)))),
    CONSTRAINT ck_route_legs_travel_mode CHECK ((travel_mode = ANY (ARRAY['WALK'::text, 'DRIVE'::text])))
);


--
-- Name: TABLE route_legs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.route_legs IS 'Directed leg between consecutive saved stops. Distance/duration only from the routing provider (BRU-006); NULL when unavailable or expired.';


--
-- Name: routes_matrix_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.routes_matrix_cache (
    origin_key text NOT NULL,
    destination_key text NOT NULL,
    travel_mode text NOT NULL,
    availability text NOT NULL,
    distance_m integer,
    duration_s integer,
    provider_policy_id uuid NOT NULL,
    fetched_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    CONSTRAINT ck_routes_matrix_cache_availability CHECK ((availability = ANY (ARRAY['AVAILABLE'::text, 'UNAVAILABLE'::text]))),
    CONSTRAINT ck_routes_matrix_cache_destination_key_format CHECK ((destination_key ~ '^(place|web|anchor):[a-z0-9-]{1,64}$'::text)),
    CONSTRAINT ck_routes_matrix_cache_distinct_keys CHECK ((origin_key <> destination_key)),
    CONSTRAINT ck_routes_matrix_cache_expiry CHECK (((expires_at > fetched_at) AND (expires_at <= (fetched_at + '30 days'::interval)))),
    CONSTRAINT ck_routes_matrix_cache_measurement CHECK (((availability = 'AVAILABLE'::text) = ((distance_m IS NOT NULL) AND (duration_s IS NOT NULL)))),
    CONSTRAINT ck_routes_matrix_cache_measurement_values CHECK ((((distance_m IS NULL) OR (distance_m >= 0)) AND ((duration_s IS NULL) OR (duration_s >= 0)))),
    CONSTRAINT ck_routes_matrix_cache_origin_key_format CHECK ((origin_key ~ '^(place|web|anchor):[a-z0-9-]{1,64}$'::text)),
    CONSTRAINT ck_routes_matrix_cache_travel_mode CHECK ((travel_mode = ANY (ARRAY['WALK'::text, 'DRIVE'::text])))
);


--
-- Name: TABLE routes_matrix_cache; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.routes_matrix_cache IS 'Pairwise Google Routes measurements (ADR-011, ADR-006 google_routes EPHEMERAL <= 30 d). Keys: place:<places.id>, web:<web_place_candidates.id>, anchor:<fixed day-start anchor code>; never traveler GPS. WALK is requested only for pairs <= 2.5 km. UNAVAILABLE pairs are cached as unavailable, never estimated (BRU-006).';


--
-- Name: source_revisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.source_revisions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_id uuid NOT NULL,
    locator text NOT NULL,
    title text,
    retrieved_at timestamp with time zone NOT NULL,
    content_sha256 character(64),
    private_evidence_key text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_source_revisions_content_sha256_format CHECK (((content_sha256 IS NULL) OR (content_sha256 ~ '^[0-9a-f]{64}$'::text)))
);


--
-- Name: TABLE source_revisions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.source_revisions IS 'Immutable capture of one URL/document as consulted; private_evidence_key points to an access-controlled object store key. The research agent appends one row per fetched URL (locator = URL, retrieved_at = fetched_at, content_sha256 of the page text; the text itself is EPHEMERAL in research_cache under the web_page policy).';


--
-- Name: sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sources (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    data_provider_id uuid,
    publisher text NOT NULL,
    source_kind text NOT NULL,
    homepage_url text,
    license_code text NOT NULL,
    attribution_text text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_sources_source_kind CHECK ((source_kind = ANY (ARRAY['OFFICIAL'::text, 'OPEN_DATA'::text, 'REFERENCE'::text, 'OWN_OBSERVATION'::text, 'WEB'::text])))
);


--
-- Name: TABLE sources; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sources IS 'Publisher with licence and required attribution text (FR-008, FR-016). NULL attribution blocks publication. WEB = a web site reached by the research agent (DEC-015); one source per host, one source_revisions row per fetched URL.';


--
-- Name: study_participants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study_participants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    account_id uuid,
    participant_code text NOT NULL,
    enrolled_at timestamp with time zone DEFAULT now() NOT NULL,
    withdrawn_at timestamp with time zone,
    CONSTRAINT ck_study_participants_participant_code_format CHECK ((participant_code ~ '^[A-Z0-9-]{2,16}$'::text))
);


--
-- Name: TABLE study_participants; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.study_participants IS 'Flags study accounts with a pseudonymous code. Link to the account is cut on account deletion (OQ-017).';


--
-- Name: study_session_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study_session_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    study_participant_id uuid NOT NULL,
    interface_locale text NOT NULL,
    request_submitted_at timestamp with time zone NOT NULL,
    first_proposal_displayed_at timestamp with time zone,
    save_outcome text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_study_session_logs_interface_locale CHECK ((interface_locale = ANY (ARRAY['vi'::text, 'en'::text]))),
    CONSTRAINT ck_study_session_logs_order CHECK (((first_proposal_displayed_at IS NULL) OR (first_proposal_displayed_at >= request_submitted_at))),
    CONSTRAINT ck_study_session_logs_save_outcome CHECK ((save_outcome = ANY (ARRAY['SAVED'::text, 'NOT_SAVED'::text, 'SAVE_REFUSED'::text])))
);


--
-- Name: TABLE study_session_logs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.study_session_logs IS 'FR-077 five fields only; no request or question text. Deleted by 2027-06-30 (NFR-018).';


--
-- Name: trip_days; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trip_days (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    trip_id uuid NOT NULL,
    day_index smallint NOT NULL,
    day_window_start time without time zone NOT NULL,
    day_window_end time without time zone NOT NULL,
    CONSTRAINT ck_trip_days_day_index CHECK (((day_index >= 1) AND (day_index <= 3))),
    CONSTRAINT ck_trip_days_window CHECK ((day_window_start < day_window_end))
);


--
-- Name: trip_stops; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trip_stops (
    id uuid NOT NULL,
    trip_id uuid NOT NULL,
    trip_day_id uuid NOT NULL,
    city_id uuid NOT NULL,
    trust_level text DEFAULT 'VERIFIED'::text NOT NULL,
    place_id uuid,
    catalog_publication_id uuid,
    web_place_candidate_id uuid,
    ordinal smallint NOT NULL,
    planned_arrival time without time zone NOT NULL,
    planned_departure time without time zone NOT NULL,
    visit_minutes smallint NOT NULL,
    is_locked boolean DEFAULT false NOT NULL,
    CONSTRAINT ck_trip_stops_ordinal CHECK ((ordinal > 0)),
    CONSTRAINT ck_trip_stops_shape CHECK ((((trust_level = 'VERIFIED'::text) AND (place_id IS NOT NULL) AND (catalog_publication_id IS NOT NULL) AND (web_place_candidate_id IS NULL)) OR ((trust_level = 'WEB_UNVERIFIED'::text) AND (web_place_candidate_id IS NOT NULL) AND (place_id IS NULL) AND (catalog_publication_id IS NULL)))),
    CONSTRAINT ck_trip_stops_times CHECK ((planned_arrival < planned_departure)),
    CONSTRAINT ck_trip_stops_trust_level CHECK ((trust_level = ANY (ARRAY['VERIFIED'::text, 'WEB_UNVERIFIED'::text]))),
    CONSTRAINT ck_trip_stops_visit_minutes CHECK (((visit_minutes >= 1) AND (visit_minutes <= 600)))
);


--
-- Name: TABLE trip_stops; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.trip_stops IS 'Saved stops with stable IDs from the preview; composite FKs enforce same-city membership (BR-006) and the catalog revision used. trust_level (DEC-015): VERIFIED pins a publication; WEB_UNVERIFIED references a web_place_candidates row and is shown with its source URL and fetched date. The stored level never changes; vw_trip_stop_trust derives the effective level.';


--
-- Name: COLUMN trip_stops.trust_level; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trip_stops.trust_level IS 'VERIFIED or WEB_UNVERIFIED (canonical TrustLevel values, shared with the API).';


--
-- Name: trips; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trips (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    account_id uuid NOT NULL,
    city_id uuid NOT NULL,
    title text,
    start_date date,
    day_count smallint NOT NULL,
    status text DEFAULT 'DRAFT'::text NOT NULL,
    revision integer DEFAULT 0 NOT NULL,
    planning_preferences jsonb DEFAULT '{}'::jsonb NOT NULL,
    saved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_trips_day_count CHECK (((day_count >= 1) AND (day_count <= 3))),
    CONSTRAINT ck_trips_planning_preferences_object CHECK ((jsonb_typeof(planning_preferences) = 'object'::text)),
    CONSTRAINT ck_trips_revision CHECK ((revision >= 0)),
    CONSTRAINT ck_trips_saved_revision CHECK (((status = 'SAVED'::text) = ((revision > 0) AND (saved_at IS NOT NULL)))),
    CONSTRAINT ck_trips_status CHECK ((status = ANY (ARRAY['DRAFT'::text, 'SAVED'::text]))),
    CONSTRAINT ck_trips_title_length CHECK (((title IS NULL) OR (length(title) <= 120)))
);


--
-- Name: TABLE trips; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.trips IS 'Trip header; revision = accepted (saved) version, advanced only by explicit Save (BR-011, FR-040..FR-042). One enabled city, 1-3 days (BRU-007 rev. 1).';


--
-- Name: vw_guide_chunks; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_guide_chunks AS
 SELECT kc.id AS knowledge_chunk_id,
    kc.place_id,
    cp.city_id,
    kc.locale,
    kc.section,
    kc.corpus_revision,
    kc.content,
    kc.embedding,
    kc.embedding_model
   FROM (public.knowledge_chunks kc
     JOIN public.catalog_publications cp ON (((cp.place_id = kc.place_id) AND (cp.state = 'PUBLISHED'::text) AND (cp.corpus_revision = kc.corpus_revision))))
  WHERE (kc.review_state = 'APPROVED'::text);


--
-- Name: vw_published_place_facts; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_published_place_facts AS
 SELECT cp.place_id,
    cp.id AS catalog_publication_id,
    f.id AS place_fact_id,
    f.field_code,
    ff.is_operational,
    f.knowledge_state,
    f.value,
    f.verified_at,
    f.valid_until,
    (ff.is_operational AND ((f.verified_at < (now() - make_interval(days => (ff.stale_after_days)::integer))) OR ((f.valid_until IS NOT NULL) AND (f.valid_until < CURRENT_DATE)))) AS is_stale,
    ( SELECT jsonb_agg(jsonb_build_object('source_revision_id', sr.id, 'publisher', s.publisher, 'locator', sr.locator, 'retrieved_at', sr.retrieved_at, 'license_code', s.license_code, 'attribution_text', s.attribution_text) ORDER BY sr.retrieved_at DESC) AS jsonb_agg
           FROM ((public.fact_evidence e
             JOIN public.source_revisions sr ON ((sr.id = e.source_revision_id)))
             JOIN public.sources s ON ((s.id = sr.source_id)))
          WHERE (e.place_fact_id = f.id)) AS sources
   FROM (((public.catalog_publications cp
     JOIN public.publication_facts pf ON ((pf.catalog_publication_id = cp.id)))
     JOIN public.place_facts f ON ((f.id = pf.place_fact_id)))
     JOIN public.fact_fields ff ON ((ff.code = f.field_code)))
  WHERE (cp.state = 'PUBLISHED'::text);


--
-- Name: vw_published_places; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_published_places AS
 SELECT cp.id AS catalog_publication_id,
    cp.place_id,
    cp.city_id,
    cp.publication_revision,
    cp.category_code,
    lv.name AS name_vi,
    le.name AS name_en,
    lv.short_description AS short_description_vi,
    le.short_description AS short_description_en,
    lv.description AS description_vi,
    le.description AS description_en,
    cp.location,
    cp.entrance_location,
    cp.visit_minutes_min,
    cp.visit_minutes_suggested,
    cp.visit_minutes_max,
    cp.corpus_revision,
    cp.published_at
   FROM ((public.catalog_publications cp
     JOIN public.place_localizations lv ON ((lv.id = cp.localization_vi_id)))
     JOIN public.place_localizations le ON ((le.id = cp.localization_en_id)))
  WHERE (cp.state = 'PUBLISHED'::text);


--
-- Name: web_place_candidates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.web_place_candidates (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    city_id uuid NOT NULL,
    name text NOT NULL,
    name_vi text,
    name_en text,
    category_guess text,
    location public.geography(Point,4326),
    coordinate_source text,
    google_place_id text,
    places_check_outcome text DEFAULT 'SKIPPED'::text NOT NULL,
    places_checked_at timestamp with time zone,
    source_revision_id uuid NOT NULL,
    fetched_at timestamp with time zone NOT NULL,
    tavily_query text,
    extraction jsonb DEFAULT '{}'::jsonb NOT NULL,
    extraction_model text,
    review_state text DEFAULT 'PENDING'::text NOT NULL,
    promoted_place_id uuid,
    reviewed_by_account_id uuid,
    reviewed_at timestamp with time zone,
    review_note text,
    times_proposed integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_web_place_candidates_coordinate_source CHECK (((coordinate_source IS NULL) OR (coordinate_source = ANY (ARRAY['WEB_PAGE'::text, 'TAVILY'::text, 'OSM_NOMINATIM'::text, 'CURATOR'::text])))),
    CONSTRAINT ck_web_place_candidates_extraction_object CHECK ((jsonb_typeof(extraction) = 'object'::text)),
    CONSTRAINT ck_web_place_candidates_location_source CHECK (((location IS NULL) = (coordinate_source IS NULL))),
    CONSTRAINT ck_web_place_candidates_name_length CHECK (((length(name) >= 1) AND (length(name) <= 200))),
    CONSTRAINT ck_web_place_candidates_places_check_identity CHECK (((places_check_outcome = ANY (ARRAY['SKIPPED'::text, 'NOT_FOUND'::text])) OR (google_place_id IS NOT NULL))),
    CONSTRAINT ck_web_place_candidates_places_check_outcome CHECK ((places_check_outcome = ANY (ARRAY['EXISTS_OPERATIONAL'::text, 'EXISTS_CLOSED'::text, 'NOT_FOUND'::text, 'OUTSIDE_CITY'::text, 'SKIPPED'::text]))),
    CONSTRAINT ck_web_place_candidates_places_checked CHECK (((places_check_outcome = 'SKIPPED'::text) = (places_checked_at IS NULL))),
    CONSTRAINT ck_web_place_candidates_promoted CHECK (((review_state = 'PROMOTED'::text) = (promoted_place_id IS NOT NULL))),
    CONSTRAINT ck_web_place_candidates_review_state CHECK ((review_state = ANY (ARRAY['PENDING'::text, 'PROMOTED'::text, 'REJECTED'::text, 'EXPIRED'::text]))),
    CONSTRAINT ck_web_place_candidates_reviewed CHECK (((review_state = ANY (ARRAY['PENDING'::text, 'EXPIRED'::text])) OR (reviewed_at IS NOT NULL))),
    CONSTRAINT ck_web_place_candidates_times_proposed CHECK ((times_proposed >= 1))
);


--
-- Name: TABLE web_place_candidates; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.web_place_candidates IS 'Curator queue of places found by the research agent (DEC-015, FR-101). Every row is WEB_UNVERIFIED until a curator promotes it: promotion creates a places row (IMPORTED), an external_place_identities row and a localization draft, then the ordinary publication gate applies. The EXPIRED sweep skips rows referenced by trip_stops.';


--
-- Name: COLUMN web_place_candidates.coordinate_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.web_place_candidates.coordinate_source IS 'Where location came from: WEB_PAGE, TAVILY, OSM_NOMINATIM or CURATOR. Google coordinates are never stored canonically (ADR-006; ephemeral copy only in places_lookup_cache).';


--
-- Name: COLUMN web_place_candidates.places_check_outcome; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.web_place_candidates.places_check_outcome IS 'Gonarra verdict from the Google Places existence/status check (FR-100), not the raw Google string: EXISTS_OPERATIONAL, EXISTS_CLOSED, NOT_FOUND, OUTSIDE_CITY (outside cities.boundary) or SKIPPED (quota or check disabled).';


--
-- Name: COLUMN web_place_candidates.extraction; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.web_place_candidates.extraction IS 'Validated structured output of the extraction model (Pydantic-checked JSON object): hours/price/address claims as text with the supporting quote. Never copied into place_facts without curator review.';


--
-- Name: vw_trip_stop_trust; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_trip_stop_trust AS
 SELECT ts.id AS trip_stop_id,
    ts.trip_id,
    ts.trip_day_id,
    ts.city_id,
    ts.trust_level AS stored_trust_level,
        CASE
            WHEN (ts.trust_level = 'VERIFIED'::text) THEN 'VERIFIED'::text
            WHEN ((wpc.review_state = 'PROMOTED'::text) AND (cp.id IS NOT NULL)) THEN 'VERIFIED'::text
            ELSE 'WEB_UNVERIFIED'::text
        END AS effective_trust_level,
    COALESCE(ts.place_id,
        CASE
            WHEN (cp.id IS NOT NULL) THEN wpc.promoted_place_id
            ELSE NULL::uuid
        END) AS effective_place_id,
    COALESCE(ts.catalog_publication_id, cp.id) AS effective_catalog_publication_id,
    ts.web_place_candidate_id,
    wpc.review_state AS candidate_review_state,
    wpc.places_check_outcome,
    sr.locator AS source_url,
    wpc.fetched_at
   FROM (((public.trip_stops ts
     LEFT JOIN public.web_place_candidates wpc ON ((wpc.id = ts.web_place_candidate_id)))
     LEFT JOIN public.catalog_publications cp ON (((cp.place_id = wpc.promoted_place_id) AND (cp.state = 'PUBLISHED'::text))))
     LEFT JOIN public.source_revisions sr ON ((sr.id = wpc.source_revision_id)));


--
-- Name: VIEW vw_trip_stop_trust; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.vw_trip_stop_trust IS 'Per saved stop: stored and effective trust_level, resolved place/publication, candidate state, source URL and fetched_at (DEC-015, FR-098).';


--
-- Name: accounts accounts_clerk_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_clerk_user_id_key UNIQUE (clerk_user_id);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- Name: account_deletion_jobs pk_account_deletion_jobs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_deletion_jobs
    ADD CONSTRAINT pk_account_deletion_jobs PRIMARY KEY (id);


--
-- Name: account_preferences pk_account_preferences; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_preferences
    ADD CONSTRAINT pk_account_preferences PRIMARY KEY (account_id);


--
-- Name: ai_invocations pk_ai_invocations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_invocations
    ADD CONSTRAINT pk_ai_invocations PRIMARY KEY (id);


--
-- Name: ai_quota_ledger pk_ai_quota_ledger; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_quota_ledger
    ADD CONSTRAINT pk_ai_quota_ledger PRIMARY KEY (id);


--
-- Name: areas pk_areas; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT pk_areas PRIMARY KEY (code);


--
-- Name: catalog_audit_events pk_catalog_audit_events; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_audit_events
    ADD CONSTRAINT pk_catalog_audit_events PRIMARY KEY (id);


--
-- Name: catalog_publications pk_catalog_publications; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_publications
    ADD CONSTRAINT pk_catalog_publications PRIMARY KEY (id);


--
-- Name: categories pk_categories; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT pk_categories PRIMARY KEY (code);


--
-- Name: cities pk_cities; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT pk_cities PRIMARY KEY (id);


--
-- Name: data_providers pk_data_providers; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_providers
    ADD CONSTRAINT pk_data_providers PRIMARY KEY (id);


--
-- Name: external_place_identities pk_external_place_identities; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_place_identities
    ADD CONSTRAINT pk_external_place_identities PRIMARY KEY (id);


--
-- Name: fact_evidence pk_fact_evidence; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_evidence
    ADD CONSTRAINT pk_fact_evidence PRIMARY KEY (place_fact_id, source_revision_id);


--
-- Name: fact_fields pk_fact_fields; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_fields
    ADD CONSTRAINT pk_fact_fields PRIMARY KEY (code);


--
-- Name: guide_message_citations pk_guide_message_citations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_message_citations
    ADD CONSTRAINT pk_guide_message_citations PRIMARY KEY (guide_message_id, source_revision_id);


--
-- Name: guide_messages pk_guide_messages; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_messages
    ADD CONSTRAINT pk_guide_messages PRIMARY KEY (id);


--
-- Name: guide_sessions pk_guide_sessions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_sessions
    ADD CONSTRAINT pk_guide_sessions PRIMARY KEY (id);


--
-- Name: idempotency_records pk_idempotency_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idempotency_records
    ADD CONSTRAINT pk_idempotency_records PRIMARY KEY (account_id, operation, idempotency_key);


--
-- Name: import_records pk_import_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_records
    ADD CONSTRAINT pk_import_records PRIMARY KEY (id);


--
-- Name: import_runs pk_import_runs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_runs
    ADD CONSTRAINT pk_import_runs PRIMARY KEY (id);


--
-- Name: knowledge_chunk_sources pk_knowledge_chunk_sources; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_chunk_sources
    ADD CONSTRAINT pk_knowledge_chunk_sources PRIMARY KEY (knowledge_chunk_id, source_revision_id);


--
-- Name: knowledge_chunks pk_knowledge_chunks; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_chunks
    ADD CONSTRAINT pk_knowledge_chunks PRIMARY KEY (id);


--
-- Name: media_assets pk_media_assets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.media_assets
    ADD CONSTRAINT pk_media_assets PRIMARY KEY (id);


--
-- Name: place_aliases pk_place_aliases; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_aliases
    ADD CONSTRAINT pk_place_aliases PRIMARY KEY (id);


--
-- Name: place_closure_rules pk_place_closure_rules; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_closure_rules
    ADD CONSTRAINT pk_place_closure_rules PRIMARY KEY (id);


--
-- Name: place_facts pk_place_facts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_facts
    ADD CONSTRAINT pk_place_facts PRIMARY KEY (id);


--
-- Name: place_localizations pk_place_localizations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_localizations
    ADD CONSTRAINT pk_place_localizations PRIMARY KEY (id);


--
-- Name: place_media pk_place_media; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_media
    ADD CONSTRAINT pk_place_media PRIMARY KEY (place_id, media_asset_id);


--
-- Name: places pk_places; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places
    ADD CONSTRAINT pk_places PRIMARY KEY (id);


--
-- Name: places_lookup_cache pk_places_lookup_cache; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places_lookup_cache
    ADD CONSTRAINT pk_places_lookup_cache PRIMARY KEY (id);


--
-- Name: plan_previews pk_plan_previews; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_previews
    ADD CONSTRAINT pk_plan_previews PRIMARY KEY (id);


--
-- Name: preview_revisions pk_preview_revisions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preview_revisions
    ADD CONSTRAINT pk_preview_revisions PRIMARY KEY (plan_preview_id, preview_revision);


--
-- Name: provider_field_rules pk_provider_field_rules; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_field_rules
    ADD CONSTRAINT pk_provider_field_rules PRIMARY KEY (provider_policy_id, field_name);


--
-- Name: provider_policies pk_provider_policies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_policies
    ADD CONSTRAINT pk_provider_policies PRIMARY KEY (id);


--
-- Name: publication_facts pk_publication_facts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_facts
    ADD CONSTRAINT pk_publication_facts PRIMARY KEY (catalog_publication_id, place_fact_id);


--
-- Name: publication_media pk_publication_media; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_media
    ADD CONSTRAINT pk_publication_media PRIMARY KEY (catalog_publication_id, media_asset_id);


--
-- Name: query_embedding_cache pk_query_embedding_cache; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_embedding_cache
    ADD CONSTRAINT pk_query_embedding_cache PRIMARY KEY (text_sha256, locale, embedding_model);


--
-- Name: research_cache pk_research_cache; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.research_cache
    ADD CONSTRAINT pk_research_cache PRIMARY KEY (provider, key_sha256);


--
-- Name: route_legs pk_route_legs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_legs
    ADD CONSTRAINT pk_route_legs PRIMARY KEY (id);


--
-- Name: routes_matrix_cache pk_routes_matrix_cache; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routes_matrix_cache
    ADD CONSTRAINT pk_routes_matrix_cache PRIMARY KEY (origin_key, destination_key, travel_mode);


--
-- Name: source_revisions pk_source_revisions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_revisions
    ADD CONSTRAINT pk_source_revisions PRIMARY KEY (id);


--
-- Name: sources pk_sources; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sources
    ADD CONSTRAINT pk_sources PRIMARY KEY (id);


--
-- Name: study_participants pk_study_participants; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_participants
    ADD CONSTRAINT pk_study_participants PRIMARY KEY (id);


--
-- Name: study_session_logs pk_study_session_logs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_session_logs
    ADD CONSTRAINT pk_study_session_logs PRIMARY KEY (id);


--
-- Name: trip_days pk_trip_days; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_days
    ADD CONSTRAINT pk_trip_days PRIMARY KEY (id);


--
-- Name: trip_stops pk_trip_stops; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_stops
    ADD CONSTRAINT pk_trip_stops PRIMARY KEY (id);


--
-- Name: trips pk_trips; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT pk_trips PRIMARY KEY (id);


--
-- Name: web_place_candidates pk_web_place_candidates; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_place_candidates
    ADD CONSTRAINT pk_web_place_candidates PRIMARY KEY (id);


--
-- Name: ai_quota_ledger uq_ai_quota_ledger_scope_account_id_bucket_period_start; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_quota_ledger
    ADD CONSTRAINT uq_ai_quota_ledger_scope_account_id_bucket_period_start UNIQUE NULLS NOT DISTINCT (scope, account_id, bucket, period_start);


--
-- Name: areas uq_areas_code_city_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT uq_areas_code_city_id UNIQUE (code, city_id);


--
-- Name: catalog_publications uq_catalog_publications_id_place_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_publications
    ADD CONSTRAINT uq_catalog_publications_id_place_id UNIQUE (id, place_id);


--
-- Name: catalog_publications uq_catalog_publications_place_id_publication_revision; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_publications
    ADD CONSTRAINT uq_catalog_publications_place_id_publication_revision UNIQUE (place_id, publication_revision);


--
-- Name: cities uq_cities_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT uq_cities_code UNIQUE (code);


--
-- Name: data_providers uq_data_providers_provider_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_providers
    ADD CONSTRAINT uq_data_providers_provider_key UNIQUE (provider_key);


--
-- Name: external_place_identities uq_external_place_identities_data_provider_id_upstream_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_place_identities
    ADD CONSTRAINT uq_external_place_identities_data_provider_id_upstream_id UNIQUE (data_provider_id, upstream_id);


--
-- Name: guide_messages uq_guide_messages_guide_session_id_seq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_messages
    ADD CONSTRAINT uq_guide_messages_guide_session_id_seq UNIQUE (guide_session_id, seq);


--
-- Name: import_records uq_import_records_import_run_id_upstream_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_records
    ADD CONSTRAINT uq_import_records_import_run_id_upstream_id UNIQUE (import_run_id, upstream_id);


--
-- Name: knowledge_chunks uq_knowledge_chunks_city_id_place_id_locale_corpus_revision_chu; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_chunks
    ADD CONSTRAINT uq_knowledge_chunks_city_id_place_id_locale_corpus_revision_chu UNIQUE NULLS NOT DISTINCT (city_id, place_id, locale, corpus_revision, chunk_index);


--
-- Name: knowledge_chunks uq_knowledge_chunks_city_id_place_id_locale_corpus_revision_sec; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_chunks
    ADD CONSTRAINT uq_knowledge_chunks_city_id_place_id_locale_corpus_revision_sec UNIQUE NULLS NOT DISTINCT (city_id, place_id, locale, corpus_revision, section);


--
-- Name: media_assets uq_media_assets_object_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.media_assets
    ADD CONSTRAINT uq_media_assets_object_key UNIQUE (object_key);


--
-- Name: media_assets uq_media_assets_sha256; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.media_assets
    ADD CONSTRAINT uq_media_assets_sha256 UNIQUE (sha256);


--
-- Name: place_aliases uq_place_aliases_place_id_locale_alias_normalized; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_aliases
    ADD CONSTRAINT uq_place_aliases_place_id_locale_alias_normalized UNIQUE (place_id, locale, alias_normalized);


--
-- Name: place_facts uq_place_facts_place_id_field_code_fact_revision; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_facts
    ADD CONSTRAINT uq_place_facts_place_id_field_code_fact_revision UNIQUE (place_id, field_code, fact_revision);


--
-- Name: place_localizations uq_place_localizations_place_id_locale_localization_revision; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_localizations
    ADD CONSTRAINT uq_place_localizations_place_id_locale_localization_revision UNIQUE (place_id, locale, localization_revision);


--
-- Name: place_media uq_place_media_place_id_ordinal; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_media
    ADD CONSTRAINT uq_place_media_place_id_ordinal UNIQUE (place_id, ordinal);


--
-- Name: places uq_places_city_id_slug; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places
    ADD CONSTRAINT uq_places_city_id_slug UNIQUE (city_id, slug);


--
-- Name: places uq_places_id_city_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places
    ADD CONSTRAINT uq_places_id_city_id UNIQUE (id, city_id);


--
-- Name: places_lookup_cache uq_places_lookup_cache_google_place_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places_lookup_cache
    ADD CONSTRAINT uq_places_lookup_cache_google_place_id UNIQUE (google_place_id);


--
-- Name: places_lookup_cache uq_places_lookup_cache_query_sha256; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places_lookup_cache
    ADD CONSTRAINT uq_places_lookup_cache_query_sha256 UNIQUE (query_sha256);


--
-- Name: provider_policies uq_provider_policies_data_provider_id_policy_revision; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_policies
    ADD CONSTRAINT uq_provider_policies_data_provider_id_policy_revision UNIQUE (data_provider_id, policy_revision);


--
-- Name: route_legs uq_route_legs_from_stop_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_legs
    ADD CONSTRAINT uq_route_legs_from_stop_id UNIQUE (from_stop_id);


--
-- Name: route_legs uq_route_legs_to_stop_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_legs
    ADD CONSTRAINT uq_route_legs_to_stop_id UNIQUE (to_stop_id);


--
-- Name: source_revisions uq_source_revisions_source_id_locator_retrieved_at; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_revisions
    ADD CONSTRAINT uq_source_revisions_source_id_locator_retrieved_at UNIQUE (source_id, locator, retrieved_at);


--
-- Name: study_participants uq_study_participants_account_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_participants
    ADD CONSTRAINT uq_study_participants_account_id UNIQUE (account_id);


--
-- Name: study_participants uq_study_participants_participant_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_participants
    ADD CONSTRAINT uq_study_participants_participant_code UNIQUE (participant_code);


--
-- Name: trip_days uq_trip_days_id_trip_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_days
    ADD CONSTRAINT uq_trip_days_id_trip_id UNIQUE (id, trip_id);


--
-- Name: trip_days uq_trip_days_trip_id_day_index; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_days
    ADD CONSTRAINT uq_trip_days_trip_id_day_index UNIQUE (trip_id, day_index);


--
-- Name: trip_stops uq_trip_stops_id_trip_day_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_stops
    ADD CONSTRAINT uq_trip_stops_id_trip_day_id UNIQUE (id, trip_day_id);


--
-- Name: trip_stops uq_trip_stops_trip_day_id_ordinal; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_stops
    ADD CONSTRAINT uq_trip_stops_trip_day_id_ordinal UNIQUE (trip_day_id, ordinal) DEFERRABLE;


--
-- Name: trip_stops uq_trip_stops_trip_id_place_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_stops
    ADD CONSTRAINT uq_trip_stops_trip_id_place_id UNIQUE (trip_id, place_id);


--
-- Name: trips uq_trips_id_account_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT uq_trips_id_account_id UNIQUE (id, account_id);


--
-- Name: trips uq_trips_id_city_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT uq_trips_id_city_id UNIQUE (id, city_id);


--
-- Name: web_place_candidates uq_web_place_candidates_id_city_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_place_candidates
    ADD CONSTRAINT uq_web_place_candidates_id_city_id UNIQUE (id, city_id);


--
-- Name: ix_account_deletion_jobs_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_account_deletion_jobs_account_id ON public.account_deletion_jobs USING btree (account_id);


--
-- Name: ix_account_deletion_jobs_clerk_subject_sha256_completed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_account_deletion_jobs_clerk_subject_sha256_completed ON public.account_deletion_jobs USING btree (clerk_subject_sha256) WHERE (status = 'COMPLETED'::text);


--
-- Name: ix_account_deletion_jobs_status_requested_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_account_deletion_jobs_status_requested_at ON public.account_deletion_jobs USING btree (status, requested_at);


--
-- Name: ix_ai_invocations_account_id_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_invocations_account_id_created_at ON public.ai_invocations USING btree (account_id, created_at);


--
-- Name: ix_ai_invocations_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_invocations_created_at ON public.ai_invocations USING btree (created_at);


--
-- Name: ix_ai_quota_ledger_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_quota_ledger_account_id ON public.ai_quota_ledger USING btree (account_id);


--
-- Name: ix_ai_quota_ledger_period_start; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_quota_ledger_period_start ON public.ai_quota_ledger USING btree (period_start);


--
-- Name: ix_areas_city_id_sort_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_areas_city_id_sort_order ON public.areas USING btree (city_id, sort_order);


--
-- Name: ix_catalog_audit_events_actor_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_catalog_audit_events_actor_account_id ON public.catalog_audit_events USING btree (actor_account_id);


--
-- Name: ix_catalog_audit_events_entity_table_entity_id_occurred_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_catalog_audit_events_entity_table_entity_id_occurred_at ON public.catalog_audit_events USING btree (entity_table, entity_id, occurred_at);


--
-- Name: ix_catalog_publications_category_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_catalog_publications_category_code ON public.catalog_publications USING btree (category_code);


--
-- Name: ix_catalog_publications_city_id_area_code_published; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_catalog_publications_city_id_area_code_published ON public.catalog_publications USING btree (city_id, area_code) WHERE (state = 'PUBLISHED'::text);


--
-- Name: ix_catalog_publications_city_id_category_code_published; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_catalog_publications_city_id_category_code_published ON public.catalog_publications USING btree (city_id, category_code) WHERE (state = 'PUBLISHED'::text);


--
-- Name: ix_catalog_publications_localization_en_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_catalog_publications_localization_en_id ON public.catalog_publications USING btree (localization_en_id);


--
-- Name: ix_catalog_publications_localization_vi_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_catalog_publications_localization_vi_id ON public.catalog_publications USING btree (localization_vi_id);


--
-- Name: ix_catalog_publications_location_gist_published; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_catalog_publications_location_gist_published ON public.catalog_publications USING gist (location) WHERE (state = 'PUBLISHED'::text);


--
-- Name: ix_catalog_publications_published_by_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_catalog_publications_published_by_account_id ON public.catalog_publications USING btree (published_by_account_id);


--
-- Name: ix_external_place_identities_place_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_external_place_identities_place_id ON public.external_place_identities USING btree (place_id);


--
-- Name: ix_fact_evidence_source_revision_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fact_evidence_source_revision_id ON public.fact_evidence USING btree (source_revision_id);


--
-- Name: ix_guide_message_citations_knowledge_chunk_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_guide_message_citations_knowledge_chunk_id ON public.guide_message_citations USING btree (knowledge_chunk_id);


--
-- Name: ix_guide_message_citations_place_fact_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_guide_message_citations_place_fact_id ON public.guide_message_citations USING btree (place_fact_id);


--
-- Name: ix_guide_message_citations_source_revision_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_guide_message_citations_source_revision_id ON public.guide_message_citations USING btree (source_revision_id);


--
-- Name: ix_guide_sessions_account_id_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_guide_sessions_account_id_created_at ON public.guide_sessions USING btree (account_id, created_at DESC);


--
-- Name: ix_guide_sessions_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_guide_sessions_expires_at ON public.guide_sessions USING btree (expires_at);


--
-- Name: ix_guide_sessions_place_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_guide_sessions_place_id ON public.guide_sessions USING btree (place_id);


--
-- Name: ix_guide_sessions_trip_id_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_guide_sessions_trip_id_account_id ON public.guide_sessions USING btree (trip_id, account_id);


--
-- Name: ix_idempotency_records_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_idempotency_records_expires_at ON public.idempotency_records USING btree (expires_at);


--
-- Name: ix_import_records_location_gist; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_records_location_gist ON public.import_records USING gist (location);


--
-- Name: ix_import_records_place_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_records_place_id ON public.import_records USING btree (place_id);


--
-- Name: ix_import_runs_city_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_runs_city_id ON public.import_runs USING btree (city_id);


--
-- Name: ix_import_runs_provider_policy_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_runs_provider_policy_id ON public.import_runs USING btree (provider_policy_id);


--
-- Name: ix_knowledge_chunk_sources_source_revision_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_knowledge_chunk_sources_source_revision_id ON public.knowledge_chunk_sources USING btree (source_revision_id);


--
-- Name: ix_knowledge_chunks_city_id_scope_locale_approved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_knowledge_chunks_city_id_scope_locale_approved ON public.knowledge_chunks USING btree (city_id, scope, locale) WHERE (review_state = 'APPROVED'::text);


--
-- Name: ix_knowledge_chunks_content_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_knowledge_chunks_content_trgm ON public.knowledge_chunks USING gin (lower(content) public.gin_trgm_ops) WHERE (review_state = 'APPROVED'::text);


--
-- Name: ix_knowledge_chunks_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_knowledge_chunks_embedding_hnsw ON public.knowledge_chunks USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64') WHERE (review_state = 'APPROVED'::text);


--
-- Name: ix_media_assets_source_revision_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_media_assets_source_revision_id ON public.media_assets USING btree (source_revision_id);


--
-- Name: ix_place_aliases_alias_normalized_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_place_aliases_alias_normalized_trgm ON public.place_aliases USING gin (alias_normalized public.gin_trgm_ops);


--
-- Name: ix_place_closure_rules_area_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_place_closure_rules_area_code ON public.place_closure_rules USING btree (area_code);


--
-- Name: ix_place_closure_rules_city_id_review_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_place_closure_rules_city_id_review_state ON public.place_closure_rules USING btree (city_id, review_state);


--
-- Name: ix_place_closure_rules_place_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_place_closure_rules_place_id ON public.place_closure_rules USING btree (place_id);


--
-- Name: ix_place_closure_rules_reviewed_by_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_place_closure_rules_reviewed_by_account_id ON public.place_closure_rules USING btree (reviewed_by_account_id);


--
-- Name: ix_place_closure_rules_source_revision_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_place_closure_rules_source_revision_id ON public.place_closure_rules USING btree (source_revision_id);


--
-- Name: ix_place_facts_field_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_place_facts_field_code ON public.place_facts USING btree (field_code);


--
-- Name: ix_place_media_media_asset_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_place_media_media_asset_id ON public.place_media USING btree (media_asset_id);


--
-- Name: ix_places_area_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_places_area_code ON public.places USING btree (area_code);


--
-- Name: ix_places_category_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_places_category_code ON public.places USING btree (category_code);


--
-- Name: ix_places_location_gist; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_places_location_gist ON public.places USING gist (location);


--
-- Name: ix_places_lookup_cache_location_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_places_lookup_cache_location_expires_at ON public.places_lookup_cache USING btree (location_expires_at) WHERE (location_expires_at IS NOT NULL);


--
-- Name: ix_places_lookup_cache_outcome_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_places_lookup_cache_outcome_expires_at ON public.places_lookup_cache USING btree (outcome_expires_at);


--
-- Name: ix_places_lookup_cache_provider_policy_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_places_lookup_cache_provider_policy_id ON public.places_lookup_cache USING btree (provider_policy_id);


--
-- Name: ix_plan_previews_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_plan_previews_account_id ON public.plan_previews USING btree (account_id);


--
-- Name: ix_plan_previews_expires_at_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_plan_previews_expires_at_active ON public.plan_previews USING btree (expires_at) WHERE (status = 'ACTIVE'::text);


--
-- Name: ix_plan_previews_trip_id_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_plan_previews_trip_id_account_id ON public.plan_previews USING btree (trip_id, account_id);


--
-- Name: ix_publication_facts_place_fact_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_publication_facts_place_fact_id ON public.publication_facts USING btree (place_fact_id);


--
-- Name: ix_publication_media_media_asset_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_publication_media_media_asset_id ON public.publication_media USING btree (media_asset_id);


--
-- Name: ix_query_embedding_cache_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_query_embedding_cache_expires_at ON public.query_embedding_cache USING btree (expires_at);


--
-- Name: ix_query_embedding_cache_provider_policy_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_query_embedding_cache_provider_policy_id ON public.query_embedding_cache USING btree (provider_policy_id);


--
-- Name: ix_research_cache_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_research_cache_expires_at ON public.research_cache USING btree (expires_at);


--
-- Name: ix_research_cache_provider_policy_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_research_cache_provider_policy_id ON public.research_cache USING btree (provider_policy_id);


--
-- Name: ix_research_cache_source_revision_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_research_cache_source_revision_id ON public.research_cache USING btree (source_revision_id);


--
-- Name: ix_route_legs_data_provider_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_route_legs_data_provider_id ON public.route_legs USING btree (data_provider_id);


--
-- Name: ix_route_legs_expires_at_available; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_route_legs_expires_at_available ON public.route_legs USING btree (expires_at) WHERE (availability = 'AVAILABLE'::text);


--
-- Name: ix_route_legs_trip_day_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_route_legs_trip_day_id ON public.route_legs USING btree (trip_day_id);


--
-- Name: ix_routes_matrix_cache_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_routes_matrix_cache_expires_at ON public.routes_matrix_cache USING btree (expires_at);


--
-- Name: ix_routes_matrix_cache_provider_policy_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_routes_matrix_cache_provider_policy_id ON public.routes_matrix_cache USING btree (provider_policy_id);


--
-- Name: ix_sources_data_provider_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sources_data_provider_id ON public.sources USING btree (data_provider_id);


--
-- Name: ix_study_session_logs_study_participant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_study_session_logs_study_participant_id ON public.study_session_logs USING btree (study_participant_id);


--
-- Name: ix_trip_stops_catalog_publication_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trip_stops_catalog_publication_id ON public.trip_stops USING btree (catalog_publication_id);


--
-- Name: ix_trip_stops_place_id_city_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trip_stops_place_id_city_id ON public.trip_stops USING btree (place_id, city_id);


--
-- Name: ix_trip_stops_web_place_candidate_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trip_stops_web_place_candidate_id ON public.trip_stops USING btree (web_place_candidate_id);


--
-- Name: ix_trips_account_id_updated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trips_account_id_updated_at ON public.trips USING btree (account_id, updated_at DESC);


--
-- Name: ix_trips_city_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trips_city_id ON public.trips USING btree (city_id);


--
-- Name: ix_web_place_candidates_city_id_review_state_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_web_place_candidates_city_id_review_state_created_at ON public.web_place_candidates USING btree (city_id, review_state, created_at DESC);


--
-- Name: ix_web_place_candidates_location_gist; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_web_place_candidates_location_gist ON public.web_place_candidates USING gist (location);


--
-- Name: ix_web_place_candidates_promoted_place_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_web_place_candidates_promoted_place_id ON public.web_place_candidates USING btree (promoted_place_id);


--
-- Name: ix_web_place_candidates_reviewed_by_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_web_place_candidates_reviewed_by_account_id ON public.web_place_candidates USING btree (reviewed_by_account_id);


--
-- Name: ix_web_place_candidates_source_revision_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_web_place_candidates_source_revision_id ON public.web_place_candidates USING btree (source_revision_id);


--
-- Name: uq_account_deletion_jobs_account_id_open; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_account_deletion_jobs_account_id_open ON public.account_deletion_jobs USING btree (account_id) WHERE (status = ANY (ARRAY['REQUESTED'::text, 'IN_PROGRESS'::text, 'FAILED'::text]));


--
-- Name: uq_catalog_publications_place_id_published; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_catalog_publications_place_id_published ON public.catalog_publications USING btree (place_id) WHERE (state = 'PUBLISHED'::text);


--
-- Name: uq_import_runs_succeeded_release; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_import_runs_succeeded_release ON public.import_runs USING btree (data_provider_id, city_id, release_id, checksum_sha256, importer_version) WHERE (status = 'SUCCEEDED'::text);


--
-- Name: uq_place_facts_place_id_field_code_approved; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_place_facts_place_id_field_code_approved ON public.place_facts USING btree (place_id, field_code) WHERE (review_state = 'APPROVED'::text);


--
-- Name: uq_place_localizations_place_id_locale_approved; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_place_localizations_place_id_locale_approved ON public.place_localizations USING btree (place_id, locale) WHERE (review_state = 'APPROVED'::text);


--
-- Name: uq_plan_previews_trip_id_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_plan_previews_trip_id_active ON public.plan_previews USING btree (trip_id) WHERE (status = 'ACTIVE'::text);


--
-- Name: uq_provider_policies_data_provider_id_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_provider_policies_data_provider_id_active ON public.provider_policies USING btree (data_provider_id) WHERE (status = 'ACTIVE'::text);


--
-- Name: uq_trip_stops_trip_id_web_place_candidate_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_trip_stops_trip_id_web_place_candidate_id ON public.trip_stops USING btree (trip_id, web_place_candidate_id) WHERE (web_place_candidate_id IS NOT NULL);


--
-- Name: uq_web_place_candidates_google_place_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_web_place_candidates_google_place_id ON public.web_place_candidates USING btree (google_place_id) WHERE (google_place_id IS NOT NULL);


--
-- Name: account_deletion_jobs trg_account_deletion_jobs_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_account_deletion_jobs_set_updated_at_before BEFORE UPDATE ON public.account_deletion_jobs FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: account_preferences trg_account_preferences_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_account_preferences_set_updated_at_before BEFORE UPDATE ON public.account_preferences FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: accounts trg_accounts_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_accounts_set_updated_at_before BEFORE UPDATE ON public.accounts FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: ai_quota_ledger trg_ai_quota_ledger_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_ai_quota_ledger_set_updated_at_before BEFORE UPDATE ON public.ai_quota_ledger FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: areas trg_areas_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_areas_set_updated_at_before BEFORE UPDATE ON public.areas FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: catalog_publications trg_catalog_publications_guard_update_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_catalog_publications_guard_update_before BEFORE UPDATE ON public.catalog_publications FOR EACH ROW EXECUTE FUNCTION public.fn_guard_catalog_publication_update();


--
-- Name: categories trg_categories_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_categories_set_updated_at_before BEFORE UPDATE ON public.categories FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: cities trg_cities_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_cities_set_updated_at_before BEFORE UPDATE ON public.cities FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: data_providers trg_data_providers_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_data_providers_set_updated_at_before BEFORE UPDATE ON public.data_providers FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: external_place_identities trg_external_place_identities_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_external_place_identities_set_updated_at_before BEFORE UPDATE ON public.external_place_identities FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: media_assets trg_media_assets_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_media_assets_set_updated_at_before BEFORE UPDATE ON public.media_assets FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: place_aliases trg_place_aliases_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_place_aliases_set_updated_at_before BEFORE UPDATE ON public.place_aliases FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: place_closure_rules trg_place_closure_rules_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_place_closure_rules_set_updated_at_before BEFORE UPDATE ON public.place_closure_rules FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: place_facts trg_place_facts_guard_update_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_place_facts_guard_update_before BEFORE UPDATE ON public.place_facts FOR EACH ROW EXECUTE FUNCTION public.fn_guard_place_fact_update();


--
-- Name: places trg_places_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_places_set_updated_at_before BEFORE UPDATE ON public.places FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: plan_previews trg_plan_previews_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_plan_previews_set_updated_at_before BEFORE UPDATE ON public.plan_previews FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: preview_revisions trg_preview_revisions_reject_update_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_preview_revisions_reject_update_before BEFORE UPDATE ON public.preview_revisions FOR EACH ROW EXECUTE FUNCTION public.fn_reject_update();


--
-- Name: source_revisions trg_source_revisions_reject_update_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_source_revisions_reject_update_before BEFORE UPDATE ON public.source_revisions FOR EACH ROW EXECUTE FUNCTION public.fn_reject_update();


--
-- Name: sources trg_sources_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_sources_set_updated_at_before BEFORE UPDATE ON public.sources FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: trip_days trg_trip_days_check_day_index_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_trip_days_check_day_index_before BEFORE INSERT OR UPDATE OF day_index, trip_id ON public.trip_days FOR EACH ROW EXECUTE FUNCTION public.fn_check_trip_day_index();


--
-- Name: trips trg_trips_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_trips_set_updated_at_before BEFORE UPDATE ON public.trips FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: web_place_candidates trg_web_place_candidates_set_updated_at_before; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_web_place_candidates_set_updated_at_before BEFORE UPDATE ON public.web_place_candidates FOR EACH ROW EXECUTE FUNCTION public.fn_set_updated_at();


--
-- Name: account_deletion_jobs fk_account_deletion_jobs_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_deletion_jobs
    ADD CONSTRAINT fk_account_deletion_jobs_account_id FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- Name: account_preferences fk_account_preferences_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_preferences
    ADD CONSTRAINT fk_account_preferences_account_id FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE CASCADE;


--
-- Name: ai_invocations fk_ai_invocations_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_invocations
    ADD CONSTRAINT fk_ai_invocations_account_id FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE CASCADE;


--
-- Name: ai_quota_ledger fk_ai_quota_ledger_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_quota_ledger
    ADD CONSTRAINT fk_ai_quota_ledger_account_id FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE CASCADE;


--
-- Name: areas fk_areas_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT fk_areas_city_id FOREIGN KEY (city_id) REFERENCES public.cities(id) ON DELETE RESTRICT;


--
-- Name: catalog_audit_events fk_catalog_audit_events_actor_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_audit_events
    ADD CONSTRAINT fk_catalog_audit_events_actor_account_id FOREIGN KEY (actor_account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- Name: catalog_publications fk_catalog_publications_area_code_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_publications
    ADD CONSTRAINT fk_catalog_publications_area_code_city_id FOREIGN KEY (area_code, city_id) REFERENCES public.areas(code, city_id) ON DELETE RESTRICT;


--
-- Name: catalog_publications fk_catalog_publications_category_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_publications
    ADD CONSTRAINT fk_catalog_publications_category_code FOREIGN KEY (category_code) REFERENCES public.categories(code) ON DELETE RESTRICT;


--
-- Name: catalog_publications fk_catalog_publications_localization_en_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_publications
    ADD CONSTRAINT fk_catalog_publications_localization_en_id FOREIGN KEY (localization_en_id) REFERENCES public.place_localizations(id) ON DELETE RESTRICT;


--
-- Name: catalog_publications fk_catalog_publications_localization_vi_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_publications
    ADD CONSTRAINT fk_catalog_publications_localization_vi_id FOREIGN KEY (localization_vi_id) REFERENCES public.place_localizations(id) ON DELETE RESTRICT;


--
-- Name: catalog_publications fk_catalog_publications_place_id_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_publications
    ADD CONSTRAINT fk_catalog_publications_place_id_city_id FOREIGN KEY (place_id, city_id) REFERENCES public.places(id, city_id) ON DELETE RESTRICT;


--
-- Name: catalog_publications fk_catalog_publications_published_by_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_publications
    ADD CONSTRAINT fk_catalog_publications_published_by_account_id FOREIGN KEY (published_by_account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- Name: external_place_identities fk_external_place_identities_data_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_place_identities
    ADD CONSTRAINT fk_external_place_identities_data_provider_id FOREIGN KEY (data_provider_id) REFERENCES public.data_providers(id) ON DELETE RESTRICT;


--
-- Name: external_place_identities fk_external_place_identities_place_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_place_identities
    ADD CONSTRAINT fk_external_place_identities_place_id FOREIGN KEY (place_id) REFERENCES public.places(id) ON DELETE CASCADE;


--
-- Name: fact_evidence fk_fact_evidence_place_fact_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_evidence
    ADD CONSTRAINT fk_fact_evidence_place_fact_id FOREIGN KEY (place_fact_id) REFERENCES public.place_facts(id) ON DELETE CASCADE;


--
-- Name: fact_evidence fk_fact_evidence_source_revision_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_evidence
    ADD CONSTRAINT fk_fact_evidence_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES public.source_revisions(id) ON DELETE RESTRICT;


--
-- Name: guide_message_citations fk_guide_message_citations_guide_message_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_message_citations
    ADD CONSTRAINT fk_guide_message_citations_guide_message_id FOREIGN KEY (guide_message_id) REFERENCES public.guide_messages(id) ON DELETE CASCADE;


--
-- Name: guide_message_citations fk_guide_message_citations_knowledge_chunk_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_message_citations
    ADD CONSTRAINT fk_guide_message_citations_knowledge_chunk_id FOREIGN KEY (knowledge_chunk_id) REFERENCES public.knowledge_chunks(id) ON DELETE SET NULL;


--
-- Name: guide_message_citations fk_guide_message_citations_place_fact_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_message_citations
    ADD CONSTRAINT fk_guide_message_citations_place_fact_id FOREIGN KEY (place_fact_id) REFERENCES public.place_facts(id) ON DELETE SET NULL;


--
-- Name: guide_message_citations fk_guide_message_citations_source_revision_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_message_citations
    ADD CONSTRAINT fk_guide_message_citations_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES public.source_revisions(id) ON DELETE RESTRICT;


--
-- Name: guide_messages fk_guide_messages_guide_session_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_messages
    ADD CONSTRAINT fk_guide_messages_guide_session_id FOREIGN KEY (guide_session_id) REFERENCES public.guide_sessions(id) ON DELETE CASCADE;


--
-- Name: guide_sessions fk_guide_sessions_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_sessions
    ADD CONSTRAINT fk_guide_sessions_account_id FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE CASCADE;


--
-- Name: guide_sessions fk_guide_sessions_place_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_sessions
    ADD CONSTRAINT fk_guide_sessions_place_id FOREIGN KEY (place_id) REFERENCES public.places(id) ON DELETE RESTRICT;


--
-- Name: guide_sessions fk_guide_sessions_trip_id_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.guide_sessions
    ADD CONSTRAINT fk_guide_sessions_trip_id_account_id FOREIGN KEY (trip_id, account_id) REFERENCES public.trips(id, account_id) ON DELETE CASCADE;


--
-- Name: idempotency_records fk_idempotency_records_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idempotency_records
    ADD CONSTRAINT fk_idempotency_records_account_id FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE CASCADE;


--
-- Name: import_records fk_import_records_import_run_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_records
    ADD CONSTRAINT fk_import_records_import_run_id FOREIGN KEY (import_run_id) REFERENCES public.import_runs(id) ON DELETE CASCADE;


--
-- Name: import_records fk_import_records_place_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_records
    ADD CONSTRAINT fk_import_records_place_id FOREIGN KEY (place_id) REFERENCES public.places(id) ON DELETE SET NULL;


--
-- Name: import_runs fk_import_runs_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_runs
    ADD CONSTRAINT fk_import_runs_city_id FOREIGN KEY (city_id) REFERENCES public.cities(id) ON DELETE RESTRICT;


--
-- Name: import_runs fk_import_runs_data_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_runs
    ADD CONSTRAINT fk_import_runs_data_provider_id FOREIGN KEY (data_provider_id) REFERENCES public.data_providers(id) ON DELETE RESTRICT;


--
-- Name: import_runs fk_import_runs_provider_policy_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_runs
    ADD CONSTRAINT fk_import_runs_provider_policy_id FOREIGN KEY (provider_policy_id) REFERENCES public.provider_policies(id) ON DELETE RESTRICT;


--
-- Name: knowledge_chunk_sources fk_knowledge_chunk_sources_knowledge_chunk_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_chunk_sources
    ADD CONSTRAINT fk_knowledge_chunk_sources_knowledge_chunk_id FOREIGN KEY (knowledge_chunk_id) REFERENCES public.knowledge_chunks(id) ON DELETE CASCADE;


--
-- Name: knowledge_chunk_sources fk_knowledge_chunk_sources_source_revision_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_chunk_sources
    ADD CONSTRAINT fk_knowledge_chunk_sources_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES public.source_revisions(id) ON DELETE RESTRICT;


--
-- Name: knowledge_chunks fk_knowledge_chunks_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_chunks
    ADD CONSTRAINT fk_knowledge_chunks_city_id FOREIGN KEY (city_id) REFERENCES public.cities(id) ON DELETE RESTRICT;


--
-- Name: knowledge_chunks fk_knowledge_chunks_place_id_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_chunks
    ADD CONSTRAINT fk_knowledge_chunks_place_id_city_id FOREIGN KEY (place_id, city_id) REFERENCES public.places(id, city_id) ON DELETE CASCADE;


--
-- Name: media_assets fk_media_assets_source_revision_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.media_assets
    ADD CONSTRAINT fk_media_assets_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES public.source_revisions(id) ON DELETE RESTRICT;


--
-- Name: place_aliases fk_place_aliases_place_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_aliases
    ADD CONSTRAINT fk_place_aliases_place_id FOREIGN KEY (place_id) REFERENCES public.places(id) ON DELETE CASCADE;


--
-- Name: place_closure_rules fk_place_closure_rules_area_code_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_closure_rules
    ADD CONSTRAINT fk_place_closure_rules_area_code_city_id FOREIGN KEY (area_code, city_id) REFERENCES public.areas(code, city_id) ON DELETE RESTRICT;


--
-- Name: place_closure_rules fk_place_closure_rules_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_closure_rules
    ADD CONSTRAINT fk_place_closure_rules_city_id FOREIGN KEY (city_id) REFERENCES public.cities(id) ON DELETE RESTRICT;


--
-- Name: place_closure_rules fk_place_closure_rules_place_id_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_closure_rules
    ADD CONSTRAINT fk_place_closure_rules_place_id_city_id FOREIGN KEY (place_id, city_id) REFERENCES public.places(id, city_id) ON DELETE CASCADE;


--
-- Name: place_closure_rules fk_place_closure_rules_reviewed_by_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_closure_rules
    ADD CONSTRAINT fk_place_closure_rules_reviewed_by_account_id FOREIGN KEY (reviewed_by_account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- Name: place_closure_rules fk_place_closure_rules_source_revision_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_closure_rules
    ADD CONSTRAINT fk_place_closure_rules_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES public.source_revisions(id) ON DELETE RESTRICT;


--
-- Name: place_facts fk_place_facts_field_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_facts
    ADD CONSTRAINT fk_place_facts_field_code FOREIGN KEY (field_code) REFERENCES public.fact_fields(code) ON DELETE RESTRICT;


--
-- Name: place_facts fk_place_facts_place_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_facts
    ADD CONSTRAINT fk_place_facts_place_id FOREIGN KEY (place_id) REFERENCES public.places(id) ON DELETE CASCADE;


--
-- Name: place_localizations fk_place_localizations_place_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_localizations
    ADD CONSTRAINT fk_place_localizations_place_id FOREIGN KEY (place_id) REFERENCES public.places(id) ON DELETE CASCADE;


--
-- Name: place_media fk_place_media_media_asset_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_media
    ADD CONSTRAINT fk_place_media_media_asset_id FOREIGN KEY (media_asset_id) REFERENCES public.media_assets(id) ON DELETE RESTRICT;


--
-- Name: place_media fk_place_media_place_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.place_media
    ADD CONSTRAINT fk_place_media_place_id FOREIGN KEY (place_id) REFERENCES public.places(id) ON DELETE CASCADE;


--
-- Name: places fk_places_area_code_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places
    ADD CONSTRAINT fk_places_area_code_city_id FOREIGN KEY (area_code, city_id) REFERENCES public.areas(code, city_id) ON DELETE RESTRICT;


--
-- Name: places fk_places_category_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places
    ADD CONSTRAINT fk_places_category_code FOREIGN KEY (category_code) REFERENCES public.categories(code) ON DELETE RESTRICT;


--
-- Name: places fk_places_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places
    ADD CONSTRAINT fk_places_city_id FOREIGN KEY (city_id) REFERENCES public.cities(id) ON DELETE RESTRICT;


--
-- Name: places_lookup_cache fk_places_lookup_cache_provider_policy_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places_lookup_cache
    ADD CONSTRAINT fk_places_lookup_cache_provider_policy_id FOREIGN KEY (provider_policy_id) REFERENCES public.provider_policies(id) ON DELETE RESTRICT;


--
-- Name: plan_previews fk_plan_previews_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_previews
    ADD CONSTRAINT fk_plan_previews_account_id FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE CASCADE;


--
-- Name: plan_previews fk_plan_previews_trip_id_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plan_previews
    ADD CONSTRAINT fk_plan_previews_trip_id_account_id FOREIGN KEY (trip_id, account_id) REFERENCES public.trips(id, account_id) ON DELETE CASCADE;


--
-- Name: preview_revisions fk_preview_revisions_plan_preview_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preview_revisions
    ADD CONSTRAINT fk_preview_revisions_plan_preview_id FOREIGN KEY (plan_preview_id) REFERENCES public.plan_previews(id) ON DELETE CASCADE;


--
-- Name: provider_field_rules fk_provider_field_rules_provider_policy_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_field_rules
    ADD CONSTRAINT fk_provider_field_rules_provider_policy_id FOREIGN KEY (provider_policy_id) REFERENCES public.provider_policies(id) ON DELETE CASCADE;


--
-- Name: provider_policies fk_provider_policies_data_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_policies
    ADD CONSTRAINT fk_provider_policies_data_provider_id FOREIGN KEY (data_provider_id) REFERENCES public.data_providers(id) ON DELETE RESTRICT;


--
-- Name: publication_facts fk_publication_facts_catalog_publication_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_facts
    ADD CONSTRAINT fk_publication_facts_catalog_publication_id FOREIGN KEY (catalog_publication_id) REFERENCES public.catalog_publications(id) ON DELETE RESTRICT;


--
-- Name: publication_facts fk_publication_facts_place_fact_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_facts
    ADD CONSTRAINT fk_publication_facts_place_fact_id FOREIGN KEY (place_fact_id) REFERENCES public.place_facts(id) ON DELETE RESTRICT;


--
-- Name: publication_media fk_publication_media_catalog_publication_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_media
    ADD CONSTRAINT fk_publication_media_catalog_publication_id FOREIGN KEY (catalog_publication_id) REFERENCES public.catalog_publications(id) ON DELETE RESTRICT;


--
-- Name: publication_media fk_publication_media_media_asset_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_media
    ADD CONSTRAINT fk_publication_media_media_asset_id FOREIGN KEY (media_asset_id) REFERENCES public.media_assets(id) ON DELETE RESTRICT;


--
-- Name: query_embedding_cache fk_query_embedding_cache_provider_policy_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_embedding_cache
    ADD CONSTRAINT fk_query_embedding_cache_provider_policy_id FOREIGN KEY (provider_policy_id) REFERENCES public.provider_policies(id) ON DELETE RESTRICT;


--
-- Name: research_cache fk_research_cache_provider_policy_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.research_cache
    ADD CONSTRAINT fk_research_cache_provider_policy_id FOREIGN KEY (provider_policy_id) REFERENCES public.provider_policies(id) ON DELETE RESTRICT;


--
-- Name: research_cache fk_research_cache_source_revision_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.research_cache
    ADD CONSTRAINT fk_research_cache_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES public.source_revisions(id) ON DELETE SET NULL;


--
-- Name: route_legs fk_route_legs_data_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_legs
    ADD CONSTRAINT fk_route_legs_data_provider_id FOREIGN KEY (data_provider_id) REFERENCES public.data_providers(id) ON DELETE RESTRICT;


--
-- Name: route_legs fk_route_legs_from_stop_id_trip_day_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_legs
    ADD CONSTRAINT fk_route_legs_from_stop_id_trip_day_id FOREIGN KEY (from_stop_id, trip_day_id) REFERENCES public.trip_stops(id, trip_day_id) ON DELETE CASCADE;


--
-- Name: route_legs fk_route_legs_to_stop_id_trip_day_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_legs
    ADD CONSTRAINT fk_route_legs_to_stop_id_trip_day_id FOREIGN KEY (to_stop_id, trip_day_id) REFERENCES public.trip_stops(id, trip_day_id) ON DELETE CASCADE;


--
-- Name: route_legs fk_route_legs_trip_day_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_legs
    ADD CONSTRAINT fk_route_legs_trip_day_id FOREIGN KEY (trip_day_id) REFERENCES public.trip_days(id) ON DELETE CASCADE;


--
-- Name: routes_matrix_cache fk_routes_matrix_cache_provider_policy_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routes_matrix_cache
    ADD CONSTRAINT fk_routes_matrix_cache_provider_policy_id FOREIGN KEY (provider_policy_id) REFERENCES public.provider_policies(id) ON DELETE RESTRICT;


--
-- Name: source_revisions fk_source_revisions_source_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_revisions
    ADD CONSTRAINT fk_source_revisions_source_id FOREIGN KEY (source_id) REFERENCES public.sources(id) ON DELETE RESTRICT;


--
-- Name: sources fk_sources_data_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sources
    ADD CONSTRAINT fk_sources_data_provider_id FOREIGN KEY (data_provider_id) REFERENCES public.data_providers(id) ON DELETE SET NULL;


--
-- Name: study_participants fk_study_participants_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_participants
    ADD CONSTRAINT fk_study_participants_account_id FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- Name: study_session_logs fk_study_session_logs_study_participant_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_session_logs
    ADD CONSTRAINT fk_study_session_logs_study_participant_id FOREIGN KEY (study_participant_id) REFERENCES public.study_participants(id) ON DELETE CASCADE;


--
-- Name: trip_days fk_trip_days_trip_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_days
    ADD CONSTRAINT fk_trip_days_trip_id FOREIGN KEY (trip_id) REFERENCES public.trips(id) ON DELETE CASCADE;


--
-- Name: trip_stops fk_trip_stops_catalog_publication_id_place_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_stops
    ADD CONSTRAINT fk_trip_stops_catalog_publication_id_place_id FOREIGN KEY (catalog_publication_id, place_id) REFERENCES public.catalog_publications(id, place_id) ON DELETE RESTRICT;


--
-- Name: trip_stops fk_trip_stops_place_id_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_stops
    ADD CONSTRAINT fk_trip_stops_place_id_city_id FOREIGN KEY (place_id, city_id) REFERENCES public.places(id, city_id) ON DELETE RESTRICT;


--
-- Name: trip_stops fk_trip_stops_trip_day_id_trip_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_stops
    ADD CONSTRAINT fk_trip_stops_trip_day_id_trip_id FOREIGN KEY (trip_day_id, trip_id) REFERENCES public.trip_days(id, trip_id) ON DELETE CASCADE;


--
-- Name: trip_stops fk_trip_stops_trip_id_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_stops
    ADD CONSTRAINT fk_trip_stops_trip_id_city_id FOREIGN KEY (trip_id, city_id) REFERENCES public.trips(id, city_id) ON DELETE CASCADE;


--
-- Name: trip_stops fk_trip_stops_web_place_candidate_id_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_stops
    ADD CONSTRAINT fk_trip_stops_web_place_candidate_id_city_id FOREIGN KEY (web_place_candidate_id, city_id) REFERENCES public.web_place_candidates(id, city_id) ON DELETE RESTRICT;


--
-- Name: trips fk_trips_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT fk_trips_account_id FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE CASCADE;


--
-- Name: trips fk_trips_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT fk_trips_city_id FOREIGN KEY (city_id) REFERENCES public.cities(id) ON DELETE RESTRICT;


--
-- Name: web_place_candidates fk_web_place_candidates_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_place_candidates
    ADD CONSTRAINT fk_web_place_candidates_city_id FOREIGN KEY (city_id) REFERENCES public.cities(id) ON DELETE RESTRICT;


--
-- Name: web_place_candidates fk_web_place_candidates_promoted_place_id_city_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_place_candidates
    ADD CONSTRAINT fk_web_place_candidates_promoted_place_id_city_id FOREIGN KEY (promoted_place_id, city_id) REFERENCES public.places(id, city_id) ON DELETE RESTRICT;


--
-- Name: web_place_candidates fk_web_place_candidates_reviewed_by_account_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_place_candidates
    ADD CONSTRAINT fk_web_place_candidates_reviewed_by_account_id FOREIGN KEY (reviewed_by_account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- Name: web_place_candidates fk_web_place_candidates_source_revision_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.web_place_candidates
    ADD CONSTRAINT fk_web_place_candidates_source_revision_id FOREIGN KEY (source_revision_id) REFERENCES public.source_revisions(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

\unrestrict MCSzH36Do0ebXGp4YcFXLtnQuLSrUj0AHmKTQJqBkCHKCzjeWPW7UzDGQLichQI

