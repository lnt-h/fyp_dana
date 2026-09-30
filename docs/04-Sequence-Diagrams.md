# Danang TourGuide — Runtime Sequences

Version 1.0 | 2026-09-30. API paths and schemas owned by [API Design](06-API-Design.md). Nest module lifelines are in-process, not microservices.

## Build proposal and accept
```mermaid
sequenceDiagram
  actor U as Traveler
  participant A as App
  participant N as NestJS
  participant M as AI/Routes providers
  participant D as PostgreSQL
  U->>A: Enter constraints and Generate
  A->>N: POST trips/id/build (revision, idempotency key)
  N->>D: Authorise and load curated candidates
  N->>M: Structured candidate-only AI request
  M-->>N: Draft JSON
  N->>N: Validate IDs/schema/known facts
  N->>M: Fetch route legs
  M-->>N: Durations or unavailable
  N->>N: Schedule and flag conflicts
  N->>D: Store proposal with base revision
  N-->>A: Proposal, warnings, route status
  U->>A: Accept
  A->>N: POST trips/id/proposals/pid/accept
  N->>D: Revision check and atomic persist
  N-->>A: Planned itinerary / 409 conflict
```
Provider calls outside transactions. Invalid output is rejected with bounded repair/retry; provider deadlines return unavailable. No automatic replacement of current accepted plan.

## Edit and recalculate
```mermaid
sequenceDiagram
  participant A as App
  participant N as Trips/Routing
  participant D as PostgreSQL
  participant R as Routes
  A->>N: PUT stops/order with full IDs and revision
  N->>D: Check owner, membership, immutable visited stops
  N->>D: Atomic reorder, revision++, clear affected leg values
  N-->>A: Updated stops, routeStatus=stale
  A->>N: POST route/refresh (revision)
  N->>R: Fetch affected legs
  R-->>N: Legs or failure
  N->>D: Apply only if revision still matches
  N-->>A: fresh / unavailable / 409 changed
```

## Foreground arrival and recorded audio
```mermaid
sequenceDiagram
  participant G as Device GPS
  participant A as App
  participant N as NestJS
  participant S as S3/CDN
  G-->>A: Foreground fixes
  A->>A: Current stop, accuracy, radius, dwell
  A->>N: POST stops/id/arrivals (method and evidence)
  N->>N: Owner/state checks; unique event
  N-->>A: Event and guide metadata
  alt Auto-play opted in and not already played
    A->>S: GET reviewed recorded audio
    S-->>A: Audio bytes
    A->>A: Playback
  else No asset or disabled
    A->>A: Show manual Play / unavailable / transcript
  end
```
Permission denial uses method=manual. Simulation requires demo flag. Network failure retains a local pending arrival report with stable replay key; no server event is claimed until acknowledged. Foreground playback may use known POI asset while reporting retries; local once-per-stop guard remains necessary.

## Contextual RAG
```mermaid
sequenceDiagram
  actor U as Traveler
  participant A as App
  participant N as AI module
  participant D as PostgreSQL/pgvector
  participant M as Model provider
  U->>A: Ask question
  A->>N: POST ai/ask with context IDs
  N->>D: Authorise trip; load verified facts
  N->>M: Text query embedding
  M-->>N: Vector in pinned space
  N->>D: Filtered exact retrieval
  D-->>N: Source passages
  alt Sufficient relevant evidence
    N->>M: Grounded prompt with allowed citation IDs
    M-->>N: Draft structured answer
    N->>N: Validate citation IDs/format, enforce fact rules
    N-->>A: grounded answer and source links
  else Insufficient or conflicting evidence
    N-->>A: insufficient_evidence with explanation
  end
```
Known operational facts may be answered from structured records without narrative chunks. Unknown facts cannot be filled by general model knowledge. Claim support requires measured evaluation beyond ID validation.

## P1 camera
App permission/capture → private upload with size/type checks → NestJS calls Gemini Vision with candidate corpus/context → validates returned candidate IDs → matched/ambiguous/unknown → user confirms place. Delete temporary image after processing/expiry. Camera result is identification assistance, not evidence for POI historical facts.
