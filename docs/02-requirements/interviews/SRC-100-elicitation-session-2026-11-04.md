# SRC-100 — Direction elicitation session (Gonarra)

> **Kit prompt:** `analysis/BRD_Elicitation_Prompt_IEEE_standard.md` (SDLC-Prompt-Checklist @ 6996dae), §7.3 Phase 0 triage
> **Interviewee (BA / product owner):** Lê Ngọc Tấn Hiền, project author (A-001)
> **Facilitator:** Claude Code (agent; drafts only, never approves)
> **Started:** 2026-11-04 · **Status:** open

## Source register used for this session

| ID | Source | Notes |
|---|---|---|
| SRC-001 | `plan.md` (2026-11-02) | Implementation baseline; wins on conflict per `AGENTS.md` |
| SRC-002 | `progress.md` (2026-11-02) | Delivery tracker |
| SRC-003 | `AGENTS.md` | Product and implementation constraints |
| SRC-004 | `docs/BRD.md` (pre-rebuild) | BR-01..BR-04 |
| SRC-005 | `docs/PRD.md` (pre-rebuild) | FR-00..FR-07 |
| SRC-006 | `docs/USE-CASES.md`, `docs/USER-STORIES.md` | UC-00..06, US-00..08 |
| SRC-007 | `docs/ARCHITECTURE.md`, `API.md`, `DATA.md`, `DATABASE-DESIGN.md`, `SECURITY.md` | Engineering contracts |
| SRC-008 | `docs/TESTING.md`, `docs/RESEARCH.md` | HA-02 acceptance, FYP evaluation |
| SRC-009 | `apps/api`, `apps/mobile` code at `4c03e7f` | Implemented baseline |

## Round 0 — intake summary (pre-filled from sources, to be confirmed)

**Known**
- F-001: Initiative = Gonarra (working name), bilingual VI/EN AI itinerary planner, 5 cities, 1–3 day single-city trips (SRC-001 §1).
- F-002: Primary users = independent travelers planning a short city visit (SRC-004).
- F-003: Business outcomes BR-01..BR-04 exist but have no baseline/target numbers (SRC-004).
- F-004: Context is a final-year project (FYP) with a researcher and supervisor (SRC-004, SRC-008).
- F-005: Implemented so far: mobile foundation + backend foundation only; planner, catalog, AI not started (SRC-002).

**Missing (blocking)**
- Named sponsor / outcome owner / approver (supervisor) — Q-003.
- FYP timeline, deadline and what the examiners will assess — Q-001.
- Whether full 5-city V1 is the FYP deliverable or an aspirational product scope — scope boundary.

**Biggest risks to BRD quality**
1. Success measures have no numeric baseline/target (BR-01..04).
2. Scope (5 cities × ≥30 reviewed bilingual POIs, iOS+Android, Guide) may exceed FYP time/capacity.
3. No named approver; author ≠ approver cannot be enforced.

## Round log

### Round 1 — questions asked
- Q-003 [BLOCKING] Who owns, who approves?
- Q-001 [BLOCKING] What is the FYP deadline and assessment?
- Q-S01 [BLOCKING] FYP deliverable scope vs product V1 scope.

### Round 1 — answers (2026-11-04)
- A-001 → Q-003: Owner/author = **Lê Ngọc Tấn Hiền**, student, FYP author. Mentor/approver = **trantrongminh** (as given; full name/title to confirm — ASM-001).
- A-002 → Q-001: Submission deadline ≈ **early February 2027**. Exact date and assessment basis not given → OQ-002, OQ-003.
- A-003 → Q-S01: Long-term vision = a **tour guide for the whole of Vietnam**; near-term (FYP) scope = **5 major cities** (Hà Nội, TP.HCM, Đà Nẵng, Hội An, Huế) — consistent with SRC-001.

**Assumptions raised**
- ASM-001: Mentor "trantrongminh" = Trần Trọng Minh, acts as approver for all gates — validation: confirm spelling/title — owner: Lê Ngọc Tấn Hiền.

**Open questions**
- OQ-002: Exact FYP submission date — blocks: BRD §timeline, SDP schedule — owner: Lê Ngọc Tấn Hiền — needed by: 2026-11-11.
- OQ-003: What the examiners assess (working product / report / user study) — blocks: success measures, test plan — owner: Lê Ngọc Tấn Hiền — needed by: 2026-11-11.

