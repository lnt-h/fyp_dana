# Product Requirements Document — Gonarra

| Field | Value |
|---|---|
| Title | Product Requirements Document — Gonarra |
| Version | 2.0 |
| Date | 2026-11-09 |
| Owner | Lê Ngọc Tấn Hiền (student author, product owner, operator) |
| Approver | trantrongminh, FYP mentor (full name and title pending, OQ-001) |
| Status | Draft — [Pending] mentor sign-off at M0 (see the [BRD](../02-requirements/BRD.md) status row) |
| Lineage | Condensed from PRD 0.2 and the re-baseline requirements 1.2 (DEC-013..DEC-028). IDs preserved; merged and withdrawn IDs are listed, never renumbered. Full previous text at git tag `docs-sdlc-full`. |

This document holds the product half of the requirements: functional requirements (FR), non-functional
requirements (NFR), traceability and release criteria. Product, personas, objectives, metrics, scope, business
rules (BRU-xxx) and the glossary are in the [BRD](../02-requirements/BRD.md); decisions, open questions and risks in
the [decision log](../decisions.md); user stories in [user-stories.md](user-stories.md); the design in the
[SAD](../04-design/architecture/SAD.md), the [ADRs](../04-design/adr/) and the
[API contract](../04-design/api/openapi.yaml); verification in the [test plan](../07-verification/TEST_PLAN.md).

## 1. Conventions

- Priorities are MoSCoW and follow the BRD scope; the cut order is DEC-003 rev. 1.
- "Golden set", "conflict set" and the other evaluation sets are frozen in the [test plan](../07-verification/TEST_PLAN.md)
  before tuning.
- Verified behaviour of providers, devices and bilingual content is claimed only from live runs, never from mocks.
- `rev. n` marks a revised requirement; the decision that revised it is named in the row.

## 2. Functional requirements

Implementation status per area is summarised in §2.1 below the table.

