# DaNavi — Canonical UI/UX Design

Version 1.3 | 2026-10-19 | Status: canonical mobile UI contract for review. Document control and evidence status: [Index](00-INDEX.md).

## Ownership and product surface

This document is the single canonical source for DaNavi flow, screen inventory, supporting sheets/states, navigation, tokens, responsive behavior and Figma handoff. [wireframes.html](UI_UX_design/wireframes.html) is its review rendering. Root design.md and [19-App-Feature-Screens.md](19-App-Feature-Screens.md) are retired stubs retained for history; they do not own tokens, components or screen scope.

Reference mobile viewport is iPhone 393×852. P0 app copy and reviewed content are English. Vietnamese names and romanization appear only as reviewed search aliases. All examples are fixtures unless linked to approved content; screenshots/references inspire patterns and are not production UI.

## End-to-end flow

    Welcome → Home → Explore/Search or Explore Map → Place Detail
      Save → Login gate
      Ask AI → Login gate
      Plan with AI → Preferences → Generate → Login gate when needed

    Generate → AI Itinerary Result → Save & customize → Edit Itinerary
      → Route Map / Trip Ready → Active Trip → External directions
      → return and reconcile → I've arrived → Arrival & Audio / Ask AI
      → Next stop → Trip Completed

    Home · Explore · Trips · Saved are bottom destinations.
    Profile & Settings opens from the avatar, not a fifth tab.

A guest can browse Home/Explore/Map/Detail and play a bounded audio preview. Trips and Saved show a “Sign in to view” state. Save, Ask and Generate open login. Planning inputs survive login; return to the filled form and require another explicit Generate tap. Never start an AI request automatically after authentication.

## Stable screen inventory

Primary screens are full destinations or steps with distinct user goals. Sheets, confirmations, loading/error/empty/offline variants and permission explanations are supporting states, not additional primary screens.

| ID | Primary screen | Essential content/actions | Trace |
|---|---|---|---|
| UI-17 | Welcome | English value proposition, privacy/trust cue, Continue, Skip to explore | App shell; D-23/D-25 |
| UI-18 | Home | Greeting, featured reviewed places, Plan my day, nearby/curated entry points, avatar | BIZ-01/02; FR-EXP-01, FR-PREF-01 |
| UI-01 | Explore / Search | Search English/Vietnamese/romanized aliases, four category chips, cards, map switch | US-01/02; FR-POI-01, FR-EXP-01 |
| UI-02 | Explore Map | Curated pins, selected-place sheet, list fallback, provider attribution | US-04; FR-MAP-01 |
| UI-03 | Place Detail | Gallery/credit, English description, local name, facts/source date, preview audio, Save, Ask | US-01/03/05/13/14; FR-POI/PLC/SAV/TRV-03/AI |
| UI-04 | AI Trip Preferences | Date, fixed one day, required map pin/current location/preset, interests, pace, time, budget; car/ride-hailing shown read-only | US-07; FR-PREF-01 |
| UI-05 | AI Itinerary Result | Honest generation state, one-day stop proposal, uncertainty panel, Regenerate, Save & customize | US-08; FR-TRP-02 |
| UI-06 | Edit Itinerary | Accepted stops, add/remove/reorder/duration, accessible move controls, route freshness | US-08/09/10; FR-TRP-02/03/04 |
| UI-07 | Route Map / Trip Ready | Ordered pins, start leg, car route, unavailable/stale labels, cache estimate/status, Start Trip | US-04/10/11/19/20; FR-MAP/TRP-04/TRV-01/04/OFF-01 |
| UI-19 | Trips | Active/upcoming/completed cards, restore active trip, guest sign-in state | US-11/19/20; FR-TRV-01/04, FR-OFF-01 |
| UI-11 | Saved | Saved list, unsave, add to planning, guest sign-in state | US-05; FR-SAV-01 |
| UI-08 | Active Trip | Current/next stop, map preview, Open directions, I've arrived, Complete/Skip, pending-sync state | US-11/12/19/20; FR-TRV-01/02/04, FR-OFF-01 |
| UI-09 | Arrival & Audio | Current POI/method, human audio controls/transcript, cache state, Ask, next action | US-12/13/20; FR-TRV-02/03, FR-OFF-01 |
| UI-14 | Ask AI | Current context, one question, answer-level source cards, local-only history, insufficient-evidence/provider states | US-14; FR-AI-01 |
| UI-13 | Profile & Settings | Account, English language status, permissions, privacy, logout, Delete account entry | US-06/18; FR-AUTH-01/03 |

