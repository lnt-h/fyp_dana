# Architecture and stack

The target is one Expo client and one Python modular monolith. The [repository overview](../README.md) describes the implemented mobile baseline. Domain modules own identity, catalog, trips, planning, routing and contextual answers inside the API process.

| Boundary | Implementation target |
|---|---|
| Mobile shell and identity | Expo SDK 58, React Native 0.88.1, React 19.3, TypeScript 6, Expo Router, Clerk Expo and SecureStore |
| Planner UI | React Hook Form + Zod for input, Zustand for draft/UI state, TanStack Query v5 for server state, i18next/react-i18next and expo-localization for vi/en |
| Native interaction | react-native-maps with Google Maps on iOS/Android, draggable-flatlist with Expo-compatible Reanimated and Gesture Handler, external Apple/Google Maps for navigation |
| Transport | HTTPS REST and SSE through expo/fetch, native-device streaming spike before selecting a fallback. Generate mobile types from FastAPI OpenAPI with openapi-typescript |
| API and persistence | Python 3.12 with uv, FastAPI/Uvicorn, Pydantic v2/settings, SQLAlchemy 2 async, psycopg 3, Alembic, PostgreSQL 16 with PostGIS and pgvector |
| Integrations | Agno/AgentOS, Gemini through Google GenAI SDK, HTTPX for Routes, Clerk JWKS verification, sse-starlette for stream delivery |
| Quality | Ruff, mypy, pytest/asyncio/cov, respx, testcontainers. Jest/jest-expo and React Native Testing Library for components, Maestro for native E2E |

## Request path

1. Verify Clerk identity, resource ownership, revision and request limits before private retrieval or paid calls.
2. Concierge routes intent to Planner or Local Guide. Planner receives eligible published IDs, restrictions and reviewed facts. Local Guide reads approved evidence for the scoped POI or trip. Agents receive typed read tools.
3. Validate the Planner proposal with Pydantic and domain checks. Permit Repair one bounded attempt for a correctable output error. Google Routes supplies WALK/DRIVE measurements. The scheduler computes times and Plan Health. A missing required leg yields a blocked/incomplete result.
4. Store a revision-bound preview. Only the explicit accept operation can atomically promote it. Recheck revision and publication after provider work, outside long-lived transactions. See [API](API.md).
5. Guide answers stream in the selected locale with source identifiers, or return insufficient_evidence. Cancellation and stream failure preserve the current edit.

## Deployment boundary

GitHub Actions builds a multi-stage API image in Artifact Registry. Cloud Run serves it under a dedicated service account with scoped Cloud SQL and Secret Manager access. Cloud Storage serves licensed versioned media. Cloud Logging/Monitoring collect redacted outcomes, latency, failure and quota signals. Separate development, staging and production configuration. Store server credentials outside the client. Restrict the client Maps SDK key by platform, app and API.

Benchmark and pin Gemini model/settings during prototype work. Record provider configuration, prompt, corpus and content revisions with evaluation results. See [development](DEVELOPMENT.md) for release gates.
