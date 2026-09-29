# Software Design Description (Blueprint) — Danang TourGuide

| Attribute | Value |
|-----------|-------|
| System Name | Danang TourGuide |
| SDD Version | 0.1 |
| Document Date | 2026-09-29 |
| Document Owner | Graduation developer (TBD name) |
| Standard | IEEE 1016-2009 |
| Revision | 0.1 — initial from product spec |

---

## 1. Context & subject

### 1.1 Identification

Danang TourGuide is a mobile-first AI travel companion for Da Nang: visual taste → personalized POIs → structured itinerary → GPS/audio/RAG companion.

### 1.2 External boundaries

| Boundary | Description |
|----------|-------------|
| System purpose | Persistent personalization + curated POIs + trip context |
| External systems | Gemini, S3, Google Maps/Routes, Weather, Google OAuth, TTS, Expo push |
| User types | Traveler (guest/authenticated), future admin ingest (scripts/CLI) |
| External interfaces | REST HTTPS, third-party HTTPS, S3 signed PUT |
| Trust boundaries | Device; public API; AWS account; Google/Gemini tenants |
| Deployment | AWS (target); local Docker (dev) |

### 1.3 Assumptions and constraints

See [ASSUMPTIONS.md](./ASSUMPTIONS.md). Technical: Expo + NestJS + PG/PostGIS/pgvector. Business: 8 months, 1 person, Da Nang only.

---

## 2. Stakeholders & concerns

| Stakeholder | Role | Primary interest |
|-------------|------|------------------|
| Traveler | End user | Taste match, usable itinerary, trusted facts |
| Developer | Implementer | Modularity, testability |
| Advisor/examiner | Academic | Completeness of SE + AI slice |
| Cloud provider | Platform | Cost, secrets, logs |
| Data sources | Licensors | Attribution, no unlicensed scrape |

### 2.2 Concerns and acceptance

| Stakeholder | Concern | Priority | Acceptance |
|-------------|---------|----------|------------|
| Traveler | Rec feels personal | High | For You uses DNA + image similarity |
| Traveler | No fake places | High | Rec IDs ⊆ places table |
| Developer | One codebase | High | Single Nest app |
| Examiner | Explainable AI | High | Six Degrees from stored matches |
| Security | Photo isolation | High | Object keys scoped by user_id |

### 2.3 Quality attribute scenarios

| QA | Scenario |
|----|----------|
| Performance | Cached For You p95 < 2s (demo) |
| Availability | Demo: single instance OK; production target 99.9% later |
| Security | TLS 1.2+; JWT; signed uploads; rate limit login and AI |
| Maintainability | Module change localized |
| Testability | Ranking pure functions unit-tested |
| Deployability | Docker image + GitHub Actions (Month 7) |

---

## 3. Design views

### 3.1 Composition (UI + API layers)

- **App:** Expo Router screens grouped: Taste, Discovery, Trip, On-trip, Account.
- **API:** Nest feature modules listed in SAD §4.
- **Workers (same process or Bull/Redis later):** vision job, embedding job, TTS job.

### 3.2 Component & connector

Connectors: HTTP REST (app↔API), SQL (API↔RDS), Redis protocol, HTTPS (Gemini, Maps, Weather), S3 SDK.

### 3.3 Interaction (primary flows)

1. Taste analysis (async job + poll)
2. For You generation
3. Trip build
4. Arrival + guide + RAG

See sequence diagrams.

Contracts: the app PUTs bytes directly to a signed S3 URL and confirms the upload with the API; taste processing is a durable async job polled by the app. The recommendation engine uses exact vector retrieval for the small V1 corpus and stores evidence before any optional explanation wording. Arrival uses foreground GPS with a manual fallback and an idempotent event per stop.

### 3.4 Information

Entities: User, MediaAsset, PreferenceProfile, Place, PlaceImage, PlaceKnowledgeChunk, Save, Collection, Trip, TripDay, TripStop, RecommendationRun, MatchEvidence, Feedback, ArrivalEvent.

### 3.5 Interface

REST resource groups: `/auth`, `/me`, `/media`, `/preferences`, `/places`, `/search`, `/recommendations`, `/saved`, `/trips`, `/guides`, `/ai/ask`, `/weather`.

### 3.6 State dynamics

**TripStop.status:** `upcoming` → `current` → `completed` | `skipped`; manual/simulated arrival is an event method, not a new stop state. Route freshness is independent (`fresh|estimated|stale`).

**TasteJob.status:** `queued` → `processing` → `succeeded` | `failed`

**Trip.status:** `draft` → `planned` → `active` → `completed`

---

## 4. Design elements (responsibilities)

| Element | Responsibility | Not responsible for |
|---------|----------------|---------------------|
| RecommendationService | Retrieve, score, re-rank | Inventing POIs |
| AiFacade | Provider calls, timeouts | Business facts |
| RagService | Chunk retrieval + prompt pack | Ranking For You |
| ItineraryBuilder | Constraint-aware packing | Charging money |
| LocationService | Geofence vs stop coords | Turn-by-turn (Maps app) |

### Resources (V1)

Single Fargate task + RDS small; Redis cache. GPU not required (Gemini hosted).

---

## 5. Design rationale

- **pgvector in RDS:** joins + one backup story for thesis.
- **LLM after retrieval:** examiners can inspect scores and evidence rows.
- **Guest session:** conversion after value, spec §5.1.
- **No Graph DB:** evidence is a small path; SQL JSON/path table is enough.

---

## 6. Traceability

| PRD ID | Design element |
|--------|----------------|
| FR-PREF-* | Media + Preference + AI Vision |
| FR-REC-* | Recommendation + MatchEvidence |
| FR-TRP-* | Trip + Itinerary + Routing |
| FR-TRV-* | Location + Guide + Context |
| FR-AI-01 | RAG + AI + Place knowledge |
| NFR-SEC-01 | Auth + validation + rate limit |

## 7. Decisions and verification

| Decision | Rationale | How to verify |
|----------|-----------|---------------|
| Single NestJS deployment | One developer and shared data transactions | Module dependency review and E2E demo |
| One PostgreSQL with PostGIS/pgvector | One consistency/backup boundary | Migration test and exact retrieval fixtures |
| Pinned multimodal embeddings | Image–image search and text RAG require explicit model lineage | Image/text spike with 768-d assertion |
| Curated facts with source metadata | Prevent unverifiable place/history claims | No-source refusal and provenance tests |
| Foreground arrival with manual fallback | Permission and indoor GPS uncertainty | Permission-denied and duplicate arrival tests |

The source repository's blueprint prompt stops during its first composition view; this artifact completes the missing view/rationale coverage using the PRD and SAD as inputs. The IEEE label indicates adapted organization, not a claim of independently audited compliance.
