# Gonarra — Requirements (v1.0, 2026-11-06)

This file is the single requirements baseline for Gonarra: objectives, scope, business rules, functional and
non-functional requirements, constraints and glossary. It is the input to `docs/architecture.md`,
`docs/api/openapi.yaml` and `docs/test-plan.md`, and the reference for every FR/NFR/BRU/MET ID used in code and tests.

| Field | Value |
|---|---|
| Owner | Lê Ngọc Tấn Hiền (student author, product owner, curator) |
| Mentor / approver | trantrongminh, FYP mentor — [Pending] at the M0 gate (DEC-013, DEC-015 need explicit confirmation) |
| Status | Draft 1.0, re-baselined 2026-11-06 (DEC-013..DEC-021) |
| Lineage | Condensed from BRD 0.4 / PRD 0.2 (git tag `docs-sdlc-full`); IDs preserved. Withdrawn or merged IDs are listed, never renumbered. |

## 1. Product and personas

Gonarra is a bilingual (VI/EN) AI travel planner and grounded local assistant for **Đà Nẵng**, including the
Hội An area (part of Đà Nẵng since the 2025 merger). A traveler describes a 1–3 day trip in Vietnamese or English,
receives a proposal built from curator-verified places (and, when the catalog is thin, web-found places that are
always labelled `WEB_UNVERIFIED`), sees whether each day fits (timeline, map, Plan Health with calendar rules),
edits it and keeps it only by an explicit Save. On site the traveler uses a bilingual place card, asks the Guide
anything about Đà Nẵng and receives answers with sources and trust labels, and hands off to booking partners. The
thesis claim is a *verified local layer*: every place, hour and answer carries a source, a verification date and a
trust label, which the user study measures against ChatGPT/Gemini.

- **P-01 Linh** — domestic weekend traveler, 27, Android, Vietnamese; 2 days in Đà Nẵng with a friend; wants a plan that fits and a driver-ready address.
- **P-02 Tom** — international first-time visitor, 34, iPhone, English only; 2 relaxed days in the Hội An area; cannot read Vietnamese addresses, distrusts unsourced AI answers.
- **P-03 Curator** — Lê Ngọc Tấn Hiền on a desktop browser; must publish ≥ 100 bilingual places alone and review the web-candidate queue. (P-04 study participants are P-01/P-02 under consent.)

## 2. Objectives and metrics

| ID | Objective (outcome) | Metrics |
|---|---|---|
| BO-001 | Travelers obtain a valid 1–3 day Đà Nẵng itinerary from trusted, labelled local content with little effort | MET-001, MET-002, MET-003 |
| BO-002 | Travelers can judge feasibility (hours, legs, calendar) and change a trip without losing their choices | MET-004, MET-005, MET-006 |
| BO-003 | Travelers act on local information they can trust, recognise uncertainty and see what is unverified | MET-007, MET-008, MET-014 |
| BO-004 | The project operates a private Đà Nẵng service on free tiers, with a reviewed catalog above the release gate | MET-011 |
| BO-005 | The product is evaluated with real users against ChatGPT/Gemini before submission | MET-014, MET-001..003 |

| ID | Metric | Formula / data | Target |
|---|---|---|---|
| MET-001 | Planning task completion | participants who save a valid itinerary ÷ participants (study) | ≥ 80% |
| MET-002 | Time to first proposal | median minutes from first request to first displayed proposal (study) | ≤ 3 min |
| MET-003 | Perceived usability | mean SUS score (post-task questionnaire) | ≥ 70 |
| MET-004 | Conflict detection | conflict-set scenarios (incl. calendar cases) whose blocking conflict is flagged ÷ scenarios | 100% |
| MET-005 | Lock integrity | locked stops whose place, day or duration changed after regeneration | 0 |
| MET-006 | Saved-trip integrity | saved itineraries changed without Save + unsaved edits lost, under failure injection | 0 |
| MET-007 | Guide grounding | sampled answers fully supported by their cited evidence ÷ sampled answers (human review) | ≥ 95% |
| MET-008 | Correct refusal | out-of-evidence questions answered `insufficient_evidence` ÷ such questions | ≥ 90% |
| MET-011 rev. 1 | Catalog coverage (release gate) | published, reviewed, bilingual places in Đà Nẵng, of which in the Hội An area (weekly report) | ≥ 100 Đà Nẵng; ≥ 30 Hội An area |
| MET-014 | Comparative accuracy and trust | per participant, same Đà Nẵng prompt in Gonarra and in ChatGPT or Gemini: errors per day (closed place, wrong hours, non-existent place), trust rating (Likert), and whether the trust label was noticed | Gonarra errors/day < baseline; label noticed by majority; targets fixed in `docs/test-plan.md` before the study |

