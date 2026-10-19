-- DaNavi v1.3 design DDL, 2026-10-19.
-- Reviewable proposed schema, NOT an executed migration. No production seed data.
-- ORM/engine/embedding model & dimension are pending compatibility spike.
BEGIN;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE TABLE users (
 id uuid PRIMARY KEY, email text NOT NULL UNIQUE CHECK(email=lower(email)),
 password_hash text NOT NULL, google_sub text UNIQUE, locale text NOT NULL DEFAULT 'en' CHECK(locale IN('vi','en')), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE sessions (
 id uuid PRIMARY KEY,user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 refresh_token_hash text NOT NULL UNIQUE, expires_at timestamptz NOT NULL, revoked_at timestamptz, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE sources (
 id uuid PRIMARY KEY,title text NOT NULL,url text,document_reference text,publisher text,
 source_language text NOT NULL CHECK(source_language ~ '^[a-z]{2}(-[A-Z]{2})?$'),
 accessed_at timestamptz NOT NULL,reviewed_at timestamptz,rights_reference text NOT NULL,revision text NOT NULL,
 CHECK(url IS NOT NULL OR document_reference IS NOT NULL)
);
CREATE TABLE places (
 id uuid PRIMARY KEY,slug text NOT NULL UNIQUE,name_vi text NOT NULL,name_en text NOT NULL,aliases text[] NOT NULL DEFAULT '{}',
 description_vi text,description_en text NOT NULL,category text NOT NULL CHECK(category IN('Culture','Beach','Food','Nature')),tags text[] NOT NULL DEFAULT '{}',
 translation_review_status text NOT NULL CHECK(translation_review_status IN('draft','approved','retired')),
 translation_reviewer_reference text,translation_reviewed_at timestamptz,
 location geography(Point,4326) NOT NULL,arrival_target geography(Point,4326),arrival_radius_m numeric CHECK(arrival_radius_m>0),
 opening_hours jsonb CHECK(opening_hours IS NULL OR jsonb_typeof(opening_hours)='object'),suggested_visit_minutes integer NOT NULL CHECK(suggested_visit_minutes>0),
 published boolean NOT NULL DEFAULT false,revision integer NOT NULL DEFAULT 0 CHECK(revision>=0),updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(translation_review_status<>'approved' OR (translation_reviewer_reference IS NOT NULL AND translation_reviewed_at IS NOT NULL)),
 CHECK(NOT published OR translation_review_status='approved')
);
CREATE TABLE place_sources (
 place_id uuid NOT NULL REFERENCES places(id) ON DELETE CASCADE,source_id uuid NOT NULL REFERENCES sources(id),
 relationship text NOT NULL DEFAULT 'supports' CHECK(relationship IN('supports','translation_origin')),
 PRIMARY KEY(place_id,source_id)
);
CREATE TABLE place_facts (
 id uuid PRIMARY KEY,place_id uuid NOT NULL REFERENCES places(id),fact_key text NOT NULL,value jsonb,unit text,currency text,
 source_id uuid REFERENCES sources(id),verified_at timestamptz,valid_from timestamptz,valid_to timestamptz,
 status text NOT NULL CHECK(status IN('known','unknown','conflicting')),
 CHECK(status<>'known' OR (value IS NOT NULL AND value<>'null'::jsonb AND source_id IS NOT NULL AND verified_at IS NOT NULL)),
 CHECK(valid_to IS NULL OR valid_from IS NULL OR valid_to>valid_from)
);
CREATE TABLE place_images (
 id uuid PRIMARY KEY,place_id uuid NOT NULL REFERENCES places(id),s3_key text NOT NULL UNIQUE,
 rights_reference text NOT NULL,attribution text NOT NULL,alt_text text NOT NULL,sort_order integer NOT NULL CHECK(sort_order>=0),hero boolean NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX place_one_hero ON place_images(place_id) WHERE hero;
CREATE TABLE audio_guides (
 id uuid PRIMARY KEY,place_id uuid NOT NULL REFERENCES places(id),locale text NOT NULL CHECK(locale IN('vi','en')),
 s3_key text NOT NULL UNIQUE,size_bytes bigint NOT NULL CHECK(size_bytes>0),duration_seconds numeric NOT NULL CHECK(duration_seconds>0),transcript text NOT NULL,
 narrator_reference text NOT NULL,permission_reference text NOT NULL,offline_cache_allowed boolean NOT NULL DEFAULT false,offline_permission_reference text,
 review_status text NOT NULL CHECK(review_status IN('draft','approved','retired')),
 version integer NOT NULL CHECK(version>0),reviewed_at timestamptz,
 UNIQUE(place_id,locale,version),CHECK(review_status<>'approved' OR reviewed_at IS NOT NULL),
 CHECK(NOT offline_cache_allowed OR offline_permission_reference IS NOT NULL)
);
CREATE UNIQUE INDEX one_approved_audio ON audio_guides(place_id,locale) WHERE review_status='approved';
CREATE TABLE embedding_spaces (
 id uuid PRIMARY KEY,provider text NOT NULL,model text NOT NULL,dimension integer NOT NULL CHECK(dimension>0),
 preprocessing_version text NOT NULL,task_config jsonb NOT NULL,config_version text NOT NULL UNIQUE,active boolean NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX one_active_text_space ON embedding_spaces(active) WHERE active;
CREATE TABLE knowledge_chunks (
 id uuid PRIMARY KEY,place_id uuid NOT NULL REFERENCES places(id),source_id uuid NOT NULL REFERENCES sources(id),
 locale text NOT NULL CHECK(locale IN('vi','en')),source_language text NOT NULL CHECK(source_language ~ '^[a-z]{2}(-[A-Z]{2})?$'),heading text,body text NOT NULL,corpus_revision text NOT NULL,source_revision text NOT NULL,
 translation_review_status text NOT NULL CHECK(translation_review_status IN('not_required','draft','approved')),translation_reviewer_reference text,translation_reviewed_at timestamptz,
 review_status text NOT NULL CHECK(review_status IN('draft','approved','stale','retired')),
 embedding_space_id uuid NOT NULL REFERENCES embedding_spaces(id),embedding vector,
 CHECK(review_status<>'approved' OR embedding IS NOT NULL),
 CHECK(source_language='en' OR locale<>'en' OR (translation_review_status='approved' AND translation_reviewer_reference IS NOT NULL AND translation_reviewed_at IS NOT NULL))
);
-- Unbounded vector permits an explicit spike-selected dimension without inventing D.
-- Trigger enforces row space dimension; queries additionally pin active config/model/task.
CREATE FUNCTION check_chunk_embedding_dimension() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected integer;
BEGIN
 SELECT dimension INTO expected FROM embedding_spaces WHERE id=NEW.embedding_space_id;
 IF NEW.embedding IS NOT NULL AND vector_dims(NEW.embedding)<>expected THEN
  RAISE EXCEPTION 'embedding dimension mismatch';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER knowledge_embedding_dimension BEFORE INSERT OR UPDATE ON knowledge_chunks FOR EACH ROW EXECUTE FUNCTION check_chunk_embedding_dimension();
-- Embedding identity is immutable once defined; active flag may switch after full re-embedding.
CREATE FUNCTION protect_embedding_space_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF ROW(NEW.provider,NEW.model,NEW.dimension,NEW.preprocessing_version,NEW.task_config,NEW.config_version)
    IS DISTINCT FROM ROW(OLD.provider,OLD.model,OLD.dimension,OLD.preprocessing_version,OLD.task_config,OLD.config_version) THEN
  RAISE EXCEPTION 'create a new embedding space instead of changing its identity';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER embedding_space_identity BEFORE UPDATE ON embedding_spaces FOR EACH ROW EXECUTE FUNCTION protect_embedding_space_identity();
CREATE TABLE saved_places (
 user_id uuid REFERENCES users(id) ON DELETE CASCADE,place_id uuid REFERENCES places(id),created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(user_id,place_id)
);
CREATE TABLE trips (
 id uuid PRIMARY KEY,owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,title text NOT NULL,
 start_date date NOT NULL,day_count integer NOT NULL CHECK(day_count>0),timezone text NOT NULL DEFAULT 'Asia/Ho_Chi_Minh' CHECK(timezone='Asia/Ho_Chi_Minh'),
 start_point geography(Point,4326) NOT NULL,start_point_source text NOT NULL CHECK(start_point_source IN('map_pin','current_location','preset')),start_point_preset_id text,
 preferences jsonb NOT NULL CHECK(jsonb_typeof(preferences)='object'),status text NOT NULL DEFAULT 'draft' CHECK(status IN('draft','planned','active','completed')),
 revision integer NOT NULL DEFAULT 0 CHECK(revision>=0),created_at timestamptz NOT NULL DEFAULT now(),
 CHECK((start_point_source='preset' AND start_point_preset_id IS NOT NULL) OR (start_point_source<>'preset' AND start_point_preset_id IS NULL))
);
CREATE TABLE trip_days (
 id uuid PRIMARY KEY,trip_id uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,day_index integer NOT NULL CHECK(day_index>0),date date NOT NULL,
 UNIQUE(trip_id,day_index),UNIQUE(trip_id,date),UNIQUE(id,trip_id)
);
CREATE TABLE trip_stops (
 id uuid PRIMARY KEY,trip_id uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,day_id uuid NOT NULL,place_id uuid NOT NULL REFERENCES places(id),
 seq integer NOT NULL CHECK(seq>0),arrival_at timestamptz,departure_at timestamptz,visit_duration_min integer NOT NULL CHECK(visit_duration_min>0),
 state text NOT NULL DEFAULT 'upcoming' CHECK(state IN('upcoming','current','completed','skipped')),
 FOREIGN KEY(day_id,trip_id) REFERENCES trip_days(id,trip_id) ON DELETE CASCADE,
 UNIQUE(day_id,seq) DEFERRABLE INITIALLY DEFERRED,UNIQUE(id,trip_id),UNIQUE(id,day_id,trip_id),CHECK(departure_at IS NULL OR arrival_at IS NULL OR departure_at>arrival_at)
);
CREATE UNIQUE INDEX one_current_stop_per_trip ON trip_stops(trip_id) WHERE state='current';
CREATE TABLE route_legs (
 id uuid PRIMARY KEY,trip_id uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,day_id uuid NOT NULL,from_stop_id uuid NOT NULL,to_stop_id uuid NOT NULL,
 mode text NOT NULL CHECK(mode='car'),distance_m numeric CHECK(distance_m>=0),duration_s numeric CHECK(duration_s>=0),polyline text,
 provider text NOT NULL,provider_warnings jsonb NOT NULL DEFAULT '[]' CHECK(jsonb_typeof(provider_warnings)='array'),fetched_at timestamptz,status text NOT NULL CHECK(status IN('fresh','stale','unavailable')),itinerary_revision integer NOT NULL CHECK(itinerary_revision>=0),
 FOREIGN KEY(day_id,trip_id) REFERENCES trip_days(id,trip_id) ON DELETE CASCADE,
 FOREIGN KEY(from_stop_id,day_id,trip_id) REFERENCES trip_stops(id,day_id,trip_id) ON DELETE CASCADE,
 FOREIGN KEY(to_stop_id,day_id,trip_id) REFERENCES trip_stops(id,day_id,trip_id) ON DELETE CASCADE,
 UNIQUE(trip_id,from_stop_id,to_stop_id,mode),CHECK(from_stop_id<>to_stop_id),
 CHECK(status<>'fresh' OR (duration_s IS NOT NULL AND distance_m IS NOT NULL AND fetched_at IS NOT NULL)),
 CHECK(status='fresh' OR (duration_s IS NULL AND distance_m IS NULL AND polyline IS NULL))
);
CREATE TABLE day_start_legs (
 id uuid PRIMARY KEY,trip_id uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,day_id uuid NOT NULL UNIQUE,to_stop_id uuid NOT NULL,
 start_point geography(Point,4326) NOT NULL,mode text NOT NULL CHECK(mode='car'),distance_m numeric CHECK(distance_m>=0),duration_s numeric CHECK(duration_s>=0),polyline text,
 provider text NOT NULL,provider_warnings jsonb NOT NULL DEFAULT '[]' CHECK(jsonb_typeof(provider_warnings)='array'),fetched_at timestamptz,status text NOT NULL CHECK(status IN('fresh','stale','unavailable')),itinerary_revision integer NOT NULL CHECK(itinerary_revision>=0),
 FOREIGN KEY(day_id,trip_id) REFERENCES trip_days(id,trip_id) ON DELETE CASCADE,
 FOREIGN KEY(to_stop_id,day_id,trip_id) REFERENCES trip_stops(id,day_id,trip_id) ON DELETE CASCADE,
 CHECK(status<>'fresh' OR (duration_s IS NOT NULL AND distance_m IS NOT NULL AND fetched_at IS NOT NULL)),
 CHECK(status='fresh' OR (duration_s IS NULL AND distance_m IS NULL AND polyline IS NULL))
);
CREATE TABLE arrival_events (
 id uuid PRIMARY KEY,stop_id uuid NOT NULL UNIQUE REFERENCES trip_stops(id) ON DELETE CASCADE,
 method text NOT NULL CHECK(method IN('gps','manual','simulated')),detected_at timestamptz NOT NULL,
 accuracy_m numeric CHECK(accuracy_m>=0),distance_m numeric CHECK(distance_m>=0),dwell_s numeric CHECK(dwell_s>=0),
 CHECK(method<>'gps' OR (accuracy_m IS NOT NULL AND distance_m IS NOT NULL AND dwell_s IS NOT NULL))
);
CREATE TABLE itinerary_proposals (
 id uuid PRIMARY KEY,trip_id uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,base_revision integer NOT NULL CHECK(base_revision>=0),
 structured_draft jsonb NOT NULL CHECK(jsonb_typeof(structured_draft)='object'),warnings jsonb NOT NULL CHECK(jsonb_typeof(warnings)='array'),provider text NOT NULL,model_version text NOT NULL,corpus_version text NOT NULL,
 fact_version_snapshot jsonb NOT NULL,expires_at timestamptz NOT NULL,accepted_at timestamptz,created_at timestamptz NOT NULL DEFAULT now(),CHECK(expires_at>created_at)
);
CREATE TABLE idempotency_records (
 owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,scope text NOT NULL,key text NOT NULL,request_hash text NOT NULL,
 status text NOT NULL CHECK(status IN('in_progress','completed','failed')),result_reference jsonb,response_status integer,response_body jsonb,expires_at timestamptz NOT NULL,
 started_at timestamptz NOT NULL DEFAULT now(),operation_deadline_at timestamptz NOT NULL,
 CHECK(operation_deadline_at>=started_at),CHECK(expires_at>operation_deadline_at),PRIMARY KEY(owner_id,scope,key)
);
CREATE INDEX places_location_gist ON places USING gist(location);
CREATE INDEX places_category_published ON places(category,published);
CREATE INDEX places_tags_gin ON places USING gin(tags);
CREATE INDEX places_aliases_gin ON places USING gin(aliases);
CREATE INDEX trips_owner_created ON trips(owner_id,created_at DESC,id);
CREATE INDEX chunks_filter ON knowledge_chunks(place_id,locale,review_status,embedding_space_id);
CREATE INDEX facts_place_key ON place_facts(place_id,fact_key);
CREATE INDEX sessions_user ON sessions(user_id);
CREATE INDEX sources_review ON sources(reviewed_at);
CREATE INDEX idempotency_expiry ON idempotency_records(expires_at);
COMMIT;
-- Application validates English publication/translation provenance, alias normalisation,
-- P0 day_count=1, transportMode=car, preset configuration ownership, JSON structures,
-- exactly-one-current for active trips, progress transitions and source/corpus compatibility.
-- POST /account/delete reauthenticates, then deletes users; ON DELETE CASCADE removes the owner graph.
-- Security-log and backup expiry are governed outside this DDL by O-08.
-- Initial exact vector retrieval; no ANN index until dimension pinned and benchmark justifies it.
