# Gonarra Development

## Local setup

Requirements:

- Node.js and npm.
- Android Studio for an Android emulator.
- Xcode for an iOS simulator on macOS.

```bash
cd apps/mobile
npm ci
# Restore development keys for the existing linked Clerk application:
npx -y clerk@latest auth login
npx -y clerk@latest env pull
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
npm run typecheck
npm run check:dependencies
npx expo-doctor
npx expo export --platform web
```

The app uses React Native with Expo and Expo Router. Keep dependencies aligned
with the installed Expo SDK using `npx expo install --fix`, then rerun the checks
above. Commit both `package.json` and `package-lock.json` after dependency changes.
The `android` and `ios` scripts generate native projects when needed; those
directories are not required for the Expo Go workflow. A successful export does
not replace testing a native build on Android and iOS.

For UI work, also verify:

- A compact phone width and the 440 × 956 reference viewport.
- Android and iOS safe areas.
- Large text, screen-reader labels, focus order, and 44-point touch targets.
- Loading, empty, error, offline, pending, stale, and denied-permission states in scope.
- No temporary Figma URLs or remote expiring assets.

## Clerk authentication

The Expo app uses `@clerk/expo` with the existing application
`app_3LMZTjYuwkyRVTf4y9g9aE5cTuB`. Do not run accountless initialization or
create a replacement application. The CLI writes development keys to
`apps/mobile/.env.local`, which is ignored by Git. Only
`EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` is referenced by client code; never prefix
`CLERK_SECRET_KEY` with `EXPO_PUBLIC_` or import it in the app.

The integration preserves the custom React Native UI and supports Expo Go:

- Email/password registration with email-code verification and resend.
- Password sign-in, new-device email verification, TOTP when requested by Clerk,
  and email-code password recovery.
- Google/Apple browser SSO, with cancellation and failure handling.
- Secure native session caching through Clerk's `tokenCache` and Expo SecureStore.
- Signed-in profile names and travel preferences saved through Clerk. Preferences
  use `unsafeMetadata` only for personalization, never authorization.
- Guest discovery remains available. Guest preferences are session-only.
- Sign-out clears local state; editing an account profile requires a signed-in session.

On 2026-10-29 the development instance's Native API was verified enabled.
Google and Apple were already enabled. Email/password and email verification
were enabled to match the app forms; the existing 15-character password policy
was preserved. The `gonarra://sso-callback` redirect was registered for native
builds. Expo Go uses an Expo callback URL, which must also be allowed if Clerk
requests it on the test device. Production settings were not changed.

Account deletion and email changes are not implemented. Required session tasks
are blocked with an explanation and a sign-out action; they must not grant access
to the rest of the app. Additional MFA factors and social accounts with missing
required fields report unsupported states rather than proceeding as signed in.
Legal documents remain unpublished; this is a development setup, not a public
release.

Verification: TypeScript, Expo dependency checks, Expo Doctor (20/20), Clerk
Doctor, and Android/iOS/web bundle export pass. The web Welcome/login/register
screens render and empty form submissions show validation errors. Expo Go was
launched on the iPhone 18 Pro simulator; the Welcome layout and empty login
validation were visually verified. A real account
sign-up/sign-in, social round trip, sign-out, and session persistence after restart
still require user/device verification. No test users were created by the agent.

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

- Discovery and tab navigation still contain placeholder behavior.
- No persistent onboarding state exists.
- Clerk is integrated; the travel backend and other provider integrations are pending.
- The Android package name remains a development placeholder.
- Native-device and accessibility evidence has not yet been collected.
