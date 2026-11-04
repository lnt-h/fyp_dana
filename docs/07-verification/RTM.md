# Requirements Traceability Matrix — Gonarra (BR → FR/NFR → US/AC → UC → API → TC)

## Document control

| Field | Value |
|---|---|
| Document ID | GONARRA-RTM |
| Version | 0.1 |
| Status | Draft |
| Owner | Lê Ngọc Tấn Hiền, student author and test lead |
| Approver | trantrongminh, FYP mentor (OQ-001) — [Pending] |
| Date | 2026-11-04 |
| Tested commit | TBD per release (no case executed yet) |
| Tested environment | TBD per run: local Docker, GitHub Actions CI, AWS staging, physical devices |
| Prompt used | `verification/TestCase_RTM_IEEE_829_Prompt.md` v2.0, adapted copy `docs/00-governance/prompt-templates/verification/TestCase_RTM_IEEE_829_Prompt.md` (kit commit `6996dae`) |
| Sources | `BRD.md` 0.4 (BR, AC-0nn), `PRD.md` 0.2 (FR, NFR), `user-stories.md` 0.2 (US-nnn-ACn), `use-cases.md` (UC index), `openapi.yaml` (`x-api-id`, `x-fr`), `TEST_CASES.md` 0.1 (TC-001..TC-265) |

The matrix was generated mechanically from the ID tables of the sources above by a throw-away script (deleted after use, as recorded in `docs/00-governance/template-adaptation-log.md`). Regenerate it whenever a source table or `TEST_CASES.md` changes. Derivation rules: a case covers the criteria, NFRs and FRs named in its **Traces to** field; a user-story criterion also brings the FRs of its story; BRs come from the FR/NFR source column and from BRD `AC-0nn` ↔ `BR-0nn`; UCs come from the UC index (stories and FR ranges); APIs from the case's **API** field. `[ORPHAN]` marks a broken branch (an item with no case, or a case with no criterion). Result is `NOT RUN` for every row at design time; Evidence and Defect stay empty until execution.

## 1. Coverage summary

| Check | Must | Should | Could | Result |
|---|---|---|---|---|
| User-story acceptance criteria (`US-nnn-ACn`) with ≥ 1 case | 93/93 | 30/30 | 4/4 | Pass |
| BRD acceptance criteria (`AC-0nn`) with ≥ 1 case | 40/40 | 7/7 | 3/3 | Pass |
| FRs with ≥ 1 case | 70/70 | 23/23 | 4/4 | Pass |
| NFRs with ≥ 1 case | 31/31 | 7/7 | 0/0 | Pass |
| BRs with ≥ 1 case | 40/40 | 7/7 | 3/3 | Pass |
| Use cases with ≥ 1 case | 15/15 | 6/6 | 1/1 | Pass |
| API operations with ≥ 1 named case (all 42 also run in the schema-wide contract case) | 42/42 | — | — | Pass |
| Cases tracing to a criterion (`US-nnn-ACn`, `AC-0nn` or `NFR-xxx`) | 265/265 | — | — | Pass |
| Cases citing only IDs that exist in the baselines | 265/265 | — | — | Pass |
| **[ORPHAN] for Must** | **0** | — | — | target 0 — Pass |

Cases: 265 in total — P0 168, P1 35, P2 62 (P2 = cuttable Should/Could). By level: Acceptance 60, Contract 3, Integration 127, System/E2E 62, Unit 8, Usability study 5.

## 2. Forward matrix by business requirement (BR → FR/NFR → US/AC → UC → API → TC)

| BR | Priority | BRD AC | FR / NFR | User-story criteria | UC | API | Test cases |
|---|---|---|---|---|---|---|---|
| BR-001 | Must | AC-001 | FR-001, FR-002, FR-003, NFR-001 | US-001-AC1, US-001-AC2, US-001-AC3, US-002-AC1, US-002-AC2, US-002-AC3, US-002-AC4, US-002-AC5 | UC-001 | API-008, API-009, API-010, API-011, API-017 | TC-001, TC-002, TC-003, TC-004, TC-005, TC-006, TC-007, TC-008, TC-011, TC-012, TC-013, TC-014, TC-015, TC-016, TC-061, TC-222 |
| BR-002 | Must | AC-002 | FR-004, FR-017 | US-003-AC1, US-003-AC2, US-007-AC1, US-007-AC2 | UC-001, UC-020 | API-010, API-011, API-018, API-024, API-028, API-033, API-034, API-035, API-036, API-037, API-038, API-039, API-040, API-041, API-042 | TC-009, TC-010, TC-028, TC-029, TC-037, TC-150 |
| BR-003 | Must | AC-003 | FR-005 | US-002-AC1, US-002-AC2, US-002-AC3, US-002-AC4, US-002-AC5 | UC-001 | API-011, API-017 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-012, TC-013, TC-014, TC-015 |
| BR-024 | Must | AC-024 | FR-006 | US-002-AC1, US-002-AC2, US-002-AC3, US-002-AC4, US-002-AC5 | UC-001 | API-011, API-017 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-012, TC-013, TC-014, TC-015 |
| BR-025 | Must | AC-025 | FR-007 | US-002-AC1, US-002-AC2, US-002-AC3, US-002-AC4, US-002-AC5 | UC-001 | API-011, API-017 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-012, TC-013, TC-014, TC-015 |
| BR-004 | Must | AC-004 | FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, FR-082, FR-084, NFR-015, NFR-029 | US-004-AC1, US-004-AC2, US-004-AC3, US-005-AC1, US-005-AC2, US-005-AC3, US-005-AC4, US-006-AC1, US-006-AC2, US-006-AC3, US-006-AC4, US-008-AC1, US-009-AC1, US-009-AC2, US-009-AC3 | UC-017, UC-018, UC-019, UC-021 | API-010, API-033, API-034, API-035, API-036, API-037, API-038, API-039, API-040, API-041, API-042 | TC-017, TC-018, TC-019, TC-020, TC-021, TC-022, TC-023, TC-024, TC-025, TC-026, TC-027, TC-030, TC-031, TC-032, TC-033, TC-034, TC-035, TC-036, TC-037, TC-038, TC-237, TC-251 |
| BR-047 | Must | AC-047 | FR-008, FR-016, FR-083 | US-002-AC1, US-002-AC2, US-002-AC3, US-002-AC4, US-002-AC5, US-005-AC1, US-005-AC2, US-005-AC3, US-005-AC4 | UC-001, UC-018, UC-019 | API-011, API-017, API-034, API-035, API-036, API-041 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-012, TC-013, TC-014, TC-015, TC-020, TC-021, TC-022, TC-023, TC-035 |
| BR-005 | Must | AC-005 | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096, NFR-002, NFR-003, NFR-019, NFR-020, NFR-021 | US-010-AC1, US-010-AC2, US-010-AC3, US-011-AC1, US-011-AC2, US-012-AC1, US-012-AC2, US-012-AC3, US-013-AC1, US-013-AC2, US-013-AC3, US-013-AC4, US-038-AC1, US-038-AC2, US-038-AC3 | UC-002, UC-016 | API-004, API-005, API-009, API-012, API-018, API-019, API-020, API-022, API-032 | TC-039, TC-040, TC-041, TC-042, TC-043, TC-044, TC-045, TC-046, TC-047, TC-048, TC-049, TC-050, TC-051, TC-052, TC-053, TC-054, TC-055, TC-056, TC-057, TC-058, TC-059, TC-060, TC-061, TC-215, TC-221, TC-223, TC-224, TC-241, TC-242, TC-243 |
| BR-006 | Must | AC-006 | FR-025, FR-087 | US-013-AC1, US-013-AC2, US-013-AC3, US-013-AC4 | UC-002 | API-018, API-019 | TC-050, TC-051, TC-052, TC-053, TC-056, TC-057, TC-058, TC-059, TC-060, TC-116, TC-215 |
| BR-007 | Must | AC-007 | FR-027, FR-028, FR-088, NFR-025 | US-014-AC1, US-014-AC2, US-014-AC3, US-014-AC4 | UC-002, UC-015 | API-018, API-019 | TC-062, TC-063, TC-064, TC-065, TC-070, TC-071, TC-113, TC-215, TC-247 |
| BR-026 | Must | AC-026 | FR-029 | US-014-AC1, US-014-AC2, US-014-AC3, US-014-AC4 | UC-002, UC-015 | API-018, API-019 | TC-057, TC-062, TC-063, TC-064, TC-065, TC-070, TC-071, TC-113, TC-215 |
| BR-008 | Must | AC-008 | FR-030, FR-031 | US-015-AC1, US-015-AC2, US-015-AC3, US-015-AC4 | UC-015 | API-018, API-019, API-020, API-022 | TC-066, TC-067, TC-068, TC-069, TC-072, TC-073, TC-074, TC-216, TC-221 |
| BR-009 | Must | AC-009 | FR-032 | US-015-AC1, US-015-AC2, US-015-AC3, US-015-AC4 | UC-004, UC-015 | API-018, API-019, API-020, API-022 | TC-066, TC-067, TC-068, TC-069, TC-072, TC-073, TC-074, TC-216, TC-221 |
| BR-010 | Must | AC-010 | FR-033 | US-016-AC1, US-016-AC2, US-016-AC3, US-016-AC4 | UC-003 | API-014, API-018, API-020, API-022 | TC-075, TC-076, TC-077, TC-078, TC-216, TC-221 |
| BR-027 | Must | AC-027 | FR-034 | US-039-AC1, US-039-AC2, US-039-AC3 | UC-003 | API-010, API-020 | TC-079, TC-080, TC-081 |
| BR-028 | Must | AC-028 | FR-035 | US-040-AC1, US-040-AC2, US-040-AC3 | UC-003 | API-014, API-020, API-022 | TC-082, TC-083, TC-084 |
| BR-029 | Must | AC-029 | FR-036 | US-041-AC1, US-041-AC2, US-041-AC3 | UC-003 | API-010, API-020 | TC-085, TC-086, TC-087, TC-091 |
| BR-030 | Must | AC-030 | FR-037 | US-017-AC1, US-017-AC2, US-017-AC3 | UC-003 | API-020 | TC-088, TC-089, TC-090, TC-092, TC-093 |
| BR-031 | Must | AC-031 | FR-038 | US-017-AC1, US-017-AC2, US-017-AC3 | UC-003 | API-020 | TC-088, TC-089, TC-090, TC-092, TC-093 |
| BR-032 | Must | AC-032 | FR-039, FR-089, NFR-004 | US-016-AC1, US-016-AC2, US-016-AC3, US-016-AC4, US-017-AC1, US-017-AC2, US-017-AC3, US-039-AC1, US-039-AC2, US-039-AC3, US-040-AC1, US-040-AC2, US-040-AC3, US-041-AC1, US-041-AC2, US-041-AC3 | UC-003, UC-015 | API-010, API-014, API-018, API-020, API-022 | TC-075, TC-076, TC-077, TC-078, TC-079, TC-080, TC-081, TC-082, TC-083, TC-084, TC-085, TC-086, TC-087, TC-088, TC-089, TC-090, TC-091, TC-092, TC-093, TC-095, TC-216, TC-221, TC-225 |
| BR-011 | Must | AC-011 | FR-040, FR-041, FR-045, FR-046, FR-090 | US-018-AC1, US-018-AC2, US-018-AC3, US-018-AC4, US-020-AC1, US-020-AC2 | UC-004, UC-006 | API-013, API-014, API-016, API-018, API-019, API-020, API-021, API-022 | TC-096, TC-097, TC-098, TC-099, TC-104, TC-105, TC-106, TC-107, TC-108, TC-109, TC-126, TC-160, TC-216, TC-219, TC-221 |
| BR-012 | Must | AC-012 | FR-042, FR-043, NFR-009, NFR-010, NFR-011, NFR-038 | US-019-AC1, US-019-AC2, US-019-AC3, US-019-AC4 | UC-004 | API-002, API-010, API-014, API-017, API-018, API-019, API-020, API-021, API-022, API-031 | TC-095, TC-100, TC-101, TC-102, TC-103, TC-111, TC-112, TC-113, TC-114, TC-115, TC-116, TC-117, TC-118, TC-119, TC-120, TC-127, TC-185, TC-218, TC-219, TC-230, TC-231, TC-232, TC-233, TC-262, TC-265 |
| BR-033 | Must | AC-033 | FR-044 | US-019-AC1, US-019-AC2, US-019-AC3, US-019-AC4 | UC-004 | API-014, API-018, API-019, API-020, API-021, API-022 | TC-095, TC-100, TC-101, TC-102, TC-103, TC-111, TC-112, TC-114, TC-115, TC-117, TC-118, TC-119, TC-120, TC-218, TC-219 |
| BR-034 | Should | AC-034 | FR-047, FR-091 | US-021-AC1, US-021-AC2, US-021-AC3 | UC-005 | API-014, API-019, API-020, API-021, API-022 | TC-121, TC-122, TC-123, TC-130, TC-217 |
| BR-013 | Should | AC-013 | FR-048, FR-050 | US-042-AC1, US-042-AC2, US-042-AC3, US-042-AC4 | UC-005 | API-014, API-020, API-021 | TC-118, TC-119, TC-120, TC-124, TC-125, TC-126, TC-127, TC-128, TC-129, TC-217 |
| BR-035 | Should | AC-035 | FR-049 | US-042-AC1, US-042-AC2, US-042-AC3, US-042-AC4 | UC-005 | API-014, API-020, API-021 | TC-118, TC-119, TC-120, TC-124, TC-125, TC-126, TC-127, TC-128, TC-129, TC-217 |
| BR-014 | Must | AC-014 | FR-051, FR-055 | US-022-AC1, US-022-AC2, US-022-AC3, US-024-AC1 | UC-007 | API-014, API-017, API-030 | TC-131, TC-132, TC-133, TC-136, TC-137, TC-138, TC-139, TC-220 |
| BR-036 | Must | AC-036 | FR-052, FR-054 | US-022-AC1, US-022-AC2, US-022-AC3, US-023-AC1, US-023-AC2 | UC-007 | API-017, API-030 | TC-131, TC-132, TC-133, TC-134, TC-135, TC-137, TC-138, TC-139, TC-220 |
| BR-037 | Must | AC-037 | FR-053 | US-022-AC1, US-022-AC2, US-022-AC3 | UC-007 | API-017, API-030 | TC-131, TC-132, TC-133, TC-137, TC-138, TC-139, TC-220 |
| BR-015 | Must | AC-015 | FR-056, FR-058, NFR-005, NFR-006 | US-025-AC1, US-025-AC2, US-025-AC3 | UC-008 | API-024, API-027, API-028 | TC-141, TC-142, TC-143, TC-146, TC-147, TC-148, TC-226, TC-227 |
| BR-048 | Must | AC-048 | FR-078 | US-025-AC1, US-025-AC2, US-025-AC3 | UC-008 | API-024, API-027, API-028 | TC-141, TC-142, TC-143, TC-146, TC-147, TC-148 |
| BR-038 | Must | AC-038 | FR-057 | US-026-AC1, US-026-AC2 | UC-008 | API-024, API-027, API-028 | TC-143, TC-144, TC-145, TC-149 |
| BR-016 | Should | AC-016 | FR-059, FR-063 | US-027-AC1, US-027-AC2, US-027-AC3 | UC-009, UC-010 | API-022, API-028 | TC-152, TC-153, TC-154, TC-157, TC-158, TC-159, TC-160, TC-162 |
| BR-039 | Should | AC-039 | FR-060 | US-043-AC1, US-043-AC2 | UC-009 | — | TC-155, TC-156, TC-161 |
| BR-017 | Should | AC-017 | FR-061, FR-092, FR-093 | US-028-AC1, US-028-AC2, US-028-AC3, US-028-AC4 | UC-010 | API-029 | TC-163, TC-164, TC-165, TC-166, TC-167, TC-168, TC-170 |
| BR-040 | Should | AC-040 | FR-062 | US-028-AC1, US-028-AC2, US-028-AC3, US-028-AC4 | UC-010 | API-029 | TC-163, TC-164, TC-165, TC-166, TC-167, TC-168, TC-170 |
| BR-018 | Must | AC-018 | FR-064 | US-029-AC1, US-029-AC2 | UC-011 | API-017, API-030 | TC-171, TC-172, TC-175, TC-179, TC-220 |
| BR-041 | Must | AC-041 | FR-065 | US-030-AC1 | UC-011 | API-030 | TC-173, TC-177 |
| BR-042 | Must | AC-042 | FR-079 | US-037-AC1 | UC-011 | API-017, API-030 | TC-174, TC-176, TC-220 |
| BR-019 | Could | AC-019 | FR-066 | US-031-AC1, US-031-AC2, US-031-AC3, US-031-AC4 | UC-012 | API-014, API-022, API-031 | TC-180, TC-181, TC-182, TC-183, TC-184, TC-185, TC-186 |
| BR-043 | Could | AC-043 | FR-067, FR-081 | US-031-AC1, US-031-AC2, US-031-AC3, US-031-AC4 | UC-012 | API-014, API-022, API-031 | TC-180, TC-181, TC-182, TC-183, TC-184, TC-185, TC-186 |
| BR-049 | Could | AC-049 | FR-080 | US-031-AC1, US-031-AC2, US-031-AC3, US-031-AC4 | UC-012 | API-014, API-022, API-031 | TC-180, TC-181, TC-182, TC-183, TC-184, TC-185, TC-186 |
| BR-020 | Must | AC-020 | FR-068, FR-069, FR-094, FR-095, NFR-012, NFR-013, NFR-014, NFR-016 | US-032-AC1, US-032-AC2, US-032-AC3, US-032-AC4 | UC-013 | API-001, API-003, API-004, API-007, API-013, API-014, API-015, API-016, API-017, API-019, API-020, API-021, API-022, API-023, API-025, API-026, API-027, API-028, API-030, API-031 | TC-094, TC-110, TC-140, TC-151, TC-178, TC-187, TC-188, TC-189, TC-190, TC-197, TC-203, TC-234, TC-235, TC-236, TC-238, TC-260, TC-264 |
| BR-046 | Must | AC-046 | FR-070, FR-074, NFR-017 | US-035-AC1, US-035-AC2 | UC-002, UC-008, UC-010 | API-001, API-018, API-028, API-029 | TC-159, TC-169, TC-195, TC-196, TC-198, TC-199, TC-239, TC-263 |
| BR-021 | Must | AC-021 | FR-071 | US-033-AC1, US-033-AC2, US-033-AC3, US-033-AC4 | UC-014 | API-006, API-007 | TC-191, TC-192, TC-193, TC-194, TC-200, TC-201, TC-202 |
| BR-044 | Must | AC-044 | FR-072 | US-033-AC1, US-033-AC2, US-033-AC3, US-033-AC4 | UC-014 | API-006, API-007 | TC-191, TC-192, TC-193, TC-194, TC-200, TC-201, TC-202 |
| BR-022 | Must | AC-022 | FR-075, FR-076, FR-097, NFR-022, NFR-023, NFR-024, NFR-026 | US-034-AC1, US-034-AC2, US-034-AC3 | UC-016 | API-008, API-011, API-018, API-019 | TC-204, TC-205, TC-206, TC-207, TC-208, TC-209, TC-215, TC-244, TC-245, TC-246, TC-248 |
| BR-023 | Must | AC-023 | FR-077, NFR-007, NFR-008, NFR-018, NFR-027, NFR-028, NFR-030, NFR-031, NFR-032 | US-036-AC1, US-036-AC2, US-036-AC3 | UC-022 | API-001, API-002, API-006, API-010, API-018, API-019, API-020, API-021, API-028, API-032 | TC-074, TC-202, TC-210, TC-211, TC-212, TC-213, TC-214, TC-228, TC-229, TC-240, TC-249, TC-250, TC-252, TC-253, TC-254, TC-260, TC-261, TC-262 |
| BR-050 | Must | AC-050 | NFR-033, NFR-034, NFR-035, NFR-036, NFR-037 | — | — | API-018, API-028 | TC-255, TC-256, TC-257, TC-258, TC-259 |
| BR-045 | Must | AC-045 | FR-077 | US-036-AC1, US-036-AC2, US-036-AC3 | UC-022 | API-032 | TC-210, TC-211, TC-212, TC-213, TC-214 |

## 3. Criterion → test case matrix (kit §7.2 columns, one row per case)

Columns follow the kit (§7.2) with BR, UC and API added. AC text is shortened to 90 characters; full text is in the source documents.

### 3.1 User-story acceptance criteria

