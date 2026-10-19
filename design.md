---
version: "1.3.0"
name: "DaNavi"
status: "canonical"
description: "English-first coastal mobile guide for first-time international visitors to Da Nang."
reference_viewport: "393x852"
figma: "https://www.figma.com/design/JvXw7rVf5KxoA6LlDJEqAt/Tourguide-app-UI"
---

# DaNavi Design System

This file is the visual contract for the DaNavi mobile app. Its structure follows the nine-part DESIGN.md format documented by [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md). It is written for designers, developers and coding agents working in this repository.

Use sources in this order:

1. **design.md** — visual language, tokens, components and layout rules.
2. **docs/07-UI-UX-Design.md** — product flow, screen inventory, behavior and required states.
3. **Figma** — visual review and asset handoff. Existing frames are prototypes and must follow the two documents above when they conflict.

The product is English-first. Vietnamese place names may appear as reviewed local-name metadata, never as untranslated interface copy.

## 1. Visual Theme & Atmosphere

DaNavi should feel coastal, calm and trustworthy rather than like a crowded booking marketplace. The interface helps a visitor understand where to go, why a recommendation is credible and what to do next.

- **Coastal minimalism:** white canvas, pale sky-blue surfaces and deep ocean-blue actions.
- **Premium restraint:** one dominant action per region, generous spacing and few decorative effects.
- **Destination-led imagery:** licensed Da Nang photography provides emotion; opaque labels preserve readability and attribution.
- **Map clarity:** route previews use strong contrast, numbered stops and readable sheets instead of decorative map chrome.
- **Visible trust:** sources, freshness, offline status, uncertainty and human-recorded audio are named directly.
- **Mobile-native hierarchy:** thumb-reachable actions, safe-area spacing, bottom sheets and 44-point targets.

| Product mode | Visual behavior |
|---|---|
| Welcome and Home | Large coastal image or illustration, short promise, one clear next action |
| Explore | Search-first, editorial place cards, four simple category filters |
| Planning | Structured form and itinerary rows; uncertainty stays visible |
| On trip | Map-first canvas, current-stop sheet and persistent status |
| Ask AI | Quiet reading surface with sources directly below the answer |
| Profile and privacy | Plain grouped rows, minimal imagery and explicit destructive actions |

Avoid glassmorphism, neon gradients, dense dashboards, travel-poster decoration, ornamental AI effects and competing primary buttons.

## 2. Color Palette & Roles

### Brand and action

| Token | Value | Role |
|---|---:|---|
| color.primary | #075985 | Primary actions, active navigation and focus emphasis |
| color.primaryPressed | #0C4A6E | Pressed primary action |
| color.primarySoft | #E0F2FE | Selected chips and informational emphasis |
| color.coastalAccent | #0284C7 | Illustration and map accent; not body text on white |
| color.onPrimary | #FFFFFF | Text and icons on primary surfaces |

Use one primary-blue call to action per section. Blue may also identify selection or focus, but should not turn every card into an action.

### Surfaces and text

| Token | Value | Role |
|---|---:|---|
| color.canvas | #FFFFFF | Main screen and card surface |
| color.background | #F0F9FF | Coastal background wash |
| color.surfaceGrouped | #F8FAFC | Grouped controls and secondary cards |
| color.ink | #0F172A | Headings and highest-emphasis text |
| color.body | #334155 | Body copy |
| color.muted | #64748B | Metadata on white |
| color.border | #BAE6FD | Dividers and control boundaries |
| color.mapOverlay | #0F172A | Opaque map labels and overlays |

### Semantic colors

| Token | Foreground / background | Role |
|---|---:|---|
| success | #166534 / #DCFCE7 | Synced, verified and completed |
| warning | #854D0E / #FEF3C7 | Pending, uncertain and simulated |
| error | #B91C1C / #FEF2F2 | Invalid input and provider failure |
| info | #075985 / #E0F2FE | Explanations and non-blocking notices |

Never communicate state with color alone. Pair every semantic color with text and, where useful, an icon. White on primary is 7.56:1; ink, body and muted on white are 17.85:1, 10.35:1 and 4.76:1 respectively.

## 3. Typography Rules

Use Inter with the platform system font as fallback. Use sentence case throughout the interface.

