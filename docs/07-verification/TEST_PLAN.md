# Master Test Plan — Gonarra

| Field | Value |
|---|---|
| Version / date | 2.1 / 2026-11-09 |
| Owner | Lê Ngọc Tấn Hiền |
| Approver | FYP mentor — [Pending] |
| Scope | Đà Nẵng-only FYP release, including the Hội An area (DEC-013); decisions and open questions in [`docs/decisions.md`](../decisions.md) |
| Companion | [Research protocol](RESEARCH_PROTOCOL.md) (comparative user study, consent forms, session script) |
| History | 2.0 condenses the 2026-11-04 IEEE 829 set (test plan 0.1, `TEST_CASES.md`, `RTM.md`) and the condensed test plan 1.2 of 2026-11-08 (DEC-022, DEC-023, DEC-025); 2.1 applies DEC-031..DEC-034 (no AI catalog content, Wikivoyage, description optional, API hardening) and MET-011 rev. 4. The full set is kept at git tag `docs-sdlc-full`; `TC-nnn` cited below refer to `TEST_CASES.md` at that tag. |

Nothing in this plan has been executed as an acceptance run. A check passes only at its stated threshold with
evidence stored; missing evidence means `NOT RUN`, not `PASS`. Unit and integration suites exist and run in CI
(§7); AI evals, golden sets and device checks do not exist yet (M4).

## 1. What is verified and how

| Layer | Check | When | Command / method |
|---|---|---|---|
| Docs | Relative links resolve; every `XXX-nnn` ID is defined once; `openapi.yaml` lints; `schema.sql` applies on a fresh PostGIS + pgvector container | Every docs PR | Link-check script over `docs/`; ID uniqueness grep; OpenAPI lint; `psql -f docs/04-design/data/schema.sql` against `docker compose up db` |
| API static | Lint, strict types, import contracts (architecture layering; Agno confined to `app/agents/` and `app/ai/`) | Every push and PR | `uv run ruff check .` · `uv run mypy app` · `uv run lint-imports` |
| API unit | Domain, scheduling, Plan Health, calendar, validators, redactor, quota ledger; agents and providers faked through dependency overrides | Every push and PR | `uv run pytest` (integration excluded by default) |
| API contract | Generated OpenAPI matches the committed `apps/api/openapi.json` | Every push and PR | `uv run python scripts/export_openapi.py --check` |
| API integration | Repositories, migrations, seed, SSE, Save/idempotency and quota ledger against a real database; Alembic round trip | Every push and PR | `docker compose up -d db --wait` · create a scratch database named `gonarra_<x>_test` (the name must end `_test`, `_it` or `_ci`; DEC-034) · `GONARRA_DATABASE_URL=...gonarra_<x>_test uv run alembic upgrade head` · `... uv run python -m app.cli seed` · `... uv run pytest -m integration` · `... uv run alembic downgrade base && ... uv run alembic upgrade head` |
| API image | Docker image builds for arm64 and amd64 | Every push and PR | `docker buildx build --platform linux/arm64,linux/amd64 .` |
| Mobile | Type check; Expo dependency versions | Every push and PR | `npm run typecheck` · `npm run check:dependencies` |
| AI evals | Golden sets (§3) against real providers (Gemini, Groq, Tavily, routing); results committed as JSON | Nightly and on dispatch only, never per push (planned, M4) | `uv run pytest -m eval` (marker and `apps/api/evals/` not created yet); Agno `AccuracyEval` with a Groq or Flash-Lite judge; `Case(expected_tool_calls=...)` for the researcher |
| Device / provider | Anything that needs a phone, a native build or a live key (bilingual rendering, maps handoff, voice STT, photo) | Before each release candidate | Manual run on the devices in OQ-112; evidence in `docs/07-verification/evidence/<run-id>/` (created at the first run) |

## 2. Acceptance metrics

