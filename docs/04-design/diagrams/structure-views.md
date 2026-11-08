# Gonarra Structure Views — Logical, Development and Physical

| Field | Value |
|---|---|
| Document ID | GONARRA-STRUCT |
| Version | 2.0 (0.1–0.2 five-city text at git tag `docs-sdlc-full`) |
| Date | 2026-11-09 |
| Owner | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor — **[Pending]** |
| Inputs | [SAD](../architecture/SAD.md) 2.0, [data model](../data/data-model.md) 2.0, Alembic head `20261108_0009`, `apps/api/app/`, `apps/mobile/src/` |

The Mermaid previews below describe the current architecture. `logical-view.drawio`, `development-view.drawio` and `physical-view.drawio` date from 2026-11-04 (five cities, curator admin SPA, AWS-only) and are stale until redrawn; see the [diagram index](README.md).

## 1. Logical view

Main entities by owning module (tables in the [data model](../data/data-model.md); `created_at`/`updated_at`, junction tables and caches omitted).

```mermaid
classDiagram
  direction LR
  class City { code = da-nang; boundary }
  class Area { code; boundary }
  class Place { workflow_state; location; visit_minutes }
  class PlaceLocalization { locale; name; description; translation_origin; name_is_source_fallback }
  class PlaceFact { field_code; knowledge_state; value; verified_at; origin; grounding }
  class SourceRevision { locator; retrieved_at; content_sha256 }
  class CatalogPublication { publication_revision; state }
  class KnowledgeChunk { scope; locale; section; embedding[768] }
  class PlaceClosureRule { rule_kind; effect; severity; params }
  class WebPlaceCandidate { name; places_check_outcome; review_state }
  class Account { clerk_user_id }
  class Trip { day_count; status; revision }
  class TripStop { trust_level; ordinal; is_locked }
  class RouteLeg { travel_mode; availability; distance_m; duration_s }
  class PlanPreview { head_revision; status }
  class PreviewRevision { origin; plan_health; snapshot }
  class GuideSession { place_id nullable = city scope }
  class GuideMessage { role; answer_status }
  City "1" o-- "*" Area
  City "1" o-- "*" Place
  Place "1" *-- "*" PlaceLocalization
  Place "1" *-- "*" PlaceFact
  PlaceFact "*" --> "1..*" SourceRevision : evidence
  Place "1" --> "*" CatalogPublication
  CatalogPublication "*" --> "*" PlaceFact : pins
  Place "1" *-- "*" KnowledgeChunk
  PlaceClosureRule "*" --> "0..1" Place
  WebPlaceCandidate "*" --> "0..1" Place : promoted_place
  Account "1" *-- "*" Trip
  Trip "1" *-- "*" TripStop
  TripStop "*" --> "0..1" CatalogPublication : VERIFIED
  TripStop "*" --> "0..1" WebPlaceCandidate : WEB_UNVERIFIED
  TripStop "1" -- "*" RouteLeg
  Trip "1" *-- "*" PlanPreview
  PlanPreview "1" *-- "*" PreviewRevision
  Account "1" *-- "*" GuideSession
  GuideSession "1" *-- "*" GuideMessage
```

Rules shown by the model: a `TripStop` references either a publication (`VERIFIED`) or a web candidate (`WEB_UNVERIFIED`), never both; facts are pinned by a publication; publications and source revisions are immutable; `PlaceFact.grounding` exists only for `origin = AI_EXTRACTED` (DEC-028). Operations on entities are the database functions `fn_publication_gate_violations`, `fn_publish_place`, `fn_withdraw_place` and the Save transaction (ADR-009).

## 2. Development view

```mermaid
flowchart LR
  subgraph mob["apps/mobile (Expo, Expo Router)"]
    screens["screens: home, explore, plan, trip, place, guide, settings"]
    client["lib/api: generated types, SSE client"]
    i18n["i18n (VI/EN)"]
    screens --> client
    screens --> i18n
  end
  subgraph api["apps/api (FastAPI modular monolith)"]
    routes["api/routes + sse"]
    sec["security (Clerk, operator allow-list, demo user)"]
    trips["trips"]
    plan["planning.orchestrator"]
    solver["planning.solver + calendar + health"]
    routing["routing (google | estimate | none)"]
    guide["guide (service, retrieval)"]
    agents["agents (selector, researcher, grounded_writer)"]
    ai["ai (providers, quota, redaction, invocations)"]
    research["research (tavily, fetch, places_check, enrich, fact_extract)"]
    catalog["catalog"]
    cur["curation (auto_publish, web_promotion, operator)"]
    ing["ingestion (wikidata, osm, wikipedia, commons, sheet, closure rules)"]
    cli["cli (Typer)"]
    routes --> sec & trips & plan & guide & catalog & cur
    plan --> solver & routing & agents & research & catalog
    guide --> agents & catalog
    agents --> ai
    research --> ai
    cli --> ing & cur & research & routing
  end
  db[("PostgreSQL 16 + PostGIS + pgvector")]
  client -->|"/v1 REST + SSE"| routes
  trips & plan & guide & catalog & cur & ing --> db
```

Dependency rules enforced by `import-linter` are listed in [SAD §2](../architecture/SAD.md#2-deployables-and-modules). Agno is imported only in `agents/` and `ai/`. The curator admin SPA (CMP-002) is withdrawn (DEC-022). Voice (CMP-021) and photo capture (CMP-022) are planned mobile components.

## 3. Physical view

Hosting is open: [ADR-002](../adr/ADR-002-aws-ec2-rds-hosting.md) (AWS EC2 + RDS) stays the default on paper, and OQ-129 decides before M2, with one VM running Docker Compose as the recommendation for the study.

```mermaid
flowchart LR
  phone["iPhone (Expo build)<br/>apps/mobile · Apple Maps"]
  subgraph local["Today: developer workstation"]
    subgraph dc["Docker Compose"]
      api["api :8000<br/>FastAPI + Typer CLI"]
      db[("db :5432<br/>PostGIS + pgvector (infra/postgres)")]
    end
  end
  subgraph vm["Study host (OQ-129): one VM, Docker Compose"]
    caddy["Caddy TLS (planned)"]
    api2["api container + CLI on a timer"]
    db2[("PostgreSQL (container, or RDS under ADR-002)")]
  end
  subgraph ext["External services"]
    clerk["Clerk"]; gem["Gemini"]; groq["Groq"]; tav["Tavily"]; od["Wikidata · OSM · Wikipedia · Commons"]; rt["Google Routes (optional) / Valhalla (planned)"]
  end
  partners["Agoda · Booking.com · Klook · 12Go"]
  gha["GitHub Actions CI<br/>lint, types, tests, OpenAPI drift, migrations, arm64 + amd64 images"]
  phone -->|HTTPS| caddy --> api2 --> db2
  phone -.->|dev| api --> db
  api & api2 --> clerk & gem & groq & tav & od & rt
  phone --> clerk & partners
  gha -.->|images| vm
```

| Node | Notes |
|---|---|
| Traveler phone | iPhone-first demo with Apple Maps; Android map deferred (OQ-135) |
| Compose `api` | Python 3.12 image, multi-arch (arm64, amd64); the same image runs the CLI (pipeline, publication gate, deletion jobs, `routes warm`) |
| Compose `db` | PostgreSQL 16 with PostGIS, pgvector, pg_trgm, pgcrypto |
| Caddy | TLS and SSE pass-through on the hosted VM (planned) |
| External | Server-side keys only; no Google Maps Platform in the demo (DEC-023) |
| Recovery | Single host, no DR site; RPO 24 h, RTO 4 h from backups and image rebuild |
