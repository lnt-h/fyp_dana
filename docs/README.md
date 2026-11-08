# Gonarra documentation

Gonarra (working name) is a bilingual Vietnamese/English AI travel planner and grounded local assistant. The FYP
release covers **Đà Nẵng only**, including the Hội An area; other cities are roadmap. A traveller gets a 1–3 day
proposal from published places, checks it on a timeline, map and Plan Health (including calendar rules), edits it
and saves it explicitly, and asks a city-level Guide that answers only from cited sources. Web-found places are
labelled `WEB_UNVERIFIED`. Owner: Lê Ngọc Tấn Hiền; approver: FYP mentor ([Pending]).

## Start here

1. [Decision log](decisions.md): decisions, open questions, assumptions and risks.
2. [BRD](02-requirements/BRD.md) and [PRD](03-analysis/PRD.md): why and what.
3. [SAD](04-design/architecture/SAD.md) and the [ADRs](04-design/adr/): how, and why that way.
4. [Development plan](05-development/Software_Development_Plan.md) and [test plan](07-verification/TEST_PLAN.md): when and how it is checked.

## Structure

```text
docs/
├── README.md                    this index
├── decisions.md                 DEC, OQ, ASM, RSK
├── 02-requirements/             BRD.md, interviews/ (SRC-100, SRC-105)
├── 03-analysis/                 PRD.md, user-stories.md
├── 04-design/
│   ├── architecture/SAD.md
│   ├── adr/                     ADR-001 … ADR-014
│   ├── api/                     openapi.yaml, api-contract.md
│   ├── data/                    schema.sql, data-model.md
│   ├── diagrams/                UML sources (.drawio) and previews
│   └── ui-ux/                   README, screen-specs, ui-research-2026-11-08, wireframes/, reference/
├── 05-development/              Software_Development_Plan.md
└── 07-verification/             TEST_PLAN.md, RESEARCH_PROTOCOL.md
```

## Documents

| Document | Content |
|---|---|
| [decisions.md](decisions.md) | Single log of decisions, open questions, live assumptions and risks |
| [BRD](02-requirements/BRD.md) | Business objectives, metrics, scope, business rules |
| [Elicitation records](02-requirements/interviews/) | SRC-100 (2026-11-04) and SRC-105 re-baseline session (2026-11-06) |
| [PRD](03-analysis/PRD.md) | Functional and non-functional requirements, acceptance case HA-02 |
| [User stories](03-analysis/user-stories.md) | Stories with acceptance criteria |
| [SAD](04-design/architecture/SAD.md) | Architecture views, modules, AI roles, deployment |
| [ADRs](04-design/adr/) | ADR-001 … ADR-014, binding once accepted |
| [OpenAPI](04-design/api/openapi.yaml) · [API contract](04-design/api/api-contract.md) | HTTP `/v1` contract (REST + SSE) and its rules |
| [schema.sql](04-design/data/schema.sql) · [data model](04-design/data/data-model.md) | PostgreSQL DDL and data rules |
| [Diagrams](04-design/diagrams/README.md) | UML 4+1 views in draw.io |
| [UI/UX](04-design/ui-ux/README.md) | Design spec, [screen specs](04-design/ui-ux/screen-specs.md), [UI research](04-design/ui-ux/ui-research-2026-11-08.md), [wireframes](04-design/ui-ux/wireframes/index.html), [reference screens](04-design/ui-ux/reference/README.md) |
| [Development plan](05-development/Software_Development_Plan.md) | Milestones M0–M7, cut order, team, CI, configuration management |
| [Test plan](07-verification/TEST_PLAN.md) | Checks, metrics, golden sets, verification tasks, entry/exit criteria |
| [Research protocol](07-verification/RESEARCH_PROTOCOL.md) | Comparative user study, consent forms (EN/VI), session script |

The previous full SDLC set (intake, audits, traceability, use cases, blueprint, WBS, task cards, test cases, RTM)
is kept at git tag `docs-sdlc-full`. This structure is recorded as DEC-029 in [decisions.md](decisions.md). IDs are
never renumbered; changed items are revised, withdrawn or superseded.
