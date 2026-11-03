# ADR-002 — AWS hosting on EC2 (Docker Compose) + RDS; ECS Express Mode, App Runner and Cloud Run rejected

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | DEC-005 (SRC-100), CON-001, CON-004 |

## Context

Cash budget is USD 0; the owner has USD 200 AWS credits (CON-001). Hosting is on AWS (CON-004). Load is ≤ 15
concurrent users (ASM-030). Availability is needed only for the study window with RTO 4 h / RPO 24 h (ASM-006).
Facts checked in SRC-103: AWS App Runner closed to new customers on 2026-04-30; AWS recommends ECS Express Mode,
which runs on Fargate (not free); RDS db.t4g.micro is eligible for the AWS Free Plan; AWS credits do not cover
Google APIs. The pre-rebuild docs targeted Google Cloud Run + Cloud SQL (SRC-007).

## Drivers

CON-001, CON-004, ASM-006, ASM-030, RSK-005, RSK-009, QAS-08, QAS-09.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. EC2 t4g.small running Docker Compose (Caddy TLS + FastAPI), RDS PostgreSQL 16 db.t4g.micro, S3, ECR, SSM Parameter Store, CloudWatch; no NAT/ALB | Lowest fixed cost; RDS managed backups; Caddy gives free TLS without ALB; SSE works without proxy limits | Single instance (no HA); owner patches the OS | **Chosen** |
| B. ECS Express Mode (Fargate) | Managed containers, AWS-recommended successor to App Runner | Fargate is not free; needs a load balancer; higher steady cost against USD 200 | Rejected |
| C. AWS App Runner | Simple container hosting | Closed to new customers since 2026-04-30 (SRC-103) | Rejected (unavailable) |
| D. Google Cloud Run + Cloud SQL (pre-rebuild target) | Scale to zero; previous docs | Credits are on AWS, not GCP; Cloud SQL has no free instance; contradicts CON-004 | Rejected |
| E. EC2 with self-hosted PostgreSQL in Compose | Cheapest | Owner runs backups/restore; data on same host as app (no failure isolation) | Rejected |
| F. Lightsail instance | Bundled price | Separate product with its own networking; RDS integration and IAM roles weaker; not in DEC-005 | Rejected |

## Decision

AWS ap-southeast-1: one VPC; EC2 t4g.small (arm64) in a public subnet running Docker Compose (Caddy, API) with an
Elastic IP and an instance role; RDS PostgreSQL 16 db.t4g.micro (PostGIS, pgvector) in private subnets reachable only
from the EC2 security group; S3 for media, admin build and import files; ECR for the API image (multi-arch build,
linux/arm64 for production); SSM Parameter Store SecureString for secrets; CloudWatch Logs and alarms; AWS Budgets
alarms at USD 20/50/100. No NAT gateway, ALB, Fargate or App Runner. Deploy by GitHub Actions → ECR → SSM Run
Command. Host access by SSM Session Manager only.

## Consequences

- Positive: predictable low cost; simple topology; data isolated on RDS with automated backups (RPO ≤ 24 h).
- Negative: single point of failure (RSK-030) and no zero-downtime deploys — acceptable for the study (ASM-006);
  images must be built for arm64; OS patching is the owner's task.
- Follow-up: OQ-033 cost estimate; OQ-035 admin SPA over HTTPS; OQ-039 hostname; restore rehearsal (ASM-032).

## Verification

Restore rehearsal within RTO 4 h; budget alarms tested; port scan shows only 80/443 open; RDS not publicly accessible.
