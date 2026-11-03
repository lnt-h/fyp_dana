# Stakeholders — Gonarra

| Field | Value |
|---|---|
| Document ID | GONARRA-INTAKE-STAKEHOLDERS |
| Version | 0.1 |
| Status | Draft |
| Owner | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor (OQ-001) — [Pending] |
| Date | 2026-11-04 (written retroactively from SRC-100 and BRD v0.4) |
| Prompt used | `requirements/Intake_Intent_Prompt.md` v2.0, adapted copy `docs/00-governance/prompt-templates/requirements/Intake_Intent_Prompt.md` |

Rows are taken from BRD §6 (STK-001..STK-010). "Who decides" names who makes the decisions that settle that
stakeholder's concern, based on the decision makers recorded in SRC-100 and BRD §9, §13 and §15.

**Decision rights.** Accountable owner and decision maker for scope, direction and priorities: Lê Ngọc Tấn Hiền
(DEC-001..DEC-004, SRC-100 A-001). Approver of every gate: trantrongminh, FYP mentor (SRC-100 A-001; ASM-001,
OQ-001) — approvals [Pending]. Agents draft only and never approve.

| ID | Person or group | Role in the change | Concern | Influence | Who decides | Source |
|---|---|---|---|---|---|---|
| STK-001 | Vietnamese-speaking independent travelers (persona P-01) | Primary users | Feasible plan with little effort (SN-001..SN-004, SN-008, SN-011) | Medium | Owner decides scope and priority; mentor approves; participants' feedback in the user study informs later decisions | SRC-004 |
| STK-002 | English-speaking international travelers (persona P-02) | Primary users | Same, plus local names and addresses (SN-001..SN-005, SN-008, SN-011) | Medium | As STK-001 | SRC-004 |
| STK-003 | Lê Ngọc Tấn Hiền | Owner and author; also holds the curator role | Deliver and pass the FYP; manageable curation (SN-006, SN-009) | High | Decides scope, direction, priorities and curation (DEC-001..DEC-004) | SRC-100 A-001, A-009 |
| STK-004 | trantrongminh (full name and title to confirm, OQ-001) | FYP mentor, approver | Sound scope, method and evidence (SN-009) | High | Approves every gate; confirms DEC-001/DEC-002 at BRD sign-off | SRC-100 A-001 |
| STK-005 | FYP examination committee | Assessor | Working demo, report, evaluation (SN-009) | High | Decides the FYP assessment; assessment basis unconfirmed (OQ-003, ASM-003) | SRC-100 A-002 |
| STK-006 | Study participants | Evaluators | Informed consent, data protection (SN-007) | Low | Each participant decides whether to consent; study rules set by STK-010 (OQ-004) | SRC-008 |
| STK-007 | Data and service providers (Google, Overture, Foursquare, Wikidata, LiteAPI, Clerk, AWS) | Suppliers | Terms, attribution, quotas (SN-010) | High (can block) | Each provider decides its own terms and quotas; owner decides use within them (CON-001, BRU-004) | SRC-007 DATA.md |
| STK-008 | Venues and heritage authorities | Sources of facts | Correct representation of their places (SN-010) | Low | Venues decide their own facts; curator decides what is published (BRU-003) | SRC-007 DATA.md |
| STK-009 | Booking partners (Agoda, Booking.com, Klook, 12Go) | Handoff targets | Valid links, affiliate terms (SN-010) | Low | Each partner decides acceptance into its affiliate program (DEP-007); owner decides the partner list (glossary "Booking partner") | SRC-102 |
| STK-010 | University / faculty, research-ethics body | Sets deadline and study rules | Compliance of the study (SN-007, SN-009) | High (can block) | Decides the submission deadline (CON-003, OQ-002) and whether ethics approval is required (OQ-004) | SRC-100 A-002, OQ-004 |
