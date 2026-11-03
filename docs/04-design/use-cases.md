# Gonarra Use Case Specification

## Document control

| Field | Value |
|---|---|
| Document ID | GONARRA-UC |
| Version | 0.2 |
| Status | Draft |
| Owner | Lê Ngọc Tấn Hiền, student author, product owner and engineer |
| Contributors | Claude Code (drafting agent; no approval authority) |
| Approver | trantrongminh, FYP mentor (full name and title pending OQ-001) |
| Date | 2026-11-04 |
| Prompt used | `design/useCase_prompt.md` v2.0 (kit commit `6996dae`), adapted copy `docs/00-governance/prompt-templates/design/useCase_prompt.md` |
| Standard | UML 2.0 use case notation; IEEE 1016-2009 Scenarios view (SAD §3.5) |
| Diagram | [`diagrams/scenarios-view.drawio`](diagrams/scenarios-view.drawio) (source of truth); index in [`diagrams/README.md`](diagrams/README.md) |
| Classification | Internal — FYP |

| Version | Date | Author | Change summary |
|---|---|---|---|
| 0.1 | 2026-11-04 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | First kit-based use case specification. Replaces pre-rebuild `docs/USE-CASES.md` (UC-00..UC-06, HA-02); legacy IDs kept in the Legacy ID column |
| 0.2 | 2026-11-04 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | DA-GONARRA-01 fixes F-01, F-02, F-06, F-07, F-10: UC-019 embeds before publication; UC-014 follows the deletion job states and Clerk-last order (no receipt); travel modes in UC-016; guests see Home and onboarding only; OQ-081, OQ-083, OQ-084 closed |

**Inputs.** PRD 0.1 (`docs/03-analysis/PRD.md`), USER_STORIES (`docs/03-analysis/user-stories.md`),
GONARRA-TRACE 0.1 (`docs/03-analysis/traceability.md`), GONARRA-SAD 0.1 §3.3, §3.5, §3.6 (`docs/04-design/architecture/SAD.md`),
blueprint §3.6 interface groups (`docs/04-design/architecture/blueprint.md`), legacy `docs/USE-CASES.md`.

## 1. Scope and conventions

- The system boundary is **Gonarra**: traveler mobile app (CMP-001), curator admin SPA (CMP-002) and API (CMP-003
  with modules CMP-004..CMP-014), CLI and jobs runner (CMP-018) and their data stores. Everything else is an actor.
- Use case IDs are `UC-001`..`UC-022`. Legacy `UC-00..UC-06` are aliases only (§4); they are not reused.
- Every use case traces to at least one `US-xxx` and `FR-xxx` (PRD 0.1). Steps are written as "Actor does" /
  "System does"; alternative (`A`) and exception (`E`) flows name the step they branch from.
- Use cases describe behaviour, not screen layout. Screen design is in `docs/04-design/ui-ux/`.
- "Signed in" means a valid Clerk session whose JWT is verified by CMP-004 (FR-068, NFR-014). Ownership is
  checked before any external call (FR-069).

## 2. Actors

| Actor | Kind | Description | Source |
|---|---|---|---|
| Traveler | Primary, human | Visitor planning and taking a 1–3 day trip in one launch city; uses the mobile app | BRD personas; SAD §3.5 |
| Study participant | Primary, human (specialises Traveler) | Traveler whose account is flagged as a study account; inherits every Traveler use case | FR-077, US-035, US-036 |
| Curator | Primary, human | Role that imports, reviews, publishes and unpublishes places (held by the owner) | FR-009..FR-019, NFR-015 |
| Clerk | Secondary, external system | Identity provider: sign-in, session tokens, user deletion | SAD §2.5; CON-004 |
| Gemini | Secondary, external system | Google GenAI: ID selection/ranking, Guide answers, embeddings, vision; reached only via CMP-012 | SAD §2.5 I-002; DEC-008 |
| Google Routes | Secondary, external system | Route matrix and single routes, WALK/DRIVE | SAD §2.5; CMP-009 |
| Google Places | Secondary, external system | Live opening hours at runtime only | SAD §2.5; CMP-013 |
| Stay price provider | Secondary, external system | LiteAPI (fallback Hotelbeds) indicative prices, runtime only | DEC-001 Could; CMP-011 |
| Booking partner | Secondary, external system | Stay, activity and transport partner sites opened by handoff link | FR-064, FR-065, FR-079 |
| Device maps app | Secondary, external system | Google/Apple Maps opened for directions | FR-054 |
| Open data source | Secondary, external system | Overture Places, Foursquare OS Places, Wikidata releases used for import | DEC-009; SRC-104 |

Actors are roles. The owner is both Curator and (in testing) Traveler; no named person is an actor.

## 3. Use case index

