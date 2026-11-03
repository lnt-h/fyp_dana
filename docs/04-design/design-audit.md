# Gonarra Design Audit

| Field | Value |
|---|---|
| Audit ID | DA-GONARRA-01 |
| Date | 2026-11-04 |
| Design set | design-v0.1 candidate. All files are untracked on branch `docs/sdlc-documentation-baseline`, base commit `4c03e7f` |
| Auditor | Independent design auditor (AI agent, read-only), for Lê Ngọc Tấn Hiền |
| Design owner / approver | Lê Ngọc Tấn Hiền / mentor trantrongminh (ASM-001) |
| Prompt | `design/Design_Audit_Prompt.md` v2.0, adapted copy `docs/00-governance/prompt-templates/design/Design_Audit_Prompt.md` (2.0-gonarra.1) |
| Baselines | BRD 0.4, PRD, USER_STORIES, traceability. Owner decisions SRC-100 A-021..A-027 are treated as decided |
| Security review done | No |

## 1. Inventory audited

| Artifact | ID / version |
|---|---|
| `architecture/SAD.md` | GONARRA-SAD 0.1 |
| `ADR-001..ADR-010` | Proposed |
| `ADR-011`, `ADR-012` | Accepted (A-021) |
| `architecture/blueprint.md` | GONARRA-SDD 0.1 |
| `data/model.md`, `data/schema.sql` | GONARRA-DATA 0.1 |
| `api/openapi.yaml` | OpenAPI 3.1.0, info.version 0.1.0 |
| `api/api-contract.md` | GONARRA-API 0.1 |
| `use-cases.md` | GONARRA-UC 0.1 |
| `diagrams/README.md` | GONARRA-DIAG 0.1 |
| `diagrams/structure-views.md` | GONARRA-STRUCT 0.1 |
| `diagrams/*.drawio` (6 files) | Same set as GONARRA-DIAG / GONARRA-STRUCT 0.1 |
| `ui-ux/README.md` and 16 `*.html` pages | GONARRA-UIUX 0.1 / Draft |

**Mechanical checks that were run:**

| Check | Result |
|---|---|
| `xmllint --noout` on each of the 6 `.drawio` files | All OK |
| `openapi-spec-validator 0.9.0` on `api/openapi.yaml` | OK |
| Uniqueness of OQ/ASM/RSK across `docs/`, by script: IDs defined in more than one file | See §1.1 |
| FR coverage, by script: 81 FRs in the PRD | Every FR appears in the SAD, blueprint, api/api-contract.md, model.md, use-cases.md and UI README |
| FR coverage in `api/openapi.yaml` | 79 of 81. FR-060 and FR-063 are client-only, as api/api-contract.md says |
| NFR coverage in SAD §6.2 | 37 of 37 |
| CMP IDs: SAD §3.1.1 (CMP-001..CMP-024) against structure-views and the drawio files | No unknown CMP. Lifeline names in `process-view.drawio` match the SAD names. `development-view.drawio` omits CMP-015, as structure-views §2.2 explains |
| API fields against `schema.sql` columns (19 schema/table pairs, by script) | Preferences, AccountDeletionStatus, Trip, CatalogPublication, ImportRun, Source, GuideSession, StudySessionLog, City and Category match exactly. The extra fields in Stop, PlaceDetail, PlanPreview, Media and PlaceFact are locale-resolved, joined or derived from `preview_revisions` / `place_localizations` / `catalog_publications`. `Stop.rationale` is documented as preview only |

### 1.1 ID uniqueness result

The only true collisions are inside the design set. These IDs were issued twice, with different meanings:

| ID | `use-cases.md` (and `diagrams/README.md`, `process-view.drawio`) | `diagrams/structure-views.md` (and `physical-view.drawio`) |
|---|---|---|
| OQ-080 | SAD §3.5 link to use-cases (l.515) | EC2 OS image (l.509; drawio c14 label) |
| OQ-081 | 409 / 422 codes (l.516; README l.160; drawio pages 2 and 5) | SAD §3.1.2 against the schema (l.510; §1.4 heading l.211) |
| OQ-082 | Deletion retry cadence (l.517, l.410; README l.254; drawio page 6) | SAD §3.4.1 nodes (l.511) |
| ASM-080 | Save endpoint (l.507) | One node per piece of software (l.512) |

Other IDs that appear in more than one file are legitimate:
- intake/SRC-100 IDs carried into the BRD with the same meaning (OQ-001..008, ASM-001..003, RSK-001..003);
- kit template placeholders;
- ASM-006 cited by the SAD with the BRD meaning;
- OQ-030/032/036/038/039 cross-referenced in api/api-contract.md as "existing, SAD".

OQ-085..OQ-099 and ASM-083..ASM-099 are unused.

