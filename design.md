---
version: "2.0.0"
name: DaNavi
description: "DaNavi is a Vietnamese-first mobile travel companion for Da Nang. White surfaces, restrained lavender actions, real destination photography, Iconly Essential icons, modest Inter typography, and map-first on-trip guidance. Human-recorded narration stays separate from Ask AI; voice input is a focused, contextual flow."

colors:
  primary: "#7058C9"
  primary-pressed: "#5D46B7"
  primary-soft: "#F1EDFC"
  primary-soft-pressed: "#E7DFF8"
  on-primary: "#FFFFFF"
  canvas: "#FFFFFF"
  background: "#FFFFFF"
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
  scrim: "#20242C"
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
  accent-blue-soft: "#E8F2FF"
  accent-pink-soft: "#FCECF2"
  route: "#F36863"
  route-halo: "#FFFFFF"
  current-stop: "#C94642"
  on-current-stop: "#FFFFFF"
  completed-stop: "#2C7046"
  upcoming-stop: "#454B57"
  skipped-stop: "#646B78"
  user-location: "#1685FF"
  map-land-reference: "#F2F3F0"
  map-water-reference: "#DCEAF0"

typography:
  screen-title:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 26px
    fontWeight: 600
    lineHeight: 1.385
    letterSpacing: -0.65px
  sheet-title:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 21px
    fontWeight: 600
    lineHeight: 1.429
    letterSpacing: -0.45px
  section-title:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.444
    letterSpacing: -0.30px
  navigation-title:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.50
    letterSpacing: -0.20px
  card-title:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 17px
    fontWeight: 600
    lineHeight: 1.412
    letterSpacing: -0.20px
  voice-transcript:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 23px
    fontWeight: 500
    lineHeight: 1.478
    letterSpacing: -0.45px
  body:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.50
    letterSpacing: 0
  body-strong:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.50
    letterSpacing: 0
  label:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.429
    letterSpacing: 0
  helper:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.538
    letterSpacing: 0
  caption:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.50
    letterSpacing: 0
  button:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 15px
    fontWeight: 600
    lineHeight: 1.467
    letterSpacing: -0.10px
  tab-label:
    fontFamily: "Inter, system-ui, -apple-system, sans-serif"
    fontSize: 11px
    fontWeight: 500
    lineHeight: 1.455
    letterSpacing: 0

spacing:
  micro: 4px
  xs: 8px
  sm: 12px
  md: 16px
  sheet: 20px
  content: 22px
  lg: 24px
  xl: 32px
  xxl: 40px
  section: 24px

rounded:
  tag: 8px
  chip: 12px
  button: 13px
  input: 14px
  compact-card: 16px
  card: 20px
  sheet: 26px
  full: 9999px

elevation:
  flat: "none"
  card: "0 7px 24px rgba(40, 36, 63, 0.04)"
  floating: "0 3px 15px rgba(40, 36, 53, 0.11)"
  sheet: "0 -6px 28px rgba(35, 32, 52, 0.07)"
  microphone: "0 8px 25px rgba(112, 88, 201, 0.18)"

motion:
  fast: 120ms
  standard: 200ms
  deliberate: 320ms
  easing-standard: "cubic-bezier(0.2, 0, 0, 1)"
  easing-enter: "cubic-bezier(0, 0, 0, 1)"

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    minHeight: 48px
    padding: "12px 20px"
  button-secondary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    borderColor: "{colors.border-control}"
    borderWidth: 1px
    rounded: "{rounded.button}"
    minHeight: 48px
  button-tonal:
    backgroundColor: "{colors.primary-soft}"
    textColor: "{colors.primary-pressed}"
    rounded: "{rounded.chip}"
    minHeight: 44px
  button-icon:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.body}"
    rounded: "{rounded.button}"
    minSize: 44px
    iconSize: 22px
  search-field:
    backgroundColor: "{colors.surface-input}"
    textColor: "{colors.ink}"
    placeholderColor: "{colors.muted}"
    borderColor: "{colors.border-control}"
    borderWidth: 1px
    rounded: "{rounded.input}"
    minHeight: 48px
    padding: "12px"
  text-input:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    borderColor: "{colors.border-strong}"
    borderWidth: 1px
    rounded: "{rounded.input}"
    minHeight: 48px
  chip-default:
    backgroundColor: "{colors.surface-grouped}"
    textColor: "{colors.muted}"
    rounded: "{rounded.chip}"
    visualHeight: 36px
    minHitHeight: 44px
  chip-selected:
    backgroundColor: "{colors.primary-soft}"
    textColor: "{colors.primary-pressed}"
    borderColor: "{colors.border-selected}"
    borderWidth: 1px
    rounded: "{rounded.chip}"
    visualHeight: 36px
    minHitHeight: 44px
  place-card:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    borderColor: "{colors.border}"
    borderWidth: 1px
    rounded: "{rounded.card}"
    elevation: "{elevation.card}"
    imageAspectRatio: "2:1"
  place-card-compact:
    backgroundColor: "{colors.surface-card}"
    borderColor: "{colors.border}"
    borderWidth: 1px
    rounded: "{rounded.compact-card}"
    thumbnailSize: 76px
    minHeight: 80px
    padding: "8px"
  bottom-navigation:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    activeColor: "{colors.primary}"
    activeBackgroundColor: "{colors.primary-soft}"
    borderColor: "{colors.border}"
    contentHeight: 60px
  arrival-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "12px"
    elevation: "{elevation.floating}"
  map-pin-current:
    backgroundColor: "{colors.current-stop}"
    textColor: "{colors.on-current-stop}"
    borderColor: "{colors.route-halo}"
    borderWidth: 3px
    visualSize: 40px
    minHitSize: 44px
  map-pin-upcoming:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.upcoming-stop}"
    borderColor: "{colors.upcoming-stop}"
    borderWidth: 2px
    visualSize: 28px
    minHitSize: 44px
  audio-sheet:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sheet}"
    padding: "8px 20px"
    elevation: "{elevation.sheet}"
  audio-play-button:
    backgroundColor: "{colors.media}"
    textColor: "{colors.on-media}"
    rounded: "{rounded.full}"
    size: 56px
  context-chip:
    backgroundColor: "{colors.primary-soft}"
    textColor: "{colors.primary-pressed}"
    rounded: "{rounded.chip}"
    visualHeight: 36px
    minHitHeight: 44px
  voice-microphone:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.full}"
    size: 70px
    elevation: "{elevation.microphone}"
  source-card:
    backgroundColor: "{colors.surface-grouped}"
    textColor: "{colors.body}"
    borderColor: "{colors.border}"
    rounded: "{rounded.input}"
    padding: "14px"
  itinerary-stop:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.compact-card}"
    padding: "16px"
