# Use cases

The traveler is the primary actor. Curators import and publish traceable catalog revisions. Clerk authenticates the owner, the catalog supplies reviewed content, Gemini proposes choices among supplied IDs, and Google Routes provides travel measurements. Private actions require a valid session. The app preserves draft input across an authentication interruption.

| ID / requirements | Trigger and precondition | Main success flow | Alternative / postcondition |
|---|---|---|---|
| UC-00 Curate · FR-00 | Authorized curator selects an approved provider release/source. Provider persistence rules exist. | Import to staging → validate → resolve identity/conflicts → add field evidence and bilingual review → publish an immutable manifest. | Failed/replayed import does not alter current publication. Disallowed fields, ambiguous identities, unsupported claims or missing rights cannot publish. |
| UC-01 Discover · FR-01 | Traveler selects a launch city and locale. Published catalog exists. | Search by name or alias → open details → inspect evidence/freshness/attribution → add a place to draft. | No results offers a new search. An unpublished ID cannot be added. Runtime enrichment failure leaves canonical details usable. |
| UC-02 Generate · FR-02/03 | Owner submits preferences for a supported trip. | Clarify material gaps → select published candidates → validate IDs → fetch route legs → schedule → display preview and health. | Unsupported mode/day count is rejected before provider calls. Missing required route blocks acceptance. |
| UC-03 Edit and Save · FR-03/04/05 | Owner opens an editable revision. | Select day/segment → lock or manually edit stops → regenerate → inspect diff, health and map → explicitly Save. | Detailed scenario below. |
| UC-04 Use trip · FR-05/06 | Owner opens a saved trip. | Open Today → select stop → inspect execution card → hand reviewed coordinates to external navigation. | A missing entrance note or price is marked unknown. Previously accepted trip remains available on provider failure. |
| UC-05 Ask Local Guide · FR-06 | Traveler opens an authenticated place/trip question. | Authorize context → retrieve reviewed evidence → answer in app locale with references. | Insufficient evidence returns a refusal. Cross-owner context is rejected before retrieval. |
| UC-06 Manage account · FR-07 | Signed-in traveler opens account controls. | Change locale or saved preferences → resume in the chosen locale. For deletion, reauthenticate, confirm and revoke sessions/purge owner records. | Cancellation preserves data. Report pending cleanup accurately and allow safe retry. |

## UC-03 detailed flow • HA-02

**Setup.** Owner has a saved two-day Hội An itinerary in Vietnamese. Capture the accepted trip revision and both days' stops. Open an edit preview against that revision.

1. The traveler locks one day-two stop and requests regeneration of day two.
2. The service checks ownership and expected revision, limits candidates to one published Hội An catalog manifest and preserves day one. The lock retains stop ID, place publication revision, day, duration and order relative to other locks.
3. The service refreshes affected Google Routes legs and recomputes times and Plan Health. Timeline and map display the same new preview revision.
4. The traveler reviews changes and explicitly taps Save. The service rechecks base revision, expiry and health and atomically promotes the chosen snapshot.
5. Reopening the trip shows the accepted revision. A replay with the same key returns the same acceptance result.

**Exceptions.** On Gemini or Routes failure, retain the saved snapshot and recoverable edits. On a stale base revision, show the conflict and let the owner reopen current data before another Save. On BLOCKED health, keep the preview editable and identify the blocking leg/stop. See the [API contract](API.md).
