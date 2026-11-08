# Software Development Plan — Gonarra

| Field | Value |
|---|---|
| Version / date | 2.0 / 2026-11-09 |
| Owner | Lê Ngọc Tấn Hiền |
| Approver | FYP mentor — [Pending] |
| Scope | Đà Nẵng-only FYP release, including the Hội An area (DEC-013); other cities are roadmap |
| History | 2.0 replaces the ISO/IEC/IEEE 24748-5 plan 0.1 of 2026-11-04 (five cities, WBS and task cards), kept at git tag `docs-sdlc-full`. Decisions, open questions and risks live in [`docs/decisions.md`](../decisions.md); verification in [`TEST_PLAN.md`](../07-verification/TEST_PLAN.md) |

## 1. Purpose and baseline

This plan says how Gonarra is built and delivered for the FYP: life cycle, milestones and gates, cut order, team
and working agreements, tooling and CI, and configuration management. It does not restate scope or design.

| Topic | Source of truth |
|---|---|
| Scope, priorities, business rules | [BRD](../02-requirements/BRD.md), [PRD](../03-analysis/PRD.md), [user stories](../03-analysis/user-stories.md) |
| Decisions, open questions, assumptions, risks | [`docs/decisions.md`](../decisions.md) |
| Architecture and binding ADRs | [SAD](../04-design/architecture/SAD.md), [ADRs](../04-design/adr/) |
| Contracts | [`openapi.yaml`](../04-design/api/openapi.yaml), [`schema.sql`](../04-design/data/schema.sql) |
| Verification | [Master test plan](../07-verification/TEST_PLAN.md), [research protocol](../07-verification/RESEARCH_PROTOCOL.md) |
| Day-to-day state and evidence | `progress.md` and `plan.md` at the repository root (local working files, not versioned) |

If code must differ from a contract, the contract is updated in the same change.

## 2. Life cycle

Incremental delivery in short waves against fixed milestones. Each wave is a set of tasks with disjoint file
ownership, executed in parallel, reviewed, and merged through one pull request to `main`. A milestone closes only
when its exit evidence exists; anything verified only with mocks or static checks is reported as such.

The submission date is assumed to be **2027-02-01** (ASM-002, OQ-002). Scope freezes on **2027-01-15**.

## 3. Milestones and gates

| ID | Window | Exit evidence (gate) | Status 2026-11-09 |
|---|---|---|---|
| M0 | 2026-11-06 → 11-20 | Docs condensed and re-baselined (DEC-021, DEC-029) and merged; mentor signs DEC-013, DEC-015, DEC-022..025 (OQ-131..133). `agno==3.1.12` pinned | Docs condensation in progress; mentor sign-off pending |
| M1 | 2026-11-16 → 12-08 | SPK-004: researcher agent on 10 Đà Nẵng prompts with real keys (latency, quota use, `WEB_UNVERIFIED` precision) → research trigger threshold (OQ-127). Catalog pipeline producing ≥ 15 auto-published places a week (ASM-004 rev. 1) | SPK-004 partial (model pins replaced, DEC-026); threshold not set |
| M2 | 2026-12-09 → 12-22 | Foundation: pure-ASGI middleware + SSE helper; Alembic migrations from `schema.sql` + seed; `app/ai` (providers, quota ledger, redactor); catalog repositories and search; automated ingestion and publication gate (DEC-022, DEC-024); mobile wired to `/v1` | Code landed early (migrations to `0009`); CI green on the merged PRs |
| M3 | 2026-12-23 → 2027-01-05 | Planner: selector + validator + rule-based fallback; researcher and existence check; routing (Google Routes, or estimates outside staging/production, DEC-023); OR-Tools multi-day solver; Plan Health incl. calendar and web conflicts; writer; `propose_trip` / `regenerate_day` over SSE; edit + explicit Save. HA-02 passes in the Hội An area | Pieces in code; owner-reported live smoke 2026-11-08 (DEC-026); readiness blockers open (first Save of a new trip, deletion not wired in the app) |
| M4 | 2027-01-06 → 01-15 | Guide (city-level retrieval, citation validation, labelled web fallback); place card with trust label and closure rules; handoff links; account deletion end to end. Catalog gate MET-011 rev. 3 met. Eval harness: golden sets, `score_itinerary.py`, nightly `pytest -m eval` | City-level Guide in code without web fallback; eval harness not started |
| M5 | 2027-01-06 → 01-15 (parallel) | Should/Could: lock + day regeneration, voice, photo identification, indicative prices — cut in order if late (§4) | Not started (regeneration endpoint exists) |
| M6 | 2027-01-16 → 01-31 | Acceptance run per the test plan; comparative user study (DEC-020, MET-014); test summary report | Not started; depends on OQ-004 |
| M7 | 2027-02-01 | FYP report and submission | — |

