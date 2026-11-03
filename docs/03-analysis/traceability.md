# Traceability Matrix — Gonarra (BO → BR → FR/NFR → US)

## Document control

| Field | Value |
|---|---|
| Document ID | GONARRA-TRACE |
| Version | 0.2 |
| Status | Draft |
| Owner | Lê Ngọc Tấn Hiền, student author and product owner |
| Approver | trantrongminh, FYP mentor (OQ-001) |
| Date | 2026-11-04 |
| Prompt used | `analysis/PRD_prompt.md` v2.0, adapted copy `docs/00-governance/prompt-templates/analysis/PRD_prompt.md` (kit commit `6996dae`) |
| Sources | `docs/02-requirements/BRD.md` 0.4 (BO, BR), `docs/03-analysis/PRD.md` 0.2 (FR, NFR), `docs/03-analysis/user-stories.md` 0.2 (US) |

The matrix is generated mechanically from the ID tables of the three source documents; any edit to those tables requires regenerating it. `[ORPHAN]` marks a broken branch: a BR without FR/NFR, an FR/NFR without a valid source BR, an FR without a user story, or a story without an FR. Downstream columns for design (CMP-, API-) and verification (TC-) are added in Phases 4 and 7.

## 1. Coverage summary

| Check | Covered | Total | Result |
|---|---|---|---|
| BOs with at least one BR | 5 | 5 | Pass |
| BRs with an objective (BO) | 50 | 50 | Pass |
| BRs with at least one FR or NFR | 50 | 50 | Pass |
| FRs with a valid source BR | 97 | 97 | Pass |
| NFRs with a valid source BR | 38 | 38 | Pass |
| FRs covered by at least one user story | 97 | 97 | Pass |
| User stories with at least one FR | 43 | 43 | Pass |
| Priority consistency (FR/NFR ≤ source BR; story = highest linked FR) | all | — | Pass |
| **[ORPHAN] branches** | **0** | target 0 | Pass |

NFRs are verified by test, inspection or study rather than by stories; NFR → US links are therefore not required. BR-023 and BR-045 are project obligations of the owner; they are covered by FR-077 (study log, Should) and the release criteria RC-08 of the PRD, and by NFRs that keep the service running for the study.

Enabler traces (not orphans, but weaker): NFR-030..NFR-032 (maintainability) trace to BR-023 because the BRD has no explicit maintainability requirement (kept; mentor acceptance requested at sign-off, OQ-009); NFR-022..NFR-024 (accessibility) trace to BR-022. Cost and quota NFRs NFR-033..NFR-037 trace to BR-050 (BRD 0.4). OQ-009 closed by owner delegation SRC-100 A-022.

## 2. Forward matrix: BO → BR → FR/NFR → US

### BO-001

| BR | Priority | FR | NFR | User stories |
|---|---|---|---|---|
| BR-001 | Must | FR-001, FR-002, FR-003 | NFR-001 | US-001, US-002 |
| BR-005 | Must | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | NFR-002, NFR-003, NFR-019, NFR-020, NFR-021 | US-010, US-011, US-012, US-013, US-038 |
| BR-018 | Must | FR-064 | — | US-029 |
| BR-019 | Could | FR-066 | — | US-031 |
| BR-022 | Must | FR-075, FR-076, FR-097 | NFR-022, NFR-023, NFR-024, NFR-026 | US-034 |
| BR-041 | Must | FR-065 | — | US-030 |
| BR-042 | Must | FR-079 | — | US-037 |
| BR-043 | Could | FR-067, FR-081 | — | US-031 |
| BR-049 | Could | FR-080 | — | US-031 |

### BO-002

