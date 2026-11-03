# User Stories — Gonarra

## Document control

| Field | Value |
|---|---|
| Document ID | GONARRA-USER-STORIES |
| Version | 0.2 |
| Status | Draft |
| Owner | Lê Ngọc Tấn Hiền, student author and product owner |
| Approver | trantrongminh, FYP mentor (OQ-001) |
| Date | 2026-11-04 |
| Prompt used | `analysis/PRD_prompt.md` v2.0, adapted copy `docs/00-governance/prompt-templates/analysis/PRD_prompt.md` (kit commit `6996dae`) |
| Requirements baseline | `docs/03-analysis/PRD.md` (GONARRA-PRD 0.1), `docs/02-requirements/BRD.md` 0.4 |

| Version | Date | Author | Change summary |
|---|---|---|---|
| 0.1 | 2026-11-04 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | First kit-based stories; replace pre-rebuild `docs/USER-STORIES.md` (SRC-006). Legacy US-00..US-08 kept as a "Legacy ID" column |
| 0.2 | 2026-11-04 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | Fix round 1 for PRD-AUDIT-01: FIX-03 split FRs linked; FIX-14 stories split (US-012→US-038, US-016→US-039..US-041, US-021→US-042, US-027→US-043) |

## Conventions

- Form: "As a `<role>`, I want `<capability>`, so that `<benefit>`". One story = one user-visible outcome.
- Roles: **traveler** (personas P-01 Linh, P-02 Tom), **curator** (P-03, curator tool), **study participant**
  (P-04). See PRD §3.3.
- Each story has at most five Given/When/Then acceptance criteria (`US-nnn-ACn`) and lists the FR IDs it
  implements. Priority equals the highest priority among its FRs that the story is needed for, and never exceeds
  the source BR priority.
- Delivery: Incremental, 2-week sprints; increment per PRD §11.4. A story is done when every criterion passes
  against named fixtures, with build, language, environment and provider mode (live or recorded) recorded.
- Evaluation-set sizes follow ASM-011.

## Story index

