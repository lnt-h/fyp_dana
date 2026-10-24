# Gonarra Development

## Local setup

Requirements:

- Node.js and npm.
- Android Studio for an Android emulator.
- Xcode for an iOS simulator on macOS.

```bash
cd apps/mobile
npm ci
npx expo start --go
```

Press `a` for Android, `i` for iOS, or `w` for web. Expo Go is the quickest UI workflow. Native development builds use:

```bash
npm run android
npm run ios
```

## Quality checks

Run these before merging application changes:

```bash
npx tsc --noEmit
npx expo-doctor
npx expo export --platform web
```

For UI work, also verify:

- A compact phone width and the 440 × 956 reference viewport.
- Android and iOS safe areas.
- Large text, screen-reader labels, focus order, and 44-point touch targets.
- Loading, empty, error, offline, pending, stale, and denied-permission states in scope.
- No temporary Figma URLs or remote expiring assets.

## Repository conventions

- Routes stay in `src/app` and remain thin.
- Feature-specific UI belongs under `src/features/<feature>`.
- Shared primitives belong under `src/components`.
- Shared visual tokens belong under `src/theme`.
- Editable vector brand sources belong in `assets/brand`.
- Screen photography belongs in a named feature folder under `assets`.
- Use semantic names; avoid Figma layer IDs and raw export hashes.
- Keep user-facing copy in English unless a reviewed local name is part of the content.

## Delivery roadmap

1. Complete onboarding flow and persistent completion state.
2. Build navigation shell, Home, Explore, and Place Detail.
3. Define reviewed place fixtures and the backend contract.
4. Implement authentication and owner-scoped saves.
5. Implement one-day preferences, validated proposal review, and itinerary editing.
6. Add route preview, external-map handoff, active-trip state, and arrival handling.
7. Add approved audio, read-only essentials cache, and source-grounded questions.
8. Complete accessibility, privacy, failure, native-device, and store-release verification.

Each milestone should ship as a usable vertical slice. Provider integrations require deterministic fixtures before live-provider testing.

## Test strategy

### Required automated coverage

- Navigation and state transitions.
- Validation of unknown, duplicate, or unpublished place IDs.
- Revision conflicts and idempotent replay.
- Authentication and cross-user ownership boundaries.
- Account deletion and session revocation.
- Cache revision invalidation and pending-action reconciliation.
- Provider timeout and malformed-response handling.

### Required native checks

- App launch, icon, splash, and first-run onboarding.
- GPS denied, inaccurate, stale, and foreground-return behavior.
- External map handoff and state reconciliation.
- Audio play, pause, interruption, transcript, and unavailable state.
- Process kill and active-trip restoration.
- Screen reader, text scaling, keyboard avoidance, and reduced motion.

### AI evaluation

- Freeze a held-out question and planning set before tuning.
- Record model, prompt, corpus, and configuration versions.
- Measure unknown-ID rejection, constraint validity, source support, appropriate refusal, latency, and provider failure.
- Report answerable coverage and false refusal; high refusal alone is not success.
- Never fabricate evaluation results.

## Definition of done

A change is done when:

- Behavior and failure states match its accepted scope.
- TypeScript and Expo checks pass.
- Relevant automated and native checks have evidence.
- Accessibility labels and touch targets are reviewed.
- Assets have clear ownership and do not rely on expiring URLs.
- Documentation describes actual behavior and known limitations.
- The commit is focused, reviewable, and contains no secrets or unrelated local changes.

## Current known gaps

- Onboarding actions do not yet lead to later product screens.
- No persistent onboarding state exists.
- No backend or provider integration is present.
- The Android package name remains a development placeholder.
- Native-device and accessibility evidence has not yet been collected.
