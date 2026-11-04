# Master Test Plan — Gonarra

## Document control

| Field | Value |
|---|---|
| Test plan identifier | TP-GONARRA-v0.1 (document ID GONARRA-TEST-PLAN) |
| Version | 0.1 |
| Status | Draft |
| Classification | Internal (FYP) |
| Owner | Lê Ngọc Tấn Hiền, student author, product owner and test lead |
| Approver | trantrongminh, FYP mentor (full name pending, OQ-001) — [Pending] |
| Date | 2026-11-04 |
| Tested commit / release | TBD per release. Each run records its commit SHA and build IDs under `docs/07-verification/evidence/<run-id>/` (owner Lê Ngọc Tấn Hiền; first run M2, by 2026-12-22). Baseline at writing: `main` @ `5d0e397` (documentation baseline; no product feature beyond identity/health implemented) |
| Prompt used | `verification/TestPlan_IEEE 829-2008_prompt.md` v2.0, adapted copy `docs/00-governance/prompt-templates/verification/TestPlan_IEEE 829-2008_prompt.md` (kit commit `6996dae`) |
| Companion documents | `TEST_CASES.md` (TC-001..TC-265), `RTM.md`, `RESEARCH_PROTOCOL.md` |

| Version | Date | Author | Change summary |
|---|---|---|---|
| 0.1 | 2026-11-04 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | First IEEE 829 master test plan for the study release candidate; replaces pre-rebuild `TESTING.md` (in git history) |

Parameters used (adapted prompt §2.2): levels unit, integration, contract (OpenAPI), system/E2E (Maestro), acceptance,
usability study; environments local Docker, GitHub Actions CI, AWS staging; data synthetic + fixtures + frozen
evaluation sets (ASM-011); coverage target 100% of Must acceptance criteria covered by at least one executed case;
risk tier Medium.

---

## 0. Input analysis (kit §7.1)

### 0.1 Input document inventory

| Document type | Document | Version | Source | Key information used |
|---|---|---|---|---|
| BRD | `docs/02-requirements/BRD.md` | 0.4 | Owner (SRC-100) | BR-001..BR-050, AC-0nn, MET-001..MET-013, ASM-010, ASM-011, SC-01..SC-03, RSK-002, OQ-004, OQ-006 |
| PRD (SRS) | `docs/03-analysis/PRD.md` | 0.2 | Owner | 97 FR, 38 NFR with metric/threshold/method, §9 V&V methods, §11.2 HA-02, §11.3 RC-01..RC-08 |
| User stories | `docs/03-analysis/user-stories.md` | 0.2 | Owner | 43 stories, 127 Given/When/Then criteria (93 Must, 30 Should, 4 Could) |
| Traceability | `docs/03-analysis/traceability.md` | 0.2 | Owner | BO → BR → FR/NFR → US; extended to UC/API/TC in `RTM.md` |
| SAD (IEEE 1016) | `docs/04-design/architecture/SAD.md` | 0.1 | Owner | CMP-001..CMP-024, QAS-01..QAS-15 quality scenarios, interfaces I-001..I-009 |
| Use cases | `docs/04-design/use-cases.md` | 0.1 | Owner | UC-001..UC-022 |
| API design | `docs/04-design/api/openapi.yaml`, `api-contract.md` | 0.1 | Owner | API-001..API-042 (`x-api-id`, `x-fr`), error envelope, Idempotency-Key, 409/410/422 semantics |
| Data design | `docs/04-design/data/data-model.md`, `schema.sql` | 0.1 | Owner | Publication workflow, explicit Save transaction (§6.2), deletion cascade (§3.2), study tables (§2.7), backups (§10.1) |
| UI/UX | `docs/04-design/ui-ux/README.md`, `wireframes/*.html` | 0.1 | Owner | Screen inventory for bilingual and accessibility inspection, WCAG 2.1 AA tokens |
| Development plan | `docs/05-development/` (SDP, WBS) | — | Phase 5 (in progress in parallel) | Not yet available; schedule here aligned to milestones M1–M6 of `plan.md`. Re-align when the SDP is approved (OQ-116) |
| Existing tests and CI | `apps/api/tests/**`, `.github/workflows/ci.yml` | `5d0e397` | Code | 9 pytest tests (health, identity, Clerk verifier, account mapping); CI jobs `api` (ruff, mypy, pytest, OpenAPI drift, migrations up/down, multi-arch image) and `mobile` (typecheck, dependency check) |
| Risk tier / obligations | BRD §9–§10, PRD §3.5 | — | Owner | Risk tier Medium; obligations: consent for the study (OQ-004), data-protection rules (OQ-008), free-tier AI terms (RSK-002), licences (BR-047) |

Missing or ambiguous inputs: the SDP/WBS (phase 5, parallel); the staging environment is required by PRD §7 but the
SAD physical view has no staging node (OQ-110); ethics/consent requirement (OQ-004, open).

### 0.2 Requirements extracted (summary)

| Requirement set | Count | Must | Should | Could | Where tested |
|---|---|---|---|---|---|
| Business requirements BR | 50 | 40 | 7 | 3 | `RTM.md` §2 |
| BRD acceptance criteria AC-0nn | 50 | 40 | 7 | 3 | Acceptance cases, `RTM.md` §3.2 |
| Functional requirements FR | 97 | 70 | 23 | 4 | `RTM.md` §7 |
| Non-functional requirements NFR | 38 | 31 | 7 | 0 | §6.1.6–§6.1.9 here, TC-222..TC-259 |
| User-story criteria US-nnn-ACn | 127 | 93 | 30 | 4 | One case per criterion at least, `RTM.md` §3.1 |
| Business metrics MET | 13 | — | — | — | §7 pass/fail criteria |

The full requirement list with IDs is not repeated here; `RTM.md` is generated from the source tables.

### 0.3 Design elements to verify (IEEE 1016 views)

| Design view | Element | Interfaces | States / rules to exercise | Test level |
|---|---|---|---|---|
| Composition | `apps/api` modules identity, catalog, trips, planning, routing, guide, stays, curation (CMP-004..CMP-013) | HTTP `/v1` | Module boundaries, no model-created data | Unit, integration |
| Component & connector | AI gateway (CMP-012), routing adapter (CMP-009), provider adapters (CMP-013) | I-002 Gemini, I-003 Routes, I-004 Places, I-005 LiteAPI | Typed inputs only; failure handling; no identity in payloads | Integration with recorded fixtures and fault injection |
| Interaction | Proposal → edit → Save (ADR-009); Guide RAG (ADR-010) | SSE streams | Preview revisions, idempotent Save, stale-revision 409 | Integration, E2E |
| Information | `schema.sql` (40 tables) | Alembic migrations | Publication gate, deletion cascade, idempotency records, study logs | Integration (DB), inspection |
| Interface | OpenAPI 3.1, 42 operations | REST + SSE | Schemas, error envelope, auth | Contract |
| State dynamics | Place (CANDIDATE → PUBLISHED → UNPUBLISHED), preview (ACTIVE/DISCARDED/expired), deletion job | — | Valid/invalid transitions | Integration |

### 0.4 UI/UX elements to verify

