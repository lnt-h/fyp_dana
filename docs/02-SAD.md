# Software Architecture Description — Danang TourGuide

| Attribute | Value |
|-----------|-------|
| Document ID | SAD-DTG-001 |
| Version | 0.1 |
| Date | 2026-09-29 |
| Standard | IEEE 1016-2009 (views + rationale) |
| Inputs | Product spec, [01-PRD.md](./01-PRD.md) |

---

## 1. Technical constraints (summary)

- **Mobile:** React Native, Expo, TypeScript, Expo Router, Reanimated.
- **API:** NestJS TypeScript **modular monolith**.
- **Data:** PostgreSQL + PostGIS + pgvector; Redis cache; S3 media.
- **AI:** Gemini Vision/LLM, pinned multimodal embedding model (`gemini-embedding-2`, 768-d assumption), RAG and TTS — **server-side**; provider spike required before ingest.
- **External:** Google Maps/Routes, Weather, Push (P1).
- **Cloud:** AWS ECS/Fargate, RDS, S3, CloudFront, Secrets Manager, CloudWatch, ECR; Docker + GitHub Actions.
- **Team:** one developer → avoid premature microservices.
- **Quality:** facts from DB/RAG; recommend without “prompt Gemini for 10 places”.

---

## 2. Architectural drivers

### 2.1 Concerns

| ID | Stakeholder | Concern | Priority |
|----|-------------|---------|----------|
| C-01 | Traveler | Fast, understandable personalization | High |
| C-02 | Traveler | Trusted hours/prices/history | High |
| C-03 | Developer | Clear module boundaries, one deployable | High |
| C-04 | Examiner | Explainable rec + RAG, not a chatbot shell | High |
| C-05 | Ops | Secrets, logs, deployability | High |
| C-06 | Legal | User images and POI licenses | High |

### 2.2 Quality attribute scenarios

| QA | Scenario |
|----|----------|
| Performance | Under demo load, For You (cached DNA) p95 < 2s excluding first-time vision |
| Reliability | If Gemini times out, taste analysis shows retry; itinerary builder falls back to heuristic packing of saved POIs |
| Security | User A cannot read User B trips/media; API JWT; uploads via signed URLs |
| Maintainability | New Nest module does not require splitting the repo |
| Accuracy | Rec engine never inserts POI IDs not in `places` table |
| Privacy | Account deletion removes S3 objects and preference rows |
| Location | Foreground arrival only in V1; permission denial or inaccurate fix exposes manual arrival |

---

## 3. Context view

```text
[Traveler device: Expo app]
        | HTTPS REST + JWT
        v
[NestJS API — modular monolith]
        |          |           |
        v          v           v
   [RDS PG]    [Redis]      [S3]
   PostGIS
   pgvector
        |
        +-- Gemini (Vision, LLM, Embeddings)
        +-- TTS
        +-- Google Routes
        +-- Weather API
```

**Trust boundary:** public internet → API (auth) → AWS VPC. AI providers are third-party; **do not send unrelated PII**; send images/text needed for the feature.

---

## 4. Logical view — module map

Suggested NestJS modules (from spec §33):

| Module | Responsibility |
|--------|----------------|
| Auth | JWT, Google OAuth, guest session |
| User | Profile, language, settings |
| Media | Signed upload, image variants, ownership |
| Preference | Taste jobs, Travel DNA, edits |
| Place | POI CRUD/read, taxonomy, ops fields |
| Search | Text search, category, near-me (PostGIS) |
| Recommendation | Retrieval, similarity, aggregation, re-rank |
| Saved | Saves, collections |
| Trip | Trip aggregate |
| Itinerary | Days/stops, builder, constraints |
| Routing | Distance/duration via Routes API + cache |
| Location | Geofence config, arrival events |
| Context | Assemble user+POI+trip+time for AI |
| Guide | Narratives, TTS jobs |
| RAG | Chunk search, citation |
| AI | Gemini orchestration, timeouts |
| Weather | Forecast fetch + cache |
| Notification | P1 push |

**Internal engines (logical, not separate services):**

- **Travel Engine:** Recommendation + Trip Planner + Route
- **AI Layer:** Vision, LLM, Embeddings, RAG
- **Context Engine:** GPS, time, weather, trip state

---

## 5. Runtime pipelines

### 5.1 Offline ingestion (ops / scripts)