| Style | Specification | Typical use |
|---|---|---|
| Display | 28/36, 700 | Welcome promise and Home hero |
| Screen title | 26/34, 700 | Full-screen destinations |
| Sheet title | 21/30, 600 | Map and arrival sheets |
| Section title | 18/26, 600 | Content groups |
| Card title | 17/24, 600 | Place and itinerary cards |
| Body | 16/24, 400 | Main reading text |
| Body strong | 16/24, 600 | Emphasis and compact actions |
| Button | 15/22, 600 | Buttons |
| Label | 14/20, 500 | Fields, chips and badges |
| Helper | 13/20, 400 | Validation, sources and status |
| Caption | 12/18, 400 | Attribution and timestamps |
| Tab | 11/16, 600 | Bottom navigation |

Do not shrink critical content to reproduce a screenshot. Text and containers grow vertically with the user's font scale. Avoid all caps except short map or status labels where accessibility remains intact.

## 4. Component Stylings

Build a small semantic component set and reuse it across features. Component names describe purpose, not appearance.

### Buttons and icon controls

- **Button:** 48-point minimum height, full or 16-point radius, 20-point horizontal padding.
- Primary uses color.primary; pressed uses color.primaryPressed; disabled uses a neutral surface and readable muted text.
- Secondary uses a white surface, visible border and primary text.
- Destructive uses the error foreground/background pair and appears only in a confirmation flow.
- **IconButton:** minimum 44×44 points with an accessible name.
- Enabled controls may scale to 0.98 for 120 ms; disabled controls do not animate.

### Search, fields and chips

- **SearchField:** 48 points high, grouped surface, 16-point radius and persistent accessible label.
- **TextField:** minimum 52 points high with label above and validation directly below.
- Focus uses a 2-point primary ring without shifting layout.
- **Chip:** minimum 44 points high; selected state uses primarySoft, primary text and a visible boundary.
- Chip rows scroll horizontally rather than compressing or truncating labels.

### Cards, lists and trust surfaces

- **PlaceCard:** 4:3 image, 16–24-point radius, opaque attribution and no text directly on busy photography.
- **CompactPlaceCard:** place identity and essential metadata for Saved and itinerary contexts.
- **StopRow:** order, place, visit duration, route freshness and state; reorder also offers Move up/Move down actions.
- **SourceCard:** sits directly below the fact or answer it supports.
- **Notice:** info, warning or error surface kept in reading flow.
- **StatePanel:** explicit loading, empty, error and offline recovery pattern.

### Navigation, maps and audio

- **BottomNavigation:** four destinations—Home, Explore, Trips and Saved. Profile opens from the avatar.
- **BottomSheet:** 28-point top radii, clear drag handle and content that remains operable without dragging.
- **MapPin:** numbered for itinerary order; selection is shown by shape/label as well as color.
- **AudioPlayer:** always labels narration as human-recorded; play, pause, seek, transcript, cache and unavailable states are explicit.
- **AskComposer:** one-question input with current place/trip context and a visible insufficient-evidence state.

Use one outlined icon family through a project adapter once the library is selected. Do not mix icon families, emoji and platform-specific glyphs in the same interface.

## 5. Layout Principles

The reference viewport is 393×852 points. It is a reference, not a fixed canvas.

- Spacing scale: 4, 8, 12, 16, 20, 24, 32 and 40.
- Standard horizontal gutter: 20 points; compact chrome may use 16.
- Corner radii: 8 for small labels, 12 for controls, 16 for cards, 24 for feature cards, 28 for sheets and full pill where appropriate.
- Bottom navigation reserves 82 points plus the device safe-area inset.
- Forms are single-column. Validation remains adjacent to the field.
- Maps and media can fill width; reading and form content caps near 560 points on wider devices.
- Keep at least 8 points between adjacent touch targets and make every target at least 44×44 points.

### Screen composition

- Welcome: coastal visual, one-sentence value proposition, trust cue and Continue/Skip actions.
- Home: compact header/avatar, featured reviewed places, Plan my day and curated entry points.
- Explore: persistent search, four category chips, place cards and map switch.
- Place Detail: 260-point hero, attribution, local name, reviewed facts, sources, audio preview, Save and Ask.
- AI Plan: start point, one-day preferences and a fixed Generate action; inputs survive login.
- Result/Edit: proposed stops and uncertainty first; editing begins only after Save & customize.
- Route/Active Trip: map-first upper region with an accessible sheet and persistent current-stop/sync state.
- Arrival & Audio: arrival method, human narration, transcript, cache status, Ask and next action.
- Ask AI: context, answer, adjacent sources and composer; no decorative chatbot avatar is required.

## 6. Depth & Elevation

Depth explains hierarchy; it is not decoration.

| Level | Shadow | Use |
|---|---|---|
| Flat | none | Backgrounds, rows and grouped controls |
| Card | 0 8px 24px rgba(15,23,42,.06) | Image-led place cards |
| Floating | 0 4px 16px rgba(15,23,42,.12) | Map controls and floating actions |
| Sheet | 0 -8px 28px rgba(15,23,42,.10) | Bottom sheets over maps |