| UI area | Screens | Interactions | States | Accessibility | Flow |
|---|---|---|---|---|---|
| Explore | City select, search, place details | Search, open details | Loading, empty, error, unknown/stale fact | Labels, contrast, 200% font | SC-02 |
| Planner | Request (text/form), clarification, proposal timeline + map, edit sheet, Plan Health | Submit, reorder, add, remove, replace, duration, mode, Save | Progress, unsaved, blocked, recalculating (Save disabled), conflict | Plan Health reasons announced | SC-01, HA-02 |
| On site | Place card, Today, directions | Show to driver, open maps | Address/entrance unknown | Large text | SC-02 |
| Guide | Question, answer with sources, voice, read-aloud | Ask, Send, play | Streaming, insufficient evidence, permission denied | Live region for streamed answer | SC-02 |
| Handoff | Find a stay / activities / transport, prices | Open partner | Prices hidden with message | — | SC-03 |
| Account | Sign-in, settings, language, deletion | Delete with confirmation | In progress, completed, failed | — | — |
| Curator tool | Candidates, review, publish, coverage | Edit, confirm AI draft, publish, unpublish | Refusal naming missing items | Desktop Chrome | — |

### 0.5 API elements

All 42 operations (API-001..API-042) are listed with their FRs and named cases in `RTM.md` §5. Auth: Clerk JWT RS256
on every `/v1` operation except `/health` and `/ready`; curator role claim on `/v1/admin/*`. Errors use the envelope
`{ "error": { code, message, retryable, request_id, context } }`.

### 0.6 User stories

127 criteria from 43 stories; each is mapped to cases in `RTM.md` §3.1. Must stories: 30; Should: 12; Could: 1.

### 0.7 Risk assessment (testing view)

Scores are likelihood × impact (1–5 each). IDs `TR-xx` are local to this plan; project risks keep their BRD `RSK-` IDs.

| ID | Risk | L | I | Score | Mitigation / test response |
|---|---|---|---|---|---|
| TR-01 | Saved trip or unsaved edits lost under provider/network failure (MET-006) | 3 | 5 | 15 | Failure-injection matrix §6.3, run each release candidate; P0 cases TC-096..TC-120 |
| TR-02 | Cross-traveler data disclosure (MET-010) or identity sent to AI (BR-046) | 2 | 5 | 10 | Permission cases for every private resource; payload capture and unit test; log canary scan |
| TR-03 | Model output adds unknown/other-city places or facts (AC-006, BRU-002) | 3 | 5 | 15 | Injection fixtures, schema validation unit tests, golden set |
| TR-04 | Conflict missed and infeasible plan saved (MET-004) | 3 | 4 | 12 | Conflict set EVS-CONF ≥ 20; deterministic Plan Health unit tests |
| TR-05 | Guide answers unsupported claims (MET-007/008) | 3 | 4 | 12 | EVS-GUIDE claim-to-source review, EVS-OOC refusal set, prompt-injection case |
| TR-06 | Catalog < 30 places per city at release (MET-011, RSK-001) | 4 | 5 | 20 | Weekly coverage check (US-008, API-042); acceptance entry criterion; test fixtures do not depend on real catalog |
| TR-07 | Free-tier quotas exhausted by test runs (NFR-035) | 3 | 3 | 9 | Recorded fixtures for regression; live runs limited (OQ-114) |
| TR-08 | Evaluation sets tuned to after freeze (metrics not comparable) | 2 | 4 | 8 | Freeze 2026-12-08 with version tag and hash; changes create a new version, both results reported |
| TR-09 | One-person team: no independent review of test results | 4 | 3 | 12 | Mentor sample review (OQ-111); automated evidence; reproducibility check NFR-032 |
| TR-10 | No staging environment in the SAD (OQ-110) | 3 | 3 | 9 | Proposed separate Compose project and database on existing resources; confirm before M2 |
| TR-11 | Study cannot start without ethics/consent decision (OQ-004) | 3 | 5 | 15 | Protocol and consent drafted now; RC-08 gate; escalate on 2026-11-11 due date |
| TR-12 | Device/OS availability for NFR-027/028 (OQ-112) | 2 | 3 | 6 | Identify devices by 2026-12-15; emulator for smoke only |

Order of testing (highest risk first): TR-06 coverage tracking (weekly from M1), then TR-03 and TR-04 (planner
correctness, M3), TR-01 (failure injection, M3), TR-02 (privacy, M2–M4), TR-05 (Guide, M4), then usability (M6).

---

## 1.0 Test plan identifier (IEEE 829 cl. 5.1)

| Attribute | Value |
|---|---|
| Document ID | TP-GONARRA-v0.1 |
| Document version | 0.1 |
| Issue date | 2026-11-04 |
| Status | Draft |
| Classification | Internal (FYP) |
| Prepared by | Lê Ngọc Tấn Hiền |
| Approved by | trantrongminh — [Pending] |

## 2.0 Introduction (cl. 5.2)

### 2.1 Purpose

This master test plan defines how Gonarra — a bilingual (VI/EN) AI travel planner and grounded local assistant for
five Vietnamese cities — is verified for its study release candidate and evaluated in the user study. It sets the
test levels, approach, environments, data, entry and exit criteria, responsibilities and schedule, and provides
traceability from business requirements to test cases (`RTM.md`).

### 2.2 Scope

In scope:

- Functional testing of every Must, Should and Could FR of PRD 0.2 through its user-story criteria.
- Non-functional testing of all 38 NFRs: performance, reliability, security and privacy, usability and accessibility
  (WCAG 2.1 AA), localization, compatibility, maintainability, cost.
- API contract testing of all 42 operations of `openapi.yaml`.
- Evaluation-set acceptance runs for MET-004..MET-011 (§6.2).
- Failure injection for MET-006 (§6.3), security and privacy tests (§6.4), bilingual checks (§6.6).
- End-to-end reference journeys HA-02 and SC-01..SC-03.
- The user study for MET-001..MET-003 and MET-013 (`RESEARCH_PROTOCOL.md`).

Out of scope: see §5.0.

### 2.3 Objectives

| ID | Objective | Success criterion | Trace |
|---|---|---|---|
| OBJ-001 | Validate functional requirements | 100% of Must user-story criteria pass on the release candidate (RC-01) | US-nnn-ACn, FR-xxx |
| OBJ-002 | Validate API contracts | 0 schema violations across API-001..API-042; 0 OpenAPI drift (NFR-030) | API-001..API-042 |
| OBJ-003 | Validate trust properties | MET-004 = 100%, MET-006 = 0, MET-010 = 0, MET-007 ≥ 95%, MET-008 ≥ 90% (RC-05) | BR-008, BR-012, BR-020, BR-015, BR-038 |
| OBJ-004 | Validate accessibility | NFR-022..NFR-024 met on traveler screens (WCAG 2.1 SC 4.1.2, 1.4.3, 1.4.4) | BR-022 |
| OBJ-005 | Validate performance | NFR-001..NFR-007 thresholds on staging + device | BR-001, BR-005, BR-015, BR-023, BR-032 |
| OBJ-006 | Validate security and privacy | 0 accepted bad tokens (NFR-014), 0 secrets (NFR-016), 0 sensitive log items (NFR-017), 0 identity items to AI (AC-046) | BR-020, BR-046 |
| OBJ-007 | Validate bilingual delivery | 0 untranslated strings per language (AC-022); 0 corrupted diacritics (NFR-026) | BR-022 |
| OBJ-008 | Evaluate with users | MET-001 ≥ 80%, MET-002 ≤ 3 min, MET-003 ≥ 70, 10–15 participants with ≥ 4 per language | BR-005, BR-023, BR-045 |

### 2.4 References

