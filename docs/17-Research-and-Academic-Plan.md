# Danang TourGuide — Research and Academic Evidence

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Aim and objectives: proposed, not institutionally approved

Proposed aim: design and evaluate a source-aware mobile Da Nang travel companion integrating curated discovery, editable AI-assisted itineraries and foreground visit assistance. The actual approved proposal/rubric is unavailable; the following working objectives must be compared with it, not substituted silently.

| Objective | Planned evidence | Trace |
|---|---|---|
| OBJ-01 Understand traveler needs and define bounded requirements | Discovery themes, contradictory cases, reviewed requirements | BIZ-01–04; BRD/PRD |
| OBJ-02 Design traceable mobile/API/data architecture | Alternatives, 4+1 views, state/DTO/integrity rules | BIZ-05/06; SAD/Blueprint/DB/API/UI |
| OBJ-03 Deliver curated discovery and editable validated planning | Rights-reviewed corpus, end-to-end plan/edit demonstration | FR-POI/EXP/PLC/MAP/PREF/TRP |
| OBJ-04 Provide foreground/manual arrival, reviewed audio and source-grounded Ask | Device/field and held-out source-support evidence | FR-TRV-01–03, FR-AI-01 |
| OBJ-05 Evaluate engineering and usability with explicit limitations | Ownership/concurrency/failure/performance/accessibility/UAT results | Six NFRs; Test Plan |

All implementation, participant and measured-outcome evidence is pending. Objective IDs here are working IDs; preserve the official wording/IDs when supplied and record changes/approval.

## Research questions and discovery method

RQ-01: How do relevant travelers currently choose places, estimate a day and revise it? RQ-02: Which facts, sources and uncertainty states affect decisions? RQ-03: When are foreground arrival and recorded audio useful/acceptable? RQ-04: Does the delivered core journey support unassisted tasks and perceived usability? RQ-05: How often does source-grounded Ask provide supported answers versus refuse appropriately?
Discovery: proposed five semi-structured interviews with travelers of differing familiarity/device habits. This is a feasible initial qualitative target, not a universal sample-size rule or proof of saturation. Use a survey only for a stated research question and approved sampling approach; no mandatory 20-response quota is asserted. Supervisor confirms method before recruitment.
Interview sequence: consent → recent real trip/tools → place selection/time/changes → trusted facts → reveal proposed journey → audio/location/source inspection/failure preferences → contradictory or unwanted behavior. Avoid leading questions. Code anonymised observations into themes, distinguish observation from interpretation, retain negative cases and map justified requirement changes to BIZ/FR IDs.

## Reviewed research foundations

Public sources below were checked on 2026-10-12. Summaries state what the source supports; implications are this project's design reasoning. Literature review remains preliminary and must be expanded with domain-specific studies before the final academic report.