| UC ID | Name | Primary actor | Secondary actors | Priority | US | FR | Legacy ID |
|---|---|---|---|---|---|---|---|
| UC-001 | Search and view a place | Traveler | Google Places | Must | US-001, US-002, US-003 | FR-001..FR-008 | UC-01 |
| UC-002 | Generate a trip proposal | Traveler | Gemini, Google Routes | Must | US-010, US-012, US-013, US-014, US-035 | FR-020..FR-028, FR-070, FR-074 | UC-02 |
| UC-003 | Edit a proposal | Traveler | Google Routes | Must | US-016, US-017 | FR-033..FR-039 | UC-03 |
| UC-004 | Save an itinerary | Traveler | — | Must | US-018, US-019 | FR-032, FR-040..FR-044 | UC-03 |
| UC-005 | Lock stops and regenerate a day | Traveler | Gemini, Google Routes | Should | US-021 | FR-047..FR-050 | UC-03 (HA-02) |
| UC-006 | Manage saved trips | Traveler | — | Must | US-018, US-020 | FR-045, FR-046 | UC-04 |
| UC-007 | Use a saved trip on site | Traveler | Device maps app, Google Places | Must | US-022, US-023, US-024 | FR-051..FR-055 | UC-04 |
| UC-008 | Ask the Guide a question | Traveler | Gemini | Must | US-025, US-026, US-035 | FR-056..FR-058, FR-078, FR-070, FR-074 | UC-05 |
| UC-009 | Ask the Guide by voice | Traveler | — | Should | US-027 | FR-059, FR-060, FR-063 | — (new) |
| UC-010 | Identify a place from a photo | Traveler | Gemini | Should | US-028 | FR-061..FR-063, FR-070 | — (new) |
| UC-011 | Open a booking handoff | Traveler | Booking partner | Must | US-029, US-030, US-037 | FR-064, FR-065, FR-079 | — (new) |
| UC-012 | View indicative stay prices | Traveler | Stay price provider | Could | US-031 | FR-066, FR-067, FR-080, FR-081 | — (new) |
| UC-013 | Sign in and keep data private | Traveler | Clerk | Must | US-032 | FR-068, FR-069 | UC-06 |
| UC-014 | Delete my account | Traveler | Clerk | Must | US-033 | FR-071, FR-072 | UC-06 |
| UC-015 | Check plan feasibility (Plan Health) | — (included) | Google Routes | Must | US-014, US-015 | FR-029..FR-031, FR-039 | UC-02 |
| UC-016 | Set language and preferences | Traveler | — | Must | US-011, US-034 | FR-073, FR-075, FR-076 | UC-06 |
| UC-017 | Import candidate places | Curator | Open data source | Must | US-004 | FR-009, FR-010 | UC-00 |
| UC-018 | Review candidate content | Curator | Gemini (AI draft, optional) | Must | US-005, US-009 | FR-011, FR-012, FR-016, FR-019 | UC-00 |
| UC-019 | Publish a place | Curator | Gemini (embeddings) | Must | US-006 | FR-013..FR-016 | UC-00 |
| UC-020 | Unpublish a place | Curator | — | Should | US-007 | FR-017 | UC-00 |
| UC-021 | View city coverage | Curator | — | Should | US-008 | FR-018 | UC-00 |
| UC-022 | Record study session measures | Study participant | — | Should | US-036 | FR-077 | — (new) |

Coverage: 22 use cases, 37/37 stories and 81/81 functional requirements (FR-001..FR-081) traced.

### 3.1 Relationships

| Relationship | From | To | Condition / reason |
|---|---|---|---|
| «include» | UC-002 Generate a trip proposal | UC-015 Check plan feasibility | Every proposal is validated and given Plan Health (FR-030, FR-031) |
| «include» | UC-003 Edit a proposal | UC-015 | Every edit recalculates times, legs and conflicts (FR-039) |
| «include» | UC-004 Save an itinerary | UC-015 | Save rechecks health; blocked plan refused (FR-032) |
| «include» | UC-005 Lock stops and regenerate a day | UC-015 | Regenerated day is validated like a proposal |
| «extend» | UC-005 → UC-003 | Extension point "day action" | [traveler chooses Regenerate day] (Should, DEC-003 cut order) |
| «extend» | UC-009 → UC-008 | Extension point "question input / answer shown" | [traveler chooses voice input or read-aloud] |
| «extend» | UC-012 → UC-011 | Extension point "stay handoff" | [stay-prices feature flag on] (Could) |
| «extend» | UC-022 → UC-002 | Extension point "proposal displayed" | [account is a study account] |
| «extend» | UC-022 → UC-004 | Extension point "save outcome" | [account is a study account] |
| Generalization | Study participant | Traveler | Study participant inherits all Traveler associations |

Sign-in (UC-013) is a **precondition** of every private use case, not an «include»: it is performed once per
session by Clerk, not as a step of each use case.

## 4. Legacy mapping (UC-00..UC-06, HA-02)

| Legacy | Legacy name | New use cases | Note |
|---|---|---|---|
| UC-00 | Curate | UC-017, UC-018, UC-019, UC-020, UC-021 | Split by curator goal |
| UC-01 | Discover | UC-001 | "Add place to draft" is FR-034 in UC-003 |
| UC-02 | Generate | UC-002, UC-015 | Plan Health factored out as included use case |
| UC-03 | Edit and Save (HA-02) | UC-003, UC-004, UC-005 | HA-02 is UC-005 scenario §5.5 |
| UC-04 | Use trip | UC-006, UC-007 | Booking handoff is new UC-011 |
| UC-05 | Ask Local Guide | UC-008 | Voice (UC-009) and photo (UC-010) are new Should use cases |
| UC-06 | Manage account | UC-013, UC-014, UC-016 | — |
| HA-02 | Hội An lock + regenerate day 2 reference case | UC-005 main flow; activity `process-view-activity.drawio` page 2 | Kept as scenario label |

## 5. Use case specifications

Common business rules referenced below:
BR-046 / FR-070 (no account ID, contact details or precise location to AI), FR-004 (only published places),
FR-069 (ownership before external calls), BRU-008 / NFR-017 (no tokens, precise location, question text or full
prompts in logs), NFR-036 (daily AI quota per traveler, ASM-016).

### 5.1 UC-001 — Search and view a place

| Item | Value |
|---|---|
| Description | The traveler finds a published place in the current city and reads its sourced, current facts. |
| Primary / secondary actors | Traveler / Google Places (live hours, runtime only) |
| Trigger | Traveler enters a query or opens a place. |
| Preconditions | Signed in (guests see Home and onboarding only, ASM-082); app open with a selected locale; at least one city has published places. |
| Postconditions (success) | Place details shown with source and verification date per fact; nothing persisted. |
| Postconditions (failure) | Search result list or "no results" shown; canonical details still shown when live hours fail (NFR-011). |
| Trace | US-001, US-002, US-003, US-034 · FR-001..FR-008, FR-076 · NFR-001, NFR-026 · CMP-001, CMP-005, CMP-013 |