| ID | Requirement | Priority | Acceptance |
|---|---|---|---|
| **Catalog & trust** | | | |
| FR-001 | The traveler app shall present Đà Nẵng as the current and only enabled city, with its travel areas (e.g. Hội An Old Town) as filters. | Must | `/v1/cities` returns exactly one enabled city with its areas; 100% of search results belong to Đà Nẵng. |
| FR-002 | Gonarra shall return published Đà Nẵng places matching a query by Vietnamese name, English name or sourced alias, ignoring case and diacritics. | Must | 30 name/alias searches plus 10 diacritic-free queries: the target place is in the first 5 results in 100% of cases. |
| FR-003 | Gonarra shall show a place's details in the chosen language — both names, description, category, area, suggested duration, map position — with the Vietnamese name always visible. A description written by the grounded writer from sources is labelled "Summarised from sources" (DEC-025). | Must | 20 random published places: all elements present or labelled unknown; Vietnamese name shown in both locales. |
| FR-004 | Gonarra shall exclude unpublished candidate places from search, place details, proposals, Guide answers and photo results; a web-found place appears only as a stop or citation labelled `WEB_UNVERIFIED`. | Must | 10 candidates: 0 appear in any output; a direct ID request returns `not_found`; every web-found appearance carries the label. |
| FR-005 | For each displayed operational fact, Gonarra shall show its source and source-check date, show "unknown" when no supported value exists, and label it stale after 180 days. An AI-extracted fact (DEC-028) is labelled "Summarised from sources" with its source link. | Must | 20 places: 0 facts without source and date; 5 missing facts show "unknown"; stale label at 181 days, none at 179. |
| FR-008 | Gonarra shall display the attribution recorded for a data source wherever that source's data is shown. | Must | Inspection of every traveler screen showing provider or open-data content finds the attribution; 0 misses. |
| FR-098 rev. 1 | Gonarra shall show a trust label — `VERIFIED` ("Source-checked · <date>" / "Đã đối chiếu nguồn · <date>") or `WEB_UNVERIFIED` with source URL and fetched date — on every surface that shows a place: search result, proposal stop, timeline, map, place card and Guide citation. No surface or string claims human review (DEC-022). | Must | Inspection of all six surfaces for one trip containing a web-found stop finds the label on 100% of items; a `fetched_at` older than 7 days shows a stale mark; a grep of VI/EN locale files finds 0 strings such as "Verified", "reviewed", "Đã kiểm duyệt". |
| **Planning** | | | |
| FR-020 | Gonarra shall accept a trip request as free text in Vietnamese or English and as a structured form (city, start date, days 1–3, day windows, pace, interests, travel modes, must-sees) usable without free text. | Must | Golden-set requests in both languages accepted; a proposal can be requested from the form alone. |
| FR-022 | When start date or number of days is missing or ambiguous, Gonarra shall ask for it before generating a proposal. | Must | 100% of golden requests with a missing field receive a `clarification_required` naming it; 0 proposals generated first. |
| FR-086 | Gonarra shall refuse a request for more than 3 days, more than one city, or a city other than Đà Nẵng, and state the reason. | Must | 4-day, two-city and Nha Trang requests are each refused with the reason; 0 model or provider calls recorded. |
| FR-025 | Gonarra shall generate a proposal with the requested number of days from a pool of published Đà Nẵng places ranked by the selector agent; items referencing IDs outside the pool are discarded, must-sees are included or a reason is stated, and web-found places are added only as `WEB_UNVERIFIED` stops (FR-099). | Must | Golden set: 100% of proposals have the requested day count; 100% of `VERIFIED` stops are published Đà Nẵng places; 100% of injected unknown or other-city IDs discarded; planning completes with the rule-based fallback when the selector fails. |
| FR-029 | For each leg, Gonarra shall show mode, distance and duration from the routing provider (Google Routes cache or live; BRU-006 rev. 1), or show the leg as unavailable. In development, test and demo only, an estimated leg is shown with "≈" and `LEG_ESTIMATED` (DEC-023). | Must | Staging/production golden legs show provider values or "unavailable"; 0 model-estimated values anywhere; every estimated leg (demo) carries `estimated=true` and "≈". |
| **Plan Health** | | | |
| FR-027 | Gonarra shall show each day as an ordered timeline with arrival and departure times computed by the deterministic scheduler, and the same revision on a map with synchronised selection. | Must | Every golden day shows non-overlapping ordered times; map and timeline carry the same revision id; selection syncs both ways. |
| FR-030 | Gonarra shall flag each conflict at the affected stop, leg or day with type (`CLOSED_AT_PLANNED_TIME`, `CLOSED_ON_DATE`, `LUNAR_EVENT_CONFLICT`, `TICKET_VALIDITY`, `SEASONAL_WARNING`, `LEG_MODE_RESTRICTED`, `LEG_UNAVAILABLE`, `DAY_WINDOW_EXCEEDED`, `WEB_PLACE_UNVERIFIED`, `WEB_PLACE_UNRESOLVED`), severity and, for calendar conflicts, rule id and date. | Must | MET-004 = 100% on the conflict set; each flag names the stop/leg/day and type. |
| FR-031 | Gonarra shall show Plan Health as `BLOCKED` (any blocking conflict), `WARNING` (any non-blocking issue) or `GOOD`, with reasons; a plan containing a `WEB_UNVERIFIED` stop is capped at `WARNING`. `INFO` conflicts (e.g. `LEG_ESTIMATED`, DEC-023) are shown but never change the status. | Must | Status is `BLOCKED` iff a blocking conflict exists (100%); 5 plans with a web-found stop and no other issue show `WARNING`, never `GOOD`. |
| FR-032 | Gonarra shall refuse to save a `BLOCKED` proposal and show the reason. | Must | 100% of conflict-set saves refused with `plan_blocked` and reasons. |
| FR-102 rev. 1 | Plan Health shall apply the owner-maintained calendar rules loaded from `apps/api/data/closure_rules/da-nang.yaml` (DEC-022; was "curator-reviewed") — weekly closures, fixed dates, lunar dates (incl. Tết and Hội An lantern nights), ticket validity and seasonal notices — to each stop's planned date. | Must | Calendar conflict set (incl. Tết 2026-02-17, 2027-02-06 and a lantern night): recall 100%; lunar conversion passes its golden vectors. |
| FR-103 | Gonarra shall expose the city calendar (effective closure rules and events for a date range) to the traveler app. | Should | `GET /v1/cities/da-nang/calendar` for a 3-day range returns every loaded rule effective in the range and none outside it. |
| **Edit & Save** | | | |
| FR-033 | Gonarra shall let the traveler move a stop to another position within its day or to another day. | Must | New order and recalculated times shown; after Save and reopen, the order persists. |
| FR-034 | Gonarra shall let the traveler add, remove or replace a stop using a published Đà Nẵng place or a web-found candidate (labelled). | Must | Same-city add/replace succeeds; a non-Đà Nẵng place is refused; a removed stop and its legs are absent after Save. |
| FR-037 | Gonarra shall let the traveler change a stop's visit duration and a leg's mode between walking and driving. | Must | Departure and later times update; the leg's distance and duration come from the routing provider (estimates only under BRU-006 rev. 1). |
| FR-039 | After each edit, Gonarra shall recalculate affected times, legs and Plan Health and keep Save unavailable until done. | Must | For each edit type, recalculated values shown, new blocking conflicts flagged, Save disabled during recalculation. |
| FR-040 | Gonarra shall persist an itinerary only on explicit Save and label any differing proposal as unsaved. | Must | Closing the app, leaving the screen, regeneration or a route refresh without Save leave the saved trip unchanged; unsaved label until Save. |
| FR-041 | Save shall be idempotent (`Idempotency-Key`) and refused against a stale trip revision. | Must | Repeated Save creates one version; a Save from a stale copy returns `revision_conflict` and the second device's edits remain. |
| FR-043 | When a model, research, routing or network call fails or arrives late, Gonarra shall keep the saved itinerary and unsaved edits unchanged. | Must | Under injected failures, 100% of runs keep the saved trip and the edits (MET-006 = 0). |
| FR-045 | Gonarra shall list the traveler's saved trips, reopen each at its last saved version and delete one after confirmation. | Must (delete: Should) | 3 trips listed and reopened at the last version; confirmed deletion removes a trip, cancelled keeps it. |
| FR-047 | Gonarra shall let the traveler lock and unlock a stop, show the lock, and keep a locked stop's place, day and duration through regeneration. | Should | Lock persists after Save and reopen; MET-005 = 0 over the regeneration set. |
| FR-048 | Gonarra shall regenerate one selected day, leaving other days unchanged, as a new unsaved proposal. | Should | Regenerating day 2 leaves day 1 identical; reopening before Save shows the previous saved version. |
| **Place card** | | | |
| FR-051 | For each stop of a saved itinerary, Gonarra shall provide a place card with both names, a Vietnamese address for a driver or "unknown", the sourced entrance or "unknown", the trust label and applicable closure rules. | Must | One saved trip with ≥ 5 stops: every card shows all items; ≥ 90% of stops show an address. |
| FR-054 | From a place card, Gonarra shall open the device maps app with directions to the entrance, or to the place position when the entrance is unknown. | Must | On one Android and one iOS device, 5 stops open at the expected coordinates. |
| FR-055 | Gonarra shall show a Today view of the saved day matching the device date, else day 1. | Should | Device date on day 2 lists day 2; outside the trip dates lists day 1. |
| **Guide** | | | |
| FR-104 | Gonarra shall provide a Guide session scoped to the city (Đà Nẵng), a place or a trip, with conversation history rebuilt by code (last 4 turns). | Must | `POST /v1/guide/sessions` with scope `CITY` accepts questions about Đà Nẵng without a place id; place and trip scopes restrict evidence accordingly. |
| FR-056 | Gonarra shall answer a text question in the selected language with claims that each cite supplied evidence. | Must | MET-007 ≥ 95% on the Guide sample; 100% of answers in the selected language. |
| FR-058 | Gonarra shall build Guide evidence by hybrid retrieval over approved facts and chunks (entity → lexical → vector, rank fusion) and shall drop any claim whose evidence IDs are not in the supplied set. | Must | Citation validity ≥ 95% on the Guide sample; 0 citations to IDs outside the retrieved set. |
| FR-078 | Gonarra shall list with each answer at least one source with its source-check date, or for web evidence its URL, fetched date and `WEB_UNVERIFIED` label. | Must | Every answer in the Guide sample lists ≥ 1 source; web citations carry URL, date and label. |
| FR-057 | When evidence does not support an answer, Gonarra shall return `insufficient_evidence` instead of answering. | Must | MET-008 ≥ 90%; precision and recall of the status ≥ 90% on the out-of-evidence set. |
| FR-105 | When catalog evidence is insufficient and quota allows, Gonarra shall run the research agent and answer with status `ANSWERED_WEB_UNVERIFIED`, every claim cited to a fetched page. | Must | 10 web-only questions: answers carry the status and labelled web citations, or `insufficient_evidence`; 0 unlabelled web claims; 0 runs when the daily Tavily cap is reached. |
| **Research agent & auto-promotion** | | | |
| FR-099 | Gonarra shall run the research agent only when the catalog pool for the request is thin or the selector reports unmet requests, within per-plan caps (≤ 2 searches, ≤ 3 fetches, ≤ 3 Places checks). | Must | Golden requests with a sufficient pool record 0 research calls; a thin-pool request records ≤ the caps; the threshold is set from the research spike (OQ-127). |
| FR-100 | Each web-found candidate shall pass a Google Places existence and status check before it becomes a `WEB_UNVERIFIED` stop; unresolved candidates are dropped or flagged `WEB_PLACE_UNRESOLVED`. (DEC-023: Google Places is not used for the demo; the existence check moves to open-data matching, OQ-134; until then web candidates are not scheduled.) | Must | 10 fixture candidates: existing ones become stops, non-existent ones are never shown; only `place_id` is stored canonically. |
| FR-101 rev. 1 | (Revised by DEC-022; was: curator promotes or rejects from a queue.) Gonarra shall auto-promote a web-found candidate into the ingestion pipeline when its Places check returns `EXISTS_OPERATIONAL` inside the Đà Nẵng boundary; any other outcome leaves it a request-scoped `WEB_UNVERIFIED` candidate. Promotion never publishes; only the automated gate (FR-013) does. | Must | 10 fixture candidates: each `EXISTS_OPERATIONAL`-inside one creates exactly one `IMPORTED` place linked to the candidate (re-run creates none); outside-boundary, closed or not-found ones create none; trips holding a promoted candidate show `VERIFIED` only after the gate publishes it. |
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
| **Ingestion pipeline and operator (rev. DEC-022; was "Admin (curator tool)")** | | | |
| FR-009 rev. 1 | The ingestion pipeline (Typer CLI) shall import candidate places for Đà Nẵng from named open-data releases (Wikidata, OSM; Wikipedia extracts with attribution) and the owner's CSV sheet, without duplicates or changes to published places. | Must | Import tags candidates with source and release; re-import yields the same count; published set unchanged by import alone. |
| FR-011 rev. 1 | The ingestion pipeline shall record bilingual names and descriptions, area, category and, for each operational fact, a value or "unknown" linked to an attributed source revision; a value with no source stays "unknown" — nothing is invented. The offline `enrich facts` CLI may add a value only when the model cites a supplied evidence id and code accepts it (BRU-002 rev. 2, DEC-028). | Must | 5 candidates with all four fact types: every non-unknown value links to a source revision; a CSV row without a source yields "unknown". |
| FR-013 rev. 1 | The automated publication gate shall refuse a candidate lacking Vietnamese content, English content, a location inside the Đà Nẵng boundary, a category, an attributed source revision for any shown fact, or a recorded licence, naming each failed check in the run report. | Must | Each incomplete case refused with the check named; a complete candidate publishes. |
| FR-014 rev. 1 | The gate shall auto-publish every candidate that passes (visible in search within 1 minute; actor `system:gonarra-pipeline` and time recorded), idempotently; the operator can unpublish a place through `POST /v1/admin/places/{id}/unpublish` (emergency takedown). | Must (unpublish: Should) | 5 passing candidates visible within 1 min with system actor/time; a second run creates no new publication; an unpublished place is absent from new searches, proposals and answers and is not re-published by the next run unless its source revision changes. |
| FR-016 rev. 1 | The ingestion pipeline shall record each source's licence and required attribution text from its source registry entry; a source without them blocks publication of facts that cite it. | Must | 5 sources carry licence and attribution; a source with no licence fails the gate for its facts. |
| FR-018 rev. 1 | `GET /v1/admin/cities/summary` (operator only) shall return published-place counts for Đà Nẵng and per area against the gate (≥ 100 / ≥ 30) and gate rejections per reason. | Should | Counts equal the catalog report (MET-011 rev. 2). |
| FR-019 | **Withdrawn by DEC-022** (AI-draft confirmation removed with curator review). Successor rule: BRU-002 rev. 2 (evidence-id rule for any model-extracted fact, DEC-028). | — | — |
| FR-107 rev. 1 | Closure rules (place/area/city; weekly, date, lunar, season, ticket validity) with bilingual notes and a source shall be maintained by the owner in `apps/api/data/closure_rules/da-nang.yaml`, versioned in git and loaded by a CLI command that validates the schema; models never write rules (DEC-022; was: created and reviewed in the curator tool). | Must | Loading the file is idempotent and records the file's git revision; an invalid rule fails the load naming the rule; 0 rule rows written by any model path. |

