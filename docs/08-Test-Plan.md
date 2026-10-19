# DaNavi — Test Plan and Evaluation

Version 1.3 | 2026-10-19 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Test plan control and strategy

Identifier DN-MTP-1.3. Scope: native mobile, API/session/ownership, database/migrations, curation/media, external map handoff, read-only essentials cache, Routes/model adapters and the core journey. Future features and third-party internal correctness are excluded; dependency failure handling is included. P1 cases 31–33 are deferred unless scope is activated. TC-36 is retired and its ID is not reused. Every runtime result is currently NOT RUN; design/schema checks do not count as app tests.
Unit: deterministic schedule/constraints, reorder/state transitions, GPS filtering, evidence handling. Integration: API plus isolated real PostgreSQL/PostGIS/pgvector; migrations, concurrency, ownership. System/E2E: native flow with deterministic provider fixtures plus separate real-provider smoke/evaluation. Field: actual foreground GPS/audio on target phone. UAT: proposed ≥5 independent consenting participants; method confirmed by supervisor before recruitment.
Jest/Supertest and a native E2E runner are implementation candidates to pin after trial; no executed test suite is claimed. Fixtures are synthetic and labelled; real corpus/provider/field data is separately versioned.

## Environments, entry and exit

Entry for a case: safe isolated environment, versioned relevant fixture, stable build/config and required dependencies/rights. Owner tests use two users; AI tests identify corpus/model/prompt/embedding version. Begin relevant tests with the first slice.
P0 exit: every required P0 case executed and passed; no unresolved blocking/major defect; core UAT and AI/GPS evaluation performed; all deviations and limitations recorded. P1 is excluded from P0 denominator. A percentage of passing low-risk tests cannot waive a failed ownership or factual-integrity case. Quantitative quality targets are proposals in PRD/Decisions, not institutionally imposed quotas.
Suspend affected testing for wrong environment, invalid fixtures, exposure, incompatible embedding space or missing approved content; record Blocked. Resume after root cause fixed and relevant smoke checks pass on the exact new build. Dates follow milestones once capacity/deadline are known.
Developer prepares/runs tests; reviewer examines risk-sensitive evidence; UAT users perform tasks without hidden developer assistance. Required independent review follows SOP. Deliver evidence/defect/retest records, configuration manifests and a final summary with actual results.

## Coverage inventory

