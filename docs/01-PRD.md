# Product Requirements Document — Danang TourGuide

| Attribute | Value |
|-----------|-------|
| Document ID | PRD-DTG-001 |
| Version | 0.1 |
| Date | 2026-09-29 |
| Standard | IEEE 29148-2018 (adapted) |
| Source | `Danang_TourGuide_Product_Spec.md` |
| Status | Draft |

---

## 0. Product pillars (validation)

| Pillar | Statement | Verified in spec |
|--------|-----------|------------------|
| Visual personalization | Taste is inferred from 5–10 user-selected images, not from a blank questionnaire | §6–7 |
| Curated local data | Recommendations come from a Da Nang POI corpus, not invented places | §9, §27 |
| Explainability | Why-this-place is evidence-based (Six Degrees metaphor) | §12 |
| Structured planning | Itineraries are typed entities (Trip/Day/Stop), not LLM prose | §18–19 |
| On-trip companion | GPS, audio, contextual RAG after planning | §22–25 |
| User control | Preferences editable; itinerary changes proposed, not silent | §7, §28, §42 |

Generic ChatGPT itineraries are **out of scope as the product**. Differentiation is persistent taste + curated POIs + trip context.

---

## 1. Executive summary & strategy

### 1.1 Product vision

Danang TourGuide is a personalized AI travel companion: the traveler shows photos they like, the system infers a Travel DNA, recommends curated Da Nang places that match that taste, builds a realistic itinerary, and stays with the traveler via map, GPS, audio, and context-aware answers.

**Positioning (EN):** Give us a few photos. We'll show you the Da Nang that feels like you.  
**Positioning (VI):** Chọn vài bức ảnh bạn thích, Danang TourGuide sẽ hiểu gu du lịch của bạn, tìm những nơi phù hợp ở Đà Nẵng, lên lịch trình và đồng hành trong suốt chuyến đi.

### 1.2 Business / academic objectives

Graduation project: Software Engineering + AI. One developer. This draft follows the supplied eight-month product spec; A-02 records the unresolved 3–4 month alternative. The demo must show a **complete vertical slice** in-app without Postman or manual database edits.

### 1.3 OKRs (V1 / defense)

| Objective | Key result | Measure |
|-----------|------------|---------|
| O1 Understand me | Photos → Travel DNA E2E | 5–10 images produce editable profile in-app |
| O2 Recommend me | For You + Six Degrees | Top-K POIs with match % and evidence path |
| O3 Plan for me | Structured 3-day itinerary | Trip with days/stops, editable, mapped |
| O4 Travel with me | GPS → arrival → audio → Ask AI | Simulated or real geofence in demo |
| O5 Engineering quality | Modular API, tests, deploy | NestJS modules, tests, Docker/AWS as per Month 7 |

Demo target load is **showcase**, not 10k concurrent users. NFRs below are split into **Thesis/Demo** vs **Production-aspirational**.

---

## 2. Stakeholders, personas, journeys

### 2.1 Stakeholders

| ID | Stakeholder | Need |
|----|-------------|------|
| SH-01 | Traveler (domestic) | Fast, Vietnamese, realistic plans |
| SH-02 | Traveler (international) | English, visual discovery without local knowledge |
| SH-03 | Developer (you) | Modular monolith, 8-month scope |
| SH-04 | Advisor / examiners | Traceable AI, SE NFRs, live demo |
| SH-05 | POI data curator (you) | License-safe images and facts |

### 2.2 Personas

| Persona | Goals | Pain | Frequency |
|---------|-------|------|-----------|
| **Lan** — domestic weekender (25–35) | Beaches + cafes that match her Instagram saves | TikTok + Maps + ChatGPT fragmentation | Per trip |
| **Alex** — first-time visitor (28–45) | Nature/photography spots, not tourist traps | Doesn't know Sơn Trà vs Mỹ Khê vibe | One Da Nang trip |
| **Minh** — couple trip planner | 3-day plan, weather-aware | Generic “Day 1: city tour” dumps | Before + during trip |

### 2.3 Core journey (P0)

```text
Welcome → Visual Taste (5–10 photos) → Analysis → Travel DNA (edit/confirm)
  → For You → Why (Six Degrees) → Save → Create trip (3 days)
  → AI Trip Builder → Edit itinerary → Trip map → Start trip
  → Arrival → Audio → Ask AI → Complete stop → Feedback
```

Value **before** heavy account: visual taste can start as guest; persist after sign-in.

---

## 3. Functional requirements

Priority: **P0** Must for graduation demo, **P1** Should, **P2** If time. Out of V1: booking, payment, hotels, social, AR, multi-city, full voice agent.

### 3.1 Requirement catalog

