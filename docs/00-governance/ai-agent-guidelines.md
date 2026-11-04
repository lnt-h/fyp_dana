# Agent brief — Gonarra documentation rebuild

Read this before generating or auditing any artifact. It is a summary; the sources of truth are the files listed.

## Sources of truth (read, do not modify unless you are told to write them)

- Requirements baseline: `docs/02-requirements/BRD.md` (BO-, MET-, SN-, BR-, AC-, BRU-, CON-, ASM-, DEP-, RSK-, OQ-, DEC- IDs).
- Elicitation record: `docs/02-requirements/interviews/SRC-100-elicitation-session-2026-11-04.md` (decisions DEC-001..007, data sources SRC-104, stack).
- Product baseline: `plan.md` (SRC-001; §4 amended by BRD §5.2), `progress.md` (SRC-002), `AGENTS.md` (SRC-003 — hard rules).
- Pre-rebuild contracts (still in `docs/`, to be replaced): `ARCHITECTURE.md`, `API.md`, `DATA.md`, `DATABASE-DESIGN.md`, `SECURITY.md`, `TESTING.md`, `RESEARCH.md`, `USE-CASES.md`, `USER-STORIES.md`, `PRD.md`, `DEVELOPMENT.md`. Reuse their substance; they cite FR-00..07, US-00..08, UC-00..06, HA-02.
- Code baseline: `apps/api` (FastAPI, migration `migrations/versions/20261102_0001_foundation.py`, `openapi.json`), `apps/mobile` (Expo Router screens in `src/app`).
- Kit (read-only): `/Users/lengoctanhien/SDLC-Prompt-Checklist` — prompts and `.xlsx` checklists; `step-by-step-guidance.md` §A4–A9.

## People and roles

- Owner, author, BA, curator, engineer: **Lê Ngọc Tấn Hiền** (student).
- Mentor, approver of every gate: **trantrongminh** (full name pending, OQ-001). Agents never approve; approval rows stay `[Pending]`.

## Fixed decisions (do not re-open; raise conflicts as OQ-xxx)

- Direction (DEC-001): trustworthy planner + grounded assistant. Must: search, proposal 1–3 days single city, timeline+map, Plan Health, edits, explicit Save, place card, text Guide with sources, booking handoff, bilingual VI/EN, 5 cities (Hà Nội, TP.HCM, Đà Nẵng, Hội An, Huế). Should: lock + day regeneration, voice Q&A, photo identification. Could: indicative stay prices (LiteAPI, fallback Hotelbeds; runtime only). Won't (roadmap): in-app booking/payment, flights, social, multi-city.
- Cut order (DEC-003): prices → photo → voice → lock/regeneration → iOS.
- Stack (CON-004/005, DEC-005/006): three separate deployables talking only over HTTP API `/v1` (REST + SSE): `apps/api` Python 3.12/uv/FastAPI/Pydantic v2/SQLAlchemy 2 async/Alembic/httpx, modular monolith (identity, catalog, trips, planning, routing, guide, stays, curation); `apps/mobile` Expo SDK 58/RN 0.88/TS/Expo Router/Clerk/TanStack Query/Zustand/RHF+Zod/i18next/react-native-maps; `apps/admin` curator SPA React+Vite+TS+TanStack Query+Clerk (curator role). OpenAPI → `openapi-typescript` types. PostgreSQL 16 + PostGIS + pgvector.
- AI: Gemini (Google GenAI SDK) free tier — structured itinerary proposal choosing only supplied published place IDs; embeddings for Guide RAG; vision for photo ID restricted to published places within 300 m. Voice: on-device STT/TTS (expo-speech + Expo speech-recognition module), Gemini Live optional later. Never send account IDs, contact data or precise location to AI (BR-046).
- Routing: Google Routes (WALK/DRIVE). Live hours: Google Places runtime only. Data seed: Overture Places, Foursquare OS Places, Wikidata; facts from official sources; images own/Wikimedia Commons.
- Hosting (DEC-005): AWS ap-southeast-1 — EC2 t4g.small running Docker Compose (FastAPI + Caddy TLS), RDS PostgreSQL 16 db.t4g.micro, S3 (media, admin SPA), ECR, SSM Parameter Store, CloudWatch, budget alarms USD 20/50/100. No NAT gateway, ALB, Fargate or App Runner. CI GitHub Actions; EAS Build for mobile.
- Budget: USD 0 cash, AWS credits USD 200 (CON-001). Deadline ~2027-02-01 (ASM-002). User study 10–15 participants mid-January 2027.