Merged (kept IDs absorb the listed ones): FR-003 ← FR-076; FR-005 ← FR-006, FR-007; FR-009 ← FR-010; FR-011 ← FR-012;
FR-013 ← FR-082, FR-083; FR-014 ← FR-015, FR-017; FR-019 ← FR-084; FR-020 ← FR-021; FR-025 ← FR-024, FR-026, FR-087;
FR-027 ← FR-028, FR-088; FR-034 ← FR-035, FR-036; FR-037 ← FR-038; FR-039 ← FR-089; FR-040 ← FR-090; FR-041 ← FR-042;
FR-043 ← FR-044; FR-045 ← FR-046; FR-047 ← FR-049, FR-091; FR-048 ← FR-050; FR-051 ← FR-052, FR-053; FR-059 ← FR-060, FR-063;
FR-061 ← FR-062, FR-092, FR-093; FR-064 ← FR-065, FR-079; FR-066 ← FR-067, FR-080, FR-081; FR-068 ← FR-069, FR-094, FR-095;
FR-071 ← FR-072; FR-073 ← FR-096; FR-075 ← FR-097; FR-086 ← FR-023, FR-085.
Withdrawn: FR-019 (DEC-022). FR-058 "no runtime web search" is superseded by its new wording and FR-105 (DEC-015).
Revised by DEC-022: BRU-002, BRU-003, FR-009, FR-011, FR-013, FR-014, FR-016, FR-018, FR-098, FR-101, FR-102, FR-107, NFR-012, MET-011 (rev. 2).
Revised or annotated by DEC-023 and DEC-025 (2026-11-08): BRU-006 (rev. 1), FR-029, FR-031, FR-037, FR-100, NFR-026 (stated exception), MET-011 (rev. 3).
Annotated by DEC-028 (2026-11-08): BRU-002 (rev. 2), FR-003, FR-005, FR-011, FR-019 successor rule.