| TC | FR/NFR | Preconditions → action | Expected |
|---|---|---|---|
| TC-01 | FR-POI-01 | Final corpus → run publication validator | 15–20 valid published POIs across four categories; exactly five approved English audio assets; invalid records rejected |
| TC-02 | FR-EXP-01 | Seed English/local names and aliases → search name/tag/category | Correct accent-insensitive matching of published records |
| TC-03 | FR-EXP-01 | No matching term → search | Empty state; no invented result |
| TC-04 | FR-PLC-01 | Unknown hours/price → detail | Unknown labels, no default open/free |
| TC-05 | FR-MAP-01 | Itinerary exists → select marker 2 | Matching second stop detail |
| TC-06 | FR-PREF-01 | Invalid day count/time/start source/transport → generate | One-day/car/start-point validation; no provider request |
| TC-07 | FR-TRP-02 | Valid candidates/Routes fixture → build and accept | Structured persisted trip with corpus IDs and provenance |
| TC-08 | FR-TRP-02 | Model returns invented/unpublished ID → build | Rejected; not saved or shown as valid |
| TC-09 | FR-TRP-02 | Known closed hours/impossible time window → build | Conflict/relax constraints; no invented availability |
| TC-10 | FR-TRP-04 | Routes unavailable → build/refresh | Null duration, unavailable status, provisional warning |
| TC-11 | FR-TRP-03 | Planned trip → reorder/add/remove/duration edit | Atomic valid order; changed legs stale; updated revision |
| TC-12 | FR-TRP-03 | Concurrent old revision/invalid ID permutation → reorder | 409/400 and no partial changes |
| TC-13 | FR-TRV-01 | Start → complete/skip all stops | One current stop; consistent progress and completed trip |
| TC-14 | FR-TRV-02 | Use primary “I’ve arrived” action twice | One manual event and one auto-play opportunity |
| TC-15 | FR-TRV-02 | Foreground accurate dwell or denied permission → arrive | Optional GPS event only when qualified; manual path remains available |
| TC-16 | FR-TRV-02 | Next-stop fix/non-demo simulated request → report | No wrong-stop arrival; simulation rejected outside demo |
| TC-17 | FR-TRV-03 | Approved asset and opt-in → arrival/play/pause | Real human asset, correct POI/locale, playback works |
| TC-18 | FR-TRV-03 | No audio/failed media fetch → listen | Unavailable/retry/transcript; zero TTS calls |
| TC-19 | FR-AI-01 | Reviewed matching passages → ask | Supported answer with valid supporting sources |
| TC-20 | FR-AI-01 | Empty/weak/wrong-POI passages → single-turn Ask | Insufficient evidence, no invented fact/citation or server conversation state |
| TC-21 | FR-AI-01 | Unknown price or injected question/source → ask | No operational invention or permission/rule override |
| TC-22 | FR-AI-01, NFR-REL-01 | AI provider times out → ask/build | Typed unavailable state, prior plan preserved |
| TC-23 | FR-SAV-01 | A saves twice/unsaves; B tries access | No duplicate; private scope enforced |
| TC-24 | FR-AUTH-01, NFR-SEC-01 | Valid/invalid login; expired/revoked session | Appropriate success/rejection; no plaintext password/token storage |
| TC-25 | NFR-SEC-01 | B uses A trip/stop/proposal in paths/Ask | 403/404; no data leak or mutation |
| TC-26 | NFR-REL-01 | Replay build/accept with same/different body | Same result or typed in-progress; mismatch 409 |
| TC-27 | NFR-PER-01 | Final seed, 10 concurrent users → list/detail | Report p95 against 2s target with workload details |
| TC-28 | NFR-ACC-01 | Native scaled text/screen reader → core screens | Readable labels, controls and status; record gaps |
| TC-29 | FR-AI-01 | Wrong embedding model/dimension → ingest/query | Reject incompatible space; no mixed vectors |
| TC-30 | FR-TRV-02/03 | Arrival report offline then retry | Stable event dedup and local playback guard; no false sync claim |
| TC-31 | FR-CAM-01 P1 | Corpus landmarks/non-landmarks, denied camera | Valid candidate or unknown/ambiguous; no new POI |
| TC-32 | FR-STT-01 P1 | Record question, edit, submit; denied microphone | Correct editable text or typing fallback; text answer only |
| TC-33 | FR-AUTH-02 P1 | Valid/invalid Google token and linking | Verified identity; no unintended account takeover |

| TC-34 | FR-PREF-01, FR-TRP-02/03 | Preferences/title across trip states | Preserve accepted plan; correct revision/state rules |
| TC-35 | FR-TRP-02/03/04, FR-TRV-01 | Known conflict versus unknown facts | Block hard conflicts; acknowledge uncertainty |
| TC-36 | Retired | Superseded by TC-41 and TC-42 on 2026-10-19 | Retained for audit; never reuse this ID |
| TC-37 | NFR-SEC/REL, FR-TRP-03/04, FR-AI-01 | Apply schema and invalid writes | Enforced DB integrity plus service checks |
| TC-38 | FR-AUTH-03 | Re-authenticate and delete account | Owned data cascades; retained operational records follow policy |
| TC-39 | FR-TRV-04 | Open external directions, return and arrive | HTTPS handoff works; fresh foreground fix/dwell; manual arrival remains primary |
| TC-40 | FR-OFF-01 | Start trip with partial cache and offline rights | Eligible essentials cached read-only; failures are explicit and resumable |
| TC-41 | FR-EXP-01, FR-PLC-01 | Search English/local aliases with accents and `đ` | Published results match deterministically without false invented records |
| TC-42 | FR-POI-01, FR-AI-01, FR-TRV-03 | Validate translated text and English audio provenance | `source_language`, origin source and human review/rights are present |
| TC-43 | FR-AUTH-01, FR-PREF-01, FR-SAV-01, FR-AI-01 | Use guest gates then sign in | Guest may browse/preview; protected actions gate; planner form survives login |
| TC-44 | FR-OFF-01, FR-TRV-01/02 | Kill/relaunch during active trip and pending arrival | Active trip and stable idempotency key restore without duplicate event/audio |
| TC-45 | NFR-REL-01 | Old/minimum/current app call API | Version headers are emitted; unsupported client receives typed upgrade response |

