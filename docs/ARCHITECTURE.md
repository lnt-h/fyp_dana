# Gonarra Architecture

## Current implementation

The repository currently contains one Expo application at `apps/mobile`. It implements the splash and first onboarding screen; backend services described below are a target architecture, not deployed software.

### Mobile stack

- React Native 0.88 and React 19.
- Expo SDK 58.
- Expo Router for file-based navigation.
- TypeScript in strict mode.
- `react-native-svg` for resolution-independent brand marks.
- `expo-linear-gradient` for branded visual treatments.

### Mobile structure

```text
apps/mobile/
├── assets/
│   ├── brand/          # Editable SVG brand sources
│   └── onboarding/     # Screen-specific photography
└── src/
    ├── app/            # Expo Router routes and root layout
    ├── components/     # Reusable brand and UI components
    ├── features/       # Feature-owned components
    └── theme/          # Shared design tokens
```

The splash route is `/`. After a short branded transition it replaces itself with `/onboarding`, preventing the splash screen from remaining in navigation history.

Images remain local, deterministic application assets. Vector brand marks are React components when they need runtime rendering and tracked SVG files when they are build or platform-icon sources.

## Target system boundary

The intended product can remain a modular monolith until measurement demonstrates a need for additional services:

```text
Mobile app
  → HTTPS API
    → PostgreSQL and object storage
    → map and route provider
    → language model and embedding provider
```

Proposed backend modules:

- Identity and sessions.
- Published places and search.
- Saves.
- Trip preferences, proposal validation, and itinerary editing.
- Route metadata and external-map handoff.
- Arrival and trip progression.
- Audio metadata and authorised cache manifests.
- Source-backed question answering.
- Restricted content curation.

No microservices, queue, Redis, or background-location service is required for the first release.

## State and data model

Conceptual records:

- `User` and revocable `Session`.
- `Place`, reviewed aliases, media, facts, and sources.
- `Trip`, `TripDay`, ordered `TripStop`, and revisioned `RouteLeg`.
- Accepted proposal metadata and idempotency records.
- `ArrivalEvent` with one accepted event per trip stop.
- `AudioGuide` with language, version, transcript, rights, and offline policy.
- `Save`, source passages, and content revisions.

The physical database schema will be designed when backend implementation starts. This repository deliberately does not keep speculative production DDL.

## API principles

- Validate every request at the boundary and return typed errors.
- Authenticate private operations and enforce ownership on the server.
- Version client/API compatibility and reject unsupported clients explicitly.
- Use optimistic revisions for itinerary edits.
- Persist idempotency keys for replayable build, acceptance, and arrival operations.
- Keep provider calls outside database transactions.
- Never invent missing route, opening-hour, price, or source data.
- Paginate list endpoints and include locale and freshness metadata where relevant.

## Security and privacy invariants

- Secrets remain server-side and are never embedded in the mobile bundle.
- Passwords use an approved adaptive hash; refresh credentials are stored only as hashes and rotate atomically.
- Logout and account deletion revoke active sessions.
- Private trips, saves, questions, and arrival records are owner-scoped.
- Logs omit raw passwords, tokens, precise location, questions, and media by default.
- Location is requested only for a visible action and used in the foreground.
- Account deletion requires reauthentication and an explicit confirmation.
- Source, translation, image, narration, and offline-use rights are recorded before publication.

## Reliability invariants

- Accepted itineraries are not overwritten by a failed generation or edit.
- Active-trip progress has one current stop and an immutable visited prefix.
- Cached content is bound to itinerary and content revisions.
- Offline mutations are pending until reconciled.
- Route/provider failures produce recoverable states, not fabricated values.
- Process restart restores the active trip and stable replay keys.

## Open production decisions

- Final Android application ID and iOS bundle identifier.
- Minimum supported OS versions and physical test-device matrix.
- Backend framework, hosting region, database service, and restore objectives.
- Map, route, language-model, embedding, and media-storage providers.
- Content licensing, privacy policy, retention periods, and store declarations.

These decisions must be recorded when implementation evidence exists; documentation must not present options as completed infrastructure.
