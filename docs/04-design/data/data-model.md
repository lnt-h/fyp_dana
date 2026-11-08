# Gonarra Data Model

| Field | Value |
|---|---|
| Document ID | GONARRA-DATA |
| Version | 2.0 (condensed; 0.1–0.3 five-city text at git tag `docs-sdlc-full`) |
| Date | 2026-11-09 |
| Owner | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor — **[Pending]** |
| DBMS | PostgreSQL 16 + PostGIS + pgvector + pg_trgm + pgcrypto |
| Implementation | Alembic `apps/api/migrations/versions`, head **`20261108_0009`** |
| Contract file | [schema.sql](./schema.sql) |

This document summarises the physical model, ownership, retention and the main transactions. Architecture: [SAD](../architecture/SAD.md) §4; API: [api-contract.md](../api/api-contract.md).

**Source of truth.** The Alembic migrations at head (`20261108_0009`) are what runs. [`schema.sql`](./schema.sql) is generated from them with `pg_dump --schema-only` (the command is in its header) and must be regenerated after every migration; it applies cleanly on a fresh PostGIS/pgvector database (verified 2026-11-09, 48 tables). This document explains the model; the SQL file is the exact DDL.

| Version | Date | Change |
|---|---|---|
| 0.1–0.3 | 2026-11-04..05 | Five-city model with curator review |
| 2.0 | 2026-11-09 | Rewritten against migrations 0001–0009: Đà Nẵng only, areas, web candidates and trust levels, closure rules, quota ledger and caches, automated publication gate (DEC-022), content origin (DEC-025), city-level Guide sessions (DEC-017), fact origin and grounding (DEC-028) |

## 1. Conventions

- Surrogate keys are `uuid` (`gen_random_uuid()`); `catalog_audit_events.id` is a `bigint` identity.
- Enumerations are `text` + `CHECK`, extended by a constraint swap in a migration (no `CREATE TYPE`).
- `geography(Point, 4326)` and `geography(MultiPolygon, 4326)` for locations and boundaries (metres, GIST); `vector(768)` for embeddings (`gemini-embedding-001`); `timestamptz` stored in UTC and shown in `Asia/Ho_Chi_Minh`; `time` for local day windows and planned times; `char(64)` for SHA-256 hex.
- `updated_at` is set by the shared trigger `fn_set_updated_at`. Append-only tables (`source_revisions`, `preview_revisions`) reject updates (`fn_reject_update`).
- Vietnamese search uses diacritic-folded normalized columns with trigram indexes, not collation.

## 2. Tables by area

### 2.1 Identity and reference data (migrations 0001, 0002)

| Table | Purpose |
|---|---|
| `accounts` | Clerk subject (`clerk_user_id`) → account UUID. No e-mail, name or phone is stored. Seeded pseudo-accounts: `system:gonarra-pipeline` (publication gate actor) and the demo shared user (non-production only) |
| `cities` | Launch cities with boundary and `is_enabled`; seed contains only `da-nang` (DEC-013) |
| `areas` | Travel areas inside a city (e.g. Hội An), with boundary polygons loaded from `apps/api/data/areas/da-nang.yaml` |
| `categories` | Place categories (bilingual names, sort order) |
| `fact_fields` | Fact field codes (OPENING_HOURS, ADMISSION_PRICE, ADDRESS_VI, …) with value kind, `required_for_publication` and `stale_after_days` |

### 2.2 Provider governance and staging (0002, 0006)

| Table | Purpose |
|---|---|
| `data_providers` | Every external source or service (kinds: OPEN_DATASET, RUNTIME_API, OFFICIAL_SOURCE, MEDIA_LIBRARY, AI_SERVICE, WEB_SEARCH, WEB_CONTENT, OPERATOR_DATA) |
| `provider_policies` | Versioned terms per provider (`DRAFT` / `ACTIVE` / `RETIRED`), attribution text, review date |
| `provider_field_rules` | Default-deny persistence per field: `ALLOW_CANONICAL`, `ALLOW_EPHEMERAL` (with `max_retention`), `ALLOW_IDENTIFIER_ONLY`, `DENY` (ADR-006) |
| `import_runs`, `import_records` | One run per source release; each record keeps only policy-allowed payload, validation and match state |
| `external_place_identities` | Upstream IDs (Wikidata QID, OSM element, Google `place_id`) linked to a place |

### 2.3 Catalog content, provenance and media (0002, 0007, 0009)