| ID | Legacy ID | Role | Story | FR IDs | Priority | Increment |
|---|---|---|---|---|---|---|
| US-001 | US-01 | Traveler | Find a place in my city by its Vietnamese or English name | FR-001, FR-002 | Must | INC-1 |
| US-002 | US-01 | Traveler | See where each fact about a place comes from and how current it is | FR-003, FR-005, FR-006, FR-007, FR-008 | Must | INC-1 |
| US-003 | US-01 | Traveler | See only reviewed places | FR-004 | Must | INC-1 |
| US-004 | US-00 | Curator | Import candidate places without affecting the live catalog | FR-009, FR-010 | Must | INC-1 |
| US-005 | US-00 | Curator | Complete a candidate's bilingual content and sourced facts | FR-011, FR-012, FR-016, FR-083 | Must | INC-1 |
| US-006 | US-00 | Curator | Publish a place only when it is complete | FR-013, FR-014, FR-015, FR-082 | Must | INC-1 |
| US-007 | — | Curator | Withdraw a place I published by mistake | FR-017 | Should | INC-1 |
| US-008 | — | Curator | See how many places each city has | FR-018 | Should | INC-1 |
| US-009 | — | Curator | Use AI drafts but review them before publishing | FR-019, FR-084 | Should | INC-1 |
| US-010 | US-02 | Traveler | Describe my trip in my own words or with a form | FR-020, FR-021 | Must | INC-2 |
| US-011 | — | Traveler | Reuse my saved preferences | FR-073, FR-096 | Should | INC-2 |
| US-012 | US-02 | Traveler | Be asked for missing trip details | FR-022 | Must | INC-2 |
| US-013 | US-02 | Traveler | Receive a proposal made only of reviewed places in my city | FR-024, FR-025, FR-026, FR-087 | Must | INC-2 |
| US-014 | US-03 | Traveler | See each day as a timeline and on a map with real travel legs | FR-027, FR-028, FR-029, FR-088 | Must | INC-2 |
| US-015 | US-03 | Traveler | See whether my day fits and what blocks it | FR-030, FR-031, FR-032 | Must | INC-2 |
| US-016 | US-05 | Traveler | Reorder the stops of a day | FR-033, FR-039, FR-089 | Must | INC-2 |
| US-017 | US-05 | Traveler | Adjust visit durations and travel modes | FR-037, FR-038, FR-039, FR-089 | Must | INC-2 |
| US-018 | US-05 | Traveler | Decide which version becomes my saved trip | FR-040, FR-041, FR-045, FR-090 | Must | INC-2 |
| US-019 | US-05 | Traveler | Never lose my saved trip or my edits when something fails | FR-042, FR-043, FR-044 | Must | INC-2 |
| US-020 | — | Traveler | Delete a trip I no longer need | FR-046 | Should | INC-2 |
| US-021 | US-04 | Traveler | Lock a must-see stop (HA-02) | FR-047, FR-091 | Should | INC-4 |
| US-022 | US-06 | Traveler | Show a driver where I am going and find the entrance | FR-051, FR-052, FR-053 | Must | INC-3 |
| US-023 | US-06 | Traveler | Open directions to a stop in my maps app | FR-054 | Must | INC-3 |
| US-024 | — | Traveler | See today's stops at a glance | FR-055 | Should | INC-3 |
| US-025 | US-07 | Traveler | Ask a question about a place and see the sources of the answer | FR-056, FR-058, FR-078 | Must | INC-3 |
| US-026 | US-07 | Traveler | Be told when Gonarra does not know | FR-057 | Must | INC-3 |
| US-027 | — | Traveler | Ask a question by speaking | FR-059, FR-063 | Should | INC-4 |
| US-028 | — | Traveler | Identify the place in front of me from a photo | FR-061, FR-062, FR-092, FR-093 | Should | INC-4 |
| US-029 | — | Traveler | Look for a stay for my trip on a booking site | FR-064 | Must | INC-3 |
| US-030 | — | Traveler | Look for activities at a stop on a booking site | FR-065 | Must | INC-3 |
| US-031 | — | Traveler | See indicative stay prices while planning | FR-066, FR-067, FR-080, FR-081 | Could | INC-4 |
| US-032 | US-08 | Traveler | Keep my trips private to my account | FR-068, FR-069, FR-094, FR-095 | Must | INC-2 |
| US-033 | US-08 | Traveler | Delete my account and see when it is done | FR-071, FR-072 | Must | INC-3 |
| US-034 | — | Traveler | Use the whole app in Vietnamese or English | FR-075, FR-076, FR-097 | Must | INC-1 |
| US-035 | — | Study participant | Know what is sent to the AI service | FR-070, FR-074 | Must | INC-3 |
| US-036 | — | Study participant | Have my session measured without my identity or questions | FR-077 | Should | INC-3 |
| US-037 | — | Traveler | Look for transport to my trip's city on a booking site | FR-079 | Must | INC-3 |
| US-038 | US-02 | Traveler | Be told clearly when a request is unsupported | FR-023, FR-085, FR-086 | Must | INC-2 |
| US-039 | US-05 | Traveler | Add a place to a day | FR-034, FR-039, FR-089 | Must | INC-2 |
| US-040 | US-05 | Traveler | Remove a stop from a day | FR-035, FR-039, FR-089 | Must | INC-2 |
| US-041 | US-05 | Traveler | Replace a stop with another place | FR-036, FR-039, FR-089 | Must | INC-2 |
| US-042 | US-04 | Traveler | Regenerate one day while keeping locked stops (HA-02) | FR-048, FR-049, FR-050 | Should | INC-4 |
| US-043 | — | Traveler | Hear a Guide answer read aloud | FR-060 | Should | INC-4 |

## Stories and acceptance criteria

### US-001 — Find a place by name (Must · Legacy US-01 · FR-001, FR-002)

As a **traveler**, I want to find a place in my chosen city by its Vietnamese name, English name or a common
alias, so that I can locate the same destination whichever language I know it in.

- **AC1** Given I selected Huế, when I search "Đại Nội", then the published place appears in the first 5 results.
- **AC2** Given I selected Huế, when I search "Imperial City" or "Dai Noi" (no diacritics), then the same place appears in the first 5 results.
- **AC3** Given I selected Hội An, when I search a place that exists only in Huế, then it does not appear.

### US-002 — See sources and freshness (Must · Legacy US-01 · FR-003, FR-005, FR-006, FR-007, FR-008)

As a **traveler**, I want to see the source and verification date of each fact about a place, so that I can
decide how much to rely on it.