| Acceptance criterion | Requirement | Story | BR | UC | API | Test case | Result | Evidence | Defect | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| US-001-AC1 Given I selected Huế, when I search "Đại Nội", then the published place appears in the fi… | FR-001, FR-002 | US-001 | BR-001 | UC-001 | API-008, API-010 | TC-001 | NOT RUN | | |  |
| US-001-AC1 Given I selected Huế, when I search "Đại Nội", then the published place appears in the fi… | FR-001, FR-002 | US-001 | BR-001 | UC-001 | API-010 | TC-011 | NOT RUN | | |  |
| US-001-AC2 Given I selected Huế, when I search "Imperial City" or "Dai Noi" (no diacritics), then th… | FR-001, FR-002 | US-001 | BR-001 | UC-001 | API-008, API-010 | TC-002 | NOT RUN | | |  |
| US-001-AC2 Given I selected Huế, when I search "Imperial City" or "Dai Noi" (no diacritics), then th… | FR-001, FR-002 | US-001 | BR-001 | UC-001 | API-010 | TC-011 | NOT RUN | | |  |
| US-001-AC3 Given I selected Hội An, when I search a place that exists only in Huế, then it does not… | FR-001, FR-002 | US-001 | BR-001 | UC-001 | API-008, API-010 | TC-003 | NOT RUN | | |  |
| US-001-AC3 Given I selected Hội An, when I search a place that exists only in Huế, then it does not… | FR-001, FR-002 | US-001 | BR-001 | UC-001 | API-010 | TC-016 | NOT RUN | | |  |
| US-002-AC1 Given a published place, when I open its details, then I see both names, a description in… | FR-003, FR-005, FR-006, FR-007, FR-008 | US-002 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 | TC-004 | NOT RUN | | |  |
| US-002-AC2 Given its opening hours are known, when I view them, then the source name and verificatio… | FR-003, FR-005, FR-006, FR-007, FR-008 | US-002 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 | TC-005 | NOT RUN | | |  |
| US-002-AC2 Given its opening hours are known, when I view them, then the source name and verificatio… | FR-003, FR-005, FR-006, FR-007, FR-008 | US-002 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 | TC-013 | NOT RUN | | |  |
| US-002-AC3 Given a fact has no supported value, when I view it, then it reads "unknown", not blank o… | FR-003, FR-005, FR-006, FR-007, FR-008 | US-002 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 | TC-006 | NOT RUN | | |  |
| US-002-AC3 Given a fact has no supported value, when I view it, then it reads "unknown", not blank o… | FR-003, FR-005, FR-006, FR-007, FR-008 | US-002 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 | TC-014 | NOT RUN | | |  |
| US-002-AC4 Given a fact was verified 181 days ago, when I view it, then it is labelled stale. | FR-003, FR-005, FR-006, FR-007, FR-008 | US-002 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 | TC-007 | NOT RUN | | |  |
| US-002-AC4 Given a fact was verified 181 days ago, when I view it, then it is labelled stale. | FR-003, FR-005, FR-006, FR-007, FR-008 | US-002 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 | TC-012 | NOT RUN | | |  |
| US-002-AC5 Given the place uses open-data content, when I view the details, then the required attrib… | FR-003, FR-005, FR-006, FR-007, FR-008 | US-002 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 | TC-008 | NOT RUN | | |  |
| US-002-AC5 Given the place uses open-data content, when I view the details, then the required attrib… | FR-003, FR-005, FR-006, FR-007, FR-008 | US-002 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011, API-017 | TC-015 | NOT RUN | | |  |
| US-003-AC1 Given 10 candidate places exist, when I search, plan or ask the Guide, then none of them… | FR-004 | US-003 | BR-002 | UC-001 | API-010, API-018, API-028 | TC-009 | NOT RUN | | |  |
| US-003-AC1 Given 10 candidate places exist, when I search, plan or ask the Guide, then none of them… | FR-004 | US-003 | BR-002 | UC-001 | API-024 | TC-150 | NOT RUN | | |  |
| US-003-AC2 Given a candidate's identifier, when the app requests its details, then "not found" is re… | FR-004 | US-003 | BR-002 | UC-001 | API-010, API-011 | TC-010 | NOT RUN | | |  |
| US-004-AC1 Given a named release for Hội An, when I import it, then candidates appear tagged with th… | FR-009, FR-010 | US-004 | BR-004 | UC-017 | API-038, API-039, API-033 | TC-017 | NOT RUN | | |  |
| US-004-AC2 Given the import completed, when a traveler searches, then the published results are unch… | FR-009, FR-010 | US-004 | BR-004 | UC-017 | API-038, API-039, API-033 | TC-018 | NOT RUN | | |  |
| US-004-AC3 Given I import the same release again, when it completes, then the candidate count is unc… | FR-009, FR-010 | US-004 | BR-004 | UC-017 | API-038, API-039, API-033 | TC-019 | NOT RUN | | |  |
| US-004-AC3 Given I import the same release again, when it completes, then the candidate count is unc… | FR-009, FR-010 | US-004 | BR-004 | UC-017 | API-039 | TC-038 | NOT RUN | | |  |
| US-005-AC1 Given a candidate, when I enter names and descriptions in both languages and reload, then… | FR-011, FR-012, FR-016, FR-083 | US-005 | BR-004, BR-047 | UC-018, UC-019 | API-034, API-035, API-041 | TC-020 | NOT RUN | | |  |
| US-005-AC2 Given a candidate, when I record opening hours with a source and verification date, then… | FR-011, FR-012, FR-016, FR-083 | US-005 | BR-004, BR-047 | UC-018, UC-019 | API-034, API-035, API-041 | TC-021 | NOT RUN | | |  |
| US-005-AC3 Given an entrance is not verified, when I record it as "unknown" with a source, then it i… | FR-011, FR-012, FR-016, FR-083 | US-005 | BR-004, BR-047 | UC-018, UC-019 | API-034, API-035, API-041 | TC-022 | NOT RUN | | |  |
| US-005-AC4 Given a source, when I record its licence and attribution text, then the text is availabl… | FR-011, FR-012, FR-016, FR-083 | US-005 | BR-004, BR-047 | UC-018, UC-019 | API-034, API-035, API-041 | TC-023 | NOT RUN | | |  |
| US-005-AC4 Given a source, when I record its licence and attribution text, then the text is availabl… | FR-011, FR-012, FR-016, FR-083 | US-005 | BR-004, BR-047 | UC-018, UC-019 | API-036, API-041 | TC-035 | NOT RUN | | |  |
| US-006-AC1 Given a candidate lacks English content, when I publish, then it is refused and the missi… | FR-013, FR-014, FR-015, FR-082 | US-006 | BR-004 | UC-019 | API-036 | TC-024 | NOT RUN | | |  |
| US-006-AC1 Given a candidate lacks English content, when I publish, then it is refused and the missi… | FR-013, FR-014, FR-015, FR-082 | US-006 | BR-004 | UC-019 | API-036 | TC-034 | NOT RUN | | |  |
| US-006-AC2 Given a candidate has a fact without a source, when I publish, then it is refused and the… | FR-013, FR-014, FR-015, FR-082 | US-006 | BR-004 | UC-019 | API-036 | TC-025 | NOT RUN | | |  |
| US-006-AC3 Given a complete candidate, when I publish it from the curator tool, then a traveler can… | FR-013, FR-014, FR-015, FR-082 | US-006 | BR-004 | UC-019 | API-036, API-010 | TC-026 | NOT RUN | | |  |
| US-006-AC3 Given a complete candidate, when I publish it from the curator tool, then a traveler can… | FR-013, FR-014, FR-015, FR-082 | US-006 | BR-004 | UC-019 | API-036 | TC-036 | NOT RUN | | |  |
| US-006-AC3 Given a complete candidate, when I publish it from the curator tool, then a traveler can… | FR-013, FR-014, FR-015, FR-082 | US-006 | BR-004 | UC-019 | API-033, API-034, API-035, API-036, API-037, API-038, API-039, API-040, API-041, API-042 | TC-037 | NOT RUN | | |  |
| US-006-AC4 Given I published a place, when I view it in the curator tool, then my name and the publi… | FR-013, FR-014, FR-015, FR-082 | US-006 | BR-004 | UC-019 | API-034 | TC-027 | NOT RUN | | |  |
| US-007-AC1 Given a published place, when I unpublish it, then it no longer appears in new searches,… | FR-017 | US-007 | BR-002 | UC-020 | API-037 | TC-028 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-007-AC2 Given it was unpublished, when I view the candidate list, then it is there for correction. | FR-017 | US-007 | BR-002 | UC-020 | API-037 | TC-029 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-008-AC1 Given places are published in five cities, when I open the coverage view, then each city'… | FR-018 | US-008 | BR-004 | UC-021 | API-042 | TC-030 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-009-AC1 Given a field drafted by AI, when I view it, then it is marked "AI draft". | FR-019, FR-084 | US-009 | BR-004 | UC-018 | API-034, API-035, API-036 | TC-031 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-009-AC2 Given any AI-draft field is unconfirmed, when I publish, then publication is refused. | FR-019, FR-084 | US-009 | BR-004 | UC-018 | API-034, API-035, API-036 | TC-032 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-009-AC3 Given I confirm every drafted field, when I publish, then it succeeds. | FR-019, FR-084 | US-009 | BR-004 | UC-018 | API-034, API-035, API-036 | TC-033 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-010-AC1 Given English is selected, when Tom writes "2 relaxed days in Hội An, old town and food",… | FR-020, FR-021 | US-010 | BR-005 | UC-002 | API-012, API-018 | TC-039 | NOT RUN | | |  |
| US-010-AC1 Given English is selected, when Tom writes "2 relaxed days in Hội An, old town and food",… | FR-020, FR-021 | US-010 | BR-005 | UC-002 | API-018, API-020, API-022 | TC-221 | NOT RUN | | |  |
| US-010-AC2 Given Vietnamese is selected, when Linh writes "2 ngày ở Huế, thích di tích", then the re… | FR-020, FR-021 | US-010 | BR-005 | UC-002 | API-012, API-018 | TC-040 | NOT RUN | | |  |
| US-010-AC2 Given Vietnamese is selected, when Linh writes "2 ngày ở Huế, thích di tích", then the re… | FR-020, FR-021 | US-010 | BR-005 | UC-002 | API-018, API-019 | TC-215 | NOT RUN | | |  |
| US-010-AC3 Given I do not want to type, when I fill in city, start date, days, daily hours, pace, in… | FR-020, FR-021 | US-010 | BR-005 | UC-002 | API-012, API-018 | TC-041 | NOT RUN | | |  |
| US-010-AC3 Given I do not want to type, when I fill in city, start date, days, daily hours, pace, in… | FR-020, FR-021 | US-010 | BR-005 | UC-002 | API-009 | TC-061 | NOT RUN | | |  |
| US-011-AC1 Given I saved pace "relaxed" and interest "food", when I start a new request, then the fo… | FR-073, FR-096 | US-011 | BR-005 | UC-016 | API-004, API-005 | TC-042 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-011-AC2 Given I did not choose to save, when I finish a request, then no preferences are stored. | FR-073, FR-096 | US-011 | BR-005 | UC-016 | API-004, API-005 | TC-043 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-012-AC1 Given my request has no start date, when I submit it, then I am asked for the start date… | FR-022 | US-012 | BR-005 | UC-002 | API-018 | TC-044 | NOT RUN | | |  |
| US-012-AC1 Given my request has no start date, when I submit it, then I am asked for the start date… | FR-022 | US-012 | BR-005 | UC-002 | API-018 | TC-058 | NOT RUN | | |  |
| US-012-AC2 Given my request names no city, when I submit it, then I am asked for the city. | FR-022 | US-012 | BR-005 | UC-002 | API-018 | TC-045 | NOT RUN | | |  |
| US-012-AC3 Given "a few days" instead of a number of days, when I submit, then I am asked for 1, 2 o… | FR-022 | US-012 | BR-005 | UC-002 | API-018 | TC-046 | NOT RUN | | |  |
| US-038-AC1 Given I ask for 4 days, when I submit, then I am told trips are 1–3 days. | FR-023, FR-085, FR-086 | US-038 | BR-005 | UC-002 | API-012, API-018 | TC-047 | NOT RUN | | |  |
| US-038-AC1 Given I ask for 4 days, when I submit, then I am told trips are 1–3 days. | FR-023, FR-085, FR-086 | US-038 | BR-005 | UC-002 | API-012, API-018 | TC-054 | NOT RUN | | |  |
| US-038-AC2 Given I ask for Huế and Hội An together, when I submit, then I am told a trip covers one… | FR-023, FR-085, FR-086 | US-038 | BR-005 | UC-002 | API-012, API-018 | TC-048 | NOT RUN | | |  |
| US-038-AC2 Given I ask for Huế and Hội An together, when I submit, then I am told a trip covers one… | FR-023, FR-085, FR-086 | US-038 | BR-005 | UC-002 | API-018 | TC-055 | NOT RUN | | |  |
| US-038-AC3 Given I ask for Nha Trang, when I submit, then I am told the five supported cities. | FR-023, FR-085, FR-086 | US-038 | BR-005 | UC-002 | API-012, API-018 | TC-049 | NOT RUN | | |  |
| US-038-AC3 Given I ask for Nha Trang, when I submit, then I am told the five supported cities. | FR-023, FR-085, FR-086 | US-038 | BR-005 | UC-002 | API-018 | TC-055 | NOT RUN | | |  |
| US-013-AC1 Given a complete request for 2 days in Hội An, when the proposal appears, then it has exa… | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018, API-019 | TC-050 | NOT RUN | | |  |
| US-013-AC1 Given a complete request for 2 days in Hội An, when the proposal appears, then it has exa… | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018 | TC-058 | NOT RUN | | |  |
| US-013-AC1 Given a complete request for 2 days in Hội An, when the proposal appears, then it has exa… | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018, API-019 | TC-215 | NOT RUN | | |  |
| US-013-AC2 Given the proposal, when I inspect every stop, then each is a published Hội An place. | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018, API-019 | TC-051 | NOT RUN | | |  |
| US-013-AC2 Given the proposal, when I inspect every stop, then each is a published Hội An place. | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018, API-019 | TC-059 | NOT RUN | | |  |
| US-013-AC3 Given the generator returned an unknown or other-city place, when the proposal is shown,… | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018, API-019 | TC-052 | NOT RUN | | |  |
| US-013-AC3 Given the generator returned an unknown or other-city place, when the proposal is shown,… | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018 | TC-056 | NOT RUN | | |  |
| US-013-AC3 Given the generator returned an unknown or other-city place, when the proposal is shown,… | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018 | TC-057 | NOT RUN | | |  |
| US-013-AC3 Given the generator returned an unknown or other-city place, when the proposal is shown,… | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018, API-019 | TC-059 | NOT RUN | | |  |
| US-013-AC4 Given I marked a must-see, when the proposal appears, then it contains the must-see or st… | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018, API-019 | TC-053 | NOT RUN | | |  |
| US-013-AC4 Given I marked a must-see, when the proposal appears, then it contains the must-see or st… | FR-024, FR-025, FR-026, FR-087 | US-013 | BR-005, BR-006 | UC-002 | API-018 | TC-060 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-014-AC1 Given a proposal, when I open day 1, then stops are in order with arrival and departure t… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 | TC-062 | NOT RUN | | |  |
| US-014-AC1 Given a proposal, when I open day 1, then stops are in order with arrival and departure t… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-019 | TC-070 | NOT RUN | | |  |
| US-014-AC1 Given a proposal, when I open day 1, then stops are in order with arrival and departure t… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 | TC-215 | NOT RUN | | |  |
| US-014-AC2 Given I tap a stop on the map, when the timeline is shown, then the same stop is selected… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 | TC-063 | NOT RUN | | |  |
| US-014-AC2 Given I tap a stop on the map, when the timeline is shown, then the same stop is selected… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 | TC-215 | NOT RUN | | |  |
| US-014-AC3 Given a leg, when I view it, then it shows walk or drive, distance and duration from the… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 | TC-064 | NOT RUN | | |  |
| US-014-AC3 Given a leg, when I view it, then it shows walk or drive, distance and duration from the… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-019 | TC-071 | NOT RUN | | |  |
| US-014-AC4 Given the routing provider has no route for a leg, when I view it, then it reads "unavail… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 | TC-065 | NOT RUN | | |  |
| US-014-AC4 Given the routing provider has no route for a leg, when I view it, then it reads "unavail… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-019 | TC-071 | NOT RUN | | |  |
| US-014-AC4 Given the routing provider has no route for a leg, when I view it, then it reads "unavail… | FR-027, FR-028, FR-029, FR-088 | US-014 | BR-007, BR-026 | UC-002, UC-015 | API-018 | TC-113 | NOT RUN | | |  |
| US-015-AC1 Given a museum is planned when it is closed, when I view the day, then the stop is flagge… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-019, API-022 | TC-066 | NOT RUN | | |  |
| US-015-AC1 Given a museum is planned when it is closed, when I view the day, then the stop is flagge… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-019 | TC-072 | NOT RUN | | |  |
| US-015-AC1 Given a museum is planned when it is closed, when I view the day, then the stop is flagge… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-018, API-020, API-022 | TC-221 | NOT RUN | | |  |
| US-015-AC2 Given the last stop ends after my day window, when I view the day, then the day is flagge… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-019, API-022 | TC-067 | NOT RUN | | |  |
| US-015-AC2 Given the last stop ends after my day window, when I view the day, then the day is flagge… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-019 | TC-072 | NOT RUN | | |  |
| US-015-AC3 Given at least one blocking conflict, when I view the proposal, then Plan Health is "bloc… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-019, API-022 | TC-068 | NOT RUN | | |  |
| US-015-AC3 Given at least one blocking conflict, when I view the proposal, then Plan Health is "bloc… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-019 | TC-072 | NOT RUN | | |  |
| US-015-AC3 Given at least one blocking conflict, when I view the proposal, then Plan Health is "bloc… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-019 | TC-074 | NOT RUN | | |  |
| US-015-AC4 Given the proposal is blocked, when I tap Save, then saving is refused and the reason is… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-022 | TC-069 | NOT RUN | | |  |
| US-015-AC4 Given the proposal is blocked, when I tap Save, then saving is refused and the reason is… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-022 | TC-073 | NOT RUN | | |  |
| US-015-AC4 Given the proposal is blocked, when I tap Save, then saving is refused and the reason is… | FR-030, FR-031, FR-032 | US-015 | BR-008, BR-009 | UC-004, UC-015 | API-020, API-022 | TC-216 | NOT RUN | | |  |
| US-016-AC1 Given day 1, when I move stop 3 to position 1, then the new order and recalculated times… | FR-033, FR-039, FR-089 | US-016 | BR-010, BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-075 | NOT RUN | | |  |
| US-016-AC1 Given day 1, when I move stop 3 to position 1, then the new order and recalculated times… | FR-033, FR-039, FR-089 | US-016 | BR-010, BR-032 | UC-003, UC-015 | API-018, API-020, API-022 | TC-221 | NOT RUN | | |  |
| US-016-AC2 Given the move, when recalculation is running, then Save is unavailable. | FR-033, FR-039, FR-089 | US-016 | BR-010, BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-076 | NOT RUN | | |  |
| US-016-AC3 Given the new order creates a blocking conflict, when recalculation completes, then the c… | FR-033, FR-039, FR-089 | US-016 | BR-010, BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-077 | NOT RUN | | |  |
| US-016-AC4 Given I save, when I reopen the trip, then the new order is shown. | FR-033, FR-039, FR-089 | US-016 | BR-010, BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-078 | NOT RUN | | |  |
| US-016-AC4 Given I save, when I reopen the trip, then the new order is shown. | FR-033, FR-039, FR-089 | US-016 | BR-010, BR-032 | UC-003, UC-015 | API-020, API-022 | TC-216 | NOT RUN | | |  |
| US-039-AC1 Given a published Hội An place, when I add it to day 2 of a Hội An trip, then it is inser… | FR-034, FR-039, FR-089 | US-039 | BR-027, BR-032 | UC-003, UC-015 | API-020, API-010 | TC-079 | NOT RUN | | |  |
| US-039-AC2 Given a Huế place, when I try to add it to a Hội An trip, then it is refused. | FR-034, FR-039, FR-089 | US-039 | BR-027, BR-032 | UC-003, UC-015 | API-020, API-010 | TC-080 | NOT RUN | | |  |
| US-039-AC3 Given the addition, when recalculation is running, then Save is unavailable. | FR-034, FR-039, FR-089 | US-039 | BR-027, BR-032 | UC-003, UC-015 | API-020, API-010 | TC-081 | NOT RUN | | |  |
| US-040-AC1 Given a stop, when I remove it, then the stop and its legs disappear and times are recalc… | FR-035, FR-039, FR-089 | US-040 | BR-028, BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-082 | NOT RUN | | |  |
| US-040-AC2 Given the removal, when recalculation is running, then Save is unavailable. | FR-035, FR-039, FR-089 | US-040 | BR-028, BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-083 | NOT RUN | | |  |
| US-040-AC3 Given I save, when I reopen the trip, then the stop is absent. | FR-035, FR-039, FR-089 | US-040 | BR-028, BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-084 | NOT RUN | | |  |
| US-041-AC1 Given a stop, when I choose Replace, then only published places of the trip's city are of… | FR-036, FR-039, FR-089 | US-041 | BR-029, BR-032 | UC-003, UC-015 | API-010 | TC-085 | NOT RUN | | |  |
| US-041-AC2 Given I pick a replacement, when recalculation completes, then times and legs reflect it… | FR-036, FR-039, FR-089 | US-041 | BR-029, BR-032 | UC-003, UC-015 | API-020, API-010 | TC-086 | NOT RUN | | |  |
| US-041-AC2 Given I pick a replacement, when recalculation completes, then times and legs reflect it… | FR-036, FR-039, FR-089 | US-041 | BR-029, BR-032 | UC-003, UC-015 | API-020 | TC-091 | NOT RUN | | |  |
| US-041-AC3 Given I save, when I reopen the trip, then the replacement is shown. | FR-036, FR-039, FR-089 | US-041 | BR-029, BR-032 | UC-003, UC-015 | API-020, API-010 | TC-087 | NOT RUN | | |  |
| US-017-AC1 Given a stop of 60 min, when I set 90 min, then its departure and all later times on that… | FR-037, FR-038, FR-039, FR-089 | US-017 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 | TC-088 | NOT RUN | | |  |
| US-017-AC1 Given a stop of 60 min, when I set 90 min, then its departure and all later times on that… | FR-037, FR-038, FR-039, FR-089 | US-017 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 | TC-092 | NOT RUN | | |  |
| US-017-AC2 Given a walking leg, when I switch it to driving, then its distance and duration update a… | FR-037, FR-038, FR-039, FR-089 | US-017 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 | TC-089 | NOT RUN | | |  |
| US-017-AC2 Given a walking leg, when I switch it to driving, then its distance and duration update a… | FR-037, FR-038, FR-039, FR-089 | US-017 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 | TC-093 | NOT RUN | | |  |
| US-017-AC3 Given either change creates a blocking conflict, when recalculation completes, then the c… | FR-037, FR-038, FR-039, FR-089 | US-017 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 | TC-090 | NOT RUN | | |  |
| US-018-AC1 Given a new proposal, when I view it, then it is labelled unsaved. | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-019 | TC-096 | NOT RUN | | |  |
| US-018-AC1 Given a new proposal, when I view it, then it is labelled unsaved. | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-019, API-022 | TC-109 | NOT RUN | | |  |
| US-018-AC1 Given a new proposal, when I view it, then it is labelled unsaved. | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-018, API-020, API-022 | TC-221 | NOT RUN | | |  |
| US-018-AC2 Given I leave the screen before Save, when I reopen my trip, then the previous saved vers… | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-014 | TC-097 | NOT RUN | | |  |
| US-018-AC2 Given I leave the screen before Save, when I reopen my trip, then the previous saved vers… | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-014 | TC-107 | NOT RUN | | |  |
| US-018-AC2 Given I leave the screen before Save, when I reopen my trip, then the previous saved vers… | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-018, API-014 | TC-108 | NOT RUN | | |  |
| US-018-AC3 Given I tap Save and the request is retried, when I reopen the trip, then exactly one new… | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-022, API-014 | TC-098 | NOT RUN | | |  |
| US-018-AC3 Given I tap Save and the request is retried, when I reopen the trip, then exactly one new… | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-022 | TC-106 | NOT RUN | | |  |
| US-018-AC3 Given I tap Save and the request is retried, when I reopen the trip, then exactly one new… | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-020, API-022 | TC-216 | NOT RUN | | |  |
| US-018-AC3 Given I tap Save and the request is retried, when I reopen the trip, then exactly one new… | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-022 | TC-219 | NOT RUN | | |  |
| US-018-AC4 Given I have 3 saved trips, when I open my trips, then all 3 are listed and each reopens… | FR-040, FR-041, FR-045, FR-090 | US-018 | BR-011 | UC-004, UC-006 | API-013, API-014 | TC-099 | NOT RUN | | |  |
| US-019-AC1 Given the AI service fails during generation, when I return to my trip, then the saved ve… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-018, API-020, API-022, API-014 | TC-100 | NOT RUN | | |  |
| US-019-AC1 Given the AI service fails during generation, when I return to my trip, then the saved ve… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-018, API-020, API-021, API-022 | TC-117 | NOT RUN | | |  |
| US-019-AC1 Given the AI service fails during generation, when I return to my trip, then the saved ve… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-018, API-020 | TC-218 | NOT RUN | | |  |
| US-019-AC2 Given the routing provider fails after my edits, when the error is shown, then my unsaved… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-018, API-020, API-022, API-014 | TC-101 | NOT RUN | | |  |
| US-019-AC2 Given the routing provider fails after my edits, when the error is shown, then my unsaved… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-018, API-019 | TC-112 | NOT RUN | | |  |
| US-019-AC2 Given the routing provider fails after my edits, when the error is shown, then my unsaved… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-020 | TC-114 | NOT RUN | | |  |
| US-019-AC2 Given the routing provider fails after my edits, when the error is shown, then my unsaved… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-018, API-020, API-021, API-022 | TC-117 | NOT RUN | | |  |
| US-019-AC2 Given the routing provider fails after my edits, when the error is shown, then my unsaved… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-018, API-020 | TC-218 | NOT RUN | | |  |
| US-019-AC3 Given the network drops during Save, when I retry, then either the save completed once or… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-018, API-020, API-022, API-014 | TC-102 | NOT RUN | | |  |
| US-019-AC3 Given the network drops during Save, when I retry, then either the save completed once or… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-018, API-020, API-021, API-022 | TC-117 | NOT RUN | | |  |
| US-019-AC4 Given my trip was saved from another device after I opened it, when I Save, then I see a… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-020 | TC-095 | NOT RUN | | |  |
| US-019-AC4 Given my trip was saved from another device after I opened it, when I Save, then I see a… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-022 | TC-103 | NOT RUN | | |  |
| US-019-AC4 Given my trip was saved from another device after I opened it, when I Save, then I see a… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-022 | TC-111 | NOT RUN | | |  |
| US-019-AC4 Given my trip was saved from another device after I opened it, when I Save, then I see a… | FR-042, FR-043, FR-044 | US-019 | BR-012, BR-033 | UC-004 | API-022 | TC-219 | NOT RUN | | |  |
| US-020-AC1 Given a saved trip, when I delete it and confirm, then it disappears from my trips. | FR-046 | US-020 | BR-011 | UC-006 | API-016, API-013 | TC-104 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-020-AC2 Given I cancel the confirmation, when I return to my trips, then the trip is still there. | FR-046 | US-020 | BR-011 | UC-006 | API-016, API-013 | TC-105 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-021-AC1 Given the HA-02 saved 2-day Hội An trip, when I lock a day-2 stop, then it shows a lock i… | FR-047, FR-091 | US-021 | BR-034 | UC-005 | API-020, API-022, API-014 | TC-121 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-021-AC1 Given the HA-02 saved 2-day Hội An trip, when I lock a day-2 stop, then it shows a lock i… | FR-047, FR-091 | US-021 | BR-034 | UC-005 | API-019 | TC-130 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-021-AC1 Given the HA-02 saved 2-day Hội An trip, when I lock a day-2 stop, then it shows a lock i… | FR-047, FR-091 | US-021 | BR-034 | UC-005 | API-020, API-021 | TC-217 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-021-AC2 Given the lock, when I save and reopen the trip, then the stop is still locked. | FR-047, FR-091 | US-021 | BR-034 | UC-005 | API-020, API-022, API-014 | TC-122 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-021-AC3 Given a locked stop, when I unlock it, then the indicator disappears. | FR-047, FR-091 | US-021 | BR-034 | UC-005 | API-020, API-022, API-014 | TC-123 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC1 Given the HA-02 trip with a locked day-2 stop, when I regenerate day 2, then day 1 is ide… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-021, API-014 | TC-124 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC1 Given the HA-02 trip with a locked day-2 stop, when I regenerate day 2, then day 1 is ide… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-021 | TC-128 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC1 Given the HA-02 trip with a locked day-2 stop, when I regenerate day 2, then day 1 is ide… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-020, API-021 | TC-217 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC2 Given the same, when I regenerate day 2, then the locked stop keeps its place, day and vi… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-021, API-014 | TC-125 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC2 Given the same, when I regenerate day 2, then the locked stop keeps its place, day and vi… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-021 | TC-129 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC2 Given the same, when I regenerate day 2, then the locked stop keeps its place, day and vi… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-020, API-021 | TC-217 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC3 Given the regenerated day, when I reopen the trip before Save, then the previous saved ve… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-021, API-014 | TC-126 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC4 Given an AI or routing failure during regeneration, when it ends, then the saved trip, my… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-021 | TC-118 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC4 Given an AI or routing failure during regeneration, when it ends, then the saved trip, my… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-021 | TC-119 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC4 Given an AI or routing failure during regeneration, when it ends, then the saved trip, my… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-021 | TC-120 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-042-AC4 Given an AI or routing failure during regeneration, when it ends, then the saved trip, my… | FR-048, FR-049, FR-050 | US-042 | BR-013, BR-035 | UC-005 | API-021, API-014 | TC-127 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| US-022-AC1 Given a stop of my saved trip, when I open its card, then I see its Vietnamese and Englis… | FR-051, FR-052, FR-053 | US-022 | BR-014, BR-036, BR-037 | UC-007 | API-017 | TC-131 | NOT RUN | | |  |
| US-022-AC1 Given a stop of my saved trip, when I open its card, then I see its Vietnamese and Englis… | FR-051, FR-052, FR-053 | US-022 | BR-014, BR-036, BR-037 | UC-007 | API-017 | TC-137 | NOT RUN | | |  |
| US-022-AC1 Given a stop of my saved trip, when I open its card, then I see its Vietnamese and Englis… | FR-051, FR-052, FR-053 | US-022 | BR-014, BR-036, BR-037 | UC-007 | API-017, API-030 | TC-220 | NOT RUN | | |  |
| US-022-AC2 Given the card, when I show it to a driver, then it shows the Vietnamese address or "addr… | FR-051, FR-052, FR-053 | US-022 | BR-014, BR-036, BR-037 | UC-007 | API-017 | TC-132 | NOT RUN | | |  |
| US-022-AC2 Given the card, when I show it to a driver, then it shows the Vietnamese address or "addr… | FR-051, FR-052, FR-053 | US-022 | BR-014, BR-036, BR-037 | UC-007 | API-017 | TC-138 | NOT RUN | | |  |
| US-022-AC3 Given the card, when I look for the entrance, then the verified entrance is shown or "unk… | FR-051, FR-052, FR-053 | US-022 | BR-014, BR-036, BR-037 | UC-007 | API-017 | TC-133 | NOT RUN | | |  |
| US-022-AC3 Given the card, when I look for the entrance, then the verified entrance is shown or "unk… | FR-051, FR-052, FR-053 | US-022 | BR-014, BR-036, BR-037 | UC-007 | API-017 | TC-139 | NOT RUN | | |  |
| US-023-AC1 Given a stop with a verified entrance, when I tap Directions, then the maps app opens wit… | FR-054 | US-023 | BR-036 | UC-007 | API-017 | TC-134 | NOT RUN | | |  |
| US-023-AC1 Given a stop with a verified entrance, when I tap Directions, then the maps app opens wit… | FR-054 | US-023 | BR-036 | UC-007 | API-017, API-030 | TC-220 | NOT RUN | | |  |
| US-023-AC2 Given a stop whose entrance is unknown, when I tap Directions, then the maps app opens wi… | FR-054 | US-023 | BR-036 | UC-007 | API-017 | TC-135 | NOT RUN | | |  |
| US-024-AC1 Given today is day 2 of a saved trip, when I open Today, then day 2's stops are listed in… | FR-055 | US-024 | BR-014 | UC-007 | API-014 | TC-136 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-025-AC1 Given Linh's language is Vietnamese, when she asks when a pagoda closes, then the answer… | FR-056, FR-058, FR-078 | US-025 | BR-015, BR-048 | UC-008 | API-024, API-028, API-027 | TC-141 | NOT RUN | | |  |
| US-025-AC1 Given Linh's language is Vietnamese, when she asks when a pagoda closes, then the answer… | FR-056, FR-058, FR-078 | US-025 | BR-015, BR-048 | UC-008 | API-028 | TC-146 | NOT RUN | | |  |
| US-025-AC1 Given Linh's language is Vietnamese, when she asks when a pagoda closes, then the answer… | FR-056, FR-058, FR-078 | US-025 | BR-015, BR-048 | UC-008 | API-028 | TC-148 | NOT RUN | | |  |
| US-025-AC2 Given any answer in either language, when it is shown, then at least one reviewed source… | FR-056, FR-058, FR-078 | US-025 | BR-015, BR-048 | UC-008 | API-024, API-028, API-027 | TC-142 | NOT RUN | | |  |
| US-025-AC2 Given any answer in either language, when it is shown, then at least one reviewed source… | FR-056, FR-058, FR-078 | US-025 | BR-015, BR-048 | UC-008 | API-028 | TC-146 | NOT RUN | | |  |
| US-025-AC2 Given any answer in either language, when it is shown, then at least one reviewed source… | FR-056, FR-058, FR-078 | US-025 | BR-015, BR-048 | UC-008 | API-028, API-027 | TC-147 | NOT RUN | | |  |
| US-025-AC3 Given the answer exists only on the open web, when I ask, then I am told evidence is insu… | FR-056, FR-058, FR-078 | US-025 | BR-015, BR-048 | UC-008 | API-024, API-028, API-027 | TC-143 | NOT RUN | | |  |
| US-026-AC1 Given a question outside the reviewed sources, when I ask it, then I see "insufficient ev… | FR-057 | US-026 | BR-038 | UC-008 | API-028 | TC-144 | NOT RUN | | |  |
| US-026-AC1 Given a question outside the reviewed sources, when I ask it, then I see "insufficient ev… | FR-057 | US-026 | BR-038 | UC-008 | API-028 | TC-149 | NOT RUN | | |  |
| US-026-AC2 Given the out-of-catalog set, when it is run, then at least 90% return "insufficient evid… | FR-057 | US-026 | BR-038 | UC-008 | API-028 | TC-145 | NOT RUN | | |  |
| US-027-AC1 Given microphone permission was never asked, when I first tap the microphone, then the pe… | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | API-028 | TC-152 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-027-AC1 Given microphone permission was never asked, when I first tap the microphone, then the pe… | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | n/a (device) | TC-162 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-027-AC2 Given I speak a question in Vietnamese or English, when it is transcribed, then the answe… | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | API-028 | TC-153 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-027-AC2 Given I speak a question in Vietnamese or English, when it is transcribed, then the answe… | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | API-028 | TC-157 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-027-AC2 Given I speak a question in Vietnamese or English, when it is transcribed, then the answe… | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | API-028 | TC-158 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-027-AC2 Given I speak a question in Vietnamese or English, when it is transcribed, then the answe… | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | API-028 | TC-159 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-027-AC2 Given I speak a question in Vietnamese or English, when it is transcribed, then the answe… | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | API-022 | TC-160 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-027-AC3 Given I denied the microphone, when I use the Guide, then text questions still work. | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | API-028 | TC-154 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-043-AC1 Given a completed answer in Vietnamese, when I tap Read aloud, then the audio matches the… | FR-060 | US-043 | BR-039 | UC-009 | n/a (on-device TTS) | TC-155 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-043-AC1 Given a completed answer in Vietnamese, when I tap Read aloud, then the audio matches the… | FR-060 | US-043 | BR-039 | UC-009 | n/a (on-device TTS) | TC-161 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-043-AC2 Given a completed answer in English, when I tap Read aloud, then the audio matches the di… | FR-060 | US-043 | BR-039 | UC-009 | n/a (on-device TTS) | TC-156 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-043-AC2 Given a completed answer in English, when I tap Read aloud, then the audio matches the di… | FR-060 | US-043 | BR-039 | UC-009 | n/a (on-device TTS) | TC-161 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| US-028-AC1 Given I first use the photo feature, when I tap it, then camera and location permissions… | FR-061, FR-062, FR-092, FR-093 | US-028 | BR-017, BR-040 | UC-010 | API-029 | TC-163 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| US-028-AC1 Given I first use the photo feature, when I tap it, then camera and location permissions… | FR-061, FR-062, FR-092, FR-093 | US-028 | BR-017, BR-040 | UC-010 | n/a (device) | TC-170 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| US-028-AC2 Given I am within 300 m of a published place, when I photograph it, then that place is th… | FR-061, FR-062, FR-092, FR-093 | US-028 | BR-017, BR-040 | UC-010 | API-029 | TC-164 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| US-028-AC2 Given I am within 300 m of a published place, when I photograph it, then that place is th… | FR-061, FR-062, FR-092, FR-093 | US-028 | BR-017, BR-040 | UC-010 | API-029 | TC-167 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| US-028-AC3 Given no published place within 300 m matches, when I photograph, then I see "not recogni… | FR-061, FR-062, FR-092, FR-093 | US-028 | BR-017, BR-040 | UC-010 | API-029 | TC-165 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| US-028-AC3 Given no published place within 300 m matches, when I photograph, then I see "not recogni… | FR-061, FR-062, FR-092, FR-093 | US-028 | BR-017, BR-040 | UC-010 | API-029 | TC-168 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| US-028-AC4 Given I denied camera or location, when I use the app, then search, planning and text que… | FR-061, FR-062, FR-092, FR-093 | US-028 | BR-017, BR-040 | UC-010 | API-029 | TC-166 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| US-029-AC1 Given a saved 2-day Hội An trip, when I tap "Find a stay" and choose a partner, then it o… | FR-064 | US-029 | BR-018 | UC-011 | API-030 | TC-171 | NOT RUN | | |  |
| US-029-AC1 Given a saved 2-day Hội An trip, when I tap "Find a stay" and choose a partner, then it o… | FR-064 | US-029 | BR-018 | UC-011 | API-030 | TC-175 | NOT RUN | | |  |
| US-029-AC1 Given a saved 2-day Hội An trip, when I tap "Find a stay" and choose a partner, then it o… | FR-064 | US-029 | BR-018 | UC-011 | API-030 | TC-179 | NOT RUN | | |  |
| US-029-AC1 Given a saved 2-day Hội An trip, when I tap "Find a stay" and choose a partner, then it o… | FR-064 | US-029 | BR-018 | UC-011 | API-017, API-030 | TC-220 | NOT RUN | | |  |
| US-029-AC2 Given a partner that cannot accept check-in and check-out dates, when I view the partner… | FR-064 | US-029 | BR-018 | UC-011 | API-030 | TC-172 | NOT RUN | | |  |
| US-030-AC1 Given a stop in Huế, when I tap "Find activities" and choose a partner, then it opens wit… | FR-065 | US-030 | BR-041 | UC-011 | API-030 | TC-173 | NOT RUN | | |  |
| US-030-AC1 Given a stop in Huế, when I tap "Find activities" and choose a partner, then it opens wit… | FR-065 | US-030 | BR-041 | UC-011 | API-030 | TC-177 | NOT RUN | | |  |
| US-031-AC1 Given a saved trip, when I open stays, then prices for at least one stay are shown, or th… | FR-066, FR-067, FR-080, FR-081 | US-031 | BR-019, BR-043, BR-049 | UC-012 | API-031, API-022, API-014 | TC-180 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| US-031-AC1 Given a saved trip, when I open stays, then prices for at least one stay are shown, or th… | FR-066, FR-067, FR-080, FR-081 | US-031 | BR-019, BR-043, BR-049 | UC-012 | API-031 | TC-184 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| US-031-AC1 Given a saved trip, when I open stays, then prices for at least one stay are shown, or th… | FR-066, FR-067, FR-080, FR-081 | US-031 | BR-019, BR-043, BR-049 | UC-012 | API-031 | TC-185 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| US-031-AC1 Given a saved trip, when I open stays, then prices for at least one stay are shown, or th… | FR-066, FR-067, FR-080, FR-081 | US-031 | BR-019, BR-043, BR-049 | UC-012 | API-031 | TC-186 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| US-031-AC2 Given a price is shown, when I read it, then I see its retrieval time. | FR-066, FR-067, FR-080, FR-081 | US-031 | BR-019, BR-043, BR-049 | UC-012 | API-031, API-022, API-014 | TC-181 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| US-031-AC3 Given a price is shown, when I read it, then I see a notice that the partner confirms the… | FR-066, FR-067, FR-080, FR-081 | US-031 | BR-019, BR-043, BR-049 | UC-012 | API-031, API-022, API-014 | TC-182 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| US-031-AC4 Given I save the trip, when I reopen it, then no price is stored with it. | FR-066, FR-067, FR-080, FR-081 | US-031 | BR-019, BR-043, BR-049 | UC-012 | API-022, API-014 | TC-183 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| US-032-AC1 Given I am signed out, when I open My trips, then I am asked to sign in. | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-003, API-013, API-014 | TC-187 | NOT RUN | | |  |
| US-032-AC1 Given I am signed out, when I open My trips, then I am asked to sign in. | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | all | TC-260 | NOT RUN | | |  |
| US-032-AC1 Given I am signed out, when I open My trips, then I am asked to sign in. | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-003 | TC-264 | NOT RUN | | |  |
| US-032-AC2 Given another traveler's trip identifier, when it is requested with my account, then acce… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-020 | TC-094 | NOT RUN | | |  |
| US-032-AC2 Given another traveler's trip identifier, when it is requested with my account, then acce… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-022 | TC-110 | NOT RUN | | |  |
| US-032-AC2 Given another traveler's trip identifier, when it is requested with my account, then acce… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-017 | TC-140 | NOT RUN | | |  |
| US-032-AC2 Given another traveler's trip identifier, when it is requested with my account, then acce… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-025, API-027, API-028 | TC-151 | NOT RUN | | |  |
| US-032-AC2 Given another traveler's trip identifier, when it is requested with my account, then acce… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-030 | TC-178 | NOT RUN | | |  |
| US-032-AC2 Given another traveler's trip identifier, when it is requested with my account, then acce… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-014 | TC-188 | NOT RUN | | |  |
| US-032-AC2 Given another traveler's trip identifier, when it is requested with my account, then acce… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-004, API-007, API-014, API-015, API-016, API-017, API-019, API-020, API-021, API-022, API-023, API-025, API-026, API-027, API-028, API-030, API-031 | TC-197 | NOT RUN | | |  |
| US-032-AC3 Given a denied request, when it is processed, then no external service is called. | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-020 | TC-094 | NOT RUN | | |  |
| US-032-AC3 Given a denied request, when it is processed, then no external service is called. | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-025, API-027, API-028 | TC-151 | NOT RUN | | |  |
| US-032-AC3 Given a denied request, when it is processed, then no external service is called. | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-014, API-017, API-028 | TC-189 | NOT RUN | | |  |
| US-032-AC3 Given a denied request, when it is processed, then no external service is called. | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-004, API-007, API-014, API-015, API-016, API-017, API-019, API-020, API-021, API-022, API-023, API-025, API-026, API-027, API-028, API-030, API-031 | TC-197 | NOT RUN | | |  |
| US-032-AC4 Given I sign out, when I return to the app, then my private screens are not shown. | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-003, API-013, API-014 | TC-190 | NOT RUN | | |  |
| US-032-AC4 Given I sign out, when I return to the app, then my private screens are not shown. | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-013 | TC-203 | NOT RUN | | |  |
| US-033-AC1 Given I confirm deletion, when I view account status, then it shows "in progress". | FR-071, FR-072 | US-033 | BR-021, BR-044 | UC-014 | API-006, API-007 | TC-191 | NOT RUN | | |  |
| US-033-AC1 Given I confirm deletion, when I view account status, then it shows "in progress". | FR-071, FR-072 | US-033 | BR-021, BR-044 | UC-014 | API-006 | TC-200 | NOT RUN | | |  |
| US-033-AC2 Given deletion completes, when I view status, then it shows "completed"; if it fails, the… | FR-071, FR-072 | US-033 | BR-021, BR-044 | UC-014 | API-006, API-007 | TC-192 | NOT RUN | | |  |
| US-033-AC2 Given deletion completes, when I view status, then it shows "completed"; if it fails, the… | FR-071, FR-072 | US-033 | BR-021, BR-044 | UC-014 | API-007 | TC-201 | NOT RUN | | |  |
| US-033-AC3 Given 24 hours have passed since confirmation, when the live service, identity provider a… | FR-071, FR-072 | US-033 | BR-021, BR-044 | UC-014 | API-006, API-007 | TC-193 | NOT RUN | | |  |
| US-033-AC3 Given 24 hours have passed since confirmation, when the live service, identity provider a… | FR-071, FR-072 | US-033 | BR-021, BR-044 | UC-014 | API-006 | TC-202 | NOT RUN | | |  |
| US-033-AC4 Given a backup taken before my deletion is restored in a test, when the restore completes… | FR-071, FR-072 | US-033 | BR-021, BR-044 | UC-014 | API-006, API-007 | TC-194 | NOT RUN | | |  |
| US-034-AC1 Given I choose English, when I open every screen, then no untranslated string appears. | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | API-008, API-011 | TC-204 | NOT RUN | | |  |
| US-034-AC1 Given I choose English, when I open every screen, then no untranslated string appears. | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | n/a (client) | TC-207 | NOT RUN | | |  |
| US-034-AC1 Given I choose English, when I open every screen, then no untranslated string appears. | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | n/a (client) | TC-209 | NOT RUN | | |  |
| US-034-AC2 Given I choose Vietnamese, when I open every screen, then no untranslated string appears. | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | API-008, API-011 | TC-205 | NOT RUN | | |  |
| US-034-AC2 Given I choose Vietnamese, when I open every screen, then no untranslated string appears. | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | n/a (client) | TC-207 | NOT RUN | | |  |
| US-034-AC2 Given I choose Vietnamese, when I open every screen, then no untranslated string appears. | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | n/a (client) | TC-209 | NOT RUN | | |  |
| US-034-AC3 Given English is selected, when I view a place, then its description is in English and it… | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | API-011 | TC-206 | NOT RUN | | |  |
| US-034-AC3 Given English is selected, when I view a place, then its description is in English and it… | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | API-011 | TC-208 | NOT RUN | | |  |
| US-035-AC1 Given I have not planned before, when I start my first request, then a notice explains th… | FR-070, FR-074 | US-035 | BR-046 | UC-002, UC-008, UC-010 | API-018, API-028, API-029 | TC-195 | NOT RUN | | |  |
| US-035-AC1 Given I have not planned before, when I start my first request, then a notice explains th… | FR-070, FR-074 | US-035 | BR-046 | UC-002, UC-008, UC-010 | API-018 | TC-199 | NOT RUN | | |  |
| US-035-AC2 Given 20 recorded AI requests from test sessions, when they are inspected, then none cont… | FR-070, FR-074 | US-035 | BR-046 | UC-002, UC-008, UC-010 | API-029 | TC-169 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| US-035-AC2 Given 20 recorded AI requests from test sessions, when they are inspected, then none cont… | FR-070, FR-074 | US-035 | BR-046 | UC-002, UC-008, UC-010 | API-018, API-028, API-029 | TC-196 | NOT RUN | | |  |
| US-035-AC2 Given 20 recorded AI requests from test sessions, when they are inspected, then none cont… | FR-070, FR-074 | US-035 | BR-046 | UC-002, UC-008, UC-010 | API-018, API-028 | TC-198 | NOT RUN | | |  |
| US-036-AC1 Given a study account, when I complete a planning task, then a session log records partic… | FR-077 | US-036 | BR-023, BR-045 | UC-022 | API-032 | TC-210 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-036-AC1 Given a study account, when I complete a planning task, then a session log records partic… | FR-077 | US-036 | BR-023, BR-045 | UC-022 | API-032 | TC-213 | NOT RUN | | |  |
| US-036-AC1 Given a study account, when I complete a planning task, then a session log records partic… | FR-077 | US-036 | BR-023, BR-045 | UC-022 | API-032 | TC-214 | NOT RUN | | |  |
| US-036-AC2 Given the log, when it is inspected, then it contains no request or question text and no… | FR-077 | US-036 | BR-023, BR-045 | UC-022 | API-032 | TC-211 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-036-AC3 Given a non-study account, when it plans, then no session log is created. | FR-077 | US-036 | BR-023, BR-045 | UC-022 | API-032 | TC-212 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| US-037-AC1 Given a saved trip to Đà Nẵng starting on a given date, when I tap "Find transport", then… | FR-079 | US-037 | BR-042 | UC-011 | API-030 | TC-174 | NOT RUN | | |  |
| US-037-AC1 Given a saved trip to Đà Nẵng starting on a given date, when I tap "Find transport", then… | FR-079 | US-037 | BR-042 | UC-011 | API-030 | TC-176 | NOT RUN | | |  |
| US-037-AC1 Given a saved trip to Đà Nẵng starting on a given date, when I tap "Find transport", then… | FR-079 | US-037 | BR-042 | UC-011 | API-017, API-030 | TC-220 | NOT RUN | | |  |