| BR | Priority | FR | NFR | User stories |
|---|---|---|---|---|
| BR-007 | Must | FR-027, FR-028, FR-088 | NFR-025 | US-014 |
| BR-008 | Must | FR-030, FR-031 | — | US-015 |
| BR-009 | Must | FR-032 | — | US-015 |
| BR-010 | Must | FR-033 | — | US-016 |
| BR-011 | Must | FR-040, FR-041, FR-045, FR-046, FR-090 | — | US-018, US-020 |
| BR-012 | Must | FR-042, FR-043 | NFR-009, NFR-010, NFR-011, NFR-038 | US-019 |
| BR-013 | Should | FR-048, FR-050 | — | US-042 |
| BR-026 | Must | FR-029 | — | US-014 |
| BR-027 | Must | FR-034 | — | US-039 |
| BR-028 | Must | FR-035 | — | US-040 |
| BR-029 | Must | FR-036 | — | US-041 |
| BR-030 | Must | FR-037 | — | US-017 |
| BR-031 | Must | FR-038 | — | US-017 |
| BR-032 | Must | FR-039, FR-089 | NFR-004 | US-016, US-017, US-039, US-040, US-041 |
| BR-033 | Must | FR-044 | — | US-019 |
| BR-034 | Should | FR-047, FR-091 | — | US-021 |
| BR-035 | Should | FR-049 | — | US-042 |

### BO-003

| BR | Priority | FR | NFR | User stories |
|---|---|---|---|---|
| BR-002 | Must | FR-004, FR-017 | — | US-003, US-007 |
| BR-003 | Must | FR-005 | — | US-002 |
| BR-006 | Must | FR-025, FR-087 | — | US-013 |
| BR-014 | Must | FR-051, FR-055 | — | US-022, US-024 |
| BR-015 | Must | FR-056, FR-058 | NFR-005, NFR-006 | US-025 |
| BR-016 | Should | FR-059, FR-063 | — | US-027 |
| BR-017 | Should | FR-061, FR-092, FR-093 | — | US-028 |
| BR-024 | Must | FR-006 | — | US-002 |
| BR-025 | Must | FR-007 | — | US-002 |
| BR-036 | Must | FR-052, FR-054 | — | US-022, US-023 |
| BR-037 | Must | FR-053 | — | US-022 |
| BR-038 | Must | FR-057 | — | US-026 |
| BR-039 | Should | FR-060 | — | US-043 |
| BR-040 | Should | FR-062 | — | US-028 |
| BR-048 | Must | FR-078 | — | US-025 |

### BO-004

| BR | Priority | FR | NFR | User stories |
|---|---|---|---|---|
| BR-004 | Must | FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, FR-082, FR-084 | NFR-015, NFR-029 | US-004, US-005, US-006, US-008, US-009 |
| BR-020 | Must | FR-068, FR-069, FR-094, FR-095 | NFR-012, NFR-013, NFR-014, NFR-016 | US-032 |
| BR-021 | Must | FR-071 | — | US-033 |
| BR-044 | Must | FR-072 | — | US-033 |
| BR-046 | Must | FR-070, FR-074 | NFR-017 | US-035 |
| BR-047 | Must | FR-008, FR-016, FR-083 | — | US-002, US-005 |
| BR-050 | Must | — | NFR-033, NFR-034, NFR-035, NFR-036, NFR-037 | — |

### BO-005

| BR | Priority | FR | NFR | User stories |
|---|---|---|---|---|
| BR-023 | Must | FR-077 | NFR-007, NFR-008, NFR-018, NFR-027, NFR-028, NFR-030, NFR-031, NFR-032 | US-036 |
| BR-045 | Must | FR-077 | — | US-036 |

## 3. Backward matrix: FR → BR → BO, and FR → US