- **AC1** Given a published place, when I open its details, then I see both names, a description in my language, category, suggested duration and map position.
- **AC2** Given its opening hours are known, when I view them, then the source name and verification date are shown.
- **AC3** Given a fact has no supported value, when I view it, then it reads "unknown", not blank or zero.
- **AC4** Given a fact was verified 181 days ago, when I view it, then it is labelled stale.
- **AC5** Given the place uses open-data content, when I view the details, then the required attribution is shown.

### US-003 — Only reviewed places (Must · Legacy US-01 · FR-004)

As a **traveler**, I want to see only places a curator has reviewed, so that I do not act on unchecked data.

- **AC1** Given 10 candidate places exist, when I search, plan or ask the Guide, then none of them appears.
- **AC2** Given a candidate's identifier, when the app requests its details, then "not found" is returned.

### US-004 — Import candidates safely (Must · Legacy US-00 · FR-009, FR-010)

As a **curator**, I want to import candidate places from a named open-dataset release, so that I can review them
without changing what travelers see.

- **AC1** Given a named release for Hội An, when I import it, then candidates appear tagged with the release name.
- **AC2** Given the import completed, when a traveler searches, then the published results are unchanged.
- **AC3** Given I import the same release again, when it completes, then the candidate count is unchanged.

### US-005 — Complete bilingual, sourced content (Must · Legacy US-00 · FR-011, FR-012, FR-016, FR-083)

As a **curator**, I want to record Vietnamese and English content and a dated source for each operational fact,
so that a place is ready to publish.

- **AC1** Given a candidate, when I enter names and descriptions in both languages and reload, then they are unchanged.
- **AC2** Given a candidate, when I record opening hours with a source and verification date, then all three are stored.
- **AC3** Given an entrance is not verified, when I record it as "unknown" with a source, then it is accepted.
- **AC4** Given a source, when I record its licence and attribution text, then the text is available for display.

### US-006 — Publish only complete places (Must · Legacy US-00 · FR-013, FR-014, FR-015, FR-082)

As a **curator**, I want publishing to be refused until a place is complete, so that I cannot publish an
unreviewed or unsourced place by mistake.

- **AC1** Given a candidate lacks English content, when I publish, then it is refused and the missing item is named.
- **AC2** Given a candidate has a fact without a source, when I publish, then it is refused and the fact is named.
- **AC3** Given a complete candidate, when I publish it from the curator tool, then a traveler can find it within 1 minute.
- **AC4** Given I published a place, when I view it in the curator tool, then my name and the publication time are shown.

### US-007 — Unpublish (Should · FR-017)

As a **curator**, I want to unpublish a place, so that a wrong or no-longer-licensed place stops reaching travelers.

- **AC1** Given a published place, when I unpublish it, then it no longer appears in new searches, proposals or Guide answers.
- **AC2** Given it was unpublished, when I view the candidate list, then it is there for correction.

### US-008 — Coverage per city (Should · FR-018)

As a **curator**, I want to see the number of published places per city, so that I can track progress toward
30 per city.

- **AC1** Given places are published in five cities, when I open the coverage view, then each city's count equals the catalog report.

### US-009 — Review AI drafts (Should · FR-019, FR-084)

As a **curator**, I want AI-drafted text to be marked and to require my confirmation, so that I can work faster
without publishing unchecked content.

- **AC1** Given a field drafted by AI, when I view it, then it is marked "AI draft".
- **AC2** Given any AI-draft field is unconfirmed, when I publish, then publication is refused.
- **AC3** Given I confirm every drafted field, when I publish, then it succeeds.

### US-010 — Describe my trip (Must · Legacy US-02 · FR-020, FR-021)

As a **traveler**, I want to describe my trip in Vietnamese or English, or fill in a form, so that I can start
planning in the way that suits me.

- **AC1** Given English is selected, when Tom writes "2 relaxed days in Hội An, old town and food", then the request is accepted.
- **AC2** Given Vietnamese is selected, when Linh writes "2 ngày ở Huế, thích di tích", then the request is accepted.
- **AC3** Given I do not want to type, when I fill in city, start date, days, daily hours, pace, interests, travel modes and must-sees, then I can request a proposal from the form alone.

### US-011 — Reuse preferences (Should · FR-073, FR-096)

