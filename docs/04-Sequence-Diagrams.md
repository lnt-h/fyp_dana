# DaNavi — Runtime Sequences

Version 1.3 | 2026-10-19 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Source ownership

The editable .drawio files below own the sequences; SVG previews support review and report embedding. This file documents contracts and exceptions without a second Mermaid version of each diagram. [Use Cases](03-Use-Cases.md) own user-level alternatives; [Blueprint](12-Blueprint.md) owns state/transaction rules.

| Scenario | Source | Preview | Trace |
|---|---|---|---|
| Guest gate/build/accept | [drawio](diagrams/sequence-planning.drawio) | [SVG](diagrams/previews/sequence-planning.svg) | UC-05/06; FR-PREF-01, FR-TRP-02/04; TC-06–10/26/43 |
| Edit/refresh | [drawio](diagrams/sequence-edit.drawio) | [SVG](diagrams/previews/sequence-edit.svg) | UC-07; FR-TRP-03/04; TC-11/12 |
| Start/cache/handoff/arrival/audio | [drawio](diagrams/sequence-arrival.drawio) | [SVG](diagrams/previews/sequence-arrival.svg) | UC-08–10/17/18; FR-TRV-01–04, FR-OFF-01; TC-13–18/30/39/40/44 |
| Contextual Ask | [drawio](diagrams/sequence-rag.drawio) | [SVG](diagrams/previews/sequence-rag.svg) | UC-11; FR-AI-01; TC-19–22/29 |

## Build and acceptance

A guest can enter one-day/car/start-point preferences locally. Generate opens the login gate, preserves the form and returns without sending a model request; the authenticated traveler must tap Generate again. The API then authenticates owner/revision/key, supplies published candidates and receives structured model IDs/order/durations. It validates schema/IDs, obtains Routes durations and checks known constraints outside a trip transaction. A short transaction stores a revision-bound preview. **Save & customize** rechecks expiry, publication and facts, then persists plan/revision atomically before editing. Provider failure cannot replace the previous accepted plan; known infeasibility is rejected, unknown feasibility is provisional.

## Edit and route refresh

A short transaction checks owner, parent membership, revision and fixed current/visited prefix, applies edits and marks affected estimates stale/null. Routes executes outside the transaction. Apply only to the same itinerary revision and do not overwrite a newer refresh result. The daily start-to-first-stop leg is invalidated when its first stop or start preferences change.

## Arrival and playback

At Start, the device stores active-trip state and a revision manifest, then prefetches stop text/transcripts and rights-approved audio with explicit partial progress; it does not cache maps or provider routing. Directions hand off the reviewed entrance through an allowlisted HTTPS Google/Apple Maps URL. When DaNavi returns to foreground it refreshes current state and requests a fresh fix; no background watcher is implied. The primary **I've arrived** action, or an optional qualifying foreground dwell, persists a stable event key before sending. Server checks current-state/ownership/evidence and stores one event per stop. Arrival does not complete the stop. GPS denial leaves manual arrival available; simulation needs server demo mode. If offline, UI shows pending and may play an eligible cached asset under the local playback guard; it must not claim server synchronization. Process relaunch restores the same key until acknowledgement. Exact replay does not cause a new auto-play and requires reconciliation if later progression occurred. Expired media URLs are refreshed through guide metadata.

## Ask with evidence

An authenticated single-turn place/trip context controls retrieval. Structured operational facts are separate from narrative English passages. The query uses the pinned embedding space and current source revisions. Weak/conflicting evidence yields refusal; provider failure yields a typed error. Model reference IDs/format and operational values are validated server-side; factual entailment is assessed by the evaluation protocol, not guaranteed by an ID check. The API stores no conversation history; optional recent history is device-only and clearable.

## Notation and review

Lifelines, synchronous calls, dashed returns and execution bars describe the depicted scenarios. Transaction boundaries and exception semantics are specified above and in Blueprint. No background location service, offline map/routing engine, async queue or independent microservice is implied. Account deletion uses the Identity transaction/cascade described in Blueprint/API/Security and is verified by TC-38; it does not need a separate sequence diagram to be unambiguous. P1 camera/STT/Google sequences are deferred until activated.