### Supporting screens, sheets and states

| ID / owner | Supporting surface | Rule |
|---|---|---|
| UI-12 | Login / Register | Return to the initiating action; no password-recovery promise in P0; keyboard-safe state |
| UI-20 | Delete Account confirmation | Explain cascade/retention, password reauthentication, exact confirmation, cancel, transaction failure |
| UI-15 | Camera Landmark Recognition (P1) | Permission, capture, candidate confirmation, unknown/ambiguous/manual fallback; outside P0 demo |
| UI-16 | Speech Input (P1) | Permission, recording, editable transcript, typing fallback; outside P0 demo |
| UI-02/UI-04/UI-08 | Location explanation | Request only on use; current-location shortcut never blocks map pin/preset |
| UI-07/UI-08/UI-09 | Cache/pending sheet | Per-item progress; partial/retry/online-only; pending is never shown as synced |
| All data screens | Loading / empty / error / offline | Recovery action and last-known/stale label where applicable; no generic toast-only failure |
| UI-14 | Insufficient evidence | No unsupported answer; show empty evidence and a useful next action |
| UI-08 | Trip completed state | Summary and return to Trips; state of UI-08, not a new primary screen |

UI-10 Audio player is **Retired 2026-10-19**, superseded by the Arrival & Audio states inside UI-09. Its ID is never reused. UI-01–09 and UI-11–16 keep their historical meanings; the v1.3 labels clarify them without assigning an old ID to a different screen.

## Navigation and interaction contracts

Bottom navigation: **Home · Explore · Trips · Saved**. Preserve each tab stack when switching. Avatar opens UI-13. Ask is contextual, not a tab. Back from an authentication gate returns to the initiating screen with safe local inputs intact.

External directions use an HTTPS Google/Apple Maps handoff to the reviewed entrance. The in-app map says “Route preview”; it never says turn-by-turn. When DaNavi returns to foreground, show a short “Updating your trip…” state, reconcile the active trip/current stop, request a fresh fix and then expose **I've arrived** as the primary action. GPS dwell is a helper, not a promise of background tracking.

Proposal stops are read-only until **Save & customize** succeeds. Edit controls appear only on the accepted itinerary. Current/completed/skipped stops remain fixed during an active trip. Route/provider failure never replaces user edits.

## Screen composition at 393×852

- Safe-area-aware top region; standard horizontal gutter 20 px, compact chrome 16 px.
- Bottom navigation reserves 82 px plus device inset. Sticky actions clear it.
- Reading/forms cap near 560 px on wide devices; maps/media can expand behind centered sheets.
- Welcome: coastal image/illustration region, short English promise, one dominant Continue action.
- Home: 56 px header/avatar, featured reviewed places, primary Plan my day card, curated sections.
- Explore: persistent 48 px search, horizontally scrollable category chips, 4:3 place cards and map switch.
- Detail: 260 px hero, opaque attribution, local-name/helper row, facts/sources before secondary actions.
- Planning: single column; start point map/preset section; validation adjacent to fields; fixed Generate footer.
- Result/Edit: stop cards and warnings; result uses Save & customize, edit uses Save changes/Trip ready.
- Route/Active: map-first upper region; accessible sheet handles; persistent current-stop and sync status.
- Ask: context chip, local display history, answer followed immediately by source cards, composer.

Compact phones 320–374 px keep at least 16 px gutters, scroll chips/carousels and stack paired actions. Reference phones 375–430 px scale the 393 px layout. Larger phones/tablets cap text/forms; no tablet split-view commitment. Components grow vertically with larger text; critical source/status/recovery copy is never truncated.

## Coastal blue-white design tokens

