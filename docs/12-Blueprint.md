# DaNavi — Software design blueprint

Version 1.3 | 2026-10-19 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Subject, constraints and stakeholders

Design subject: mobile travel companion plus API, curated ingestion and media. Trust boundaries: device/API, API/database, API/providers, storage/public media, curator/publication. One API deployable and one PostgreSQL consistency boundary. Deadline, capacity, cloud budget and specific version compatibility remain open. [PRD](01-PRD.md) owns behaviour; [SAD](02-SAD.md) owns architecture.

| Concern | Stakeholders | Requirements | Design elements | Verification |
|---|---|---|---|---|
| C-01 trusted facts | Traveler, curator | BIZ-01, BIZ-04; FR-POI-01, FR-AI-01 | Publication validator; fact store; filtered retrieval; refusal | TC-01, TC-19..21 |
| C-02 private persistence | Traveler, owner | BIZ-05; FR-AUTH-03; NFR-SEC-01 | Identity; ownership guard; trip revision; reauthenticated deletion | TC-24, TC-25, TC-38 |
| C-03 reliable edits | Traveler, developer | BIZ-02; FR-TRP-03/04 | Atomic reorder; stale legs; optimistic lock | TC-11, TC-12 |
| C-04 usable arrival | Traveler | BIZ-03; FR-TRV-02/03/04, FR-OFF-01 | External handoff; foreground/resume accuracy/dwell; manual arrival; unique event; cache/playback guard | TC-14..18, TC-30, TC-39, TC-40 |
| C-05 limited delivery capacity | Developer, supervisor | BIZ-06; NFR-REL-01 | Modular monolith; exact vector search; staged slices | TASK-01..04, TC-22, TC-29 |
| C-06 inclusive UI | Traveler, reviewer | NFR-ACC-01, NFR-USAB-01 | Tokens; alternative controls; source/uncertainty states | TC-28; UAT-01..05 |

## Design views

| View | Concern | Elements / owning artifact |
|---|---|---|
| Context | C-01..06 | Actors, mobile app, Nest API, providers, DB/storage; SAD context |
| Composition | C-02, C-05 | Identity, Places, Saved, Trips, Routing, Guides, AI; development-view.drawio |
| Logical | C-01..04 | Place, Trip, TripDay, TripStop, RouteLeg, ArrivalEvent, AudioGuide, Source; logical-view.drawio |
| Dependency | C-02, C-05 | Controllers → services → repository/ports; Trips orchestrates AI/Routing; AI cannot mutate trips |
| Interaction | C-01, C-03, C-04 | Build/accept; edit/refresh; arrival/audio; RAG; 04-Sequence-Diagrams.md and sequence sources |
| Information | C-01..04 | UUID entity references; factual provenance; locale/model/corpus versions; 05-Database-Design.md |
| Interface | C-02, C-03 | HTTPS /api/v1; DTO schemas; current revision; error envelope; 06-API-Design.md |
| State dynamics | C-03, C-04 | Trip/stop/route/proposal/session rules in 12-Blueprint.md |
| Algorithm | C-01, C-03, C-04 | Candidate validation, schedule constraints, filtered retrieval, arrival detection below |
| Resources | C-05 | Single API process; DB indexes; bounded provider deadlines; 02-SAD.md |

## Element responsibilities and ports

Identity: issue/rotate/revoke sessions, authenticate subject and coordinate reauthenticated hard deletion. Places: published English content plus reviewed Vietnamese/romanized search aliases, facts and entrance coordinates; read-only runtime corpus. Saved: owner-scoped idempotent saves. Trips: aggregate, revision, proposal acceptance and stop progression. Routing: provider-backed `car` legs/freshness; mobile owns HTTPS external-map handoff. Guides: published English human asset metadata/transcript/offline-rights flags. Cache: mobile-only revision-bound read store plus pending mutation journal. AI: propose permitted IDs and answer single-turn from permitted English evidence. Ingestion: validate source language, translation review, aliases, rights and facts before publication.
Ports: ModelPort.propose(candidateFacts, constraints) → structured draft; EmbeddingPort.embed(text, configVersion) → matching vector; RoutesPort.resolve(points, `car`) → legs/unavailable; GuideRepository.approved(place, `en`) → asset/unavailable. Ports return bounded typed failure; no raw provider response becomes public API. Repository implementation/ORM TBD; application rules independent of ORM choice.

