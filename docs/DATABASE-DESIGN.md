# Database design

**PostgreSQL 16, PostGIS and pgvector.** Migration `20261102_0001` enables `pgcrypto`, `postgis` and `vector` and creates the unique Clerk-subject-to-account mapping. Later migrations implement the remaining relations below. The [data contract](DATA.md) governs publication, bilingual review and rights.

## Relationships and keys

| Relation | Identity and references | Constraints / access path |
|---|---|---|
| accounts, preferences, saved_places | Internal account UUID with unique Clerk subject. Preferences reference the account. Saved places link account and place. | One preferences row per owner, unique (owner_id, place_id). |
| cities, places | City 1:N places. Each place has a stable UUID, city FK, publication state, content revision, category, verified entrance point and duration estimate. | Unique (city_id, slug), index (city_id, publication_state), spatial index for entrance queries. |
| place_localizations, place_aliases | Both reference place_id. Localization identity is (place_id, locale). Aliases retain original and normalized spelling. | Review both vi/en rows before publishing. Index normalized alias for lookup and filter by city. |
| sources, place_facts, place_media, knowledge_chunks | Versioned source records support facts and narrative chunks. Media references place, object key and rights record. Embeddings identify chunk revision and model configuration. | Index by place and publication/review state. Preserve evidence revisions used by a saved itinerary. Retire stale chunks from retrieval. |
| trips, trip_days, trip_stops | Trip references owner and city, has start date, day count and accepted revision. A day belongs to a trip. A stop references day and catalog place and has a stable ID, ordinal and visit duration. | Unique (trip_id, day_index) and (day_id, ordinal). Enforce 1–3 days and same-city membership before commit. Index trips by owner and recent update. |
| route_legs | Each directed leg belongs to a day. Its origin is the day start or preceding stop. Its destination is a stop on the same day. | Store WALK/DRIVE, availability, provider, measured distance/time units and freshness where retention permits. Missing measurement is null. |
| plan_previews, preview_revisions | Preview belongs to trip/owner and carries base trip revision and expiry. Immutable child revisions contain ordered days, stable stops, locks, affected legs, health, warnings and content versions. | Unique (preview_id, revision). Validate nested IDs against trip and owner. Index expiry for cleanup. |
| ai_sessions, ai_messages | Session references owner and authorized place/trip context. Ordered messages reference session. | Index session and sequence. Apply retention and deletion policy. |
| idempotency_records | Owner + operation + key identify request digest and outcome. | Unique (owner_id, operation, key). Reject key reuse with a different digest. |

## Transaction and lifecycle rules

1. Generation reads reviewed catalog revisions and an owned trip base. Call model and route providers outside DB transactions. On completion, append a preview revision only if its expected parent is still current.
2. Manual edits or scoped regeneration append a snapshot. Locked day/stop invariants are checked before writing. Editing a segment invalidates boundary legs and dependent schedule values.
3. Save checks owner, expiry, Plan Health, publication and both expected revisions. In one transaction, conditionally advance the trip revision, replace the accepted days/stops/legs and record the idempotent result. Concurrent stale writers receive a conflict. A provider failure or rollback leaves the accepted snapshot intact.
4. Cascade private child records on owner/trip deletion. Shared catalog rows survive account removal. Versioned media manifests participate in restore verification. Retention and recovery controls are defined in [security](SECURITY.md).

## Migration acceptance

Apply migrations to an empty database and test populated upgrades in staging. Verify foreign keys, duplicate ordinals, cross-city stops, foreign-owner preview access, concurrent Save and deletion cascades. Rehearse restore with media references. HA-02 exercises revision integrity across a failed and successful edit of the same trip.
