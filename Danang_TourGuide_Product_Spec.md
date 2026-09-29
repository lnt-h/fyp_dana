# Danang TourGuide — Product Specification & Development Direction

> **Product:** Personalized AI Travel Companion for Da Nang  
> **Project:** Graduation Project — Software Engineering + AI  
> **Team:** 1 developer  
> **Timeline:** 7–8 months  
> **Platform:** Mobile, iOS-first UX, cross-platform implementation

---

## 1. Product Vision

**Danang TourGuide** is not just a travel chatbot. It is an **AI travel companion** that understands a user's travel taste from images, recommends places in Da Nang that fit that taste, builds a realistic itinerary, and continues assisting the user during the trip.

### Core product loop

```text
USER PHOTOS
    ↓
UNDERSTAND
Understand travel taste
    ↓
DISCOVER
Recommend suitable places
    ↓
PLAN
Build realistic itinerary
    ↓
TRAVEL
Map + GPS + Audio + Contextual AI
    ↓
LEARN
Feedback improves personalization
    ↺
```

### One-sentence positioning

> **Give us a few photos. We'll show you the Da Nang that feels like you.**

Vietnamese:

> **Chọn vài bức ảnh bạn thích, Danang TourGuide sẽ hiểu gu du lịch của bạn, tìm những nơi phù hợp ở Đà Nẵng, lên lịch trình và đồng hành trong suốt chuyến đi.**

---

## 2. Why This Product Exists

A traveler can already ask ChatGPT to create a 3-day Da Nang itinerary. The product therefore needs value beyond generic text generation.

Danang TourGuide maintains travel context that a generic chatbot normally does not own as a product state:

- visual preferences,
- saved places,
- visited places,
- current location,
- current trip state,
- opening hours,
- route and distance,
- weather,
- available time,
- budget,
- current POI context.

The product differentiator is therefore:

> **Persistent personalization + curated local data + real trip context.**

---

## 3. Target Users

### Primary users

- Domestic travelers visiting Da Nang.
- International travelers visiting Da Nang.
- Travelers who do not know which attractions fit their personal style.
- Travelers who want one continuous experience instead of manually combining TikTok, Google Maps, travel blogs and ChatGPT.

### V1 languages

- Vietnamese
- English

---

# 4. Main Product Journey

```text
1. UNDERSTAND ME
2. RECOMMEND FOR ME
3. PLAN FOR ME
4. TRAVEL WITH ME
5. LEARN FROM ME
```

---

# 5. Functional Modules

## 5.1 Authentication & Profile

Functions:

- Sign up / Sign in.
- Google authentication.
- User profile.
- Preferred language.
- Saved Travel DNA / preference profile.
- Trip history.
- Saved places / collections.
- Notification settings.

The app should show value before forcing the user through a heavy account setup.

---

# 6. Visual Travel Profile — Core AI Feature

This is the signature AI capability of Danang TourGuide.

## 6.1 User input

The user selects/uploads **5–10 images that represent places or experiences they like**.

The images may be:

- their own previous travel photos,
- images already stored in their gallery,
- screenshots,
- reference travel images.

They do not need to be photos taken by the user.

Suggested UX copy:

> **Chọn 5–10 ảnh thể hiện những nơi bạn yêu thích.**

## 6.2 Image understanding

Each image is analyzed independently.

```text
Photo A
→ beach
→ quiet
→ sunset
→ photography
→ relaxing

Photo B
→ mountain
→ scenic
→ nature
→ adventure
```

The system creates two representations.

### A. Semantic attributes

Examples:

- Nature
- Beach
- Mountain
- Urban
- Architecture
- Quiet
- Vibrant
- Romantic
- Local
- Relaxing
- Photography
- Adventure
- Food
- Cafe
- Shopping
- Culture
- Scenic
- Sunset
- Historic
- Nightlife

### B. Embedding

```text
Image
  ↓
Embedding model
  ↓
[0.18, -0.42, 0.77, ...]
```

Embeddings are used for semantic similarity with destination images and POIs.

---

# 7. Travel DNA / User Preference Profile

Evidence from the selected images is aggregated into a persistent profile.

Example:

```text
Nature          92%
Beach           87%
Scenic Views    84%
Photography     76%
Local Food      68%
Cafe            61%
Culture         43%
Adventure       37%
Nightlife       12%
```

The user can:

- view the profile,
- edit it,
- confirm it.

### Naming

- **UI / Marketing:** Travel DNA
- **Backend / Database:** User Preference Profile

AI inference is not treated as absolute truth; the user remains in control.

---

# 8. Research Idea Adapted into the Product

The uploaded paper **Travel Direction Recommendation Model Based on Photos of User Social Network Profile** uses social-network travel photos, object detection, metadata, similarity, classification and clustering/SOM to recommend travel countries.

A key idea from the paper is that multiple user photos can be processed separately and their recommendation results aggregated, instead of relying on one image only or only one common representation.

## Paper concept

```text
User Photos
    ↓
Historical Photo Dataset
    ↓
Object Detection / Similarity / Clustering
    ↓
Recommended Country
```

## Danang TourGuide adaptation

```text
User Photos
    ↓
Vision + Embeddings
    ↓
Curated Da Nang POI Image Dataset
    ↓
Similarity
    ↓
Aggregate POI Candidates
    ↓
Context Re-ranking
    ↓
Recommended Places
```

### Product decision

Danang TourGuide does **not** need to crawl thousands of Instagram users as a core V1 capability.

Instead:

- users provide/select their own reference images,
- the product maintains a curated Da Nang destination corpus,
- modern embeddings replace much of the need for a large object-detection-heavy research pipeline,
- SOM is not required for V1.

---

# 9. Data Strategy

Two main data groups are required.

## 9.1 Runtime user images

```text
5–10 user-selected images
        ↓
Vision analysis
        ↓
Semantic attributes
        +
Image embeddings
```

## 9.2 Curated destination corpus

Target:

**100–150 POIs in Da Nang**

Each POI should have approximately:

- 5–10 representative images,
- location metadata,
- travel attributes,
- operational information,
- trusted knowledge documents.

Example:

```text
Ghềnh Bàng
├── image_01
├── image_02
├── image_03
├── image_04
├── metadata
├── preference attributes
└── knowledge documents
```

A reasonable V1 corpus could be:

```text
120 POIs × 6 representative images
≈ 720 destination images
```

This is much more realistic for a one-person graduation project than reproducing a research-scale social-network dataset.

---

# 10. POI Data Model

```text
Place
│
├── Identity
│   ├── id
│   ├── name
│   ├── category
│   ├── description
│   ├── latitude
│   ├── longitude
│   └── source references
│
├── Media
│   ├── images
│   └── image embeddings
│
├── Preference Attributes
│   ├── nature
│   ├── beach
│   ├── food
│   ├── culture
│   ├── photography
│   ├── adventure
│   ├── cafe
│   ├── nightlife
│   ├── quiet
│   └── scenic
│
├── Experience
│   ├── crowded / quiet
│   ├── local / tourist
│   ├── family
│   ├── couple
│   ├── solo
│   └── physical_activity_level
│
├── Operational
│   ├── opening_hours
│   ├── average_duration
│   ├── price
│   └── best_visit_time
│
├── Context
│   ├── indoor / outdoor
│   ├── rain_suitable
│   ├── morning
│   ├── sunset
│   └── night
│
└── AI
    ├── semantic tags
    ├── place embedding
    └── RAG knowledge chunks
```

---

# 11. Recommendation Engine

Recommendation must not be only:

```text
User Profile
    ↓
Prompt Gemini
    ↓
“Recommend 10 places”
```

Instead:

```text
User Preference
      ↓
Candidate Retrieval
      ↓
Visual / Semantic Similarity
      ↓
Aggregation Across Images
      ↓
Context Re-ranking
      ↓
Top K POIs
      ↓
LLM Explanation
```

## 11.1 Stage 1 — Visual matching

Each user image produces candidate POIs.

```text
User Image 1 → Top POIs
User Image 2 → Top POIs
User Image 3 → Top POIs
...
              ↓
          Aggregation
```

Example:

```text
Sơn Trà        ████
Ghềnh Bàng     ███
Bãi Bắc        ███
Hải Vân        ██
Mỹ Khê         ██
```