## Algorithm A — validated proposal and acceptance

1. Authenticate session/owner. A guest Generate action first preserves the local form and completes login; it never auto-replays after login. Validate `dayCount=1`, `transportMode=car`, configured size limits, current revision and durable idempotency key/hash. Build is allowed only for draft/planned trips.
2. Read published candidate IDs, reviewed operational facts, suggested durations and corpus/fact versions. No model-provided name, coordinate, price or route duration becomes canonical data. Opening-hours source schema and dated exceptions are validated before scheduling.
3. Request ordered candidate IDs and positive bounded visit durations. Reject unknown/unpublished IDs, duplicated POI visits within one proposal, empty days and malformed schema. At most one repair is allowed within the total deadline; otherwise 422. Duplicate visits are excluded in V1, not an optimisation claim.
4. Resolve the reviewed startPoint → first POI leg and consecutive inter-stop `car` legs outside a DB transaction. Start coordinates include source `map_pin`, `current_location` or `preset`. Unknown travel durations remain null. The retained multi-day schema does not expose multi-day P0 behavior.
5. Schedule deterministically: start at local dailyStart; add rounded-up provider travel minutes; select the earliest verified open interval fitting the entire visit, including explicit wait; add visit duration; check dailyEnd. Exception dates override weekly hours. Unknown/conflicting/expired hours cannot establish opening. For a missing leg, that stop and downstream ETAs remain null; subsequent known legs do not restore the unknown clock origin. The daily end may not cross midnight in V1; split source opening intervals explicitly by local date.
6. A known closed visit or dailyEnd overrun is a blocking conflict: return 422 with precise constraint details, not an acceptable proposal. Missing hours/prices or travel time are nonblocking uncertainty warnings: return a provisional preview. Budget preference is a qualitative filter, not a currency ceiling or a guarantee of affordability. No claim of shortest/optimal route is made.
7. Store preview with base revision, fact snapshot, warnings, provenance and expiry; accepted itinerary remains unchanged. A concurrent edit makes the preview stale; check revision again before storing or accepting.
8. **Save & customize** authenticates/rechecks expiry/base revision/publication/fact versions and known feasibility. Persist day/stop/start/inter-stop records and revision in one transaction. Editing becomes available only after this acceptance. A second new acceptance of an already accepted proposal returns 409; exact stored replay returns its original result.
9. On provider failure retain the accepted plan and return typed error. A client cancelling its wait does not guarantee server cancellation; GET/reconcile before a new action.

## Algorithm B — edits and routing

Lock trip, authenticate parent membership/revision and validate state. Stops can be edited only after acceptance (planned/active), not in a draft without persisted days or in a completed trip. During active trip preserve the current stop plus completed/skipped prefix; only upcoming stops may change. An insertion/move may not place a stop before that fixed prefix.
Apply add/remove/duration/full-day permutation atomically. Reorder includes every persisted stop of the named day; fixed stops retain their relative position and position ahead of future stops. Duplicate/missing/foreign IDs fail. Increment revision; null affected ETAs/durations/distances/polylines and mark route records stale. First-stop changes invalidate the day's start leg. Recompute both days for a move.
An edit may temporarily leave a planned day empty or violate constraints; save the explicit edit with a blocking warning and disable Start until corrected. Route refresh recomputes schedules and warnings; it cannot silently undo user edits. Provider requests run outside transactions. On apply, lock/check the same revision and discard older concurrent refresh results; a late failed refresh may not downgrade a newer successful result. Persist provider warnings and freshness metadata. Refresh does not increment itinerary revision.
Preferences are editable only in draft. Planned/active/completed preference changes return 409; create a new draft for changed dates/day count/start constraints, preserving the previous trip. Title-only updates are allowed in all states with revision. This avoids silently discarding accepted days/stops.

## Algorithm C — external handoff, foreground arrival and audio

