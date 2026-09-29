# API Design — Danang TourGuide

| Attribute | Value |
|-----------|-------|
| System | Danang TourGuide HTTP API |
| SDD Version | 0.1 |
| Date | 2026-09-29 |
| Style | REST, JSON, OpenAPI 3.0 (this doc is the design source) |
| Auth | Bearer JWT; optional guest token |
| Base path | `/api/v1` |

---

## 1. Context

| Attribute | Value |
|-----------|-------|
| System purpose | Mobile companion backend |
| API consumers | First-party Expo app only (V1) |
| External systems | Gemini, S3, Maps, Weather, OAuth, TTS |
| UI channel | React Native |
| Trust | Public internet → authenticated API |
| Devices | iOS/Android phones |

### Constraints

OpenAPI 3; validation via class-validator/Zod; rate limit AI and auth; timeouts on Gemini.

---

## 2. Conventions

- Resource names: plural nouns.
- Errors: `{ "code": "TASTE_JOB_FAILED", "message": "...", "details": {}, "requestId": "..." }`; no stack traces or provider secrets.
- Pagination: `?cursor=&limit=` for lists; `limit` default 20 max 50.
- IDs: UUID.
- Language: `Accept-Language` or `X-Lang: vi|en`.
- Idempotency: `Idempotency-Key` on `POST /trips/{id}/build`.
- Owner scope: JWT/guest token is checked on every media, job, profile, explanation, trip and arrival operation; an ID alone never grants access.

### HTTP mapping

| Status | Use |
|--------|-----|
| 200/201 | Success |
| 202 | Async job created |
| 400 | Validation |
| 401 | Missing/invalid token |
| 403 | Not owner |
| 404 | Unknown resource |
| 409 | Conflict (e.g. trip not draft) |
| 429 | Rate limit |
| 503 | Dependency timeout |

---

## 3. Endpoints (V1)

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Email register |
| POST | `/auth/login` | No | Email login |
| POST | `/auth/google` | No | Google ID token |
| POST | `/auth/guest` | No | Guest session |
| POST | `/auth/guest/merge` | User | Attach guest DNA/saves |
| POST | `/auth/refresh` | Refresh | Rotate tokens |

### Media

| Method | Path | Description |
|--------|------|-------------|
| POST | `/media/uploads` | Body: `{ count, purpose: taste\|explore_image }`. Returns `{ assets: [{ id, putUrl }] }` |
| POST | `/media/{id}/complete` | API verifies object exists, size/type and owner before marking uploaded |

### Preferences

| Method | Path | Description |
|--------|------|-------------|
| POST | `/preferences/taste-jobs` | `{ mediaIds: UUID[5..10] }` → 202 `{ jobId }` |
| GET | `/preferences/taste-jobs/{jobId}` | Status + DNA when done |
| GET | `/preferences/me` | Current Travel DNA |
| PATCH | `/preferences/me` | Edit attribute scores; sets confirmed |

### Places & search

| Method | Path | Description |
|--------|------|-------------|
| GET | `/places` | Filter category, bbox; paginated |
| GET | `/places/{id}` | Detail + optional `?matchForUser=true` |
| GET | `/search` | `q`, `near=lat,lng`, `radiusM` |
| GET | `/places/{id}/explanation?runId={runId}` | Evidence from caller-owned run; 404 if not in that run |

### Recommendations

| Method | Path | Description |
|--------|------|-------------|
| GET | `/recommendations/for-you` | Top-K; query `lat,lng` optional |
| POST | `/recommendations/explore-by-image` | `{ mediaId }` P1 |
| POST | `/places/{id}/signals` | `{ type: not_interested }`; guest or user scope, idempotent |

### Saved

| Method | Path | Description |
|--------|------|-------------|
| GET | `/saved` | List |
| POST | `/saved` | `{ placeId, collectionId? }` |
| DELETE | `/saved/{placeId}` | |
| GET/POST | `/collections` | P1 |

### Trips

