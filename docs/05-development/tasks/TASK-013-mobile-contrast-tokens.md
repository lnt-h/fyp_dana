---
task_id: TASK-013
wbs_element_id: WP-064
wbs_element_number: "1.7.3"
wbs_element_name: "Contrast tokens and accessibility labels"
title: "Add WCAG AA text tokens textMuted and tealText and apply them"
type: feature
slice: horizontal
priority: P2
milestone: M2
wave: "Sprint 1 (may start in M0/M1 slack)"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 0.5
estimate_hours: 4
estimate_confidence: High
depends_on: []
blocks: []
requirement_links: ["NFR-023", "NFR-024"]
design_links: ["ui-ux README §5.1", "apps/mobile/src/theme/colors.ts"]
deliverable: DEL-008
risk: —
branch: fix/mobile-contrast-tokens
pr_title: "fix(mobile): add AA text colour tokens for muted and teal text"
status: NOT STARTED
---

# TASK-013 — Add WCAG AA text tokens textMuted and tealText and apply them

Parent: [`WBS.md`](../WBS.md) WP-064 (1.7.3). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

Normal text that used failing colours uses `textMuted` #5E7585 or `tealText` #00788F, so all normal text on built screens reaches a contrast ratio ≥ 4.5:1.

## 2. Context

Contrast follow-up [Source: plan.md "Known code follow-ups"]; NFR-023 WCAG 2.1 SC 1.4.3. Horizontal slice justified: shared design tokens.

## 3. Scope

**In scope (closed list)**

- Add the two tokens to `colors.ts`
- Replace text usages of the failing colours (audioTeal as text, muted greys) on built screens
- Keep non-text uses (fills, switch tracks) unchanged

**Do not do (out of scope)**

- Do not redesign screens
- Do not change brand colours used for fills
- Do not touch i18n files

## 4. Inputs

- docs/04-design/ui-ux/README.md §5.1 token table
- apps/mobile/src/theme/colors.ts

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/mobile/src/theme/colors.ts` | existing |
| `apps/mobile/src/features/auth/` | existing |
| `apps/mobile/src/features/account/AccountUI.tsx` | existing |
| `apps/mobile/src/app/onboarding.tsx` | existing |

## 6. Implementation guidance

- Check each pair with a contrast calculator against its real background (#FFFFFF or surface token).
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: NFR-023, NFR-024.

- **AC1.** Given the built screens, when each text colour/background pair is checked, then every normal-text pair is ≥ 4.5:1.
- **AC2.** Given selected chips and switch tracks, when they render, then they keep `audioTeal` as fill.

## 8. Verification

```sh
cd apps/mobile && npm ci
npm run typecheck
npm run check:dependencies
grep -rn "audioTeal" apps/mobile/src | grep -i "color:" (review each remaining text use)
Manual contrast check recorded in the PR (pair, ratio)
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

- Missed usages → grep by token name

## 11. Rollback

Revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: none.
- Unblocks: nothing directly.

## 13. Execution guardrails

- Branch `fix/mobile-contrast-tokens` from up-to-date `main`; one PR titled `fix(mobile): add AA text colour tokens for muted and teal text`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
