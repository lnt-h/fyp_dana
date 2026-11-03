# Glossary — Gonarra

| Field | Value |
|---|---|
| Document ID | GONARRA-INTAKE-GLOSSARY |
| Version | 0.1 |
| Status | Draft |
| Owner | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor (OQ-001) — [Pending] |
| Date | 2026-11-04 (written retroactively from SRC-100 and BRD v0.4) |
| Prompt used | `requirements/Intake_Intent_Prompt.md` v2.0, adapted copy `docs/00-governance/prompt-templates/requirements/Intake_Intent_Prompt.md` |

Terms are taken from BRD §14 (GONARRA-BRD v0.4) without change of meaning. "—" means the BRD names no synonym to
avoid.

| Term | Definition | Synonyms to avoid |
|---|---|---|
| Published place | A place the curator reviewed and published, with sources and content in both languages; visible to travelers | "POI" for unreviewed records |
| Candidate place | An imported place not yet published; never visible to travelers | — |
| Curator | The role that reviews and publishes places; held by STK-003 | — |
| Operational fact | A fact that affects a visit: opening hours, admission, entrance, closure | — |
| Stale | An operational fact verified more than 180 days earlier (ASM-008) | "old" |
| Proposal | An unsaved itinerary produced or changed by Gonarra | "plan" when unsaved |
| Saved itinerary | The itinerary version the traveler explicitly saved | "final plan" |
| Valid itinerary | A saved itinerary of 1–3 days in one launch city with no blocking conflict | — |
| Leg | The travel between two consecutive stops on a day | "route" |
| Day window | The start and end time the traveler sets for a day | "time window" |
| Blocking conflict | A stop planned outside its known opening hours; a leg without a distance and duration; or a day whose last stop ends after its day window | "error" |
| Plan Health | The overall feasibility status of a proposal (good, warning, blocked) with its reasons | "score" |
| Lock | A traveler's mark that a stop must keep its place, day and duration during regeneration | — |
| Place card | The on-site view of a stop with names, driver address, entrance and dated facts | "execution card" (legacy) |
| Guide | Question answering about published places from reviewed sources | "chatbot" |
| Nearby | Within 300 m of the traveler's location (ASM-009) | — |
| Handoff | Opening a partner's app or site with the trip's city (and dates) | "booking" |
| Booking partner | Agoda and Booking.com (stays), Klook (activities), 12Go (transport); the list may change only if a partner cannot accept the required search parameters (AC-018) | "OTA" |
| Confirmed preferences | The trip inputs the traveler confirms before generation: city, start date, number of days, day windows, party, pace, interests, dietary needs, budget band, must-see and avoided places, allowed travel modes | "settings" |
| Reviewed alias | An alternative name for a place, approved by the curator and searchable in both languages | — |
| Precise location | Device coordinates more exact than the city or a published place | — |
| Indicative price | A partner price shown at a point in time; not confirmed, not stored | "price" |
| Private data | A traveler's account, trips, preferences, questions and saved places | — |
| Golden scenario / evaluation set | A fixed, pre-defined test input with its expected result, frozen before tuning (ASM-011) | — |
| User study | The consented usability evaluation of BR-023 | "pilot" |