## Case execution procedure

For every case record fixture/build/device/config and exact actions; compare response, persisted state and visible UI against assertions. Pass requires all assertions; an unavailable prerequisite is Blocked, not Pass. Preserve redacted failure evidence and retest links. Reset isolated fixtures as needed; avoid live user/media data. This common procedure replaces repeated administrative paragraphs in each case.

### TC-01 — Final English-first corpus → run publication validator

FR-POI-01. Priority: P0 / quality.
Fixture: Load final approved corpus and publication validator.
Action: Attempt import with missing source and invalid coordinate; run validation on valid final corpus.
Assert: Invalid rows rejected with reasons; 15–20 published places cover Culture, Beach, Food and Nature; exactly five approved human English audio assets have rights records.

### TC-02 — Seed English/local names and aliases → search name/tag/category

FR-EXP-01. Priority: P0 / quality.
Fixture: Seed published English names, Vietnamese local names, aliases/romanisations/tags plus unpublished control.
Action: Search exact/normalised accented and unaccented names, aliases, tags and category; paginate.
Assert: Matching corpus IDs only, deterministic next cursor; unpublished absent.

### TC-03 — No matching term → search

FR-EXP-01. Priority: P0 / quality.
Fixture: Use search term absent from fixture.
Action: Submit search and remove filter.
Assert: No invented result; useful empty action.

### TC-04 — Unknown hours/price → detail

FR-PLC-01. Priority: P0 / quality.
Fixture: Seed known and unknown facts with dates/sources.
Action: Open detail for unknown hours/price and verified controls.
Assert: Unknown stays unknown; source/date rendered for known facts.

### TC-05 — Itinerary exists → select marker 2

FR-MAP-01. Priority: P0 / quality.
Fixture: Create ordered trip stops and Explore fixture.
Action: Select Explore pin and itinerary pin 2.
Assert: Correct POI/stop detail; numbering agrees with persisted seq.

### TC-06 — Invalid day count/time/start source/transport → generate

FR-PREF-01. Priority: P0 / quality.
Fixture: Authenticate and create invalid day count, time window, start source, preset/pin/current-location payload and transport fixture.
Action: Submit invalid preferences.
Assert: Only one day and car/ride-hailing are accepted; a valid pin, current location or supported preset is required; 400 field details and provider call counter remains zero.

### TC-07 — Valid candidates/Routes fixture → build and accept

FR-TRP-02. Priority: P0 / quality.
Fixture: Seed valid candidates and deterministic route/model responses.
Action: Create draft; build preview; inspect unchanged draft; accept using key/revision.
Assert: Structured accepted owner trip; actual corpus IDs/legs/model revision.

### TC-08 — Model returns invented/unpublished ID → build

FR-TRP-02. Priority: P0 / quality.
Fixture: Model fixture returns unknown/unpublished POI ID.
Action: Request build and inspect DB/proposal response.
Assert: 422; invalid ID absent from valid preview/persisted plan.

### TC-09 — Known closed hours/impossible time window → build

FR-TRP-02. Priority: P0 / quality.
Fixture: Seed known closed hours and too-short time window.
Action: Request itinerary using conflicting constraints.
Assert: Known conflict shown/rejected; no invented availability/feasibility.

