# ADR-014 — Catalog-first runtime research agent, trust labels and auto-promotion of web candidates

| Field | Value |
|---|---|
| Status | Proposed; accepted by the owner (DEC-015, DEC-022); mentor review at M0 [Pending] (OQ-131) |
| Date | 2026-11-06 |
| Version | 0.1 (reconstructed from [SAD](../architecture/SAD.md) §3.4–3.5 and §5, DEC-015, DEC-017, DEC-022) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | DEC-015, DEC-017, DEC-018, DEC-022 ([decisions](../../decisions.md)); reverses ADR-010 option D and BRD §5.2 "no runtime web search" |

> **Superseded in part by DEC-023 (2026-11-08).** The existence check by Google Places is replaced by open-data
> matching (OSM/Wikidata name and location; design OQ-134). Until it exists, research candidates are stored without
> coordinates, are not scheduled and are not auto-promoted. The researcher stays Groq-only (`openai/gpt-oss-120b`,
> DEC-026). The decision text below is kept as history.

## Context

A thin Đà Nẵng catalog leaves requests unmet and Guide questions unanswered. Web content can fill gaps but may be
wrong (RSK-012), and free-tier search quota is small (RSK-013). The thesis claim is that travelers can tell what
Gonarra has checked from what it has not (MET-014). Since DEC-022 there is no human review: `VERIFIED` means "passed
Gonarra's automated source checks" (ADR-012), and no curator queue exists.

## Decision

- **Catalog-first.** The `researcher` (ADR-013) runs only when the catalog pool is thin (threshold OQ-127), the
  selector reports unmet requests, or Guide evidence is insufficient — and only within quota and per-plan caps.
- **Existence check.** Every web-found place passes `places_check` (Google Places, minimal field mask). It is stored
  only in `web_place_candidates` (name, source URL, `fetched_at`, Google `place_id`, Gonarra's existence verdict,
  `coordinate_source`); only `place_id` is kept canonically (ADR-006). An unresolved candidate is
  `WEB_PLACE_UNRESOLVED` (blocking) or dropped.
- **Trust labels.** Enum values stay `VERIFIED` / `WEB_UNVERIFIED` (no contract or DB change). `VERIFIED` = published
  place that passed the automated publication gate; copy "Source-checked · <date>" / "Đã đối chiếu nguồn · <date>".
  `WEB_UNVERIFIED` = web-found place or web evidence, shown with source host/URL and fetched date (stale after
  7 days) on every surface: search result, proposal stop, timeline, map pin, place card, Guide citation. No copy says
  "Verified", "reviewed" or "Đã kiểm duyệt".
- **Plans.** A `WEB_UNVERIFIED` stop is real and saveable; Plan Health is capped at `WARNING`
  (`WEB_PLACE_UNVERIFIED`); Save of such a plan requires acknowledgement (OQ-128).
- **Guide.** Deterministic web fallback when catalog evidence is empty: status `ANSWERED_WEB_UNVERIFIED`, every claim
  cited to a fetched page; otherwise `INSUFFICIENT_EVIDENCE` (ADR-010).
- **Auto-promotion (DEC-022).** A candidate whose Places check returns `EXISTS_OPERATIONAL` inside the Đà Nẵng
  boundary is auto-promoted into the ingestion pipeline (an `IMPORTED` place, idempotent per candidate). It becomes
  `VERIFIED` only if the automated publication gate later passes it; trips holding it then show the upgraded trust
  through `vw_trip_stop_trust`. Any other outcome stays request-scoped `WEB_UNVERIFIED`. There is no curator queue.
- **Model limits.** A model may propose a candidate only through the research schema; it never publishes a place and
  never authors a free-form displayed fact, hour, price, distance or duration. Any future model-extracted fact must
  carry a verbatim quote that code finds in the fetched page text, else it is rejected.
- **Safety.** SSRF-guarded fetch (HTTPS, public addresses, ≤ 3 redirects, size/time limits); redacted queries
  (BR-046); feature flag, turned off for the study if precision is below threshold (OQ-128, RSK-012).

## Options

| Option | Verdict | Why |
|---|---|---|
| A. Catalog-first research with Places check, labels, WARNING cap, auto-promotion through the gate | **Chosen** (DEC-015 rev. by DEC-022) | Fills gaps, keeps the trust distinction visible, no review workload |
| B. Same, with a curator review queue (DEC-015 original) | Superseded by DEC-022 | Review workload threatens the release gate (RSK-001) |
| C. No runtime web search (ADR-010 option D, BRD §5.2) | Reversed | Thin catalog leaves requests unmet |
| D. Model decides when to search and publishes what it finds | Rejected | Non-deterministic; models never publish |

## Consequences

- Positive: thin-catalog requests still complete; web content is always labelled; the catalog grows from real,
  checked places without human review.
- Negative: no human catches a wrong but existing place (RSK-105); Tavily, Groq and Places quotas bound use
  (RSK-013); research precision must be measured (ASM-020, MET-014).

## Drivers

BRU-002, BRU-003, FR-004, FR-030, FR-031, FR-098, FR-099, FR-100, FR-101, FR-105, MET-014, RSK-012, RSK-013, RSK-105,
OQ-122, OQ-124, OQ-127, OQ-128, OQ-131.