**Contradictions or conflicts found**
- C-001: Vision "tour guide for all of Vietnam" (A-003) vs SRC-001 product identity "itinerary planner first, Local Guide secondary" — decision owner: Lê Ngọc Tấn Hiền.
- C-002: Full 5-city V1 (SRC-001 phases 2–10, ≥30 reviewed bilingual POIs/city, iOS+Android) vs ~3 months to deadline with phases 2–10 NOT STARTED (SRC-002) — decision owner: Lê Ngọc Tấn Hiền with mentor.

**Coverage:** 0/11 topics closed (triage in progress) · Blocking questions open: 4

### Round 2 — questions asked
- Q-C01 [BLOCKING] Resolve C-001: primary product identity.
- Q-S02 [BLOCKING] Resolve C-002: Must vs cut-first list if time runs short.
- Q-001b [BLOCKING] OQ-002/OQ-003: exact date and assessment basis.

### Round 2 — answer (2026-11-04)
- A-004 → Q-C01: Interviewee asked for market research before deciding. Interest areas: AI assistant that plans e.g. "3 days 2 nights"; voice (STT/TTS) as an **advanced** feature; hotel/ticket price or booking; point the camera at a place and have the assistant introduce it. Q-C01, Q-S02, Q-001b remain open.

### SRC-101 — Market scan (2026-11-04, desk research, secondary sources)

| Capability | Who already does it | Implication for Gonarra |
|---|---|---|
| Prompt → multi-day itinerary | Mindtrip, Layla (global); Vie Travel AI, Tripion, "Visit Vietnam" national app (VN, launching late 2026); general assistants (ChatGPT, Gemini) | Commodity. Not a differentiator on its own. |
| In-chat booking / live prices | Mindtrip (flights via Sabre/PayPal), Layla (Skyscanner/Booking/GetYourGuide), Klook AI agent, Visit Vietnam app | Needs affiliate/commercial partnership; Amadeus Self-Service closed 2026-07-17; Booking.com/Agoda APIs are partner-approved. Real booking is not feasible for an FYP. |
| Camera → identify landmark + narration | Gemini Live (camera, general purpose), Google Lens, many small App Store apps (Landmark Identifier, Chiaro, Travelscope) | Exists, but generic and unsourced. A catalog-grounded VI/EN version is a defensible FYP demo. |
| Voice conversation | Gemini Live API supports vi-VN, audio + 1 fps images; server-to-server mode keeps keys server-side | Technically feasible through the existing backend; latency/cost need a spike. |

Addendum to SRC-101 (2026-11-04, recorded after BRD-AUDIT-01):
- Agoda 2026 survey: 81% of Vietnamese travellers intend to use AI to plan their next trip — https://www.tourexpi.com/en-intl/news/agoda-report-81-percent-of-vietnamese-travellers-want-to-use-ai-to-plan-their-next-trip-214807.html (secondary report of an Agoda press release).
- No reviewed source states whether the named AI planners show per-fact sources; the BRD marks that comparison [Unverified].

Candidate differentiator (to confirm): Vietnam-local, verified bilingual data with sources and explicit "unknown", feasibility checks (hours, routes, Plan Health), user control (locks, explicit Save). This is already SRC-001's thesis.

- C-003: Interest in booking and voice/camera (A-004) vs SRC-001/SRC-003 "no booking in MVP", "Voice only after text planner + Guide acceptance" — decision owner: Lê Ngọc Tấn Hiền with mentor.

### Round 3 — questions asked
- Q-D01 [BLOCKING] Choose direction option (A/B/C).
- Q-S03 [BLOCKING] Booking: deep-link handoff only vs out of scope.
- Q-001b [BLOCKING] Exact deadline and assessment basis (carried over).

### Round 3 — answer (2026-11-04)
- A-005 → Q-D01, Q-S03, Q-001b: Interviewee delegated the choice to the facilitator ("you know what is the best choice").
  Facilitator recommendation recorded below as **proposed decisions**; they become decisions only when the owner confirms them at BRD review (agent never approves).