As a **traveler**, I want to save my usual pace and interests, so that I do not re-enter them for each trip.

- **AC1** Given I saved pace "relaxed" and interest "food", when I start a new request, then the form is prefilled with them.
- **AC2** Given I did not choose to save, when I finish a request, then no preferences are stored.

### US-012 — Clarify missing details (Must · Legacy US-02 · FR-022)

As a **traveler**, I want to be asked for anything missing from my request, so that I get a proposal that matches
what I asked for.

- **AC1** Given my request has no start date, when I submit it, then I am asked for the start date before any proposal appears.
- **AC2** Given my request names no city, when I submit it, then I am asked for the city.
- **AC3** Given "a few days" instead of a number of days, when I submit, then I am asked for 1, 2 or 3 days.

### US-038 — Refuse unsupported requests (Must · Legacy US-02 · FR-023, FR-085, FR-086)

As a **traveler**, I want to be told clearly when a request is outside what Gonarra supports, so that I can
change it instead of receiving a wrong plan.

- **AC1** Given I ask for 4 days, when I submit, then I am told trips are 1–3 days.
- **AC2** Given I ask for Huế and Hội An together, when I submit, then I am told a trip covers one city.
- **AC3** Given I ask for Nha Trang, when I submit, then I am told the five supported cities.

### US-013 — Proposal from reviewed places (Must · Legacy US-02 · FR-024, FR-025, FR-026, FR-087)

As a **traveler**, I want a proposal for the days and city I asked for, built only from reviewed places, so that
I can trust every stop exists and is in that city.

- **AC1** Given a complete request for 2 days in Hội An, when the proposal appears, then it has exactly 2 days.
- **AC2** Given the proposal, when I inspect every stop, then each is a published Hội An place.
- **AC3** Given the generator returned an unknown or other-city place, when the proposal is shown, then that item is absent.
- **AC4** Given I marked a must-see, when the proposal appears, then it contains the must-see or states why not.

### US-014 — Timeline, map and legs (Must · Legacy US-03 · FR-027, FR-028, FR-029, FR-088)

As a **traveler**, I want each day as an ordered timeline and on a map with real travel times, so that I can
picture how the day runs.

- **AC1** Given a proposal, when I open day 1, then stops are in order with arrival and departure times that do not overlap.
- **AC2** Given I tap a stop on the map, when the timeline is shown, then the same stop is selected, and vice versa.
- **AC3** Given a leg, when I view it, then it shows walk or drive, distance and duration from the routing provider.
- **AC4** Given the routing provider has no route for a leg, when I view it, then it reads "unavailable" with no estimate.

### US-015 — Feasibility and blocking (Must · Legacy US-03 · FR-030, FR-031, FR-032)

As a **traveler**, I want to see whether each day fits and exactly what blocks it, so that I fix problems before
I go rather than on site.

- **AC1** Given a museum is planned when it is closed, when I view the day, then the stop is flagged "closed at planned time".
- **AC2** Given the last stop ends after my day window, when I view the day, then the day is flagged "day window exceeded".
- **AC3** Given at least one blocking conflict, when I view the proposal, then Plan Health is "blocked" with the list of reasons.
- **AC4** Given the proposal is blocked, when I tap Save, then saving is refused and the reason is shown.

### US-016 — Reorder stops (Must · Legacy US-05 · FR-033, FR-039, FR-089)

As a **traveler**, I want to change the order of stops in a day, so that the day follows the sequence I prefer.

- **AC1** Given day 1, when I move stop 3 to position 1, then the new order and recalculated times are shown.
- **AC2** Given the move, when recalculation is running, then Save is unavailable.
- **AC3** Given the new order creates a blocking conflict, when recalculation completes, then the conflict is flagged.
- **AC4** Given I save, when I reopen the trip, then the new order is shown.

### US-039 — Add a place (Must · Legacy US-05 · FR-034, FR-039, FR-089)

As a **traveler**, I want to add a place I found to a day, so that the plan includes what I want to see.

- **AC1** Given a published Hội An place, when I add it to day 2 of a Hội An trip, then it is inserted and times are recalculated.
- **AC2** Given a Huế place, when I try to add it to a Hội An trip, then it is refused.
- **AC3** Given the addition, when recalculation is running, then Save is unavailable.

