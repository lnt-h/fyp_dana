# DaNavi — Business Requirements

Version 1.3 | 2026-10-19 | Status: product scope selected; technical and academic review still required. Document control and evidence status: [Index](00-INDEX.md).

## Problem and value hypothesis

International first-time visitors to Da Nang may need to move between place articles, maps, planning tools and local explanations, often across English and Vietnamese place names. The proposed value is an English-first, source-aware mobile journey from discovery to an editable one-day plan and on-site assistance. Fragmentation, trust needs and the value of this integrated journey are hypotheses to test; this document does not claim that individual features or their combination are novel or superior.

Current-process hypothesis: collect places → estimate travel/visit time → transfer a plan to a map → search for explanations during visits. Proposed product flow: Welcome → Home → Explore/Detail → planning preferences → validated Preview → **Save & customize** → Edit → route preview → Trip Ready → external directions/Active Trip → **I've arrived** → Audio/Ask → next stop → Completed. Save, Ask and Generate introduce authentication only at the protected action; browsing and an audio preview remain public.

## Stakeholders

| Stakeholder | Goal / responsibility |
|---|---|
| International first-time visitor | Discover places in English, match familiar and local place names, control a one-day itinerary, understand uncertainty and obtain useful local information |
| Student developer/product owner | Own requirements/design, curate content and maintain evidence |
| Academic supervisor | Confirm approved objectives, research method and assessment requirements |
| Technical/factual reviewer | Review applicable design, access control and source-supported claims |
| English narrator/media rights holder | Authorise recording, publication and permitted offline use; review attribution |
| Bilingual translation reviewer | Check English place content against Vietnamese-language sources and record source language/revision |
| Research/UAT participant | Voluntary feedback or task evaluation under agreed consent |

One person may cover multiple development roles; reviewer names are recorded when assigned. Required independent reviews in the repository SOP remain applicable to high-risk implementation/release changes. Guests can Explore, open Detail and play an audio preview. Save, Ask and Generate require a session; a completed guest planning form survives the login round trip and is not auto-submitted.

## Business requirements

| ID | Outcome | Acceptance intent | Engineering requirements |
|---|---|---|---|
| BIZ-01 | Discover reliable Da Nang places | Travelers can browse, search English/Vietnamese/romanized place aliases and inspect curated published places with factual sources. | FR-POI-01, FR-EXP-01, FR-PLC-01, FR-MAP-01 |
| BIZ-02 | Plan a realistic one-day trip | Travelers provide an explicit start point and preferences, review a structured proposal, accept through “Save & customize” and edit stops without losing prior work. | FR-PREF-01, FR-TRP-02, FR-TRP-03, FR-TRP-04 |
| BIZ-03 | Receive help during a visit | An active trip identifies its current stop, hands off to external directions, reconciles on return, supports manual/foreground arrival and makes authorised essentials available from a read-only cache. | FR-TRV-01, FR-TRV-02, FR-TRV-03, FR-TRV-04, FR-OFF-01 |
| BIZ-04 | Ask questions with evidence | Answers cite reviewed sources or state that evidence is insufficient. | FR-AI-01 |
| BIZ-05 | Control private data and account lifecycle | Owner-scoped persistent trips/saves, renewable sessions and reauthenticated account deletion. | FR-AUTH-01, FR-AUTH-03, FR-SAV-01 |
| BIZ-06 | Deliver defensible engineering evidence | Traceable design, repeatable evaluation, usability study and honest limitations. | NFR-SEC-01, NFR-PER-01, NFR-REL-01, NFR-ACC-01, NFR-USAB-01, NFR-TRUST-01 |
| BIZ-07 | Optional input conveniences | Landmark scan, speech input and alternate login only after P0 acceptance. | FR-CAM-01, FR-STT-01, FR-AUTH-02 |

## Delivery boundary

[PRD](01-PRD.md) owns feature priorities, corpus targets, acceptance and exclusions. BIZ-01–06 are P0; BIZ-07 is optional backlog. The agreed product includes 15–20 reviewed POIs, a one-day car/ride-hailing plan, editable AI assistance, route preview and external handoff, foreground/manual arrival, five flagship human audio guides, a read-only essentials cache, authenticated source-grounded Ask and account deletion. No payment, booking, background tracking, in-app turn-by-turn navigation or full offline map/routing workflow is required.

## Success and research

Success is assessed through traceable requirements, preserved guest form and user edits, source-supported answers, reliable return from external directions, honest cache/sync state and usability of the core journey. Numeric targets and study protocols are owned by [PRD](01-PRD.md) and [Test Plan](08-Test-Plan.md); they are project proposals, not institutional standards or existing results.
[Research Plan](17-Research-and-Academic-Plan.md) tests English-first discovery, alias search, planning habits, factual trust, edit needs, audio usefulness and authentication/permission/failure handling with the target audience. Record contradictory findings and revise business hypotheses when warranted.

## Constraints and acceptance authority

One developer. Deadline/capacity, budget, target device and approved academic proposal are unresolved. Student/product owner reviews product scope; supervisor confirms academic fit; technical reviewer examines significant design/security risks; a bilingual reviewer approves English translations before publication. [Decisions](09-Project-Decisions.md) records owners and blocking gates. Product scope selection does not imply approval of deployment cost, content rights, study consent or institutional requirements.

## Vocabulary

POI: point of interest. RAG: retrieval of reviewed evidence before answer generation. P0: required core delivery. P1: optional expansion after P0 evaluation. Corpus: versioned reviewed collection of POI facts and passages. These terms also apply to all other documents.
