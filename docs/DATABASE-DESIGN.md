# Database design

**PostgreSQL 16, PostGIS and pgvector.** Migration `20261102_0001` enables `pgcrypto`, `postgis` and `vector` and creates the unique Clerk-subject-to-account mapping. Later migrations implement the remaining relations below. The [data contract](DATA.md) governs provider use, imports, provenance, publication, bilingual review and rights.

## Relationships and keys

| Relation | Identity and references | Constraints / access path |
|---|---|---|
| accounts, preferences, saved_places | Internal account UUID with unique Clerk subject. Preferences reference the account. Saved places link account and place. | One preferences row per owner, unique (owner_id, place_id). |
| data_providers, provider_policies | Stable provider key and policy revision. Policy declares purpose, allowed fields, persistence/cache/attribution rules, region, approval owner and review dates. | Never allow a provider field to persist without an active matching rule. Policy revisions are immutable. Secrets are references, never database values. |
| import_runs, import_records | Run identifies provider, release/request scope, checksum and importer version. Staging records preserve raw upstream identity, normalized values, validation result and rejection reason. | Unique successful run by provider/release/checksum/importer version. Raw payload retention follows provider policy. Failed runs cannot alter published rows. |
| external_place_identities | Gonarra place + provider + upstream ID/release, match method/confidence and review state. | Unique (provider_id, upstream_id). Ambiguous matches cannot auto-merge a published place. Index place_id and provider/release. |
| cities, places | City 1:N places. Each place has a stable UUID, city FK, publication state, content revision, category, verified entrance point and duration estimate. | Unique (city_id, slug), index (city_id, publication_state), spatial index for entrance queries. |
| place_localizations, place_aliases | Both reference place_id. Localization identity is (place_id, locale). Aliases retain original and normalized spelling. | Review both vi/en rows before publishing. Index normalized alias for lookup and filter by city. |
| sources, source_revisions | Publisher identity plus exact URL/document/release, license, retrieved date and immutable content fingerprint or private evidence pointer. | Never infer that one source supports every place field. Respect robots, copyright and contractual collection rules. |
| place_facts, fact_evidence | Versioned structured facts reference place, field, typed value, knowledge state, confidence, validity window and review state. Evidence joins a fact revision to a specific source revision and supported claim. | Required operational fields use `KNOWN`, `UNKNOWN` or `NOT_APPLICABLE`; null alone is insufficient. Index current approved facts by place/field/freshness. Conflicts stay explicit. |
| media_assets, media_rights, place_media | Versioned object references and derivatives link to creator/source, license/permission proof, allowed use, expiry and attribution. | An approved rights row or intentional no-media state is required for publication. Private permission evidence is access-controlled. |
| knowledge_chunks | Approved original narrative chunks reference place, source/fact revisions, language, corpus revision and embedding configuration. | Operational facts do not originate in chunks. Retire stale/superseded chunks from retrieval without deleting historical evidence. |
| catalog_publications | Immutable manifest of exact place, fact, localization, source, media and taxonomy revisions promoted together. | One current publication per place. Planner/Explore read manifests, not staging. Suspend/retire without destroying trip snapshots. |
| trips, trip_days, trip_stops | Trip references owner and city, has start date, day count and accepted revision. A day belongs to a trip. A stop references day and catalog place and has a stable ID, ordinal and visit duration. | Unique (trip_id, day_index) and (day_id, ordinal). Enforce 1–3 days and same-city membership before commit. Index trips by owner and recent update. |
| provider_runtime_refs, route_legs | Runtime ref records permitted identifiers, request/expiry metadata and attribution without copying restricted provider payloads. Each directed route leg belongs to a day and references permitted route provenance. | Persist only provider-policy allowlisted fields. Store WALK/DRIVE, availability, measured units and freshness where permitted. Missing measurement is null and never model-filled. |
| plan_previews, preview_revisions | Preview belongs to trip/owner and carries base trip revision and expiry. Immutable child revisions contain ordered days, stable stops, locks, affected legs, health, warnings and content versions. | Unique (preview_id, revision). Validate nested IDs against trip and owner. Index expiry for cleanup. |
| ai_sessions, ai_messages | Session references owner and authorized place/trip context. Ordered messages reference session. | Index session and sequence. Apply retention and deletion policy. |
| idempotency_records | Owner + operation + key identify request digest and outcome. | Unique (owner_id, operation, key). Reject key reuse with a different digest. |

## Transaction and lifecycle rules

1. An import transaction writes only staging, evidence and immutable run results. It cannot publish. Replaying the same release is idempotent; a rejected or failed run leaves the current publication manifests unchanged.
2. Publication locks the candidate place, checks provider persistence rules, identity conflicts, bilingual review, field evidence, freshness and media rights, then creates one immutable manifest and advances the current publication pointer atomically.
3. A refresh creates new evidence/fact/publication revisions. Never rewrite the revisions referenced by an accepted trip. Suspension removes a place from new planning while preserving historical trip display.
4. Generation reads published manifests and an owned trip base. Call model and route providers outside DB transactions. On completion, append a preview revision only if its expected parent is still current.
5. Manual edits or scoped regeneration append a snapshot. Locked day/stop invariants are checked before writing. Editing a segment invalidates boundary legs and dependent schedule values.
6. Save checks owner, expiry, Plan Health, current publication eligibility and both expected revisions. In one transaction, conditionally advance the trip revision, replace the accepted days/stops/legs and record the idempotent result. Concurrent stale writers receive a conflict. A provider failure or rollback leaves the accepted snapshot intact.
7. Cascade private child records on owner/trip deletion. Shared catalog/evidence rows survive account removal. Versioned media and publication manifests participate in restore verification. Retention and recovery controls are defined in [security](SECURITY.md).

## Provider-persistence invariant

Provider data crosses a persistence boundary only through a policy-aware adapter:

```text
provider response
  -> classify(provider, field, purpose, terms revision)
  -> ALLOW_CANONICAL | ALLOW_EPHEMERAL | ALLOW_IDENTIFIER_ONLY | DENY
  -> repository dedicated to that class
```

The generic catalog repository must not accept arbitrary provider JSON. Google Places content cannot be copied into canonical facts/media; an expressly permitted place ID and request metadata use the identifier/runtime tables. Open dataset rows retain their source license/release and required notices. Application logs never become a shadow provider cache.

## Migration acceptance

Apply migrations to an empty database and test populated upgrades in staging. Verify provider-policy denial, duplicate import replay, ambiguous identity matches, publication manifest atomicity, stale evidence, media rights, foreign keys, duplicate ordinals, cross-city stops, foreign-owner preview access, concurrent Save and deletion cascades. Rehearse restore with publication/media references. HA-02 exercises catalog and trip revision integrity across a failed and successful edit of the same trip.
