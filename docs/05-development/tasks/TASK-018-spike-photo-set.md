---
task_id: TASK-018
wbs_element_id: WP-007
wbs_element_number: "1.2.3"
wbs_element_name: "SPK-003 Photo identification feasibility and photo-set protocol"
title: "SPK-003: photo identification pilot and photo-set protocol"
type: spike
slice: horizontal
priority: P2
milestone: M1
wave: "Sprint 0 (M1)"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: Medium
depends_on: []
blocks: ["WP-072"]
requirement_links: ["US-028", "FR-061", "FR-062", "MET-009", "ASM-009", "ASM-011"]
design_links: ["CMP-010", "CMP-022", "ADR-008", "API-029"]
deliverable: DEL-004
risk: RSK-004
branch: docs/spike-003-photo-set
pr_title: "docs(spike): SPK-003 photo identification pilot and photo-set protocol"
status: NOT STARTED
---

# TASK-018 — SPK-003: photo identification pilot and photo-set protocol

Parent: [`WBS.md`](../WBS.md) WP-007 (1.2.3). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

A pilot top-1 accuracy of Gemini vision choosing among published-place candidates within 300 m on ≥ 20 own Hội An photos, plus a written protocol for collecting the ≥ 100-photo set (≥ 20 per city).

## 2. Context

Photo identification is Should, second in the cut order (DEC-003); candidates limited to published places within 300 m (ADR-008, ASM-009); MET-009 target ≥ 85%.

## 3. Scope

**In scope (closed list)**

- ≥ 20 photos taken by the owner or Wikimedia Commons with compatible licence, metadata stripped
- Candidate list per photo = places within 300 m from a manual coordinate
- Measure top-1 accuracy and latency
- Protocol: photo sources and licences, per-city counts, lighting/angle variety, labelling, storage, consent if people appear
- Report `docs/05-development/spikes/SPK-003-photo-set.md` with go/no-go

**Do not do (out of scope)**

- Do not upload photos with faces or EXIF location
- Do not build the endpoint or mobile camera flow
- Do not store images in git (keep them local or in a private bucket)

## 4. Inputs

- ADR-008
- BRD MET-009, ASM-009, ASM-011

## 5. Files and components touched

| Path | State |
|---|---|
| `docs/05-development/spikes/SPK-003-photo-set.md` | planned (WP-007) |
| `apps/api/scripts/spikes/spk003_photo.py` | planned, throw-away |

## 6. Implementation guidance

- Send only the image and candidate summaries; never the traveler's location to the model (BR-046).
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-028, FR-061, FR-062, MET-009, ASM-009, ASM-011.

- **AC1.** Given ≥ 20 pilot photos, when the pilot runs, then the report gives top-1 accuracy, latency and failure examples.
- **AC2.** Given the protocol, when it is read, then it fixes the ≥ 100-photo set composition (≥ 20 per city) and licence rules.

## 8. Verification

```sh
Report exists; `git ls-files | grep -iE "\.(jpg|jpeg|heic|png)$" | grep -i spike` has no output
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

- Too few published places in M1 → use the CSV research sheet candidates; note the bias

## 11. Rollback

Revert the docs PR.

## 12. Dependencies and ordering notes

- Must be true before start: none.
- Unblocks: WP-072.

## 13. Execution guardrails

- Branch `docs/spike-003-photo-set` from up-to-date `main`; one PR titled `docs(spike): SPK-003 photo identification pilot and photo-set protocol`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