Withdrawn as standalone metrics (thresholds kept where named): MET-009 → FR-061 acceptance; MET-010 → NFR-012;
MET-012 → NFR-033; MET-013 → §9 CON-003 (10–15 consenting participants, ≥ 4 per language, by 2027-01-31).

## 3. Scope

**One city: Đà Nẵng** (`cities` keeps `da-nang` enabled only; Hà Nội, TP. Hồ Chí Minh and Huế are roadmap). One trip = 1–3 days.

| Priority | Items |
|---|---|
| Must | Place search; proposal from a prompt plus preferences; timeline and map; Plan Health incl. calendar rules; edits and explicit Save; place card; city-level text Guide with sources; trust label on every surface; catalog-first research agent with Places check and curator queue; booking handoff links (Agoda, Booking.com, Klook, 12Go); accounts and deletion; curator tool with closure-rule curation |
| Should | Stop lock with single-day regeneration; voice questions (on-device STT/TTS); photo identification of published places within 300 m; Today view; trip deletion; AI drafts in the curator tool |
| Could | Indicative stay prices (LiteAPI) behind a flag, never stored |
| Won't (roadmap) | Other cities; in-app booking or payment; flights; social features; multi-city trips; check-in or GPS arrival; audio tours; turn-by-turn navigation; **unlabelled** web content; an LLM team leader or AgentOS service |

- **Cut order if late (DEC-003 rev. 1):** prices → photo → voice → lock/regeneration → iOS. Never cut bilingual content, the Đà Nẵng catalog gate (MET-011 rev. 1) or explicit Save.
- **Release gate:** MET-011 rev. 1 met; all Must FRs pass; MET-004 = 100%, MET-006 = 0, MET-007 ≥ 95%, MET-008 ≥ 90%; Should/Could features pass or are recorded as cut.

## 4. Business rules

| ID | Rule |
|---|---|
| BRU-002 | A model may **propose** a `WEB_UNVERIFIED` candidate for the curator queue. It never publishes a place and never authors a displayed fact, opening hour, price, distance or duration; such values in model output are rejected by validation. |
| BRU-003 | A place is `VERIFIED` (published) only after curator review with bilingual content, at least one source per operational fact and rights clearance. A web-found place stays `WEB_UNVERIFIED` until promoted and published. |
| BRU-004 | Provider data is stored only under a named provider policy (provider, field, purpose, class, TTL); unknown combinations are not stored. |
| BRU-005 | Indicative prices are shown at viewing time only and never stored with a trip. |
| BRU-006 | Travel distance and duration come only from Google Routes, never from a model or a straight-line estimate. |
| BRU-007 | Each trip covers one city — Đà Nẵng, including the Hội An area — and 1–3 days. |
| BRU-008 | Logs contain no access tokens, precise locations, questions or transcripts, or full AI prompts. |

BRU-001 remains withdrawn (duplicate of FR-040).

## 5. Functional requirements