---

# DaNavi Design System

**Version 2.0.0 · Updated 2026-10-17 · Approved visual direction: V08**

DaNavi (project name: _Danang TourGuide_) is a Vietnamese-first mobile companion for exploring Da Nang, building an editable AI-assisted itinerary, and getting calm guidance on the trip. This file defines visual language and interaction behavior. Feature scope, data rules, and acceptance criteria live in the product docs.

- **Target:** Expo / React Native on iOS and Android. Web previews are for review only.
- **Structure:** YAML tokens + nine Markdown sections, following [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md). Only the structure is borrowed; no other brand's palette, fonts, or layouts.
- **UI copy:** Vietnamese. Section prose is English; quoted labels (e.g. "Tôi đã đến nơi") are the exact UI strings.

---

## 1. Visual Theme & Atmosphere

**Clean white, deliberate lavender, real photography.** A compact, soft iOS-style mobile feel: moderate titles, consistent stroke icons, white rounded cards, and low depth. Legibility outdoors comes first.

- White is the app background. Lavender signals actions and selection only.
- Real Da Nang photographs carry emotion; names and metadata sit on white below the image.
- Icons are **Iconly Essential**: outline (`light`) for actions, `bold` for the active tab.
- Hierarchy comes from size, weight, spacing, and grouping before borders or color.
- Travel mode prioritizes map, current stop, and player. Voice mode prioritizes context, transcript, and microphone.
- Screens are rendered from real components. No AI-generated bitmaps stand in for UI, icons, or place photos.

### Product modes

| Mode     | Rhythm                                  | Content                                             |
| -------- | --------------------------------------- | --------------------------------------------------- |
| Discover | Photo-led, airy lists                   | Curated POIs, detail, saved                         |
| Plan     | Ordered, clearly editable               | Preferences, AI proposal, warnings, stop reordering |
| Travel   | Minimal chrome, current goal emphasized | Map, arrival, human audio, place-scoped Ask         |

**Scope.** Core: curated POIs, Explore/Search, editable AI itinerary, map + GPS arrival, human-recorded audio, source-backed RAG Ask AI, saved places. **P1:** Camera, speech input, Google login. **Out of scope:** TTS, continuous voice conversation, booking/payment, social.

### Reference images

| Image                                  | Role                  | Must preserve                                                                             |
| -------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------- |
| `design/references/v08/01-explore.png` | Explore               | White canvas, wordmark, search, categories, real photo, white-caption cards, four tabs    |
| `design/references/v08/02-voice.png`   | Voice input           | Dragon Bridge context, small lavender orb, central transcript, mic, "Nhập chữ / Kết thúc" |
| `design/references/v08/03-map.png`     | Arrived at audio stop | Readable map, state-coded markers, white sheet, dark media control, lavender CTA          |

The images set direction and structure; tokens and accessibility rules in this file win. Do not copy sample metadata, durations, coordinates, or the drawn status bar into the real app. Pre-V08 teal palettes and AI-drawn 3D icons are obsolete. There is no official logo yet: use the "DaNavi" wordmark.

---

## 2. Color Palette & Roles

### Brand and surfaces

