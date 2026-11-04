---
task_id: TASK-006
wbs_element_id: WP-020
wbs_element_number: "1.4.1.1"
wbs_element_name: "CLI skeleton and import-run recording"
title: "Ingestion CLI skeleton with import-run recording and policy check"
type: feature
slice: vertical
priority: P1
milestone: M2
wave: "Sprint 1"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: Medium
depends_on: ["TASK-003 (FS)"]
blocks: ["WP-021", "WP-022", "WP-023"]
requirement_links: ["US-004", "FR-009", "FR-010", "BRU-004"]
design_links: ["CMP-018", "CMP-013", "ADR-012", "ADR-006", "import_runs", "import_records", "provider_policies", "data_providers"]
deliverable: DEL-006
risk: RSK-001
branch: feat/cli-ingestion-skeleton
pr_title: "feat(cli): add Typer ingestion CLI skeleton with import runs"
status: NOT STARTED
---

# TASK-006 — Ingestion CLI skeleton with import-run recording and policy check

Parent: [`WBS.md`](../WBS.md) WP-020 (1.4.1.1). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

`uv run gonarra-cli import --source <provider> --city <code> --dry-run` creates an `import_runs` record and refuses a source without a provider policy, without touching published data.

## 2. Context

Ingestion is a Typer/DuckDB CLI inside `apps/api`; no workers or queues [Source: ADR-012; AGENTS.md]. Provider data may be stored only under a named provider policy; default deny [Source: ADR-006].

## 3. Scope

**In scope (closed list)**

- Typer app under `apps/api/app/cli/` with a console script `gonarra-cli` in pyproject.toml
- Commands: `import` (with `--dry-run`), `runs list`
- Policy check: unknown provider/field/purpose → exit code ≠ 0 and no rows written
- Record start/finish/status/counts in `import_runs`
- Unit and integration tests

**Do not do (out of scope)**

- Do not read Overture/Foursquare/Wikidata files yet (WP-021, WP-022)
- Do not write to places, publications or any published table
- Do not add DuckDB as a dependency yet unless needed by the skeleton
- Do not add an API endpoint (imports are CLI-only, A-024)

## 4. Inputs

- ADR-012
- ADR-006
- schema.sql §3
- SAD §3.1 CMP-018

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/api/app/cli/__init__.py` | planned (SAD: apps/api/app/cli/) |
| `apps/api/app/cli/main.py` | planned |
| `apps/api/pyproject.toml` | existing |
| `apps/api/tests/test_cli.py` | planned |
| `apps/api/tests/integration/test_cli_import_runs.py` | planned |

## 6. Implementation guidance

- Use the async session from `app/db/session.py` via `asyncio.run` in commands.
- Import runs are idempotent by (provider, release, city); a re-run creates a new run linked to the same source release.
- Log counts only, never row payloads.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-004, FR-009, FR-010, BRU-004.

- **AC1.** Given a provider with a provider policy, when `gonarra-cli import --source <p> --city hoi-an --dry-run` runs, then an import_runs row with status DRY_RUN (or the designed equivalent) is written and exit code is 0.
- **AC2.** Given a provider without a policy, when the import command runs, then exit code is non-zero, the message names the missing policy, and no row is written.
- **AC3.** Given any run, when the command finishes, then no row in places, catalog_publications or knowledge_chunks changed.

## 8. Verification

```sh
cd apps/api && uv sync --all-groups
uv run ruff check . && uv run mypy app && uv run pytest
docker compose up -d db && uv run alembic upgrade head && uv run pytest -m integration
uv run python scripts/export_openapi.py --check
uv run gonarra-cli --help
uv run gonarra-cli runs list
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

- Status values differ from schema.sql check constraints → use schema values

## 11. Rollback

Revert the PR (no schema change).

## 12. Dependencies and ordering notes

- Must be true before start: TASK-003 (FS).
- Unblocks: WP-021, WP-022, WP-023.

## 13. Execution guardrails

- Branch `feat/cli-ingestion-skeleton` from up-to-date `main`; one PR titled `feat(cli): add Typer ingestion CLI skeleton with import runs`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