Do not combine a strong shadow, strong border and tinted background on the same element. Use opaque map overlays so text contrast does not depend on map tiles.

Motion uses 120 ms for press feedback and about 200 ms for standard transitions with cubic-bezier(0.2, 0, 0, 1). Respect reduced-motion settings. Avoid looping decorative animation and fabricated loading percentages.

## 7. Do's and Don'ts

### Do

- Use the tokens and semantic components in this file.
- Keep all app copy in clear, concise English.
- Preserve source, attribution, freshness, uncertainty, fixture and offline labels.
- Treat Ask AI, route estimates and GPS arrival as fallible states with recovery actions.
- Keep external directions visually distinct from the in-app route preview.
- Use licensed local assets and record their source, author, licence and production rights.
- Verify compact width, larger text, keyboard, focus order, screen reader and reduced motion.

### Don't

- Do not restore the retired lavender/Vietnamese interface.
- Do not trace or ship moodboard/reference screenshots as production UI.
- Do not invent opening hours, prices, route durations, citations or accessibility facts.
- Do not imply turn-by-turn navigation or background GPS.
- Do not label audio as AI-generated or request microphone permission for playback.
- Do not hide provider failure behind an empty state.
- Do not add a fifth bottom-navigation tab for Ask or Profile.
- Do not create a one-off component when an existing semantic component fits.

## 8. Responsive Behavior

### Compact phones: 320–374 points

- Preserve at least 16-point gutters.
- Let chips and horizontal cards scroll.
- Stack paired actions when labels would become cramped.
- Keep map controls and sheets inside safe areas.

### Reference phones: 375–430 points

- Follow the 393-point composition proportionally.
- Keep primary actions thumb reachable and maintain image ratios.

### Large phones and tablets: 431 points and above

- Cap forms and reading content near 560 points.
- Maps and media may expand while sheets remain centered.
- Do not introduce a tablet split view until it has its own reviewed requirement.

### Accessibility adaptation

- Allow cards, controls and sheets to grow vertically.
- Never truncate source, status, error or recovery copy.
- Keep focused inputs above the keyboard.
- Provide list alternatives for map-only interaction.
- Disable entrance, stagger and scale effects when reduced motion is enabled.

## 9. Agent Prompt Guide

### Workflow

1. Read design.md for visual rules and docs/07-UI-UX-Design.md for behavior and screen IDs.
2. Identify the exact UI, user story, functional requirement and required states.
3. Inspect existing repository components and tokens before creating anything new.
4. Implement with semantic components and real local assets; do not copy a screenshot.
5. Verify the 393×852 reference, one compact width and larger text.

### Quick reference

~~~text
Canvas:          #FFFFFF
Background:      #F0F9FF
Primary:         #075985
Primary pressed: #0C4A6E
Primary soft:    #E0F2FE
Accent:          #0284C7
Ink:             #0F172A
Body:            #334155
Muted:           #64748B
Border:          #BAE6FD
Font:            Inter + system fallback
Gutters:         20 standard, 16 compact
Radii:           8 / 12 / 16 / 24 / 28 / full
Targets:         44×44 minimum
Navigation:      Home / Explore / Trips / Saved
~~~

### Implementation prompt

~~~text
Implement [screen ID and name] for DaNavi using design.md and
docs/07-UI-UX-Design.md. Reuse semantic tokens and existing components.
Keep app copy in English and cover every required loading, empty, error,
offline, pending, stale and insufficient-evidence state in scope. Preserve
source, attribution, rights and simulation labels. Verify 393×852, a compact
phone, larger text, keyboard avoidance, focus order and 44-point targets.
~~~

### Review prompt

~~~text
Review [screen or component] against design.md and docs/07-UI-UX-Design.md.
Report mismatches in this order: behavior/state, trust labels, component reuse,
layout, typography, color, imagery/attribution, interaction and accessibility.
Do not claim a native or provider test unless it was actually executed.
~~~

### Definition of done

- Uses repository tokens and semantic components instead of isolated lookalikes.
- Matches the English-first coastal blue–white direction.
- Covers all in-scope states and recovery actions.
- Contains no temporary Figma URLs, reference screenshots or invented facts.
- Preserves safe areas, keyboard behavior, accessibility labels and touch targets.
- Has been checked at 393×852, one compact width and larger text.

Update this file whenever a visual token, component contract or cross-screen visual rule changes. Update docs/07-UI-UX-Design.md only when product flow, behavior, screen ownership or required states change.
