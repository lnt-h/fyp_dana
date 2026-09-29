# Sequence Diagrams — Danang TourGuide

UML 2.0. Lifelines: Traveler, App, API Gateway/Nest, Media, Preference, Rec, Place, Trip, RAG, AI, S3, Gemini, Maps, Weather, TTS, Postgres.

---

## S1. Taste analysis (happy path)

```mermaid
sequenceDiagram
  actor U as Traveler
  participant App
  participant API
  participant Media
  participant S3
  participant Pref as Preference
  participant AI
  participant Gemini
  participant DB as Postgres

  U->>App: Select 5-10 photos
  App->>API: POST /media/uploads (intent)
  API->>Media: Create assets + signed URLs
  Media-->>App: asset IDs + short-lived putUrl
  App->>S3: PUT image bytes to signed URL
  S3-->>App: upload complete
  App->>API: POST /media/{id}/complete for each asset
  API->>Media: HEAD object; mark uploaded
  App->>API: POST /preferences/taste-jobs
  API->>Pref: Enqueue TasteJob
  Pref->>AI: Analyze images
  par Vision
    AI->>Gemini: Vision tags
    Gemini-->>AI: attributes
  and Embed
    AI->>Gemini: Embeddings
    Gemini-->>AI: vectors
  end
  AI->>DB: Store tags + vectors
  Pref->>DB: Upsert preference_profiles
  App->>API: GET /preferences/taste-jobs/{jobId}
  API-->>App: job succeeded + DNA
  App-->>U: Travel DNA screen
```

---

## S2. For You + Why this place

```mermaid
sequenceDiagram
  actor U as Traveler
  participant App
  participant Rec as Recommendation
  participant Vec as pgvector
  participant DB as Postgres

  U->>App: Open For You
  App->>Rec: GET /recommendations/for-you
  Rec->>DB: Load DNA + visited + saves
  Rec->>Vec: kNN per image embedding
  Vec-->>Rec: POI image hits
  Rec->>Rec: Aggregate + re-rank
  Rec->>DB: Save run + evidence
  Rec-->>App: Top-K + match%
  U->>App: Why this place?
  App->>Rec: GET /places/{id}/explanation?runId=...
  Rec->>DB: Load MatchEvidence path
  Rec-->>App: Six Degrees nodes
```

---

## S3. Trip builder

```mermaid
sequenceDiagram
  actor U as Traveler
  participant App
  participant Trip
  participant Rec as Recommendation
  participant Route as Routing
  participant Maps
  participant DB as Postgres

  U->>App: Create trip + Generate
  App->>Trip: POST /trips/{id}/build
  Trip->>Rec: Candidate POIs
  Trip->>DB: Opening hours, durations
  Trip->>Route: Leg durations
  Route->>Maps: Routes API (cached)
  Maps-->>Route: duration/distance
  Trip->>Trip: Pack days + validate hours
  Trip->>DB: Insert days/stops
  Trip-->>App: Structured itinerary
```

---

## S4. Arrival → Audio → Ask AI

```mermaid
sequenceDiagram
  actor U as Traveler
  participant App
  participant Loc as Location
  participant Guide
  participant TTS
  participant Ask as ContextAI
  participant RAG
  participant Gemini

  App->>Loc: POST /trips/{id}/location (foreground, permission granted)
  Loc-->>App: arrival of current stop N, method=gps
  U->>App: Play Main Story
  App->>Guide: GET /places/{id}/guides/main
  Guide->>TTS: Synthesize curated narrative if missing
  TTS-->>Guide: audio URL
  Guide-->>App: play
  U->>App: Ask "Tượng này có ý nghĩa gì?"
  App->>Ask: POST /ai/ask {placeId, tripId, text}
  Ask->>RAG: Retrieve chunks
  RAG-->>Ask: authorized, sourced passages
  alt Evidence sufficient
    Ask->>Gemini: Grounded prompt with chunk IDs
    Gemini-->>Ask: draft answer
    Ask-->>App: answer + server-validated citations
  else No reliable evidence
    Ask-->>App: insufficient evidence, refusedFact=true
  end
```

---

## Message notes

- **Sync:** REST request/response.
- **Async:** TasteJob, TTS (poll `jobId` or push P1).
- **Errors:** 4xx validation; 503 AI timeout with retry-after; never 200 with invented place IDs.
- **Upload:** The app sends bytes directly to S3; the API signs and verifies but does not upload on behalf of the app.
- **Arrival:** Manual “I’m here” uses a separate endpoint when permission is denied; duplicate reports return the same event.