| Method | Path | Description |
|--------|------|-------------|
| POST | `/trips` | `{ startDate, endDate, companions, budget, pace }` |
| GET | `/trips` | History |
| GET | `/trips/{id}` | Aggregate + days/stops |
| POST | `/trips/{id}/build` | AI/heuristic builder 202 or 200 |
| PATCH | `/trips/{id}/stops/{stopId}` | Duration, day, seq |
| POST | `/trips/{id}/stops` | Add place |
| DELETE | `/trips/{id}/stops/{stopId}` | |
| POST | `/trips/{id}/optimize` | P1 `{ mode: min_distance\|balanced\|favorites }` |
| GET | `/trips/{id}/route` | Polyline + legs |
| POST | `/trips/{id}/start` | status active |
| POST | `/trips/{id}/location` | Foreground `{ lat, lng, accuracyM, at }` → current-stop arrival if accurate/in radius; idempotent |
| POST | `/trips/{id}/stops/{stopId}/arrive` | Manual “I’m here”; simulator mode only in labeled demo build |
| POST | `/trips/{id}/stops/{stopId}/complete` | |
| POST | `/trips/{id}/stops/{stopId}/skip` | |

### Guide & AI

| Method | Path | Description |
|--------|------|-------------|
| GET | `/places/{id}/guides` | `{ quick, main, fact }` texts |
| GET | `/places/{id}/guides/{kind}/audio` | URL or 202 synthesizing |
| POST | `/ai/ask` | `{ text, placeId?, tripId? }` |

### Weather (P1)

| GET | `/trips/{id}/weather-alerts` | Proposals |

### Feedback (P1)

| POST | `/places/{id}/feedback` | `{ rating, reasons[] }` |

---

## 4. Core schemas

```json
{
  "PlaceSummary": {
    "id": "uuid",
    "name": "string",
    "category": "string",
    "lat": 16.05,
    "lng": 108.2,
    "heroImageUrl": "string",
    "matchPercent": 89,
    "tags": ["Beach", "Quiet"]
  },
  "TripStop": {
    "id": "uuid",
    "placeId": "uuid",
    "arrivalTime": "09:30",
    "departureTime": "11:00",
    "visitDurationMin": 90,
    "travelTimeToNextMin": 15,
    "status": "upcoming"
  },
  "TravelDna": {
    "attributes": { "nature": 0.92, "beach": 0.87 },
    "confirmed": true,
    "version": 2
  },
  "Explanation": {
    "runId": "uuid",
    "placeId": "uuid",
    "nodes": [
      { "type": "photo", "mediaId": "uuid" },
      { "type": "attribute", "key": "nature" },
      { "type": "place", "placeId": "uuid" }
    ]
  },
  "AskAiResponse": {
    "answer": "string",
    "citations": [{ "chunkId": "uuid", "placeId": "uuid" }],
    "refusedFact": false
  }
}
```

`matchPercent` is a calibrated 0–100 display score with a scoring version, not a raw cosine value or probability. The `TripStop` response includes `routeStatus: fresh|estimated|stale`, and an arrival response includes `method: gps|manual|simulated`.

---

## 5. Quality

| Concern | Design |
|---------|--------|
| Performance | Cache For You in Redis 5–15 min; paginate places |
| Security | Owner checks on trips/media; signed S3 PUT with short TTL |
| Reliability | Job status machine; 503 + retry on Gemini |
| Traceability | `requestId` in logs and error body |

### State and error contracts

- Taste job: `POST` returns 202 and `{jobId,status:"queued"}`; `GET` returns `queued|processing|succeeded|failed` with a sanitized retryable error. A repeated completion request is safe.
- Trip build: one documented mode per deployment. V1 uses 200 for a completed synchronous heuristic build; if it becomes asynchronous, return 202 with `{jobId}` and add a polling endpoint before mobile integration. Idempotency key + request body hash prevents duplicate plans.
- Editing stops marks route legs stale until a route refresh succeeds. Failed provider calls return a clearly labeled estimate or an unavailable status.
- For You with no confirmed DNA returns a typed `PROFILE_REQUIRED` state. Guest saves require sign-in/merge; guest `not_interested` is scoped to the guest session.
- `POST /ai/ask` distinguishes grounded answer, insufficient evidence and provider unavailable. Citations are assembled from retrieved database chunk/source IDs after generation, never accepted from arbitrary model text.

---

## 6. Out of public API

Admin ingest is **CLI/scripts** against DB, not public REST in V1 (optional internal `/admin` later with separate auth).
