# Gonarra

<p align="center">
  <img src="apps/mobile/assets/brand/gonarra-app-icon.svg" width="72" alt="Gonarra" />
</p>

Gonarra is the working name for a bilingual Vietnamese/English AI itinerary planner for travel in Vietnam. The FYP release covers Đà Nẵng only, including the Hội An area, with editable one-to-three-day itineraries shown as a timeline and map; Hà Nội, Thành phố Hồ Chí Minh and Huế are on the roadmap.

Built with React Native, Expo, TypeScript, Expo Router and a Python/FastAPI modular monolith. The current build includes onboarding and Clerk sign-in, the Đà Nẵng catalog with search and place cards, AI trip proposals with a timeline, map, Plan Health and explicit Save, and the city-level Guide, on PostgreSQL 16 with PostGIS and pgvector.

The catalog comes from open data (OpenStreetMap, Wikidata, Wikipedia, Wikivoyage, Wikimedia Commons) and the owner's sheet, with field-level provenance and an automated publication gate (DEC-022). Descriptions and facts are human-written from cited sources and never AI-generated (DEC-031); each description carries its attribution and licence. Restricted provider content remains runtime-only under its terms. Models may select only published Gonarra place IDs; route distances and durations come from Google Routes, or from a labelled estimate in the demo (DEC-023). AI is used only for planning rationales and Guide answers, from supplied evidence. See the [data model](docs/04-design/data/data-model.md) and the [project guide](docs/PROJECT_GUIDE.md).

## Getting started

```bash
cd apps/mobile
npm ci
# Authenticate the CLI, then restore keys for the existing linked Clerk app:
npx -y clerk@latest auth login
npx -y clerk@latest env pull
npx expo start --go
```

Press `a` for Android, `i` for iOS, or `w` for web. To create a native development build, run `npm run android` or `npm run ios`.

Run the backend foundation from the repository root:

```bash
docker compose up -d db
cd apps/api
cp .env.example .env   # then fill in the keys; GONARRA_DATABASE_URL points at the Postgres container
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Running the app day to day

The app has no offline or demo data: every screen reads from the API, and the API reads from PostgreSQL. All three must be up, in this order, before the app can load. Skipping step 1 is the usual cause of a red "could not load data" banner on the home screen: `/health` still answers 200, but every `/v1/*` endpoint returns 500 with `connection to server at "127.0.0.1", port 5432 failed`.

1. **Database** (Docker Desktop must be running first; it does not start on login):

   ```bash
   open -a Docker                      # macOS; wait until the whale icon stops animating
   cd /path/to/fyp_dana
   docker compose up -d db --wait
   ```

2. **API** (from `apps/api`; `.env` must already exist):

   ```bash
   cd apps/api
   uv run python -m app.cli db-check   # alembic head == database revision, otherwise run the next line
   uv run alembic upgrade head
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   `--host 0.0.0.0` is required for a phone on the same Wi-Fi to reach the API. Check with `curl http://localhost:8000/ready` (needs the DB) and `curl "http://localhost:8000/v1/cities?locale=vi"`.

3. **Mobile** (from `apps/mobile`):

   ```bash
   cd apps/mobile
   npx expo start --go
   ```

   `apps/mobile/.env.local` must set `EXPO_PUBLIC_API_URL=http://<your LAN IP>:8000` (no trailing `/v1`). Your LAN IP changes between networks: get it with `ipconfig getifaddr en0` and restart Metro after editing the file, because `EXPO_PUBLIC_*` values are inlined at build time. A phone cannot reach `localhost` on your computer.

   Demo mode (`EXPO_PUBLIC_DEMO_NO_AUTH=1` in the mobile `.env.local`) requires `GONARRA_DEMO_SHARED_USER=1` in the API `.env`; set both or neither.

### Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Home shows an error banner; `/health` is 200 but `/v1/cities` is 500 | Postgres is down (Docker Desktop not running) | Step 1, then pull to refresh |
| "Not configured" screen in the app | `EXPO_PUBLIC_API_URL` empty or not `http(s)://` | Fix `.env.local`, restart Metro |
| App shows offline / network error, `curl` on the computer works | Phone cannot reach the API: wrong LAN IP, API bound to `127.0.0.1`, or phone on another network | Update the IP, start uvicorn with `--host 0.0.0.0` |
| `db-check` exits 1 | Migrations behind the code | `uv run alembic upgrade head` |
| Catalog is empty after a fresh volume | Database recreated | Re-run the ingestion pipeline (`apps/api/README.md`) |

## Deploy

Production runs on one VM with `docker-compose.prod.yml`: Caddy (automatic HTTPS) in front of the API, PostgreSQL 16 + PostGIS + pgvector with no published port, a one-shot migration job before every API start, and nightly `pg_dump` backups kept 14 days. Images build natively on arm64 and amd64.

```bash
cp infra/.env.example .env && chmod 600 .env   # host name, ACME email, DB password, provider keys
GONARRA_API_TAG=$(git rev-parse --short HEAD) docker compose -f docker-compose.prod.yml up -d --build --wait
curl -fsS https://<GONARRA_API_HOST>/ready
```

First deploy on a fresh Ubuntu VM, updates, rollback, restore from backup and logs: [infra/README.md](infra/README.md). The local `docker-compose.yml` stays the development stack (settings from `infra/dev.env` then `apps/api/.env`; database on `127.0.0.1` only).

## Documentation

Start at the [documentation index](docs/README.md). Key documents: [decision log](docs/decisions.md), [business requirements](docs/02-requirements/BRD.md), [product requirements](docs/03-analysis/PRD.md) and [user stories](docs/03-analysis/user-stories.md), [architecture](docs/04-design/architecture/SAD.md) and [ADRs](docs/04-design/adr/), [API contract](docs/04-design/api/openapi.yaml), [database schema](docs/04-design/data/schema.sql) and [data model](docs/04-design/data/data-model.md), [UI/UX](docs/04-design/ui-ux/README.md), [development plan](docs/05-development/Software_Development_Plan.md), [test plan](docs/07-verification/TEST_PLAN.md) and [research protocol](docs/07-verification/RESEARCH_PROTOCOL.md).

The previous full SDLC set is kept at git tag `docs-sdlc-full`.
