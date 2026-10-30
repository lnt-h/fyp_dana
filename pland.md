# Gonarra — Working Plan

Last updated: 2026-10-29

**Status:** Provisional product and delivery roadmap. This is not yet a decision-complete implementation specification. Resolve each phase's decision gates before implementing dependent work.

## 1. Confirmed direction

Gonarra is a mobile-first travel companion for international first-time visitors exploring Da Nang.

- Builder: solo developer.
- Initial release: real visitor pilot with a flexible deadline.
- Primary outcome: help a visitor plan and complete a realistic one-day trip.
- Pilot geography: a compact central Da Nang area; exact boundary remains open.
- Transport: **walking only**. This supersedes the earlier taxi/Grab recommendation and existing car-based planning documentation.
- Stack: React Native, Expo, TypeScript, Expo Router.
- Navigation: Home, Explore, Trips, Saved; Profile and Settings through the avatar rather than a separate tab.
- Visual direction: navy, sky blue, teal, warm orange, immersive destination imagery, modern minimal layouts, accessible audio controls, and clear source attribution.
- Content readiness: no reviewed content currently exists.
- Existing product and architecture documents are context; consequential decisions must be revalidated.
- Unchosen providers, infrastructure, and budget are explicit decision gates, not silently selected defaults.

The repository already contains an app shell, branded splash, onboarding, and preview account/home screens. The dependency baseline was aligned using Expo CLI on 2026-10-29: Expo `~58.0.21`, React Native `0.88.1`, React `19.3.0`, Expo Router `~58.0.28`, and TypeScript `~6.0.3`. TypeScript validation and dependency validation pass, and Expo Doctor passes 20/20 checks. Native builds and device behavior remain unverified. npm audit reports eight dependency findings (five low, three high) in the Expo tooling dependency chain; its proposed automatic fix downgrades Expo to SDK 51 and was not applied. Inspect current compatibility again before future dependency changes.

### Authentication implementation update — 2026-10-29

- Integrated the selected existing Clerk application with `@clerk/expo` and secure native token caching.
- Connected the custom React Native sign-up, email verification, password sign-in/recovery, Google/Apple SSO, and sign-out controls.
- Profile names and travel preferences now use Clerk user data; guest preferences remain session-only.
- Enabled email/password and email-code verification in the development instance. Google, Apple, and Native API were already enabled. Production is not configured.
- TypeScript, Expo Doctor (20/20), Clerk Doctor, and bundle export pass; web screens and empty-field validation were inspected. Expo Go launch, Welcome layout, and empty login validation were also verified on the iPhone 18 Pro simulator.
- Real account sign-in, social callbacks, and native session restoration still need verification. Account deletion, email updates, legal documents, and additional session-task flows remain unfinished.

## 2. Intended capabilities

These are requested capabilities; their pilot release priority still needs confirmation.

### Discovery and place details

- Explore curated places across Culture, Beach, Food, and Nature.
- Search by English names, Vietnamese names, and romanized aliases.
- View destination images, reviewed facts, sources, and map locations.
- Present honest unavailable, uncertain, stale, loading, offline, and empty states.

Walking-only central coverage may not support every category meaningfully. Confirm the boundary and available places before promising category coverage.

### Identity and personal data

- Email/password registration and login.
- Google login is optional and not committed to the pilot.
- Save and unsave places.
- Manage trips and settings, log out, and delete the account.
- Decide guest capabilities and authentication prompts before implementing these flows.

### Planning and trip execution

- Generate a personalized one-day itinerary from interests, pace, available time, budget preference, and starting location.
- Review AI-generated proposals before using them.
- Add, remove, reorder, and change stop durations.
- Preview walking routes and open Google Maps or Apple Maps directions.
- Start a trip, show current and next stops, mark arrival, complete or skip stops, and show progress.

### Audio, questions, and connectivity

- Play human-recorded English audio guides and read transcripts.
- Ask contextual place questions and receive source-supported answers.
- Cache essential trip content and audio authorized for offline use.
- Make connectivity limitations and unsupported actions explicit.

## 3. Step-by-step delivery sequence

All steps below are pending; existing splash/onboarding work does not imply completion of a phase.

### Step 1 — Reconcile scope and inspect the app