Priorities are MoSCoW. "Golden set", "conflict set" and other evaluation sets are frozen in `docs/test-plan.md`
before tuning. Verified behaviour of providers, devices and bilingual content is claimed only from live runs.

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| **Catalog & trust** | | | |
| FR-001 | The traveler app shall present Đà Nẵng as the current and only enabled city, with its travel areas (e.g. Hội An Old Town) as filters. | Must | `/v1/cities` returns exactly one enabled city with its areas; 100% of search results belong to Đà Nẵng. |
| FR-002 | Gonarra shall return published Đà Nẵng places matching a query by Vietnamese name, English name or reviewed alias, ignoring case and diacritics. | Must | 30 name/alias searches plus 10 diacritic-free queries: the target place is in the first 5 results in 100% of cases. |
| FR-003 | Gonarra shall show a place's details in the chosen language — both names, description, category, area, suggested duration, map position — with the Vietnamese name always visible. | Must | 20 random published places: all elements present or labelled unknown; Vietnamese name shown in both locales. |
| FR-004 | Gonarra shall exclude unpublished candidate places from search, place details, proposals, Guide answers and photo results; a web-found place appears only as a stop or citation labelled `WEB_UNVERIFIED`. | Must | 10 candidates: 0 appear in any output; a direct ID request returns `not_found`; every web-found appearance carries the label. |
| FR-005 | For each displayed operational fact, Gonarra shall show its source and verification date, show "unknown" when no supported value exists, and label it stale after 180 days. | Must | 20 places: 0 facts without source and date; 5 missing facts show "unknown"; stale label at 181 days, none at 179. |
| FR-008 | Gonarra shall display the attribution recorded for a data source wherever that source's data is shown. | Must | Inspection of every traveler screen showing provider or open-data content finds the attribution; 0 misses. |
| FR-098 | Gonarra shall show a trust label — `VERIFIED` or `WEB_UNVERIFIED` with source URL and fetched date — on every surface that shows a place: search result, proposal stop, timeline, map, place card and Guide citation. | Must | Inspection of all six surfaces for one trip containing a web-found stop finds the label on 100% of items; a `fetched_at` older than 7 days shows a stale mark. |
| **Planning** | | | |
| FR-020 | Gonarra shall accept a trip request as free text in Vietnamese or English and as a structured form (city, start date, days 1–3, day windows, pace, interests, travel modes, must-sees) usable without free text. | Must | Golden-set requests in both languages accepted; a proposal can be requested from the form alone. |
| FR-022 | When start date or number of days is missing or ambiguous, Gonarra shall ask for it before generating a proposal. | Must | 100% of golden requests with a missing field receive a `clarification_required` naming it; 0 proposals generated first. |
| FR-086 | Gonarra shall refuse a request for more than 3 days, more than one city, or a city other than Đà Nẵng, and state the reason. | Must | 4-day, two-city and Nha Trang requests are each refused with the reason; 0 model or provider calls recorded. |
| FR-025 | Gonarra shall generate a proposal with the requested number of days from a pool of published Đà Nẵng places ranked by the selector agent; items referencing IDs outside the pool are discarded, must-sees are included or a reason is stated, and web-found places are added only as `WEB_UNVERIFIED` stops (FR-099). | Must | Golden set: 100% of proposals have the requested day count; 100% of `VERIFIED` stops are published Đà Nẵng places; 100% of injected unknown or other-city IDs discarded; planning completes with the rule-based fallback when the selector fails. |
| FR-029 | For each leg, Gonarra shall show mode, distance and duration from Google Routes (cache or live), or show the leg as unavailable. | Must | Every golden leg shows provider values or "unavailable"; 0 straight-line or model-estimated values. |
| **Plan Health** | | | |
| FR-027 | Gonarra shall show each day as an ordered timeline with arrival and departure times computed by the deterministic scheduler, and the same revision on a map with synchronised selection. | Must | Every golden day shows non-overlapping ordered times; map and timeline carry the same revision id; selection syncs both ways. |
| FR-030 | Gonarra shall flag each conflict at the affected stop, leg or day with type (`CLOSED_AT_PLANNED_TIME`, `CLOSED_ON_DATE`, `LUNAR_EVENT_CONFLICT`, `TICKET_VALIDITY`, `SEASONAL_WARNING`, `LEG_MODE_RESTRICTED`, `LEG_UNAVAILABLE`, `DAY_WINDOW_EXCEEDED`, `WEB_PLACE_UNVERIFIED`, `WEB_PLACE_UNRESOLVED`), severity and, for calendar conflicts, rule id and date. | Must | MET-004 = 100% on the conflict set; each flag names the stop/leg/day and type. |
| FR-031 | Gonarra shall show Plan Health as `BLOCKED` (any blocking conflict), `WARNING` (any non-blocking issue) or `GOOD`, with reasons; a plan containing a `WEB_UNVERIFIED` stop is capped at `WARNING`. | Must | Status is `BLOCKED` iff a blocking conflict exists (100%); 5 plans with a web-found stop and no other issue show `WARNING`, never `GOOD`. |
| FR-032 | Gonarra shall refuse to save a `BLOCKED` proposal and show the reason. | Must | 100% of conflict-set saves refused with `plan_blocked` and reasons. |
| FR-102 | Plan Health shall apply curator-reviewed calendar rules — weekly closures, fixed dates, lunar dates (incl. Tết and Hội An lantern nights), ticket validity and seasonal notices — to each stop's planned date. | Must | Calendar conflict set (incl. Tết 2026-02-17, 2027-02-06 and a lantern night): recall 100%; lunar conversion passes its golden vectors. |
| FR-103 | Gonarra shall expose the city calendar (effective closure rules and events for a date range) to the traveler app. | Should | `GET /v1/cities/da-nang/calendar` for a 3-day range returns every approved rule effective in the range and none outside it. |
| **Edit & Save** | | | |
| FR-033 | Gonarra shall let the traveler move a stop to another position within its day or to another day. | Must | New order and recalculated times shown; after Save and reopen, the order persists. |
| FR-034 | Gonarra shall let the traveler add, remove or replace a stop using a published Đà Nẵng place or a web-found candidate (labelled). | Must | Same-city add/replace succeeds; a non-Đà Nẵng place is refused; a removed stop and its legs are absent after Save. |
| FR-037 | Gonarra shall let the traveler change a stop's visit duration and a leg's mode between walking and driving. | Must | Departure and later times update; the leg's distance and duration come from Google Routes. |
| FR-039 | After each edit, Gonarra shall recalculate affected times, legs and Plan Health and keep Save unavailable until done. | Must | For each edit type, recalculated values shown, new blocking conflicts flagged, Save disabled during recalculation. |
| FR-040 | Gonarra shall persist an itinerary only on explicit Save and label any differing proposal as unsaved. | Must | Closing the app, leaving the screen, regeneration or a route refresh without Save leave the saved trip unchanged; unsaved label until Save. |
| FR-041 | Save shall be idempotent (`Idempotency-Key`) and refused against a stale trip revision. | Must | Repeated Save creates one version; a Save from a stale copy returns `revision_conflict` and the second device's edits remain. |
| FR-043 | When a model, research, routing or network call fails or arrives late, Gonarra shall keep the saved itinerary and unsaved edits unchanged. | Must | Under injected failures, 100% of runs keep the saved trip and the edits (MET-006 = 0). |
| FR-045 | Gonarra shall list the traveler's saved trips, reopen each at its last saved version and delete one after confirmation. | Must (delete: Should) | 3 trips listed and reopened at the last version; confirmed deletion removes a trip, cancelled keeps it. |
| FR-047 | Gonarra shall let the traveler lock and unlock a stop, show the lock, and keep a locked stop's place, day and duration through regeneration. | Should | Lock persists after Save and reopen; MET-005 = 0 over the regeneration set. |
| FR-048 | Gonarra shall regenerate one selected day, leaving other days unchanged, as a new unsaved proposal. | Should | Regenerating day 2 leaves day 1 identical; reopening before Save shows the previous saved version. |
| **Place card** | | | |
| FR-051 | For each stop of a saved itinerary, Gonarra shall provide a place card with both names, a Vietnamese address for a driver or "unknown", the verified entrance or "unknown", the trust label and applicable closure rules. | Must | One saved trip with ≥ 5 stops: every card shows all items; ≥ 90% of stops show an address. |
| FR-054 | From a place card, Gonarra shall open the device maps app with directions to the entrance, or to the place position when the entrance is unknown. | Must | On one Android and one iOS device, 5 stops open at the expected coordinates. |
| FR-055 | Gonarra shall show a Today view of the saved day matching the device date, else day 1. | Should | Device date on day 2 lists day 2; outside the trip dates lists day 1. |
| **Guide** | | | |
| FR-104 | Gonarra shall provide a Guide session scoped to the city (Đà Nẵng), a place or a trip, with conversation history rebuilt by code (last 4 turns). | Must | `POST /v1/guide/sessions` with scope `CITY` accepts questions about Đà Nẵng without a place id; place and trip scopes restrict evidence accordingly. |
| FR-056 | Gonarra shall answer a text question in the selected language with claims that each cite supplied evidence. | Must | MET-007 ≥ 95% on the Guide sample; 100% of answers in the selected language. |
| FR-058 | Gonarra shall build Guide evidence by hybrid retrieval over approved facts and chunks (entity → lexical → vector, rank fusion) and shall drop any claim whose evidence IDs are not in the supplied set. | Must | Citation validity ≥ 95% on the Guide sample; 0 citations to IDs outside the retrieved set. |
| FR-078 | Gonarra shall list with each answer at least one source with its verification date, or for web evidence its URL, fetched date and `WEB_UNVERIFIED` label. | Must | Every answer in the Guide sample lists ≥ 1 source; web citations carry URL, date and label. |
| FR-057 | When evidence does not support an answer, Gonarra shall return `insufficient_evidence` instead of answering. | Must | MET-008 ≥ 90%; precision and recall of the status ≥ 90% on the out-of-evidence set. |
| FR-105 | When catalog evidence is insufficient and quota allows, Gonarra shall run the research agent and answer with status `ANSWERED_WEB_UNVERIFIED`, every claim cited to a fetched page. | Must | 10 web-only questions: answers carry the status and labelled web citations, or `insufficient_evidence`; 0 unlabelled web claims; 0 runs when the daily Tavily cap is reached. |
| **Research agent & curator queue** | | | |
| FR-099 | Gonarra shall run the research agent only when the catalog pool for the request is thin or the selector reports unmet requests, within per-plan caps (≤ 2 searches, ≤ 3 fetches, ≤ 3 Places checks). | Must | Golden requests with a sufficient pool record 0 research calls; a thin-pool request records ≤ the caps; the threshold is set from the research spike (OQ-127). |
| FR-100 | Each web-found candidate shall pass a Google Places existence and status check before it becomes a `WEB_UNVERIFIED` stop; unresolved candidates are dropped or flagged `WEB_PLACE_UNRESOLVED`. | Must | 10 fixture candidates: existing ones become stops, non-existent ones are never shown; only `place_id` is stored canonically. |
| FR-101 | The curator tool shall list web-found candidates with their source URL, fetched date, extraction and check outcome, and let the curator promote one to a candidate place or reject it. | Must | Promote creates an `IMPORTED` place with a localisation draft linked to the candidate; reject marks it and hides it from proposals; trips holding it upgrade to `VERIFIED` only after publication. |
| **Booking handoff** | | | |
| FR-064 | From a saved itinerary, Gonarra shall open a stay partner (Agoda, Booking.com) with Đà Nẵng and the trip's dates, an activity partner (Klook) from a stop, and a transport partner (12Go) with Đà Nẵng as destination and the start date. | Must | Each listed partner opens with the parameters filled; a partner that cannot accept dates is not listed. |
| **Accounts & privacy** | | | |
| FR-068 | Gonarra shall require sign-in for trips, preferences and questions, let the traveler sign out, deny access to another traveler's resources and check ownership before any model or provider call. | Must | Unauthenticated and cross-account requests refused for every private resource type; 0 external calls during refused requests. |
| FR-070 | Gonarra shall exclude account identifiers, contact data and precise location from content sent to any AI or search provider (Gemini, Groq, Tavily, Google Places); the redactor fails closed. | Must | 20 recorded requests per provider contain 0 such items; a request that cannot be redacted is not sent. |
| FR-071 | After confirmed account deletion, Gonarra shall delete the traveler's private data within 24 hours and show the status until done. | Must | At 24 h: 0 records in database, identity provider and logs; backups expire within 7 days and a test restore re-applies the deletion; status shows in progress → completed/failed. |
| FR-073 | Gonarra shall let the traveler save travel preferences explicitly and prefill the form from them. | Should | Stored only after explicit save; saved pace and interests prefilled in a new request. |
| FR-074 | Before the first use of planning or the Guide, Gonarra shall tell the traveler that request content goes to external AI and search providers and that identity and precise location do not. | Should | Notice shown once per account, in the selected language. |
| FR-075 | Gonarra shall let the traveler choose Vietnamese or English and show all traveler-facing text in that language. | Must | Switch works both ways and persists; 0 untranslated strings on all screens in each locale. |
| FR-077 | For study accounts, Gonarra shall record a pseudonymous session log (participant code, language, request time, first-proposal time, Save outcome, research used) without request or question text. | Should | One log per session with the fields and 0 free text; none for non-study accounts. |
| FR-106 | Gonarra shall enforce free-tier quota caps per account/day and per provider/day via a ledger, and degrade gracefully: selector fallback, no rationales, no research, `insufficient_evidence`, never a failed save. | Must | Exceeding each cap returns `quota_exhausted` or the degraded path; 0 provider calls above a cap; saved trips and edits unchanged. |
| **Voice / Photo / Prices (Should / Could)** | | | |
| FR-059 | Gonarra shall accept a spoken question (on-device STT) with an editable transcript and explicit Send, and read a completed answer aloud (on-device TTS); microphone permission is requested on first use and text input always remains. | Should | ≥ 8 of 10 spoken questions per language yield an answer meeting FR-056; audio matches displayed text; no prompt at app start; denied permission keeps text working. |
| FR-061 | Gonarra shall identify a published place within 300 m from a photo, or state "not recognised"; camera and location permissions are requested on first use. | Should | First result correct for ≥ 85% of the photo set; ≥ 90% of 20 non-catalog photos "not recognised". |
| FR-066 | Gonarra shall show indicative stay prices for the trip's dates with retrieval time and a partner-confirmation notice, behind a flag, and never store them. | Could | Prices for ≥ 1 stay or a hidden section with message; 100% carry time and notice; 0 prices in saved-trip records. |
| **Admin (curator tool)** | | | |
| FR-009 | The curator tool shall import candidate places for Đà Nẵng from a named open-dataset release without duplicates or changes to published places. | Must | Import tags candidates with the release; re-import yields the same count; published set unchanged. |
| FR-011 | The curator tool shall let the curator record bilingual names and descriptions, area, and for each operational fact a value or "unknown" with at least one source and verification date. | Must | Values for 5 candidates and all four fact types persist after reload. |
| FR-013 | Gonarra shall refuse publication of a candidate lacking Vietnamese content, English content, a source for any fact or an attribution entry for a cited source, naming each missing item. | Must | Each incomplete case refused with the item named; a complete candidate publishes. |
| FR-014 | The curator tool shall publish a complete candidate (visible in search within 1 minute, reviewer and time recorded) and unpublish a place back to the candidate set. | Must (unpublish: Should) | 5 publications visible within 1 min with reviewer/time; an unpublished place is absent from new searches, proposals and answers. |
| FR-016 | The curator tool shall record each source's licence and required attribution text. | Must | 5 sources show licence and attribution after reload. |
| FR-018 | The curator tool shall show published-place counts for Đà Nẵng and per area against the gate (≥ 100 / ≥ 30). | Should | Counts equal the catalog report (MET-011 rev. 1). |
| FR-019 | The curator tool shall mark model-drafted content "AI draft" until confirmed and refuse publication while any draft is unconfirmed. | Should | Every drafted field marked; publish refused with ≥ 1 unconfirmed field, allowed after confirmation. |
| FR-107 | The curator tool shall let the curator create, review and expire closure rules (place/area/city; weekly, date, lunar, season, ticket validity) with bilingual notes and a source; models never write rules. | Must | A rule is applied by Plan Health only when `review_state` is approved; 0 rule rows written by any model path. |