### TC-10 — Routes unavailable → build/refresh

FR-TRP-04. Priority: P0 / quality.
Fixture: Prepare routes timeout/failure after valid AI draft.
Action: Build provisional or refresh existing route; reload aggregate.
Assert: Null time/distance; unavailable/provisional warnings; old ETA not current.

### TC-11 — Planned trip → reorder/add/remove/duration edit

FR-TRP-03. Priority: P0 / quality.
Fixture: Create three-stop planned trip.
Action: Add/remove/reorder/change duration with current revisions.
Assert: Atomic valid seq/duration; revision advances; affected legs stale/null.

### TC-12 — Concurrent old revision/invalid ID permutation → reorder

FR-TRP-03. Priority: P0 / quality.
Fixture: Read same revision in two clients.
Action: Save first edit; submit old revision and duplicate/missing reorder IDs.
Assert: 409/400; persisted plan equals first valid edit, no partial writes.

### TC-13 — Start → complete/skip all stops

FR-TRV-01. Priority: P0 / quality.
Fixture: Create nonempty planned trip.
Action: Start; complete first; skip next; finish remaining.
Assert: One current stop throughout; final trip completed.

### TC-14 — Use primary “I’ve arrived” action twice

FR-TRV-02. Priority: P0 / quality.
Fixture: Activate current stop and prepare the manual arrival control.
Action: Tap “I’ve arrived” twice using the same persisted idempotency key, including one retry after reconnect.
Assert: One event with manual method; client offers automatic playback once and keeps intentional replay available.

### TC-15 — Foreground dwell and denied-permission behavior

FR-TRV-02. Priority: P0 / quality.
Fixture: Use a qualifying fresh foreground fix/dwell, then deny permission or inject stale/poor-accuracy fixes.
Action: Resume the app, observe optional dwell, then use manual arrival where GPS does not qualify.
Assert: Qualifying foreground dwell creates at most one GPS event; stale/poor/denied data creates none; manual action stays visible and persists its method.

### TC-16 — Next-stop fix/non-demo simulated request → report

FR-TRV-02. Priority: P0 / quality.
Fixture: Activate stop A; fix at future stop B; server demo off.
Action: Report wrong-stop GPS and simulated arrival.
Assert: Rejected; no event and no wrong-place audio.

### TC-17 — Approved asset and opt-in → arrival/play/pause

FR-TRV-03. Priority: P0 / quality.
Fixture: Approve human audio for locale; Start opt-in enabled.
Action: Arrive; play/pause/seek; inspect transcript and intentional replay.
Assert: Correct version/narrator asset; auto-play once; manual replay works.

### TC-18 — No audio/failed media fetch → listen

FR-TRV-03. Priority: P0 / quality.
Fixture: Create missing-audio POI and media fetch failure.
Action: Open player; attempt load/retry.
Assert: Unavailable/retry/transcript; TTS call counter zero.

### TC-19 — Reviewed matching passages → ask

FR-AI-01. Priority: P0 / quality.
Fixture: Seed reviewed matching passages and allowed sources.
Action: Ask an answerable question; inspect each factual claim.
Assert: Valid permitted references with actual claim support.

### TC-20 — Empty/weak/wrong-POI passages → single-turn Ask

FR-AI-01. Priority: P0 / quality.
Fixture: Use empty/weak/wrong-POI evidence fixture.
Action: Ask unsupported history question.
Assert: Insufficient evidence; no invented fact/reference; no server-side conversation or message history is created.

### TC-21 — Unknown price or injected question/source → ask

FR-AI-01. Priority: P0 / quality.
Fixture: Seed unknown price and adversarial question/passage.
Action: Ask price and request instruction override.
Assert: No invented price or expanded context; refused unsupported instructions.

### TC-22 — AI provider times out → ask/build