Main flow:
1. Traveler selects one of the five launch cities (FR-001).
2. Traveler enters a name or alias in Vietnamese or English.
3. System returns published places of that city matching name or reviewed alias, ignoring case and diacritics (FR-002, FR-004).
4. Traveler opens a place.
5. System shows names (VI and EN), description in the chosen language, category, visit duration and map position (FR-003, FR-076).
6. System shows each operational fact with source name and verification date, "unknown" when unsupported and a stale label after 180 days (FR-005..FR-007), plus attribution text (FR-008).

Alternative flows:
- A1 (from 3) No match: system shows "no results" and keeps the query for a new search.
- A2 (from 6) Live hours available: system shows Google Places live hours with attribution next to the curated hours.

Exception flows:
- E1 (from 6) Google Places fails or times out: curated facts are shown without live hours (NFR-011).
- E2 (from 4) Place is not published or was unpublished: system returns not found (FR-004, FR-017).

Data: city ID, query, locale; place ID, names, description, category, visitMinutes, position, facts {value | unknown, source, verifiedAt}, attribution.

### 5.2 UC-002 — Generate a trip proposal

| Item | Value |
|---|---|
| Description | The traveler describes a 1–3 day trip in one launch city and receives an unsaved proposal built only from published places, with real legs and Plan Health. |
| Primary / secondary actors | Traveler / Gemini, Google Routes |
| Trigger | Traveler submits a free-text request or the preference form. |
| Preconditions | Signed in (UC-013); trip exists for the owner; AI notice acknowledged on first use (FR-074); daily AI quota not exhausted (NFR-036). |
| Postconditions (success) | A preview revision (unsaved, labelled unsaved) exists for the trip; the saved itinerary is unchanged (FR-040). |
| Postconditions (failure) | Typed recoverable error; saved itinerary and previous preview unchanged (FR-043, FR-044). |
| Trace | US-010, US-012, US-013, US-014, US-035 · FR-020..FR-028, FR-070, FR-074 · NFR-002, NFR-003 · CMP-001, CMP-004, CMP-005, CMP-008, CMP-009, CMP-012, CMP-014 · Sequence page 1; Activity page 2 |

Main flow:
1. Traveler enters a request in Vietnamese or English, or fills the form: city, start date, 1–3 days, day window, pace, interests, modes, must-sees (FR-020, FR-021).
2. System verifies the session and trip ownership and checks the quota before any external call (FR-069).
3. System checks that city, start date and day count are present and supported (FR-022, FR-023).
4. System shows a progress state (NFR-003) and builds the candidate set of published places of the city (FR-025).
5. System asks Gemini to select and rank place IDs per day from the candidate set, sending no identifiers or precise location (FR-070).
6. System discards any ID outside the candidate set and checks day count and duplicates (FR-025).
7. System obtains the route matrix for the selected places (WALK/DRIVE) from Google Routes.
8. System orders stops and computes times with OR-Tools using opening hours and the day window.
9. System includes UC-015 to validate the plan and compute Plan Health.
10. System stores a preview revision and shows each day as a timeline and on a map from the same revision, labelled unsaved (FR-027, FR-028, FR-040).

Alternative flows:
- A1 (from 3) Missing or ambiguous city, date or day count: system asks for it and returns to step 1 (FR-022).
- A2 (from 6) Repairable selection: system repairs once and re-runs step 6.
- A3 (from 6) Must-see place cannot be included: system states why (FR-026).
- A4 (from 7) A pair has no route: leg marked unavailable; it becomes a blocking conflict in UC-015 (FR-029).

Exception flows:
- E1 (from 2) Not signed in or not owner: refused (401/403) before any external call (FR-068, FR-069).
- E2 (from 2) Quota exhausted: refused with reason; nothing changed (NFR-036).
- E3 (from 3) More than 3 days, more than one city or unsupported city: refused with reason before calling AI (FR-023).
- E4 (from 5 or 7) Gemini or Routes error/timeout, or selection rejected after one repair: typed recoverable error; saved itinerary and last preview unchanged (FR-043, FR-044).

Data: request text or PlanningPreferences {cityId, startDate, days, dayStart, dayEnd, pace, interests[], modes[], mustSee[]}, locale, Idempotency-Key; preview {previewId, previewRevision, baseRevision, manifestId, days[], legs[], planHealth}.

### 5.3 UC-003 — Edit a proposal

| Item | Value |
|---|---|
| Description | The traveler changes stops, durations or modes and sees times, legs and conflicts recalculated. |
| Primary / secondary actors | Traveler / Google Routes |
| Trigger | Traveler performs an edit on an open preview. |
| Preconditions | Signed in; an active (not expired, not superseded) preview owned by the traveler. |
| Postconditions (success) | New preview revision with recalculated times, legs and Plan Health; saved itinerary unchanged. |
| Postconditions (failure) | Edit kept in the draft store (CMP-020); saved itinerary unchanged (FR-043, FR-044). |
| Trace | US-016, US-017 · FR-033..FR-039 · NFR-004 · CMP-020, CMP-008, CMP-009 |

Main flow:
1. Traveler moves, adds, removes or replaces a stop, changes a visit duration or switches a leg mode (FR-033..FR-038).
2. System keeps the edit in the draft store and disables Save (FR-039).
3. System checks that an added or replacing place is published in the trip's city (FR-034, FR-036).
4. System recomputes affected legs from Google Routes and re-times the day.
5. System includes UC-015 and stores a new preview revision.
6. System shows the updated timeline, map and Plan Health and re-enables Save.