| FR | Priority | Source BR | Objective | User stories |
|---|---|---|---|---|
| FR-001 | Must | BR-001 | BO-001 | US-001 |
| FR-002 | Must | BR-001 | BO-001 | US-001 |
| FR-003 | Must | BR-001 | BO-001 | US-002 |
| FR-004 | Must | BR-002 | BO-003 | US-003 |
| FR-005 | Must | BR-003 | BO-003 | US-002 |
| FR-006 | Must | BR-024 | BO-003 | US-002 |
| FR-007 | Must | BR-025 | BO-003 | US-002 |
| FR-008 | Must | BR-047 | BO-004 | US-002 |
| FR-009 | Must | BR-004 | BO-004 | US-004 |
| FR-010 | Must | BR-004 | BO-004 | US-004 |
| FR-011 | Must | BR-004 | BO-004 | US-005 |
| FR-012 | Must | BR-004 | BO-004 | US-005 |
| FR-013 | Must | BR-004 | BO-004 | US-006 |
| FR-014 | Must | BR-004 | BO-004 | US-006 |
| FR-015 | Must | BR-004 | BO-004 | US-006 |
| FR-016 | Must | BR-047 | BO-004 | US-005 |
| FR-017 | Should | BR-002 | BO-003 | US-007 |
| FR-018 | Should | BR-004 | BO-004 | US-008 |
| FR-019 | Should | BR-004 | BO-004 | US-009 |
| FR-020 | Must | BR-005 | BO-001 | US-010 |
| FR-021 | Must | BR-005 | BO-001 | US-010 |
| FR-022 | Must | BR-005 | BO-001 | US-012 |
| FR-023 | Must | BR-005 | BO-001 | US-038 |
| FR-024 | Must | BR-005 | BO-001 | US-013 |
| FR-025 | Must | BR-006 | BO-003 | US-013 |
| FR-026 | Should | BR-005 | BO-001 | US-013 |
| FR-027 | Must | BR-007 | BO-002 | US-014 |
| FR-028 | Must | BR-007 | BO-002 | US-014 |
| FR-029 | Must | BR-026 | BO-002 | US-014 |
| FR-030 | Must | BR-008 | BO-002 | US-015 |
| FR-031 | Must | BR-008 | BO-002 | US-015 |
| FR-032 | Must | BR-009 | BO-002 | US-015 |
| FR-033 | Must | BR-010 | BO-002 | US-016 |
| FR-034 | Must | BR-027 | BO-002 | US-039 |
| FR-035 | Must | BR-028 | BO-002 | US-040 |
| FR-036 | Must | BR-029 | BO-002 | US-041 |
| FR-037 | Must | BR-030 | BO-002 | US-017 |
| FR-038 | Must | BR-031 | BO-002 | US-017 |
| FR-039 | Must | BR-032 | BO-002 | US-016, US-017, US-039, US-040, US-041 |
| FR-040 | Must | BR-011 | BO-002 | US-018 |
| FR-041 | Must | BR-011 | BO-002 | US-018 |
| FR-042 | Must | BR-012 | BO-002 | US-019 |
| FR-043 | Must | BR-012 | BO-002 | US-019 |
| FR-044 | Must | BR-033 | BO-002 | US-019 |
| FR-045 | Must | BR-011 | BO-002 | US-018 |
| FR-046 | Should | BR-011 | BO-002 | US-020 |
| FR-047 | Should | BR-034 | BO-002 | US-021 |
| FR-048 | Should | BR-013 | BO-002 | US-042 |
| FR-049 | Should | BR-035 | BO-002 | US-042 |
| FR-050 | Should | BR-013 | BO-002 | US-042 |
| FR-051 | Must | BR-014 | BO-003 | US-022 |
| FR-052 | Must | BR-036 | BO-003 | US-022 |
| FR-053 | Must | BR-037 | BO-003 | US-022 |
| FR-054 | Must | BR-036 | BO-003 | US-023 |
| FR-055 | Should | BR-014 | BO-003 | US-024 |
| FR-056 | Must | BR-015 | BO-003 | US-025 |
| FR-057 | Must | BR-038 | BO-003 | US-026 |
| FR-058 | Must | BR-015 | BO-003 | US-025 |
| FR-059 | Should | BR-016 | BO-003 | US-027 |
| FR-060 | Should | BR-039 | BO-003 | US-043 |
| FR-061 | Should | BR-017 | BO-003 | US-028 |
| FR-062 | Should | BR-040 | BO-003 | US-028 |
| FR-063 | Should | BR-016 | BO-003 | US-027 |
| FR-064 | Must | BR-018 | BO-001 | US-029 |
| FR-065 | Must | BR-041 | BO-001 | US-030 |
| FR-066 | Could | BR-019 | BO-001 | US-031 |
| FR-067 | Could | BR-043 | BO-001 | US-031 |
| FR-068 | Must | BR-020 | BO-004 | US-032 |
| FR-069 | Must | BR-020 | BO-004 | US-032 |
| FR-070 | Must | BR-046 | BO-004 | US-035 |
| FR-071 | Must | BR-021 | BO-004 | US-033 |
| FR-072 | Must | BR-044 | BO-004 | US-033 |
| FR-073 | Should | BR-005 | BO-001 | US-011 |
| FR-074 | Should | BR-046 | BO-004 | US-035 |
| FR-075 | Must | BR-022 | BO-001 | US-034 |
| FR-076 | Must | BR-022 | BO-001 | US-034 |
| FR-077 | Should | BR-023, BR-045 | BO-005 | US-036 |
| FR-078 | Must | BR-048 | BO-003 | US-025 |
| FR-079 | Must | BR-042 | BO-001 | US-037 |
| FR-080 | Could | BR-049 | BO-001 | US-031 |
| FR-081 | Could | BR-043 | BO-001 | US-031 |
| FR-082 | Must | BR-004 | BO-004 | US-006 |
| FR-083 | Must | BR-047 | BO-004 | US-005 |
| FR-084 | Should | BR-004 | BO-004 | US-009 |
| FR-085 | Must | BR-005 | BO-001 | US-038 |
| FR-086 | Must | BR-005 | BO-001 | US-038 |
| FR-087 | Must | BR-006 | BO-003 | US-013 |
| FR-088 | Must | BR-007 | BO-002 | US-014 |
| FR-089 | Must | BR-032 | BO-002 | US-016, US-017, US-039, US-040, US-041 |
| FR-090 | Must | BR-011 | BO-002 | US-018 |
| FR-091 | Should | BR-034 | BO-002 | US-021 |
| FR-092 | Should | BR-017 | BO-003 | US-028 |
| FR-093 | Should | BR-017 | BO-003 | US-028 |
| FR-094 | Must | BR-020 | BO-004 | US-032 |
| FR-095 | Must | BR-020 | BO-004 | US-032 |
| FR-096 | Should | BR-005 | BO-001 | US-011 |
| FR-097 | Must | BR-022 | BO-001 | US-034 |

