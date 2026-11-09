# Gonarra API Contract (`/v1`, REST + SSE)

| Field | Value |
|---|---|
| Document ID | GONARRA-API |
| Document version | 2.0 (condensed; 0.1–0.4 five-city text at git tag `docs-sdlc-full`) |
| Contract | [openapi.yaml](./openapi.yaml) `info.version` 1.0.5 (OpenAPI 3.1.0); 34 operations; the generated `apps/api/openapi.json` is checked in CI |
| Date | 2026-11-09 |
| Owner | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor — **[Pending]** |
| Scope | Đà Nẵng only (`City.code` = `da-nang`, incl. the Hội An area); traveler app and two operator routes |

This document explains the rules that `openapi.yaml` cannot express on its own. When the two differ, `openapi.yaml` wins and this document is corrected. Architecture: [SAD](../architecture/SAD.md) §5; data: [data model](../data/data-model.md); screens: [screen specs](../ui-ux/screen-specs.md).

| Version | Date | Change |
|---|---|---|
| 0.1–0.4 | 2026-11-04..05 | Five-city design with curator admin routes (API-033..API-063) |
| 2.0 | 2026-11-09 | Rewritten against openapi 1.0.4: Đà Nẵng only; curator routes withdrawn (DEC-022); trust labels, research stages, calendar conflicts (DEC-015..017); `Leg.estimated` and INFO `LEG_ESTIMATED` (DEC-023); guest catalog reads, content-origin labels (1.0.3); AI-extracted facts `PlaceFact.origin` / `grounding` (DEC-028, 1.0.4) |
| 2.1 | 2026-11-09 | Against openapi 1.0.5 (DEC-031/DEC-032): AI-written catalog content retired (`AI_SUMMARY` descriptions and `AI_EXTRACTED` facts no longer produced); `PlaceSummary.is_area`; `PlaceDetail.description_source` attribution with licence and link; no description → 'No description yet' |

## 1. Consumers and boundaries

- **Consumers:** the traveler app `apps/mobile` (types generated from the contract) and the operator (owner) for two `/v1/admin` routes. No third-party consumers. The curator admin SPA is withdrawn (DEC-022).
- **External systems** (Clerk, Gemini, Groq, Tavily, Google Routes/Places, open-data sources, booking partners) are called only by the API, never by clients. Booking partners are reached through links built by API-030.
- **Out of scope:** booking or payment, flights, multi-city trips, social features, check-in, navigation.

## 2. Resource model

| Resource | Path | Persisted as | Notes |
|---|---|---|---|
| Identity, preferences | `/v1/me`, `/v1/me/preferences` | `accounts`, `account_preferences` | Clerk `sub` → account UUID; preferences saved explicitly |
| Account deletion | `/v1/me/deletion` | `account_deletion_jobs` | Singleton status resource |
| City, category | `/v1/cities`, `/v1/categories` | `cities`, `categories` | Small lists, not paginated; guests allowed |
| Place | `/v1/places`, `/v1/places/{place_id}` | publications, localizations, facts, sources, media | Published places only; guests allowed |
| Trip | `/v1/trips/{trip_id}` | `trips`, `trip_days`, `trip_stops`, `route_legs` | `revision` is the optimistic-concurrency token |
| Place card | `/v1/trips/{trip_id}/stops/{stop_id}/place-card` | publication of a saved stop | Sub-resource of a saved stop |
| Plan preview | `/v1/trips/{trip_id}/plan-previews`, `/v1/plan-previews/{preview_id}` | `plan_previews`, `preview_revisions` | Immutable revisions; `/regenerate` and `/accept` are state transitions |
| Guide session, message | `/v1/ai/sessions/{session_id}/messages` | `guide_sessions`, `guide_messages`, `guide_message_citations` | Scope `CITY` (default) or `PLACE` |
| Photo identification | `/v1/ai/photo-identifications` | nothing | Planned |
| Handoff link, stay prices | `/v1/trips/{trip_id}/handoff-links`, `/stay-prices` | nothing | Prices `Cache-Control: no-store` |
| Study timing event | `/v1/study/timing-events` | `study_session_logs` | Planned |
| Operator | `/v1/admin/places/{place_id}/unpublish`, `/v1/admin/cities/summary` | publications, audit events | Operator allow-list |