Gate rules:

- A gate is passed only with stored evidence (CI run, test output, recorded run or study data). Missing evidence = not passed.
- The mentor confirms decisions at the next gate; approval rows stay `[Pending]` until signed.
- Slip handling: if a milestone slips by more than 3 days, apply the cut order (§4) before moving any date.

### 3.1 Open readiness items (2026-11-09)

From the read-only readiness review recorded in `progress.md`; each becomes a task in the next wave.

- Blockers: the first Save of a new trip fails with 409 (the app sends trip revision 1; new trips start at 0);
  account deletion is not wired in the app.
- Catalog: lists fetch only the first page of places; no FOOD, CAFE, MARKET, NIGHTLIFE or CRAFT_VILLAGE place is
  published; some AI-written descriptions are wrong and some places are duplicated (RSK-107, RSK-108).
- Mobile: Wikimedia refuses the Android HTTP client's user agent (photos); Plan Health messages are English only.
- API: database engine logging must not print bound parameters; a NUL byte in a query returns a plain-text 500; the
  Compose file forces `development`.
- `apps/admin` is not built. DEC-022 removed the review UI; the operator uses the `/v1/admin` endpoints (unpublish,
  city summary) and the CLI. Whether an operator SPA is still needed is open.
- Demo mode (`GONARRA_DEMO_SHARED_USER`, `EXPO_PUBLIC_DEMO_NO_AUTH`) exists for owner demos only; it needs a decision
  entry if kept past the demo.

## 4. Cut order (DEC-003 rev. 1)

If late, cut in this order: **indicative prices → photo identification → voice → lock/regeneration → iOS build**
(keep Android). Never cut **bilingual content**, the **Đà Nẵng catalog gate** (≥ 100 published bilingual places,
≥ 30 in the Hội An area) or **explicit Save**. A cut is recorded in `docs/decisions.md` with the approver's agreement
and the feature is disabled, not left half-working. The demo-only iPhone-first map (DEC-023, OQ-135) does not change
this order.

## 5. Team and working agreements

| Role | Who | Responsibility |
|---|---|---|
| Owner, product owner, operator, study lead | Lê Ngọc Tấn Hiền | Scope, priorities, catalog operation (unpublish, CSV sheet, closure-rule YAML), merges, study |
| Approver | FYP mentor | Confirms decisions and signs gates |
| Coordinator | Main AI session | Plans waves, writes task briefs, reviews results, keeps docs and `progress.md` current |
| Implementers | Opus 5.5 subagents at medium effort | Code (`apps/*`), CI, scripts, spikes and delegated docs, in parallel with disjoint file ownership (git worktrees when needed) |

- Owner's standing delegation: when the owner says "best choice", the coordinator decides and records the decision
  in `docs/decisions.md`; the mentor confirms at the gate. Agents draft; they never approve.
- Each task brief names the files the agent owns, the source documents, and the exit checks. An agent preserves
  unrelated changes and touches only its files.
- Every handoff states what changed, which checks ran, passed or were not run, new decisions or risks, and the
  `progress.md` update. Provider, device, cloud or bilingual-content behaviour is never claimed as verified when only
  mocks or static checks ran.
- Hard rules from the architecture apply to every change: domain, scheduling, validation and authorization logic stay
  out of prompts; all AI output is validated with Pydantic and domain rules; models never publish places or invent
  facts, hours, prices, distances or durations; no account IDs, contact data or precise location reach any provider
  (BR-046); every provider call goes through the quota ledger.

## 6. Tooling and CI

| Area | Tools |
|---|---|
| API | Python 3.12, `uv`, FastAPI, SQLAlchemy 2 async, Alembic, Typer CLI (`python -m app.cli`), Agno 3.1.12, OR-Tools; `ruff`, `mypy --strict`, `import-linter`, `pytest` (+ `pytest-asyncio`, `pytest-httpx`) |
| Mobile | Expo SDK 58, React Native, TypeScript, Expo Router, Clerk, i18next; `tsc --noEmit`, `expo install --check`; API types generated from `openapi.yaml` with `npm run gen:api`; native builds with `npm run android` / `npm run ios` (needed for on-device STT) |
| Database | PostgreSQL 16 + PostGIS + pgvector in Docker Compose (`docker compose up -d db --wait`) |
| AI and data providers | Gemini, Groq, Tavily (free tiers, DEC-018); Google Routes optional (DEC-023); open data: Wikidata, OSM, Wikipedia, Wikimedia Commons (DEC-024) |
| CI | GitHub Actions `.github/workflows/ci.yml` on every pull request and push to `main` |