FR-AI-01, NFR-REL-01. Priority: P0 / quality.
Fixture: Accepted trip exists; model provider times out.
Action: Call build and Ask; replay within configured deadlines.
Assert: 503 typed unavailable; prior plan unchanged; bounded request duration.

### TC-23 — A saves twice/unsaves; B tries access

FR-SAV-01. Priority: P0 / quality.
Fixture: Create independent accounts A/B.
Action: A save twice/unsave twice; B list/access A resources.
Assert: One save then none; no cross-owner rows.

### TC-24 — Valid/invalid login; expired/revoked session

FR-AUTH-01, NFR-SEC-01. Priority: P0 / quality.
Fixture: Create hashed-account fixture and sessions.
Action: Valid/invalid login; refresh rotation; expired/revoked replay/logout.
Assert: Correct success/401; hashes not plaintext; one concurrent refresh rotation succeeds; revoked refresh cannot renew; access JWT for a logged-out session is rejected by session-state check; repeated well-formed logout204.

### TC-25 — B uses A trip/stop/proposal in paths/Ask

NFR-SEC-01. Priority: P0 / quality.
Fixture: A owns trip/day/stop/proposal; B authenticated.
Action: B submits each A nested ID/read/edit/accept/Ask context.
Assert: 404 for inaccessible foreign IDs, no content leak and no mutation.

### TC-26 — Replay build/accept with same/different body

NFR-REL-01. Priority: P0 / quality.
Fixture: Use deterministic build response and key.
Action: Repeat build/accept key with same then different canonical body.
Assert: Same result or typed in-progress; mismatched body409; no duplicate aggregate.

### TC-27 — Final seed, 10 concurrent users → list/detail

NFR-PER-01. Priority: P0 / quality.
Fixture: Load final corpus and document environment.
Action: Run 10-concurrent-user list/detail workload; collect request durations.
Assert: Report server p95 versus ≤2s, count/errors and conditions.

### TC-28 — Native scaled text/screen reader → core screens

NFR-ACC-01. Priority: P0 / quality.
Fixture: Target native build on supported phone.
Action: Enable text scaling/screen reader; traverse core actions including reorder/audio/source/error.
Assert: Readable labels, touch targets/focus/status; actual gaps recorded.

### TC-29 — Wrong embedding model/dimension → ingest/query

FR-AI-01. Priority: P0 / quality.
Fixture: Prepare incompatible embedding model/dimension/task revisions.
Action: Import/query mixed-space vectors.
Assert: Dimension/model/config mismatch rejected; stale chunks excluded.

### TC-30 — Arrival report offline then retry

FR-TRV-02/03. Priority: P0 / quality.
Fixture: Active trip; opt-in; media known; network off.
Action: Trigger arrival; retry after reconnect/restart while keeping key.
Assert: Pending until ack; unique event; no repeated automatic playback.

### TC-31 — Corpus landmarks/non-landmarks, denied camera

FR-CAM-01 P1. Priority: P1 optional.
Fixture: P1 enabled with held-out landmarks/unknowns.
Action: Capture/upload/identify and deny camera.
Assert: Existing confirmed candidate or unknown; no new POI; privacy cleanup.

### TC-32 — Record question, edit, submit; denied microphone

FR-STT-01 P1. Priority: P1 optional.
Fixture: P1 microphone enabled then denied.
Action: Dictate; edit transcript; submit; simulate transcription failure.
Assert: Editable text follows Ask contract; typed fallback; no spoken answer.

### TC-33 — Valid/invalid Google token and linking

FR-AUTH-02 P1. Priority: P1 optional.
Fixture: P1 Google configured; valid/invalid/link collision tokens.
Action: Sign in and attempt email-only takeover.
Assert: Verified intended account; invalid/linking attack rejected.

### TC-34 — Preference updates respect accepted plans