### 3.2 BRD acceptance criteria

| Acceptance criterion | Requirement | Story | BR | UC | API | Test case | Result | Evidence | Defect | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| AC-001 Per city, searches for 2 published places by Vietnamese name, 2 by English name and 2 by… | FR-001, FR-002, FR-003 | US-001, US-002 | BR-001 | UC-001 | API-008, API-010 | TC-001 | NOT RUN | | |  |
| AC-001 Per city, searches for 2 published places by Vietnamese name, 2 by English name and 2 by… | FR-001, FR-002, FR-003 | US-001, US-002 | BR-001 | UC-001 | API-008, API-010 | TC-002 | NOT RUN | | |  |
| AC-001 Per city, searches for 2 published places by Vietnamese name, 2 by English name and 2 by… | FR-001, FR-002, FR-003 | US-001, US-002 | BR-001 | UC-001 | API-010 | TC-011 | NOT RUN | | |  |
| AC-002 For 10 candidate places, 0 appear in search, proposals or answers. | FR-004, FR-017 | US-003, US-007 | BR-002 | UC-001, UC-020 | API-010, API-018, API-028 | TC-009 | NOT RUN | | |  |
| AC-002 For 10 candidate places, 0 appear in search, proposals or answers. | FR-004, FR-017 | US-003, US-007 | BR-002 | UC-001, UC-020 | API-010, API-011 | TC-010 | NOT RUN | | |  |
| AC-002 For 10 candidate places, 0 appear in search, proposals or answers. | FR-004, FR-017 | US-003, US-007 | BR-002 | UC-001, UC-020 | API-024 | TC-150 | NOT RUN | | |  |
| AC-003 Inspection of 20 randomly chosen published places finds 0 displayed operational facts wit… | FR-005 | US-002 | BR-003 | UC-001 | API-011 | TC-005 | NOT RUN | | |  |
| AC-003 Inspection of 20 randomly chosen published places finds 0 displayed operational facts wit… | FR-005 | US-002 | BR-003 | UC-001 | API-011 | TC-013 | NOT RUN | | |  |
| AC-024 For 5 places with a deliberately missing fact, 100% show that fact as unknown, never blan… | FR-006 | US-002 | BR-024 | UC-001 | API-011 | TC-006 | NOT RUN | | |  |
| AC-024 For 5 places with a deliberately missing fact, 100% show that fact as unknown, never blan… | FR-006 | US-002 | BR-024 | UC-001 | API-011 | TC-014 | NOT RUN | | |  |
| AC-025 For a fact whose verification date is set 181 days in the past, the fact is labelled stal… | FR-007 | US-002 | BR-025 | UC-001 | API-011 | TC-007 | NOT RUN | | |  |
| AC-025 For a fact whose verification date is set 181 days in the past, the fact is labelled stal… | FR-007 | US-002 | BR-025 | UC-001 | API-011 | TC-012 | NOT RUN | | |  |
| AC-004 An attempt to publish a candidate missing Vietnamese content, English content or a source… | FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, FR-082, FR-084 | US-004, US-005, US-006, US-008, US-009 | BR-004 | UC-017, UC-018, UC-019, UC-021 | API-036 | TC-024 | NOT RUN | | |  |
| AC-004 An attempt to publish a candidate missing Vietnamese content, English content or a source… | FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, FR-082, FR-084 | US-004, US-005, US-006, US-008, US-009 | BR-004 | UC-017, UC-018, UC-019, UC-021 | API-036 | TC-025 | NOT RUN | | |  |
| AC-004 An attempt to publish a candidate missing Vietnamese content, English content or a source… | FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, FR-082, FR-084 | US-004, US-005, US-006, US-008, US-009 | BR-004 | UC-017, UC-018, UC-019, UC-021 | API-036, API-010 | TC-026 | NOT RUN | | |  |
| AC-004 An attempt to publish a candidate missing Vietnamese content, English content or a source… | FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, FR-082, FR-084 | US-004, US-005, US-006, US-008, US-009 | BR-004 | UC-017, UC-018, UC-019, UC-021 | API-036 | TC-034 | NOT RUN | | |  |
| AC-004 An attempt to publish a candidate missing Vietnamese content, English content or a source… | FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-018, FR-019, FR-082, FR-084 | US-004, US-005, US-006, US-008, US-009 | BR-004 | UC-017, UC-018, UC-019, UC-021 | API-036 | TC-036 | NOT RUN | | |  |
| AC-047 Inspection of every screen that shows provider or open-data content finds the required at… | FR-008, FR-016, FR-083 | US-002, US-005 | BR-047 | UC-001, UC-018, UC-019 | API-011 | TC-008 | NOT RUN | | |  |
| AC-047 Inspection of every screen that shows provider or open-data content finds the required at… | FR-008, FR-016, FR-083 | US-002, US-005 | BR-047 | UC-001, UC-018, UC-019 | API-011, API-017 | TC-015 | NOT RUN | | |  |
| AC-047 Inspection of every screen that shows provider or open-data content finds the required at… | FR-008, FR-016, FR-083 | US-002, US-005 | BR-047 | UC-001, UC-018, UC-019 | API-034, API-035, API-041 | TC-023 | NOT RUN | | |  |
| AC-005 Over the golden planning set, 100% of requests either produce a proposal with the request… | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | US-010, US-011, US-012, US-013, US-038 | BR-005 | UC-002, UC-016 | API-012, API-018 | TC-039 | NOT RUN | | |  |
| AC-005 Over the golden planning set, 100% of requests either produce a proposal with the request… | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | US-010, US-011, US-012, US-013, US-038 | BR-005 | UC-002, UC-016 | API-012, API-018 | TC-040 | NOT RUN | | |  |
| AC-005 Over the golden planning set, 100% of requests either produce a proposal with the request… | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | US-010, US-011, US-012, US-013, US-038 | BR-005 | UC-002, UC-016 | API-012, API-018 | TC-041 | NOT RUN | | |  |
| AC-005 Over the golden planning set, 100% of requests either produce a proposal with the request… | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | US-010, US-011, US-012, US-013, US-038 | BR-005 | UC-002, UC-016 | API-018 | TC-044 | NOT RUN | | |  |
| AC-005 Over the golden planning set, 100% of requests either produce a proposal with the request… | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | US-010, US-011, US-012, US-013, US-038 | BR-005 | UC-002, UC-016 | API-018 | TC-045 | NOT RUN | | |  |
| AC-005 Over the golden planning set, 100% of requests either produce a proposal with the request… | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | US-010, US-011, US-012, US-013, US-038 | BR-005 | UC-002, UC-016 | API-018 | TC-046 | NOT RUN | | |  |
| AC-005 Over the golden planning set, 100% of requests either produce a proposal with the request… | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | US-010, US-011, US-012, US-013, US-038 | BR-005 | UC-002, UC-016 | API-018, API-019 | TC-050 | NOT RUN | | |  |
| AC-005 Over the golden planning set, 100% of requests either produce a proposal with the request… | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | US-010, US-011, US-012, US-013, US-038 | BR-005 | UC-002, UC-016 | API-018 | TC-058 | NOT RUN | | |  |
| AC-005 Over the golden planning set, 100% of requests either produce a proposal with the request… | FR-020, FR-021, FR-022, FR-023, FR-024, FR-026, FR-073, FR-085, FR-086, FR-096 | US-010, US-011, US-012, US-013, US-038 | BR-005 | UC-002, UC-016 | API-018, API-019 | TC-215 | NOT RUN | | |  |
| AC-006 Over the golden planning set, 100% of proposed places belong to the requested city; an in… | FR-025, FR-087 | US-013 | BR-006 | UC-002 | API-018, API-019 | TC-051 | NOT RUN | | |  |
| AC-006 Over the golden planning set, 100% of proposed places belong to the requested city; an in… | FR-025, FR-087 | US-013 | BR-006 | UC-002 | API-018, API-019 | TC-052 | NOT RUN | | |  |
| AC-006 Over the golden planning set, 100% of proposed places belong to the requested city; an in… | FR-025, FR-087 | US-013 | BR-006 | UC-002 | API-018 | TC-056 | NOT RUN | | |  |
| AC-006 Over the golden planning set, 100% of proposed places belong to the requested city; an in… | FR-025, FR-087 | US-013 | BR-006 | UC-002 | API-018, API-019 | TC-059 | NOT RUN | | |  |
| AC-007 Every day of every golden proposal shows stops in order with arrival and departure times… | FR-027, FR-028, FR-088 | US-014 | BR-007 | UC-002 | API-018, API-019 | TC-062 | NOT RUN | | |  |
| AC-007 Every day of every golden proposal shows stops in order with arrival and departure times… | FR-027, FR-028, FR-088 | US-014 | BR-007 | UC-002 | API-019 | TC-070 | NOT RUN | | |  |
| AC-026 Every leg of every golden proposal shows mode, distance and duration, or the label "unava… | FR-029 | US-014 | BR-026 | UC-015 | API-018, API-019 | TC-064 | NOT RUN | | |  |
| AC-026 Every leg of every golden proposal shows mode, distance and duration, or the label "unava… | FR-029 | US-014 | BR-026 | UC-015 | API-018, API-019 | TC-065 | NOT RUN | | |  |
| AC-026 Every leg of every golden proposal shows mode, distance and duration, or the label "unava… | FR-029 | US-014 | BR-026 | UC-015 | API-019 | TC-071 | NOT RUN | | |  |
| AC-008 MET-004 = 100% on the conflict set; each flag names the affected stop or leg. | FR-030, FR-031 | US-015 | BR-008 | UC-015 | API-019, API-022 | TC-066 | NOT RUN | | |  |
| AC-008 MET-004 = 100% on the conflict set; each flag names the affected stop or leg. | FR-030, FR-031 | US-015 | BR-008 | UC-015 | API-019, API-022 | TC-067 | NOT RUN | | |  |
| AC-008 MET-004 = 100% on the conflict set; each flag names the affected stop or leg. | FR-030, FR-031 | US-015 | BR-008 | UC-015 | API-019, API-022 | TC-068 | NOT RUN | | |  |
| AC-008 MET-004 = 100% on the conflict set; each flag names the affected stop or leg. | FR-030, FR-031 | US-015 | BR-008 | UC-015 | API-019 | TC-072 | NOT RUN | | |  |
| AC-009 Saving each conflict-set proposal is refused with the reason shown, in 100% of cases. | FR-032 | US-015 | BR-009 | UC-004 | API-022 | TC-069 | NOT RUN | | |  |
| AC-009 Saving each conflict-set proposal is refused with the reason shown, in 100% of cases. | FR-032 | US-015 | BR-009 | UC-004 | API-022 | TC-073 | NOT RUN | | |  |
| AC-009 Saving each conflict-set proposal is refused with the reason shown, in 100% of cases. | FR-032 | US-015 | BR-009 | UC-004 | API-020, API-022 | TC-216 | NOT RUN | | |  |
| AC-010 Moving a stop to a new position shows the new order and recalculated times; after Save, r… | FR-033 | US-016 | BR-010 | UC-003 | API-020, API-022, API-014 | TC-075 | NOT RUN | | |  |
| AC-010 Moving a stop to a new position shows the new order and recalculated times; after Save, r… | FR-033 | US-016 | BR-010 | UC-003 | API-020, API-022, API-014 | TC-078 | NOT RUN | | |  |
| AC-027 Adding a published same-city place inserts it into the chosen day; adding a place from an… | FR-034 | US-039 | BR-027 | UC-003 | API-020, API-010 | TC-079 | NOT RUN | | |  |
| AC-027 Adding a published same-city place inserts it into the chosen day; adding a place from an… | FR-034 | US-039 | BR-027 | UC-003 | API-020, API-010 | TC-080 | NOT RUN | | |  |
| AC-028 Removing a stop removes it and its legs; after Save the stop is absent on reopening. | FR-035 | US-040 | BR-028 | UC-003 | API-020, API-022, API-014 | TC-082 | NOT RUN | | |  |
| AC-028 Removing a stop removes it and its legs; after Save the stop is absent on reopening. | FR-035 | US-040 | BR-028 | UC-003 | API-020, API-022, API-014 | TC-084 | NOT RUN | | |  |
| AC-029 Replacing a stop offers only published same-city places; after Save the replacement appea… | FR-036 | US-041 | BR-029 | UC-003 | API-010 | TC-085 | NOT RUN | | |  |
| AC-029 Replacing a stop offers only published same-city places; after Save the replacement appea… | FR-036 | US-041 | BR-029 | UC-003 | API-020, API-010 | TC-087 | NOT RUN | | |  |
| AC-030 Changing a visit duration updates that stop's departure and all later times on the day. | FR-037 | US-017 | BR-030 | UC-003 | API-020 | TC-088 | NOT RUN | | |  |
| AC-031 Switching a leg between walking and driving updates that leg's distance and duration and… | FR-038 | US-017 | BR-031 | UC-003 | API-020 | TC-089 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-076 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-077 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020, API-010 | TC-081 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020, API-022, API-014 | TC-083 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020, API-010 | TC-086 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020 | TC-090 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020 | TC-091 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020 | TC-092 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020 | TC-093 | NOT RUN | | |  |
| AC-032 For each edit type (AC-010, AC-027..AC-031), Save is not available until recalculation co… | FR-039, FR-089 | US-016, US-017, US-039, US-040, US-041 | BR-032 | UC-003, UC-015 | API-020, API-022 | TC-216 | NOT RUN | | |  |
| AC-011 Each of these leaves the previously saved itinerary unchanged when reopened: closing the… | FR-040, FR-041, FR-045, FR-046, FR-090 | US-018, US-020 | BR-011 | UC-004, UC-006 | API-014 | TC-097 | NOT RUN | | |  |
| AC-011 Each of these leaves the previously saved itinerary unchanged when reopened: closing the… | FR-040, FR-041, FR-045, FR-046, FR-090 | US-018, US-020 | BR-011 | UC-004, UC-006 | API-014 | TC-107 | NOT RUN | | |  |
| AC-011 Each of these leaves the previously saved itinerary unchanged when reopened: closing the… | FR-040, FR-041, FR-045, FR-046, FR-090 | US-018, US-020 | BR-011 | UC-004, UC-006 | API-018, API-014 | TC-108 | NOT RUN | | |  |
| AC-011 Each of these leaves the previously saved itinerary unchanged when reopened: closing the… | FR-040, FR-041, FR-045, FR-046, FR-090 | US-018, US-020 | BR-011 | UC-004, UC-006 | API-021, API-014 | TC-126 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-018, API-020, API-022, API-014 | TC-100 | NOT RUN | | |  |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-018, API-020, API-022, API-014 | TC-102 | NOT RUN | | |  |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-018 | TC-113 | NOT RUN | | |  |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-018 | TC-116 | NOT RUN | | |  |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-018, API-020, API-021, API-022 | TC-117 | NOT RUN | | |  |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-021 | TC-118 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-021 | TC-119 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-021 | TC-120 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-021, API-014 | TC-127 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-012 Under injected AI, routing and network failures, the saved itinerary is unchanged in 100%… | FR-042, FR-043 | US-019 | BR-012 | UC-004 | API-018, API-020 | TC-218 | NOT RUN | | |  |
| AC-033 Under the same injected failures, unsaved edits are still present after the failure in 10… | FR-044 | US-019 | BR-033 | UC-004 | API-018, API-020, API-022, API-014 | TC-101 | NOT RUN | | |  |
| AC-033 Under the same injected failures, unsaved edits are still present after the failure in 10… | FR-044 | US-019 | BR-033 | UC-004 | API-018, API-019 | TC-112 | NOT RUN | | |  |
| AC-033 Under the same injected failures, unsaved edits are still present after the failure in 10… | FR-044 | US-019 | BR-033 | UC-004 | API-020 | TC-114 | NOT RUN | | |  |
| AC-033 Under the same injected failures, unsaved edits are still present after the failure in 10… | FR-044 | US-019 | BR-033 | UC-004 | API-020 | TC-115 | NOT RUN | | |  |
| AC-033 Under the same injected failures, unsaved edits are still present after the failure in 10… | FR-044 | US-019 | BR-033 | UC-004 | API-018, API-020, API-021, API-022 | TC-117 | NOT RUN | | |  |
| AC-033 Under the same injected failures, unsaved edits are still present after the failure in 10… | FR-044 | US-019 | BR-033 | UC-004 | API-021 | TC-118 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-033 Under the same injected failures, unsaved edits are still present after the failure in 10… | FR-044 | US-019 | BR-033 | UC-004 | API-021 | TC-119 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-033 Under the same injected failures, unsaved edits are still present after the failure in 10… | FR-044 | US-019 | BR-033 | UC-004 | API-021 | TC-120 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-033 Under the same injected failures, unsaved edits are still present after the failure in 10… | FR-044 | US-019 | BR-033 | UC-004 | API-018, API-020 | TC-218 | NOT RUN | | |  |
| AC-034 A locked stop shows a lock indicator and stays locked after the trip is reopened. | FR-047, FR-091 | US-021 | BR-034 | UC-005 | API-020, API-022, API-014 | TC-121 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-034 A locked stop shows a lock indicator and stays locked after the trip is reopened. | FR-047, FR-091 | US-021 | BR-034 | UC-005 | API-020, API-022, API-014 | TC-122 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-034 A locked stop shows a lock indicator and stays locked after the trip is reopened. | FR-047, FR-091 | US-021 | BR-034 | UC-005 | API-019 | TC-130 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-013 Regenerating day 2 of a 2-day trip changes only day 2; day 1 is identical before and afte… | FR-048, FR-050 | US-042 | BR-013 | UC-005 | API-021, API-014 | TC-124 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-013 Regenerating day 2 of a 2-day trip changes only day 2; day 1 is identical before and afte… | FR-048, FR-050 | US-042 | BR-013 | UC-005 | API-021 | TC-128 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-013 Regenerating day 2 of a 2-day trip changes only day 2; day 1 is identical before and afte… | FR-048, FR-050 | US-042 | BR-013 | UC-005 | API-020, API-021 | TC-217 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-035 MET-005 = 0 over the regeneration set. | FR-049 | US-042 | BR-035 | UC-005 | API-021, API-014 | TC-125 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-035 MET-005 = 0 over the regeneration set. | FR-049 | US-042 | BR-035 | UC-005 | API-021 | TC-129 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-035 MET-005 = 0 over the regeneration set. | FR-049 | US-042 | BR-035 | UC-005 | API-020, API-021 | TC-217 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 4 (lock/regeneration) |
| AC-014 For one saved trip per city with at least 5 stops, every card shows both names. | FR-051, FR-055 | US-022, US-024 | BR-014 | UC-007 | API-017 | TC-131 | NOT RUN | | |  |
| AC-014 For one saved trip per city with at least 5 stops, every card shows both names. | FR-051, FR-055 | US-022, US-024 | BR-014 | UC-007 | API-017 | TC-137 | NOT RUN | | |  |
| AC-036 For the same sample, every card shows a Vietnamese address or the label "unknown"; at lea… | FR-052, FR-054 | US-022, US-023 | BR-036 | UC-007 | API-017 | TC-132 | NOT RUN | | |  |
| AC-036 For the same sample, every card shows a Vietnamese address or the label "unknown"; at lea… | FR-052, FR-054 | US-022, US-023 | BR-036 | UC-007 | API-017 | TC-138 | NOT RUN | | |  |
| AC-037 For the same sample, every card shows an entrance location or the label "unknown". | FR-053 | US-022 | BR-037 | UC-007 | API-017 | TC-133 | NOT RUN | | |  |
| AC-037 For the same sample, every card shows an entrance location or the label "unknown". | FR-053 | US-022 | BR-037 | UC-007 | API-017 | TC-139 | NOT RUN | | |  |
| AC-015 MET-007 ≥ 95% on the Guide answer sample; 100% of answers are in the selected language. | FR-056, FR-058 | US-025 | BR-015 | UC-008 | API-024, API-028, API-027 | TC-141 | NOT RUN | | |  |
| AC-015 MET-007 ≥ 95% on the Guide answer sample; 100% of answers are in the selected language. | FR-056, FR-058 | US-025 | BR-015 | UC-008 | API-028 | TC-146 | NOT RUN | | |  |
| AC-015 MET-007 ≥ 95% on the Guide answer sample; 100% of answers are in the selected language. | FR-056, FR-058 | US-025 | BR-015 | UC-008 | API-028 | TC-148 | NOT RUN | | |  |
| AC-048 Every answer in the Guide answer sample lists at least one reviewed source. | FR-078 | US-025 | BR-048 | UC-008 | API-024, API-028, API-027 | TC-142 | NOT RUN | | |  |
| AC-048 Every answer in the Guide answer sample lists at least one reviewed source. | FR-078 | US-025 | BR-048 | UC-008 | API-028, API-027 | TC-147 | NOT RUN | | |  |
| AC-038 MET-008 ≥ 90% on the out-of-catalog question set. | FR-057 | US-026 | BR-038 | UC-008 | API-024, API-028, API-027 | TC-143 | NOT RUN | | |  |
| AC-038 MET-008 ≥ 90% on the out-of-catalog question set. | FR-057 | US-026 | BR-038 | UC-008 | API-028 | TC-144 | NOT RUN | | |  |
| AC-038 MET-008 ≥ 90% on the out-of-catalog question set. | FR-057 | US-026 | BR-038 | UC-008 | API-028 | TC-145 | NOT RUN | | |  |
| AC-016 For 10 spoken questions per language, ≥ 8 are transcribed well enough that the answer mee… | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | API-028 | TC-153 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| AC-016 For 10 spoken questions per language, ≥ 8 are transcribed well enough that the answer mee… | FR-059, FR-063 | US-027 | BR-016 | UC-009, UC-010 | API-028 | TC-157 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| AC-039 For 10 completed answers per language, the read-aloud audio matches the displayed text. | FR-060 | US-043 | BR-039 | UC-009 | n/a (on-device TTS) | TC-155 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| AC-039 For 10 completed answers per language, the read-aloud audio matches the displayed text. | FR-060 | US-043 | BR-039 | UC-009 | n/a (on-device TTS) | TC-156 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| AC-039 For 10 completed answers per language, the read-aloud audio matches the displayed text. | FR-060 | US-043 | BR-039 | UC-009 | n/a (on-device TTS) | TC-161 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| AC-017 MET-009 ≥ 85% on the photo test set. | FR-061, FR-092, FR-093 | US-028 | BR-017 | UC-010 | API-029 | TC-164 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| AC-017 MET-009 ≥ 85% on the photo test set. | FR-061, FR-092, FR-093 | US-028 | BR-017 | UC-010 | API-029 | TC-167 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| AC-040 For 20 photos of places not in the catalog, ≥ 90% return "not recognised". | FR-062 | US-028 | BR-040 | UC-010 | API-029 | TC-165 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| AC-040 For 20 photos of places not in the catalog, ≥ 90% return "not recognised". | FR-062 | US-028 | BR-040 | UC-010 | API-029 | TC-168 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| AC-018 From a saved trip in each city, each listed stay partner opens with the trip's city, chec… | FR-064 | US-029 | BR-018 | UC-011 | API-030 | TC-171 | NOT RUN | | |  |
| AC-018 From a saved trip in each city, each listed stay partner opens with the trip's city, chec… | FR-064 | US-029 | BR-018 | UC-011 | API-030 | TC-172 | NOT RUN | | |  |
| AC-018 From a saved trip in each city, each listed stay partner opens with the trip's city, chec… | FR-064 | US-029 | BR-018 | UC-011 | API-030 | TC-175 | NOT RUN | | |  |
| AC-042 From a saved trip in each city, the transport partner opens with the trip's city as desti… | FR-079 | US-037 | BR-042 | UC-011 | API-030 | TC-174 | NOT RUN | | |  |
| AC-042 From a saved trip in each city, the transport partner opens with the trip's city as desti… | FR-079 | US-037 | BR-042 | UC-011 | API-030 | TC-176 | NOT RUN | | |  |
| AC-041 From one stop per city, each listed activity partner opens with the stop's city filled in. | FR-065 | US-030 | BR-041 | UC-011 | API-030 | TC-173 | NOT RUN | | |  |
| AC-041 From one stop per city, each listed activity partner opens with the stop's city filled in. | FR-065 | US-030 | BR-041 | UC-011 | API-030 | TC-177 | NOT RUN | | |  |
| AC-019 Prices appear for at least one stay in each city for a test date range, or the section is… | FR-066 | US-031 | BR-019 | UC-012 | API-031, API-022, API-014 | TC-180 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| AC-019 Prices appear for at least one stay in each city for a test date range, or the section is… | FR-066 | US-031 | BR-019 | UC-012 | API-031 | TC-184 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| AC-019 Prices appear for at least one stay in each city for a test date range, or the section is… | FR-066 | US-031 | BR-019 | UC-012 | API-031 | TC-185 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| AC-019 Prices appear for at least one stay in each city for a test date range, or the section is… | FR-066 | US-031 | BR-019 | UC-012 | API-031 | TC-186 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| AC-043 Every displayed price shows its retrieval time; no price is stored with a saved trip. | FR-067, FR-081 | US-031 | BR-043 | UC-012 | API-031, API-022, API-014 | TC-181 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| AC-043 Every displayed price shows its retrieval time; no price is stored with a saved trip. | FR-067, FR-081 | US-031 | BR-043 | UC-012 | API-022, API-014 | TC-183 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| AC-049 Every displayed price shows the partner-confirmation notice. | FR-080 | US-031 | BR-049 | UC-012 | API-031, API-022, API-014 | TC-182 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| AC-020 MET-010 = 0: for each private resource type, a request using another traveler's identifie… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-020 | TC-094 | NOT RUN | | |  |
| AC-020 MET-010 = 0: for each private resource type, a request using another traveler's identifie… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-022 | TC-110 | NOT RUN | | |  |
| AC-020 MET-010 = 0: for each private resource type, a request using another traveler's identifie… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-017 | TC-140 | NOT RUN | | |  |
| AC-020 MET-010 = 0: for each private resource type, a request using another traveler's identifie… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-025, API-027, API-028 | TC-151 | NOT RUN | | |  |
| AC-020 MET-010 = 0: for each private resource type, a request using another traveler's identifie… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-030 | TC-178 | NOT RUN | | |  |
| AC-020 MET-010 = 0: for each private resource type, a request using another traveler's identifie… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-014 | TC-188 | NOT RUN | | |  |
| AC-020 MET-010 = 0: for each private resource type, a request using another traveler's identifie… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-014, API-017, API-028 | TC-189 | NOT RUN | | |  |
| AC-020 MET-010 = 0: for each private resource type, a request using another traveler's identifie… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-004, API-007, API-014, API-015, API-016, API-017, API-019, API-020, API-021, API-022, API-023, API-025, API-026, API-027, API-028, API-030, API-031 | TC-197 | NOT RUN | | |  |
| AC-020 MET-010 = 0: for each private resource type, a request using another traveler's identifie… | FR-068, FR-069, FR-094, FR-095 | US-032 | BR-020 | UC-013 | API-003 | TC-236 | NOT RUN | | |  |
| AC-046 Inspection of the content sent to AI services in 20 recorded test requests finds 0 accoun… | FR-070, FR-074 | US-035 | BR-046 | UC-002, UC-008, UC-010 | API-029 | TC-169 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 2 (photo) |
| AC-046 Inspection of the content sent to AI services in 20 recorded test requests finds 0 accoun… | FR-070, FR-074 | US-035 | BR-046 | UC-002, UC-008, UC-010 | API-018, API-028, API-029 | TC-196 | NOT RUN | | |  |
| AC-046 Inspection of the content sent to AI services in 20 recorded test requests finds 0 accoun… | FR-070, FR-074 | US-035 | BR-046 | UC-002, UC-008, UC-010 | API-018, API-028 | TC-198 | NOT RUN | | |  |
| AC-046 Inspection of the content sent to AI services in 20 recorded test requests finds 0 accoun… | FR-070, FR-074 | US-035 | BR-046 | UC-002, UC-008, UC-010 | API-018, API-028 | TC-239 | NOT RUN | | |  |
| AC-021 24 hours after a confirmed deletion, queries of the production database and of the identi… | FR-071 | US-033 | BR-021 | UC-014 | API-006, API-007 | TC-193 | NOT RUN | | |  |
| AC-021 24 hours after a confirmed deletion, queries of the production database and of the identi… | FR-071 | US-033 | BR-021 | UC-014 | API-006, API-007 | TC-194 | NOT RUN | | |  |
| AC-044 During deletion the app shows "in progress", then "completed" or the failure reason. | FR-072 | US-033 | BR-044 | UC-014 | API-006, API-007 | TC-191 | NOT RUN | | |  |
| AC-044 During deletion the app shows "in progress", then "completed" or the failure reason. | FR-072 | US-033 | BR-044 | UC-014 | API-006, API-007 | TC-192 | NOT RUN | | |  |
| AC-044 During deletion the app shows "in progress", then "completed" or the failure reason. | FR-072 | US-033 | BR-044 | UC-014 | API-007 | TC-201 | NOT RUN | | |  |
| AC-022 Inspection of all traveler-facing screens in each language finds 0 untranslated strings. | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | API-008, API-011 | TC-204 | NOT RUN | | |  |
| AC-022 Inspection of all traveler-facing screens in each language finds 0 untranslated strings. | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | API-008, API-011 | TC-205 | NOT RUN | | |  |
| AC-022 Inspection of all traveler-facing screens in each language finds 0 untranslated strings. | FR-075, FR-076, FR-097 | US-034 | BR-022 | UC-016 | n/a (client) | TC-209 | NOT RUN | | |  |
| AC-023 Signed consent and session records exist for 10–15 participants dated on or before 2027-0… | FR-077 | US-036 | BR-023 | UC-022 | API-032 | TC-213 | NOT RUN | | |  |
| AC-050 Weekly billing records from 2026-11-04 to 2027-01-31 show USD 0 cash spend and AWS spend… | — | — | BR-050 | — | n/a (billing) | TC-255 | NOT RUN | | |  |
| AC-050 Weekly billing records from 2026-11-04 to 2027-01-31 show USD 0 cash spend and AWS spend… | — | — | BR-050 | — | n/a (billing) | TC-256 | NOT RUN | | |  |
| AC-045 Session records show at least 4 participants per language. | FR-077 | US-036 | BR-045 | UC-022 | API-032 | TC-214 | NOT RUN | | |  |