**Proposed decisions (owner: Lê Ngọc Tấn Hiền; confirm at BRD review)**
- DEC-001 (Q-D01): Direction **B — trustworthy planner + grounded multimodal assistant**.
  Must: prompt + form → feasible 1–3 day itinerary, timeline/map, edit, locks, explicit Save, Plan Health, text Local Guide with sources, bilingual VI/EN, 5 cities.
  Should (advanced): camera "what is this place" matched only to nearby published catalog POIs; voice Q&A (STT/TTS) VI/EN over the same grounded Guide.
  Won't (FYP): in-app booking, live prices, payments, social, multi-city trips.
- DEC-002 (Q-S03): Booking = **(b) deep-link handoff only** (open Agoda/Klook/Google Maps externally); no price display, no partner API.
- DEC-003 (C-002 cut order if behind schedule, first to cut → last): camera → voice → scoped regeneration → second native platform (keep Android) → (never cut) bilingual, 5 cities, explicit Save.
- C-003 resolution proposed: DEC-001/002 amend SRC-001 §3 (voice moves from Deferred to Should, after text Guide acceptance; booking handoff link added). Requires a `plan.md` change after BRD baseline.

**Assumptions raised**
- ASM-002: Submission date = 2027-02-01 for planning — validation: confirm with faculty — owner: Lê Ngọc Tấn Hiền — needed by 2026-11-11 (OQ-002 stays open).
- ASM-003: Assessment = working demo + report + small consented user study (per SRC-008 RESEARCH.md) — owner: Lê Ngọc Tấn Hiền — validate with mentor by 2026-11-11 (OQ-003 stays open).

**Coverage:** triage closed · Topic 3 (Scope) provisionally closed by DEC-001..003 · Topics 1, 4–11 partly pre-filled from SRC-001..008 · Blocking open: OQ-002, OQ-003

### Round 4 — questions asked (Topic 2 — objectives and success measures)
- Q-201b [BLOCKING] Confirm candidate targets for BR-01 (planning usefulness).
- Q-202b [BLOCKING] Confirm candidate targets for BR-02/BR-03 (feasibility and trust).
- Q-203b [BLOCKING] User study size and timing.

### Round 4 — interviewee response (2026-11-04)
- A-006: Asked for deeper research on whether any hotel/ticket price API is feasible. Q-201b, Q-202b, Q-203b still open.

### SRC-102 — Hotel / ticket price API feasibility (2026-11-04, desk research)

| Option | Access for a student | Evidence | Verdict |
|---|---|---|---|
| LiteAPI (Nuitée) | Self-serve; free account; sandbox key without card; production key after adding a card; core endpoints free, premium billed | docs.liteapi.travel FAQ | **Best fit** — rates + prebook/book flow testable in sandbox. Verify VN coverage and whether sandbox rates are real. |
| Hotelbeds APItude | Free evaluation keys, 50 requests/day, test env on production servers, no real bookings; production needs contract | developer.hotelbeds.com | **Fallback** for realistic rates in a demo. |
| Affiliate deep links (Agoda, Booking.com, Klook, 12Go for bus/train/ferry) | Sign-up affiliate programs | partner pages | **Baseline**, zero integration risk, no prices in-app. |
| Booking.com Demand API | Managed Affiliate Partner contract required; sandbox has 1 test hotel | developers.booking.com | Not feasible for FYP. |
| Agoda Search API | Partner credentials + certification | developer.agoda.com | Not feasible for FYP timeline. |
| Amadeus Self-Service | Shut down 2026-07-17 | PhocusWire | Not available. |
| Travelpayouts Hotellook | Closed 2025-10-20 | Travelpayouts FAQ | Not available. |
| SerpApi Google Hotels | Paid (free ~100–250 searches/mo); Google litigation history | third-party pricing pages | Not recommended (legal/terms risk). |
| Xotelo, Apify scrapers, Vexere internal endpoint | No published terms / unofficial | xotelo.com, apify.com | Rejected — conflicts with SRC-003 provider-policy rule. |

**Proposed revision of DEC-002 (supersedes earlier proposal, owner to confirm):**
- Must: booking handoff via deep links (Agoda/Booking.com/Klook/12Go) from a stop or day.
- Could: "Stays near your plan" — indicative nightly rates from LiteAPI behind a provider adapter; runtime-only (no persistence, per SRC-003), timestamp + "indicative, confirm on partner site" label; sandbox/production mode shown in the UI. Fallback: Hotelbeds evaluation key.
- Won't: payment, in-app confirmed booking, flight booking.
- Spike SPK-001 (≤2 days, before design baseline): verify LiteAPI coverage for the 5 cities, sandbox vs real rates, display/caching terms, rate limits.
- Cut order (DEC-003) updated: in-app indicative prices → camera → voice → scoped regeneration → iOS.

