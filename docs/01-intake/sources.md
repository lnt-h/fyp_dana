# Source register — Gonarra

| Field | Value |
|---|---|
| Document ID | GONARRA-INTAKE-SOURCES |
| Version | 0.1 |
| Status | Draft |
| Owner | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor (OQ-001) — [Pending] |
| Date | 2026-11-04 (written retroactively from SRC-100 and BRD v0.4) |
| Prompt used | `requirements/Intake_Intent_Prompt.md` v2.0, adapted copy `docs/00-governance/prompt-templates/requirements/Intake_Intent_Prompt.md` |

IDs are those already assigned in SRC-100 ("Source register used for this session", SRC-101..SRC-104 sections) and
BRD §14; none is new. The owner of every repository document is the project owner, Lê Ngọc Tấn Hiền (SRC-100
A-001). Desk research SRC-101..SRC-104 was compiled by the facilitating agent (Claude Code) during SRC-100 and is
owned as a record by Lê Ngọc Tấn Hiền. Where a source records only a commit, no calendar date is given.

| ID | Source | Type | Location | Owner | Date / version | What it evidences |
|---|---|---|---|---|---|---|
| SRC-001 | Implementation baseline | Internal planning document | `plan.md` | Lê Ngọc Tấn Hiền | 2026-11-02 | Product identity, five launch cities, 1–3 day single-city trips, bilingual VI/EN (§1, §2); curator workflow (§3); excluded directions (§4, amended by BRD §5.2, OQ-007). Wins on conflict per `AGENTS.md` |
| SRC-002 | Delivery tracker | Internal status record | `progress.md` | Lê Ngọc Tấn Hiền | 2026-11-02 | Implemented state: mobile and backend foundation only, phases 2–10 not started; 0 published places, no deployed service |
| SRC-003 | Agent and product constraints | Internal policy | `AGENTS.md` | Lê Ngọc Tấn Hiền | commit 4c03e7f | Hard rules: AI never publishes or creates facts, provider-data storage rules, logging rules, no runtime web search (BRU-002, BRU-004, BRU-006, BRU-008) |
| SRC-004 | Pre-rebuild BRD | Internal requirements document (superseded) | git history `docs/BRD.md` | Lê Ngọc Tấn Hiền | commit 4c03e7f | Original business outcomes BR-01..BR-04 (now BO-001..BO-004), primary user groups, manual-planning problem |
| SRC-005 | Pre-rebuild PRD | Internal requirements document (to be replaced) | git history `docs/PRD.md` | Lê Ngọc Tấn Hiền | commit 4c03e7f | FR-00..FR-07, including accounts, privacy and deletion (FR-07) |
| SRC-006 | Use cases and user stories | Internal requirements documents (to be replaced) | git history `docs/USE-CASES.md`, `docs/USER-STORIES.md` | Lê Ngọc Tấn Hiền | commit 4c03e7f | UC-00..UC-06, US-00..US-08 |
| SRC-007 | Engineering contracts | Internal design documents (to be replaced) | git history `docs/ARCHITECTURE.md`, `API.md`, `DATA.md`, `DATABASE-DESIGN.md`, `SECURITY.md` | Lê Ngọc Tấn Hiền | commit 4c03e7f | Data-source and attribution rules, publication rule, privacy and security expectations; provider and venue stakeholders |
| SRC-008 | Testing and research | Internal test and research documents (to be replaced) | git history `docs/TESTING.md`, `docs/RESEARCH.md` | Lê Ngọc Tấn Hiền | commit 4c03e7f | HA-02 acceptance case; FYP evaluation with a consented user study; study participants as stakeholders |
| SRC-009 | Code baseline | Source code | `apps/api`, `apps/mobile` | Lê Ngọc Tấn Hiền | commit 4c03e7f | Existing implementation behind CON-005 (Clerk, Expo/React Native, FastAPI, PostgreSQL); backend foundation unverified (SRC-100 A-020) |
| SRC-100 | Direction elicitation session | Interview / elicitation record | `docs/02-requirements/interviews/SRC-100-elicitation-session-2026-11-04.md` | Lê Ngọc Tấn Hiền (interviewee); facilitated by Claude Code | 2026-11-04 (rounds 1–9, A-001..A-022) | Owner and approver (A-001), deadline (A-002), vision and five-city scope (A-003), direction and booking decisions DEC-001..DEC-004, success targets (A-007), curation, budget and hosting constraints (A-009..A-013), ASM-001..ASM-012, OQ-001..OQ-007, current implementation status (A-020), stack decisions DEC-005..DEC-009 (A-021) |
| SRC-101 | Market scan (including Agoda 2026 survey addendum) | Desk research, secondary sources | SRC-100 §SRC-101 | Lê Ngọc Tấn Hiền (compiled by Claude Code) | 2026-11-04 | AI itinerary generation is common (Mindtrip, Layla, Vie Travel AI, Visit Vietnam); booking needs partnerships; camera and voice assistants are general purpose; 81% of Vietnamese travelers intend to use AI to plan (Agoda 2026, secondary report); per-fact sourcing by competitors unverified |
| SRC-102 | Hotel / ticket price API feasibility | Desk research | SRC-100 §SRC-102 | Lê Ngọc Tấn Hiền (compiled by Claude Code) | 2026-11-04 | LiteAPI best fit and Hotelbeds fallback for indicative prices; affiliate deep links as baseline; Booking.com, Agoda, Amadeus, Travelpayouts not feasible; scrapers rejected. Basis of DEC-002 (revised), CON-006, BRU-005 |
| SRC-103 | Infrastructure and provider facts | Desk research | SRC-100 §SRC-103 | Lê Ngọc Tấn Hiền (compiled by Claude Code) | 2026-11-04 | AWS Free Plan credits and limits; App Runner closed to new customers; Google Maps per-SKU free calls not covered by AWS credits; Gemini free-tier quotas and data-use terms (RSK-002); basis of OQ-005 |
| SRC-104 | Data source plan (proposed) | Desk research / proposed plan | SRC-100 §SRC-104 | Lê Ngọc Tấn Hiền (compiled by Claude Code) | 2026-11-04 | Candidate data sources and their licences/terms (Overture, Foursquare OS Places, Wikidata, official sites, Wikimedia Commons, Google Places/Routes runtime only, LiteAPI, booking partners); proposed decision DEC-007, decided in the SAD |
