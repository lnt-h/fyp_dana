# Intake record — Gonarra bilingual AI travel planner and grounded local assistant

| Field | Value |
|---|---|
| Document ID | GONARRA-INTAKE |
| Version | 0.1 |
| Status | Draft |
| Owner (requester and accountable owner) | Lê Ngọc Tấn Hiền, student author and product owner [SRC-100 A-001] |
| Approver | trantrongminh, FYP mentor (full name and title to confirm — OQ-001) — [Pending] |
| Organization | Gonarra FYP |
| Date | 2026-11-04 |
| Target timeline | Early February 2027 (ASM-002: 2027-02-01 for planning; exact date OQ-002) |
| Prompt used | `requirements/Intake_Intent_Prompt.md` v2.0, adapted copy `docs/00-governance/prompt-templates/requirements/Intake_Intent_Prompt.md` |
| Companion files | `sources.md`, `stakeholders.md`, `glossary.md` |

**Retroactive record.** This intake record was written retroactively on 2026-11-04 from the elicitation record
SRC-100 (`docs/02-requirements/interviews/SRC-100-elicitation-session-2026-11-04.md`), cross-checked against
`docs/02-requirements/BRD.md` v0.4. It adds no new facts, decisions, IDs or approvals; requirements work (BRD, PRD)
already started from SRC-100 before this record existed.

**Proposed risk tier: Medium** (applying AI_SDLC-SOP.md §5.1, "use the highest applicable tier").

- Reason: the initiative contains business logic (itinerary feasibility rules, BRU-001..BRU-008), APIs and
  external dependencies (DEP-001..DEP-007), data handling of traveler accounts, trips, questions and study
  participants (BR-020, BR-021, BR-046; ASM-007), and authentication-adjacent work through an existing third-party
  identity provider (CON-005) [SRC-100 A-013, A-020]. High-tier triggers are excluded at intake level: payments and
  in-app booking are out of scope (DEC-004), no safety-critical behaviour is in scope, and the service is a
  non-commercial FYP evaluation service [BRD §2]. Individual later changes that touch authorization, account
  deletion or production infrastructure are tiered per change in later phases and may be raised to High.
- Controls and reviewers implied (SOP §5.1, Medium): human owner Lê Ngọc Tấn Hiền; documented acceptance criteria
  (BRD §7.6, AC-001..AC-050); focused tests; security-aware review; all required CI checks. Reviewer and approver of
  every gate: trantrongminh (FYP mentor, STK-004) — [Pending]. Compliance review: covered by mentor review pending
  OQ-004 and OQ-008 [BRD §15]. Agents draft only and never approve [SRC-100 header].

**Intake self-check (prompt §6 against SOP §5.1 exit criteria)**

| # | Criterion | Status | Evidence | Owner / due |
|---|---|---|---|---|
| 1 | Named human owner, acceptance criteria and risk tier recorded | Pass | Document control (owner); §5 success measures and BRD §7.6 AC-001..AC-050; risk tier above | — |
| 2 | Every success measure has a baseline, target and measurement method | Partial | §5: all 13 measures have target and method; MET-001..MET-003 baseline unknown, recorded as OQ-006 (not invented) | Lê Ngọc Tấn Hiền / 2026-11-15 (OQ-006) |
| 3 | Out of scope explicit; every source registered as SRC-xxx | Pass | §6 table; `sources.md` SRC-001..009, SRC-100..104 | — |
| 4 | Every open question has an owner and needed-by date; none scope-blocking without one | Pass | §7 table: OQ-001..004, OQ-006..008 have owner and date; OQ-005 closed | — |
| 5 | No solution, technology choice, architecture or estimate | Pass | Technology appears only as pre-existing constraints CON-004, CON-005 (§4), as the prompt §4 requires | — |
| 6 | Requester confirms problem and outcome are represented accurately | Partial | Owner accepted direction and targets in SRC-100 A-005, A-007; no confirmation of this record yet | Lê Ngọc Tấn Hiền / 2026-11-15 (with BRD sign-off, ASM-005) |

Score: 4 Pass, 2 Partial, 0 Fail, 0 N/A.

---

## 1. Problem

- A traveler planning a short (1–3 day) visit to a Vietnamese city assembles a plan from scattered sources —
  blogs, maps, social media — and checks by hand whether opening hours and travel time between stops let the day
  fit [SRC-004; BRD §3.1]. The effort this takes has not been measured [Unverified — OQ-006].
- Root causes: opening hours and real travel legs are not checked together; AI answers are not restricted to
  reviewed, dated sources; there is no single bilingual, source-backed view of a place for use on site
  [BRD §3.4].
- English-speaking visitors additionally struggle with Vietnamese names, addresses and entrances on site
  [SRC-001 §2; SRC-004].
