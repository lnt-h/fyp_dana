# Documentation map — Gonarra × SDLC-Prompt-Checklist

Each artifact is generated from a kit prompt (adapted copy in `prompt-templates/`), audited against its kit checklist in a
separate session, fixed (max three rounds) and approved by the mentor. The agent drafts; it never approves.

| Phase | Artifact | Prompt template | Checklist | Replaces (retired) | Status |
|---|---|---|---|---|---|
| 2 Requirements | `02-requirements/interviews/SRC-100-elicitation-session-2026-11-04.md` | `analysis/BRD_Elicitation_Prompt_IEEE_standard.md` | — | — | Closed 2026-11-04 |
| 2 Requirements | `02-requirements/BRD.md`, `brd-audit.md` | `analysis/BRD_Prompt_IEEE_standard.md` | `analysis/BRD_IEEE_29148_Checklist.xlsx` | `BRD.md`, `RESEARCH.md` (in part) | v0.4 — Ready with conditions (BRD-AUDIT-03) |
| 3 Analysis | `03-analysis/PRD.md`, `user-stories.md`, `traceability.md`, `prd-audit.md` | `analysis/PRD_prompt.md` | `analysis/PRD_IEEE_29148_Checklist.xlsx` | `PRD.md`, `USER-STORIES.md` | PRD 0.2, stories 0.2 — Ready with conditions (PRD-AUDIT-01) |
| 4 Design | `04-design/architecture/SAD.md`, `adr/ADR-*.md` | `design/SAD_prompt.md` | `design/SAD_IEEE_1016_Checklist.xlsx` | `ARCHITECTURE.md`, `SECURITY.md` | Draft — Pass with conditions (DA-GONARRA-02) |
| 4 Design | `04-design/architecture/blueprint.md` | `design/bluePrint_design_prompt.md` | `design/BluePrint_Design_IEEE_1016_2009_Checklist.xlsx` | — | Draft — Pass with conditions (DA-GONARRA-02) |
| 4 Design | `04-design/use-cases.md`, `diagrams/scenarios-view.drawio` | `design/useCase_prompt.md` | `design/UseCase_Document_UML2.0_Checklist.xlsx` | `USE-CASES.md` | Draft — Pass with conditions (DA-GONARRA-02) |
| 4 Design | `diagrams/logical-view`, `development-view`, `physical-view`, `process-view`, `process-view-activity` `.drawio` | class / component / deployment / sequence / activity prompts | matching UML 2.0 checklists | Mermaid in `ARCHITECTURE.md` | Draft — Pass with conditions (DA-GONARRA-02) |
| 4 Design | `04-design/api/openapi.yaml`, `api/api-contract.md` | `design/apiDesign_prompt.md` | `design/API_Design_IEEE-1016-2009Checklist.xlsx` | `API.md` | Draft — Pass with conditions (DA-GONARRA-02); spec validates |
| 4 Design | `04-design/data/data-model.md`, `schema.sql` | `design/databaseDesign_SQL_prompt.md` (+ VectorDB prompt) | `design/Database_Design_Checklist.xlsx`, `Polyglot_DB_Design_Checklist.xlsx` | `DATABASE-DESIGN.md`, `DATA.md` | Draft — Pass with conditions (DA-GONARRA-02); DDL not yet applied to a database |
| 4 Design | `04-design/ui-ux/` | `design/UI-UX-Design_prompt.md` | `design/UI_UX_Design_IEEE-1016-2009_Checklist.xlsx` | root `design/` | Draft — Pass with conditions (DA-GONARRA-02) |
| 4 Design | `04-design/design-audit.md` | `design/Design_Audit_Prompt.md` | all design checklists | — | DA-GONARRA-01 Fail → DA-GONARRA-02 Pass with conditions |
| 5 Planning | `05-development/Software_Development_Plan.md`, `WBS.md`, `tasks/` | `development/DevPlan_ISO_24748_5_Prompt.md`, `TaskBreakdown_ISO_21511_Prompt.md` | `development/DevPlan_ISO_24748_5_Checklist.xlsx` | `DEVELOPMENT.md`, phase list in `plan.md` | Not started |
| 7 Verification | `07-verification/TEST_PLAN.md`, `TEST_CASES.md`, `RTM.md`, `RESEARCH_PROTOCOL.md` | `verification/TestPlan_IEEE 829-2008_prompt.md`, `TestCase_RTM_IEEE_829_Prompt.md` | `verification/Test_Plan_IEEE_829_Checklist.xlsx` | `TESTING.md`, `RESEARCH.md` | Not started |

| 1 Intake | `01-intake/intent.md`, `sources.md`, `glossary.md`, `stakeholders.md` | `requirements/Intake_Intent_Prompt.md` | SOP §5.1 exit criteria | — | Draft — self-check 4 Pass / 2 Partial |

Retired on 2026-11-04: the flat `docs/*.md` contracts (content preserved in git history at `4c03e7f`) and the root
`design/` folder (moved to `04-design/ui-ux/reference/`). Phases 5 and 7 are scheduled next.