### 2.1 Implementation status (2026-11-09)

Status of the code in `apps/api` and `apps/mobile` on 2026-11-09, from the code, not from live verification. It is a
snapshot for planning; `progress.md` holds the evidence.

| Area | FRs | Status |
|---|---|---|
| Catalog, search, place details, trust labels | FR-001..FR-008, FR-098 | Implemented (API and app). Descriptions and facts carry their origin (`AI_SUMMARY`, `AI_EXTRACTED`; migrations 0007, 0009). |
| Planning, scheduling, Plan Health | FR-020, FR-022, FR-086, FR-025, FR-027, FR-029..FR-032, FR-102 | Implemented: selector with rule-based fallback, OR-Tools scheduler, Plan Health with closure rules from the YAML file. Routing runs on the haversine estimate provider in development/test/demo (DEC-023); the Google Routes adapter exists but is not used for the demo; Valhalla is not implemented. |
| City calendar endpoint | FR-103 | Not implemented (no `/v1/cities/{city}/calendar` route). |
| Edit, Save, trips | FR-033..FR-045 | Implemented (revisioned previews, idempotent Save, trip list, reopen, delete). |
| Lock and single-day regeneration | FR-047, FR-048 | Implemented in the planner and API (`/plan-previews/{id}/regenerate`). |
| Place card, directions, Today | FR-051, FR-054, FR-055 | Implemented. |
| Guide | FR-104, FR-056, FR-058, FR-078, FR-057 | Implemented: city, place and trip sessions with hybrid retrieval and citation validation (migration 0008). |
| Guide web fallback | FR-105 | **Not implemented**: an extension point in `app/guide/service.py`; questions without catalog evidence return `insufficient_evidence`. |
| Research agent and auto-promotion | FR-099..FR-101 | Implemented behind `GONARRA_RESEARCH_ENABLED` (off by default). The existence check is the Google Places adapter, which returns `SKIPPED` without a Google key, so in the demo no web candidate is scheduled; open-data matching (OQ-134) is not implemented. Promotion runs through the `web-candidates promote` CLI. |
| Booking handoff | FR-064 | Implemented (Agoda, Booking.com, Klook, 12Go links). |
| Accounts, privacy, quota | FR-068, FR-070, FR-071, FR-073..FR-075, FR-106 | Implemented. Non-production exception: with `GONARRA_DEMO_SHARED_USER` an unsigned request acts as one shared demo account; settings refuse it outside development, test and demo. |
| Study session log | FR-077 | Table only (migration 0005); nothing writes it yet. |
| Voice | FR-059 | Not implemented (a hidden app entry point behind `EXPO_PUBLIC_FEATURE_VOICE`; no STT/TTS). |
| Photo identification | FR-061 | Not implemented. |
| Indicative stay prices | FR-066 | Not implemented: the endpoint returns `feature_disabled`, or `not_implemented` when the flag is on. |
| Ingestion pipeline, gate, operator | FR-009..FR-018, FR-107 | Implemented as Typer CLIs (`ingest wikidata/osm/wikipedia/commons/sheet`, `publish auto/takedown/summary/audit-sample`, `closure-rules load`, `pipeline run`) plus `enrich descriptions` (DEC-025) and `enrich facts` (DEC-028); operator endpoints `POST /v1/admin/places/{id}/unpublish` and `GET /v1/admin/cities/summary`. |