| Metric | Measures | Approach | Threshold |
|---|---|---|---|
| MET-001 | Planning task completion | Study: participants who save a valid itinerary ÷ participants | ≥ 80% |
| MET-002 | Time to first proposal | Study log: median minutes from request to first displayed proposal | ≤ 3 min |
| MET-003 | Perceived usability | SUS questionnaire after the Gonarra arm | ≥ 70 |
| MET-004 | Conflict detection | Eval: conflict set (calendar + hours + overrun + missing leg), blocking conflict flagged | 100% recall on the conflict set |
| MET-005 | Lock integrity | Eval: locked stops changed after day regeneration | 0 |
| MET-006 | Saved-trip integrity | Failure injection {AI, routing, network} × {generate, edit, Save, regenerate}, 3 runs per cell (§5) | 0 saved trips changed without Save; 0 unsaved edits lost |
| MET-007 | Guide grounding | Eval: citation validity (every claim cites supplied evidence) plus a 20% human claim-to-source sample (OQ-111) | ≥ 95% |
| MET-008 | Correct refusal | Eval: `insufficient_evidence` precision and recall on answerable + out-of-evidence sets | P and R ≥ 90% |
| MET-011 rev. 4 | Catalog coverage | Weekly report from `GET /v1/admin/cities/summary`; count of places with human-written VI+EN descriptions; random 10% `audit-sample` CSV of published places hand-checked by the owner (DEC-033) | ≥ 100 auto-published complete-card places in Đà Nẵng passing the code gate, ≥ 30 in the Hội An area; human-written description count and audit accuracy reported in the thesis |
| MET-014 | Itinerary errors per day | `evals/score_itinerary.py` on study outputs: closed place, wrong hours, non-existent place, per planned day | Reported per arm; Gonarra lower than the baseline is the thesis claim, no pass threshold |
| Eval-only | Selection validity | Selector output IDs ⊆ candidates, no duplicates, must-sees present (after ≤ 1 repair) | 100% |
| Eval-only | Hallucinated-place rate | Stops whose `place_id` is not a published Đà Nẵng place and not a labelled web candidate | 0 |
| Eval-only | Determinism (NFR-032) | Same request, same cached matrix, same selection → identical plan snapshot | Identical |

Performance thresholds (NFR-001, NFR-002, NFR-004, NFR-006) are measured on the release candidate with scripted
query, request and edit sets; study-day availability (NFR-008) by 1-minute probes.

## 3. Golden sets

Location (planned): `apps/api/evals/golden/`. Built by the owner from the published catalog, frozen before tuning
(tag `EVS-v1.0`, content hash in the run report); a change after freezing creates `v1.1` and both versions are reported.

| File | Size | Content | Used by |
|---|---|---|---|
| `facts_danang.yaml` | 50 places | Name VI/EN, area, opening hours, weekly closure, ticket rule, status, source URL and source-check date, taken from published `place_facts` and checked by the owner against the source for scoring only (not a catalog review; RSK-105) | MET-004, MET-014 scoring, VT-005..VT-007 |
| `planning_prompts.yaml` | 20 prompts | VI and EN, 1–3 days, with and without must-sees; dates deliberately hitting Mondays, lunar 14th (lantern night) and Tết 2027-02-06 | Selection validity, hallucinated-place rate, determinism, MET-004 |
| `guide_answerable.yaml` | 30 questions | Answerable from approved facts and chunks, VI and EN, place- and city-scoped, with expected evidence IDs | MET-007, MET-008 recall |
| `guide_out_of_evidence.yaml` | 10 questions | Not supported by approved evidence (open-web-only facts, other cities, opinions) | MET-008 precision, VT-014 |

Maintenance: a pipeline or source change to a place in `facts_danang.yaml` re-exports that entry in the same PR;
`pytest -m eval` fails if a fact in the set no longer matches the approved fact in the database.

## 4. Verification tasks

Level: U unit · I integration · E eval (real providers) · M manual.

