# Danang TourGuide — REST API Contract

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Contract ownership and boundary

Base path /api/v1. [openapi.json](openapi.json) owns DTO fields, schema validation and operation responses; this document owns semantic rules not expressible by schema alone. It is a design contract, not a running API inventory. The selected contract format is [OpenAPI 3.0.3](https://spec.openapis.org/oas/v3.0.3.html), not a claim that it is the latest version.
Public reads expose published content only. Private endpoints authenticate JWT/session and verify owner plus every nested resource's parent membership before data or provider access. Inaccessible foreign IDs return 404 consistently to avoid disclosure. P1 is excluded from this P0 contract.

## P0 operations

| Method/path | Input or behaviour | Auth |
|---|---|---|
| POST /auth/register | email/password, validation and password hash | Public |
| POST /auth/login | returns access and refresh session | Public |
| POST /auth/refresh | rotates refresh token | Session |
| POST /auth/logout | revokes session | Session |
| GET /places | q/category/tags/bbox/near/radius/cursor filters | Public |
| GET /places/{id} | facts with provenance, media, audio availability | Public |
| GET /saved | caller saves | Owner |
| PUT /saved/{placeId} | idempotent save published place | Owner |
| DELETE /saved/{placeId} | idempotent unsave | Owner |
| POST /trips | preferences and dates → draft trip | Owner |
| GET /trips | caller trips | Owner |
| GET /trips/{id} | aggregate, revision, stops, route status | Owner |
| PATCH /trips/{id} | constraints/title with expectedRevision | Owner |
| POST /trips/{id}/build | expectedRevision → proposal and warnings, synchronous 200 | Owner |
| POST /trips/{id}/proposals/{pid}/accept | expectedRevision; revalidate publication/expiry → planned trip | Owner |
| POST /trips/{id}/stops | placeId/dayId/position/duration/expectedRevision | Owner |
| PATCH /trips/{id}/stops/{sid} | duration/day change with expectedRevision | Owner |
| DELETE /trips/{id}/stops/{sid} | expectedRevision | Owner |
| PUT /trips/{id}/days/{dayId}/stops/order | complete orderedStopIds + expectedRevision | Owner |
| GET /trips/{id}/route | legs/polyline/freshness, nullable unavailable durations | Owner |
| POST /trips/{id}/route/refresh | expectedRevision → route or unavailable | Owner |
| POST /trips/{id}/start | expectedRevision; confirm provisional warnings | Owner |
| POST /trips/{id}/stops/{sid}/arrivals | method/time and GPS quality evidence if gps | Owner |
| POST /trips/{id}/stops/{sid}/complete | transition current stop; activate next | Owner |
| POST /trips/{id}/stops/{sid}/skip | transition current stop; activate next | Owner |
| GET /places/{id}/audio-guide | locale → approved asset metadata/URL, or audio_unavailable | Public |
| POST /ai/ask | question, placeId and/or owned tripId, locale | User |

## HTTP and errors

Success: register/create-trip 201; save/unsave/logout 204 without body; other operations 200. Provider_unavailable is HTTP503 with Error, not a successful Ask response. Build may return 200 provisional for route-only failure when model/constraint validation succeeds. Route refresh failure returns 503; GET shows reconciled unavailable/stale data.
Error shape: code, message, optional details, requestId. Never return stack traces/provider secrets. 400 malformed input; 401 invalid session; 404 absent/inaccessible resource; 409 state/revision/key mismatch; 422 known constraint or invalid model output; 429 quota; 500 safe unexpected error; 503 dependency failure. Simulation outside demo is 403. Responses are specified per operation, rather than listing irrelevant errors on every endpoint.
Stable error codes include validation_error, unauthenticated, not_found, revision_conflict, state_conflict, idempotency_mismatch, request_in_progress, proposal_expired, invalid_proposal, constraint_violation, quota_exceeded, provider_unavailable and simulation_disabled. A retryable error includes a safe explanation; HTTP429 uses Retry-After when known. Dynamic limits must be visible in validation details without exposing secrets.

## Identity

Register accepts normalised email and the configured 12–128-character password proposal; no truncation. Login verifies supplied credentials without applying a registration minimum that rejects existing passwords. Password hash algorithm/parameters require a trial. JWT carries subject and session identifier; protected requests validate signature/issuer/audience/expiry plus session owner/not-revoked/not-expired. Refresh rotates the stored token hash atomically; simultaneous use of the old token cannot create two valid replacements. Logout takes the refresh token, revokes the matching session, and is idempotent for a well-formed already-revoked/unknown token. It discloses no account existence. Account deletion/export policy is separate and required before pilot.

## Pagination, filtering and locale

Default limit 20/max50. Places sort by normalised name then ID; trips and saved records sort newest-first with ID tie-breakers. Cursor binds the caller where private, filters, locale and ordering; invalid/mismatched cursor is 400. Cursor pagination is not snapshot isolation: document behavior if curated records change between pages.
Search normalises Unicode/case, removes Vietnamese diacritics and maps đ to d; test accented/unaccented names, category/tags and unpublished exclusions. Category uses controlled vocabulary; comma-separated tags use AND matching. bbox is west,south,east,north with ordered bounded coordinates. near is lat,lng with positive radius metres. bbox and near are mutually exclusive; near/radius must be paired. Range/size ceilings follow configuration review.
locale accepts vi/en, default vi. Vietnamese is required. A missing reviewed English POI text may fall back to Vietnamese with requestedLocale/contentLocale returned and UI label. Audio does not silently fall back language: unavailable for the requested locale. Ask P0 is Vietnamese; en without reviewed/evaluated coverage returns 400 locale_unavailable. A configured English capability needs corpus/translation evaluation before activation.

## Trip semantics

Create returns draft/revision0. Preferences contain startDate/dayCount/startPoint/interests/pace/dailyStart/dailyEnd/budgetPreference/transportMode. dailyStart < dailyEnd within one local day; dates use Asia/Ho_Chi_Minh. Budget is qualitative, not a numeric guaranteed cost. Supported day/mode/stop limits are checked server-side after O-04.
PATCH requires at least title or preferences plus expectedRevision. Preferences can change only in draft; otherwise 409 preserves the accepted plan. Title can change in any state with revision. Draft has no required stop/day records. Stop edits require planned/active; completed/current prefix is fixed during active travel. Removing the last stop of a planned day persists the explicit edit but creates a blocking empty_day warning.
Build returns proposalId/baseRevision/status(valid|provisional)/expiresAt/days/warnings/routeStatus/modelVersion/corpusVersion. Nonempty days use published unique candidate IDs. Known infeasibility returns 422, not a valid preview. Accept rechecks owner/trip/revision/expiry/fact versions and creates a planned aggregate atomically. Start requires nonempty days, no severity=error warnings and acknowledgement of any uncertainty warning; otherwise 422/409. Travel progression requires expectedRevision; arrival has its own unique event contract and does not advance progression revision.
Warnings include code/message/severity and optional placeId. routeStatus fresh does not imply complete feasibility. [Blueprint](12-Blueprint.md) owns the complete action matrix.

## Routing and schedule

Each day has an explicit start-to-first-stop leg; inter-stop legs connect stops within that day. Proposal startLeg references toPlaceId; persisted startLeg references dayId/toStopId. GET route returns dayStartLegs and inter-stop legs. Provider duration/distance/fetchedAt/mode/revision are recorded; no LLM travel estimates. Stale/unavailable responses use null estimates and no current polyline. Provider attribution/warnings must be preserved; caching/retention must follow approved provider terms.
Edit response marks affected routes/ETAs stale. Refresh runs outside the trip transaction and applies only to the same revision; older concurrent results cannot replace newer results. The server can project expired persisted legs as stale/null on GET without mutating the database. [Google Compute Routes](https://developers.google.com/maps/documentation/routes/compute-route-over) is the integration reference; supported modes, regional behavior and terms must be verified during trial.

## Arrival and media

GPS requires detectedAt, accuracyMeters, distanceMeters and dwellSeconds. Manual/simulated methods make no GPS claim. Server checks current stop, configured report age/plausibility, owner and uniqueness; simulation requires demo mode. No continuous location endpoint/history is included. A pending local report is not synced until acknowledged.
Audio available requires URL/urlExpiresAt/duration/transcript/version/human_recorded type; expiry is null only for an approved nonexpiring URL; unavailable has no URL. Missing POI is 404; missing guide/language returns 200 unavailable. URL expiry is separate from asset availability: refresh metadata on expired access URL. GET guide never enqueues synthesis. Exact event replay must not start another automatic playback.

## Revision and idempotency

Required Idempotency-Key: create trip, build, accept, start, arrival, complete and skip. Owner/path/key scope and canonical request hash are durable. Authenticate access before replay. Same request returns original outcome; mismatched payload is 409; in-progress is typed409. New intent/new retry after failure uses a new key after reconciliation; network retry uses the original key. Deadline/recovery and expired media semantics are in Blueprint. Client GET/reconciles after timeout or stale replay response.
PATCH/add-stop/reorder/delete-stop use expectedRevision to prevent repeat mutation; save/unsave use natural idempotency. DELETE stop places revision in the query. Read/build-preview/route-refresh do not increment itinerary revision; trip/progress mutations do. No 202/polling job contract exists in P0.

## Ask response

Ask requires question plus placeId and/or owned tripId; when both exist, place must belong to permitted trip context. question is nonblank and bounded. Context validation precedes embedding/model calls. grounded response contains answer, supporting citations and/or factReferences, and requestId. insufficient_evidence contains an explanation with empty evidence arrays and no unsupported factual answer. A verified citation ID is necessary but does not establish claim entailment; held-out evaluation assesses support.
Example below is a schema fixture, not a POI fact or measured model response:
```json
{
  "status": "insufficient_evidence",
  "answer": "Chưa có nguồn đã kiểm duyệt đủ để trả lời câu hỏi này.",
  "citations": [],
  "factReferences": [],
  "requestId": "fixture-request-001"
}
```

## Optional backlog and evolution

P1 extensions (Google identity, private landmark uploads/recognition and editable STT) have FR/US/UC identifiers but require a new reviewed API/media lifecycle before activation. Their earlier endpoint sketches are not part of the mandatory contract. No collections, weather, taste jobs or TTS endpoints.
Add optional fields compatibly; breaking changes require a new API major version and migration notice. Reconcile generated implementation OpenAPI with this design and run real request/schema tests before acceptance. Design JSON validation alone cannot prove authentication, transaction or model behavior.
