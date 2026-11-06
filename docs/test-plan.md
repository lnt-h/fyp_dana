# Gonarra — Test plan

| Field | Value |
|---|---|
| Version / date | 1.1 / 2026-11-06 (1.1: DEC-022 — curator-review cases replaced by automated-gate cases VT-019, VT-025..VT-028) |
| Owner | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor — [Pending] |
| Replaces | `TEST_PLAN.md`, `TEST_CASES.md`, `RTM.md`, `RESEARCH_PROTOCOL.md` (kept at tag `docs-sdlc-full`; `TC-nnn` cited below refer to that tag) |
| Scope | Đà Nẵng-only release (DEC-013); decisions and open questions in `docs/decisions.md` |

Nothing in this plan has been executed. A check passes only at its stated threshold with evidence stored; missing evidence means `NOT RUN`, not `PASS`.

## 1. What is verified and how

| Layer | Check | When | Command / method |
|---|---|---|---|
| Docs | Links resolve; every `XXX-nnn` ID is defined once; `openapi.yaml` lints; `schema.sql` applies on a fresh PostGIS + pgvector container | Every docs PR | Link-check script over `docs/`; ID uniqueness grep; OpenAPI lint; `psql -f docs/data/schema.sql` against `docker compose up db` |
| API code | Lint, types, unit tests (agents mocked through dependency overrides), OpenAPI export matches the contract | Every push (`.github/workflows/ci.yml`) | `uv run ruff check .` · `uv run mypy app` · `uv run pytest` · `uv run python scripts/export_openapi.py --check` |
| API integration | Repositories, migrations, SSE and quota ledger against a real database; Alembic round-trip | Every push | `docker compose up -d db --wait` · `uv run alembic upgrade head` · `uv run pytest -m integration` · `alembic downgrade base && alembic upgrade head` |
| Mobile | Type check; Expo dependency versions | Every push | `npm run typecheck` · `npm run check:dependencies` |
| AI evals | Golden sets against real providers (Gemini, Groq, Tavily, Routes, Places); results committed as JSON | Nightly and on dispatch only, never per push | `uv run pytest -m eval` in `apps/api/evals/`; Agno `AccuracyEval` with a Groq or Flash-Lite judge; `Case(expected_tool_calls=...)` for the researcher |
| Device / provider | Anything that needs a phone, a native build or a live key (voice STT, photo, maps handoff, bilingual rendering) | Before each release candidate | Manual run on the devices in OQ-112; recorded in `docs/07-verification/evidence/<run-id>/` |

## 2. Acceptance metrics

| Metric | Measures | Approach | Threshold |
|---|---|---|---|
| MET-001 | Planning task completion | Study: participants who save a valid itinerary ÷ participants | ≥ 80% |
| MET-002 | Time to first proposal | Study log: median minutes from request to first displayed proposal | ≤ 3 min |
| MET-003 | Perceived usability | SUS questionnaire after the Gonarra arm | ≥ 70 |
| MET-004 | Conflict detection | Eval: conflict set (calendar + hours + overrun + missing leg), blocking conflict flagged | 100% recall on the conflict set |
| MET-005 | Lock integrity | Eval: locked stops changed after day regeneration | 0 |
| MET-006 | Saved-trip integrity | Failure injection {AI, Routes, network} × {generate, edit, Save, regenerate}, 3 runs per cell | 0 saved trips changed without Save; 0 unsaved edits lost |
| MET-007 | Guide grounding | Eval: citation validity (every claim cites supplied evidence) plus a 20% human claim-to-source sample (OQ-111) | ≥ 95% |
| MET-008 | Correct refusal | Eval: `insufficient_evidence` precision and recall on answerable + out-of-evidence sets | P and R ≥ 90% |
| MET-011 rev. 2 | Catalog coverage | Weekly report from `GET /v1/admin/cities/summary` | ≥ 100 auto-published bilingual places in Đà Nẵng passing the automated gate, ≥ 30 in the Hội An area codes |
| MET-014 | Itinerary errors per day | `evals/score_itinerary.py` on study outputs: closed place, wrong hours, non-existent place, per planned day | Reported per arm; Gonarra lower than the baseline is the thesis claim, no pass threshold |
| Eval-only | Selection validity | Selector output IDs ⊆ candidates, no duplicates, must-sees present (after ≤ 1 repair) | 100% |
| Eval-only | Hallucinated-place rate | Stops whose `place_id` is not a published Đà Nẵng place and not a labelled web candidate | 0 |
| Eval-only | Determinism | Same request, same cached matrix, same selection → identical plan snapshot | Identical |