Alternative flows:
- A1 (from 1) Traveler chooses "Regenerate day": extension point "day action" → UC-005.

Exception flows:
- E1 (from 3) Place from another city or unpublished: edit refused with reason (FR-034).
- E2 (from 4) Routes failure: edit kept, error shown, Save stays disabled until a successful recalculation (FR-044).
- E3 (from 5) Preview revision changed meanwhile: 409 conflict; app reloads the current preview and re-applies the kept edit.

Data: previewId, expected previewRevision, edit {type, stopId, position, placeId, minutes, mode}, Idempotency-Key.

### 5.4 UC-004 — Save an itinerary

| Item | Value |
|---|---|
| Description | The traveler explicitly saves a preview revision; it becomes the trip's saved itinerary exactly once. |
| Primary / secondary actors | Traveler / — |
| Trigger | Traveler taps Save. |
| Preconditions | Signed in; active preview owned by the traveler; recalculation complete. |
| Postconditions (success) | Trip revision incremented once; preview state SAVED (FR-040, FR-041). |
| Postconditions (failure) | Saved itinerary unchanged; preview and edits kept (FR-042..FR-044). |
| Trace | US-018, US-019 · FR-032, FR-040..FR-044 · NFR-010 · CMP-001, CMP-007, CMP-014 · Sequence page 2; Activity page 3 |

Main flow:
1. Traveler taps Save; app sends preview ID, expected preview revision, expected trip base revision and an Idempotency-Key.
2. System looks up the key: unseen key continues.
3. System verifies ownership, preview expiry and that the base revision is current (FR-042).
4. System includes UC-015 to confirm health is not blocked (FR-032).
5. System promotes the preview atomically, increments the trip revision and records the key result.
6. System returns the saved revision; app clears the "unsaved" label.

Alternative flows:
- A1 (from 2) Same key, same payload (retry): system returns the stored result; no second version (FR-041).

Exception flows:
- E1 (from 2) Same key, different payload: refused; nothing changed.
- E2 (from 3) Base revision changed (save from another device): 409 conflict with current revision; app keeps the preview and offers to reopen current data (FR-042).
- E3 (from 3) Preview expired or superseded: refused with reason.
- E4 (from 4) Plan Health blocked: refused with the blocking stop/leg (FR-032).
- E5 (any step) Network failure: draft store keeps edits; retry with the same key is safe (FR-044).

Data: previewId, previewRevision, baseRevision, Idempotency-Key; result {tripId, savedRevision}.

### 5.5 UC-005 — Lock stops and regenerate a day (HA-02)

| Item | Value |
|---|---|
| Description | The traveler locks must-keep stops and regenerates one day; other days and locked stops stay unchanged. |
| Primary / secondary actors | Traveler / Gemini, Google Routes |
| Trigger | Traveler selects "Regenerate day" on a day (extends UC-003). |
| Preconditions | Signed in; trip with ≥ 1 saved or previewed day; regeneration feature enabled (DEC-003). |
| Postconditions (success) | New unsaved preview where only the chosen day changed and every locked stop keeps place, day and duration (FR-048..FR-050). |
| Postconditions (failure) | Previous preview and saved itinerary unchanged. |
| Trace | US-021 · FR-047..FR-050 · NFR-007 (HA-02 script) · CMP-008, CMP-012, CMP-009 · Activity page 2 |

Main flow (HA-02: saved two-day Hội An trip in Vietnamese):
1. Traveler locks a day-2 stop; system shows the lock indicator (FR-047).
2. Traveler requests regeneration of day 2.
3. System checks ownership, expected revision and quota; keeps day 1 unchanged.
4. System asks Gemini for a selection for day 2 only from published Hội An candidates, with locked stops fixed.
5. System obtains route legs for day 2 and runs OR-Tools with locks as constraints.
6. System includes UC-015 and stores a new preview revision labelled unsaved (FR-050).
7. Traveler reviews and saves through UC-004.

Alternative flows:
- A1 (from 1) Traveler unlocks a stop: indicator removed; stop is free in regeneration.

Exception flows:
- E1 (from 4/5) Gemini or Routes failure: error shown; previous preview and saved trip unchanged.
- E2 (from 5) Locks cannot be satisfied in the day window: Plan Health blocked with reason; preview kept editable.

Data: previewId, day number, locks [{stopId, placeId, day, visitMinutes}], Idempotency-Key.

### 5.6 UC-006 — Manage saved trips

| Item | Value |
|---|---|
| Description | The traveler lists saved trips, reopens one at its last saved version or deletes one. |
| Primary / secondary actors | Traveler / — |
| Trigger | Traveler opens the trip list. |
| Preconditions | Signed in. |
| Postconditions (success) | Trip reopened at last saved version, or deleted after confirmation. |
| Postconditions (failure) | List unchanged; cancelled deletion keeps the trip. |
| Trace | US-018, US-020 · FR-045, FR-046 · CMP-007 |

Main flow: 1. Traveler opens trips. 2. System lists the owner's saved trips (FR-045). 3. Traveler opens a trip. 4. System shows the last saved version.
Alternative: A1 (from 3) Traveler deletes a trip and confirms; system removes it (FR-046). A2 (from A1) Traveler cancels; trip kept.
Exceptions: E1 (from 3) Trip not owned or deleted: not found (FR-069). E2 (from 2) Network failure: cached list shown read-only (NFR-011).

### 5.7 UC-007 — Use a saved trip on site

