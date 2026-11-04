# Task index

Document: GONARRA-WBS 0.1 task index (kit name `tasks/INDEX.md`, kept as `tasks/README.md` — tailoring in the template-adaptation log). Date 2026-11-04. Owner Lê Ngọc Tấn Hiền; approver trantrongminh [Pending].

Rolling wave: cards exist only for M2 (Sprint 1) and the M1 spikes. Work packages of M3–M7 stay in [`../WBS.md`](../WBS.md) and get cards in the last two days of the preceding sprint (WP-004).

Status values: NOT STARTED, IN PROGRESS, IN REVIEW, DONE, BLOCKED (reason).

| ID | Title | WP | Milestone | Estimate (days) | Depends on | Status |
|---|---|---|---|---|---|---|
| [TASK-001](./TASK-001-wire-mobile-me.md) | Wire mobile → GET /v1/me with Clerk token via EXPO_PUBLIC_API_URL | WP-062 | M2 | 1.0 | TASK-002 (FS) | NOT STARTED |
| [TASK-002](./TASK-002-verify-backend-foundation.md) | Re-verify the backend foundation locally with uv and Docker | WP-010 | M2 | 0.5 | — | NOT STARTED |
| [TASK-003](./TASK-003-alembic-0002-catalog.md) | Alembic revision 0002_catalog from schema.sql §1–§6, §9 (drop duplicate index) | WP-011 | M2 | 1.0 | TASK-002 (FS) | NOT STARTED |
| [TASK-004](./TASK-004-alembic-0003-planning.md) | Alembic revision 0003_planning from schema.sql §7 | WP-012 | M2 | 0.5 | TASK-003 (FS) | NOT STARTED |
| [TASK-005](./TASK-005-alembic-0004-study.md) | Alembic revision 0004_study from schema.sql §8 | WP-013 | M2 | 0.5 | TASK-004 (FS) | NOT STARTED |
| [TASK-006](./TASK-006-ingestion-cli-skeleton.md) | Ingestion CLI skeleton with import-run recording and policy check | WP-020 | M2 | 1.0 | TASK-003 (FS) | NOT STARTED |
| [TASK-007](./TASK-007-admin-scaffold.md) | Curator admin SPA scaffold with Clerk curator-role gate and CI job | WP-028 | M2 | 1.0 | — | NOT STARTED |
| [TASK-008](./TASK-008-place-search-api.md) | Place search API-010 over published places, VI/EN and aliases | WP-033 | M2 | 1.0 | TASK-003 (FS) | NOT STARTED |
| [TASK-009](./TASK-009-aws-baseline.md) | AWS baseline: budgets, IAM, VPC, RDS, S3, ECR and SSM in ap-southeast-1 | WP-080 | M2 | 1.0 | OQ-033 answered (FS), OQ-100 answered (FS), OQ-106 answered (FS) | NOT STARTED |
| [TASK-010](./TASK-010-aws-ec2-caddy-api.md) | EC2 host with Docker Compose and Caddy serving the API /health over HTTPS | WP-081 | M2 | 1.0 | TASK-009 (FS), TASK-003 (FS), OQ-039 hostname answered (FS) | NOT STARTED |
| [TASK-011](./TASK-011-mobile-i18n-setup.md) | Set up i18next VI/EN and move onboarding and auth strings | WP-063 | M2 | 1.0 | — | NOT STARTED |
| [TASK-012](./TASK-012-mobile-i18n-account-screens.md) | Localise Home, Profile, Settings and Preferences; add language setting | WP-063 | M2 | 1.0 | TASK-011 (FS) | NOT STARTED |
| [TASK-013](./TASK-013-mobile-contrast-tokens.md) | Add WCAG AA text tokens textMuted and tealText and apply them | WP-064 | M2 | 0.5 | — | NOT STARTED |
| [TASK-014](./TASK-014-mobile-preferences-pace-modes.md) | Add pace and travel modes to Travel preferences (SCR-011) | WP-065 | M2 | 0.5 | TASK-012 (SS, shared files) | NOT STARTED |
| [TASK-015](./TASK-015-mobile-guest-home-cleanup.md) | Guest mode limited to Home and onboarding; remove bell and weather | WP-065 | M2 | 0.5 | TASK-012 (SS, shared files) | NOT STARTED |
| [TASK-016](./TASK-016-spike-liteapi.md) | SPK-001: LiteAPI coverage, rates and terms for the five cities | WP-005 | M1 | 1.0 | — | NOT STARTED |
| [TASK-017](./TASK-017-spike-gemini-latency.md) | SPK-002: Gemini structured selection latency and free-tier quota | WP-006 | M1 | 1.0 | — | NOT STARTED |
| [TASK-018](./TASK-018-spike-photo-set.md) | SPK-003: photo identification pilot and photo-set protocol | WP-007 | M1 | 1.0 | — | NOT STARTED |
| [TASK-019](./TASK-019-curation-research-sheet.md) | Curation research-sheet template and field mapping for early curation | WP-023 | M1 | 0.5 | — | NOT STARTED |

**Totals:** 19 cards, 15.5 developer-days (M1: 3.5; M2: 12.0).

## Suggested execution order

M0/M1 slack: TASK-019 → TASK-016 → TASK-017 → TASK-018 → TASK-002 → TASK-001 → TASK-013. Sprint 1 (M2): TASK-003 → TASK-004 → TASK-005 → TASK-006 → TASK-008 → TASK-007 → TASK-011 → TASK-012 → TASK-014 → TASK-015 → TASK-009 → TASK-010.

Sprint 1 capacity: 10 weekdays − about 2 days of curation = about 8 developer-days. The M2 cards total 12.0 days; with TASK-001, TASK-002 and TASK-013 (2.0 days) pulled into M0/M1 slack, 10.0 days remain — over capacity by about 2 days. If Sprint 1 runs late, move TASK-012 and TASK-015 to Sprint 2 first (SDP §5.6).

External blockers: TASK-009 needs OQ-033, OQ-100 and OQ-106; TASK-010 needs OQ-039 (hostname); TASK-017 needs a Gemini API key; TASK-016 needs a LiteAPI sandbox key.
