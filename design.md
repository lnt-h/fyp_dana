---
version: "3.0.0"
name: DaNavi
status: canonical
description: "Vietnamese-first mobile travel companion for Da Nang: calm white surfaces, restrained lavender actions, sourced photography, map-first guidance, and explicit trust states."
figma:
  file: "https://www.figma.com/design/JvXw7rVf5KxoA6LlDJEqAt/Untitled"
  foundations: "9:3"
  components: "4:4"
  screens: "4:5"
  reference-viewport: "393x852"
colors:
  primary: "#7058C9"
  primary-pressed: "#5D46B7"
  primary-soft: "#F1EDFC"
  primary-soft-pressed: "#E7DFF8"
  on-primary: "#FFFFFF"
  canvas: "#FFFFFF"
  surface-grouped: "#F7F7FA"
  surface-input: "#FAFAFD"
  surface-card: "#FFFFFF"
  ink: "#20242C"
  body: "#535C69"
  muted: "#646B78"
  disabled-ink: "#858B97"
  disabled-bg: "#EEEDF3"
  border: "#E8EBF0"
  border-control: "#DADDE7"
  border-strong: "#848D9E"
  border-selected: "#DED4F3"
  focus: "#7058C9"
  media: "#222633"
  on-media: "#FFFFFF"
  success: "#2C7046"
  success-bg: "#EDF7EF"
  warning: "#7A4D12"
  warning-bg: "#FFF7E7"
  error: "#B42318"
  error-bg: "#FEF3F2"
  info: "#5D46B7"
  info-bg: "#F1EDFC"
  route: "#F36863"
  route-halo: "#FFFFFF"
  user-location: "#1685FF"
typography:
  family: "Inter, system-ui, -apple-system, sans-serif"
  display: "28px/36px 700, -0.8px"
  screen-title: "26px/36px 600, -0.65px"
  sheet-title: "21px/30px 600, -0.45px"
  section-title: "18px/26px 600, -0.3px"
  navigation-title: "16px/24px 600, -0.2px"
  card-title: "17px/24px 600, -0.2px"
  body: "16px/24px 400"
  body-strong: "16px/24px 600"
  input: "15px/22px 400"
  button: "15px/22px 600, -0.1px"
  label: "14px/20px 500"
  helper: "13px/20px 400"
  caption: "12px/18px 400"
  tab-label: "11px/16px 500"
spacing: [4px, 8px, 12px, 16px, 20px, 22px, 24px, 32px, 40px]
radii:
  tag: 8px
  field: 16px
  card: 24px
  sheet: 28px
  full: 9999px
elevation:
  card: "0 10px 30px rgba(40, 36, 63, 0.06)"
  floating: "0 3px 15px rgba(40, 36, 53, 0.11)"
  sheet: "0 -6px 28px rgba(35, 32, 52, 0.07)"
  microphone: "0 8px 25px rgba(112, 88, 201, 0.18)"
motion:
  press: "scale(0.98), 120ms"
  standard: 200ms
  stagger: 40ms
  enter-rise: 8px
  easing: "cubic-bezier(0.2, 0, 0, 1)"
---

# DaNavi Design System

This is DaNavi's visual contract. It follows the nine-section format used by [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md); all product-specific values come from the DaNavi Figma file and this repository.

Resolve conflicts in this order:

1. This `design.md` for tokens, components, visual layout, and presentation.
2. [UI/UX Design](docs/07-UI-UX-Design.md) for behavior, accessibility, permissions, and required states.
3. [App Feature Screens](docs/19-App-Feature-Screens.md) for feature scope and screen inventory.
4. Figma for visual inspection and geometry.

The Figma file is a review prototype. Labels such as `Fixture`, `Mô phỏng`, and `Chưa xác minh` remain visible whenever content is simulated or unverified.

## 1. Visual Theme & Atmosphere

DaNavi is calm, useful, and locally grounded. It helps a visitor decide where to go, understand why information is credible, and continue a trip without visual noise.

- **White-first canvas:** white is the working surface; pale grouped surfaces separate controls.
- **Lavender hierarchy:** purple marks primary actions, focus, selection, and active navigation.
- **Destination photography:** real imagery carries emotion and context; every photo has readable attribution.
- **Large soft geometry:** cards and sheets use generous radii; controls use pills or circles.
- **Visible trust:** sources, offline mode, provider failure, insufficient evidence, simulation, and human-recorded audio are stated directly.

| Mode | Visual behavior |
|---|---|
| Discovery | Editorial photography, featured carousel, search, filters, generous white space |
| Planning | Structured cards, compact facts, itinerary rows, clear actions |
| On trip | Map-first canvas, floating controls, route colors, bottom sheets |
| Ask AI | Quiet chat, current-place context, sources beside claims, explicit evidence/failure states |
| Account/settings | Plain grouped lists, minimal imagery, high legibility |