## 4. Backward matrix: NFR → BR → BO

| NFR | ISO 25010 area | Priority | Source BR | Objective |
|---|---|---|---|---|
| NFR-001 | Performance efficiency | Must | BR-001 | BO-001 |
| NFR-002 | Performance efficiency | Must | BR-005 | BO-001 |
| NFR-003 | Performance efficiency | Must | BR-005 | BO-001 |
| NFR-004 | Performance efficiency | Must | BR-032 | BO-002 |
| NFR-005 | Performance efficiency | Should | BR-015 | BO-003 |
| NFR-006 | Performance efficiency | Must | BR-015 | BO-003 |
| NFR-007 | Performance efficiency | Must | BR-023 | BO-005 |
| NFR-008 | Reliability and availability | Must | BR-023 | BO-005 |
| NFR-009 | Reliability and availability | Must | BR-012 | BO-002 |
| NFR-010 | Reliability and availability | Must | BR-012 | BO-002 |
| NFR-011 | Reliability and availability | Must | BR-012 | BO-002 |
| NFR-012 | Security and privacy | Must | BR-020 | BO-004 |
| NFR-013 | Security and privacy | Must | BR-020 | BO-004 |
| NFR-014 | Security and privacy | Must | BR-020 | BO-004 |
| NFR-015 | Security and privacy | Must | BR-004 | BO-004 |
| NFR-016 | Security and privacy | Must | BR-020 | BO-004 |
| NFR-017 | Security and privacy | Must | BR-046 | BO-004 |
| NFR-018 | Security and privacy | Must | BR-023 | BO-005 |
| NFR-019 | Usability and accessibility | Must | BR-005 | BO-001 |
| NFR-020 | Usability and accessibility | Must | BR-005 | BO-001 |
| NFR-021 | Usability and accessibility | Must | BR-005 | BO-001 |
| NFR-022 | Usability and accessibility | Should | BR-022 | BO-001 |
| NFR-023 | Usability and accessibility | Should | BR-022 | BO-001 |
| NFR-024 | Usability and accessibility | Should | BR-022 | BO-001 |
| NFR-025 | Localization | Must | BR-007 | BO-002 |
| NFR-026 | Localization | Must | BR-022 | BO-001 |
| NFR-027 | Compatibility | Must | BR-023 | BO-005 |
| NFR-028 | Compatibility | Should | BR-023 | BO-005 |
| NFR-029 | Compatibility | Must | BR-004 | BO-004 |
| NFR-030 | Maintainability | Must | BR-023 | BO-005 |
| NFR-031 | Maintainability | Must | BR-023 | BO-005 |
| NFR-032 | Maintainability | Must | BR-023 | BO-005 |
| NFR-033 | Cost and quotas | Must | BR-050 | BO-004 |
| NFR-034 | Cost and quotas | Must | BR-050 | BO-004 |
| NFR-035 | Cost and quotas | Must | BR-050 | BO-004 |
| NFR-036 | Cost and quotas | Should | BR-050 | BO-004 |
| NFR-037 | Cost and quotas | Should | BR-050 | BO-004 |
| NFR-038 | Reliability and availability | Must | BR-012 | BO-002 |