| Token                   | Hex       | Role                                                   |
| ----------------------- | --------- | ------------------------------------------------------ |
| `primary`               | `#7058C9` | CTA, active tab, microphone, actionable links          |
| `primary-pressed`       | `#5D46B7` | Pressed state; text on lavender tint                   |
| `primary-soft`          | `#F1EDFC` | Context chip, selected category, active-tab capsule    |
| `canvas` / `background` | `#FFFFFF` | App background, header, sheets, navigation             |
| `surface-grouped`       | `#F7F7FA` | Settings groups, sources, skeletons, secondary content |
| `surface-input`         | `#FAFAFD` | Search and input areas                                 |
| `ink`                   | `#20242C` | Titles, place names, key content                       |
| `body`                  | `#535C69` | Supporting text, action icons                          |
| `muted`                 | `#646B78` | Metadata that must still be readable                   |
| `border`                | `#E8EBF0` | Hairlines, decorative borders                          |
| `border-control`        | `#DADDE7` | Search and secondary controls                          |
| `border-strong`         | `#848D9E` | Required boundaries, high-contrast needs               |
| `media`                 | `#222633` | Play/Pause for human audio                             |

One dominant lavender action per decision area. Media controls use the dark `media` color to separate _listening_ from _trip actions_. Pastel blue/pink are optional decorative fills only, never action or status colors.

### Map and status colors

| Meaning              | Token                     | Rule                                                  |
| -------------------- | ------------------------- | ----------------------------------------------------- |
| Route                | `route` + `route-halo`    | Coral `#F36863` with white halo                       |
| Current stop         | `current-stop`            | Deeper coral `#C94642`, white number, pin shape       |
| Completed            | `completed-stop`          | Green `#2C7046` + ✓                                   |
| Upcoming             | `upcoming-stop`           | White fill, dark border and number                    |
| User location        | `user-location`           | Blue dot `#1685FF` with white ring; never a POI shape |
| Unverified / limited | `warning` on `warning-bg` | Icon + specific explanation                           |
| Blocking error       | `error` on `error-bg`     | Message, remedy, link to the error                    |
| Info / context       | `info` on `info-bg`       | Dark lavender on light tint                           |

Route coral is never used for delete or errors. Do not use the completed color for a stop that was only reached, is pending sync, or belongs to a trip not yet started. Never rely on color alone: pair with icon, text, or number.

### Contrast

- Normal text target is ≥ 4.5:1. White on `primary` ≈ 5.35:1; white on `current-stop` ≈ 4.73:1.
- Do not lower the opacity of secondary text; use `muted`.
- Hairlines are secondary separators, never the only cue for a control or selection. Use `focus` / `border-strong` where a boundary is required.
- Map reference colors do not replace provider tiles. Check pins and routes over varied tiles and keep attribution visible.

---

## 3. Typography Rules

**Inter** (bundled 400/500/600/700, full Vietnamese coverage), with system sans as fallback. No other bundled brand fonts.

| Token                  | Size / line height | Weight    | Use                                   |
| ---------------------- | ------------------ | --------- | ------------------------------------- |
| `screen-title`         | 26 / 36            | 600       | "Khám phá Đà Nẵng", page titles       |
| `sheet-title`          | 21 / 30            | 600       | Arrival card place name, sheet titles |
| `section-title`        | 18 / 26            | 600       | Content groups, result lists          |
| `navigation-title`     | 16 / 24            | 600       | Compact Voice/Travel header           |
| `card-title`           | 17 / 24            | 600       | Place name in cards                   |
| `voice-transcript`     | 23 / 34            | 500       | Short recognized speech               |
| `body` / `body-strong` | 16 / 24            | 400 / 600 | Descriptions, transcripts, answers    |
| `label`                | 14 / 20            | 500       | Form labels, control names            |
| `helper`               | 13 / 20            | 400       | Hints, short descriptions             |
| `caption`              | 12 / 18            | 400       | Metadata, duration, sources           |
| `button`               | 15 / 22            | 600       | Actions                               |
| `tab-label`            | 11 / 16            | 500       | Four tab labels                       |

**Rules**

- 600 for hierarchy, 500 for labels, 400 for paragraphs. 700 is rare; never bold a whole screen.
- Let titles wrap; grow height rather than shrinking type. Never ellipsize warnings, visit conditions, or sources.
- Minimum 12 for product metadata (tab labels are the 11 exception). Labels of 8–10 in the preview PNGs must be enlarged in implementation.
- Long body/transcript text keeps line height ≥ 1.45. Keep Vietnamese diacritics unclipped.
- Honor OS text scale and bold-text settings; no global font-scale cap.
- Tabular numerals for media time and stop numbers. No monospace for the whole app.
- **React Native note:** YAML `px` values are logical points at scale 1. Pass numbers to `fontSize` and convert ratio line heights to absolute numbers; never pass CSS strings like `"26px"` to native styles.

---

## 4. Component Stylings

### 4.1 Icons, photos, assets

