# Gonarra Product

## Purpose

Gonarra helps first-time international visitors discover and understand Da Nang without switching between disconnected articles, maps, and planning tools. The experience is English-first while preserving reviewed Vietnamese place names and aliases.

The product should feel calm, local, and trustworthy. Unknown information remains unknown, AI output is validated before it reaches the user, and navigation or location capabilities are described honestly.

## Current status

Gonarra is an early mobile product build.

Implemented:

- Branded splash screen with an automatic transition.
- First onboarding screen based on the Figma design.
- Responsive layouts, safe-area handling, accessible button semantics, and branded application icons.
- Expo Router application shell for iOS, Android, and web.

Not yet implemented:

- Authentication, place discovery, maps, trip planning, audio playback, offline support, backend APIs, and production analytics.

Documentation distinguishes current behavior from planned behavior. A planned feature must not be presented as shipped.

## Primary user

An English-speaking visitor who is unfamiliar with Da Nang and wants to:

- Match English, Vietnamese, and romanized place names.
- Discover reviewed places and understand why they matter.
- Build and edit a realistic one-day itinerary.
- Receive useful guidance during a visit without hidden background tracking.

## Planned core journey

Welcome → Explore → Place detail → Plan a day → Review proposal → Save and edit → Route preview → Start trip → Open external directions → Confirm arrival → Listen or ask → Continue to the next stop.

## Product scope

### First release

- A reviewed set of 15–20 Da Nang places across culture, beach, food, and nature.
- Search by English name, Vietnamese name, alias, category, and tag.
- Place details with reviewed facts, sources, imagery, and audio availability.
- One-day planning for car or ride-hailing travel.
- AI-assisted itinerary proposals constrained to published place IDs and verified route data.
- Explicit proposal acceptance before the itinerary becomes editable.
- External Google Maps or Apple Maps handoff; no in-app turn-by-turn navigation.
- Manual arrival as the primary action, with optional foreground-only location assistance.
- Five reviewed, human-recorded English audio guides.
- Source-grounded, single-turn questions with a clear insufficient-evidence response.
- Authenticated saves, private trips, session management, and account deletion.
- Revision-bound read-only trip essentials cache; no offline maps or routing.

### Later candidates

- Landmark recognition.
- Speech-to-text question input.
- Google sign-in.
- Multi-day planning and broader destination coverage.

### Explicitly out of scope for the first release

- Payments or bookings.
- Background GPS tracking.
- Text-to-speech or an autonomous voice assistant.
- In-app turn-by-turn navigation.
- Full offline maps or routing.
- Social feeds and public trip sharing.

## Product rules

- Published place IDs and operational facts come from reviewed records, never from model invention.
- AI proposals are schema-validated, checked for duplicate or unknown places, and explicitly accepted by the user.
- User edits are not silently overwritten.
- Route duration comes from the selected route provider and includes freshness metadata.
- No supporting evidence means no factual answer.
- Guest inputs survive an authentication round trip and are never submitted automatically.
- Cached or offline actions are labelled pending until the server confirms them.
- Audio is identified as human-recorded and is unavailable when no approved asset exists.
- Current and future private data remains owner-scoped.

## Experience direction

- Deep ocean, white, teal, and warm yellow form the core palette.
- Da Nang photography is the primary visual material.
- One dominant action per region, generous spacing, and clear status language.
- Touch targets must be at least 44 points and text must support platform scaling.
- Error, offline, pending, stale, simulated, and insufficient-evidence states must be explicit.

The implementation source of truth is the codebase. The visual reference is the [Gonarra Figma prototype](https://www.figma.com/design/JvXw7rVf5KxoA6LlDJEqAt/Tourguide-app-UI).

## Acceptance baseline

- Core screens work on a compact phone and the 440 × 956 reference viewport.
- Critical actions have accessible roles and labels.
- Cross-user access, invented facts or IDs, duplicate arrival events, and silent data loss are release blockers.
- Provider, permission, and network failures have visible recovery paths.
- Fixture or simulated behavior is labelled and never reported as live evidence.
