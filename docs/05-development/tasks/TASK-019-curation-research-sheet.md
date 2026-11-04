---
task_id: TASK-019
wbs_element_id: WP-023
wbs_element_number: "1.4.1.4"
wbs_element_name: "Curation research-sheet template and CSV import"
title: "Curation research-sheet template and field mapping for early curation"
type: documentation
slice: horizontal
priority: P0
milestone: M1
wave: "Sprint 0 (start in M0)"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 0.5
estimate_hours: 4
estimate_confidence: High
depends_on: []
blocks: ["WP-090", "WP-023 import"]
requirement_links: ["US-004", "US-005", "FR-011", "FR-012", "MET-011"]
design_links: ["CMP-018", "place_localizations", "place_facts", "sources", "media_assets", "ADR-006"]
deliverable: DEL-006
risk: RSK-001
branch: docs/curation-research-sheet
pr_title: "docs(curation): add research-sheet template and field mapping"
status: NOT STARTED
---

# TASK-019 — Curation research-sheet template and field mapping for early curation

Parent: [`WBS.md`](../WBS.md) WP-023 (1.4.1.4). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

A CSV template and a mapping to schema.sql columns let the owner start reviewing Hội An places before the admin tool exists, so the curation rate (ASM-004) starts on time.

## 2. Context

Curation is the critical path (RSK-001, CON-002); the admin tool arrives in M3 (WP-030). ASM-101: reviewed rows wait in the sheet and count only after publication. Horizontal task justified: enabling artefact for the content workstream.

## 3. Scope

**In scope (closed list)**

- `docs/05-development/curation/research-sheet-template.csv` with one row per place and columns for VI/EN names, aliases, category, coordinates, suggested duration, VI/EN description, each fact with source URL and verification date, media file with licence and author
- `docs/05-development/curation/README.md`: field → table.column mapping, allowed providers (ADR-006: no Google Places data except place_id), review checklist mirroring the publication gates
- Weekly count rule for progress.md

**Do not do (out of scope)**

- Do not write the import command (WP-023, rolling wave)
- Do not copy Google Places content into the sheet
- Do not put real research data in the template

## 4. Inputs

- docs/04-design/data/schema.sql §4
- fn_publication_gate_violations in schema.sql §6
- ADR-006

## 5. Files and components touched

| Path | State |
|---|---|
| `docs/05-development/curation/research-sheet-template.csv` | planned (WP-023) |
| `docs/05-development/curation/README.md` | planned (WP-023) |

## 6. Implementation guidance

- Column names equal schema column names where possible so the import is a direct mapping.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: US-004, US-005, FR-011, FR-012, MET-011.

- **AC1.** Given the template, when each publication gate in fn_publication_gate_violations is compared, then every gate has a column or a checklist item.
- **AC2.** Given the README, when the owner follows it for one sample place, then the row is complete without guessing a field.

## 8. Verification

```sh
python3 -c "import csv;print(next(csv.reader(open('docs/05-development/curation/research-sheet-template.csv'))))"
Link check of the README
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

- Gate list changes → the mapping is reviewed when WP-023 is implemented

## 11. Rollback

Revert the docs PR.

## 12. Dependencies and ordering notes

- Must be true before start: none.
- Unblocks: WP-090, WP-023 import.

## 13. Execution guardrails

- Branch `docs/curation-research-sheet` from up-to-date `main`; one PR titled `docs(curation): add research-sheet template and field mapping`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
