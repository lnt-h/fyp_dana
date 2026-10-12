# Danang TourGuide — Documentation Review Record

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Purpose and review scope

Internal engineering review, separate from the main dissertation. Version1.2 retains selected P0 and file organization. Reviews identify source support, consistency and validation limits; they are not institutional/IEEE/UML certification. Named technical/academic sign-off is still pending.

## Changes reviewed

- One owner per requirement/design/contract/configuration; shared controls replace repetitive task/use-case/test administration.
- Correct unsupported COMP1682 sample-size attribution; distinguish public academic guidance from the actual missing rubric.
- Cite preliminary primary research and official integration references; competitor capabilities are publisher descriptions, not measured app findings.
- Clarify draft-only preferences, fixed active prefix, hard conflicts versus uncertainty, per-day start legs, language fallback, session logout and replay/media expiration.
- Encode additional DTO branch validation and physical same-day/embedding-space integrity. Add TC-34–37 to cover these contracts.
- Keep P1 identifiers but exclude optional scope from mandatory delivery/acceptance. Keep security, curation, traceability and evaluation details.

## Current review results

Validation results are filled only from checks actually performed on the final artifacts. Runtime/database/browser/native execution is outside the performed document checks.

| Check | Result actually observed | Limit |
|---|---|---|
| Markdown local links/table shapes | No unresolved local link or inconsistent table columns in the 19 documents | Checks existence/structure, not external factual truth |
| Requirement/trace identifiers | 17 distinct FRs, six NFRs; all in RTM; no unknown full requirement ID | Planned coverage only |
| Cases/tasks | 37 distinct TC procedures, 24 task outputs; all TC IDs referenced in RTM | 34 P0/quality and three deferred P1; none executed |
| OpenAPI structure | Parsed JSON, resolved local refs; 27 unique operation IDs, 39 schemas; required path parameters present | No external full OpenAPI validator or live API execution available |
| Selected schema branches | 22 synthetic positive/negative fixtures match expected acceptance using an in-session checker | Checker covers selected type/required/enum/oneOf/anyOf/not/range/format rules; not a standards-certified validator or service test |
| Wireframe links/IDs | 16 screen sections, unique IDs, no dangling internal navigation anchor | No browser render/interaction or native device verification in this revision |
| Color tokens | Five specified text pairs numerically exceed4.5:1; input border3.03:1 | Token calculation only; no full accessibility conformance claim |
| Draw.io source structure | Ten retained sources: balanced tags, unique cell IDs, valid cell references | Source import/render not executed; prior v1.1 previews were inspected and are unchanged |
| DDL review |19 tables; same-day route FKs, nonfresh-null rules, embedding identity and operation deadlines specified | Not executed/parsed by PostgreSQL; migration/extension trial remains TC-37 |
| Source support | Primary papers/instrument and official technical/product/academic pages inspected; access dates and claim limits recorded | Preliminary literature review; no institutional approval or competitor benchmark |
| Evidence integrity | No participant responses, measured model scores, real POI/media rights or runtime results inserted | These require real collection/execution later |

## Repository checklist applicability

The 15 checklist workbooks were read in the preceding document review; the retained mapping below identifies applicable design topics. This revision preserves their role as review aids. File names containing IEEE/UML are not evidence of certification, and no blanket pass is asserted for each workbook row. Official standard editions/applicability and institutional rubric require separate confirmation if claimed.

