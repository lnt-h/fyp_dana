# Gonarra project guide

| Field | Value |
|---|---|
| Audience | Whoever picks the repository up next: developer, reviewer, examiner |
| Date | 2026-11-09 |
| Scope | Everything in this repository as built on 2026-11-09 (DEC-034) |
| Sources of truth | [BRD](02-requirements/BRD.md) · [PRD](03-analysis/PRD.md) · [decisions](decisions.md) · [SAD](04-design/architecture/SAD.md) · [ADR](04-design/adr/) · [OpenAPI](04-design/api/openapi.yaml) · [schema.sql](04-design/data/schema.sql) |

This guide explains **how the project is put together and how a request travels through it**. It does not restate the
requirements; where a rule matters, it names the document that owns it. Read this first, then follow the links.

## 1. What Gonarra is

Gonarra (working name) is a bilingual Vietnamese/English travel planner and grounded local assistant. The FYP release
covers **Đà Nẵng only**, including the Hội An area (part of Đà Nẵng since the 2025 merger). One trip = one city, 1–3
days. VI and EN are equal launch locales; neither is a machine translation of the other.

The traveller can:

1. browse and search a catalog of published Đà Nẵng places, with a place card and cited sources;
2. answer a short prompt and preferences, receive an editable 1–3 day proposal on a timeline and map, with Plan Health
   (opening hours, calendar rules, ticket validity, travel legs);
3. edit the proposal (move, add, remove, replace, regenerate one day) and **save explicitly**;
4. open a saved trip, the "Today" view and booking handoff links (Agoda, Booking.com, Klook, 12Go);
5. ask a city-level or place-level Guide question answered only from supplied evidence, with citations;
6. delete the account and all its personal data.

Catalog content is **human-written and cited** (owner sheet, Wikivoyage, Wikipedia, Wikidata, OpenStreetMap, Wikimedia
Commons); AI is used only for planning rationales and Guide answers (DEC-031). Models never publish places and never
author descriptions, facts, hours, prices, distances or durations.

Release gate (MET-011 rev. 4): ≥ 100 published, gate-approved places in Đà Nẵng, ≥ 30 in the Hội An area, and ≥ 20
publishable food/café/market venues. On 2026-11-09 the rebuilt catalog has **173 published places, 63 in the Hội An
area**, and 60 publishable food/café/market places.

## 2. Repository map

```text
fyp_dana/
├── AGENTS.md                     rules for every coding agent (read first when changing code)
├── README.md                     how to run the app day to day, deploy, where the docs are
├── plan.md                       roadmap, milestones, cut order
├── progress.md                   current state and HANDOFF (implementation evidence)
├── docker-compose.yml            local development stack: db + api
├── docker-compose.prod.yml       production stack: migrate, api, caddy, backup
├── infra/                        Caddyfile, dev.env, postgres image, backup script, runbook
├── apps/
│   ├── api/                      Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · Typer
│   └── mobile/                   Expo SDK 58 · React Native · TypeScript · Expo Router · Clerk
└── docs/                         requirements, decisions, design, plans, verification, this guide
```

Generated or maintained artifacts:

| Artifact | Produced by | Checked by |
|---|---|---|
| `docs/04-design/api/openapi.yaml` | hand-maintained contract (source for mobile types) | lint in CI |
| `apps/api/openapi.json` | `uv run python scripts/export_openapi.py` | `--check` in CI |
| `docs/04-design/data/schema.sql` | `pg_dump` of a freshly migrated DB (header command) | applies on a fresh PostGIS/pgvector DB |
| `apps/mobile/src/lib/api/schema.d.ts` | `npm run gen:api` from `openapi.yaml` | `npm run typecheck` |

## 3. Runtime architecture

```mermaid
flowchart LR
  subgraph client["apps/mobile"]
    UI["Expo Router screens"]
    API_CLIENT["lib/api: typed client + SSE"]
    I18N["i18n (vi / en)"]
    UI --> API_CLIENT
  end

  subgraph server["apps/api (one container)"]
    HTTP["FastAPI /v1 REST + SSE"]
    PLAN["planning: orchestrator, pool, rule selector, OR-Tools solver, Plan Health"]
    GUIDE["guide: retrieval + grounded answer"]
    TRIPS["trips: preview edit, Save, snapshot, handoff"]
    CUR["curation: publication gate, chunks"]
    ING["ingestion: CLI importers"]
    AI["ai + agents: quota, redaction, Agno roles"]
    HTTP --> PLAN & GUIDE & TRIPS
    PLAN --> AI
    GUIDE --> AI
    ING --> CUR
  end

  DB[("PostgreSQL 16<br/>PostGIS · pgvector · pg_trgm")]
  CLERK["Clerk (identity)"]
  GEM["Gemini (selector, writer, embeddings)"]
  GROQ["Groq (researcher, fallback)"]
  TAV["Tavily (research)"]
  ROUTES["Google Routes (or demo estimate)"]
  PLACES["Google Places (existence check)"]
  OPEN["Open data: Wikidata, OSM, Wikipedia,<br/>Wikivoyage, Wikimedia Commons"]

  API_CLIENT -->|"HTTP /v1"| HTTP
  API_CLIENT -.->|"sign-in"| CLERK
  HTTP -->|"JWKS verify"| CLERK
  HTTP --> DB
  PLAN --> ROUTES & PLACES
  GUIDE --> GEM
  PLAN --> GEM & GROQ
  ING --> OPEN
  AI --> GEM & GROQ & TAV
```

