# Gonarra UI research — reference review and gap analysis (2026-11-08)

| Field | Value |
|---|---|
| Document | UI research note (input to SCR-021..SCR-034 refresh; not a spec change) |
| Date | 2026-11-08 |
| Author | UI/UX research (drafted with Claude Code) for Lê Ngọc Tấn Hiền |
| Inputs | `ref/` (14 Vietdetour screenshots, 5 Dribbble mockups), `apps/mobile/src/**`, [`README.md`](./README.md), [`screen-specs.md`](./screen-specs.md) |
| Status | Draft. Approvals **[Pending]** |

Screen IDs follow [`screen-specs.md`](./screen-specs.md). "Current" cites files under `apps/mobile/src/`. Every new
string is given in VI and EN. Nothing below proposes ratings, review counts, social features, check-in, expenses,
budgets, multi-city, flights or in-app booking.

---

## 1. Summary

- **Adopt the Vietdetour itinerary left rail** (time · mode icon · distance per leg, beside each stop card). It is the
  single biggest legibility win over today's `LegRow` pill, and it maps 1:1 to `Stop.planned_arrival` and `Leg`.
  Every distance and duration on the rail is prefixed with **≈** and the day carries a one-line estimate notice.
- **Adopt a stepped create-trip wizard** (4 steps with a segmented progress bar, Back/Next footer, review step with
  "tap a section to change it"). Every step maps to an existing `TripCreate` / `PlanPreviewCreate` field; no contract
  change is needed for P0. The "Describe" free-text mode stays as the alternative entry.
- **Adopt the cover header + date chips** for the proposal (title, `dates · days · stops` meta) — Gonarra already has
  most of this (`ProposalHeader`); the gap is the date-labelled day chips and a "ready, not saved" toast.
- **Adapt the "Spots in Hội An" rail** for Home and Explore using the existing `area_code` filter on API-010. Cards
  show photo (Wikimedia, credited) or category illustration, name, category and suggested visit time — **no stars, no
  review counts, no distance from the user**.
- **Adapt the Dribbble place detail** (hero with thumbnail gallery, three info tiles, tags). Gonarra's tiles are
  Hours · Visit time · Ticket, each showing *chưa rõ / unknown* when unknown; Distance/Temp/Rating tiles are rejected.
- **Reject** everything social or financial in the references: feed, people, check-ins, reviews and stars, expenses
  and split bills, budget/currency step, multi-destination picker, flights, "Book this trip", weather stories.
- **Reject dark theme for the demo.** Keep the warm light tokens in `theme/colors.ts` (contrast already audited);
  dark mode is P2 and needs its own contrast pass.
- **One blocker to clear first:** the API does not tell the client a leg is estimated, and BRU-006 forbids showing
  straight-line estimates to travelers. The ≈ rail needs a recorded decision and a `Leg` field (see §4 P0-0, §5 Q1).

## 2. Reference review

