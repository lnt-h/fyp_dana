# Danang TourGuide — REST API Design

Version 1.0 | 2026-09-30. Base /api/v1; JSON; UUID IDs. This is a contract baseline, not generated OpenAPI or deployed endpoint inventory.
JWT access sessions for private resources; public read endpoints expose published POIs only. Every nested trip/stop/proposal ID is verified against ownership and parent membership. AI credentials never go to app.

## Conventions
Cursor pagination default 20/max 50. locale=vi|en; reject unsupported values. Structured error: code, message, details, requestId. 400 validation; 401 unauthenticated; 403/404 inaccessible; 409 revision/state conflict; 422 invalid AI/constraint result; 429 quota; 503 dependency unavailable. Never expose provider secrets or stacks.
Build/accept/create/arrival use stable idempotency keys where applicable. Store owner+endpoint+key+request hash in PostgreSQL; same key/different body returns 409. Return stored result for retries; in-progress retry returns typed conflict. No 202 build response until real async polling is implemented.

## P0 endpoints
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

GPS computation stays on app; no continuous /location stream. API cannot independently prove user presence. Simulated arrival requires server demo mode and preserves label in response. Route-unavailable plans may start only with explicit acknowledgement; UI shows missing times rather than claims of feasibility. Navigation handoff opens Maps, not a new turn-by-turn engine.

## Core request/response shapes
```json
{
  "TripPreferences": {
    "startDate": "2026-10-10", "dayCount": 1,
    "startPoint": {"lat": 16.05, "lng": 108.20},
    "interests": ["culture", "beach"], "pace": "balanced",
    "dailyStart": "09:00", "dailyEnd": "17:00",
    "budgetPreference": "moderate", "transportMode": "walking"
  },
  "BuildResponse": {
    "proposalId": "uuid", "baseRevision": 2,
    "status": "valid_or_provisional", "days": [],
    "warnings": [], "routeStatus": "fresh_or_unavailable",
    "modelVersion": "configured-model", "corpusVersion": "snapshot-id"
  },
  "Stop": {
    "id": "uuid", "placeId": "uuid", "seq": 1,
    "arrivalAt": null, "departureAt": null,
    "visitDurationMin": 45, "status": "upcoming"
  },
  "RouteLeg": {
    "fromStopId": "uuid", "toStopId": "uuid",
    "durationSeconds": null, "distanceMeters": null,
    "mode": "walking", "status": "unavailable",
    "provider": "google_routes", "fetchedAt": null
  },
  "AudioGuide": {
    "status": "available", "placeId": "uuid", "locale": "vi",
    "url": "short-lived-media-url", "durationSeconds": 180,
    "transcript": "reviewed text", "version": 1,
    "narrationType": "human_recorded"
  },
  "AskResponse": {
    "status": "grounded", "answer": "supported answer",
    "citations": [{"sourceId": "uuid", "chunkId": "uuid", "title": "source title", "url": "reviewed source URL"}],
    "factReferences": [], "requestId": "trace-id"
  }
}
```
Example status strings with _or_ illustrate alternatives, not literal enum values. Build status enum valid|provisional; route status fresh|stale|unavailable. Ask status grounded|insufficient_evidence|provider_unavailable. Provider_unavailable normally returns 503 with typed error. Structured operational answers use factReferences with source/date; citation IDs are server-validated, not accepted as arbitrary model URLs.
Audio-unavailable returns metadata with status=unavailable and no URL; missing POI is 404. Existing audio playback consumes media URL directly; GET never enqueues synthesis.

## P1 extensions
POST /auth/google verifies Google token and account-linking policy.
POST /media/scan-uploads returns owner-scoped short-lived PUT intent; POST /media/{id}/complete verifies object type/size; POST /ai/recognize receives mediaId/context → matched|ambiguous|unknown with corpus IDs and user-confirmation requirement.
POST /ai/transcribe receives approved short audio or upload ID → editable text. Enforce size/duration limits and temporary deletion. Provider/native STT implementation remains pending; text Ask endpoint unchanged.
No collections, weather, taste jobs, recommendations/for-you or TTS endpoints in V1.

## Validation and security
Allowlist preference fields/modes; validate coordinate bounds and day limits configured after timeline decision. Enforce request/AI quotas, bounded provider timeouts and input size limits. Refresh tokens in platform secure storage; access tokens short lived. Public maps use restricted client key. Ingestion is developer CLI with restricted credentials, not unauthenticated admin CRUD.