Requirement: FR-PREF-01, FR-TRP-02/03, NFR-REL-01. Priority: P0.
Fixture: draft, planned, active and completed owner trips with known revisions.
Action: update preferences in each state; submit title-only update; replay an old revision.
Assert: draft preference change increments revision and invalidates previews; accepted/active/completed preference changes return409 preserving plan; title update succeeds with current revision; stale writes return409.

### TC-35 — Known conflicts block Start; uncertainty requires acknowledgement

Requirement: FR-TRP-02/03/04, FR-TRV-01, NFR-TRUST-01. Priority: P0.
Fixture: known-closed/time-overrun/empty-day plans and separate unknown-hours or unavailable-route plan.
Action: build known-infeasible preview; remove final planned-day stop; attempt Start; fix conflict and refresh; Start provisional plan with/without acknowledgement.
Assert: known infeasible build returns422; explicit edit persists with severity=error warning and Start blocked; corrected plan can start; uncertainty alone remains provisional and requires acknowledgement. Fresh routing does not remove unknown-hours warning.

### TC-36 — Retired language-fallback case

Retired on 2026-10-19. English is the P0 product language, so Vietnamese fallback and `locale_unavailable` are no longer the expected behavior. Alias/search coverage moved to TC-41 and translation provenance moved to TC-42. This identifier must not be reassigned.

### TC-37 — Apply physical schema and probe integrity

Requirement: NFR-SEC-01, NFR-REL-01, FR-TRP-03/04, FR-AI-01. Priority: P0.
Fixture: isolated empty PostgreSQL with selected PostGIS/pgvector versions; design DDL and test seed.
Action: apply migration; attempt duplicate day positions/current stops/arrivals, cross-trip/day edges, wrong-dimension chunks, embedding identity update and nonfresh nonnull estimates; execute valid deferred reorder.
Assert: invalid writes rejected and transaction rolls back; valid reorder commits; one active embedding space; application tests cover state/publication rules beyond SQL. Record actual DB/ORM versions; design-file inspection is not this test's execution.

### TC-38 — Account deletion with re-authentication

Requirement: FR-AUTH-03, NFR-SEC-01. Priority: P0.
Fixture: Account A owns trips, saves, sessions and pending idempotency records; account B is an isolation control; retention policy is pinned.
Action: Attempt deletion without/with wrong password, then confirm with the current password and call `POST /account/delete`; replay old access/refresh credentials.
Assert: Missing/wrong re-authentication is rejected; successful call returns 204, revokes sessions and removes or anonymises A-owned rows according to the documented cascade/retention matrix; B is unchanged; old credentials fail. Record backup/log retention limitations rather than claiming immediate erasure there.

### TC-39 — External map handoff and foreground return

Requirement: FR-TRV-04, FR-TRV-02. Priority: P0.
Fixture: Active trip on supported iOS/Android device with destination coordinates and Google Maps/Apple Maps availability combinations.
Action: Open Directions, verify the HTTPS destination, switch to the external app, return to DaNavi and then use “I’ve arrived”; separately allow a fresh accurate foreground dwell.
Assert: Correct destination and safe fallback browser choice; no background-tracking claim; return triggers a fresh location read; dwell is optional/deduplicated; manual arrival is still the primary, visible path.

### TC-40 — Read-only essentials cache with partial failure

Requirement: FR-OFF-01, NFR-REL-01. Priority: P0.
Fixture: Planned trip with eligible/ineligible audio, transcripts and stop content; storage and network failure variants.
Action: Start Trip, interrupt and resume downloads, go offline, then open every stop and audio control.
Assert: Text/transcripts and rights-approved audio cache read-only; no map/routing tiles are promised; progress and partial failure are explicit; cached content opens offline; unavailable content does not appear downloaded; retry is safe.

### TC-41 — English/local alias and accent-insensitive search

Requirement: FR-EXP-01, FR-PLC-01. Priority: P0.
Fixture: Published/unpublished controls for English name, Vietnamese name, romanisation, common alias, accents and `đ`, with distractors.
Action: Query every supported variant, case and accent form; combine category/tag filters; submit invalid geo/cursor filters.
Assert: Correct published records and deterministic ordering/cursor; no unpublished/distractor leak; invalid filters return 400; result displays canonical English name and local name where useful.