Two deployables, coupled only through the HTTP `/v1` contract (ADR-001). There is no shared database schema, no
server-side session for the mobile app (Clerk JWT on every request), and no queue or worker: planning runs inside the
request, the ingestion pipeline is a CLI, and retention is a CLI sweep.

Key invariants:

- **Authorization before work.** Ownership is checked before retrieval, model or provider calls. Account IDs, contact
  data and precise location never leave the server (BR-046).
- **Deterministic code owns decisions.** Domain, scheduling, validation and authorization live in code. Models propose
  IDs or write cited text; code validates both. Distances and durations come only from the routing provider.
- **Default deny for provider data.** Persistence is allowed only under an ACTIVE provider policy (ADR-006); DRAFT
  policies exist only in development/test/demo.
- **Quota degrades, never fails.** Every provider call passes the quota ledger; over a cap the request falls back
  (cheaper model, rule-based selection, null rationale) instead of failing silently.
- **Save is explicit.** A preview is a draft with revisions; only `POST /v1/plan-previews/{id}/accept` creates or
  updates a saved trip (ADR-009).

## 4. Backend — `apps/api`

### 4.1 Layering and import rules

`import-linter` (configured in `apps/api/pyproject.toml`) enforces the layering:

```text
api  →  planning / guide / trips / catalog / curation / research
planning → routing, ai, agents (only orchestrator)
agents → ai, config
catalog / curation / ingestion → never agents or AI output at runtime
solver → pure: no DB, AI, HTTP, routing
models / schemas / db / security / observability → never api
```

Provider SDKs live only in their adapter (`ai/providers.py`, `research/tavily.py`, `routing/google_routes.py`, …).

### 4.2 Folder and file roles