### Round 4 — answers (2026-11-04)
- A-007 → DEC-002 (revised), Q-201b, Q-202b, Q-203b: **"ok hết"** — owner accepted all proposed targets and the revised DEC-002. DEC-001..003 confirmed by owner in this session (formal sign-off still at BRD review by mentor).
  - BO-01 / BR-01: ≥80% of study participants save a valid itinerary; median time to first usable proposal ≤3 min; SUS ≥70.
  - BR-02: 100% of golden scenarios with known conflicts flagged by Plan Health; 0 lock violations; 0 lost saved trips.
  - BR-03: ≥95% of sampled Guide answers supported by cited sources; ≥90% correct `insufficient_evidence` on out-of-catalog questions; camera top-1 identification ≥85% on a test photo set of catalog POIs.
  - User study: 10–15 participants split VI/EN, mid-January 2027.
- A-008: Owner still wants the Won't items (in-app booking/payment, flight booking, social, multi-city) — keep them **out of the MVP but in the product roadmap**.

**Decision**
- DEC-004: Reclassify "Won't" as **Won't (this release) → Post-MVP roadmap**. BRD records them in a "Future scope" section with rationale and preconditions (e.g. partner contract for booking); the design keeps extension points (provider adapter, booking handoff interface) but no implementation. Supersedes the Won't line of DEC-001/DEC-002.

**Coverage:** Topics 2, 3 closed · Topics 1, 4–11 pre-filled from sources, gaps below · Blocking open: OQ-002, OQ-003

### Round 5 — questions asked (Topics 4, 7, 9)
- Q-401 [BLOCKING] Who curates/reviews the bilingual POIs, and capacity.
- Q-701 [BLOCKING] Monthly budget cap for cloud + AI + map APIs.
- Q-901 [BLOCKING] University ethics/consent requirement for the user study.

### Round 5 — answers (2026-11-04)
- A-009 → Q-401: The owner is the **sole curator/reviewer** of all POIs (≥150 for 5 cities). Weekly capacity not stated.
- A-010 → Q-701: **Free tier only** — no paid budget.
- A-011 → Q-901: Unknown whether ethics approval is required → OQ-004.

**Constraints**
- CON-001: Zero paid budget; all providers must run within free tiers or education/trial credits (imposer: owner; impact: model choice, hosting, quotas).
- CON-002: Single curator for bilingual POI review (imposer: team size; impact: content throughput is the critical path).

**Risks**
- RSK-001 (High): Solo review of ≥150 bilingual POIs in ~12 weeks competes with engineering time. Response proposed: Hội An first, AI-assisted drafts from open data with mandatory human review (AI never publishes, per SRC-003), track throughput weekly.
- RSK-002 (High): Gemini API free tier — Google may use prompts/responses to improve its products. Response proposed: never send personal data or private trip content beyond what is needed; disclose in consent form; or use trial credits on the paid tier.
- RSK-003 (Medium): Free-tier quotas (Gemini RPM/RPD, Maps per-SKU monthly free calls) may throttle the user study. Response: cache catalog-side results, golden fixtures for tests, quota alerts.

**Contradictions or conflicts found**
- C-004: CON-001 vs SRC-001 delivery target (Cloud SQL, which has no free tier) — decision owner: Lê Ngọc Tấn Hiền.

**Open questions**
- OQ-004: Does the university require ethics approval / consent template for a 10–15 person usability study? — blocks: research protocol, test plan — owner: Lê Ngọc Tấn Hiền (ask mentor) — needed by: 2026-11-11.

### Round 6 — questions asked (Topics 7, 8, 11)
- Q-702 [BLOCKING] Resolve C-004 hosting option.
- Q-801 [BLOCKING] Accept RSK-001 response (AI-assisted drafts + human review) and weekly curation hours.
- Q-1101 [BLOCKING] Target BRD baseline date with mentor sign-off.