### US-040 — Remove a stop (Must · Legacy US-05 · FR-035, FR-039, FR-089)

As a **traveler**, I want to remove a stop, so that the day is not overloaded.

- **AC1** Given a stop, when I remove it, then the stop and its legs disappear and times are recalculated.
- **AC2** Given the removal, when recalculation is running, then Save is unavailable.
- **AC3** Given I save, when I reopen the trip, then the stop is absent.

### US-041 — Replace a stop (Must · Legacy US-05 · FR-036, FR-039, FR-089)

As a **traveler**, I want to swap a stop for another place, so that I can change my mind without rebuilding the day.

- **AC1** Given a stop, when I choose Replace, then only published places of the trip's city are offered.
- **AC2** Given I pick a replacement, when recalculation completes, then times and legs reflect it and any new blocking conflict is flagged.
- **AC3** Given I save, when I reopen the trip, then the replacement is shown.

### US-017 — Durations and modes (Must · Legacy US-05 · FR-037, FR-038, FR-039, FR-089)

As a **traveler**, I want to change how long I stay and whether I walk or drive, so that the day fits my pace.

- **AC1** Given a stop of 60 min, when I set 90 min, then its departure and all later times on that day move by 30 min.
- **AC2** Given a walking leg, when I switch it to driving, then its distance and duration update and later times follow.
- **AC3** Given either change creates a blocking conflict, when recalculation completes, then the conflict is flagged.

### US-018 — Explicit Save (Must · Legacy US-05 · FR-040, FR-041, FR-045, FR-090)

As a **traveler**, I want only the version I explicitly save to become my trip, so that Gonarra never replaces my
plan without my decision.

- **AC1** Given a new proposal, when I view it, then it is labelled unsaved.
- **AC2** Given I leave the screen before Save, when I reopen my trip, then the previous saved version is shown.
- **AC3** Given I tap Save and the request is retried, when I reopen the trip, then exactly one new version exists.
- **AC4** Given I have 3 saved trips, when I open my trips, then all 3 are listed and each reopens at its last saved version.

### US-019 — Nothing lost on failure (Must · Legacy US-05 · FR-042, FR-043, FR-044)

As a **traveler**, I want my saved trip and my unsaved edits to survive failures, so that I can trust Gonarra with
my plan.

- **AC1** Given the AI service fails during generation, when I return to my trip, then the saved version is unchanged.
- **AC2** Given the routing provider fails after my edits, when the error is shown, then my unsaved edits are still present.
- **AC3** Given the network drops during Save, when I retry, then either the save completed once or my edits are still present.
- **AC4** Given my trip was saved from another device after I opened it, when I Save, then I see a conflict message, the other save is kept and my edits remain.

### US-020 — Delete a trip (Should · FR-046)

As a **traveler**, I want to delete a trip I no longer need, so that my trip list stays relevant.

- **AC1** Given a saved trip, when I delete it and confirm, then it disappears from my trips.
- **AC2** Given I cancel the confirmation, when I return to my trips, then the trip is still there.

### US-021 — Lock a must-see stop (Should · Legacy US-04 · FR-047, FR-091) — HA-02

As a **traveler** with a must-see stop, I want to lock it, so that later changes cannot remove or move it.

- **AC1** Given the HA-02 saved 2-day Hội An trip, when I lock a day-2 stop, then it shows a lock indicator.
- **AC2** Given the lock, when I save and reopen the trip, then the stop is still locked.
- **AC3** Given a locked stop, when I unlock it, then the indicator disappears.

### US-042 — Regenerate one day (Should · Legacy US-04 · FR-048, FR-049, FR-050) — HA-02

As a **traveler**, I want to regenerate only one day while keeping my locked stops, so that I can change my
afternoon without losing what I care about.

- **AC1** Given the HA-02 trip with a locked day-2 stop, when I regenerate day 2, then day 1 is identical before and after.
- **AC2** Given the same, when I regenerate day 2, then the locked stop keeps its place, day and visit duration.
- **AC3** Given the regenerated day, when I reopen the trip before Save, then the previous saved version is shown.
- **AC4** Given an AI or routing failure during regeneration, when it ends, then the saved trip, my edits and the lock are unchanged.

### US-022 — Place card on site (Must · Legacy US-06 · FR-051, FR-052, FR-053)