Merged (kept IDs absorb the listed ones): FR-003 ← FR-076; FR-005 ← FR-006, FR-007; FR-009 ← FR-010; FR-011 ← FR-012;
FR-013 ← FR-082, FR-083; FR-014 ← FR-015, FR-017; FR-019 ← FR-084; FR-020 ← FR-021; FR-025 ← FR-024, FR-026, FR-087;
FR-027 ← FR-028, FR-088; FR-034 ← FR-035, FR-036; FR-037 ← FR-038; FR-039 ← FR-089; FR-040 ← FR-090; FR-041 ← FR-042;
FR-043 ← FR-044; FR-045 ← FR-046; FR-047 ← FR-049, FR-091; FR-048 ← FR-050; FR-051 ← FR-052, FR-053; FR-059 ← FR-060, FR-063;
FR-061 ← FR-062, FR-092, FR-093; FR-064 ← FR-065, FR-079; FR-066 ← FR-067, FR-080, FR-081; FR-068 ← FR-069, FR-094, FR-095;
FR-071 ← FR-072; FR-073 ← FR-096; FR-075 ← FR-097; FR-086 ← FR-023, FR-085.
Withdrawn: none (FR-058 "no runtime web search" is superseded by its new wording and FR-105, DEC-015).

## 6. Non-functional requirements

