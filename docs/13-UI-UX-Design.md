# UI/UX Design Specification — Danang TourGuide

Input: product spec §30–32, [03-Blueprint-IEEE-1016.md](./03-Blueprint-IEEE-1016.md).  
Output of this doc: screen inventory, IA, design system, states. **Figma file is not generated here** (needs your Figma account). HTML prototypes can be added later under `docs/design/UI_UX_design`.

---

## 1. Design direction

**iOS-first editorial travel:** large photography, clean white, blue/cyan accent, frosted cards, large titles, bottom sheets, haptics, subtle motion, map overlays.

**Signature motif:** selected photos as a **connected constellation** around an AI center node → DNA → recommendations.

---

## 2. Information architecture

**Tabs (only four):** For You · Explore · Trips · Profile

Not tabs: Chat, Map, Audio, Saved (contextual).

| From | Opens |
|------|--------|
| Trip | Map |
| Place | Ask AI |
| Travel Mode | Audio |
| For You | Save |

---

## 3. Screen inventory (spec §31)

### Visual taste

| # | Screen | Goal | Key components |
|---|--------|------|----------------|
| 1 | Welcome | Positioning + CTA | Hero, “Chọn vài bức ảnh…” |
| 2 | Visual Taste Intro | Explain 5–10 photos | Constellation preview empty |
| 3 | System Photo Picker | Native picker | OS UI |
| 4 | Selected Photo Constellation | Confirm set | Graph of photos + center node |
| 5 | AI Analysis | Wait without dead screen | Progress, cancellable |
| 6 | Travel DNA | Understand scores | Bars Nature/Beach/… |
| 7 | Edit Preference | User control | Sliders, confirm |

### Discovery

| # | Screen | Notes |
|---|--------|--------|
| 8 | For You | Match %, tags, Save, Not interested, Add, Why |
| 9 | Six Degrees | Evidence path, photo thumbnails |
| 10 | Explore | Search, categories |
| 11 | Explore by Image | P1 single upload |
| 12 | Similar Image Results | Vibe % |
| 13 | Explore Map | POI pins |
| 14 | Place Detail | Facts from DB, gallery, actions |
| 15 | Saved / Collections | Sheet or stack from Profile/For You |

### Trip

| # | Screen |
|---|--------|
| 16 | Create Trip |
| 17 | AI Trip Builder (progress) |
| 18 | Trip Overview |
| 19 | Day Itinerary |
| 20 | Edit / Reorder (drag) |
| 21 | Trip Map |

### On-trip

| # | Screen |
|---|--------|
| 22 | Today / Start Trip |
| 23 | Travel Mode |
| 24 | Arrival Card (sheet) |
| 25 | Audio Guide |
| 26 | Contextual Ask AI |
| 27 | Weather Adaptation (P1 sheet) |

### Account

| # | Screen |
|---|--------|
| 28 | Travel Profile |
| 29 | Trip History |
| 30 | Feedback |
| 31 | Settings |

---

## 4. Personas → tasks

| Persona | Primary path |
|---------|----------------|
| Lan | Taste → For You → Save cafes/beaches → weekend trip |
| Alex | Taste → Why → map → 3-day builder |
| Minh | Edit DNA → builder → weather proposal |

---

## 5. UX quality

| Category | Requirement | AC |
|----------|-------------|-----|
| Usability | Taste confirm in few steps | < 5 screens to DNA |
| Accessibility | Dynamic type, contrast | WCAG 2.1 AA targets |
| Feedback | Analysis < perceived hang | Skeleton + progress < 300ms first paint |
| Errors | Inline + retry | No blank crash |
| IA | 4 tabs | Spec §30 |

---

## 6. States

| State | Empty | Error | Loading |
|-------|-------|-------|---------|
| For You | CTA to Visual Taste | Retry rec | Skeleton cards |
| Explore | No results copy | Retry search | Spinner |
| Trip | Create trip | Build failed → heuristic fallback message | Builder animation |
| Ask AI | Placeholder questions | RAG refuse / timeout | Typing indicator |
| Audio | Generate | TTS fail → read text | Waveform |

### Mobile states that must be designed

| Flow | Normal | Fallback / permission | Simulated demo label |
|------|--------|-----------------------|----------------------|
| Voice guidance | Play/pause, transcript, language, audio progress | TTS unavailable → readable story; audio permission not required for playback | “Sample narration” if prerecorded fixture |
| Arrival | Current stop card after accurate foreground GPS fix | Permission denied/low accuracy → “I’m here” manual action; no repeated card | “Simulated arrival” badge and method retained |
| Camera scan (P2) | Preview → capture → recognition confidence → matched POI | Unknown/low confidence → choose place manually; denied camera → explain permissions | “Scan simulation” badge until live vision exists |
| Route edit | Drag stops, save, refresh travel legs | Provider unavailable → `estimated`/`stale` chip, no fabricated live ETA | “Sample route” if fixture |

Camera scan remains P2 under A-16. Its states are design preparation, not a claim that the V1 API or model is implemented.

---

## 7. Copy (seed)

- Taste: **Chọn 5–10 ảnh thể hiện những nơi bạn yêu thích.**
- Arrival: **Bạn đã đến Chùa Linh Ứng.**
- Why: path labels from persisted match evidence (photo → matched tag → POI), with a maximum of six nodes; score is calibrated display, not probability.

Bilingual: all UI strings in `vi`/`en` resource files.

---

## 8. Design system tokens (starter)

| Token | Value |
|-------|--------|
| Accent | Cyan/blue (exact hex in Figma) |
| Surface | White / translucent |
| Radius | Large cards 16–24 |
| Type | Large title + body |

Components: PhotoConstellation, MatchBadge, PlaceCard, StopTimeline, ArrivalSheet, DnaBars.

---

## 9. Traceability

| Screen | PRD |
|--------|-----|
| 1–7 | FR-PREF-* |
| 8–9 | FR-REC-* |
| 10–14 | FR-EXP-*, FR-PLC-01 |
| 16–21 | FR-TRP-* |
| 22–26 | FR-TRV-*, FR-AI-01 |

---

## 10. Next (you)

1. Figma file for the 31-screen inventory, prioritizing P0 and the mobile states above (light mode first).
2. Optional HTML in `docs/design/UI_UX_design` for advisor review without Figma.
