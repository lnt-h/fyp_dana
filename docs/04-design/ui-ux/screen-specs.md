# Gonarra Screen Specifications

> **DEC-022 (2026-11-06):** curator review is removed. The curator admin (`apps/admin`), its screens SCR-101..SCR-105 and the
> wireframes `a01-candidate-queue.html`, `a02-place-review.html`, `a03-import-runs.html` are **withdrawn** (kept as history,
> IDs not reused). `VERIFIED` means "passed Gonarra's automated source checks"; traveler copy reads "Source-checked · <date>" /
> "Đã đối chiếu nguồn · <date>" and never claims human review (copy strings in this document updated accordingly). The
> binding sources are [decisions](../../decisions.md) (DEC-022), the [BRD](../../02-requirements/BRD.md) and the [PRD](../../03-analysis/PRD.md).

## Document control

| Field | Value |
|---|---|
| Document ID | GONARRA-UI-SCREENS |
| Title | Gonarra — detailed screen specifications (traveler app and curator admin) |
| Version / status | 0.2 / Draft |
| Date | 2026-11-05 |
| Owner | Lê Ngọc Tấn Hiền, student author, product owner, curator and engineer |
| Contributors | Claude Code (drafting agent; no approval authority) |
| Approver | trantrongminh, FYP mentor (full name and title pending OQ-001) — **[Pending]** |
| Companion to | [`README.md`](./README.md) (GONARRA-UIUX 0.2: design system §5–§6, states §8, flows §9, copy rules §10, accessibility §11); wireframes `wireframes/*.html` (viewer: `wireframes/index.html`) |
| Inputs | README §4 inventory; the 16 wireframes and their specification notes; `docs/04-design/api/api-contract.md` §3.2–§3.11 and `api/openapi.yaml` (operation IDs API-001..API-042, schema field names); `docs/03-analysis/user-stories.md` (US-001..US-043); as-built screens `apps/mobile/src/app/*.tsx` and `src/features/**` |
| Standard | IEEE 1016-2009 (user-interface view); WCAG 2.1 AA |
| Classification | Internal — FYP |

| Version | Date | Author | Change summary |
|---|---|---|---|
| 0.1 | 2026-11-05 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | First issue: one section per screen SCR-001..SCR-012, SCR-020..SCR-040, SCR-101..SCR-105 with purpose, route, layout, data, actions, states, validation, accessibility, flags and open points |
| 0.2 | 2026-11-05 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | Open points OQ-108..OQ-113 closed (SRC-100 A-029); SCR-025, SCR-102, SCR-104 use the new API 0.4.0 fields |

## Purpose and how to read this document

This document is the hand-off for visual design (Figma frames) and for the mobile and admin developers. Each screen
section is self-contained: a designer can build the frame from it without opening the API contract or the user
stories. It does not redesign the as-built screens SCR-001..SCR-007, SCR-009 and SCR-012 (README §4 "existing"); for
those it records what is built and the agreed additions only.

Conventions:

- **Screen IDs** `SCR-xxx` are the README §4 inventory. **Story and requirement IDs** `US-xxx`, `FR-xxx`, `NFR-xxx`
  are the PRD and user stories. **API IDs** `API-xxx` are the operations in `api-contract.md` §3.11; JSON field names
  are the `openapi.yaml` schema names (snake_case).
- **Viewports**: traveler app 390 pt portrait (also checked at 360 and 430); curator admin 1280 pt desktop (also
  1440). Every region is listed top to bottom in reading order, which is also the focus order unless stated.