## 3. Non-functional requirements

| ID | Requirement | Threshold / verification |
|---|---|---|
| NFR-001 | Place search shall display results quickly. | p95 ≤ 2 s over 100 scripted queries, device timing. |
| NFR-002 | Proposal generation, including research when triggered, shall complete with a visible progress stream. | p95 ≤ 60 s for 3-day golden requests; first SSE stage within 2 s. |
| NFR-004 | Recalculation after an edit shall be fast. | p95 ≤ 5 s over 50 scripted edits. |
| NFR-006 | A Guide answer with sources shall complete quickly, streaming validated text. | p95 ≤ 15 s incl. web fallback; first text within 5 s. |
| NFR-008 | The service shall be available during scheduled study sessions and recoverable. | ≥ 99% of 1-minute probes per session; RTO ≤ 4 h, RPO ≤ 24 h (restore drill); failure of any single provider leaves search, place cards and saved trips working. |
| NFR-012 rev. 1 | Security: traffic encrypted in transit and private data at rest; invalid, expired or foreign credentials rejected; secrets never in clients; `/v1/admin` operator endpoints (unpublish, city summary) limited to the operator allow-list `GONARRA_CURATOR_CLERK_USER_IDS` (rev. 1, DEC-022). | 0 non-TLS endpoints; 0 unencrypted stores; 0 accepted invalid credentials; 0 cross-account disclosures (former MET-010); 0 secrets in builds. |
| BR-046 | Privacy: no account identifiers, contact data or precise location reach Gemini, Groq, Tavily or Google Places; the user is told what is sent (FR-074). | 20 recorded requests per provider, 0 findings; redactor unit tests fail closed. |
| NFR-017 | Logging: logs, traces and AI invocation records exclude tokens, precise locations, question text, transcripts and full prompts (BRU-008). | 0 occurrences in logs of a full HA-02 and Guide run. |
| NFR-022 | Accessibility (WCAG 2.1 AA, selected criteria): screen-reader labels in both languages, text contrast ≥ 4.5:1, usable at 200% system text. | 0 unlabelled controls; 0 contrast failures; 0 truncated essential text on key screens. |
| NFR-026 | Bilingual parity: VI and EN are both launch locales with owner-reviewed UI strings; catalog content in both locales comes from attributed sources or the owner's CSV and is never machine-translated to pass the gate (stated exception, DEC-025: grounded `AI_SUMMARY` descriptions written separately in VI and EN from cited sources, labelled "Tóm tắt từ nguồn" / "Summarised from sources"; an EN name with no English source equals the Vietnamese proper name and is flagged, never translated; mentor OQ-133); times in UTC+7 regardless of device zone; diacritics render correctly. | 0 untranslated strings per locale; 0 wrong times of 20; 0 corrupted diacritics in a 50-place sample. |
| NFR-032 | Determinism: for identical inputs (candidate pool, route matrix, windows, rules) the scheduler and Plan Health produce identical output; acceptance runs are reproducible with recorded providers. | Snapshot equality on two runs; 0 pass/fail differences on re-run. |
| NFR-033 | Cost: cash spend USD 0 through 2027-01-31; quotas (FR-106) never interrupt a study session. | Weekly billing review; 0 quota failures logged during sessions; AWS spend within credits if used. |