| Image | Pattern shown | Verdict | Gonarra screen |
|---|---|---|---|
| `Unknown-9.jpg` | Wizard step 1: multi-destination list with search, "pick in visit order" | **Reject** (one city). Replace with a fixed destination card *Đà Nẵng · gồm cả Hội An* | SCR-022 wizard step 1 |
| `Unknown-8.jpg` | Range calendar (tap start, tap end) under a destination card with photo | **Adopt**, capped at 3 days | SCR-022 step 1 |
| `Unknown-7.jpg` | Who is going · pace · famous vs hidden gems · interests; coloured icon chips; "Optional, tap again to clear" | **Adapt**: pace + interests (exist). Who → open question Q2. Famous/hidden **reject** (no popularity data without ratings) | SCR-022 step 2 |
| `Unknown-6.jpg` | Food needs (vegetarian, halal…) + other prefs (no early starts, central walkable, nightlife, avoid crowds) + free text | **Mostly reject**: no dietary or crowd facts in the catalog, so the chip would promise what we cannot check. **Adapt** "No early starts" → `day_start_time` preset, free text → `request_text` | SCR-022 steps 2–3 |
| `Unknown-5.jpg` | Name & budget step; review cards with "Tap a section to change it"; Back / Create Trip footer | **Adapt**: optional name (`TripCreate.title`) + review cards. Budget/currency **reject** | SCR-022 step 4 |
| `Unknown-4.jpg` | "Your trip is ready" toast; cover photo with `dates · 3 days · 0 activity`; tabs; date chips; empty-day illustration | **Adopt** cover meta, date chips, empty-day state. **Adapt** toast copy to "ready — not saved yet". **Reject** Expenses/Notes/Memory tabs | SCR-024 |
| `Unknown-3.jpg` | "Spots in Hội An" / "Food & Drink" photo rails with + button, rating and km | **Adapt**: area and category rails, + adds to must-sees. **Reject** rating and km | SCR-008 Home sheet, SCR-021 Explore |
| `867713709…webp` | Cover hero, date chips, left rail with start/end times, km and mode icon for each leg | **Adopt** the rail (primary model for P0) | SCR-024 |
| `867162340…webp` | Same rail, light theme; category icon tile, address, user note, cost chip | **Adopt** rail and category tile. **Reject** cost chips and user notes (we show the labelled AI rationale instead) | SCR-024 |
| `870806627…webp` | Expenses, split, paid/unpaid | **Reject** (out of scope) | — |
| `Unknown-14.jpg` | Dark map home: labelled category pins, numbered route, filter chips (Friends/Events/Meetups), sheet with "Starts tomorrow" trip card | **Adapt**: labelled pin for the selected/zoomed place, upcoming-trip card (exists as `TodayCard`). **Reject** social chips and dark map | SCR-008 |
| `Unknown-13.jpg` | "Spots in Huế"/"Specialties" rails with bookmark, rating, address; floating "Map" pill | **Adapt** rails; floating Map pill on Explore (P1). **Reject** rating, bookmark (no saved-places feature) | SCR-021 |
| `Unknown-12.jpg`, `Unknown-2.jpg` | Social feed, people, reviews with star sub-scores, weather story cards | **Reject** | — |
| `Unknown-10.jpg`, `Unknown-11.jpg` | Profile with trips/check-ins/saved stats; FAB speed-dial (Check in, Join by code, Create itinerary) | **Reject** (check-in, sharing). Single "Plan a trip" entry already exists (`PlanBanner`) | — |
| `02-place-detail.png` | Hero with vertical thumbnail gallery, Distance/Temp/Rating tiles, description, price + CTA | **Adapt** gallery and tiles (Hours/Visit/Ticket). **Reject** temp, rating, price | SCR-033 |
| `03-travel-home-detail.png` | Hero with circular photo carousel, tag chips, rating, price, "Book this trip"; home with greeting, search, category grid | **Adapt** tag chips (category, area) and photo thumbs. **Reject** rating, price, booking CTA (handoff links only, trip-scoped) | SCR-033, SCR-008 |
| `04-map-discovery.png` | Map + sheet, search, "My spots"/lists tiles, "Near you" rail with km and rating | **Adapt** map + sheet (exists). **Reject** lists, ratings; "Near you" distance needs device location and is straight-line → P2 at most | SCR-008 |
| `06-ai-travel-marketing.png` | AI chat landing ("Ask anything") with capability cards; Explore sheet with For you / Things to do / Restaurants | **Adapt** Guide empty state with suggested-question chips. **Reject** flights/booking claims | SCR-034, SCR-021 |
| `07-welcome-collage.png` | Onboarding with stacked photo cards, step dots, Back + Get started | **Adapt** (P2): onboarding already has a mosaic; any photo must be Wikimedia with credit | SCR-002 |

## 3. Screen-by-screen gap analysis

### 3.1 Home (SCR-008) and Explore (SCR-021)

**Current.** Home is a map with a bottom sheet (`app/(tabs)/home.tsx`, `features/home/map/HomeMap.tsx`,
`features/home/sections/HomeSheetContent.tsx`): greeting, `PlanBanner`, `TodayCard`, `CategoryChips`, `SavedTrips`,
`ExplorePlaces` (160×200 photo tiles). Explore (`features/explore/ExploreScreen.tsx`) has search, category chips,
featured + grid/list (`components/PlaceCards.tsx`). `searchPlaces` in `lib/api/source.ts` takes `q` and
`category_code` but not `area_code`, although API-010 supports it.