### 3.3 Non-functional requirements

| Acceptance criterion | Requirement | Story | BR | UC | API | Test case | Result | Evidence | Defect | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| NFR-001 Place search shall display results within 2 s (p95). | NFR-001 | — | BR-001 | — | API-010 | TC-222 | NOT RUN | | |  |
| NFR-002 Proposal generation shall complete within 60 s (p95), inside the MET-002 budget of 3 min… | NFR-002 | — | BR-005 | — | API-018 | TC-223 | NOT RUN | | |  |
| NFR-003 The traveler app shall acknowledge a proposal request with a visible progress state. | NFR-003 | — | BR-005 | — | API-018 | TC-224 | NOT RUN | | |  |
| NFR-004 Recalculation after an edit shall complete within 5 s (p95). | NFR-004 | — | BR-032 | — | API-020 | TC-225 | NOT RUN | | |  |
| NFR-005 The Guide shall show the first answer text within 5 s (p95). | NFR-005 | — | BR-015 | — | API-028 | TC-226 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| NFR-006 The Guide shall complete an answer with its sources within 20 s (p95). | NFR-006 | — | BR-015 | — | API-028 | TC-227 | NOT RUN | | |  |
| NFR-007 The service shall support the study's concurrent load while NFR-001..NFR-006 hold. | NFR-007 | — | BR-023 | — | API-010, API-018, API-020, API-028 | TC-228 | NOT RUN | | |  |
| NFR-008 The service shall be available during scheduled study sessions. | NFR-008 | — | BR-023 | — | API-001, API-002 | TC-229 | NOT RUN | | |  |
| NFR-008 The service shall be available during scheduled study sessions. | NFR-008 | — | BR-023 | — | API-001 | TC-261 | NOT RUN | | |  |
| NFR-008 The service shall be available during scheduled study sessions. | NFR-008 | — | BR-023 | — | API-002 | TC-262 | NOT RUN | | |  |
| NFR-009 After an outage the service shall be restored within the recovery time objective. | NFR-009 | — | BR-012 | — | API-002 | TC-230 | NOT RUN | | |  |
| NFR-009 After an outage the service shall be restored within the recovery time objective. | NFR-009 | — | BR-012 | — | API-002 | TC-262 | NOT RUN | | |  |
| NFR-009 After an outage the service shall be restored within the recovery time objective. | NFR-009 | — | BR-012 | — | n/a (database) | TC-265 | NOT RUN | | |  |
| NFR-010 Data loss after an outage shall not exceed the recovery point objective. | NFR-010 | — | BR-012 | — | API-014 | TC-231 | NOT RUN | | |  |
| NFR-011 Failure of any single external provider shall not stop search, place cards or reopening s… | NFR-011 | — | BR-012 | — | API-031 | TC-185 | NOT RUN | | | Cuttable — Could, DEC-003 cut position 1 (prices) |
| NFR-011 Failure of any single external provider shall not stop search, place cards or reopening s… | NFR-011 | — | BR-012 | — | API-010, API-014, API-017 | TC-232 | NOT RUN | | |  |
| NFR-038 When the identity provider is unavailable, a traveler already signed in shall still reope… | NFR-038 | — | BR-012 | — | API-014, API-017 | TC-233 | NOT RUN | | |  |
| NFR-012 All client–server traffic shall be encrypted in transit. | NFR-012 | — | BR-020 | — | API-001 | TC-234 | NOT RUN | | |  |
| NFR-013 Stored private data and its backups shall be encrypted at rest. | NFR-013 | — | BR-020 | — | n/a (infrastructure) | TC-235 | NOT RUN | | |  |
| NFR-014 Requests with missing, invalid, expired or foreign-issuer credentials shall be rejected. | NFR-014 | — | BR-020 | — | API-003 | TC-236 | NOT RUN | | |  |
| NFR-015 Curation operations shall be limited to the curator role. | NFR-015 | — | BR-004 | — | API-033, API-034, API-035, API-036, API-037, API-038, API-039, API-040, API-041, API-042 | TC-037 | NOT RUN | | |  |
| NFR-015 Curation operations shall be limited to the curator role. | NFR-015 | — | BR-004 | — | API-036 | TC-237 | NOT RUN | | |  |
| NFR-016 Provider credentials shall never be delivered to clients. | NFR-016 | — | BR-020 | — | n/a (build) | TC-238 | NOT RUN | | |  |
| NFR-017 Logs, traces and crash reports shall exclude access tokens, precise locations, question t… | NFR-017 | — | BR-046 | — | API-028 | TC-159 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 3 (voice) |
| NFR-017 Logs, traces and crash reports shall exclude access tokens, precise locations, question t… | NFR-017 | — | BR-046 | — | API-018, API-028 | TC-239 | NOT RUN | | |  |
| NFR-017 Logs, traces and crash reports shall exclude access tokens, precise locations, question t… | NFR-017 | — | BR-046 | — | API-001 | TC-263 | NOT RUN | | |  |
| NFR-018 Study data shall be deleted at the end of its retention period. | NFR-018 | — | BR-023 | — | API-006 | TC-202 | NOT RUN | | |  |
| NFR-018 Study data shall be deleted at the end of its retention period. | NFR-018 | — | BR-023 | — | API-032 | TC-240 | NOT RUN | | |  |
| NFR-019 Participants shall rate the app's usability at a mean SUS score of at least 70. | NFR-019 | — | BR-005 | — | n/a (study) | TC-241 | NOT RUN | | |  |
| NFR-020 Participants shall complete the planning task. | NFR-020 | — | BR-005 | — | API-032 | TC-242 | NOT RUN | | |  |
| NFR-021 Participants shall reach a first proposal within a median of 3 minutes. | NFR-021 | — | BR-005 | — | API-032 | TC-243 | NOT RUN | | |  |
| NFR-022 Interactive elements of the traveler app shall have screen-reader labels in the selected… | NFR-022 | — | BR-022 | — | n/a (client) | TC-244 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| NFR-023 Normal text shall meet a contrast ratio of at least 4.5:1 (WCAG 2.1 SC 1.4.3). | NFR-023 | — | BR-022 | — | n/a (client) | TC-245 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| NFR-024 Key screens shall remain usable with large system text (WCAG 2.1 SC 1.4.4). | NFR-024 | — | BR-022 | — | n/a (client) | TC-246 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| NFR-025 Trip times shall be shown in Vietnam local time regardless of the device time zone. | NFR-025 | — | BR-007 | — | API-019 | TC-247 | NOT RUN | | |  |
| NFR-026 Vietnamese text shall render without missing or corrupted diacritics. | NFR-026 | — | BR-022 | — | API-011 | TC-248 | NOT RUN | | |  |
| NFR-027 The traveler app shall run on supported Android versions. | NFR-027 | — | BR-023 | — | API-018 | TC-249 | NOT RUN | | |  |
| NFR-028 The traveler app shall run on supported iOS versions. | NFR-028 | — | BR-023 | — | API-018 | TC-250 | NOT RUN | | | Cuttable — Should, DEC-003 cut position 5 (iOS) |
| NFR-029 The curator tool shall run in the curator's browser. | NFR-029 | — | BR-004 | — | API-033 | TC-251 | NOT RUN | | |  |
| NFR-030 Client code shall match the published API description. | NFR-030 | — | BR-023 | — | all | TC-252 | NOT RUN | | |  |
| NFR-030 Client code shall match the published API description. | NFR-030 | — | BR-023 | — | all | TC-260 | NOT RUN | | |  |
| NFR-031 Every Must FR shall have at least one test case before the study. | NFR-031 | — | BR-023 | — | n/a (docs) | TC-253 | NOT RUN | | |  |
| NFR-032 Acceptance results shall be reproducible. | NFR-032 | — | BR-023 | — | API-019 | TC-074 | NOT RUN | | |  |
| NFR-032 Acceptance results shall be reproducible. | NFR-032 | — | BR-023 | — | API-018, API-021, API-028 | TC-254 | NOT RUN | | |  |
| NFR-033 Operating Gonarra shall cost no cash. | NFR-033 | — | BR-050 | — | n/a (billing) | TC-255 | NOT RUN | | |  |
| NFR-034 Cloud spend shall stay within the AWS credits. | NFR-034 | — | BR-050 | — | n/a (billing) | TC-256 | NOT RUN | | |  |
| NFR-035 External service quotas shall not interrupt study sessions. | NFR-035 | — | BR-050 | — | API-018, API-028 | TC-257 | NOT RUN | | |  |
| NFR-036 Gonarra shall cap AI-backed requests per traveler per day. | NFR-036 | — | BR-050 | — | API-018, API-028 | TC-258 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |
| NFR-037 Budget alarms shall notify the owner. | NFR-037 | — | BR-050 | — | n/a (billing) | TC-259 | NOT RUN | | | Cuttable — Should, not in the DEC-003 list; de-scoping needs an owner decision |

