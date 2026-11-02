# Data, publication and curation

## Catalog ledger

| Record | Required evidence |
|---|---|
| City/place | Stable IDs, city membership, category/tags, verified public entrance, address, bounded estimated visit duration, publication state and revision |
| Localization and alias | Reviewed vi/en names and descriptions, original spelling, searchable normalized aliases, source language, translation origin, reviewer and date |
| Source and fact | Publisher, specific URL/document and revision, access date, factual review date, supported claim and status. Prefer dated operator evidence for hours/prices and credible primary or scholarly sources for history. Record unknown or conflicting values explicitly. |
| Media | Versioned object key, creator, proof of licence/permission, allowed uses, expiry, attribution and bilingual alt text. Check reproduction rights separately from factual credibility. Store private permission evidence outside the public catalog. |
| Guide evidence | Approved chunks linked to place, source and source revision, language, corpus revision and embedding configuration. Operational fields come from structured facts. |

Curator imports drafts, deduplicates aliases and entrances, records provenance and rights, obtains human review in both languages and validates before publication. Reject missing mandatory fields, unsupported facts and unlicensed media. When sources change, invalidate affected facts/chunks, review translations and re-embed the approved revision. Exclude stale evidence from affirmative answers. Show missing hours/prices as unknown. Execution cards use reviewed names, entrance, driver address, hours, sourced etiquette and freshness.

Each of the five cities needs at least 12 published planning-ready places (target 15) and golden cases for one to three days. Verify restore against the versioned media manifest. Persist provider-derived content only within approved use and retention terms.

## Private planning records

Trips own days, stable stop IDs and directed route legs. Store local travel dates/times in Asia/Ho_Chi_Minh, duration units explicitly and prices with currency. Distinguish suggested visit time from Google Routes travel time/distance. Private saved places, preferences, sessions/messages and idempotency records have an owner.

A preview identity groups immutable revisions bound to owner, trip base revision, expiry, locks and content revisions. Plan Health records status, per-day slack, walking/travel load, source uncertainty and identified conflicts. Changed edges invalidate their routes and downstream schedule. Treat missing required route values as unknown and blocking. A transaction promotes exactly one reviewed revision on explicit Save. Restrict nested objects to their owning trip and cascade private data on deletion.

## HA-02 • two days in Hội An

Fixture: Vietnamese trip with two days and a saved baseline. Lock one day-two stop and regenerate only day two. Preserve day one and the locked stop's ID, day, order among locks and duration in the new preview. Store Google Routes provenance for affected edges. Timeline and map read that same revision. An interrupted provider call preserves saved rows and pending edits. Only explicit Save advances the accepted trip revision.
