# Danang TourGuide — Development Plan

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Planning basis and roles

One student developer owns implementation, curation and evidence. Supervisor confirms academic requirements; a qualified reviewer examines applicable high-risk changes. Narrator/participant roles are assigned when recruited. Technical/task work is not assumed parallel for one developer.
Deadline/capacity and budget are unknown. Estimates are preliminary judgement ranges, not measured productivity or calendar promises. Re-estimate after feasibility trials and a timed content-production sample; allow explicit research, recording, fieldwork, review and report time. No fictitious dated Gantt is supplied.

## Milestones

| Milestone | Deliverable | Exit evidence |
|---|---|---|
| M0 requirements/design | BRD/PRD/stories/use cases, SAD/Blueprint, data/API/UI, security/curation/research, plan/tests/trace | Document checks; product/technical review; academic objectives mapped when supplied |
| M1 feasibility and configuration | Native map/GPS/audio, PostgreSQL extensions/ORM and model/embedding/Routes trials | Actual device/DB/provider records; pinned versions/config, realistic effort/cost |
| M2 vertical slice | Five reviewed POIs, 2–3 recordings, one-day plan and Ask | Complete app flow plus ownership, refusal, provider failure and replay checks |
| M3 P0 delivery | All core behavior; proposed final corpus/media coverage | P0 cases executed; critical defects fixed; curation permissions/evidence |
| M4 evaluation | Held-out AI/planning, field GPS/audio, native accessibility and UAT | Measured results, task/SUS data, limitations; optional P1 decision |
| M5 submission/demo | Report, demo and approved deployment if required | Objective-level evaluation, reproducible artifacts and review; restore if deployed |

Discovery research may proceed during M0 after the consent/academic method gate; update requirements before affected implementation. Trial outcomes feed back into docs; documentation completion does not imply compatibility success.

## Backlog

| Task | Outcome | Requirements | Estimate hours | Dependencies |
|---|---|---|---|---|
| TASK-01 | Compatibility trial: native maps/GPS/audio | — | 6–12 | None |
| TASK-02 | Compatibility trial: database/ORM | — | 6–12 | None |
| TASK-03 | Compatibility trial: AI JSON and text retrieval | — | 8–16 | TASK-02 |
| TASK-04 | Documentation and configuration baseline | — | 4–8 | TASK-01, TASK-02, TASK-03 |
| TASK-05 | publish validated places | FR-POI-01 | 16–32 | TASK-02 |
| TASK-06 | search places | FR-EXP-01 | 8–20 | TASK-05 |
| TASK-07 | inspect place facts | FR-PLC-01 | 8–20 | TASK-05 |
| TASK-08 | select places on a map | FR-MAP-01 | 8–20 | TASK-06, TASK-01 |
| TASK-09 | save and unsave places | FR-SAV-01 | 8–20 | TASK-07, TASK-10 |
| TASK-10 | register and maintain a session | FR-AUTH-01 | 8–20 | TASK-02 |
| TASK-11 | enter trip constraints | FR-PREF-01 | 8–20 | TASK-10 |
| TASK-12 | review and accept an AI proposal | FR-TRP-02 | 24–48 | TASK-11, TASK-03, TASK-14 |
| TASK-13 | edit itinerary stops | FR-TRP-03 | 16–32 | TASK-12 |
| TASK-14 | inspect route provenance | FR-TRP-04 | 12–24 | TASK-11, TASK-01 |
| TASK-15 | progress through my trip | FR-TRV-01 | 8–20 | TASK-12, TASK-13 |
| TASK-16 | record arrival safely | FR-TRV-02 | 12–24 | TASK-15, TASK-01 |
| TASK-17 | listen to reviewed recorded audio | FR-TRV-03 | 8–20 | TASK-05, TASK-01 |
| TASK-18 | ask about a place with sources | FR-AI-01 | 24–48 | TASK-05, TASK-03, TASK-10 |
| TASK-19 | identify a supported landmark | FR-CAM-01 | 8–16 | P0 gate, TASK-18 |
| TASK-20 | dictate and edit a question | FR-STT-01 | 8–16 | P0 gate, TASK-18 |
| TASK-21 | use Google login | FR-AUTH-02 | 8–16 | P0 gate, TASK-10 |
| TASK-22 | Cross-cutting security/reliability hardening | NFR-SEC-01, NFR-REL-01 | 12–24 | First core slice |
| TASK-23 | Final corpus, held-out evaluation and UAT | NFR-TRUST-01, NFR-PER-01, NFR-ACC-01, NFR-USAB-01 | 40–80 | TASK-22 |
| TASK-24 | Deployment, restore, demo and report evidence | BIZ-06 | 24–48 | TASK-23; budget/cloud gate |