| Document | Version | Source |
|---|---|---|
| Gonarra BRD | 0.4 | `docs/02-requirements/BRD.md` |
| Gonarra PRD | 0.2 | `docs/03-analysis/PRD.md` |
| User stories | 0.2 | `docs/03-analysis/user-stories.md` |
| SAD (IEEE 1016-2009) | 0.1 | `docs/04-design/architecture/SAD.md` |
| Use cases | 0.1 | `docs/04-design/use-cases.md` |
| API specification (OpenAPI 3.1) | 0.1 | `docs/04-design/api/openapi.yaml` |
| Data model | 0.1 | `docs/04-design/data/data-model.md` |
| UI/UX specification | 0.1 | `docs/04-design/ui-ux/README.md` |
| Roadmap (milestones M0–M7) | 2026-11-04 | `plan.md` (local, not versioned) |
| IEEE 829-2008 | 2008 | IEEE Standard for Software and System Test Documentation |
| WCAG 2.1 | 2018 | W3C Recommendation |

## 3.0 Test items (cl. 5.3)

### 3.1 Software items

| Item ID | Item | Version | Source | Status at writing |
|---|---|---|---|---|
| SI-001 | `apps/api` — FastAPI modular monolith (identity, catalog, trips, planning, routing, guide, stays, curation, study) | Commit per run | Owner | Foundation only (health, ready, `/v1/me`, Clerk verifier, migration 0001) |
| SI-002 | `apps/mobile` — Expo SDK 58 traveler app (Android; iOS unless cut) | EAS build ID per run | Owner | Onboarding and Clerk sign-in done; not wired to the API |
| SI-003 | `apps/admin` — React + Vite curator SPA | Build per run | Owner | Planned |
| SI-004 | Catalog ingestion CLI (Typer + DuckDB) inside `apps/api` | Commit per run | Owner | Planned |
| SI-005 | Database schema (`schema.sql` → Alembic 0002–0004) on PostgreSQL 16 + PostGIS + pgvector | Migration head per run | Owner | Designed; migration 0001 only |
| SI-006 | API contract `openapi.yaml` and generated `openapi.json` / TypeScript types | Commit per run | Owner | Designed |
| SI-007 | Deployment configuration (Docker Compose, Caddy, AWS EC2/RDS/S3/SSM) | Tag per run | Owner | Not started |
| SI-008 | Catalog content: published places per city (≥ 30 each) | Catalog report date | Owner (curator) | 0 published |

### 3.2 Test artifacts

| ID | Artifact | Format | Location |
|---|---|---|---|
| TA-001 | Test cases | Markdown | `docs/07-verification/TEST_CASES.md` |
| TA-002 | Fixtures (synthetic catalog, accounts, recorded provider responses) | JSON / SQL | `apps/api/tests/fixtures/` (proposed, Phase 5 task) |
| TA-003 | Evaluation sets EVS-* (frozen, versioned) | JSON / CSV / images | `apps/api/tests/evaluation/` (proposed); photos outside git if > 50 MB |
| TA-004 | Automated tests | pytest, Jest, Maestro YAML | `apps/api/tests`, `apps/mobile` |
| TA-005 | Fault-injection profiles | Config | Test-only provider adapters (§6.3) |
| TA-006 | Evidence and run records | Files | `docs/07-verification/evidence/<run-id>/` |
| TA-007 | Study materials | Markdown + printed forms | `RESEARCH_PROTOCOL.md`; signed forms kept offline |

## 4.0 Features to be tested (cl. 5.4)

### 4.1 Test priority matrix

| Priority | Feature | Stories | Requirements | Risk score |
|---|---|---|---|---|
| High | F-04 Explicit Save and failure safety | US-018, US-019 | BR-011, BR-012, BR-033; FR-040..FR-045 | 15 (TR-01) |
| High | F-03 Proposal from published places | US-010, US-012, US-013, US-038 | BR-005, BR-006; FR-020..FR-026, FR-085..FR-087 | 15 (TR-03) |
| High | F-11 Privacy and access control | US-032, US-033, US-035 | BR-020, BR-021, BR-044, BR-046 | 10 (TR-02) |
| High | F-02 Curation and publication gate | US-004..US-009 | BR-002, BR-004, BR-047 | 20 (TR-06, catalog) |
| High | F-05 Feasibility and Plan Health | US-014, US-015 | BR-007, BR-008, BR-009, BR-026 | 12 (TR-04) |
| High | F-08 Guide (text, grounded) | US-025, US-026 | BR-015, BR-038, BR-048 | 12 (TR-05) |
| Medium | F-06 Editing | US-016, US-017, US-039..US-041 | BR-010, BR-027..BR-032 | 9 |
| Medium | F-01 Search and place details | US-001..US-003 | BR-001, BR-003, BR-024, BR-025 | 9 |
| Medium | F-07 Place card and directions | US-022..US-024 | BR-014, BR-036, BR-037 | 8 |
| Medium | F-10 Booking handoff | US-029, US-030, US-037 | BR-018, BR-041, BR-042 | 6 |
| Medium | F-12 Language VI/EN | US-034 | BR-022 | 9 |
| Medium | F-13 Study support | US-036 | BR-023, BR-045 | 9 |
| Low (cuttable) | F-09 Lock and regeneration | US-021, US-042 | BR-013, BR-034, BR-035 | 6 |
| Low (cuttable) | F-14 Voice | US-027, US-043 | BR-016, BR-039 | 4 |
| Low (cuttable) | F-15 Photo identification | US-028 | BR-017, BR-040 | 4 |
| Low (cuttable) | F-16 Indicative prices | US-031 | BR-019, BR-043, BR-049 | 3 |

### 4.2 Feature test matrix

| Feature | Unit | Integration | Contract | System/E2E | Acceptance | Regression | Performance | Security | Accessibility | Study |
|---|---|---|---|---|---|---|---|---|---|---|
| F-01 Search and details | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| F-02 Curation | ✓ | ✓ | ✓ | ✓ (Chrome) | ✓ | ✓ | – | ✓ | – | – |
| F-03 Proposal | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F-04 Save and failure safety | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| F-05 Feasibility | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ |
| F-06 Editing | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F-07 Place card | – | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| F-08 Guide | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F-09 Lock/regeneration | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | optional |
| F-10 Handoff | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | ✓ |
| F-11 Privacy | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | – |
| F-12 Language | ✓ | ✓ | – | ✓ | ✓ | ✓ | – | – | ✓ | ✓ |
| F-13 Study support | – | ✓ | ✓ | – | ✓ | – | – | ✓ | – | ✓ |
| F-14 Voice | – | – | – | ✓ (device) | ✓ | – | – | ✓ | ✓ | optional |
| F-15 Photo | ✓ | ✓ | ✓ | ✓ (device) | ✓ | – | – | ✓ | – | – |
| F-16 Prices | ✓ | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | – | – |

### 4.3 Feature descriptions

Each feature's testable behaviours are its user-story criteria; the mapping to cases is in `TEST_CASES.md` (sections
1–17) and `RTM.md` §3. Reference journeys (HA-02, SC-01) are TC-215..TC-221.

## 5.0 Features not to be tested (cl. 5.5)