Avoid travel-poster decoration, glassmorphism, excessive gradients, neon effects, and dense dashboard styling.

## 2. Color Palette & Roles

### Brand and action

| Token | Value | Role |
|---|---:|---|
| `primary` | `#7058C9` | Primary actions, active navigation, focus, selected emphasis |
| `primary-pressed` | `#5D46B7` | Pressed primary control |
| `primary-soft` | `#F1EDFC` | Selected chips, info backgrounds, soft emphasis |
| `primary-soft-pressed` | `#E7DFF8` | Pressed tonal control |
| `on-primary` | `#FFFFFF` | Text and icons on primary |

Use one dominant purple action per region. Purple state indicators may coexist, but should not compete as simultaneous primary calls to action.

### Surfaces and text

| Token | Value | Role |
|---|---:|---|
| `canvas` / `surface-card` | `#FFFFFF` | Screen and card surface |
| `surface-grouped` | `#F7F7FA` | Search and grouped blocks |
| `surface-input` | `#FAFAFD` | Text fields |
| `ink` | `#20242C` | Titles and highest-emphasis content |
| `body` | `#535C69` | Body copy and inactive navigation |
| `muted` | `#646B78` | Metadata and helper text |
| `border` | `#E8EBF0` | Subtle separation |
| `border-control` | `#DADDE7` | Default control border |
| `border-strong` | `#848D9E` | Text input boundary |
| `border-selected` | `#DED4F3` | Selected chip boundary |

### Semantic and map colors

| Token | Value | Role |
|---|---:|---|
| `success` | `#2C7046` | Completed, available, verified-positive |
| `warning` | `#7A4D12` | Limited, pending, simulated, caution |
| `error` | `#B42318` | Invalid field or provider failure |
| `info` | `#5D46B7` | Informational status |
| `route` | `#F36863` | Route and trip progression |
| `user-location` | `#1685FF` | Current user position only |

Color never carries state alone. Pair it with a label or icon. Map routes use a white halo over varied tiles.

## 3. Typography Rules

Use Inter throughout; system fallbacks are allowed while it loads.

| Style | Specification | Typical use |
|---|---|---|
| Display | 28/36, Bold, -0.8px | Explore hero |
| Screen title | 26/36, Semibold, -0.65px | Saved, Settings |
| Sheet title | 21/30, Semibold, -0.45px | Arrival/audio sheet |
| Section title | 18/26, Semibold, -0.3px | Featured places, facts, sources |
| Navigation title | 16/24, Semibold | Compact app bar |
| Card title | 17/24, Semibold | Place and itinerary cards |
| Body | 16/24, Regular | Reading text |
| Body strong | 16/24, Semibold | Emphasized content |
| Input | 15/22, Regular | Search and fields |
| Button | 15/22, Semibold, -0.1px | Actions |
| Label | 14/20, Medium | Chips, labels, badges |
| Helper | 13/20, Regular | Assistance and status |
| Caption | 12/18, Regular | Counts, metadata, attribution |
| Tab label | 11/16, Medium | Bottom navigation |

Use Vietnamese sentence case. Do not place critical content below 12px or shrink text to match a screenshot.

## 4. Component Stylings

Figma components live on page `01 Components` (`4:4`). Reuse variants rather than building one-off controls.

### 4.1 Icons and imagery

- Use **Phosphor** outline icons through the project icon adapter; source group: `10:2`.
- Standard glyphs are 24px inside a minimum 44×44px target.
- Do not mix Iconly, SF Symbols, emoji, or hand-drawn substitutes.
- Decorative icons have empty accessibility labels; action icons require accessible names.
- Photography uses `object-fit: cover` and the Figma crop.
- Photo category and attribution text always has an opaque or near-opaque backing.
- Never ship temporary `figma.com/api/mcp/asset/...` URLs. Store licensed assets locally and preserve attribution.

### 4.2 Buttons and icon controls

**Button** (`10:108`) is a 48px pill with 20px horizontal padding and 15/22 Semibold text.

| Variant | Surface | Text | Use |
|---|---|---|---|
| Primary | `primary` | `on-primary` | Main action |
| Primary pressed | `primary-pressed` | `on-primary` | Touch down |
| Primary disabled | `disabled-bg` | `disabled-ink` | Unavailable |
| Secondary | `canvas` + `border-control` | `primary` | Alternative |
| Tonal | `primary-soft` | `primary` | Lower emphasis |
| Text | transparent | `primary` | Tertiary |
| Danger | `error-bg` | `error` | Destructive |

Enabled buttons press to 0.98 for 120ms. Disabled controls do not animate.