Construct Google/Apple directions as HTTPS using the current stop's reviewed entrance point and `car`; opening it has no trip-state effect. Stop the watcher when backgrounded. On foreground return, fetch authoritative trip/current-stop state, request a fresh fix and only then run the optional dwell helper. The in-app route is a preview, never described as turn-by-turn.
**I've arrived** is the primary path. GPS dwell is only a foreground/resume helper for the reconciled current stop, with configurable radius, accuracy, report age and dwell. Reset dwell on inaccurate/out-of-zone fix, current-stop change or watcher suspension. Field trials fix O-09 values before GPS acceptance.
Report method/time and GPS accuracy/distance/dwell where applicable. Server authenticates owner/parent/current state, rejects simulation outside demo, checks configured age/plausibility and records one event per stop under the trip lock. Client evidence cannot prove physical presence. Arrival does not increment itinerary/progression revision or complete a stop. An exact idempotency replay returns the existing event after ownership verification, even after progression; a new report for a noncurrent stop fails. An already-recorded current-stop arrival returns the canonical event and does not create a second playback opportunity.
Persist the local guard keyed by trip/stop before an automatic playback attempt so retry/resume/process restart cannot initiate another automatic play. Session opt-in defaults off; an interrupted or failed attempt can be retried manually. Intentional replay remains available. Offline reporting is visibly pending; after reconnection reconcile current trip before retrying stale reports. Revision-matched cached audio may play while reporting remains pending. Server-issued media URLs can expire; refresh through guide metadata rather than replay expired URLs. Pause/background/end stops the watcher. Resume follows the reconciliation sequence above.

## Algorithm D — contextual RAG

Authenticate place/trip context before embedding or provider calls. Ask is server-side single-turn: the client sends the current question and explicit context, never an implicit conversation transcript. Place-only uses a published place. Trip-only permits its published stops; place+trip must refer to a permitted member. Unpublished content is excluded and disclosed as unavailable.
Retrieve known structured facts separately. Embed the English question in the pinned immutable space and exact-search reviewed English chunks filtered by POI/locale, source revision and corpus/config compatibility. Deduplicate and use calibrated relevance; nearest result alone is not sufficient evidence. Disputed/unknown operational facts remain unknown even if a model knows a plausible value. Client-only display history is not persisted as server conversation state.
Generate a structured answer with allowed chunk/fact IDs, then expose answer-level source cards. Reject malformed or fabricated references and operational values inconsistent with known structured facts. A failed draft is withheld; weak/conflicting evidence produces insufficient_evidence. Model/provider failure produces HTTP503. The model has no mutation tools or secrets. Claim-level citation presentation is stretch; independent held-out claim review still measures support. Avoid asserting zero hallucination outside the tested set.

## Algorithm E — trip essentials cache and offline pending actions

At Start Trip, compute eligible text, transcript and offline-authorised audio for accepted stops, estimate bytes and prefetch within the configured device limit. Store itinerary/content/asset revisions, rights flag and completion state; never cache map tiles, route responses for offline navigation or expiring access URLs as permanent assets. A content/itinerary revision mismatch invalidates the affected entry before use.
Partial download remains partial. The user can retry or continue online-only; the app never labels the trip ready offline unless every declared eligible item completed. Cached content is read-only. Complete, Skip and Arrival made offline are separate pending commands with a locally persisted idempotency key/request hash/status created before the first network attempt.
On foreground/connectivity recovery, restore the active trip ID and pending journal from device storage, GET authoritative state, then replay only safe still-applicable commands with their original keys. A confirmed response clears the pending flag; conflict fetches state and does not silently overwrite newer progression. Account deletion/logout clears private cache and pending records. Cache size, eviction and audio storage rights remain trial/curation gates.

## State and action contract

Trip states: draft → planned → active → completed. Stop states: upcoming → current → completed/skipped. Draft has preferences and no required day/stop plan. Acceptance creates upcoming stops; Start chooses the first current stop. Only one current stop exists in an active nonempty trip. All terminal stops make the trip completed. Arrival is independent of stop completion. Pause is local session suspension, not another trip state.