## 4. Backward matrix (TC → criterion → FR/NFR → BR, UC, API)

| Test case | Priority | Level | Criteria | FR / NFR | BR | UC | API |
|---|---|---|---|---|---|---|---|
| TC-001 | P0 | Integration | AC-001, US-001-AC1 | FR-001, FR-002 | BR-001 | UC-001 | API-008, API-010 |
| TC-002 | P0 | Integration | AC-001, US-001-AC2 | FR-001, FR-002 | BR-001 | UC-001 | API-008, API-010 |
| TC-003 | P0 | Integration | US-001-AC3 | FR-001, FR-002 | BR-001 | UC-001 | API-008, API-010 |
| TC-004 | P0 | System/E2E | US-002-AC1 | FR-003, FR-005, FR-006, FR-007, FR-008 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 |
| TC-005 | P0 | System/E2E | AC-003, US-002-AC2 | FR-003, FR-005, FR-006, FR-007, FR-008 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 |
| TC-006 | P0 | System/E2E | AC-024, US-002-AC3 | FR-003, FR-005, FR-006, FR-007, FR-008 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 |
| TC-007 | P0 | Integration | AC-025, US-002-AC4 | FR-003, FR-005, FR-006, FR-007, FR-008 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 |
| TC-008 | P0 | System/E2E | AC-047, US-002-AC5 | FR-003, FR-005, FR-006, FR-007, FR-008 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 |
| TC-009 | P0 | Acceptance | AC-002, US-003-AC1 | FR-004 | BR-002 | UC-001 | API-010, API-018, API-028 |
| TC-010 | P0 | Integration | AC-002, US-003-AC2 | FR-004 | BR-002 | UC-001 | API-010, API-011 |
| TC-011 | P0 | Acceptance | AC-001, US-001-AC1, US-001-AC2 | FR-001, FR-002 | BR-001 | UC-001 | API-010 |
| TC-012 | P0 | Unit | AC-025, US-002-AC4 | FR-003, FR-005, FR-006, FR-007, FR-008 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 |
| TC-013 | P0 | Acceptance | AC-003, US-002-AC2 | FR-003, FR-005, FR-006, FR-007, FR-008 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 |
| TC-014 | P0 | System/E2E | AC-024, US-002-AC3 | FR-003, FR-005, FR-006, FR-007, FR-008 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001 | API-011 |
| TC-015 | P0 | Acceptance | AC-047, US-002-AC5 | FR-003, FR-005, FR-006, FR-007, FR-008, FR-016 | BR-001, BR-003, BR-024, BR-025, BR-047 | UC-001, UC-018, UC-019 | API-011, API-017 |
| TC-016 | P1 | Integration | US-001-AC3 | FR-001, FR-002 | BR-001 | UC-001 | API-010 |
| TC-017 | P0 | Integration | US-004-AC1 | FR-009, FR-010 | BR-004 | UC-017 | API-033, API-038, API-039 |
| TC-018 | P0 | Integration | US-004-AC2 | FR-009, FR-010 | BR-004 | UC-017 | API-033, API-038, API-039 |
| TC-019 | P0 | Integration | US-004-AC3 | FR-009, FR-010 | BR-004 | UC-017 | API-033, API-038, API-039 |
| TC-020 | P0 | Integration | US-005-AC1 | FR-011, FR-012, FR-016, FR-083 | BR-004, BR-047 | UC-018, UC-019 | API-034, API-035, API-041 |
| TC-021 | P0 | Integration | US-005-AC2 | FR-011, FR-012, FR-016, FR-083 | BR-004, BR-047 | UC-018, UC-019 | API-034, API-035, API-041 |
| TC-022 | P0 | Integration | US-005-AC3 | FR-011, FR-012, FR-016, FR-083 | BR-004, BR-047 | UC-018, UC-019 | API-034, API-035, API-041 |
| TC-023 | P0 | Integration | AC-047, US-005-AC4 | FR-011, FR-012, FR-016, FR-083 | BR-004, BR-047 | UC-018, UC-019 | API-034, API-035, API-041 |
| TC-024 | P0 | Integration | AC-004, US-006-AC1 | FR-013, FR-014, FR-015, FR-082 | BR-004 | UC-019 | API-036 |
| TC-025 | P0 | Integration | AC-004, US-006-AC2 | FR-013, FR-014, FR-015, FR-082 | BR-004 | UC-019 | API-036 |
| TC-026 | P0 | Integration | AC-004, US-006-AC3 | FR-013, FR-014, FR-015, FR-082 | BR-004 | UC-019 | API-010, API-036 |
| TC-027 | P0 | Integration | US-006-AC4 | FR-013, FR-014, FR-015, FR-082 | BR-004 | UC-019 | API-034 |
| TC-028 | P2 | Integration | US-007-AC1 | FR-017 | BR-002 | UC-020 | API-037 |
| TC-029 | P2 | Integration | US-007-AC2 | FR-017 | BR-002 | UC-020 | API-037 |
| TC-030 | P2 | Integration | US-008-AC1 | FR-018 | BR-004 | UC-021 | API-042 |
| TC-031 | P2 | Integration | US-009-AC1 | FR-019, FR-084 | BR-004 | UC-018 | API-034, API-035, API-036 |
| TC-032 | P2 | Integration | US-009-AC2 | FR-019, FR-084 | BR-004 | UC-018 | API-034, API-035, API-036 |
| TC-033 | P2 | Integration | US-009-AC3 | FR-019, FR-084 | BR-004 | UC-018 | API-034, API-035, API-036 |
| TC-034 | P0 | Integration | AC-004, US-006-AC1 | FR-013, FR-014, FR-015, FR-082 | BR-004 | UC-019 | API-036 |
| TC-035 | P0 | Integration | US-005-AC4 | FR-011, FR-012, FR-016, FR-083 | BR-004, BR-047 | UC-018, UC-019 | API-036, API-041 |
| TC-036 | P0 | System/E2E | AC-004, US-006-AC3 | FR-013, FR-014, FR-015, FR-082 | BR-004 | UC-019 | API-036 |
| TC-037 | P0 | Integration | US-006-AC3 | FR-013, FR-014, FR-015, FR-017, FR-082, NFR-015 | BR-002, BR-004 | UC-019, UC-020 | API-033, API-034, API-035, API-036, API-037, API-038, API-039, API-040, API-041, API-042 |
| TC-038 | P1 | Integration | US-004-AC3 | FR-009, FR-010 | BR-004 | UC-017 | API-039 |
| TC-039 | P0 | Integration | AC-005, US-010-AC1 | FR-020, FR-021 | BR-005 | UC-002 | API-012, API-018 |
| TC-040 | P0 | Integration | AC-005, US-010-AC2 | FR-020, FR-021 | BR-005 | UC-002 | API-012, API-018 |
| TC-041 | P0 | System/E2E | AC-005, US-010-AC3 | FR-020, FR-021 | BR-005 | UC-002 | API-012, API-018 |
| TC-042 | P2 | System/E2E | US-011-AC1 | FR-073, FR-096 | BR-005 | UC-016 | API-004, API-005 |
| TC-043 | P2 | Integration | US-011-AC2 | FR-073, FR-096 | BR-005 | UC-016 | API-004, API-005 |
| TC-044 | P0 | Integration | AC-005, US-012-AC1 | FR-022 | BR-005 | UC-002 | API-018 |
| TC-045 | P0 | Integration | AC-005, US-012-AC2 | FR-022 | BR-005 | UC-002 | API-018 |
| TC-046 | P0 | Integration | AC-005, US-012-AC3 | FR-022 | BR-005 | UC-002 | API-018 |
| TC-047 | P0 | Integration | US-038-AC1 | FR-023, FR-085, FR-086 | BR-005 | UC-002 | API-012, API-018 |
| TC-048 | P0 | Integration | US-038-AC2 | FR-023, FR-085, FR-086 | BR-005 | UC-002 | API-012, API-018 |
| TC-049 | P0 | Integration | US-038-AC3 | FR-023, FR-085, FR-086 | BR-005 | UC-002 | API-012, API-018 |
| TC-050 | P0 | Integration | AC-005, US-013-AC1 | FR-024, FR-025, FR-026, FR-087 | BR-005, BR-006 | UC-002 | API-018, API-019 |
| TC-051 | P0 | Integration | AC-006, US-013-AC2 | FR-024, FR-025, FR-026, FR-087 | BR-005, BR-006 | UC-002 | API-018, API-019 |
| TC-052 | P0 | Integration | AC-006, US-013-AC3 | FR-024, FR-025, FR-026, FR-087 | BR-005, BR-006 | UC-002 | API-018, API-019 |
| TC-053 | P0 | Integration | US-013-AC4 | FR-024, FR-025, FR-026, FR-087 | BR-005, BR-006 | UC-002 | API-018, API-019 |
| TC-054 | P0 | Integration | US-038-AC1 | FR-023, FR-085, FR-086 | BR-005 | UC-002 | API-012, API-018 |
| TC-055 | P0 | Integration | US-038-AC2, US-038-AC3 | FR-023, FR-085, FR-086 | BR-005 | UC-002 | API-018 |
| TC-056 | P0 | Integration | AC-006, US-013-AC3 | FR-024, FR-025, FR-026, FR-087 | BR-005, BR-006 | UC-002 | API-018 |
| TC-057 | P0 | Unit | US-013-AC3 | FR-024, FR-025, FR-026, FR-029, FR-087 | BR-005, BR-006, BR-026 | UC-002, UC-015 | API-018 |
| TC-058 | P0 | Acceptance | AC-005, US-012-AC1, US-013-AC1 | FR-020, FR-022, FR-024, FR-025, FR-026, FR-087 | BR-005, BR-006 | UC-002 | API-018 |
| TC-059 | P0 | Acceptance | AC-006, US-013-AC2, US-013-AC3 | FR-024, FR-025, FR-026, FR-087 | BR-005, BR-006 | UC-002 | API-018, API-019 |
| TC-060 | P2 | Acceptance | US-013-AC4 | FR-024, FR-025, FR-026, FR-087 | BR-005, BR-006 | UC-002 | API-018 |
| TC-061 | P0 | Integration | US-010-AC3 | FR-003, FR-020, FR-021 | BR-001, BR-005 | UC-001, UC-002 | API-009 |
| TC-062 | P0 | Integration | AC-007, US-014-AC1 | FR-027, FR-028, FR-029, FR-088 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 |
| TC-063 | P0 | System/E2E | US-014-AC2 | FR-027, FR-028, FR-029, FR-088 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 |
| TC-064 | P0 | Integration | AC-026, US-014-AC3 | FR-027, FR-028, FR-029, FR-088 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 |
| TC-065 | P0 | Integration | AC-026, US-014-AC4 | FR-027, FR-028, FR-029, FR-088 | BR-007, BR-026 | UC-002, UC-015 | API-018, API-019 |
| TC-066 | P0 | Integration | AC-008, US-015-AC1 | FR-030, FR-031, FR-032 | BR-008, BR-009 | UC-004, UC-015 | API-019, API-022 |
| TC-067 | P0 | Integration | AC-008, US-015-AC2 | FR-030, FR-031, FR-032 | BR-008, BR-009 | UC-004, UC-015 | API-019, API-022 |
| TC-068 | P0 | Integration | AC-008, US-015-AC3 | FR-030, FR-031, FR-032 | BR-008, BR-009 | UC-004, UC-015 | API-019, API-022 |
| TC-069 | P0 | Integration | AC-009, US-015-AC4 | FR-030, FR-031, FR-032 | BR-008, BR-009 | UC-004, UC-015 | API-022 |
| TC-070 | P0 | Acceptance | AC-007, US-014-AC1 | FR-027, FR-028, FR-029, FR-088 | BR-007, BR-026 | UC-002, UC-015 | API-019 |
| TC-071 | P0 | Acceptance | AC-026, US-014-AC3, US-014-AC4 | FR-027, FR-028, FR-029, FR-088 | BR-007, BR-026 | UC-002, UC-015 | API-019 |
| TC-072 | P0 | Acceptance | AC-008, US-015-AC1, US-015-AC2, US-015-AC3 | FR-030, FR-031, FR-032 | BR-008, BR-009 | UC-004, UC-015 | API-019 |
| TC-073 | P0 | Acceptance | AC-009, US-015-AC4 | FR-030, FR-031, FR-032 | BR-008, BR-009 | UC-004, UC-015 | API-022 |
| TC-074 | P1 | Unit | US-015-AC3 | FR-030, FR-031, FR-032, NFR-032 | BR-008, BR-009, BR-023 | UC-004, UC-015 | API-019 |
| TC-075 | P0 | Integration | AC-010, US-016-AC1 | FR-033, FR-039, FR-089 | BR-010, BR-032 | UC-003, UC-015 | API-014, API-020, API-022 |
| TC-076 | P0 | System/E2E | AC-032, US-016-AC2 | FR-033, FR-039, FR-089 | BR-010, BR-032 | UC-003, UC-015 | API-014, API-020, API-022 |
| TC-077 | P0 | Integration | AC-032, US-016-AC3 | FR-033, FR-039, FR-089 | BR-010, BR-032 | UC-003, UC-015 | API-014, API-020, API-022 |
| TC-078 | P0 | Integration | AC-010, US-016-AC4 | FR-033, FR-039, FR-089 | BR-010, BR-032 | UC-003, UC-015 | API-014, API-020, API-022 |
| TC-079 | P0 | Integration | AC-027, US-039-AC1 | FR-034, FR-039, FR-089 | BR-027, BR-032 | UC-003, UC-015 | API-010, API-020 |
| TC-080 | P0 | Integration | AC-027, US-039-AC2 | FR-034, FR-039, FR-089 | BR-027, BR-032 | UC-003, UC-015 | API-010, API-020 |
| TC-081 | P0 | System/E2E | AC-032, US-039-AC3 | FR-034, FR-039, FR-089 | BR-027, BR-032 | UC-003, UC-015 | API-010, API-020 |
| TC-082 | P0 | Integration | AC-028, US-040-AC1 | FR-035, FR-039, FR-089 | BR-028, BR-032 | UC-003, UC-015 | API-014, API-020, API-022 |
| TC-083 | P0 | System/E2E | AC-032, US-040-AC2 | FR-035, FR-039, FR-089 | BR-028, BR-032 | UC-003, UC-015 | API-014, API-020, API-022 |
| TC-084 | P0 | Integration | AC-028, US-040-AC3 | FR-035, FR-039, FR-089 | BR-028, BR-032 | UC-003, UC-015 | API-014, API-020, API-022 |
| TC-085 | P0 | Integration | AC-029, US-041-AC1 | FR-036, FR-039, FR-089 | BR-029, BR-032 | UC-003, UC-015 | API-010 |
| TC-086 | P0 | Integration | AC-032, US-041-AC2 | FR-036, FR-039, FR-089 | BR-029, BR-032 | UC-003, UC-015 | API-010, API-020 |
| TC-087 | P0 | Integration | AC-029, US-041-AC3 | FR-036, FR-039, FR-089 | BR-029, BR-032 | UC-003, UC-015 | API-010, API-020 |
| TC-088 | P0 | Integration | AC-030, US-017-AC1 | FR-037, FR-038, FR-039, FR-089 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 |
| TC-089 | P0 | Integration | AC-031, US-017-AC2 | FR-037, FR-038, FR-039, FR-089 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 |
| TC-090 | P0 | Integration | AC-032, US-017-AC3 | FR-037, FR-038, FR-039, FR-089 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 |
| TC-091 | P0 | System/E2E | AC-032, US-041-AC2 | FR-036, FR-039, FR-089 | BR-029, BR-032 | UC-003, UC-015 | API-020 |
| TC-092 | P0 | System/E2E | AC-032, US-017-AC1 | FR-037, FR-038, FR-039, FR-089 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 |
| TC-093 | P0 | System/E2E | AC-032, US-017-AC2 | FR-037, FR-038, FR-039, FR-089 | BR-030, BR-031, BR-032 | UC-003, UC-015 | API-020 |
| TC-094 | P0 | Integration | AC-020, US-032-AC2, US-032-AC3 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-020 |
| TC-095 | P0 | Integration | US-019-AC4 | FR-039, FR-042, FR-043, FR-044 | BR-012, BR-032, BR-033 | UC-003, UC-004, UC-015 | API-020 |
| TC-096 | P0 | System/E2E | US-018-AC1 | FR-040, FR-041, FR-045, FR-090 | BR-011 | UC-004, UC-006 | API-019 |
| TC-097 | P0 | System/E2E | AC-011, US-018-AC2 | FR-040, FR-041, FR-045, FR-090 | BR-011 | UC-004, UC-006 | API-014 |
| TC-098 | P0 | Integration | US-018-AC3 | FR-040, FR-041, FR-045, FR-090 | BR-011 | UC-004, UC-006 | API-014, API-022 |
| TC-099 | P0 | Integration | US-018-AC4 | FR-040, FR-041, FR-045, FR-090 | BR-011 | UC-004, UC-006 | API-013, API-014 |
| TC-100 | P0 | Integration | AC-012, US-019-AC1 | FR-042, FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-014, API-018, API-020, API-022 |
| TC-101 | P0 | Integration | AC-033, US-019-AC2 | FR-042, FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-014, API-018, API-020, API-022 |
| TC-102 | P0 | Integration | AC-012, US-019-AC3 | FR-042, FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-014, API-018, API-020, API-022 |
| TC-103 | P0 | Integration | US-019-AC4 | FR-042, FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-022 |
| TC-104 | P2 | Integration | US-020-AC1 | FR-046 | BR-011 | UC-006 | API-013, API-016 |
| TC-105 | P2 | System/E2E | US-020-AC2 | FR-046 | BR-011 | UC-006 | API-013, API-016 |
| TC-106 | P0 | Integration | US-018-AC3 | FR-040, FR-041, FR-045, FR-090 | BR-011 | UC-004, UC-006 | API-022 |
| TC-107 | P0 | System/E2E | AC-011, US-018-AC2 | FR-040, FR-041, FR-045, FR-090 | BR-011 | UC-004, UC-006 | API-014 |
| TC-108 | P0 | Integration | AC-011, US-018-AC2 | FR-040, FR-041, FR-045, FR-090 | BR-011 | UC-004, UC-006 | API-014, API-018 |
| TC-109 | P0 | System/E2E | US-018-AC1 | FR-040, FR-041, FR-045, FR-090 | BR-011 | UC-004, UC-006 | API-019, API-022 |
| TC-110 | P0 | Integration | AC-020, US-032-AC2 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-022 |
| TC-111 | P1 | Integration | US-019-AC4 | FR-042, FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-022 |
| TC-112 | P0 | Integration | AC-033, US-019-AC2 | FR-042, FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-018, API-019 |
| TC-113 | P0 | Integration | AC-012, US-014-AC4 | FR-027, FR-028, FR-029, FR-043, FR-088 | BR-007, BR-012, BR-026 | UC-002, UC-004, UC-015 | API-018 |
| TC-114 | P0 | System/E2E | AC-033, US-019-AC2 | FR-042, FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-020 |
| TC-115 | P0 | Integration | AC-033 | FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-020 |
| TC-116 | P0 | Integration | AC-012 | FR-043, FR-087 | BR-006, BR-012 | UC-004 | API-018 |
| TC-117 | P0 | Acceptance | AC-012, AC-033, US-019-AC1, US-019-AC2, US-019-AC3 | FR-042, FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-018, API-020, API-021, API-022 |
| TC-118 | P2 | Integration | AC-012, AC-033, US-042-AC4 | FR-043, FR-044, FR-048, FR-049, FR-050 | BR-012, BR-013, BR-033, BR-035 | UC-004, UC-005 | API-021 |
| TC-119 | P2 | Integration | AC-012, AC-033, US-042-AC4 | FR-043, FR-044, FR-048, FR-049, FR-050 | BR-012, BR-013, BR-033, BR-035 | UC-004, UC-005 | API-021 |
| TC-120 | P2 | System/E2E | AC-012, AC-033, US-042-AC4 | FR-043, FR-044, FR-048, FR-049, FR-050 | BR-012, BR-013, BR-033, BR-035 | UC-004, UC-005 | API-021 |
| TC-121 | P2 | System/E2E | AC-034, US-021-AC1 | FR-047, FR-091 | BR-034 | UC-005 | API-014, API-020, API-022 |
| TC-122 | P2 | Integration | AC-034, US-021-AC2 | FR-047, FR-091 | BR-034 | UC-005 | API-014, API-020, API-022 |
| TC-123 | P2 | System/E2E | US-021-AC3 | FR-047, FR-091 | BR-034 | UC-005 | API-014, API-020, API-022 |
| TC-124 | P2 | Integration | AC-013, US-042-AC1 | FR-048, FR-049, FR-050 | BR-013, BR-035 | UC-005 | API-014, API-021 |
| TC-125 | P2 | Integration | AC-035, US-042-AC2 | FR-048, FR-049, FR-050 | BR-013, BR-035 | UC-005 | API-014, API-021 |
| TC-126 | P2 | Integration | AC-011, US-042-AC3 | FR-048, FR-049, FR-050 | BR-011, BR-013, BR-035 | UC-005 | API-014, API-021 |
| TC-127 | P2 | Integration | AC-012, US-042-AC4 | FR-048, FR-049, FR-050 | BR-012, BR-013, BR-035 | UC-005 | API-014, API-021 |
| TC-128 | P2 | Acceptance | AC-013, US-042-AC1 | FR-048, FR-049, FR-050 | BR-013, BR-035 | UC-005 | API-021 |
| TC-129 | P2 | Acceptance | AC-035, US-042-AC2 | FR-048, FR-049, FR-050 | BR-013, BR-035 | UC-005 | API-021 |
| TC-130 | P2 | System/E2E | AC-034, US-021-AC1 | FR-047, FR-091 | BR-034 | UC-005 | API-019 |
| TC-131 | P0 | System/E2E | AC-014, US-022-AC1 | FR-051, FR-052, FR-053 | BR-014, BR-036, BR-037 | UC-007 | API-017 |
| TC-132 | P0 | System/E2E | AC-036, US-022-AC2 | FR-051, FR-052, FR-053 | BR-014, BR-036, BR-037 | UC-007 | API-017 |
| TC-133 | P0 | System/E2E | AC-037, US-022-AC3 | FR-051, FR-052, FR-053 | BR-014, BR-036, BR-037 | UC-007 | API-017 |
| TC-134 | P0 | System/E2E | US-023-AC1 | FR-054 | BR-036 | UC-007 | API-017 |
| TC-135 | P0 | System/E2E | US-023-AC2 | FR-054 | BR-036 | UC-007 | API-017 |
| TC-136 | P2 | System/E2E | US-024-AC1 | FR-055 | BR-014 | UC-007 | API-014 |
| TC-137 | P0 | Acceptance | AC-014, US-022-AC1 | FR-051, FR-052, FR-053 | BR-014, BR-036, BR-037 | UC-007 | API-017 |
| TC-138 | P0 | Acceptance | AC-036, US-022-AC2 | FR-051, FR-052, FR-053 | BR-014, BR-036, BR-037 | UC-007 | API-017 |
| TC-139 | P0 | Acceptance | AC-037, US-022-AC3 | FR-051, FR-052, FR-053 | BR-014, BR-036, BR-037 | UC-007 | API-017 |
| TC-140 | P0 | Integration | AC-020, US-032-AC2 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-017 |
| TC-141 | P0 | Integration | AC-015, US-025-AC1 | FR-056, FR-058, FR-078 | BR-015, BR-048 | UC-008 | API-024, API-027, API-028 |
| TC-142 | P0 | Integration | AC-048, US-025-AC2 | FR-056, FR-058, FR-078 | BR-015, BR-048 | UC-008 | API-024, API-027, API-028 |
| TC-143 | P0 | Integration | AC-038, US-025-AC3 | FR-056, FR-058, FR-078 | BR-015, BR-038, BR-048 | UC-008 | API-024, API-027, API-028 |
| TC-144 | P0 | Integration | AC-038, US-026-AC1 | FR-057 | BR-038 | UC-008 | API-028 |
| TC-145 | P0 | Acceptance | AC-038, US-026-AC2 | FR-057 | BR-038 | UC-008 | API-028 |
| TC-146 | P0 | Acceptance | AC-015, US-025-AC1, US-025-AC2 | FR-056, FR-058, FR-078 | BR-015, BR-048 | UC-008 | API-028 |
| TC-147 | P0 | Acceptance | AC-048, US-025-AC2 | FR-056, FR-058, FR-078 | BR-015, BR-048 | UC-008 | API-027, API-028 |
| TC-148 | P0 | Integration | AC-015, US-025-AC1 | FR-056, FR-058, FR-078 | BR-015, BR-048 | UC-008 | API-028 |
| TC-149 | P0 | Integration | US-026-AC1 | FR-057 | BR-038 | UC-008 | API-028 |
| TC-150 | P0 | Integration | AC-002, US-003-AC1 | FR-004 | BR-002 | UC-001 | API-024 |
| TC-151 | P0 | Integration | AC-020, US-032-AC2, US-032-AC3 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-025, API-027, API-028 |
| TC-152 | P2 | System/E2E | US-027-AC1 | FR-059, FR-063 | BR-016 | UC-009, UC-010 | API-028 |
| TC-153 | P2 | System/E2E | AC-016, US-027-AC2 | FR-059, FR-063 | BR-016 | UC-009, UC-010 | API-028 |
| TC-154 | P2 | System/E2E | US-027-AC3 | FR-059, FR-063 | BR-016 | UC-009, UC-010 | API-028 |
| TC-155 | P2 | System/E2E | AC-039, US-043-AC1 | FR-060 | BR-039 | UC-009 | — |
| TC-156 | P2 | System/E2E | AC-039, US-043-AC2 | FR-060 | BR-039 | UC-009 | — |
| TC-157 | P2 | System/E2E | AC-016, US-027-AC2 | FR-059, FR-063 | BR-016 | UC-009, UC-010 | API-028 |
| TC-158 | P2 | System/E2E | US-027-AC2 | FR-059, FR-063 | BR-016 | UC-009, UC-010 | API-028 |
| TC-159 | P2 | Acceptance | US-027-AC2 | FR-059, FR-063, NFR-017 | BR-016, BR-046 | UC-009, UC-010 | API-028 |
| TC-160 | P2 | System/E2E | US-027-AC2 | FR-040, FR-059, FR-063 | BR-011, BR-016 | UC-004, UC-009, UC-010 | API-022 |
| TC-161 | P2 | System/E2E | AC-039, US-043-AC1, US-043-AC2 | FR-060 | BR-039 | UC-009 | — |
| TC-162 | P2 | System/E2E | US-027-AC1 | FR-059, FR-063 | BR-016 | UC-009, UC-010 | — |
| TC-163 | P2 | System/E2E | US-028-AC1 | FR-061, FR-062, FR-092, FR-093 | BR-017, BR-040 | UC-010 | API-029 |
| TC-164 | P2 | Acceptance | AC-017, US-028-AC2 | FR-061, FR-062, FR-092, FR-093 | BR-017, BR-040 | UC-010 | API-029 |
| TC-165 | P2 | Integration | AC-040, US-028-AC3 | FR-061, FR-062, FR-092, FR-093 | BR-017, BR-040 | UC-010 | API-029 |
| TC-166 | P2 | System/E2E | US-028-AC4 | FR-061, FR-062, FR-092, FR-093 | BR-017, BR-040 | UC-010 | API-029 |
| TC-167 | P2 | Acceptance | AC-017, US-028-AC2 | FR-061, FR-062, FR-092, FR-093 | BR-017, BR-040 | UC-010 | API-029 |
| TC-168 | P2 | Acceptance | AC-040, US-028-AC3 | FR-061, FR-062, FR-092, FR-093 | BR-017, BR-040 | UC-010 | API-029 |
| TC-169 | P2 | Integration | AC-046, US-035-AC2 | FR-070, FR-074 | BR-046 | UC-002, UC-008, UC-010 | API-029 |
| TC-170 | P2 | System/E2E | US-028-AC1 | FR-061, FR-062, FR-092, FR-093 | BR-017, BR-040 | UC-010 | — |
| TC-171 | P0 | Integration | AC-018, US-029-AC1 | FR-064 | BR-018 | UC-011 | API-030 |
| TC-172 | P0 | Integration | AC-018, US-029-AC2 | FR-064 | BR-018 | UC-011 | API-030 |
| TC-173 | P0 | Integration | AC-041, US-030-AC1 | FR-065 | BR-041 | UC-011 | API-030 |
| TC-174 | P0 | Integration | AC-042, US-037-AC1 | FR-079 | BR-042 | UC-011 | API-030 |
| TC-175 | P0 | Acceptance | AC-018, US-029-AC1 | FR-064 | BR-018 | UC-011 | API-030 |
| TC-176 | P0 | Acceptance | AC-042, US-037-AC1 | FR-079 | BR-042 | UC-011 | API-030 |
| TC-177 | P0 | Acceptance | AC-041, US-030-AC1 | FR-065 | BR-041 | UC-011 | API-030 |
| TC-178 | P0 | Integration | AC-020, US-032-AC2 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-030 |
| TC-179 | P0 | Integration | US-029-AC1 | FR-064 | BR-018 | UC-011 | API-030 |
| TC-180 | P2 | Integration | AC-019, US-031-AC1 | FR-066, FR-067, FR-080, FR-081 | BR-019, BR-043, BR-049 | UC-012 | API-014, API-022, API-031 |
| TC-181 | P2 | Integration | AC-043, US-031-AC2 | FR-066, FR-067, FR-080, FR-081 | BR-019, BR-043, BR-049 | UC-012 | API-014, API-022, API-031 |
| TC-182 | P2 | Integration | AC-049, US-031-AC3 | FR-066, FR-067, FR-080, FR-081 | BR-019, BR-043, BR-049 | UC-012 | API-014, API-022, API-031 |
| TC-183 | P2 | Integration | AC-043, US-031-AC4 | FR-066, FR-067, FR-080, FR-081 | BR-019, BR-043, BR-049 | UC-012 | API-014, API-022 |
| TC-184 | P2 | Acceptance | AC-019, US-031-AC1 | FR-066, FR-067, FR-080, FR-081 | BR-019, BR-043, BR-049 | UC-012 | API-031 |
| TC-185 | P2 | Integration | AC-019, US-031-AC1 | FR-066, FR-067, FR-080, FR-081, NFR-011 | BR-012, BR-019, BR-043, BR-049 | UC-012 | API-031 |
| TC-186 | P2 | System/E2E | AC-019, US-031-AC1 | FR-066, FR-067, FR-080, FR-081 | BR-019, BR-043, BR-049 | UC-012 | API-031 |
| TC-187 | P0 | System/E2E | US-032-AC1 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-003, API-013, API-014 |
| TC-188 | P0 | Integration | AC-020, US-032-AC2 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-014 |
| TC-189 | P0 | Integration | AC-020, US-032-AC3 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-014, API-017, API-028 |
| TC-190 | P0 | System/E2E | US-032-AC4 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-003, API-013, API-014 |
| TC-191 | P0 | Integration | AC-044, US-033-AC1 | FR-071, FR-072 | BR-021, BR-044 | UC-014 | API-006, API-007 |
| TC-192 | P0 | Integration | AC-044, US-033-AC2 | FR-071, FR-072 | BR-021, BR-044 | UC-014 | API-006, API-007 |
| TC-193 | P0 | Acceptance | AC-021, US-033-AC3 | FR-071, FR-072 | BR-021, BR-044 | UC-014 | API-006, API-007 |
| TC-194 | P0 | Acceptance | AC-021, US-033-AC4 | FR-071, FR-072 | BR-021, BR-044 | UC-014 | API-006, API-007 |
| TC-195 | P0 | System/E2E | US-035-AC1 | FR-070, FR-074 | BR-046 | UC-002, UC-008, UC-010 | API-018, API-028, API-029 |
| TC-196 | P0 | Acceptance | AC-046, US-035-AC2 | FR-070, FR-074 | BR-046 | UC-002, UC-008, UC-010 | API-018, API-028, API-029 |
| TC-197 | P0 | Acceptance | AC-020, US-032-AC2, US-032-AC3 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-004, API-007, API-014, API-015, API-016, API-017, API-019, API-020, API-021, API-022, API-023, API-025, API-026, API-027, API-028, API-030, API-031 |
| TC-198 | P0 | Unit | AC-046, US-035-AC2 | FR-070, FR-074 | BR-046 | UC-002, UC-008, UC-010 | API-018, API-028 |
| TC-199 | P0 | System/E2E | US-035-AC1 | FR-070, FR-074 | BR-046 | UC-002, UC-008, UC-010 | API-018 |
| TC-200 | P0 | Integration | US-033-AC1 | FR-071, FR-072 | BR-021, BR-044 | UC-014 | API-006 |
| TC-201 | P0 | Integration | AC-044, US-033-AC2 | FR-071, FR-072 | BR-021, BR-044 | UC-014 | API-007 |
| TC-202 | P0 | Integration | US-033-AC3 | FR-071, FR-072, NFR-018 | BR-021, BR-023, BR-044 | UC-014 | API-006 |
| TC-203 | P0 | Integration | US-032-AC4 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-013 |
| TC-204 | P0 | Acceptance | AC-022, US-034-AC1 | FR-075, FR-076, FR-097 | BR-022 | UC-016 | API-008, API-011 |
| TC-205 | P0 | Acceptance | AC-022, US-034-AC2 | FR-075, FR-076, FR-097 | BR-022 | UC-016 | API-008, API-011 |
| TC-206 | P0 | System/E2E | US-034-AC3 | FR-075, FR-076, FR-097 | BR-022 | UC-016 | API-011 |
| TC-207 | P0 | Unit | US-034-AC1, US-034-AC2 | FR-075, FR-076, FR-097 | BR-022 | UC-016 | — |
| TC-208 | P0 | System/E2E | US-034-AC3 | FR-075, FR-076, FR-097 | BR-022 | UC-016 | API-011 |
| TC-209 | P0 | Acceptance | AC-022, US-034-AC1, US-034-AC2 | FR-075, FR-076, FR-097 | BR-022 | UC-016 | — |
| TC-210 | P2 | Integration | US-036-AC1 | FR-077 | BR-023, BR-045 | UC-022 | API-032 |
| TC-211 | P2 | Acceptance | US-036-AC2 | FR-077 | BR-023, BR-045 | UC-022 | API-032 |
| TC-212 | P2 | Integration | US-036-AC3 | FR-077 | BR-023, BR-045 | UC-022 | API-032 |
| TC-213 | P0 | Usability study | AC-023, US-036-AC1 | FR-077 | BR-023, BR-045 | UC-022 | API-032 |
| TC-214 | P0 | Usability study | AC-045, US-036-AC1 | FR-077 | BR-023, BR-045 | UC-022 | API-032 |
| TC-215 | P0 | System/E2E | AC-005, US-010-AC2, US-013-AC1, US-014-AC1, US-014-AC2 | FR-020, FR-021, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029, FR-075, FR-087, FR-088 | BR-005, BR-006, BR-007, BR-022, BR-026 | UC-002, UC-015, UC-016 | API-018, API-019 |
| TC-216 | P0 | System/E2E | AC-009, AC-032, US-015-AC4, US-016-AC4, US-018-AC3 | FR-030, FR-031, FR-032, FR-033, FR-039, FR-040, FR-041, FR-045, FR-089, FR-090 | BR-008, BR-009, BR-010, BR-011, BR-032 | UC-003, UC-004, UC-006, UC-015 | API-020, API-022 |
| TC-217 | P2 | System/E2E | AC-013, AC-035, US-021-AC1, US-042-AC1, US-042-AC2 | FR-047, FR-048, FR-049, FR-050, FR-091 | BR-013, BR-034, BR-035 | UC-005 | API-020, API-021 |
| TC-218 | P0 | System/E2E | AC-012, AC-033, US-019-AC1, US-019-AC2 | FR-042, FR-043, FR-044 | BR-012, BR-033 | UC-004 | API-018, API-020 |
| TC-219 | P0 | System/E2E | US-018-AC3, US-019-AC4 | FR-040, FR-041, FR-042, FR-043, FR-044, FR-045, FR-090 | BR-011, BR-012, BR-033 | UC-004, UC-006 | API-022 |
| TC-220 | P0 | System/E2E | US-022-AC1, US-023-AC1, US-029-AC1, US-037-AC1 | FR-051, FR-052, FR-053, FR-054, FR-064, FR-079 | BR-014, BR-018, BR-036, BR-037, BR-042 | UC-007, UC-011 | API-017, API-030 |
| TC-221 | P0 | System/E2E | US-010-AC1, US-015-AC1, US-016-AC1, US-018-AC1 | FR-020, FR-021, FR-030, FR-031, FR-032, FR-033, FR-039, FR-040, FR-041, FR-045, FR-089, FR-090 | BR-005, BR-008, BR-009, BR-010, BR-011, BR-032 | UC-002, UC-003, UC-004, UC-006, UC-015 | API-018, API-020, API-022 |
| TC-222 | P1 | Acceptance | — | NFR-001 | BR-001 | — | API-010 |
| TC-223 | P1 | Acceptance | — | NFR-002 | BR-005 | — | API-018 |
| TC-224 | P1 | Acceptance | — | NFR-003 | BR-005 | — | API-018 |
| TC-225 | P1 | Acceptance | — | NFR-004 | BR-032 | — | API-020 |
| TC-226 | P2 | Acceptance | — | NFR-005 | BR-015 | — | API-028 |
| TC-227 | P1 | Acceptance | — | NFR-006 | BR-015 | — | API-028 |
| TC-228 | P1 | Acceptance | — | NFR-007 | BR-023 | — | API-010, API-018, API-020, API-028 |
| TC-229 | P1 | Acceptance | — | NFR-008 | BR-023 | — | API-001, API-002 |
| TC-230 | P1 | Acceptance | — | NFR-009 | BR-012 | — | API-002 |
| TC-231 | P1 | Acceptance | — | NFR-010 | BR-012 | — | API-014 |
| TC-232 | P0 | Integration | — | NFR-011 | BR-012 | — | API-010, API-014, API-017 |
| TC-233 | P1 | Integration | — | NFR-038 | BR-012 | — | API-014, API-017 |
| TC-234 | P1 | Acceptance | — | NFR-012 | BR-020 | — | API-001 |
| TC-235 | P1 | Acceptance | — | NFR-013 | BR-020 | — | — |
| TC-236 | P0 | Integration | AC-020 | NFR-014 | BR-020 | — | API-003 |
| TC-237 | P0 | Integration | — | NFR-015 | BR-004 | — | API-036 |
| TC-238 | P0 | Contract | — | NFR-016 | BR-020 | — | — |
| TC-239 | P0 | Acceptance | AC-046 | NFR-017 | BR-046 | — | API-018, API-028 |
| TC-240 | P1 | Acceptance | — | NFR-018 | BR-023 | — | API-032 |
| TC-241 | P1 | Usability study | — | NFR-019 | BR-005 | — | — |
| TC-242 | P1 | Usability study | — | NFR-020 | BR-005 | — | API-032 |
| TC-243 | P1 | Usability study | — | NFR-021 | BR-005 | — | API-032 |
| TC-244 | P2 | Acceptance | — | NFR-022 | BR-022 | — | — |
| TC-245 | P2 | Acceptance | — | NFR-023 | BR-022 | — | — |
| TC-246 | P2 | Acceptance | — | NFR-024 | BR-022 | — | — |
| TC-247 | P1 | System/E2E | — | NFR-025 | BR-007 | — | API-019 |
| TC-248 | P1 | Acceptance | — | NFR-026 | BR-022 | — | API-011 |
| TC-249 | P1 | System/E2E | — | NFR-027 | BR-023 | — | API-018 |
| TC-250 | P2 | System/E2E | — | NFR-028 | BR-023 | — | API-018 |
| TC-251 | P1 | System/E2E | — | NFR-029 | BR-004 | — | API-033 |
| TC-252 | P1 | Contract | — | NFR-030 | BR-023 | — | all (contract) |
| TC-253 | P1 | Acceptance | — | NFR-031 | BR-023 | — | — |
| TC-254 | P1 | Acceptance | — | NFR-032 | BR-023 | — | API-018, API-021, API-028 |
| TC-255 | P1 | Acceptance | AC-050 | NFR-033 | BR-050 | — | — |
| TC-256 | P1 | Acceptance | AC-050 | NFR-034 | BR-050 | — | — |
| TC-257 | P1 | Acceptance | — | NFR-035 | BR-050 | — | API-018, API-028 |
| TC-258 | P2 | Integration | — | NFR-036 | BR-050 | — | API-018, API-028 |
| TC-259 | P2 | Acceptance | — | NFR-037 | BR-050 | — | — |
| TC-260 | P1 | Contract | US-032-AC1 | FR-068, FR-069, FR-094, FR-095, NFR-030 | BR-020, BR-023 | UC-013 | all (contract) |
| TC-261 | P1 | Unit | — | NFR-008 | BR-023 | — | API-001 |
| TC-262 | P1 | Unit | — | NFR-008, NFR-009 | BR-012, BR-023 | — | API-002 |
| TC-263 | P1 | Unit | — | NFR-017 | BR-046 | — | API-001 |
| TC-264 | P0 | Integration | US-032-AC1 | FR-068, FR-069, FR-094, FR-095 | BR-020 | UC-013 | API-003 |
| TC-265 | P1 | Integration | — | NFR-009 | BR-012 | — | — |