| ID | Type | Description | Priority | Source |
|----|------|-------------|----------|--------|
| FR-AUTH-01 | Functional | Sign up / sign in (email + Google) | P0 | §5.1 |
| FR-AUTH-02 | Functional | Guest flow for photo taste; merge on login | P0 | §5.1 |
| FR-AUTH-03 | Functional | Profile: language, notifications, trip history | P1 | §5.1 |
| FR-PREF-01 | Functional | Select 5–10 images from device | P0 | §6.1 |
| FR-PREF-02 | Functional | Per-image vision tags + embeddings | P0 | §6.2 |
| FR-PREF-03 | Functional | Aggregate Travel DNA; user view/edit/confirm | P0 | §7 |
| FR-POI-01 | Functional | Curated POI CRUD (admin/ingest); public read APIs | P0 | §9–10 |
| FR-REC-01 | Functional | Retrieve + aggregate + context re-rank Top-K | P0 | §11 |
| FR-REC-02 | Functional | For You feed: match %, tags, actions | P0 | §13 |
| FR-REC-03 | Functional | Six Degrees explanation from matched evidence | P0 | §12 |
| FR-EXP-01 | Functional | Search, categories, near me, explore map | P0 | §14 |
| FR-EXP-02 | Functional | Explore by Image (single image similarity) | P1 | §15 |
| FR-PLC-01 | Functional | Place detail: ops facts from DB, match, actions | P0 | §16 |
| FR-SAV-01 | Functional | Save place; add to trip | P0 | §17 |
| FR-SAV-02 | Functional | Named collections | P1 | §17 |
| FR-TRP-01 | Functional | Create trip (dates, days, companions, budget, pace) | P0 | §18 |
| FR-TRP-02 | Functional | AI builder emits structured itinerary | P0 | §18–19 |
| FR-TRP-03 | Functional | Edit: reorder, add/remove, duration, day move | P0 | §20 |
| FR-TRP-04 | Functional | Route display + travel times | P0 | §21 |
| FR-TRP-05 | Functional | Route optimization modes | P1 | §20 |
| FR-TRV-01 | Functional | Travel Mode: next stop, progress, navigate | P0 | §22 |
| FR-TRV-02 | Functional | Foreground GPS arrival with permission handling, manual fallback, and one arrival event per stop | P0 | §23 |
| FR-TRV-03 | Functional | Audio Guide (TTS from trusted narrative) | P0 | §24 |
| FR-AI-01 | Functional | Contextual RAG assistant at POI/trip | P0 | §25–27 |
| FR-WX-01 | Functional | Weather proposes itinerary change; user accepts/keeps | P1 | §28 |
| FR-FB-01 | Functional | Post-visit Loved/Okay/Not for me + reasons | P1 | §29 |
| FR-I18N-01 | Functional | Vietnamese and English UI + AI language | P1 | §3 |
| FR-CAM-01 | Functional | Camera scan/landmark recognition, with confidence and unknown result | P2, scope decision A-16 | §37 |
| NFR-REL-01 | Quality | Timeouts, retries, graceful AI degradation | P0 | §41 |
| NFR-SEC-01 | Quality | AuthZ, validation, secrets, rate limits | P0 | §41 |
| NFR-PER-01 | Quality | Pagination, image variants, indexes (PostGIS + vector) | P0 | §41 |
| NFR-OBS-01 | Quality | Structured logs; CloudWatch in Month 7 | P1 | §41 |
| NFR-TST-01 | Quality | Unit + integration + E2E for demo path | P0 | §41 |

### 3.2 User stories (P0 with AC)

**US-PREF-01** — As a traveler, I want to pick 5–10 photos I like, so that the app infers my taste without a long quiz.

- **Priority:** P0  
- **AC:**
  - Given I am on Visual Taste, when I select fewer than 5 images, then Continue is disabled with copy to add more.
  - Given I select 5–10 images, when I confirm, then upload starts and I see analysis progress.
  - Given analysis succeeds, when I open Travel DNA, then I see aggregated attribute scores I can edit.

**US-REC-01** — As a traveler, I want a For You list of Da Nang places matching my DNA, so that I do not start from a generic ranking.

- **AC:**
  - Given confirmed Travel DNA, when I open For You, then I see ranked POIs with match % and 2–4 tags.
  - Given a POI, when I tap Why, then I see an evidence path derived from matched features (not free-form hallucination).
  - Given I tap Not interested, when I refresh, then that POI is demoted/hidden for this profile.

**US-TRP-01** — As a planner, I want a 3-day structured itinerary, so that I can follow times and places, not a paragraph.

- **AC:**
  - Given trip constraints + saved/recommended POIs, when builder completes, then API returns Trip with days and stops (`place_id`, times, duration, travel_time, status).
  - Given the itinerary, when I reorder a stop, then times/route are recalculated or marked stale with regenerate.
  - Given opening hours conflict, when a stop is invalid, then the builder flags it (does not silently invent hours).
  - Given route provider failure, when the plan is built, then estimated legs are labeled as estimates or the route is marked stale; no invented travel time is presented as live.

**US-TRV-01** — As a traveler on site, I want arrival detection and a trusted audio story, so that the app acts as a companion.