| ID | Requirement | Threshold / verification |
|---|---|---|
| NFR-001 | Place search shall display results quickly. | p95 ≤ 2 s over 100 scripted queries, device timing. |
| NFR-002 | Proposal generation, including research when triggered, shall complete with a visible progress stream. | p95 ≤ 60 s for 3-day golden requests; first SSE stage within 2 s. |
| NFR-004 | Recalculation after an edit shall be fast. | p95 ≤ 5 s over 50 scripted edits. |
| NFR-006 | A Guide answer with sources shall complete quickly, streaming validated text. | p95 ≤ 15 s incl. web fallback; first text within 5 s. |
| NFR-008 | The service shall be available during scheduled study sessions and recoverable. | ≥ 99% of 1-minute probes per session; RTO ≤ 4 h, RPO ≤ 24 h (restore drill); failure of any single provider leaves search, place cards and saved trips working. |
| NFR-012 | Security: traffic encrypted in transit and private data at rest; invalid, expired or foreign credentials rejected; curation and queue operations limited to the curator; secrets never in clients. | 0 non-TLS endpoints; 0 unencrypted stores; 0 accepted invalid credentials; 0 cross-account disclosures (former MET-010); 0 secrets in builds. |
| BR-046 | Privacy: no account identifiers, contact data or precise location reach Gemini, Groq, Tavily or Google Places; the user is told what is sent (FR-074). | 20 recorded requests per provider, 0 findings; redactor unit tests fail closed. |
| NFR-017 | Logging: logs, traces and AI invocation records exclude tokens, precise locations, question text, transcripts and full prompts (BRU-008). | 0 occurrences in logs of a full HA-02 and Guide run. |
| NFR-022 | Accessibility (WCAG 2.1 AA, selected criteria): screen-reader labels in both languages, text contrast ≥ 4.5:1, usable at 200% system text. | 0 unlabelled controls; 0 contrast failures; 0 truncated essential text on key screens. |
| NFR-026 | Bilingual parity: VI and EN are both reviewed locales; times in UTC+7 regardless of device zone; diacritics render correctly. | 0 untranslated strings per locale; 0 wrong times of 20; 0 corrupted diacritics in a 50-place sample. |
| NFR-032 | Determinism: for identical inputs (candidate pool, route matrix, windows, rules) the scheduler and Plan Health produce identical output; acceptance runs are reproducible with recorded providers. | Snapshot equality on two runs; 0 pass/fail differences on re-run. |
| NFR-033 | Cost: cash spend USD 0 through 2027-01-31; quotas (FR-106) never interrupt a study session. | Weekly billing review; 0 quota failures logged during sessions; AWS spend within credits if used. |

