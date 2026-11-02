# Mobile–API contract

REST resources use `/v1`. `GET /health` is process liveness, `GET /ready` verifies database connectivity, and authenticated `GET /v1/me` maps the verified Clerk subject to an internal account UUID. The committed `apps/api/openapi.json` is generated from FastAPI and checked for drift in CI. Client-supplied owner IDs never authorize access.

| Operation | Target contract |
|---|---|
| Explore | GET /cities, GET /places with cityId, locale, query and pagination, GET /places/{id}. Serve one immutable publication revision with reviewed execution-card fields, evidence/freshness summaries and required attribution. |
| Trips | POST /trips creates a private draft with one city, start date and dayCount 1–3. GET /trips and GET /trips/{id} return owned drafts/saved trips. PATCH updates metadata with expectedRevision. DELETE requires confirmation. |
| Generate/read | POST /trips/{id}/plan-previews accepts PlanningPreferences and prompt. Return missing required fields for clarification or a PlanPreview. GET /plan-previews/{id} resumes the latest owned preview. |
| Manual edit | PATCH /plan-previews/{id} with expectedRevision and requested edits appends a preview revision. Recompute affected routes, schedule and health. |
| Regenerate | POST /plan-previews/{id}/regenerate with expectedRevision, scope (trip/day/segment), target day or stop range, lockedStopIds and optional instruction. A locked day excludes all its stops and schedule from regeneration. |
| Save | POST /plan-previews/{id}/accept with expected preview revision and expected trip base revision. Revalidate expiry, content, ownership and health, then commit the accepted snapshot and increment trip revision atomically. |
| Local Guide | POST /ai/sessions then POST /ai/sessions/{id}/messages with scoped place/trip context. SSE delivers progress, text and a terminal result with citations, insufficient_evidence or typed failure. |

PlanPreview returns previewId, previewRevision, baseRevision, catalogManifestId, expiresAt, ordered days/stops/legs with stable IDs, planHealth, warnings, assumptions, locks and provenance. Each stop references the exact place publication/fact revision used. Each leg carries mode, route availability and permitted Google Routes distance/duration provenance when available. Timeline and map consume the same revision. A revision may be selected for review before acceptance.

## Catalog response boundary

Mobile receives Gonarra-owned/reviewed display fields and a compact provenance summary, not raw provider payloads. Operational fields use explicit knowledge and freshness states:

```json
{
  "value": "08:00-17:00",
  "knowledgeState": "KNOWN",
  "freshness": "CURRENT",
  "verifiedAt": "2026-11-02",
  "sourceRefs": ["src_..."],
  "attributions": []
}
```

Valid knowledge states are `KNOWN`, `UNKNOWN` and `NOT_APPLICABLE`; valid freshness states are policy-defined values such as `CURRENT`, `STALE` and `EXPIRED`. The API must not collapse unknown into an empty string or zero. Provider-only runtime fields include provider/retrieval time, expiry and mandatory attribution. They are omitted when unavailable rather than replaced by model output.

Catalog ingestion and review are privileged application workflows, not public mobile endpoints. Import commands accept a named provider/release and write staging only. Separate review/publish commands require authorized curator roles, expected candidate revision and an idempotency key. The generated OpenAPI must mark any future operational endpoints as internal/admin and the mobile client must not receive provider credentials.

## Failure and replay

Errors use `{ "error": { "code", "message", "retryable", "request_id", "context" } }`. Every response carries `X-Request-ID`; logs record request metadata without tokens or bodies.

Scope idempotency keys by owner and operation for generation, edits, regeneration and Save. Replay an identical successful request once logically, and reject key reuse with a different payload. Reject stale revisions with a conflict before committing. A blocked or expired preview cannot be accepted. Use a typed error code, request ID and field/revision details where applicable. Report retryability for timeouts/unavailability. Reject foreign nested IDs before a model or routing request. Keep accepted and pending state recoverable across retry.

Provider errors are typed by capability (`catalog_import_unavailable`, `runtime_place_unavailable`, `route_unavailable`) without leaking credentials or raw third-party bodies. A runtime enrichment failure may remove only that enrichment. A catalog import failure cannot change the current publication. A required route failure blocks the new preview but cannot damage the accepted trip.

## HA-02 • two days in Hội An

Create a Vietnamese two-day draft from a named published Hội An catalog manifest and Save a baseline. Open an edit preview, lock a day-two stop, regenerate day two only and return a new preview revision. Day one and the lock's stop identity, publication revision, day, relative lock order and visit duration survive. Use Google Routes for affected legs. Timeline and map show that revision before explicit Save. Force catalog refresh, Gemini or Routes failure on a retry: the prior accepted trip and pending edits remain available. A successful Save promotes the reviewed revision exactly once.
