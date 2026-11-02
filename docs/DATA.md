# Data supply, provenance and publication

This contract defines where Gonarra data comes from, what may be retained, how facts become publishable and what Generative AI may do. A provider response, model output or imported row is never trusted merely because it is machine-readable.

## Data ownership classes

| Class | Examples | Persistence rule | Authority |
|---|---|---|---|
| Gonarra canonical catalog | Reviewed place identity, original bilingual copy, suggested visit duration, execution-card facts | Store and version in PostgreSQL | Gonarra publication workflow |
| Open licensed seed data | Overture Places, Foursquare Open Source Places, Wikidata | Store only with source release, record-level identifiers, license and required notices | Candidate discovery and identity evidence; never automatically publish |
| Licensed local provider data | VietMap, Goong or Map4D place/address data | Retain only fields and durations allowed by a signed/current agreement | Provider for the contracted fields |
| Runtime restricted provider data | Google Places current hours, business status, rating, reviews or photos | Do not prefetch or turn into the permanent catalog. Persist only expressly permitted identifiers/metadata and ephemeral cache state | Provider response at the displayed retrieval time |
| Route measurements | Google Routes distance, duration, polyline/status | Retain only as permitted, with provider, mode, request time and expiry; recompute when invalidated | Google Routes for the measured leg |
| First-party evidence | Official operator, monument authority, tourism authority or verified partner facts | Store the supported claim, source revision/URL and review date; write original summaries rather than copying protected prose | Named publisher for the supported claim |
| Licensed media | Owned images, written permission or a compatible Wikimedia Commons asset | Store rights proof, creator, license, attribution, derivative status and expiry | Rights holder/license |
| User data | Preferences, saved places, prompts, previews and trips | Owner-scoped retention and deletion rules apply | User action plus application state |
| AI-derived draft | Translation draft, rationale, summary or candidate ordering | Never authoritative; keep unpublished until deterministic checks and required human review pass | No factual authority |

## Approved source strategy

1. **Seed candidates from open data.** Import a geographically bounded release of Overture Places or Foursquare Open Source Places. Record the release identifier, upstream ID, source attribution and license. Do not import the planet or query a public community endpoint for normal application traffic.
2. **Resolve identity and location.** Deduplicate by external IDs, normalized names, category, entrance distance, address and official website. Preserve all upstream identities instead of overwriting one provider with another.
3. **Enrich from primary evidence.** Use the official venue/operator, heritage authority, local tourism authority and stable scholarly sources for hours, admission, entrances, access rules and historical claims. A URL alone is not evidence: capture the specific claim, publisher, revision/access date and reviewer.
4. **Evaluate local map providers.** Benchmark VietMap, Goong and Map4D for Vietnam address, entrance and route coverage. No response becomes permanent catalog data until storage, redistribution, attribution and refresh rights are documented.
5. **Use Google Places only within policy.** A Google place ID may be retained and refreshed. Other Places content is fetched and displayed only under current caching, attribution and map-display terms; it must not silently seed or enrich Gonarra's permanent database.
6. **Measure routes at runtime.** Google Routes supplies required `WALK`/`DRIVE` measurements. The scheduler consumes provider output; neither the LLM nor a straight-line calculation may masquerade as a route.
7. **Review and publish.** Only a reviewed, sourced, rights-cleared record that passes deterministic publication gates may enter Explore, planning candidates or Local Guide retrieval.

Provider approval is a controlled record, not a comment in code. For every provider keep owner, purpose, permitted fields, retention/cache limits, attribution text, rate/quota, region, environment, contract/terms version, approval date and next review date. A provider adapter must default to deny persistence for fields without an explicit rule.

## Catalog ledger

| Record | Required evidence |
|---|---|
| Provider and import run | Provider key, terms/license version, approved use, release/request identifier, checksum, started/completed time, importer version, counts and rejection report |
| External place identity | Stable Gonarra place ID, provider, upstream ID, upstream release, match method, match confidence, reviewer and active/retired state |
| City/place | City membership, category/tags, verified public entrance, canonical address, bounded visit-duration estimate, publication state and content revision |
| Localization and alias | Reviewed vi/en names and original descriptions, original spelling, searchable normalized aliases, source language, translation origin, reviewer and date |
| Source and field evidence | Publisher, specific URL/document/revision, retrieved and verified dates, supported field/claim, confidence, validity window, conflict status and reviewer |
| Media | Versioned object key, creator, source, proof of licence/permission, allowed uses, expiry, attribution, derivative status and bilingual alt text |
| Guide evidence | Approved original chunks linked to place, source and source revision, language, corpus revision and embedding configuration. Operational fields remain structured facts. |

Every externally sourced value must be traceable at field or claim level. Do not attach one generic source to a whole POI and imply that it supports every field.

## Ingestion and publication workflow