NFR-003, 005, 009..011, 013..016, 018..021, 023..025, 027..031, 034..038 are absorbed by the rows above or by
`docs/test-plan.md` (compatibility, maintainability and release checks); no NFR is withdrawn.

## 7. Provider-data rules (ADR-006 summary)

- Every provider field is classified `CANONICAL`, `EPHEMERAL` (with TTL), `IDENTIFIER_ONLY` or `DENY` under a named policy row; unknown provider/field/purpose combinations are denied (BRU-004). Raw provider bodies are never logged.
- Google Places: only `place_id` is stored canonically; lat/lng are ephemeral (≤ 30 days, pending OQ-124); `business_status` and `opening_hours` are `DENY` — fetched at view or check time, shown with retrieval time and Google attribution, never persisted.
- Google Routes: pairwise distance and duration are cached ≤ 30 days keyed by (from, to, mode); day-start anchors are fixed points, never user GPS; no model or straight-line value is accepted (BRU-006).
- Tavily and fetched pages: search results and extracted text are ephemeral (7 days, pending OQ-122); a fetched page's URL, hash and `retrieved_at` are kept as an immutable source revision; Groq receives only redacted page text (OQ-123).
- Open data (Overture, Foursquare OS Places, Wikidata) keeps licence and attribution per source and displays it (FR-008, FR-016); LiteAPI prices are never stored (BRU-005).