- **AC:**
  - Given Travel Mode, foreground permission and a location fix within the configured radius, when I arrive at the current stop, then I see one arrival card and at most one arrival event for that stop.
  - Given location permission denied or poor accuracy, when I tap “I’m here”, then arrival is recorded as manual and clearly labeled.
  - Given arrival, when I play Main Story, then TTS plays text from curated/RAG narrative, not an invented history.
  - Given current POI, when I Ask AI, then the answer cites retrieved chunks or refuses operational facts not in DB.

**US-AI-01** — As a user, I want AI answers grounded in POI knowledge, so that I can trust the app for a thesis demo.

- **AC:**
  - Given a question about a place, when RAG finds chunks, then the model answers using those chunks.
  - Given no chunks and no DB fact, when the question is factual, then the app says it does not have that fact.

---

## 4. UX & UI requirements

See [13-UI-UX-Design.md](./13-UI-UX-Design.md) for screens.

- **IA tabs:** For You | Explore | Trips | Profile. Chat/Map/Audio/Saved are **contextual**, not top tabs.
- **Identity:** iOS-first editorial travel; large photography; white + cyan; constellation of selected photos around an AI node.
- **Empty:** No DNA → prompt Visual Taste. No saves → CTA from For You. No trip → Create trip.
- **Error:** Network fail → retry. Vision fail → retry + keep photos. LLM fail → show retrieval-only or “try later”; never fake POIs.
- **Offline:** P2; V1 requires connectivity for AI/maps.

---

## 5. Data, AI, and product rules (business rules)

| ID | Rule |
|----|------|
| BR-01 | Do not recommend POIs outside the curated Da Nang corpus. |
| BR-02 | Operational facts (hours, price, coordinates) come from DB/trusted APIs, not LLM. |
| BR-03 | Historical/cultural claims come from RAG documents or are withheld. |
| BR-04 | Recommendation is retrieve → similarity → aggregate → re-rank; LLM only explains. |
| BR-05 | Weather/route changes are **proposals** requiring user accept/keep. |
| BR-06 | AI inference is editable; user-confirmed DNA is source of truth for ranking. |
| BR-07 | Per-image candidates are aggregated (paper idea); SOM and Instagram crawl are out of V1. |
| BR-08 | Match percent is a calibrated presentation score based on defined features; raw cosine similarity is not displayed as probability. |
| BR-09 | Guest photos and profiles expire if not merged; account deletion removes user records and owned objects under a documented retention policy. |

---

## 6. Interface requirements

| Interface | Consumer | Notes |
|-----------|----------|--------|
| REST JSON API | Expo app | NestJS modular monolith |
| Gemini Vision / LLM / Embeddings | Backend only | Keys in Secrets Manager |
| S3 | Media service | Signed upload |
| Google Maps / Routes | App + backend | Keys split client/server as required |
| Weather API | Backend | Cached in Redis |
| Push | P1 | Expo notifications |

---

## 7. Constraints

| Type | Constraint |
|------|------------|
| Technical | React Native + Expo + TS; NestJS; PostgreSQL + PostGIS + pgvector; Redis; AWS |
| Technical | Modular monolith, not microservices |
| Business | 1 developer, 8 months, Da Nang only |
| Legal | Licensed/trusted POI images and texts; user photo consent |
| Academic | Demo must run in-app (Definition of Done §40) |

---

## 8. Release criteria & metrics

### 8.1 Launch gate (graduation demo)

- [ ] Guest → DNA → For You → Why → Save → 3-day trip → map → Travel Mode → arrival (sim or GPS) → audio → Ask AI → feedback
- [ ] No invented POIs in recommendations
- [ ] Auth for saved trips
- [ ] Unit tests for ranking aggregation; integration tests for POI + trip APIs; one E2E happy path
- [ ] Secrets not in repo
- [ ] Location permission denied and provider timeout flows work; simulated arrival is visibly labeled in demo builds
- [ ] No model-generated hours, prices, citations or travel times are shown as verified facts

### 8.2 Analytics events (instrument when productizing)

`taste_started`, `photos_confirmed`, `dna_confirmed`, `for_you_impression`, `why_opened`, `place_saved`, `trip_created`, `itinerary_generated`, `stop_reordered`, `trip_started`, `arrival_detected`, `audio_played`, `ask_ai_sent`, `feedback_submitted`

---

## 9. Traceability (needs → FR)

| Need | FR IDs |
|------|--------|
| Understand visual taste | FR-PREF-01..03 |
| Personalized places | FR-REC-01..03 |
| Plan trip | FR-TRP-01..04 |
| Companion | FR-TRV-01..03, FR-AI-01 |
| Trust | BR-01..07, NFR-SEC-01 |
| Privacy and accurate claims | BR-08..09, NFR-SEC-01, FR-AI-01 |

---

## 10. Out of scope (V1)

Booking, payment, flights, hotel marketplace, social network, AR navigation, full real-time voice agent, multi-city, Instagram crawling, SOM clustering as a product feature.