NFR-003, 005, 009..011, 013..016, 018..021, 023..025, 027..031, 034..038 are absorbed by the rows above or by
the [test plan](../07-verification/TEST_PLAN.md) (compatibility, maintainability and release checks); no NFR is withdrawn.


## 4. Traceability

Traceability is kept by IDs, not by a separate matrix file: objectives and metrics (BRD) → requirements (this
document) → design (ADRs, `x-fr` tags in [openapi.yaml](../04-design/api/openapi.yaml)) → verification tasks
(`VT-nnn` in the [test plan](../07-verification/TEST_PLAN.md)) → stories ([user-stories.md](user-stories.md)). ID
uniqueness and resolution are checked by the docs link/ID check.

### 4.1 Objectives to requirements

| Objective | Metrics | Requirements |
|---|---|---|
| BO-001 Valid itinerary with little effort | MET-001..003 | FR-001, FR-002, FR-003, FR-020, FR-022, FR-086, FR-025, FR-029, FR-040, FR-064, FR-066, FR-073, FR-075; NFR-001, NFR-002, NFR-022, NFR-026 |
| BO-002 Judge feasibility and change a trip safely | MET-004..006 | FR-027, FR-030, FR-031, FR-032, FR-102, FR-103, FR-033, FR-034, FR-037, FR-039, FR-040, FR-041, FR-043, FR-045, FR-047, FR-048, FR-051, FR-054, FR-055; NFR-004, NFR-032 |
| BO-003 Trusted, labelled information and honest uncertainty | MET-007, MET-008, MET-014 | FR-004, FR-005, FR-008, FR-098, FR-099, FR-100, FR-104, FR-056, FR-058, FR-078, FR-057, FR-105, FR-059, FR-061; NFR-006 |
| BO-004 Private, free-tier service with a source-checked catalog above the gate | MET-011 rev. 3 | FR-009, FR-011, FR-013, FR-014, FR-016, FR-018, FR-101, FR-107, FR-068, FR-070, FR-071, FR-074, FR-106; BR-046, NFR-008, NFR-012, NFR-017, NFR-033 |
| BO-005 Evaluation with real users against ChatGPT/Gemini | MET-014, MET-001..003 | FR-074, FR-077; NFR-008, NFR-033 |