| Source checklist in repository | Final artifacts | Coverage / applicability |
|---|---|---|
| analysis/PRD_IEEE_29148_Checklist.xlsx | 01-PRD.md; 10-BRD.md; 11-User-Stories.md; 14-Traceability.md | Context/personas, measurable FR/NFR/interfaces, numbered trace. Exact SLA/capacity beyond bounded test target not committed. |
| design/SAD_IEEE_1016_Checklist.xlsx | 02-SAD.md; 12-Blueprint.md; 09-Project-Decisions.md | Composition, logical/interaction/information/interfaces, physical target, alternatives. Resource values remain pending trial/budget. |
| design/BluePrint_Design_IEEE_1016_2009_Checklist.xlsx | 12-Blueprint.md; 14-Traceability.md | Stakeholder concerns/views/algorithms/quality scenarios; no standards certification. |
| design/UseCase_Document_UML2.0_Checklist.xlsx | 03-Use-Cases.md; diagrams/scenarios-view.drawio | IDs/actors/triggers/pre/postconditions/main/alternate/exception/data. Include/extend not forced where semantics unnecessary. |
| design/Class_Diagram_UML2.0_Checklist.xlsx | diagrams/logical-view.drawio; 05-Database-Design.md | Conceptual classes/visibility/types/operations/multiplicities; abstract/static/inheritance not claimed. |
| design/Activity_Diagram_UML2.0_Checklist.xlsx | diagrams/process-view.drawio; 12-Blueprint.md | Actions/decisions/guards/start/end; advanced fork/pin/signal/exception symbols N/A to the depicted control-flow subset. |
| design/Component_Diagram_UML2.0_Checklist.xlsx | diagrams/development-view.drawio; 02-SAD.md | Internal components/dependencies/interfaces in SAD; formal notation import review pending. |
| design/Deployment_Diagram_UML2.0_Checklist.xlsx | diagrams/physical-view.drawio; 02-SAD.md | Execution nodes, communication and resource target. No deployed IP/resources invented. |
| design/Sequence_Diagram_UML2.0_Checklist.xlsx | 04-Sequence-Diagrams.md; diagrams/sequence-*.drawio | Named lifelines/synchronous calls/returns/execution bars; simple scenario paths; combined fragments not forced. |
| design/API_Design_IEEE-1016-2009Checklist.xlsx | 06-API-Design.md; openapi.json | Auth/ownership, error envelope, cursors, revision/idempotency, version evolution. HATEOAS N/A; nested parent paths deliberate tradeoff. |
| design/UI_UX_Design_IEEE-1016-2009_Checklist.xlsx | 07-UI-UX-Design.md; UI_UX_design/wireframes.html | Personas/navigation/tokens/states/trace/targets. Desktop dashboards N/A; native/HTML visual accessibility review pending. |
| design/Database_Design_Checklist.xlsx | 05-Database-Design.md; database.sql; 16-Data-Curation.md | Relational/geographic/vector integrity/indexes/source lifecycle; DDL execution and benchmark pending. |
| design/Polyglot_DB_Design_Checklist.xlsx | 05-Database-Design.md; database.sql | Postgres + extensions selected; extra NoSQL/Graph stores N/A; ANN deferred pending measured need. |
| design/Checklist_Database Design Review.xlsx | 05-Database-Design.md; database.sql; 02-SAD.md | Normalization/keys/cardinality/physical constraints/backup plan; runtime DB review not claimed. |
| verification/Test_Plan_IEEE_829_Checklist.xlsx | 08-Test-Plan.md; 13-Development-Plan.md | Identifier/items/scope/approach/criteria/suspension/resume/owners/evidence/risks. Dates/approvals not yet supplied. |

## Unresolved evidence and next gates

| Gate | Required evidence / owner |
|---|---|
| Academic alignment | Actual approved objectives/template/rubric; student and supervisor |
| Feasibility configuration | Native/DB/ORM/model/Routes trials and pinned versions; developer |
| Visual import/native review | draw.io import and full-size readability; gallery/browser review and later native accessibility |
| Research/content policy | Consent/storage and genuine source/image/narration rights; student/curator |
| Implementation acceptance | Real builds/migrations, P0 cases and failure/retest history; developer/reviewer |
| Evaluation | Real held-out claim support/planning/field/UAT evidence and validity limits |
| Deployment if required | Agreed budget, actual smoke/restore and authorized release |

## Review outcome interpretation

Design content can be complete for review while these external/empirical gates remain open. Unknown inputs are tracked with owner and dependent gate in Decisions rather than filled with invented data. No reviewer approval, competitor benchmark, participant response or system test outcome has been inferred from a written design.