## 3. Golden sets

Location: `apps/api/evals/golden/`. Built by the owner from the published catalog, frozen before tuning (tag `EVS-v1.0`, content hash in the run report); a change after freezing creates `v1.1` and both versions are reported.

| File | Size | Content | Used by |
|---|---|---|---|
| `facts_danang.yaml` | 50 places | Name VI/EN, area, opening hours, weekly closure, ticket rule, status, source URL and source-check date, taken from published `place_facts` and checked by the owner against the source for scoring only (not a catalog review; RSK-105) | MET-004, MET-014 scoring, VT-006..008 |
| `planning_prompts.yaml` | 20 prompts | VI and EN, 1–3 days, with and without must-sees; dates deliberately hitting Mondays, lunar 14th (lantern night) and Tết 2027-02-06 | Selection validity, hallucinated-place rate, determinism, MET-004 |
| `guide_answerable.yaml` | 30 questions | Answerable from approved facts and chunks, VI and EN, place- and city-scoped, with expected evidence IDs | MET-007, MET-008 recall |
| `guide_out_of_evidence.yaml` | 10 questions | Not supported by approved evidence (open-web-only facts, other cities, opinions) | MET-008 precision, VT-014 |

Maintenance: a pipeline or source change to a place in `facts_danang.yaml` re-exports that entry in the same PR; `pytest -m eval` fails if a fact in the set no longer matches the approved fact in the database.

## 4. Verification tasks

Level: U unit · I integration · E eval (real providers) · M manual. `TC-nnn` = case in the retired `TEST_CASES.md`.

