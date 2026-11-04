---
task_id: TASK-009
wbs_element_id: WP-080
wbs_element_number: "1.9.1"
wbs_element_name: "AWS baseline"
title: "AWS baseline: budgets, IAM, VPC, RDS, S3, ECR and SSM in ap-southeast-1"
type: infrastructure
slice: horizontal
priority: P1
milestone: M2
wave: "Sprint 1"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: Low
depends_on: ["OQ-033 answered (FS)", "OQ-100 answered (FS)", "OQ-106 answered (FS)"]
blocks: ["TASK-010", "WP-014"]
requirement_links: ["NFR-013", "NFR-016", "NFR-033", "NFR-034", "NFR-037", "MET-012"]
design_links: ["ADR-002", "CMP-016", "CMP-017", "SAD deployment view"]
deliverable: DEL-010
risk: RSK-005
branch: chore/aws-baseline
pr_title: "chore(infra): add AWS baseline scripts and runbook for ap-southeast-1"
status: NOT STARTED
---

# TASK-009 — AWS baseline: budgets, IAM, VPC, RDS, S3, ECR and SSM in ap-southeast-1

Parent: [`WBS.md`](../WBS.md) WP-080 (1.9.1). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

The AWS account has budget alarms at USD 20/50/100, a VPC without NAT gateway, a private RDS PostgreSQL 16 db.t4g.micro with PostGIS and pgvector, S3 buckets, an ECR repository and SSM SecureString parameters, all created by version-controlled scripts.

## 2. Context

Hosting decision [Source: ADR-002]; budget USD 200 credits (CON-001). Horizontal slice justified: environment for every later deploy. Provisioning method per OQ-106.

## 3. Scope

**In scope (closed list)**

- AWS Budgets alarms 20/50/100 to the owner's e-mail (NFR-037)
- VPC with public subnet (EC2) and private subnets (RDS); no NAT gateway, no ALB
- RDS PostgreSQL 16 db.t4g.micro, not publicly accessible, encrypted at rest, 7-day backups (ASM-012); extensions postgis, vector, pg_trgm enabled
- S3 buckets (media, admin build, imports) with block public access and encryption
- ECR repository for the API image
- SSM SecureString parameters for DB URL, Clerk, Gemini, Routes keys (placeholders only in git)
- Scripts and runbook under `infra/aws/`

**Do not do (out of scope)**

- Do not create EC2 or deploy the API (TASK-010)
- Do not create a second environment (OQ-100)
- Do not commit any secret, account ID or ARN with account ID
- Do not create NAT gateway, ALB, Fargate or App Runner (ADR-002)

## 4. Inputs

- ADR-002
- SAD §3.8 deployment view
- data-model §13
- OQ-033 cost estimate

## 5. Files and components touched

| Path | State |
|---|---|
| `infra/aws/README.md` | planned (OQ-106 recommendation) |
| `infra/aws/01-budgets.sh` | planned |
| `infra/aws/02-network.sh` | planned |
| `infra/aws/03-rds.sh` | planned |
| `infra/aws/04-storage-ecr-ssm.sh` | planned |

## 6. Implementation guidance

- Scripts are idempotent (describe before create) and parameterised by environment variables; no hard-coded account ID.
- RDS security group allows 5432 only from the future EC2 security group.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: NFR-013, NFR-016, NFR-033, NFR-034, NFR-037, MET-012.

- **AC1.** Given the scripts have run, when the owner lists budgets, then three alarms at USD 20, 50 and 100 exist and a test notification was received (NFR-037).
- **AC2.** Given the RDS instance, when its settings are read, then PubliclyAccessible=false, StorageEncrypted=true, BackupRetentionPeriod=7, engine 16.x.
- **AC3.** Given a psql session through a temporary bastion or SSM port forward, when `select extname from pg_extension` runs, then postgis, vector and pg_trgm are listed.
- **AC4.** Given the repository, when `git grep -nE "AKIA|aws_secret|[0-9]{12}" infra/` runs, then no secret or account ID is found.

## 8. Verification

```sh
bash -n infra/aws/*.sh
aws budgets describe-budgets --account-id "$AWS_ACCOUNT_ID"
aws rds describe-db-instances --query 'DBInstances[].{p:PubliclyAccessible,e:StorageEncrypted,b:BackupRetentionPeriod,v:EngineVersion}'
git grep -nE "AKIA|aws_secret" infra/ (expect no output)
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

- Cost higher than estimate → stop after budgets and check OQ-033
- Free-plan limits (RSK-009)

## 11. Rollback

Delete the created resources with the teardown section of the runbook; revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: OQ-033 answered (FS), OQ-100 answered (FS), OQ-106 answered (FS).
- Unblocks: TASK-010, WP-014.

## 13. Execution guardrails

- Branch `chore/aws-baseline` from up-to-date `main`; one PR titled `chore(infra): add AWS baseline scripts and runbook for ap-southeast-1`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- OQ-033 (SAD) cost estimate — owner Lê Ngọc Tấn Hiền; due per SDP Appendix E or source document
- OQ-100 environments — owner Lê Ngọc Tấn Hiền; due per SDP Appendix E or source document
- OQ-106 provisioning method — owner Lê Ngọc Tấn Hiền; due per SDP Appendix E or source document
