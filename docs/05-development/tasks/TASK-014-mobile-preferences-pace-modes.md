---
task_id: TASK-014
wbs_element_id: WP-065
wbs_element_number: "1.7.4"
wbs_element_name: "Account follow-ups"
title: "Add pace and travel modes to Travel preferences (SCR-011)"
type: feature
slice: vertical
priority: P2
milestone: M2
wave: "Sprint 1"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 0.5
estimate_hours: 4
estimate_confidence: High
depends_on: ["TASK-012 (SS, shared files)"]
blocks: ["WP-075", "WP-048"]
requirement_links: ["US-010", "FR-073"]
design_links: ["SCR-011", "OQ-065 (closed A-027)", "CMP-001"]
deliverable: DEL-008
risk: —
branch: feat/mobile-preferences-pace-modes
pr_title: "feat(mobile): add pace and travel modes to travel preferences"
status: NOT STARTED
---

# TASK-014 — Add pace and travel modes to Travel preferences (SCR-011)

Parent: [`WBS.md`](../WBS.md) WP-065 (1.7.4). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

The Travel preferences screen lets the traveler choose a pace and one or more travel modes (walk, drive) in the existing chip pattern, stored with the other preferences.

## 2. Context

The planner needs pace and travel modes (US-010 AC3, US-011); OQ-065 closed by A-027: add them to SCR-011 in the existing chip pattern [Source: ui-ux README OQ-065]. Routing supports WALK and DRIVE only [Source: BRD §5.2].

## 3. Scope

**In scope (closed list)**

- Pace options with the openapi `Pace` codes RELAXED, BALANCED, PACKED
- Travel modes with the openapi codes WALK and DRIVE (`allowed_modes`, multi-select, at least one)
- Store in the same place as interests today (Clerk `unsafeMetadata`) until the preferences API exists (WP-075)
- VI/EN labels

**Do not do (out of scope)**

- Do not call API-004/API-005 (WP-075)
- Do not add transit, motorcycle or bicycle (out of scope)
- Do not change interests/travel type behaviour

## 4. Inputs

- docs/04-design/api/openapi.yaml preferences schema (codes)
- docs/04-design/ui-ux/README.md SCR-011, OQ-065
- apps/mobile/src/features/account/TravelPreferences.tsx

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/mobile/src/features/account/TravelPreferences.tsx` | existing |
| `apps/mobile/src/features/account/AccountContext.tsx` | existing |
| `apps/mobile/src/i18n/locales/vi.json` | planned (TASK-011) |
| `apps/mobile/src/i18n/locales/en.json` | planned (TASK-011) |

## 6. Implementation guidance

- Use the enum codes of the OpenAPI preferences schema so WP-075 can sync without mapping.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-010, FR-073.

- **AC1.** Given the Travel preferences screen, when the traveler selects a pace and modes and saves, then the choice persists after restart.
- **AC2.** Given both modes deselected, when the traveler tries to save, then the screen keeps at least one mode selected and explains why.

## 8. Verification

```sh
cd apps/mobile && npm ci
npm run typecheck
npm run check:dependencies
Manual check on a device
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

- Enum codes differ from openapi → follow openapi

## 11. Rollback

Revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: TASK-012 (SS, shared files).
- Unblocks: WP-075, WP-048.

## 13. Execution guardrails

- Branch `feat/mobile-preferences-pace-modes` from up-to-date `main`; one PR titled `feat(mobile): add pace and travel modes to travel preferences`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
