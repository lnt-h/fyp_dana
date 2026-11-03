# BRD Audit — BRD-AUDIT-01

| Field | Value |
|---|---|
| Audit ID | BRD-AUDIT-01 |
| Date | 2026-11-04 |
| Artifact | `docs/02-requirements/BRD.md` — GONARRA-BRD, version 0.1 (Status: Draft) |
| Supporting record (read-only) | `docs/02-requirements/interviews/SRC-100-elicitation-session-2026-11-04.md`; also opened to check citations: `plan.md` (SRC-001), `git show 4c03e7f:docs/BRD.md` (SRC-004) |
| Auditor | Independent agent session (did not author the BRD and did not edit it) |
| Checklist | `SDLC-Prompt-Checklist/analysis/BRD_IEEE_29148_Checklist.xlsx` (20 rows), plus §6 self-check, §7.3 review checklist, §7.4 anti-patterns of `analysis/BRD_Prompt_IEEE_standard.md` v2.0; scoring per §A8 of `step-by-step-guidance.md` |
| Standard | ISO/IEC/IEEE 29148-2018 |
| Fix owner (all rows) | Lê Ngọc Tấn Hiền |

Scoring rules applied (§A8): `Pass` only where the evidence can be opened in the BRD; `Partial` carries an owner and a due date and does not count as done; every `Fail` is blocking; `Pending` is not used. Items that need human sign-off (sponsor or mentor confirmation) are not scored `Pass`.

## 1. Checklist results

### 1.1 IEEE 29148 BRD checklist (xlsx, all 20 rows)

| # | Category | Item | Status | Evidence (BRD section / ID) | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| X-01 | 1. Document & Business Overview | Business Purpose & Drivers | Pass | §2 Problem; §3.1, §3.3 root causes; §4 driver column BO-001..005 | Problem and drivers are stated. Problems with the evidence behind them are scored in R-5.3-1. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-02 | 1. Document & Business Overview | Business Objectives & Success Metrics | Partial | §4 BO-001..005; §4.1 MET-001..013 | (1) BO-001 has no baseline (`[TBD: OQ-006]`). (2) No ROI or benefit expectation, and no statement that ROI does not apply to an FYP. (3) MET-001 counts a "valid itinerary" but never defines it (for example, saved with no blocking conflict). (4) MET-011 gives two targets, "≥ 30 per city (target 50)". Say which one is the pass threshold. Action: close OQ-006, define "valid itinerary", fix the MET-011 threshold, add an ROI/benefit line or an explicit N/A. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |
| X-03 | 1. Document & Business Overview | Scope & Boundaries | Partial | §5.1, §5.2, §5.3 | In/out scope and boundaries are clear. However, §5.2 leaves out exclusions listed in SRC-001 §4 (`plan.md`): expense tracking/journals, public-transit/motorcycle/bicycle routing, offline maps, public trip sharing. It also leaves out the SRC-001 §1 deferral of accommodation planning, which is relevant to BR-019. Action: add these rows to §5.2 or mark them as superseded by DEC-00x. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-04 | 1. Document & Business Overview | Vision Statement | Pass | §3.5 (traced to SRC-100 A-003) | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-05 | 2. Stakeholder & User Analysis | Stakeholder Identification | Partial | §6 STK-001..009 | The university/faculty and any research-ethics body are missing as stakeholders, even though they impose CON-003 and CON-007 and own the answer to OQ-004. STK-003 combines owner, author and sole curator, but BR-004 and BRU-003 treat "the curator" as a separate role. Action: add STK-010 University/faculty (ethics, deadline) and say whether "curator" is a role of STK-003. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-06 | 2. Stakeholder & User Analysis | User Personas & Profile Characteristics | Partial | §3.2, §6 STK-001/002 | User classes are named by language only. There are no profiles: travel experience, trip party, device and connectivity on site, digital/AI familiarity, or domain experience. Action: add a short profile per traveler class, or reference SRC-006 user stories with the attributes carried over. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-07 | 2. Stakeholder & User Analysis | Business Constraints | Pass | §9 CON-001..007 | Budget, organizational, time, technical, contractual and regulatory constraints are present. Note: CON-003 is TBD (OQ-002), and CON-007 rests on assumption ASM-007 (see R-7.4-6). | Lê Ngọc Tấn Hiền | Non-blocking |
| X-08 | 3. Business Process & Operational Concept | Current State ('As-Is') Workflow | Pass | §3.1 Mermaid diagram and bullets | Effort is correctly marked Unverified (OQ-006). | Lê Ngọc Tấn Hiền | Non-blocking |
| X-09 | 3. Business Process & Operational Concept | Target State ('To-Be') Workflow | Pass | §3.6 Mermaid diagram | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-10 | 3. Business Process & Operational Concept | Operational Scenario & Use Cases | Partial | §3.6 only | No scenario narratives (for example, "VI traveler plans a 2-day Huế trip"; "EN traveler on site asks about an entrance"; "curator publishes a place"). SRC-006 use cases are referenced but not summarized. Action: add 3–5 business scenarios that map to BR IDs. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-11 | 4. Business & High-Level Functional Requirements | Singularity & Clarity | Fail | §7.1–§7.5; see §2 of this audit | Compound obligations in BR-004, BR-007, BR-010, BR-012, BR-013, BR-014, BR-015, BR-016, BR-017, BR-018, BR-019, BR-021, BR-022, BR-023. BR-019 uses "could", which is not a permitted normative verb (shall/should/may). BR-006, BR-012 and BR-022 have no actor. Action: split per §2 below and replace "could" with "may". Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |
| X-12 | 4. Business & High-Level Functional Requirements | Completeness & Implementation-Free | Partial | §7, §7.6, §14 | Gaps: (1) terms needed to decide Must requirements are undefined: "blocking conflict" (BR-009), "time window" (BR-008), "segment" (BR-013), "private data" (BR-021), "nearby" (BR-017), "confirmed preferences" (BR-005). (2) No requirement lets a traveler set or remove a lock, although DEC-001 makes locks Must (SRC-100 l.98). (3) Changing the per-leg transport mode (SRC-001 §1 step 5) is missing from BR-010. (4) Design-level wording appears in AC-004 ("without editing the database directly"), AC-020 ("before any external service is called") and AC-021 ("no rows owned"). Action: define the terms in §14, add a lock BR, and restate the ACs as outcomes. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |
| X-13 | 4. Business & High-Level Functional Requirements | Traceability & Rationale | Partial | §7 Source column; §12 | Every BR has an ID and a source, but several links are wrong. BR-020 lists SN-003, which is not in the §12 BO-004 row. BR-021 lists SN-007, a study-participant need, for traveler account deletion. The §12 coverage text says "SN-010 → BR-004", but BR-004's source is SN-006 only. BR-018 is Must but traces to SN-008, which is Should. BR-018 → BO-001 ("itinerary from trusted local content") is a weak fit. Rationales are 1–2 words ("Control", "Core value", "Grounding") and do not justify the requirement. Action: correct the source cells and the §12 coverage statement; write one-sentence rationales. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-14 | 4. Business & High-Level Functional Requirements | Feasibility & Realism | Partial | §10 RSK-001, RSK-002, DEP-005; §9 CON-001 | (1) BR-020 (questions accessible only to the traveler) conflicts with RSK-002 and DEP-002: free-tier Gemini terms let the provider use inputs, and BR-015 sends questions to that provider. (2) BR-019 depends on SPK-001, which has not run, and LiteAPI production needs a card (SRC-100 SRC-102), which is in tension with CON-001. (3) One curator must deliver ≥150 places in about 12 weeks while phases 2–10 have not started (SRC-002). This is mitigated only by assumption ASM-004. Action: resolve BR-020 vs RSK-002 (narrow BR-020, or require a no-training/paid tier) and record the feasibility basis per Must area. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |
| X-15 | 5. Business Quality & Non-Functional Attributes | Compliance & Regulatory Standards | Partial | §9 CON-007; §10 ASM-007; §11; OQ-004 | The applicable law is assumed (ASM-007), not confirmed. Ethics approval is unknown (OQ-004). There is no data-retention period, no deletion deadline, no consent content, and no statement on cross-border transfer to US-hosted providers (Clerk, Gemini, Google). Provider-terms compliance is covered (BRU-004, BRU-005). Action: close OQ-004 and ASM-007; add retention and deletion-time expectations. Due 2026-11-30 (ASM-007) / 2026-11-11 (OQ-004). | Lê Ngọc Tấn Hiền | Blocking |
| X-16 | 5. Business Quality & Non-Functional Attributes | Business Continuity & Availability | Partial | §11; ASM-006 | Availability ("during study sessions") and RPO (≤24 h) exist only as an unconfirmed assumption. There is no RTO and no expectation outside the study window (for example, demo or examination day). Action: confirm ASM-006 with the mentor and add an RTO and a demo-day availability expectation. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-17 | 5. Business Quality & Non-Functional Attributes | Security & Business Policy Constraints | Pass | §11 Security policy; BR-020; BRU-002..005, BRU-008 | Note: curator-role authorization (who may publish) is implied by BR-004/BRU-003 but not stated as a policy. Consider adding it. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-18 | 6. Assumptions, Dependencies & Risks | Business Assumptions | Pass | §10 ASM-001..007, each with owner, validation and due date | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-19 | 6. Assumptions, Dependencies & Risks | Dependencies & Constraints | Partial | §10 DEP-001..006 | Missing: (1) acceptance into affiliate programs (Agoda, Booking.com, Klook, 12Go), which Must requirement BR-018 depends on (SRC-100 SRC-102 "sign-up affiliate programs"); (2) the mentor/university ethics decision (OQ-004) as a dependency of BR-023; (3) the required `plan.md` (SRC-001) amendment that SRC-100 C-003 makes a precondition of DEC-001/002. Action: add DEP-007..009. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-20 | 6. Assumptions, Dependencies & Risks | Business Risks & Mitigation | Partial | §10 RSK-001..006 | Mitigations are present, but contingency plans exist only for RSK-001 and RSK-004 (DEC-003). Missing risks: ethics approval delays the study (OQ-004 → BR-023), affiliate applications are rejected (BR-018), and the AWS Free Plan expires before the deadline (SRC-100 SRC-103: 6-month plan; closed only by owner assurance, A-015). Action: add these risks with contingencies. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |

### 1.2 Prompt §6 self-check

| # | Category | Item | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| S-1 | §6 Self-check | Every business objective has ≥1 requirement and a measurable success measure | Pass | §12 rows BO-001..005; §4.1 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-2 | §6 Self-check | Every requirement uses `shall`, contains one obligation, avoids solution language | Fail | §7; see §2 | Compound statements are listed in X-11. BR-019 uses "could". Solution-flavored wording in BR-017 ("point the camera") and in ACs. Action: as X-11. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |
| S-3 | §6 Self-check | Every requirement has an acceptance criterion and a verification method | Pass | §7 AC and Verif. columns; §7.6 AC-001..023 | Each BR has an AC and a method. Whether those ACs actually decide the requirement is scored in R-4.7. | Lê Ngọc Tấn Hiền | Non-blocking |
| S-4 | §6 Self-check | Every requirement traces to an objective or need; no orphan | Pass | §7 Source; §12 | No orphans. Incorrect links are scored in X-13. | Lê Ngọc Tấn Hiền | Non-blocking |
| S-5 | §6 Self-check | Scope, exclusions, assumptions, dependencies and risks populated | Pass | §5, §10 | Gaps in content are scored in X-03, X-19, X-20. | Lê Ngọc Tấn Hiền | Non-blocking |
| S-6 | §6 Self-check | Every open question has an owner and a needed-by date | Pass | §13 OQ-001..004, OQ-006 | OQ-005 is closed, so a blank date is acceptable. | Lê Ngọc Tấn Hiền | Non-blocking |
| S-7 | §6 Self-check | Sponsor confirms problem and desired outcome are represented accurately | Partial | §15 both decisions `[Pending]`; SRC-100 A-007 (owner accepted targets/DEC-001..003) | Needs human sign-off and cannot pass yet. The owner's in-session confirmation is evidence, but the mentor (approver, ASM-001) has not reviewed. Action: hold the mentor review and record the decision and date in §15. Due 2026-11-15 (ASM-005). | Lê Ngọc Tấn Hiền | Blocking |

### 1.3 Prompt §7.3 review checklist

| # | Category | Item | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| R-5.1-1 | §7.3 5.1 Requirement quality | `shall` syntax and one obligation | Fail | §7 | Same defect as X-11/S-2. | Lê Ngọc Tấn Hiền | Blocking |
| R-5.1-2 | §7.3 5.1 Requirement quality | Free of solution/design language | Partial | BR-017; AC-004, AC-020, AC-021; BRU-006 | BR-017 prescribes the interaction ("point the camera"); state the outcome instead (identify a place from a photo taken on site). The ACs reference DB rows and call order. Action: restate as outcomes. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-3 | §7.3 5.1 Requirement quality | Quantified where quantity affects acceptance | Partial | BR-003, BR-015, BR-016, BR-017, BR-021, AC-005 | No freshness limit on verification dates (BR-003, despite the RSK-006 "freshness rules"). No answer-latency expectation (BR-015/016). "Nearby" has no distance (BR-017). No deletion deadline (BR-021). No success threshold in AC-005. Sizes of the golden, evaluation and photo test sets (AC-006/008/015/017) are not stated. Action: add the quantities. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-4 | §7.3 5.1 Requirement quality | No vague qualifiers | Partial | BR-012 "available", BR-014 "verified entrance", BR-017 "nearby", BR-019 "near the itinerary", BR-004 "one workflow", SN-006 "efficiently and safely" | Action: replace each with a measurable term or a glossary definition. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-5 | §7.3 5.1 Requirement quality | Specialized terms in glossary | Partial | §14 | Missing: blocking conflict, time window, segment, valid itinerary, launch city, curator, reviewed alias, operational fact, private data, golden scenario, booking partner (listed set). Plan Health "blocked" exists, but nothing maps it to BR-009's "blocking conflict". Action: add the terms. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |
| R-5.1-6 | §7.3 5.1 Requirement quality | No duplicate or contradictory requirements | Fail | BR-020 vs RSK-002; BR-014 vs AC-014; BR-018 (Must) vs SN-008 (Should); BR-013 (Should) vs DEC-001 (locks Must); BR-016/BR-018/BR-019 vs SRC-001 §1/§4; BR-011 ≈ BRU-001; BR-002 ⊃ BR-006 (published-only) | Contradictions: (1) BR-020 owner-only questions vs free-tier provider use of inputs. (2) AC-014 accepts "unknown" where BR-014 demands a "verified entrance". (3) Priority mismatches. (4) SRC-001 §4, the baseline that "wins on conflict", excludes "Booking, payment and affiliate inventory" and voice before the acceptance gates. SRC-100 C-003 says a `plan.md` change is needed, but the BRD does not record it. Duplicates: BR-011/BRU-001 and BR-002/BR-006. Keep them only with a cross-reference. Action: resolve each contradiction and record the C-003 resolution as an OQ or DEP. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |
| R-5.1-7 | §7.3 5.1 Requirement quality | Unique permanent IDs | Pass | All ID columns; legacy IDs mapped in §4 | "DEC-005..007" shares one row; give each its own row. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-1 | §7.3 5.2 Completeness & traceability | Every objective has ≥1 requirement | Pass | §12 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-2 | §7.3 5.2 Completeness & traceability | Every requirement traces to objective or need | Pass | §7 Source | Incorrect links are scored in X-13. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-3 | §7.3 5.2 Completeness & traceability | Every requirement has ≥1 acceptance criterion | Pass | §7.6 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-4 | §7.3 5.2 Completeness & traceability | Every requirement has a verification method | Pass | §7 Verif. column | BR-005 lists "S, T", but its AC covers only S. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-5 | §7.3 5.2 Completeness & traceability | Every stakeholder group has ≥1 need | Pass | §6 STK→SN columns | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-6 | §7.3 5.2 Completeness & traceability | Scope, exclusions, assumptions, dependencies, risks populated | Pass | §5, §10 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-7 | §7.3 5.2 Completeness & traceability | Every OQ has owner and needed-by date | Pass | §13 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.3-1 | §7.3 5.3 Business validation | Problem statement evidenced, not asserted | Fail | §3.2 "81% of Vietnamese travelers intend to use AI to plan trips [SRC-101]"; §2 and §3.1 claims about general AI assistants and named planners citing SRC-101 | SRC-101 (SRC-100 l.74–83) has no 81% figure. The figure also does not appear in SRC-004 or in `plan.md`. SRC-101 calls itinerary generation "commodity". It does not say that Mindtrip, Layla, Vie Travel AI or the Visit Vietnam app lack per-fact sources or unknown marking, nor that general assistants "cannot say what they do not know". The effort problem is Unverified (OQ-006). Action: cite a real source (publisher, date, URL) for the 81% figure or remove it; reword the competitor claims to what SRC-101 says or mark them `[Unverified]`. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |
| R-5.3-2 | §7.3 5.3 Business validation | Baseline and target values sourced and measurable | Partial | §4, §4.1; SRC-100 A-007; SRC-004 (30/50 places) | Targets trace to A-007 and SRC-004. BO-001 baseline is TBD (OQ-006, which the BRD itself lists as blocking). Action: close OQ-006 (for example, a manual-planning pre-task in the study). Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |
| R-5.3-3 | §7.3 5.3 Business validation | Benefits and costs stated in business terms | Partial | §2 "Investment"; §4.1 MET-012 | Cost is stated (USD 0 cash, USD 200 credits). The benefit is expressed only as study metrics. No traveler benefit is stated in business terms (time saved versus baseline, fewer failed days), and there is no note that ROI does not apply. Action: add a benefit statement tied to MET-002 and the OQ-006 baseline. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.3-4 | §7.3 5.3 Business validation | Sponsor confirms problem and outcome | Partial | §15 `[Pending]` | Same as S-7. Human sign-off is required, so this cannot pass yet. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |
| R-5.3-5 | §7.3 5.3 Business validation | Understandable by a business reader without technical translation | Partial | AC-012 "failure-injection", AC-020, AC-021 "rows", CON-005 stack names, "golden scenarios" | Most of the document is readable. Test and DB jargon in the ACs needs either a glossary entry or plain wording. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |

### 1.4 Prompt §7.4 anti-patterns (rejection list)

| # | Category | Item | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| R-7.4-1 | §7.4 Anti-patterns | Unverifiable quality words ("user-friendly", "fast") | Pass | §7 | None of the listed words appear in the BRs. The milder vague terms are scored in R-5.1-4. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-2 | §7.4 Anti-patterns | Solution prescription in requirements | Pass | CON-004/005 hold the technology; DEC-005..007 are deferred to the SAD | The BRs name no vendor or technology. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-3 | §7.4 Anti-patterns | Compound requirements ("view and edit and export") | Fail | BR-010 (reorder, add, remove, replace stops, and change durations), and the others in X-11 | BR-010 is the exact anti-pattern. Action: split. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |
| R-7.4-4 | §7.4 Anti-patterns | Improvement target with no baseline | Partial | BO-001 baseline `[TBD: OQ-006]` | The targets are absolute (so verifiable), but the BO-001 "effort" objective has no baseline. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |
| R-7.4-5 | §7.4 Anti-patterns | Requirements with no source | Pass | §7 Source column | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-6 | §7.4 Anti-patterns | Assumptions presented as facts | Fail | §3.2 "81%" [SRC-101]; §3.1 competitor claims; CON-007 states the law "applies" while its source is ASM-007; §3.4 "which the project has already designed for" | The unsupported statistic is presented as a sourced fact. CON-007 turns an assumption into a constraint. Action: as R-5.3-1; also mark CON-007 as conditional on ASM-007. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |
| R-7.4-7 | §7.4 Anti-patterns | Scope defined only by inclusions | Pass | §5.2 | Omissions are scored in X-03. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-8 | §7.4 Anti-patterns | Open questions resolved silently | Partial | SRC-100 C-003 ("Requires a `plan.md` change after BRD baseline"), not carried into §13; Readiness lists OQ-006 as blocking but the §15 conditions omit it | The resolution of C-003 (voice and booking against the SRC-001/SRC-003 exclusions) is applied in the BRD without an OQ, DEP or condition. Action: add an OQ/DEP for the SRC-001 amendment and make the §15 conditions match the Readiness list. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |

### 1.5 Auditor-added row (prompt §7.2 4.7)

| # | Category | Item | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| R-4.7 | §7.2 4.7 Business requirements | Acceptance criteria are objectively decidable and do not restate the BR | Fail | AC-005, AC-010, AC-012, AC-014, AC-016, AC-018 (all for Must or Should BRs) | AC-005 has no pass threshold ("MET-001..003 are reported" is a reporting step). AC-012 checks only saved trips, not unsaved edits. AC-014 contradicts BR-014. AC-018 contains an escape clause ("where the partner supports it") and does not test handoff from a stop. AC-010 and AC-016 are single demonstrations with no pass condition. Details are in §2. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |

## 2. Requirement-level defect list (BR-001..BR-023)

Key: **Syn** = shall-syntax / normative verb; **Sing** = singular; **Impl** = implementation-free; **Ver** = verifiable; **Tr** = traceability; **AC** = does the AC decide the BR? ✓ = no defect; ✗ = defect, explained in the Defects column.