**Target.** Below `CategoryChips`, two themed rails in the Vietdetour style: **Spots in Hội An** (`area_code` filter)
and **Food & drink** (`FOOD` + `CAFE`). Each card: photo or `PhotoFallback` illustration, name, `category · about n
min`, and a 44 pt **+** that adds the place to the planner draft's must-sees (`features/planner/input/draftStore.ts`,
max 10). No rating, no distance. Labelled pin bubble on the selected marker (P1). Floating "Map" pill on Explore (P1).

**Components.** `PlaceRail` (new, `features/home/sections/PlaceRail.tsx`, reuses `PhotoCard`/`SectionHeader`),
`AddToPlanButton` (new, in `components/ui/`), `searchPlaces(cityId, q, category, areaCode)` param.

| Key (`homeSheet.rails.*`) | VI | EN |
|---|---|---|
| `hoiAn.title` | Điểm đến ở Hội An | Spots in Hội An |
| `hoiAn.subtitle` | Địa điểm đã kiểm tra nguồn trong khu Hội An | Source-checked places in the Hội An area |
| `food.title` | Ăn uống | Food & drink |
| `food.subtitle` | Quán ăn và cà phê đã kiểm tra nguồn | Source-checked food and cafés |
| `seeAll` | Xem tất cả | See all |
| `meta` | {{category}} · khoảng {{count}} phút | {{category}} · about {{count}} min |
| `add.a11y` | Thêm {{name}} vào điểm muốn ghé | Add {{name}} to must-sees |
| `add.done` | Đã thêm vào chuyến đi sắp tạo | Added to your next plan |
| `add.full` | Đã đủ 10 điểm muốn ghé | You already have 10 must-sees |
| `empty` | Chưa có địa điểm nào ở đây | No places here yet |

### 3.2 Create-trip wizard (SCR-022)

**Current.** One long form (`features/planner/input/PlannerInputScreen.tsx`, `PlannerUI.tsx`, route `app/plan/new.tsx`)
with a Form/Describe segmented control, city tiles, native date picker, 1–3 day segmented, day hours, pace, interest
chips, travel modes, must-see picker (`MustSeePicker.tsx`), AI notice. Submit = `createTrip` (API-012) then
`PlanPreviewCreate` via `setPlanRequest`. `app/travel-preferences.tsx` stores profile interests and a profile-only
`travelType` (Solo/Couple/Family/Friends in `features/account/AccountContext.tsx`) that **is not sent** to the planner.

**Target.** Same screen, same draft store, split into 4 steps with a 4-segment progress bar under the header (as in
`Unknown-7/8.jpg`), sticky footer `Back` (secondary) + `Next` / `Create proposal` (primary). Describe mode stays as a
link on step 1 (*Hoặc mô tả bằng lời / Or describe it in words*) and keeps its clarification flow.

| Step | Vietdetour equivalent | Controls | Contract field | Status |
|---|---|---|---|---|
| 1 When | Destinations + dates | Fixed destination card (city photo + credit, *Đà Nẵng · gồm cả Hội An*); `RangeCalendar` (tap start, tap end, max 3 days, past disabled) | `TripCreate.city_id`, `start_date`, `day_count` (1–3) | Exists; calendar is new UI |
| 2 Style | Who / pace / interests | Pace chips (Thong thả / Vừa phải / Dày đặc); interest chips from `listCategories`; travel modes (Walk/Drive); day hours with preset chip *Không đi sớm* (sets start 09:30) | `preferences.pace`, `interest_category_codes`, `allowed_modes`, `day_start_time`, `day_end_time` | Exists |
| 3 Must-sees & notes | Food needs + "Anything else?" | Must-see list + picker; free-text note (500 chars, counter from 400); AI notice banner if not acknowledged | `preferences.must_see_place_ids`, `request_text` | Exists |
| 4 Review | Name & budget + review cards | Optional trip name; summary cards (When / Style / Must-sees) each tappable to jump back; Create | `TripCreate.title` | Field exists, not yet sent |
| — | Who is going, famous vs hidden, dietary, avoid crowds, budget, currency | Not shown | none | Rejected / Q2 |