| ID | Feature / aspect | Reason | Risk | Future plan |
|---|---|---|---|---|
| NT-01 | In-app booking, payment, flights, social features, multi-city trips, check-in/GPS arrival, audio tours, runtime web search, turn-by-turn navigation | Won't in BRD §5.2 / DEC-004 | Low | Roadmap |
| NT-02 | Availability and correctness of third-party services (Gemini, Google Routes, Google Places, Clerk, LiteAPI, partner sites) | Vendor responsibility; only Gonarra's handling of their failures is tested (§6.3) | Medium | — |
| NT-03 | Booking partner flows after the deep link opens | Outside the product boundary (handoff only, DEC-002) | Low | — |
| NT-04 | Navigation quality inside Google/Apple Maps | Handoff only (FR-054) | Low | — |
| NT-05 | Load beyond 5 concurrent travelers; stress, soak and spike tests | Study scale only (ASM-015, NFR-007) | Low | After FYP |
| NT-06 | Formal penetration testing | No budget or independent team; replaced by the targeted checks in §6.4 | Medium | Before any public release |
| NT-07 | iOS device testing if iOS is cut (DEC-003 position 5) | Cut order | Low | Recorded as SKIP under RC-06 |
| NT-08 | Curator tool in browsers other than desktop Chrome | NFR-029 scope | Low | — |
| NT-09 | App-store distribution, push notifications, offline maps | Not in scope of BRD 0.4 | Low | — |
| NT-10 | Gemini Live realtime voice | Roadmap (plan.md) | Low | — |
| NT-11 | Factual accuracy of the real-world catalog content beyond the review sample | Curator responsibility (BR-004); sampled by AC-003 and MET-007 | Medium | Weekly curation review |
| NT-12 | NFR-018 deletion of study data after 2027-06-30 | Falls after submission; inspected on 2027-07-01, reported separately | Low | Post-study check |

## 6.0 Approach (cl. 5.6)

### 6.1 Test levels

#### 6.1.1 Unit

| Attribute | Description |
|---|---|
| Responsible | Lê Ngọc Tấn Hiền (AI coding agents may draft; owner reviews and merges) |
| Tools | pytest + pytest-asyncio (`apps/api`); Jest + React Native Testing Library (`apps/mobile`, proposed in Phase 5) |
| Coverage target | Line coverage reported in CI, not gated; every domain rule in planning, Plan Health, publication gate, payload builder and freshness has unit tests |
| Entry | Code compiles; ruff and mypy clean |
| Exit | All unit tests pass in CI |
| Focus | Pydantic validation of model output, Plan Health, staleness boundary, payload stripping (BR-046), i18n key parity |
| Mocking | All external services mocked; no network |

#### 6.1.2 Integration

| Attribute | Description |
|---|---|
| Responsible | Lê Ngọc Tấn Hiền |
| Tools | pytest `-m integration`, httpx AsyncClient, PostgreSQL 16 + PostGIS + pgvector in Docker Compose (as in CI) |
| Scope | API endpoints against a real database; provider adapters with recorded responses (FX-GEM, FX-RTE, FX-PLC, FX-PRC) and fault injection (§6.3) |
| Entry | Unit tests green; migrations apply (`alembic upgrade head`) |
| Exit | All integration cases of the increment pass |
| Focus | Ownership checks, publication workflow, Save idempotency and revision conflicts, deletion cascade, study log contents |

#### 6.1.3 Contract (OpenAPI)

| Attribute | Description |
|---|---|
| Tools | Existing `scripts/export_openapi.py --check` (code ↔ committed `openapi.json`); Schemathesis against `openapi.yaml` (proposed); `openapi-typescript` regeneration diff for the mobile and admin clients (NFR-030) |
| Scope | All 42 operations: request/response schemas, status codes, error envelope, auth requirements, Idempotency-Key |
| Entry | API runs locally with fixtures |
| Exit | 0 schema violations; 0 drift on every merge to `main` |

#### 6.1.4 System / E2E (Maestro)

| Attribute | Description |
|---|---|
| Tools | Maestro flows (`apps/mobile/.maestro/`, proposed) on an Android emulator in local runs; release runs on physical devices (NFR-027/028). Curator SPA: manual in Chrome (Playwright optional) |
| Scope | User-visible behaviour: labels, disabled Save while recalculating, map ↔ timeline sync, permissions prompts, language switching, journeys HA-02 and SC-01 |
| Entry | Integration green; build installed against staging; fixtures loaded |
| Exit | All P0 E2E cases pass on the release candidate |
| Note | Native modules (speech recognition, camera) need a development or EAS build, not Expo Go |

#### 6.1.5 Acceptance

| Attribute | Description |
|---|---|
| Responsible | Lê Ngọc Tấn Hiền runs; mentor reviews the report and signs exit (§16) |
| Tools | Evaluation runner over frozen sets (§6.2), inspection checklists, Maestro/device runs |
| Scope | BRD AC-0nn, MET-004..MET-012, PRD RC-01..RC-08, inspections (AC-003, AC-022, AC-047, NFR-013, NFR-022..NFR-026) |
| Entry | Acceptance entry criteria §7.2 |
| Exit | Exit criteria §7.3 |
| Provider mode | Each set is run with recorded responses (reproducibility, NFR-032) and once live on the release candidate; results reported separately (PRD §9) |

#### 6.1.6 Usability study

Defined in `RESEARCH_PROTOCOL.md`: 10–15 participants, at least 4 per language, sessions from mid-January 2027
(M6), tasks SC-01..SC-03 with optional HA-02 variant; measures MET-001..MET-003 and SUS. Requires RC-08 (OQ-004).

#### 6.1.7 Regression

| Suite | Scope | Trigger | Automation |
|---|---|---|---|
| REG-CI | All unit, integration and contract tests | Every pull request and push to `main` (existing CI jobs `api`, `mobile`) | Automated |
| REG-EVAL | EVS-* sets with recorded responses | Every merge touching planning, guide, catalog or routing; before each release candidate | Automated (runner) |
| REG-E2E | Maestro P0 flows (HA-02 steps 1, 2, 4, 5, 6; SC-01) | Before each release candidate and after any fix to a P0 defect | Automated on emulator; device run for RC |
| REG-SMOKE | `/health`, `/ready`, sign-in, search, open saved trip | After every staging deployment | Scripted |

#### 6.1.8 Performance

NFR-001..NFR-007 are measured on staging with a physical Android device on Wi-Fi/4G in Vietnam (client timing) and a
load script of 5 virtual travelers running HA-02 for 15 minutes (k6 or Locust, proposed). Thresholds are the PRD
values; none is lowered to pass.

#### 6.1.9 Security and privacy — see §6.4. Accessibility — see §6.5. Bilingual — see §6.6.

### 6.2 Golden and evaluation sets (ASM-011)

Sets are built by the owner from synthetic requests and questions written for the published catalog, frozen on
**2026-12-08** (ASM-011 due date), tagged `EVS-<name>-v1.0` with a content hash recorded in the run report, and never
tuned against after freezing. A change after freezing creates `v1.1`; results on both versions are reported.

| Set | Minimum size (ASM-011) | Composition | Used for | Cases |
|---|---|---|---|---|
| EVS-PLAN — golden planning set | ≥ 30 requests | ≥ 6 per city; each city has 1-, 2- and 3-day requests; VI and EN; with/without must-sees; some missing preferences | AC-005, AC-006, AC-007, AC-026, FR-026, NFR-002, NFR-003 | TC-058..TC-060, TC-070, TC-071, TC-223, TC-224 |
| EVS-CONF — conflict set | ≥ 20 scenarios | Closed-at-planned-time, day-window overrun, missing leg, overlap; each with expected flag target | AC-008 (MET-004), AC-009 | TC-072, TC-073 |
| EVS-REGEN — regeneration set | ≥ 10 trips | Multi-day saved trips with 0–2 locked stops | AC-013, AC-035 (MET-005) | TC-128, TC-129 |
| EVS-GUIDE — Guide answer sample | ≥ 50 questions | Questions answerable from reviewed sources, ≥ 5 per city, VI and EN | AC-015 (MET-007), AC-048, NFR-005, NFR-006 | TC-146, TC-147, TC-226, TC-227 |
| EVS-OOC — out-of-catalog set | ≥ 30 questions | Questions not supported by reviewed sources, incl. open-web-only facts; VI and EN | AC-038 (MET-008) | TC-145 |
| EVS-PHOTO — photo set | ≥ 100 photos | ≥ 20 per city of published places with capture location; plus 20 non-catalog photos | AC-017 (MET-009), AC-040 | TC-167, TC-168 |
| EVS-SEARCH — search set | 30 queries | 6 per city: 2 VI names, 2 EN names, 2 aliases (AC-001) | AC-001 | TC-011 |