### 4.2 Requirements to design and verification

| Area | Requirements | Design | Verification tasks |
|---|---|---|---|
| Catalog and trust | FR-001..FR-008, FR-098 | ADR-003, ADR-006, ADR-012, ADR-014 | VT-001, VT-023, VT-028 |
| Planning and routing | FR-020, FR-022, FR-086, FR-025, FR-029 | ADR-004, ADR-011, ADR-013 | VT-002, VT-004, VT-021 |
| Plan Health and calendar | FR-027, FR-030..FR-032, FR-102, FR-103 | ADR-011 | VT-005, VT-006, VT-007, VT-008 |
| Edit and Save | FR-033..FR-045 | ADR-009 | VT-010, VT-011, VT-012, VT-024 |
| Lock and regeneration | FR-047, FR-048 | ADR-009, ADR-011 | VT-009 |
| Place card and Today | FR-051, FR-054, FR-055 | ADR-006 | VT-023 |
| Guide | FR-104, FR-056, FR-058, FR-078, FR-057, FR-105 | ADR-010, ADR-013 | VT-013, VT-014, VT-015, VT-016 |
| Research agent | FR-099, FR-100, FR-101 | ADR-013, ADR-014 | VT-003, VT-008, VT-019 rev. 1 |
| Booking handoff and prices | FR-064, FR-066 | ADR-006 (prices never stored) | Manual feature checks in the test plan |
| Accounts, privacy, quota, language | FR-068, FR-070, FR-071, FR-073..FR-075, FR-077, FR-106; BR-046, NFR-012, NFR-017 | ADR-005, ADR-013 | VT-017, VT-018, VT-020, VT-022, VT-023 |
| Voice and photo | FR-059, FR-061 | ADR-007, ADR-008 | Feature checks in the test plan |
| Ingestion, gate, operator | FR-009..FR-018, FR-107; BRU-002, BRU-003 | ADR-012 | VT-025, VT-026, VT-027, VT-028 |
| Platform | NFR-001..NFR-033 | ADR-001, ADR-002, ADR-003 | Performance, restore and accessibility checks in the test plan |