As a **traveler** on site, I want a card with the place's names, a Vietnamese address and its entrance, so that I
can show a driver where to go and find the way in.

- **AC1** Given a stop of my saved trip, when I open its card, then I see its Vietnamese and English names.
- **AC2** Given the card, when I show it to a driver, then it shows the Vietnamese address or "address unknown".
- **AC3** Given the card, when I look for the entrance, then the verified entrance is shown or "unknown".

### US-023 — Directions handoff (Must · Legacy US-06 · FR-054)

As a **traveler**, I want to open directions to a stop in my usual maps app, so that I can navigate there.

- **AC1** Given a stop with a verified entrance, when I tap Directions, then the maps app opens with the entrance as destination.
- **AC2** Given a stop whose entrance is unknown, when I tap Directions, then the maps app opens with the place position.

### US-024 — Today view (Should · FR-055)

As a **traveler** during my trip, I want today's stops in order, so that I know what is next without searching.

- **AC1** Given today is day 2 of a saved trip, when I open Today, then day 2's stops are listed in order.

### US-025 — Grounded answers (Must · Legacy US-07 · FR-056, FR-058, FR-078)

As a **traveler**, I want to ask about a place and see where the answer comes from, so that I can trust it.

- **AC1** Given Linh's language is Vietnamese, when she asks when a pagoda closes, then the answer is in Vietnamese.
- **AC2** Given any answer in either language, when it is shown, then at least one reviewed source with its verification date is listed.
- **AC3** Given the answer exists only on the open web, when I ask, then I am told evidence is insufficient.

### US-026 — Honest "I don't know" (Must · Legacy US-07 · FR-057)

As a **traveler**, I want to be told when reviewed sources do not cover my question, so that I am not misled by an
invented answer.

- **AC1** Given a question outside the reviewed sources, when I ask it, then I see "insufficient evidence" and no answer text.
- **AC2** Given the out-of-catalog set, when it is run, then at least 90% return "insufficient evidence".

### US-027 — Spoken question (Should · FR-059, FR-063)

As a **traveler** with my hands full, I want to ask a question by speaking, so that I can use the Guide while
walking.

- **AC1** Given microphone permission was never asked, when I first tap the microphone, then the permission is requested at that moment.
- **AC2** Given I speak a question in Vietnamese or English, when it is transcribed, then the answer follows the same rules as a text answer.
- **AC3** Given I denied the microphone, when I use the Guide, then text questions still work.

### US-043 — Read-aloud answer (Should · FR-060)

As a **traveler**, I want to hear a Guide answer read aloud, so that I can keep my eyes on the street.

- **AC1** Given a completed answer in Vietnamese, when I tap Read aloud, then the audio matches the displayed text.
- **AC2** Given a completed answer in English, when I tap Read aloud, then the audio matches the displayed text.

### US-028 — Photo identification (Should · FR-061, FR-062, FR-092, FR-093)

As a **traveler**, I want to take a photo of the place in front of me and learn which published place it is, so
that I can open its card and ask about it.

- **AC1** Given I first use the photo feature, when I tap it, then camera and location permissions are requested at that moment.
- **AC2** Given I am within 300 m of a published place, when I photograph it, then that place is the first result.
- **AC3** Given no published place within 300 m matches, when I photograph, then I see "not recognised".
- **AC4** Given I denied camera or location, when I use the app, then search, planning and text questions still work.

### US-029 — Stay handoff (Must · FR-064)

As a **traveler**, I want to open a booking site for stays with my trip's city and dates, so that I can book where
to sleep without re-entering my trip.

- **AC1** Given a saved 2-day Hội An trip, when I tap "Find a stay" and choose a partner, then it opens with Hội An and my check-in and check-out dates.
- **AC2** Given a partner that cannot accept check-in and check-out dates, when I view the partner list, then it is not listed.

### US-030 — Activity handoff (Must · FR-065)

As a **traveler**, I want to open a booking site for activities from a stop, so that I can look for tours there.

- **AC1** Given a stop in Huế, when I tap "Find activities" and choose a partner, then it opens with Huế filled in.

### US-031 — Indicative prices (Could · FR-066, FR-067, FR-080, FR-081)

As a **traveler**, I want to see indicative stay prices for my dates, so that I can judge cost while planning.