```text
apps/api/app/
├── main.py                     create_app(): middleware, error envelopes, routers, startup checks
├── config.py                   Settings (all GONARRA_* env vars), environment gates, quota caps
├── cli.py                      Typer entry point: seed, db-check, deletion jobs, caches, routes, pipeline groups
├── errors.py                   AppError and the {error:{code,message,retryable,request_id,context}} envelope
├── observability.py            request ids, structured failure logs without prompts/locations/tokens
├── api/
│   ├── router.py               mounts health + all /v1 routers
│   ├── sse.py                  ProgressSink, SSE framing, heartbeats, disconnect handling
│   ├── input_guard.py          rejects NUL (U+0000) in path/query/body with 422
│   └── routes/
│       ├── health.py           /health, /ready
│       ├── identity.py         GET /v1/me (Clerk subject → account)
│       ├── preferences.py      GET/PUT /v1/me/preferences
│       ├── deletion.py         POST/GET /v1/me/deletion
│       ├── catalog.py          cities, categories, place search, place card
│       ├── trips.py            trips CRUD, place card, handoff links, stay prices (flag)
│       ├── previews.py         plan previews: create (SSE or JSON), read, edit, discard, regenerate, accept
│       ├── guide.py            Guide sessions, messages, ask (SSE or JSON)
│       └── admin.py            operator-only unpublish + city summary
├── ai/
│   ├── providers.py            Role → model chain, ModelSpec, provider_configured()
│   ├── quota.py                quota ledger, per-account and global buckets, budgets per operation
│   ├── redaction.py            removes account ids, contact data, precise coordinates; DTOs for prompts
│   └── invocations.py          stored invocation metadata (purpose, model, outcome, tokens; never prompts)
├── agents/                     the only place an Agno Agent is built (agno pinned)
│   ├── runtime.py              AgentRunner, instructions loading, retry/timeout, context
│   ├── selector.py             PLACE_SELECTOR: ranks a pool of published IDs, no tools
│   ├── researcher.py           RESEARCHER: Tavily search, page fetch, Places existence check
│   ├── writer.py               GROUNDED_WRITER: rationales, Guide answers (cited evidence only)
│   ├── schemas.py              Pydantic output models (selection, rationale, Guide answer, research)
│   └── validators.py           domain validation: unknown IDs/fields are failures
├── planning/
│   ├── orchestrator.py         propose_trip / regenerate_day: the deterministic stage runner
│   ├── workflows.py            PlanningWorkflow protocol, commands, FastAPI dependency
│   ├── pool.py                 published, non-area places + localized names/descriptions/rules
│   ├── rule_selector.py        pre-ranking, diversity, per-day caps, fallback selection
│   ├── assemble.py             day frames, locker, schedule input, attach conflicts, health_plan
│   ├── leg_modes.py            car-free zones → WALK; restricted pairs
│   ├── health.py               Plan Health evaluation in code
│   ├── calendar/               lunar dates, closure rules, effective opening windows
│   └── solver/                 OR-Tools model (model.py) and solve loop (solve.py)
├── routing/
│   ├── provider.py             select_provider(), LatLng, haversine, UNAVAILABLE semantics
│   ├── google_routes.py        Google Routes adapter (TRAFFIC_UNAWARE only, ADR-018)
│   ├── estimate.py             demo-only straight-line estimate (never staging/production)
│   ├── matrix.py               leg matrix assembly
│   ├── matrix_cache.py         Routes cache, used only under an ACTIVE policy
│   ├── anchors.py              city anchors used as matrix endpoints
│   └── warm.py                 `routes warm` pre-computation
├── guide/
│   ├── service.py              ask pipeline: validate → quota → retrieve → answer → persist → SSE
│   ├── retrieval.py            entity → lexical → vector hybrid retrieval, rank fusion
│   ├── evidence.py             evidence units supplied to the writer
│   ├── answer.py               citation verification, compose, insufficient_evidence
│   ├── embedding.py            query/corpus embeddings behind the ledger
│   ├── repository.py           evidence reads (facts, chunks, places)
│   └── store.py                sessions, messages, citations, unit of work
├── research/
│   ├── tavily.py               search adapter
│   ├── fetch.py                page fetch with SSRF guard
│   ├── extract.py              text extraction
│   ├── places_check.py         Google Places existence/status check (field mask limited)
│   ├── candidates_repo.py      web_place_candidates persistence
│   ├── toolbox.py              the researcher's tool surface
│   └── store.py                research run bookkeeping
├── catalog/
│   ├── places.py               place card assembly, sources, description origin
│   ├── search.py               accent-insensitive search, category/area filters, cursor paging
│   ├── normalize.py            name/description normalisation
│   ├── preferences.py          travel preferences repository
│   └── reference.py            cities, categories, areas
├── curation/                   publishing is code, never a model
│   ├── auto_publish.py         the publication gate (rules, description priority, AI restoration path)
│   ├── identity.py             dedupe/identity of a place across providers
│   ├── dedupe.py               duplicate detection
│   ├── names.py                localized names and EN fallback
│   ├── overrides.py            owner overrides
│   ├── facts.py                fact records with provenance
│   ├── chunks.py               knowledge chunks + embeddings on write
│   ├── city_chunks.py          city-level Guide chunks
│   ├── closure_rules.py        calendar rules from data/closure_rules/*.yaml
│   ├── web_promotion.py        web candidates → catalog candidates (never published directly)
│   ├── operator.py             operator actions (unpublish)
│   └── audit_sample.py         random audit CSV (measurement, not review)
├── ingestion/                  Typer CLI importers, one module per provider
│   ├── cli.py                  ingest/publish/pipeline command groups
│   ├── wikidata.py             Wikidata items in the Đà Nẵng bbox (parts, classes)
│   ├── wikidata_link.py        links staged places to Wikidata items
│   ├── wikipedia.py            extracts, page images
│   ├── osm.py                  Overpass import (tags, names, opening_hours)
│   ├── wikivoyage.py           listings and descriptions (CC BY-SA 4.0)
│   ├── commons.py              Wikimedia Commons images and licences
│   ├── sheet.py                owner sheet (curated descriptions/facts)
│   ├── areas.py                travel-area polygons
│   ├── calendar.py             closure-rule YAML loader
│   ├── categories.py           category mapping
│   ├── policies.py             provider policy activation
│   └── common.py               staging records, runs, revisions
├── trips/
│   ├── service.py              trip/preview read, edit, accept (Save), regenerate plumbing
│   ├── snapshot.py             plan snapshot model, snapshot edit, saved-trip health re-evaluation
│   ├── repository.py           persistence, revisions, locks
│   ├── render.py               locale rendering of stored plans
│   ├── idempotency.py          Idempotency-Key claims, replay, conflict codes
│   ├── measure.py              leg measurement (Routes) for edits
│   ├── handoff.py              Agoda/Booking.com/Klook/12Go deep links
│   ├── assumptions.py          stable assumption keys
│   └── deletion.py             account deletion request + purge jobs
├── security/
│   ├── clerk.py                JWT verification, demo shared user
│   ├── clerk_backend.py        Clerk user deletion after purge
│   └── curator.py              operator allow-list
├── models/                     SQLAlchemy tables (account, catalog, knowledge, planning, providers, guide, caches…)
├── schemas/                    Pydantic request/response models (mirror openapi.yaml)
├── repositories/               account lookups
└── db/                         engine/session, base, types, retention sweep
```

### 4.3 HTTP surface

All application routes are under `/v1`; `/health` and `/ready` are unversioned. Mutating planning calls accept an
optional `Idempotency-Key`; Save requires one. SSE is used when the client sends `Accept: text/event-stream`.

| Area | Endpoint | Notes |
|---|---|---|
| Ops | `GET /health`, `GET /ready` | readiness checks the DB |
| Identity | `GET /v1/me` | Clerk `sub` mapped to an account |
| Preferences | `GET/PUT /v1/me/preferences` | structured planner input whenever the user wants it |
| Deletion | `POST/GET /v1/me/deletion` | demo shared account answers `409 demo_account_not_deletable` |
| Catalog | `GET /v1/cities`, `/v1/categories`, `/v1/places`, `/v1/places/{id}` | public reads (a token, if sent, must be valid) |
| Trips | `GET/POST /v1/trips`, `GET/PATCH/DELETE /v1/trips/{id}` | optimistic `revision` |
| | `GET /v1/trips/{id}/stops/{stop}/place-card` | on-site card for a saved stop |
| | `GET /v1/trips/{id}/handoff-links` | booking partner link |
| | `GET /v1/trips/{id}/stay-prices` | 501 unless the Could-scope flag is on |
| Planning | `POST /v1/trips/{id}/plan-previews` | SSE (`progress` …, `preview_ready`) or JSON |
| | `GET/PATCH/DELETE /v1/plan-previews/{id}` | head or `?revision=`; edit has no AI/routing call |
| | `POST …/regenerate` | single-day regeneration, SSE or JSON |
| | `POST …/accept` | explicit Save, required `Idempotency-Key`, blocks on WARNING conflicts |
| Guide | `POST /v1/ai/sessions`, `GET/DELETE …/{id}`, `GET …/messages` | city or place scope, 30-day retention |
| | `POST /v1/ai/sessions/{id}/messages` | SSE `text` deltas then `result`, or JSON |
| Admin | `POST /v1/admin/places/{id}/unpublish`, `GET /v1/admin/cities/summary` | operator allow-list only |
| Planned | photo identification, study timing events | contract stubs; not part of the Must flow |