TASK-01/02 may be investigated independently; TASK-03 needs the DB/model context. Execute TASK-14 before TASK-12. TASK-17 begins once reviewed sample audio exists and does not depend on GPS. TASK-22 hardening starts with the first slice, not only at the end. TASK-19–21 are DEFERRED; all implementation/field/runtime tasks remain NOT STARTED. TASK-04 has design material prepared, with review/trial-dependent configuration pending.
These are work packages. Split each into focused model/service/API/UI/test changes with the mapped FR and acceptance condition; do not treat a whole feature as one opaque commit. Generic input documents are referenced once in [Traceability](14-Traceability.md), not repeated for every task.

## Work package outputs

<a id="task-01"></a>

### TASK-01 — Compatibility trial: native maps/GPS/audio

Trace: —; BIZ-06.
Output/acceptance: Run a development build on target phone, render map, obtain a foreground fix, play approved test recording; record device/build/permission limits.

<a id="task-02"></a>

### TASK-02 — Compatibility trial: database/ORM

Trace: —; BIZ-06.
Output/acceptance: Select ORM/engine after applying proposed DDL with both extensions in isolated DB; verify custom constraints and dimension rejection.

<a id="task-03"></a>

### TASK-03 — Compatibility trial: AI JSON and text retrieval

Trace: —; BIZ-06.
Output/acceptance: Compare available providers on reviewed Vietnamese cases, JSON validity/latency/usage; pin model/dimension/task and report failures.

<a id="task-04"></a>

### TASK-04 — Documentation and configuration baseline

Trace: —; BIZ-06.
Output/acceptance: Resolve deadline/capacity/budget/day/mode configuration gates; reviewer records selected baseline and approved changes.

<a id="task-05"></a>

### TASK-05 — publish validated places

Trace: FR-POI-01; US-01 / BIZ-01.
Output/acceptance: Given missing sources/coordinates/media rights, When I validate an import, Then publication is blocked with row errors. Given valid reviewed records, When published, Then they appear in the public corpus.

<a id="task-06"></a>

### TASK-06 — search places

Trace: FR-EXP-01; US-02 / BIZ-01.
Output/acceptance: Given Vietnamese published names/tags, When I search/filter, Then matching published records appear. Given no matches/network failure, Then empty/retry actions appear.

<a id="task-07"></a>

### TASK-07 — inspect place facts

Trace: FR-PLC-01; US-03 / BIZ-01.
Output/acceptance: Given unknown hours/price, When I open detail, Then facts remain labelled unknown. Verified facts show source/date; unpublished IDs are inaccessible publicly.

<a id="task-08"></a>

### TASK-08 — select places on a map

Trace: FR-MAP-01; US-04 / BIZ-01.
Output/acceptance: Given Explore/itinerary markers, When I select a marker, Then the matching place/stop opens; numbered pins follow stop sequence.

<a id="task-09"></a>

### TASK-09 — save and unsave places

Trace: FR-SAV-01; US-05 / BIZ-05.
Output/acceptance: Given my account, When I save twice, Then one row exists. When I unsave twice, Then it remains absent. Another account cannot access my saves.

<a id="task-10"></a>

### TASK-10 — register and maintain a session

Trace: FR-AUTH-01; US-06 / BIZ-05.
Output/acceptance: Given valid registration/login, Then a renewable session is issued. Expired/revoked credentials and another owner ID cannot access private data. Logout revokes the refresh session.

<a id="task-11"></a>

### TASK-11 — enter trip constraints

