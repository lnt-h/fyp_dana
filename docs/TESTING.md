# Acceptance and traceability

These are planned checks. Attach build, fixture, environment, observed result and failures to each release test run. Distinguish static checks, mocks, live providers and physical-device evidence.

## HA-02 • two days in Hội An

1. Set locale to Vietnamese, choose Hội An and generate a two-day trip from a named published catalog/import manifest. Save the initial valid proposal and record its trip, place-publication and fact revisions.
2. Lock a stop on day two and request regeneration of day two. Assert day one is unchanged and the lock keeps its stop ID, day, duration and order among locks. Manual changes outside the requested scope survive.
3. Verify only affected route legs need refresh, displayed distance/time comes from Google Routes and the schedule and Plan Health are recomputed. Compare day/stop selection and revision in timeline and map.
4. Inject a failed catalog refresh, Gemini timeout and required Routes failure separately. Verify the last publication, saved snapshot and pending edits remain recoverable. No invented place, fact or route values. A blocked preview cannot be accepted.
5. Retry successfully, inspect both views and explicitly Save. Reopen the accepted revision. Replay Save with the same key and verify a single revision increment. Attempt acceptance against a stale trip base and verify conflict without loss.

| Requirement | Evidence before release |
|---|---|
| FR-00, FR-01 / Data supply, Explore and curation | Pin open dataset release/license; reject disallowed provider persistence; replay imports idempotently; exercise malformed coordinates, city bounds, duplicate/ambiguous identities and source conflicts. Five independent city manifests, both locales, alias/accent search, absent rights/unreviewed translation rejected, stale claim excluded. |
| FR-02, FR-03 / Planning and Plan Health | Golden requests for 1/2/3 days in each city and locale. Include missing input, different parties, impossible windows, closures, unknown hours, unsupported modes, duplicate/cross-city IDs and missed must-sees. Compare constraint results with a deterministic baseline. |
| FR-03, FR-04 / Routes, edits and locks | WALK/DRIVE provenance, start leg, timeout, reorder/add/remove/replace/duration changes, boundary edges of a segment, locked day, retry and late response. Exercise HA-02. |
| FR-05, FR-07 / Plan acceptance | Owner isolation before provider calls, expiry, simultaneous saves, idempotency key mismatch and no automatic acceptance on AI completion or app restart |
| FR-06 / Execution cards and Guide | Check local address/entrance, rights, confidence and date on each supported field. Human claim-to-source review, correct refusals, false refusals, cross-place and injection cases. |
| Mobile and cloud | Contract drift, accessible bilingual labels, device iOS/Android map/SSE/auth/deep links, DB migration, startup, backup/restore, rollback and secret/log inspection |
| User evaluation | Freeze evaluation set and thresholds before tuning. Record actual consented usability tasks, completion, time, edit effort, trust and limitations under the [research protocol](RESEARCH.md). |

Documentation gate: check local links, retired filenames and stale active requirements, trace BR → FR → UC → US and inspect HA-02 across requirements, API, database and testing. This gate establishes specification consistency.

## Provider and AI data tests

- Contract-test each provider adapter against recorded, redacted fixtures and a small opt-in live suite. Record provider terms/release and distinguish mock from live evidence.
- Verify the persistence classifier returns only `ALLOW_CANONICAL`, `ALLOW_EPHEMERAL`, `ALLOW_IDENTIFIER_ONLY` or `DENY`; deny is the default for unknown provider/field/purpose combinations.
- Assert Google Places runtime fields never appear in canonical fact/media tables or logs. Verify required attribution and expiry behavior in the rendered response.
- Re-import one Overture/FSQ release twice and assert stable external identities, no duplicate place and no unreviewed publication. Import the next release and inspect additions, closures, moved identities and conflicts before publish.
- Run a 100-POI and 100-route Vietnam benchmark across Google Routes and approved local-provider candidates before selecting a local provider. Measure match/entrance accuracy, route coverage, mode, latency, error rate, terms and projected cost; do not select on latency alone.
- Give Gemini adversarial names, coordinates, hours, prices, ratings and unknown place IDs. Assert schema/domain validation rejects every unsupported value and accepted output contains only supplied published IDs.
- Remove or expire candidates used by a golden plan. The planner must return a smaller feasible proposal or a typed insufficiency/block, never fabricate replacements.