## 11.2 Stage 2 — Context re-ranking

Candidates are re-ranked using:

- Taste Match
- Image Similarity
- Distance
- Opening Hours
- Weather
- Time
- Budget
- Available duration
- Already visited places
- Route compatibility
- Diversity

Conceptual score:

```text
FinalScore =
    TasteMatch
  + ImageSimilarity
  + ContextFit
  + DistanceFit
  + TimeFit
  + Diversity
```

Initial weights can be rule-based. A learning-to-rank model is not required for V1.

---

# 12. Six Degrees — Explainable Recommendation

The product should explain why a POI was recommended.

Example:

```text
YOUR PHOTOS
     ↓
Nature
     ↓
Quiet
     ↓
Scenic
     ↓
Photography
     ↓
Coastal Landscape
     ↓
GHỀNH BÀNG
```

This is the product interpretation of **Six Degrees of Separation**.

It is an explainability metaphor, not a strict requirement that every recommendation contains exactly six nodes.

The graph should be generated from actual matched features/evidence, not invented LLM reasoning.

---

# 13. For You

Primary personalized discovery screen.

Example:

```text
FOR YOU IN DA NANG

Sơn Trà
93% Match
Nature • Scenic • Photography

Ghềnh Bàng
89% Match
Beach • Quiet • Adventure

Bãi Bắc
85% Match
Nature • Beach • Relaxing
```

Actions:

- Save
- Not interested
- Add to trip
- Why this place?
- View details

---

# 14. Explore

**For You** and **Explore** serve different purposes.

```text
For You
= the system proactively recommends places based on the user.

Explore
= the user actively searches and browses.
```

Explore functions:

- Search
- Browse categories
- Near me
- Explore map
- Explore by Image

---

# 15. Explore by Image

The user uploads one reference image.

```text
Reference Image
      ↓
Image Embedding
      ↓
Vector Similarity
      ↓
POI Image Embeddings
      ↓
Similar Places
```

Example:

```text
Ghềnh Bàng      94% vibe match
Bãi Bắc         88%
Hải Vân         82%
```

### Difference from Travel DNA

```text
Travel DNA
5–10 images
→ understand the traveler.

Explore by Image
1 image
→ find places with a similar vibe.
```

Both reuse the same embedding infrastructure.

---

# 16. Place Detail

Each place detail should contain:

- hero images,
- place name,
- category,
- distance,
- rating/source if available,
- match percentage,
- why it fits the user,
- description,
- opening hours,
- estimated duration,
- price,
- best visiting time,
- weather suitability,
- gallery,
- highlights,
- Save,
- Directions,
- Add to Trip,
- Ask AI.

---

# 17. Saved Places & Collections

Users can organize places into collections such as:

- Want to Go
- Beaches
- Food Crawl
- Cafes
- Weekend Trip

Saved places can become input to the Trip Builder.

---

# 18. AI Trip Builder

Inputs:

- travel dates,
- number of days,
- companions,
- budget,
- travel pace,
- Travel DNA,
- selected/saved POIs,
- priority categories.

Planning context:

```text
Travel DNA
+
Saved POIs
+
Opening Hours
+
Distances
+
Weather
+
Budget
+
Available Time
```

The output must be a **structured itinerary**, not just a block of LLM-generated text.

---

# 19. Structured Itinerary

```text
Trip
├── Day 1
│   ├── Stop 1
│   ├── Stop 2
│   └── Stop 3
├── Day 2
└── Day 3
```

Each stop should include:

```text
place_id
arrival_time
departure_time
visit_duration
travel_time_to_next
status
```

Stop status:

```text
upcoming
current
completed
skipped
```

---

# 20. Itinerary Editing

The user can:

- drag & drop stops,
- remove a stop,
- add a stop,
- move a stop to another day,
- change duration,
- optimize the route.

Possible route modes:

- Minimum travel distance
- Balanced
- Prioritize favorite places

---

# 21. Map & Route

The map is part of the trip experience, not just a static POI viewer.

```text
① Hotel
   ↓
② Chùa Linh Ứng
   ↓
③ Sơn Trà
   ↓
④ Mỹ Khê
   ↓
⑤ Chợ Hàn
```