## Rules for every artifact

- Run the named kit prompt literally: its §5 output contract, §6 self-check, §7 structure. Fill its `2.2` parameters in an adapted copy under `docs/00-governance/prompt-templates/<kit-path>` (keep the six sections; add a first-line HTML comment naming the kit file and commit `6996dae`) and add a row to `docs/00-governance/template-adaptation-log.md`.
- Write in English. Document control: ID `GONARRA-<KIND>`, version 0.1, status Draft, owner Lê Ngọc Tấn Hiền, approver trantrongminh, date 2026-11-04, prompt path + version.
- Preserve every existing ID; never renumber; new IDs continue the scheme of kit A9 (FR-, NFR-, US-, AC-, CMP-, ADR-, API-, TASK-, TC-, DEF-). Legacy FR-00..07 / US-00..08 / UC-00..06 / HA-02 may be kept as a "Legacy ID" column.
- Never invent people, dates, numbers, approvals or test results. Unknowns → `OQ-xxx` (continue after OQ-007) with owner Lê Ngọc Tấn Hiền and a needed-by date; assumptions → `ASM-xxx` (continue after ASM-011).
- Only write the files your task names. Do not edit `BRD.md`, `plan.md`, `AGENTS.md`, code, or old docs.
- End your reply with: files written, self-check score (Pass/Partial/Fail counts), and any direction question that needs the owner (with your recommendation).

## Current implementation status (owner, SRC-100 A-020)

Done by the owner: mobile onboarding screens and Clerk third-party authentication. The repository also contains an
unverified backend foundation in `apps/api` (FastAPI, foundation migration, Clerk JWT verifier, health endpoints).
Everything else (catalog, planner, routing, guide, admin, AWS) is not started. Plans and test documents must not
present anything else as implemented.

## Stack review additions (2026-11-04, accepted by owner — SRC-100 A-021)

- DEC-008 Scheduling: Google OR-Tools (time-window routing) orders stops and computes times from visit durations and a cached Google Routes Compute Route Matrix; Gemini only selects/ranks published place IDs and writes rationales; locks are solver constraints; Plan Health is deterministic validation.
- DEC-009 Ingestion: Typer CLI in `apps/api` using DuckDB over Overture/Foursquare GeoParquet (city bounding box) and Wikidata; no worker/queue/Redis. Chunk embeddings are computed on write by the curation API before approval and publication (DEC-012, ADR-012 0.3); the CLI only backfills and re-embeds.

## AI design alignment (2026-11-05, accepted by owner — SRC-100 A-028)

- DEC-010 Guide retrieval in two tiers (ADR-010 0.3): a place-scoped question (v1) uses every approved fact and every approved chunk of the place's pinned corpus revision as evidence, with no question embedding and no similarity threshold; city-scoped questions (roadmap) use hybrid lexical + pgvector retrieval with a calibrated threshold. Chunks are authored per section (OVERVIEW, HISTORY, HIGHLIGHTS, VISIT_TIPS, ETIQUETTE, ACCESS).
- DEC-011 Scheduling as one multi-day OR-Tools model per proposal (ADR-011 0.2): days are vehicles, (place, day) nodes carry that date's opening window, drop penalties follow Gemini ranks, locks are mandatory nodes. Gemini ranks one pool for the trip and never assigns days, orders stops or sets times (ADR-004 0.2).
- DEC-012 Chunk embeddings on write (ADR-012 0.3): `PATCH /v1/admin/candidates/{id}` accepts `chunks[]`, embeds new or changed chunks synchronously through the AI gateway and records `embedding_model`; the question embedder (Tier 2) must use the same model; a model change runs `cli embed --reembed-all`.
- No Agno/AgentOS. Production images built for linux/arm64 (EC2 t4g).
