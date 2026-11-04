---
task_id: TASK-008
wbs_element_id: WP-033
wbs_element_number: "1.4.4.2"
wbs_element_name: "Place search API (API-010)"
title: "Place search API-010 over published places, VI/EN and aliases"
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
blocks: ["WP-034", "WP-035"]
requirement_links: ["US-001", "US-003", "FR-002", "FR-004", "FR-076", "NFR-001"]
design_links: ["CMP-005", "API-010", "vw_published_places", "place_aliases", "pg_trgm"]
deliverable: DEL-005
risk: —
branch: feat/api-place-search
pr_title: "feat(api): add GET /v1/places search over published places"
status: NOT STARTED
---

# TASK-008 — Place search API-010 over published places, VI/EN and aliases

Parent: [`WBS.md`](../WBS.md) WP-033 (1.4.4.2). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

`GET /v1/places?city_id=…&q=…` returns only published places of that city whose VI name, EN name or reviewed alias matches the query ignoring case and diacritics, as specified for API-010.

## 2. Context

FR-002 and FR-004 [Source: PRD]; contract API-010 with cursor pagination, Locale parameter and PlaceSummaryPage [Source: openapi.yaml /v1/places]. Diacritic-free alias search uses pg_trgm (schema.sql §1 Q-S1).

## 3. Scope

**In scope (closed list)**

- Route `GET /v1/places` matching openapi.yaml API-010 (params city_id, q, category_code, sort, locale, cursor, limit)
- Repository query over `vw_published_places` and reviewed aliases; diacritic- and case-insensitive
- Clerk auth required (HTTPBearer) as in the contract
- Unit tests for normalisation; integration tests with seeded published and candidate places
- OpenAPI export updated so the drift check passes

**Do not do (out of scope)**

- Do not implement place detail (API-011) or cities (API-008)
- Do not return candidate or withdrawn places
- Do not change the contract; if it is wrong, stop and raise an OQ
- Do not add Elasticsearch or external search

## 4. Inputs

- docs/04-design/api/openapi.yaml API-010 and PlaceSummaryPage
- docs/04-design/api/api-contract.md (pagination, errors)
- schema.sql §1, §4, §9 views
- PRD FR-002 acceptance (AC-001)

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/api/app/api/routes/catalog.py` | planned (CMP-005; follows existing routes layout) |
| `apps/api/app/repositories/places.py` | planned |
| `apps/api/app/schemas/catalog.py` | planned |
| `apps/api/app/api/router.py` | existing |
| `apps/api/openapi.json` | existing (regenerated) |
| `apps/api/tests/integration/test_place_search.py` | planned |

## 6. Implementation guidance

- Normalise both sides with the same function (lower + remove Vietnamese diacritics, đ → d) used by `place_aliases`/`import_records.normalized_name`.
- p95 ≤ 2 s at study scale (NFR-001): use the trigram index; no N+1 queries.
- Error envelope and X-Request-ID as in the contract.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-001, US-003, FR-002, FR-004, FR-076, NFR-001.

- **AC1.** Given published places 'Chùa Cầu' (alias 'Japanese Covered Bridge') in Hội An, when a traveler searches `q=chua cau`, `q=CHÙA CẦU` or `q=japanese bridge`, then the place is returned in each case.
- **AC2.** Given a candidate (unpublished) place matching the query, when the search runs, then it is not returned (FR-004).
- **AC3.** Given a published place in Huế, when a search with Hội An's city_id runs, then it is not returned.
- **AC4.** Given no Authorization header, when the request is sent, then 401 with the error envelope.

## 8. Verification

```sh
cd apps/api && uv sync --all-groups
uv run ruff check . && uv run mypy app && uv run pytest
docker compose up -d db && uv run alembic upgrade head && uv run pytest -m integration
uv run python scripts/export_openapi.py --check
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

- Normalisation differs between import and search → one shared helper with tests

## 11. Rollback

Revert the PR (read-only endpoint).

## 12. Dependencies and ordering notes

- Must be true before start: TASK-003 (FS).
- Unblocks: WP-034, WP-035.

## 13. Execution guardrails

- Branch `feat/api-place-search` from up-to-date `main`; one PR titled `feat(api): add GET /v1/places search over published places`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