Display:

- ordered markers,
- route,
- current location,
- travel time,
- trip progress,
- next destination.

---

# 22. Travel Mode

When the user starts the trip:

```text
CURRENT TRIP

Next:
Chùa Linh Ứng

2.3 km
~8 min

[Navigate]

Progress:
✓ Hotel
● Chùa Linh Ứng
○ Sơn Trà
○ Mỹ Khê
○ Dinner
```

Travel Mode is the transition from **planner** to **companion**.

---

# 23. GPS Auto Guide

```text
Location Update
      ↓
Geofence / Distance Check
      ↓
Arrival Event
```

Example:

> **Bạn đã đến Chùa Linh Ứng.**

Actions:

- Listen to story
- Ask AI
- Mark as visited

---

# 24. Audio Guide

V1 does not require a full real-time voice agent.

```text
Trusted POI Knowledge
        ↓
Prepared / RAG-assisted Narrative
        ↓
Text-to-Speech
        ↓
Audio Guide
```

Possible modes:

- Quick Story
- Main Story
- Interesting Fact

---

# 25. Context-aware AI

Chat is not the main homepage.

AI is surfaced where context is useful.

Example at a POI:

> “Tượng này có ý nghĩa gì?”

Context:

```text
Current User
+
Current POI
+
Current Trip
+
Travel Profile
+
RAG Knowledge
```

Example during a trip:

> “Gần đây có chỗ ăn nào hợp gu tôi?”

Additional context:

- current location,
- time,
- remaining itinerary.

---

# 26. Embeddings

Embeddings are used in three major areas.

## 26.1 Image → POI similarity

```text
User Image Embedding
        ↕
POI Image Embeddings
```

Used by:

- Explore by Image
- Personalized recommendation

## 26.2 Preference → POI similarity

```text
User Preference Representation
        ↕
POI Semantic Representation
```

Used by the Recommendation Engine.

## 26.3 RAG retrieval

```text
Question Embedding
      ↓
Vector Search
      ↓
Knowledge Chunk Embeddings
```

Used to retrieve trusted knowledge before answering.

---

# 27. RAG

RAG is used for **knowledge reliability**, not as the primary recommendation engine.

Knowledge can include:

- history,
- architecture,
- cultural background,
- local stories,
- visitor information,
- travel tips,
- curated POI documents.

Flow:

```text
User Question
      ↓
Embedding
      ↓
pgvector Search
      ↓
Relevant Knowledge Chunks
      ↓
Gemini
      ↓
Grounded Answer
```

### AI reliability rules

AI may:

- explain,
- summarize,
- personalize,
- communicate naturally.

AI should not invent:

- POIs,
- opening hours,
- prices,
- historical facts,
- operational information.

Facts should come from:

- curated POI database,
- trusted APIs,
- RAG knowledge base.

---

# 28. Weather-aware Adaptation

Example:

```text
Tomorrow 14:00
Bà Nà Hills
       ↓
Weather API
       ↓
Heavy Rain
```

The app proposes an alternative instead of silently rewriting the itinerary.

User actions:

- Accept change
- Keep old plan

---

# 29. Feedback Loop

After visiting a place:

```text
Loved it
Okay
Not for me
```

Optional reasons:

- Too crowded
- Too touristy
- Loved the scenery
- Loved the food
- Too far
- Too expensive

Feedback updates the preference profile.

```text
Visual Preference
      +
Explicit Preference
      +
Actual Trip Feedback
      ↓
Better Personalization
```

---

# 30. Navigation Structure

Recommended main tabs:

```text
For You
Explore
Trips
Profile
```

Do not create separate top-level tabs for:

- Chat
- Map
- Audio
- Saved

These are contextual features.

Examples:

```text
Trip → Map
Place → Ask AI
Travel Mode → Audio
For You → Save
```

---

# 31. Main Screens

## Visual Taste & Personalization

1. Welcome
2. Visual Taste Intro
3. System Photo Picker
4. Selected Photo Constellation
5. AI Analysis
6. Travel DNA
7. Edit Preference

## Discovery

