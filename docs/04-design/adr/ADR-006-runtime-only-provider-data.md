# ADR-006 — Runtime-only provider data policy (Google Places, Routes, Tavily, web pages, Groq, LiteAPI)

| Field | Value |
|---|---|
| Status | Proposed (mentor approval at M0) |
| Date | 2026-11-04 (0.2: 2026-11-06) |
| Version | 0.2 (0.1 → 0.2: providers `tavily`, `web_page`, `groq`; Places `place_id` identifier-only, lat/lng ephemeral ≤ 30 d, status and hours runtime-only; DEC-015, DEC-018) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | BRU-004, BRU-005, SRC-104; SRC-105 OQ-122, OQ-123, OQ-124 |

> **Superseded in part by DEC-023 (2026-11-08).** No Google Maps Platform product (Routes, Places) is called in the
> FYP demo; the `google_places` and `google_routes` rows below apply only when Google is configured
> (`GONARRA_ROUTES_PROVIDER=google` or `auto` with a key). The demo's straight-line estimates come from code, not a
> provider: they are attributed to the `routes_estimate` data provider, are never written to `routes_matrix_cache`
> and are allowed only in `development`, `test` and `demo`. Open-data sources added by DEC-024: `osm` (Overpass, ODbL
> 1.0, "© OpenStreetMap contributors", one source revision per element) and `wikimedia_commons` (per-file licence
> CC0 / PD / CC BY / CC BY-SA with author; thumbnails hot-linked, `media_assets.object_key` is an absolute URL). The
> web-candidate existence check moves to open-data matching (OQ-134). The decision text below is kept as history.

## Context

Provider terms restrict what may be stored: Google Places (hours, status, coordinates), Google Routes (matrix
values), Tavily (search results and extracted text), fetched web pages (copyright), Groq and Gemini (free-tier data
use), LiteAPI (prices never stored). Free tiers force caches, so every cache needs a named policy and a TTL.
Attribution must appear wherever provider or open data appears. Logs must not become a shadow cache.

## Decision

- Every provider has a `data_providers` row (`provider_kind` adds `WEB_SEARCH`, `WEB_CONTENT`) and one ACTIVE
  `provider_policies` revision; `provider_field_rules` classify each field as `ALLOW_CANONICAL`, `ALLOW_EPHEMERAL`
  (with `max_retention`), `ALLOW_IDENTIFIER_ONLY` or `DENY`. A field without a rule is denied. The seed script
  installs the policies below; the owner records terms versions before the first live call.
- Cache tables carry `expires_at` derived from the policy `max_retention`; the CLI `jobs` sweep deletes expired rows.
- Raw provider bodies are never logged or persisted.

| Provider | Field | Class | Retention / store |
|---|---|---|---|
| `google_places` | `place_id` | IDENTIFIER_ONLY | `external_place_identities`, `web_place_candidates.google_place_id`, `places_lookup_cache` |
| `google_places` | lat/lng | EPHEMERAL | `places_lookup_cache.location` ≤ 30 d (OQ-124); never copied into `places` or `web_place_candidates` |
| `google_places` | `business_status`, `regular_opening_hours` | DENY (runtime only) | Shown on the card with "retrieved at"; Gonarra's own verdict `places_check_outcome` cached 24 h |
| `google_routes` | distance, duration per pair | EPHEMERAL | `routes_matrix_cache` 30 d; saved `route_legs` keep `measured_at`/`expires_at` |
| `tavily` | results (url, title, snippet) | EPHEMERAL | `research_cache` 7 d (OQ-122) |
| `web_page` | url, `content_sha256`, `retrieved_at` | CANONICAL | one `source_revisions` row per fetched URL |
| `web_page` | extracted text | EPHEMERAL | `research_cache` 7 d; evidence quotes ≤ 300 chars in `web_place_candidates.extraction` |
| `groq`, `gemini` | prompts, raw responses | DENY | `ai_invocations` metadata only; same redaction for both (OQ-123) |
| `liteapi` | prices, rates | DENY | Displayed per view behind `FEATURE_STAY_PRICES`; nothing stored |

## Options

| Option | Verdict | Why |
|---|---|---|
| A. Policy registry, default-deny, TTL caches in PostgreSQL | **Chosen** | Terms-compliant by construction; auditable; one sweep |
| B. Prefetch Places details into the catalog | Rejected | Breaches terms; restricted data becomes "fact" |
| C. Store web text as catalog content | Rejected | Copyright; unreviewed text would look verified |
| D. Providers called from the mobile app | Rejected | Exposes keys; bypasses quotas and redaction |

## Consequences

- Positive: compliance is testable (0 denied fields persisted, 0 prices stored, every cache row has a policy).
- Negative: every new provider needs a policy before code may persist anything; Places checks cost quota per
  candidate (capped, ADR-014).

## Drivers

BRU-004, BRU-005, BR-043, BR-047, CON-006, RSK-002, QAS-12, OQ-122..OQ-124.
