# DaNavi — Research and Academic Evidence

Version 1.3 | 2026-10-19 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Aim and objectives: proposed, not institutionally approved

Proposed aim: design and evaluate an English-first, source-aware mobile Da Nang companion for first-time international visitors, integrating curated discovery, an editable one-day AI-assisted itinerary and foreground visit assistance. The actual approved proposal/rubric is unavailable; the following working objectives must be compared with it, not substituted silently.

| Objective | Planned evidence | Trace |
|---|---|---|
| OBJ-01 Understand traveler needs and define bounded requirements | Discovery themes, contradictory cases, reviewed requirements | BIZ-01–04; BRD/PRD |
| OBJ-02 Design traceable mobile/API/data architecture | Alternatives, 4+1 views, state/DTO/integrity rules | BIZ-05/06; SAD/Blueprint/DB/API/UI |
| OBJ-03 Deliver curated English-first discovery and editable validated one-day planning | Rights-reviewed 15–20-POI corpus, alias search, end-to-end plan/edit demonstration | FR-POI/EXP/PLC/MAP/PREF/TRP |
| OBJ-04 Provide map handoff, foreground/manual arrival, reviewed English audio, P0-lite cache and source-grounded Ask | Device/field/cache and held-out source-support evidence | FR-TRV-01–04, FR-OFF-01, FR-AI-01 |
| OBJ-05 Evaluate engineering and usability with explicit limitations | Ownership/concurrency/failure/performance/accessibility/UAT results | Six NFRs; Test Plan |

All implementation, participant and measured-outcome evidence is pending. Objective IDs here are working IDs; preserve the official wording/IDs when supplied and record changes/approval.

## Research questions and discovery method

RQ-01: How do first-time or low-familiarity international visitors choose Da Nang places, estimate one day and revise it? RQ-02: Which English facts, source cues and uncertainty states affect decisions? RQ-03: When are external-map handoff, manual arrival and recorded English audio useful/acceptable? RQ-04: Does the delivered core journey support unassisted mobile tasks and perceived usability? RQ-05: How often does source-grounded English Ask provide supported answers versus refuse appropriately?
Discovery: proposed five semi-structured interviews with English-speaking international visitors who are first-time or low-familiarity Da Nang travelers, with varied device/navigation habits. This is a feasible initial qualitative target, not a universal sample-size rule or proof of saturation. If recruitment requires a broader proxy sample, record the mismatch and do not call it target-user validation. Use a survey only for a stated research question and approved sampling approach; no mandatory 20-response quota is asserted. Supervisor confirms method before recruitment.
Interview sequence: consent → recent real trip/tools → place selection/time/changes → trusted facts → reveal proposed journey → audio/location/source inspection/failure preferences → contradictory or unwanted behavior. Avoid leading questions. Code anonymised observations into themes, distinguish observation from interpretation, retain negative cases and map justified requirement changes to BIZ/FR IDs.

## Reviewed research foundations

The academic sources below were checked on 2026-10-12. Summaries state what the source supports; implications are this project's design reasoning. Their access dates were not changed in v1.3 because they were not re-opened in this update. Literature review remains preliminary and must be expanded with domain-specific studies before the final academic report.

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

## Mobile product policy references checked for v1.3

The following official pages were opened and read on 2026-10-19. They support product/release constraints, not a claim that DaNavi already complies.

