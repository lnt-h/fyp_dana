---
task_id: TASK-016
wbs_element_id: WP-005
wbs_element_number: "1.2.1"
wbs_element_name: "SPK-001 LiteAPI coverage and terms report"
title: "SPK-001: LiteAPI coverage, rates and terms for the five cities"
type: spike
slice: horizontal
priority: P3
milestone: M1
wave: "Sprint 0 (M1)"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: High
depends_on: []
blocks: ["WP-073"]
requirement_links: ["US-031", "FR-066", "FR-067", "FR-080", "FR-081", "DEP-005"]
design_links: ["CMP-011", "CMP-013", "API-031", "ADR-006"]
deliverable: DEL-004
risk: RSK-004
branch: docs/spike-001-liteapi
pr_title: "docs(spike): SPK-001 LiteAPI coverage and terms"
status: NOT STARTED
---

# TASK-016 — SPK-001: LiteAPI coverage, rates and terms for the five cities

Parent: [`WBS.md`](../WBS.md) WP-005 (1.2.1). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

A written go/no-go for indicative stay prices (WP-073) based on measured LiteAPI sandbox coverage for the five cities, rate realism, display and caching terms and rate limits.

## 2. Context

SPK-001 time-boxed ≤ 2 days in SRC-100; time-box here 1 day. Prices are Could and first in the cut order (DEC-003); never stored (ADR-006).

## 3. Scope

**In scope (closed list)**

- Sandbox key; for each city one 1-night and one 2-night query for dates in the study window
- Count hotels returned, check rate fields, currency, retrieval timestamp
- Read terms on display, caching and attribution; note rate limits
- Fallback note on Hotelbeds
- Report `docs/05-development/spikes/SPK-001-liteapi.md` with recommendation and effect on WP-073

**Do not do (out of scope)**

- Do not write production adapter code or persist any rate
- Do not commit the API key or raw responses with personal data
- Do not exceed the 1-day time-box

## 4. Inputs

- BRD DEP-005
- ADR-006
- openapi.yaml API-031

## 5. Files and components touched

| Path | State |
|---|---|
| `docs/05-development/spikes/SPK-001-liteapi.md` | planned (WP-005) |
| `apps/api/scripts/spikes/spk001_liteapi.py` | planned, throw-away (optional) |

## 6. Implementation guidance

- Keep the probe script outside the app package; read the key from the environment.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-031, FR-066, FR-067, FR-080, FR-081, DEP-005.

- **AC1.** Given the spike is done, when the report is read, then it states hotels found per city, sample rate fields, terms relevant to display/caching, rate limits and a go/no-go.
- **AC2.** Given a no-go, when WP-073 is reviewed, then it is marked cut with the reason.

## 8. Verification

```sh
Report exists and links DEP-005; `git grep -n "LITEAPI_KEY=" -- . ':!*.example'` has no output
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

- Sandbox data not representative → state it in the report

## 11. Rollback

Revert the docs PR.

## 12. Dependencies and ordering notes

- Must be true before start: none.
- Unblocks: WP-073.

## 13. Execution guardrails

- Branch `docs/spike-001-liteapi` from up-to-date `main`; one PR titled `docs(spike): SPK-001 LiteAPI coverage and terms`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
