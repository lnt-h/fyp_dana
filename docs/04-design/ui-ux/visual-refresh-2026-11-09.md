# Visual refresh 2026-11-09: design reference

Status: Draft, implemented in `apps/mobile/src/theme/**` and `apps/mobile/src/components/ui/**` on `feat/ui-refresh`.
Owner request 2026-11-09: "The UI is boring, no colour", plus too much noise (needs-attention cards, AI labels, unknown
hours, repeated estimate notices). References: Wanderlog, Mindtrip, Airbnb. Supersedes the 2026-11-05 warm paper palette.

## 1. Look and feel

Bright and photo-first. White surfaces, near-black text, **one** brand colour (teal) for primary actions. Categories and
days carry the colour; photos and the map carry the rest. No beige or paper canvas. Sentence case everywhere.

## 2. Palette (`theme/colors.ts`)

Contrast is WCAG 2.1 against white (W) and surface (S). Text needs at least 4.5:1, icons and strokes at least 3:1.

| Token | Hex | Contrast | Use |
|---|---|---|---|
| canvas | `#FFFFFF` | — | page background |
| surface | `#F5F7F8` | — | grouped backgrounds, chips, skeletons, icon tiles |
| hairline | `#E5E8EB` | — | dividers (not card borders) |
| ink | `#16212B` | 16.3 W · 15.2 S | text |
| textSecondary | `#4A5562` | 7.6 W · 7.1 S | secondary text, kickers |
| textMuted | `#6B7480` | 4.74 W · 4.41 S | captions on white only |
| primary | `#0B7A75` | white on it 5.18 · 4.82 S · 4.59 on primarySoft | buttons, links, selected |
| primaryPressed | `#09625E` | 7.2 W | pressed primary |
| primarySoft | `#E6F4F3` | — | selected chip bg, soft fills |
| coral | `#E8553D` | white on it 3.62 | fills, FAB, highlights only (no small text) |
| coralText | `#C2412A` | 5.14 W · 4.49 on coralSoft | coral text (on white) |
| coralSoft | `#FDECE8` | — | soft coral fills |
| ai | `#6D28D9` | 7.1 W | **only** the sparkle mark |
| aiSoft | `#F3EEFE` | — | rare soft AI fill |
| success / successBg | `#15803D` / `#DCFCE7` | 4.57 | "Looks good" |
| warning / warningBg | `#92400E` / `#FEF3C7` | 6.37 | "N to check", "From the web" outline |
| danger / dangerBg | `#B91C1C` / `#FEE2E2` | 5.30 | "Needs changes", "Closed on Mon" |
| info / infoBg | `#1D4ED8` / `#DBEAFE` | 5.49 | neutral information |
| deepOcean, sun | `#0B3045`, `#F6A623` | — | brand mark only |

Legacy key names still work and map onto the palette: `surfaceTint` → surface, `accentText` → textSecondary,
`tealText`/`teal`/`audioTeal` → primary, `tealDark` → primaryPressed, `terracotta` → coral, `skyWash` → primarySoft,
`ok`/`okBg` → success, `warn`/`warnBg` → warning. New code should use the semantic names.

**Day colours** (`dayColors`, `dayColor(i)`): day 1 teal `#0B7A75`, day 2 coral `#E8553D`, day 3 indigo `#4F46E5`
(route lines, day chips; soft variants in `dayColorsSoft`). Numbered pins use `dayPinColors`, where day 2 is coralText
`#C2412A` so the small white number keeps 5.14:1. Timeline pins and map pins use the same colour per day.

**Category colours** (`categoryColors`, `categoryColor(code)`; unknown → primary). Always paired with the category icon,
tile = soft bg + strong icon. The strong colour is for icons only; category labels stay ink.

| Code | fg / bg | fg on bg | Code | fg / bg | fg on bg |
|---|---|---|---|---|---|
| HERITAGE | `#B45309` / `#FEF3C7` | 4.51 | BEACH | `#0284C7` / `#E0F2FE` | 3.57 |
| RELIGIOUS_SITE | `#7C3AED` / `#EDE9FE` | 4.80 | THEME_PARK | `#DB2777` / `#FCE7F3` | 3.91 |
| MUSEUM | `#2563EB` / `#DBEAFE` | 4.24 | FOOD | `#EA580C` / `#FFEDD5` | 3.11 |
| VIEWPOINT | `#0891B2` / `#CFFAFE` | 3.29 | CAFE | `#92400E` / `#FEF3C7` | 6.37 |
| NATURE | `#16A34A` / `#DCFCE7` | 3.00 | MARKET | `#CA8A04` / `#FEF9C3` | 2.74 (icon only, decorative) |
| NIGHTLIFE | `#9333EA` / `#F3E8FF` | 4.56 | CRAFT_VILLAGE | `#0D9488` / `#CCFBF1` | 3.32 |

## 3. Type (`theme/typography.ts`, Hanken Grotesk)

| Token | Size / line | Weight |
|---|---|---|
| display | 30 / 36 | bold |
| title | 24 / 30 | bold |
| headline | 19 / 25 | semibold |
| body | 16 / 24 | regular |
| bodyStrong | 16 / 24 | semibold |
| label | 15 / 20 | medium |
| caption | 13 / 18 | regular, textMuted |
| micro | 12 / 16 | medium, textMuted |
| eyebrow | 13 / 18 | semibold, textSecondary, **sentence case, no tracking** |

