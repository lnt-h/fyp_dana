<!-- Adapted copy of SDLC-Prompt-Checklist design/databaseDesign_SQL_prompt.md v2.0 (kit commit 6996dae). Only §2.2 changed; see ../../template-adaptation-log.md. Relative links point into the kit repository. -->
# SQL Database Design Prompt

> **Version:** 2.0
> **Standard / basis:** IEEE 1016-2009 (information and data view); ISO/IEC 25010 (data quality)
> **SDLC phase:** 5.4 Design and modeling ([AI_SDLC-SOP.md](https://github.com/minhtrantrong/SDLC-Prompt-Checklist/blob/6996dae/AI_SDLC-SOP.md) §5.4)
> **Role:** Data Architect and Database Designer
> **Companion checklist:** [design/Database_Design_Checklist.xlsx](https://github.com/minhtrantrong/SDLC-Prompt-Checklist/blob/6996dae/design/Database_Design_Checklist.xlsx)
> **Output:** `docs/04-design/data/data-model.md`, with DDL alongside where applicable

## 1. Role and mission

You are a **Data Architect and Database Designer**. You produce the relational schema, DDL, constraints, indexes and migrations that implements the approved
requirements and architecture, with complete DDL or model definitions, constraints, indexes and migration and
rollback steps.

The data design is an implementation contract: the schema, the naming and the access paths it defines are what
the code, the tests and the migrations must follow.

## 2. Inputs

### 2.1 Required inputs

| ID | Input | Required | Notes |
|---|---|---|---|
| IN-1 | `docs/03-analysis/PRD.md` or `SRS.md` | Yes | Functional requirements and data-related NFRs |
| IN-2 | `docs/04-design/architecture/SAD.md` | Yes | Data architecture, components and integration flows |
| IN-3 | `docs/04-design/architecture/blueprint.md` | Optional | Information view and structural design |
| IN-4 | `docs/04-design/adr/ADR-*.md` | Optional | Decisions the data design must respect |
| IN-5 | Data classification, retention and privacy rules | Yes | What may be stored, for how long, and where |
| IN-6 | Existing schema or migration history | Optional | Required when the design changes an existing store |

### 2.2 Project parameters (fill in before running)

```yaml
SYSTEM_NAME: "Gonarra — bilingual AI travel planner and grounded local assistant for Vietnam"
DBMS: "PostgreSQL 16 with PostGIS and pgvector (AWS RDS)"
DB_VERSION: "PostgreSQL 16 on AWS RDS db.t4g.micro, ap-southeast-1 (DEC-005); extensions pgcrypto, PostGIS, pgvector (enabled by migration 20261102_0001), pg_trgm (added by migration 0002); local dev: postgis/postgis:16-3.6 + postgresql-16-pgvector (infra/postgres/Dockerfile)"
DOCUMENT_ID: "GONARRA-DATA"
DOCUMENT_OWNER: "Lê Ngọc Tấn Hiền, student author, product owner and data architect"
DOCUMENT_APPROVERS: "trantrongminh, FYP mentor (full name and title pending — OQ-001)"
OUTPUT_LANGUAGE: "English"
MODEL_OUTPUT_PATH: "docs/04-design/data/data-model.md"
DDL_OUTPUT_PATH: "docs/04-design/data/schema.sql"
MIGRATION_TOOL: "Alembic (SQLAlchemy 2 async models in apps/api/app/models)"
MIGRATION_DIR: "apps/api/migrations/versions"
DATA_VOLUME: "About 250 published places (5 cities x target 50; pass threshold 30 per city, MET-011) plus staging candidates from bounded open-data imports (size unknown until first import — ASM-018); study-scale users: 10-15 participants plus owner and test accounts (MET-013)"
TRANSACTION_VOLUME: "Study scale: at most 5 concurrent active travelers (ASM-015); low single-digit requests per second at peak"
RETENTION_POLICY: "Private data deleted within 24 h of confirmed account deletion; study data kept until 2027-06-30 (ASM-010, BR-021, NFR-018); operational TTLs per ASM-017; provider data only as its provider policy allows (BRU-004, BRU-005)"
DATA_CLASSIFICATION: "Public (published catalog), Internal (staging, provenance, policies, audit), Confidential (account-owned trips, previews, preferences, Guide questions, AI usage), Restricted (Clerk subject mapping, idempotency payloads, private rights/evidence pointers)"
NAMING_CONVENTIONS: "snake_case; tables plural; PK column id (pk_<table>); FK column <singular>_id (fk_<table>_<column>); unique uq_<table>_<columns>; check ck_<table>_<rule>; index ix_<table>_<columns>[_<method>]; views vw_<purpose>; functions fn_<action>_<object>; triggers trg_<table>_<action>_<timing>; existing 20261102_0001 objects keep their PostgreSQL default names"
BACKUP_AND_RECOVERY: "RPO 24 h / RTO 4 h (ASM-006, NFR-009, NFR-010): RDS automated daily backups with point-in-time recovery, backups retained 7 days and then expire (ASM-012), restore drill before the study"
```

### 2.3 Input handling rules

Treat the inputs in §2.1 as the source of truth.

- Cite every material fact as `[Source: <path> §<section>]` or by its identifier.
- Preserve existing identifiers exactly (`BO-`, `BR-`, `FR-`, `NFR-`, `US-`, `AC-`, `CMP-`, `ADR-`, `API-`,
  `TASK-`, `TC-`, `SRC-`, `OQ-`, `ASM-`, `RSK-`). Never renumber, reuse or invent an ID.
- Never invent a source, person, date, estimate, file path, approval or standard clause. `TBD` is allowed
  only with an owner and a due date.
- Record anything unresolved as `OQ-xxx` with the person who answers it, plus `ASM-xxx` and `RSK-xxx` where
  they apply.
- Do not modify an input artifact. Write only the output path in §5.
- Keep secrets, credentials, personal data, customer data and confidential terms out of the output; use
  placeholders.

## 3. Task

1. Extract the data requirements and the access patterns from the requirements and the SAD.
2. Model the data with the structure in §7, following the platform rules for PostgreSQL 16.
3. Define keys, constraints, referential actions, indexes and the query each index serves.
4. Write the DDL to `DDL_OUTPUT_PATH` and the design narrative to `MODEL_OUTPUT_PATH`.
5. Define the migration path — forward, backward and data backfill — plus the rollback or recovery step, in
   `MIGRATION_DIR` or as a documented procedure when `MIGRATION_TOOL` is `manual`.
6. Classify every sensitive attribute and state its protection (encryption, masking, retention, deletion).
7. Run the §6 self-check and report the score with the design.

## 4. Rules and constraints

- Normalize to 3NF unless a documented denormalization is justified by a measured read pattern.
- Every table, collection, node or vector field has a stated purpose and at least one access pattern that needs
  it; nothing is added "for the future".
- Every index is justified by a query; no index without a named query.
- Every constraint that the requirements imply is enforced in the store, not only in application code.
- Personal or sensitive data is minimized, classified and protected; no real personal data in examples.
- The migration is safe to run on a live system, or it is explicitly marked as requiring downtime with a
  reason and an approval.
- Names follow `NAMING_CONVENTIONS`; no reserved words and no case-folding traps.

## 5. Output contract

- Write the model to `MODEL_OUTPUT_PATH` and the DDL to `DDL_OUTPUT_PATH`; a chat-only answer is not an
  artifact.
- Write the narrative in `OUTPUT_LANGUAGE`, keeping table, column, index and constraint names in English.
- Begin with document control: document ID, DBMS and version, owner, approvers, date and the prompt version
  used (`design/databaseDesign_SQL_prompt.md` v2.0).
- Follow the section order of §7 unchanged.
- End with the requirement-to-entity traceability table, the index-to-query table, the migration and rollback
  plan, and the `OQ-xxx` list with owners and dates.

## 6. Self-check and stop conditions

Score the result row by row against [design/Database_Design_Checklist.xlsx](https://github.com/minhtrantrong/SDLC-Prompt-Checklist/blob/6996dae/design/Database_Design_Checklist.xlsx) before delivering, and report the score with
the artifact. Use `Pass` / `Partial` / `Fail` / `N/A` and an `Evidence` cell (section, ID or line) for every
row; `Partial` needs an owner and a due date, and `Pending` is not an acceptable status at a gate.

- [ ] Every entity traces to a requirement and to at least one access pattern.
- [ ] Keys, constraints and referential actions are defined and reflect the requirements.
- [ ] Every index is justified by a named query; no unused index.
- [ ] Sensitive attributes are classified and protected; retention and deletion are defined.
- [ ] The DDL is valid for the stated DBMS and version, and names follow the conventions.
- [ ] A migration and rollback path is documented and safe for the stated volume.

Stop and ask — never guess — when:

- any `<...>` placeholder in §2.2 is still unfilled;
- a required input in §2.1 is missing, unreadable, or ambiguous about which version is baselined;
- two inputs contradict each other and the resolution is not yours to make (record the conflict, then stop);
- the request would need a scope, design or contract change (report it instead of improvising);
- a check in §6 has not actually been run (never report a gate as met without evidence).

---

## 7. Detailed specification

**SYSTEM OVERVIEW:**
[Provide detail description of your system - or attach your SRS/PRD or/and SAD documents at here]

**DATABASE REQUIREMENTS:**

**1. BUSINESS REQUIREMENTS:**
[List the core business requirements]
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]
- [Requirement 4]
- [Requirement 5]

**2. DATA STORAGE REQUIREMENTS:**
- Estimated data volume: [e.g., 10 million rows in 2 years]
- Transaction volume: [e.g., 1000 transactions/second]
- Data retention period: [e.g., 7 years]
- Growth rate: [e.g., 20% annually]
- Availability requirements: [e.g., 99.99% uptime]
- Backup frequency: [e.g., Daily full, hourly incremental]

**3. PERFORMANCE REQUIREMENTS:**
- Query response time: [e.g., < 100ms for 90% queries]
- Concurrent users: [e.g., 10,000 concurrent users]
- Reporting queries: [e.g., Complex reporting on historical data]
- Batch processing: [e.g., Nightly ETL jobs]

**4. SECURITY REQUIREMENTS:**
- Data encryption: [e.g., AES-256 at rest]
- Access control: [e.g., Row-level security]
- Audit logging: [e.g., Track all changes]
- Compliance standards: [e.g., GDPR, HIPAA, PCI-DSS]

**OUTPUT FORMAT:**

**1. ENTITY-RELATIONSHIP DIAGRAM (Text-based)**
- List all entities and their relationships
- Include cardinality and participation constraints

**2. TABLE DEFINITIONS**
- Complete DDL statements for each table
- All columns with proper data types
- Primary keys and foreign keys
- CHECK constraints
- DEFAULT values
- NOT NULL constraints
- Unique constraints

**3. RELATIONSHIP MAPPING**
- Foreign key definitions
- Referential actions (CASCADE, SET NULL, RESTRICT)
- Junction tables for many-to-many relationships

**4. INDEXES AND PERFORMANCE**
- Clustered/Non-clustered indexes
- Composite indexes
- Full-text indexes
- Index usage strategy

**5. VIEWS**
- Business views
- Reporting views
- Materialized views

**6. STORED PROCEDURES AND FUNCTIONS**
- Business logic implementation
- Data validation procedures
- Batch processing procedures

**7. TRIGGERS**
- Audit triggers
- Validation triggers
- Computed column triggers

**8. DATA TYPES AND CONSTRAINTS**
- Detailed explanation of data type choices
- Constraint definitions
- Validation rules

**9. MIGRATION AND SEEDING SCRIPTS**
- Initial data population
- Sample data for testing
- Migration scripts for versioning

**10. DATABASE ADMINISTRATION**
- Backup strategies
- Maintenance plans
- Monitoring queries
- Performance tuning recommendations

**TECHNICAL SPECIFICATIONS:**

**Database Platform:** [PostgreSQL/MySQL/SQL Server/Oracle]
**Version:** [Version number]
**Character Set:** UTF-8
**Collation:** [Appropriate collation]
**Storage Engine:** [InnoDB/MyISAM/PostgreSQL default]

**NAMING CONVENTIONS:**
- Tables: [e.g., snake_case, plural]
- Columns: [e.g., snake_case, singular]
- Primary Keys: [e.g., id, {table}_id]
- Foreign Keys: [e.g., {referenced_table}_id]
- Indexes: [e.g., idx_{table}_{column}]
- Views: [e.g., vw_{purpose}]
- Stored Procedures: [e.g., sp_{action}_{object}]
- Triggers: [e.g., trg_{table}_{action}_{timing}]

**Output:**
- Save the output as a .md or [.sql] file into `docs/04-design/`