| ID | Verifies | Level | Expected result | Source |
|---|---|---|---|---|
| VT-001 | Search by Vietnamese name with diacritics, by English name and by ASCII alias | I | Same published place in the first 5 results for all three forms; disabled-city places never appear | TC-001..003, AC-001 |
| VT-002 | Proposal when the catalog pool is sufficient | I, E | Every stop is a published Đà Nẵng place; researcher not invoked; `research_used=false`; ≤ 1 selector + 1 writer call | TC-051, DEC-015, DEC-026 |
| VT-003 | Proposal with research (thin pool or unmet asks) | E | Researcher runs within caps (≤ 2 Tavily, ≤ 3 fetches, ≤ 3 existence checks); web stops carry `WEB_UNVERIFIED`, source URL, `fetched_at`; one `web_place_candidates` row each | DEC-015, OQ-127, OQ-134 |
| VT-004 | Invalid-ID injection in selector output | U | ID not in candidates, unknown field or model-supplied distance → validation failure, one repair, then rule-based fallback; no place created | TC-056, TC-057 |
| VT-005 | Calendar: weekly closure (Monday) | U, E | Stop planned on a closed weekday → `CLOSED_ON_DATE` naming stop, date and `rule_id` | DEC-016 |
| VT-006 | Calendar: lantern night (lunar 14th) and Tết | U, E | Lunar conversion matches test vectors (Tết 2026-02-17, 2027-02-06); affected stops flagged `LUNAR_EVENT_CONFLICT` or `SEASONAL_WARNING` with the rule's bilingual note from the YAML file | OQ-125 |
| VT-007 | Calendar: same-day ticket validity | U | Old Town stops split across two days → `TICKET_VALIDITY` conflict with both `stop_ids` | DEC-016 |
| VT-008 | Web stop saved with WARNING cap | I | Plan with one `WEB_UNVERIFIED` stop: Plan Health ≤ WARNING, never OK; Save succeeds only with acknowledgement (OQ-128); `vw_trip_stop_trust` upgrades once the candidate is auto-promoted and published by the gate | DEC-015, DEC-022 |
| VT-009 | Lock + single-day regeneration | I | Only the target day changes; locked stop keeps place, day and duration; saved trip untouched until Save | TC-124, TC-125, TC-129 |
| VT-010 | Edit + Save idempotency | I | Save without `Idempotency-Key` → 400; same key + same body → same response; same key + different body → 422 `idempotency_key_mismatch` | TC-106 |
| VT-011 | Revision conflict | I | Save or edit on a stale revision → 409 `revision_conflict`; newer revision kept; the first Save of a new trip succeeds | TC-095 |
| VT-012 | Late provider result | I | Result arriving after a newer edit never overwrites the newer revision or the saved trip | TC-115 |
| VT-013 | Guide answerable question | E | Answer in the request language; every claim cites ≥ 1 supplied evidence ID; citations show verification date | TC-146, TC-147 |
| VT-014 | Guide unanswerable question | E | `insufficient_evidence`, no answer text, no web call when research is off or quota is spent | TC-144, TC-145 |
| VT-015 | Guide web fallback labelled | E | Evidence insufficient and quota available → `ANSWERED_WEB_UNVERIFIED`; citations `evidence_kind=WEB` with URL and `fetched_at`; badge shown. **Not implemented yet** (extension point in `app/guide/service.py`); `NOT RUN` until it lands | DEC-017 |
| VT-016 | Citation validation | U | Claim whose evidence ID is not in the supplied set is dropped; zero remaining claims → `INSUFFICIENT_EVIDENCE` | DEC-017 |
| VT-017 | Quota cap degrade path | I | Ledger at cap → selector falls back to rule-based ranking, rationales null, research skipped, Guide returns a quota status; no provider call is made; plan still completes | DEC-018 |
| VT-018 | Account deletion | I, M | Status IN_PROGRESS → completed; requests during deletion → 409 `deletion_in_progress`; Clerk user deleted; no record in live service or logs; restore re-applies deletion; reachable from the app | TC-191..194 |
| VT-019 rev. 1 | Web-candidate auto-promotion | I | Existence check positive inside the boundary → exactly one `IMPORTED` place + external identity, re-run creates none; outside boundary, closed or not found → no place, stop stays `WEB_UNVERIFIED`; promotion alone never publishes | FR-101 rev. 1, DEC-022 |
| VT-020 | Redactor never leaks | U, I | No account ID, e-mail, phone or raw coordinate in any prompt or search query to Gemini, Groq or Tavily; redactor fails closed; logs exclude tokens, locations, questions, prompts | TC-169, TC-239, BR-046 |
| VT-021 | SSE event order | I | Stages arrive in order VALIDATING_REQUEST → SELECTING_PLACES → [RESEARCHING → VERIFYING_WEB_PLACES] → ROUTING → SCHEDULING → CHECKING_HEALTH → WRITING → `preview_ready`; first event p95 ≤ 2 s | TC-224 |
| VT-022 | Ownership before any call | I | Another account's trip or session → refused; no model, routing or search call made | TC-188, TC-189 |
| VT-023 | Bilingual surfaces | M | Place card, conflicts, trust labels ("Source-checked · <date>" / "Đã đối chiếu nguồn · <date>", web label) and Guide answers render in VI and EN from published content, on device | DEC-019, DEC-022 |
| VT-024 | Failure injection matrix | I, M | 36 runs (27 if regeneration is cut) per release candidate; MET-006 = 0 | TC-117 |
| VT-025 | Automated gate rejects incomplete candidates | U, I | Each of: missing VI content, missing EN content, location outside the Đà Nẵng boundary, no category, a shown fact without an attributed source revision, a cited source without a licence → not published, the failed check named in the run report and counted per reason in the city summary; a complete candidate publishes with actor `system:gonarra-pipeline` | FR-013 rev. 1, FR-014 rev. 1, DEC-022 |
| VT-026 | Auto-publish idempotent; unpublish sticks | I | Running the gate twice on unchanged input creates no second publication and no duplicate place; an operator-unpublished place is not re-published unless its source revision changes; unpublish and city summary refused for non-operators | FR-014 rev. 1, FR-018 rev. 1, NFR-012 rev. 1 |
| VT-027 | No model authors catalog content; unknown stays unknown | U | No code path from `agents`/`ai` writes publications, `place_facts`, descriptions or `place_closure_rules` (import-linter + test); the gate rule `AI_CONTENT` rejects any localization with `translation_origin` `AI_SUMMARY`/`AI_DRAFT` and any fact with `origin = AI_EXTRACTED`; a CSV/open-data row without a source yields "unknown" (DEC-031) | BRU-002 rev. 3, FR-011 rev. 2 |
| VT-028 | Copy never claims human review; closure YAML load | U, M | Grep of VI/EN locale files and API-served strings finds 0 occurrences of "Verified", "reviewed", "kiểm duyệt", "curator"; `VERIFIED` renders "Source-checked · <date>" / "Đã đối chiếu nguồn · <date>"; Wikivoyage text shows its attribution and CC BY-SA 4.0 link (DEC-032); no catalog surface carries an AI label; loading `closure_rules/da-nang.yaml` twice is idempotent, records the git revision and rejects an invalid rule naming it | FR-098 rev. 1, FR-107 rev. 1, DEC-022, DEC-032 |
| VT-029 | Estimated legs stay out of acceptance | U, I | Estimate routing refuses to start when `GONARRA_ENVIRONMENT` is `staging` or `production`; estimated legs carry `estimated=true` and INFO `LEG_ESTIMATED`, are shown with "≈" and are never cached | DEC-023, BRU-006 rev. 1 |