Trusted sources → POI clean/dedupe/validate → images → vision tags + embeddings → preference attributes → PostgreSQL + pgvector.

### 5.2 Taste analysis (online)

Select 5–10 images → upload S3 → Vision tags ∥ embeddings → aggregate DNA → persist profile → optional candidate warmup.

### 5.3 Recommend

Preference + per-image vectors → exact cosine search on the small V1 POI corpus → aggregate scores → context re-rank (distance, hours, weather, visited, diversity) → Top-K → stored evidence. A calibrated match display is derived from features; the LLM may phrase an explanation but cannot add evidence. ANN is conditional on measured growth.

### 5.4 RAG

Question + context IDs → embed question → exact pgvector search on chunks filtered by authorized `place_id` and locale → threshold and source checks → Gemini with server-assigned citations → state insufficient evidence when retrieval is empty or weak. Operational facts use validated place records.

---

## 6. Information view

Canonical stores:

- Relational: users, places, trips, itinerary, saves, feedback, jobs
- Geographic: `geography(Point, 4326)` on places; GIST indexes
- Vectors: image embeddings, place embeddings, chunk embeddings
- Objects: S3 keys on media rows
- Cache: Redis (weather, routes, For You payloads)

Details: [11-Database-SQL.md](./11-Database-SQL.md), [12-Database-Vector.md](./12-Database-Vector.md).

---

## 7. Deployment view (logical)

See [09-Deployment-Diagram.md](./09-Deployment-Diagram.md).

Month 2–6: local Docker Compose (API, Postgres with extensions, Redis, optional LocalStack S3).  
Month 7: ECS Fargate + RDS + S3 + CloudFront + Secrets + CI.

---

## 8. Key decisions (ADR-lite)

| Decision | Choice | Alternatives | Why |
|----------|--------|--------------|-----|
| Architecture | Modular monolith | Microservices | One developer, shared DB transactions |
| Vectors | pgvector in same RDS | Pinecone / Qdrant | Simpler ops, joins with POI metadata |
| Rec vs LLM | Hybrid retrieve-then-explain | Prompt-only rec | Spec §11, §27 |
| SOM / IG crawl | Out of V1 | Paper pipeline | Product decision §8 |
| Guest taste | Allowed | Login-first | Show value before account |
| Explainability | Structured evidence graph | LLM chain-of-thought | Must match features |

---

## 9. Risks

| Risk | Mitigation |
|------|------------|
| Gemini cost/latency | Batch embeddings, cache DNA, async jobs + push/poll |
| Embedding dimension mismatch | Pin model + migration for vector size |
| Image/text model mismatch | Use a model documented for multimodal input, configure output dimension, test both image and text before corpus ingest; never compare vectors from different models/spaces |
| Maps billing | Cache routes; demo polyline subset |
| POI copyright | Curate licensed images; document sources |
| GPS demo indoor | Simulator / “simulate arrival” debug flag for defense only, documented |
| Hallucination | System prompts + retrieval filter + unit tests on “no POI invention” |

---

## 10. Traceability

| Concern | Design element |
|---------|----------------|
| C-01 | Preference + Rec modules, Expo For You |
| C-02 | Place ops fields, RAG, BR in PRD |
| C-03 | Nest modules, single API |
| C-04 | Six Degrees from evidence table |
| C-05 | Docker, Secrets Manager, CloudWatch |
| C-06 | Media ownership, deletion, source refs on POI |

## 11. Data ownership and execution contracts

- NestJS is the only public API. An authenticated owner or short-lived guest token scopes photos, jobs, profile, recommendations and trips. Signed S3 URLs are short lived and tied to a pending media record; completion verifies the object before analysis.
- A bounded worker/queue processes taste and TTS jobs asynchronously; API returns a job ID and the app polls. Redis may back the queue only after persistence/retry behavior is decided; the database holds the durable state machine.
- Arrival is computed from foreground location while Travel Mode is active. It checks the current stop, accuracy and radius, records detection method (`gps`/`manual`/`simulated`), and deduplicates by trip stop.
- For You cache keys include owner/profile version and context inputs. Profile edits, saves/not-interested signals and itinerary changes invalidate relevant entries.
- Backups cover PostgreSQL plus an S3 object manifest. Account deletion uses a retryable cleanup job and a visible completion status; a soft-delete marker alone does not remove personal data.