**IconButton** (`10:121`) is circular and 44px; pressed uses `primary-soft`. **FilterButton** is 48px and uses `primary-soft` when active.

### 4.3 Search, inputs, and chips

- **SearchField** (`10:138`): 48px, `surface-grouped`, 16px radius, borderless by default, 12px padding. Focus adds a 2px ring without layout shift. Always provide a label.
- **TextInput** (`10:150`): 52px, `surface-input`, 16px radius, 16px padding. Default uses `border-strong`, focus uses a 2px `focus` border, error uses `error` plus adjacent validation text.
- **Chip** (`10:143`): 44px full pill, 16px horizontal padding. Selected uses `primary-soft`, `border-selected`, and primary text.

Placeholder text is not a field label. Chip rows scroll horizontally instead of shrinking labels.

### 4.4 Cards, carousel, and trust overlays

- **PlaceCard:** 349px reference width, 4:3 media, 24px radius, white surface, card elevation.
- **FeaturedCarousel** (`21:237`): one 317.6px card in a 349px viewport so the next card peeks in. Manual swipe and accessible previous/next controls; never auto-rotate.
- **CompactPlaceCard** (`21:158`): 84px high for itinerary and saved lists.
- **PhotoChip** and **PhotoAttribution:** standard category and source overlays.
- **SourceCard** (`21:143`): stays adjacent to the fact or answer it supports.
- **SkeletonCard:** matches final geometry to avoid layout shift.
- **StatePanel:** fixed Empty, Error, and Offline patterns with a message and recovery action.

### 4.5 Navigation and settings

- **BottomNavigation** (`10:220`): 393×82px at reference size, four equal destinations—Khám phá, Chuyến đi, Đã lưu, Cài đặt. Active icon and label use `primary`.
- **FloatingCta** (`10:202`): 164×48px purple pill above navigation and the safe-area inset.
- **SettingsRow** (`10:209`): 64px with label, optional value, and a 44px trailing target.

Ask AI is contextual; do not add it as a fifth bottom-navigation destination.

### 4.6 Planning and on-trip components

- **Badge:** Info, Warning, Success, Error; text remains visible.
- **Notice:** Info, Warning, Error for explanations kept in reading flow.
- **StopRow** (`21:168`): 92px; shows order, place, timing, and state.
- **MapCanvas** (`21:178`): map base with floating chrome and overlapping sheets.
- **BottomSheet** (`21:190`): 28px top radii, 44×4px handle, sheet shadow, 22px content gutter.
- **AudioPlayer** (`21:197`): human-recorded narration; never label it AI speech.
- **ChatBubble** (`21:207`): preserves speakers and supports source cards.

### 4.7 Required states

Every data-backed surface handles loading, loaded, empty, provider failure, and offline where relevant. Do not collapse these into a generic toast.

| Flow | Figma frames |
|---|---|
| Explore states | Loaded, Loading, Empty, Provider failure, Offline |
| Discovery/planning | Explore map, POI detail, Create trip, Generating, Build preview, Itinerary |
| On trip | Trip map, Travel mode, Arrival sheet, Audio player |
| Saved/account | Saved, Saved empty, Login default, Login keyboard open |
| Settings/AI | Settings, Ask AI initial, Insufficient evidence, Provider failure |

## 5. Layout Principles

The product viewport is 393×852px in Figma. The outer 393×884px review frame includes a 32px screen label that must not appear in the app.

### Mobile grid

- Standard content gutter: 22px.
- Dense top controls and bottom navigation may use 16px gutters.
- At 393px, content is typically 349px with 22px gutters or 361px with 16px gutters.
- Use the 4, 8, 12, 16, 20, 22, 24, 32, 40px spacing scale.
- Use 24–32px between major sections.
- Keep 44px targets and at least 8px between adjacent actions.

### Screen composition

- Explore begins with a 260px `primary-soft`-to-white wash; search at y=144, filters at y=204, content at y=270.
- Image-led detail screens may use a 260px hero followed by white content.
- Map screens fill the upper region. Sheets overlap the map instead of reducing it to a small card.
- Forms are single-column; labels sit above fields and validation sits immediately below.
- Bottom navigation is pinned to the safe bottom. Floating actions clear navigation and the home indicator.

Prioritize one decision per viewport. Use progressive disclosure for detail while keeping trust-critical labels visible. Allow scrolling when content grows.

## 6. Depth & Elevation

Shadow clarifies physical layering:

| Level | Token | Use |
|---|---|---|
| Flat | none | Backgrounds, grouped controls, most rows |
| Card | `0 10px 30px rgba(40,36,63,.06)` | Photography cards |
| Floating | `0 3px 15px rgba(40,36,53,.11)` | Floating CTA and controls |
| Sheet | `0 -6px 28px rgba(35,32,52,.07)` | Bottom sheets over maps |
| Microphone | `0 8px 25px rgba(112,88,201,.18)` | Voice capture only |