## 5. API coverage

| API | Operation | FR (`x-fr`) | Test cases (named) |
|---|---|---|---|
| API-001 | `GET /health` | — | TC-229, TC-234, TC-261, TC-263 |
| API-002 | `GET /ready` | — | TC-229, TC-230, TC-262 |
| API-003 | `GET /v1/me` | FR-068, FR-069 | TC-187, TC-190, TC-236, TC-264 |
| API-004 | `GET /v1/me/preferences` | FR-073, FR-074, FR-075 | TC-042, TC-043, TC-197 |
| API-005 | `PUT /v1/me/preferences` | FR-073, FR-074, FR-075 | TC-042, TC-043 |
| API-006 | `POST /v1/me/deletion` | FR-071, FR-072 | TC-191, TC-192, TC-193, TC-194, TC-200, TC-202 |
| API-007 | `GET /v1/me/deletion` | FR-072 | TC-191, TC-192, TC-193, TC-194, TC-197, TC-201 |
| API-008 | `GET /v1/cities` | FR-001, FR-075 | TC-001, TC-002, TC-003, TC-204, TC-205 |
| API-009 | `GET /v1/categories` | FR-003, FR-021 | TC-061 |
| API-010 | `GET /v1/places` | FR-002, FR-004, FR-076 | TC-001, TC-002, TC-003, TC-009, TC-010, TC-011, TC-016, TC-026, TC-079, TC-080, TC-081, TC-085, TC-086, TC-087, TC-222, TC-228, TC-232 |
| API-011 | `GET /v1/places/{place_id}` | FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-076 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-010, TC-012, TC-013, TC-014, TC-015, TC-204, TC-205, TC-206, TC-208, TC-248 |
| API-012 | `POST /v1/trips` | FR-021, FR-023, FR-068 | TC-039, TC-040, TC-041, TC-047, TC-048, TC-049, TC-054 |
| API-013 | `GET /v1/trips` | FR-045, FR-068, FR-069 | TC-099, TC-104, TC-105, TC-187, TC-190, TC-203 |
| API-014 | `GET /v1/trips/{trip_id}` | FR-045, FR-055, FR-069 | TC-075, TC-076, TC-077, TC-078, TC-082, TC-083, TC-084, TC-097, TC-098, TC-099, TC-100, TC-101, TC-102, TC-107, TC-108, TC-121, TC-122, TC-123, TC-124, TC-125, TC-126, TC-127, TC-136, TC-180, TC-181, TC-182, TC-183, TC-187, TC-188, TC-189, TC-190, TC-197, TC-231, TC-232, TC-233 |
| API-015 | `PATCH /v1/trips/{trip_id}` | FR-042, FR-069 | TC-197 |
| API-016 | `DELETE /v1/trips/{trip_id}` | FR-046, FR-069 | TC-104, TC-105, TC-197 |
| API-017 | `GET /v1/trips/{trip_id}/stops/{stop_id}/place-card` | FR-005, FR-008, FR-051, FR-052, FR-053, FR-054 | TC-015, TC-131, TC-132, TC-133, TC-134, TC-135, TC-137, TC-138, TC-139, TC-140, TC-189, TC-197, TC-220, TC-232, TC-233 |
| API-018 | `POST /v1/trips/{trip_id}/plan-previews` | FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-029, FR-030, FR-031, FR-043, FR-044, FR-069, FR-070 | TC-009, TC-039, TC-040, TC-041, TC-044, TC-045, TC-046, TC-047, TC-048, TC-049, TC-050, TC-051, TC-052, TC-053, TC-054, TC-055, TC-056, TC-057, TC-058, TC-059, TC-060, TC-062, TC-063, TC-064, TC-065, TC-100, TC-101, TC-102, TC-108, TC-112, TC-113, TC-116, TC-117, TC-195, TC-196, TC-198, TC-199, TC-215, TC-218, TC-221, TC-223, TC-224, TC-228, TC-239, TC-249, TC-250, TC-254, TC-257, TC-258 |
| API-019 | `GET /v1/plan-previews/{preview_id}` | FR-027, FR-028, FR-029, FR-030, FR-031, FR-040, FR-044, FR-069 | TC-050, TC-051, TC-052, TC-053, TC-059, TC-062, TC-063, TC-064, TC-065, TC-066, TC-067, TC-068, TC-070, TC-071, TC-072, TC-074, TC-096, TC-109, TC-112, TC-130, TC-197, TC-215, TC-247 |
| API-020 | `PATCH /v1/plan-previews/{preview_id}` | FR-033, FR-034, FR-035, FR-036, FR-037, FR-038, FR-039, FR-044, FR-047, FR-069 | TC-075, TC-076, TC-077, TC-078, TC-079, TC-080, TC-081, TC-082, TC-083, TC-084, TC-086, TC-087, TC-088, TC-089, TC-090, TC-091, TC-092, TC-093, TC-094, TC-095, TC-100, TC-101, TC-102, TC-114, TC-115, TC-117, TC-121, TC-122, TC-123, TC-197, TC-216, TC-217, TC-218, TC-221, TC-225, TC-228 |
| API-023 | `DELETE /v1/plan-previews/{preview_id}` | FR-040, FR-069 | TC-197 |
| API-021 | `POST /v1/plan-previews/{preview_id}/regenerate` | FR-043, FR-044, FR-047, FR-048, FR-049, FR-050, FR-069, FR-070 | TC-117, TC-118, TC-119, TC-120, TC-124, TC-125, TC-126, TC-127, TC-128, TC-129, TC-197, TC-217, TC-254 |
| API-022 | `POST /v1/plan-previews/{preview_id}/accept` | FR-032, FR-040, FR-041, FR-042, FR-043, FR-050, FR-069 | TC-066, TC-067, TC-068, TC-069, TC-073, TC-075, TC-076, TC-077, TC-078, TC-082, TC-083, TC-084, TC-098, TC-100, TC-101, TC-102, TC-103, TC-106, TC-109, TC-110, TC-111, TC-117, TC-121, TC-122, TC-123, TC-160, TC-180, TC-181, TC-182, TC-183, TC-197, TC-216, TC-219, TC-221 |
| API-024 | `POST /v1/ai/sessions` | FR-056, FR-069, FR-074 | TC-141, TC-142, TC-143, TC-150 |
| API-025 | `GET /v1/ai/sessions/{session_id}` | FR-056, FR-069 | TC-151, TC-197 |
| API-026 | `DELETE /v1/ai/sessions/{session_id}` | FR-069, FR-071 | TC-197 |
| API-027 | `GET /v1/ai/sessions/{session_id}/messages` | FR-056, FR-069, FR-078 | TC-141, TC-142, TC-143, TC-147, TC-151, TC-197 |
| API-028 | `POST /v1/ai/sessions/{session_id}/messages` | FR-056, FR-057, FR-058, FR-059, FR-069, FR-070, FR-078 | TC-009, TC-141, TC-142, TC-143, TC-144, TC-145, TC-146, TC-147, TC-148, TC-149, TC-151, TC-152, TC-153, TC-154, TC-157, TC-158, TC-159, TC-189, TC-195, TC-196, TC-197, TC-198, TC-226, TC-227, TC-228, TC-239, TC-254, TC-257, TC-258 |
| API-029 | `POST /v1/ai/photo-identifications` | FR-004, FR-061, FR-062, FR-070 | TC-163, TC-164, TC-165, TC-166, TC-167, TC-168, TC-169, TC-195, TC-196 |
| API-030 | `GET /v1/trips/{trip_id}/handoff-links` | FR-064, FR-065, FR-069, FR-079 | TC-171, TC-172, TC-173, TC-174, TC-175, TC-176, TC-177, TC-178, TC-179, TC-197, TC-220 |
| API-031 | `GET /v1/trips/{trip_id}/stay-prices` | FR-066, FR-067, FR-069, FR-080, FR-081 | TC-180, TC-181, TC-182, TC-184, TC-185, TC-186, TC-197 |
| API-032 | `POST /v1/study/timing-events` | FR-077 | TC-210, TC-211, TC-212, TC-213, TC-214, TC-240, TC-242, TC-243 |
| API-033 | `GET /v1/admin/candidates` | FR-009, FR-011, FR-012 | TC-017, TC-018, TC-019, TC-037, TC-251 |
| API-034 | `GET /v1/admin/candidates/{place_id}` | FR-011, FR-012, FR-015, FR-019 | TC-020, TC-021, TC-022, TC-023, TC-027, TC-031, TC-032, TC-033, TC-037 |
| API-035 | `PATCH /v1/admin/candidates/{place_id}` | FR-011, FR-012, FR-019 | TC-020, TC-021, TC-022, TC-023, TC-031, TC-032, TC-033, TC-037 |
| API-036 | `POST /v1/admin/candidates/{place_id}/publish` | FR-013, FR-014, FR-015, FR-016, FR-019 | TC-024, TC-025, TC-026, TC-031, TC-032, TC-033, TC-034, TC-035, TC-036, TC-037, TC-237 |
| API-037 | `POST /v1/admin/places/{place_id}/unpublish` | FR-015, FR-017 | TC-028, TC-029, TC-037 |
| API-038 | `GET /v1/admin/imports` | FR-009, FR-010 | TC-017, TC-018, TC-019, TC-037 |
| API-039 | `GET /v1/admin/imports/{import_run_id}` | FR-009, FR-010 | TC-017, TC-018, TC-019, TC-037, TC-038 |
| API-040 | `GET /v1/admin/sources` | FR-012, FR-016 | TC-037 |
| API-041 | `POST /v1/admin/sources` | FR-012, FR-016 | TC-020, TC-021, TC-022, TC-023, TC-035, TC-037 |
| API-042 | `GET /v1/admin/cities/summary` | FR-018 | TC-030, TC-037 |