### TC-42 — English translation and media provenance

Requirement: FR-POI-01, FR-AI-01, FR-TRV-03. Priority: P0 / quality.
Fixture: English content translated from Vietnamese, native-English content, incomplete review, missing origin link and audio without offline rights.
Action: Run publication/ingestion validators, retrieve Ask sources and attempt audio caching.
Assert: Published translations record `source_language`, origin source and human review; incomplete provenance is rejected; citations resolve to reviewed text; only explicitly licensed audio is cached. No machine translation is represented as human-reviewed.

### TC-43 — Guest gates and planner-form preservation

Requirement: FR-AUTH-01, FR-PREF-01, FR-SAV-01, FR-AI-01. Priority: P0.
Fixture: Logged-out app with Explore data and audio preview; valid account for continuation.
Action: Browse Explore/Detail and preview audio; attempt Save, Ask and Generate; fill planning form before Generate; sign in from the gate and return.
Assert: Browse/detail/preview work as guest; protected actions present a clear sign-in gate; completed form values survive; generation does not start automatically after login and requires explicit Generate; server also rejects unauthenticated protected calls.

### TC-44 — Restore active trip and pending arrival after process kill

Requirement: FR-OFF-01, FR-TRV-01, FR-TRV-02, NFR-REL-01. Priority: P0.
Fixture: Active trip with cached essentials and a locally persisted unsynchronised arrival event/idempotency key.
Action: Kill the app before acknowledgement, relaunch offline, reconnect and retry; repeat after server acknowledgement.
Assert: Active trip/current stop/cache state restore; the original stable key is reused until acknowledgement; server stores one arrival; automatic audio fires at most once; no false synced state is shown.

### TC-45 — App/API compatibility gate

Requirement: NFR-REL-01. Priority: P0 / release.
Fixture: API configured with current API version and minimum supported app version; old, minimum and current client builds.
Action: Call representative public and authenticated endpoints and exercise the app startup check.
Assert: Responses expose API/minimum-app version headers; minimum/current clients continue; unsupported old client receives typed 426 and a user-facing required-update state; version comparison is deterministic and documented.

## Evaluation protocol

### Evaluation ownership and reproducibility

Developer prepares fixtures and runs evaluation; independent factual reviewer/UAT participants validate claims/tasks. Assign reviewer identity/consent and confirm academic method before collection. Separate development/tuning set from held-out reporting set; retain model/prompt/embedding/source/corpus/config/device versions and real-provider timestamps. No scores supplied by this package.

### Source-grounded question answering

Prepare 40–60 manually reviewed English held-out questions across supported history/culture, known/unknown hours and prices, distractor passages, cross-POI confusion, ambiguous/conflicting evidence and adversarial prompts. Label relevant chunks, supported acceptable claims and expected refusal. Use a separate tuning set for threshold/K/prompt. Record repeated-run variation. Because the corpus is deliberately small, report per-POI coverage and prevent duplicate or near-duplicate passages from leaking across tuning and held-out sets.
Metrics: Recall@K = relevant labelled chunks retrieved in top K / total labelled relevant chunks (only answerable retrieval cases); supported-claim rate = cited-supported factual claims / factual claims generated; unsupported-claim rate = unsupported factual claims / factual claims generated; citation validity = allowed IDs / returned IDs; citation support separately reviews whether cited passage supports associated claim; correct refusal rate and false refusal rate on their respective labelled subsets. A zero denominator is N/A, never 100%. Report per-language/category and micro/macro choices. Latency includes full API path; distinguish retrieval versus generation failure.
Proposed held-out targets from PRD/Test Plan: ≥90% supported factual claims, ≥90% correct no-answer handling, zero observed invented corpus IDs/operational facts. Finite sample is not a universal guarantee. Reviewer checks actual cited passage/claim, not model confidence.