Do not stack a strong border, strong shadow, and tint unless a defined component requires them. The only default atmospheric gradient is the Explore header wash; buttons and semantic states are flat colors.

## 7. Do's and Don'ts

### Do

- Use semantic tokens and Figma component variants.
- Keep Vietnamese copy concise and in sentence case.
- Show sources, photo credit, verification/simulation state, and recovery actions.
- Keep Ask AI separate from human narration.
- Preserve safe areas, keyboard avoidance, dynamic text, and 44px targets.
- Use local licensed assets and record attribution.
- Validate loading, empty, failure, offline, and insufficient-evidence states.

### Don't

- Do not use Iconly; the current system uses Phosphor.
- Do not invent place facts, hours, sources, accessibility claims, or audio provenance.
- Do not hide provider failure behind an empty state.
- Do not present simulated GPS, maps, or AI output as live or verified.
- Do not use purple for every card or decorative shape.
- Do not auto-rotate the carousel.
- Do not place text directly on busy photography.
- Do not use temporary Figma asset URLs.
- Do not reproduce Figma's outer screen label inside the app.

## 8. Responsive Behavior

DaNavi is mobile-first. The 393px Figma width is a reference, not a fixed implementation width.

### Compact phones: 320–374px

- Preserve at least 16px outer gutters.
- Let chips and carousels scroll horizontally.
- Stack paired actions if labels would become cramped.
- Keep map controls and sheet content within safe areas.

### Reference phones: 375–430px

- Follow 393px geometry proportionally.
- Keep 349px blocks centered with 22px gutters at 393px.
- Preserve the next-card peek in the featured carousel.

### Large phones and tablets: 431px+

- Cap forms and reading content around 560px.
- Maps and media may expand while sheets and forms stay centered.
- A tablet split view is allowed only if it preserves hierarchy and states.

### Accessibility adaptation

- Let cards, rows, buttons, and sheets grow vertically with larger text.
- Never truncate critical status, source, or recovery copy.
- Keep focused controls above the keyboard; use `Login / Keyboard open` as reference.
- Disable entrance, stagger, press-scale, and photo fade under reduced motion.

## 9. Agent Prompt Guide

### Workflow

1. Read this file and the relevant behavior in [UI/UX Design](docs/07-UI-UX-Design.md).
2. Find the screen on Figma page `02 Screens` and reusable parts on `01 Components`.
3. Confirm data states, permissions, and trust labels.
4. Reuse repo tokens, Phosphor adapter, components, and local assets.
5. Compare at 393px, then test a compact width and larger text.

### Quick reference

```text
Canvas:          #FFFFFF
Primary:         #7058C9
Primary soft:    #F1EDFC
Ink:             #20242C
Body:            #535C69
Grouped surface: #F7F7FA
Border:          #E8EBF0
Font:            Inter
Gutters:         22px standard, 16px dense chrome
Radii:           8 tag, 16 field, 24 card, 28 sheet, full pill
Targets:         44px minimum
Icons:           Phosphor outline
```

### Implementation prompt

```text
Implement [Figma screen name/node] using design.md and docs/07-UI-UX-Design.md.
Reuse existing tokens, the Phosphor adapter, components, and local assets.
Cover every required loaded/loading/empty/error/offline state in scope.
Preserve source, attribution, fixture, simulation, and verification labels.
Match the 393px reference, then verify compact width, keyboard avoidance,
larger text, 44px targets, focus order, contrast, and reduced motion.
```

### Review prompt

```text
Compare [implemented screen] with its Figma node and design.md.
Report mismatches in this order: missing states or trust labels, component misuse,
layout, typography, color, imagery/attribution, interaction, accessibility.
Fix in-scope mismatches and verify at 393px plus one compact width.
```

### Definition of done

- Tokens and reusable components are used instead of isolated lookalikes.
- Required loaded, loading, empty, provider-failure, and offline states exist.
- Photography, icons, and attribution use local production assets.
- No temporary Figma URLs, invented facts, or hidden simulation states remain.
- Touch, keyboard, screen reader, contrast, dynamic text, safe area, and reduced motion are checked.
- The render matches Figma without copying the review-frame label into the app.

### Provenance

- Format: [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md), nine-section DESIGN.md structure.
- Visual source: Figma file `JvXw7rVf5KxoA6LlDJEqAt`, foundations `9:3`, components `4:4`, screens `4:5`.
- Behavior and scope: repository documents linked at the top.

Update this file whenever a token, component contract, or cross-screen rule changes. Update Figma in the same change so both sources remain reviewable together.
