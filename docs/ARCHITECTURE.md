# Architecture and stack

The system uses one Expo client and one Python modular monolith. The implemented foundation includes FastAPI, typed settings, async SQLAlchemy/psycopg, Alembic, PostgreSQL 16 with PostGIS/pgvector, health/readiness endpoints, Clerk JWT verification, internal account mapping, error envelopes, request IDs, Docker and CI. Domain modules own identity, catalog, trips, planning, routing and contextual answers inside the API process.

| Boundary | Implementation target |
|---|---|
| Mobile shell and identity | Expo SDK 58, React Native 0.88.1, React 19.3, TypeScript 6, Expo Router, Clerk Expo and SecureStore |
| Planner UI | React Hook Form + Zod for input, Zustand for draft/UI state, TanStack Query v5 for server state, i18next/react-i18next and expo-localization for vi/en |
| Native interaction | react-native-maps with Google Maps on iOS/Android, draggable-flatlist with Expo-compatible Reanimated and Gesture Handler, external Apple/Google Maps for navigation |
| Transport | HTTPS REST and SSE through expo/fetch, native-device streaming spike before selecting a fallback. Generate mobile types from FastAPI OpenAPI with openapi-typescript |
| API and persistence | Python 3.12 with uv, FastAPI/Uvicorn, Pydantic v2/settings, SQLAlchemy 2 async, psycopg 3, Alembic, PostgreSQL 16 with PostGIS and pgvector |
| Data supply | Versioned Overture/FSQ Open Source imports, Wikidata and first-party source evidence; provider-policy adapters for VietMap/Goong/Map4D evaluation, Google Places runtime enrichment and Google Routes measurements |
| Integrations | Gemini through Google GenAI SDK, optional Agno/AgentOS orchestration behind a domain interface, HTTPX provider adapters, Clerk JWKS verification, sse-starlette for stream delivery |
| Quality | Ruff, mypy, pytest/asyncio/cov, respx, testcontainers. Jest/jest-expo and React Native Testing Library for components, Maestro for native E2E |

## Data plane

```text
Overture/FSQ release   Wikidata   official/operator evidence   licensed media
        \                 |                 |                       /
         -> importer -> staging -> identity resolution -> bilingual review
                                            |
                                            v
                                 immutable publication manifest
                                            |
                       +--------------------+--------------------+
                       |                                         |
                  Explore/search                    planner candidate DTO
                                                                 |
                                                      Gemini proposes IDs/order
                                                                 |
                                                deterministic validation/schedule
                                                                 |
                                        Google Routes -> preview -> explicit Save

Google Places / local map providers -> policy-aware runtime adapter -> attributed view
                                      (no implicit canonical persistence)
```

Provider adapters are anti-corruption layers. Each adapter maps external schemas into typed internal DTOs and declares which fields are identifiers, ephemeral display values or contractually retainable. Domain repositories never accept raw provider JSON. Import jobs and refresh jobs are application commands inside the modular monolith, not model tools and not independent microservices.

The catalog publication manifest is the consistency boundary shared by Explore, Planner and Local Guide. A refresh creates new revisions; accepted trips retain the catalog/fact revisions used when they were saved. Suspended places disappear from new candidate sets while historical trips remain explainable.

## Request path

1. Verify Clerk identity, resource ownership, revision and request limits before private retrieval or paid calls.
2. Load the exact publication manifest and resolve runtime provider fields only through approved adapters. Planner receives eligible published IDs, restrictions and reviewed facts. Local Guide reads approved evidence for the scoped POI or trip. The model receives no generic network, SQL or provider tool.
3. Validate the Planner proposal with Pydantic and domain checks. Permit Repair one bounded attempt for a correctable output error. Unknown IDs or facts are rejected. Google Routes supplies WALK/DRIVE measurements. The scheduler computes times and Plan Health. A missing required leg yields a blocked/incomplete result.
4. Store a revision-bound preview. Only the explicit accept operation can atomically promote it. Recheck revision and publication after provider work, outside long-lived transactions. See [API](API.md).
5. Guide answers stream in the selected locale with source identifiers, or return insufficient_evidence. Cancellation and stream failure preserve the current edit.

## Deployment boundary

GitHub Actions builds a multi-stage API image in Artifact Registry. Cloud Run serves it under a dedicated service account with scoped Cloud SQL and Secret Manager access. Cloud Storage serves licensed versioned media. Cloud Logging/Monitoring collect redacted outcomes, latency, failure and quota signals. Separate development, staging and production configuration. Store server credentials outside the client. Restrict the client Maps SDK key by platform, app and API.

Benchmark and pin Gemini model/settings during implementation. Start with a deterministic workflow and one schema-constrained model boundary; adopt Agno/AgentOS orchestration only where an evaluation proves it reduces complexity or improves quality. Record provider terms/configuration, prompt, corpus, import release and content revisions with evaluation results. See [development](DEVELOPMENT.md) for release gates.