### Planning

At least 20 feasible/infeasible one-day scenarios with pinned/current/preset start point, time window, known hours, pace, budget uncertainty, car/ride-hailing and unavailable routes. Assert schema/corpus IDs, start-to-first leg, Asia/Ho_Chi_Minh display, VND prices, known-constraint violations, explicit warnings, edit preservation, revision/replay and timeout. Compare to deterministic candidate/constraint baseline using identical facts; record feasibility and end-to-end planning latency rather than unproved optimality.

### GPS/audio field study

Use real target phone at several flagship POIs and varied approaches/accuracy. Record arrival target/radius/accuracy/dwell, foreground-resume fix sequence, ground-truth approach, detection time and duplicate count. Count true/missed/false arrivals; manual and simulated trials separate. Report limitations from entrances/buildings/device/network. Verify external-map return, the primary manual arrival action, opt-in defaults, one automatic playback, manual replay, interruptions, offline reporting and transcript fallback. Do not generalise foreground testing to background behavior.

### Usability protocol

At least five independent consenting users not involved in building. Task list UAT-01..05; scripted starting state and goals, no instruction naming the exact button. Record unassisted completion, time, errors/help, withdrawals and qualitative comments. Report denominators and participant/device context; retain anonymised codes, no contact information in repo.
After tasks administer the standard ten-item SUS questionnaire using an approved questionnaire source provided for the study. Responses 1–5; odd item contribution = response−1; even = 5−response; participant SUS = sum(contributions)×2.5. Missing responses → incomplete score; do not impute silently. Project targets, requiring review: mean ≥68; task completion ≥80%; report actual distribution/sample limitations, not population claims. Study consent/retention policy agreed before recruitment.

### Academic objective evaluation

Obtain actual approved aim/objectives/template. For each objective list requirement/design, implemented artifact later, measured evidence, met/partially met/not met and limitations. Literature/competitor/user research belong to separate evidence tables; no fabricated citations/respondents/results. The selected product scope must be compared with the actual approved objectives; no missing proposal is inferred.

## Evaluation interpretation and source support

Sampling, question counts and thresholds are project proposals with coverage/capacity rationale; confirm before collection. Five users do not establish population representativeness or a standard graduation minimum. SUS is a perceived-usability score, not a percentage of tasks completed; report it separately from success rate. Use the exact questionnaire/version and document translation/pilot understanding. [Brooke's original SUS instrument (AHRQ-hosted)](https://digital.ahrq.gov/sites/default/files/docs/survey/systemusabilityscale%2528sus%2529_comp%255B1%255D.pdf) is the instrument reference; this package does not reproduce or invent participant answers.
A claim supported by a source means supported by that specific reviewed source, not independently proven universally true. Report answerable-question coverage and false refusal as well as supported-claim rate so excessive refusal cannot masquerade as successful QA. Separate fixture verification from held-out live-model evaluation. [Research](17-Research-and-Academic-Plan.md) owns academic-source applicability and hypothesis limitations.

## Execution ledger

No application/DB/field/UAT execution exists in this repository. TC-01–30, TC-34–35 and TC-37–45: NOT RUN. TC-31–33: DEFERRED P1. TC-36: RETIRED. UAT-01–05: NOT COLLECTED. AI/planning/GPS/performance: NOT MEASURED. Deployment/restore: NOT EXECUTED.

Use one row per actual run when execution starts:

| Run/case | Build/device/config and fixture | Expected / actual | Status | Evidence / defect / retest | Tester / date |
|---|---|---|---|---|---|
| No execution records | — | — | NOT RUN | — | — |

A run captures commit/app/API build, device/OS, seed/source/media/corpus revisions, model/prompt/config, real-provider versus fixture mode, exact actions, output and Pass/Fail/Blocked. Retain failed attempts and withdrawal/incomplete study records; do not overwrite history with only final successes. No participant contact details/secrets/raw private content in public evidence.
