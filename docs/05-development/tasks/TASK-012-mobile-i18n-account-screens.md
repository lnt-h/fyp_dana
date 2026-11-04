---
task_id: TASK-012
wbs_element_id: WP-063
wbs_element_number: "1.7.2"
wbs_element_name: "VI/EN localisation of the traveler app"
title: "Localise Home, Profile, Settings and Preferences; add language setting"
type: feature
slice: vertical
priority: P2
milestone: M2
wave: "Sprint 1"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: Medium
depends_on: ["TASK-011 (FS)"]
blocks: ["WP-060"]
requirement_links: ["US-034", "FR-075", "FR-076", "FR-097", "NFR-022", "NFR-026"]
design_links: ["CMP-023", "SCR-008", "SCR-009", "SCR-010", "SCR-011", "SCR-012", "SCR-039"]
deliverable: DEL-008
risk: —
branch: feat/mobile-i18n-account
pr_title: "feat(mobile): localise account screens and add language setting"
status: NOT STARTED
---

# TASK-012 — Localise Home, Profile, Settings and Preferences; add language setting

Parent: [`WBS.md`](../WBS.md) WP-063 (1.7.2). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

Home, Profile, Edit profile, Settings and Travel preferences use VI/EN resources, the Đà Nẵng-specific copy is replaced by city-neutral copy, and Settings has a Language row (SCR-039) that persists the choice.

## 2. Context

Copy is Đà Nẵng-specific and English-only [Source: plan.md "Known code follow-ups"]; SCR-039 Language setting [Source: ui-ux README].

## 3. Scope

**In scope (closed list)**

- Move strings of `home.tsx`, `profile.tsx`, `edit-profile.tsx`, `settings.tsx`, `travel-preferences.tsx`, `features/account/*`
- City-neutral copy (five cities)
- Language row: System / Tiếng Việt / English, stored locally
- Locale value exposed for API calls (`Locale` parameter) for later use

**Do not do (out of scope)**

- Do not change Home layout beyond removing city-specific copy (Home clean-up is TASK-015)
- Do not add pace/modes (TASK-014)
- Do not call preferences API (WP-075)

## 4. Inputs

- docs/04-design/ui-ux/README.md SCR-008..SCR-012, SCR-039, m13 wireframe
- TASK-011 i18n setup

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/mobile/src/app/home.tsx` | existing |
| `apps/mobile/src/app/profile.tsx` | existing |
| `apps/mobile/src/app/edit-profile.tsx` | existing |
| `apps/mobile/src/app/settings.tsx` | existing |
| `apps/mobile/src/app/travel-preferences.tsx` | existing |
| `apps/mobile/src/features/account/AccountUI.tsx` | existing |
| `apps/mobile/src/features/account/TravelPreferences.tsx` | existing |
| `apps/mobile/src/i18n/locales/vi.json` | planned (TASK-011) |
| `apps/mobile/src/i18n/locales/en.json` | planned (TASK-011) |

## 6. Implementation guidance

- Interest and travel-type option values stay stable codes; only labels are translated.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-034, FR-075, FR-076, FR-097, NFR-022, NFR-026.

- **AC1.** Given Language set to Tiếng Việt in Settings, when the user opens every account screen, then all text is Vietnamese and stays so after an app restart.
- **AC2.** Given Language set to System on an English device, when the screens open, then text is English.
- **AC3.** Given the Home screen, when it is shown, then no copy names Đà Nẵng as the only city.

## 8. Verification

```sh
cd apps/mobile && npm ci
npm run typecheck
npm run check:dependencies
Manual: switch the Language row and restart the app on a device
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

- Persisted locale storage choice → AsyncStorage key only, no personal data

## 11. Rollback

Revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: TASK-011 (FS).
- Unblocks: WP-060.

## 13. Execution guardrails

- Branch `feat/mobile-i18n-account` from up-to-date `main`; one PR titled `feat(mobile): localise account screens and add language setting`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