- [ ] Compare current implementation with this working baseline.
- [ ] Confirm installed dependencies and check official compatibility documentation.
- [ ] Preserve the stated stack.
- [ ] Record documentation conflicts, especially walking versus car routing and visual colors.
- [ ] Confirm target platforms and physical test devices.
- [ ] Agree the pilot boundary and prioritize requested capabilities.

**Completion:** agreed pilot boundary, prioritized capabilities, and verified app baseline.

### Step 2 — Establish the content foundation

- [ ] Define the geographic boundary using realistic pedestrian routes.
- [ ] Inventory candidate places, opening information, visit durations, costs, entrance coordinates, and accessibility information.
- [ ] Assign responsibility for factual review and updates.
- [ ] Record image, narration, transcript, and offline-use rights.
- [ ] Prepare a small reviewed collection before depending on it for itinerary generation.
- [ ] Confirm achievable coverage across the four requested categories.

**Completion:** enough approved content to support at least one realistic day and alternative stops.

### Step 3 — Resolve architecture and service decisions

- [ ] Choose backend, database, authentication, media storage, map rendering, pedestrian routing, and AI services.
- [ ] Set spending limits and behavior when quotas are exhausted.
- [ ] Define client/server responsibilities and API contracts.
- [ ] Resolve offline scope, synchronization rules, and trip persistence behavior.
- [ ] Specify account deletion and content retention behavior.
- [ ] Define content publishing and review workflow.
- [ ] Confirm environments, deployment, secrets management, and required CI checks.

**Completion:** recorded service decisions and contracts sufficient to implement without guessing.

### Step 4 — Build discovery and identity

- [ ] Implement four-tab navigation and avatar entry points.
- [ ] Connect curated discovery, multilingual name search, details, source attribution, and maps.
- [ ] Implement agreed guest access, authentication, and saved places.
- [ ] Cover permission denial, unavailable imagery, empty results, and network errors.

**Completion:** a visitor can find and understand a reviewed place and retain it through the agreed save flow.

### Step 5 — Build itinerary creation and editing

- [ ] Implement preference collection and starting-location entry.
- [ ] Generate proposals using the approved place catalog, subject to confirmation of this provisional catalog constraint.
- [ ] Validate walking feasibility, timing, and available operational facts.
- [ ] Implement review, persistence, stop editing, and route recalculation.
- [ ] Preserve user edits when generation or routing fails.
- [ ] Explain infeasible requests and uncertain estimates.
- [ ] Confirm generation retry, cancellation, duplicate-request, and timeout behavior before integration.

**Completion:** a visitor can create and customize a plausible day within the pilot area.

### Step 6 — Build active trips

- [ ] Implement current/next stop presentation, arrival, completion, skipping, and progress.
- [ ] Support external walking directions.
- [ ] Restore the trip after app restart.
- [ ] Define how edits affect an active trip before implementing them.
- [ ] Prevent repeated taps or retries from producing duplicate progress.

**Completion:** a visitor can follow and finish a trip with consistent progress.

### Step 7 — Add audio, contextual answers, and caching

- [ ] Implement playback, transcripts, availability states, and authorized downloads.
- [ ] Answer contextual questions using approved supporting material.
- [ ] Return an honest insufficient-evidence response when necessary.
- [ ] Implement the agreed offline scope and storage controls.
- [ ] Show download, stale-content, and reconnection states.
- [ ] Verify audio licensing and offline authorization before enabling downloads.

**Completion:** supported content remains useful under the agreed weak-connectivity scenarios.

### Step 8 — Run a controlled visitor pilot

- [ ] Perform field checks of pedestrian routes, entrances, durations, and content.
- [ ] Observe visitors completing the primary journey.
- [ ] Capture failures and feedback with privacy-conscious diagnostics.
- [ ] Resolve release-blocking defects before expanding access.
- [ ] Record pilot findings and reprioritize later work from evidence.

**Completion:** visitors can complete the core journey; pilot findings determine the next iteration.

## 4. Data and interface boundaries

Candidate entities, pending detailed design:

- User and authentication session.
- Place, localized names/aliases, categories, facts, sources, and media.
- Saved place.
- Trip, preferences, ordered stops, route estimates, and progress.
- Audio guide, transcript, rights, and content version.
- Supporting passages for contextual answers.
- Download/cache metadata.

Required interface families:

- Public place discovery and detail retrieval.
- Authentication and account management.
- Owner-scoped saves and trips.
- Itinerary generation, review, editing, and routing.
- Trip progress.
- Audio access and authorized downloads.
- Source-supported contextual questions.

