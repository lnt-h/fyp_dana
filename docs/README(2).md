# Danang TourGuide — SDLC Artifacts (v0.1)

Generated from `Danang_TourGuide_Product_Spec.md` using the prompt templates in this repository.

**System:** Personalized AI travel companion for Da Nang  
**Date:** 2026-09-29  
**Status:** Design baseline for review; implementation and provider assumptions remain open  
**Scope:** Graduation V1 — Da Nang only, no booking/payment

## Document map

| File | Source prompt | Standard |
|------|---------------|----------|
| [01-PRD.md](./01-PRD.md) | `PRD_prompt.md`, `PRD_Prompt_with_template.md` | IEEE 29148-2018 (adapted) |
| [02-SAD.md](./02-SAD.md) | `SAD_prompt.md`, `SAD_Prompt_with_template_.md` | IEEE 1016-2009 views |
| [03-Blueprint-IEEE-1016.md](./03-Blueprint-IEEE-1016.md) | `bluePrint_design_prompt.md` | IEEE 1016-2009 SDD |
| [04-Use-Cases.md](./04-Use-Cases.md) | `useCase_prompt.md` | UML 2.0 |
| [05-Activity-Diagrams.md](./05-Activity-Diagrams.md) | `activityDiagram_prompt.md` | UML 2.0 |
| [06-Sequence-Diagrams.md](./06-Sequence-Diagrams.md) | `sequenceDiagram_prompt.md` | UML 2.0 |
| [07-Class-Diagram.md](./07-Class-Diagram.md) | `classDiagram_prompt.md` | UML 2.0 |
| [08-Component-Diagram.md](./08-Component-Diagram.md) | `componentDiagram_prompt.md` | UML 2.0 |
| [09-Deployment-Diagram.md](./09-Deployment-Diagram.md) | `deploymentDiagram_prompt.md` | UML 2.0 |
| [10-API-Design.md](./10-API-Design.md) | `apiDesign_prompt.md` | IEEE 1016-2009 (API view) |
| [11-Database-SQL.md](./11-Database-SQL.md) | `databaseDesign_SQL_prompt.md` | PostgreSQL + PostGIS |
| [12-Database-Vector.md](./12-Database-Vector.md) | `databaseDesign_VectorDB_prompt.md` | pgvector |
| [13-UI-UX-Design.md](./13-UI-UX-Design.md) | `UI-UX-Design_prompt.md` | IEEE 1016 → screens |
| [14-Test-Plan.md](./14-Test-Plan.md) | `testPlan_prompt.md` | IEEE 829-2008 |

## Intentionally not generated

- **Graph DB** (`databaseDesign_GraphrDB_prompt.md`) — V1 stores explainability as structured evidence graphs in PostgreSQL, not Neo4j.
- **NoSQL** (`databaseDesign_NoSQL_prompt.md`) — primary store is PostgreSQL; Redis is cache only (covered in SAD/deployment).

UML diagrams are **Mermaid** (render in GitHub/Cursor). Draw.io XML can be added later if you need import into diagrams.net.

## Reading order and source of truth

`ASSUMPTIONS.md` records unresolved decisions; `01-PRD.md` owns product scope and requirement IDs; `02-SAD.md` owns architectural decisions; `10-API-Design.md`, `11-Database-SQL.md` and `12-Database-Vector.md` own their respective contracts. Diagrams illustrate those contracts. If two files differ, resolve the discrepancy in the owning document and update the dependent files together.

The Mermaid use case view is a compatibility-oriented interaction map; the use case catalog and brief specifications carry the UML semantics. The diagrams are not editable Draw.io XML despite the source prompt requesting it. Standards names describe the structure used for review; they do not certify formal IEEE/UML conformance.

**Scope checkpoint:** the supplied product spec assumes eight months and places camera scanning in P2. Earlier project discussions mention 3–4 months and a core camera flow. Decide this before freezing P0; see A-02/A-16.

## Working assumptions (confirm or replace)

See [ASSUMPTIONS.md](./ASSUMPTIONS.md).