| BR | Pri | Syn | Sing | Impl | Ver | Tr | AC | Defects and required fix |
|---|---|---|---|---|---|---|---|---|
| BR-001 | Must | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | AC-001 tests only reviewed aliases. Search by Vietnamese name and by English name is not tested, nor search without diacritics (SRC-001 §2), and no sample size is given. Fix: one AC case per name type per city. |
| BR-002 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | AC-002 covers imported candidates in search, proposals and answers. It does not cover the place card or camera results (BR-014, BR-017), or places that were unpublished or withdrawn. Overlaps BR-006 and BRU-003. Fix: extend AC-002 to every traveler-facing surface; cross-reference BR-006. |
| BR-003 | Must | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | The list "(hours, admission, entrance)" may be open-ended; state that it is closed or define "operational fact". There is no maximum age for a verification date (RSK-006 "freshness rules" are undefined). AC-003 inspects stored data for 20 places rather than what is displayed, and does not cover runtime Google Places hours (SRC-104). Fix: define the term, add a freshness limit, and verify on displayed screens. |
| BR-004 | Must | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | Review and publish are two obligations. "In one workflow" is vague and design-flavored. There is no throughput target, although SN-006 asks for "efficiently" and ASM-004 assumes ≥15 places a week. AC-004 ("without editing the database directly") is implementation-level and does not test review, reject or return. The trace to BO-004 (private service within budget) is weak, and the §12 coverage text claims SN-010, which is not in the source. Fix: split into review / publish (/ reject), add a throughput measure, fix the trace. |
| BR-005 | Must | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | "Confirmed preferences" is undefined. AC-005 has no pass threshold (how many requests, what success rate, which languages) and only the study (S) is covered, although the method also lists T. Fix: AC such as "for N golden requests per city and language, a proposal of the requested length is returned; ≥X% in the study". Define preferences (SRC-001 §1 step 2). |
| BR-006 | Must | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | Passive voice with no actor ("A proposed itinerary shall contain"). AC-006 is decisive, but the size of the golden set is not stated. Fix: "Gonarra shall include in a proposal only…" and state the size of the golden set. |
| BR-007 | Must | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | Three display obligations: order, times, travel legs. AC-007 adds mode, distance and duration, so the BR is narrower than its AC. Fix: split, or align the BR with the AC content. |
| BR-008 | Must | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | "Known conflict" is enumerated, but "time window" is undefined. The golden conflict set (size, coverage of each conflict type) is not specified. Fix: define "time window" and state that the set covers each conflict type. |
| BR-009 | Must | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | "Blocking conflict" is undefined. Nothing states which BR-008 conflicts block a save (the glossary entry for Plan Health "blocked" has no mapping), so AC-009 cannot be decided. Fix: define blocking conflicts in a BRU or the glossary. |
| BR-010 | Must | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | Five obligations (reorder, add, remove, replace, change duration). This is the §7.4 compound anti-pattern. It omits changing the per-leg transport mode (SRC-001 §1). AC-010 introduces a new obligation (recalculation) and a demonstration with no pass condition. Fix: split into separate BRs, add a recalculation BR, and give each a decisive AC. |
| BR-011 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | Duplicates BRU-001. AC-011 tests only closing the app or navigating away. It does not test that an AI regeneration or route refresh leaves the saved itinerary unchanged, nor that Save does persist the change. Fix: add those cases and cross-reference BRU-001. |
| BR-012 | Must | ✗ | ✗ | ✓ | ✗ | ✓ | ✗ | No actor. Two triggers ("generation or a provider") and two objects (saved itinerary, unsaved edits). "Remain available" is vague: available for how long, and across an app restart? AC-012 (MET-006) measures saved trips only, so the unsaved-edits half is not decided. Fix: split into saved / unsaved, define "available", and add an AC for unsaved edits. |
| BR-013 | Should | ✓ (should) | ✗ | ✓ | ✗ | ✓ | ✗ | Regeneration and lock preservation are combined. "Segment" is undefined. The lock capability itself has no BR, although DEC-001 lists locks as Must, so the priority conflicts with DEC-001. AC-013 does not test that regeneration produces a new proposal for the scoped part. Fix: separate BR (Must) "Travelers shall be able to lock a stop or day"; define "segment"; extend AC-013. |
| BR-014 | Must | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | The card must hold four items (local name, translated name, driver address, entrance). The BR demands a "verified entrance", but AC-014 also passes when the entrance is marked "unknown", so the AC weakens the BR. "A sample saved trip" is one trip, not a coverage set. Fix: align the BR and the AC (allow an explicit unknown in the BR, or require a verified entrance in the AC) and sample across cities. |
| BR-015 | Must | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | Several obligations (ask, answer in the traveler's language, cite sources, or give an insufficient-evidence statement). The scope "a question about a place" is unbounded. No sizes are given for the evaluation sets. No latency is stated. Conflicts with BR-020 and RSK-002, because questions go to a free-tier AI provider. Fix: split into language and grounding; state set sizes; resolve the privacy conflict. |
| BR-016 | Should | ✓ (should) | ✗ | ✓ | ✗ | ✓ | ✗ | Voice input and spoken output are separate obligations. AC-016 is one demonstration per language, with no transcription accuracy or pass threshold. Conflicts with SRC-001 §4 (voice only after the text gates; on-device STT; no raw audio stored), and the conflict is not recorded. Fix: split; add a threshold; record the SRC-001 amendment and the no-raw-audio rule as a BRU. |
| BR-017 | Should | ✓ (should) | ✗ | ✗ | ✗ | ✓ | ✗ | Combines identification, introduction and the "not recognised" outcome. "Point the camera" names the mechanism. "Nearby" is unquantified. AC-017 does not test "nearby" or the introduction, and the photo-set size and composition are undefined. Fix: restate as an outcome, define the radius, and extend the AC. |
| BR-018 | Must | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | Two entry points (trip, stop), three categories (stays, activities, transport) and context pre-fill. Must priority but SN-008 is Should. Conflicts with SRC-001 §4 ("Booking, payment and affiliate inventory" excluded), and the conflict is not recorded. There is no DEP for affiliate acceptance. AC-018 tests only "from a saved trip", "each listed partner" refers to a list the BRD never defines, and "where the partner supports it" makes the AC undecidable. Fix: split; align the priorities; define the partner list; remove the escape clause or name the fields per partner; add the DEP and the SRC-001 amendment. |
| BR-019 | Could | ✗ ("could") | ✗ | ✓ | ✗ | ✓ | ✗ | "Could" is not a permitted normative verb; use "may". Three obligations (show the price, the retrieval time, the notice). "Near the itinerary" is vague. AC-019 does not test that prices are shown or their relevance, only the labels and non-storage (BRU-005). Depends on SPK-001 and DEP-005; in tension with CON-001 (production key requires a card) and the SRC-001 §1 deferral of accommodation planning. Fix: reword with "may", define "near" (radius or city), and add a display AC. |
| BR-020 | Must | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | Conflicts with RSK-002 and DEP-002 (free-tier provider may use questions) and with BR-015. Does not say whether curator or admin access is excluded. The trace to SN-003 (control) is a mismatch and not in the §12 BO-004 row. AC-020 adds a design rule ("before any external service is called") and covers only cross-traveler requests. It does not cover disclosure to providers. Fix: resolve the conflict with RSK-002, fix the trace, and state the AC as an outcome. |
| BR-021 | Must | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | Two obligations (remove the data, report the status). "Private data" is undefined. No deadline. It is silent on copies at the identity provider (Clerk), in backups (ASM-006 daily backup) and in logs. The trace to SN-007 (study participants) is wrong for account holders. AC-021 ("no rows owned") checks only the primary database. Fix: split; define the data scope, including third parties and backups; add a time limit (for example, 30 days, subject to ASM-007); fix the trace. |
| BR-022 | Must | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | No actor (passive). Two objects (interface text, published place content). AC-022 is decisive but does not state the inspection method (full or sampled). Fix: "Gonarra shall present…" and split UI text from content. |
| BR-023 | Must | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | Combines participant count, consent, language coverage and deadline. This is a project obligation rather than a capability; acceptable for an FYP but should be labeled as such. AC-023 says "both languages represented" without a minimum per language (SRC-100 A-007: "split VI/EN"). Depends on OQ-004, with no DEP. Fix: add a minimum per language (for example, ≥5 each) and a DEP on the ethics decision. |

Summary of defects: shall-syntax or normative-verb defects in 4 BRs (BR-006, BR-012, BR-019, BR-022). Non-singular: 14 BRs. Implementation wording: 2 BRs (BR-004, BR-017). Verifiability gaps: 15 BRs. Traceability defects: 4 BRs (BR-004, BR-018, BR-020, BR-021). The AC does not fully decide the BR in 18 of 23 BRs; only BR-006, BR-007, BR-008, BR-015 and BR-022 have deciding ACs.

## 3. Summary

**Counts (55 rows):**

| Source | Pass | Partial | Fail | N/A |
|---|---|---|---|---|
| xlsx (20) | 7 | 12 | 1 | 0 |
| §6 self-check (7) | 5 | 1 | 1 | 0 |
| §7.3 review checklist (19) | 8 | 8 | 3 | 0 |
| §7.4 anti-patterns (8) | 4 | 2 | 2 | 0 |
| Auditor-added §7.2 4.7 (1) | 0 | 0 | 1 | 0 |
| **Total** | **24** | **23** | **8** | **0** |

**Blocking items (18):**

- Fail (8): X-11, S-2, R-5.1-1, R-5.1-6, R-5.3-1, R-7.4-3, R-7.4-6, R-4.7.
- Partial, blocking (10): X-02, X-12, X-14, X-15, S-7, R-5.1-5, R-5.3-2, R-5.3-4, R-7.4-4, R-7.4-8.

**Verdict: Not ready.**

Under §A8, any `Fail` blocks the gate. Under §7.3, the document must not be marked ready while a Must requirement fails a check, and Must requirements BR-004, BR-005, BR-009, BR-010, BR-012, BR-014, BR-018, BR-020 and BR-021 fail at least one. The BRD's own Readiness statement ("Ready with conditions") overstates the position. It also omits the evidence defect (unsupported "81%" statistic) and the unrecorded conflict with the SRC-001 exclusions.

Minimum to reach "Ready with conditions":

1. Split the compound BRs and fix BR-019's verb.
2. Make every Must AC decisive.
3. Remove or properly source the 81% claim and the competitor claims.
4. Resolve BR-020 vs RSK-002 and BR-014 vs AC-014.
5. Record the SRC-001 amendment (C-003) as an OQ or DEP.
6. Define "blocking conflict" and the other glossary gaps.

After that, the remaining conditions are OQ-002, OQ-003, OQ-004 and OQ-006, plus mentor sign-off (§15).

---

# BRD-AUDIT-02 (version 0.2)

| Field | Value |
|---|---|
| Audit ID | BRD-AUDIT-02 (re-audit) |
| Date | 2026-11-04 |
| Artifact | `docs/02-requirements/BRD.md` — GONARRA-BRD, version 0.2 (Status: Draft — in review) |
| Supporting record (read-only) | `docs/02-requirements/interviews/SRC-100-elicitation-session-2026-11-04.md`, including the SRC-101 addendum (l.83–85) and "Post-session corrections" (l.231–233) |
| Auditor | Independent agent session (did not edit `BRD.md`) |
| Checklist and rules | As BRD-AUDIT-01 (xlsx 20 rows, §6, §7.3, §7.4, auditor row §7.2 4.7; §A8 scoring) |
| Fix owner (all rows) | Lê Ngọc Tấn Hiền |

Every row of BRD-AUDIT-01 is re-scored below. "01" is the previous status. Items that need human sign-off or an external answer (mentor, university) are still not scored `Pass`.

Limitation: the auditor did not open the tourexpi.com URL now cited for the 81% figure. The citation can be opened, but its content was not verified in this session.

## A2-1. Checklist re-score

### A2-1.1 IEEE 29148 BRD checklist (xlsx)

| # | Category | Item | 01 | Status | Evidence (BRD 0.2) | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|---|
| X-01 | 1. Overview | Business Purpose & Drivers | Pass | Pass | §2 Problem; §3.1; §3.4; §4 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-02 | 1. Overview | Business Objectives & Success Metrics | Partial | Partial | §2 "Return on investment is not applicable"; §4.1 MET-011 "≥ 30 … (pass threshold)"; §14 "Valid itinerary"; §4 BO-001 baseline `[TBD: OQ-006]` | Fixed: ROI is marked N/A, "valid itinerary" is defined, and MET-011 has a single pass threshold. Still open: the BO-001 baseline (OQ-006). Action: close OQ-006. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |
| X-03 | 1. Overview | Scope & Boundaries | Partial | Pass | §5.2 (12 rows incl. SRC-001 §4 exclusions, accommodation planning); §5.2 "Amendment to SRC-001"; §5.3 | Scope is bounded. The dropped transport handoff is scored in R-7.4-8. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-04 | 1. Overview | Vision Statement | Pass | Pass | §3.6 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-05 | 2. Stakeholders | Stakeholder Identification | Partial | Pass | §6 STK-010; STK-003 "also holds the curator role"; §14 Curator | Note: 12Go has been removed from STK-009 (see R-7.4-8). | Lê Ngọc Tấn Hiền | Non-blocking |
| X-06 | 2. Stakeholders | User Personas & Profile Characteristics | Partial | Pass | §3.3 P-01, P-02 (age, context, device, connectivity, language, AI familiarity) | The personas are correctly marked `[Unverified]` and are to be validated in the study. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-07 | 2. Stakeholders | Business Constraints | Pass | Pass | §9 CON-001..006; CON-007 withdrawn and replaced by ASM-007/OQ-004 | No regulatory constraint is confirmed yet. That is tracked in X-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-08 | 3. Process | As-Is Workflow | Pass | Pass | §3.1 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-09 | 3. Process | To-Be Workflow | Pass | Pass | §3.7 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-10 | 3. Process | Operational Scenario & Use Cases | Partial | Pass | §3.8 SC-01..SC-03, each mapped to BR IDs | No scenario covers the curator or account deletion. Optional: add one for each. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-11 | 4. Requirements | Singularity & Clarity | Fail | Partial | §7.1–§7.5; A2-2 | Compound statements are split (BR-024..BR-047) and BR-019 now uses "may". Residual: (1) BR-035 ("Regeneration should…") and BR-045 ("The evaluation shall…") have no actor; BR-036, BR-037 and BR-043 use an artifact as the subject. (2) BR-015 still has two qualities (language, citation), and BR-043 has two labels. Action: rephrase with "Gonarra shall/should…" and split BR-043 if the labels are tested separately. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-12 | 4. Requirements | Completeness & Implementation-Free | Partial | Partial | §14 glossary; BR-034; BR-031; AC-004; AC-020 | Fixed: blocking conflict, day window, private data, nearby and lock are defined; a lock BR and a transport-mode BR exist. Still open: (1) "confirmed preferences" (BR-005, Must), "reviewed alias" (BR-001) and "precise location" (BR-046) are undefined. (2) Design-level clauses remain in AC-004 ("without direct database editing") and AC-020 ("no external service is called"). Action: define the terms and restate the clauses as outcomes. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-13 | 4. Requirements | Traceability & Rationale | Partial | Partial | §7 Source; §12 | Fixed: BR-020 and BR-021 now trace to SN-011, BR-004 to SN-010, and SN-008 is Must. Still open: (1) BR-043 lists SN-010 and BR-046 lists SN-007, but neither need appears in the Needs column of its BO row in §12. (2) The §12 "Need coverage" list is incomplete. It omits BR-001 under SN-001; BR-009, BR-031 and BR-032 under SN-002; BR-006, BR-016, BR-017, BR-024, BR-025, BR-037 and BR-040 under SN-004; BR-022, BR-037 and BR-039 under SN-005; BR-047 under SN-010 is present. (3) Eight BRs still have the one-word rationale "Control". Action: complete §12 and expand the rationales. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-14 | 4. Requirements | Feasibility & Realism | Partial | Partial | BR-020/BR-046 vs RSK-002; BR-021 vs ASM-006; BR-026 and §14 Blocking conflict vs RSK-003/DEP-001; DEP-005 | Fixed: the BR-020 vs RSK-002 conflict (BR-020 is narrowed, BR-046 is added, and RSK-002 has a contingency). Still open: (1) BR-021 requires 0 private-data records 24 h after deletion, but ASM-006 implies daily backups. Say whether backups are in scope, and give their retention. (2) A leg with no distance or duration is a blocking conflict, so a routing quota outage makes every proposal unsavable during the study. Record this as a risk and contingency, or allow saving with a warning. (3) BR-019 depends on SPK-001, which has not run (Could only). Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-15 | 5. Quality | Compliance & Regulatory Standards | Partial | Partial | ASM-007, ASM-010, OQ-004, DEP-008, RSK-007; BR-021, BR-046 | Retention, deletion time and AI-data minimisation are now present. The legal basis and the ethics requirement are still unconfirmed and depend on an external answer (OQ-004, ASM-007). Transfer of data to non-Vietnamese providers (Clerk, Google, AWS region) is still not addressed. Action: obtain the OQ-004 answer and add a cross-border transfer statement. Due 2026-11-11 (OQ-004) / 2026-11-30 (ASM-007). | Lê Ngọc Tấn Hiền | Blocking |
| X-16 | 5. Quality | Business Continuity & Availability | Partial | Partial | ASM-006 (RTO 4 h, RPO 24 h); §11 | The targets are now defined but exist only as an unconfirmed assumption (mentor confirmation needed). Demo-day and examination availability are not covered. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-17 | 5. Quality | Security & Business Policy | Pass | Pass | §11; BR-020; BR-046; BRU-002..008; §14 Curator | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-18 | 6. ADR | Business Assumptions | Pass | Pass | §10 ASM-001..011 with validation and due dates | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-19 | 6. ADR | Dependencies & Constraints | Partial | Pass | §10 DEP-007 (affiliates), DEP-008 (ethics), DEP-009 (`plan.md`) | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-20 | 6. ADR | Business Risks & Mitigation | Partial | Pass | §10 RSK-007..009; contingencies on RSK-001..004, RSK-007..009 | RSK-005 and RSK-006 have mitigations only (medium severity). The routing-outage risk is noted in X-14. | Lê Ngọc Tấn Hiền | Non-blocking |

### A2-1.2 Prompt §6 self-check

| # | Item | 01 | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| S-1 | Every BO has requirement and measurable measure | Pass | Pass | §12; §4.1 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-2 | `shall`, one obligation, no solution language | Fail | Partial | §7; A2-2 | Residual actor and compound issues as in X-11. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| S-3 | AC and verification method for every BR | Pass | Pass | §7 AC/Verif.; §7.6 (46 ACs, AC-0nn = BR-0nn; BR-042 unused) | Decisiveness is scored in R-4.7. | Lê Ngọc Tấn Hiền | Non-blocking |
| S-4 | Every BR traces; no orphan | Pass | Pass | §7 Source; §12 | Matrix gaps are scored in X-13. | Lê Ngọc Tấn Hiền | Non-blocking |
| S-5 | Scope, exclusions, assumptions, dependencies, risks populated | Pass | Pass | §5, §10 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-6 | Every OQ has owner and needed-by | Pass | Pass | §13 OQ-001..007 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-7 | Sponsor confirms problem and outcome | Partial | Partial | §15 `[Pending]` | Needs human sign-off and cannot pass yet. The mentor must also confirm the post-audit DEC-001 change (locks moved from Must to Should; see R-7.4-8). Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |

### A2-1.3 Prompt §7.3 review checklist

| # | Item | 01 | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| R-5.1-1 | `shall` syntax and one obligation | Fail | Partial | §7 | As X-11. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-2 | Free of solution/design language | Partial | Partial | BR-017 restated as "from a photo"; AC-004, AC-020 | The BRs are clean. Two ACs still prescribe mechanism. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-3 | Quantified where quantity matters | Partial | Partial | BR-025 (180 d), BR-021 (24 h), §14 Nearby (300 m), ASM-011 set sizes, BR-045 (≥4) | Still unquantified: answer time for on-site questions (BR-015, BR-016, BR-017), and the sample size of AC-014/036/037 ("a sample saved trip per city"). Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-4 | No vague qualifiers | Partial | Pass | §7, §14 | "Nearby", "verified", "near the itinerary" and "one workflow" are resolved. "Suitable for showing to a driver" (BR-036) is decided by AC-036 as "a Vietnamese address". | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-5 | Specialized terms in glossary | Partial | Partial | §14 (21 terms) | Missing: confirmed preferences, reviewed alias, precise location, booking/activity partner list ("each listed partner" in AC-018/041), launch city (defined only by the §5.1 list). Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-6 | No duplicate or contradictory requirements | Fail | Partial | BR-036 vs AC-036; BR-018 vs AC-018; BR-021 vs ASM-006; BR-023 vs AC-023 | Fixed: BR-020/RSK-002, BR-014/AC-014, SN-008 priority, BRU-001 duplicate, SRC-001 conflict (now OQ-007). Still open: (1) BR-036 requires an address, but AC-036 passes "unknown". (2) BR-018 requires the trip's dates, but AC-018 passes with city only. (3) BR-021 requires full deletion in 24 h, while ASM-006 implies daily backups. (4) BR-023 says "before 2027-01-31", but AC-023 says "on or before". Items 1–3 affect Must BRs. Action: align each BR/AC pair, and state the backup handling in BR-021 or ASM-010. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |
| R-5.1-7 | Unique permanent IDs | Pass | Pass | Withdrawn rows kept (BRU-001, CON-007); "BR-042 is not used" | DEC-005..007 still share one row (cosmetic). | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-1 | Every BO has ≥1 BR | Pass | Pass | §12 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-2 | Every BR traces | Pass | Pass | §7 Source | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-3 | Every BR has ≥1 AC | Pass | Pass | §7.6 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-4 | Every BR has a verification method | Pass | Pass | §7 Verif. | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-5 | Every stakeholder has a need | Pass | Pass | §6 (STK-010 → SN-007, SN-009) | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-6 | Scope, exclusions, ASM, DEP, RSK populated | Pass | Pass | §5, §10 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-7 | Every OQ has owner and date | Pass | Pass | §13 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.3-1 | Problem statement evidenced | Fail | Partial | §2, §3.2 cite Agoda 2026 via SRC-101 addendum (SRC-100 l.84); competitor comparison marked `[Unverified]` | The misattribution is fixed. The demand figure comes from a secondary report rather than Agoda's release, and the auditor did not open it. The core problem (planning effort) still rests only on SRC-004 and is marked Unverified, tracked by OQ-006. Action: cite the primary Agoda release if one is available; close OQ-006. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.3-2 | Baseline and targets sourced and measurable | Partial | Partial | §4 BO-001 `[TBD: OQ-006]` | Targets are sourced (SRC-100 A-007, SRC-004). The BO-001 baseline is still missing. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |
| R-5.3-3 | Benefits and costs in business terms | Partial | Pass | §2 "Benefits in business terms"; "Investment" | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.3-4 | Sponsor confirms problem and outcome | Partial | Partial | §15 `[Pending]` | Same as S-7. Human sign-off is required. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |
| R-5.3-5 | Understandable by business reader | Partial | Pass | §14 defines golden/evaluation set, user study; AC wording mostly plain | AC-004 and AC-020 jargon is noted under R-5.1-2. | Lê Ngọc Tấn Hiền | Non-blocking |

### A2-1.4 Prompt §7.4 anti-patterns

| # | Item | 01 | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| R-7.4-1 | Unverifiable quality words | Pass | Pass | §7 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-2 | Solution prescription in BRs | Pass | Pass | §7; CON-004/005 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-3 | Compound requirements | Fail | Pass | BR-010, BR-027..BR-031 (former BR-010 split) | Remaining minor double qualities are scored in X-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-4 | Improvement target with no baseline | Partial | Partial | BO-001 `[TBD: OQ-006]` | Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking |
| R-7.4-5 | Requirements with no source | Pass | Pass | §7 Source | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-6 | Assumptions presented as facts | Fail | Pass | 81% cited (SRC-100 l.84); comparison `[Unverified]`; CON-007 withdrawn; personas `[Unverified]`; "already designed for" removed | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-7 | Scope only by inclusions | Pass | Pass | §5.2 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-8 | Open questions resolved silently | Partial | Partial | OQ-007 and DEP-009 added; §15 conditions include OQ-006 (fixed). SRC-100 l.232 "DEC-001 clarified … locks … (Should)"; BRD §13 DEC-001 "clarified after BRD-AUDIT-01"; STK-009 and BR-018/BR-041 drop 12Go/transport | Two scope decisions were changed with no recorded owner answer. (1) DEC-001 listed locks as Must (SRC-100 l.102), and the change to Should is recorded only as a "post-session correction from BRD-AUDIT-01". It has no A-0nn answer ID, and BRD-AUDIT-01 flagged the inconsistency but did not recommend demotion. (2) The owner-accepted revised DEC-002 (A-007) made handoff Must for Agoda/Booking.com/Klook/12Go, including transport. BRD 0.2 drops transport handoff and 12Go without a decision row. Action: record both decisions with an owner answer (or restore the scope) and get mentor confirmation. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |

### A2-1.5 Auditor-added row (§7.2 4.7)

| # | Item | 01 | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| R-4.7 | ACs objectively decidable and actually decide their BR | Fail | Partial | §7.6; A2-2 | All ACs now have thresholds, and set sizes are fixed in ASM-011. 9 of 46 ACs still do not fully decide their BR. Five are for Must BRs: AC-001 (tests only aliases, not Vietnamese or English names), AC-011 (no case where AI regeneration or a route refresh must not persist), AC-018 (dates optional), AC-021 (scope of "records" undefined: backups, identity provider, logs), AC-036 (passes "unknown"). Four are minor: AC-013, AC-017, AC-019, AC-041. Under §7.3, a Must requirement that fails a check blocks readiness. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Blocking |

## A2-2. Requirement-level check (all BRs in 0.2)

Key: ✓ = no defect; ~ = minor defect (non-blocking); ✗ = defect that blocks a Must or makes the AC fail to decide the BR. Columns: Syn = shall-syntax/actor; Sing = singular; Impl = implementation-free; Ver = verifiable/unambiguous; Tr = trace; AC = AC decides the BR.

| BR | Pri | Syn | Sing | Impl | Ver | Tr | AC | Finding (fix by 2026-11-11, owner Lê Ngọc Tấn Hiền) |
|---|---|---|---|---|---|---|---|---|
| BR-001 | Must | ✓ | ✓ | ✓ | ~ | ✓ | ✗ | AC-001 still tests only "reviewed aliases" (20 searches). Search by Vietnamese name and by English name is untested. "Reviewed alias" is not in §14. |
| BR-002 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-003 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Note: the source and date shown for runtime provider facts (live Google Places hours, SRC-104) are unspecified. |
| BR-024 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-025 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Depends on ASM-008 confirmation. |
| BR-004 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | AC-004 "without direct database editing" is design wording. The rights-clearance part of BRU-003 is not checked. |
| BR-047 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-005 | Must | ✓ | ✓ | ✓ | ~ | ✓ | ✓ | "Confirmed preferences" is undefined (SRC-001 §1 step 2 lists them). |
| BR-006 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-007 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-026 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | See X-14: an unavailable leg is a blocking conflict, so feasibility depends on the routing quota. |
| BR-008 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Note: no BR covers non-blocking warnings, although Plan Health has a "warning" state. |
| BR-009 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-010 | Must | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | Rationale is one word. |
| BR-027 | Must | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | Rationale is one word. |
| BR-028 | Must | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | Rationale is one word. |
| BR-029 | Must | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | Rationale is one word. |
| BR-030 | Must | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | Rationale is one word. |
| BR-031 | Must | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | Rationale is one word. Missing from the SN-002 coverage list. |
| BR-032 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Times, legs and conflicts form a single recalculation, so this is acceptable as singular. |
| BR-011 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | AC-011 covers only closing or leaving the screen. Add a case: AI regeneration or a route refresh does not change the saved itinerary until Save. |
| BR-012 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-033 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-034 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Priority changed from Must (DEC-001) without a recorded owner answer (R-7.4-8). |
| BR-013 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | AC-013 checks that day 1 is unchanged, but does not require that day 2 is regenerated into a valid, unsaved proposal. |
| BR-035 | Should | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | No actor ("Regeneration should…"). Use "Gonarra should keep…". |
| BR-014 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | "A sample saved trip per city" does not state a size. |
| BR-036 | Must | ~ | ✓ | ✓ | ✓ | ✓ | ✗ | AC-036 passes "labels it unknown", which BR-036 does not allow. Align them as BR-037 does. The subject is the place card. |
| BR-037 | Must | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | The subject is the place card. |
| BR-015 | Must | ✓ | ~ | ✓ | ~ | ✓ | ✓ | Two qualities (language, citation). No answer time is stated. |
| BR-038 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-016 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Note: the SRC-001 §4 voice limits (no raw audio stored; start only after AC-015 passes) appear only in §5.2 prose and are not a BRU. |
| BR-039 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-017 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | AC-017/MET-009 does not test the 300 m "nearby" restriction. |
| BR-040 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-018 | Must | ✓ | ✓ | ✓ | ~ | ✓ | ✗ | BR-018 requires "city and dates", but AC-018 passes with city only. The partner list is undefined. Transport handoff was dropped (R-7.4-8). |
| BR-041 | Must | ✓ | ✓ | ✓ | ~ | ✓ | ~ | "Each listed activity partner": no list is defined. |
| BR-019 | Could | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | AC-019's alternative ("section is hidden with a message") lets the AC pass even when no price is ever shown. Require prices in N cities, or drop the alternative. Non-blocking because the priority is Could. |
| BR-043 | Could | ~ | ~ | ✓ | ✓ | ~ | ✓ | Passive subject; two labels. SN-010 is not in the §12 BO-001 Needs column. |
| BR-020 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | AC-020 adds a design clause ("no external service is called"). Curator/admin access to private data is not addressed. |
| BR-046 | Must | ✓ | ✓ | ✓ | ~ | ~ | ~ | "Precise location" is undefined. AC-046 should include photo requests (image location metadata). SN-007 is not in the §12 BO-004 Needs column. |
| BR-021 | Must | ✓ | ✓ | ✓ | ~ | ✓ | ✗ | AC-021 "0 records of that traveler's private data" does not say where: database, backups (ASM-006 daily backups), identity provider (Clerk), logs. This conflicts with the backup retention in ASM-006. |
| BR-044 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-022 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Bilingual place content is now enforced by BR-004 and the §14 Published place definition. |
| BR-023 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | "Before 2027-01-31" (BR) vs "on or before" (AC). Depends on DEP-008/OQ-004. |
| BR-045 | Must | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | Subject is "The evaluation"; use "The project owner shall include…". |

**Result:** 46 BRs checked (BR-042 unused).

| Outcome | BRs |
|---|---|
| ✗ (5 Must, 1 Could) | BR-001, BR-011, BR-018, BR-021, BR-036 (Must); BR-019 (Could) |
| Minor (~) only | 19 BRs |
| No defect | 21 BRs |

Change from BRD-AUDIT-01: the ACs of 18 of 23 BRs did not decide them; in 0.2, 6 of 46 BRs have an AC that does not decide them.

## A2-3. Summary (BRD-AUDIT-02)

**Counts (55 rows):**

| Source | Pass | Partial | Fail | N/A |
|---|---|---|---|---|
| xlsx (20) | 13 | 7 | 0 | 0 |
| §6 self-check (7) | 5 | 2 | 0 | 0 |
| §7.3 review checklist (19) | 11 | 8 | 0 | 0 |
| §7.4 anti-patterns (8) | 6 | 2 | 0 | 0 |
| Auditor-added §7.2 4.7 (1) | 0 | 1 | 0 | 0 |
| **Total** | **35** | **20** | **0** | **0** |
| Change from BRD-AUDIT-01 | +11 | −3 | −8 | 0 |

**Blocking items (9, all Partial).** They fall into two groups:

- **Document fixes the owner can make now:**
  - R-5.1-6: BR/AC contradictions on BR-018, BR-021 and BR-036.
  - R-4.7: the ACs of Must BRs BR-001, BR-011, BR-018, BR-021 and BR-036 do not decide them.
  - R-7.4-8: the lock demotion and the dropped transport handoff have no recorded owner decision.
- **External answers or human sign-off:**
  - X-02, R-5.3-2 and R-7.4-4: BO-001 baseline (OQ-006).
  - X-15: ethics and legal basis (OQ-004, ASM-007).
  - S-7 and R-5.3-4: mentor sign-off.

**Verdict: Not ready.** There are no Fail rows. However, under §7.3 the document cannot be marked ready while Must requirements BR-001, BR-011, BR-018, BR-021 and BR-036 fail an acceptance-criterion check. The BRD's own Readiness line ("All other audit findings of BRD-AUDIT-01 are addressed in 0.2") is not accurate.

Once R-5.1-6, R-4.7 and R-7.4-8 are fixed, the expected verdict is **Ready with conditions**. The conditions would be:

- OQ-002, OQ-003, OQ-004 and OQ-006 answered.
- ASM-006 and ASM-008..011 confirmed.
- Mentor confirmation of the DEC-001/DEC-002 scope changes.
- Mentor sign-off in §15.

---

# BRD-AUDIT-03 (version 0.3)

| Field | Value |
|---|---|
| Audit ID | BRD-AUDIT-03 (re-audit, final round 3 of 3) |
| Date | 2026-11-04 |
| Artifact | `docs/02-requirements/BRD.md` — GONARRA-BRD, version 0.3 |
| Supporting record (read-only) | `SRC-100-elicitation-session-2026-11-04.md`, including Round 8 (A-017) and Round 9 (A-018, A-019, correction on 12Go) |
| Auditor | Independent agent session (did not edit `BRD.md`) |
| Checklist and rules | As BRD-AUDIT-01/02; scoring per §A8 |
| Fix owner (all rows) | Lê Ngọc Tấn Hiền |

Every row is re-scored below. "02" is the status in BRD-AUDIT-02. Items that need mentor or university input, or sign-off, are still not `Pass`.

## A3-1. Checklist re-score

### A3-1.1 IEEE 29148 BRD checklist (xlsx)

| # | Category | Item | 02 | Status | Evidence (BRD 0.3) | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|---|
| X-01 | 1. Overview | Business Purpose & Drivers | Pass | Pass | §2; §3.1; §3.4 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-02 | 1. Overview | Business Objectives & Success Metrics | Partial | Partial | §4 BO-001 baseline `[TBD: OQ-006]`; §15 conditions | This is an external condition: the owner must decide the baseline method (OQ-006), and the value is measured in the study. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking (external) |
| X-03 | 1. Overview | Scope & Boundaries | Pass | Pass | §5.1–§5.3 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-04 | 1. Overview | Vision Statement | Pass | Pass | §3.6 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-05 | 2. Stakeholders | Stakeholder Identification | Pass | Partial | §6 STK-009 "Booking partners (Agoda, Booking.com, Klook)"; §14 Booking partner incl. 12Go; BR-042; DEP-007 | Document defect. 12Go (the transport partner of BR-042) is missing from STK-009, and the DEP-007 impact names only BR-018 and BR-041. Action: add 12Go to STK-009 and BR-042 to DEP-007. Due 2026-11-11. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-06 | 2. Stakeholders | User Personas | Pass | Pass | §3.3 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-07 | 2. Stakeholders | Business Constraints | Pass | Pass | §9 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-08 | 3. Process | As-Is Workflow | Pass | Pass | §3.1 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-09 | 3. Process | To-Be Workflow | Pass | Pass | §3.7 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-10 | 3. Process | Operational Scenarios | Pass | Pass | §3.8 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-11 | 4. Requirements | Singularity & Clarity | Partial | Pass | BR-035/036/037/045 now use "Gonarra"/"The project owner"; BR-015/BR-048 and BR-043/BR-049 split | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-12 | 4. Requirements | Completeness & Implementation-Free | Partial | Pass | §14 Confirmed preferences, Reviewed alias, Precise location, Booking partner; AC-004 "through the curator workflow" | AC-020 still says "no external service is called". This is acceptable because it implements the §11 security expectation. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-13 | 4. Requirements | Traceability & Rationale | Partial | Pass | §12 BO rows now include SN-010/SN-007; "Control" rationales replaced | Cosmetic: the "complete" need-coverage list omits BR-001 under SN-001, although BR-001 lists SN-001. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-14 | 4. Requirements | Feasibility & Realism | Partial | Pass | ASM-012 + BR-021 "from the live service"; RSK-010; RSK-001 contingency | BR-019 still depends on SPK-001 (Could; DEP-005). | Lê Ngọc Tấn Hiền | Non-blocking |
| X-15 | 5. Quality | Compliance & Regulatory | Partial | Partial | OQ-004, OQ-008 (new), ASM-007, ASM-010, ASM-012; BR-021, BR-046 | Every compliance item is now captured. The answers are external (mentor or university: ethics, applicable law, cross-border transfer). Note: ASM-010 is marked "confirmed by owner", but its stated validation is "Confirm with OQ-004 answer". The owner's confirmation does not close it. Due 2026-11-11 (OQ-004) / 2026-11-30 (OQ-008, ASM-007). | Lê Ngọc Tấn Hiền | Blocking (external) |
| X-16 | 5. Quality | Business Continuity & Availability | Partial | Partial | ASM-006 "Confirm with mentor — confirmed by owner (A-017)" | (1) External: ASM-006's stated validator is the mentor, and the mentor's confirmation is not among the §15 conditions. (2) Document gap, minor: availability for the demo or examination is not stated. Action: add mentor confirmation of ASM-006 to §15 and add one line on demo-day availability. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| X-17 | 5. Quality | Security & Policy | Pass | Pass | §11; BR-020; BR-046; BRU-008 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-18 | 6. ADR | Business Assumptions | Pass | Pass | ASM-001..012 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| X-19 | 6. ADR | Dependencies | Pass | Pass | DEP-001..009 | BR-042 is missing from the DEP-007 impact (counted in X-05). | Lê Ngọc Tấn Hiền | Non-blocking |
| X-20 | 6. ADR | Risks & Mitigation | Pass | Pass | RSK-001..010 | — | Lê Ngọc Tấn Hiền | Non-blocking |

### A3-1.2 Prompt §6 self-check

| # | Item | 02 | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| S-1 | BO → requirement + measure | Pass | Pass | §12; §4.1 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-2 | `shall`, one obligation, no solution language | Partial | Pass | §7 (49 BRs, A3-2) | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-3 | AC + verification method | Pass | Pass | §7.6 AC-001..AC-049 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-4 | Traces, no orphan | Pass | Pass | §12 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-5 | Scope, exclusions, ASM, DEP, RSK populated | Pass | Pass | §5, §10 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-6 | OQ owner + needed-by | Pass | Pass | §13 OQ-001..008 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| S-7 | Sponsor confirms problem and outcome | Partial | Partial | §15 `[Pending]`; DEC-001 "mentor to confirm" (A-018 was delegated by the owner to the facilitator) | Needs mentor sign-off and cannot pass yet. Due 2026-11-15 (ASM-005). | Lê Ngọc Tấn Hiền | Blocking (external) |

### A3-1.3 Prompt §7.3 review checklist

| # | Item | 02 | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| R-5.1-1 | `shall` syntax, one obligation | Partial | Pass | §7 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-2 | Free of solution language | Partial | Pass | §7 BRs; AC-004 rewritten | AC-020 is noted under X-12. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-3 | Quantified where quantity matters | Partial | Partial | AC-014/036/037 now "one saved trip per city with at least 5 stops"; BR-015, BR-016, BR-017 | Document gap, minor: no response time is stated for on-site answers (text, voice or photo), although on-site use makes this a business expectation. Action: add a target, for example "answer shown within N s for ≥90% of the Guide sample", or record it as an OQ for the PRD. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-4 | No vague qualifiers | Pass | Pass | §7, §14 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-5 | Glossary | Partial | Pass | §14 (25 terms) | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-6 | No duplicates or contradictions | Partial | Pass | BR-018/AC-018; BR-021/AC-021/ASM-012; BR-036/AC-036; BR-023/AC-023 | All four pairs from BRD-AUDIT-02 are aligned. The STK-009/12Go omission is a list gap, not a requirement contradiction (X-05). | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.1-7 | Unique permanent IDs | Pass | Pass | BR-042 now used; withdrawn rows kept | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-1 | Every BO has a BR | Pass | Pass | §12 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-2 | Every BR traces | Pass | Pass | §7 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-3 | Every BR has an AC | Pass | Pass | §7.6 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-4 | Every BR has a verification method | Pass | Pass | §7 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-5 | Every stakeholder has a need | Pass | Pass | §6 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-6 | Scope/ASM/DEP/RSK populated | Pass | Pass | §5, §10 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.2-7 | OQ owner + date | Pass | Pass | §13 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.3-1 | Problem statement evidenced | Partial | Partial | §2, §3.2 (Agoda figure via secondary report, SRC-100 l.84); effort `[TBD: OQ-006]` | Unchanged. The demand evidence is secondary, and the core effort problem is still unmeasured (OQ-006, external). Optional: cite the primary Agoda release. | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.3-2 | Baseline and targets sourced | Partial | Partial | BO-001 `[TBD: OQ-006]` | External condition (OQ-006). Due 2026-11-15. | Lê Ngọc Tấn Hiền | Blocking (external) |
| R-5.3-3 | Benefits and costs | Pass | Pass | §2 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-5.3-4 | Sponsor confirms | Partial | Partial | §15 `[Pending]` | Same as S-7 (external). | Lê Ngọc Tấn Hiền | Blocking (external) |
| R-5.3-5 | Business-readable | Pass | Pass | §14; §7.6 | — | Lê Ngọc Tấn Hiền | Non-blocking |

### A3-1.4 Prompt §7.4 anti-patterns

| # | Item | 02 | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| R-7.4-1 | Unverifiable quality words | Pass | Pass | §7 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-2 | Solution prescription | Pass | Pass | §7; CON-004/005 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-3 | Compound requirements | Pass | Pass | BR-015/048, BR-043/049 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-4 | No baseline | Partial | Partial | BO-001 `[TBD: OQ-006]` | External condition (OQ-006). | Lê Ngọc Tấn Hiền | Blocking (external) |
| R-7.4-5 | No source | Pass | Pass | §7 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-6 | Assumptions as facts | Pass | Pass | §2 `[Unverified]`; §3.3 `[Unverified]` | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-7 | Scope only by inclusions | Pass | Pass | §5.2 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| R-7.4-8 | OQs resolved silently | Partial | Pass | SRC-100 A-018 (lock priority; delegated, "Mentor to confirm"); 12Go correction and BR-042; DEC-001/002 rows; §15 condition "mentor confirms DEC-001 and DEC-002" | Both decisions are now recorded with an answer ID and routed to the mentor. | Lê Ngọc Tấn Hiền | Non-blocking |

### A3-1.5 Auditor-added row (§7.2 4.7)

| # | Item | 02 | Status | Evidence | Notes / Action | Owner | Gate |
|---|---|---|---|---|---|---|---|
| R-4.7 | ACs decidable and decide their BR | Partial | Partial | AC-001, AC-011, AC-018, AC-021, AC-036 rewritten (all Must ACs now decide their BR); residual AC-013, AC-017, AC-019, AC-046 | Document defects, none on a Must outcome except a minor AC-046 gap. AC-019 (Could) can still pass with no price shown ("or the section is hidden"). AC-013 (Should) does not require day 2 to change into a valid proposal. AC-017 (Should) does not test the 300 m filter. AC-046's 20-request sample does not state that it covers photo requests (location metadata). Action: tighten these four ACs before the PRD derives test cases. Due 2026-11-15. | Lê Ngọc Tấn Hiền | Non-blocking |

## A3-2. Requirement-level check (all 49 BRs in 0.3)

Key: ✓ = no defect; ~ = minor defect; ✗ = the AC does not decide the BR. Columns: Syn / Sing / Impl / Ver / Tr / AC.

| BR | Pri | Syn | Sing | Impl | Ver | Tr | AC | Finding |
|---|---|---|---|---|---|---|---|---|
| BR-001 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | AC-001 now covers VI name, EN name and alias (30 searches). |
| BR-002 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-003 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Note: how runtime provider facts are sourced and dated is left to the PRD. |
| BR-004 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-005 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | "Confirmed preferences" is now defined. |
| BR-006 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-007 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-008 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Note: no BR covers non-blocking warnings (PRD level). |
| BR-009 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-010 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-011 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | AC-011 now covers regeneration and route refresh. |
| BR-012 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-013 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | AC-013 does not require day 2 to be regenerated into a valid, unsaved proposal. |
| BR-014 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-015 | Must | ✓ | ✓ | ✓ | ~ | ✓ | ✓ | No on-site response time (R-5.1-3). |
| BR-016 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-017 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | AC-017 does not test the 300 m nearby restriction. |
| BR-018 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | AC-018 requires city, check-in and check-out. |
| BR-019 | Could | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | AC-019's "or the section is hidden" alternative still lets it pass with no price shown. Non-blocking (Could). |
| BR-020 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-021 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | AC-021 covers the DB, identity provider, logs, 7-day backup expiry and a restore test. |
| BR-022 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-023 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | BR and AC agree ("on or before"). |
| BR-024 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-025 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-026 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | The routing-outage effect is covered by RSK-010. |
| BR-027 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-028 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-029 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-030 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-031 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-032 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-033 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-034 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Priority pending mentor confirmation (A-018). |
| BR-035 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Actor fixed. |
| BR-036 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | BR and AC agree; AC adds ≥90% address coverage. |
| BR-037 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-038 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-039 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-040 | Should | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-041 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | The partner list is defined in §14. |
| BR-042 | Must | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | 12Go is missing from STK-009, and BR-042 is missing from the DEP-007 impact (X-05). |
| BR-043 | Could | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-044 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-045 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Actor fixed. |
| BR-046 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | AC-046 sample does not state that it covers photo requests (location metadata). |
| BR-047 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-048 | Must | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| BR-049 | Could | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |

**Result:** 49 BRs checked.

| Outcome | BRs |
|---|---|
| ✗ | 1 (BR-019, Could) |
| Minor (~) | 5 (BR-013, BR-015, BR-017, BR-042, BR-046 — 3 of them Must: BR-015, BR-042, BR-046) |
| Clean | 43 |

No Must requirement has a failing check. The five minor rows are BR-015 (counted under R-5.1-3), three AC gaps (BR-013, BR-017, BR-046) and the BR-042 trace gap. The fourth AC gap in R-4.7 is BR-019, shown as ✗.

## A3-3. Summary (BRD-AUDIT-03)

**Counts (55 rows):**

| Source | Pass | Partial | Fail | N/A |
|---|---|---|---|---|
| xlsx (20) | 16 | 4 | 0 | 0 |
| §6 self-check (7) | 6 | 1 | 0 | 0 |
| §7.3 review checklist (19) | 15 | 4 | 0 | 0 |
| §7.4 anti-patterns (8) | 7 | 1 | 0 | 0 |
| Auditor-added §7.2 4.7 (1) | 0 | 1 | 0 | 0 |
| **Total** | **44** | **11** | **0** | **0** |
| Change from BRD-AUDIT-02 | +9 | −9 | 0 | 0 |
| Change from BRD-AUDIT-01 | +20 | −12 | −8 | 0 |

**Blocking items (6, all Partial). Each is an external condition, not a document defect:**

| Row(s) | Condition | Who must act |
|---|---|---|
| X-02, R-5.3-2, R-7.4-4 | BO-001 baseline (OQ-006) | Owner decision on method; value from the study pre-task |
| X-15 | Ethics, applicable law, cross-border transfer (OQ-004, OQ-008, ASM-007; also closes ASM-010) | Mentor or university answer |
| S-7, R-5.3-4 | Mentor confirms problem, outcome, DEC-001 (A-018 lock priority) and DEC-002, and signs §15 | Mentor sign-off |

**Non-blocking Partials (5).** These contain minor document defects to fix in a 0.3.x touch-up or carry into the PRD:

- X-05: 12Go is missing from STK-009, and BR-042 is missing from DEP-007.
- X-16: there is no demo-day availability line, and the mentor's confirmation of ASM-006 is not a §15 condition.
- R-5.1-3: no on-site answer response time.
- R-5.3-1: the 81% figure comes from a secondary source; the effort problem is unmeasured (OQ-006).
- R-4.7: AC-013, AC-017, AC-019 and AC-046 do not fully decide their BRs.

**Verdict: Ready with conditions.** No row fails, no Must requirement fails a check, and every blocking item depends on an owner, mentor or university answer or on sign-off. The conditions are:

- OQ-002, OQ-003, OQ-004, OQ-006 and OQ-008 answered.
- The mentor confirms DEC-001/DEC-002 and ASM-006.
- The mentor signs §15.
- Recommended addition to §15: OQ-001 (the approver's identity), because approval is invalid if ASM-001 is false.

Two housekeeping points:

- The BRD's Readiness statement ("all outside the document") is accurate for the blocking items. It is not accurate for the five non-blocking document defects above.
- §16 still says "re-audit on 0.2"; update it to reference BRD-AUDIT-03.
