---
task_id: TASK-001
wbs_element_id: WP-062
wbs_element_number: "1.7.1"
wbs_element_name: "Mobile API client and wiring (CMP-019)"
title: "Wire mobile → GET /v1/me with Clerk token via EXPO_PUBLIC_API_URL"
type: integration
slice: vertical
priority: P0
milestone: M2
wave: "Sprint 1 (may start in M0/M1 slack)"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: Medium
depends_on: ["TASK-002 (FS)"]
blocks: ["Mobile feature work in M3 (WP-035, WP-048)"]
requirement_links: ["US-032", "FR-068", "FR-069", "NFR-012", "NFR-014", "NFR-016"]
design_links: ["CMP-019", "CMP-004", "API-003", "ADR-005", "SCR-001", "SCR-009"]
deliverable: DEL-008
risk: RSK-102
branch: feat/mobile-api-me
pr_title: "feat(mobile): call GET /v1/me with the Clerk session token"
status: NOT STARTED
---

# TASK-001 — Wire mobile → GET /v1/me with Clerk token via EXPO_PUBLIC_API_URL

Parent: [`WBS.md`](../WBS.md) WP-062 (1.7.1). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

A signed-in traveler's app calls `GET /v1/me` on the API named by `EXPO_PUBLIC_API_URL` with the Clerk session token and shows that the account is linked.

## 2. Context

The mobile app does not call the API yet [Source: plan.md "Known code follow-ups"; progress.md Next actions 7]. `/v1/me` exists in `apps/api/app/api/routes/identity.py` and maps the Clerk subject to an internal account UUID [Source: ADR-005; openapi.yaml API-003].

## 3. Scope

**In scope (closed list)**

- Add `EXPO_PUBLIC_API_URL` to `apps/mobile/.env.example` and read it in one config module
- A minimal API client function that attaches `Authorization: Bearer <token>` from Clerk `getToken()`
- Call `/v1/me` after sign-in and keep the result (account linked yes/no) in the account context
- Show a non-blocking error state when the API is unreachable or returns 401/503
- Install `@tanstack/react-query` only if used by this call (CMP-019 stack)

**Do not do (out of scope)**

- Do not generate OpenAPI types yet (follow-up in WP-062, rolling wave)
- Do not store the token or the account ID in AsyncStorage or logs
- Do not change the API, the OpenAPI contract or Clerk sign-in screens
- Do not add other endpoints, screens or i18n work
- Do not commit a real `.env` file

## 4. Inputs

- docs/04-design/api/openapi.yaml (API-003, error envelope)
- apps/api/app/api/routes/identity.py
- apps/mobile/src/features/account/AccountContext.tsx
- ADR-005

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/mobile/.env.example` | existing |
| `apps/mobile/src/lib/api/config.ts` | planned (CMP-019, SAD §3.1) |
| `apps/mobile/src/lib/api/client.ts` | planned (CMP-019) |
| `apps/mobile/src/features/account/AccountContext.tsx` | existing |
| `apps/mobile/package.json` | existing (only if TanStack Query is added) |

## 6. Implementation guidance

- Base URL must come from `process.env.EXPO_PUBLIC_API_URL`; fail clearly (dev warning, no crash) when it is missing.
- Get the token with `useAuth().getToken()` per request; never cache it yourself.
- Parse the error envelope `{ error: { code, message, retryable, request_id } }` and surface `request_id` only in dev logs.
- Use HTTPS in any non-local URL (NFR-012); `http://<LAN-IP>:8000` is allowed for local device testing only.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-032, FR-068, FR-069, NFR-012, NFR-014, NFR-016.

- **AC1.** Given a signed-in user and the API running locally with a valid Clerk configuration, when the app starts and the session is restored, then the app sends `GET /v1/me` with `Authorization: Bearer <token>` and stores `account_id` in memory (account linked).
- **AC2.** Given a guest (not signed in), when the app starts, then no request to `/v1/me` is made.
- **AC3.** Given the API is unreachable or returns 503, when the call fails, then the user stays signed in, sees a retryable message and the app does not crash.
- **AC4.** Given an expired or invalid token, when the API returns 401, then the app does not loop; it shows the sign-in gate after one refresh attempt.

## 8. Verification

```sh
cd apps/mobile && npm ci
npm run typecheck
npm run check:dependencies
Manual: run `uv run uvicorn app.main:app --reload --host 0.0.0.0` in apps/api, set EXPO_PUBLIC_API_URL to the LAN URL, sign in on a device with Expo Go, and confirm a 200 for /v1/me in the API log and the linked state in the app
grep -rn "getToken\|Authorization" apps/mobile/src shows no token logging
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

- Device cannot reach the laptop API → use LAN IP or a tunnel; record which was used
- Clerk JWT template/issuer mismatch → check `GONARRA_CLERK_*` settings in apps/api/.env.example

## 11. Rollback

Revert the PR; the app works without the call (feature not yet used by other screens).

## 12. Dependencies and ordering notes

- Must be true before start: TASK-002 (FS).
- Unblocks: Mobile feature work in M3 (WP-035, WP-048).

## 13. Execution guardrails

- Branch `feat/mobile-api-me` from up-to-date `main`; one PR titled `feat(mobile): call GET /v1/me with the Clerk session token`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- OQ-107 (no mobile unit-test runner): manual device check is the verification until the test plan decides — owner Lê Ngọc Tấn Hiền; due per SDP Appendix E or source document