### Round 6 — answers (2026-11-04)
- A-012 → Q-702: Owner already has **AWS credits (USD 200)** → host on AWS. Resolves C-004 (Cloud SQL dropped).
- A-013: Backend and frontend(s) must be **separate deployables communicating only through the HTTP API** (already the case: `apps/api`, `apps/mobile`).
- A-014: Owner asked where data comes from and to **freeze the tech stack** now.
- Q-801 (curation hours) and Q-1101 (BRD sign-off date) not answered — carried over.

### SRC-103 — Infrastructure/provider facts checked (2026-11-04)
- AWS Free Plan (accounts after 2025-07-15): up to USD 200 credits; RDS PostgreSQL db.t4g.micro eligible; plan ends after 6 months or when credits run out (sources conflict 6 vs 12 months → OQ-005).
- AWS App Runner closed to new customers 2026-04-30; AWS recommends ECS Express Mode (Fargate, not free).
- Google Maps Platform: free monthly calls per SKU (Compute Routes Essentials 10,000/month) — AWS credits do not cover Google APIs.
- Gemini API free tier: per-project RPM/RPD limits vary by model; free-tier data-use terms differ from paid (verify in Gemini API Additional Terms) → RSK-002 stands.

**Proposed decisions (design-level; become ADRs in the SAD)**
- DEC-005 Hosting: AWS, one region (ap-southeast-1). EC2 t4g.small (Docker Compose: FastAPI + Caddy TLS) + RDS PostgreSQL 16 db.t4g.micro (PostGIS, pgvector) + S3 (licensed media, admin SPA) + ECR + SSM Parameter Store + CloudWatch. No NAT gateway, no ALB, no Fargate (cost). Budget alarm at USD 20/50/100.
- DEC-006 Separation: three deployables — `apps/api` (FastAPI), `apps/mobile` (Expo), `apps/admin` (curator web SPA) — sharing only the versioned REST/SSE contract (OpenAPI → generated TS types). No shared database access from clients.
- DEC-007 Data sources: see SRC-104 below.

### SRC-104 — Data source plan (proposed)
| Data | Source | Licence/terms | Use |
|---|---|---|---|
| POI candidates | Overture Maps Places; Foursquare OS Places | CDLA-Permissive-2.0; Apache-2.0 | Import, bounded to 5 cities; seed only |
| Identity, multilingual names | Wikidata | CC0 | Link IDs, VI/EN labels as evidence |
| Facts (hours, tickets, history) | Official sites: heritage/conservation centres of Hội An and Huế, city tourism departments, venue operators | per site | Evidence per field; original summaries written by owner |
| Background reading | Wikipedia / Wikivoyage | CC BY-SA | Evidence only, never copied prose |
| Images | Own photos; Wikimedia Commons with compatible licence | per file | With attribution record |
| Live hours/status | Google Places API | Google terms (runtime only) | Display, not stored |
| Route distance/time | Google Routes API | Google terms | Runtime, permitted provenance only |
| Hotel indicative rates | LiteAPI (fallback Hotelbeds eval) | provider terms | Runtime only (Could) |
| Booking handoff | Agoda, Booking.com, Klook, 12Go deep links | affiliate terms | Must |
| Guide RAG embeddings | Gemini embedding model over reviewed chunks | Gemini terms | pgvector |

**Open questions**
- OQ-005: AWS account creation date and plan type (6-month Free Plan?) — must cover until ≥2027-02-15 — owner: Lê Ngọc Tấn Hiền — needed by: 2026-11-11.

### Round 7 — answers (2026-11-04)
- A-015 → OQ-005: Owner confirms the AWS account stays active through the project. **OQ-005 closed** (owner assurance).
- A-016 → Q-801: Owner has "plenty of time" for curation; accepts the RSK-001 response. Quantity not given → ASM-004: ≥15 POIs reviewed per week from 2026-11-16; tracked weekly in `progress.md`; below 10/week for two weeks triggers DEC-003 cut order.
- Q-1101 not answered → ASM-005: BRD sign-off target 2026-11-15 (facilitator proposal) — owner may change.

**Not elicited, recorded as assumptions for review:** ASM-006 availability expectation limited to the evaluation window; ASM-007 Vietnamese personal-data law applies to participant and account data.

## Session close (2026-11-04)
Superseded in part by [SRC-105](SRC-105-re-baseline-session-2026-11-06.md) (2026-11-06): A-003 five-city scope, A-021 "Agno/AgentOS dropped", DEC-003 "never cut five cities" and DEC-010 Tier 2 "roadmap" are replaced by DEC-013..DEC-021.