| Item | Value |
|---|---|
| Description | During the trip the traveler sees today's stops, a place card for a driver and directions. |
| Primary / secondary actors | Traveler / Device maps app, Google Places |
| Trigger | Traveler opens "Today" or a stop of a saved trip. |
| Preconditions | Signed in; saved itinerary exists. |
| Postconditions (success) | Place card shown; maps app opened with directions when requested. |
| Postconditions (failure) | Card shown with "unknown" for missing address or entrance. |
| Trace | US-022, US-023, US-024 · FR-051..FR-055 · CMP-001, CMP-005, CMP-024 |

Main flow: 1. Traveler opens Today. 2. System lists the current day's stops in order in Vietnam local time (FR-055, NFR-025). 3. Traveler opens a stop. 4. System shows VI and EN names, Vietnamese address and verified entrance (FR-051..FR-053). 5. Traveler taps Directions. 6. System opens the device maps app to the entrance, or the place position when the entrance is unknown (FR-054).
Alternatives: A1 (from 2) Trip date not today: system shows day 1. A2 (from 4) Address or entrance missing: labelled "unknown".
Exceptions: E1 (from 6) No maps app: system shows the address to copy. E2 (from 4) Live hours fail: curated facts only (NFR-011).

### 5.8 UC-008 — Ask the Guide a question

| Item | Value |
|---|---|
| Description | The traveler asks about a published place and gets a streamed answer grounded in reviewed sources, or an "insufficient evidence" reply. |
| Primary / secondary actors | Traveler / Gemini |
| Trigger | Traveler sends a text question from a place card or trip. |
| Preconditions | Signed in; AI notice acknowledged (FR-074); quota available; place is published. |
| Postconditions (success) | Answer in the chosen language with ≥ 1 cited reviewed source and verification date (FR-056, FR-078); Guide message stored as ANSWERED. |
| Postconditions (failure) | INSUFFICIENT_EVIDENCE or FAILED state shown; no unsupported claim. |
| Trace | US-025, US-026, US-035 · FR-056..FR-058, FR-078, FR-070, FR-074 · NFR-005, NFR-006 · CMP-010, CMP-005, CMP-012 · Sequence page 3 |

Main flow:
1. Traveler types a question about a place.
2. System verifies session and ownership of the Guide session.
3. System reads the place's structured facts and retrieves reviewed knowledge chunks above the similarity threshold for the place and locale (FR-058).
4. System asks Gemini for an answer citing only supplied evidence; no identifiers sent (FR-070).
5. System drops any citation not in the supplied evidence and streams the answer over SSE (NFR-005).
6. System sends the final result with citations and verification dates (FR-078, NFR-006).

Alternative flows:
- A1 (from 3) No evidence above threshold: system streams `insufficient_evidence` without calling Gemini for an answer (FR-057).
- A2 (from 5) All citations rejected: result is `insufficient_evidence` (FR-057).
- A3 (from 1) Voice input or read-aloud: extension → UC-009.

Exception flows:
- E1 (from 2) Not owner: 403 before retrieval (FR-069).
- E2 (from 4) Gemini timeout or error: SSE `error` event; message FAILED; traveler may retry.
- E3 (any) Stream dropped: app resumes with GET of the stored message, not a new request.

Data: sessionId, placeId, locale, question text (not logged, NFR-017); answer text, citations [{sourceId, title, verifiedAt}], outcome.

### 5.9 UC-009 — Ask the Guide by voice (extends UC-008)

Actors: Traveler. Trigger: Traveler taps the microphone. Preconditions: UC-008 preconditions; voice feature enabled.
Postconditions: success — question sent as text after explicit Send, or answer read aloud; failure — text input remains available.
Trace: US-027 · FR-059, FR-060, FR-063 · CMP-021.
Main flow: 1. System asks for microphone permission on first use only (FR-063). 2. Traveler speaks in VI or EN. 3. System transcribes on device and shows the editable transcript. 4. Traveler taps Send; UC-008 continues at step 2. 5. Traveler taps "Read aloud" on the completed answer; system reads the displayed text on device (FR-060).
Alternatives: A1 (from 3) Traveler edits the transcript before Send.
Exceptions: E1 (from 1) Permission denied: system offers text input. E2 (from 3) No speech recognised: system asks to retry or type.

### 5.10 UC-010 — Identify a place from a photo

| Item | Value |
|---|---|
| Description | The traveler photographs a place on site and is told which published place within 300 m it is, or that it is not recognised. |
| Primary / secondary actors | Traveler / Gemini (vision) |
| Trigger | Traveler takes a photo in the Guide. |
| Preconditions | Signed in; photo feature enabled; AI notice acknowledged. |
| Postconditions (success) | Place card of the matched place offered; photo and location not stored (SAD §3.6.3). |
| Postconditions (failure) | "Not recognised" shown (FR-062). |
| Trace | US-028 · FR-061..FR-063, FR-070 · CMP-022, CMP-010, CMP-016, CMP-012 · ADR-008 · Sequence page 4 |

Main flow: 1. System asks for camera and location permission on first use (FR-063). 2. Traveler takes a photo; app strips metadata and takes one foreground location fix. 3. System finds published places within 300 m (ASM-009) with PostGIS. 4. System sends only the image and the candidate place descriptors to Gemini vision — not the coordinates (FR-070). 5. System accepts a match only if it is one of the candidates and returns the place (FR-061).
Alternatives: A1 (from 3) No published place within 300 m: "not recognised" without calling Gemini (FR-062). A2 (from 5) Gemini picks no candidate or one outside the set: "not recognised".
Exceptions: E1 (from 1) Permission denied: feature unavailable message; Guide text still works. E2 (from 4) Gemini error: error shown; nothing stored.

### 5.11 UC-011 — Open a booking handoff