Error handling: one JSON envelope for every failure, request id always present, NUL characters → 422, unexpected
exceptions → `500 internal_error` without exception text, SQL parameters hidden.

### 4.4 Data model (main groups)

| Group | Tables | Purpose |
|---|---|---|
| Accounts | `accounts`, `account_deletions` | internal ID, Clerk subject, purge jobs |
| Reference | `cities`, `areas`, `categories`, `fact_fields` | Đà Nẵng, travel areas, category taxonomy |
| Staging | `import_runs`, `import_records`, `source_revisions` | every provider import with provenance |
| Catalog | `places`, `place_localizations`, `place_facts`, `media_assets`, `catalog_publications` | published places, localized text, cited facts, images |
| Providers | `data_providers`, `provider_policies`, `external_place_identities`, `web_place_candidates` | default-deny persistence, web candidates |
| Knowledge | `knowledge_facts`, `knowledge_chunks`, `knowledge_chunk_sources` | Guide evidence; facts never live in chunks |
| Planning | `trips`, `plan_previews`, `preview_revisions`, `idempotency_keys` | drafts, revisions, replay safety |
| Guide | `guide_sessions`, `guide_messages`, `guide_citations` | sessions and cited answers |
| Caches | `routes_cache`, `tavily_cache`, retrieval caches | retention-swept, never user data |
| AI | `ai_invocations` | model, purpose, outcome, tokens; never prompts |

`schema.sql` is generated from migrations, never edited by hand. Migrations are additive and never renumbered.

## 5. Mobile — `apps/mobile`

Expo Router file routes under `src/app`, screens composed from `src/features`. All data comes from the API; there is no
offline or demo dataset.

### 5.1 Routes

| Route | Screen | Notes |
|---|---|---|
| `index.tsx` | start/redirect | first-run → onboarding, signed out → welcome |
| `onboarding.tsx` | onboarding | seen flag in secure storage |
| `(auth)/welcome`, `login`, `register`, `sso-callback`, `auth-task` | Clerk auth | Clerk components + custom UI |
| `(tabs)/home`, `explore`, `guide`, `trips` | main tabs | |
| `place/[placeId]` | place card | public read; sources, description credit, "No description yet" |
| `plan/new` | planner wizard | dates, pace, interests, must-sees, free text |
| `plan/[previewId]/index` → `proposal` | generation progress → proposal | SSE progress, then timeline + map + Plan Health |
| `plan/[previewId]/health` | Plan Health detail | aggregated conflicts, calendar rules |
| `trip/[tripId]/today` | Today | saved itinerary for the current date |
| `trip/[tripId]/book` | booking handoff | modal, partner deep link |
| `profile`, `settings`, `edit-profile`, `language`, `travel-preferences`, `delete-account` | account | |

### 5.2 Data layer (`src/lib/api`)

| File | Role |
|---|---|
| `config.ts` | `EXPO_PUBLIC_API_URL` (required; no fallback) |
| `client.ts` | typed fetch wrapper: Clerk bearer, `X-Request-ID`, `Accept-Language`, `Idempotency-Key` |
| `auth.ts` + `ApiAuthBridge.tsx` | bridges the Clerk session token into the plain-function client |
| `sse.ts` | WHATWG SSE parser over `expo/fetch` (POST body + headers; EventSource cannot) |
| `streams.ts` | typed planning and Guide streams, terminal-event handling, forward-compatible skipping |
| `source.ts` | catalog, trips, Guide session reads and planning start |
| `sourcePlanning.ts` | preview head, edit ops, regenerate, picker search |
| `sourceTrips.ts` | Save (accept), handoff link, trip deletion, stay prices |
| `sourceAccount.ts` | preferences, account deletion |
| `types.ts` | app-facing domain aliases over generated contract types |
| `schema.d.ts` | generated from `openapi.yaml` (`npm run gen:api`) |
| `errors.ts` | `ApiError` with the server error envelope |

### 5.3 UI building blocks

