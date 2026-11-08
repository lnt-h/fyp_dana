# Gonarra documentation

Standards-aligned SDLC documentation for Gonarra, a bilingual (Vietnamese/English) AI travel planner and grounded
local assistant for five Vietnamese cities. Each document is drafted from a versioned prompt template of the
[SDLC Prompt Checklist](https://github.com/minhtrantrong/SDLC-Prompt-Checklist) kit, audited independently against
its checklist and approved by the FYP mentor.

- **Owner:** Lê Ngọc Tấn Hiền (student author)
- **Approver:** FYP mentor (trantrongminh)
- **Status:** every document is a draft awaiting mentor sign-off

## Start here

1. [Business requirements (BRD)](02-requirements/BRD.md): why, objectives, scope and business requirements.
2. [Product requirements (PRD)](03-analysis/PRD.md) and [user stories](03-analysis/user-stories.md): what to build.
3. [Software architecture (SAD)](04-design/architecture/SAD.md) and the [architecture decision records](04-design/adr/): how it is built and why.

## Folder structure

```text
docs/
├── README.md                     this index
├── 00-governance/                document control for the whole set
│   ├── document-register.md      every artifact, its template, checklist and status
│   ├── template-adaptation-log.md
│   └── ai-agent-guidelines.md    fixed decisions and rules for AI-assisted drafting
├── 01-intake/                    intent, sources, glossary, stakeholders
├── 02-requirements/              BRD, BRD audit, elicitation session record (interviews/)
├── 03-analysis/                  PRD, user stories, traceability matrix, PRD audit
└── 04-design/
    ├── README.md                 design index
    ├── design-audit.md           cross-artifact design audit
    ├── use-cases.md
    ├── architecture/             SAD (4+1 views), IEEE 1016 blueprint
    ├── adr/                      ADR-001 … ADR-012
    ├── api/                      OpenAPI 3.1 spec and API contract
    ├── data/                     data model and PostgreSQL DDL
    ├── diagrams/                 UML sources (.drawio) and Mermaid previews
    └── ui-ux/                    design specification, HTML wireframes, reference screenshots
```

Phases 05-development (development plan, WBS, task cards) and 07-verification (test plan, test cases, RTM,
research protocol) are scheduled next. The documents they replace (`TESTING.md`, `RESEARCH.md`,
`DEVELOPMENT.md`) are retired. Their content is captured in the BRD and PRD and remains in git history at commit
`4c03e7f`.

## Document register

| Phase | Document | Audit result |
|---|---|---|
| 1 Intake | [Intent](01-intake/intent.md) · [sources](01-intake/sources.md) · [glossary](01-intake/glossary.md) · [stakeholders](01-intake/stakeholders.md) | Self-check |
| 2 Requirements | [BRD](02-requirements/BRD.md) · [elicitation record](02-requirements/interviews/SRC-100-elicitation-session-2026-11-04.md) | [Ready with conditions](02-requirements/brd-audit.md) |
| 3 Analysis | [PRD](03-analysis/PRD.md) · [user stories](03-analysis/user-stories.md) · [traceability](03-analysis/traceability.md) | [Ready with conditions](03-analysis/prd-audit.md) |
| 4 Design | [Design index](04-design/README.md) | [Pass with conditions](04-design/design-audit.md) |

The full register, including the prompt template and checklist behind each artifact, is in
[00-governance/document-register.md](00-governance/document-register.md).

## Conventions

- **Traceability:** IDs are permanent and traced end to end: `BO` → `BR` → `FR`/`NFR` → `US` → `UC`/`CMP`/`API`, and later `TASK`/`TC`.
- **Open items:** open questions (`OQ-xxx`) and assumptions (`ASM-xxx`) always carry an owner and a due date.
- **File names:** kebab-case, except standard acronyms (`BRD`, `PRD`, `SAD`, `ADR-NNN-<topic>`) and `README.md`.
- **Diagrams:** `.drawio` files are the source of truth; Mermaid previews sit next to them.
- **Changing a contract:** update its owner document, its traceability and its audit in the same change.