8. For You
9. Six Degrees / Why Recommended
10. Explore
11. Explore by Image
12. Similar Image Results
13. Explore Map
14. Place Detail
15. Saved / Collections

## Trip Planning

16. Create Trip
17. AI Trip Builder
18. Trip Overview
19. Day Itinerary
20. Edit / Reorder
21. Trip Map

## On-trip

22. Today / Start Trip
23. Travel Mode
24. Arrival Card
25. Audio Guide
26. Contextual Ask AI
27. Weather Adaptation

## Account

28. Travel Profile
29. Trip History
30. Feedback
31. Settings

---

# 32. UI Direction

Design direction:

> **iOS-first editorial travel experience**

Characteristics:

- large travel photography,
- clean white surfaces,
- blue/cyan accent,
- translucent/frosted cards,
- large title hierarchy,
- bottom sheets,
- contextual actions,
- haptics,
- subtle animations,
- map overlays.

### Signature visual identity

Selected user photos form a **connected visual constellation** around an AI center node.

```text
Photos
↓
Connected Photo Graph
↓
Travel DNA
↓
Recommendation
```

This visual motif should become part of the product identity.

---

# 33. Tech Stack

## Mobile

```text
React Native
Expo
TypeScript
Expo Router
React Native Reanimated
```

## Backend

```text
NestJS
TypeScript
Modular Monolith
```

Suggested modules:

```text
Auth
User
Media
Preference
Place
Search
Recommendation
Saved
Trip
Itinerary
Routing
Location
Context
Guide
RAG
AI
Weather
Notification
```

## Database

```text
PostgreSQL
PostGIS
pgvector
```

Roles:

```text
PostgreSQL → relational data
PostGIS    → geographic/location queries
pgvector   → embeddings, vector similarity and RAG
```

## Cache

```text
Redis
```

## AI

```text
Gemini Vision
Gemini LLM
Embedding Model
RAG
Text-to-Speech
```

## External APIs

```text
Google Maps / Routes
Weather API
Push Notifications
```

## Storage

```text
AWS S3
```

## Cloud

```text
AWS ECS / Fargate
AWS RDS PostgreSQL
AWS S3
CloudFront
Secrets Manager
CloudWatch
ECR
```

## DevOps

```text
Docker
GitHub Actions
CI/CD
```

---

# 34. High-level Architecture

```text
                    MOBILE APP
             React Native + Expo
                       │
                       ▼
                  NestJS API
                Modular Monolith
                       │
      ┌────────────────┼─────────────────┐
      │                │                 │
      ▼                ▼                 ▼
 Travel Engine      AI Layer       Context Engine
      │                │                 │
 Recommendation     Vision             GPS
 Trip Planner       LLM                Time
 Route              Embeddings         Weather
                    RAG                Trip State
      │                │                 │
      └────────────────┼─────────────────┘
                       ▼
        PostgreSQL + PostGIS + pgvector
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
             Redis     S3    External APIs
```

---

# 35. Offline Data Ingestion Pipeline

```text
Trusted / Licensed Sources
          ↓
      POI Collection
          ↓
        Cleaning
          ↓
      Deduplication
          ↓
       Validation
          ↓
 Representative Images
          ↓
  Vision + Embeddings
          ↓
Preference Attributes
          ↓
PostgreSQL + pgvector
```

This is preferable to making large-scale social-media crawling a major V1 feature.

---

# 36. Runtime AI Pipeline

```text
USER SELECTS 5–10 IMAGES
              ↓
           Upload
              ↓
       ┌──────┴──────┐
       ↓             ↓
Gemini Vision    Embeddings
       ↓             ↓
Semantic Tags   Vector Search
       ↓             ↓
 Travel DNA     POI Candidates
       └──────┬──────┘
              ↓
          Aggregation
              ↓
        Context Re-ranking
       /       |       \
 Weather    Distance    Time
       \       |       /
              ↓
      Personalized POIs
              ↓
         Trip Builder
              ↓
          Travel Mode
              ↓
         RAG + Audio
```

---

# 37. Product Scope

## P0 — Must Have