Validation stays in `validateForm()`; a step's Next is disabled with the existing reason line until its required
fields are set (step 1 only). Under reduced motion, step changes do not slide.

**Components.** `WizardShell` (header ×/back, `StepProgress`, footer), `StepProgress` (4 segments, `accessibilityRole
="progressbar"`, value `current/total`), `RangeCalendar` (month grid, 44 pt cells, `accessibilityLabel` per day),
`DestinationCard`, `ReviewCard`. Reuse `Chip`, `Segmented`, `PickerField`, `MustSeePicker`, `Banner`.

| Key (`planner.wizard.*`) | VI | EN |
|---|---|---|
| `title` | Tạo lịch trình | Create itinerary |
| `step` | Bước {{current}}/{{total}} | Step {{current}} of {{total}} |
| `next` / `back` | Tiếp / Quay lại | Next / Back |
| `when.title` | Khi nào bạn đi? | When are you going? |
| `when.destination` | Đà Nẵng | Đà Nẵng |
| `when.destinationSub` | Gồm cả khu Hội An | Including the Hội An area |
| `when.hint` | Chạm ngày bắt đầu, rồi chạm ngày kết thúc. Tối đa 3 ngày. | Tap the start date, then the end date. Up to 3 days. |
| `when.max` | Chuyến đi tối đa 3 ngày. | Trips are up to 3 days. |
| `when.range` | {{start}} – {{end}} · {{count}} ngày | {{start}} – {{end}} · {{count}} days |
| `when.describe` | Hoặc mô tả bằng lời | Or describe it in words |
| `style.title` | Phong cách chuyến đi | Your travel style |
| `style.hint` | Không bắt buộc. Chạm lần nữa để bỏ chọn. | Optional. Tap again to clear. |
| `style.noEarly` | Không đi sớm (từ 9:30) | No early starts (from 9:30) |
| `notes.title` | Nơi muốn ghé và ghi chú | Must-sees and notes |
| `notes.placeholder` | Còn gì nữa không? Ví dụ: muốn ngắm hoàng hôn ở Hội An | Anything else? E.g. sunset in Hội An |
| `review.title` | Xem lại | Review |
| `review.hint` | Chạm vào một mục để sửa. | Tap a section to change it. |
| `review.name` | Tên chuyến đi (không bắt buộc) | Trip name (optional) |
| `review.namePlaceholder` | Đà Nẵng {{count}} ngày | {{count}} days in Đà Nẵng |
| `exit.title` | Rời khỏi đây? | Leave this screen? |
| `exit.body` | Lựa chọn của bạn vẫn được giữ trong phiên này. | Your choices are kept for this session. |

### 3.3 Generation progress (SCR-023)

**Current.** `features/planner/progress/GenerationProgressScreen.tsx`: stage list with icons (incl. optional
RESEARCHING / VERIFYING_WEB_PLACES), rotating status lines, slow notice, cancel, reassurance copy. Already stronger
than any reference.

**Target.** Keep. P1: a compact summary card at top (`dates · pace · n must-sees`) so the user sees what was asked.
P2: photo stack art from `07-welcome-collage.png` using credited Wikimedia city photos (respect reduced motion).

| Key | VI | EN |
|---|---|---|
| `planner.progress.summary` | {{dates}} · {{pace}} · {{count}} điểm muốn ghé | {{dates}} · {{pace}} · {{count}} must-sees |

### 3.4 Proposal / trip timeline (SCR-024)

**Current.** `app/plan/[previewId]/proposal.tsx` composes `ProposalHeader` (photo hero, city · dates eyebrow, days ·
stops meta, saved badge), `HealthActionCard`, a day section with `DayTabs` (segmented Day 1/2/3 + date) and an
embedded `ProposalMap`, then accordion `DayCard`s containing `StopCard` (64 pt thumb, number, time range, names,
conflicts, "Why this?" AI rationale, trust badge) joined by `LegRow` (dotted rail + pill `Walk · 2.1 km · 8 min`),
`HealthSummary`, `SaveBar`. `format.ts` and `LegRow.tsx` comments state values come from Google Routes.

