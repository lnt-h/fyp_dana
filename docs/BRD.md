# Business requirements • Vietnam itinerary planner

**Decision baseline · 2026-11-02**

Gonarra is the working name. The primary audience is independent travelers planning a short city visit in Vietnamese or English. A traveler may already know which places they want to visit but still has to check whether the opening times, travel legs and daily schedule fit together. Reducing that effort while preserving traveler control is the business hypothesis to test.

## Objectives and evidence for the release decision

| ID | Business outcome | Measurement and decision owner |
|---|---|---|
| BR-01 | Travelers can assemble a usable short city itinerary from trusted local content. | Product owner reviews completed planning tasks, time to first usable proposal and reasons for abandonment, split by city and language. |
| BR-02 | Travelers can judge feasibility and change part of a trip without losing their choices. | QA reviews known-conflict detection, lock violations and saved-plan integrity. Researcher observes whether participants understand warnings and Save. |
| BR-03 | Travelers can act on local information and recognize uncertainty. | Content reviewer samples execution cards and Guide claims against dated sources, including unknown facts and appropriate refusals. |
| BR-04 | The team can operate a private service across all launch destinations. | Technical lead reviews ownership tests, deletion and recovery evidence, provider cost per completed proposal and native-device release results. |

## Stakeholders and responsibilities

Travelers choose and accept itineraries. The product owner decides scope and release. Bilingual curators own sourcing, rights and publication. Engineering owns scheduling, provider integrations and recovery. QA maintains release evidence. The FYP researcher and supervisor agree recruitment, consent and evaluation thresholds before collection.

## Scope, dependencies and decision gates

Release the five cities together: Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Hội An and Huế. Each needs at least 12 reviewed planning-ready bilingual places (target 15) and feasible one-, two- and three-day test cases. A trip covers one city. The business scope ends at itinerary acceptance and local assistance. Booking, payments, social publishing, GPS arrival and recorded audio are outside V1.

Content review capacity, rights, route coverage and provider spend constrain launch. If a city misses its gate, hold the common release and record the missing evidence. Freeze performance, cost and pilot targets before evaluation. A cross-owner disclosure, lost accepted trip or changed locked stop blocks release. Product and technical leads review findings with the [research protocol](RESEARCH.md) and [acceptance suite](TESTING.md). The [PRD](PRD.md) translates these objectives into product requirements.