Coverage gate (§7.8): topics 1–11 closed or carried as OQ/ASM with owners. Blocking items carried into the BRD: OQ-002 (exact deadline), OQ-003 (assessment basis), OQ-004 (ethics). Facilitator closes the session on the owner's instruction to continue; next step is BRD authoring with `analysis/BRD_Prompt_IEEE_standard.md`.

## Post-session corrections (2026-11-04, from BRD-AUDIT-01)
- DEC-001 clarified: locks belong with scoped regeneration (Should); the Must list is "edit, explicit Save, Plan Health" — locks are not a separate Must item.
- C-003 remains open as a document change: `plan.md` §4 (booking/affiliate, voice) must be amended after the BRD baseline → OQ-007.

### Round 8 — answers (2026-11-04)
- A-017: Owner confirms ASM-006 (RTO 4 h / RPO 24 h during study), ASM-008 (180-day staleness), ASM-009 (300 m nearby), ASM-010 (24 h deletion; study data to 2027-06-30), ASM-011 (evaluation-set sizes): "ok hết". To be marked confirmed in BRD 0.3.

### Round 9 — answers (2026-11-04, after BRD-AUDIT-02)
- A-018 → lock/regeneration priority: owner delegated ("you know what is the best choice"); facilitator recommendation **Should** recorded — lock and day regeneration are Should and are cut together under DEC-003. Mentor to confirm at sign-off.
- A-019 → deletion vs backups: owner chose "delete from live service within 24 h; database backups expire automatically after 7 days; a restore re-applies recorded deletions; stated in the consent form" (ASM-012).
- Correction: the 12Go transport handoff accepted in A-007 (DEC-002 revised) was dropped in BRD 0.2 by mistake; restored as BR-042 in BRD 0.3.
- A-020 (2026-11-04): Owner states current progress = onboarding screens + third-party authentication through Clerk only. Note: the repository also contains a backend foundation (apps/api: FastAPI, migration, Clerk JWT verifier, health endpoints; SRC-002 "Phase 1 IN PROGRESS"). Planning (SDP/WBS) treats onboarding + Clerk mobile auth as DONE-pending-verification and the backend foundation as existing-but-unverified (to be re-verified in Sprint 1).
- A-021 (2026-11-04): Owner delegated the stack review ("you know what is the best choice") and authorised code fixes. DEC-008 (OR-Tools scheduling) and DEC-009 (CLI ingestion with DuckDB, no queue) accepted; Agno/AgentOS dropped; API images built for linux/arm64. Code changed: CI multi-arch image build; docker-compose comment (GCP reference removed).
- A-022 (2026-11-04): Owner's standing delegation ("you know what is the best choice") applied to PRD questions OQ-009..OQ-014; facilitator recommendations adopted: BR-050 operating-cost requirement added (OQ-009); minimum OS = Expo SDK 58 toolchain minimums, test on participants' devices (OQ-010); ASM-013 performance thresholds accepted, verified in a latency spike by 2026-12-15 (OQ-011); legacy whole-trip/segment regeneration, day locks, category/tag search and curated collections dropped per BRD, `plan.md` updated with OQ-007 (OQ-012); in-app pseudonymous study timing log subject to OQ-004 (OQ-013); trip deletion and Today view stay Should, cut before lock/regeneration (OQ-014). Mentor confirms at sign-off.
- A-023 (2026-11-04): Standing delegation applied to data-design questions OQ-016..OQ-020; recommendations adopted: Google `place_id` stored as identifier only, other Places fields denied, Routes values kept only as long as terms allow (OQ-016, verify terms before first import); pseudonymous study logs kept to 2027-06-30 after account deletion, stated in consent (OQ-017); restore re-applies deletions by removing accounts whose Clerk user no longer exists (OQ-018); retention of unsaved proposals, Guide sessions, idempotency and AI-usage records set in API config (OQ-019); drop duplicate unique index on accounts.clerk_user_id (OQ-020). Open design defect for design audit: Guide embeddings must become searchable on first publication, not after a second publish.
- A-024 (2026-11-04): Standing delegation applied to API questions: OQ-070 imports run via CLI, admin API read-only for imports; OQ-071 already answered by BRD §14 "Booking partner" (Agoda, Booking.com, Klook, 12Go) — api/api-contract.md to align in design audit; OQ-072 price feature flag off until LiteAPI terms are read (SPK-001), responses no-store; OQ-073 Clerk user deleted last, app treats 401 after IN_PROGRESS as completed.
- A-025 (2026-11-04): Standing delegation applied to structure-view questions: OQ-080 EC2 OS = Amazon Linux 2023 arm64 (SSM agent included); OQ-081 SAD §3.1.2 domain model to adopt schema names (design audit fix); OQ-082 SAD §3.4.1 to add partner sites, EAS Build and local development (design audit fix).
- A-026 (2026-11-04): Standing delegation applied to behavioural-design questions: 409 `revision_conflict` / 422 `idempotency_key_mismatch` adopted; deletion job hourly, FAILED with reason, alert after 12 h; photo identification sends text descriptions of places within 300 m plus ≤1 licensed reference image each, final choice after photo-set spike; deletion status follows A-024/OQ-073 (Clerk user deleted last; 401 after IN_PROGRESS = completed) instead of a deletion receipt. Note: OQ-080..082 / ASM-080 were issued twice by two design agents — renumber in design audit.
### Round 10 — AI design review (2026-11-05)
- A-028 (2026-11-05): Owner reviewed the whole docs set with the facilitator and confirmed the direction (DEC-001 trustworthy planner + grounded assistant; bounded AI per ADR-004) and the stack; schedule capacity (SDP OQ-101) is explicitly deprioritised by the owner in favour of (1) consistent AI documentation, (2) detailed per-screen specifications for UI design and (3) completing and merging the docs set. The owner's concern "when data updates, can RAG update?" was answered by the two-layer design (structured facts in `place_facts`, narrative chunks pinned per publication) and three decisions were adopted under the standing delegation:
  - **DEC-010** Guide retrieval in two tiers: place-scoped questions (v1) use all approved facts and all approved sectioned chunks of the place's pinned corpus revision, no question embedding, no similarity threshold; city-scoped questions (roadmap) use hybrid lexical + pgvector retrieval with a threshold calibrated on the frozen sets. Chunk sections: OVERVIEW, HISTORY, HIGHLIGHTS, VISIT_TIPS, ETIQUETTE, ACCESS (ADR-010 0.3).
  - **DEC-011** One multi-day OR-Tools model per proposal (days as vehicles, per-date opening windows, drop penalties from Gemini ranks, locks mandatory); Gemini ranks one pool for the trip and no longer assigns days (ADR-011 0.2, ADR-004 0.2).
  - **DEC-012** Chunk embeddings computed on write by the curation API (API-035 `chunks[]`), `embedding_model` recorded, same model required for question embeddings, CLI `embed` only for backfill and re-embed (ADR-012 0.3).
  - Facts checked 2026-11-05 (web, secondary sources, to be verified on the official Gemini pages in SPK-002): Gemini Pro models are paid-only since 2026-04; Flash free-tier daily quotas have been reduced and sources conflict on the numbers; unpaid-tier terms allow Google to use inputs and outputs for product improvement, including human review → RSK-002 stands; SPK-002 (TASK-017) is to run first and the paid-tier trial credit is the contingency.
  - Mentor to confirm at the design gate.
- A-029 (2026-11-05): Standing delegation applied to the screen-spec open points: OQ-108 city stays device-local; OQ-109 `City.centre` from the boundary centroid; OQ-110 no straight-line distance hint in the picker; OQ-112 additive curator fields (`provider_release`, `gate_missing_count`, `duplicate_count`, `failure_code`, API-033 `import_run_id`); OQ-111 and OQ-113 closed by A-028 / PR #4. API 0.4.0, data model 0.4, screen specs 0.2.

- A-027 (2026-11-04): Standing delegation applied to UI/UX questions OQ-060..069: as-built screens move to i18next VI/EN with city-neutral copy, layouts kept (OQ-060); guests see Home and onboarding only, other actions show a sign-in sheet (OQ-061); add `textMuted` #5E7585 and `tealText` #00788F tokens for text, originals kept for icons (OQ-064); travel preferences gain pace and travel modes with the chip pattern (OQ-065); Home bell and weather removed; onboarding/profile trace as supporting US-032/US-011; admin read endpoints for import runs and coverage; bundled place images need rights records; language setting added; deletion-completed display follows OQ-073 (OQ-066).