## 6. Use-case coverage

| UC | Name | Priority | Stories | Test cases |
|---|---|---|---|---|
| UC-001 | Search and view a place | Must | US-001, US-002, US-003 | TC-001, TC-002, TC-003, TC-004, TC-005, TC-006, TC-007, TC-008, TC-009, TC-010, TC-011, TC-012, TC-013, TC-014, TC-015, TC-016, TC-061, TC-150 |
| UC-002 | Generate a trip proposal | Must | US-010, US-012, US-013, US-014, US-035 | TC-039, TC-040, TC-041, TC-044, TC-045, TC-046, TC-047, TC-048, TC-049, TC-050, TC-051, TC-052, TC-053, TC-054, TC-055, TC-056, TC-057, TC-058, TC-059, TC-060, TC-061, TC-062, TC-063, TC-064, TC-065, TC-070, TC-071, TC-113, TC-169, TC-195, TC-196, TC-198, TC-199, TC-215, TC-221 |
| UC-003 | Edit a proposal | Must | US-016, US-017 | TC-075, TC-076, TC-077, TC-078, TC-079, TC-080, TC-081, TC-082, TC-083, TC-084, TC-085, TC-086, TC-087, TC-088, TC-089, TC-090, TC-091, TC-092, TC-093, TC-095, TC-216, TC-221 |
| UC-004 | Save an itinerary | Must | US-018, US-019 | TC-066, TC-067, TC-068, TC-069, TC-072, TC-073, TC-074, TC-095, TC-096, TC-097, TC-098, TC-099, TC-100, TC-101, TC-102, TC-103, TC-106, TC-107, TC-108, TC-109, TC-111, TC-112, TC-113, TC-114, TC-115, TC-116, TC-117, TC-118, TC-119, TC-120, TC-160, TC-216, TC-218, TC-219, TC-221 |
| UC-005 | Lock stops and regenerate a day | Should | US-021 | TC-118, TC-119, TC-120, TC-121, TC-122, TC-123, TC-124, TC-125, TC-126, TC-127, TC-128, TC-129, TC-130, TC-217 |
| UC-006 | Manage saved trips | Must | US-018, US-020 | TC-096, TC-097, TC-098, TC-099, TC-104, TC-105, TC-106, TC-107, TC-108, TC-109, TC-216, TC-219, TC-221 |
| UC-007 | Use a saved trip on site | Must | US-022, US-023, US-024 | TC-131, TC-132, TC-133, TC-134, TC-135, TC-136, TC-137, TC-138, TC-139, TC-220 |
| UC-008 | Ask the Guide a question | Must | US-025, US-026, US-035 | TC-141, TC-142, TC-143, TC-144, TC-145, TC-146, TC-147, TC-148, TC-149, TC-169, TC-195, TC-196, TC-198, TC-199 |
| UC-009 | Ask the Guide by voice | Should | US-027 | TC-152, TC-153, TC-154, TC-155, TC-156, TC-157, TC-158, TC-159, TC-160, TC-161, TC-162 |
| UC-010 | Identify a place from a photo | Should | US-028 | TC-152, TC-153, TC-154, TC-157, TC-158, TC-159, TC-160, TC-162, TC-163, TC-164, TC-165, TC-166, TC-167, TC-168, TC-169, TC-170, TC-195, TC-196, TC-198, TC-199 |
| UC-011 | Open a booking handoff | Must | US-029, US-030, US-037 | TC-171, TC-172, TC-173, TC-174, TC-175, TC-176, TC-177, TC-179, TC-220 |
| UC-012 | View indicative stay prices | Could | US-031 | TC-180, TC-181, TC-182, TC-183, TC-184, TC-185, TC-186 |
| UC-013 | Sign in and keep data private | Must | US-032 | TC-094, TC-110, TC-140, TC-151, TC-178, TC-187, TC-188, TC-189, TC-190, TC-197, TC-203, TC-260, TC-264 |
| UC-014 | Delete my account | Must | US-033 | TC-191, TC-192, TC-193, TC-194, TC-200, TC-201, TC-202 |
| UC-015 | Check plan feasibility (Plan Health) | Must | US-014, US-015 | TC-057, TC-062, TC-063, TC-064, TC-065, TC-066, TC-067, TC-068, TC-069, TC-070, TC-071, TC-072, TC-073, TC-074, TC-075, TC-076, TC-077, TC-078, TC-079, TC-080, TC-081, TC-082, TC-083, TC-084, TC-085, TC-086, TC-087, TC-088, TC-089, TC-090, TC-091, TC-092, TC-093, TC-095, TC-113, TC-215, TC-216, TC-221 |
| UC-016 | Set language and preferences | Must | US-011, US-034 | TC-042, TC-043, TC-204, TC-205, TC-206, TC-207, TC-208, TC-209, TC-215 |
| UC-017 | Import candidate places | Must | US-004 | TC-017, TC-018, TC-019, TC-038 |
| UC-018 | Review candidate content | Must | US-005, US-009 | TC-015, TC-020, TC-021, TC-022, TC-023, TC-031, TC-032, TC-033, TC-035 |
| UC-019 | Publish a place | Must | US-006 | TC-015, TC-020, TC-021, TC-022, TC-023, TC-024, TC-025, TC-026, TC-027, TC-034, TC-035, TC-036, TC-037 |
| UC-020 | Unpublish a place | Should | US-007 | TC-028, TC-029, TC-037 |
| UC-021 | View city coverage | Should | US-008 | TC-030 |
| UC-022 | Record study session measures | Should | US-036 | TC-210, TC-211, TC-212, TC-213, TC-214 |

