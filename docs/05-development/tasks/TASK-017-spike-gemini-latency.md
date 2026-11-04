---
task_id: TASK-017
wbs_element_id: WP-006
wbs_element_number: "1.2.2"
wbs_element_name: "SPK-002 Gemini selection latency and quota report"
title: "SPK-002: Gemini structured selection latency and free-tier quota"
type: spike
slice: horizontal
priority: P0
milestone: M1
wave: "Sprint 0 (M1)"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: Medium
depends_on: []
blocks: ["WP-016", "WP-043"]
requirement_links: ["US-013", "FR-024", "FR-025", "FR-026", "NFR-002", "NFR-036", "DEP-002"]
design_links: ["CMP-008", "CMP-012", "ADR-004", "ADR-011"]
deliverable: DEL-004
risk: RSK-003
branch: docs/spike-002-gemini-latency
pr_title: "docs(spike): SPK-002 Gemini selection latency and quota"
status: NOT STARTED
---

# TASK-017 — SPK-002: Gemini structured selection latency and free-tier quota

Parent: [`WBS.md`](../WBS.md) WP-006 (1.2.2). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

Measured p50/p95 latency and validation rate of one Gemini structured-output selection call (choose and rank supplied place IDs) for 1/2/3-day requests, the free-tier daily quota, and a recommended model and payload size.

## 2. Context

Gemini only selects and ranks supplied published place IDs [Source: ADR-004]; proposal p95 ≤ 60 s end to end (NFR-002); quota risk RSK-003.

## 3. Scope

**In scope (closed list)**

- Throw-away script with a synthetic list of 40–60 Hội An place summaries (IDs, names, categories, durations; no personal data)
- Pydantic schema for the response; count invalid or unknown IDs
- 20 calls per day length (1/2/3) in EN and VI; record latency p50/p95
- Record free-tier limits and whether inputs may be used by the provider (RSK-002)
- Report `docs/05-development/spikes/SPK-002-gemini-latency.md`

**Do not do (out of scope)**

- Do not send account IDs, contact data or locations (BR-046)
- Do not build the planning module
- Do not commit the API key

## 4. Inputs

- ADR-004
- ADR-011
- PRD NFR-002
- BRD RSK-002, RSK-003

## 5. Files and components touched

| Path | State |
|---|---|
| `docs/05-development/spikes/SPK-002-gemini-latency.md` | planned (WP-006) |
| `apps/api/scripts/spikes/spk002_gemini.py` | planned, throw-away |

## 6. Implementation guidance

- Use the Google GenAI SDK response schema feature; set temperature low; log only timings and counts.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-013, FR-024, FR-025, FR-026, NFR-002, NFR-036, DEP-002.

- **AC1.** Given 60 recorded calls, when the report is read, then it gives p50/p95 per day length, invalid-output rate, quota numbers and a recommended model.
- **AC2.** Given p95 > 30 s for 3-day requests, when the report recommends, then a mitigation (smaller candidate set, per-day calls) is stated for WP-043.

## 8. Verification

```sh
Report exists with the measurement table; `git grep -n "GEMINI_API_KEY=" -- . ':!*.example'` has no output
```

Expected: every command exits 0 (or prints nothing where stated). Any check not run is named in the PR body with the reason (AGENTS.md).

## 9. Definition of Done

- [ ] All acceptance criteria demonstrated, with evidence in the PR body
- [ ] Tests written for new logic and passing locally and in CI (or the reason they do not apply)
- [ ] CI jobs green (`gh pr checks <n> --watch`)
- [ ] PR ≤ ~400 changed lines (or the exception named in §14)
- [ ] Owner reviewed and approved the diff; merged with a merge commit on the owner's instruction
- [ ] `tasks/README.md` status, `progress.md` and traceability updated

## 10. Risks and mitigations

- Free-tier throttling during measurement → spread calls; report it

## 11. Rollback

Revert the docs PR.

## 12. Dependencies and ordering notes

- Must be true before start: none.
- Unblocks: WP-016, WP-043.

## 13. Execution guardrails

- Branch `docs/spike-002-gemini-latency` from up-to-date `main`; one PR titled `docs(spike): SPK-002 Gemini selection latency and quota`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