- Demand for AI help is high: an Agoda 2026 survey reports that 81% of Vietnamese travelers intend to use AI to plan
  their next trip [SRC-101]. AI itinerary generation is already common (Mindtrip, Layla, Vie Travel AI, "Visit
  Vietnam") [SRC-101]; whether these show the source of each fact or flag unknown facts is not documented in reviewed
  sources [SRC-101; Unverified].
- Why now: the project is a final-year project that must show a working, evaluated product by early February 2027
  [SRC-100 A-002; ASM-002]. As of 2026-11-04 only mobile onboarding and third-party sign-in are done; a backend
  foundation exists but is unverified [SRC-100 A-020; SRC-002].

## 2. Proposed outcome

When the problem is solved, observable from outside the project:

- A Vietnamese- or English-speaking traveler can obtain a valid 1–3 day itinerary for one of five launch cities
  (Hà Nội, Thành phố Hồ Chí Minh, Đà Nẵng, Hội An, Huế) built only from reviewed local places, can see whether each
  day is feasible, and decides what becomes the final plan [SRC-100 A-003, DEC-001; BRD BO-001, BO-002].
- On site, the traveler can rely on local information that shows its source and says when a fact is unknown
  [SRC-100 DEC-001; BRD BO-003].
- The traveler can move from the plan to a booking partner without re-searching [SRC-100 DEC-002 (revised), A-007].
- The service operates privately across all five cities within the zero-cash budget [SRC-100 A-010, A-012; BRD
  BO-004].
- The product has been evaluated with 10–15 consenting participants before submission [SRC-100 A-007; BRD BO-005].

Long-term vision (not this outcome): a tour guide for the whole of Vietnam [SRC-100 A-003].

## 3. Affected users

| Group | How affected | Size | Source |
|---|---|---|---|
| Vietnamese-speaking independent (domestic) travelers planning a short city visit (STK-001, persona P-01) | Time spent assembling and checking plans; unreliable opening hours | Population not stated in any source [Unverified]; 10–15 study participants split VI/EN, at least 4 per language (BR-045) | SRC-004; SRC-101; SRC-100 A-007 |
| English-speaking international travelers (STK-002, persona P-02) | Same, plus difficulty with Vietnamese names, addresses and entrances on site | As above | SRC-001 §2; SRC-004 |
| Curator (role held by the owner, STK-003) | Must review and publish at least 150 bilingual places alone | 1 person | SRC-100 A-009 |
| Study participants (STK-006) | Take part in the evaluation; their data must be protected | 10–15 | SRC-008; SRC-100 A-007 |

Personas P-01 and P-02 are illustrative and are validated in the user study [BRD §3.3, Unverified]. Other
stakeholders: `stakeholders.md`.

## 4. Constraints

| ID | Constraint | Type | Source |
|---|---|---|---|
| CON-001 | No cash budget: AWS credits (USD 200) and Google free tiers only | Budget | SRC-100 A-010, A-012 |
| CON-002 | One person curates and reviews all places | Headcount | SRC-100 A-009 |
| CON-003 | FYP submission in early February 2027; 2027-02-01 assumed for planning (ASM-002); exact date OQ-002 | Deadline | SRC-100 A-002 |
| CON-004 | Hosting on AWS; the traveler app and the curator tool are separate from the backend and use only its HTTP API (pre-existing owner decision, recorded as a constraint) | Technical / legacy | SRC-100 A-012, A-013 |
| CON-005 | Existing implementation: identity provider Clerk; Expo/React Native mobile app; Python/FastAPI backend with PostgreSQL (recorded as a constraint, not chosen here) | Legacy | SRC-003; SRC-009 |
| CON-006 | Booking, payment and live inventory need partner agreements the project does not have | Contractual | SRC-102 |
| — | Vietnamese personal-data protection law assumed to apply to account and study data (ASM-007); ethics approval requirement unknown (OQ-004); cross-border transfer obligations unknown (OQ-008) | Regulatory (unconfirmed) | SRC-100 §Session close; BRD §10, §13 |
| — | Free-tier AI terms may allow the provider to use inputs; account identifiers, contact details and precise location must not be sent to external AI services | Data handling | SRC-100 RSK-002; BRD BR-046 |
| — | Provider data stored only where its terms allow; AI may not create places or facts | Policy | SRC-003; BRD BRU-002, BRU-004 |
| — | Cut order if late (DEC-003): indicative prices → photo → voice → lock/regeneration → iOS; never cut bilingual, five cities, explicit Save | Scope / schedule | SRC-100 DEC-003; BRD §13 |
| — | Planning assumptions: curation ≥ 15 places/week from 2026-11-16 (ASM-004); BRD sign-off by 2026-11-15 (ASM-005) | Assumption | SRC-100 A-016 |

## 5. Success measures

Measurement owner for every measure: Lê Ngọc Tấn Hiền. Definitions and formulas: BRD §4.1. Evaluation-set sizes
are fixed before tuning (ASM-011). Targets accepted by the owner in SRC-100 A-007.

| ID | Measure | Baseline | Target | Measurement method |
|---|---|---|---|---|
| MET-001 | Planning task completion | Unknown — OQ-006 | ≥ 80% of participants save a valid itinerary | Study session records, January 2027 study |
| MET-002 | Time to first proposal | Unknown — OQ-006 | Median ≤ 3 min | Study timing, January 2027 study |
| MET-003 | Perceived usability | Unknown — OQ-006 | Mean SUS ≥ 70 | Post-task System Usability Scale questionnaire |
| MET-004 | Conflict detection | No Gonarra system (0 checks) | 100% of conflict-set scenarios flagged | Acceptance run on each release candidate |
| MET-005 | Lock integrity | No Gonarra system | 0 locked stops changed by regeneration | Acceptance run on each release candidate |
| MET-006 | Saved-trip integrity | No Gonarra system | 0 saved itineraries changed without Save and 0 unsaved edits lost | Failure-injection run on each release candidate |
| MET-007 | Guide grounding | No Gonarra system | ≥ 95% of sampled answers fully supported by cited sources | Human claim-to-source review before the study |
| MET-008 | Correct refusal | No Gonarra system | ≥ 90% of out-of-catalog questions answered "insufficient evidence" | Evaluation set before the study |
| MET-009 | Photo identification | No Gonarra system | ≥ 85% top-1 correct on the photo test set | Photo test set before the study |
| MET-010 | Privacy | No Gonarra system | 0 cross-traveler disclosures | Access tests on each release candidate |
| MET-011 | Catalog coverage | 0 published places per city (2026-11-04) | ≥ 30 per city (pass); 50 stretch | Weekly catalog report |
| MET-012 | Cost | USD 0 (2026-11-04) | USD 0 cash; AWS spend ≤ USD 200 credits | Weekly AWS and Google billing records |
| MET-013 | Evaluation delivered | 0 participants (2026-11-04) | 10–15 consenting participants by 2027-01-31 | Signed consent and session records |

## 6. Out of scope

| Item | Classification | Precondition to start | Source |
|---|---|---|---|
| In-app booking confirmation and payment | Won't (this release) → post-MVP roadmap | Signed partner agreement | SRC-102; SRC-100 A-008, DEC-004 |
| Flight booking | Won't (this release) → roadmap | Partner agreement | SRC-102; DEC-004 |
| Social feed, following, public reviews, public trip sharing | Won't (this release) → roadmap | Post-FYP decision | SRC-001 §4; DEC-004 |
| Multi-city trips and intercity routing | Won't (this release) → roadmap | Five-city catalog stable | SRC-001 §4; DEC-004 |
| Accommodation planning inside the itinerary | Won't (this release) | — | SRC-001 §1 |
| Check-in, GPS arrival, background location | Out of scope | — | SRC-001 §4 |
| Recorded or GPS-triggered audio tours, offline audio | Out of scope | — | SRC-001 §4 |
| Expense tracking, memories, journals | Out of scope | — | SRC-001 §4 |
| Public-transit, motorcycle and bicycle routing | Out of scope (walking and driving only) | — | SRC-001 §4 |
| In-app turn-by-turn navigation, offline maps | Out of scope (handoff to external maps) | — | SRC-001 §4 |
| Runtime web search by the assistant | Out of scope | — | SRC-001 §4; SRC-003 |
| Live prices persisted with a trip | Out of scope (indicative prices only at time of viewing, Could) | — | SRC-102; BRU-005 |
| Cities beyond the five launch cities | Deferred | All five cities meet MET-011 | SRC-100 A-003 |

## 7. Open questions

| ID | Question | Answers it | Needed by | Status | Source |
|---|---|---|---|---|---|
| OQ-001 | Mentor's full name and title (validates ASM-001) | Lê Ngọc Tấn Hiền (with mentor) | 2026-11-11 | Open | SRC-100 A-001; BRD §13 |
| OQ-002 | Exact FYP submission date (ASM-002 assumes 2027-02-01) | Lê Ngọc Tấn Hiền (with faculty) | 2026-11-11 | Open | SRC-100 A-002 |
| OQ-003 | What the examiners assess: working product, report, user study (ASM-003) | Lê Ngọc Tấn Hiền (with mentor) | 2026-11-11 | Open | SRC-100 A-002 |
| OQ-004 | Is ethics approval or a consent template required for the 10–15 person study? | Lê Ngọc Tấn Hiền (ask mentor) | 2026-11-11 | Open | SRC-100 A-011 |
| OQ-005 | AWS account validity through the project | Lê Ngọc Tấn Hiền | — | Closed — owner assurance (SRC-100 A-015) | SRC-100 SRC-103 |
| OQ-006 | Baseline for BO-001 (MET-001..MET-003): measure participants' manual planning time in a study pre-task? | Lê Ngọc Tấn Hiền | 2026-11-15 | Open | BRD §4, §13 |
| OQ-007 | Update `plan.md` §4 to match the scope amendment (booking handoff in scope; voice is Should) | Lê Ngọc Tấn Hiền | 2026-11-20 | Open | SRC-100 post-session corrections; BRD §5.2 |
| OQ-008 | Which obligations apply to transferring traveler and study data to providers outside Vietnam? | Lê Ngọc Tấn Hiền (ask mentor) | 2026-11-30 | Open | BRD §13 |

Scope-blocking: OQ-002, OQ-003 and OQ-004 were carried as blocking from SRC-100 (session close); each has an owner
and a needed-by date. OQ-009..OQ-014, raised during PRD authoring, were resolved by owner delegation (SRC-100
A-022) and do not affect this intake.
