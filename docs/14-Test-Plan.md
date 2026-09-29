# Test Plan — Danang TourGuide

| Attribute | Value |
|-----------|-------|
| Standard | IEEE 829-2008 (adapted) |
| Version | 0.1 |
| Date | 2026-09-29 |
| Inputs | PRD, SAD, API, UI spec, product spec §40–41 |

---

## 1. Test items

Mobile app (Expo), NestJS API, PostgreSQL (PostGIS/pgvector), jobs (taste, TTS), integrations (Gemini, Maps, Weather) with **mocks** in CI.

---

## 2. Features to test (priority)

P0 demo path from spec §40. P1 weather, collections, explore-by-image, i18n, notifications.

---

## 3. Approach

| Level | Scope | Tooling (suggested) |
|-------|--------|---------------------|
| Unit | Scoring, aggregation, hours validation, geofence | Jest |
| Integration | API + testcontainers Postgres | Jest/Supertest |
| Contract | OpenAPI vs app types | Optional |
| E2E | Detox/Maestro happy path | Before the first complete vertical-slice demo; harden in Month 7 |
| Manual | GPS field test in Da Nang | Defense week |
| AI eval | Grounding: no invented POI; RAG refuse | Golden questions |

**Risk-based:** hallucination, authz on trips, upload auth, ranking correctness, itinerary hours.

---

## 4. Requirements extracted (testable)

| ID | Type | Test idea |
|----|------|-----------|
| FR-PREF-01 | Functional | Cannot confirm < 5 photos |
| FR-PREF-03 | Functional | PATCH DNA changes For You order |
| FR-REC-01 | Functional | Returned IDs ⊆ published places |
| FR-REC-03 | Functional | Explanation nodes ⊆ stored tags/evidence |
| FR-TRP-02 | Functional | JSON itinerary not free text only |
| FR-TRV-02 | Functional | Location inside radius → arrival |
| FR-AI-01 | Functional | No chunk → no fake history |
| NFR-SEC-01 | Quality | User B 403 on User A trip |
| BR-05 | Rule | Weather change requires accept |

---

## 5. Pass/fail (demo DoD)

Graduation demo **fails** if it needs DB edits, Postman, or slides instead of in-app flow.

---

## 6. Test cases (sample P0)

### TC-PREF-001 Select photos bounds

- **Pre:** Visual Taste  
- **Steps:** Select 4 photos → Continue disabled; add 5th → enabled; 11th rejected  
- **Expect:** Client + API validation  

### TC-REC-001 Corpus closed world

- **Pre:** Fixture 10 places; mock vectors  
- **Steps:** For You  
- **Expect:** Every `placeId` in fixture; none invented  

### TC-REC-002 Six Degrees evidence

- **Steps:** Why on a recommended place  
- **Expect:** Path nodes match `match_evidence`; no extra LLM-only place names  

### TC-TRP-001 Structured build

- **Steps:** Build 3-day trip  
- **Expect:** Days/stops with `place_id`, status `upcoming`  

### TC-TRP-002 Hours conflict flagged

- **Pre:** Place closed Tuesday  
- **Steps:** Force Tuesday visit  
- **Expect:** Warning or skip, no silent open hours  

### TC-AUTH-001 Isolation

- **Steps:** A creates trip; B GET  
- **Expect:** 403/404  

### TC-AI-001 Ungrounded fact

- **Pre:** Empty chunks for place  
- **Steps:** “When was this temple built?”  
- **Expect:** Refuse or “no source”, not a year  

### TC-TRV-001 Geofence

- **Steps:** POST location inside 80m of stop  
- **Expect:** Arrival event once (idempotent)  

### TC-MEDIA-001 Signed upload ownership

- **Steps:** Guest A requests signed PUT, uploads bytes, completes; guest B tries to complete/use the media ID.
- **Expect:** A's object is verified and usable; B gets 403/404; absent or wrong-size object remains pending/failed.

### TC-TRV-002 Manual arrival and permission denial

- **Steps:** Deny location; tap “I’m here” twice; repeat on simulated demo build.
- **Expect:** One event per stop, `method=manual` or `simulated`, visibly labeled; no false GPS claim.

### TC-VEC-001 Model and vector lineage

- **Steps:** Embed one image and one Vietnamese/English query with pinned model/config, then attempt to ingest wrong dimension/model.
- **Expect:** 768-d image/text outputs; incompatible rows rejected; no cross-model similarity.

### TC-API-001 Evidence ownership

- **Steps:** User A gets a recommendation run; B requests explanation with A's run ID.
- **Expect:** 403/404; A sees only stored evidence for the requested place/run.

### TC-RAG-002 Weak or wrong-place evidence

- **Steps:** Ask an unsupported history question with low-score or another POI's chunks.
- **Expect:** Insufficient-evidence response; no model-invented citation.

---

## 7. Environments

| Env | Gemini | Maps |
|-----|--------|------|
| CI | Mock | Mock |
| Staging | Real keys quota | Real |
| Demo | Real | Real + simulate arrival flag documented |

---

## 8. Suspension / resumption

If Gemini down: taste/Ask AI blocked; Explore + saved itinerary still testable.

---

## 9. Deliverables

- This plan  
- Test case spreadsheet (optional later)  
- CI reports  
- Traceability matrix: TC ↔ FR  

| TC | FR |
|----|-----|
| TC-PREF-001 | FR-PREF-01 |
| TC-REC-001 | FR-REC-01, BR-01 |
| TC-REC-002 | FR-REC-03 |
| TC-TRP-001 | FR-TRP-02 |
| TC-AUTH-001 | NFR-SEC-01 |
| TC-AI-001 | FR-AI-01, BR-03 |
| TC-TRV-001 | FR-TRV-02 |
| TC-MEDIA-001 | FR-PREF-01, NFR-SEC-01 |
| TC-TRV-002 | FR-TRV-02 |
| TC-VEC-001 | FR-PREF-02, FR-AI-01 |
| TC-API-001 | FR-REC-03, NFR-SEC-01 |
| TC-RAG-002 | FR-AI-01, BR-03 |

---

## 10. Schedule (aligned to roadmap)

| Month | Testing focus |
|-------|----------------|
| 2 | Place/search/saved API tests |
| 3 | Taste job integration |
| 4 | Rec unit + For You |
| 5 | Itinerary constraints |
| 6 | Geofence + RAG golden set |
| 7 | E2E, load light, security |
| 8 | Bug verification, demo rehearsal |

---

## 11. Risks

| Risk | Test response |
|------|----------------|
| GPS indoor | Simulator + manual “I’m here” |
| Flaky LLM | Deterministic mocks in CI; weekly live smoke |
| Copyright POI images | Ingest checklist, not automated |

## 12. Entry, exit and evidence

- Entry: seeded licensed POIs and source-backed chunks, migrations applied, mock provider fixtures and two isolated test identities available.
- Exit for P0: all demo-path cases pass, no unresolved high severity access-control or fabricated-fact defect, and a saved video/log shows the complete in-app flow. Record known P1/P2 exclusions.
- Performance: measure cached For You p95 under a documented small demo workload; exclude first-time provider vision calls and report them separately. Do not infer production availability from one thesis demo.
- Rehearse provider failure, no network, denied GPS, wrong-owner media/run IDs, route stale state and no-evidence RAG. Camera scanning is P2 until A-16 is resolved.
