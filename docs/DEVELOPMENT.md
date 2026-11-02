# Development and release

## Available in the current checkout

From the repository root, enter the mobile app and install its locked dependencies. Configure the existing linked Clerk app locally as described in the [root README](../README.md). Keep local environment files private.

```sh
cd apps/mobile
npm ci
npm start
```

From apps/mobile, npm run ios and npm run android invoke local native builds with the corresponding platform toolchain. npm run web opens a browser preview. The current static checks are:

```sh
npm run typecheck
npm run check:dependencies
```

Before native handoff run npx expo-doctor and verify the actual device flow. Metro startup or web rendering alone cannot verify native sessions, maps or streaming.

Backend dependencies are locked to Python 3.12 with uv. Docker Desktop can run PostgreSQL with all required extensions and the API:

```sh
docker compose build db api
docker compose up -d db
cd apps/api
uv sync --all-groups
uv run alembic upgrade head
uv run ruff check .
uv run mypy app
uv run pytest
uv run pytest -m integration
uv run python scripts/export_openapi.py --check
```

From the repository root, `docker compose up -d api` serves `/health`, `/ready`, `/docs` and `/openapi.json` on port 8000. The official PostGIS image currently runs through amd64 emulation on Apple Silicon development machines.

## Planned commands and prerequisites

The following commands become applicable when their projects, profiles, dependencies and scripts are added. Production releases target iOS and Android.

| Working directory | Prerequisite | Planned commands |
|---|---|---|
| apps/api | Catalog schema, provider registry and importer CLI | `uv run gonarra catalog import --provider overture --release <release> --city hoi-an --dry-run`, then the reviewed non-dry run; exact command is not available until Phase 2 implements it |
| apps/api | Curator workflow and publication validator | Validate a candidate manifest, review conflicts/rights and publish by expected revision; commands/API will be documented when implemented |
| apps/api | Provider benchmark fixtures and opted-in credentials | Run the 100-POI/100-route benchmark separately from normal unit tests; live-provider evidence must name provider/configuration and may incur cost |
| apps/mobile | jest-expo, component tests and Maestro flows | `npm test` and native Maestro acceptance on preview builds |
| apps/mobile | EAS project, platform credentials, eas.json | `eas build --profile development --platform ios`, `eas build --profile development --platform android`. Use preview for QA and production for release. |

## CI, staging and release

GitHub Actions checks docs, mobile types and dependencies, backend lint/types/tests, migrations against a clean database, OpenAPI-generated mobile types, image build and leaked secrets. Keep provider secrets in server configuration. Never commit provider payload dumps unless they are minimal, redacted, contractually retainable test fixtures with source/license metadata. Compare generated types to the committed contract.

Phase 2 import development uses pinned provider releases and bounded city extracts. A developer must be able to run schema and deterministic importer tests without network access. Live import/benchmark jobs are explicit opt-in commands with quota and cost guardrails; unit tests never call Google, Gemini or local-map providers. Do not copy credentials into Compose files, mobile environment files, notebooks or shell history.

Deploy the tagged image via Artifact Registry to staging Cloud Run. Apply Alembic migrations as a controlled step against Cloud SQL. Check health, authenticated access, denied cross-owner access, planner and explicit Save. Verify media after a test restore, rehearse application rollback and document migration compatibility/forward fixes. Record measured recovery time and recoverable data window.

Promote the tested image from protected main or release tag after gates. Review obsolete audio/location dependencies and permissions against actual use, store disclosures and naming approval before production builds. Test on at least one physical device per platform. Use EAS Submit with the tested production builds after release approval.