Naming: plural nouns, kebab-case path segments, snake_case parameters and JSON fields that match `schema.sql` column names where they overlap. Nesting at most two levels.

## 3. Rules

### 3.1 Composition

All routes are FastAPI routers under `apps/api/app/api/routes/` (`health`, `identity`, `preferences`, `catalog`, `trips`, `previews`, `guide`, `deletion`, `admin`). Routing, agents, research and provider adapters expose no HTTP route; clients reach them only through the operations in §3.11.

### 3.2 Locale

Content operations take `locale` (`vi` | `en`); it defaults to the account preference, then `vi`. Vietnamese names are always returned. `PlaceSummary.name_is_source_fallback = true` means the EN name is the Vietnamese proper name reused unchanged, never machine-translated. Descriptions are verbatim human-written text from a cited source (DEC-031): `PlaceDetail.description_origin` is `SOURCE` or null, and `PlaceDetail.description_source` names the provider, publisher, licence and link (Wikivoyage CC BY-SA 4.0, Wikipedia, the owner sheet); a place without one returns null description and the client shows 'No description yet' / 'Chưa có mô tả'. `PlaceFact.origin` is `SOURCE` or `OWNER` (`AI_EXTRACTED` is retired); `grounding` stays null. `PlaceSummary.is_area` marks a bay, peninsula, mountain range or old town: it appears on the map and in Guide answers but can never be added as a planner stop — clients disable 'Add to trip' and say 'Area — pick a place inside it' / 'Khu vực — chọn điểm cụ thể bên trong'.

### 3.3 Authentication and authorization

- **Bearer token.** Every `/v1` operation takes `Authorization: Bearer <Clerk session JWT>`, except the public probes `/health` and `/ready`. The API verifies the RS256 signature against the cached Clerk JWKS plus issuer, time claims, subject and authorized party (`app/security/clerk.py`, ADR-005). The API is stateless.
- **Guests.** API-008..API-011 (catalog reads) declare `security: [{}, HTTPBearer]`: a request without a token is served; a token that is sent must still be valid (401 otherwise).
- **Demo shared user** (non-production only): with `GONARRA_DEMO_SHARED_USER=true` and `GONARRA_ENVIRONMENT` in `development`, `test` or `demo`, a request without an `Authorization` header acts as one shared demo account. A sent token is still verified. Never available in staging or production; never grants the operator role.
- **Owner checks.** The account comes from `sub`, never from a client-supplied ID. Each private resource is loaded with `account_id = caller`; a foreign or missing resource answers **404 `resource_not_found`**. Nested IDs (`place_id`, `stop_id`, `locked_stop_ids`, `trip_id`) are checked before any model, search or provider call.
- **Operator.** `/v1/admin/*` declares `HTTPBearer: [curator]`; the server checks the subject against `GONARRA_CURATOR_CLERK_USER_IDS` (default empty = nobody). Others get **403 `curator_role_required`**.
- **Deletion in progress.** Every authenticated route except API-006 and API-007 answers **409 `deletion_in_progress`** while the caller's account deletion runs.

### 3.4 Error envelope

Every non-2xx response uses `ErrorResponse` and carries `X-Request-ID`:

```json
{ "error": { "code": "revision_conflict", "message": "The trip changed since this preview was opened.",
  "retryable": false, "request_id": "req_example_0002",
  "context": { "expected_trip_revision": 1, "current_revision": 2 } } }
```