```text
DISCOVERED -> IMPORTED -> NORMALIZED -> MATCH_REVIEW -> CONTENT_REVIEW
           -> READY_TO_PUBLISH -> PUBLISHED -> SUSPENDED/RETIRED
```

1. Create an immutable import run with provider terms/release and checksum.
2. Validate schema, coordinates, city boundary, required attribution and allowed fields before staging rows.
3. Normalize Unicode, names, aliases, category taxonomy, address units and coordinates without discarding the raw upstream value.
4. Resolve duplicates. Ambiguous matches go to review; automated matching cannot merge two published places.
5. Attach source-specific field evidence and surface conflicts. Prefer current primary evidence for operational facts, but retain the disagreement and resolution.
6. Draft original Vietnamese and English content. AI translation or summarization is labelled `AI_DRAFT`; a bilingual reviewer approves the displayed revision.
7. Validate media rights independently from factual credibility.
8. Run publication gates and publish atomically. Publication records the exact fact, localization, source and media revisions.
9. Refresh by provider/source schedule. A refresh creates a new revision; it never mutates evidence used by an accepted trip without trace.
10. Suspend a place when closed, duplicate, legally disputed, materially stale or unsafe. Existing trips keep a historical snapshot and show the current warning.

Importers must be deterministic and idempotent for the same provider release and configuration. Failed imports leave the last published catalog available.

## Publication and freshness gates

A planning-ready place requires:

- stable Gonarra identity and at least one retained upstream/official identity;
- one supported launch city and a verified public entrance point;
- reviewed Vietnamese and English names, aliases and original descriptions;
- category, planning tags and bounded suggested visit duration;
- source-backed operational state with hours explicitly `KNOWN`, `UNKNOWN` or `NOT_APPLICABLE`;
- price/payment/access fields explicitly known, unknown or not applicable—never inferred;
- field-level provenance and freshness status;
- rights-cleared media or an intentional no-media state;
- no unresolved duplicate, closure, coordinate, license or high-severity conflict;
- successful deterministic publication validation.

Freshness policy is field-specific. Business status and special hours expire faster than historical facts. Store `retrieved_at`, `verified_at`, `valid_until` and `freshness_status`; do not invent one universal TTL. Expired required operational facts create a visible warning or block the affected capability according to policy.

Development proceeds with one production vertical slice in Hội An. Before the common five-city release, each city must have at least **30** published planning-ready POIs and a target of **50 or more** for useful three-day alternatives, distributed across required categories, neighborhoods, price bands and day/time windows. Counts alone do not pass the gate; one-, two- and three-day golden cases must remain feasible after closed/stale candidates are removed.

## AI data boundary

Gemini receives a bounded DTO containing published Gonarra place IDs and approved attributes. It may normalize user intent, choose/order eligible IDs, propose bounded visit durations and write a rationale supported by supplied facts. It may not introduce a place, fact, coordinate, address, hour, price, rating, route or provider status.

Reject and record—without publishing—unknown IDs, unsupported claims and values outside the supplied schema. Deterministic code performs identity checks, scheduling, opening-window checks, route enrichment, Plan Health and Save eligibility. Local Guide answers cite approved evidence or return `insufficient_evidence`; it has no unrestricted web or provider tool.

## Private planning records

Trips own days, stable stop IDs and directed route legs. Store local travel dates/times in `Asia/Ho_Chi_Minh`, duration units explicitly and prices with currency plus evidence state. Distinguish estimated visit duration from provider route distance/time. Private saved places, preferences, sessions/messages and idempotency records have an owner.

A preview identity groups immutable revisions bound to owner, trip base revision, expiry, locks, catalog snapshot and provider measurements. Plan Health records status, per-day slack, walking/travel load, source uncertainty and conflicts. Changed edges invalidate routes and downstream schedules. A transaction promotes exactly one reviewed revision on explicit Save. Restrict nested objects to their owning trip and cascade private data on deletion.

## Data quality acceptance

- Re-importing the same release produces no duplicate canonical place or new publication revision.
- A conflicting or ambiguous external identity cannot auto-merge a published place.
- A provider field without an approved persistence rule cannot leave staging.
- A Google Places payload cannot be copied into canonical fact/media tables; only explicitly permitted identifiers/metadata may persist.
- Removing stale, closed or unpublished candidates cannot cause the planner to invent replacements.
- Every displayed operational claim resolves to evidence and freshness; every media asset resolves to rights and attribution.
- Provider failure or a rejected import leaves the last published catalog and accepted trips intact.

## HA-02 • two days in Hội An

The Vietnamese fixture references published catalog and fact revisions from a named import/review manifest. Lock one day-two stop and regenerate only day two. Preserve day one and the locked stop's identity, day, order among locks and duration. Store permitted Google Routes provenance for affected edges. Timeline and map read that same preview revision. If a catalog refresh, Gemini call or route request fails, saved rows and pending edits survive. Only explicit Save advances the accepted trip revision.