| ID | Verifies | Level | Expected result | Source |
|---|---|---|---|---|
| VT-001 | Search by Vietnamese name with diacritics, by English name and by ASCII alias | I | Same published place in the first 5 results for all three forms; disabled-city places never appear | TC-001..003, AC-001 |
| VT-002 | Proposal when the catalog pool is sufficient | I, E | Every stop is a published Đà Nẵng place; researcher not invoked; `research_used=false`; ≤ 1 Flash + 1 Flash-Lite call | TC-051, DEC-015 |
| VT-003 | Proposal with research (thin pool or unmet asks) | E | Researcher runs within caps (≤ 2 Tavily, ≤ 3 fetches, ≤ 3 Places checks); web stops carry `WEB_UNVERIFIED`, source URL, `fetched_at`; one `web_place_candidates` row each | DEC-015, OQ-127 |
| VT-004 | Invalid-ID injection in selector output | U | ID not in candidates, unknown field or model-supplied distance → validation failure, one repair, then rule-based fallback; no place created | TC-056, TC-057 |
| VT-005 | Calendar: weekly closure (Monday) | U, E | Stop planned on a closed weekday → `CLOSED_ON_DATE` naming stop, date and `rule_id` | DEC-016 |
| VT-006 | Calendar: lantern night (lunar 14th) and Tết | U, E | Lunar conversion matches test vectors (Tết 2026-02-17, 2027-02-06); affected stops flagged `LUNAR_EVENT_CONFLICT` or `SEASONAL_WARNING` with the rule's bilingual note from the YAML file | OQ-125 |
| VT-007 | Calendar: same-day ticket validity | U | Old Town stops split across two days → `TICKET_VALIDITY` conflict with both `stop_ids` | DEC-016 |
| VT-008 | Web stop saved with WARNING cap | I | Plan with one `WEB_UNVERIFIED` stop: Plan Health ≤ WARNING, never OK; Save succeeds after acknowledgement (OQ-128); `vw_trip_stop_trust` upgrades once the candidate is auto-promoted and published by the gate | DEC-015, DEC-022 |
| VT-009 | Lock + single-day regeneration | I | Only the target day changes; locked stop keeps place, day and duration; saved trip untouched until Save | TC-124, TC-125, TC-129 |
| VT-010 | Edit + Save idempotency | I | Save without `Idempotency-Key` → 400; same key + same body → same response; same key + different body → 422 `idempotency_key_mismatch` | TC-106 |
| VT-011 | Revision conflict | I | Save or edit on a stale revision → 409 `revision_conflict`; newer revision kept | TC-095 |
| VT-012 | Late provider result | I | Result arriving after a newer edit never overwrites the newer revision or the saved trip | TC-115 |
| VT-013 | Guide answerable question | E | Answer in the request language; every claim cites ≥ 1 supplied evidence ID; citations show verification date | TC-146, TC-147 |
| VT-014 | Guide unanswerable question | E | `insufficient_evidence`, no answer text, no web call when research is off or quota is spent | TC-144, TC-145 |
| VT-015 | Guide web fallback labelled | E | Evidence insufficient and quota available → `ANSWERED_WEB_UNVERIFIED`; citations `evidence_kind=WEB` with URL and `fetched_at`; badge shown on screen | DEC-017 |
| VT-016 | Citation validation | U | Claim whose evidence ID is not in the supplied set is dropped; zero remaining claims → `INSUFFICIENT_EVIDENCE` | DEC-017 |
| VT-017 | Quota cap degrade path | I | Ledger at cap → selector falls back to rule-based ranking, rationales null, research skipped, Guide returns a quota status; no provider call is made; plan still completes | DEC-018 |
| VT-018 | Account deletion | I, M | Status IN_PROGRESS → completed; Clerk user deleted last; no record in live service or logs; restore re-applies deletion | TC-191..194 |
| VT-019 rev. 1 | Web-candidate auto-promotion (replaces "admin queue promote / reject", DEC-022) | I | `EXISTS_OPERATIONAL` inside the boundary → exactly one `IMPORTED` place + external identity, re-run creates none; outside boundary, closed or not found → no place, stop stays `WEB_UNVERIFIED`; promotion alone never publishes | FR-101 rev. 1, DEC-022 |
| VT-020 | Redactor never leaks | U, I | No account ID, e-mail, phone or raw coordinate in any prompt or search query to Gemini, Groq or Tavily; redactor fails closed; logs exclude tokens, locations, questions, prompts | TC-169, TC-239, BR-046 |
| VT-021 | SSE event order | I | Stages arrive in order VALIDATING_REQUEST → SELECTING_PLACES → [RESEARCHING → VERIFYING_WEB_PLACES] → ROUTING → SCHEDULING → CHECKING_HEALTH → WRITING → `preview_ready`; first event p95 ≤ 2 s | TC-224 |
| VT-022 | Ownership before any call | I | Another account's trip or session → refused; no model, routing or search call made | TC-188, TC-189 |
| VT-023 | Bilingual surfaces | M | Place card, conflicts, trust labels (`trust.verified` = "Source-checked · <date>" / "Đã đối chiếu nguồn · <date>", `trust.web`) and Guide answers render in VI and EN from published content, on device | DEC-019, DEC-022 |
| VT-024 | Failure injection matrix | I, M | 36 runs (27 if regeneration is cut) per release candidate; MET-006 = 0 | TC-117 |
| VT-025 | Automated gate rejects incomplete candidates | U, I | Each of: missing VI content, missing EN content, location outside the Đà Nẵng boundary, no category, a shown fact without an attributed source revision, a cited source without a licence → not published, the failed check named in the run report and counted per reason in the city summary; a complete candidate publishes with actor `system:gonarra-pipeline` | FR-013 rev. 1, FR-014 rev. 1, DEC-022 |
| VT-026 | Auto-publish idempotent; unpublish sticks | I | Running the gate twice on unchanged input creates no second publication and no duplicate place; an operator-unpublished place is not re-published by the next run unless its source revision changes; unpublish and city summary refused for non-operators | FR-014 rev. 1, FR-018 rev. 1, NFR-012 rev. 1 |
| VT-027 | No model publishes; verbatim-quote rule; unknown stays unknown | U | No code path from `agents`/`ai` writes publications, `place_facts` or `place_closure_rules` (import-linter + test); a model-extracted fact whose quote is not found verbatim in the fetched text is rejected; a CSV/open-data row without a source yields "unknown" | BRU-002 rev. 1, FR-011 rev. 1 |
| VT-028 | Copy never claims human review; closure YAML load | U, M | Grep of VI/EN locale files and API-served strings finds 0 occurrences of "Verified", "reviewed", "kiểm duyệt", "curator"; `VERIFIED` renders "Source-checked · <date>" / "Đã đối chiếu nguồn · <date>"; loading `closure_rules/da-nang.yaml` twice is idempotent, records the git revision and rejects an invalid rule naming it | FR-098 rev. 1, FR-107 rev. 1, DEC-022 |

