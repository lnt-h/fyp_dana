---
task_id: TASK-005
wbs_element_id: WP-013
wbs_element_number: "1.3.2.3"
wbs_element_name: "Alembic revision 0004_study"
title: "Alembic revision 0004_study from schema.sql §8"
type: migration
slice: horizontal
priority: P1
milestone: M2
wave: "Sprint 1"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 0.5
estimate_hours: 4
estimate_confidence: High
depends_on: ["TASK-004 (FS)"]
blocks: ["WP-078", "WP-059"]
requirement_links: ["FR-077", "NFR-018"]
design_links: ["CMP-016", "schema.sql §8", "data-model §9.2"]
deliverable: DEL-005
risk: —
branch: feat/db-0004-study
pr_title: "feat(db): add Alembic revision 0004_study"
status: NOT STARTED
---

# TASK-005 — Alembic revision 0004_study from schema.sql §8

Parent: [`WBS.md`](../WBS.md) WP-013 (1.3.2.3). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

`alembic upgrade head` creates the user-study tables of schema.sql §8, so the full designed schema is in place.

## 2. Context

Revision plan [Source: data-model.md §9.2]; study data retention until 2027-06-30 (ASM-010, NFR-018).

## 3. Scope

**In scope (closed list)**

- `apps/api/migrations/versions/20261211_0004_study.py` executing schema.sql §8
- Downgrade drops §8 tables
- Integration test asserts all 40 base tables of schema.sql exist at head

**Do not do (out of scope)**

- Do not implement the study API (WP-078)
- Do not add retention jobs

## 4. Inputs

- docs/04-design/data/schema.sql §8
- data-model.md §9.2

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/api/migrations/versions/20261211_0004_study.py` | planned (data-model §9.2) |
| `apps/api/tests/integration/test_migrations.py` | planned (TASK-003) |

## 6. Implementation guidance

- No column may hold account IDs in study tables beyond what §8 defines (pseudonymous, US-036).
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: FR-077, NFR-018.

- **AC1.** Given a database at 0003, when `alembic upgrade head` runs, then study_participants and study_session_logs exist and the public schema has the 40 base tables of schema.sql.
- **AC2.** Given the head database, when `alembic downgrade base && alembic upgrade head` runs, then it succeeds.

## 8. Verification

```sh
cd apps/api && uv sync --all-groups
uv run ruff check . && uv run mypy app && uv run pytest
docker compose up -d db && uv run alembic upgrade head && uv run pytest -m integration
uv run python scripts/export_openapi.py --check
uv run alembic downgrade base && uv run alembic upgrade head
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

- Table count differs from 40 → compare with schema.sql and raise an OQ, do not edit schema.sql

## 11. Rollback

`alembic downgrade` to 0003; revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: TASK-004 (FS).
- Unblocks: WP-078, WP-059.

## 13. Execution guardrails

- Branch `feat/db-0004-study` from up-to-date `main`; one PR titled `feat(db): add Alembic revision 0004_study`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