Actors: Traveler / Booking partner. Trigger: Traveler taps a stay, activity or transport link. Preconditions: Signed in; saved itinerary.
Postconditions: success — partner site opened with city and dates (stay, transport) or city (activity); failure — message shown, trip unchanged. No booking or payment in Gonarra (DEC-001 Won't).
Trace: US-029, US-030, US-037 · FR-064, FR-065, FR-079 · CMP-011.
Main flow: 1. Traveler opens the handoff section of a saved trip or stop. 2. System builds partner links from the trip's city and dates (FR-064, FR-079) or stop city (FR-065). 3. Traveler picks a partner. 4. System opens the partner site in the browser.
Alternative: A1 (from 2) Stay-prices flag on: extension → UC-012.
Exception: E1 (from 4) Browser cannot open: link shown to copy.

### 5.12 UC-012 — View indicative stay prices (extends UC-011)

Actors: Traveler / Stay price provider. Trigger: Stay handoff section opened with the feature flag on. Preconditions: UC-011 preconditions.
Postconditions: success — prices with retrieval time and "partner confirms final price" notice (FR-067, FR-080); prices never stored with the trip (FR-081). Failure — section hidden with a message (FR-066).
Trace: US-031 · FR-066, FR-067, FR-080, FR-081 · CMP-011, CMP-013.
Main flow: 1. System requests prices for city and dates from LiteAPI. 2. System shows prices with retrieval time and notice. Exception: E1 (from 1) LiteAPI fails: Hotelbeds fallback; if that fails, section hidden with message.

### 5.13 UC-013 — Sign in and keep data private

Actors: Traveler / Clerk. Trigger: Traveler opens a private feature without a session. Preconditions: App installed.
Postconditions: success — Clerk session; API maps subject → account; only the owner's data is visible (FR-069). Failure — the guest sees Home and onboarding only; other actions show the sign-in sheet SCR-040 (ASM-082).
Trace: US-032 · FR-068, FR-069 · NFR-012, NFR-014, NFR-016 · CMP-004, CMP-019.
Main flow: 1. Traveler signs in with Clerk (owner-built onboarding, SRC-100 A-020). 2. App attaches the JWT to API calls. 3. System verifies issuer, signature and expiry and resolves the account. 4. System checks ownership on every private resource before any external call. 5. Traveler may sign out; the app clears the session and cached private data.
Exceptions: E1 (from 3) Missing, invalid, expired or foreign-issuer token: 401 (NFR-014). E2 (from 4) Resource of another traveler: 403/404, no data disclosed (FR-069).

### 5.14 UC-014 — Delete my account

| Item | Value |
|---|---|
| Description | The traveler deletes the account; private data is removed within 24 h and status is shown until done. |
| Primary / secondary actors | Traveler / Clerk |
| Trigger | Traveler confirms "Delete account". |
| Preconditions | Signed in. |
| Postconditions (success) | Deletion job COMPLETED; 0 private records after 24 h (FR-071); Clerk user deleted. |
| Postconditions (failure) | State FAILED with reason shown (FR-072); jobs runner retries. |
| Trace | US-033 · FR-071, FR-072 · CMP-001, CMP-004, CMP-018 · SAD §3.3.5 · Sequence page 6 |

Main flow: 1. Traveler requests deletion and confirms. 2. System creates a deletion job (REQUESTED) and returns status (202). 3. Jobs runner sets IN_PROGRESS and deletes the traveler's private records (trips, previews, preferences, Guide sessions). 4. Jobs runner deletes the Clerk user last and sets COMPLETED. 5. App polls the status; it shows completed on COMPLETED, or on a 401 after IN_PROGRESS was seen (OQ-073) (FR-072).
Alternatives: A1 (from 1) Traveler cancels confirmation: nothing changes.
Exceptions: E1 (from 3 or 4) Clerk or database failure: state FAILED with reason; the jobs runner retries until COMPLETED within 24 h (OQ-082).

### 5.15 UC-015 — Check plan feasibility (Plan Health) (included)

Actors: none directly (included by UC-002, UC-003, UC-004, UC-005); Google Routes for leg data.
Preconditions: a scheduled preview. Postconditions: each stop/leg flagged with blocking conflicts; status GOOD / WARNING / BLOCKED with reasons (FR-031).
Trace: US-014, US-015 · FR-029..FR-031, FR-039 · CMP-008, CMP-009.
Main flow: 1. System checks each leg has provider distance/duration or marks it unavailable (FR-029). 2. System checks opening hours at planned times and the day window. 3. System flags each blocking conflict by type: closed, leg unavailable, day window exceeded (FR-030). 4. System sets status BLOCKED if any blocking conflict, WARNING for non-blocking issues, otherwise GOOD.
Exception: E1 (from 1) Routes unavailable for a pair: leg "unavailable" (never straight-line or AI-estimated).

### 5.16 UC-016 — Set language and preferences

Actors: Traveler. Trigger: Traveler opens settings. Preconditions: language choice needs no sign-in; saved preferences need sign-in.
Postconditions: interface and place content in the chosen language with the Vietnamese name always available (FR-075, FR-076); preferences saved only on explicit Save and used to prefill the form (FR-073).
Trace: US-011, US-034 · FR-073, FR-075, FR-076 · NFR-022, NFR-026 · CMP-023, CMP-004.
Main flow: 1. Traveler chooses VI or EN. 2. System switches all traveler-facing text. 3. Traveler edits pace, interests and travel modes and taps Save. 4. System stores preferences.
Exception: E1 (from 4) Save fails: values kept in the form; error shown.

### 5.17 UC-017 — Import candidate places

| Item | Value |
|---|---|
| Description | The curator imports candidate places for one city from a named open-data release into staging without touching the live catalog. |
| Primary / secondary actors | Curator / Open data source |
| Trigger | Curator runs the import CLI command for a city and release. |
| Preconditions | Curator has host access (OQ-036); provider policy exists in the registry (CMP-013). |
| Postconditions (success) | Candidates tagged with the release; no duplicates on re-import (FR-010); published catalog unchanged. |
| Postconditions (failure) | Staging rolled back for that run; published catalog unchanged. |
| Trace | US-004 · FR-009, FR-010 · CMP-018, CMP-006, CMP-013 · Activity page 1 |

Main flow: 1. Curator runs import for a city and release. 2. System reads the release bounded by the city bounding box (DuckDB over GeoParquet; Wikidata). 3. System keeps only fields the provider policy allows. 4. System upserts candidates keyed by source ID and release (FR-010). 5. System reports counts.
Exceptions: E1 (from 2) File unreadable or release unknown: run aborted, nothing written. E2 (from 3) No policy for the provider: default deny, run aborted.

### 5.18 UC-018 — Review candidate content

Actors: Curator / Gemini (optional AI draft). Trigger: Curator opens a candidate in the admin SPA. Preconditions: signed in with curator role (NFR-015).
Postconditions: VI/EN name and description, facts with value or "unknown", sources, verification dates and media rights recorded; AI-drafted fields marked "AI draft" until confirmed (FR-019).
Trace: US-005, US-009 · FR-011, FR-012, FR-016, FR-019 · CMP-002, CMP-006, CMP-017.
Main flow: 1. Curator opens a candidate. 2. Curator enters VI and EN content (FR-011). 3. Curator records each fact as value or unknown with ≥ 1 source and a verification date (FR-012). 4. Curator records the licence and attribution of each source (FR-016). 5. System saves the candidate revision.
Alternative: A1 (from 2) Curator requests an AI draft; system marks drafted fields "AI draft"; curator confirms each field (FR-019).
Exceptions: E1 (from 5) Candidate revision changed: 409, reload. E2 (from 1) Non-curator: 403 (NFR-015).

### 5.19 UC-019 — Publish a place

| Item | Value |
|---|---|
| Description | The curator publishes a complete candidate so it becomes a published place used by search, planning and the Guide. |
| Primary / secondary actors | Curator / Gemini (embeddings, before publication) |
| Trigger | Curator clicks Publish. |
| Preconditions | Signed in with curator role; candidate reviewed (UC-018); its draft chunks embedded by `cli embed` and approved (ADR-012). |
| Postconditions (success) | Place PUBLISHED; reviewer and time recorded (FR-015); the publication pins the approved corpus revision, so the Guide can cite the place from its first publication (FR-058). |
| Postconditions (failure) | Candidate unchanged; missing items listed (FR-013, FR-016). |
| Trace | US-006 · FR-013..FR-016 · NFR-015 · CMP-002, CMP-004, CMP-006, CMP-005, CMP-018, CMP-012 · Sequence page 5; Activity page 1 |

Main flow: 1. Before publication, the embed CLI embeds the place's draft chunks and the curator approves them (ADR-012). 2. Curator clicks Publish with expected candidate revision and Idempotency-Key. 3. System verifies curator role. 4. System checks the publication gate: VI content, EN content, a source per fact, attribution per source, no unconfirmed AI draft, media rights, approved chunks embedded. 5. System publishes the place in a new city manifest pinning the approved corpus revision and records reviewer and time.
Exceptions: E1 (from 4) Gate fails: refused, missing items named. E2 (from 3) Not curator: 403. E3 (from 1) Embedding fails: place stays in READY_TO_PUBLISH; chunks retried on the next run; the publish gate refuses unembedded approved chunks.

### 5.20 UC-020 — Unpublish a place

Actors: Curator. Trigger: Curator clicks Unpublish. Preconditions: curator role; place PUBLISHED.
Postconditions: place returned to candidates (SUSPENDED); absent from new searches, proposals and Guide answers (FR-017); existing saved trips keep their snapshot.
Trace: US-007 · FR-017 · CMP-006, CMP-005.
Main flow: 1. Curator selects the place and confirms. 2. System changes state and issues a new manifest. Exception: E1 (from 2) revision changed: 409.

### 5.21 UC-021 — View city coverage

Actors: Curator. Trigger: Curator opens the dashboard. Preconditions: curator role.
Postconditions: published-place counts per launch city shown (FR-018, MET-011). Trace: US-008 · FR-018 · CMP-002, CMP-006.
Main flow: 1. Curator opens coverage. 2. System counts published places per city. Exception: E1 (from 2) query fails: error shown.

### 5.22 UC-022 — Record study session measures (extends UC-002, UC-004)

Actors: Study participant. Trigger: proposal displayed or Save outcome for a study account.
Preconditions: account flagged as study account; consent recorded (BR-023).
Postconditions: session log row with pseudonymous participant code, interface language, request-submitted time, first-proposal-displayed time and Save outcome — no identity or question text (FR-077); deleted after 2027-06-30 (NFR-018, ASM-010).
Trace: US-036 · FR-077 · NFR-018 · CMP-014.
Main flow: 1. At extension point "proposal displayed" the system records times. 2. At extension point "save outcome" it records the outcome. Exception: E1 logging fails: main use case continues; gap noted in study record.

## 6. Non-functional and data constraints by use case

| Constraint | Applies to |
|---|---|
| NFR-001 search p95 ≤ 2 s | UC-001 |
| NFR-002 proposal p95 ≤ 60 s; NFR-003 progress ≤ 2 s | UC-002, UC-005 |
| NFR-004 recalculation p95 ≤ 5 s | UC-003 |
| NFR-005 / NFR-006 Guide first text ≤ 5 s, complete ≤ 20 s | UC-008, UC-009 |
| NFR-011 provider failure does not stop search, place card, reopening trips | UC-001, UC-006, UC-007 |
| NFR-014 credential rejection; FR-069 ownership | All private use cases |
| NFR-015 curator role only | UC-017..UC-021 |
| NFR-017 / BRU-008 log redaction | UC-002, UC-008, UC-010 |
| NFR-025 Vietnam local time | UC-002, UC-007 |
| NFR-036 daily AI cap | UC-002, UC-005, UC-008, UC-010 |

## 7. Assumptions

| ID | Assumption | Affects | Owner |
|---|---|---|---|
| ASM-080 | Save is `POST /v1/plan-previews/{id}/accept` in the Trips module with expected preview and base revisions (blueprint §3.6); exact status codes follow the API design | UC-004 | Lê Ngọc Tấn Hiền |
| ASM-081 | Sign-in is a precondition, not an «include», because Clerk performs it once per session | UC-013 and all private use cases | Lê Ngọc Tấn Hiền |
| ASM-082 | Guests see Home and onboarding only (A-027); search, place details and every other action show the sign-in sheet SCR-040; `/v1/places` and `/v1/cities` require a bearer token (openapi) | UC-001, UC-016 | Lê Ngọc Tấn Hiền |

## 8. Open questions

| ID | Question | Recommendation | Owner | Needed by |
|---|---|---|---|---|
| OQ-080 | SAD §3.5 shows 9 use-case ovals; this document refines them into UC-001..UC-022. Should SAD §3.5 link to `use-cases.md` and `scenarios-view.drawio` instead of keeping its own list? | Yes — replace the SAD Mermaid list with a link at the next SAD revision | Lê Ngọc Tấn Hiền | 2026-11-18 |
| OQ-081 | Which status and error codes are used for a stale revision (409) and for Idempotency-Key reuse with a different payload? | Closed (A-026): 409 `revision_conflict` and 422 `idempotency_key_mismatch`, fixed in the API design / OpenAPI | Lê Ngọc Tấn Hiền | 2026-11-18 |
| OQ-082 | How often does the jobs runner retry account deletion so FR-071 (24 h) holds after a Clerk failure? | systemd timer hourly; mark FAILED with reason after each failed attempt and alert the owner if not COMPLETED after 12 h | Lê Ngọc Tấn Hiền | 2026-11-25 |
| OQ-083 | Are the PostGIS candidate descriptors sent to Gemini vision text only (names, category) or also reference images from S3? | Closed (A-026): text descriptors of places within 300 m plus at most one licensed reference image per candidate; final choice after the photo-set spike (cut order DEC-003) | Lê Ngọc Tấn Hiền | 2026-12-09 |
| OQ-084 | Once Clerk deletes the user its JWT is revoked, so how does the app keep showing deletion status (FR-072) until completion? | Closed by A-024/A-026: Clerk user deleted last; the app treats 401 after IN_PROGRESS as completed (OQ-073); no receipt | Lê Ngọc Tấn Hiền | 2026-11-18 |

## 9. Self-check (UseCase_Document_UML2.0_Checklist)

| # | Checklist item | Status | Evidence |
|---|---|---|---|
| 1 | Use Case ID | Pass | §3 UC-001..UC-022 unique |
| 2 | Use Case Name (active verb phrase) | Pass | §3 names |
| 3 | Description | Pass | Description rows §5 (short form for UC-009, UC-011..UC-013, UC-015, UC-016, UC-018, UC-020..UC-022 in first line) |
| 4 | Version & Date | Pass | Document control |
| 5 | Author & Stakeholders | Pass | Owner, approver in document control |
| 6 | Status | Pass | Draft |
| 7 | Primary Actor | Pass | §2, §3 |
| 8 | Secondary Actors | Pass | §2, §3 |
| 9 | System Boundary | Pass | §1; boundary box in `scenarios-view.drawio` |
| 10 | Trigger | Pass | Each §5 entry |
| 11 | Pre-conditions | Pass | Each §5 entry |
| 12 | Post-conditions (Success) | Pass | Each §5 entry |
| 13 | Post-conditions (Failure) | Pass | Each §5 entry |
| 14 | Main Success Scenario | Pass | Numbered main flows |
| 15 | Action/Response Format | Pass | "Traveler …" / "System …" steps |
| 16 | Alternate Flows | Pass | A-flows; UC-015, UC-020, UC-021 have none (single path) |
| 17 | Exception Flows | Pass | E-flows in every use case |
| 18 | Flow References | Pass | "(from n)" on every A/E flow |
| 19 | Association | Pass | Diagram actor–use case lines |
| 20 | Include | Pass | §3.1, 4 «include» to UC-015 |
| 21 | Extend | Pass | §3.1, 5 «extend» with conditions |
| 22 | Generalization | Pass | Study participant → Traveler |
| 23 | Business Rules | Pass | §5 common rules and per-step FR/BR references |
| 24 | Non-Functional Requirements | Pass | §6 |
| 25 | Data Requirements | Partial | Data lines given for UC-001..UC-005, UC-008; others implicit — owner Lê Ngọc Tấn Hiền, due 2026-11-18 with API design |
| 26 | No UI specifics | Pass | §1 convention; flows say what, not layout |
| 27 | No Technical Jargon | Partial | Some steps name design elements (SSE, PostGIS, OR-Tools) for design traceability — owner Lê Ngọc Tấn Hiền, due 2026-11-18 (keep; glossary in SAD §1.4) |
| 28 | Assumptions Listed | Pass | §7 |
| 29 | Open Issues | Pass | §8 |

Score: 27 Pass, 2 Partial, 0 Fail, 0 N/A.

### Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Approver | trantrongminh (FYP mentor) | [Pending] | |
| Owner | Lê Ngọc Tấn Hiền | [Pending] | |
