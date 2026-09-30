# Danang TourGuide — Testing and Evaluation

Version 1.0 | 2026-09-30. Plan only; every execution/result field is NOT RUN until actual evidence exists. No invented results. [PRD](01-PRD.md) owns acceptance scope.

## Strategy and environments
Unit: constraint/schedule validation, reorder, GPS checks, source/fact handling. Integration: NestJS + real test PostgreSQL/PostGIS/pgvector, ownership and transactions. System/E2E: complete native app flow with deterministic provider fixtures in CI and real provider smoke before demo. Field: GPS/audio on target phone outdoors; simulation separate. UAT: minimum five external participants not involved in building app, consent/anonymisation and SUS.
Use Jest/Supertest and a chosen native E2E runner (e.g. Maestro after compatibility spike). No enterprise load claim. Mock AI/Routes failures deterministically; real evaluation captures model/config/corpus version and latency.

## Cases and RTM
Each row defines precondition → action → expected outcome. During execution attach device/build, precise numbered steps, actual result, Pass/Fail/Blocked, timestamp and defect ID. All initial results NOT RUN.

| TC | FR/NFR | Preconditions → action | Expected |
|---|---|---|---|
| TC-01 | FR-POI-01 | Final corpus → run publication validator | 30–50 valid published POIs; missing source/coordinates rejected |
| TC-02 | FR-EXP-01 | Seed Vietnamese names → search name/tag/category | Correct matching published records |
| TC-03 | FR-EXP-01 | No matching term → search | Empty state; no invented result |
| TC-04 | FR-PLC-01 | Unknown hours/price → detail | Unknown labels, no default open/free |
| TC-05 | FR-MAP-01 | Itinerary exists → select marker 2 | Matching second stop detail |
| TC-06 | FR-PREF-01 | Invalid dates/time/coordinates → generate | Field/API validation; no provider request |
| TC-07 | FR-TRP-02 | Valid candidates/Routes fixture → build and accept | Structured persisted trip with corpus IDs and provenance |
| TC-08 | FR-TRP-02 | Model returns invented/unpublished ID → build | Rejected; not saved or shown as valid |
| TC-09 | FR-TRP-02 | Known closed hours/impossible time window → build | Conflict/relax constraints; no invented availability |
| TC-10 | FR-TRP-04 | Routes unavailable → build/refresh | Null duration, unavailable status, provisional warning |
| TC-11 | FR-TRP-03 | Planned trip → reorder/add/remove/duration edit | Atomic valid order; changed legs stale; updated revision |
| TC-12 | FR-TRP-03 | Concurrent old revision/invalid ID permutation → reorder | 409/400 and no partial changes |
| TC-13 | FR-TRV-01 | Start → complete/skip all stops | One current stop; consistent progress and completed trip |
| TC-14 | FR-TRV-02 | Accurate dwell within current-stop zone → arrive twice | One event and one auto-play opportunity |
| TC-15 | FR-TRV-02 | Poor accuracy/denied permission → manual arrival | No GPS event; one labelled manual event |
| TC-16 | FR-TRV-02 | Next-stop fix/non-demo simulated request → report | No wrong-stop arrival; simulation rejected outside demo |
| TC-17 | FR-TRV-03 | Approved asset and opt-in → arrival/play/pause | Real human asset, correct POI/locale, playback works |
| TC-18 | FR-TRV-03 | No audio/failed media fetch → listen | Unavailable/retry/transcript; zero TTS calls |
| TC-19 | FR-AI-01 | Reviewed matching passages → ask | Supported answer with valid supporting sources |
| TC-20 | FR-AI-01 | Empty/weak/wrong-POI passages → ask history | Insufficient evidence, no invented fact/citation |
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

## AI evaluation protocol
Prepare 40–60 manually reviewed questions split into answerable history/culture, operational known/unknown, ambiguous/wrong-POI, conflicting sources and adversarial instructions. Use separate development set to tune retrieval threshold/K; reserve held-out questions for reported results. Label relevant chunk IDs and acceptable claims/refusals. Report number/type/language, corpus/model/prompt versions, repeated-run variability and manual-review rubric.
Metrics: retrieval Recall@K; proportion of factual claims supported by cited sources; citation validity and citation support; unsupported-fact rate; appropriate refusal rate (and over-refusal); answer latency. Separate retrieval from generation errors. Proposed held-out targets: ≥90% supported factual claims and ≥90% correct no-answer handling, with zero invented POI IDs/operational facts observed. These targets require measurement; finite sample never proves zero general hallucination.
Structured planning evaluation: ≥20 feasible/infeasible scenarios, varying pace/start/window/hours/mode. Measure schema/corpus validity, known-constraint violations, warnings, provider failure and edit consistency. Compare AI-assisted plan to deterministic baseline using same candidate facts; do not assert optimal route without an optimisation proof.
P1 Vision: held-out photos for supported landmarks plus unknown/ambiguous scenes; report identification accuracy, false-positive rate and unknown rejection. Avoid model self-reported confidence as ground truth.

## GPS and audio field evaluation
Record target device/OS, zone parameters, fix accuracy, approaches/departures and detection time at several flagship POIs. Count true arrival, false arrival, missed arrival and duplicates. Report manual and simulated trials separately. Verify audio once on arrival and intentional replay, headset/speaker behaviour, interruption and network failure. Any native background behaviour remains outside foreground-only commitment.

## UAT and academic evidence
Minimum five qualifying users; consent before sessions; anonymised P1–P5 identities. Tasks: discover/save, build, edit/map, arrive/audio, Ask/source inspection. Record unassisted completion, errors, assistance and task time. Administer standard 10-item SUS and calculate scores; target mean ≥68 and ≥80% task completion. Small sample supports limited usability findings, not population-level claims.
COMP1682 template also calls for user research (five interviews/20 survey responses), research/competitor analysis and references, management evidence and objective-level evaluation. Those are separate report activities, not fabricated test results.

## Entry / exit / scheduling
Entry: reviewed fixtures/corpus, migrations, two independent users, stable app build and provider mocks. Begin tests with first vertical slice; do not defer all GPS/RAG tests to final week.
Exit: all critical P0 cases pass, every P0 mapped and executed, ≥90% overall functional pass rate target, no unresolved major access-control/fabricated-fact defect, UAT completed and known limitations recorded. P1 exclusions explicit. Capture real demo video/log and actual result ledger. Dates pending deadline; sequence: seed/slice → core hardening → final corpus/evaluation → UAT/fixes → rehearsal/report.