**Iconly Essential** is the only UI icon source (free pack via `react-iconly@2.2.10`, based on Iconly v2). Outline = `light`; selected = `bold`. Keep original SVG paths and the 24×24 viewBox; change only size, color, and built-in variant. No AI-redrawn, emoji, or mixed icon packs. If no exact glyph exists, use the closest Essential icon plus a clear label (e.g. the "Có audio" badge uses `VolumeUp`).

Sizes: default 22 · inline 16–18 · tab 23–24 · microphone 28–30. Hit areas are separate from glyph size.

| Function                           | Asset                                                                          |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| Explore / Trips / Saved / Settings | `Discovery`, `Location`, `Bookmark`, `Setting` (light + bold)                  |
| Search / Filter                    | `Search-light`, `Filter-light`                                                 |
| Ask AI / context                   | `Chat-light`, `Location-light`                                                 |
| Back / open detail                 | `ChevronLeft-light`, `ChevronRight-light`                                      |
| More / collapse                    | `MoreCircle-light`, `ChevronDown-light`                                        |
| Audio / play / transcript          | `VolumeUp-light`, `Play-bold`, `Document-light`                                |
| Seek back / forward                | `ChevronLeftCircle-light`, `ChevronRightCircle-light` + "−15s" / "+15s" labels |
| Mic / type / end                   | `Voice2-light`, `EditSquare-light`, `CloseSquare-light`                        |
| Itinerary / add / reorder          | `Calendar-light`, `Plus-light`, `Swap-light`                                   |
| Info / error / done                | `InfoCircle-light`, `Danger-light`, `TickSquare-light`                         |

**Place photos** must be real photographs of the correct landmark with source and license recorded. No AI-generated Da Nang images. Crop with `cover`; never alter content.

| Asset                                    | Source                              | Terms                                               |
| ---------------------------------------- | ----------------------------------- | --------------------------------------------------- |
| `assets/images/places/dragon-bridge.jpg` | allPhoto Bangkok / Unsplash         | Hero and audio thumbnail; focal point x≈0.5, y≈0.45 |
| `assets/images/places/my-khe.jpg`        | . Ray in Manila / Wikimedia Commons | CC BY 2.0; credit author, license, and cropping     |
| `assets/icons/iconly/`                   | Piqo / Iconly Essential             | Original SVGs + package license                     |
| `assets/fonts/inter/`                    | Inter / Google Fonts                | TTF 400/500/600/700 + OFL                           |
| `design/ASSET-SOURCES.md`                | Manifest                            | URLs, authors, licenses, edits, fixture notes       |

Missing photo → neutral placeholder with place name and loading state. Missing audio → "chưa có thuyết minh". Never fill gaps with generated assets.

### 4.2 Buttons

| Variant   | Spec                                                         | Use                                |
| --------- | ------------------------------------------------------------ | ---------------------------------- |
| Primary   | `button-primary`: lavender, white text, radius 13, ≥ 48 high | One dominant CTA per decision area |
| Secondary | White, dark text, `border-control`, same height              | Alternatives, cancel               |
| Tonal     | `primary-soft`, `primary-pressed` text                       | Ask AI, grouped secondary actions  |
| Text      | No frame, primary text, still a full hit area                | See all, sources, edit             |
| Icon      | 22 glyph in ≥ 44×44 target, accessible label                 | Compact actions                    |

Pressed: `primary-pressed` or surface darkening, 120ms. Loading: same size, contextual label, blocks duplicate submit. Disabled: `disabled-bg` / `disabled-ink` with a nearby reason when useful. Focus: visible primary ring. Errors belong to fields and notices, never turn buttons red.

### 4.3 Search, inputs, categories

- Search: ≥ 48 high, radius 14, `surface-input`, magnifier left, single line. Filter button is its own 44–48 target, 8 apart.
- Inputs: real label or accessible label (placeholder is not a label). Focus = primary 2px; invalid = error + specific helper.
- Categories: ~36 visual height, ≥ 44 hit area, horizontal scroll. Selected changes fill, text, and border and exposes selected state. Never shrink text to fit four labels.
- Search covers Vietnamese place names, tags, and topics. **No results** names the query and offers "Xóa bộ lọc". **Network error** offers "Thử lại" and keeps the query. These are separate states.

### 4.4 Place cards

- **Featured:** real photo ~2:1, radius 20, white caption area with name + one category/area line, 1px border, low shadow. Save sits on the photo (white, glyph 20–22, visual 36–40, target 44). "Có audio" badge (icon + text) only when matching audio exists.
- **Compact:** thumbnail 64–76, radius 16, name + category + chevron, min height 80 but grows with text scale. Used in Search and Saved; do not repeat large hero photos per row.
- Card opens detail; Save is a separate control. No rating, price, open-now, or distance unless verified data exists.

### 4.5 Header and bottom navigation

Four tabs: **Khám phá / Chuyến đi / Đã lưu / Cài đặt**, always icon + label. Active: bold icon, lavender label, small `primary-soft` capsule. Inactive: outline icon, `muted`. White bar, one top divider, no center "+" button.

