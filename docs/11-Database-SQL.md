# SQL Database Design — Danang TourGuide

PostgreSQL 16+ with **PostGIS** and **pgvector**. Vector index details in [12-Database-Vector.md](./12-Database-Vector.md).

## 1. Business requirements

- Users, guest merge, profiles, media ownership
- Curated POIs with ops + preference attributes
- Saves, collections, trips, days, stops, stop status
- Rec runs + explanation evidence
- Feedback, arrival events
- Knowledge chunks for RAG (text in SQL; vectors in pgvector)

## 2. Volume (thesis)

| Entity | V1 estimate |
|--------|-------------|
| Places | 150 |
| Place images | ~900 |
| Users (demo) | < 100 |
| Embeddings | < 5k rows |

Availability: single RDS OK. Backup: daily snapshot.

## 3. ER (text)

```text
users 1—0..1 preference_profiles
users 1—* media_assets
users 1—* trips *—1 users
trips 1—* trip_days 1—* trip_stops *—1 places
places 1—* place_images
places 1—* knowledge_chunks
users *—* places (saved_places)
users 1—* collections 1—* saved_places
users 1—* recommendation_runs 1—* match_evidence *—1 places
```

---

## 4. DDL (core)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email         TEXT UNIQUE,
  password_hash TEXT,
  google_sub    TEXT UNIQUE,
  language      TEXT NOT NULL DEFAULT 'vi' CHECK (language IN ('vi', 'en')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at    TIMESTAMPTZ
);

CREATE TABLE guest_sessions (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  device_hint TEXT,
  merged_into UUID REFERENCES users(id),
  expires_at  TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE preference_profiles (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id      UUID UNIQUE REFERENCES users(id),
  guest_id     UUID UNIQUE REFERENCES guest_sessions(id),
  attributes   JSONB NOT NULL DEFAULT '{}',
  confirmed_at TIMESTAMPTZ,
  version      INT NOT NULL DEFAULT 1,
  CHECK ((user_id IS NOT NULL) <> (guest_id IS NOT NULL))
);

CREATE TABLE media_assets (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_user_id UUID REFERENCES users(id),
  guest_id     UUID REFERENCES guest_sessions(id),
  s3_key       TEXT NOT NULL,
  purpose      TEXT NOT NULL CHECK (purpose IN ('taste', 'explore_image', 'poi')),
  status       TEXT NOT NULL CHECK (status IN ('pending', 'uploaded', 'ready', 'failed')),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK ((owner_user_id IS NOT NULL) <> (guest_id IS NOT NULL) OR
         (purpose = 'poi' AND owner_user_id IS NULL AND guest_id IS NULL))
);

CREATE TABLE places (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  slug               TEXT UNIQUE NOT NULL,
  name_vi            TEXT NOT NULL,
  name_en            TEXT NOT NULL,
  category           TEXT NOT NULL,
  description_vi     TEXT,
  description_en     TEXT,
  location           GEOGRAPHY(Point, 4326) NOT NULL,
  source_refs        JSONB NOT NULL DEFAULT '[]',
  pref_attributes    JSONB NOT NULL DEFAULT '{}',
  experience         JSONB NOT NULL DEFAULT '{}',
  opening_hours      JSONB,
  avg_duration_min   INT CHECK (avg_duration_min > 0),
  price_level        INT CHECK (price_level BETWEEN 0 AND 4),
  best_visit_time    TEXT,
  context_flags      JSONB NOT NULL DEFAULT '{}',
  semantic_tags      TEXT[] NOT NULL DEFAULT '{}',
  place_embedding    VECTOR(768),
  is_published       BOOLEAN NOT NULL DEFAULT true,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE place_images (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  place_id    UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  s3_key      TEXT NOT NULL,
  is_hero     BOOLEAN NOT NULL DEFAULT false,
  embedding   VECTOR(768),
  sort_order  INT NOT NULL DEFAULT 0
);

CREATE TABLE knowledge_chunks (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  place_id    UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  locale      TEXT NOT NULL CHECK (locale IN ('vi', 'en')),
  heading     TEXT,
  body        TEXT NOT NULL,
  source      TEXT NOT NULL,
  source_url  TEXT,
  verified_at TIMESTAMPTZ,
  embedding   VECTOR(768)
);

CREATE TABLE collections (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (id, user_id)
);

CREATE TABLE saved_places (
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  place_id      UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  collection_id UUID,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, place_id),
  FOREIGN KEY (collection_id, user_id) REFERENCES collections(id, user_id)
);

CREATE TABLE trips (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title         TEXT,
  start_date    DATE NOT NULL,
  end_date      DATE NOT NULL,
  companions    TEXT,
  budget_level  INT CHECK (budget_level BETWEEN 0 AND 4),
  pace          TEXT CHECK (pace IN ('relaxed', 'balanced', 'packed')),
  status        TEXT NOT NULL CHECK (status IN ('draft', 'planned', 'active', 'completed')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (end_date >= start_date)
);

CREATE TABLE trip_days (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  trip_id    UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  day_index  INT NOT NULL,
  date       DATE NOT NULL,
  UNIQUE (trip_id, day_index)
);

CREATE TABLE trip_stops (
  id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  trip_day_id           UUID NOT NULL REFERENCES trip_days(id) ON DELETE CASCADE,
  place_id              UUID NOT NULL REFERENCES places(id),
  seq                   INT NOT NULL,
  arrival_time          TIME,
  departure_time        TIME,
  visit_duration_min    INT,
  travel_time_to_next_min INT,
  status                TEXT NOT NULL DEFAULT 'upcoming'
    CHECK (status IN ('upcoming', 'current', 'completed', 'skipped')),
  UNIQUE (trip_day_id, seq)
);

CREATE TABLE taste_jobs (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id      UUID REFERENCES users(id),
  guest_id     UUID REFERENCES guest_sessions(id),
  status       TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'succeeded', 'failed')),
  error        TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK ((user_id IS NOT NULL) <> (guest_id IS NOT NULL))
);