| Action | Precondition | Persisted effect / failure |
|---|---|---|
| Create trip | Valid session/preferences | draft, revision 0; invalid input 400 |
| Change preferences | draft; current revision | preferences/revision++; invalidate outstanding previews; otherwise 409 |
| Change title | Owner; current revision | title/revision++; no implicit preference edit |
| Build | draft/planned; current revision | preview only; 422 malformed/infeasible; 503 provider |
| Accept | Same trip/revision; unexpired unaccepted preview; current facts | planned aggregate/revision++; stale/expired 409; invalid facts 422 |
| Edit stops | planned/active; mutable upcoming suffix | atomic edit/revision++; fresh estimates invalidated; completed/draft 409 |
| Start | planned one-day trip; nonempty; no blocking warning | initiate eligible cache prefetch; active/first current/revision++; uncertainty/cache acknowledgement required; conflicts 422 |
| Open directions | active/current with reviewed entrance | no persisted trip change; HTTPS external handoff; foreground return reconciles before location helper |
| Arrival | active/current or exact prior replay | unique event only; wrong stop/state 409; simulation outside demo 403 |
| Complete/skip | active/current; current revision | terminal stop; next current or trip completed; revision++; conflict 409 |
| Route refresh | planned/active/completed with accepted plan; current revision | same-revision estimates/warnings; provider failure 503; late result 409/discard |
| Audio replay | Published POI/approved locale asset | read only; unavailable metadata or missing-place 404 |
| Delete account | authenticated owner; password reauthentication and explicit confirmation | revoke sessions and hard-delete owner graph atomically; wrong password 401; failure does not claim success |

Current-stop progression follows day_index/seq; moving to the next day is explicit progression, with no background clock or notification claim. A place becoming unpublished causes a blocking trip warning and permits an explicit skip/removal where state rules allow; it is never replaced silently. Completion is allowed without an arrival event, including manual user decisions.

## Warnings and freshness

Warning severity error blocks Start/accept where applicable; warning describes uncertainty requiring acknowledgement. Codes include empty_day, known_closed, window_exceeded, unpublished_place, unknown_hours, unknown_price, route_unavailable and route_stale. Messages identify affected place/day where available. Aggregate routeStatus describes travel data, not overall feasibility: a fresh route can accompany unknown hours and a provisional plan.
A fresh leg has provider duration/distance/fetch time and matching itinerary revision. A configured age limit makes it stale; since GET is side-effect free, the response may project stale/null values from expired persisted data without writing on read. Unknown or stale leg estimates are never displayed as current. Stored historic metadata is not a feasibility guarantee.

## Transactions and replay

ExpectedRevision guards preference/title/stop/progress edits and accept/start; arrival uses unique event/current-stop checks instead. Build and refresh check revision without incrementing it. Lock/check/update in short DB transactions; provider calls never hold the trip transaction open. DB enforces same-trip/day membership, deferred seq uniqueness and at most one current stop; application enforces exactly one for active trips and allowed transitions.
Idempotency scope is owner + logical endpoint/path IDs + key, with canonical request hash. The mobile client persists key, canonical request metadata and pending status before its first network attempt, so suspend/process kill does not create a new logical command. Authenticate and verify resource access before returning a stored outcome. Same key/hash returns original status/result; mismatch returns 409; in-progress returns typed 409. Results and mutation commit together. In-progress reservations carry an operation deadline; recovery marks overdue reservations failed only after proving no successful outcome was committed, and stale workers cannot finalize a recovered reservation. New deliberate retries use a new key after reconciliation. Security/environment settings are rechecked; stale responses cannot roll back UI progression. Refresh media access separately when signed URLs expire.
Route refresh of the same revision compares request start/fetch generation and serialized apply to prevent older responses replacing newer ones. Store/reconstruct canonical event/proposal results without pretending dynamic signed URLs are permanent. After retention expiry reconcile state before retrying old commands.

## Design quality and handoff

Quality scenarios and measurable targets are in [PRD](01-PRD.md) and [Test Plan](08-Test-Plan.md). Versioned configuration/limits have one owner in [Decisions](09-Project-Decisions.md). Alternatives: no microservices/queue/Redis initially; no ANN until recall/latency measurement; no background GPS; no automatic model mutation. Security and deployment details are in their owning documents.
Before a dependent implementation slice, resolve its trial-dependent settings, update API/DDL/diagram impact and review the exact artifact version. Account deletion is P0; O-08 must settle security-log retention and backup expiry before an external pilot. No standalone trip deletion/export API is committed in P0.