Exact fields, relationships, uniqueness rules, validation, endpoints, providers, and synchronization contracts remain decision gates. Provider secrets must remain server-side, and private records must enforce ownership.

## 5. Verification and pilot acceptance

- [ ] Search finds reviewed English, Vietnamese, and romanized names.
- [ ] Generated itineraries contain valid places and plausible pedestrian routes.
- [ ] Impossible schedules and missing facts produce understandable outcomes.
- [ ] Stop edits update relevant route and timing information without losing work.
- [ ] Restart and retry scenarios preserve consistent trip progress.
- [ ] Location denial has an agreed usable fallback.
- [ ] External-map handoff works on each supported platform, including unavailable-app behavior.
- [ ] Audio availability, playback, transcripts, and authorized caching work as specified.
- [ ] Contextual answers cite supporting sources or acknowledge insufficient evidence.
- [ ] Offline behavior matches the documented contract.
- [ ] Users cannot access another user's private records.
- [ ] Logout and deletion follow the selected authentication and retention design.
- [ ] Core screens support accessible controls, text scaling, and compact phones.
- [ ] Provider failures, quota exhaustion, and slow networks have understandable recovery paths.

Numeric performance targets, supported devices, automated test coverage, and pilot success thresholds remain to be agreed. Use appropriate unit, integration, device, and field checks after the relevant behavior is specified.

## 6. Assumptions — provisional, not confirmed

- English is the initial interface and narration language.
- Planning uses a curated catalog rather than unrestricted AI-discovered places.
- External apps provide turn-by-turn navigation.
- Arrival is manually confirmed unless foreground assistance is explicitly approved.
- Payments, bookings, social features, background tracking, and multi-day trips are deferred.
- Full offline maps and offline AI are excluded unless explicitly added.

The earlier recommendation of 10–15 reviewed places and 3–5 audio guides is not a confirmed target. Existing documents mentioning 15–20 places and five guides also require revalidation.

## 7. Open decision gates

### Product and content

- Exact walking boundary, category coverage, place count, and audio count.
- Content reviewer, recording process, licensing, and update ownership.
- Guest access, first-signup journey, and exact authentication gates.
- Pilot feature priorities and monetization expectations.
- Itinerary scheduling rules, budget meaning, meals, breaks, opening-hour handling, and start/end behavior.
- Active-trip editing, repeated visits, and multiple active trips.

### Architecture and operations

- Monthly infrastructure/API budget and quota behavior.
- Backend, authentication, maps, pedestrian routing, AI, and hosting providers.
- AI request limits, grounding workflow, retries, and failure handling.
- Offline read/write behavior, download controls, and conflict resolution.
- Platforms, minimum OS versions, permissions, deployment, and release channels.
- Privacy retention, diagnostics, alerts, accessibility targets, and pilot success measures.
- Account recovery, deletion semantics, and supported content management workflow.

## 8. Open risks

- Walking-only coverage may conflict with the intended breadth of attractions.
- Routing data may miss pedestrian entrances or practical access restrictions.
- Content production and verification may constrain delivery more than coding.
- Unverified operating information can make otherwise valid itineraries unusable.
- Offline mutations and active-trip edits can create substantial synchronization complexity.
- Unset API budgets and quotas prevent a credible operating-cost estimate.
- Existing documentation may conflict with newly confirmed decisions and must not silently override them.

## 9. Research context

These comparisons informed interview recommendations; they are not validated evidence of visitor demand or commitments to match competitor features.

- [Wanderlog route optimization](https://help.wanderlog.com/hc/en-us/articles/13545624787867-Optimize-route): a reference for ordering a day's stops to reduce travel time.
- [How VoiceMap tours work](https://support.voicemap.me/how-does-a-voicemap-tour-work/): a reference for place-based audio experiences and walking tours.
- [VoiceMap offline support](https://support.voicemap.me/can-i-use-voicemap-offline/): a reference for downloaded tour content; Gonarra's exact offline scope remains undecided.

## 10. Working-plan maintenance

- Record answers as confirmed decisions only after explicit agreement or implementation evidence.
- Keep assumptions and unresolved decisions visibly separate from requirements.
- Update conflicting project documentation when decisions are finalized.
- Mark checklist items complete only with implementation or verification evidence.
- Do not treat this working roadmap as authorization to invent unresolved provider, budget, or product choices.