**Target — left rail spec (from `867713709…webp`, `867162340…webp`).**

```
 ┌─ rail 64pt ─┐ ┌──────────── StopCard ─────────────┐
 │   08:30     │ │ [cat] 1  Ngũ Hành Sơn  ⓥ          │   time chip = planned_arrival (HH:mm, Asia/Ho_Chi_Minh)
 │     │       │ │ 08:30 – 10:00 · 90 phút           │
 │  ≈ 2,1 km   │ └───────────────────────────────────┘
 │   [car]     │   leg segment: mode icon (WALK=walk, DRIVE=car),
 │  ≈ 8 phút   │   ≈ distance, ≈ duration; solid line
 │     │       │
 │   10:08     │ ┌ next StopCard …
```

| Element | Rule |
|---|---|
| Rail width | 64 pt fixed column left of cards; cards keep `radii.card`, `colors.white`, `hairline` border |
| Time chip | `planned_arrival` as `HH:mm`; white pill, `fonts.bold` 13 pt, `colors.ink`; missing → `—` and stop a11y says time unknown |
| Leg segment | Vertical 2 pt line in `colors.mutedDot`; centred stack: `≈ {distance}` (12 pt bold, `deepOcean`), mode `Icon` 16 pt `tealText`, `≈ {duration}` |
| Estimated | When the leg is estimated (P0-0), prefix both values with `≈` and add "estimated" to the a11y label. A day with any estimated leg shows one notice line under the day chips |
| Unavailable | Dashed 2 pt `palette.error` line, mode icon in error colour, text *Không có tuyến đường / Route unavailable*, no numbers (unchanged rule) |
| WEB_UNVERIFIED stop | Rail time chip unchanged; card keeps `StopTrustBadge`; never hide it to save space |
| Touch | Rail is not interactive; the card stays the 44 pt+ target. Rail + card read as one a11y element per stop, one per leg |

**Target — header and days.** Cover meta line `Đà Nẵng · 16–18/01 · 3 ngày · 12 điểm dừng` (exists, re-order only).
Replace segmented `DayTabs` with **date chips** (`T6 16/01`, `T7 17/01`…) — horizontal pills, 44 pt high, selected =
`deepOcean` fill + white text, same `accessibilityRole="tab"`. Keep the accordion `DayCard` only for the saved,
read-only view; in preview, show the active day's stops flat under the chips (Vietdetour pattern). On first
`preview_ready`, show a toast: *ready — not saved yet* (Save stays explicit). Empty day: illustration + existing
empty copy + Add a stop.

**Components.** `TimeRail` + `RailLeg` (new, `features/planner/timeline/TimeRail.tsx`, replaces `LegRow` visuals;
keep `LegRow` export as a wrapper so call sites in `DayCard` change minimally), `DateChips` (new or rewrite of
`DayTabs.tsx`), `EstimateNotice` (new, small), `format.ts` gains `formatApprox()`.

| Key (`proposal.*`) | VI | EN |
|---|---|---|
| `leg.approx` | ≈ {{value}} | ≈ {{value}} |
| `leg.estimatedA11y` | {{mode}}, khoảng {{distance}}, khoảng {{duration}}, ước tính | {{mode}}, about {{distance}}, about {{duration}}, estimated |
| `leg.unavailableShort` | Không có tuyến đường | Route unavailable |
| `leg.estimateNotice` | Khoảng cách và thời gian di chuyển là ước tính theo đường thẳng, chưa đo theo đường thực tế. | Distances and travel times are estimated from straight lines, not measured on real roads. |
| `day.chip` | {{weekday}} {{date}} | {{weekday}} {{date}} |
| `day.chipA11y` | Ngày {{day}}, {{date}}, {{count}} điểm dừng | Day {{day}}, {{date}}, {{count}} stops |
| `ready.toast` | Đề xuất đã sẵn sàng — chưa lưu | Your proposal is ready — not saved yet |
| `cover.meta` | {{city}} · {{dates}} · {{days}} · {{stops}} | {{city}} · {{dates}} · {{days}} · {{stops}} |