## 2. Pairwise checks (§7.1)

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | SAD ↔ blueprint | Partial | Packages map one to one to CMP (blueprint §2 table, l.157–170). There is drift. Blueprint l.461–465 uses deletion states DELETION_REQUESTED/DELETING/DELETED, but `schema.sql` l.1151 uses REQUESTED/IN_PROGRESS/COMPLETED/FAILED. Blueprint l.210 `PreviewRevision.manifestId` and l.205 `visitDurationBounds` do not exist in the schema (corpus_revision/snapshot; visit_minutes_*). Blueprint l.378–379 and l.394 embed after publication (F-01) |
| 2 | SAD ↔ diagrams | Partial | CMP IDs and lifelines are consistent. The SAD §3.1.2 domain model (l.311–396) differs from `logical-view.drawio` and the schema (F-03). SAD §3.4.1 (l.633–667) lacks three nodes that `physical-view.drawio` has: booking partner sites, Expo EAS Build, and the Local development environment (F-04) |
| 3 | SAD ↔ `api/openapi.yaml` | Partial | Every SAD interface I-001..I-006 has operations, and the spec validates. Deletion contract drift: the `GET /v1/me/deletion` 401 response (openapi l.221) is not described as "completed after IN_PROGRESS" (OQ-073/A-024). Booking partner names are missing from api/api-contract.md OQ-071 (l.566) and from `HandoffLink.partner_key` (openapi l.2891) (F-05) |
| 4 | SAD ↔ `data/model.md` | Fail | Deletion order: model.md §3.2 step 2 (l.305) deletes the Clerk user *before* `DELETE FROM accounts`, which contradicts OQ-073 "Clerk user deleted last". Guide corpus: model.md §6.1 step 6 (l.396–397) and §5 (l.370) make chunks searchable only after re-publication, which contradicts A-023 (F-01, F-02). SAD §3.3.5 (l.616–622) state names differ from schema enums for places, previews, deletion and Guide answers (F-03) |
| 5 | SAD ↔ UI/UX | Partial | Screens need only capabilities that exist. Voice runs on the device (CMP-021) and the photo flow uses CMP-022 → API-028. Drift: UI README OQ-066 (l.605) waits for "DELETED", a state the API does not have, instead of COMPLETED or 401 after IN_PROGRESS. The UI README state table l.101 uses the SAD deletion states (F-02) |
| 6 | Requirements ↔ design | Pass | 81/81 FRs and 37/37 NFRs are traced. No design FR is absent from the PRD. FR-009 is met by CLI + SPA (OQ-070/A-024) |
| 7 | NFR ↔ scenario ↔ design | Partial | Every NFR has a QAS in SAD §2.4 and a realization in §6.2. QAS-10 (deletion) is realized inconsistently (F-02). The FR-058 "searchable" scenario fails on first publication (F-01) |
| 8 | Stories ↔ screens | Partial | 37/37 US appear in the UI README. SCR-002 Onboarding (l.173) and SCR-012 Edit profile (l.183) are still "GAP → OQ-062", but A-027 decided that they trace as supporting US-032/US-011 (F-08) |
| 9 | Diagram sources ↔ SAD references | Pass | Each 4+1 view has a `.drawio` source that the SAD references (logical, development, process ×2, physical, scenarios). All six are well-formed XML. There are no image-only diagrams |
| 10 | Decisions ↔ design | Fail | ADR-012 l.37 and ADR-010 l.32 ("embeddings … after publication") cause the A-023 defect (F-01). `use-cases.md` OQ-084 (l.519), `diagrams/README.md` l.253 and `process-view.drawio` page 6 (messages 14, 22) introduce a "deletion receipt" that contradicts A-024/A-026. `use-cases.md` ASM-082 (l.509) lets guests search and view places, which contradicts A-027 ("guests see Home and onboarding only") and the openapi bearer security on `/v1/places` and `/v1/cities` (F-07) |

Explicit assessments (§3.3):

| Category | Result |
|---|---|
| Orphan elements | None. Schema-only classes are listed in structure-views §1.4 |
| Missing flows | None. All six process scenarios have drawio pages |
| Contract drift | F-01, F-02, F-03, F-05, F-06 |
| Ownerless NFRs | None |
| Orphan screens | SCR-002 and SCR-012, pending the edit in F-08 |

## 3. Per-artifact score