- **AC1** Given a saved trip, when I open stays, then prices for at least one stay are shown, or the section is hidden with a message.
- **AC2** Given a price is shown, when I read it, then I see its retrieval time.
- **AC3** Given a price is shown, when I read it, then I see a notice that the partner confirms the final price.
- **AC4** Given I save the trip, when I reopen it, then no price is stored with it.

### US-032 — Private trips (Must · Legacy US-08 · FR-068, FR-069, FR-094, FR-095)

As a **traveler**, I want my trips, preferences and questions visible only to my account, so that my plans stay
private.

- **AC1** Given I am signed out, when I open My trips, then I am asked to sign in.
- **AC2** Given another traveler's trip identifier, when it is requested with my account, then access is denied.
- **AC3** Given a denied request, when it is processed, then no external service is called.
- **AC4** Given I sign out, when I return to the app, then my private screens are not shown.

### US-033 — Delete my account (Must · Legacy US-08 · FR-071, FR-072)

As a **traveler** or **study participant**, I want to delete my account and see when it is done, so that I know my
data is gone.

- **AC1** Given I confirm deletion, when I view account status, then it shows "in progress".
- **AC2** Given deletion completes, when I view status, then it shows "completed"; if it fails, the reason is shown.
- **AC3** Given 24 hours have passed since confirmation, when the live service, identity provider and logs are checked, then no record of mine remains.
- **AC4** Given a backup taken before my deletion is restored in a test, when the restore completes, then my deletion is re-applied.

### US-034 — Bilingual app (Must · FR-075, FR-076, FR-097)

As a **traveler**, I want all screens and place content in Vietnamese or English, so that I can use Gonarra in my
language.

- **AC1** Given I choose English, when I open every screen, then no untranslated string appears.
- **AC2** Given I choose Vietnamese, when I open every screen, then no untranslated string appears.
- **AC3** Given English is selected, when I view a place, then its description is in English and its Vietnamese name is visible.

### US-035 — AI data transparency (Must · FR-070, FR-074)

As a **study participant**, I want to know what Gonarra sends to the AI service, so that I can take part with
informed consent.

- **AC1** Given I have not planned before, when I start my first request, then a notice explains that request content goes to an external AI service and identity and precise location do not.
- **AC2** Given 20 recorded AI requests from test sessions, when they are inspected, then none contains an account identifier, contact detail or precise coordinates.

### US-036 — Pseudonymous session measurement (Should · FR-077)

As a **study participant**, I want my session measured under a code without my identity or my questions, so that
I contribute evidence without exposing myself.

- **AC1** Given a study account, when I complete a planning task, then a session log records participant code, language, request time, first-proposal time and Save outcome.
- **AC2** Given the log, when it is inspected, then it contains no request or question text and no account identifier.
- **AC3** Given a non-study account, when it plans, then no session log is created.

### US-037 — Transport handoff (Must · FR-079)

As a **traveler**, I want to open a transport booking site for getting to my trip's city on its start date, so
that I can arrange how to get there without re-entering my trip.

- **AC1** Given a saved trip to Đà Nẵng starting on a given date, when I tap "Find transport", then the transport partner opens with Đà Nẵng as destination and that date filled in.

## Legacy mapping

| Legacy story | Legacy FR / UC | New stories |
|---|---|---|
| US-00 | FR-00 / UC-00 | US-004, US-005, US-006 |
| US-01 | FR-01 / UC-01 | US-001, US-002, US-003 |
| US-02 | FR-02 / UC-02 | US-010, US-012, US-013, US-038 |
| US-03 | FR-03 / UC-02 | US-014, US-015 |
| US-04 | FR-04 / UC-03 (HA-02) | US-021, US-042 (scope narrowed to one-day regeneration, OQ-012) |
| US-05 | FR-05 / UC-03 | US-016, US-017, US-018, US-019, US-039, US-040, US-041 |
| US-06 | FR-05, FR-06 / UC-04 | US-022, US-023 |
| US-07 | FR-06 / UC-05 | US-025, US-026 |
| US-08 | FR-07 / UC-06 | US-032, US-033 |

Coverage: 43 stories; 97/97 FRs covered (full matrix in `traceability.md`). Open questions affecting stories:
OQ-012 (regeneration scope), OQ-013 (US-036) and OQ-014 (US-020, US-024) are closed as recommended (SRC-100 A-022) — see PRD.