| Table | Purpose |
|---|---|
| `places` | Place identity, area, category, location, visit durations; `workflow_state` IMPORTED → … → PUBLISHED / RETIRED (internal, never traveler-visible) |
| `place_localizations` | VI and EN name and descriptions per revision. `translation_origin` ORIGINAL, HUMAN_TRANSLATION, AI_DRAFT or **AI_SUMMARY** (0007, DEC-025: written by the grounded writer from cited sources). `name_is_source_fallback` (0007): the EN name is the Vietnamese proper name reused unchanged |
| `place_aliases` | Search names per locale (`NAME` = display name, `ALIAS`); unique per (place, locale, normalized alias) since 0006 |
| `sources`, `source_revisions` | Publisher, licence and attribution; each consulted URL or record as an immutable revision with retrieval time and content hash |
| `place_facts` | One value per field per revision: `knowledge_state` KNOWN / UNKNOWN / NOT_APPLICABLE, `value` jsonb, `verified_at`, `valid_until`, conflict state. **`origin`** SOURCE / OWNER / AI_EXTRACTED and **`grounding`** STRONG / WEAK, the latter only for AI_EXTRACTED (0009, DEC-028) |
| `fact_evidence` | Fact → source revision, with the supported claim |
| `media_assets`, `place_media` | Licensed images (Wikimedia Commons, DEC-024) with creator, licence, attribution and rights state; ordered per place |
| `place_closure_rules` | Calendar rules (`WEEKLY`, `DATE`, `LUNAR_DATE`, `SEASON`, `TICKET_VALIDITY`) for a place, area or city with effect `CLOSED` / `PARTIAL` / `EVENT` / `NOTICE` and severity; loaded only from the owner's YAML file (ADR-011, DEC-022) |
| `web_place_candidates` | Research-agent finds: name, source revision, `fetched_at`, optional location with `coordinate_source`, `places_check_outcome` (EXISTS_OPERATIONAL, EXISTS_CLOSED, NOT_FOUND, OUTSIDE_CITY, SKIPPED), state PENDING / PROMOTED / REJECTED / EXPIRED, `promoted_place_id` (ADR-014) |

### 2.4 Guide corpus and publications (0002)

| Table | Purpose |
|---|---|
| `knowledge_chunks` | Approved narrative chunks per place (`scope = PLACE`) or city (`scope = CITY`, sections CITY_OVERVIEW, GETTING_AROUND, EVENTS_CALENDAR, PRACTICAL), per locale and corpus revision, with `embedding vector(768)` and `embedding_model`. Never a source of operational facts |
| `knowledge_chunk_sources` | Chunk → source revision |
| `catalog_publications` | Immutable snapshot per publication revision (`PUBLISHED` / `SUPERSEDED` / `WITHDRAWN`) pinning location, category, area, both localizations and the corpus revision |
| `publication_facts`, `publication_media` | Facts and media pinned by a publication |
| `catalog_audit_events` | Append-only audit; actions include AUTO_APPROVE, AUTO_PUBLISH, AUTO_REJECT (0006), PUBLISH, WITHDRAW, WEB_PROMOTE, POLICY_CHANGE |

### 2.5 Private planning and assistance (0003, 0006, 0007, 0008)

| Table | Purpose |
|---|---|
| `account_preferences` | Locale, pace, interests, allowed modes, day window, AI-notice acknowledgement |
| `trips` | One city, 1–3 days; `status` DRAFT / SAVED; `revision` (0 = never saved) is the Save concurrency token; `planning_preferences` jsonb |
| `trip_days`, `trip_stops`, `route_legs` | The saved itinerary. A stop is either a published place + publication (`trust_level = VERIFIED`) or a web candidate (`WEB_UNVERIFIED`), enforced by CHECK. Legs are WALK or DRIVE with availability AVAILABLE / UNAVAILABLE / EXPIRED. Estimated demo legs (DEC-023) are flagged `estimated` in the preview snapshot and API; they are never cached |
| `plan_previews`, `preview_revisions` | Unsaved proposals; revisions are immutable (`origin` GENERATED, MANUAL_EDIT, DAY_REGENERATED, REPAIRED) with `plan_health`, snapshot jsonb and model/prompt/corpus provenance |
| `guide_sessions` | City-level (`place_id` NULL) or one published place, optionally linked to an owned trip (0008 dropped the context CHECK) |
| `guide_messages`, `guide_message_citations` | Immutable messages; `answer_status` ANSWERED, ANSWERED_WEB_UNVERIFIED (reserved, 0008), INSUFFICIENT_EVIDENCE, NOT_RECOGNISED; citations point to a source revision and a chunk or fact |
| `ai_invocations` | Metadata only: purpose (incl. RESEARCH, GUIDE_ANSWER, CONTENT_SUMMARY from 0007), model, outcome, latency, tokens, `agent_run_id`. Never prompts or responses |
| `idempotency_records` | (account, operation, key) with request hash, state and stored response; operations TRIP_SAVE, TRIP_CREATE, PREVIEW_CREATE, PREVIEW_EDIT, DAY_REGENERATE, ACCOUNT_DELETE, PUBLISH, GUIDE_ASK |
| `account_deletion_jobs` | REQUESTED → IN_PROGRESS → COMPLETED / FAILED; `clerk_subject_sha256` (0006) |