## 5. Comparative user study (DEC-020)

| Element | Protocol |
|---|---|
| Participants | 10–15 adults (≥ 18), ≥ 4 using VI and ≥ 4 using EN; no one who worked on or pre-tested Gonarra; recruited per OQ-113; no payment |
| Design | Within-subject: each participant plans the same two Đà Nẵng prompts (one Hội An-area, one city-centre, 2 days each, fixed dates), once with Gonarra and once with ChatGPT or Gemini (OQ-130); tool order counterbalanced; baseline tool and model version recorded per session |
| Measures | MET-014 errors per day, scored by `evals/score_itinerary.py` against `facts_danang.yaml` and the calendar module for both arms (baseline itineraries pasted as text); trust rating 1–5 per itinerary; whether the trust label was noticed (asked after the Gonarra arm); SUS for Gonarra (MET-003); MET-001, MET-002 from the study log |
| Session | About 50 minutes, in person on an owner-provided Android phone and a laptop for the baseline; pseudonymous codes `P01`..`P15`; observer sheet; no audio or video |
| Data handling | Pseudonymous logs only (no request text, no account ID); consent forms stored separately; data kept until 2027-06-30 then destroyed; withdrawal possible until then; AI notice: content goes to Google, Groq and Tavily under free-tier terms, nothing personal is sent (BR-046); ethics and consent template per OQ-004 |
| Schedule | Pilot 2027-01-16 or 2027-01-17; sessions 2027-01-18 → 2027-01-29 over ≥ 2 days so free quotas are not exhausted (RSK-013); eval harness runs on Groq/Flash-Lite on study days |
| Reporting | Per arm and per language; descriptive only, no statistical generalisation claimed |

## 6. Entry and exit criteria

- Entry (any level): commit recorded; CI `api` and `mobile` green on it; `/health` and `/ready` return 200 on the target environment.
- Entry (evals, acceptance): golden sets frozen and tagged; MET-011 rev. 2 met for runs on the real catalog; migrations at head on a clean database.
- Entry (study): OQ-004 and OQ-131 answered and consent approved; VT-001..VT-028 passed on the study build; pilot session done.
- Exit (release candidate): all Must criteria pass; MET-004 = 100%, MET-005 = 0, MET-006 = 0, MET-007 ≥ 95%, MET-008 ≥ 90%, selection validity 100%, hallucinated-place rate 0; 0 open blocking defects.
- Exit (release candidate): Should/Could features pass their checks or are disabled and recorded as cut under DEC-003 rev. 1 with the approver's agreement.
- Exit (cost): USD 0 cash spend to date.
- Suspend when CI is red on the tested commit, a privacy or data-integrity defect is open, a free quota is exhausted, or a golden set changed without a new version; resume after the fix and a re-run of the affected suite.
- Study results (MET-001..003, MET-014) are reported, not release gates.