## 7. FR and NFR coverage

| ID | Priority | Source BR | Test cases |
|---|---|---|---|
| FR-001 | Must | BR-001 | TC-001, TC-002, TC-003, TC-011, TC-016 |
| FR-002 | Must | BR-001 | TC-001, TC-002, TC-003, TC-011, TC-016 |
| FR-003 | Must | BR-001 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-012, TC-013, TC-014, TC-015, TC-061 |
| FR-004 | Must | BR-002 | TC-009, TC-010, TC-150 |
| FR-005 | Must | BR-003 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-012, TC-013, TC-014, TC-015 |
| FR-006 | Must | BR-024 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-012, TC-013, TC-014, TC-015 |
| FR-007 | Must | BR-025 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-012, TC-013, TC-014, TC-015 |
| FR-008 | Must | BR-047 | TC-004, TC-005, TC-006, TC-007, TC-008, TC-012, TC-013, TC-014, TC-015 |
| FR-009 | Must | BR-004 | TC-017, TC-018, TC-019, TC-038 |
| FR-010 | Must | BR-004 | TC-017, TC-018, TC-019, TC-038 |
| FR-011 | Must | BR-004 | TC-020, TC-021, TC-022, TC-023, TC-035 |
| FR-012 | Must | BR-004 | TC-020, TC-021, TC-022, TC-023, TC-035 |
| FR-013 | Must | BR-004 | TC-024, TC-025, TC-026, TC-027, TC-034, TC-036, TC-037 |
| FR-082 | Must | BR-004 | TC-024, TC-025, TC-026, TC-027, TC-034, TC-036, TC-037 |
| FR-014 | Must | BR-004 | TC-024, TC-025, TC-026, TC-027, TC-034, TC-036, TC-037 |
| FR-015 | Must | BR-004 | TC-024, TC-025, TC-026, TC-027, TC-034, TC-036, TC-037 |
| FR-016 | Must | BR-047 | TC-015, TC-020, TC-021, TC-022, TC-023, TC-035 |
| FR-083 | Must | BR-047 | TC-020, TC-021, TC-022, TC-023, TC-035 |
| FR-017 | Should | BR-002 | TC-028, TC-029, TC-037 |
| FR-018 | Should | BR-004 | TC-030 |
| FR-019 | Should | BR-004 | TC-031, TC-032, TC-033 |
| FR-084 | Should | BR-004 | TC-031, TC-032, TC-033 |
| FR-020 | Must | BR-005 | TC-039, TC-040, TC-041, TC-058, TC-061, TC-215, TC-221 |
| FR-021 | Must | BR-005 | TC-039, TC-040, TC-041, TC-061, TC-215, TC-221 |
| FR-022 | Must | BR-005 | TC-044, TC-045, TC-046, TC-058 |
| FR-023 | Must | BR-005 | TC-047, TC-048, TC-049, TC-054, TC-055 |
| FR-085 | Must | BR-005 | TC-047, TC-048, TC-049, TC-054, TC-055 |
| FR-086 | Must | BR-005 | TC-047, TC-048, TC-049, TC-054, TC-055 |
| FR-024 | Must | BR-005 | TC-050, TC-051, TC-052, TC-053, TC-056, TC-057, TC-058, TC-059, TC-060, TC-215 |
| FR-025 | Must | BR-006 | TC-050, TC-051, TC-052, TC-053, TC-056, TC-057, TC-058, TC-059, TC-060, TC-215 |
| FR-087 | Must | BR-006 | TC-050, TC-051, TC-052, TC-053, TC-056, TC-057, TC-058, TC-059, TC-060, TC-116, TC-215 |
| FR-026 | Should | BR-005 | TC-050, TC-051, TC-052, TC-053, TC-056, TC-057, TC-058, TC-059, TC-060, TC-215 |
| FR-027 | Must | BR-007 | TC-062, TC-063, TC-064, TC-065, TC-070, TC-071, TC-113, TC-215 |
| FR-028 | Must | BR-007 | TC-062, TC-063, TC-064, TC-065, TC-070, TC-071, TC-113, TC-215 |
| FR-088 | Must | BR-007 | TC-062, TC-063, TC-064, TC-065, TC-070, TC-071, TC-113, TC-215 |
| FR-029 | Must | BR-026 | TC-057, TC-062, TC-063, TC-064, TC-065, TC-070, TC-071, TC-113, TC-215 |
| FR-030 | Must | BR-008 | TC-066, TC-067, TC-068, TC-069, TC-072, TC-073, TC-074, TC-216, TC-221 |
| FR-031 | Must | BR-008 | TC-066, TC-067, TC-068, TC-069, TC-072, TC-073, TC-074, TC-216, TC-221 |
| FR-032 | Must | BR-009 | TC-066, TC-067, TC-068, TC-069, TC-072, TC-073, TC-074, TC-216, TC-221 |
| FR-033 | Must | BR-010 | TC-075, TC-076, TC-077, TC-078, TC-216, TC-221 |
| FR-034 | Must | BR-027 | TC-079, TC-080, TC-081 |
| FR-035 | Must | BR-028 | TC-082, TC-083, TC-084 |
| FR-036 | Must | BR-029 | TC-085, TC-086, TC-087, TC-091 |
| FR-037 | Must | BR-030 | TC-088, TC-089, TC-090, TC-092, TC-093 |
| FR-038 | Must | BR-031 | TC-088, TC-089, TC-090, TC-092, TC-093 |
| FR-039 | Must | BR-032 | TC-075, TC-076, TC-077, TC-078, TC-079, TC-080, TC-081, TC-082, TC-083, TC-084, TC-085, TC-086, TC-087, TC-088, TC-089, TC-090, TC-091, TC-092, TC-093, TC-095, TC-216, TC-221 |
| FR-089 | Must | BR-032 | TC-075, TC-076, TC-077, TC-078, TC-079, TC-080, TC-081, TC-082, TC-083, TC-084, TC-085, TC-086, TC-087, TC-088, TC-089, TC-090, TC-091, TC-092, TC-093, TC-216, TC-221 |
| FR-040 | Must | BR-011 | TC-096, TC-097, TC-098, TC-099, TC-106, TC-107, TC-108, TC-109, TC-160, TC-216, TC-219, TC-221 |
| FR-090 | Must | BR-011 | TC-096, TC-097, TC-098, TC-099, TC-106, TC-107, TC-108, TC-109, TC-216, TC-219, TC-221 |
| FR-041 | Must | BR-011 | TC-096, TC-097, TC-098, TC-099, TC-106, TC-107, TC-108, TC-109, TC-216, TC-219, TC-221 |
| FR-042 | Must | BR-012 | TC-095, TC-100, TC-101, TC-102, TC-103, TC-111, TC-112, TC-114, TC-117, TC-218, TC-219 |
| FR-043 | Must | BR-012 | TC-095, TC-100, TC-101, TC-102, TC-103, TC-111, TC-112, TC-113, TC-114, TC-115, TC-116, TC-117, TC-118, TC-119, TC-120, TC-218, TC-219 |
| FR-044 | Must | BR-033 | TC-095, TC-100, TC-101, TC-102, TC-103, TC-111, TC-112, TC-114, TC-115, TC-117, TC-118, TC-119, TC-120, TC-218, TC-219 |
| FR-045 | Must | BR-011 | TC-096, TC-097, TC-098, TC-099, TC-106, TC-107, TC-108, TC-109, TC-216, TC-219, TC-221 |
| FR-046 | Should | BR-011 | TC-104, TC-105 |
| FR-047 | Should | BR-034 | TC-121, TC-122, TC-123, TC-130, TC-217 |
| FR-091 | Should | BR-034 | TC-121, TC-122, TC-123, TC-130, TC-217 |
| FR-048 | Should | BR-013 | TC-118, TC-119, TC-120, TC-124, TC-125, TC-126, TC-127, TC-128, TC-129, TC-217 |
| FR-049 | Should | BR-035 | TC-118, TC-119, TC-120, TC-124, TC-125, TC-126, TC-127, TC-128, TC-129, TC-217 |
| FR-050 | Should | BR-013 | TC-118, TC-119, TC-120, TC-124, TC-125, TC-126, TC-127, TC-128, TC-129, TC-217 |
| FR-051 | Must | BR-014 | TC-131, TC-132, TC-133, TC-137, TC-138, TC-139, TC-220 |
| FR-052 | Must | BR-036 | TC-131, TC-132, TC-133, TC-137, TC-138, TC-139, TC-220 |
| FR-053 | Must | BR-037 | TC-131, TC-132, TC-133, TC-137, TC-138, TC-139, TC-220 |
| FR-054 | Must | BR-036 | TC-134, TC-135, TC-220 |
| FR-055 | Should | BR-014 | TC-136 |
| FR-056 | Must | BR-015 | TC-141, TC-142, TC-143, TC-146, TC-147, TC-148 |
| FR-078 | Must | BR-048 | TC-141, TC-142, TC-143, TC-146, TC-147, TC-148 |
| FR-057 | Must | BR-038 | TC-144, TC-145, TC-149 |
| FR-058 | Must | BR-015 | TC-141, TC-142, TC-143, TC-146, TC-147, TC-148 |
| FR-059 | Should | BR-016 | TC-152, TC-153, TC-154, TC-157, TC-158, TC-159, TC-160, TC-162 |
| FR-060 | Should | BR-039 | TC-155, TC-156, TC-161 |
| FR-061 | Should | BR-017 | TC-163, TC-164, TC-165, TC-166, TC-167, TC-168, TC-170 |
| FR-062 | Should | BR-040 | TC-163, TC-164, TC-165, TC-166, TC-167, TC-168, TC-170 |
| FR-063 | Should | BR-016 | TC-152, TC-153, TC-154, TC-157, TC-158, TC-159, TC-160, TC-162 |
| FR-092 | Should | BR-017 | TC-163, TC-164, TC-165, TC-166, TC-167, TC-168, TC-170 |
| FR-093 | Should | BR-017 | TC-163, TC-164, TC-165, TC-166, TC-167, TC-168, TC-170 |
| FR-064 | Must | BR-018 | TC-171, TC-172, TC-175, TC-179, TC-220 |
| FR-065 | Must | BR-041 | TC-173, TC-177 |
| FR-079 | Must | BR-042 | TC-174, TC-176, TC-220 |
| FR-066 | Could | BR-019 | TC-180, TC-181, TC-182, TC-183, TC-184, TC-185, TC-186 |
| FR-067 | Could | BR-043 | TC-180, TC-181, TC-182, TC-183, TC-184, TC-185, TC-186 |
| FR-081 | Could | BR-043 | TC-180, TC-181, TC-182, TC-183, TC-184, TC-185, TC-186 |
| FR-080 | Could | BR-049 | TC-180, TC-181, TC-182, TC-183, TC-184, TC-185, TC-186 |
| FR-068 | Must | BR-020 | TC-094, TC-110, TC-140, TC-151, TC-178, TC-187, TC-188, TC-189, TC-190, TC-197, TC-203, TC-260, TC-264 |
| FR-094 | Must | BR-020 | TC-094, TC-110, TC-140, TC-151, TC-178, TC-187, TC-188, TC-189, TC-190, TC-197, TC-203, TC-260, TC-264 |
| FR-069 | Must | BR-020 | TC-094, TC-110, TC-140, TC-151, TC-178, TC-187, TC-188, TC-189, TC-190, TC-197, TC-203, TC-260, TC-264 |
| FR-095 | Must | BR-020 | TC-094, TC-110, TC-140, TC-151, TC-178, TC-187, TC-188, TC-189, TC-190, TC-197, TC-203, TC-260, TC-264 |
| FR-070 | Must | BR-046 | TC-169, TC-195, TC-196, TC-198, TC-199 |
| FR-071 | Must | BR-021 | TC-191, TC-192, TC-193, TC-194, TC-200, TC-201, TC-202 |
| FR-072 | Must | BR-044 | TC-191, TC-192, TC-193, TC-194, TC-200, TC-201, TC-202 |
| FR-073 | Should | BR-005 | TC-042, TC-043 |
| FR-096 | Should | BR-005 | TC-042, TC-043 |
| FR-074 | Should | BR-046 | TC-169, TC-195, TC-196, TC-198, TC-199 |
| FR-075 | Must | BR-022 | TC-204, TC-205, TC-206, TC-207, TC-208, TC-209, TC-215 |
| FR-097 | Must | BR-022 | TC-204, TC-205, TC-206, TC-207, TC-208, TC-209 |
| FR-076 | Must | BR-022 | TC-204, TC-205, TC-206, TC-207, TC-208, TC-209 |
| FR-077 | Should | BR-023, BR-045 | TC-210, TC-211, TC-212, TC-213, TC-214 |
| NFR-001 | Must | BR-001 | TC-222 |
| NFR-002 | Must | BR-005 | TC-223 |
| NFR-003 | Must | BR-005 | TC-224 |
| NFR-004 | Must | BR-032 | TC-225 |
| NFR-005 | Should | BR-015 | TC-226 |
| NFR-006 | Must | BR-015 | TC-227 |
| NFR-007 | Must | BR-023 | TC-228 |
| NFR-008 | Must | BR-023 | TC-229, TC-261, TC-262 |
| NFR-009 | Must | BR-012 | TC-230, TC-262, TC-265 |
| NFR-010 | Must | BR-012 | TC-231 |
| NFR-011 | Must | BR-012 | TC-185, TC-232 |
| NFR-038 | Must | BR-012 | TC-233 |
| NFR-012 | Must | BR-020 | TC-234 |
| NFR-013 | Must | BR-020 | TC-235 |
| NFR-014 | Must | BR-020 | TC-236 |
| NFR-015 | Must | BR-004 | TC-037, TC-237 |
| NFR-016 | Must | BR-020 | TC-238 |
| NFR-017 | Must | BR-046 | TC-159, TC-239, TC-263 |
| NFR-018 | Must | BR-023 | TC-202, TC-240 |
| NFR-019 | Must | BR-005 | TC-241 |
| NFR-020 | Must | BR-005 | TC-242 |
| NFR-021 | Must | BR-005 | TC-243 |
| NFR-022 | Should | BR-022 | TC-244 |
| NFR-023 | Should | BR-022 | TC-245 |
| NFR-024 | Should | BR-022 | TC-246 |
| NFR-025 | Must | BR-007 | TC-247 |
| NFR-026 | Must | BR-022 | TC-248 |
| NFR-027 | Must | BR-023 | TC-249 |
| NFR-028 | Should | BR-023 | TC-250 |
| NFR-029 | Must | BR-004 | TC-251 |
| NFR-030 | Must | BR-023 | TC-252, TC-260 |
| NFR-031 | Must | BR-023 | TC-253 |
| NFR-032 | Must | BR-023 | TC-074, TC-254 |
| NFR-033 | Must | BR-050 | TC-255 |
| NFR-034 | Must | BR-050 | TC-256 |
| NFR-035 | Must | BR-050 | TC-257 |
| NFR-036 | Should | BR-050 | TC-258 |
| NFR-037 | Should | BR-050 | TC-259 |

## 8. [ORPHAN] and GAP list

None. Every criterion, FR, NFR, BR, use case and API operation has at least one case, and every case traces to a criterion.

## 9. Execution columns

At each run the owner copies §3 into `docs/07-verification/evidence/<run-id>/rtm-run.md`, fills Result (`PASS`/`FAIL`/`SKIP`/`NOT RUN`), Evidence (path under `docs/07-verification/evidence/<run-id>/TC-xxx/`) and Defect (`DEF-xxx` on `FAIL`). A `SKIP` needs a reason and the approver (cut features: `SKIP — cut (DEC-003)`, approved by the owner, reported to the mentor). The test report (kit `TestReport_IEEE_829_Prompt.md`) summarises the run.
