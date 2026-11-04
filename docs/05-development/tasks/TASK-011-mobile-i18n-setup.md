---
task_id: TASK-011
wbs_element_id: WP-063
wbs_element_number: "1.7.2"
wbs_element_name: "VI/EN localisation of the traveler app"
title: "Set up i18next VI/EN and move onboarding and auth strings"
type: feature
slice: vertical
priority: P1
milestone: M2
wave: "Sprint 1"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: Medium
depends_on: []
blocks: ["TASK-012", "WP-060"]
requirement_links: ["US-034", "FR-075", "FR-076", "FR-097", "NFR-022", "NFR-026"]
design_links: ["CMP-023", "SCR-001", "SCR-002", "SCR-003", "SCR-004", "SCR-005", "SCR-006", "SCR-007"]
deliverable: DEL-008
risk: —
branch: feat/mobile-i18n-setup
pr_title: "feat(mobile): add i18next VI/EN and localise onboarding and auth"
status: NOT STARTED
---

# TASK-011 — Set up i18next VI/EN and move onboarding and auth strings

Parent: [`WBS.md`](../WBS.md) WP-063 (1.7.2). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

The app uses i18next with reviewed `vi` and `en` resources; onboarding and all auth screens show no hard-coded user-facing string and follow the device locale by default.

## 2. Context

Built screens are English-only [Source: plan.md "Known code follow-ups"]; CMP-023 i18next [Source: SAD]. VI and EN are both reviewed launch locales, not machine translations [Source: AGENTS.md].

## 3. Scope

**In scope (closed list)**

- Install `i18next`, `react-i18next`, `expo-localization` with `npx expo install` where applicable
- `src/i18n/index.ts` init; `src/i18n/locales/vi.json`, `en.json`
- Move strings of `index.tsx`, `onboarding.tsx`, `(auth)/welcome|login|register.tsx`, `sso-callback.tsx`, `auth-task.tsx`, `features/auth/authErrors.ts`
- Accessibility labels moved too (NFR-022)
- Owner reviews the Vietnamese text

**Do not do (out of scope)**

- Do not localise Home, Profile, Settings, Preferences (TASK-012)
- Do not add a language switch UI (TASK-012)
- Do not machine-translate without owner review
- Do not change layouts or flows

## 4. Inputs

- docs/04-design/ui-ux/README.md (copy rules, locales vi-VN/en-US)
- apps/mobile/src/app/*
- AGENTS.md bilingual rules

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/mobile/package.json` | existing |
| `apps/mobile/src/i18n/index.ts` | planned (CMP-023) |
| `apps/mobile/src/i18n/locales/vi.json` | planned |
| `apps/mobile/src/i18n/locales/en.json` | planned |
| `apps/mobile/src/app/_layout.tsx` | existing |
| `apps/mobile/src/app/onboarding.tsx` | existing |
| `apps/mobile/src/app/(auth)/welcome.tsx` | existing |
| `apps/mobile/src/app/(auth)/login.tsx` | existing |
| `apps/mobile/src/app/(auth)/register.tsx` | existing |
| `apps/mobile/src/features/auth/authErrors.ts` | existing |

## 6. Implementation guidance

- Keys by screen (`auth.login.title`); interpolation for dynamic values; no string concatenation.
- Fallback language `en`; Vietnamese diacritics must render with the app fonts (NFR-026).
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-034, FR-075, FR-076, FR-097, NFR-022, NFR-026.

- **AC1.** Given a device set to Vietnamese, when the user opens onboarding, welcome, login and register, then all visible text and accessibility labels are Vietnamese with correct diacritics.
- **AC2.** Given a device set to English, when the same screens open, then all text is English.
- **AC3.** Given the source tree, when a search for user-facing string literals in the touched files runs, then none remain outside the locale files.

## 8. Verification

```sh
cd apps/mobile && npm ci
npm run typecheck
npm run check:dependencies
Manual: Expo Go on a device switched between vi and en
grep -nE ">[A-Z][a-z]+ [a-z]+" apps/mobile/src/app/onboarding.tsx apps/mobile/src/app/\(auth\)/*.tsx (expect no output)
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

- Large diff → if > 400 lines, split auth and onboarding into two PRs

## 11. Rollback

Revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: none.
- Unblocks: TASK-012, WP-060.

## 13. Execution guardrails

- Branch `feat/mobile-i18n-setup` from up-to-date `main`; one PR titled `feat(mobile): add i18next VI/EN and localise onboarding and auth`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
