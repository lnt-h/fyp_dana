---
task_id: TASK-010
wbs_element_id: WP-081
wbs_element_number: "1.9.2"
wbs_element_name: "EC2 host: Docker Compose + Caddy TLS serving the API"
title: "EC2 host with Docker Compose and Caddy serving the API /health over HTTPS"
type: infrastructure
slice: vertical
priority: P1
milestone: M2
wave: "Sprint 1"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: Low
depends_on: ["TASK-009 (FS)", "TASK-003 (FS)", "OQ-039 hostname answered (FS)"]
blocks: ["WP-082", "WP-083"]
requirement_links: ["NFR-012", "NFR-008", "NFR-016"]
design_links: ["ADR-002", "CMP-003", "CMP-015", "API-001", "API-002"]
deliverable: DEL-010
risk: RSK-005
branch: chore/aws-ec2-caddy
pr_title: "chore(infra): run the API on EC2 behind Caddy TLS (REL-001)"
status: NOT STARTED
---

# TASK-010 — EC2 host with Docker Compose and Caddy serving the API /health over HTTPS

Parent: [`WBS.md`](../WBS.md) WP-081 (1.9.2). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

`https://<hostname>/health` and `/ready` return 200 from the API container on an EC2 t4g.small behind Caddy with a valid TLS certificate, and the database is migrated to head (REL-001).

## 2. Context

ADR-002 decision: EC2 t4g.small, Docker Compose (Caddy + API), Elastic IP, SSM Session Manager only. Hostname per OQ-039.

## 3. Scope

**In scope (closed list)**

- EC2 t4g.small (arm64) in the public subnet with instance role (ECR pull, SSM read), Elastic IP, security group 80/443 only
- Compose file for production (`infra/aws/compose.prod.yml`) with Caddy and the API image from ECR (linux/arm64)
- Caddyfile with automatic TLS for the hostname
- Settings from SSM at container start
- Manual deploy steps and `alembic upgrade head` in the runbook
- Tag `rel-001` after acceptance

**Do not do (out of scope)**

- Do not build CD automation (WP-082)
- Do not serve the admin SPA (WP-083)
- Do not open port 22; use SSM Session Manager
- Do not put secrets in the compose file or user data

## 4. Inputs

- ADR-002
- apps/api/Dockerfile
- docker-compose.yml
- TASK-009 runbook

## 5. Files and components touched

| Path | State |
|---|---|
| `infra/aws/05-ec2.sh` | planned |
| `infra/aws/compose.prod.yml` | planned |
| `infra/aws/Caddyfile` | planned |
| `infra/aws/README.md` | planned (TASK-009) |

## 6. Implementation guidance

- Build and push the image with `docker buildx build --platform linux/arm64` (CI already builds both).
- Readiness must fail when the DB is unreachable (API-002).
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: NFR-012, NFR-008, NFR-016.

- **AC1.** Given the host is running, when `curl -sSf https://<hostname>/health` runs from outside AWS, then HTTP 200 over TLS 1.2 or higher.
- **AC2.** Given an nmap or security-group check, when open ports are listed, then only 80 and 443 are reachable.
- **AC3.** Given the RDS database, when `alembic current` runs in the API container, then the head revision of TASK-005 (or the latest merged) is reported.
- **AC4.** Given the mobile app with EXPO_PUBLIC_API_URL set to the hostname, when a signed-in user opens the app, then `/v1/me` returns 200 (TASK-001 against staging).

## 8. Verification

```sh
curl -sSf https://<hostname>/health && curl -sSf https://<hostname>/ready
openssl s_client -connect <hostname>:443 -tls1_2 </dev/null | grep -q 'Verify return code: 0'
aws ec2 describe-security-groups --group-ids <sg> --query 'SecurityGroups[].IpPermissions[].FromPort'
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

- No hostname yet (OQ-039) → blocked; do not use a brand hostname (AGENTS.md naming rule)
- arm64 image issues → CI multi-arch build already exists

## 11. Rollback

Stop the instance and release the Elastic IP per runbook; revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: TASK-009 (FS), TASK-003 (FS), OQ-039 hostname answered (FS).
- Unblocks: WP-082, WP-083.

## 13. Execution guardrails

- Branch `chore/aws-ec2-caddy` from up-to-date `main`; one PR titled `chore(infra): run the API on EC2 behind Caddy TLS (REL-001)`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- OQ-039 (SAD) hostname — owner Lê Ngọc Tấn Hiền; due per SDP Appendix E or source document
- OQ-100 environments — owner Lê Ngọc Tấn Hiền; due per SDP Appendix E or source document