### 3.5 Map (SCR-025)

**Current.** `features/planner/map/ProposalMap.tsx`: 260 pt card inside the scroll, Apple Maps on iOS, numbered pins
matching the timeline, straight `Polyline` connectors (no length label), dashed red for unavailable, legend, selected
stop strip with Previous/Next and Place card. Same revision as the timeline (FR-088).

**Target.** Keep. P0: add a legend line stating connectors are straight lines, not routes. P1: name bubble on the
selected pin (Vietdetour `Unknown-14.jpg`), expand button → full-screen map with the same selection. P2: day colour
per day when "all days" is shown.

| Key | VI | EN |
|---|---|---|
| `proposal.map.legendStraight` | Đường nối thẳng giữa các điểm, không phải lộ trình thực tế. | Lines join stops directly; they are not the actual route. |
| `proposal.map.expand` | Xem bản đồ toàn màn hình | Open full-screen map |

### 3.6 Place card (SCR-033)

**Current.** `features/place/PlaceScreen.tsx`: 380 pt `PhotoHero` (credit), names, horizontal quick tiles (Hours,
Visit, Ticket; `chưa rõ` when unknown), driver panel (`name_vi`, `address_vi`, source), facts list with `SourceLine`,
`UnknownBadge`, `StaleBadge`, description, horizontal media row with attribution captions, attributions section,
action bar Directions + Ask the Guide. Booking handoff exists only per trip (`features/handoff/*`, API-030).

**Target.** (a) **Hero gallery**: up to 4 thumbnail squares overlapping the hero's lower-right edge (`02-place-detail.png`);
tapping a thumb swaps the hero; the credit line always shows the **current** photo's `attribution_text` and licence.
No photo → `PhotoFallback` category illustration, no thumbs. (b) **Tag chips** under the title: category, area name
(e.g. *Hội An*), trust label (`VERIFIED` → *Đã kiểm tra nguồn / Source-checked*). (c) Tiles stay three, as equal-width
cards (`02` style) instead of a horizontal scroller. (d) Source/attribution line directly under the tiles: *Nguồn:
{publishers}* linking to the attributions section. (e) Booking links (P1): when opened from a saved trip stop, show
the existing `HandoffPanel` (`kinds=['ACTIVITY']`, `stopId`); from Explore, no booking section (Q5).

| Key (`place.*`) | VI | EN |
|---|---|---|
| `gallery.thumbA11y` | Ảnh {{index}}/{{total}} của {{name}} | Photo {{index}} of {{total}} of {{name}} |
| `gallery.credit` | Ảnh: {{credit}} ({{license}}) | Photo: {{credit}} ({{license}}) |
| `tags.verified` | Đã kiểm tra nguồn | Source-checked |
| `sources.line` | Nguồn: {{publishers}} | Sources: {{publishers}} |
| `booking.title` | Đặt trước (mở trang đối tác) | Book ahead (opens partner site) |

### 3.7 Guide (SCR-034)

**Current.** `features/guide/GuideScreen.tsx`, `GuideChat.tsx`, `components/GuideBubbles.tsx`: city/place scope row,
empty state with avatar, streamed answers with citations and trust labels, place picker.

**Target.** P1: three suggested-question chips in the empty state (`06-ai-travel-marketing.png` "Ask anything"), each
fills the input (does not auto-send, mirroring the voice rule). Answers keep citations and `WEB_UNVERIFIED` labels.

| Key (`guide.suggest.*`) | VI | EN |
|---|---|---|
| `title` | Bạn có thể hỏi | You could ask |
| `q1` | Vào phố cổ Hội An có cần mua vé không? | Do I need a ticket for Hội An Old Town? |
| `q2` | Nên thử món gì ở Đà Nẵng? | Which dishes should I try in Đà Nẵng? |
| `q3` | Chùa Linh Ứng Sơn Trà mở cửa lúc mấy giờ? | When does Linh Ứng Pagoda on Sơn Trà open? |