## 5. Backward matrix: US → FR → BR

| User story | Legacy ID | Role | Priority | FR | Source BR |
|---|---|---|---|---|---|
| US-001 | US-01 | Find a place in my city by its Vietnamese or English name | Must | FR-001, FR-002 | BR-001 |
| US-002 | US-01 | See where each fact about a place comes from and how current it is | Must | FR-003, FR-005, FR-006, FR-007, FR-008 | BR-001, BR-003, BR-024, BR-025, BR-047 |
| US-003 | US-01 | See only reviewed places | Must | FR-004 | BR-002 |
| US-004 | US-00 | Import candidate places without affecting the live catalog | Must | FR-009, FR-010 | BR-004 |
| US-005 | US-00 | Complete a candidate's bilingual content and sourced facts | Must | FR-011, FR-012, FR-016, FR-083 | BR-004, BR-047 |
| US-006 | US-00 | Publish a place only when it is complete | Must | FR-013, FR-014, FR-015, FR-082 | BR-004 |
| US-007 | — | Withdraw a place I published by mistake | Should | FR-017 | BR-002 |
| US-008 | — | See how many places each city has | Should | FR-018 | BR-004 |
| US-009 | — | Use AI drafts but review them before publishing | Should | FR-019, FR-084 | BR-004 |
| US-010 | US-02 | Describe my trip in my own words or with a form | Must | FR-020, FR-021 | BR-005 |
| US-011 | — | Reuse my saved preferences | Should | FR-073, FR-096 | BR-005 |
| US-012 | US-02 | Be asked for missing trip details | Must | FR-022 | BR-005 |
| US-013 | US-02 | Receive a proposal made only of reviewed places in my city | Must | FR-024, FR-025, FR-026, FR-087 | BR-005, BR-006 |
| US-014 | US-03 | See each day as a timeline and on a map with real travel legs | Must | FR-027, FR-028, FR-029, FR-088 | BR-007, BR-026 |
| US-015 | US-03 | See whether my day fits and what blocks it | Must | FR-030, FR-031, FR-032 | BR-008, BR-009 |
| US-016 | US-05 | Reorder the stops of a day | Must | FR-033, FR-039, FR-089 | BR-010, BR-032 |
| US-017 | US-05 | Adjust visit durations and travel modes | Must | FR-037, FR-038, FR-039, FR-089 | BR-030, BR-031, BR-032 |
| US-018 | US-05 | Decide which version becomes my saved trip | Must | FR-040, FR-041, FR-045, FR-090 | BR-011 |
| US-019 | US-05 | Never lose my saved trip or my edits when something fails | Must | FR-042, FR-043, FR-044 | BR-012, BR-033 |
| US-020 | — | Delete a trip I no longer need | Should | FR-046 | BR-011 |
| US-021 | US-04 | Lock a must-see stop (HA-02) | Should | FR-047, FR-091 | BR-034 |
| US-022 | US-06 | Show a driver where I am going and find the entrance | Must | FR-051, FR-052, FR-053 | BR-014, BR-036, BR-037 |
| US-023 | US-06 | Open directions to a stop in my maps app | Must | FR-054 | BR-036 |
| US-024 | — | See today's stops at a glance | Should | FR-055 | BR-014 |
| US-025 | US-07 | Ask a question about a place and see the sources of the answer | Must | FR-056, FR-058, FR-078 | BR-015, BR-048 |
| US-026 | US-07 | Be told when Gonarra does not know | Must | FR-057 | BR-038 |
| US-027 | — | Ask a question by speaking | Should | FR-059, FR-063 | BR-016 |
| US-028 | — | Identify the place in front of me from a photo | Should | FR-061, FR-062, FR-092, FR-093 | BR-017, BR-040 |
| US-029 | — | Look for a stay for my trip on a booking site | Must | FR-064 | BR-018 |
| US-030 | — | Look for activities at a stop on a booking site | Must | FR-065 | BR-041 |
| US-031 | — | See indicative stay prices while planning | Could | FR-066, FR-067, FR-080, FR-081 | BR-019, BR-043, BR-049 |
| US-032 | US-08 | Keep my trips private to my account | Must | FR-068, FR-069, FR-094, FR-095 | BR-020 |
| US-033 | US-08 | Delete my account and see when it is done | Must | FR-071, FR-072 | BR-021, BR-044 |
| US-034 | — | Use the whole app in Vietnamese or English | Must | FR-075, FR-076, FR-097 | BR-022 |
| US-035 | — | Know what is sent to the AI service | Must | FR-070, FR-074 | BR-046 |
| US-036 | — | Have my session measured without my identity or questions | Should | FR-077 | BR-023, BR-045 |
| US-037 | — | Look for transport to my trip's city on a booking site | Must | FR-079 | BR-042 |
| US-038 | US-02 | Be told clearly when a request is unsupported | Must | FR-023, FR-085, FR-086 | BR-005 |
| US-039 | US-05 | Add a place to a day | Must | FR-034, FR-039, FR-089 | BR-027, BR-032 |
| US-040 | US-05 | Remove a stop from a day | Must | FR-035, FR-039, FR-089 | BR-028, BR-032 |
| US-041 | US-05 | Replace a stop with another place | Must | FR-036, FR-039, FR-089 | BR-029, BR-032 |
| US-042 | US-04 | Regenerate one day while keeping locked stops (HA-02) | Should | FR-048, FR-049, FR-050 | BR-013, BR-035 |
| US-043 | — | Hear a Guide answer read aloud | Should | FR-060 | BR-039 |