The uppercase kicker style is gone. `eyebrow` keeps its name for existing imports.

## 4. Shape and elevation (`theme/spacing.ts`, `theme/elevation.ts`)

- Radii: card 16, photoCard 16, photo (inside cards) 12, button 14, inset 12, iconTile 12, chip and pill 999, sheet 28.
- Cards have **no borders**. Elevation only for things floating over the map or a sheet: `elevation.floating`
  (y 4, blur 16, opacity 0.08). `sm`/`md`/`lg` remain for existing screens.
- 4-pt spacing scale; screen gutter 16–20. Buttons 52 tall; touch targets at least 44.

## 5. Components (`components/ui`)

| Component | Props (main) | Look |
|---|---|---|
| PrimaryButton | label, onPress, icon?, iconPosition?, loading?, disabled? | teal fill, white text, 52 tall, radius 14; one per screen |
| SecondaryButton | same | surface fill, ink text, no border |
| GhostButton | same | text-only in primary |
| Chip | label, icon?, selected?, onPress?, tone? (`default` / `tint` / `categoryColor(code)`) | pill, 40 tall; selected = primarySoft + primary text; category tone = soft bg + coloured icon |
| SectionHeader | title, subtitle?, actionLabel?, onAction? | 19 semibold sentence case; "See all" link in primary (`common.seeAll`) |
| PhotoCard / PhotoHero / PhotoFallback | image, fallbackCategory, fallbackName, … | no border; fallback = soft category gradient with a big category icon in the category colour (`tone="dark"` = strong category gradient, white glyph) |
| Skeleton | width, height, radius | surface with shimmer |
| AiMark | size? (14), decorative? | violet sparkle; a11y "Written by AI" / "Do AI viết" (`common.aiMark`) |
| StatusPill | tone (success, warning, danger, info, neutral), label, icon?, onPress? | soft bg + strong text, 32 tall, pill; chevron when pressable |
| CategoryBadge | code, label, variant (`tile` / `chip`), size? | tile = soft bg + coloured icon; chip = pill with icon + ink label |
| NumberPin | number, dayIndex?, size? (24 / 28), accessibilityLabel? | day-coloured circle, white bold number, white ring |
| DayDot | dayIndex, size? | small day-coloured dot |
| Toast | text, tone? (success, info, neutral), icon?, onDismiss? | ink pill, white text, polite live region; caller positions and times it |

## 6. Anti-noise rules (binding for the refresh)

1. Unknown facts are never shown as tiles, badges or rows on cards. The place screen shows only KNOWN facts as tiles;
   unknown ones are listed once, quietly, at the bottom of the facts section: "Not listed yet: hours, ticket price" /
   "Chưa có thông tin: giờ mở cửa, giá vé". Never invent values (unknown stays unknown).
2. No "Address unknown" and no "unknown" on list cards, rails, timeline stops, Today or the driver card: hide the row.
3. AI marking: `AiMark` (14–16 px) next to AI text. At most one explanatory line per screen ("Gonarra AI wrote these
   notes from the place descriptions." / "Ghi chú do Gonarra AI viết từ mô tả địa điểm."). No uppercase "AI
   SUGGESTION", no AI banner per item. "Summarised from sources" (DEC-025/028) stays as a small caption with the
   sparkle, once per section, tappable to the sources.
4. No "Source-checked" badges or kickers on Home, Explore, cards or hero. Sources live in the place screen's sources
   section only.
5. Estimates (DEC-023): keep "≈" before estimated distance and duration on legs, with a dashed connector. One legend
   line per proposal or day header ("≈ estimated travel times"). No repeated EstimateNotice, no per-stop INFO chips,
   no LEG_ESTIMATED in any visible health list.
6. Plan Health is one `StatusPill` in the proposal header: "Looks good" (success) / "N to check" (warning) / "Needs
   changes" (danger); VI "Ổn" / "N điểm cần xem" / "Cần chỉnh". Tapping opens the health detail. No big HealthSummary
   card in the proposal body and no "Warning · N warnings" badge.
7. Stops show a chip only for WARNING or BLOCKING conflicts that concern them (e.g. "Closed on Mon" in danger soft).
   No per-day "N warnings".
8. Health detail lists real problems first (BLOCKING, then WARNING) as compact rows: icon · localized title · stop
   name · "Go to stop". Unknown hours appear once as a quiet aggregated note: "Hours not listed for 6 stops — check
   before you go." / "Chưa có giờ mở cửa của 6 điểm — nên kiểm tra trước khi đi." Always localized from the conflict
   type on the client; never show the server's English `message`.
9. A `WEB_UNVERIFIED` stop gets a small outlined chip "From the web" / "Từ web" (warning outline), not a yellow card.
10. One primary button per screen. Save confirmation is a short `Toast`.

Plan Health severity (DEC-030, owner 2026-11-09): `OPENING_HOURS_UNKNOWN` becomes INFO; overall health counts only real
problems (WARNING or BLOCKING). `LEG_ESTIMATED` stays INFO. Calendar and closed-on-date rules are unchanged.