Bar content ≈ 60 plus the real safe-area inset (not a fixed 84). Header ≈ 48–52 plus top inset. Status bar, home indicator, and permission dialogs are native; never redraw them. Travel, player, Voice, and detail use contextual back navigation, not extra tabs. Returning from Ask/Voice preserves trip, markers, camera, and audio progress.

### 4.6 Map and markers

- V08 tiles are OpenStreetMap, a visual reference only. The real SDK follows architecture; keep attribution and provide a list fallback if the provider fails.
- Route: coral, 3–4 pt line, white halo ≈ 7–8. Do not connect points with straight lines and call it navigation.
- Selecting a pin opens the matching POI card. Marker order always follows the current itinerary; reordering marks routes stale until recomputed.

| Marker    | Look                                                    | State                         |
| --------- | ------------------------------------------------------- | ----------------------------- |
| User      | Blue dot, white ring; accuracy halo only with real data | Not a POI shape               |
| Upcoming  | White circle, dark border and number                    | Ordered, no check             |
| Current   | Deep-coral pin, white number, slightly larger           | One per trip                  |
| Completed | Green circle + ✓                                        | Only after a valid completion |
| Skipped   | Number + "Đã bỏ qua", subdued                           | Never the ✓ style             |
| Has audio | Small `VolumeUp` badge                                  | Means available, not playing  |

Visual size 28–40, hit area ≥ 44. Sample positions must be labelled "Mô phỏng" / "Tuyến minh họa". No completed markers before Start. Map controls sit at the right, white, 44 targets, clear of pins, sheets, and attribution. Preserve zoom when audio appears; only re-center when needed.

### 4.7 Arrival and human audio

**Arrived ≠ completed ≠ synced.** The arrival card shows place name, sequence, and method/state: GPS, manual, simulated, pending sync. "Hoàn thành điểm" and "Bỏ qua điểm" are separate actions.

Before arrival: show the next stop and, where allowed, "Tôi đã đến nơi"; **do not show the arrival player yet**. On arriving at a stop with audio, a white sheet appears over the visible map. POI detail may offer "Nghe thử" as a separate user-initiated flow.

Player order: real thumbnail → title → "Giọng người thật · Tiếng Việt/English" → status → seek/time → controls → "Hỏi AI về điểm này" → trip CTA. Play/Pause is dark (`media`); progress is lavender.

