# Activity Diagrams — Danang TourGuide

UML 2.0 activities for P0 processes. Swimlanes where useful.

---

## A1. Visual Taste → Travel DNA

**Initial:** Traveler opens Visual Taste.

**Actions:** Show intro → Open picker → Select images → Validate count 5–10 → Upload to S3 → Enqueue analysis → **fork** Vision tags ∥ Embeddings → **join** → Aggregate attributes → Persist DNA → Show DNA screen → User edit/confirm.

**Decisions:** Count invalid? Loop picker. Job failed? Retry or abort.

```mermaid
flowchart TD
  start((Start)) --> intro[Show visual taste intro]
  intro --> pick[System photo picker]
  pick --> count{Count 5-10?}
  count -->|No| pick
  count -->|Yes| upload[Upload images to S3]
  upload --> job[Create TasteJob]
  job --> fork{{Fork}}
  fork --> vis[Gemini Vision tags]
  fork --> emb[Multimodal image embedding]
  vis --> join{{Join}}
  emb --> join
  join --> agg[Aggregate Travel DNA]
  agg --> save[Persist preference profile]
  save --> show[Show DNA]
  show --> edit{User edits?}
  edit -->|Yes| patch[Patch attribute weights]
  edit -->|Confirm| done((Confirmed))
  patch --> done
  vis -. timeout/error .-> retry[Bounded retry or failed job]
  emb -. timeout/error .-> retry
  retry --> showError[Preserve photos and show retry]
```

---

## A2. Recommendation → For You

**Actions:** Load DNA → Per-image exact vector search for V1 → Aggregate POI scores → Load context (location, hours, weather cache, visited) → Re-rank → Diversity penalty → Persist RecommendationRun + evidence → Return Top-K → Optional LLM tagline **from evidence only**.

```mermaid
flowchart TD
  s((Start)) --> dna[Load confirmed DNA]
  dna --> loop[For each user image vector]
  loop --> knn[pgvector exact kNN on POI images]
  knn --> agg[Aggregate candidate scores]
  agg --> ctx[Context features]
  ctx --> rank[Weighted re-rank]
  rank --> div[Diversity adjust]
  div --> ev[Store match evidence]
  ev --> k[Top-K POIs]
  k --> e((End For You))
```

---

## A3. AI Trip Builder

**Actions:** Load trip constraints → Candidate POIs (saved ∪ For You) → Filter closed/infeasible → Pack days by pace/budget/distance → Assign times vs opening hours → Call Routes for legs → Persist stops → If conflict, flag stops.

**Decision:** User accepts generated plan or regenerates.

---

## A4. Travel Mode arrival + audio + Ask AI

**Actions:** Start trip → Watch location → Distance check → Arrival event → Show card → **decision** Listen / Ask AI / Mark visited.

**Fork optional:** TTS synth if audio not cached.

```mermaid
flowchart TD
  s((Start trip)) --> watch[Location updates]
  watch --> geo{Within geofence?}
  geo -->|No| watch
  geo -->|Yes, accuracy acceptable| arr[Deduplicated GPS arrival event]
  watch -. Permission denied or inaccurate fix .-> manual[Manual I'm here]
  manual --> arrManual[Manual arrival event]
  arrManual --> card
  arr --> card[Arrival card]
  card --> a{Action}
  a -->|Audio| tts[Play cached or synth TTS]
  a -->|Ask AI| rag[RAG + Gemini]
  a -->|Visited| done[Mark completed]
  tts --> watch
  rag --> watch
  done --> next{More stops?}
  next -->|Yes| watch
  next -->|No| end((Trip complete))
```

---

## A5. Weather adaptation (P1)

Forecast fetch → Compare outdoor stops → If heavy rain → Propose alternative indoor/rain-suitable POI → User Accept or Keep.

## Exception and completion rules

- The app must keep a failed taste job and uploaded photo selection visible for a bounded retry; no silent infinite loop.
- Route API failure leaves an explicit stale/estimated itinerary state. A user edit invalidates travel times until recalculation succeeds.
- Arrival is idempotent per stop. Manual or simulated arrivals carry the method into the event and UI; GPS is not polled after Travel Mode ends.
