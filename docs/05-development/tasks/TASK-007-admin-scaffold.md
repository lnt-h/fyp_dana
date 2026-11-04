---
task_id: TASK-007
wbs_element_id: WP-028
wbs_element_number: "1.4.3.1"
wbs_element_name: "Curator admin scaffold with curator sign-in (SCR-101)"
title: "Curator admin SPA scaffold with Clerk curator-role gate and CI job"
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
blocks: ["WP-029", "WP-030", "WP-083"]
requirement_links: ["NFR-015", "NFR-029", "US-004"]
design_links: ["CMP-002", "SCR-101", "ADR-005", "ADR-001", "OQ-036 (curator claim location)"]
deliverable: DEL-007
risk: —
branch: feat/admin-scaffold
pr_title: "feat(admin): scaffold curator SPA with Clerk curator gate"
status: NOT STARTED
---

# TASK-007 — Curator admin SPA scaffold with Clerk curator-role gate and CI job

Parent: [`WBS.md`](../WBS.md) WP-028 (1.4.3.1). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

`apps/admin` is a React + Vite + TypeScript app where a Clerk user with the curator role reaches an empty Candidates page and any other user sees access denied; CI builds it.

## 2. Context

Curator SPA is a separate deployable talking only to `/v1` [Source: ADR-001; SAD CMP-002]. Curator role comes from the Clerk JWT claim (OQ-036 in SAD).

## 3. Scope

**In scope (closed list)**

- Vite React TS project in `apps/admin` with Clerk provider and TanStack Query
- Routes `/` (sign-in, SCR-101) and `/candidates` (placeholder)
- Role gate reading the curator claim (UI only; the API enforces NFR-015)
- `VITE_API_URL`, `VITE_CLERK_PUBLISHABLE_KEY` in `.env.example`
- CI job `admin`: `npm ci`, typecheck, build

**Do not do (out of scope)**

- Do not build candidate, review or import screens (WP-029..WP-031)
- Do not call admin API endpoints that do not exist yet
- Do not add a UI component library beyond what is needed
- Do not deploy (WP-083)

## 4. Inputs

- docs/04-design/ui-ux/README.md SCR-101..SCR-105
- docs/04-design/ui-ux/wireframes (a01..a03)
- ADR-005
- SAD §3.1 CMP-002

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/admin/` | planned (SAD CMP-002; blueprint `apps/admin/src/pages/*`) |
| `apps/admin/src/pages/Candidates.tsx` | planned |
| `apps/admin/.env.example` | planned |
| `.github/workflows/ci.yml` | existing |

## 6. Implementation guidance

- Same Clerk instance as mobile; curator check must not be the only control (API checks role).
- Keep the bundle free of any secret (NFR-016).
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: NFR-015, NFR-029, US-004.

- **AC1.** Given a Clerk user with the curator role, when they sign in, then they see the Candidates page.
- **AC2.** Given a signed-in user without the curator role, when they open /candidates, then they see an access-denied page and no admin API call is made.
- **AC3.** Given a PR touching apps/admin, when CI runs, then the `admin` job installs, typechecks and builds successfully.

## 8. Verification

```sh
cd apps/admin && npm ci && npx tsc --noEmit && npm run build
gh pr checks <n> --watch shows `admin` green
Manual: `npm run dev`, sign in with a curator and a non-curator test user
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

- Curator claim location undecided (OQ-036) → read it from one helper so it changes in one place

## 11. Rollback

Revert the PR; remove the CI job.

## 12. Dependencies and ordering notes

- Must be true before start: none.
- Unblocks: WP-029, WP-030, WP-083.

## 13. Execution guardrails

- Branch `feat/admin-scaffold` from up-to-date `main`; one PR titled `feat(admin): scaffold curator SPA with Clerk curator gate`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- OQ-036 (SAD) curator claim location — owner Lê Ngọc Tấn Hiền; due per SDP Appendix E or source document