| Token | Value | Role |
|---|---:|---|
| color.primary | #075985 | Primary actions, active destination, focus emphasis |
| color.primaryPressed | #0C4A6E | Pressed action |
| color.primarySoft | #E0F2FE | Selected chip, info surface |
| color.coastalAccent | #0284C7 | Map/illustration accent, not body text on white |
| color.canvas | #FFFFFF | Main surface |
| color.background | #F0F9FF | Coastal page background |
| color.surfaceGrouped | #F8FAFC | Grouped controls/cards |
| color.ink | #0F172A | Headings |
| color.body | #334155 | Body text |
| color.muted | #64748B | Metadata on white only |
| color.border | #BAE6FD | Dividers/control boundary; never the sole state cue |
| color.success / successBg | #166534 / #DCFCE7 | Verified/synced/completed |
| color.warning / warningBg | #854D0E / #FEF3C7 | Pending/uncertain/simulated |
| color.error / errorBg | #B91C1C / #FEF2F2 | Invalid/provider failure |
| color.mapOverlay | #0F172A | Opaque map/status overlay with white text |

Typography: Inter with system fallback; display 28/36 700, screen title 26/34 700, section 18/26 600, body 16/24 400, button 15/22 600, helper 13/20 400, tab 11/16 600. Spacing 4/8/12/16/20/24/32/40. Radius 8/12/16/24/28/full. Interactive targets are at least 44×44 logical points.

### Contrast calculation record

Ratios below were calculated from sRGB relative luminance on 2026-10-19; they are arithmetic checks, not an accessibility certification:

| Foreground / background | Ratio |
|---|---:|
| White / primary #075985 | 7.56:1 |
| White / primaryPressed #0C4A6E | 9.46:1 |
| Ink #0F172A / white | 17.85:1 |
| Body #334155 / white | 10.35:1 |
| Muted #64748B / white | 4.76:1 |
| Primary #075985 / primarySoft #E0F2FE | 6.59:1 |
| Success / successBg | 6.49:1 |
| Warning / warningBg | 6.15:1 |
| Error / errorBg | 5.91:1 |
| White / mapOverlay #0F172A | 17.85:1 |

Native text scaling, VoiceOver/TalkBack, focus order, real map tiles, photography overlays and disabled/pressed states still require device checks.

## Components and required states

Use a small semantic set: Button, IconButton, TextField, SearchField, Chip, PlaceCard, CompactPlaceCard, StopRow, SourceCard, Notice, StatePanel, MapPin/ListFallback, BottomNavigation, BottomSheet, AudioPlayer and AskComposer. Each interactive component covers normal/pressed/focused/loading/disabled where applicable. Drag reorder has Move up/Move down alternatives.

State labels are explicit:

- loading: skeleton/progress without fabricated percentages;
- empty: what is missing and the next action;
- error: provider/network/validation distinction plus retry;
- offline: last updated/revision and unavailable actions;
- pending: local action not yet server-confirmed;
- stale: route/content revision expired;
- insufficient evidence: no factual answer;
- simulated: persistent badge in demo-only GPS/route fixtures.

Audio always says “Human-recorded guide”. Playback never requests microphone permission. Guest preview and full active-trip audio are distinguishable. Auto-play defaults off and the per-stop guard survives resume/process restart.

## Content and accessibility rules

All production copy is English. Display Da Nang time as Asia/Ho_Chi_Minh where ambiguity exists and prices in VND. Unknown hours do not mean open; unknown price does not mean free. Suggested visit duration is an estimate. Route time shows mode/fetch freshness and provider attribution. Source cards stay adjacent to the fact/answer they support.

Support text scaling, screen-reader labels, logical focus, keyboard avoidance, reduced motion and list alternatives for map gestures. Do not rely on colour alone. Permission prompts are preceded by a plain-language explanation and requested only at the action that needs them.

## Figma and engineering handoff

- Frame: 393×852; use English screen names matching the inventory.
- Keep Mood Board/reference screenshots separate from production frames; never trace or ship a reference screenshot as UI.
- The Figma screen set is a review prototype. Tokens and behavior in this document take precedence when old Figma styling conflicts with v1.3.
- Annotate guest/auth state, live/fixture/simulated data, provider attribution, offline rights and source ownership.
- Provide one canonical frame per primary screen; use variants/adjacent frames only for required states, not duplicate screens.
- Engineering maps each frame to its UI/US/FR/TC IDs and verifies 393 px plus one compact width.

## Review status and limitations

The HTML wireframes were updated as a docs review artifact. They do not prove native behavior, Figma synchronization, map/provider integration, accessibility or factual/media rights. Product review confirms copy/actions before implementation; native evidence is recorded only after real builds and tests.
