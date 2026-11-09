# User Stories — Gonarra

| Field | Value |
|---|---|
| Title | User Stories — Gonarra |
| Version | 1.0 |
| Date | 2026-11-09 |
| Owner | Lê Ngọc Tấn Hiền (student author, product owner, operator) |
| Approver | trantrongminh, FYP mentor (full name and title pending, OQ-001) |
| Status | Draft — [Pending] mentor sign-off at M0 |
| Requirements baseline | [PRD](PRD.md) 2.0, [BRD](../02-requirements/BRD.md) 2.0 |

## Conventions

- Form: "As a `<role>`, I want `<capability>`, so that `<benefit>`". One story = one user-visible outcome.
- Roles: **traveler** (P-01 Linh, P-02 Tom), **operator** (P-03, the owner at a terminal; was "curator" before
  DEC-022), **study participant** (P-04). Personas are in the [BRD](../02-requirements/BRD.md#1-product-and-personas).
- Scope is Đà Nẵng only, including the Hội An area (DEC-013). Every story lists the PRD FRs it implements; its
  priority is the highest priority among those FRs. Merged FR IDs (PRD §2) are cited by their surviving ID.
- Acceptance criteria are Given/When/Then (`US-nnn-ACn`). A story is done when every criterion passes against named
  fixtures, with build, language, environment and provider mode (live or recorded) recorded.
- IDs are never renumbered; a story that no longer applies is withdrawn with its reason.

## Story index

| ID | Role | Story | FRs | Priority |
|---|---|---|---|---|
| US-001 | Traveler | Find a Đà Nẵng place by its Vietnamese or English name | FR-001, FR-002 | Must |
| US-002 | Traveler | See where each fact comes from and how current it is | FR-003, FR-005, FR-008 | Must |
| US-003 | Traveler | See only published places, or web-found places that are labelled | FR-004 | Must |
| US-004 | Operator | Import candidate places without affecting the live catalog | FR-009 | Must |
| US-005 | Operator | Record bilingual content and sourced facts for candidates | FR-011, FR-016 | Must |
| US-006 | Operator | Have only complete places published, automatically | FR-013, FR-014 | Must |
| US-007 | Operator | Take down a wrong place in an emergency | FR-014 | Should |
| US-008 | Operator | See the release-gate count | FR-018 | Should |
| US-009 | — | *Withdrawn (DEC-022): review AI drafts in a curator tool* | (FR-019 withdrawn) | — |
| US-010 | Traveler | Describe my trip in my own words or with a form | FR-020 | Must |
| US-011 | Traveler | Reuse my saved preferences | FR-073 | Should |
| US-012 | Traveler | Be asked for missing trip details | FR-022 | Must |
| US-013 | Traveler | Receive a proposal made of Đà Nẵng places | FR-025 | Must |
| US-014 | Traveler | See each day as a timeline and on a map with travel legs | FR-027, FR-029 | Must |
| US-015 | Traveler | See whether my day fits and what blocks it | FR-030, FR-031, FR-032 | Must |
| US-016 | Traveler | Reorder the stops of a day | FR-033, FR-039 | Must |
| US-017 | Traveler | Adjust visit durations and travel modes | FR-037, FR-039 | Must |
| US-018 | Traveler | Decide which version becomes my saved trip | FR-040, FR-041, FR-045 | Must |
| US-019 | Traveler | Never lose my saved trip or my edits when something fails | FR-041, FR-043 | Must |
| US-020 | Traveler | Delete a trip I no longer need | FR-045 | Should |
| US-021 | Traveler | Lock a must-see stop | FR-047 | Should |
| US-022 | Traveler | Show a driver where I am going and find the entrance | FR-051 | Must |
| US-023 | Traveler | Open directions to a stop in my maps app | FR-054 | Must |
| US-024 | Traveler | See today's stops at a glance | FR-055 | Should |
| US-025 | Traveler | Ask about Đà Nẵng or a place and see the sources of the answer | FR-104, FR-056, FR-058, FR-078 | Must |
| US-026 | Traveler | Be told when Gonarra does not know | FR-057 | Must |
| US-027 | Traveler | Ask a question by speaking | FR-059 | Should |
| US-028 | Traveler | Identify the place in front of me from a photo | FR-061 | Should |
| US-029 | Traveler | Look for a stay for my trip on a booking site | FR-064 | Must |
| US-030 | Traveler | Look for activities at a stop on a booking site | FR-064 | Must |
| US-031 | Traveler | See indicative stay prices while planning | FR-066 | Could |
| US-032 | Traveler | Keep my trips private to my account | FR-068 | Must |
| US-033 | Traveler, study participant | Delete my account and see when it is done | FR-071 | Must |
| US-034 | Traveler | Use the whole app in Vietnamese or English | FR-075, FR-003 | Must |
| US-035 | Study participant | Know what is sent to AI and search providers | FR-070, FR-074 | Must |
| US-036 | Study participant | Have my session measured without my identity or questions | FR-077 | Should |
| US-037 | Traveler | Look for transport to Đà Nẵng on a booking site | FR-064 | Must |
| US-038 | Traveler | Be told clearly when a request is unsupported | FR-086 | Must |
| US-039 | Traveler | Add a place to a day | FR-034, FR-039 | Must |
| US-040 | Traveler | Remove a stop from a day | FR-034, FR-039 | Must |
| US-041 | Traveler | Replace a stop with another place | FR-034, FR-039 | Must |
| US-042 | Traveler | Regenerate one day while keeping locked stops | FR-048, FR-047 | Should |
| US-043 | Traveler | Hear a Guide answer read aloud | FR-059 | Should |
| US-044 | Traveler | See a trust label on every place and citation | FR-098 | Must |
| US-045 | Traveler | Get labelled web-found suggestions when the catalog is thin | FR-099, FR-100, FR-025, FR-031 | Must |
| US-046 | Traveler | Be warned about closures, Tết and lantern nights on my dates | FR-102, FR-103 | Must |
| US-047 | Traveler | Get a labelled web answer when the catalog has no evidence | FR-105 | Must |
| US-048 | Operator | Maintain closure and calendar rules in one versioned file | FR-107 | Must |
| US-049 | Operator | Have confirmed web-found places enter the catalog pipeline automatically | FR-101 | Must |
| US-050 | Traveler | Keep planning when a free quota runs out | FR-106 | Must |
| US-051 | Operator | Fill missing descriptions and facts from cited sources | FR-011, FR-003, FR-005 | Must |

## Stories and acceptance criteria

### Catalog and trust

**US-001 — Find a place by name** (Must · FR-001, FR-002). As a traveler, I want to find a Đà Nẵng place by its
Vietnamese name, English name or a common alias, so that I find the same destination whichever language I know.

- AC1 Given the app, when I open search, then Đà Nẵng is the only city and its travel areas (e.g. Hội An Old Town) are filters.
- AC2 When I search "Chùa Cầu", "Japanese Covered Bridge" or "chua cau" (no diacritics), then the published place is in the first 5 results.
- AC3 Given any search, then 100% of results are Đà Nẵng places.

**US-002 — Sources and freshness** (Must · FR-003, FR-005, FR-008). As a traveler, I want to see the source and
source-check date of each fact, so that I can decide how much to rely on it.

- AC1 Given a published place, when I open it, then I see both names, a description in my language when a human-written one exists (otherwise "No description yet"), category, area, suggested duration and map position.
- AC2 Given a known fact, when I view it, then its source and source-check date are shown with the source link (catalog text and facts are human-written, never AI-generated).
- AC3 Given a fact with no supported value, then it reads "unknown"; given a fact checked 181 days ago, then it is labelled stale.
- AC4 Given open-data content (OSM, Wikipedia, Wikivoyage, Commons photo), then the required attribution and licence are shown.

**US-003 — Only published or labelled places** (Must · FR-004). As a traveler, I want to see only places that
passed Gonarra's source checks, or web-found places clearly labelled as such, so that I do not act on unchecked data.

- AC1 Given 10 candidate places, when I search, plan or ask the Guide, then none appears; a direct ID request returns "not found".
- AC2 Given a web-found place appears, then it carries the `WEB_UNVERIFIED` label.

**US-044 — Trust label everywhere** (Must · FR-098). As a traveler, I want every place and citation to show whether
it is source-checked or unverified web content, so that I know what I can rely on.

- AC1 Given a trip with a web-found stop, when I view search, proposal, timeline, map, place card and Guide citations, then every item shows "Source-checked · <date>" or `WEB_UNVERIFIED` with source URL and fetched date.
- AC2 Given web content fetched more than 7 days ago, then it shows a stale mark.
- AC3 Given either language, then no text claims the content was reviewed by a person.

### Operator and catalog pipeline

**US-004 — Import candidates safely** (Must · FR-009). As the operator, I want to import Đà Nẵng candidates from named
open-data releases and my CSV sheet, so that the catalog grows without changing what travelers see.

- AC1 Given an import, then candidates are tagged with source and release; the published set is unchanged.
- AC2 Given the same release is imported again, then the candidate count is unchanged.

**US-005 — Sourced, bilingual content** (Must · FR-011, FR-016). As the operator, I want each candidate's content and
facts linked to an attributed source revision with its licence, so that nothing shown is unsourced.

- AC1 Given a candidate with facts, then every non-unknown value links to a source revision; a CSV row without a source yields "unknown".
- AC2 Given a source without licence or attribution text, then facts citing it cannot be published.

**US-006 — Automated publication gate** (Must · FR-013, FR-014). As the operator, I want the gate to publish only
complete candidates, automatically, so that the catalog grows without a review queue.

- AC1 Given a candidate missing English content, an in-boundary location, a category, a sourced fact or a licence, when the gate runs, then it is refused and the failed check is named in the run report.
- AC2 Given a complete candidate, when the gate runs, then it is searchable within 1 minute with actor `system:gonarra-pipeline` and the time recorded.
- AC3 Given the gate runs twice, then no second publication is created.

**US-007 — Emergency takedown** (Should · FR-014). As the operator, I want to unpublish a wrong place, so that it stops
reaching travelers.

- AC1 Given a published place, when I call the unpublish endpoint, then it is absent from new searches, proposals and answers.
- AC2 Given the next pipeline run, then the place is not re-published unless its source revision changed.

**US-008 — Release-gate count** (Should · FR-018). As the operator, I want published counts for Đà Nẵng and per area
with gate rejections per reason, so that I can track the ≥ 100 / ≥ 30 release gate.

- AC1 Given `GET /v1/admin/cities/summary` with an operator account, then the counts equal the catalog report; a non-operator is refused.

**US-009 — Withdrawn.** Reviewing AI drafts in a curator tool was removed with curator review (DEC-022; FR-019
withdrawn). Model-extracted content is covered by BRU-002 rev. 2 and US-051.

**US-048 — Closure rules file** (Must · FR-107). As the operator, I want closure and calendar rules in one versioned
YAML file loaded by a CLI, so that Plan Health uses rules I control.

- AC1 Given a valid file, when I load it twice, then the result is identical and the file's git revision is recorded.
- AC2 Given an invalid rule, when I load the file, then the load fails naming the rule.

**US-049 — Auto-promotion of web places** (Must · FR-101). As the operator, I want a web-found place whose existence
check confirms it operating inside Đà Nẵng to enter the pipeline as a candidate, so that the catalog learns from
research without a queue.

- AC1 Given an `EXISTS_OPERATIONAL` candidate inside the boundary, when promotion runs, then exactly one imported place is created; a re-run creates none.
- AC2 Given a closed, not-found or outside-boundary candidate, then nothing is created.
- AC3 Given a trip holding a promoted candidate, then it shows `VERIFIED` only after the gate publishes the place.

**US-051 — Descriptions and facts from human-written sources** (Must · FR-011, FR-003, FR-005). As the operator, I want
place screens filled from cited human-written sources, so that they are not empty and nothing is invented.

- AC1 Given a place with no description, then the pipeline stores one only from the owner sheet, Wikivoyage or Wikipedia in that locale, with its source revision, attribution and licence; otherwise the card says "No description yet" (DEC-031, DEC-033).
- AC2 Given a place with unknown address, hours or price, then a value is stored only from a human-written source record with its source revision and must pass code parsing; contact data is rejected.
- AC3 Given any candidate, then the gate rule `AI_CONTENT` rejects AI-generated descriptions and facts, and no CLI command can enable them without `allow_ai_content` and an ACTIVE provider policy.

### Planning

**US-010 — Describe my trip** (Must · FR-020). As a traveler, I want to describe my trip in Vietnamese or English, or
fill in a form, so that I can start planning the way that suits me.

- AC1 Given English, when Tom writes "2 relaxed days in Hội An, old town and food", then the request is accepted.
- AC2 Given Vietnamese, when Linh writes "2 ngày ở Đà Nẵng, thích biển và hải sản", then the request is accepted.
- AC3 Given I do not want to type, when I fill in start date, days, day windows, pace, interests, travel modes and must-sees, then I can request a proposal from the form alone.

**US-011 — Reuse preferences** (Should · FR-073). As a traveler, I want to save my usual pace and interests, so that I
do not re-enter them.

- AC1 Given saved pace "relaxed" and interest "food", when I start a new request, then the form is prefilled.
- AC2 Given I did not choose to save, then no preferences are stored.

**US-012 — Clarify missing details** (Must · FR-022). As a traveler, I want to be asked for anything missing, so that
the proposal matches what I asked for.

- AC1 Given no start date, when I submit, then I am asked for it before any proposal appears.
- AC2 Given "a few days", when I submit, then I am asked for 1, 2 or 3 days.

**US-038 — Refuse unsupported requests** (Must · FR-086). As a traveler, I want to be told clearly when a request is
outside what Gonarra supports, so that I can change it instead of receiving a wrong plan.

- AC1 Given 4 days, when I submit, then I am told trips are 1–3 days.
- AC2 Given two cities, or a city other than Đà Nẵng (e.g. Nha Trang), when I submit, then I am told a trip covers Đà Nẵng only, and no model or provider is called.

**US-013 — Proposal from Đà Nẵng places** (Must · FR-025). As a traveler, I want a proposal for the days I asked for,
built from published Đà Nẵng places, so that every stop exists and is in the city.

- AC1 Given a complete request for 2 days, then the proposal has exactly 2 days.
- AC2 Given the proposal, then every `VERIFIED` stop is a published Đà Nẵng place; unknown or other-city items from the model are absent.
- AC3 Given a must-see, then the proposal contains it or states why not.
- AC4 Given the selector model fails, then a proposal is still produced by the rule-based fallback.

**US-045 — Labelled web suggestions** (Must · FR-099, FR-100, FR-025, FR-031). As a traveler, I want Gonarra to look
on the web when its catalog cannot satisfy my request, and to tell me clearly, so that I get a fuller plan without
being misled.

- AC1 Given a request the catalog covers, then no research runs.
- AC2 Given a thin pool, then research runs within its caps and only existence-checked places become stops, each labelled `WEB_UNVERIFIED`.
- AC3 Given a plan with a web-found stop and no other issue, then Plan Health is `WARNING`, never `GOOD`, and I can still save it.

**US-014 — Timeline, map and legs** (Must · FR-027, FR-029). As a traveler, I want each day as an ordered timeline and
on a map with travel times, so that I can picture how the day runs.

- AC1 Given a proposal, then stops are ordered with non-overlapping arrival and departure times, and map and timeline show the same revision with selection synced both ways.
- AC2 Given a leg, then it shows mode, distance and duration from the routing provider, or "unavailable"; never a model value.
- AC3 Given a demo build using estimates, then every estimated leg is shown with "≈".

**US-015 — Feasibility and blocking** (Must · FR-030, FR-031, FR-032). As a traveler, I want to see whether each day
fits and what blocks it, so that I fix problems before I go.

- AC1 Given a stop planned while the place is closed, then it is flagged with the conflict type.
- AC2 Given any blocking conflict, then Plan Health is `BLOCKED` with reasons, and Save is refused with the reason.

**US-046 — Calendar warnings** (Must · FR-102, FR-103). As a traveler, I want Plan Health to know weekly closures,
holidays such as Tết, Hội An lantern nights and ticket validity on my dates, so that I do not arrive at a closed
place.

- AC1 Given a stop on its weekly closing day or during Tết, then it is flagged `CLOSED_ON_DATE` with the rule and date.
- AC2 Given a trip date on a lantern night, then the matching rule is shown for affected stops.
- AC3 (Should) Given a 3-day range, when the app requests the city calendar, then every rule effective in the range is returned and none outside it.

### Edit and Save

**US-016 — Reorder stops** (Must · FR-033, FR-039). As a traveler, I want to change the order of stops, so that the day
follows my preferred sequence.

- AC1 Given day 1, when I move stop 3 to position 1, then the new order and recalculated times are shown, and Save is unavailable while recalculating.
- AC2 Given I save and reopen, then the new order is shown.

**US-039 — Add a place** (Must · FR-034, FR-039). As a traveler, I want to add a place to a day, so that the plan
includes what I want to see.

- AC1 Given a published Đà Nẵng place, when I add it to day 2, then it is inserted and times are recalculated.
- AC2 Given a place outside Đà Nẵng, when I try to add it, then it is refused.

**US-040 — Remove a stop** (Must · FR-034, FR-039). As a traveler, I want to remove a stop, so that the day is not
overloaded.

- AC1 Given a stop, when I remove it, then it and its legs disappear and times are recalculated; after Save and reopen it is absent.

**US-041 — Replace a stop** (Must · FR-034, FR-039). As a traveler, I want to swap a stop for another place, so that I
can change my mind without rebuilding the day.

- AC1 Given Replace, then only published Đà Nẵng places (or labelled web-found candidates) are offered.
- AC2 Given a replacement, then times, legs and any new blocking conflict reflect it.

**US-017 — Durations and modes** (Must · FR-037, FR-039). As a traveler, I want to change how long I stay and whether I
walk or drive, so that the day fits my pace.

- AC1 Given a 60-minute stop set to 90 minutes, then its departure and all later times that day move by 30 minutes.
- AC2 Given a walking leg switched to driving, then its distance and duration come from the routing provider and later times follow.

**US-018 — Explicit Save** (Must · FR-040, FR-041, FR-045). As a traveler, I want only the version I explicitly save to
become my trip, so that Gonarra never replaces my plan without my decision.

- AC1 Given a new proposal, then it is labelled unsaved; leaving before Save keeps the previous saved version.
- AC2 Given Save is retried with the same idempotency key, then exactly one new version exists.
- AC3 Given 3 saved trips, then all are listed and each reopens at its last saved version.

**US-019 — Nothing lost on failure** (Must · FR-041, FR-043). As a traveler, I want my saved trip and unsaved edits to
survive failures, so that I can trust Gonarra with my plan.

- AC1 Given a model, research, routing or network failure, or a late result, then the saved trip and my unsaved edits are unchanged.
- AC2 Given the trip was saved from another device after I opened it, when I Save, then I see a revision conflict, the other save is kept and my edits remain.

**US-020 — Delete a trip** (Should · FR-045). As a traveler, I want to delete a trip I no longer need, so that my list
stays relevant.

- AC1 Given I confirm deletion, then the trip disappears; given I cancel, then it remains.

**US-021 — Lock a must-see stop** (Should · FR-047). As a traveler, I want to lock a stop, so that later changes cannot
remove or move it.

- AC1 Given I lock a stop, then it shows a lock indicator that persists after Save and reopen; unlocking removes it.

**US-042 — Regenerate one day** (Should · FR-048, FR-047). As a traveler, I want to regenerate one day while keeping
locked stops, so that I can change an afternoon without losing what I care about.

- AC1 Given I regenerate day 2, then day 1 is identical and the locked stop keeps its place, day and duration.
- AC2 Given the regenerated day, then it is a new unsaved proposal; reopening before Save shows the saved version.

### On site

**US-022 — Place card** (Must · FR-051). As a traveler on site, I want a card with both names, a Vietnamese address
and the entrance, so that I can show a driver where to go and find the way in.

- AC1 Given a stop of my saved trip, then its card shows both names, the Vietnamese address or "address unknown", the sourced entrance or "unknown", the trust label and applicable closure rules.

**US-023 — Directions handoff** (Must · FR-054). As a traveler, I want to open directions in my maps app, so that I can
navigate there.

- AC1 Given a known entrance, then the maps app opens at the entrance; otherwise at the place position.

**US-024 — Today view** (Should · FR-055). As a traveler during my trip, I want today's stops in order, so that I know
what is next.

- AC1 Given today is day 2 of a saved trip, then day 2 is listed; outside the trip dates, day 1 is listed.

### Guide

**US-025 — Grounded answers** (Must · FR-104, FR-056, FR-058, FR-078). As a traveler, I want to ask about Đà Nẵng, a
place or my trip and see where the answer comes from, so that I can trust it.

- AC1 Given a city-scoped session, when Linh asks in Vietnamese when a pagoda closes, then the answer is in Vietnamese and cites supplied evidence only.
- AC2 Given any answer, then at least one source with its source-check date is listed; claims citing evidence outside the retrieved set are dropped.

**US-026 — Honest "I don't know"** (Must · FR-057). As a traveler, I want to be told when the evidence does not cover my
question, so that I am not misled by an invented answer.

- AC1 Given a question outside the evidence, then I see "insufficient evidence" and no answer text; ≥ 90% of the out-of-evidence set behaves this way.

**US-047 — Labelled web answer** (Must · FR-105). As a traveler, I want Gonarra to search the web when its catalog
cannot answer, and to label that answer, so that I still get help without confusing it with source-checked content.

- AC1 Given a web-only question and available quota, then the answer has status `ANSWERED_WEB_UNVERIFIED` and every claim cites a fetched page with URL, date and label; otherwise `insufficient_evidence`.
- AC2 Given the daily Tavily cap is reached, then no web search runs.

**US-027 — Spoken question** (Should · FR-059). As a traveler with my hands full, I want to ask by speaking, so that I
can use the Guide while walking.

- AC1 Given I tap the microphone for the first time, then permission is requested at that moment, not at app start.
- AC2 Given a spoken question, then I see an editable transcript and nothing is sent until I tap Send.
- AC3 Given I denied the microphone, then text questions still work.

**US-043 — Read-aloud answer** (Should · FR-059). As a traveler, I want to hear a completed answer read aloud, so that I
can keep my eyes on the street.

- AC1 Given a completed answer in Vietnamese or English, when I tap Read aloud, then the audio matches the displayed text and no audio is stored.

**US-028 — Photo identification** (Should · FR-061). As a traveler, I want to photograph the place in front of me and
learn which published place it is, so that I can open its card.

- AC1 Given first use, then camera and location permissions are requested at that moment.
- AC2 Given a published place within 300 m, then it is the first result; otherwise "not recognised".
- AC3 Given I denied camera or location, then search, planning and text questions still work.

### Booking handoff and prices

**US-029 — Stay handoff** (Must · FR-064). As a traveler, I want to open a stay partner (Agoda, Booking.com) with
Đà Nẵng and my trip dates, so that I can book where to sleep without re-entering my trip.

- AC1 Given a saved 2-day trip, when I choose a stay partner, then it opens with Đà Nẵng and my check-in and check-out dates; a partner that cannot take dates is not listed.

**US-030 — Activity handoff** (Must · FR-064). As a traveler, I want to open Klook from a stop, so that I can look for
tours there.

- AC1 Given a stop, when I tap "Find activities", then Klook opens with the place or Đà Nẵng filled in.

**US-037 — Transport handoff** (Must · FR-064). As a traveler, I want to open 12Go for getting to Đà Nẵng on my start
date, so that I can arrange transport without re-entering my trip.

- AC1 Given a saved trip, when I tap "Find transport", then 12Go opens with Đà Nẵng as destination and the start date.

**US-031 — Indicative prices** (Could · FR-066). As a traveler, I want indicative stay prices for my dates, so that I
can judge cost while planning.

- AC1 Given the feature flag is on, then prices for at least one stay are shown with retrieval time and a partner-confirmation notice, or the section is hidden with a message.
- AC2 Given I save the trip, then no price is stored with it.

### Accounts, privacy and language

**US-032 — Private trips** (Must · FR-068). As a traveler, I want my trips, preferences and questions visible only to my
account, so that my plans stay private.

- AC1 Given I am signed out, when I open My trips, then I am asked to sign in.
- AC2 Given another traveler's trip ID, then access is denied and no external service is called.

**US-033 — Delete my account** (Must · FR-071). As a traveler or study participant, I want to delete my account and see
when it is done, so that I know my data is gone.

- AC1 Given I confirm deletion, then status shows in progress, then completed (or failed with a reason).
- AC2 Given 24 hours have passed, then no record of mine remains in the database, identity provider or logs; a test restore of an older backup re-applies the deletion.

**US-034 — Bilingual app** (Must · FR-075, FR-003). As a traveler, I want every screen and place content in Vietnamese
or English, so that I can use Gonarra in my language.

- AC1 Given either language, when I open every screen, then no untranslated string appears; the choice persists.
- AC2 Given English, when I view a place, then its description is in English and its Vietnamese name is visible.

**US-035 — Provider transparency** (Must · FR-070, FR-074). As a study participant, I want to know what Gonarra sends to
AI and search providers, so that I can take part with informed consent.

- AC1 Given my first planning request or Guide question, then a notice in my language explains that request content goes to external AI and search providers and that identity and precise location do not.
- AC2 Given 20 recorded requests per provider, then none contains an account identifier, contact detail or precise coordinates.

**US-036 — Pseudonymous session log** (Should · FR-077). As a study participant, I want my session measured under a code
without my identity or my questions, so that I contribute evidence without exposing myself.

- AC1 Given a study account, then one log per session records participant code, language, request time, first-proposal time, Save outcome and whether research was used, and no free text.
- AC2 Given a non-study account, then no session log is created.

**US-050 — Graceful quota limits** (Must · FR-106). As a traveler, I want Gonarra to keep working when a free provider
quota is used up, so that I never lose a plan to a limit.

- AC1 Given a provider cap is reached, then planning uses the rule-based fallback without rationales or research, and the Guide returns `insufficient_evidence` or `quota_exhausted`.
- AC2 Given any cap, then saved trips and edits are unchanged and no provider call is made above the cap.

## Change history

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1–0.2 | 2026-11-04 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | Kit-based stories US-001..US-043 for five cities; kept at tag `docs-sdlc-full` |
| 1.0 | 2026-11-09 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | Re-baselined to Đà Nẵng only (DEC-013..DEC-028, DEC-029): curator stories US-004..US-008 rewritten for the operator and automated gate; US-009 withdrawn; FR references moved to surviving PRD 2.0 IDs; US-044..US-051 added for trust labels, research agent, calendar rules, Guide web answers, closure-rule file, auto-promotion, quota limits and grounded enrichment; legacy and increment columns removed |