### 2.6 Quota ledger and caches (0004, DEC-018)

| Table | Purpose | Retention |
|---|---|---|
| `ai_quota_ledger` | Reserved and used counts per bucket and period (GLOBAL: GEMINI_FLASH, GEMINI_FLASH_LITE, GEMINI_EMBED, GROQ, TAVILY_DAY, TAVILY_MONTH, PLACES, ROUTES_ELEMENTS; ACCOUNT: ACCOUNT_PROPOSALS, ACCOUNT_QUESTIONS) | Period rows |
| `routes_matrix_cache` | Distance and duration per (origin key, destination key, mode); only real router measurements | 30 days |
| `research_cache` | Tavily results and fetched page text (`TAVILY`, `WEB_PAGE`) with source revision | 7 days |
| `places_lookup_cache` | Google Places existence outcome and location | location ≤ 30 days; outcome 24 h |
| `query_embedding_cache` | Guide question embeddings keyed by text hash, locale and model | 90 days |

### 2.7 User study (0005)

`study_participants` (pseudonymous code, no name) and `study_session_logs` (locale, request and first-proposal timestamps, save outcome). No API route writes them yet (API-032 is planned).

## 3. Views

| View | Purpose |
|---|---|
| `vw_published_places` | Current publication of each place with both pinned localizations; the only planner and search source |
| `vw_published_place_facts` | Facts pinned by the current publication with source, licence and an `is_stale` flag (operational fact older than `stale_after_days` or past `valid_until`) |
| `vw_guide_chunks` | Approved place chunks of the corpus revision pinned by each current publication (city-scope chunks are read from `knowledge_chunks` directly) |
| `vw_trip_stop_trust` | Effective trust of a saved stop: a web stop reads `VERIFIED` once its candidate is promoted and the place is published |

## 4. Ownership and deletion

Every private row carries `account_id` directly or through a composite FK including it (`plan_previews`, `guide_sessions` → `trips (id, account_id)`), so ownership cannot be mixed. Every private query filters by the authenticated account.

`DELETE FROM accounts WHERE id = :account_id` cascades to preferences, trips (days, stops, legs), previews and revisions, Guide sessions, messages and citations, AI invocation metadata and idempotency records. It sets NULL on `account_deletion_jobs.account_id`, `study_participants.account_id`, `catalog_publications.published_by_account_id` and `catalog_audit_events.actor_account_id`.

Deletion workflow (FR-071, FR-072, ≤ 24 h): API-006 inserts a REQUESTED job (one open job per account); `python -m app.cli run-deletion-jobs` sets IN_PROGRESS, deletes the account rows, then deletes the Clerk user last (when `GONARRA_CLERK_SECRET_KEY` is set) and marks the job COMPLETED. Failures become FAILED and are retried. After a database restore, deletions are re-applied before traffic resumes.

Referential actions: CASCADE for content that belongs to its parent; RESTRICT for evidence and history (`source_revisions`, publications, providers, policies, cities, categories, `trip_stops` → places or publications); SET NULL where a row must survive but stop pointing at a deleted person. Published places are never deleted; they are withdrawn or retired.

## 5. Main transactions

### 5.1 Automated publication (DEC-022)

`python -m app.cli publish auto` (or `pipeline run`) evaluates each candidate place in code (`curation/auto_publish.py`) and publishes through `fn_publish_place`, which re-checks the SQL gate (`fn_publication_gate_violations`) inside the same transaction. The gate requires VI and EN names and descriptions, a search name per locale, an in-boundary location, a category, an attributed source revision for every shown fact and a recorded licence. Unchanged input creates no new publication. Rejections are written to the audit log with a reason. `fn_withdraw_place` serves API-037 and `publish takedown`. AI-extracted facts (DEC-028) arrive as import records of provider `gonarra_ai_facts` and are published as `origin = AI_EXTRACTED` only where no owner-sheet or OSM value exists.

### 5.2 Explicit Save (ADR-009)

One transaction under READ COMMITTED with row locks:

1. Claim the `Idempotency-Key` in `idempotency_records` (operation `TRIP_SAVE`). Same key and hash already COMPLETED → replay the stored response; different hash → 409; still IN_PROGRESS → 409 retryable.
2. Lock the trip; `revision` ≠ expected → 409 `revision_conflict`.
3. Load the preview revision (owner, ACTIVE, expected base revision). `plan_health = BLOCKED` → 409 `plan_blocked`; a `WEB_UNVERIFIED` stop without acknowledgement → 422; a stop whose publication is no longer PUBLISHED → 409.
4. Replace `trip_days` (cascading stops and legs) from the snapshot; legs keep only router-measured values.
5. `trips.revision + 1`, `status = SAVED`; preview `status = SAVED`.
6. Store the response for replay; commit.

A crash before commit leaves the saved itinerary and the preview untouched; two different saves against the same base cannot both succeed.

## 6. Indexes

- GIST on `places.location`, `import_records.location`, `web_place_candidates.location` and published `catalog_publications.location` (radius and boundary queries, 300 m photo filter).
- GIN trigram on `place_aliases.alias_normalized` (diacritic-free name search, Guide entity leg) and on `lower(knowledge_chunks.content)` (Guide lexical leg).
- HNSW (`vector_cosine_ops`) on `knowledge_chunks.embedding` for approved chunks (Guide vector leg).
- `expires_at` indexes on previews, Guide sessions, idempotency records and every cache for expiry; owner-first composite indexes on private tables.

## 7. Classification and retention

| Class | Tables | Retention |
|---|---|---|
| Public once published | cities, areas, categories, fact fields, published content through the views | Project lifetime; withdrawn content kept as history |
| Internal | providers, policies, field rules, import runs and records, identities, drafts, audit events, closure rules, web candidates | Project lifetime; ephemeral fields follow `max_retention` |
| Confidential (account-owned) | preferences, trips, previews, Guide sessions and messages, AI invocation metadata, idempotency records, deletion jobs, study tables | Deleted ≤ 24 h after confirmed account deletion; previews, Guide sessions (30 days) and idempotency records (24 h) expire by `expires_at` and are refused on read; study records deleted by 2027-06-30 |
| Restricted | `accounts.clerk_user_id`, stored idempotency responses, private evidence and rights-proof keys | As their parent |

Sweep jobs that physically delete expired previews, sessions, idempotency records and cache rows are planned as CLI commands on a timer; today expiry is enforced when the row is read.

**Never stored** (ADR-006): Google Places hours, status, ratings, reviews, photos and contact data (only `place_id`, plus location ≤ 30 days in the cache); indicative stay prices; prompts and raw model responses; traveler precise location, photos and audio; Clerk profile data. Estimated demo legs are never cached.

## 8. Migrations and seed

| Revision | Content |
|---|---|
| `20261102_0001` | Extensions `pgcrypto`, `postgis`, `vector`; `accounts` |
| `20261106_0002` | `pg_trgm`; reference, provider, staging, catalog content, media, web candidates, closure rules, Guide corpus, publications, audit; functions, triggers and catalog views |
| `20261106_0003` | Private planning: preferences, trips, previews, Guide sessions and messages, AI invocations, idempotency, deletion jobs; `vw_trip_stop_trust` |
| `20261106_0004` | Quota ledger and provider caches |
| `20261106_0005` | Study tables |
| `20261107_0006` | Automated pipeline CHECK values (AUTO_* audit actions, OPERATOR_DATA provider kind, new idempotency operations), `clerk_subject_sha256`, per-locale alias uniqueness |
| `20261108_0007` | `AI_SUMMARY` translation origin, `name_is_source_fallback`, `CONTENT_SUMMARY` purpose |
| `20261108_0008` | City-level Guide sessions, `GUIDE_ASK` idempotency, `ANSWERED_WEB_UNVERIFIED` status |
| `20261108_0009` | `place_facts.origin` and `grounding` (DEC-028) |

Every revision has a downgrade; CI runs upgrade, integration tests and a downgrade/upgrade round-trip. Downgrades destroy data and are for development only; production rolls forward or restores from backup.

Seed (`python -m app.cli seed`, idempotent): the `da-nang` city and its areas, categories, fact fields, data providers with their policy revisions and field rules (activate with `policy activate`), and the pipeline system account. Closure rules load with `closure-rules load`; catalog content comes from `pipeline run` (Wikidata, OSM, Wikipedia, Commons, owner sheet).

## 9. Administration

- Backups: daily with point-in-time recovery where the host allows (RDS under ADR-002, or `pg_dump` on the single VM, OQ-129); RPO 24 h, RTO 4 h. Backups expire after 7 days.
- Roles: a migrator role owns the schema; the API role has DML only, insert-only on audit events. Secrets stay server-side.
- `ANALYZE` after imports and embedding runs.