### 4.1 Reference journey HA-02 (two days in the Hội An area)

The end-to-end acceptance case from the PRD (§11.2), run on one Android device and one iPhone unless iOS is cut.

| Step | Action | Expected result |
|---|---|---|
| 1 | Language VI; request a 2-day Hội An-area trip | Proposal of published Đà Nẵng places only; timeline and map show the same revision; every leg shows mode, distance and duration or "unavailable" |
| 2 | Resolve any blocking conflict by editing; Save | Save refused while blocked; after recalculation, Save succeeds; a repeated Save creates one version |
| 3 | Reopen; lock one day-2 stop; regenerate day 2 | Day 1 identical; locked stop keeps place, day and duration; new day 2 is an unsaved proposal |
| 4 | Inject an AI, a routing and a network failure during regeneration | Saved trip unchanged; unsaved edits and the lock still present; no invented place, fact or distance |
| 5 | Retry, Save; attempt a second Save from a stale copy | New version saved once; stale Save refused with conflict; reopening shows the accepted version |
| 6 | Open a day-2 place card, directions, stay and transport handoff | Both names, Vietnamese address, entrance or "unknown"; maps app opens; partners open with the area and dates |

Steps 1, 2, 4 (without lock), 5 and 6 are Must; step 3 is recorded "Not applicable — cut" if lock/regeneration is cut.