CREATE TABLE image_analyses (
  media_id    UUID PRIMARY KEY REFERENCES media_assets(id) ON DELETE CASCADE,
  tags        JSONB NOT NULL DEFAULT '{}',
  embedding   VECTOR(768)
);

CREATE TABLE recommendation_runs (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    UUID REFERENCES users(id),
  guest_id   UUID REFERENCES guest_sessions(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK ((user_id IS NOT NULL) <> (guest_id IS NOT NULL))
);

CREATE TABLE match_evidence (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id     UUID NOT NULL REFERENCES recommendation_runs(id) ON DELETE CASCADE,
  place_id   UUID NOT NULL REFERENCES places(id),
  scores     JSONB NOT NULL,
  path_nodes JSONB NOT NULL
);

CREATE TABLE visit_feedback (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  place_id   UUID NOT NULL REFERENCES places(id),
  trip_id    UUID REFERENCES trips(id),
  rating     TEXT NOT NULL CHECK (rating IN ('loved', 'okay', 'not_for_me')),
  reasons    TEXT[] NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE arrival_events (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  trip_stop_id UUID NOT NULL REFERENCES trip_stops(id) ON DELETE CASCADE,
  detected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  method       TEXT NOT NULL CHECK (method IN ('gps', 'manual', 'simulated')),
  lat          DOUBLE PRECISION,
  lng          DOUBLE PRECISION,
  UNIQUE (trip_stop_id),
  CHECK (lat IS NULL OR lat BETWEEN -90 AND 90),
  CHECK (lng IS NULL OR lng BETWEEN -180 AND 180)
);

CREATE TABLE not_interested (
  user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
  guest_id   UUID REFERENCES guest_sessions(id) ON DELETE CASCADE,
  place_id   UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK ((user_id IS NOT NULL) <> (guest_id IS NOT NULL))
);
```

---

## 5. Indexes

```sql
CREATE INDEX idx_places_location ON places USING GIST (location);
CREATE INDEX idx_places_category ON places (category) WHERE is_published;
CREATE INDEX idx_places_tags ON places USING GIN (semantic_tags);
CREATE INDEX idx_places_pref ON places USING GIN (pref_attributes);
CREATE INDEX idx_trip_user ON trips (user_id, created_at DESC);
CREATE INDEX idx_stops_day ON trip_stops (trip_day_id, seq);
CREATE INDEX idx_chunks_place ON knowledge_chunks (place_id, locale);
CREATE UNIQUE INDEX uq_not_interested_user ON not_interested (user_id, place_id) WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX uq_not_interested_guest ON not_interested (guest_id, place_id) WHERE guest_id IS NOT NULL;
CREATE INDEX idx_media_user ON media_assets (owner_user_id) WHERE owner_user_id IS NOT NULL;
CREATE INDEX idx_media_guest ON media_assets (guest_id) WHERE guest_id IS NOT NULL;
```

HNSW/IVFFlat for vectors: see vector design doc.

---

## 6. Views

```sql
CREATE VIEW v_published_places AS
SELECT id, slug, name_en, name_vi, category, location, pref_attributes
FROM places WHERE is_published;
```

---

## 7. Integrity rules

- Operational fields nullable only if unknown; API must not fill from LLM.
- `trip_stops.place_id` must reference published places at insert time (app + trigger optional).
- Validate `arrival_time < departure_time` when both are present; itinerary times use the `Asia/Ho_Chi_Minh` trip timezone and cross-day stops require an explicit day split.
- Guest-to-user merge is one transaction for ownership rows, followed by idempotent S3 key handling. A guest profile must be detached or deleted after transfer; no profile can have both owner columns.
- `deleted_at` is a temporary tombstone while a retryable cleanup job deletes owned S3 objects and personal rows. Define retention and backup expiry separately; never call the tombstone itself deletion.
- A collection must belong to the same user as its saved place. The composite foreign key enforces this; moving/deleting a collection requires an explicit application decision (currently `RESTRICT`).
- Reordering `seq` under its unique constraint needs an atomic transaction with temporary positions or a deferrable unique constraint; do not update adjacent positions one row at a time.
- A migration/seed should validate that stop `place_id` is published and that each recommended evidence path references only stored inputs; foreign keys alone do not enforce these business conditions.

---

## 8. Security

- App role `tourguide_app` DML only; no DROP.
- RDS encryption at rest; TLS in transit.
- No secrets in tables.

## 9. Graph/NoSQL

Not used. Redis keys e.g. `wx:{lat}:{lng}:{date}`, `route:{from}:{to}:{mode}`, `foryou:{userId}`.

## 10. Source and model lineage

`knowledge_chunks.source` is a human-readable title; `source_url` and `verified_at` record provenance. Ingestion also records license/permission and retrieval date in the source manifest. Store the pinned embedding model ID and output dimension in deployment configuration and in an ingestion manifest. A change to model or dimension requires new columns/indexes and full re-embedding before vectors from different spaces can be compared. The SQL above is a design baseline, not a migration already executed against RDS.