Trace: FR-PREF-01; US-07 / BIZ-02.
Output/acceptance: Given invalid dates/window/start point or unsupported mode/day count, When submitted, Then field errors appear without model calls. Valid input creates an owner-scoped draft.

<a id="task-12"></a>

### TASK-12 — review and accept an AI proposal

Trace: FR-TRP-02; US-08 / BIZ-02.
Output/acceptance: Given curated candidates, When generated, Then validated structured preview and warnings appear; unknown IDs are rejected. Acceptance with current revision persists atomically. Timeout/old revision preserves prior plan.

<a id="task-13"></a>

### TASK-13 — edit itinerary stops

Trace: FR-TRP-03; US-09 / BIZ-02.
Output/acceptance: Given my current revision, When I edit, Then changes are atomic and affected routes stale. Invalid permutations/old revisions fail; current and visited stops remain immutable in an active trip.

<a id="task-14"></a>

### TASK-14 — inspect route provenance

Trace: FR-TRP-04; US-10 / BIZ-02.
Output/acceptance: Given Routes success, Then legs show mode/fetch time/revision. Given failure, Then duration is null with unavailable state. AI never supplies operational route durations.

<a id="task-15"></a>

### TASK-15 — progress through my trip

Trace: FR-TRV-01; US-11 / BIZ-03.
Output/acceptance: Given a planned trip with nonempty days, no blocking conflicts and acknowledged uncertainties, When started, Then one stop is current. Complete/skip activates the next; last transition completes the trip.

<a id="task-16"></a>

### TASK-16 — record arrival safely

Trace: FR-TRV-02; US-12 / BIZ-03.
Output/acceptance: Given current stop and accurate foreground dwell, When arrival is reported repeatedly, Then one event exists. Denied/weak GPS offers manual arrival; simulation is labelled and rejected outside demo mode.

<a id="task-17"></a>

### TASK-17 — listen to reviewed recorded audio

Trace: FR-TRV-03; US-13 / BIZ-03.
Output/acceptance: Given approved human audio, When played, Then playback/progress/transcript work. Auto-play defaults off and occurs once per stop after opt-in. Missing audio remains unavailable without synthesis.

<a id="task-18"></a>

### TASK-18 — ask about a place with sources

Trace: FR-AI-01; US-14 / BIZ-04.
Output/acceptance: Given authorised context and sufficient reviewed evidence, Then answers reference supporting sources. Absent/conflicting evidence yields uncertainty. Injected instructions cannot broaden context or create facts.

<a id="task-19"></a>

### TASK-19 — identify a supported landmark

Trace: FR-CAM-01; US-15 / BIZ-07.
Output/acceptance: Given a supported image, Then a corpus candidate may be proposed for confirmation. Unknown/ambiguous scenes never create places; denied camera offers manual selection.

<a id="task-20"></a>

### TASK-20 — dictate and edit a question

Trace: FR-STT-01; US-16 / BIZ-07.
Output/acceptance: Given microphone permission, Then speech becomes editable text submitted through Ask. Failure/denial falls back to typing; answers remain text.

<a id="task-21"></a>

### TASK-21 — use Google login

Trace: FR-AUTH-02; US-17 / BIZ-07.
Output/acceptance: Given verified provider token, Then deliberate account linking applies. Unverified or mismatched identity cannot take over an existing email account.

<a id="task-22"></a>

### TASK-22 — Cross-cutting security/reliability hardening

Trace: NFR-SEC-01, NFR-REL-01; BIZ-06.
Output/acceptance: Exercise ownership, concurrent revisions, timeout/replay and stale routes; fix critical failures and record actual checks.

<a id="task-23"></a>

### TASK-23 — Final corpus, held-out evaluation and UAT

Trace: NFR-TRUST-01, NFR-PER-01, NFR-ACC-01, NFR-USAB-01; BIZ-06.
Output/acceptance: Expand curated corpus/audio; execute held-out AI/planning/GPS/performance/native accessibility/UAT protocols; preserve anonymised raw evidence.

<a id="task-24"></a>

### TASK-24 — Deployment, restore, demo and report evidence