| Primary source | Supported point | DaNavi implication and limit |
|---|---|---|
| Apple, [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) | Guideline 5.1.1(v) says apps without significant account-based features should remain usable without login and apps with account creation must provide in-app deletion; the same page directs beta distribution to TestFlight | Explore, Detail and audio preview remain guest-accessible; account is requested at Generate, Save and Ask. Public iOS readiness still requires a real tested deletion flow and review materials |
| Apple, [Offering account deletion](https://developer.apple.com/help/app-review/guideline-reference/5-1-1-account-deletion) | Deletion initiation should be easy to find and transparent; full account/data deletion is expected, while reasonable confirmation/reauthentication is allowed | Put Delete Account in Profile & Settings, require current-password reauthentication without artificial friction, and disclose retained backups/logs |
| Google Play, [Account deletion requirements](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en) | Apps offering account creation need an in-app deletion path and a discoverable external web resource; associated data and retention disclosures are in scope | `POST /account/delete` and UI-20 cover the in-app path; an external deletion-request page/link and Data safety answers are a release gate, not represented as already available |

These policies can change. Recheck the live pages at submission time and obtain qualified advice for legal applicability; the documents are not a certification.

## Initial competitor evidence

These are publicly documented capabilities, not app testing or a claim that competitors lack unlisted features. Rows retain their actual access date; account/tier/region differences and real user workflow remain to investigate.

| Product / official source | Accessed | Capability described by publisher | Comparison task / limit |
|---|---|---|---|
| [Google Maps: save places](https://support.google.com/maps/answer/3184808?hl=en) | 2026-10-12 | Saving and finding places using an account | Discover/save/select on map; source does not establish the whole planning/audio/RAG workflow |
| [Wanderlog: plan a trip](https://wanderlog.com/plan-a-trip) | 2026-10-12 | Trip itinerary organization with a map | Enter/edit itinerary and view mapped stops; performance/usability not measured here |
| [VoiceMap: choosing locations](https://docs.voicemap.me/tour-publishers/choosing-locations/) | 2026-10-12 | Publisher trigger zones associate GPS entry with audio playback | Compare arrival/playback and permission behavior; do not infer DaNavi needs background tracking or VoiceMap's exact thresholds |
| Mindtrip, [About](https://mindtrip.ai/about) and [Traveler FAQs](https://resources.mindtrip.ai/travelers/help/traveler-faqs) | 2026-10-19 | Publisher describes conversational AI, personalized suggestions, editable/shareable itineraries, interactive maps, reviews, booking organization and on-trip recommendations | Shows AI itinerary + map integration is not unique. Compare the same one-day edit/source/unknown-fact scenario; do not infer claim-level citations or Da Nang coverage from marketing text |
| GuideAlong, [How it works](https://guidealong.com/how-it-works/) and [FAQ](https://guidealong.com/faq/) | 2026-10-19 | Publisher describes pre-downloaded offline tours and GPS-triggered audio commentary, mainly for self-paced routes | Confirms offline audio/GPS is an established pattern. DaNavi deliberately uses a smaller rights-aware essentials cache, no offline map/routing and manual arrival as the primary path; this is a scope difference, not a superiority claim |

Next comparison uses the same scenario, dated screenshots/notes, device/account/tier and criteria: guest entry, start-point input, edit control, source visibility, unknown facts, route uncertainty, permission/manual fallback, audio and weak connectivity. Mark unobserved capabilities unknown. The proposed contribution is an evaluated integration for a bounded reviewed Da Nang corpus; novelty/superiority is not claimed from this table. The working differentiation hypothesis is the combination of curated local English content, one-day editable planning, source-visible Ask and manual-first visit assistance; it remains a hypothesis until task-based comparison and user evidence exist.

## Evaluation design and validity

[Test Plan](08-Test-Plan.md) owns held-out questions, planning scenarios, GPS/audio field procedure and UAT/SUS scoring. Freeze reporting set before tuning, record corpus/model/prompt/config and separate fixture from live-provider trials. Compare AI-assisted planning with a deterministic candidate/constraint baseline using identical input facts; measure validity/feasibility/latency, not unproved optimality. Optional QA ablation can compare retrieval-grounded versus nonretrieval generation offline under identical model settings; record evidence availability and false refusal so comparisons are not confounded by unsupported-answer volume. This experimental baseline is not a public product fallback.
Threats to validity: small/convenience international sample, English proficiency differences, selected POIs/devices, annotator/translator judgement, model variability, small-corpus memorisation or duplicate leakage, changing sources and provider coverage. Use an independent claim/translation reviewer where feasible, document disagreements, repeat selected questions and disclose selection bias. Include distractor, cross-POI and adversarial questions. Do not calculate population claims from five users or fill missing outcomes with model estimates.

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

Use the institutional format, length and referencing style when supplied. Record each reference's bibliographic metadata, accessed version, exact claim and relevance; do not cite unread secondary summaries as original experiments. Demonstration follows the English P0 journey from guest Explore through login-gated Generate, **Save & customize**, route preview, external-map handoff, manual arrival, real recorded audio and source-visible Ask. It includes honest cache/provider/GPS failure states and visible simulation labels when fixtures are used.
