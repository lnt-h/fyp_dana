# Danang TourGuide — UI/UX Design

Version 1.0 | 2026-09-30. Vietnamese P0; English content/audio only when available. Native mobile layout, scalable text, readable contrast, blue/cyan accents and large POI photography. No photo constellation, DNA bars or match-percentage interface.

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

Wireframe specifications (layout blocks, not finished rendered mockups):
- Explore: safe-area header/title; search field; horizontal category chips; list of image/name/tags cards; fixed bottom tabs.
- Detail: image gallery; name and category; facts with source/date; description; audio availability row; sticky Add/Save; contextual Ask action.
- Planner: top progress/title; form sections; validation beside fields; Generate footer. Preview replaces form with day/stop cards and warning panel above Accept.
- Itinerary: day selector; numbered draggable stop rows, duration and route status; Add stop; map toggle; Start footer.
- Travel: current-stop header; map region; arrival sheet; recorded player; Complete/Skip buttons; next-stop preview.
- Ask: POI context chip; message history; source cards beneath answer; question box; Send; microphone only when P1 available.
Produce annotated native wireframes for the final report; this specification alone is not a Figma or rendered wireframe deliverable.

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