## 6. Counts by objective

| Objective | BRs | FRs | NFRs | User stories |
|---|---|---|---|---|
| BO-001 | 9 | 23 | 10 | 12 |
| BO-002 | 17 | 28 | 6 | 12 |
| BO-003 | 15 | 23 | 2 | 12 |
| BO-004 | 7 | 22 | 12 | 9 |
| BO-005 | 2 | 1 | 8 | 1 |
| **Total (distinct)** | **50** | **97** | **38** | **43** |

## 7. Legacy ID mapping

| Legacy ID | New IDs |
|---|---|
| FR-00 | FR-004, FR-009, FR-010, FR-011, FR-012, FR-013, FR-082, FR-014, FR-015, FR-016, FR-083, FR-017, FR-018, FR-019, FR-084 |
| FR-01 | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-076 |
| FR-02 | FR-020, FR-021, FR-022, FR-023, FR-085, FR-086, FR-024, FR-025, FR-087, FR-026 |
| FR-03 | FR-027, FR-028, FR-088, FR-029, FR-030, FR-031, FR-032 |
| FR-04 | FR-033, FR-034, FR-035, FR-036, FR-037, FR-038, FR-039, FR-089, FR-047, FR-091, FR-048, FR-049, FR-050 |
| FR-05 | FR-040, FR-090, FR-041, FR-042, FR-043, FR-044, FR-045, FR-046, FR-054, FR-055 |
| FR-06 | FR-051, FR-052, FR-053, FR-054, FR-056, FR-078, FR-057, FR-058, FR-076 |
| FR-07 | FR-068, FR-094, FR-069, FR-095, FR-070, FR-071, FR-072, FR-073, FR-096, FR-075, FR-097 |
| US-00 | US-004, US-005, US-006 |
| US-01 | US-001, US-002, US-003 |
| US-02 | US-010, US-012, US-013, US-038 |
| US-03 | US-014, US-015 |
| US-04 | US-021, US-042 |
| US-05 | US-016, US-017, US-018, US-019, US-039, US-040, US-041 |
| US-06 | US-022, US-023 |
| US-07 | US-025, US-026 |
| US-08 | US-032, US-033 |
| HA-02 | PRD §11.2 (FR-001, FR-020..FR-054, FR-064, FR-079); US-021, US-042 |
| UC-00..UC-06 | Re-specified in Phase 4 `04-design/use-cases.md`; mapped through US legacy column |

## 8. [ORPHAN] list

None.
