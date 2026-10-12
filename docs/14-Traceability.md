# Requirements traceability matrix

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Coverage rule

PRD is the owner of requirement wording. This matrix connects each FR to business outcome, story, scenario, module, data, API, screen, implementation task and test. It demonstrates planned coverage only, not implemented or passed coverage.

| FR | BRD | Story / priority | Use case | Modules | Data | API contract | Screens | Task | Tests |
|---|---|---|---|---|---|---|---|---|---|
| FR-POI-01 | BIZ-01 | US-01 / P0 | UC-15 | Places | places, sources, place_facts, place_images | CLI ingestion; GET /places | UI-01, UI-03 | TASK-05 | TC-01 |
| FR-EXP-01 | BIZ-01 | US-02 / P0 | UC-02 | Places | places | GET /places | UI-01 | TASK-06 | TC-02, TC-03, TC-36 |
| FR-PLC-01 | BIZ-01 | US-03 / P0 | UC-02 | Places, Guides | places, place_facts, sources, place_images, audio_guides | GET /places/{id} | UI-03 | TASK-07 | TC-04, TC-36 |
| FR-MAP-01 | BIZ-01 | US-04 / P0 | UC-03 | Places, Routing | places, trip_stops, route_legs | GET /places; GET /trips/{id}/route | UI-02, UI-07 | TASK-08 | TC-05 |
| FR-SAV-01 | BIZ-05 | US-05 / P0 | UC-04 | Saved | saved_places | GET /saved; PUT, DELETE /saved/{placeId} | UI-03, UI-11 | TASK-09 | TC-23 |
| FR-AUTH-01 | BIZ-05 | US-06 / P0 | UC-01 | Identity | users, sessions | POST /auth/register, /auth/login, /auth/refresh, /auth/logout | UI-12, UI-13 | TASK-10 | TC-24, TC-25, TC-37 |
| FR-PREF-01 | BIZ-02 | US-07 / P0 | UC-05 | Trips | trips | POST /trips; PATCH /trips/{id} | UI-04 | TASK-11 | TC-06, TC-34 |
| FR-TRP-02 | BIZ-02 | US-08 / P0 | UC-06 | Trips, AI | trips, itinerary_proposals, trip_days, trip_stops, idempotency_records | POST /trips/{id}/build; POST /trips/{id}/proposals/{pid}/accept | UI-05, UI-06 | TASK-12 | TC-07, TC-08, TC-09, TC-22, TC-26, TC-34, TC-35 |
| FR-TRP-03 | BIZ-02 | US-09 / P0 | UC-07 | Trips | trip_days, trip_stops, route_legs | POST, PATCH, DELETE /trips/{id}/stops; PUT /trips/{id}/days/{dayId}/stops/order | UI-06 | TASK-13 | TC-11, TC-12, TC-34, TC-35, TC-37 |
| FR-TRP-04 | BIZ-02 | US-10 / P0 | UC-06, UC-07 | Routing | route_legs | GET /trips/{id}/route; POST /trips/{id}/route/refresh | UI-06, UI-07 | TASK-14 | TC-10, TC-11, TC-35, TC-37 |
| FR-TRV-01 | BIZ-03 | US-11 / P0 | UC-08 | Trips | trips, trip_stops | POST /trips/{id}/start; POST /trips/{id}/stops/{sid}/complete, /skip | UI-08 | TASK-15 | TC-13, TC-35 |
| FR-TRV-02 | BIZ-03 | US-12 / P0 | UC-09 | Trips, device GPS | arrival_events | POST /trips/{id}/stops/{sid}/arrivals | UI-08, UI-09 | TASK-16 | TC-14, TC-15, TC-16, TC-30 |
| FR-TRV-03 | BIZ-03 | US-13 / P0 | UC-10 | Guides | audio_guides | GET /places/{id}/audio-guide | UI-09, UI-10 | TASK-17 | TC-17, TC-18, TC-30, TC-36 |
| FR-AI-01 | BIZ-04 | US-14 / P0 | UC-11 | AI | knowledge_chunks, place_facts, sources | POST /ai/ask | UI-03, UI-14 | TASK-18 | TC-19, TC-20, TC-21, TC-22, TC-29, TC-36, TC-37 |
| FR-CAM-01 | BIZ-07 | US-15 / P1 | UC-12 | AI, Media | transient private asset | Deferred P1 contract review | UI-15 | TASK-19 | TC-31 |
| FR-STT-01 | BIZ-07 | US-16 / P1 | UC-13 | AI, Media | transient private asset | Deferred P1 contract review | UI-14, UI-16 | TASK-20 | TC-32 |
| FR-AUTH-02 | BIZ-07 | US-17 / P1 | UC-14 | Identity | users, sessions | Deferred P1 contract review | UI-12 | TASK-21 | TC-33 |

## Quality traceability

| NFR | BRD | Design | Tests |
|---|---|---|---|
| NFR-SEC-01 | BIZ-05, BIZ-06 | Identity/all private modules | TC-24, TC-25 |
| NFR-PER-01 | BIZ-06 | Places/database | TC-27 |
| NFR-REL-01 | BIZ-06 | Trips/AI/Routing | TC-22, TC-26, TC-30, TC-34, TC-37 |
| NFR-ACC-01 | BIZ-06 | Native UI | TC-28 |
| NFR-USAB-01 | BIZ-06 | Core journey | UAT-01, UAT-02, UAT-03, UAT-04, UAT-05 |
| NFR-TRUST-01 | BIZ-01, BIZ-04, BIZ-06 | Places/AI/Routing | TC-08, TC-19, TC-20, TC-21, TC-29, TC-35 |
All NFRs also attach to TASK-22 (security/reliability), TASK-23 (evaluation/UAT), TASK-24 (release/restore). Business rules BR-01..08 are exercised by TC-04, TC-07..12, TC-19..22 and TC-25: publication, operational provenance, source support, travel-time provenance, user acceptance, refusals and uncertainty. [Blueprint](12-Blueprint.md) assigns the responsible algorithms.

## Change control

Add or retire IDs explicitly in [Decisions](09-Project-Decisions.md). Update affected stories, API/data/UI, tasks and tests in the same change. Do not recycle retired IDs. Review every P0 row before implementation and again before demo; record actual evidence in [execution ledger](08-Test-Plan.md).

## Scope and evidence interpretation

Fourteen FRs are P0; three FRs are deferred P1. Optional rows preserve allocated IDs and future intent, not an implemented contract. Thirty-four P0/quality test cases and three deferred P1 cases are planned; five UAT tasks are separately defined. Working academic objectives OBJ-01–05 are in Research and remain unapproved; map actual institutional objectives before submission. All coverage here is planned, with runtime status in Test Plan.