## 8. Constraints and assumptions

| ID | Statement | Impact if wrong / validation |
|---|---|---|
| CON-001 | Free tiers only: Gemini, Groq, Tavily, Google Maps Platform monthly credit, Clerk free plan; AWS credits (USD 200) if hosted there. | Caps and fallback chains in design (FR-106); re-read provider terms on coding day. |
| CON-002 / ASM-004 | One person curates and reviews everything; ≥ 15 places reviewed per week from 2026-11-16. | < 10/week for two weeks triggers the cut order; weekly count in `progress.md`. |
| CON-003 / ASM-002 | FYP submission early February 2027; planning date 2027-02-01; study with 10–15 consenting participants (≥ 4 per language) by 2027-01-31. | Confirm date with faculty (OQ-002); ethics/consent (OQ-004). |
| CON-005 | Stack: Expo SDK 58 + Clerk (mobile), React + Vite (admin), Python 3.12 FastAPI + SQLAlchemy 2 + Alembic, PostgreSQL 16 + PostGIS + pgvector, OR-Tools, Agno 3.1.12 (imports confined to `app/agents/`, `app/ai/`). | Pin versions from the day-1 spike (OQ-126). |
| ASM-017 | The Hội An area contains ≥ 30 publishable places reachable within the gate. | MET-011 rev. 1 missed; count after 4 weeks of curation (2026-12-15). |
| ASM-018 | Tavily free tier (≈ 1 000 credits/month) covers development and the study with daily caps and 300 credits reserved. | Research disabled near the study; ledger in `ai_quota_ledger` (OQ-122). |
| ASM-019 | Hybrid retrieval with `pg_trgm` + pgvector gives acceptable Vietnamese recall without `unaccent`/tsvector. | Guide misses evidence; retrieval spike on the Guide golden set (2027-01-06). |
| ASM-020 | Groq free-tier models extract facts from VI/EN pages well enough for `WEB_UNVERIFIED` candidates. | Research precision too low; manual count in the research spike (2026-12-08). |
| ASM-021 | Agno agents run in-process in FastAPI without workers within a 2 GiB host. | Architecture change; day-1 spike and load test before the study (2026-11-20). |
| ASM-022 | The post-merger Đà Nẵng boundary and the Hội An area can be defined from a licensed open dataset. | `OUTSIDE_CITY` rejects Hội An places; travel-area list instead of wards (OQ-121). |

