# 07 — Verification

Phase 7 verification planning for Gonarra (IEEE 829-2008). Owner: Lê Ngọc Tấn Hiền. Approver: trantrongminh
([Pending]). All documents are version 0.1, Draft, dated 2026-11-04. Nothing has been executed yet.

| File | Content | Kit prompt (adapted copy in `docs/00-governance/prompt-templates/verification/`) |
|---|---|---|
| [`TEST_PLAN.md`](TEST_PLAN.md) | Master test plan TP-GONARRA-v0.1: scope, items, features (not) tested, approach per level, evaluation sets (ASM-011), failure injection (MET-006), security/privacy, WCAG 2.1 AA, bilingual checks, entry/exit/suspension criteria, environments, schedule M1–M6, risks, self-check | `TestPlan_IEEE 829-2008_prompt.md` v2.0 |
| [`TEST_CASES.md`](TEST_CASES.md) | 265 test cases TC-001..TC-265 with traces, level, priority, preconditions, steps, data, expected result, evidence method, automation target and cuttable flag | `TestCase_RTM_IEEE_829_Prompt.md` v2.0 |
| [`RTM.md`](RTM.md) | Two-way traceability BR → FR/NFR → US/AC → UC → API → TC with coverage counts and `[ORPHAN]` list (0) | `TestCase_RTM_IEEE_829_Prompt.md` v2.0 |
| [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md) | Usability study protocol (10–15 participants, ≥ 4 per language, mid-January 2027), tasks SC-01..SC-03 (+ HA-02 variant), measures MET-001..003 and SUS, consent forms and session script in EN and VI; items pending OQ-004 marked | Part of the test plan (§6.1.6) |
| `evidence/` | Created at the first run: `evidence/<run-id>/` per run, `defects.md` | — |

Coverage at design time (from `RTM.md` §1): 93/93 Must user-story criteria and 40/40 Must BRD acceptance criteria have
at least one case; all 97 FRs, 38 NFRs, 50 BRs, 22 use cases and 42 API operations are covered.

Regenerating the RTM: the matrix is derived mechanically from the ID tables of `BRD.md`, `PRD.md`, `user-stories.md`,
`use-cases.md`, `openapi.yaml` and `TEST_CASES.md`. The generator script was throw-away; when any of these changes,
regenerate with an equivalent script and keep the derivation rules stated in `RTM.md`.