| HTTP | `code` values (as implemented) | Meaning |
|---|---|---|
| 400 | `invalid_cursor` | Malformed cursor or request |
| 401 | `authentication_required` | Token missing, invalid or expired |
| 403 | `curator_role_required` | Not on the operator allow-list |
| 404 | `resource_not_found`, `feature_disabled` | Absent, owned by another account, or the feature flag is off |
| 409 | `revision_conflict`, `idempotency_key_reused`, `idempotency_in_progress` (retryable), `plan_blocked`, `trip_not_saved`, `deletion_in_progress` | State precondition failed |
| 410 | `preview_expired`, `preview_closed` | Preview expired, discarded or already saved |
| 413 / 415 | payload too large / unsupported media type | Photo upload limits (planned API-029) |
| 422 | `validation_error` (with `context` field errors), `unsupported_request`, `place_not_in_city`, `publication_incomplete`, `web_unverified_acknowledgement_required` | Well-formed request, rejected content |
| 429 | `quota_exceeded` (retryable) | Per-account daily cap reached (§3.8) |
| 501 | `not_implemented` | Indicative stay prices (flag on, provider not built) |
| 503 | `service_unavailable` | Dependency down; saved itinerary and last preview unchanged |

`message` is safe to show. Provider bodies, SQL errors, tokens, prompts and question text never appear in `message` or `context`. Request bodies are strict: unknown fields are rejected and lengths are bounded.

### 3.5 Idempotency and revisions

| Rule | Detail |
|---|---|
| Safe methods | GET has no side effects. PUT `/v1/me/preferences` is a full replace. DELETE of a trip, preview or Guide session can be repeated |
| `Idempotency-Key` | Client UUID header, scoped by account and operation, kept 24 h in `idempotency_records` with a request hash and the stored response. **Optional** on API-012, API-018, API-020, API-021, API-028; **required** on API-022 (Save) and API-037 (unpublish) |
| Replay | Same key + same body after completion → stored status and body with `Idempotent-Replayed: true`, no repeated side effect. Same key + different body → 409 `idempotency_key_reused`. Same key still running → 409 `idempotency_in_progress` |
| Trip revision | `trips.revision` changes only on Save (API-022) and title update (API-015). API-015, API-016, API-018 and API-022 carry an expected trip revision; a mismatch is 409 `revision_conflict` with `context.current_revision` |
| Preview revisions | Each generation, edit or regeneration appends an immutable revision whose parent must equal the current head (`expected_revision`); otherwise 409 and nothing is appended |
| Save (API-022) | One transaction: owner; preview active; `expected_preview_revision` and `expected_trip_revision` current; `plan_health` ≠ BLOCKED (else 409 `plan_blocked`); `acknowledge_web_unverified = true` when any stop is `WEB_UNVERIFIED` (else 422); every stop's publication still eligible. Then the saved days, stops and legs are replaced, `trips.revision` increments and the preview becomes SAVED (ADR-009) |
| Failure isolation | Model and provider calls run outside database transactions. A failure appends no revision and never touches the saved trip |

### 3.6 Streaming (SSE)

API-018, API-021 (planning) and API-028 (Guide) return `text/event-stream` when the client sends `Accept: text/event-stream`, otherwise one JSON body. Each event is `event: <type>` with one `data:` JSON line validated by the schema; a `: keep-alive` comment is sent every 15 s while idle.

| Stream | Event `type` | Payload | Terminal |
|---|---|---|---|
| `PlanningStreamEvent` | `progress` | `stage` (VALIDATING_REQUEST, SELECTING_PLACES, RESEARCHING, VERIFYING_WEB_PLACES, ROUTING, SCHEDULING, CHECKING_HEALTH, WRITING), `agent` (`selector`, `researcher`, `grounded_writer` or null), `detail{catalog_candidates, web_candidates, verified}` | No |
| | `clarification_required` | missing city, start date or day count | Yes |
| | `preview_ready` | `preview_id`, `preview_revision`, `plan_health` | Yes |
| | `error` | `ErrorDetail` | Yes |
| `GuideStreamEvent` | `progress` | `stage` (VALIDATING, RETRIEVING, SEARCHING_WEB, ANSWERING) | No |
| | `text` | `delta` | No |
| | `result` | stored assistant `GuideMessage` with `answer_status` and citations | Yes |
| | `error` | `ErrorDetail` | Yes |

RESEARCHING and VERIFYING_WEB_PLACES appear only when the research agent runs (flag off by default). SEARCHING_WEB and `ANSWERED_WEB_UNVERIFIED` are reserved for the Guide web fallback, which is not built yet. Results are persisted before the terminal event; after a dropped stream the client reads API-019 (preview) or API-027 (messages) instead of repeating the call. Citations not in the supplied evidence are removed; an answer left without a valid citation is `INSUFFICIENT_EVIDENCE`.