CI jobs:

- **api**: `uv sync --locked --all-groups` → `ruff check .` → `mypy app` → `lint-imports` → `pytest` →
  `export_openapi.py --check` → start the Compose database → `alembic upgrade head` → `python -m app.cli seed` →
  `pytest -m integration` → `alembic downgrade base && alembic upgrade head` → Docker image build for arm64 and amd64.
- **mobile**: `npm ci` → `npm run typecheck` → `npm run check:dependencies`.
- **AI evals** (`pytest -m eval`, real providers) run nightly or on dispatch only, never per push (planned, M4).

## 7. Configuration management

- **Branches.** `main` is the protected integration branch. Work happens on short-lived branches named by type —
  `feat/…`, `fix/…`, `docs/…`, `chore/…` — and is merged by pull request after CI passes and the owner reviews.
  Commit messages follow the `type(scope): summary` convention (e.g. `feat(api): …`, `docs: …`).
- **Pull requests.** One wave or one coherent change per PR. The PR states the checks run, what was not verified, and
  any contract or decision change. Contract changes (`openapi.yaml`, `schema.sql`, ADRs) ship in the same PR as the
  code that needs them; `apps/api/openapi.json` is regenerated and checked by CI.
- **Migrations.** Alembic revisions in `apps/api/migrations/versions/` named `YYYYMMDD_NNNN_<topic>.py`, hand-written
  from `docs/04-design/data/schema.sql` (never an unedited `--autogenerate`). Each revision must upgrade and downgrade
  cleanly; CI runs the round trip on a fresh database. `schema.sql` is updated in the same change.
- **IDs and documents.** IDs (BR, FR, NFR, MET, DEC, OQ, ASM, RSK, ADR, TC, VT) are never renumbered or reused; a
  changed item is revised ("rev. 1"), withdrawn or superseded. Documents carry a version and date; superseded sets are
  kept at git tags (`docs-sdlc-full` holds the 2026-11-04/05 SDLC set).
- **Secrets and environments.** Provider keys, database URL and Clerk secrets live only in `apps/api/.env` (never
  committed) and server-side configuration. `GONARRA_ENVIRONMENT` selects `development`, `test`, `demo`, `staging`
  or `production`; estimate routing and the shared demo user are refused in `staging` and `production`.
- **Naming.** Gonarra is a working name: app name, slug, URL scheme, bundle IDs, deep links and hostnames do not
  change without a naming decision.

## 8. Risks

The live risk register is in [`docs/decisions.md`](../decisions.md) §4. The risks that most affect this plan:

| ID | Risk | Response in this plan |
|---|---|---|
| RSK-001 rev. 1 | Too few places pass the automated gate (≥ 100 / ≥ 30 Hội An area) | Weekly count; < 10 a week for two weeks triggers the cut order; never cut the gate |
| RSK-013 | Free quotas exhausted before or during the study | Quota ledger and fallback chains; study sessions over ≥ 2 days; reserved Tavily credits |
| RSK-012 | Web-found places are wrong | `WEB_UNVERIFIED` label, WARNING cap, research behind a flag (OQ-128) |
| RSK-105 | No human review weakens the "verified" claim | "Source-checked" copy; audit sample (DEC-025); mentor decision OQ-131 |
| RSK-106 | Estimated legs make demo schedules infeasible | Estimates only outside staging/production; measured router for acceptance and study (OQ-132) |
| RSK-107 | AI-summarised descriptions contain unsupported statements | Grounded writer, citation validation, 10% audit sample (OQ-133) |
| RSK-014 | Agno API churn | Exact pin; imports confined to `app/agents/` and `app/ai/` |
| Schedule | One-person team, fixed deadline | Waves of parallel subagents; scope freeze 2027-01-15; cut order |

Open hosting choice (AWS EC2 + RDS per ADR-002 or one VM with Docker Compose) is OQ-129; the study assumes one VM.

## 9. Deferred (after the FYP)

- Hà Nội, TP. Hồ Chí Minh, Huế and further cities (DEC-013), once Đà Nẵng meets the gate.
- In-app booking or payment, flights, social features, multi-city trips, check-in or GPS arrival, audio tours,
  turn-by-turn navigation (DEC-004).
- Gemini Live and other cloud speech; voice stays on-device (ADR-007).
