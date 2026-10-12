# Danang TourGuide — Business Requirements

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Problem and value hypothesis

Travelers unfamiliar with Da Nang may need to move between place articles, maps, planning tools and local explanations. The proposed value is a continuous, source-aware journey from discovery to an editable plan and on-site assistance. Fragmentation and its severity are hypotheses to validate through interviews, not established research findings.
Current-process hypothesis: collect places → estimate travel/visit time → transfer a plan to a map → search information during visits. Proposed process: Explore → inspect/save → preferences → validated preview/accept → edit/map → active trip → arrival/audio/Ask → complete/skip.

## Stakeholders

| Stakeholder | Goal / responsibility |
|---|---|
| Traveler | Discover places, control itinerary, understand uncertainty and obtain useful local information |
| Student developer/product owner | Own requirements/design, curate content and maintain evidence |
| Academic supervisor | Confirm approved objectives, research method and assessment requirements |
| Technical/factual reviewer | Review applicable design, access control and source-supported claims |
| Narrator/media rights holder | Authorise recording and publication; review attribution |
| Research/UAT participant | Voluntary feedback or task evaluation under agreed consent |

One person may cover multiple development roles; reviewer names are recorded when assigned. Required independent reviews in the repository SOP remain applicable to high-risk implementation/release changes. Public discovery/audio needs no account; private trips/saves and Ask require a session.

## Business requirements

| ID | Outcome | Acceptance intent | Engineering requirements |
|---|---|---|---|
| BIZ-01 | Discover reliable Da Nang places | Travelers can browse, search and inspect curated published places with factual sources. | FR-POI-01, FR-EXP-01, FR-PLC-01, FR-MAP-01 |
| BIZ-02 | Plan a realistic trip | Travelers provide explicit preferences, review a structured proposal, accept and edit stops without losing prior work. | FR-PREF-01, FR-TRP-02, FR-TRP-03, FR-TRP-04 |
| BIZ-03 | Receive help during a visit | An active trip identifies its current stop; arrivals and reviewed audio support the visit without requiring background GPS. | FR-TRV-01, FR-TRV-02, FR-TRV-03 |
| BIZ-04 | Ask questions with evidence | Answers cite reviewed sources or state that evidence is insufficient. | FR-AI-01 |
| BIZ-05 | Keep private trips and saves | Owner-scoped persistent trips/saves and renewable sessions. | FR-AUTH-01, FR-SAV-01 |
| BIZ-06 | Deliver defensible engineering evidence | Traceable design, repeatable evaluation, usability study and honest limitations. | NFR-SEC-01, NFR-PER-01, NFR-REL-01, NFR-ACC-01, NFR-USAB-01, NFR-TRUST-01 |
| BIZ-07 | Optional input conveniences | Landmark scan, speech input and alternate login only after P0 acceptance. | FR-CAM-01, FR-STT-01, FR-AUTH-02 |

## Delivery boundary

[PRD](01-PRD.md) owns feature priorities, corpus targets, acceptance and exclusions. BIZ-01–06 are P0; BIZ-07 is optional backlog. The agreed product includes curated discovery, editable AI-assisted planning, foreground/manual arrival, human audio and source-grounded RAG. No payment or booking workflow is required.

## Success and research

Success is assessed through traceable requirements, preserved user edits, source-supported answers, reliable progression and usability of the core journey. Numeric targets and study protocols are owned by [PRD](01-PRD.md) and [Test Plan](08-Test-Plan.md); they are project proposals, not institutional standards or existing results.
[Research Plan](17-Research-and-Academic-Plan.md) tests planning habits, factual trust, edit needs, audio usefulness and permission/failure handling. Record contradictory findings and revise business hypotheses when warranted.

## Constraints and acceptance authority

One developer. Deadline/capacity, budget, target device and approved academic proposal are unresolved. Student/product owner reviews product scope; supervisor confirms academic fit; technical reviewer examines significant design/security risks. [Decisions](09-Project-Decisions.md) records owners and blocking gates. Product scope selection does not imply approval of deployment cost, study consent or institutional requirements.

## Vocabulary

POI: point of interest. RAG: retrieval of reviewed evidence before answer generation. P0: required core delivery. P1: optional expansion after P0 evaluation. Corpus: versioned reviewed collection of POI facts and passages. These terms also apply to all other documents.