Basis:
- **SAD:** re-scored row by row against `SAD_IEEE_1016_Checklist.xlsx` (16 rows plus the prompt's trace row).
- **Other artifacts:** the score is the artifact's own self-check against its kit checklist (row counts verified in the xlsx), adjusted for this audit's findings.

Every Partial is owned by Lê Ngọc Tấn Hiền, due 2026-11-11.

| Artifact | Checklist | Self-score (P/Pa/F/NA) | Audited score (P/Pa/F/NA) | Rows lowered by the audit |
|---|---|---|---|---|
| architecture/SAD.md | SAD_IEEE_1016 | 15/2/0/0 | **12/5/0/0** | Logical view (F-03); state dynamics (F-03, F-02); information view (F-01); physical mapping (F-04); interface view (F-05) |
| ADR-001..012 | (SAD rationale rows) | — | 11 Pass, 1 Partial | ADR-012 together with ADR-010 embedding order (F-01) |
| architecture/blueprint.md | BluePrint IEEE 1016 | 17/2/0/0 | **15/4/0/0** | State model (F-02); data types (F-06) |
| data/model.md + schema.sql | Database_Design | 19/3/0/3 | **17/5/0/3** | Workflow/transactions (F-01); deletion cascade (F-02) |
| api/openapi.yaml + api/api-contract.md | API_Design IEEE 1016 | 19/1/0/1 | **17/3/0/1** | External partners (F-05); deletion status semantics (F-02) |
| use-cases.md | UseCase_Document UML 2.0 | 27/2/0/0 | **24/5/0/0** | UC-014 flow (F-02); ASM-082 (F-07); duplicate IDs (F-09) |
| process-view.drawio (sequence) | Sequence_Diagram UML 2.0 | 19/2/0/1 | **17/4/0/1** | Page 5 publish→embed (F-01); page 6 deletion (F-02) |
| process-view-activity.drawio | Activity_Diagram UML 2.0 | 25/2/0/1 | **24/3/0/1** | Page 1 publish→embed (F-01) |
| logical-view.drawio | Class_Diagram UML 2.0 | 17/1/0/7 | 17/1/0/7 | No change. It follows the schema |
| development-view.drawio | Component_Diagram UML 2.0 | 14/3/0/1 | 14/3/0/1 | No change |
| physical-view.drawio | Deployment_Diagram UML 2.0 | 11/3/0/2 | 11/3/0/2 | No change. The OS label is still "OQ-080" (F-09) |
| scenarios-view.drawio | UseCase (via use-cases.md) | — | as use-cases.md | — |
| ui-ux | UI_UX_Design IEEE 1016 | 18/4/0/0 | **17/5/0/0** | Traceability SCR-002/012 (F-08); deletion state copy (F-02) |

## 4. Findings and fix list (ordered by severity)

### Critical (block baseline)

**F-01 — Guide embeddings become searchable only after a second publication.** This contradicts A-023 and FR-058.

- **Cause:**
  - Approved chunks must have an embedding (`ck_knowledge_chunks_approved_embedded`, schema l.510).
  - `fn_publish_place` pins `max(corpus_revision)` of APPROVED chunks (schema l.749–750).
  - `vw_guide_chunks` joins `cp.corpus_revision = kc.corpus_revision` (schema l.1282).
  - Because `cli embed` runs *after* publication, the first publication pins NULL.
- **Fix:** embed and approve chunks *before* the publish gate. No schema change is needed.
- **Decision owner:** Lê Ngọc Tấn Hiền (already decided, A-023).

Exact edits:
1. `data/model.md` §6.1 step 6 (l.396–398):
   - Old: "Narrative chunks are written and embedded by the CLI, approved (an approved chunk must have an embedding) and linked to sources. Because the embedding step runs after the place is first published (DEC-009), the place is published again so the new publication pins the corpus revision."
   - New: "Narrative chunks are written and linked to sources during CONTENT_REVIEW; `cli embed` embeds DRAFT chunks of places in CONTENT_REVIEW or READY_TO_PUBLISH; the curator then approves them (an approved chunk must have an embedding). Publication pins the latest approved corpus revision, so the Guide can search the place from its first publication; later corpus changes are picked up by the next publication."
2. `data/model.md` §5 row `vw_guide_chunks` (l.370):
   - Old: "Chunks embedded after publication become visible only after the place is re-published (§6.1 step 6)"
   - New: "Chunks are embedded and approved before publication, so they are visible from the first publication (§6.1 step 6)".
3. `adr/ADR-012-cli-ingestion-embedding.md` §Decision (l.37): "After the curator publishes, `embed` computes embeddings for new or changed reviewed chunks" → "Before the curator publishes, `embed` computes embeddings for new or changed draft chunks so they can be approved and pinned by the first publication". Make the same change in §Context (l.16): "after publication" → "before publication".
4. `adr/ADR-010-grounded-guide-retrieval.md` l.32: "computed after publication by the CLI" → "computed by the CLI before publication, so a place is searchable from its first publication".
5. `architecture/SAD.md`, three places:
   - DEC-009 row (l.192): "embeddings by the same CLI after publication" → "embeddings by the same CLI before publication".
   - §3.5 SC-05 (l.708): reorder to "CMP-018 import CLI → CMP-002 → CMP-006 → CMP-018 embed CLI → CMP-012 → CMP-016 → CMP-005 (publish)".
   - §3.7.2 (l.786): "(after publication)" → "(before publication)".
6. `architecture/blueprint.md`:
   - l.378–379: move "`cli embed` embeds new reviewed chunks" before `curation.publish(...)`.
   - l.394: change the matching wording in the same way.
7. `diagrams/README.md` publish sequence (l.230–240): move the `C->>CLI: cli embed` block above `C->>ADM: publish(candidateId)`.
8. `process-view.drawio` page 5: move messages 21–31 before message 1, then renumber.
   - Message 30: "place stays published" → "place stays in READY_TO_PUBLISH; publish gate refuses unembedded approved chunks".
9. `process-view-activity.drawio` page 1: move "Select reviewed chunks without embedding" / "Compute embeddings" / "embedded?" before "Request publish".

**F-02 — The deletion workflow contradicts OQ-073 / A-024 / A-026, and the state names drift.**

The decided rule is:
- The Clerk user is deleted last.
- The app treats a 401 after IN_PROGRESS as completed.
- There is no deletion receipt.
- The states are the schema enum REQUESTED / IN_PROGRESS / COMPLETED / FAILED.

Decision owner: Lê Ngọc Tấn Hiền (decided).

1. `data/model.md` §3.2 step 2 (l.304–307):
   - Old: "sets `IN_PROGRESS`, increments `attempt_count`, deletes the Clerk user through the Clerk API, then runs the `DELETE FROM accounts` above. The FK sets the job's `account_id` to NULL; the job is then set `COMPLETED`"
   - New: "sets `IN_PROGRESS`, increments `attempt_count`, runs the `DELETE FROM accounts` above (the FK sets the job's `account_id` to NULL), then deletes the Clerk user through the Clerk API as the last step; the job is then set `COMPLETED`".
   - In step 4, add: "Once the Clerk user is deleted the JWT is rejected; the app treats a 401 received after it has seen IN_PROGRESS as completed (OQ-073)."
2. `use-cases.md` UC-014 (l.404–410):
   - Main flow: "2. System records DELETION_REQUESTED … 3. System revokes the traveler's sessions and requests Clerk user deletion. 4. Jobs runner deletes the traveler's private records … and marks DELETED." → "2. System creates a deletion job (REQUESTED) and returns status (202). 3. Jobs runner sets IN_PROGRESS and deletes the traveler's private records. 4. Jobs runner deletes the Clerk user last and sets COMPLETED. 5. App polls the status; it shows completed on COMPLETED, or on a 401 after IN_PROGRESS was seen (OQ-073)."
   - Postconditions: "Account state DELETED" → "Deletion job COMPLETED".
   - E1: "until DELETED" → "until COMPLETED".
3. `use-cases.md` OQ-084 (l.519): replace the receipt answer.
   - Old: "API returns a single-purpose deletion receipt (opaque, expires after 48 h) … accepts it instead of a JWT"
   - New: "Closed by A-024/A-026: Clerk user deleted last; the app treats 401 after IN_PROGRESS as completed (OQ-073); no receipt".
4. `diagrams/README.md` deletion sequence (l.246–256): delete `ID->>CLK: deleteUser(subject)` from the request path.
   - `ID-->>APP: 202 status + receipt (OQ-084)` → `ID-->>APP: 202 status REQUESTED`.
   - Loop body: `CLI->>DB: delete private records, set IN_PROGRESS → COMPLETED | FAILED(reason)` preceded by `CLI->>CLK: deleteUser(subject) (last step)` after the DB delete.
   - Loop label: "until DELETED" → "until COMPLETED".
   - Add `alt 401 after IN_PROGRESS → app shows completed (OQ-073)`.
5. `process-view.drawio` page 6, to match item 4:
   - Message 14: "202 status(in_progress | failed) + deletion receipt (OQ-084)" → "202 status(REQUESTED)".
   - Message 22: "GET /v1/me/deletion(deletion receipt)" → "GET /v1/me/deletion (Bearer JWT); 401 after IN_PROGRESS ⇒ completed [OQ-073]".
   - Move the Clerk deleteUser message after the private-row delete in the jobs loop.
6. `architecture/SAD.md`:
   - §3.3.5 (l.621): "ACTIVE → DELETION_REQUESTED → DELETING → DELETED, or FAILED" → "REQUESTED → IN_PROGRESS → COMPLETED, or FAILED → retried (job states in `account_deletion_jobs`)".
   - §3.6.3 (l.755–756): add "Clerk user deleted as the last step; app treats 401 after IN_PROGRESS as completed (OQ-073)".
7. `architecture/blueprint.md` state diagram (l.459–466): rename the states to REQUESTED / IN_PROGRESS / COMPLETED / FAILED.
   - Transition label: "private rows deleted + Clerk user deleted" → "private rows deleted, then Clerk user deleted (last)".
8. `api/openapi.yaml` `getAccountDeletionStatus` (l.204), `401` response: add the description "After the Clerk user is deleted (last step), the token is rejected; a client that has observed IN_PROGRESS treats this 401 as COMPLETED (OQ-073)". Make the same addition in api/api-contract.md for API-007.
9. `ui-ux/README.md`:
   - l.101: states → "REQUESTED, IN_PROGRESS, COMPLETED, FAILED".
   - OQ-066 (l.605): answer → "Closed by A-027/OQ-073: poll until COMPLETED, or a 401 after IN_PROGRESS; then sign out locally and show completed".
   - `m13-account-deletion.html` l.191–194: the "DEL-••••" support reference must be labelled as a non-credential display ID (job `id`), not a receipt.

### High

**F-03 — The SAD §3.1.2 domain model and §3.3.5 state names differ from `schema.sql`.** This is A-025 / OQ-081 (structure-views).

Decision owner: Lê Ngọc Tấn Hiền (decided: adopt schema names).

`architecture/SAD.md` §3.1.2:
- l.311 `class Preferences` → `class AccountPreferences` (attributes locale, pace, interestCategoryCodes, allowedModes, dayStartTime, dayEndTime). l.378 `Account "1" -- "0..1" Preferences` → `Account "1" -- "0..1" AccountPreferences`.
- l.338 `class CatalogManifest` → `class CatalogPublication`. l.389 `CatalogManifest "1" -- "*" Place : pins revisions` → `Place "1" -- "0..*" CatalogPublication : publication revisions (≤1 PUBLISHED)`, because `catalog_publications.place_id` is NOT NULL (schema l.535, l.569).
- l.396 `PreviewRevision "*" -- "1" CatalogManifest` → `PreviewRevision ..> CatalogPublication : snapshot pins (no FK)`, drawn as a dependency.
- l.382 `Place "1" -- "2" PlaceLocalization` → `Place "1" -- "0..*" PlaceLocalization` (note: a publication pins exactly 2, VI + EN).
- l.387 `Place "1" -- "*" MediaAsset` → `Place "*" -- "*" MediaAsset` via `PlaceMedia`.
- l.316 `visitDurationBounds` → `visitMinutesMin/Suggested/Max`. l.353 `visitDuration` → `visitMinutes`. l.326 `freshness` → `/freshness` (derived, not stored).
- Add a sentence: "Schema-only classes are listed in structure-views §1.4".

`architecture/SAD.md` §3.3.5 (l.616–622):
- Place publication → "IMPORTED → MATCH_REVIEW → CONTENT_REVIEW → READY_TO_PUBLISH → PUBLISHED → (withdraw) CONTENT_REVIEW / RETIRED [schema ck_places_workflow_state]".
- Preview: "SUPERSEDED" → "DISCARDED".
- Guide answer → "ANSWERED / INSUFFICIENT_EVIDENCE / NOT_RECOGNISED (stream errors are not stored)".
- Account deletion: see F-02.

**F-04 — SAD §3.4.1 lacks partner sites, EAS Build and local development.** This is A-025 / OQ-082 (structure-views).

Decision owner: Lê Ngọc Tấn Hiền (decided).

In `architecture/SAD.md` §3.4.1 (Mermaid l.633–667), add:
- `partners["Booking partner sites — Agoda, Booking.com, Klook, 12Go"]` with `phone -->|"HTTPS deep link (I-006)"| partners`;
- `eas["Expo EAS Build"]` with `gh -->|"trigger build"| eas -->|"binary"| phone`;
- `subgraph local["Local development — Docker Compose (api + PostGIS/pgvector)"]`, with the app on a device or simulator pointing to the local or production API.

In §3.4.2, add three rows: Booking partner sites (external), Expo EAS Build (external CI), and Local development (developer laptop, `docker-compose.yml`). Also add the EC2 OS "Amazon Linux 2023 arm64 (SSM agent included)" (A-025) to the EC2 row.

**F-05 — Booking partners are not named in the API.** This is A-024 / OQ-071 and BRD §14 "Booking partner".

Decision owner: Lê Ngọc Tấn Hiền (decided).
- `api/api-contract.md` OQ-071 (l.566):
  - Recommendation "Choose one partner per kind with a public search URL" → "Closed by A-024: Agoda and Booking.com (STAY), Klook (ACTIVITY), 12Go (TRANSPORT) per BRD §14; deep-link parameter support verified per partner before INC-3 (AC-018)".
  - Status → Closed.
- `api/api-contract.md` l.52: "booking partners (I-006, link only)" → "booking partners Agoda, Booking.com, Klook, 12Go (I-006, link only)".
- `api/openapi.yaml` `HandoffLink.partner_key` (l.2891): add `enum: [agoda, booking_com, klook, twelve_go]` and the description "STAY: agoda | booking_com; ACTIVITY: klook; TRANSPORT: twelve_go (BRD §14)".

### Medium

**F-06 — The new preference fields (A-027 / OQ-065) are not carried everywhere.**

API and data already carry them: `account_preferences.pace` / `allowed_modes` (schema l.825–838), openapi `Preferences` / `PreferencesWrite` / `Pace` / `TravelMode`, and m02. The UI tokens `textMuted` #5E7585 and `tealText` #00788F appear in all 16 pages and the README; they do not affect API or data (Pass). Remaining gaps:
- `architecture/SAD.md` l.530: "Collect preferences: city, dates, 1–3 days, pace, interests, locale" → "… pace, interests, travel modes (WALK/DRIVE), locale".
- `use-cases.md` l.425, UC-016 step 3: "edits pace and interests" → "edits pace, interests and travel modes".
- `architecture/blueprint.md` l.205 `CandidatePlace.visitDurationBounds` → `visitMinutesMin/Suggested/Max`. l.210 `PreviewRevision.manifestId` → `corpusRevision, snapshot (pinned publication IDs)`.
- `architecture/blueprint.md` l.127: add "includes `textMuted` and `tealText` text tokens (OQ-064 / A-027)".

**F-07 — Guest access contradicts A-027.**

`use-cases.md` ASM-082 (l.509):
- Old: "Search and place details (UC-001) and language choice (UC-016) do not require sign-in"
- New: "Guests see Home and onboarding only (A-027); search, place details and every other action show the sign-in sheet SCR-040; `/v1/places` and `/v1/cities` require a bearer token (openapi)". Check that UC-001 preconditions match.

Decision owner: Lê Ngọc Tấn Hiền.

**F-08 — Orphan screens.**

In `ui-ux/README.md` (A-027):
- l.173 SCR-002 "GAP → OQ-062" → "US-032 (supporting)".
- l.183 SCR-012 "GAP → OQ-062" → "US-011 (supporting)".
- OQ-062 status → Closed (A-027).

### Low

**F-09 — Duplicate OQ/ASM IDs** (A-026). Keep the behavioural meanings, which have more references, including in the drawio files. Renumber the structure-view IDs in `diagrams/structure-views.md` only:
- OQ-080 → **OQ-085**, OQ-081 → **OQ-086**, OQ-082 → **OQ-087**, ASM-080 → **ASM-083**. This covers l.509–512, the §1.4 heading (l.211 "raised as OQ-081" → "raised as OQ-086"), l.480 and l.497.
- Mark OQ-085..087 Closed by A-025, and add the note "A-025 refers to these as OQ-080..082 (pre-renumbering)".
- In `physical-view.drawio` cell c14, change "OQ-080 · 1 instance" → "Amazon Linux 2023 arm64 (A-025) · 1 instance".
- Leave `use-cases.md`, `diagrams/README.md` l.32 and `process-view.drawio` unchanged.
- In `docs/00-governance/template-adaptation-log.md` (classDiagram row), change "start at OQ-080, ASM-080" → "start at OQ-085, ASM-083".

**F-10 — Open questions answered by the owner but still Open.** Set the status and answer reference of each of these to "Closed (A-0xx)":
- `api/api-contract.md` OQ-070, OQ-072 and OQ-073 (A-024);
- `use-cases.md` OQ-081 and OQ-083 (A-026);
- `ui-ux/README.md` OQ-060..069 (A-027);
- `data/model.md` OQ-016..020 (A-023).

## 5. Gate result

**FAIL.** Two Critical findings, F-01 and F-02, block the design baseline. Each contradicts a recorded owner decision (A-023, A-024, A-026) in contract artifacts (`data/model.md`, ADR-012, use-cases, sequence diagrams), and they would carry directly into INC-1 code: the Guide index and the deletion job.

No new decision is needed: every fix above was already decided in SRC-100 A-023..A-027. A delta re-audit (DA-GONARRA-02) covering F-01..F-05 is expected to give **PASS WITH CONDITIONS**, with F-06..F-10 as conditions.

| Condition | Owner | Due |
|---|---|---|
| Apply F-01..F-05 and re-run this audit as a delta | Lê Ngọc Tấn Hiền | 2026-11-11 |
| Apply F-06..F-10 | Lê Ngọc Tấn Hiền | 2026-11-18 |
| Security review of the design set (SECURITY_REVIEW_DONE = no) | Lê Ngọc Tấn Hiền | 2026-11-18 |
| Mentor approval of ADR-001..ADR-010 (Proposed) at the design gate | trantrongminh (mentor) | Design gate |

Decision owners: Lê Ngọc Tấn Hiền (all fixes, as owner and designer); trantrongminh (gate approval, ADR acceptance).

## 6. Self-check (§6)

| Item | Status | Evidence |
|---|---|---|
| Every artifact listed with its version | Pass | §1 |
| Every pairwise check has a result | Pass | §2, checks 1–10 |
| Every finding cites both artifacts and locations | Pass | §4 (file + line / section on each side) |
| Orphans, missing flows, drift, ownerless NFRs, orphan screens assessed | Pass | §2, explicit assessments |
| Each artifact has a checklist score | Partial | §3. Only the SAD was re-scored row by row. The others are self-scores adjusted by the findings (Lê Ngọc Tấn Hiền, 2026-11-11, at the delta re-audit) |
| The gate states blocking findings and conditions | Pass | §5 |
| No design file modified | Pass | Writes limited to this file, the adapted prompt and the adaptation-log row |

---

## DA-GONARRA-02 (delta)

| Field | Value |
|---|---|
| Audit ID | DA-GONARRA-02 (delta of DA-GONARRA-01) |
| Date | 2026-11-04 |
| Scope | F-01..F-10, the pairwise checks they touched (1, 2, 3, 4, 5, 7, 8, 10), and the mechanical validations. The fixes were applied by a separate editor; the auditor modified no design file |
| Design set | 0.2 for the edited artifacts (SAD, ADR-010, ADR-012, blueprint, api/api-contract.md, use-cases, diagrams/README, structure-views; history rows cite DA-GONARRA-01) |

### D.1 Validations re-run

| Check | Result |
|---|---|
| `xmllint --noout` on each of the 6 `.drawio` files | All OK |
| `openapi-spec-validator` on `api/openapi.yaml` | OK |
| OQ/ASM/RSK uniqueness script over `docs/` | No collision between artifacts. OQ-080..082 / ASM-080 stay only in `use-cases.md`. Structure-view IDs are now OQ-085..087 / ASM-083. The only remaining multi-file hits are this audit report's own citations and the BRD/intake carry-overs noted in §1.1 |
| Grep "after publication", "re-published", "place stays published" (excluding this file) | 0 hits |
| Grep "receipt", "DELETION_REQUESTED", "DELETING", "until DELETED" | 0 contract hits. The 3 hits in `m13-account-deletion.html` read "Support display ID (deletion job id, not a credential or receipt)", as F-02 item 9 required. The changelog rows in use-cases.md and diagrams/README.md only describe the fix |

### D.2 Status per finding

| Finding | Status | Evidence |
|---|---|---|
| F-01 Embeddings searchable on first publication | **Closed** | `model.md` §6.1 step 6 (l.396–399) and §5 `vw_guide_chunks` (l.370). ADR-012 l.17 and l.38 and ADR-010 l.33 ("before publication", v0.2). SAD DEC-009 l.193, SC-05 l.730 (embed before CMP-005 publish) and l.808. Blueprint l.379 and l.396. README publish sequence: `cli embed` block above `publish`. `process-view.drawio` page 5: embed messages 1–11, publish 12–31, msg 10 "place stays in READY_TO_PUBLISH". Activity page 1: "Compute embeddings" (y=1152) above "Request publish" (y=1290) |
| F-02 Deletion follows OQ-073 | **Closed** | `model.md` §3.2 step 2: DB delete, then the Clerk user last. Step 4 has the 401 rule. UC-014 l.409 and OQ-084 "Closed by A-024/A-026 … no receipt". `process-view.drawio` page 6: msg 10 "202 status(REQUESTED)", msg 13 DB cascade, msg 14 "deleteUser (last step)", msg 18 "401 after IN_PROGRESS ⇒ completed". SAD §3.3.5 l.631 and §3.6.3 l.776–779. Blueprint l.462–467. openapi l.225 and api/api-contract.md API-007 l.367 401 semantics. UI README l.102 states and OQ-066 Closed |
| F-03 SAD domain model and states adopt schema names | **Closed** | SAD §3.1.2: `AccountPreferences`, `CatalogPublication`, `Place "1" -- "0..*" CatalogPublication`, `PreviewRevision ..> CatalogPublication : snapshot pins (no FK)`, `Place "*" -- "*" MediaAsset : via PlaceMedia`, `visitMinutes*`, `/freshness`, and a pointer to structure-views §1.4. SAD §3.3.5 l.627–632 match the schema enums |
| F-04 SAD deployment view complete | **Closed** | SAD §3.4.1: `partners` (Agoda, Booking.com, Klook, 12Go), `eas` Expo EAS Build, `local` Docker Compose subgraph. §3.4.2 adds three rows and Amazon Linux 2023 arm64 on the EC2 row |
| F-05 Booking partners named | **Closed** | api/api-contract.md l.53 and OQ-071 l.567 (Closed). openapi `HandoffLink.partner_key` enum `[agoda, booking_com, klook, twelve_go]` (l.2896–2897) |
| F-06 Pace / travel modes / tokens carried | **Closed** | SAD l.540 "travel modes (WALK/DRIVE)". UC-016 "edits pace, interests and travel modes". Blueprint: no `visitDurationBounds` / `manifestId` left; l.128 has the `textMuted` / `tealText` tokens |
| F-07 Guest access per A-027 | **Closed** | use-cases ASM-082 l.510. UC-001 precondition "Signed in (guests see Home and onboarding only, ASM-082)" |
| F-08 Orphan screens | **Closed** | UI README SCR-002 "US-032 (supporting)" l.174. SCR-012 "US-011 (supporting)" l.184. OQ-062 Closed (A-027) |
| F-09 Duplicate IDs | **Closed** | structure-views l.212 and l.510–515 (OQ-085..087 / ASM-083 Closed (A-025), with the pre-renumbering note). `physical-view.drawio` c14 "OS image: Amazon Linux 2023 arm64 (A-025)". adaptation-log class-diagram row "start at OQ-085, ASM-083". Cosmetic leftover: structure-views l.481 still says "OS image is not set in the SAD (OQ-085)", though OQ-085 is now closed |
| F-10 Answered OQs closed | **Closed** | api/api-contract.md OQ-070/072/073: 3/3. use-cases OQ-081/083: 2/2. UI README OQ-060..069: 10/10. model.md OQ-016..020: 5/5 |

### D.3 New residual finding

**F-11 — Medium — Drift: the place workflow states differ between the API/UI and the schema.**

- `api/openapi.yaml` `WorkflowState` (l.1940) has `[DISCOVERED, IMPORTED, NORMALIZED, MATCH_REVIEW, CONTENT_REVIEW, READY_TO_PUBLISH, PUBLISHED, SUSPENDED, RETIRED]`.
- `ui-ux/README.md` l.103 adds QUARANTINED, and `a02-place-review.html` has a "Quarantine" action.
- `schema.sql` `ck_places_workflow_state` (l.186–187) and SAD §3.3.5 l.627 have only IMPORTED, MATCH_REVIEW, CONTENT_REVIEW, READY_TO_PUBLISH, PUBLISHED and RETIRED.

Fix:
- openapi l.1940 enum → `[IMPORTED, MATCH_REVIEW, CONTENT_REVIEW, READY_TO_PUBLISH, PUBLISHED, RETIRED]`.
- UI README l.103 → "IMPORTED, MATCH_REVIEW, CONTENT_REVIEW, READY_TO_PUBLISH, PUBLISHED, RETIRED".
- Relabel the a02 "Quarantine" action as "Retire", or record "quarantine" as a gate-refused display state (SAD l.807 uses "Quarantine" only for a failed gate).

Decision owner: Lê Ngọc Tấn Hiền. The finding does not block, because no stored value is affected.

### D.4 Updated pairwise table

| # | Check | DA-01 | DA-02 | Evidence |
|---|---|---|---|---|
| 1 | SAD ↔ blueprint | Partial | **Pass** | F-01, F-02, F-06 closed |
| 2 | SAD ↔ diagrams | Partial | **Pass** | F-03, F-04 closed; CMP and lifelines unchanged |
| 3 | SAD ↔ `api/openapi.yaml` | Partial | **Partial** | F-02 and F-05 closed. F-11 `WorkflowState` enum drift remains |
| 4 | SAD ↔ `data/model.md` | Fail | **Pass** | F-01, F-02, F-03 closed |
| 5 | SAD ↔ UI/UX | Partial | **Partial** | F-02 closed. F-11 (UI README l.103, a02 Quarantine) remains |
| 6 | Requirements ↔ design | Pass | Pass | Not affected |
| 7 | NFR ↔ scenario ↔ design | Partial | **Pass** | QAS-10 and FR-058 are now realized consistently |
| 8 | Stories ↔ screens | Partial | **Pass** | F-08 closed |
| 9 | Diagram sources ↔ SAD references | Pass | Pass | Six drawio files are well-formed |
| 10 | Decisions ↔ design | Fail | **Pass** | ADR-010/012 amended. Receipt removed. ASM-082 matches A-027 |

### D.5 Gate result (DA-GONARRA-02)

**PASS WITH CONDITIONS.** No Critical or High finding is open. F-01..F-10 are closed.

| Condition | Owner | Due |
|---|---|---|
| Fix F-11 (WorkflowState enum, UI README l.103, a02 action) and the cosmetic structure-views l.481 | Lê Ngọc Tấn Hiền | 2026-11-18 |
| Security review of the design set (still not done) | Lê Ngọc Tấn Hiền | 2026-11-18 |
| Mentor approval of ADR-001..ADR-010 (Proposed) and of the design baseline | trantrongminh (mentor) | Design gate |

The design owner must accept these conditions before baseline.