- Authentication
- Curated POI database
- Upload/select 5–10 images
- Vision analysis
- Image embeddings
- Travel DNA
- Editable preference profile
- Recommendation engine
- For You
- Six Degrees explanation
- Search / Explore
- Place Detail
- Saved Places
- Trip Creation
- AI Trip Builder
- Structured Itinerary
- Trip Map
- Route
- Trip State
- GPS Arrival
- Audio Guide
- Context-aware RAG assistant

## P1 — Should Have

- Explore by Image
- Weather adaptation
- Feedback learning
- Collections
- Notifications
- Vietnamese / English
- Route optimization

## P2 — If Time Allows

- Camera Scan / landmark recognition
- Offline trip
- Offline audio
- Live Activity
- Dynamic Island integration
- More advanced personalization learning

## Not for Graduation V1

- Booking
- Payment
- Flights
- Hotel marketplace
- Social network
- AR navigation
- Full real-time voice agent
- Multi-city expansion

---

# 38. 8-Month Development Roadmap

## Month 1 — Product & Design

Deliverables:

- requirements,
- user journey,
- information architecture,
- Figma,
- design system,
- ERD,
- system architecture,
- API conventions,
- POI taxonomy,
- repository setup,
- initial 20–30 POIs.

**Goal:** Know exactly what is being built before major implementation.

## Month 2 — Core Travel Application

Build:

- React Native foundation,
- NestJS foundation,
- authentication,
- database,
- POI APIs,
- place list,
- place detail,
- search,
- basic map,
- saved places.

Grow dataset to **30–50 POIs**.

**Milestone:** A useful travel application works even without AI.

## Month 3 — Visual Personalization

Build:

- image upload,
- S3 media flow,
- Vision analysis,
- image embeddings,
- preference extraction,
- multi-photo aggregation,
- Travel DNA,
- edit preference.

**Milestone:**

```text
Photos → Travel DNA
```

works end-to-end.

## Month 4 — Recommendation & Discovery

Build:

- POI embeddings,
- pgvector similarity,
- recommendation engine,
- For You,
- explainability / Six Degrees,
- Explore,
- Explore by Image,
- collections.

Grow dataset to **70–100 POIs**.

**Milestone:**

```text
Photos
→ Travel DNA
→ Personalized POIs
→ Explanation
```

works end-to-end.

## Month 5 — Trip Planning

Build:

- Trip entity,
- Trip Day,
- Trip Stop,
- Trip Builder,
- constraints,
- opening-hours checks,
- distance checks,
- itinerary generation,
- editing,
- drag & drop,
- route optimization.

**Milestone:**

```text
Personalized POIs
→ Structured Itinerary
```

works.

## Month 6 — Travel Companion

Build:

- trip map,
- trip progress,
- GPS,
- geofence,
- arrival events,
- Travel Mode,
- Audio Guide,
- TTS,
- RAG,
- contextual AI.

**Milestone:**

```text
Start Trip
→ GPS
→ Arrival
→ Audio
→ Ask AI
```

works.

## Month 7 — Productization

Build/improve:

- AWS deployment,
- Docker,
- CI/CD,
- unit tests,
- integration tests,
- E2E tests,
- logging,
- monitoring,
- Redis caching,
- DB indexes,
- PostGIS indexes,
- validation,
- rate limiting,
- retry / timeout handling,
- Secrets Manager,
- bilingual support,
- notifications,
- weather adaptation.

Grow dataset to **100–150 POIs**.

## Month 8 — Finalization

Focus on:

- bug fixing,
- UI polish,
- animations,
- accessibility,
- performance,
- user testing,
- documentation,
- architecture diagrams,
- final report,
- defense slides,
- demo video,
- demo fallback scenarios.

Do not add large new features.

---

# 39. Major Milestones

```text
M1 — TRAVEL APP
Place + Map + Saved

M2 — UNDERSTAND ME
Images → Travel DNA

M3 — RECOMMEND ME
Travel DNA → For You

M4 — PLAN FOR ME
Recommendations → Itinerary

M5 — TRAVEL WITH ME
Itinerary → GPS → Audio → AI
```

Each milestone should work independently.

---

# 40. Graduation Demo Flow

A brand-new user should be able to complete this without developer intervention:

```text
Launch App
    ↓
Select 5–10 images
    ↓
AI analyzes travel taste
    ↓
Travel DNA appears
    ↓
User edits/confirms preferences
    ↓
For You recommendations
    ↓
Open “Why this place?”
    ↓
Six Degrees explanation
    ↓
Save places
    ↓
Create 3-day trip
    ↓
AI builds structured itinerary
    ↓
User edits itinerary
    ↓
View route on map
    ↓
Start Trip
    ↓
GPS detects arrival
    ↓
Play Audio Guide
    ↓
Ask AI about current place
    ↓
Complete stop
    ↓
Give feedback
```

### Definition of Done

The graduation demo should run inside the app without:

- manually editing the database,
- switching to Postman,
- replacing unfinished functionality with presentation slides,
- requiring hidden developer intervention.

---

# 41. Non-functional Product Requirements

Because this is a **Software Engineering** graduation project, the app should demonstrate more than features.

## Reliability

- error handling,
- retry policies,
- graceful degradation,
- API timeout handling,
- useful empty/error states.

## Security

- authentication,
- authorization,
- server-side validation,
- secret management,
- rate limiting.

## Performance

- caching,
- pagination,
- optimized images,
- database indexing,
- PostGIS indexing,
- vector indexing.

## Maintainability

- modular backend,
- clear boundaries,
- consistent DTOs,
- API conventions,
- documentation.

## Testing

- unit tests,
- integration tests,
- E2E tests.

## Observability

- structured logging,
- metrics / monitoring,
- CloudWatch,
- error tracking.

---

# 42. Product Principles

1. **AI is part of the journey, not a standalone chatbot.**
2. **Recommendation must be explainable.**
3. **Operational facts come from trusted data, not hallucination.**
4. **Users can correct inferred preferences.**
5. **The system proposes itinerary changes; the user approves them.**
6. **Curated data quality matters more than dataset size.**
7. **Keep V1 focused on Da Nang.**
8. **Do not introduce microservices without a real need.**
9. **Build a complete vertical slice before advanced features.**
10. **Product quality matters more than the number of AI features.**

---

# 43. Final Product Identity

Do not present the project only as:

> “Ứng dụng du lịch Đà Nẵng tích hợp AI.”

Present it as:

> **Danang TourGuide is a personalized AI travel companion that understands a traveler’s visual preferences, recommends curated places in Da Nang, turns those recommendations into realistic itineraries, and continues assisting the traveler through maps, GPS, audio guidance and context-aware AI during the actual trip.**

Final product loop:

```text
PHOTOS
  ↓
TASTE
  ↓
PLACES
  ↓
TRIP
  ↓
EXPERIENCE
  ↓
FEEDBACK
  ↺
```

---

# 44. Research Basis

The product direction is inspired by the uploaded paper:

**Travel Direction Recommendation Model Based on Photos of User Social Network Profile — Pavel Stefanovič & Simona Ramanauskaitė**

Ideas adopted:

- travel preference can be inferred from image content,
- historical/destination image data can be compared with user image data,
- similarity-based recommendation is useful,
- multiple photos are more informative than relying on one image,
- per-image recommendation results can be aggregated.

Ideas intentionally changed for a software product:

- country recommendation → POI recommendation,
- Instagram crawling → user-selected images + curated POI corpus,
- object-detection-heavy feature space → semantic tags + modern embeddings,
- SOM is not required for V1,
- recommendations are re-ranked using real travel context such as time, distance, opening hours and weather.

---

# Final Summary

## Technology

```text
React Native + Expo
        ↓
NestJS Modular Monolith
        ↓
PostgreSQL + PostGIS + pgvector
        ↓
Gemini Vision + LLM + Embeddings + RAG + TTS
        ↓
Google Maps / Routes + Weather
        ↓
AWS + Docker + GitHub Actions
```

## Product

```text
User Images
    ↓
Travel DNA
    ↓
Personalized POIs
    ↓
Six Degrees Explanation
    ↓
Trip Builder
    ↓
Itinerary + Map
    ↓
GPS Travel Mode
    ↓
Audio + Contextual AI
    ↓
Feedback
```

**Danang TourGuide = Visual Personalization + Reliable POI Data + Smart Trip Planning + Context-aware Travel Companion.**