Trace: BIZ-06; BIZ-06.
Output/acceptance: Produce reviewed report/demo and objective evaluation; if deployment is required/approved, build artifact, rehearse migration/restore and record authorized smoke evidence.

## Ready / done and review

Ready for a slice: linked requirement/use case, known DTO/data/state rules, dependencies and applicable configuration resolved, acceptance/test plan available. Done: reviewable artifact, developer understands behavior, actual appropriate checks and reviewer outcome recorded. Design drafting is separate from implementation Done. Required independent review under the repository SOP is retained; optional organizational roles are not fabricated.
For each task track owner, status, actual start/finish/effort, artifact/evidence and next action in the working backlog. Do not mark a task completed just because its intended behavior is documented.

## Scheduling and effort refinement

Close O-01: deadline, weekly hours, absence, supervisor review and defense buffer. Time one representative POI including source/rights/fact review, and one audio guide including transcript/recording/review; use observed ranges to estimate the remaining corpus. Account explicitly for interviews/analysis, evaluation-set labelling, UAT recruitment/sessions, outdoor trials and report writing. Early estimates above exclude unmeasured participant waiting and provider setup delay; TASK-23/24 ranges must be expanded if evidence warrants it.
Prioritize scope within P0 acceptance; defer P1 before removing core correctness/security. If capacity conflicts with selected quantitative targets, record a scope change and academic impact rather than silently lowering acceptance. Build a dated schedule only after capacity/effort are known; retain replanning history.

## Risk register

Likelihood/impact 1–5 and product scores are planning judgements, not measured probabilities. All risks OPEN until evidence resolves or an owner accepts them.

| ID | Risk | Likelihood | Impact | Score | Owner role | Mitigation / trigger |
|---|---|---|---|---|---|---|
| R-01 | Deadline/capacity unknown | 4 | 5 | 20 | Developer | Close O-01 before dated commitment; preserve P0 and defer P1 |
| R-02 | Native map/GPS/audio incompatibility | 3 | 5 | 15 | Developer | TASK-01 real phone trial before main code |
| R-03 | Model hallucination/unsupported citations | 4 | 5 | 20 | Developer + factual reviewer | Restricted context, refusals, held-out claim support and adversarial cases |
| R-04 | Wrong route ETA after edits | 3 | 5 | 15 | Developer | Revision-bound legs, stale/null values, TC-10..12 |
| R-05 | Cross-user ID/session leak | 3 | 5 | 15 | Developer + technical reviewer | Owner/membership tests TC-24/25; block release |
| R-06 | GPS inaccurate/duplicate arrival | 4 | 4 | 16 | Developer | Field-tuned zones/dwell; manual fallback; replay guard |
| R-07 | Source/media/narration rights unavailable | 3 | 5 | 15 | Curator | Record rights before publication; start sample corpus early |
| R-08 | Audio production workload | 4 | 4 | 16 | Curator/narrator TBD | 2–3 early samples; prioritise 10–15 flagship places |
| R-09 | Cloud/API cost exceeds budget | 3 | 4 | 12 | Developer/user | Close O-02; quotas; measure usage; keep deployment gated |
| R-10 | DB extension/ORM mismatch | 3 | 4 | 12 | Developer | TASK-02 apply custom constraints and vectors |
| R-11 | Academic objective mismatch | 3 | 5 | 15 | User/supervisor | Compare actual approved proposal before final scope sign-off |
| R-12 | Research/UAT participants unavailable | 3 | 4 | 12 | Developer | Recruit early with consent; supervisor confirms sample expectations |
| R-13 | Source staleness/model-config drift | 3 | 4 | 12 | Curator/developer | Version facts/corpus/model; re-review/reembed; reject mixed vectors |
| R-14 | False claims of readiness | 3 | 4 | 12 | Developer/reviewer | NOT RUN ledger; separate design checks from runtime evidence |

Review at each milestone: record evidence, revised likelihood/impact, actual owner/due date, treatment and unresolved trigger. Source staleness, academic fit and content rights are substantive risks, not formatting gaps. Change a requirement/design through [Decisions](09-Project-Decisions.md), updating affected data/API/UI/tasks/tests and academic objective mapping together.