## 4. Prioritised implementation list

**P0 — iPhone demo, one mobile engineer, one pass.** File ownership is disjoint per item; P0-0 is the only non-mobile
item and must land first (or the rail ships without ≈ and keeps today's copy).

| ID | Item | Files (owner) | Size |
|---|---|---|---|
| P0-0 | **Estimate flag in the contract**: `Leg.measurement: "ROUTES" \| "ESTIMATE"` in `docs/04-design/api/openapi.yaml`, serializer in `apps/api`, regen `lib/api/schema.d.ts`; record the BRU-006 demo exception in `docs/decisions.md` (Q1) | API engineer + facilitator | S |
| P0-1 | Timeline left rail (`TimeRail`, `RailLeg`, ≈ formatting, estimate notice, a11y labels) | `features/planner/timeline/{TimeRail.tsx (new), LegRow.tsx, StopCard.tsx, DayCard.tsx, format.ts}`, `i18n/locales/{vi,en}/proposal.json` | M |
| P0-2 | Date chips + flat active-day list in preview + "ready — not saved" toast + cover meta order | `features/planner/timeline/{DayTabs.tsx, ProposalHeader.tsx}`, `app/plan/[previewId]/proposal.tsx` | S |
| P0-3 | Map straight-line legend | `features/planner/map/ProposalMap.tsx`, `proposal.json` | XS |
| P0-4 | Create-trip wizard (4 steps, `StepProgress`, `RangeCalendar`, review + optional title → `TripCreate.title`) | `features/planner/input/{PlannerInputScreen.tsx, PlannerUI.tsx, WizardSteps.tsx (new), RangeCalendar.tsx (new)}`, `i18n/locales/{vi,en}/planner.json` | L |
| P0-5 | "Spots in Hội An" + "Food & drink" rails on Home (no + button yet) | `features/home/sections/{PlaceRail.tsx (new), HomeSheetContent.tsx}`, `lib/api/source.ts` (`areaCode` param), `homeSheet.json` | S |
| P0-6 | Place hero gallery thumbs + per-photo credit + tag chips | `features/place/{PlaceScreen.tsx, components/HeroGallery.tsx (new)}`, `place.json` | M |

Order: P0-1 → P0-2 → P0-3 (timeline is the demo centrepiece), then P0-4, P0-5, P0-6. Cut P0-6, then P0-5, if late.
Checks per item: `npm run typecheck`; both locales open on device; VoiceOver pass on rail and wizard; Dynamic Type
at the largest size does not clip the rail (rail text wraps to two lines, column stays 64 pt).

**P1.** + on rails adds to must-sees · labelled selected pin + full-screen map · Explore rails + floating Map pill ·
progress summary card · place card booking (saved-stop scope) · Guide suggested chips · "Who is going" if Q2 is
approved.

**P2.** Dark theme (new token set + contrast audit) · onboarding photo collage · per-day map colours · "Near you"
(only if a foreground, on-device, ≈-labelled distance is approved).

## 5. Open questions for the owner

1. **≈ distances vs BRU-006.** BRU-006 says distances never come from a straight-line estimate, and the estimate
   provider refuses production. Do we record a demo-only exception (non-production builds, always ≈ + notice) and add
   `Leg.measurement` to the contract, or wait for Google Routes and drop the ≈ work?
2. **"Who is going" (solo / couple / family / with children / elderly).** Add an optional `party` field to
   `PlanningPreferences` (planner uses it for pace defaults only), or drop it? Today `travelType` lives only in the
   Clerk profile and is never sent.
3. **Hội An rail scope.** Which `area_code` values form "Hội An" for the rail (only `hoi-an-old-town`, or every
   Hội An area code used by the release gate)?
4. **Booking links on the place card outside a trip.** Keep them trip-scoped (current API-030), or allow an
   untargeted partner search link from Explore (needs an API change)?
5. **Theme.** Confirm the demo stays on the warm light theme (recommended) rather than the Vietdetour dark look.
