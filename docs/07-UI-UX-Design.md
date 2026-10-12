# Danang TourGuide — UI/UX Design

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Navigation and screens

Tabs: Explore · Trips · Saved · Settings. Map, audio and Ask AI are contextual screens/sheets.

| Screen | Essential elements | Requirements |
|---|---|---|
| Explore | Search, category chips, POI cards, Map toggle | FR-EXP-01 |
| Explore map | Curated pins, selected POI bottom sheet | FR-MAP-01 |
| POI detail | Gallery, verified facts/source date, Save/Add to trip, audio availability, Ask | FR-PLC-01, FR-SAV-01 |
| Create trip | Date/day count, start point, interests, pace, transport, time window, budget preference | FR-PREF-01 |
| Build preview | Loading/cancel wait; candidate stops, conflicts, Accept/Regenerate | FR-TRP-02 |
| Itinerary | Day timeline, add/remove, drag reorder, duration, route freshness | FR-TRP-03 |
| Trip map | Ordered markers, selected stop, legs, unavailable-time labels | FR-TRP-04, FR-MAP-01 |
| Travel mode | Current/next stop, Start/Continue, location status, manual arrival, Complete/Skip | FR-TRV-01/02 |
| Arrival sheet | Correct POI, method label, audio action, Ask, next stop | FR-TRV-02 |
| Audio player | Human narrator label, language, play/pause/seek/progress, transcript | FR-TRV-03 |
| Ask AI | Current POI/trip context, editable question, source links, refusal/retry | FR-AI-01 |
| Saved | Simple list, unsave, add to trip | FR-SAV-01 |
| Login/settings | Email login, language, permissions, session/logout; OAuth P1 | FR-AUTH-01 |
| Camera / STT | P1 only; permission/capture/unknown and transcript confirmation | FR-CAM-01, FR-STT-01 |

## Core flow and low-fidelity layouts

Explore → POI detail/Save → Create trip → Preview → Accept → Edit → Trip map → Start Trip → Arrival → Audio/Ask → Complete/Skip → next.

Wireframe specifications (layout blocks, review layouts):
- Explore: safe-area header/title; search field; horizontal category chips; list of image/name/tags cards; fixed bottom tabs.
- Detail: image gallery; name and category; facts with source/date; description; audio availability row; sticky Add/Save; contextual Ask action.
- Planner: top progress/title; form sections; validation beside fields; Generate footer. Preview replaces form with day/stop cards and warning panel above Accept.
- Itinerary: day selector; numbered draggable stop rows, duration and route status; Add stop; map toggle; Start footer.
- Travel: current-stop header; map region; arrival sheet; recorded player; Complete/Skip buttons; next-stop preview.
- Ask: POI context chip; message history; source cards beneath answer; question box; Send; microphone only when P1 available.
The HTML gallery below supplies annotated review layouts. Native screenshots and actual behavior are captured after implementation; Figma is not an additional mandatory deliverable.

## Required states

| Flow | Loading/normal | Empty/error/fallback |
|---|---|---|
| Search | Skeleton; selectable cards | No result/clear filters; retry network |
| Planning | Progress without fabricated percentage | Invalid inputs, insufficient candidates, conflicts, timeout preserving prior itinerary |
| Edit | Saving; revised timeline | Stale route chip, missing durations, concurrent edit reload |
| GPS | Foreground permission/status | Denied/weak: manual arrival; never claim GPS arrival for manual |
| Arrival | One current-stop sheet | Simulated arrival badge; ignore duplicate reports |
| Audio | Opt-in automatic play or manual button | Missing language/asset: unavailable; retry/transcript; no Generate audio button |
| Ask | Context chip/typing state | Insufficient evidence, conflicting source, provider unavailable |
| Camera P1 | Preview/capture/confirm candidate | Denied, unknown, ambiguous, retry/manual choose |
| STT P1 | Recording → editable text | Denied mic/transcription failure → type question |

At Start Trip, show foreground-only explanation and auto-play toggle default off. When enabled, arrival initiates playback. Disable auto-play when user stops the active travel session; intentional replay remains allowed. Do not require microphone permission for prerecorded playback.

Facts: unknown hours ≠ open; unknown price ≠ free. Suggested visit durations labelled as planning estimates. Route-provider duration labelled with fetch time/mode, not live guaranteed ETA. No calibrated-looking vision percentage without validation.

## Accessibility and usability

Measure contrast, support text scaling, label pins/buttons/player controls for screen readers, maintain touch targets and avoid colour-only status. Verify TalkBack/VoiceOver on native builds; browser Lighthouse/Axe does not certify React Native accessibility. UAT tasks: find/save a POI, build itinerary, reorder/select marker, arrive/listen, ask and inspect source. Record task time/errors/help and SUS.

## Demo simulation

Simulated arrival and sample route badges must be visible throughout relevant screens and logs. Human prerecorded audio is real product content, not a simulation merely because it is prerecorded. Optional camera simulation must never be presented as live recognition.

## Stable screen IDs and reviewable layouts