## 5. Release and acceptance criteria

An FR is accepted when its acceptance criterion passes against named fixtures, with build, language, environment
and provider mode (live or recorded) recorded. The release candidate is accepted when:

1. **Catalog gate:** MET-011 rev. 3 is met — ≥ 100 auto-published bilingual Đà Nẵng places passing the code gate,
   ≥ 30 of them in the Hội An area codes, and the 10% owner audit sample reported as an accuracy figure.
2. **Must FRs:** every Must FR passes its acceptance criterion.
3. **Quality thresholds:** MET-004 = 100%, MET-005 = 0, MET-006 = 0, MET-007 ≥ 95%, MET-008 ≥ 90%; selector
   validity 100% and hallucinated-place rate 0; NFR thresholds met; 0 open blocking defects.
4. **Measured routing:** acceptance and study runs use a measured router (Valhalla or Google Routes), never the demo
   estimate provider (DEC-023, OQ-132).
5. **Should/Could:** each Should or Could feature passes its checks or is disabled and recorded as cut under the
   DEC-003 rev. 1 order with the approver's agreement. Bilingual content, the catalog gate and explicit Save are
   never cut.
6. **Cost:** USD 0 cash spend to date (NFR-033).

Study results (MET-001..003, MET-014) are reported in the thesis; they are not release gates.

## 6. Change history

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1–0.2 | 2026-11-04 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | Kit-based PRD for five cities (FR-001..FR-097, NFR-001..NFR-038), audit fix round 1; kept at tag `docs-sdlc-full` |
| 2.0 | 2026-11-09 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | Rewritten from the condensed re-baseline requirements 1.2 (Đà Nẵng only, DEC-013..DEC-025) plus DEC-028 under DEC-029; FR merges and withdrawals listed; implementation status (§2.1) and traceability (§4, replacing `traceability.md`) added; business content moved to the BRD |
