# Danang TourGuide — Runtime Sequences

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Source ownership

The editable .drawio files below own the sequences; SVG previews support review and report embedding. This file documents contracts and exceptions without a second Mermaid version of each diagram. [Use Cases](03-Use-Cases.md) own user-level alternatives; [Blueprint](12-Blueprint.md) owns state/transaction rules.

| Scenario | Source | Preview | Trace |
|---|---|---|---|
| Build/accept | [drawio](diagrams/sequence-planning.drawio) | [SVG](diagrams/previews/sequence-planning.svg) | UC-06; FR-TRP-02/04; TC-07–10/26 |
| Edit/refresh | [drawio](diagrams/sequence-edit.drawio) | [SVG](diagrams/previews/sequence-edit.svg) | UC-07; FR-TRP-03/04; TC-11/12 |
| Arrival/audio | [drawio](diagrams/sequence-arrival.drawio) | [SVG](diagrams/previews/sequence-arrival.svg) | UC-09/10; FR-TRV-02/03; TC-14–18/30 |
| Contextual Ask | [drawio](diagrams/sequence-rag.drawio) | [SVG](diagrams/previews/sequence-rag.svg) | UC-11; FR-AI-01; TC-19–22/29 |

## Build and acceptance

The API authenticates owner/revision/key, supplies published candidates and receives structured model IDs/order/durations. It validates schema/IDs, obtains Routes durations and checks known constraints outside a trip transaction. A short transaction stores a revision-bound preview. Explicit acceptance rechecks expiry, publication and facts, then persists plan/revision atomically. Provider failure cannot replace the previous accepted plan; known infeasibility is rejected, unknown feasibility is provisional.

## Edit and route refresh

A short transaction checks owner, parent membership, revision and fixed current/visited prefix, applies edits and marks affected estimates stale/null. Routes executes outside the transaction. Apply only to the same itinerary revision and do not overwrite a newer refresh result. The daily start-to-first-stop leg is invalidated when its first stop or start preferences change.

## Arrival and playback

The device checks foreground fixes for the current stop and reports a stable event key. Server checks current-state/ownership/evidence and stores one event per stop. Arrival does not complete the stop. GPS denial uses labelled manual arrival; simulation needs server demo mode. If offline, UI shows pending and may play an already available asset under the local playback guard; it must not claim server synchronization. Exact replay does not cause a new auto-play and requires reconciliation if later progression occurred. Expired media URLs are refreshed through guide metadata.

## Ask with evidence

Authorized place/trip context controls retrieval. Structured operational facts are separate from narrative passages. The query uses the pinned embedding space and current source revisions. Weak/conflicting evidence yields refusal; provider failure yields a typed error. Model reference IDs/format and operational values are validated server-side; factual entailment is assessed by the evaluation protocol, not guaranteed by an ID check.

## Notation and review

Lifelines, synchronous calls, dashed returns and execution bars describe the depicted scenarios. Transaction boundaries and exception semantics are specified above and in Blueprint. No background location service, async queue or independent microservice is implied. P1 camera/STT/Google sequences are deferred until activated.