| Source | Supported finding / scope | Project implication and limit |
|---|---|---|
| Lewis et al. (2020), [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/html/2005.11401v4) | Combines parametric generation with retrieved nonparametric passages; evaluates knowledge-intensive tasks | Basis for retrieval-before-generation. This project uses inference-time provider adapters, not the paper's end-to-end fine-tuned BART/DPR implementation; its reported results are not our results |
| Liu et al. (2023), [Lost in the Middle](https://arxiv.org/html/2307.03172v3) | Controlled QA/retrieval experiments show sensitivity to relevant evidence position in long context | Evaluate passage relevance/order/context size rather than assume more text always helps; findings on tested models are not a benchmark of our future chosen model |
| Brooke, [SUS: A quick and dirty usability scale](https://digital.ahrq.gov/sites/default/files/docs/survey/systemusabilityscale%2528sus%2529_comp%255B1%255D.pdf), original instrument hosted by AHRQ | Ten-item subjective usability instrument and scoring procedure | Use alongside task completion, not as task-success percentage. Mean68 is a project target requiring justification/review, not a required graduation score |
| [SWEBOK: Software Engineering Management](https://swebokwiki.org/Chapter_7:_Software_Engineering_Management) | Project scope, planning, estimates, risks and tailored management activities | Use reviewable artifacts and evidence appropriate to one developer; not a requirement for enterprise ceremonies |

## Technical integration references

| Primary source | Decision supported / limits |
|---|---|
| [pgvector maintained documentation](https://github.com/pgvector/pgvector) | Exact search, distance operators, optional approximate indexes and vector type behavior; pin actual extension version and benchmark locally |
| [Google Routes overview](https://developers.google.com/maps/documentation/routes/compute-route-over) | Provider route integration; trial modes/regional availability and review attribution/caching terms before pilot |
| [OpenAPI 3.0.3 specification](https://spec.openapis.org/oas/v3.0.3.html) | Chosen contract syntax/schema subset; describes interfaces, not runtime correctness |
| [React Native accessibility documentation](https://reactnative.dev/docs/accessibility) | Native accessibility properties/semantics; verify screen-reader/scaling behavior on target devices |

No source above establishes that RAG cannot hallucinate, that five interviews are sufficient, or that this project meets a university rubric. Dynamic provider/library documentation is access-dated; implementation records exact selected versions/configurations.

## Initial competitor evidence

These are publicly documented capabilities, not app testing or a claim that competitors lack unlisted features. Checked 2026-10-12; account/tier/region differences and actual user workflow remain to investigate.

| Product / official source | Capability described by publisher | Comparison task / limit |
|---|---|---|
| [Google Maps: save places](https://support.google.com/maps/answer/3184808?hl=en) | Saving and finding places using an account | Discover/save/select on map; source does not establish the whole planning/audio/RAG workflow |
| [Wanderlog: plan a trip](https://wanderlog.com/plan-a-trip) | Trip itinerary organization with a map | Enter/edit itinerary and view mapped stops; performance/usability not measured here |
| [VoiceMap: choosing locations](https://docs.voicemap.me/tour-publishers/choosing-locations/) | Publisher trigger zones associate GPS entry with audio playback | Compare arrival/playback and permission behavior; do not infer our app needs background tracking or its exact thresholds |

Next comparison uses the same scenario, dated screenshots/notes, device/account/tier and criteria: edit control, source visibility, unknown facts, route uncertainty, permission/manual fallback and audio. Mark unobserved capabilities unknown. The proposed contribution is an evaluated integration for a bounded reviewed Da Nang corpus; novelty/superiority is not claimed from this table.

## Evaluation design and validity

[Test Plan](08-Test-Plan.md) owns held-out questions, planning scenarios, GPS/audio field procedure and UAT/SUS scoring. Freeze reporting set before tuning, record corpus/model/prompt/config and separate fixture from live-provider trials. Compare AI-assisted planning with a deterministic candidate/constraint baseline using identical input facts; measure validity/feasibility/latency, not unproved optimality. Optional QA ablation can compare retrieval-grounded versus nonretrieval generation offline under identical model settings; record evidence availability and false refusal so comparisons are not confounded by unsupported-answer volume. This experimental baseline is not a public product fallback.
Threats to validity: small/convenience sample, selected POIs/devices, annotator judgement, model variability, changing sources and provider coverage. Use an independent claim reviewer where feasible, document disagreements, repeat selected questions and disclose selection bias. Do not calculate population claims from five users or fill missing outcomes with model estimates.

## Consent and evidence handling

Before recruitment agree purpose, voluntary participation/withdrawal, optional recording, anonymised publication, data access, storage owner and retention/deletion deadline. Use participant codes; contact details and identifiable raw recordings stay outside the repository. Participant research consent, narrator publication rights and image/text rights are separate permissions. The actual policy and institutional ethics requirements remain O-06/O-08.

## Academic requirements: verified applicability boundary

The repository does not contain an official approved proposal/rubric/COMP1682 report template. [Greenwich's public COMP1682 module specification](https://www.gre.ac.uk/modules/modules?crse=1682&subj=COMP&term=205000&title=Module+information+for+Computer+Science+%28Games%29%2C+BSc+Hons+%5BYear+3%5D) describes research, requirements, design/development, testing/UAT and critical reflection. It does not confirm the earlier claimed five-interview/20-survey quota. The consulted page is published under a Games programme; applicability to this student's course is not established.
[University of Liverpool COMP591 report guidance, 2022–23](https://www.csc.liv.ac.uk/~comp591/2022-23/COMP591FinalReportndividualReports.pdf) supports putting important design in the main discussion and detailed design/test evidence in appendices. It concerns a different programme/module and is organizational guidance only. Neither source replaces the student's supervisor/rubric.

## Report structure and evidence mapping

| Report area | Design input | Evidence needed for final submission |
|---|---|---|
| Context, aim, objectives | BRD and working objectives | Approved objective wording and discovery findings |
| Literature/related systems | Sources and initial capability table above | Critical synthesis, domain studies, dated task observations |
| Methodology/ethics | Research/Plan/Security | Chosen method rationale, actual consent/research records |
| Requirements/design | PRD/stories/use cases/SAD/Blueprint/UI/DB/API | Review history, alternatives and traceable decisions |
| Implementation | Planned task outputs | Actual code commits/configurations and native artifacts |
| Evaluation | Test Plan/Traceability | Actual tests, field/UAT/AI metrics, failures and retests |
| Discussion/conclusion | Objectives and measured evidence | Met/partial/unmet per objective, validity limits/future work |
| Appendices | OpenAPI/DDL/detailed cases/drawio/review | Supporting technical detail permitted by the official template |

Use the institutional format, length and referencing style when supplied. Record each reference's bibliographic metadata, accessed version, exact claim and relevance; do not cite unread secondary summaries as original experiments. Demonstration follows the P0 journey with real recorded audio, live AI plus honest failure states, and visible GPS/route simulation labels when fixtures are used.