- **Components** are the as-built ones in README §5.3 (`AuthShell`, `AccountShell`, `AccountRow`, `Action`,
  `Field`, `TextLink`, `HomeTabBar`, chips from `TravelPreferences`, Home sheet + handle) and the new ones in README
  §6.3 (`CityChip`, `CitySheet`, `SegmentedControl`, `Stepper`, `StopCard`, `LegRow`, `Badge`, `Banner`,
  `Sheet`/`AlertDialog`, `ChatBubble`, `SourceLine`, `Composer`, `VoiceSheet`, `Waveform`, `ReadAloudToggle`,
  `PartnerRow`, `PriceRow`, `StatusCard`, `ConfirmCheckbox`, `Skeleton`, admin `AdminShell`, `DataTable`,
  `FilterBar`, `KpiTile`, `EvidenceTable`, `PublishPanel`). Tokens are README §5.1 and §6.2 (`textMuted` #5E7585 and
  `tealText` #00788F for text).
- **Copy** is given as *vi-VN / en-US*, Vietnamese first, following README §10. Copy keys are i18next keys
  (`feature.key`). Fixed "honesty words" (README §10.8) are never paraphrased.
- **Formats** (apply everywhere): times are shown in `Asia/Ho_Chi_Minh` as 24-hour `HH:mm` (NFR-025, ASM-063);
  dates as `T7, 16/01/2027` (vi) / `Sat 16 Jan 2027` (en); durations as `60 phút` / `60 min`; distances `450 m` below
  1 km, else `4.6 km`; money `1.250.000 ₫` / `VND 1,250,000`. A fact with `knowledge_state = UNKNOWN` reads *chưa rõ /
  unknown*, never blank or zero (FR-006). A fact with `freshness = STALE` (verified more than 180 days ago, FR-007)
  carries the badge *Có thể đã cũ / May be out of date* next to its source line. Every source line reads
  `{publisher} · đối chiếu nguồn {verified_at}` / `{publisher} · source-checked {verified_at}`. Attribution text (`attribution_text`)
  is shown on every screen that shows that source's data (FR-008).

### Shared rules referenced by every screen

**S-1 Error codes → copy.** Every non-2xx response is the Gonarra envelope `{ error: { code, message, retryable,
request_id, context } }` (api-contract §3.4). The app maps `code` to localized copy and never shows provider text.
The `message` field is a safe fallback already localized by `locale`. Request IDs are shown only in the admin.

| HTTP / `code` | vi-VN | en-US | Behaviour |
|---|---|---|---|
| 401 `unauthenticated` | Phiên đăng nhập đã hết. Đăng nhập lại. | Your session ended. Sign in again. | Clear token, go to SCR-003; exception: deletion flow (SCR-038) treats it as completed after IN_PROGRESS |
| 403 `curator_role_required` | Tài khoản này không có vai trò biên tập viên | This account does not have the curator role | Admin only (SCR-102 permission state) |
| 403 `not_study_participant` | — | — | Background only (study events); never shown |
| 404 `not_found` | Không tìm thấy mục này | This item was not found | Place: "no longer available" copy (SCR-033); trip/preview: return to SCR-031 |
| 409 `revision_conflict` | Bản nháp đã thay đổi ở nơi khác | This draft changed elsewhere | Reload the resource; keep pending edit (SCR-024/027) or show conflict sheet (SCR-029) |
| 409 `idempotency_key_reused` | Yêu cầu không hợp lệ. Thử lại. | Invalid request. Try again. | New key, retry |
| 409 `idempotency_in_progress` | Đang xử lý yêu cầu trước… | Previous request still running… | Poll the resource; retry after `Retry-After` |
| 409 `plan_blocked` | Chưa thể lưu | This trip cannot be saved yet | SCR-029 refused state with `context.reasons` |
| 409 `trip_not_saved` | Lưu chuyến đi trước | Save the trip first | Handoff entry hidden on drafts; defensive only |
| 409 `deletion_in_progress` | Tài khoản đang được xoá | Your account is being deleted | Go to SCR-038 status |
| 410 `preview_expired` / `preview_closed` | Bản nháp đã hết hạn / đã đóng | This draft expired / is closed | Banner with *Tạo lại / Create again* (SCR-024) |
| 413 `payload_too_large` / 415 `unsupported_media_type` | Ảnh quá lớn hoặc sai định dạng | Photo too large or unsupported | SCR-036 retake |
| 422 `validation_failed` | Kiểm tra lại các trường được đánh dấu | Check the highlighted fields | `context.fields` → inline field errors |
| 422 `unsupported_request` | Chưa hỗ trợ yêu cầu này | This request is not supported yet | SCR-022 unsupported state |
| 422 `place_not_in_city` | Địa điểm không thuộc thành phố của chuyến đi | This place is not in the trip's city | SCR-028 refusal |
| 422 `publication_incomplete` | Chưa thể xuất bản — còn {n} mục | Cannot publish — {n} items left | SCR-103 lists `context.missing` |
| 429 `quota_exceeded` | Bạn đã dùng hết lượt hôm nay. Thử lại sau {time}. | You have used today's limit. Try again after {time}. | `context.resets_at`; action disabled until then |
| 500 `internal_error` | Có lỗi xảy ra. Thử lại. | Something went wrong. Try again. | Retryable |
| 503 `ai_unavailable` | Dịch vụ AI đang bận. Chuyến đã lưu của bạn không thay đổi. | The AI service is busy. Your saved trip is unchanged. | Request/edits kept (FR-043, FR-044) |
| 503 `route_unavailable` | Không tính lại được thời gian di chuyển | Could not recalculate travel times | Edits kept; Save stays disabled |
| 503 `runtime_place_unavailable` | — | — | Live-hours row hidden silently (NFR-011) |
| 503 `price_provider_unavailable` | Chưa lấy được giá tham khảo | Indicative prices are unavailable right now | Price section hidden with message |
| 503 `database_unavailable` | Dịch vụ tạm gián đoạn. Thử lại. | The service is briefly unavailable. Try again. | Retryable |
| 503 `feature_disabled` | — | — | Entry point hidden; never reached by a user |
| Network failure (no response) | Không có kết nối. Thử lại. | No connection. Try again. | Offline banner; retries safe when an `Idempotency-Key` was sent |

**S-2 Offline.** Saved trips (API-014 cached), their place cards (API-017 cached) and the last opened preview are
readable; search, planning, edits, Save, Guide, photo and handoffs are disabled with the reason *Bạn đang ngoại tuyến /
You are offline* (README §8).

**S-3 Guest gate.** A signed-out user may use SCR-002, SCR-003..SCR-007, SCR-008 (map and city), SCR-009, SCR-010 and
SCR-011 in session memory. Any tap on a private feature (search, Plan a trip, Trips, AI guide, place card, handoff,
preferences save) opens SCR-040 (OQ-061, A-027).

**S-4 Accessibility baseline (every screen).** Touch targets ≥ 44 × 44 pt; text contrast ≥ 4.5:1 using `textMuted` and
`tealText` for text (NFR-023); every interactive element has a label in the selected language (NFR-022); status is
conveyed by icon + word, never colour alone; sheets are modal dialogs that trap focus and return it to the opener;
polite live regions for progress and results, `alert` for errors (README §11); layouts reflow at 200 % system text
without truncating essential text (NFR-024); animations ≤ 220 ms and off under reduced motion (README §5.4).

**S-5 Feature flags (cut order DEC-003).** `FEATURE_STAY_PRICES` (cut 1st) hides the price section of SCR-037;
`FEATURE_PHOTO_ID` (2nd) hides the camera button in SCR-034 and SCR-036; `FEATURE_VOICE` (3rd) hides the mic in
SCR-008 and SCR-034 and SCR-035; `FEATURE_REGENERATION` (4th) hides Lock in SCR-027, the lock badge and SCR-030; iOS
build (5th) is a build profile, not a screen change. Flags reach the app through server configuration; a hidden entry
never shows a "coming soon" placeholder.

**S-6 Study timing (US-036, invisible).** For study accounts the app posts API-032 `POST /v1/study/timing-events`
with `event` REQUEST_SUBMITTED (SCR-022 Create proposal), FIRST_PROPOSAL_DISPLAYED (SCR-024 first render) and
SAVE_OUTCOME (SCR-029 result). No screen shows this; a 403 `not_study_participant` is swallowed.

---

## Part A — Traveler app, as-built screens (SCR-001..SCR-012)

### SCR-001 Splash

**Purpose and stories.** Session routing on launch (US-032 supporting; FR-068). Existing, not redesigned.

**Route, entry, exit.** Route `/` (`app/index.tsx`). Entry: cold start. Exit: `router.replace` to `/home` when Clerk
`isSignedIn`, else `/onboarding`; no back.

**Layout (top → bottom).** Full-bleed `deepOcean` background; centred `SplashLogo` 79 × 99 pt; `LoadingDots`
36 × 36 pt at bottom inset + 54 pt. Status bar light.

**Data shown.** None from the API.

**Actions.** None; routing happens when `isLoaded` becomes true.

**States.** Loading only. If Clerk fails to load within 10 s the screen shows *Không khởi động được. Kiểm tra kết nối /
Could not start. Check your connection* with *Thử lại / Try again* (to-be; not in the build).

**Validation and limits.** n/a.

**Accessibility.** Logo container labelled "Gonarra"; loading announced as busy.

**Flags.** None.

**Open points.** None.

### SCR-002 Onboarding (3 slides)

**Purpose and stories.** Introduce planning, map and AI picks (US-032 supporting). Existing; copy to be localized and
made city-neutral (OQ-060, A-027).

**Route, entry, exit.** Route `/onboarding`. Entry: SCR-001 when signed out. Exit: Skip or "Start your journey" →
`/welcome` (replace). Back button on slides 2–3 returns to the previous slide.

**Layout (top → bottom).** Header: `Wordmark` 133 pt (scaled from 440 × 956 design frame) left, Skip pill 88 × 40
right over a white top fade. Scene layer per slide: `OnboardingMosaic` (slide 1), `PlanningOnboardingScene` (2),
`PersonalizedOnboardingScene` (3). Slide title centred, 37 pt scaled, letter-spacing −1.35, bottom at design y 762.
Pagination dots (8 pt, active 28 × 8 `deepOcean`) at button bottom + 90. Footer row: Back 60 pt round (#B8C0C4) from
slide 2, Next/Start pill 60 pt high `ink` with arrow.

**Data shown.** Static copy only. To-be copy keys `onboarding.slide1..3`: *Khám phá câu chuyện địa phương, ở mọi điểm
dừng / Discover local stories at every stop*; *Ghim nơi bạn thích, xếp ngày của bạn / Pin what you love, plan your day*;
*Đi theo nhịp của bạn với gợi ý AI từ địa điểm đã đối chiếu nguồn / Flow at your rhythm with AI picks from source-checked places*.

**Actions.** Next → next slide (220 ms fade; 0 under reduced motion); Back → previous; Skip / Start → SCR-003.

**States.** Transition busy state disables the primary button (`accessibilityState.busy`).

**Validation and limits.** n/a.

**Accessibility.** Inactive slide layers hidden from assistive tech; dots labelled "Onboarding page n of 3"; buttons
have hint text.

**Flags.** None.

**Open points.** None.

### SCR-003 Welcome

**Purpose and stories.** Entry choice: sign up, sign in, social sign-in or continue as guest (US-032; FR-068).
Existing; copy city-neutral per OQ-060.

**Route, entry, exit.** Route `/welcome` (`app/(auth)/welcome.tsx`). Entry: SCR-002, sign-out, SCR-040 "Not now"
return path, deletion completed. Exit: Email → `/register`; "Sign in" → `/login`; Google/Apple → Clerk SSO → SCR-006;
"Explore without an account" → `/home` (replace). A signed-in user is redirected to `/home`.

**Layout (top → bottom).** `AuthShell` (gradient #D8F2FF → #F8FCFD, wave). `Wordmark` 176 pt + tagline "EXPLORE ·
PLAN · EXPERIENCE" (10 pt, tracking 2.6). Hero card 24 pt radius, height 20 % of screen (120–180 pt) with photo,
dark shade, eyebrow "VIETNAM", destination name 30 pt, sun accent bar; detail photo 96 × 120 pt bottom-right with
5 pt white border. Title 32/38 bold (28/34 compact < 750 pt): *Hành trình Việt Nam của bạn bắt đầu từ đây. / Your
Vietnam story starts here.* Subtitle 16/24 `textMuted`. `Action` primary "Sign up with Email" with email icon;
`SocialActions` (Google, Apple, secondary). Footer: "Already have an account? Sign in" (48 pt row) and `TextLink`
"Explore without an account →".

**Data shown.** None from the API.

**Actions.** See exits. Social buttons disabled while `busy || !isLoaded`; SSO errors appear as a polite inline notice.

**States.** Loading (Clerk not loaded: social disabled); error (inline notice from `authErrorMessage`).

**Validation and limits.** n/a.

**Accessibility.** Hero is decorative (`aria-hidden`); title has header role; sign-in link labelled in full.

**Flags.** None.

**Open points.** The hero photo set is Đà Nẵng only; replace with a five-city or neutral image before the study
(OQ-068 rights also apply).

### SCR-004 Sign in (email, code, reset)

**Purpose and stories.** Clerk email + password sign-in with email code / TOTP second factor and password reset
(US-032; FR-068). Existing.

**Route, entry, exit.** Route `/login`. Entry: SCR-003, SCR-005 link, SCR-040. Exit: success → `finishAuth` →
`/home` (or `/auth-task` when Clerk has a pending task); "Sign up" → `/register` (replace); guest link → `/home`.
Back → previous or `/welcome`.

**Layout (top → bottom).** `AuthShell` with back. `BrandSymbol` 64 × 76. `Heading` (title/subtitle per step:
password "Welcome back"; email-code/TOTP "Verify your identity"; new-password "Choose a new password"). Fields per
step: Email (`Field`, email keyboard) and Password (reveal 44 pt) on the password step; Verification code
(number pad, one-time-code) on code steps; New password on reset. Right-aligned `TextLink` "Forgot password?" (password
step). Polite error text. `Action` primary (label "Sign in" / "Verify" / "Update password"; "Please wait…" while
busy). `TextLink`s: "Resend code" (code steps), "Start again" (non-password steps), `SocialActions` with divider +
"Don't have an account? Sign up" (password step), "Explore without an account →".

**Data shown.** None from the Gonarra API (Clerk SDK only).

**Actions.** Submit per step (Enter on the last field submits); Forgot password → reset-code step; Resend; Start again
resets the Clerk sign-in; social SSO.

**States.** Busy (all inputs `editable=false`, action label "Please wait…"); error (inline, `authErrorMessage`);
unsupported second factor → notice "This account requires a verification method that is not supported here yet."

**Validation and limits.** Email and password required ("Enter your email address and password."); code required.
Password rules are Clerk's.

**Accessibility.** Each `Field` passes its label as `accessibilityLabel`; error text is a polite live region; password
reveal button labelled Show/Hide password.

**Flags.** None.

**Open points.** Copy is English-only in the build; move to i18next (OQ-060, TASK-012).

### SCR-005 Register (account, email code)

**Purpose and stories.** Create a Clerk account with name, email and password, verify by email code (US-032; FR-068).
Existing.

**Route, entry, exit.** Route `/register`. Entry: SCR-003, SCR-004 link, SCR-009/SCR-012 "Create an account",
SCR-040. Exit: success → `authDestination('/travel-preferences')` (SCR-011) or `/auth-task`; "Sign in" → `/login`.

**Layout (top → bottom).** `AuthShell` with back. `BrandSymbol`. `Heading` ("Create your Gonarra account" /
subtitle *Bắt đầu khám phá Việt Nam theo cách của bạn / Start exploring Vietnam your way*; verifying: "Check your
email" / "Enter the code sent to {email}."). Fields: Full name, Email address, Password (+ note "Use at least 15
characters for your password."), or Verification code when verifying. Hidden `clerk-captcha` view. Error text. `Action`
"Create account" / "Verify email". Verifying: `TextLink`s "Resend code", "Use a different email"; otherwise
`SocialActions` with divider. `TextLink` "Already have an account? Sign in".

**Data shown.** None from the Gonarra API.

**Actions.** Create account → Clerk `signUp.password` → send email code → verifying step; Verify → `verifyEmailCode` →
finalize; social SSO.

**States.** Busy; error inline; "missing requirements" notice when Clerk needs more data.

**Validation and limits.** Name, email and password required; name split into first/last on whitespace; Clerk password
policy (15+ characters recommended).

**Accessibility.** As SCR-004.

**Flags.** None.

**Open points.** Subtitle copy says "Da Nang" in the build (OQ-060).

### SCR-006 SSO callback

**Purpose and stories.** Completes a browser OAuth session (US-032; FR-068). Existing.

**Route, entry, exit.** Route `/sso-callback`. Entry: Clerk redirect. Exit: `Redirect` to `/home` once signed in.

**Layout.** Centred `ActivityIndicator` labelled "Completing sign-in" and text *Đang hoàn tất đăng nhập. Bạn có thể quay
lại ứng dụng. / Completing sign-in. You can return to the app.*

**Data / Actions.** None. **States.** Loading only. **Validation.** n/a. **Accessibility.** Indicator labelled.
**Flags.** None. **Open points.** None.

### SCR-007 Auth task (unsupported Clerk step)

**Purpose and stories.** Shown when a Clerk session has a `currentTask` the app cannot complete (US-032; FR-068).
Existing.

**Route, entry, exit.** Route `/auth-task`; guarded by `Stack.Protected` when `session.currentTask` exists. Exit:
"Sign out and return" → `/welcome`.

**Layout.** `AuthShell`; `Heading` "One more step is needed" with explanation; error text; `Action` "Sign out and
return".

**Data / Actions.** Clerk `signOut`. **States.** Busy; error "Could not sign out. Please try again."
**Validation.** n/a. **Accessibility.** Error is a polite live region. **Flags.** None. **Open points.** None.

### SCR-008 Home (to-be)

**Purpose and stories.** Entry hub: current city, search, map, plan a trip, saved trips (US-001, US-003, US-024
entry; FR-001, FR-004). Built layout kept; city button, sheet content and removals added (A-027).

**Route, entry, exit.** Route `/home` (`app/home.tsx`), Home tab. Entry: SCR-001/SCR-003/SCR-004/SCR-006 success,
Home tab. Exit: avatar → SCR-009; city button → SCR-020; search pill → SCR-021 (typing); mic → SCR-035 (flag);
"Plan a trip" → SCR-022 (guest → SCR-040); saved trip row → SCR-024 (saved view) or SCR-031 for the full list; tab
bar → Explore (SCR-021), AI guide (SCR-034), Trips (SCR-031). No back (root).

**Layout (top → bottom, 390 pt, scaled from the 440 × 956 design frame).** `HomeMapBackdrop` 458 pt tall.
`Wordmark` 128 pt at (20, 84). **City button** (replaces the static location line at (20, 148)): pin icon + `{city
name}, Việt Nam / Viet Nam` + chevron; 44 pt tall hit area. Avatar 52 pt round at top-right (initial letter or person
icon). The Notifications bell and the weather readout are **removed** (OQ-063). Search pill 408 × 52, radius 26,
border #A9D6DE, icon + placeholder + `AudioMark` 40 pt mic (hidden when `FEATURE_VOICE` off). Map markers (decorative in
the build; to-be: published places of the city with `thumbnail`, label `deepOcean`). GPS button 48 pt (centres on the
device location; foreground, one-shot, optional). Bottom sheet from y 441, radius 40, handle 68 × 4 #C9C9C9, content:
**Plan card** (sparkle icon, *Lên kế hoạch 1–3 ngày ở {city} / Plan 1–3 days in {city}*, subtitle *Chỉ dùng địa
điểm đã đối chiếu nguồn / Built only from source-checked places*, `Action` primary *Lên kế hoạch chuyến đi / Plan a trip*),
**Saved trips** section cap + up to 3 `AccountRow`s (icon trips; title `{city} · {day_count} ngày/days`; subtitle date
range; chevron) + `TextLink` *Xem tất cả / See all* when more exist. `HomeTabBar` 328 × 80 floating at y 842.

**Data shown.**

| Field | Source | Format |
|---|---|---|
| Current city name | API-008 `items[].name_vi` / `name_en` by `locale`; selection persisted on device and in `Preferences` (no field yet, see open points) | Default: device locale city not inferred; first launch shows SCR-020 |
| Map markers | API-010 `items[]` (`name`, `location`, `thumbnail.url`, `thumbnail.attribution_text`) with `city_id`, no `q`, `limit` 20 | Attribution shown in the map corner (FR-008) |
| Saved trips | API-013 `items[]` (`city_id` → city name, `day_count`, `start_date`, `status = SAVED`), `sort=-updated_at`, `limit` 3 | `Hội An · 2 ngày`, `T7 16/01 – CN 17/01/2027` |

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Tap city button | — | SCR-020 sheet |
| Tap search pill / type | API-010 `GET /v1/places?city_id&q` after 300 ms debounce (guest → SCR-040) | SCR-021 results in the sheet |
| Tap mic | — | SCR-035 (flag `FEATURE_VOICE`) |
| Tap Plan a trip | — | SCR-022 (guest → SCR-040) |
| Tap saved trip | API-014 `GET /v1/trips/{trip_id}` | SCR-024 in saved (read) mode |
| Tap GPS | device location (foreground) | Map recentres; no API call; no permission at app start |
| Tap avatar | — | SCR-009 |

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | Map backdrop shown immediately; saved-trip rows as 2 skeleton rows | — |
| Empty (no saved trips) | Plan card only; section cap hidden | — |
| Guest | Plan card visible; Saved trips replaced by one line *Đăng nhập để xem chuyến đi đã lưu / Sign in to see saved trips* (tap → SCR-040) | — |
| Error (trips) | Inline banner in the sheet, map usable | Không tải được chuyến đi. Thử lại / Could not load trips. Try again |
| Offline | Banner at the top of the sheet; search and Plan disabled; saved trips from cache | Bạn đang ngoại tuyến. Tìm kiếm và lập kế hoạch cần kết nối. Chuyến đã lưu vẫn mở được. / You are offline. Search and planning need a connection. Saved trips still open. |
| Blocked | Private actions → SCR-040 | — |

**Validation and limits.** City is one of the 5 launch cities (API-008 list is authoritative, never hard-coded).

**Accessibility.** Search pill labelled *Tìm địa điểm ở {city} / Search places in {city}*; city button labelled
*Thành phố hiện tại: {city}. Đổi thành phố / Current city: {city}. Change city*; tab bar is `Primary navigation` with
`tab` roles and `selected` state; markers labelled by place name.

**Flags.** `FEATURE_VOICE` hides the mic.

**Open points.** None. OQ-108 closed: the selected city stays device-local (no contract change).

### SCR-009 Profile

**Purpose and stories.** Account overview and entry to preferences and settings (US-011 entry; FR-073). Existing.

**Route, entry, exit.** Route `/profile`. Entry: Home avatar. Exit: Edit profile → SCR-012; Create an account →
SCR-005 (guest); Travel preferences → SCR-011; Settings → SCR-010; back → `/home`.

**Layout (top → bottom).** `AccountShell` title "Profile" (fallback `/home`). Card: gradient cover (#DBF3F5 →
#EDF7FD) with kicker "YOUR NEXT CHAPTER" and cover title; identity block with 60 pt avatar (initials), badge "YOUR
ACCOUNT" / "EXPLORER", name (28/34), email or guest copy, `Action` "Edit profile" (secondary) or "Create an account".
Section cap "YOUR WAY TO EXPLORE": `AccountRow` Travel preferences (subtitle = interests joined by " · ") + travel-type
tag (#FFF5E4/#845717). Section cap "MAKE YOURSELF AT HOME": `AccountRow` Settings. Footer note.

**Data shown.** Clerk user (`fullName`, primary email, `unsafeMetadata.interests`, `travelType`). To-be: after
TASK-001 the name/email remain from Clerk; preferences come from API-004 (`pace`, `interest_category_codes`).

**Actions.** As exits. **States.** Guest variant as built. **Validation.** n/a.

**Accessibility.** Rows are buttons with title + subtitle in one label.

**Flags.** None. **Open points.** Copy "Your Da Nang story is just beginning." → city-neutral (OQ-060).

### SCR-010 Settings (to-be additions)

**Purpose and stories.** Accessibility, personalization, privacy, language, AI data notice, account deletion,
session (US-033, US-034, US-035; FR-071, FR-074, FR-075). Built layout kept; rows added (wireframe m13 frame 1).

**Route, entry, exit.** Route `/settings`. Entry: SCR-009. Exit: Travel preferences → SCR-011; Language → SCR-039;
What is sent to AI → in-place expandable text (no new screen); Delete account → SCR-038; Sign out → `/welcome`.

**Layout (top → bottom).** `AccountShell` "Settings". Title *Cảm thấy như ở nhà. / Feel at home.* + body. Section
**ACCESSIBILITY**: `AccountRow` Reduce motion with `Switch`. Section **PERSONALIZATION**: Travel preferences row.
**New section LANGUAGE / NGÔN NGỮ**: `AccountRow` icon "文", title *Ngôn ngữ ứng dụng / App language*, subtitle current
language, chevron → SCR-039. Section **PRIVACY & ABOUT**: `AccountRow` **What is sent to AI** (`shield`, expandable:
the FR-074 notice text, see SCR-022), Your data (expandable; the sentence "Account deletion is not available in this
app yet" is **removed**), Terms & privacy, About Gonarra (version). **New row** `AccountRow` icon "✕" (error colour)
*Xoá tài khoản / Delete account*, subtitle *Xoá chuyến đi, sở thích và câu hỏi của bạn / Delete your trips, preferences
and questions* → SCR-038 (hidden for guests). Section **THIS SESSION**: Sign out / Reset guest session with inline
confirmation (as built).

**Data shown.** Reduce-motion value (account context); language from `Preferences.locale` (API-004) or device
default; app version from `expo-constants`.

**Actions.** Switch → local state; Sign out → Clerk `signOut` + clear state → `/welcome`; other rows as exits.

**States.** Busy "Please wait…" on sign-out; error "Could not end the session. Please try again."; guest hides
Delete account and shows Reset guest session.

**Validation.** n/a.

**Accessibility.** Switch labelled "Reduce motion"; expandable rows announce expanded state; Delete account row uses
the error text token with icon + word.

**Flags.** None.

**Open points.** None.

### SCR-011 Travel preferences (to-be additions)

**Purpose and stories.** Save pace, interests, travel modes (and the built travel type) for prefilling the planner
(US-011; FR-073, FR-096). Built tiles and chips kept; Pace and Travel modes added (OQ-065, A-027).

**Route, entry, exit.** Route `/travel-preferences`. Entry: SCR-009, SCR-010, SCR-005 completion. Exit: Save or
Cancel → back (or `/profile`).

**Layout (top → bottom).** `AccountShell` "Travel preferences". Body line. **I'm interested in** (checkbox image tiles
2 × 2: Culture, Beach, Food, Nature — to-be: categories from API-009 `items[].name` with `code`). **New: Pace /
Nhịp độ** radio chips *Thong thả / Relaxed*, *Vừa phải / Balanced*, *Dày đặc / Packed*. **New: Travel modes / Di
chuyển** checkbox chips *Đi bộ / Walk*, *Đi xe / Drive* (at least one). **Travel type** radio chips Solo, Couple,
Family, Friends (profile data, not sent to the planner). Error text. `Action` *Lưu sở thích / Save preferences*
("Saving…" busy). `TextLink` *Huỷ / Cancel*.

**Data shown.**

| Field | Source |
|---|---|
| Interests | API-004 `interest_category_codes[]` ↔ API-009 categories; built: Clerk `unsafeMetadata.interests` |
| Pace | API-004 `pace` (RELAXED, BALANCED, PACKED, null) |
| Travel modes | API-004 `allowed_modes[]` (WALK, DRIVE) |
| Travel type | Clerk `unsafeMetadata.travelType` (unchanged) |

**Actions.** Save → API-005 `PUT /v1/me/preferences` (full replace: `locale`, `pace`, `interest_category_codes`,
`allowed_modes`, `day_start_time`, `day_end_time`, `ai_notice_acknowledged`) + Clerk metadata for travel type; guest →
session memory only (and SCR-040 on save).

**States.** Loading (prefill from API-004); busy; error inline (S-1); offline: Save disabled with reason.

**Validation and limits.** `allowed_modes` ≥ 1 (*Chọn ít nhất một cách di chuyển / Choose at least one travel mode*);
`interest_category_codes` ≤ 20.

**Accessibility.** Tiles are `checkbox`, chips `radio`/`checkbox` with `checked` state (as built).

**Flags.** None.

**Open points.** None.

### SCR-012 Edit profile

**Purpose and stories.** Change display name (US-011 supporting). Existing.

**Route, entry, exit.** Route `/edit-profile` (signed-in only, `Stack.Protected`). Entry: SCR-009. Exit: Save or
Cancel → back.

**Layout.** `AccountShell` "Edit profile"; card with `Field` Full name, email as read-only body text + note, error
text, `Action` "Save changes", `TextLink` "Cancel". Guest: `Action` "Create an account".

**Data shown.** Clerk `fullName`, primary email. **Actions.** Save → Clerk `user.update`.
**States.** Busy; error inline. **Validation.** Name required ("Enter your name."). **Accessibility.** As SCR-004.
**Flags.** None. **Open points.** None.

---

## Part B — Traveler app, new screens (SCR-020..SCR-040)

### SCR-020 City choice sheet

**Purpose and stories.** Choose one of the five launch cities; scopes search, planning and the Guide (US-001, US-012
AC3; FR-001, FR-023). Wireframe m01.

**Route, entry, exit.** Sheet over SCR-008 (also from SCR-021 empty state "Change city" and SCR-022 unsupported
state). Entry: city button. Exit: Done or swipe down → back to the opener with the selection applied; focus returns to
the city button.

**Layout (top → bottom).** Home sheet (radius 40, handle). Title *Chọn thành phố / Choose a city* (20 bold).
Subtitle *Gonarra hỗ trợ 5 thành phố. Mỗi chuyến đi ở một thành phố. / Gonarra covers 5 cities. Each trip covers one
city.* Radio list of 5 `AccountRow`-style rows: icon tile with the first letter, primary name in UI language, secondary
other-language name in `textMuted` (e.g. *Hà Nội (Hanoi)* in en), check mark on the selected row. `Action` primary
*Xong / Done*.

**Data shown.** API-008 `GET /v1/cities` → `items[].id`, `code`, `name_vi`, `name_en`, `time_zone`; order as
returned (Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Hội An, Huế).

**Actions.** Tap row → selection (radio); Done → persist `city_id` on device; SCR-008 reloads markers and saved-trips
context.

**States.** Loading: 5 skeleton rows; error: *Không tải được danh sách thành phố. Thử lại / Could not load cities.
Try again*; offline: last cached list.

**Validation and limits.** Exactly one city; list never hard-coded.

**Accessibility.** `dialog` with heading; rows are `radio` in a `radiogroup`; Done ≥ 56 pt.

**Flags.** None. **Open points.** None (OQ-108 closed: city is device-local).

### SCR-021 Search results / Explore

**Purpose and stories.** Find a published place of the current city by Vietnamese name, English name or alias, with
or without diacritics (US-001, US-003; FR-001, FR-002, FR-004). Wireframe m01.

**Route, entry, exit.** Home sheet (typing in the search pill) and the Explore tab (same content, full-height list).
Entry: SCR-008 search, Explore tab. Exit: tap result → SCR-033; "Change city" → SCR-020; clear → SCR-008 sheet.

**Layout (top → bottom).** Search pill stays at the top (query editable, clear button 44 pt). Result count line
`{n} kết quả ở {city} / {n} results in {city}` (`role=status`). Result rows (`AccountRow` layout): category glyph
tile, primary `name` (UI language), secondary `name_vi` or `name_en` (the other language) + ` · {category}`; chevron.
Explore tab adds a category chip row (API-009) above the list and `HomeTabBar` below.

**Data shown.**

| Field | Source | Format |
|---|---|---|
| Results | API-010 `GET /v1/places?city_id={id}&q={query}&locale={vi\|en}&limit=20` (`category_code` filter on Explore) → `items[].id`, `name`, `name_vi`, `category_code`, `short_description`, `thumbnail` | Primary/secondary name per README §10.3 |
| Categories | API-009 `items[].code`, `name_vi`/`name_en` | Chips |
| Paging | `next_cursor` | "Load more" row |

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Type (≥ 1 char, 300 ms debounce) | API-010 | List replaced; previous results stay visible while loading |
| Tap result | — | SCR-033 (`place_id`) |
| Tap category chip | API-010 with `category_code` | Filtered list |
| Tap "Change city" (empty) | — | SCR-020 |
| Load more | API-010 with `cursor` | Appended |

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | 3 skeleton rows; status *Đang tìm… / Searching…* | — |
| Empty | `EmptyState` card with search glyph, title, body and `Action` secondary | Không tìm thấy "{q}" ở {city} / No match for "{q}" in {city} · Gonarra chỉ hiển thị địa điểm đã đối chiếu nguồn của thành phố đang chọn. Thử tên tiếng Việt, tên tiếng Anh, hoặc đổi thành phố. / Gonarra only shows source-checked places in the selected city. Try the Vietnamese or English name, or change city. · Đổi thành phố / Change city |
| Error | Banner, map usable | Không tìm được lúc này. Thử lại / Search is unavailable right now. Try again |
| Offline | Banner; input disabled | S-2 |
| Blocked (guest) | SCR-040 on first keystroke | — |

**Validation and limits.** `q` 1–120 characters; results ≤ 20 per page; target in first 5 (AC-001).

**Accessibility.** Result count announced politely; rows labelled `{name}, {other name}, {category}`; long names wrap
to 2 lines (no truncation).

**Flags.** None. **Open points.** None.

### SCR-022 Planner input (form, text, clarify, refuse)

**Purpose and stories.** Describe a 1–3 day single-city trip by structured form or free text; answer clarifications;
see refusals; first-use AI notice (US-010, US-011, US-012, US-038, US-035; FR-020..FR-023, FR-070, FR-073, FR-074,
FR-085, FR-086). Wireframe m02.

**Route, entry, exit.** Route `/plan/new`. Entry: SCR-008 Plan a trip, SCR-031 "New trip". Exit: Create proposal →
SCR-023; back → SCR-008 (draft input kept in memory for the session).

**Layout (top → bottom).** `AccountShell` header *Chuyến đi mới / New trip*. `SegmentedControl` **Biểu mẫu / Form**
· **Mô tả bằng lời / Describe in words** (structured form always available, DC-005). Prefill note *Đã điền sẵn từ sở
thích đã lưu / Prefilled from your saved preferences* when API-004 returned values.

*Form view:* City chips (5, radio, from API-008; preselected = Home city). Start date `Field` (date picker; shows
`T7, 16/01/2027`). Days `Stepper` 1–3. Daily hours: two `LocalTime` pickers *08:30 – 18:00*. Pace radio chips.
Interests checkbox chips (API-009). Travel modes checkbox chips Walk/Drive. Must-see places (optional): `＋ Thêm địa
điểm ở {city} / Add a place in {city}` → SCR-028 in picker mode (max 10, removable chips). Checkbox *Lưu nhịp độ và sở
thích cho lần sau / Save pace and interests for next time*. Sticky `Action` primary *Tạo đề xuất / Create proposal*.

*Describe view:* `ChatBubble`-style prompt *Bạn muốn chuyến đi thế nào? / What kind of trip do you want?*; multiline
`Field` (placeholder example *"3 ngày ở Hà Nội, đi chậm, thích ẩm thực" / "3 slow days in Hanoi, street food"*), hint
line with the switch-to-form reminder, character counter from 400 of 500; **AI notice `Banner`** (first use only):
*Gửi gì tới AI? Nội dung yêu cầu được gửi tới dịch vụ AI bên ngoài (Google Gemini). Tài khoản, liên hệ và vị trí
chính xác của bạn thì không. / What is sent to AI? Your request text goes to an external AI service (Google Gemini).
Your account, contact details and precise location do not.* + link *Tìm hiểu thêm / Learn more* (opens SCR-010 row).
`Action` *Tiếp tục / Continue* (acknowledges the notice, then submits).

*Clarification view (same route):* the request text echoed as a bubble; question *Bạn bắt đầu chuyến đi ngày nào? /
Which day does your trip start?* (or city / number of days); the missing field only; line *Đã hiểu: {city} · {n} ngày ·
{interests} / Understood: …*; `Action` *Tạo đề xuất / Create proposal* disabled with reason until filled.

*Unsupported view:* `Banner` warning *Chưa hỗ trợ yêu cầu này. Mỗi chuyến đi dài 1–3 ngày và ở một thành phố: Hà Nội,
TP.HCM, Đà Nẵng, Hội An hoặc Huế. / This request is not supported yet. A trip is 1–3 days in one city: …*; city chips to
pick one; `Action` secondary *Sửa yêu cầu / Edit request*.

**Data shown.**

| Field | Source |
|---|---|
| Cities, categories | API-008, API-009 |
| Prefill | API-004 `pace`, `interest_category_codes`, `allowed_modes`, `day_start_time`, `day_end_time`, `ai_notice_acknowledged_at` (null → show notice) |
| Must-see chips | API-010 results chosen in SCR-028 (`id`, `name`) |
| Clarification | API-018 stream event `clarification_required` → `clarification.missing_fields[]` (city, start_date, day_count), `clarification.message` |

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Create proposal / Continue | 1) API-012 `POST /v1/trips` `{city_id, start_date, day_count}` + `Idempotency-Key` (201 → `trip.id`, `revision` 0); 2) API-018 `POST /v1/trips/{trip_id}/plan-previews` `Accept: text/event-stream`, body `{source: GENERATE, expected_trip_revision, locale, request_text?, preferences{...}}` + `Idempotency-Key`; study accounts also API-032 REQUEST_SUBMITTED | SCR-023 |
| Continue on the AI notice | API-005 with `ai_notice_acknowledged: true` (merged with current preferences) | Notice not shown again |
| Save preferences checkbox | API-005 after a successful request | Prefill next time (US-011) |
| Pick a city on the unsupported view | — | Returns to the form with the city set |
| Edit request | — | Describe view with text kept |

In the Describe view with no date or days in the text, the app does **not** guess: it sends `request_text` and lets the
server answer `clarification_required` (FR-022). A 4-day or two-city request is refused by the server with 422
`unsupported_request` → unsupported view (0 AI calls, FR-023).

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | SCR-023 | — |
| Empty (Describe) | Continue disabled with hint | Mô tả chuyến đi hoặc dùng Biểu mẫu / Describe your trip or use the form |
| Error | SCR-023 error, or inline field errors (`validation_failed` → `context.fields`) | S-1 |
| Offline | Banner; Create proposal disabled with reason | S-2 |
| Blocked | Guest → SCR-040; 429 `quota_exceeded` → banner with `resets_at` | S-1 |

**Validation and limits.** `day_count` 1..3; `start_date` today or later (client) — server is authoritative;
`day_end_time` > `day_start_time`; `request_text` ≤ 500 characters in the UI (ASM-060; contract allows 1000);
`must_see_place_ids` ≤ 10 and only places of the selected city; `allowed_modes` ≥ 1.

**Accessibility.** Each field has a visible label; stepper −/+ buttons ≥ 44 pt announce the value; disabled action
states its reason in text; the clarification question is a heading and the field is focused on arrival; segmented
control uses `tab` semantics.

**Flags.** None.

**Open points.** None.

### SCR-023 Generation progress

**Purpose and stories.** Show the SSE progress of proposal generation and its failure state (US-013, US-019 AC1;
FR-024..FR-026, FR-042..FR-044; NFR-002, NFR-003). Wireframe m02.

**Route, entry, exit.** Route `/plan/[previewId]` (progress state until `preview_ready`). Entry: SCR-022 Create,
SCR-030 Regenerate. Exit: `preview_ready` → SCR-024 (same route, content swap); Cancel → SCR-022 with input kept;
error → SCR-022 (Edit request) or retry.

**Layout (top → bottom).** `AccountShell` header *Chuyến đi mới / New trip* (or trip title when regenerating).
Title *Đang tạo đề xuất cho {city} / Creating your {city} proposal*. Step line *Bước {k}/5 / Step {k} of 5*.
`ProgressSteps` list (one row per stage, ✓ done, … current, ○ pending):

| `stage` | vi-VN | en-US |
|---|---|---|
| VALIDATING_REQUEST | Hiểu yêu cầu | Understanding your request |
| SELECTING_PLACES | Chọn địa điểm đã đối chiếu nguồn | Choosing source-checked places |
| ROUTING | Tính thời gian di chuyển | Measuring travel times |
| SCHEDULING | Xếp thứ tự và giờ | Ordering stops and times |
| CHECKING_HEALTH | Kiểm tra giờ mở cửa | Checking opening hours |

Reassurance line *Thường mất dưới một phút. Bạn có thể rời màn hình; đề xuất sẽ đợi bạn. / Usually under a minute. You
can leave this screen; the proposal will wait for you.* `Action` secondary *Huỷ / Cancel*. Skeleton stop cards below
on wide screens (optional).

**Data shown.** API-018 / API-021 stream events: `type=progress` → `stage`; `type=preview_ready` → `preview_id`,
`preview_revision`, `plan_health`; `type=clarification_required` → back to SCR-022; `type=error` → `error.code`.

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Stream drops | API-019 `GET /v1/plan-previews/{preview_id}` polling every 3 s (no second POST) | Resume when `status=ACTIVE` and days present |
| Cancel | Close the stream; no server cancel (the preview may still complete and remains ACTIVE until expiry) | SCR-022 |
| Try again (error) | Repeat API-018 with the **same** `Idempotency-Key` when the failure was network; a new key after `ai_unavailable`/`route_unavailable` | SCR-023 |
| First proposal displayed | Study accounts: API-032 FIRST_PROPOSAL_DISPLAYED | — |

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | First progress row visible within 2 s (NFR-003); if no event in 2 s show VALIDATING_REQUEST as current anyway | — |
| Error | `Banner` error role=alert; request text kept; code shown small | Không tạo được đề xuất. {S-1 copy for the code}. Yêu cầu của bạn vẫn còn đây. / Could not create a proposal. {…}. Your request is kept. · Thử lại / Try again · Sửa yêu cầu / Edit request |
| Offline (mid-stream) | Banner; keeps polling when back online | S-2 |
| Slow (> 60 s) | Line *Mất lâu hơn bình thường… / Taking longer than usual…* under the steps; Cancel remains | — |

The wireframe's code label `PLANNING_UNAVAILABLE` is superseded by the contract codes `ai_unavailable` and
`route_unavailable`.

**Validation and limits.** n/a.

**Accessibility.** Steps are a list with `aria-live=polite` on the current step; Cancel is the only button; the error
banner receives focus.

**Flags.** None. **Open points.** None.

### SCR-024 Proposal timeline

**Purpose and stories.** Review each day as an ordered timeline with real legs, see conflicts and Plan Health, open
edits, Save (US-013..US-016, US-018, US-039..US-041; FR-024..FR-032, FR-039, FR-040, FR-089, FR-090). Wireframe m03.

**Route, entry, exit.** Route `/plan/[previewId]` (timeline mode). Entry: SCR-023 `preview_ready`; SCR-031/SCR-008
saved trip (opens the saved itinerary read-only via API-014; editing creates a preview with `source:
SAVED_ITINERARY`); SCR-025 toggle. Exit: Map toggle → SCR-025; health badge → SCR-026; ⋯ on a stop → SCR-027; Save →
SCR-029; ⋯ in the header → *Tạo lại ngày / Regenerate day* (SCR-030) or *Bỏ bản nháp / Discard draft* (API-023 after
confirmation); stop name → SCR-033; back → SCR-031 (draft stays ACTIVE until expiry; a banner on return offers to
resume).

**Layout (top → bottom).** `AccountShell` header: back, title `{city} · {day_count} ngày/days`, ⋯ menu (44 pt).
Status row: `Badge` *Chưa lưu / Unsaved* or *Đã lưu / Saved* + `HealthBadge` (`✓ Ổn / Good`, `⚠ Cần chú ý · {n} cảnh
báo / Warning · {n} warnings`, `⛔ Bị chặn · {b} lỗi, {w} cảnh báo / Blocked · {b} blocking, {w} warnings`; tap →
SCR-026). `SegmentedControl` *Dòng thời gian / Timeline* · *Bản đồ / Map*. `DayTabs` *Ngày {i} · {date short} / Day
{i} · {date short}* (1–3). Optional *Đang tính lại thời gian sau khi bạn sửa… / Recalculating times after your edit…*
line. List of `StopCard`s separated by `LegRow`s; each `StopCard`: ordinal circle, time range `HH:mm – HH:mm`, primary
name, secondary other-language name ` · {visit_minutes} phút/min`, optional conflict/warning line, lock badge, ⋯
button (44 pt). `LegRow`: mode glyph + *Đi bộ / Walk* or *Đi xe / Drive* ` · {distance} · {duration}` or the
unavailable variant. Sticky `Action` primary *Lưu chuyến đi / Save trip* with helper text when disabled.

**Data shown.**

| Field | Source | Format |
|---|---|---|
| Preview | API-019 `GET /v1/plan-previews/{preview_id}` → `preview_revision`, `head_revision`, `status`, `origin`, `plan_health`, `health_reasons[]`, `expires_at`, `assumptions[]`, `days[]` | Revision shown in the map/timeline toggle as the same identifier (FR-028) |
| Day | `days[].day_index`, `day_window_start`, `day_window_end` | Tab label |
| Stop | `days[].stops[].id`, `ordinal`, `planned_arrival`, `planned_departure`, `visit_minutes`, `is_locked`, `name_vi`, `name`, `rationale`, `conflicts[]` | Times in Asia/Ho_Chi_Minh; rationale shown as an optional *Vì sao chọn? / Why this?* disclosure labelled as AI text |
| Leg | `days[].legs[].from_stop_id`, `to_stop_id`, `travel_mode`, `availability`, `distance_m`, `duration_s`, `conflicts[]` | `450 m · 6 phút`; `availability` UNAVAILABLE or EXPIRED → *Không có tuyến đường — không ước tính / Route unavailable — no estimate* (never a straight-line value, BRU-006) |
| Conflicts | `conflicts[].type`, `severity`, `message` | CLOSED_AT_PLANNED_TIME → *Đóng cửa vào giờ dự kiến (đóng {time}) / Closed at planned time (closes {time})*; LEG_UNAVAILABLE → as above; DAY_WINDOW_EXCEEDED → *Vượt khung giờ trong ngày / Day window exceeded*; OPENING_HOURS_UNKNOWN → *Giờ mở cửa: chưa rõ / Opening hours: unknown*; FACT_STALE → *Giờ mở cửa có thể đã cũ / Hours may be out of date*; MUST_SEE_NOT_INCLUDED → shown once in a day-level note *Không thể xếp {place}: {message} / Could not include {place}: {message}* (US-013 AC4) |
| Saved trip (read mode) | API-014 `days[]` same shapes; `status`, `revision`, `saved_at` | Badge *Đã lưu / Saved*; Save hidden; *Chỉnh sửa / Edit* creates a preview |

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Tap health badge | — | SCR-026 |
| Tap ⋯ on a stop | — | SCR-027 (sheet) |
| Tap stop name | API-011 `GET /v1/places/{place_id}` | SCR-033 |
| Tap day tab | — | Switch day; selection kept per day |
| Toggle Map | — | SCR-025 with the same `preview_revision` and selected stop (FR-088) |
| Edit (saved read mode) | API-018 `{source: SAVED_ITINERARY, expected_trip_revision, locale}` + `Idempotency-Key` (no AI call) | New ACTIVE preview, revision 1 |
| Save | — | SCR-029 confirm sheet (disabled while recalculating, while `plan_health = BLOCKED` with helper *Xem lý do / See why* → SCR-026, or when a day has 0 stops) |
| ⋯ Regenerate day | — | SCR-030 (flag) |
| ⋯ Discard draft | API-023 `DELETE /v1/plan-previews/{preview_id}` after `AlertDialog` *Bỏ bản nháp này? Chuyến đã lưu không đổi. / Discard this draft? Your saved trip does not change.* | SCR-031 |
| Resume after a dropped edit response | API-019 | Latest `head_revision`; pending edit re-applied from the draft store (CMP-020) |

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | Skeleton stop cards (first open); after an edit, badge *↻ Đang tính lại… / Recalculating…* and Save disabled with *Có thể lưu khi tính lại xong. / You can save when recalculation finishes.* (NFR-004 ≤ 5 s p95) | — |
| Empty day | `EmptyState` *Ngày {i} chưa có điểm dừng / Day {i} has no stops yet* · *Thêm địa điểm đã đối chiếu nguồn ở {city} hoặc tạo lại ngày này. / Add a source-checked {city} place or regenerate this day.* · `＋ Thêm điểm dừng / Add a stop` → SCR-028 | — |
| Unknown / Stale | Warning badges on the stop (never blank) | fact.unknown / fact.stale |
| Blocked | Red left edge on the stop + reason; health badge counts; Save disabled | — |
| Error (edit) | `Banner` error above the list; edit kept (US-019 AC2) | Không tính lại được thời gian di chuyển. Thay đổi của bạn vẫn còn trong bản nháp. Thử lại / Could not recalculate travel times. Your change is kept in this draft. Try again |
| Conflict 409 `revision_conflict` | Banner; reload `head_revision`; pending edit offered again | Bản nháp đã thay đổi ở nơi khác / This draft changed elsewhere |
| Expired 410 | Banner with `Action` | Bản nháp đã hết hạn. Tạo lại / This draft expired. Create again (→ SCR-022 prefilled from the trip) |
| Offline | Read-only; edits, Save disabled with reason | S-2 |
| Superseded catalog (stop no longer published) | Stop card shows *Không còn khả dụng / No longer available* badge; Save refused by server (409 `plan_blocked` with reason) | — |

**Validation and limits.** 1–3 days; ≥ 1 stop per day to Save; a day's stops ≤ 20 (UI cap, server validates).

**Accessibility.** Status never by colour alone; each `StopCard` is one list item whose label is `{ordinal}, {name},
{arrival} đến {departure}, {status}`; reorder is available through SCR-027 Move up/down (no drag-only interaction,
WCAG 2.5.1); focus order header → status → view toggle → day tabs → stops → Save; the recalculating badge is a polite
live region.

**Flags.** `FEATURE_REGENERATION` hides the lock badge and the Regenerate menu item.

**Open points.** None.

### SCR-025 Proposal map

**Purpose and stories.** Picture the day spatially; selection synchronised with the timeline; legs drawn only when
measured (US-014 AC2–AC4, US-015; FR-027..FR-029, FR-031, FR-088). Wireframe m04.

**Route, entry, exit.** Same route as SCR-024, Map mode. Entry: toggle. Exit: toggle back; *Thẻ địa điểm / Place
card* → SCR-033; ⋯ → SCR-027.

**Layout (top → bottom).** Same header, status row, toggle and day tabs as SCR-024. `MapView` (react-native-maps;
Google provider on Android) filling the middle: numbered `MapPin`s (default `deepOcean`, selected larger with
`tealText` ring, blocked `error` colour), `RoutePolyline` between consecutive stops for AVAILABLE legs only; dashed
red segment with no length label for UNAVAILABLE; Fit button 44 pt (⤢) top-right; map attribution *Map data ©
Google* bottom-left (AC-047). Selected `StopCard` + its outgoing `LegRow` under the map. Row of controls: `‹ Trước /
Previous` · `Sau › / Next` · `Thẻ địa điểm / Place card`. Sticky Save as SCR-024.

**Data shown.** Same API-019 (or API-014) payload as SCR-024: `stops[].location` (`latitude`, `longitude`) for pins;
legs for polylines; selected stop card as above. Leg geometry is not provided by the API in v1: the polyline is a
straight connector drawn only as a visual link between **measured** legs and never labelled with a distance (the
distance label comes from `distance_m`).

**Actions.** Tap pin → select stop (timeline selection follows, FR-088); Previous/Next → step through stops without
touching the map; Fit → frame all pins of the day; Place card → SCR-033; ⋯ → SCR-027.

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | Map placeholder + skeleton card | — |
| Empty day | City-centre map (API-008 has no centre: use the first published place of the city or the `cities.boundary` centroid supplied later) with text | Ngày này chưa có điểm dừng / This day has no stops yet |
| Unknown entrance | Pin at `location` (place position) | — |
| Leg unavailable | Dashed segment; card line *⚠ Không có tuyến đường — không ước tính / Route unavailable — no estimate*; legend *Ngày có chặng không có tuyến đường bị đánh dấu "Bị chặn". Hãy đổi cách di chuyển hoặc thay điểm dừng. / A day with an unavailable leg is Blocked. Change the travel mode or replace the stop.* | — |
| Error (tiles) | Banner + link to timeline | Không tải được bản đồ. Dòng thời gian vẫn hiển thị. / The map could not load. The timeline is still available. |
| Offline | Banner replaces the map | Bản đồ cần kết nối mạng. Dòng thời gian vẫn hiển thị. / The map needs a connection. The timeline is still available. |

**Validation and limits.** n/a.

**Accessibility.** The map is supplementary: everything on it is in the timeline (WCAG 1.1.1); pins are buttons
labelled `Điểm dừng {n}, {name}, {time} / Stop {n}, {name}, {time}`; Previous/Next give a non-gesture path; attribution
stays visible at 200 % text.

**Flags.** As SCR-024.

**Open points.** None. OQ-109 closed: an empty day centres the map on API-008 `City.centre` (fallback: the first published place of the city when `centre` is null).

### SCR-026 Plan Health detail

**Purpose and stories.** Explain exactly what blocks a day and what to check, with shortcuts to fix (US-015,
US-002 AC3–AC4, US-014 AC4; FR-030..FR-032, FR-006, FR-007). Wireframe m05.

**Route, entry, exit.** Route `/plan/[previewId]/health`. Entry: health badge on SCR-024/025; *Xem cách sửa / See
how to fix* on SCR-029 refused. Exit: *Đến điểm dừng / Go to stop* → SCR-024 with the stop selected; fix shortcut
(*Chuyển lên buổi sáng / Move to the morning*, *Đổi cách di chuyển / Change travel mode*, *Thay địa điểm / Replace*) →
SCR-027 prefilled; back.

**Layout (top → bottom).** `AccountShell` header *Tình trạng kế hoạch / Plan Health*. `HealthSummary` card: icon +
status line (*⛔ Bị chặn — chưa thể lưu / Blocked — cannot be saved yet*, *⚠ Cần chú ý — có thể lưu / Warning — can be
saved*, *✓ Ổn — có thể lưu / Good — ready to save*) and count line *{b} lỗi chặn, {w} cảnh báo · Ngày {i} / {b}
blocking issue(s), {w} warnings · Day {i}* (per-day tabs when > 1 day). Section **Cần sửa / Must fix** (BLOCKING):
`IssueCard`s with `Badge` *⛔ Chặn / Blocking*, title (conflict type), detail line *Ngày {i} · #{ordinal} {name} ·
đến {arrival}, đóng {closes}, rời {departure} / Day {i} · #{ordinal} {name} · arrive …, closes …, leave …*, actions
(fix shortcut primary small, *Đến điểm dừng / Go to stop* secondary small). Section **Nên xem / Worth checking**
(WARNING): same card with *⚠ Cảnh báo / Warning*; FACT_STALE detail *giờ mở cửa đối chiếu nguồn {n} ngày trước / hours
verified {n} days ago*. Good state: summary card + explanation *Mọi điểm dừng mở cửa vào giờ dự kiến, mọi chặng có tuyến
đường, ngày kết thúc trước {day_window_end}. / Every stop is open at its planned time, every leg has a route, and each
day ends before {day_window_end}.* + note *Tình trạng được tính lại sau mỗi thay đổi. Giờ mở cửa thực tế có thể thay
đổi; hãy kiểm tra thẻ địa điểm trước khi đi. / Health is recalculated after every change. Real opening hours can change;
check the place card before you go.*

**Data shown.** API-019 `plan_health`, `health_reasons[]` (preview-level) plus `days[].stops[].conflicts[]` and
`days[].legs[].conflicts[]` grouped by `severity` then by day and ordinal; stop times from the stop; `closes` from the
conflict `message` (the server composes it; the UI does not compute hours).

**Actions.** Fix shortcuts map to SCR-027 operations: CLOSED_AT_PLANNED_TIME → Move (to_ordinal 1); LEG_UNAVAILABLE →
mode switch or Replace; DAY_WINDOW_EXCEEDED → Remove/Shorten (duration stepper focused); OPENING_HOURS_UNKNOWN and
FACT_STALE → *Xem thẻ địa điểm / See place card* (SCR-033).

**States.** Loading: *Đang cập nhật / Updating* with the previous result greyed; Good = empty state; error (validation
could not run): *Không kiểm tra được kế hoạch / Could not check the plan*, Save stays disabled; offline: last known
result, shortcuts disabled.

**Validation and limits.** n/a.

**Accessibility.** Severity by icon, word and section heading; each `IssueCard` is a group with its own actions;
headings for the two sections.

**Flags.** None. **Open points.** None.

### SCR-027 Edit stop sheet

**Purpose and stories.** Change duration, travel mode, position, replace, lock, remove in one place (US-016, US-017,
US-019 AC2, US-021, US-039..US-041; FR-033..FR-039, FR-043, FR-047, FR-089). Wireframe m06.

**Route, entry, exit.** Sheet over SCR-024/025. Entry: ⋯ on a `StopCard`, SCR-026 shortcuts. Exit: Apply → SCR-024
recalculating; Replace → SCR-028; Remove → confirmation `AlertDialog`; swipe down/close → no change.

**Layout (top → bottom).** `Sheet` (radius 40, handle). Title = place name (primary), subtitle *Ngày {i} · điểm dừng
{ordinal} · {arrival} – {departure} / Day {i} · stop {ordinal} · …*. **Thời gian tham quan / Visit duration**
`Stepper` − {n} phút/min + (15-minute steps, ASM-061; bounds 15–240 min, or the place's `visit_minutes_min..max` when
provided by API-011). **Cách đến điểm này / How to get here** `SegmentedControl` *Đi bộ / Walk* · *Đi xe / Drive* (for
the incoming leg; only modes in `allowed_modes`; hidden for the first stop of a day). **Vị trí / Position** button row:
*↑ Lên / Move up*, *↓ Xuống / Move down*, *⇤ Lên đầu ngày / Move to start*, *Sang ngày {j} / Move to day {j}* (one per
other day; hidden for 1-day trips). Action row (secondary small): *⇄ Thay địa điểm / Replace*, *🔒 Giữ cố định / Lock*
(toggles to *Bỏ giữ cố định / Unlock*; flag), *✕ Xoá / Remove* (destructive style). `Action` primary *Áp dụng /
Apply* (enabled only when something changed).

**Data shown.** The stop (`id`, `ordinal`, `visit_minutes`, `is_locked`, `planned_arrival`, `planned_departure`),
its incoming leg (`travel_mode`), `preview_revision` (as `expected_revision`), `day_count`.

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Apply | API-020 `PATCH /v1/plan-previews/{preview_id}` `{expected_revision, edits[]}` + `Idempotency-Key`; edits built from the changes: `SET_VISIT_MINUTES {stop_id, visit_minutes}`, `SET_LEG_MODE {from_stop_id, to_stop_id, travel_mode}`, `MOVE_STOP {stop_id, day_index, to_ordinal}`, `LOCK_STOP`/`UNLOCK_STOP {stop_id}` (≤ 20 ops) | New revision; SCR-024 recalculating → updated |
| Replace | — | SCR-028 (then `REPLACE_STOP {stop_id, place_id}`) |
| Remove → Xoá | API-020 `REMOVE_STOP {stop_id}` | Stop and its legs removed; times recalculated |
| Close | — | Pending changes discarded (sheet-local only) |

Pending edits are kept in the draft store (CMP-020) until the server acknowledges them (US-019 AC2).

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | Apply *Đang áp dụng… / Applying…* disabled; sheet not dismissible | — |
| Error | Banner in the sheet; edit kept; Save on SCR-024 stays disabled | S-1 (`route_unavailable`, network) |
| Conflict 409 | Banner; reload; pending edit re-offered | Bản nháp đã thay đổi ở nơi khác / This draft changed elsewhere |
| Offline | Apply disabled with reason | S-2 |
| Blocked | Lock hidden when flag off; Move to day hidden for 1-day trips; mode control hidden when only one mode allowed | — |
| Remove confirmation | `AlertDialog` *Xoá điểm dừng này? / Remove this stop?* · *{name} và chặng đi tới nó sẽ bị xoá khỏi bản nháp. Chuyến đã lưu không đổi cho tới khi bạn Lưu. / {name} and its leg are removed from this draft. Your saved trip does not change until you Save.* · *Xoá / Remove* (destructive, not default focus) · *Giữ lại / Keep* | — |

**Validation and limits.** `visit_minutes` 5–600 (contract), UI 15–240 in 15-min steps; `to_ordinal` within the
target day; a locked stop cannot be removed or moved to another day without unlocking first (helper text).

**Accessibility.** Modal dialog with heading = place name; stepper value announced (`aria-live`); every action has a
text label; destructive action is not the default focus.

**Flags.** `FEATURE_REGENERATION` hides Lock/Unlock.

**Open points.** None.

### SCR-028 Place picker (add / replace / must-see)

**Purpose and stories.** Offer only published places of the trip's city for Add, Replace and must-see selection
(US-016 AC2, US-039 AC2, US-041 AC1; FR-034, FR-036, FR-087). Wireframe m06.

**Route, entry, exit.** Full-height sheet. Entry: SCR-024 empty-day "Add a stop", SCR-027 Replace, SCR-022 must-see.
Exit: *Chọn / Choose* → applies the edit (SCR-024 recalculating) or adds a chip (SCR-022); back → opener.

**Layout (top → bottom).** Header: back, title *Thêm điểm dừng vào ngày {i} / Add a stop to day {i}*, *Thay điểm dừng
{ordinal} / Replace stop {ordinal}* or *Nhất định phải đến / Must-see places*. Search `Field` *Tìm địa điểm ở {city} /
Search places in {city}*. Scope line *Chỉ hiển thị địa điểm đã đối chiếu nguồn ở {city}. / Only source-checked places in {city}
are shown.* Result rows: glyph tile, primary name, secondary `{other name} · {visit_minutes_suggested} phút/min`,
`Action` small *Chọn / Choose*. Places already in the day are listed with a *Đã có trong ngày / Already in this day*
badge and a disabled button.

**Data shown.** API-010 `GET /v1/places?city_id={trip city}&q&locale&limit=20` → `items[].id`, `name`, `name_vi`,
`visit_minutes_suggested`, `category_code`. No distance label is shown in v0.1 (see OQ-110).

**Actions.** Choose → API-020 `ADD_STOP {day_index, place_id, to_ordinal?}` or `REPLACE_STOP {stop_id, place_id}` +
`Idempotency-Key`; must-see mode → local chip (`must_see_place_ids`), no call.

**States.** Loading: 3 skeleton rows; empty: *Không có địa điểm phù hợp ở {city} / No matching places in {city}*;
error: banner; offline: input disabled; refusal 422 `place_not_in_city` (defensive; the picker is already scoped):
banner S-1.

**Validation and limits.** Query 1–120 chars; ≤ 20 stops per day; ≤ 10 must-sees.

**Accessibility.** Rows labelled `{name}, {other name}, {duration}`; Choose buttons ≥ 44 pt; search field labelled.

**Flags.** None.

**Open points.** None. OQ-110 closed: no straight-line distance hint in this release.

### SCR-029 Save confirmation / result

**Purpose and stories.** Explicit Save, refusal when blocked, success with handoffs, conflict and interrupted-save
handling (US-018, US-019 AC3–AC4, US-015 AC4, US-029, US-037; FR-040..FR-045, FR-032, FR-079, FR-080). Wireframe m07.

**Route, entry, exit.** Confirm = sheet over SCR-024/025; success = full screen `/plan/[previewId]/saved`. Entry:
Save on SCR-024/025. Exit: success *Xem chuyến đi / View trip* → SCR-024 saved mode (and SCR-031 in the stack);
handoff rows → SCR-037; refused *Xem cách sửa / See how to fix* → SCR-026; *Tiếp tục chỉnh sửa / Keep editing* → back.

**Layout.**

*Confirm sheet:* title *Lưu chuyến đi này? / Save this trip?*; `TripSummaryCard` `{city} · {day_count} ngày/days ·
{start} – {end}`, `{stops} điểm dừng · ⚠ {w} cảnh báo / {stops} stops · ⚠ {w} warnings`; note *Phiên bản này sẽ thay
thế chuyến đã lưu trước đó. Giá không được lưu cùng chuyến đi. / This version replaces your previously saved trip.
Prices are never stored with a trip.* (second sentence only when `FEATURE_STAY_PRICES` on); `Action` primary *Lưu /
Save*; `TextLink` *Tiếp tục chỉnh sửa / Keep editing*.

*Refused dialog:* `AlertDialog` title *Chưa thể lưu / This trip cannot be saved yet*; body *Kế hoạch đang bị chặn.
{reason} / The plan is blocked. {reason}*; actions *Xem cách sửa / See how to fix*, *Đóng / Close*.

*Success screen:* back; ✓ illustration (pattern of `reference/05-register-complete.png`); title *Đã lưu chuyến đi /
Trip saved*; body *{city} · {day_count} ngày. Bạn có thể mở lại trong Chuyến đi. / {city} · {day_count} days. Reopen it
any time from Trips.*; handoff rows (`AccountRow`): *🛏 Tìm chỗ ở / Find a stay* subtitle `{city} · {start}–{end+1}`,
*🚌 Tìm phương tiện đến {city} / Find transport to {city}* subtitle *Ngày đi {start} / Departing {start}*; `Action`
*Xem chuyến đi / View trip*.

*Conflict banner (on SCR-024):* *Chuyến đi đã được lưu từ thiết bị khác. Bản lưu đó được giữ nguyên. Các chỉnh sửa của
bạn vẫn còn trong bản nháp này. / This trip was saved from another device. That save is kept. Your edits are still in this
draft.* Actions *Xem bản đã lưu / View saved version* (API-014) · *Lưu bản nháp của tôi thay thế / Save my draft
instead* (rebases: API-018 `SAVED_ITINERARY` is **not** used; the app re-sends accept with the new
`expected_trip_revision` after the user confirms the replacement).

*Interrupted banner:* *Mất kết nối khi đang lưu. Chưa rõ việc lưu đã hoàn tất chưa. Thử lại an toàn: chuyến đi chỉ
được lưu một lần. / Connection lost while saving. We could not confirm the save. Retrying is safe: the trip is saved only
once.* Action *Thử lưu lại / Retry save*.

**Data shown.** Summary from the preview (`days[]`, counts), `plan_health`; success from the API-022 response
`TripDetail` (`revision`, `status = SAVED`, `saved_at`, `start_date`, `day_count`).

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Save | API-022 `POST /v1/plan-previews/{preview_id}/accept` `{expected_preview_revision, expected_trip_revision}` + **required** `Idempotency-Key` K; study accounts API-032 SAVE_OUTCOME | 200 → success screen; cache the trip |
| Retry save | Same call, same key K | `Idempotent-Replayed: true` → success without a second version (FR-041) |
| 409 `plan_blocked` | — | Refused dialog with `context.reasons` |
| 409 `revision_conflict` | — | Conflict banner (`context.current_revision`) |
| 410 `preview_expired` / `preview_closed` | — | SCR-024 expired state |
| Find a stay / transport | API-030 `GET /v1/trips/{trip_id}/handoff-links?kind=STAY` / `TRANSPORT` | SCR-037 |

**States.** Loading: Save *Đang lưu… / Saving…*, sheet not dismissible; empty: n/a (Save disabled with 0 stops);
error generic: *Không lưu được. Bản nháp vẫn còn / Could not save. Your draft is kept.*; offline: interrupted banner
pattern; blocked: refused dialog.

**Validation and limits.** `expected_*` revisions always sent; one key per Save attempt series.

**Accessibility.** Success and errors announced (`status` / `alert`); focus to the sheet heading on open and back to
Save on close; full-width buttons ≥ 56 pt; the ✓ illustration is decorative.

**Flags.** `FEATURE_STAY_PRICES` only changes the note sentence.

**Open points.** None.

### SCR-030 Regenerate day (HA-02)

**Purpose and stories.** Regenerate one day while keeping locked stops and every other day (US-042, US-021; FR-047..
FR-050, FR-091). Wireframe m03. Should; cut 4th.

**Route, entry, exit.** `AlertDialog` over SCR-024 (current day). Entry: ⋯ → Regenerate day. Exit: confirm →
SCR-023 (regeneration progress) → SCR-024 new revision; Cancel → back.

**Layout.** Title *Tạo lại ngày {i}? / Regenerate day {i}?*; body lines *Ngày {others} giữ nguyên. / Day {others}
stays exactly as it is.*; *Điểm đã giữ cố định giữ nguyên vị trí, ngày và thời lượng: {locked names} / Locked stops
keep their position, day and visit duration: {locked names}* (or *Không có điểm giữ cố định / No locked stops*);
*Kết quả là bản nháp chưa lưu; chuyến đã lưu không đổi cho đến khi bạn Lưu. / The result is an unsaved draft; your saved
trip does not change until you Save.*; optional single-line `Field` *Ghi chú cho ngày này (tuỳ chọn) / Note for this day
(optional)* (≤ 500 chars → `instruction`); `Action` primary *Tạo lại ngày {i} / Regenerate day {i}*; `TextLink` *Huỷ /
Cancel*.

**Data shown.** Locked stops of the day (`stops[].is_locked`, `name`); `preview_revision`.

**Actions.** Confirm → API-021 `POST /v1/plan-previews/{preview_id}/regenerate` `{expected_revision, day_index,
locked_stop_ids[], instruction?, locale}` + `Idempotency-Key`, `Accept: text/event-stream` → SCR-023 stages → new
revision with `origin = DAY_REGENERATED`. Failure (503 `ai_unavailable` / `route_unavailable`): `head_revision`
unchanged, locks and edits kept (US-042 AC4), banner on SCR-024.

**States.** Loading: SCR-023; error: SCR-023 error with *Bản nháp và điểm giữ cố định không đổi / Your draft and locks
are unchanged*; offline: entry disabled; blocked: menu item hidden when flag off or when the trip has 1 day and no
preview.

**Validation and limits.** `day_index` 1..3; `instruction` ≤ 500.

**Accessibility.** `alertdialog` with the title as label; primary action not default-focused (destructive to the draft
day); locked names read in full.

**Flags.** `FEATURE_REGENERATION`.

**Open points.** None.

### SCR-031 My trips (list, delete)

**Purpose and stories.** List saved trips and drafts, reopen at the last saved version, delete, start a new trip
(US-018 AC4, US-020, US-032; FR-041, FR-045, FR-046, FR-068). Pattern: `AccountRow` list (no wireframe).

**Route, entry, exit.** Trips tab (`/trips`). Entry: tab bar, SCR-029 View trip, Home "See all". Exit: row → SCR-024
(saved) or SCR-024 draft resume; *＋ Chuyến đi mới / New trip* → SCR-022; guest → SCR-040; Today → SCR-032.

**Layout (top → bottom).** Title *Chuyến đi / Trips* (28/34). `Action` primary *＋ Chuyến đi mới / New trip*. Section
cap **SẮP TỚI / UPCOMING** and **ĐÃ QUA / PAST** (by `start_date` + `day_count` − 1 vs. today in Asia/Ho_Chi_Minh).
Rows (`AccountRow`): icon trips, title `{title}` or `{city} · {day_count} ngày/days`, subtitle `{date range}` + `Badge`
*Đã lưu / Saved* or *Bản nháp / Draft* (status DRAFT or `active_preview_id` present), trailing chevron; swipe or
long-press reveals *Xoá / Delete* (also reachable from the row's ⋯ button, 44 pt). An upcoming trip whose dates include
today shows a *Hôm nay / Today* chip (→ SCR-032). `HomeTabBar`.

**Data shown.** API-013 `GET /v1/trips?sort=-updated_at&limit=20` → `items[].id`, `city_id`, `title`, `start_date`,
`day_count`, `status`, `revision`, `saved_at`, `updated_at`; `next_cursor`; city names via API-008 cache.

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Tap row | API-014 `GET /v1/trips/{trip_id}` | SCR-024 saved mode (or draft resume via `active_preview_id` → API-019) |
| Delete → confirm | API-016 `DELETE /v1/trips/{trip_id}` after `AlertDialog` *Xoá chuyến đi {name}? Không thể hoàn tác. / Delete trip {name}? This cannot be undone.* · *Xoá / Delete* · *Giữ lại / Keep* | Row removed (204 or 404 both treated as done) |
| New trip | — | SCR-022 |
| Pull to refresh / Load more | API-013 (`cursor`) | — |

**States.** Loading: 3 skeleton rows; empty: `EmptyState` *Chưa có chuyến đi nào / No trips yet* · *Lên kế hoạch 1–3
ngày ở một trong 5 thành phố. / Plan 1–3 days in one of 5 cities.* · New trip; error: banner S-1; offline: cached list,
Delete and New trip disabled; guest: SCR-040 on tab tap.

**Validation and limits.** n/a.

**Accessibility.** Rows labelled `{title}, {dates}, {saved or draft}`; delete reachable without swipe; section caps
are headings.

**Flags.** None. **Open points.** None.

### SCR-032 Today

**Purpose and stories.** Today's stops of a saved trip in order (US-024; FR-055). Should. Pattern: SCR-024 read-only
(no wireframe).

**Route, entry, exit.** Route `/trips/[tripId]/today`. Entry: SCR-031 Today chip, Home saved-trip row when today is
within the trip. Exit: stop → SCR-033; *Xem cả chuyến / See the whole trip* → SCR-024 saved mode.

**Layout (top → bottom).** `AccountShell` header *Hôm nay / Today*, subtitle `{weekday, date} · Ngày {i}/{n} · {city}
/ … · Day {i} of {n} · {city}`. Read-only `StopCard` list with `LegRow`s (same shapes as SCR-024, no ⋯, no Save);
the next upcoming stop (first with `planned_arrival` ≥ now) is highlighted with a *Tiếp theo / Next* badge. Footer
`TextLink` *Xem cả chuyến / See the whole trip*.

**Data shown.** API-014 `days[]`; day chosen by device date in Asia/Ho_Chi_Minh within `start_date..start_date +
day_count − 1`; outside the trip dates the first day is shown with the line *Chuyến đi bắt đầu {date} / Your trip
starts {date}* (FR-055).

**Actions.** Tap stop → SCR-033 (`API-017` place card for that `stop_id`).

**States.** Loading skeleton; empty day: *Ngày này chưa có điểm dừng / This day has no stops*; error: banner; offline:
cached trip, fully usable.

**Validation and limits.** n/a. **Accessibility.** "Next" conveyed by badge text; list semantics as SCR-024.
**Flags.** None. **Open points.** None.

### SCR-033 Place card

**Purpose and stories.** On-site card: both names, driver panel, sourced facts with freshness, live status, entrance,
directions, Guide and activities (US-002, US-022, US-023, US-030, US-034 AC3; FR-003, FR-005..FR-008, FR-051..FR-054,
FR-065, FR-076). Wireframe m08.

**Route, entry, exit.** Route `/place/[placeId]` (and `/trips/[tripId]/stops/[stopId]` for a saved stop). Entry:
SCR-021 result, SCR-024/025 stop, SCR-032, SCR-036 result, Guide source line. Exit: Directions → device maps app; Ask
the Guide → SCR-034 scoped to this place; Find activities → SCR-037 (ACTIVITY, requires a saved stop); ＋ → SCR-028 add
(when a draft is open); back.

**Layout (top → bottom).** Header: back (44 pt), ＋ (only when a draft preview is open). `MapPreview` 160 pt with
one pin at `entrance_location` or `location`, attribution *Map data © Google*. Title block: primary name (28/34),
secondary `{other name} · {category} · khoảng {visit_minutes_suggested} phút / about {n} min`. **DriverPanel**
(`deepOcean` card, white text ≥ 18 pt): cap *ĐƯA CHO TÀI XẾ / SHOW YOUR DRIVER*, `name_vi` (24 bold), `address_vi` value
or *Địa chỉ: chưa rõ / Address unknown*. **Facts** (`FactRow` definition list): *Giờ mở cửa / Opening hours* value +
`SourceLine` *ⓘ {publisher} · đối chiếu nguồn {date}* + stale badge; *Hôm nay / Today* live row *Đang mở theo Google (trực tiếp)
/ Open now per Google (live)* or *Đang đóng theo Google / Closed per Google* with `retrieved_at` and Google attribution
(hidden when `live_status` absent); *Giá vé / Admission*; *Lối vào / Entrance* value or *Lối vào: chưa rõ / Entrance:
unknown*; other operational facts (`PAYMENT_METHODS`, `DRESS_CODE`, `ACCESS_RULES`) when KNOWN. Description
(`description`, UI language) with the note *Mô tả: nội dung do Gonarra biên soạn / Description written by Gonarra*.
Media carousel (`media[]`) with per-image attribution line. Attribution block listing every `attributions[]` entry.
Sticky `ActionBar`: `Action` primary *➤ Chỉ đường / Directions*, secondary *✦ Hỏi Hướng dẫn / Ask the Guide*, `TextLink`
*Tìm hoạt động / Find activities*.

**Data shown.**

| Field | Source | Format |
|---|---|---|
| Names, category, duration, description, media, attributions, facts | API-011 `GET /v1/places/{place_id}?locale` → `name`, `name_vi`, `name_en`, `category_code`, `visit_minutes_suggested`, `description`, `media[]` (`url`, `alt_text`, `attribution_text`, `license_code`), `attributions[]`, `facts[]` (`field_code`, `knowledge_state`, `value`, `verified_at`, `freshness`, `sources[]`) | `value` rendered per `field_code` (HOURS → `07:00 – 17:30`; MONEY → money format; TEXT; LOCATION) |
| Driver address, entrance, directions, live status | API-017 `GET /v1/trips/{trip_id}/stops/{stop_id}/place-card` → `address_vi` (`PlaceFact`), `entrance` (`PlaceFact`), `directions.target` (ENTRANCE / PLACE_POSITION), `directions.google_maps_url`, `apple_maps_url`, `live_status.open_now`, `retrieved_at`, `attribution_text` | For a place opened outside a trip (no `stop_id`), the card uses API-011 facts `ADDRESS_VI` and `ENTRANCE_LOCATION` and builds the directions URL from `entrance_location` or `location`; live status is not shown |
| Stale | `freshness = STALE` | Badge next to the source line |

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Directions | Open `google_maps_url` (Android default) or `apple_maps_url` (iOS default) | Maps app with entrance or place position (US-023) |
| Ask the Guide | API-024 `POST /v1/ai/sessions` `{place_id, trip_id?, locale}` (reuse an existing session for the place when present) | SCR-034 |
| Find activities | API-030 `?kind=ACTIVITY&stop_id=` | SCR-037; hidden when not a saved stop |
| ＋ Add to draft | SCR-028 rules → API-020 `ADD_STOP` | — |
| Tap source line | — | Expands the source (`title`, `locator`) |

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | Skeleton; the card renders from API-011 before API-017 completes (NFR-011) | Đang tải thẻ địa điểm… / Loading place card… |
| Unknown | *chưa rõ / unknown* per fact; Directions falls back to the place position | — |
| Stale | *Có thể đã cũ / May be out of date* | — |
| Live unavailable | Today row hidden; nothing else changes | — |
| Error 404 | Full-screen message + back | Địa điểm này không còn khả dụng / This place is no longer available |
| Offline | Cached card for saved-trip stops with header line; live row hidden; Directions still works (URL cached) | Ngoại tuyến · cập nhật lúc {time} / Offline · updated {time} |

**Validation and limits.** n/a.

**Accessibility.** Driver panel text ≥ 18 pt and 13.8:1 contrast; facts as a definition list; source lines are text
(not icon-only) and tappable rows ≥ 44 pt; live vs. curated data distinguished in words; map preview labelled by the
place name; images have `alt_text`.

**Flags.** None.

**Open points.** None.

### SCR-034 Guide chat (text)

**Purpose and stories.** Ask about one published place; answers always carry ≥ 1 checked source with its verified
date or the `insufficient_evidence` outcome; first-use AI notice (US-025, US-026, US-035, US-032; FR-056..FR-058,
FR-070, FR-074, FR-078; NFR-005, NFR-006). Wireframe m09.

**Route, entry, exit.** AI guide tab (`/guide`) and `/guide/[sessionId]`. Entry: tab, SCR-033 Ask the Guide, SCR-036
Ask about it, SCR-035 after Stop and send. Exit: source line → SCR-033; mic → SCR-035; camera → SCR-036; place chip →
place picker (SCR-028 in "choose a place" mode, city-scoped); guest → SCR-040.

**Layout (top → bottom).** Header: title *Hướng dẫn AI / AI guide*, 🗑 *Xoá cuộc trò chuyện / Delete conversation*
(44 pt). **ContextBadge** chip `⛩ {place name} · {city}` with chevron (tap → choose another place; required: a session
is always scoped to one place). Thread (scrollable, newest at the bottom): `ChatBubble` traveler (right, `skyWash`),
`ChatBubble` assistant (left, white, border) with body text, **SourceLine** block *Nguồn / Sources* listing each
citation `ⓘ {publisher}{, title} · đối chiếu nguồn {verified_at}` + stale badge when older than 180 days, *🔊 Đọc to / Read
aloud* toggle (flag). Insufficient-evidence bubble: heading *Chưa đủ nguồn để trả lời / Not enough evidence to answer*
and body *Nguồn đã đối chiếu của Gonarra không đề cập điều này, nên tôi không đoán. Hãy hỏi tại chỗ hoặc kênh chính
thức. / Gonarra's checked sources do not cover this, so I won't guess. Please ask on site or check an official channel.*
(no answer text). First-use AI notice `Banner` above the composer (same text as SCR-022 but *Câu hỏi của bạn / Your
question*). **Composer**: 📷 camera (flag), text `Field` placeholder *Hỏi về {place}… / Ask about {place}…*, ◉ mic
(flag), Send (44 pt). `HomeTabBar` (AI guide active).

**Data shown.**

| Field | Source |
|---|---|
| Session | API-024 create / API-025 `GET /v1/ai/sessions/{session_id}` → `place_id`, `trip_id`, `locale`, `expires_at` |
| Messages | API-027 `GET /v1/ai/sessions/{session_id}/messages?limit=50` → `items[].role`, `input_mode`, `content`, `answer_status`, `citations[]` (`publisher`, `title`, `locator`, `verified_at`, `knowledge_chunk_id`, `place_fact_id`), `created_at` |
| Streaming | API-028 stream `progress.stage` (RETRIEVING → *Đang tìm trong nguồn đã đối chiếu… / Searching checked sources…*, ANSWERING), `text.delta`, `result.message` |
| Place name | API-011 for the session's `place_id` |

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Send | API-028 `POST /v1/ai/sessions/{session_id}/messages` `{content, input_mode: TEXT}` + `Idempotency-Key`, `Accept: text/event-stream` | Traveler bubble appended immediately; assistant bubble streams; sources render on `result` |
| Suggested chip (empty state) | Same as Send with the chip text | — |
| Mic | — | SCR-035 |
| Camera | — | SCR-036 |
| Place chip | — | Picker → API-024 new session for the new place |
| Delete conversation | API-026 `DELETE /v1/ai/sessions/{session_id}` after `AlertDialog` *Xoá cuộc trò chuyện này? / Delete this conversation?* | Empty state |
| Tap a source line | — | SCR-033 of the place (fact or chunk highlighted when `place_fact_id` present) |
| Read aloud | On-device TTS of the completed, displayed text only | SCR-035 reading state |
| Stream drops | API-027 re-fetch; no second POST | Stored result shown |

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | Streaming bubble with caret and *Đang thêm nguồn… / Adding sources…* at the end; Send disabled until `result` | — |
| Empty (new conversation) | ✦ glyph, title *Hỏi về một địa điểm đã đối chiếu nguồn / Ask about a source-checked place*, body *Câu trả lời luôn kèm nguồn. Nếu nguồn không đủ, Gonarra sẽ nói rõ. / Every answer lists its sources. If they are not enough, Gonarra says so.*, chips *Mấy giờ đóng cửa? / When does it close?*, *Có phải mua vé? / Do I need a ticket?*, *Lối vào ở đâu? / Where is the entrance?* | — |
| No place selected | Context chip reads *Chọn địa điểm / Choose a place*; composer disabled with hint | Chọn một địa điểm để hỏi / Choose a place to ask |
| Insufficient evidence | As above; `answer_status = INSUFFICIENT_EVIDENCE` | — |
| Stale | Badge on the source line | Có thể đã cũ / May be out of date |
| Error | Bubble replaced by an error line; question kept in the composer | Không trả lời được lúc này. Câu hỏi của bạn vẫn còn. Thử lại / Could not answer right now. Your question is kept. Try again |
| Quota 429 | Banner with `resets_at`; composer disabled | S-1 |
| Offline | Composer disabled | Cần kết nối để hỏi / A connection is needed to ask |
| Blocked | Guest → SCR-040 | — |

**Validation and limits.** `content` 1–4000 characters (UI counter from 3500); one in-flight question per session;
messages are immutable.

**Accessibility.** New messages announced `polite` (never assertive); bubbles labelled by sender (*Bạn / You*, *Hướng
dẫn / Guide*); source lines are text links ≥ 44 pt; composer input labelled; mic and camera have text labels; read-aloud
is a toggle with `pressed` state.

**Flags.** `FEATURE_VOICE` (mic, Read aloud), `FEATURE_PHOTO_ID` (camera).

**Open points.** OQ-111 (see §Open points): city-wide questions (no `place_id`) are not in API v1; the context chip
therefore never offers "whole city" in 0.1.

### SCR-035 Voice question and read-aloud

**Purpose and stories.** Ask by speaking with on-device STT, edit the transcript, send explicitly; hear a completed
answer (US-027, US-043; FR-059, FR-060, FR-063). Wireframe m10. Should; cut 3rd.

**Route, entry, exit.** `VoiceSheet` over SCR-034 (or over SCR-008 via the search-pill mic, which first opens
SCR-034 for the current place context). Entry: mic. Exit: *Dừng và gửi / Stop and send* → SCR-034 with the transcript
sent (`input_mode: VOICE_TRANSCRIPT`); *Huỷ / Cancel* → SCR-034; permission denied → banner on SCR-034.

**Layout (top → bottom).**

*Permission (first use only):* purpose line in-app before the OS dialog: *Để chuyển câu hỏi nói thành chữ ngay trên
thiết bị. Âm thanh không được lưu. / To turn your spoken question into text on this device. Audio is not stored.*;
then the OS prompt.

*Listening sheet:* title *Đang nghe… / Listening…* (`polite`); `Waveform` (static bars under reduced motion);
**editable transcript** `Field` (multiline) showing the live text *"{transcript}"*; line *Ngôn ngữ: {Tiếng Việt |
English} · chuyển giọng nói thành chữ trên thiết bị / Language: … · speech is transcribed on this device*; `Action`
primary *■ Dừng và gửi / Stop and send* (disabled while the transcript is empty); `TextLink` *Huỷ / Cancel*. After
Stop, the transcript stays editable with the button relabelled *Gửi / Send* so the user can correct it before sending.

*Answer with read-aloud (on SCR-034):* the traveler bubble shows a 🎙 glyph; the assistant bubble's `ReadAloudToggle`
reads *⏸ Đang đọc to — Dừng / Reading aloud — Stop* while speaking.

*Denied banner (on SCR-034):* *Micrô đang tắt. Bạn vẫn có thể gõ câu hỏi. Bật micrô trong Cài đặt của thiết bị nếu muốn
hỏi bằng giọng nói. / Microphone is off. You can still type your question. Turn the microphone on in your device settings
to ask by voice.* + *Mở Cài đặt / Open Settings*.

**Data shown.** Transcript (device only); STT language = app locale (vi-VN / en-US).

**Actions.** Stop and send / Send → API-028 with `{content: transcript, input_mode: VOICE_TRANSCRIPT}` (audio never
leaves the device, DC-007); Read aloud → `expo-speech` on the completed `content` only (not while streaming); Cancel →
discard.

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | After Stop: *Đang xử lý… / Processing…* until the final transcript | — |
| Empty (no speech) | Line + retry | Không nghe rõ. Thử lại hoặc gõ câu hỏi / Didn't catch that. Try again or type. |
| Error (STT unavailable) | Same as denied with text fallback | Không dùng được nhận dạng giọng nói trên thiết bị này. Hãy gõ câu hỏi. / Speech recognition is not available on this device. Please type your question. |
| Offline | STT may work; sending needs a connection: banner | S-2 |
| Permission | As above; never re-prompt automatically | — |

**Validation and limits.** Transcript ≤ 4000 characters; recognition stops after 30 s of audio or 3 s of silence.

**Accessibility.** Voice is never the only path (text composer always present); transcript announced politely;
read-aloud toggle has `pressed` state; waveform decorative; respects reduced motion.

**Flags.** `FEATURE_VOICE`. Testing STT needs a native build (AGENTS.md).

**Open points.** None (module choice is OQ-037, SAD).

### SCR-036 Photo identification

**Purpose and stories.** Identify a published place within 300 m from a photo; "not recognised" otherwise; camera and
location asked only at first use (US-028; FR-061, FR-062, FR-092, FR-093; BR-046). Wireframe m11. Should; cut 2nd.

**Route, entry, exit.** Route `/guide/photo`. Entry: camera button in SCR-034. Exit: *Mở thẻ địa điểm / Open place
card* → SCR-033; *✦ Hỏi về nơi này / Ask about it* → SCR-034 scoped to the place; *Tìm theo tên / Search by name* →
SCR-021; ✕ → SCR-034.

**Layout (top → bottom).**

*Capture:* dark `CameraView` full-screen, header ✕ + title *Nhận diện địa điểm / Identify a place*; bottom: shutter
72 pt labelled *Chụp / Take photo*; privacy line (text ≥ 4.5:1 on the dark frame, #DCEBF2 on #2C3E48): *Ảnh không
được lưu. Chỉ dùng một lần định vị để tìm địa điểm gần bạn; vị trí không được gửi tới AI. / The photo is not stored. One
location fix is used to find nearby places; it is not sent to AI.*

*Analyzing:* captured photo thumbnail, spinner, *Đang so khớp với địa điểm đã đối chiếu nguồn gần bạn… / Matching against
source-checked places near you…*

*Result sheet (matched):* thumbnail; cap *Kết quả gần nhất trong bán kính 300 m / Best match within 300 m*; result row
(`AccountRow`): glyph, primary name, secondary `{other name} · {category} · địa điểm đã đối chiếu nguồn / source-checked place`;
`Action` primary *Mở thẻ địa điểm / Open place card*, secondary *✦ Hỏi về nơi này / Ask about it*, `TextLink` *Không
phải nơi này / Not this place* (→ Search by name); privacy line.

*Not recognised:* thumbnail; title *Không nhận ra địa điểm / Not recognised*; body *Không có địa điểm đã đối chiếu nguồn nào
trong 300 m khớp với ảnh này. Bạn có thể tìm theo tên. / No source-checked place within 300 m matches this photo. You can search
by name instead.*; `Action` *Tìm theo tên / Search by name*, secondary *Chụp lại / Retake*.

*Permission denied:* title *Cần quyền máy ảnh và vị trí / Camera and location are needed*; body *Tính năng này chỉ dùng
ảnh và một lần định vị khi bạn chụp. Tìm kiếm, lập kế hoạch và câu hỏi bằng chữ vẫn hoạt động. / This feature uses the
photo and one location fix only when you take it. Search, planning and text questions still work.*; `Action` *Mở Cài đặt
/ Open Settings*.

**Data shown.** API-029 `POST /v1/ai/photo-identifications` (multipart `image`, `latitude`, `longitude`, `accuracy_m`,
`locale`, `session_id?`) → `outcome` (IDENTIFIED / NOT_RECOGNISED), `radius_m` (300), `place` (`PlaceSummary`: `id`,
`name`, `name_vi`, `category_code`, `thumbnail`).

**Actions.** Shutter → capture → resize to ≤ 5 MB (ASM-070), strip EXIF → one foreground location fix (≤ 10 s,
ASM-062) → API-029 → result; Retake; Open place card → SCR-033 (`place.id`); Ask about it → API-024 session for
`place.id`.

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | Analyzing view | — |
| Empty | Not recognised view | — |
| Error | Banner + Retake | Không nhận diện được lúc này / Could not identify right now |
| 413 / 415 | Banner + Retake | S-1 |
| Offline | Shutter disabled with reason | S-2 |
| Permission | Denied view | — |
| Location unavailable (no fix in 10 s) | Line + Search by name | Không xác định được vị trí / Location unavailable |

**Validation and limits.** JPEG/PNG/WebP ≤ 5 MB after resizing; one request at a time; `accuracy_m` sent when known.

**Accessibility.** Shutter labelled; results announced; privacy statement is plain text near the action; dark-frame
text contrast ≥ 4.5:1.

**Flags.** `FEATURE_PHOTO_ID`.

**Open points.** None (photo-set spike is TASK-018).

### SCR-037 Booking handoff sheet

**Purpose and stories.** Open a partner's stay, activity or transport search prefilled with the trip's city and dates;
optional indicative prices (US-029, US-030, US-031, US-037; FR-064..FR-067, FR-079..FR-081). Wireframe m12.

**Route, entry, exit.** `Sheet` over SCR-029 success, SCR-024 saved mode (⋯ → *Đặt chỗ / Book*), SCR-033 (Find
activities), SCR-031 row ⋯. Exit: partner row → external browser (`Linking.openURL`); *Đóng / Close*.

**Layout (top → bottom).** Sheet with handle. Context row `{city} · {day_count} ngày/days` + `Badge` *Đã lưu /
Saved*. Title per kind: *Tìm chỗ ở tại {city} / Find a stay in {city}* with `PrefillBadge` line *Nhận {start} · Trả
{end} · {nights} đêm / Check-in {start} · Check-out {end} · {nights} nights*; *Tìm hoạt động ở {city} / Find activities in
{city}* with *Từ điểm dừng: {stop name} / From stop: {stop name}*; *Tìm phương tiện đến {city} / Find transport to
{city}* with *Ngày đi {start} / Departing {start}*. `PartnerRow`s: ↗ glyph, `partner_display_name` (text only, no
logos), subtitle *Chỗ ở · {city} / Stays · {city}*, *Hoạt động, tour / Activities, tours*, *Xe, tàu / Bus, train*; trailing
↗. **Price section** (STAY only, flag): cap *Giá tham khảo / Indicative prices*; `PriceRow`s `{name}` · *từ {price}/đêm
/ from {price}/night* (or total stay); note *Lấy lúc {time} hôm nay. Đối tác xác nhận giá cuối cùng. Giá không được lưu
cùng chuyến đi. / Retrieved {time} today. The partner confirms the final price. Prices are not saved with your trip.* +
`attribution_text`. Footer line *Bạn sẽ rời Gonarra để mở trang đối tác. Gonarra không đặt chỗ hay nhận thanh toán. / You
will leave Gonarra for the partner's site. Gonarra does not book or take payment.* `Action` secondary *Đóng / Close*.

**Data shown.**

| Field | Source | Format |
|---|---|---|
| Partners | API-030 `GET /v1/trips/{trip_id}/handoff-links?kind=STAY\|ACTIVITY\|TRANSPORT[&stop_id]` → `items[].kind`, `partner_key` (agoda, booking_com, klook, twelve_go), `partner_display_name`, `url`, `start_date`, `end_date` | Check-out = `end_date` (start + day_count); nights = day_count |
| Prices | API-031 `GET /v1/trips/{trip_id}/stay-prices` → `items[].name`, `price.amount`, `price.currency`, `price_basis`, `handoff_url`, `retrieved_at`; page `notice`, `attribution_text`, `retrieved_at`; `Cache-Control: no-store` | Money format; never cached or stored |

**Actions.** Tap partner → open `url` externally (announce *mở trang ngoài / opens external site*); tap price row →
open `handoff_url` when present; Close.

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | 2 skeleton partner rows | — |
| Empty (no partner) | Card | Chưa có đối tác phù hợp. Không đối tác nào nhận được ngày nhận và trả phòng của bạn. Thử lại sau. / No suitable partner right now. No partner can accept your check-in and check-out dates. Try again later. |
| Error | Same card + *Thử lại / Try again* | S-1 |
| Prices unavailable (503 `price_provider_unavailable` or empty) | Section replaced by one line | Chưa lấy được giá tham khảo / Indicative prices are unavailable right now |
| Offline | Rows disabled | Cần kết nối / Connection needed |
| Blocked | Entry hidden on unsaved drafts (409 `trip_not_saved` defensive) | — |

**Validation and limits.** `stop_id` required for ACTIVITY; prices page `limit` ≤ 10 in the UI.

**Accessibility.** External links announced; prices include the currency in words for screen readers (*đồng /
Vietnamese dong*); sheet focus management as other sheets.

**Flags.** `FEATURE_STAY_PRICES` (price section only; handoff rows stay).

**Open points.** None.

### SCR-038 Account deletion and status

**Purpose and stories.** Delete the account with explicit confirmation; show in progress → completed or failed with
reason (US-033; FR-071, FR-072; BR-021). Wireframe m13.

**Route, entry, exit.** Routes `/settings/delete-account` (confirm) and `/settings/delete-account/status`. Entry:
SCR-010 Delete account; Welcome link *Trạng thái xoá tài khoản / Deletion status* while a deletion is pending (stored
flag on device). Exit: Keep my account → SCR-010; completed → *Về màn hình chào / Back to Welcome* → SCR-003.

**Layout (top → bottom).**

*Confirm:* `AccountShell` *Xoá tài khoản / Delete account*. Title *Xoá tài khoản? / Delete your account?*. Lead *Sẽ bị
xoá vĩnh viễn: / This permanently deletes:* + bullet list *Mọi chuyến đi đã lưu và bản nháp / All saved trips and
drafts*, *Sở thích du lịch / Travel preferences*, *Câu hỏi với Hướng dẫn AI / Your Guide questions*, *Tài khoản đăng
nhập (Clerk) / Your sign-in account (Clerk)*. Note *Việc xoá hoàn tất trong vòng 24 giờ. Bạn sẽ được đăng xuất. Thao tác
này không thể hoàn tác. / Deletion completes within 24 hours. You will be signed out. This cannot be undone.*
`ConfirmCheckbox` *Tôi hiểu dữ liệu của tôi sẽ bị xoá vĩnh viễn / I understand my data will be permanently deleted*.
`Action` destructive *Xoá tài khoản / Delete account* (disabled until ticked, helper *Đánh dấu ô trên để tiếp tục. /
Tick the box above to continue.*). `TextLink` *Giữ tài khoản / Keep my account*.

*Status:* `AccountShell` *Trạng thái / Status*. `StatusCard`: title *Trạng thái xoá tài khoản / Account deletion
status*; state line *◌ Đang xử lý / In progress*, *✓ Đã hoàn tất / Completed*, *⛔ Chưa hoàn tất / Not completed*; body
*Đã nhận yêu cầu lúc {time}. Sẽ hoàn tất trong vòng 24 giờ. / Requested at {time}. It will complete within 24 hours.*,
*Dữ liệu của bạn đã bị xoá. / Your data has been deleted.*, or `failure_reason` mapped: *Không xoá được tài khoản đăng
nhập. Hệ thống tự thử lại trong vòng 24 giờ. / Your sign-in account could not be deleted yet. It is retried automatically
within 24 hours.*; support line *Mã hiển thị để hỗ trợ (mã công việc xoá, không phải thông tin xác thực): {short id} /
Support display ID (deletion job id, not a credential or receipt): {short id}*. Completed adds `Action` *Về màn hình
chào / Back to Welcome*.

**Data shown.** API-006 response / API-007 `GET /v1/me/deletion` → `id` (shown as `DEL-{first 4}`), `status`
(REQUESTED, IN_PROGRESS, COMPLETED, FAILED), `attempt_count`, `failure_reason`, `requested_at`, `completed_at`.

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Delete account | API-006 `POST /v1/me/deletion` `{confirm: true}` + `Idempotency-Key` | 202 → status screen; device flag "deletion pending" set |
| Poll | API-007 every 10 s while on the status screen, and once on each app start while the flag is set | Status updates |
| 401 after IN_PROGRESS or COMPLETED was observed | — | Treated as COMPLETED (OQ-073, A-024): sign out locally, show completed |
| Back to Welcome | Clear local state | SCR-003 |

**States.** Loading: Delete *Đang gửi… / Submitting…*; error (request failed): banner, nothing deleted, try again;
409 `deletion_in_progress`: go to status; offline: Delete disabled with reason; guest: row hidden.

**Validation and limits.** Checkbox must be ticked; `confirm` is the literal `true`.

**Accessibility.** Destructive action never default-focused; explicit checkbox (WCAG 3.3.4); status uses `status`
role and text, not colour alone; the bullet list is a real list.

**Flags.** None. **Open points.** None.

### SCR-039 Language setting

**Purpose and stories.** Switch the interface language between Vietnamese and English; persists after restart and
with the account (US-034; FR-075, FR-076, FR-097). Wireframe m13 (row); screen pattern: Settings radio list.

**Route, entry, exit.** Route `/settings/language`. Entry: SCR-010 Language row. Exit: back (choice applied
immediately).

**Layout (top → bottom).** `AccountShell` *Ngôn ngữ ứng dụng / App language*. Body *Áp dụng cho toàn bộ ứng dụng và
nội dung địa điểm. Tên tiếng Việt luôn hiển thị. / Applies to the whole app and place content. Vietnamese names are
always shown.* Card with two `AccountRow` radios: *Tiếng Việt* (subtitle *Vietnamese*), *English* (subtitle *Tiếng
Anh*), check mark on the current one.

**Data shown.** Current locale: API-004 `locale` when signed in, else device setting (vi → vi, otherwise en;
README §10.2).

**Actions.** Tap a row → apply i18next locale immediately, store on device; signed in → API-005 `PUT
/v1/me/preferences` with the current `allowed_modes`, `interest_category_codes`, `pace`, times and the new `locale`
(full replace). Subsequent API calls send `locale`.

**States.** Busy: row shows a small spinner; error: banner S-1 (device choice is kept, server retried on next
preferences save); offline: device choice applied, server sync deferred.

**Validation and limits.** Locale ∈ {vi, en}.

**Accessibility.** `radiogroup`; each row announces its language name in that language; the screen title re-renders in
the new language on change and is announced.

**Flags.** None. **Open points.** None.

### SCR-040 Sign-in gate

**Purpose and stories.** Guests see Home and onboarding only; any private feature opens this gate (US-032 AC1, AC4;
FR-068; OQ-061). Wireframe m01.

**Route, entry, exit.** Sheet over the current screen. Entry: guest taps search, Plan a trip, Trips tab, AI guide
tab, place card, handoff, preferences Save. Exit: Email → SCR-005; Google/Apple → Clerk SSO → SCR-006; *Đăng nhập /
Sign in* link → SCR-004; *Để sau / Not now* → close, stay on Home.

**Layout (top → bottom).** Home sheet with handle. Title per feature: *Đăng nhập để lên kế hoạch / Sign in to plan a
trip*, *Đăng nhập để xem chuyến đi / Sign in to see your trips*, *Đăng nhập để hỏi Hướng dẫn / Sign in to ask the
Guide*, *Đăng nhập để tìm địa điểm / Sign in to search places*. Body *Chuyến đi, sở thích và câu hỏi của bạn chỉ thuộc về
tài khoản của bạn. / Your trips, preferences and questions belong only to your account.* `Action` primary *✉ Tiếp tục với
Email / Continue with Email*; `SocialActions` *Tiếp tục với Google / Continue with Google*, *Tiếp tục với Apple /
Continue with Apple*; `TextLink` *Đã có tài khoản? Đăng nhập / Already have an account? Sign in*; `TextLink` *Để sau /
Not now*.

**Data shown.** None. **Actions.** As exits; after sign-in the app returns to the feature that was tapped.

**States.** Busy (social); error inline (`authErrorMessage`); offline: *Cần kết nối để đăng nhập / A connection is
needed to sign in*, buttons disabled.

**Validation and limits.** n/a.

**Accessibility.** Modal dialog titled by the feature-specific heading; focus returns to the tapped control on close.

**Flags.** None. **Open points.** None.

---

## Part C — Curator admin (SCR-101..SCR-105), desktop 1280 pt

Shared admin chrome (`AdminShell`): left sidebar 260 pt `deepOcean` with wordmark *gonarra. Biên tập / Curator*
and nav *Ứng viên / Candidates*, *Địa điểm / Places*, *Lượt nhập / Import runs*, *Độ phủ / Coverage* (`nav`
landmark, `aria-current`); top bar 56 pt with page title, language switch *Ngôn ngữ: Tiếng Việt / Language: English*
(ASM-064) and the curator chip; content area max 1180 pt with 24 pt gutters; tables radius 14; focus ring 3 px
`tealText`; selected row #EAF6F8. Every admin error banner shows `error.code` and `X-Request-ID` (never a stack).
Admin screens are never used offline (desktop online, NFR-029).

### SCR-101 Admin sign-in

**Purpose and stories.** Curator signs in with Clerk; the curator role is checked server-side on every `/v1/admin`
call (US-004..US-009 entry; NFR-015). Inventory only (Clerk hosted UI).

**Route, entry, exit.** `apps/admin` route `/`. Entry: open the admin URL. Exit: signed in with role → SCR-102; signed
in without role → access-denied state (SCR-102 permission state); sign out → `/`.

**Layout.** Centred card 420 pt: wordmark, title *Đăng nhập biên tập viên / Curator sign-in*, Clerk `<SignIn />`
component (email + password, Google), note *Chỉ tài khoản có vai trò biên tập viên mới dùng được công cụ này. / Only
accounts with the curator role can use this tool.*

**Data shown.** None from the Gonarra API until the first `/v1/admin` call. **Actions.** Clerk sign-in; on success
the app calls API-042 to verify the role (403 → denied state).

**States.** Loading (Clerk); error (Clerk messages); denied → SCR-102 permission state with *Đăng xuất / Sign out*.

**Validation.** Clerk. **Accessibility.** Clerk component is keyboard operable; page has one `h1`.
**Flags.** None. **Open points.** Role claim location is OQ-036 (SAD).

### SCR-102 Candidate queue

**Purpose and stories.** Find the next candidate to review; filter by city, state, provider, AI drafts; search by
name (US-004 AC1, US-007 AC2, US-009 AC1; FR-009, FR-010, FR-017, FR-019; NFR-015). Wireframe a01.

**Route, entry, exit.** Route `/candidates` (query string carries filters: `city`, `state`, `provider`, `ai`, `q`,
`sort`, `cursor`; back-button safe). Entry: sidebar, SCR-101, SCR-104 "New candidates" link (filtered by run). Exit:
row → SCR-103.

**Layout (top → bottom).** `AdminShell`. Page title *Hàng chờ ứng viên / Candidate queue*. **Coverage strip
(SCR-105)**. `FilterBar`: selects *Thành phố: {city} ▾ / City*, *Trạng thái: tất cả ▾ / Status: all* (WorkflowState
values localized: *Đã nhập / Imported*, *Duyệt trùng khớp / Match review*, *Duyệt nội dung / Content review*, *Sẵn sàng
xuất bản / Ready to publish*, *Đã xuất bản / Published*, *Đã gỡ / Retired*), *Nguồn: tất cả ▾ / Provider: all* (client-side
from import runs), checkbox *Chỉ có bản nháp AI / AI drafts only*, search `Field` *Tìm theo tên / Search by name*.
Result line *{n} ứng viên · {city} · sắp xếp theo cập nhật / {n} candidates · {city} · sorted by last update*.
`DataTable` columns: *Tên (VI / EN) / Name (VI / EN)* (two lines; missing EN → *Thiếu tên tiếng Anh / English name
missing* in warn colour), *Thành phố / City*, *Nguồn / bản phát hành / Provider / release*, *Trạng thái / Status*
(`Badge` + *Có bản nháp AI / AI draft* badge), *Đầy đủ / Complete* (`gate_missing_count`: *Đủ / Complete* when 0,
else *Thiếu {n} / {n} missing*), *Cập nhật / Updated* (relative, *2 giờ trước / 2 h ago*). Pager *Tải thêm /
Load more*.

**Data shown.** API-033 `GET /v1/admin/candidates?city_id&workflow_state&q&sort=-updated_at|name&limit=50` →
`items[].id`, `city_id`, `slug`, `category_code`, `workflow_state`, `name_vi`, `name_en`, `content_revision`,
`has_ai_draft`, `updated_at`; `next_cursor`. Provider/release per candidate: `provider_release`; completeness: `gate_missing_count` (API 0.4.0, OQ-112 closed).

**Actions.** Filters → URL + API-033; row click / Enter → SCR-103; coverage tile click → `city` filter; sort header
click → `sort`.

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | Skeleton rows; status *Đang tải… / Loading…* | — |
| Empty | Card with CLI hint | Không có ứng viên ở {city}. Nhập dữ liệu bằng CLI rồi tải lại trang: `cli import overture --city {code} --release <release>` / No candidates in {city}. Import with the CLI, then reload: … |
| Error | Banner with code + request ID + *Thử lại / Try again* | Không tải được danh sách / Could not load candidates |
| Permission (403) | Page replaced | Tài khoản này không có vai trò biên tập viên. Mọi thao tác nhập, sửa và xuất bản đều bị chặn. Đăng xuất để dùng tài khoản khác. / This account does not have the curator role. Import, edit and publish are blocked. Sign out to use another account. · Đăng xuất / Sign out |

**Validation and limits.** `q` ≤ 120; `limit` ≤ 50.

**Accessibility.** Table `caption`, scoped `th`; rows focusable with Enter; filters labelled; badges carry text; names
wrap, table scrolls horizontally below 1280 (unsupported width).

**Flags.** None.

**Open points.** None. OQ-112 closed: `provider_release` and `gate_missing_count` are in API 0.4.0; the queue can be filtered by `import_run_id`.

### SCR-103 Place review / publish

**Purpose and stories.** Complete bilingual content and sourced facts per field, confirm AI drafts, publish only when
complete, unpublish with a reason (US-005, US-006, US-007, US-009; FR-011..FR-017, FR-019, FR-082..FR-084; BR-004,
BR-047). Wireframe a02.

**Route, entry, exit.** Route `/places/[placeId]`. Entry: SCR-102 row. Exit: back to the queue; Publish → stays with
the published panel; Unpublish → queue.

**Layout (top → bottom).** `AdminShell`; title `{name_vi} · {name_en}` + state `Badge`. **EvidenceTable** (one row
per field): columns *Trường / Field*, *VI*, *EN*, *Nguồn / Source*, *Giấy phép / ghi công / Licence / attribution*,
*Xác minh / Verified*, *Trạng thái / State*, *Thao tác / Action*. Rows: *Tên / Name*, *Tên gọi khác / Aliases*, *Mô tả
ngắn / Short description*, *Mô tả / Description*, *Danh mục / Category*, *Thời gian gợi ý / Suggested duration*
(min/suggested/max), *Vị trí / Location*, *Địa chỉ (VI) / Address (VI)*, *Lối vào / Entrance*, *Giờ mở cửa / Opening
hours*, *Giá vé / Admission*, other `fact_fields`, *Ảnh / Photos*, *Nội dung Hướng dẫn / Guide content* (chunks, see
OQ-113). State cell values: *✓ Đủ / Complete*, *✦ Bản nháp AI — chưa xác nhận / AI draft — not confirmed*, *Chưa rõ (có
nguồn) / Unknown (sourced)*, *⛔ Thiếu nguồn / No source*, *⛔ Thiếu / Missing*, *Có thể đã cũ / May be out of date*,
*Xung đột / Conflict*. Action cell: *Sửa / Edit* (opens the **field drawer**: VI and EN inputs with the built `Field`
style, value or *chưa rõ / unknown* toggle, source picker (API-040 list + *＋ Nguồn mới / New source* → API-041 form:
publisher, kind, homepage, licence, attribution text), verified date picker) or *Xác nhận / Confirm* for AI drafts.
**PublishPanel** (right column at 1280, below at narrower): heading *Sẵn sàng xuất bản? / Ready to publish?*; blockers
list *Chưa thể xuất bản — còn {n} mục / Cannot publish — {n} items left* with each `context.missing` item localized
(`MISSING_LOCALIZATION` → *Thiếu nội dung {vi|en} / Missing {vi|en} content*, `FACT_WITHOUT_SOURCE:{field}` → *{field}:
thiếu nguồn / no source*, `SOURCE_WITHOUT_ATTRIBUTION`, `CHUNK_WITHOUT_SOURCE`, `MEDIA_RIGHTS_MISSING`,
`FACT_CONFLICT_OPEN`, `IDENTITY_UNREVIEWED`, `OUTSIDE_CITY`, `MISSING_REQUIRED_FACT:{field}`, AI draft unconfirmed);
`Action` primary *Xuất bản / Publish* (disabled while blockers exist); state line *Trạng thái: {state} · phiên bản
{content_revision} / State: … · revision …*; `TextLink` *Cách ly / Quarantine* (sets RETIRED after confirmation).
Published variant: card *Đã xuất bản / Published* · *Xuất bản bởi {curator} lúc {time}, {date}. Khách du lịch tìm thấy
trong vòng 1 phút. / Published by {curator} at …. Travelers can find it within 1 minute.* · *Bản kê xuất bản #{revision}
/ Publication manifest #{revision}* · `Action` destructive *Gỡ xuất bản / Unpublish* + explanation.

**Data shown.** API-034 `GET /v1/admin/candidates/{place_id}` → `workflow_state`, `content_revision`,
`has_ai_draft`, `location`, `visit_minutes_*`, `localizations[]` (`locale`, `name`, `short_description`,
`description`, `translation_origin`, `review_state`, `reviewed_at`), `aliases[]`, `facts[]` (`field_code`,
`knowledge_state`, `value`, `verified_at`, `review_state`, `conflict_state`, `source_revision_ids[]`),
`publications[]` (`publication_revision`, `state`, `published_by_account_id`, `published_at`, `state_reason`);
API-040 sources (`publisher`, `source_kind`, `license_code`, `attribution_text`).

**Actions.**

| Trigger | Call | Result |
|---|---|---|
| Save a field (drawer) | API-035 `PATCH /v1/admin/candidates/{place_id}` `{expected_content_revision, localizations[]?, facts[]?, category_code?, visit_minutes_*?}` + `Idempotency-Key` | Row updated; `content_revision` + 1 |
| Confirm AI draft | API-035 `{expected_content_revision, confirm_ai_draft_locales: [vi|en]}` | Badge cleared |
| New source | API-041 `POST /v1/admin/sources` + `Idempotency-Key` | Source selectable |
| Publish | API-036 `POST /v1/admin/candidates/{place_id}/publish` `{expected_content_revision}` + **required** `Idempotency-Key` | 201 `CatalogPublication` → published variant |
| Unpublish → confirm | API-037 `POST /v1/admin/places/{place_id}/unpublish` `{expected_content_revision, reason}` + **required** `Idempotency-Key`; `AlertDialog` *Gỡ xuất bản {name}? Địa điểm sẽ không xuất hiện trong tìm kiếm, đề xuất và câu trả lời mới. Chuyến đi đã lưu vẫn giữ lịch sử. / Unpublish {name}? It stops appearing in new searches, proposals and answers. Saved trips keep their history.* + required reason `Field` | Queue (CONTENT_REVIEW) |

**States.**

| State | Treatment | vi-VN / en-US |
|---|---|---|
| Loading | Skeleton table | — |
| Empty (new candidate) | All rows *⛔ Thiếu / Missing* | — |
| Unknown | Allowed when sourced | Chưa rõ (có nguồn) / Unknown (sourced) |
| Stale | Row badge when `verified_at` > 180 days | Có thể đã cũ / May be out of date |
| Error 409 `revision_conflict` | Banner + reload; drawer keeps its values | Đã có người sửa. Tải lại / Changed elsewhere. Reload |
| Error 422 `publication_incomplete` | Blockers list from `context.missing` | admin.refused |
| Error 503 `ai_unavailable` (embedding on save, when adopted) | Banner; field saved, chunk stays unembedded | Chưa tạo được chỉ mục cho nội dung Hướng dẫn. Thử lại sau. / Guide content could not be indexed yet. Try again later. |
| Blocked | Publish disabled with named items | — |

**Validation and limits.** `name` ≤ 200, `short_description` ≤ 300, `description` ≤ 4000; visit minutes 5–600 with
min ≤ suggested ≤ max; a KNOWN fact needs a value, ≥ 1 source and a verified date; UNKNOWN needs ≥ 1 source; attribution
text 1–500; unpublish reason required.

**Accessibility.** Row headers (field) and column headers; blockers listed as text, not only red; drawer is a dialog
that traps focus and returns to the row's Edit button; keyboard-only path Tab → Edit/Confirm in each row.

**Flags.** None.

**Open points.** None. OQ-113 closed: the Guide row's Edit drawer edits `chunks[]` (API-034/API-035), one sectioned
chunk per topic (OVERVIEW, HISTORY, HIGHLIGHTS, VISIT_TIPS, ETIQUETTE, ACCESS) with VI and EN text and ≥ 1 source
each; a chunk with `embedding_state: PENDING` shows *Đang chờ nhúng / Embedding pending* and cannot be approved.

### SCR-104 Import runs

**Purpose and stories.** See which imports ran, what they created, why one failed; runs are started from the CLI
(US-004; FR-009, FR-010; DEC-009; ADR-006). Wireframe a03.

**Route, entry, exit.** Route `/imports` (`?run={id}` selects a row). Entry: sidebar. Exit: *Ứng viên mới / New
candidates* count → SCR-102 filtered by run (API-033 `import_run_id`, OQ-112 closed).

**Layout (top → bottom).** `AdminShell`; title *Lượt nhập / Import runs*; caption *Lượt nhập chỉ đọc; chạy bằng CLI
(DEC-009). / Read-only; runs are started from the CLI (DEC-009).* `DataTable` columns *Lượt / Run*, *Nguồn / Provider*,
*Bản phát hành / Release*, *Thành phố / City*, *Trạng thái / Status* (*Đang chạy / Running*, *Hoàn tất / Completed*,
*Thất bại / Failed*; a re-run with 0 new candidates shows *Hoàn tất (chạy lại, không đổi) / Completed (re-run, no
change)*), *Bản ghi đọc / Records read*, *Ứng viên mới / New candidates*, *Bị loại / Rejected* (numeric columns
right-aligned). `DetailPanel` for the selected run: title `{run} · {status}`, failure message line *{reason}. Mã:
{code}. Không có ứng viên nào được tạo; danh mục công khai không đổi. / {reason}. Code: {code}. No candidates were created;
the public catalog is unchanged.*, timing *Bắt đầu {start} · kết thúc {end} · phiên bản importer {v} / Started … · ended
… · importer version {v}*, re-run hint code block `cli import {provider} --city {code} --release <release>`. *Làm mới /
Refresh* button (no auto-polling).

**Data shown.** API-038 `GET /v1/admin/imports?city_id&limit=50` and API-039 `GET /v1/admin/imports/{import_run_id}`
→ `id`, `data_provider_id` (→ provider name via a small client map, or `Source` lookup), `provider_policy_id`,
`city_id`, `release_id`, `importer_version`, `status` (RUNNING, SUCCEEDED, FAILED), `record_count`, `accepted_count`,
`rejected_count`, `started_at`, `completed_at`. Failure reason: `failure_code`; duplicates skipped: `duplicate_count` (API 0.4.0, OQ-112 closed).

**Actions.** Row click → detail; Refresh → API-038; count link → SCR-102.

**States.** Loading skeleton; empty: *Chưa có lượt nhập nào. Bắt đầu bằng: `cli import overture --city hoi-an --release
<release>` / No import runs yet. Start one with: …*; error: banner with code + request ID; running: badge with started
time; permission: as SCR-102.

**Validation and limits.** n/a.

**Accessibility.** Table caption explains read-only; failure reason in text plus code; detail panel is a region
labelled by the run id.

**Flags.** None.

**Open points.** None. OQ-112 closed: `failure_code` and `duplicate_count` are in API 0.4.0.

### SCR-105 Coverage strip

**Purpose and stories.** Published places per city against the 30-place gate (US-008; FR-018; MET-011). Wireframe a01
(strip on SCR-102).

**Route, entry, exit.** Region at the top of SCR-102 (and sidebar entry *Độ phủ / Coverage* scrolls to it). Tile
click → SCR-102 filtered by that city.

**Layout.** Five `KpiTile`s in a row (gap 16): city name (vi/en per locale), big number `{published_count} / 30`,
meter bar (fill = min(published, 30)/30; `ok` colour at ≥ 30, `warn` below), caption *đã xuất bản / published*, small
line *{candidate_count} ứng viên / candidates*.

**Data shown.** API-042 `GET /v1/admin/cities/summary` → `items[].city_id`, `code`, `published_count`,
`candidate_count`; city names via API-008. The 30 threshold is a UI constant from MET-011 (50 is the stretch goal,
shown as a tick mark on the meter).

**Actions.** Tile click → city filter.

**States.** Loading: 5 skeleton tiles; error: one-line banner, tiles hidden; permission: as SCR-102.

**Validation and limits.** n/a.

**Accessibility.** Each tile is a button labelled *{city}: {n} trên 30 địa điểm đã xuất bản / {city}: {n} of 30
published places*; the meter is decorative with the number in text.

**Flags.** None. **Open points.** None.

---

## Open points raised by this document

New questions continue after OQ-107 (the highest in use across the docs set, in the Software Development Plan). Each
has owner Lê Ngọc Tấn Hiền. None blocks visual design; they affect the
contract or copy only.

| ID | Question | Screens | Needed by | Recommendation |
|---|---|---|---|---|
| OQ-108 | Should the selected city be stored with account preferences (`Preferences.current_city_id`) so Home follows the account across devices, or stay device-local? | SCR-008, SCR-020 | **Closed 2026-11-05 (A-029)** | **Adopted:** device-local for the study (one device per participant); no contract change. Revisit only if a second device is needed |
| OQ-109 | Map centre for a day with no stops: add `centre` (GeoPoint) to API-008 `City`, or derive from the first published place? | SCR-025 | **Closed 2026-11-05 (A-029)** | **Adopted:** `City.centre` (nullable GeoPoint, centroid of `cities.boundary`) added in API 0.4.0 |
| OQ-110 | May the place picker show a straight-line "{n} m away" hint computed on the device? BRU-006 forbids straight-line values for legs; a nearby hint is not a leg but could be mistaken for one. | SCR-028 | **Closed 2026-11-05 (A-029)** | **Adopted:** no distance hint in this release; if added later, label it *cách thẳng / straight line* and never show minutes |
| OQ-111 | City-wide Guide questions (no `place_id`) are not in API v1; the context chip cannot offer "whole city". | SCR-034 | Closed by the AI alignment decision (2026-11-05) | Place-scoped only; city-scoped hybrid retrieval is roadmap (ADR-010). The chip never offers "whole city" in this release |
| OQ-112 | `CandidateSummary` lacks provider/release and a gate-completeness count; `ImportRun` lacks a failure code and a duplicates-skipped count; the queue cannot filter by import run. The wireframes show all of these. | SCR-102, SCR-104 | **Closed 2026-11-05 (A-029)** | **Adopted** in API 0.4.0 / data model 0.4: `CandidateSummary.provider_release`, `gate_missing_count`; `ImportRun.duplicate_count`, `failure_code`; API-033 `import_run_id` filter |
| OQ-113 | Guide narrative chunks have no admin read/write operation on `main` yet (`CandidateDetail` has no chunks); SCR-103 shows the row read-only until then. | SCR-103 | **Closed 2026-11-05** (PR #4 merged) | **Adopted:** `chunks[]` on API-034/API-035 with embedding on save (ADR-012 0.3); SCR-103 shows one sectioned chunk per topic with VI/EN text and sources |

Assumptions reused from README §13: ASM-060 (request text ≤ 500), ASM-061 (15-minute duration steps), ASM-062
(10 s location fix), ASM-063 (24-hour times), ASM-064 (admin localized, ≥ 1280 px). New assumptions:

| ID | Assumption |
|---|---|
| ASM-104 | Search debounce 300 ms and ≤ 20 results per page satisfy NFR-001 on the study devices. |
| ASM-105 | Polling API-007 every 10 s on the status screen and once per app start is enough for FR-072 without push notifications. |

## Self-check

| Check | Result |
|---|---|
| Every screen of README §4 has a section (12 as-built + 21 new traveler + 5 admin = 38 IDs; the gaps in the numbering are unassigned in the inventory) | Pass |
| Every section has purpose, route/entry/exit, layout, data, actions, states, validation, accessibility, flags, open points | Pass |
| Every API reference uses an operation ID from `api-contract.md` §3.11 and field names from `openapi.yaml` | Pass (checked by grep) |
| Every US/FR cited exists in `user-stories.md` / PRD | Pass (checked by grep) |
| Copy follows README §10 (VI first, fixed honesty words, Asia/Ho_Chi_Minh, no truncation) | Pass |
| Agreed decisions reflected: citations with publisher and verified date or `insufficient_evidence`; Guide scoped to one place with a place chip; planner stages VALIDATING_REQUEST → CHECKING_HEALTH; form always beside free text; voice transcript editable with explicit Send; photo asks camera and location on first use; deletion in progress → completed with 401 after IN_PROGRESS = completed | Pass |

## Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Owner | Lê Ngọc Tấn Hiền | [Pending] | |
| Approver | trantrongminh | [Pending] | |