| Folder | Contents |
|---|---|
| `src/theme` | colors, spacing, typography, elevation |
| `src/i18n` | i18next setup; `locales/en` and `locales/vi` are complete key-for-key |
| `src/components/ui` + `brand` | buttons, sheets, icons, brand mark |
| `src/features/home` | map, clustering, search, city switcher, home sheet sections |
| `src/features/explore` | category browse, debounced search, place cards |
| `src/features/place` | place screen, gallery, facts, sources, description credit |
| `src/features/planner/input` | wizard, calendar range, must-see picker, draft store |
| `src/features/planner/progress` | stage progress screen and error copy |
| `src/features/planner/timeline` | timeline, day tabs, stop cards, leg rows, assumptions, Save bar |
| `src/features/planner/map` | proposal map |
| `src/features/planner/edit` | edit ops, pending-edit draft store, sheets, regenerate day |
| `src/features/planner/health` | status pill and detail screen |
| `src/features/planner/picker` | add/replace place picker |
| `src/features/save` | Save sheet, idempotent Save hook, acknowledgement step |
| `src/features/today` | today's stops from a saved trip |
| `src/features/guide` | chat, evidence bubbles, place picker, session cache |
| `src/features/trips` | saved trip list and cards |
| `src/features/handoff` | partner sheets and link building |
| `src/features/account` | account context, preferences, deletion UI |

## 6. End-to-end flows

### 6.1 App start

1. `src/app/_layout.tsx` loads fonts, requires `EXPO_PUBLIC_API_URL` (else config-error screen), wraps the app in
   `ClerkProvider`, `ApiAuthBridge`, `AccountProvider` and `SelectedCityProvider`.
2. `AccountProvider` waits for Clerk, calls `GET /v1/me` when signed in, and exposes the account.
3. Guests reach Home, Explore and place cards. Planning, Guide, trips and account screens are guarded by
   `Stack.Protected` and `SignInGate`.
4. In demo builds (`EXPO_PUBLIC_DEMO_NO_AUTH=1` + API `GONARRA_DEMO_SHARED_USER=1`) requests without a token are
   served as one shared account; the flag is refused outside development/test/demo.

### 6.2 Home, search and place card

1. `usePlaces` loads `GET /v1/cities` and `GET /v1/places` (paged to the bound) once per city/category/area/locale and
   shares the in-flight promise across Home, its map and Explore (2-minute TTL).
2. Explore adds `GET /v1/categories`, debounced `GET /v1/places?q=…` (300 ms, accent-insensitive on the server) and
   category filters. Everything refetches on a language switch.
3. Tapping a place opens `place/[placeId]` → `GET /v1/places/{id}`: localized name and description, facts with
   sources, `description_source` credit (Wikivoyage CC BY-SA 4.0, Wikipedia, owner sheet) and the
   `WEB_UNVERIFIED` badge when applicable. A place without a description shows "No description yet" / "Chưa có mô tả".
   Areas (`is_area`) are map/Guide objects: "Add to trip" is disabled.
4. "Plan a trip" carries the place as a must-see into the planner.

### 6.3 Creating a proposal (the main flow)

```mermaid
sequenceDiagram
  participant M as Mobile
  participant A as API
  participant O as Orchestrator
  participant S as Selector LLM
  participant R as Routing
  participant T as OR-Tools
  participant H as Plan Health
  participant W as Writer LLM

  M->>A: POST /v1/trips/{id}/plan-previews (SSE)
  A->>O: ProposeTripCommand
  O->>O: VALIDATING_REQUEST (owner, revision, quota, idempotency)
  O->>O: SELECTING_PLACES (rule pre-rank)
  O->>S: re-rank published IDs
  S-->>O: ranked IDs (validated)
  O->>R: one leg matrix (Google Routes / demo estimate / none)
  O->>T: one multi-day model (dates, windows, locks, modes)
  O->>H: CHECKING_HEALTH in code
  O->>W: rationales from supplied text (nullable)
  O->>A: persist ACTIVE preview revision 1
  O-->>M: progress… then preview_ready
```

Stages and their failure behaviour:

| Stage | What happens | If it fails |
|---|---|---|
| `VALIDATING_REQUEST` | ownership before any model/provider call; expected revision; preferences; quota; idempotency claim | typed terminal `error` |
| `SELECTING_PLACES` | pool = published, non-area Đà Nẵng places (plus this request's `WEB_UNVERIFIED` candidates); rule selector pre-ranks; `PLACE_SELECTOR` re-ranks under quota | rule-based selection, `model_version` marks it |
| `RESEARCHING` | only when `GONARRA_RESEARCH_ENABLED` and the pool is thin, with a hard timeout; `RESEARCHER` uses Tavily, page fetch and Places check; candidates are stored, labelled `WEB_UNVERIFIED`, never schedulable without coordinates | plan proceeds; `RESEARCH_SKIPPED` assumption |
| `ROUTING` | one matrix over pool + day anchor; Google Routes (`TRAFFIC_UNAWARE`), demo estimate (labelled) or none | legs `UNAVAILABLE`; estimate carries `LEG_ESTIMATED` |
| `SCHEDULING` | one OR-Tools model assigns days, order and times; per-day pace caps (RELAXED 4 / BALANCED 6 / PACKED 8), category variety, must-sees, locks, car-free → WALK, ticket grouping | a place is dropped with a typed reason; `STOPS_LEFT_OUT` |
| `CHECKING_HEALTH` | opening windows, weekly/monthly closures, lunar dates, Tết, ticket validity, travel legs, stale facts, must-see missing | never blocks generation |
| `WRITING` | `GROUNDED_WRITER` writes short rationales from supplied description/area/category/time-of-day; `null` when no key/quota | null rationale |
| persist | ACTIVE preview, revision 1, 24-hour TTL, `preview_ready` event | terminal `error` |

The mobile `GenerationProgressScreen` renders `progress` events by stage. A dropped stream is not reconnected: the
client shows the error copy and can open the persisted preview when its id is known.

### 6.4 Editing a proposal

1. The timeline sends an op list (move, add, remove, replace, retime, day mode) to `PATCH /v1/plan-previews/{id}` with
   `base_revision` and an `Idempotency-Key`.
2. The server re-applies the snapshot edit, re-measures changed legs (Routes), re-times sequentially, recomputes Plan
   Health and returns a new revision. **No AI, no solver** on a manual edit.
3. Until the answer arrives the edit stays in `draftStore` (pending, saved, conflict, expired). A
   `revision_conflict` returns the current revision instead of overwriting; expired/closed previews are terminal.
4. "Regenerate day" is the only edit that runs the planner again (`POST …/regenerate`), with locks and mode
   restrictions preserved; it also streams.
5. Plan Health conflicts are rendered from server data (localized on the client); the client never computes times,
   distances or health.

### 6.5 Save (explicit)

1. `SaveBar` opens the Save sheet and `useSaveTrip` sends `POST /v1/plan-previews/{id}/accept` with the preview
   revision and a fresh `Idempotency-Key`.
2. The server validates ownership and revision, copies the preview into the trip (new revision), copies effective
   preferences and the snapshot, and returns the trip detail.
3. WARNING-or-worse conflicts block the save until acknowledged; `web_unverified_acknowledgement_required` (OQ-128)
   opens the acknowledgement step; a retry with the same key replays the stored 200
   (`Idempotent-Replayed: true`) instead of double-saving.
4. A late provider result or a failed request never overwrites a saved trip or unsaved edits (ADR-009).

### 6.6 Saved trip, Today and booking handoff

1. Home's "next trip" and the Trips tab read `GET /v1/trips` / `GET /v1/trips/{id}`; the snapshot is rendered in the
   request locale.
2. Today derives the current date's stops; a saved trip is read-only apart from explicit trip updates.
3. The stop place card is served by `GET /v1/trips/{id}/stops/{stop}/place-card` so on-site content stays tied to the
   saved revision.
4. "Book" builds the partner handoff link server-side (`/handoff-links`) and opens Agoda, Booking.com, Klook or 12Go.
   Indicative stay prices are a flag-gated, never-stored Could-scope stub.

### 6.7 Guide

```mermaid
sequenceDiagram
  participant M as Mobile
  participant A as API
  participant G as Guide service
  participant DB as PostgreSQL
  participant W as Grounded writer

  M->>A: POST /v1/ai/sessions (city or place)
  M->>A: POST /v1/ai/sessions/{id}/messages (SSE)
  A->>G: AskCommand
  G->>G: VALIDATING (owner, quota reservation, store message)
  G->>DB: RETRIEVING (place evidence, or entity → lexical → vector)
  alt no evidence
    G-->>M: INSUFFICIENT_EVIDENCE (no model call)
  else evidence
    G->>W: answer from supplied evidence only
    W-->>G: answer + citations
    G->>G: re-validate every citation
    G->>DB: store answer + citations
    G-->>M: text deltas … result
  end
```

- City scope retrieves over approved facts and chunks; place scope pins one place's evidence.
- Facts never live in chunks; every citation must point to supplied evidence, otherwise the answer is
  `insufficient_evidence`.
- Questions, answers and prompts are never logged; logs carry counts and codes.
- Sessions expire after `GONARRA_GUIDE_SESSION_TTL_DAYS` (30); an expired session answers 404.
- The deterministic `WEB_UNVERIFIED` web fallback is designed but not built; nothing unlabelled is ever shown.

### 6.8 Catalog pipeline (ingestion → publication)

Operator-run CLI, no queue:

```text
pipeline run
  areas load                 travel-area polygons
  ingest wikidata            items in the Đà Nẵng bbox, with parts and classes
  ingest wikidata-link       link staged places to items
  ingest wikipedia           extracts + page images
  ingest osm                 Overpass tags, names, opening_hours
  ingest wikivoyage          listings/descriptions (throttled: the API rate-limits)
  ingest commons             images + licences
  ingest sheet               owner sheet (curated descriptions and facts)
  web-candidates promote     web candidates → catalog candidates
  publish auto               the gate; embeds chunks on write
  closure-rules load         calendar rules from data/closure_rules/da-nang.yaml
  caches sweep               retention
```

Publication is code (DEC-022, DEC-031), never a model:

- A place needs a staged record with a source revision, an editorial source, a category, an area, a locale-valid name,
  a licence for shown content, a source for every KNOWN fact, and must pass `fn_publication_gate_violations`.
- FOOD, CAFE and NIGHTLIFE are curated-only (owner sheet, Wikivoyage listing or Wikidata item); an OSM restaurant alone
  is not a recommendation.
- Descriptions come only from the owner sheet, Wikivoyage or Wikipedia, in each locale. A description shorter than
  `MIN_DESCRIPTION_CHARS = 80` is a stub and counts as absent. With `REQUIRE_DESCRIPTION = False` (DEC-033 option A)
  a place publishes without one and the card says "No description yet".
- Wikidata classes marking an area (bay, peninsula, mountain range, old town…) publish with `is_area = true`: on the
  map and in the Guide, never a planner stop.
- Retired AI providers (`gonarra_ai_summary`, `gonarra_ai_facts`) stay as an audit trail only. `publish auto
  --allow-ai-content` is the documented restore path and requires an ACTIVE policy; it is off in the pipeline.
- `publish summary` prints the release-gate counts; `publish audit-sample` exports a random 10 % CSV for the owner's
  reported accuracy measurement (not a review).

### 6.9 Account deletion

1. The app calls `POST /v1/me/deletion`; the API creates a deletion job and immediately blocks new work for the account.
2. A job purges trips, previews, Guide sessions/messages, preferences and account rows, then deletes the Clerk user
   through the Backend API when `GONARRA_CLERK_SECRET_KEY` is set (a warning otherwise).
3. `GET /v1/me/deletion` reports progress; `python -m app.cli run-deletion-jobs` completes or retries jobs.
4. The shared demo account cannot be deleted (`409 demo_account_not_deletable`, demo builds only).

### 6.10 Operate

- `adminUnpublishPlace` removes a place from the catalog immediately (emergency use); the audit trail stays.
- `adminGetCitySummary` reports published/Hội An/food counts for the release gate.
- `python -m app.cli caches sweep` applies retention to provider caches.
- `python -m app.cli routes warm` pre-computes a Routes matrix.

## 7. Configuration

### 7.1 API (`apps/api/.env`, prefix `GONARRA_`)

| Variable | Default | Meaning |
|---|---|---|
| `GONARRA_ENVIRONMENT` | `production` | `development` / `test` / `demo` / `staging` / `production`; gates estimates, DRAFT policies, demo user and `/docs` |
| `GONARRA_DATABASE_URL` | local Postgres | SQLAlchemy URL; driver is `psycopg`, not `asyncpg` |
| `GONARRA_CLERK_ISSUER`, `_JWKS_URL`, `_AUDIENCE`, `_AUTHORIZED_PARTIES` | unset | JWT verification (JWKS derived from issuer) |
| `GONARRA_CLERK_SECRET_KEY` | unset | Clerk Backend API, used only to delete the Clerk user after a purge |
| `GONARRA_CURATOR_CLERK_USER_IDS` | empty | operator allow-list for `/v1/admin` (empty = nobody) |
| `GONARRA_DEMO_SHARED_USER` | `false` | one shared account for token-less requests; refused outside development/test/demo |
| `GONARRA_GEMINI_API_KEY`, `_GROQ_API_KEY`, `_TAVILY_API_KEY`, `_GOOGLE_MAPS_API_KEY` | unset | provider keys; server-side only |
| `GONARRA_RESEARCH_ENABLED` | `false` | research agent on thin pools (alias `..._RESEARCH_AGENT_ENABLED`) |
| `GONARRA_RESEARCH_TIMEOUT_S` | `45` | hard timeout; the plan proceeds on timeout |
| `GONARRA_ROUTES_PROVIDER` | `auto` | `auto` / `google` / `estimate` / `none` |
| `GONARRA_ROUTES_ESTIMATE_ENABLED` | `false` | demo estimate; refused in staging/production |
| `GONARRA_STAY_PRICES_ENABLED` | `false` | Could-scope prices, never stored |
| `GONARRA_QUOTA_*` | free-tier caps | per-account/day, global/day, Tavily/month, Routes elements/day |
| `GONARRA_DEFAULT_CITY_CODE` | `da-nang` | product scope |
| `GONARRA_GUIDE_SESSION_TTL_DAYS` | `30` | Guide retention |
| `GONARRA_MEDIA_BASE_URL` | local | prefix for catalog media |

`infra/dev.env` holds the committed development defaults; `docker compose` reads it and then `apps/api/.env` as an
override. Secrets never enter the mobile bundle.

### 7.2 Mobile (`apps/mobile/.env.local`)

| Variable | Required | Meaning |
|---|---|---|
| `EXPO_PUBLIC_API_URL` | yes | API origin, no trailing `/v1`; LAN IP for a phone; inlined at build time |
| `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` | yes | from `npx clerk env pull` |
| `EXPO_PUBLIC_DEMO_NO_AUTH` | no | demo mode; requires the API demo user, set both or neither |

Demo mode without Google Maps uses the estimate router; legs are labelled `≈` and `estimated`.

## 8. Commands

### API (`apps/api`)

```bash
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
uv run python -m app.cli db-check
uv run python -m app.cli seed                 # reference data (cities, categories, fact fields)
uv run python -m app.cli seed --demo-catalog  # only for local demo data

uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run lint-imports
uv run pytest -q
uv run python scripts/export_openapi.py --check
```

Integration tests (real PostgreSQL, never the dev DB):

```bash
cd /path/to/fyp_dana
docker compose up -d db --wait
docker compose exec -T db createdb -U gonarra gonarra_test
cd apps/api
GONARRA_DATABASE_URL=postgresql+psycopg://gonarra:gonarra@localhost:5432/gonarra_test uv run alembic upgrade head
GONARRA_DATABASE_URL=postgresql+psycopg://gonarra:gonarra@localhost:5432/gonarra_test uv run python -m app.cli seed
GONARRA_DATABASE_URL=postgresql+psycopg://gonarra:gonarra@localhost:5432/gonarra_test uv run pytest -m integration
```

The database name must end `_test`, `_it` or `_ci`; the guard refuses anything else. AI evals (real providers) run
nightly only: `uv run pytest -m eval`.

### Data pipeline (`apps/api`)

```bash
uv run python -m app.cli pipeline run
uv run python -m app.cli publish summary
uv run python -m app.cli publish audit-sample
uv run python -m app.cli caches sweep
uv run python -m app.cli routes warm --limit 50
```

### Mobile (`apps/mobile`)

```bash
npm ci
npm run gen:api            # regenerate schema.d.ts (contract changed)
npm run typecheck
npm run check:dependencies
npm start                  # Expo Go
npm run ios                # native development build
```

### Docs

- links resolve, IDs unique;
- `apps/api/openapi.json` matches the app (`export_openapi.py --check`);
- `docs/04-design/data/schema.sql` applies on a fresh PostGIS/pgvector container.

## 9. Deployment and operations

Production is one VM (docker-compose.prod.yml, ADR-002; final host OQ-129):

| Service | Role |
|---|---|
| `db` | PostgreSQL 16 + PostGIS + pgvector, no published port, healthcheck |
| `migrate` | one-shot `alembic upgrade head` before every API start |
| `api` | the FastAPI image, bound to the backend network |
| `caddy` | automatic HTTPS in front of the API |
| `backup` | nightly `pg_dump`, 14-day retention, restored per `infra/README.md` |

```bash
cp infra/.env.example .env && chmod 600 .env
GONARRA_API_TAG=$(git rev-parse --short HEAD) docker compose -f docker-compose.prod.yml up -d --build --wait
curl -fsS https://<GONARRA_API_HOST>/ready
```

Images build for arm64 and amd64. First deploy, updates, rollback, restore and logs: `infra/README.md`.

Operational rules: environment defaults to `production` (fails safe); demo flags and DRAFT policies are refused in
staging/production; `/docs` is off outside development; logs never carry tokens, precise locations, user questions,
transcripts or full prompts; `caches sweep` enforces retention.

## 10. Where to change what

| Change | Files |
|---|---|
| New/modified HTTP field or endpoint | `apps/api/app/schemas/*`, `api/routes/*`, `docs/04-design/api/openapi.yaml`, `openapi.json`, mobile `schema.d.ts` + `types.ts` |
| Planner ranking or fallback | `planning/pool.py`, `planning/rule_selector.py`, `agents/selector.py`, `agents/validators.py` |
| Scheduling, timing, modes | `planning/solver/`, `planning/leg_modes.py`, `planning/assemble.py`, ADR-011 |
| Plan Health rule | `planning/health.py`, `planning/calendar/`, `planning/snapshot.py`, `apps/mobile/src/features/planner/health` |
| Edit/Save semantics | `trips/service.py`, `trips/snapshot.py`, `trips/idempotency.py`, `features/planner/edit`, `features/save` |
| Guide retrieval / citations | `guide/`, `curation/city_chunks.py`, `curation/chunks.py`, `docs/04-design/adr/ADR-010` |
| Publication gate | `curation/auto_publish.py`, `apps/api/data/README.md`, DEC-022/DEC-031 |
| Import a new source | `ingestion/<source>.py`, `ingestion/cli.py`, `ingestion/policies.py`, `source_revisions` |
| Calendar rules | `apps/api/data/closure_rules/da-nang.yaml`, `ingestion/calendar.py`, `curation/closure_rules.py` |
| Copy or a new screen | `apps/mobile/src/features/…`, `src/app/…`, both `locales` files |
| Clerk/app identity | `apps/mobile/.env.local`, API Clerk settings; never change slug, scheme, bundle IDs without a naming decision |

## 11. Invariants that are easy to break

1. No AI-written catalog content: descriptions, facts, hours, prices and names come from cited human sources (DEC-031).
   AI writes only rationales and Guide answers, from supplied evidence.
2. Unknown stays unknown; never invent a value, a distance or a duration.
3. Routes is the only source of distance/duration; estimates exist only in demo builds and are labelled.
4. Published places only, and never an area, in the planner pool. Unknown IDs are validation failures.
5. Ownership before retrieval/model/provider; all provider calls pass the quota ledger and redactor.
6. Save is explicit, revisioned and idempotent; failures never overwrite saved data.
7. VI and EN are complete, equal locales; a missing translation is a defect, not a fallback.
8. IDs (DEC, OQ, ASM, RSK, ADR, requirements, tests) are never renumbered; withdraw or supersede instead.
9. When code and contract differ, update the contract in the same change.
10. Never claim provider, device, cloud or bilingual-content behaviour was verified when only mocks or static checks ran.

## 12. Built vs. not built (2026-11-09)

| Area | Status |
|---|---|
| Catalog + search + place card + sources | built; 173 published places, 63 Hội An |
| Planner proposal, timeline, map, Plan Health, edit, regenerate day | built |
| Explicit Save, trips, Today, handoff links | built |
| City/place Guide with citations and `insufficient_evidence` | built; web fallback planned |
| Account deletion and purge jobs | built (Clerk user deletion needs the secret key) |
| Research agent | built, flag-gated, runs only on thin pools |
| Voice (on-device STT/TTS), photo identification within 300 m | planned (Should) |
| Indicative stay prices | contract stub behind a flag (Could) |
| Android native map | deferred (OQ-135) |
| Hà Nội, TP.HCM, Huế | roadmap |