## 5. Failure injection, security, accessibility and bilingual checks

- **Failure injection (MET-006).** Provider adapters are injected through FastAPI dependencies; tests swap in
  fault-injecting adapters (HTTP 503, timeout, schema-invalid body, 429 quota, late result). Client network failures
  are produced with airplane mode during SSE and Save. Each run snapshots the saved trip and the unsaved edits before
  injection and compares them after recovery.
- **Security and privacy.** Cross-account access to every private resource type (0 disclosures, 0 external calls);
  missing, invalid, expired and foreign-issuer credentials on every private operation (NFR-012 rev. 1); non-operator
  token on `/v1/admin/*`; redactor and captured provider payloads (BR-046, 20 per provider); canary strings
  (token, coordinates, question text) absent from logs after an HA-02 + Guide run (NFR-017); secret scan of the
  repository and mobile bundle; the shared demo user (`GONARRA_DEMO_SHARED_USER`) refused outside development, test
  and demo.
- **Accessibility (NFR-022, WCAG 2.1 AA selected criteria).** Screen-reader labels in both languages, text contrast
  ≥ 4.5:1, usable at 200% system text, Plan Health reasons exposed as text, not only colour. Tools: Android
  Accessibility Scanner + TalkBack, iOS Accessibility Inspector + VoiceOver, contrast checker on screenshots.
- **Bilingual (NFR-026).** i18n key parity between `vi` and `en` with no empty values; every traveller screen walked in
  each language with 0 untranslated strings; Guide answers 100% in the request language; times in Vietnam local time
  whatever the device time zone; content never machine-translated, paraphrased or AI-written to pass the gate
  (DEC-031); a place without a human-written description shows "No description yet" / "Chưa có mô tả" (DEC-033).

Defect severity: **Blocking** breaks a Must criterion, an exit metric, privacy or data integrity, or prevents a
study task — fixed before exit; **Major** breaks a Should criterion or degrades a Must one with a workaround — fixed
or cut under DEC-003 rev. 1; **Minor** is cosmetic — fixed if time permits. Defects are logged as `DEF-xxx` in
`docs/07-verification/evidence/defects.md` and as GitHub issues.

## 6. Comparative user study (DEC-020)

Full procedure, consent forms and script: [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md).

| Element | Protocol |
|---|---|
| Participants | 10–15 adults (≥ 18), ≥ 4 using VI and ≥ 4 using EN; no one who worked on or pre-tested Gonarra; recruited per OQ-113; no payment |
| Design | Within-subject: each participant plans the same two Đà Nẵng prompts (one Hội An-area, one city-centre, 2 days each, fixed dates), one with Gonarra and one with ChatGPT or Gemini (OQ-130); tool order counterbalanced; baseline tool and model version recorded per session |
| Measures | MET-014 errors per day, scored by `evals/score_itinerary.py` against `facts_danang.yaml` and the calendar module for both arms (baseline itineraries pasted as text); trust rating 1–5 per itinerary; whether the trust label was noticed (asked after the Gonarra arm); SUS for Gonarra (MET-003); MET-001, MET-002 from the study log |
| Session | About 50 minutes, in person on an owner-provided phone and a laptop for the baseline; pseudonymous codes `P01`..`P15`; observer sheet; no audio or video |
| Data handling | Pseudonymous logs only (no request text, no account ID); consent forms stored separately; data kept until 2027-06-30 then destroyed; withdrawal possible until then; AI notice: content goes to Google, Groq and Tavily under free-tier terms, nothing personal is sent (BR-046); ethics and consent template per OQ-004 |
| Schedule | Pilot 2027-01-16 or 2027-01-17; sessions 2027-01-18 → 2027-01-29 over ≥ 2 days so free quotas are not exhausted (RSK-013); eval harness runs on Groq/Flash-Lite on study days |
| Reporting | Per arm and per language; descriptive only, no statistical generalisation claimed |

