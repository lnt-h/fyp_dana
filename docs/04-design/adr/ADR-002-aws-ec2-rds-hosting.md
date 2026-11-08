# ADR-002 — AWS hosting on EC2 (Docker Compose) + RDS

| Field | Value |
|---|---|
| Status | Proposed (mentor approval at M0). Re-affirmed as the default 2026-11-06 (DEC-018, DEC-021); final hosting decision deferred (OQ-129) |
| Date | 2026-11-04 (1.0: 2026-11-06) |
| Version | 1.0 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | DEC-005 (SRC-100), CON-001, CON-004; DEC-018 (SRC-105) |

## Context

Cash budget is USD 0 with USD 200 AWS credits; load is ≤ 15 concurrent users; availability matters only during
the study window (RTO 4 h, RPO 24 h). AWS App Runner is closed to new customers; ECS Express Mode runs on Fargate
(not free). The owner wants no infrastructure work now: local Docker Compose first, one VM later (A-037).

## Decision

- Default target: AWS ap-southeast-1, one VPC; EC2 t4g.small (arm64) in a public subnet running Docker Compose
  (Caddy TLS + API) with an Elastic IP and instance role; RDS PostgreSQL 16 db.t4g.micro (PostGIS, pgvector) in
  private subnets reachable only from the EC2 security group; S3 for media and the admin build; ECR for the API image
  (arm64 + amd64); SSM Parameter Store for secrets; CloudWatch logs and alarms; AWS Budgets alarms at USD 20/50/100.
- No NAT gateway, ALB, Fargate or App Runner. Deploy by GitHub Actions → ECR → SSM Run Command. Host access by SSM
  Session Manager only.
- Until OQ-129 is closed (before M2), development and the study may run on a single VM or laptop with the same
  Compose file and a PostGIS/pgvector container; the application design does not depend on the choice.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. EC2 + Docker Compose + RDS, no NAT/ALB | **Chosen (default)** | Lowest fixed cost; managed backups; Caddy gives free TLS; SSE works |
| B. ECS Express Mode (Fargate) | Rejected | Not free; needs a load balancer |
| C. AWS App Runner | Rejected | Closed to new customers (2026-04-30) |
| D. Google Cloud Run + Cloud SQL | Rejected | Credits are on AWS; Cloud SQL has no free tier |
| E. EC2 with self-hosted PostgreSQL | Rejected for production; acceptable for OQ-129 "single VM" | Owner runs backups; no failure isolation |
| F. Lightsail | Rejected | Weaker RDS/IAM integration |

## Consequences

- Positive: predictable low cost; simple topology; data isolated on RDS with automated backups.
- Negative: single point of failure and no zero-downtime deploys (acceptable for the study); OS patching is the
  owner's task; images must be built for arm64.
- Follow-up: OQ-129 (single VM vs EC2 + RDS), OQ-033 cost estimate, restore rehearsal.

## Drivers

CON-001, CON-004, ASM-006, ASM-030, RSK-005, RSK-030, QAS-08, QAS-09.