### 3.7 Pagination, filtering and sorting

List operations API-010, API-013, API-027 and API-031 take `cursor` (opaque, ≤ 512 chars) and `limit` (1–50, default 20) and return `{ "items": [...], "next_cursor": string | null }`; an invalid cursor is 400 `invalid_cursor`. Filters: API-010 `city_id` or `city_code`, `area_code`, `bbox`, `near` + `radius_m`, `q`, `category_code`, `sort`; API-013 `status`, `sort`. Cities, categories and the city summary are not paginated.

### 3.8 Quotas

Per-account daily caps (defaults): 10 proposals (API-018 generate, API-021) and 40 Guide questions (API-028). A reached cap answers 429 `quota_exceeded` before any provider call. Global provider caps live in the quota ledger ([SAD §3.3](../architecture/SAD.md#33-quota-ledger-fallback-chains-and-caches-dec-018)); exhausting one degrades the step (fallback model, rule-based selection, null rationale, `INSUFFICIENT_EVIDENCE`) instead of failing silently. Catalog reads, edits and Save are not quota-limited.

### 3.9 Privacy (BR-046)

- Prompts get redacted DTOs only: no account ID, Clerk subject, contact data, trip ID or precise location reaches Gemini, Groq, Tavily or a fetched page. The redactor fails closed.
- Logs hold request ID, route, status and latency only; never tokens, bodies, questions, answers, prompts or coordinates.
- Photo identification (planned) uses one coarse location fix only for the 300 m filter, in memory.
- Study events (planned) store a participant code, locale, two timestamps and the save outcome, never text.
- Stay prices are runtime-only and `no-store`.

### 3.10 Versioning and compatibility

- Major version in the path (`/v1`); `/health` and `/ready` are unversioned probes.
- Additive within v1: new operations, optional request fields, response fields, error codes and enum values. Clients treat unknown enum values as "other".
- Breaking changes need `/v2` and an ADR. Deprecations use `deprecated: true` plus `Deprecation` and `Sunset` headers at least one release ahead.
- `info.version` follows SemVer; the history of 1.0.1..1.0.5 is in the `info.description` of `openapi.yaml`.

### 3.11 Operation table

Status: **built** = route exists in `apps/api`; **planned** = in the contract, no route yet; **stub** = route returns a fixed error.

| API ID | Method and path | operationId | Auth | Status |
|---|---|---|---|---|
| API-001 | `GET /health` | health_health_get | public | built |
| API-002 | `GET /ready` | readiness_ready_get | public | built |
| API-003 | `GET /v1/me` | read_identity_v1_me_get | bearer | built |
| API-004 | `GET /v1/me/preferences` | getPreferences | bearer | built |
| API-005 | `PUT /v1/me/preferences` | putPreferences | bearer | built |
| API-006 | `POST /v1/me/deletion` | requestAccountDeletion | bearer | built |
| API-007 | `GET /v1/me/deletion` | getAccountDeletionStatus | bearer; 401 after the Clerk user is deleted (client treats it as completed, OQ-073) | built |
| API-008 | `GET /v1/cities` | listCities | guest or bearer | built |
| API-009 | `GET /v1/categories` | listCategories | guest or bearer | built |
| API-010 | `GET /v1/places` | searchPlaces | guest or bearer | built |
| API-011 | `GET /v1/places/{place_id}` | getPlace | guest or bearer | built |
| API-012 | `POST /v1/trips` | createTrip | bearer | built |
| API-013 | `GET /v1/trips` | listTrips | bearer | built |
| API-014 | `GET /v1/trips/{trip_id}` | getTrip | bearer | built |
| API-015 | `PATCH /v1/trips/{trip_id}` | updateTrip | bearer | built |
| API-016 | `DELETE /v1/trips/{trip_id}` | deleteTrip | bearer | built |
| API-017 | `GET /v1/trips/{trip_id}/stops/{stop_id}/place-card` | getPlaceCard | bearer | built |
| API-018 | `POST /v1/trips/{trip_id}/plan-previews` | createPlanPreview | bearer; SSE | built |
| API-019 | `GET /v1/plan-previews/{preview_id}` | getPlanPreview | bearer | built |
| API-020 | `PATCH /v1/plan-previews/{preview_id}` | editPlanPreview | bearer | built |
| API-021 | `POST /v1/plan-previews/{preview_id}/regenerate` | regeneratePlanDay | bearer; SSE | built |
| API-022 | `POST /v1/plan-previews/{preview_id}/accept` | acceptPlanPreview | bearer; key required | built |
| API-023 | `DELETE /v1/plan-previews/{preview_id}` | discardPlanPreview | bearer | built |
| API-024 | `POST /v1/ai/sessions` | createGuideSession | bearer | built |
| API-025 | `GET /v1/ai/sessions/{session_id}` | getGuideSession | bearer | built |
| API-026 | `DELETE /v1/ai/sessions/{session_id}` | deleteGuideSession | bearer | built |
| API-027 | `GET /v1/ai/sessions/{session_id}/messages` | listGuideMessages | bearer | built |
| API-028 | `POST /v1/ai/sessions/{session_id}/messages` | askGuide | bearer; SSE | built (no web fallback) |
| API-029 | `POST /v1/ai/photo-identifications` | identifyPlaceFromPhoto | bearer; multipart | planned (Should) |
| API-030 | `GET /v1/trips/{trip_id}/handoff-links` | getHandoffLink | bearer | built (Agoda, Booking.com, Klook, 12Go) |
| API-031 | `GET /v1/trips/{trip_id}/stay-prices` | getIndicativeStayPrices | bearer | stub: 404 `feature_disabled` when the flag is off, else 501 (Could) |
| API-032 | `POST /v1/study/timing-events` | recordStudyTimingEvent | bearer, study participants only | planned |
| API-033..036, API-038..041, API-043..063 | curator review, publish, imports, sources, facts, closure rules, chunks, web-candidate queue | n/a | n/a | **withdrawn** (DEC-022); IDs not reused |
| API-037 | `POST /v1/admin/places/{place_id}/unpublish` | adminUnpublishPlace | operator; key required | built |
| API-042 | `GET /v1/admin/cities/summary` | adminGetCitySummary | operator | built |

Requirement links (`x-fr`, `x-nfr`) are on each operation in `openapi.yaml`; screen links are in the [screen specs](../ui-ux/screen-specs.md).

## 4. Trust labels on the wire

`Stop`, `PlaceSummary`, `PlaceDetail` and `Citation` carry `trust_level`:

- `VERIFIED`: the place passed Gonarra's automated publication gate (DEC-022; not human review). Payload has `place_id`, `catalog_publication_id`, facts with source and `verified_at`. Copy reads "Source-checked · <date>" / "Đã đối chiếu nguồn · <date>".
- `WEB_UNVERIFIED`: a research-agent candidate. `place_id` is null; `web_source{url, fetched_at, candidate_id}`; no facts. Shown with a badge on every surface; Plan Health is at most WARNING (`WEB_PLACE_UNVERIFIED`); Save needs `acknowledge_web_unverified` (OQ-128).

`Leg.estimated = true` marks a straight-line demo estimate (development, test and demo only) and comes with an INFO `LEG_ESTIMATED` conflict that never changes `plan_health` (DEC-023).

## 5. Open points

| ID | Point | Status |
|---|---|---|
| OQ-039 | Production hostname (servers entry is a placeholder) | Open; with OQ-129 hosting |
| OQ-127 | "Thin pool" threshold and per-plan research caps | Open |
| OQ-128 | Acknowledgement before saving a plan with a `WEB_UNVERIFIED` stop | Built as `acknowledge_web_unverified`; mentor confirmation pending |
| OQ-134 | Existence check for web candidates without Google Places | Open |
| n/a | `TrustLevel` description in `openapi.yaml` still says "curator-reviewed"; correct wording is "passed the automated publication gate" (DEC-022) | Fix in the next API change (generated from code) |