## 7. Test environments and commands

| Environment | Purpose | Notes |
|---|---|---|
| Local | Development, unit and integration runs | PostgreSQL 16 + PostGIS + pgvector from the root `docker-compose.yml`; `apps/api/.env` is never committed. Run unit tests with `GONARRA_DEMO_SHARED_USER` off, and integration tests against a freshly migrated scratch database whose name ends `_test` / `_it` / `_ci` (DEC-034 refuses the developer catalog) |
| CI (GitHub Actions, `.github/workflows/ci.yml`) | Gate on every pull request and every push to `main` | Job `api`: Python 3.12 via `uv`, `uv sync --locked --all-groups`, then the API commands below and the multi-arch image build; job `mobile`: Node 22, `npm ci`, then the mobile commands |
| Demo (`GONARRA_ENVIRONMENT=demo`) | Owner demos only | May enable estimate routing (DEC-023) and the shared demo user (`GONARRA_DEMO_SHARED_USER`, mobile `EXPO_PUBLIC_DEMO_NO_AUTH`). Never used for acceptance or study runs |
| Staging | Performance, failure injection, acceptance | Second Compose project and database on the study host (OQ-110, OQ-129); measured router only (OQ-132) |
| Devices | Bilingual rendering, accessibility, HA-02, voice, photo | Devices per OQ-112; native builds needed for STT |

API (`apps/api`):

```bash
uv run ruff check .
uv run mypy app
uv run lint-imports
uv run pytest                                   # unit; integration excluded by default
uv run python scripts/export_openapi.py --check
docker compose up -d db --wait                  # from the repository root
docker compose exec -T db createdb -U gonarra gonarra_it   # name must end _test / _it / _ci (DEC-034)
export GONARRA_DATABASE_URL=postgresql+asyncpg://gonarra:gonarra@localhost:5432/gonarra_it
uv run alembic upgrade head
uv run python -m app.cli seed
uv run pytest -m integration
uv run alembic downgrade base && uv run alembic upgrade head
uv run pytest -m eval                           # planned (M4): real providers, nightly only
```

Mobile (`apps/mobile`): `npm run typecheck` · `npm run check:dependencies`.

## 8. Entry and exit criteria

- Entry (any level): commit recorded; CI `api` and `mobile` green on it; `/health` and `/ready` return 200 on the target environment.
- Entry (evals, acceptance): golden sets frozen and tagged; MET-011 rev. 4 met for runs on the real catalog; acceptance and study runs use a measured router, never the estimate provider (DEC-023, OQ-132); migrations at head on a clean database.
- Entry (study): OQ-004 and OQ-131 answered and consent approved; VT-001..VT-029 passed on the study build (VT-015 only if the Guide web fallback ships); pilot session done.
- Exit (release candidate): all Must criteria pass; HA-02 passes; MET-004 = 100%, MET-005 = 0, MET-006 = 0, MET-007 ≥ 95%, MET-008 ≥ 90%, selection validity 100%, hallucinated-place rate 0; 0 open blocking defects.
- Exit (release candidate): Should/Could features pass their checks or are disabled and recorded as cut under DEC-003 rev. 1 with the approver's agreement.
- Exit (cost): USD 0 cash spend to date (NFR-033).
- Suspend when CI is red on the tested commit, a privacy or data-integrity defect is open, a free quota is exhausted, or a golden set changed without a new version; resume after the fix and a re-run of the affected suite.
- Study results (MET-001..003, MET-014) are reported, not release gates.

## 9. Deliverables

| Deliverable | When | Location |
|---|---|---|
| This plan and the research protocol | M0 sign-off | `docs/07-verification/` |
| Frozen golden sets `EVS-v1.0` and eval harness | M4 (by 2027-01-15) | `apps/api/evals/` |
| Run evidence and defect log | Each run | `docs/07-verification/evidence/<run-id>/` |
| Test summary report with anonymised study results | 2027-01-31 (M6) | `docs/07-verification/TEST_REPORT.md` (to be written) |