- Default is **ready, user taps Play**. Autoplay stays off; any opt-in is per session and explicitly described.
- Controls: Play/Pause, −15s/+15s (labelled so they don't look like previous/next stop), speed, transcript.
- Duration comes from asset metadata; unknown shows `--:--` (never copy "3:24" from the mock).
- Missing language/asset, buffering, error, paused, finished are distinct states. No synthesized voice, no silent language switch.
- Opening transcript or Ask must not reset progress. One audio at a time; keep playback intent when interrupted.
- Initialize the player once per valid arrival; GPS jitter must not spawn extra sheets or replays, and must not dismiss active playback.
- Playing recorded audio **never requests microphone permission**. Finishing audio does not auto-complete the stop.

### 4.8 Voice input (P1)

Follows `02-voice.png`. This is **speech-to-text for Ask AI**, not an AI call or TTS. Until P1 ships, Ask AI is text-only and no dead mic is shown.

Layout: compact header "Hỏi DaNavi" → place context → small orb (~156 at 393 width) → state → transcript → mic + "Nhập chữ / Kết thúc". No tab bar. The orb is decorative, not a logo or data source.

| State          | UI                                             | Behavior                                          |
| -------------- | ---------------------------------------------- | ------------------------------------------------- |
| Idle           | Static orb, invitation                         | Not recording                                     |
| Permission     | Short explanation, then OS prompt              | Only after the user taps the mic                  |
| Listening      | "Đang nghe", live interim text                 | "Chạm để dừng"; waveform only from real data      |
| Transcribing   | "Đang nhận dạng"                               | Never keep saying "listening" after capture stops |
| Review         | Editable transcript, "Thu lại" / "Gửi câu hỏi" | **Never auto-submit**                             |
| Submitting     | Context + question retained, loading           | Block duplicates                                  |
| Answer         | Back to text Ask AI with sources               | Answer is never read aloud by AI                  |
| Error / denied | Specific error, "Thu lại" or "Nhập chữ"        | Keep context and recognized text                  |

Ending, leaving, or backgrounding must stop capture and update labels. If guide audio is playing, pause it when recording starts and keep its progress. Opening text Ask never requests the mic or pauses audio.

### 4.9 Ask AI, facts, sources

- A context chip always states scope: this POI, this trip, or Da Nang in general. The question is editable before sending.
- Sources follow the answer immediately: title, date/version when known, open action. Never invent URLs, citation numbers, confidence scores, or "verified" marks.
- Three outcomes stay distinct: supported answer · insufficient/conflicting evidence · service unavailable. P0 answers are Vietnamese; missing coverage is disclosed.
- POI detail separates description from operating facts. Unknown hours/price read "Chưa xác minh", never "Đang mở" or "Miễn phí". Visit duration is "Ước tính để lập kế hoạch".

### 4.10 Itinerary and derived screens

Derived screens reuse current tokens and components; they never introduce a new theme.

| Screen                 | Order                                                                 | Rule                                                             |
| ---------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------- |
| UI-01 Explore          | Header → title → search → categories → featured/compact cards → tabs  | Per image 01; entries for Ask AI and trip planning               |
| UI-01.search           | Query → filter → compact results → map action                         | Keep query/filter on return                                      |
| UI-02 Explore map      | Compact search → map → POI sheet → tabs                               | List fallback; no travel arrival here                            |
| UI-03 POI detail       | Gallery → name → facts → description/sources → audio → Ask → Add/Save | No card-in-card pages                                            |
| UI-04 Trip preferences | Time → start → interests → transport → CTA                            | Fixed labels, inline validation                                  |
| UI-05 AI proposal      | Wait state → warnings → ordered days → Accept/Regenerate              | No fake percentage; regenerate never overwrites an accepted plan |
| UI-06 Itinerary        | Title/day → warnings → timeline → add/map → Start                     | Drag + "Đưa lên / Đưa xuống"; no completed before Start          |
| UI-07 Trip map         | Route → stop sheet → status → Start                                   | Block Start on blockers; explain permissions                     |
| UI-08 Travel           | Map → current/next → location status → arrival action                 | Minimal chrome; foreground GPS + manual fallback                 |
| UI-09 Arrival          | State → POI → audio/Ask → next                                        | Arrival never auto-completes; pending ≠ synced                   |
| UI-10 Human audio      | Thumbnail/title → human/language → media → transcript/Ask             | Per image 03; map stays visible                                  |
| UI-11 Saved            | Title → compact cards → unsave/add                                    | Empty state leads to Explore                                     |
| UI-12 Login            | Short intro → email/password → login/create                           | Google only when P1 is on; Explore stays public                  |
| UI-13 Settings         | Language → permissions → audio → account                              | Grouped rows, not a dashboard grid                               |
| UI-14 Ask AI           | Context → conversation → answer/sources → composer                    | Text in P0; mic only when P1 is live                             |
| UI-15 Camera (P1)      | Capture → result/unknown/ambiguous → pick POI                         | Never create a POI from model output                             |
| UI-16 Speech (P1)      | Context → listening → review → Ask                                    | Per image 02; typing always available                            |

Trip rows show number, name, thumbnail if any, labelled duration estimate, route status, edit/remove. After Start, current and visited stops are protected; editing upcoming stops invalidates routes. Never restart the whole flow to fix one field.

### 4.11 Loading, empty, recovery

| Situation                 | Display                                   | Recovery                                   |
| ------------------------- | ----------------------------------------- | ------------------------------------------ |
| Loading                   | Geometry-matched skeleton, gentle shimmer | Stable replacement                         |
| Planner running           | Indeterminate + specific copy             | Cancel/retry, keep input                   |
| Empty Search/Saved        | Context-specific explanation              | Clear filters / Explore                    |
| Map/route failure         | Names the failing service                 | Retry + stop list                          |
| Weak/denied GPS           | Visible state, no fake arrival            | Settings or manual "Tôi đã đến nơi"        |
| Audio error / expired URL | Keep POI, elapsed time, intent            | Refresh/retry, no TTS                      |
| RAG lacks sources         | Say information is insufficient           | Ask more specifically                      |
| Offline / pending arrival | Separate "pending" label                  | Reconcile later, no duplicates             |
| Stale trip revision       | Explain the plan changed                  | Reload canonical state, protect user edits |

Handling network errors does not add offline maps or downloads to P0.

---

## 5. Layout Principles

- **Reference frame:** 393 × 852 logical points. The 1,179 × 2,556 PNGs are 3× exports, not layout sizes.
- **Padding:** content 22, sheets 20, small screens 16. Map is full-bleed.
- **Spacing scale:** 4 / 8 / 12 / 16 / 24 / 32 / 40. Related items 8–12; cards 12–16 apart; sections 24.
- One column on phones; content truly scrolls, never scaled down to fit a screenshot.
- Sticky actions and the tab bar respect safe areas and add content inset/scroll padding so the last item is never covered.
- Never hard-code a 44 status bar or 23 home indicator.

**Canonical layouts**

- **Explore:** wordmark + Ask → 26pt headline → search 48 + filter → categories → section → photo cards → compact destination → trip entry → tabs. Below-the-fold content scrolls; don't cram every POI onto screen one.
- **Voice:** compact header/context; orb 140–156; centered transcript (few lines, then scroll); mic at bottom; two labelled utilities. With keyboard open, switch to a text composer and drop the orb.
- **Travel/audio:** map as the main surface; arrival card near the top; compact audio sheet ~35–40% of available height at default text scale (reference only, not locked). Relevant pins and attribution stay visible; the sheet expands for transcripts.

**Hierarchy.** Each screen answers one primary question: where to go, what to edit, which stop, what to hear, or what to ask. No stat dashboards, promo cards, charts, or badges to fill space. Warnings, sources, and status sit next to the content they explain.

---

## 6. Depth & Elevation

| Level    | Applies to                                           | Token                           |
| -------- | ---------------------------------------------------- | ------------------------------- |
| Flat     | Header, forms, lists, navigation                     | `elevation.flat`                |
| Card     | Featured POI cards that truly separate from the page | `elevation.card` + light border |
| Floating | Arrival card, map controls                           | `elevation.floating`            |
| Sheet    | Audio / transcript / arrival sheets                  | `elevation.sheet`               |
| Mic      | Active Voice mic                                     | `elevation.microphone`          |

No shadows on every row, chip, or text. No neumorphism, full-screen glass blur, heavy black shadows, or contrast-reducing glows. The Voice orb is a controlled illustrative exception and its effects must not spread to search or forms. YAML shadows are CSS-style references: translate them to native styles rather than pasting `box-shadow` strings, and match hierarchy over exact blur values across iOS/Android.

**Motion**

- Press: surface change or 0.98 scale over 120ms, no layout shift.
- Selection / tab / filter: 200ms, no color flashing.
- Sheets: 320ms from the bottom, map camera stays steady.
- Never animate camera, reorder, and sheet together.
- Orb idle is static; listening animates lightly only during real capture. Live waveform only if the engine provides input data.
- Respect Reduce Motion: stop breathing/rotation/shimmer, keep labels and state. Haptics support but never replace visual or audible confirmation.

---

## 7. Do's and Don'ts

### Do

- Use white + lavender, Inter, and Iconly Essential consistently.
- Use real, correctly identified, attributed place photos.
- Build Button / Card / Input / Sheet / Pin / Player as components with variants and states.
- Keep place name, context, sources, and the next step easy to find.
- Keep arrival / completion / sync / simulation and recording / playback clearly separate.
- Provide list fallback for maps, typing fallback for speech, transcript for audio.
- Verify on phone frames, large text scale, and native accessibility.
- Keep CORE / P1 / FUTURE scope from the product docs when adding screens.

### Don't

- Return to the V01–V07 palettes/icons or adopt a theme from another skill.
- Use image generation for UI, icons, place photos, or screenshots in place of components.
- Use 3D icons, emoji, or guessed SVGs instead of the chosen Iconly assets.
- Use a screenshot as a background with hotspots to fake components.
- Invent POIs, ratings, hours, prices, distances, routes, sources, or AI progress percentages.
- Treat "has audio" as "playing" or "arrived" as "completed".
- Request the microphone for recorded audio, or show "Đang nghe" after capture has stopped.
- Add full voice AI, TTS, booking, payment, social, a new logo/app icon, or offline downloads on your own.
- Force text, warnings, sources, or footers into fixed frames just to match a PNG.

---

## 8. Responsive Behavior

| Width   | Behavior                                                                                  |
| ------- | ----------------------------------------------------------------------------------------- |
| 320–359 | Padding 16; chips scroll; cards/lists flex to content; secondary media wraps to a new row |
| 360–430 | Padding 20–22; keep V08 structure; photos scale with width                                |
| 431–767 | Padding 24; do not scale fonts or icons with the viewport                                 |
| ≥ 768   | Tablet is not P0; for previews, cap the content rail at 640 and let the map extend behind |

Always keep four labelled tabs (no hamburger, no IA change by width). Landscape handles safe areas and scrolling; no tablet/desktop completeness is promised.

**Accessibility and native behavior**

- Targets ≥ 44×44 (48 for primary or platform-required); expand hit areas without overlapping neighbors.
- Support OS text scaling and bold text. Cards grow, media toolbars wrap, transcript sheets can go full screen with a way back to the map.
- Screen readers: markers read place name + sequence + state; controls read label, selected/disabled, and time/seek values.
- Reorder offers "Đưa lên / Đưa xuống" beside drag; the map has an equivalent list.
- Move focus to the heading after arrival, errors, or sheet open; back/dismiss never loses input.
- Placeholder text, color, haptics, sound, or position are never the only cue.
- Keep provider attribution unobscured by safe-area overlays or sheets.
- This release is **light theme only**. Dark mode needs its own token, imagery, and state review, not color inversion.

**Minimum checks:** widths 320 / 360 / 393; text scale 1.0 and 1.5–2.0; VoiceOver/TalkBack on main flows; permission denied; offline; audio unavailable. V08 was render-checked on web at 393/360, which does not replace native device testing.

---

## 9. Agent Prompt Guide

### Source of truth

1. Product docs and acceptance criteria: features, P0/P1, data.
2. This `DESIGN.md`: tokens, components, visual IA, interaction contract.
3. The three V08 PNGs: approved layout and feel, within the accessibility limits above.
4. V08 source/assets and manifest: implementation evidence, not proof that GPS/audio/AI works.

`AGENTS.md` governs workflow/build/test if present. UI UX Pro Max may suggest patterns but must not override palette, icons, or scope defined here.

### Quick reference

| Item                          | Value                                                          |
| ----------------------------- | -------------------------------------------------------------- |
| Background / primary          | `#FFFFFF` / `#7058C9`                                          |
| Pressed / tint                | `#5D46B7` / `#F1EDFC`                                          |
| Text                          | `#20242C` / `#535C69` / `#646B78`                              |
| Font / weights                | Inter; 400, 500, 600 (700 rare)                                |
| Padding / card / sheet radius | 22 / 20 / 26                                                   |
| Icons / touch                 | Iconly Light + Bold; glyph 22, target ≥ 44                     |
| CTA / media play / mic        | 48 high / 56 dark circle / 70 lavender circle                  |
| Map                           | Coral route · deep-coral current · blue user · green completed |
| Target stack                  | Expo / React Native (web for review only)                      |

### File layout

```text
DESIGN.md
design/
  ASSET-SOURCES.md
  references/v08/
    01-explore.png
    02-voice.png
    03-map.png
assets/
  icons/iconly/
  images/places/
  fonts/inter/
```

If only `DESIGN.md` is copied, bring the PNGs and assets too. Map these paths to the repo's existing conventions instead of duplicating folders. No scratch absolute paths, library IDs, or hotlinks as production asset paths.

### Prompt: implement the three reference screens

```text
Read AGENTS.md if present, DESIGN.md, and the current product docs before editing.
Inspect the three images in design/references/v08 and design/ASSET-SOURCES.md.
Implement Explore, Voice input (P1), and Map/Audio with shared components in
Expo/React Native. Use the tokens, Iconly SVGs, and provided real photos;
no image generation and no substitute locations.
Follow DESIGN.md for font and spacing; fix small PNG details for accessibility.
Keep Voice behind a P1 feature flag; text Ask AI (P0) must work independently.
Without a backend/provider, use a clearly labelled central fixture and do not
claim real data. Do not add autoplay, TTS, booking, extra tabs, or change architecture.
Verify assets, 360/393 layout, safe areas, text scale, and relevant error states.
Report changed files, how you verified, and what is still simulated.
```

### Prompt: add a missing screen

```text
Using DESIGN.md and the V08 images, implement [screen/state] in the existing navigation.
Reuse Button, Input, PlaceCard, ContextChip, SourceCard, and Sheet.
Keep white/lavender, Inter, Iconly Light/Bold, and the spacing rhythm; no new theme.
Read the matching requirement for correct data, permissions, and empty/error states.
Do not expand feature scope, rebuild the app, or overwrite earlier edits.
Export a preview from real components to compare with the V08 direction.
```

### Prompt: review before sign-off

```text
Compare the implemented screen to DESIGN.md and the V08 images.
Check: original assets/sources; tokens; icon variants; typography; borders/elevation;
hit areas; keyboard/safe area; text scale; source/unknown states;
arrival vs completion, audio vs microphone, fixture vs real data.
Fix evidenced issues within this screen only; keep features and architecture.
Do not claim GPS, microphone, or playback were verified if only web render was run.
```

### Completion checklist

- [ ] DaNavi brand, current palette, and the three V08 images are used.
- [ ] Iconly SVGs / photos / fonts exist; no fake paths or generated substitutes.
- [ ] One token system and component set; no stray ad-hoc colors.
- [ ] Previews are rendered from components, not mockup backgrounds.
- [ ] Pin text/numbers are readable; no tiny metadata like some PNGs.
- [ ] Final content is not hidden by footers/sheets; controls don't overlap.
- [ ] Selected / loading / disabled / error / empty / unavailable states are defined where relevant.
- [ ] Permissions, recording, and audio states match the real engine; typing/manual-confirm recovery exists.
- [ ] Sources, attribution, unverified data, and fixtures are labelled correctly.
- [ ] Real verification results and remaining limits are reported.

### Known gaps

Final logo/app icon, map SDK, GPS thresholds, route-freshness policy, and real audio assets are undecided here. P0/P1 follows the product docs. The three PNGs fix direction only: they are not a full state library, a dark-mode spec, or an accessibility certification. Derived screens follow the current system; major brand changes need re-approval.

### Sources and version history

- **V1:** original Danang TourGuide design file; trust, permission, RAG, itinerary, and accessibility rules kept where still valid.
- **V2:** DaNavi V08: white/lavender, Iconly Essential SVG, real photos, Voice layout, map/audio, normalized tokens and asset handoff.
- Structure reference: [Awesome DESIGN.md](https://github.com/VoltAgent/awesome-design-md) at commit `3b605329240ce735b510037cca322f1831fdd7f8` (read 2026-10-17). Only the token/pattern description approach is reused.
- [Iconly](https://iconly.pro/) · [Iconly Essential package](https://github.com/jrgarciadev/react-iconly) · asset licenses in [design/ASSET-SOURCES.md](design/ASSET-SOURCES.md).

This file replaces the v1 visual design file. When tokens or interactions change, edit this canonical source and re-check the affected screens; do not keep two competing DESIGN.md files in one project scope.