| ID | Screen | Priority | Stories / FR |
|---|---|---|---|
| UI-01 | Explore | P0 | US-01 / FR-POI-01; US-02 / FR-EXP-01 |
| UI-02 | Explore map | P0 | US-04 / FR-MAP-01 |
| UI-03 | POI detail | P0 | US-01 / FR-POI-01; US-03 / FR-PLC-01; US-05 / FR-SAV-01; US-14 / FR-AI-01 |
| UI-04 | Create trip | P0 | US-07 / FR-PREF-01 |
| UI-05 | Build preview | P0 | US-08 / FR-TRP-02 |
| UI-06 | Itinerary | P0 | US-08 / FR-TRP-02; US-09 / FR-TRP-03; US-10 / FR-TRP-04 |
| UI-07 | Trip map | P0 | US-04 / FR-MAP-01; US-10 / FR-TRP-04 |
| UI-08 | Travel mode | P0 | US-11 / FR-TRV-01; US-12 / FR-TRV-02 |
| UI-09 | Arrival sheet | P0 | US-12 / FR-TRV-02; US-13 / FR-TRV-03 |
| UI-10 | Audio player | P0 | US-13 / FR-TRV-03 |
| UI-11 | Saved | P0 | US-05 / FR-SAV-01 |
| UI-12 | Login | P0 | US-06 / FR-AUTH-01; US-17 / FR-AUTH-02 |
| UI-13 | Settings | P0 | US-06 / FR-AUTH-01 |
| UI-14 | Ask AI | P0 | US-14 / FR-AI-01; US-16 / FR-STT-01 |
| UI-15 | Camera | P1 | US-15 / FR-CAM-01 |
| UI-16 | Speech input | P1 | US-16 / FR-STT-01 |

[HTML wireframe gallery](UI_UX_design/wireframes.html) and [design system](07-UI-UX-Design.md) provide annotated layouts/tokens for handoff. They use illustrative place names and maps; no real source/fact/audio or provider result is implied. Arrival design explicitly demonstrates manual mode, Ask demonstrates insufficient evidence. Buttons link between review screens; this docs artifact is not application implementation. Native accessibility and factual media review remain later evidence gates.

## Design tokens and component handoff

### Tokens

Ink #172d3c; secondary text #526779; primary #0e7490 with white label; surface #ffffff; background #edf3f6; border #ccd9e1. Warning background #fff7ed/text #78350f; success background #dcfce7/text #166534. Verify contrast numerically and on native target; diagrams/map placeholders are not content imagery.
Spacing: 4,8,12,16,24,32; default mobile content padding 20–24. Body16, helper14, title26–28, line height ≥1.4 for body; support system text scaling rather than fixed truncation. Radius8/12/16/28. Target interactive area ≥44×44 logical points; no colour-only status.

### Components and states

Button: normal/pressed/focused/loading/disabled; keep action label meaningful and prevent duplicate requests while awaiting response. Text input: default/focused/invalid/disabled; label persists, error adjacent and screen-reader announced. Card: image alt/name/tags/action; no false price/rating. Stop row: numbered label/duration/route freshness; drag plus accessible up/down alternative. Warning: description/action, never dismiss critical constraint invisibly. Source card: title/date/open source, external document reference displayed if no URL. Audio: play/pause/seek/transcript/unavailable/retry; human narration label. Arrival: current POI/method/pending/synced/duplicate guard. Map: pins with labels and list fallback. Ask: context/answer/supporting source/refusal/provider failure.

### Navigation, responsiveness and permissions

Tabs Explore/Trips/Saved/Settings; contextual Map/Audio/Ask. Minimum design phone viewport320; larger phones use flexible width. Tablet/desktop product support is not committed; HTML gallery is a review surface. Native screen reader focus goes to arrival/error heading without trapping other controls. Start Trip shows foreground-only GPS explanation and audio opt-in default off. Playing a recording never requests microphone access. P1 permissions requested on use with typing/manual fallback.

### Wireframe limitations

[wireframes.html](UI_UX_design/wireframes.html) includes 16 inspectable annotated layouts. It illustrates flow, not live GPS/maps/auth/playback. Missing verified data is deliberately unknown. P0 native VoiceOver/TalkBack/scaling checks remain TC-28; HTML review does not certify mobile accessibility. Final imagery/icons and Figma library are not required for this docs draft; later assets must preserve licensing/alt text.

### Asset and handoff checklist

Use versioned approved POI media, SVG icons with text where ambiguous, explicit loading/empty/error/permission-denied states. Engineering maps every screen to story/FR table in 11-User-Stories.md. Measurements/tokens live here; wireframes show hierarchy. Product review confirms copy/actions before implementation. Reviewer names and sign-off TBD.

## Contract-specific interaction rules

After acceptance, preferences are read-only; changing dates/start/day count requires a new draft without modifying the old trip. During travel, current/visited rows cannot be moved/removed; accessible move controls apply only to upcoming rows. An empty day, known closed visit or time-window overrun shows a blocking warning and disables Start; an uncertainty warning requires acknowledgement and is never represented as guaranteed feasibility.
Search/text fallback shows requested and actual content language. English audio unavailable does not silently play Vietnamese. P0 Ask is Vietnamese; unsupported English coverage is disclosed. Map/route screen preserves provider attribution/warnings where required; route estimates expired by policy show stale/null.
A late replay response does not replace newer displayed progression; reconcile GET. Pending arrival and URL expiration have distinct UI states. Local auto-play guard survives resume/retry; an interrupted automatic attempt exposes manual retry. Optional P1 layouts are backlog illustrations, not required P0 screens.

## Token contrast check

Calculated from specified sRGB values: ink on white14.22:1; secondary text on background5.25:1; white on primary5.36:1; warning text on warning background8.54:1; success text on success background6.49:1. These pairs exceed the 4.5:1 normal-text target described in [WCAG2.1 contrast guidance](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html). This is a numerical token check, not native/browser accessibility certification. Disabled controls and decorative borders need separate contextual review; do not rely on the low-contrast decorative border to identify an interactive control.
