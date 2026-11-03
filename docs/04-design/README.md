# Design (phase 4)

How Gonarra is built: architecture, decisions, interfaces, data, behaviour and user interface. Every artifact traces
to the requirements in [../03-analysis/PRD.md](../03-analysis/PRD.md) and is checked by the
[cross-artifact design audit](design-audit.md) (DA-GONARRA-02: Pass with conditions).

| Area | Artifact | Standard / checklist |
|---|---|---|
| Architecture | [SAD — 4+1 views](architecture/SAD.md) | ISO/IEC/IEEE 42010, IEEE 1016 |
| Architecture | [Design blueprint](architecture/blueprint.md) | IEEE 1016-2009 |
| Decisions | [ADR-001 Modular monolith over HTTP API](adr/ADR-001-modular-monolith-http-api.md) · [ADR-002 AWS EC2 + RDS](adr/ADR-002-aws-ec2-rds-hosting.md) · [ADR-003 PostgreSQL + PostGIS + pgvector](adr/ADR-003-postgresql-postgis-pgvector.md) · [ADR-004 Gemini as bounded proposal engine](adr/ADR-004-gemini-bounded-proposal-engine.md) · [ADR-005 Clerk identity](adr/ADR-005-clerk-identity.md) · [ADR-006 Runtime-only provider data](adr/ADR-006-runtime-only-provider-data.md) · [ADR-007 On-device speech](adr/ADR-007-on-device-speech.md) · [ADR-008 Photo identification within 300 m](adr/ADR-008-photo-identification-300m.md) · [ADR-009 Revisioned previews and explicit Save](adr/ADR-009-revisioned-previews-explicit-save.md) · [ADR-010 Grounded Guide retrieval](adr/ADR-010-grounded-guide-retrieval.md) · [ADR-011 OR-Tools scheduling](adr/ADR-011-or-tools-scheduling.md) · [ADR-012 CLI ingestion and embedding](adr/ADR-012-cli-ingestion-embedding.md) | ADR |
| Behaviour | [Use cases UC-001..022](use-cases.md) | UML 2.0 |
| Diagrams | [Diagram index](diagrams/README.md) · [structure views](diagrams/structure-views.md) | UML 2.0 (`.drawio` sources) |
| Interfaces | [OpenAPI 3.1 spec](api/openapi.yaml) · [API contract](api/api-contract.md) | IEEE 1016 |
| Data | [Data model](data/data-model.md) · [PostgreSQL DDL](data/schema.sql) | Database design checklists |
| User interface | [UI/UX specification](ui-ux/README.md) · [wireframes](ui-ux/wireframes/) · [reference screenshots](ui-ux/reference/) | IEEE 1016, WCAG 2.1 AA |

Open the wireframes directly in a browser, for example `open ui-ux/wireframes/m03-proposal-timeline.html`.