Exact case IDs per set are authoritative in `RTM.md` §3.2. Photos are taken by the owner or taken from Wikimedia
Commons with licence recorded; no people identifiable in photos. Recorded provider responses (FX-GEM, FX-RTE) are
captured once per set version from staging and stored with the set.

### 6.3 Failure injection (MET-006)

Goal: prove that no saved itinerary changes without Save and no unsaved edit is lost when a provider or the network
fails (BR-012, BR-033, AC-012, AC-033, QAS-02), and that single-provider failures do not stop search, place cards
and saved trips (NFR-011, NFR-038).

Mechanism (to be implemented as Phase 5 tasks):

1. Provider adapters (Gemini, Routes, Places, LiteAPI, Clerk JWKS) are injected through FastAPI dependencies. In tests
   a fault-injecting adapter replaces them; on staging a fault profile is selected per request by a test-only header
   accepted only when `ENVIRONMENT=staging` and a staging secret is present. A unit test asserts the switch is inert in
   production configuration.
2. Fault types: HTTP 503, timeout, malformed/schema-invalid body, quota error (429), delayed response (late result
   arriving after a newer edit).
3. Network failures on the client: emulator/device airplane mode and dropped connection during SSE streams and Save.
4. Each run snapshots the saved itinerary (JSON of the trip at its revision) and the client's unsaved edits before
   injection and compares them after recovery.

Matrix per release candidate (3 runs per cell): failure {AI, Routes, network} × operation {generate, edit, Save,
regenerate if not cut} = 36 runs (27 if regeneration is cut). MET-006 = number of runs where the saved itinerary
changed without Save plus unsaved edits lost; pass = 0. Aggregate case TC-117; single-cell cases
TC-100..TC-103 and TC-112..TC-120; HA-02 step 4 TC-218.

### 6.4 Security and privacy tests

| Area | Requirement | Method | Cases (see RTM) |
|---|---|---|---|
| Cross-traveler access (BOLA) | MET-010, AC-020, FR-069, FR-095 | traveler-B requests every private resource type of traveler-A; external-call spy asserts 0 calls | TC-197 (acceptance) + per-resource permission cases (TC-094, TC-110, TC-140, TC-151, TC-178) |
| Authentication | NFR-014 | 4 credential cases (missing, invalid signature, expired, foreign issuer/party) × every private operation; builds on existing `test_identity_requires_authentication`, `test_verifier_rejects_unapproved_party` | TC-236 |
| Curator role | NFR-015 | Non-curator token on API-033..API-042 | TC-037, TC-237 |
| AI boundary | BR-046, AC-046, FR-070 | Unit test of the payload builder; capture of 20 real staging payloads (proposal, Guide, photo) inspected for account IDs, emails, phone numbers, coordinates | TC-198, TC-196, TC-169 |
| Logs | NFR-017, BRU-008 | Canary strings (token, coordinates, question text) planted in an HA-02 + Guide run; log search finds 0 | TC-239 |
| Secrets | NFR-016 | Secret scanner (gitleaks, proposed) on repository and release-candidate mobile/admin bundles | TC-238 |
| Transport and storage | NFR-012, NFR-013 | TLS scan of public hostnames; AWS configuration inspection | TC-234, TC-235 |
| Deletion | BR-021, BR-044, AC-021, AC-044 | Staging deletion with 24 h check of DB, Clerk and logs; restore drill re-applies deletion | US-033 cases |
| Prompt injection | FR-057 | Hostile question must yield grounded answer or `insufficient_evidence` | TC-149 |
| Quotas | NFR-036 | Cap + 1 requests | TC-258 |
| Study data | ASM-010, NFR-018 | Pseudonymous logs only; retention check 2027-07-01 | TC-202, TC-210..TC-212, TC-240 |

### 6.5 Accessibility (WCAG 2.1 AA)

