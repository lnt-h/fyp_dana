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

## Planned commands and prerequisites

The following commands become applicable when their projects, profiles, dependencies and scripts are added. Production releases target iOS and Android.

| Working directory | Prerequisite | Planned commands |
|---|---|---|
| Repository root | Compose database with PostGIS/pgvector | `docker compose up -d db` |
| apps/api | Python 3.12, uv project/lock, settings and reachable local DB | `uv sync --all-groups`, `uv run alembic upgrade head`, `uv run uvicorn app.main:app --reload` |
| apps/api | Backend tooling and test database | `uv run ruff check .`, `uv run mypy app`, `uv run pytest` |
| Repository root | API Dockerfile and build context | `docker build -f apps/api/Dockerfile .` |
| apps/mobile | jest-expo, component tests and Maestro flows | `npm test` and native Maestro acceptance on preview builds |
| apps/mobile | EAS project, platform credentials, eas.json | `eas build --profile development --platform ios`, `eas build --profile development --platform android`. Use preview for QA and production for release. |

## CI, staging and release

GitHub Actions checks docs, mobile types and dependencies, backend lint/types/tests, migrations against a clean database, OpenAPI-generated mobile types, image build and leaked secrets. Keep provider secrets in server configuration. Compare generated types to the committed contract.

Deploy the tagged image via Artifact Registry to staging Cloud Run. Apply Alembic migrations as a controlled step against Cloud SQL. Check health, authenticated access, denied cross-owner access, planner and explicit Save. Verify media after a test restore, rehearse application rollback and document migration compatibility/forward fixes. Record measured recovery time and recoverable data window.

Promote the tested image from protected main or release tag after gates. Review obsolete audio/location dependencies and permissions against actual use, store disclosures and naming approval before production builds. Test on at least one physical device per platform. Use EAS Submit with the tested production builds after release approval.
