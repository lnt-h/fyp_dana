# Product requirements • bilingual city itineraries

**V1 target specification · 2026-11-02**

A traveler chooses one launch city, describes a trip in Vietnamese or English and reviews a proposed daily timeline and map. The traveler controls which revision becomes the saved itinerary. The [repository overview](../README.md) records the implemented mobile baseline.

## Release requirements

All rows are required for V1. BR identifiers refer to the [business requirements](BRD.md).

| ID | Outcome | Acceptance rule |
|---|---|---|
| FR-01 · BR-01 | Explore a city and collect places | Find published places by Vietnamese/English names and aliases. Place details show bilingual descriptions, duration estimate, verified entrance, attribution and freshness. |
| FR-02 · BR-01 | Generate a proposal | Collect city, dates, 1–3 days, daily windows/start points, party, pace, interests, dietary needs, budget band, must-sees and travel modes. Ask for missing required input. Only published same-city POIs may appear. |
| FR-03 · BR-02 | Review timeline, map and Plan Health | Both views use the same revision. Show order, arrival/departure, visit time and Google Routes distance/duration per WALK or DRIVE leg. Explain GOOD, WARNING or BLOCKED with the affected stop/leg. A missing required route or known infeasible schedule blocks Save. |
| FR-04 · BR-02 | Edit or regenerate selected stops | Support reorder/add/remove/replace, duration and mode changes. Regenerate a trip, day or segment. Preserve locked stops and locked days, recompute affected legs/schedule and show a fresh preview. |
| FR-05 · BR-02 | Accept and resume a trip | Only explicit Save promotes a valid preview. Duplicate Save is idempotent, stale revisions conflict, provider failure preserves saved and pending work. Reopen drafts/saved trips, use Today view and external navigation, or delete an owned trip. |
| FR-06 · BR-03 | Get local assistance | Execution cards show reviewed local/translated names, driver address, entrance and dated operational facts where available. Local Guide answers in the selected locale with sources or returns insufficient_evidence. |
| FR-07 · BR-04 | Manage identity and privacy | Clerk sign-in, private saved places/trips, locale/preferences, session controls, logout and confirmed account deletion. Authorize every private object before retrieval and paid provider calls. |

## Release boundaries and quality

Launch on iOS and Android across the five cities in the BRD. Current discovery artwork is a prototype asset. A planning-ready POI needs reviewed facts, rights and both languages. Route measurements come from Google Routes and schedules from deterministic validation. Unknown operational facts remain visible as unknown. Text planning and Guide acceptance precede any voice feasibility work.

Product review uses HA-02: on a two-day Hội An trip in Vietnamese, lock a day-two stop, regenerate that day, compare map and timeline, then Save. Day one and the lock survive. Evaluate the failure and concurrent-save branches in [testing](TESTING.md). Use the [use cases](USE-CASES.md) for system behavior and [user stories](USER-STORIES.md) for delivery acceptance.