## 9. Glossary

| Term | Definition |
|---|---|
| Published place (`VERIFIED`) | A place the curator reviewed and published with sources and VI/EN content; the only kind the selector may pick. |
| Web-found place (`WEB_UNVERIFIED`) | A place found by the research agent on the open web, checked for existence via Google Places, shown with source URL and fetched date; saveable as a stop; caps Plan Health at `WARNING`. |
| Trust label | The `VERIFIED` / `WEB_UNVERIFIED` marker shown on every surface that names a place or cites evidence. |
| Candidate place | An imported or promoted place not yet published; never visible to travelers. |
| Curator queue | The list of web-found candidates awaiting promote or reject by the curator. |
| Area | A travel area of Đà Nẵng (e.g. Hội An Old Town, Sơn Trà) used for filtering, the gate and closure rules; not an administrative ward. |
| Operational fact | A fact that affects a visit: opening hours, admission, entrance, closure; "unknown" when unsupported; stale after 180 days. |
| Proposal / preview revision | An unsaved, immutable itinerary version produced or edited; becomes the trip only on explicit Save. |
| Saved itinerary | The trip version the traveler explicitly saved; carries a revision number. |
| Leg | Travel between two consecutive stops; mode, distance and duration from Google Routes. |
| Blocking conflict | A conflict with severity `BLOCKING` (e.g. closed at planned time or date, leg unavailable, day window exceeded) that prevents Save. |
| Plan Health | Deterministic feasibility status `GOOD` / `WARNING` / `BLOCKED` with reasons, including calendar and trust conflicts. |
| Closure rule | Curator-reviewed calendar data (weekly, date, lunar, season, ticket validity) applied by Plan Health; never written by a model. |
| Place card | The on-site view of a stop: names, driver address, entrance, dated facts, trust label, closure rules, directions. |
| Guide / research agent | Guide: city-, place- or trip-scoped grounded Q&A with validated citations. Research agent: the Groq-backed Agno agent (Tavily search, page fetch, Places check) that proposes `WEB_UNVERIFIED` candidates and web evidence. |

## 10. Traceability

BO → BR/FR → ADR/API/TC are kept via IDs in this file, `docs/architecture.md`, `docs/api/openapi.yaml` (`x-fr`)
and `docs/test-plan.md`. No matrix is maintained; ID uniqueness and resolution are checked by the docs link/ID check.