Applies to the traveler app. Mandatory measured criteria are NFR-022 (SC 4.1.2 name/role/value), NFR-023 (SC 1.4.3
contrast ≥ 4.5:1, including the `textMuted` #5E7585 and `tealText` #00788F tokens planned in `plan.md`) and NFR-024
(SC 1.4.4 resize text, 200%). Additional AA checks recorded informatively on the same screens: SC 1.3.1 info and
relationships (Plan Health reasons exposed as text, not only colour), SC 1.4.1 use of colour, SC 2.4.3 focus order,
SC 3.3.1 error identification, SC 4.1.3 status messages (streamed Guide answer, recalculation state). Tools: Android
Accessibility Scanner and TalkBack; iOS Accessibility Inspector and VoiceOver (if iOS not cut); contrast checker on
screenshots. Each inspection is done in both languages. The curator tool is checked for contrast only.

### 6.6 Bilingual checks (VI/EN)

- Static: i18n key parity between `vi` and `en` resources and no empty values (TC-207), run in CI.
- Screen walk: every traveler screen in each language, 0 untranslated strings (AC-022, TC-209).
- Content: place details show the description in the selected language and both names (US-034-AC3, TC-208).
- Diacritics: 50-place sample and all VI screens (NFR-026).
- Behaviour: golden planning, Guide and out-of-catalog sets contain both languages; Guide answers are 100% in the
  selected language (AC-015); the AI notice appears in the selected language (TC-199).
- Times: shown in Vietnam local time whatever the device time zone (NFR-025).
- Study: ≥ 4 participants per language (BR-045, AC-045).
- Release gate: ≥ 30 published, reviewed, bilingual places per city (MET-011, RC-04).

Machine translation is not accepted as a pass: VI and EN content and UI strings are reviewed by the owner (native
Vietnamese) and checked by an English reader for the EN locale (OQ-111 covers the reviewer).

### 6.7 Automation vs manual

| Kind | Automated in CI | Automated, run on demand | Manual |
|---|---|---|---|
| Unit, integration, contract | ✓ (every PR) | — | — |
| Evaluation sets (recorded) | ✓ (planning/guide changes) | Live-provider runs per RC | Claim-to-source review (MET-007) |
| E2E | — | Maestro on emulator | Physical-device runs, voice, photo, maps handoff |
| Performance | — | Load script, timing harness | Device timing review |
| Security | Secret scan, auth tests | TLS scan | AWS configuration inspection |
| Accessibility, bilingual | Key parity | — | Screen inspections |
| Study | — | — | Sessions |

Of the 265 cases, the automation target is pytest/Jest/CI for 138, Maestro or the evaluation runner for 81, and manual
(inspection, device, study) for 46; the per-case target is in `TEST_CASES.md`.

### 6.8 Test data and fixtures

All data is synthetic. No real personal data is used; place data is public catalog content.

| Fixture | Content |
|---|---|
| FX-CAT | Synthetic catalog per city: published places (≥ 6 per city; includes "Đại Nội" with aliases "Imperial City", "Dai Noi"), 10 candidates (2 per city), places with deliberately missing facts, a fact verified 181 days ago, open-data-seeded places with attribution, categories with VI/EN labels |
| FX-ACC | Clerk test-instance accounts: traveler-A (EN), traveler-B (VI), curator-C (curator role), study-S01 (study flag, code P01), traveler-D (non-study), disposable deletion accounts `fixture-del-*` |
| FX-TRIP-HA02 | Saved 2-day Hội An trip of traveler-A at revision 1 |
| FX-GEM / FX-RTE / FX-PLC / FX-PRC | Recorded Gemini, Routes, Places and LiteAPI responses, including injected unknown/other-city/candidate IDs, malformed output and `no_route` |
| FX-FAULT | Fault profiles (§6.3) |
| EVS-* | Evaluation sets (§6.2) |

The owner maintains the fixtures; fixtures are versioned with the code; evaluation sets are frozen as in §6.2.

## 7.0 Item pass/fail criteria (cl. 5.7)

### 7.1 Case level

A case passes only when its expected result is observed at the stated threshold, with evidence stored. A case with
missing evidence is `NOT RUN`, not `PASS`.

### 7.2 Entry criteria

| Level | Entry criteria |
|---|---|
| All | Tested commit recorded; CI jobs `api` and `mobile` green on that commit; target environment's `/health` and `/ready` return 200 |
| Integration | Migrations at head on a clean database; fixtures FX-* loaded |
| E2E | Build installed against the environment; fixtures loaded; test accounts can sign in |
| Acceptance | Evaluation sets frozen (2026-12-08, ASM-011); staging deployed with the RC build; ≥ 30 published places per city for runs that use the real catalog (MET-011); all P0 integration cases passed on the same commit |
| Usability study | RC-08 met (OQ-004 answered, consent procedure approved); RC-01..RC-05 met on the study build; pilot session done |

### 7.3 Exit criteria (release candidate for the study)

Derived from BRD MET-004..MET-012 and PRD §11.3:

| ID | Criterion | Source |
|---|---|---|
| EX-01 | 100% of Must user-story criteria and Must BRD AC covered by at least one **executed, passed** case (COVERAGE_TARGET); 100% of Must FRs pass (RC-01) | RC-01, NFR-031 |
| EX-02 | 100% of Must NFRs meet their threshold except NFR-018..NFR-021 (measured during/after the study) | RC-02 |
| EX-03 | HA-02 passes on one Android device, and on one iPhone unless iOS is cut | RC-03 |
| EX-04 | MET-004 = 100%; MET-006 = 0; MET-010 = 0; MET-007 ≥ 95%; MET-008 ≥ 90% | RC-05 |
| EX-05 | MET-005 = 0 and MET-009 ≥ 85% if lock/regeneration and photo are not cut | BRD §4.1, RC-06 |
| EX-06 | MET-011: ≥ 30 published places in each of the five cities | RC-04 |
| EX-07 | MET-012: USD 0 cash and AWS spend ≤ USD 200 to date | NFR-033, NFR-034 |
| EX-08 | Should/Could features pass their criteria or are disabled and recorded as cut (SKIP with approver) | RC-06 |
| EX-09 | 0 open blocking defects; 0 `[ORPHAN]` for Must in `RTM.md` and `traceability.md` | RC-07 |
| EX-10 | OQ-004 answered and consent approved before the first session | RC-08 |

Study exit (reported, not a release gate): MET-001 ≥ 80%, MET-002 ≤ 3 min, MET-003 ≥ 70, MET-013 10–15 participants by
2027-01-31 with ≥ 4 per language.

### 7.4 Defect severity

| Severity | Definition | Release impact |
|---|---|---|
| Blocking | Breaks a Must criterion, an EX-04 metric, privacy, or data integrity; or prevents a study task | Must be fixed before exit (RC-07) |
| Major | Breaks a Should criterion or degrades a Must one with a workaround | Fix or cut under DEC-003 |
| Minor | Cosmetic or copy issue not affecting a criterion | Fix if time permits |

Defects are logged as `DEF-xxx` in `docs/07-verification/evidence/defects.md` (created at first run) and as GitHub issues.

## 8.0 Suspension and resumption (cl. 5.8)

| Suspend when | Resume when |
|---|---|
| CI red on `main` for the tested commit | Fix merged; new commit recorded; REG-CI green |
| Staging unavailable for > 4 h or database restore needed | Environment restored; fixtures reloaded; REG-SMOKE passes |
| A blocking privacy or data-integrity defect is found (MET-006 > 0 or MET-010 > 0) | Fix deployed; the full failure-injection or permission matrix re-run from the start |
| Provider quota exhausted (Gemini, Routes) or billing alarm at USD 50 | Quota reset or switch to recorded mode; cost reviewed with NFR-033/NFR-034 |
| An evaluation set changed after freezing without a new version | Set re-versioned, change recorded, run restarted on the new version |
| ≥ 3 blocking defects open in one cycle | Defects fixed; affected suites re-run |
| Study: a participant reports distress, a consent problem appears, or data handling deviates from the protocol | Owner and mentor review; protocol amended and approved if needed |

## 9.0 Test deliverables (cl. 5.9)

| Deliverable | When | Location |
|---|---|---|
| Master test plan (this document) | M1, approved by 2026-12-08 | `docs/07-verification/TEST_PLAN.md` |
| Test cases | M1 | `docs/07-verification/TEST_CASES.md` |
| RTM | M1, regenerated per change; filled per run | `docs/07-verification/RTM.md`, `evidence/<run-id>/rtm-run.md` |
| Research protocol, consent form, session script | M1, submitted for OQ-004 | `docs/07-verification/RESEARCH_PROTOCOL.md` |
| Frozen evaluation sets EVS-* v1.0 | 2026-12-08 | `apps/api/tests/evaluation/` (proposed) |
| Automated tests and Maestro flows | M2–M5 | `apps/api/tests`, `apps/mobile` |
| Run evidence, defect log | Each run | `docs/07-verification/evidence/` |
| Test summary report (kit `TestReport_IEEE_829_Prompt.md`) | 2027-01-31 | `docs/07-verification/TEST_REPORT.md` |
| Study results (anonymised) | 2027-01-31 | Annex of the test report |

## 10.0 Testing tasks (cl. 5.10)

These become WBS tasks in Phase 5 (`docs/05-development/`, OQ-116).

| ID | Task | Depends on | Owner | Due |
|---|---|---|---|---|
| TT-01 | Approve this plan, test cases, RTM and protocol | — | trantrongminh (approve), Lê Ngọc Tấn Hiền | 2026-12-08 |
| TT-02 | Build and freeze EVS-* v1.0 and FX-* fixtures | Catalog drafts for Hội An | Lê Ngọc Tấn Hiền | 2026-12-08 |
| TT-03 | Add Schemathesis and generated-type drift checks to CI | OpenAPI routes implemented | Lê Ngọc Tấn Hiền | 2026-12-22 |
| TT-04 | Set up Maestro and the first P0 flows | Mobile ↔ API wiring | Lê Ngọc Tấn Hiền | 2026-12-22 |
| TT-05 | Implement fault-injection adapters and the inert-in-production test | Provider adapters | Lê Ngọc Tấn Hiền | 2027-01-05 |
| TT-06 | Implement evaluation runner (recorded and live modes) | TT-02 | Lê Ngọc Tấn Hiền | 2027-01-05 |
| TT-07 | Inspect RTM for NFR-031 (every Must FR has a TC) | — | Lê Ngọc Tấn Hiền | 2027-01-04 |
| TT-08 | Accessibility, bilingual and attribution inspections | All traveler screens built | Lê Ngọc Tấn Hiền | 2027-01-15 |
| TT-09 | Performance and load measurement on staging | Staging (OQ-110) | Lê Ngọc Tấn Hiền | 2027-01-15 |
| TT-10 | Restore drill (NFR-009, NFR-010, AC-021 restore) | Backups on | Lê Ngọc Tấn Hiền | 2027-01-15 |
| TT-11 | Release-candidate acceptance run and exit review | Scope freeze 2027-01-15 | Lê Ngọc Tấn Hiền; mentor review | 2027-01-17 |
| TT-12 | Pilot session, then study sessions | RC-08, TT-11 | Lê Ngọc Tấn Hiền | 2027-01-18 → 2027-01-29 |
| TT-13 | Test summary report | TT-11, TT-12 | Lê Ngọc Tấn Hiền | 2027-01-31 |

## 11.0 Environmental needs (cl. 5.11)

| Environment | Purpose | Components | Data |
|---|---|---|---|
| Local Docker | Unit, integration, contract, Maestro on emulator | Docker Compose service `db` (PostgreSQL 16 + PostGIS + pgvector), API via `uv run uvicorn`, Android emulator, Expo dev build | FX-*; recorded providers only |
| GitHub Actions CI | REG-CI, REG-EVAL (recorded) | Existing jobs `api` and `mobile` on `ubuntu-latest`; Compose DB service; multi-arch image build | FX-*, EVS-* (recorded) |
| AWS staging | E2E, acceptance, performance, failure injection, live-provider runs | Proposed (OQ-110): same EC2 t4g.small with a second Compose project and a separate database on the RDS instance, separate SSM parameters, hostname distinct from production; test data only | FX-* plus the curated catalog snapshot; test accounts only |
| AWS production | Study sessions, NFR-008 probes | EC2 t4g.small + RDS + S3 per ADR-002 | Real curated catalog; study accounts P01..P15 |
| Devices | NFR-027, NFR-028, voice, photo, maps handoff | ≥ 2 physical Android devices (minimum supported and latest, OQ-088/OQ-112); 1 iPhone unless iOS cut; desktop Chrome for the curator tool | Study build |
| Accounts and services | Identity and providers | Clerk test instance (staging) and production instance; Gemini and Google Maps Platform free tier; LiteAPI sandbox | Keys only in SSM / CI secrets |

Software needs: `uv`, Docker, Node 22, Maestro CLI, Android SDK, EAS build (development build for native modules). As
noted in `progress.md`, `uv` is not yet installed on the owner's machine; until then local results come from CI.

## 12.0 Responsibilities (cl. 5.12)

| Role | Person | Responsibilities |
|---|---|---|
| Test lead, author, tester, test-data manager, curator | Lê Ngọc Tấn Hiền | Writes and runs all tests; builds and freezes fixtures and evaluation sets; runs the study; writes the report |
| Approver | trantrongminh | Approves this plan, the protocol and the exit decision; reviews a sample of MET-007 judgements (proposed, OQ-111) |
| AI coding agents (Claude Code) | — | Draft tests and documents under owner review; never approve gates or mark results |
| Independent reviewer for EN content and MET-007 sample | TBD (OQ-111) | Second judgement on a 20% sample |
| Study participants | 10–15 volunteers | Perform tasks and questionnaires under consent |

## 13.0 Staffing and training needs (cl. 5.13)

One person performs all test roles (CON-002), which limits independence (TR-09). Training the owner needs before M2:
Maestro flows on Expo development builds; Schemathesis; k6 or Locust basics; Android Accessibility Scanner and
TalkBack; WCAG 2.1 AA success criteria above; SUS administration and scoring; and the university's research-ethics
and consent requirements once OQ-004 is answered.

## 14.0 Schedule (cl. 5.14)

Aligned to the milestones of `plan.md`; to be re-aligned with the SDP when phase 5 is approved (OQ-116).

| Milestone | Window | Testing work | Exit evidence |
|---|---|---|---|
| M1 Planning | 2026-11-16 → 2026-12-08 | TT-01, TT-02; protocol submitted to the mentor for OQ-004 (asked by 2026-11-11); staging decision OQ-110 | Approved plan; EVS-* v1.0 tags |
| M2 Sprint 1 (foundation) | 2026-12-09 → 2026-12-22 | Catalog, search, curation, identity integration and contract tests; TT-03, TT-04; NFR-012/013/016 on staging | First run record (catalog cases) |
| M3 Sprint 2 (planner) | 2026-12-23 → 2027-01-05 | Planner, Plan Health, editing, Save cases; TT-05, TT-06; first MET-004 and MET-006 runs; TT-07 (NFR-031 by 2027-01-04) | MET-004, MET-006 run reports |
| M4 Sprint 3 | 2027-01-06 → 2027-01-15 | Place card, Guide (MET-007/008), handoff, deletion, privacy (MET-010, AC-046); TT-08, TT-09, TT-10; MET-011 check | Run reports; inspection checklists |
| M5 Sprint 4 (Should, parallel) | 2027-01-06 → 2027-01-15 | Lock/regeneration, voice, photo, prices cases or SKIP-cut; scope freeze 2027-01-15 | Cut record (RC-06) |
| M6 Verification | 2027-01-16 → 2027-01-31 | TT-11 RC acceptance (by 2027-01-17); pilot; study sessions 2027-01-18 → 2027-01-29; TT-13 | Exit review; study records; test report |
| After M7 | 2027-07-01 | NFR-018 retention inspection | Inspection note |

## 15.0 Risks and contingencies (cl. 5.15)

| Risk | Contingency |
|---|---|
| TR-06 catalog short of 30 per city by M4 (RSK-001) | Run functional cases on fixtures; acceptance on the real catalog only for complete cities; escalate to mentor at M4; never lower the gate (release gate in AGENTS.md) |
| TR-01/TR-03 planner defects late in M3 | Cut order DEC-003 frees M5 time; P0 cases take precedence |
| TR-07 quota limits | Recorded mode for regression; live runs once per RC; schedule live runs on separate days |
| TR-10 no staging | Use production stack before the study with test accounts, then reset data (fallback only if OQ-110 says no staging) |
| TR-11 ethics approval delayed | Study cannot start (RC-08); keep acceptance work going; report MET-001..003 as not measured if not approved by 2027-01-25 and agree an alternative with the mentor |
| TR-12 devices unavailable | Borrow devices; minimum-version runs on emulator recorded as a deviation |
| Model behaviour changes (Gemini version update) | Pin the model version in config; re-run REG-EVAL recorded and one live run; report both |
| Owner unavailable (illness) | Cut order; study window can shift within M6 |

## 16.0 Approvals (cl. 5.16)

| Role | Name | Decision | Date |
|---|---|---|---|
| Test plan owner | Lê Ngọc Tấn Hiền | [Pending] | — |
| Approver (mentor) | trantrongminh | [Pending] | — |

Agents do not approve. Approval authorises execution of this plan from M2.

---

## 17. Requirement-to-test-area matrix

| Requirement group | Unit | Integration | Contract | System/E2E | Acceptance | Study | Cases (`TEST_CASES.md` §) |
|---|---|---|---|---|---|---|---|
| BR-001..BR-003, BR-024, BR-025, BR-047 (catalog, trust) | ✓ | ✓ | ✓ | ✓ | ✓ (AC-001, AC-003, AC-024, AC-025, AC-047) | — | §1 |
| BR-002, BR-004 (curation, publication) | — | ✓ | ✓ | ✓ | ✓ (AC-002, AC-004) | — | §2 |
| BR-005, BR-006 (proposal) | ✓ | ✓ | ✓ | ✓ | ✓ (AC-005, AC-006) | ✓ (MET-001, MET-002) | §3 |
| BR-007, BR-008, BR-009, BR-026 (feasibility) | ✓ | ✓ | ✓ | ✓ | ✓ (AC-007..AC-009, AC-026) | — | §4 |
| BR-010, BR-027..BR-032 (editing) | — | ✓ | ✓ | ✓ | ✓ (AC-010, AC-027..AC-032) | ✓ | §5 |
| BR-011, BR-012, BR-033 (Save, failure safety) | ✓ | ✓ | ✓ | ✓ | ✓ (AC-011, AC-012, AC-033; MET-006) | ✓ | §6, §7 |
| BR-013, BR-034, BR-035 (lock, regeneration — Should) | — | ✓ | ✓ | ✓ | ✓ (AC-013, AC-034, AC-035; MET-005) | optional | §8 |
| BR-014, BR-036, BR-037 (place card) | — | ✓ | ✓ | ✓ | ✓ (AC-014, AC-036, AC-037) | ✓ | §9 |
| BR-015, BR-038, BR-048 (Guide) | ✓ | ✓ | ✓ | ✓ | ✓ (AC-015, AC-038, AC-048; MET-007, MET-008) | ✓ | §10 |
| BR-016, BR-039 (voice — Should) | — | — | — | ✓ | ✓ (AC-016, AC-039) | optional | §11 |
| BR-017, BR-040 (photo — Should) | ✓ | ✓ | ✓ | ✓ | ✓ (AC-017, AC-040; MET-009) | — | §12 |
| BR-018, BR-041, BR-042 (handoff) | — | ✓ | ✓ | ✓ | ✓ (AC-018, AC-041, AC-042) | ✓ (SC-03) | §13 |
| BR-019, BR-043, BR-049 (prices — Could) | — | ✓ | ✓ | ✓ | ✓ (AC-019, AC-043, AC-049) | — | §14 |
| BR-020, BR-021, BR-044, BR-046 (privacy) | ✓ | ✓ | ✓ | ✓ | ✓ (AC-020, AC-021, AC-044, AC-046; MET-010) | — | §15 |
| BR-022 (language) | ✓ | ✓ | — | ✓ | ✓ (AC-022) | ✓ (BR-045) | §16 |
| BR-023, BR-045 (evaluation) | — | ✓ | ✓ | — | ✓ (AC-023, AC-045) | ✓ (MET-001..003, MET-013) | §17 |
| BR-050 (budget) | — | — | — | — | ✓ (AC-050; MET-012) | — | §19 |
| NFR-001..NFR-038 | per NFR | per NFR | NFR-030 | per NFR | per NFR | NFR-019..021 | §19, §20 |

Per-ID coverage (BR → FR/NFR → US/AC → UC → API → TC) is in `RTM.md`: 93/93 Must user-story criteria and 40/40 Must
BRD criteria have at least one case; 0 `[ORPHAN]`.

## 18. Open questions

New IDs continue after the highest ID in use (OQ-099) with a gap of 10 for parallel authoring.

| ID | Question | Affects | Owner (answers) | Needed by | Recommendation |
|---|---|---|---|---|---|
| OQ-110 | Is there a separate staging environment? PRD §7 measures on "staging", but the SAD physical view has none. | §11, NFR-001..011, cost (CON-001) | Lê Ngọc Tấn Hiền (decide; mentor informed) | 2026-12-08 | Yes: second Compose project + separate database on the existing EC2/RDS, test data only; no extra AWS resources |
| OQ-111 | Who gives the independent second judgement on the MET-007 claim-to-source sample and the EN content review? | MET-007, AC-022, TR-09 | trantrongminh | 2026-12-08 | Mentor or a fellow student reviews a 20% random sample; agreement reported |
| OQ-112 | Which physical devices are used for NFR-027 (minimum and latest Android) and NFR-028 (iPhone)? | §11, RC-03 | Lê Ngọc Tấn Hiền | 2026-12-15 | Owner's phone as "latest" plus one borrowed older Android at the minimum API level fixed by OQ-088 |
| OQ-113 | How are participants recruited, and is any compensation offered? | `RESEARCH_PROTOCOL.md` §3 | Lê Ngọc Tấn Hiền (confirm with mentor under OQ-004) | 2026-12-15 | Adults ≥ 18 from university and personal networks; no payment (USD 0 budget) |
| OQ-114 | How many live-provider evaluation runs are allowed per release candidate within free-tier quotas? | §6.2, NFR-035, TR-07 | Lê Ngọc Tấn Hiền | 2026-12-08 | One live run per set per RC; all regression on recorded responses |
| OQ-115 | Are study sessions in person only, or also remote? | `RESEARCH_PROTOCOL.md` §4 | Lê Ngọc Tấn Hiền (mentor under OQ-004) | 2026-12-15 | In person on a provided Android phone; remote only as fallback with screen sharing and no recording |
| OQ-116 | Re-align §10 tasks and §14 schedule with the phase-5 SDP/WBS once approved | §10, §14 | Lê Ngọc Tấn Hiền | 2026-12-08 | Copy TT-01..TT-13 into the WBS as verification tasks |

Existing questions this plan depends on: OQ-004 (ethics/consent — gates the study), OQ-006 (baseline pre-task —
proposed design in the protocol), OQ-088 (minimum OS versions), OQ-089 (AI request cap).

## 19. Self-check

### 19.1 Kit §6 checks

| Check | Status | Evidence |
|---|---|---|
| Every acceptance criterion maps to at least one planned test case | Pass | `RTM.md` §1: 127/127 user-story criteria, 50/50 BRD AC |
| Every NFR has a measurement method and a threshold | Pass | TC-222..TC-259 (method and threshold from PRD §7); §6.1.8 |
| Test items, features not tested, environment, data and responsibilities are stated | Pass | §3, §5, §11, §6.8, §12 |
| Entry, exit, suspension and resumption criteria are defined and measurable | Pass | §7.2, §7.3, §8 |
| Risk assessment identifies high-risk areas and order of testing | Pass | §0.7, §4.1, §15 |

### 19.2 `verification/Test_Plan_IEEE_829_Checklist.xlsx` (18 rows)

| # | Category | Item | Status | Evidence |
|---|---|---|---|---|
| 1 | Document metadata | Test plan identifier | Pass | Document control, §1.0 (TP-GONARRA-v0.1) |
| 2 | Document metadata | Introduction | Pass | §2.1–§2.3 |
| 3 | Scope & features | Test items | Pass | §3.1 SI-001..SI-008 |
| 4 | Scope & features | Features to be tested | Pass | §4.1–§4.3, §17 |
| 5 | Scope & features | Features not to be tested | Pass | §5.0 NT-01..NT-12 |
| 6 | Approach | Testing approach | Pass | §6.1–§6.6 |
| 7 | Approach | Automation vs manual | Pass | §6.7; per-case automation target in `TEST_CASES.md` |
| 8 | Pass/fail & lifecycle | Item pass/fail criteria | Pass | §7.1, §7.3 EX-01..EX-10 (numeric thresholds) |
| 9 | Pass/fail & lifecycle | Suspension criteria | Pass | §8 |
| 10 | Pass/fail & lifecycle | Resumption requirements | Pass | §8 |
| 11 | Environment & resources | Environmental needs | Partial | §11 — staging environment not yet in the SAD; owner Lê Ngọc Tấn Hiền, due 2026-12-08 (OQ-110) |
| 12 | Environment & resources | Responsibilities | Pass | §12 |
| 13 | Environment & resources | Staffing & training needs | Pass | §13 |
| 14 | Execution & delivery | Testing tasks | Pass | §10 TT-01..TT-13 with owners and dates |
| 15 | Execution & delivery | Test deliverables | Pass | §9 |
| 16 | Execution & delivery | Schedule | Pass | §14 (M1–M6) |
| 17 | Risk management | Risks & contingencies | Pass | §0.7, §15 |
| 18 | Risk management | Approvals | Pass | §16 (section present; sign-off [Pending]) |

**Score: 17 Pass, 1 Partial, 0 Fail, 0 N/A.** The Partial closes when OQ-110 is answered.
