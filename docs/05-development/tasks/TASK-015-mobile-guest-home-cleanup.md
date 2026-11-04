---
task_id: TASK-015
wbs_element_id: WP-065
wbs_element_number: "1.7.4"
wbs_element_name: "Account follow-ups"
title: "Guest mode limited to Home and onboarding; remove bell and weather"
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
blocks: ["WP-035"]
requirement_links: ["US-032", "FR-068"]
design_links: ["SCR-008", "SCR-040", "CMP-001"]
deliverable: DEL-008
risk: —
branch: feat/mobile-guest-home
pr_title: "feat(mobile): restrict guests to Home and remove bell and weather"
status: NOT STARTED
---

# TASK-015 — Guest mode limited to Home and onboarding; remove bell and weather

Parent: [`WBS.md`](../WBS.md) WP-065 (1.7.4). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

Guests see only Home and onboarding, any other entry shows the sign-in gate (SCR-040), and Home no longer shows the notification bell or the weather widget.

## 2. Context

Guest mode and Home follow-ups [Source: plan.md "Known code follow-ups"]; sign-in gate SCR-040 [Source: ui-ux README].

## 3. Scope

**In scope (closed list)**

- Route guard: guests may open `/`, `/onboarding`, `/home`, auth routes; other routes redirect to the sign-in gate
- Sign-in gate sheet (SCR-040) with VI/EN text
- Remove bell and weather widget from `home.tsx`

**Do not do (out of scope)**

- Do not build search or city sheet (WP-035)
- Do not add notifications or weather elsewhere
- Do not change Clerk flows

## 4. Inputs

- docs/04-design/ui-ux/README.md SCR-008, SCR-040, m01 wireframe
- apps/mobile/src/app/_layout.tsx
- apps/mobile/src/app/home.tsx

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/mobile/src/app/_layout.tsx` | existing |
| `apps/mobile/src/app/home.tsx` | existing |
| `apps/mobile/src/features/auth/SignInGate.tsx` | planned (SCR-040) |

## 6. Implementation guidance

- Guard in one place (layout) rather than per screen.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-032, FR-068.

- **AC1.** Given a guest on Home, when they tap Profile or Settings, then the sign-in gate appears and the protected screen does not open.
- **AC2.** Given a signed-in user, when they open Profile and Settings, then the screens open.
- **AC3.** Given the Home screen, when it renders, then no bell icon and no weather widget are shown.

## 8. Verification

```sh
cd apps/mobile && npm ci
npm run typecheck
npm run check:dependencies
Manual check as guest and as signed-in user
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

- Deep links bypass the guard → test `/profile` deep link

## 11. Rollback

Revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: TASK-012 (SS, shared files).
- Unblocks: WP-035.

## 13. Execution guardrails

- Branch `feat/mobile-guest-home` from up-to-date `main`; one PR titled `feat(mobile): restrict guests to Home and remove bell and weather`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
