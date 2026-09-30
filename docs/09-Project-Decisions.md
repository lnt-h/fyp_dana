# Danang TourGuide — Project Decisions and Document Index

Version 1.0 | 2026-09-30. User approved the review and recommendations. Approval covers redesign of documentation; no implementation, deployment or measured evaluation is claimed.

## Document ownership and reading order
| File | Owns |
|---|---|
| [01-PRD.md](01-PRD.md) | Scope, stable FR/BR/NFR and acceptance |
| [02-SAD.md](02-SAD.md) | Architecture/modules/runtime/deployment |
| [03-Use-Cases.md](03-Use-Cases.md) | Actors, flows, alternatives |
| [04-Sequence-Diagrams.md](04-Sequence-Diagrams.md) | Runtime interactions |
| [05-Database-Design.md](05-Database-Design.md) | Domain, relational/geographic/vector data |
| [06-API-Design.md](06-API-Design.md) | Endpoint/schema/error/state contracts |
| [07-UI-UX-Design.md](07-UI-UX-Design.md) | Navigation/screens/mobile states |
| [08-Test-Plan.md](08-Test-Plan.md) | Test coverage, evaluation and evidence |
| [09-Project-Decisions.md](09-Project-Decisions.md) | Decision status, rationale, open items |

Resolve contradiction in owning document then update dependants; diagram is not a separate source of truth. Standards-inspired structure is not formal IEEE/UML certification.

## Accepted decisions
| ID | Decision | Rationale / verification |
|---|---|---|
| D-01 | Explore-first curated travel companion | Core flow walkthrough replaces photo onboarding |
| D-02 | One Expo app + NestJS modular monolith | Single developer; one API deployable; module review |
| D-03 | PostgreSQL/PostGIS/pgvector, no initial Redis | Shared relational/geographic/text retrieval data; migration spike |
| D-04 | Human-recorded audio only, S3 media | Reviewed narrative and predictable experience; asset metadata/playback tests |
| D-05 | Opt-in auto-play at Start Trip | GPS-triggered playback under user control; default off and duplicate tests |
| D-06 | Foreground GPS, manual fallback | Explainable implementable V1; device field trials |
| D-07 | AI itinerary proposal, backend validation, explicit acceptance | IDs/facts/routes not model authority; invalid-output tests |
| D-08 | Contextual source-grounded RAG | Facts and source-backed passages; claim evaluation and refusal tests |
| D-09 | Text embeddings only initially | No V1 visual recommendation; separate Vision P1 |
| D-10 | 30–50 POIs, 10–15 audio flagship POIs | Curation feasible; corpus QA checklist |
| D-11 | Email/password private persistence; Google OAuth P1 | Basic ownership independent of optional integration |
| D-12 | Vietnamese P0; English when content ready | Audio/content workload controlled; no empty-language promises |
| D-13 | AWS ECS/Fargate, RDS, S3, Secrets, CloudWatch, CI target | Deployability evidence; extensions/cost/network spike first |
| D-14 | P1 only after core slice | Camera, STT, Google OAuth cannot block core completion |
| D-15 | No TTS/voice agent/microservices/weather/booking/social | Scope freeze; no orphan endpoints/dependencies |

Future backlog: Visual Taste, Travel DNA, CLIP/image recommendations, Six Degrees, weather, notifications, collections and offline mode. Do not create their V1 tables/jobs/screens pre-emptively.

## Unresolved decisions (not inferred as facts)
| ID | Topic | Next action |
|---|---|---|
| O-01 | Actual deadline, weekly capacity and milestones | User supplies dates; create dated sprint plan; eight-month assumption retired |
| O-02 | AWS/API monthly budget and region | User budget; compare measured consumption/configuration before deployment |
| O-03 | GPT/Gemini primary model and embedding model/dimension | Technical spike with account access, Vietnamese answers, JSON validity, latency/cost |
| O-04 | Maximum itinerary days and supported transport modes | Start one-day development slice; choose final limits using available time and Routes support |
| O-05 | Audio production and English coverage | Confirm narrators/permissions, flagship POIs and reviewed scripts |
| O-06 | Academic aim/objectives already submitted | Compare actual approved proposal; preserve change history and discuss required institutional approval |
| O-07 | ORM, Expo native build compatibility, RDS extensions | Choose after small migration/GPS/maps/audio integration spike |
| O-08 | Data freshness, retention and account deletion policy | Set review/expiry/cleanup rules and backup expiry; do not claim legal compliance without review |
| O-09 | Arrival radius/accuracy/dwell per POI | Tune in field tests; entrances may differ from attraction centroid |
| O-10 | Optional STT implementation/provider | Select only if P1 time remains; no full voice architecture |

## Legacy consolidation and requirement migration
| Legacy file | Treatment in this baseline |
|---|---|
| 01 PRD | Modified; new scope and measurable acceptance |
| 02 SAD | Modified; canonical architecture |
| 03 Blueprint | Useful boundaries/states/rationale merged into SAD |
| 04 Use Cases | Renumbered 03; replaced old taste/discovery chain |
| 05 Activity | Useful trip/arrival flows merged into Use Cases/SAD |
| 06 Sequence | Renumbered 04; planning/edit/arrival/RAG replaced |
| 07 Class | Domain/cardinality merged into Database Design |
| 08 Component | Module boundaries merged into SAD |
| 09 Deployment | AWS/local deployment merged into SAD |
| 10 API | Renumbered 06; removed old endpoints; explicit proposals/audio |
| 11 SQL + 12 Vector | Merged into 05; source/audio/route/version design |
| 13 UI | Renumbered 07; Explore-first states |
| 14 Test | Renumbered 08; new RTM and actual-evidence policy |
| ASSUMPTIONS | Replaced by accepted/pending decisions here |
| README | Index merged here; no separate README needed |
| COMP1682 report template | Preserved unchanged outside these nine design docs |

Legacy FR-PREF-01..03 photo/DNA requirements are retired; new FR-PREF-01 simple input is a deliberate revised contract recorded here. FR-AUTH-02 now Google P1; legacy guest flow retired. FR-REC-* and FR-WX-* moved Future; FR-SAV-02 collections Future. FR-TRV-03 keeps audio purpose but implementation changes TTS→human media. FR-CAM-01 moves P2→P1; FR-STT-01 and FR-MAP-01 added. Never combine legacy test results with this revised baseline without rerunning revised cases.
Original uploaded documents remain untouched as historical inputs; this reorganised deliverable is a separate consolidated edition. The old product spec/prompt repository was not included in attachments; no unsupported claim of having reviewed those sources.

## Development order without invented dates
1. Spike maps/GPS/audio/DB extensions and model structured output/text embeddings.
2. Curate five complete POIs and 2–3 human recordings; deliver Explore → plan/edit/map → arrival/audio → RAG in-app.
3. Harden ownership, errors, source validation and route edits; expand to final corpus.
4. Evaluate held-out AI questions, planning scenarios and GPS field behaviour.
5. Add P1 only if core acceptance/evaluation capacity remains.
6. UAT/fixes, AWS deployment within budget, demo rehearsal and final report evidence.

## Academic report mapping
PRD/Use Cases/UI → Chapter 4 requirements/design; SAD/DB/Sequences → architecture/data; Decisions → Chapter 5 rationale/risks with actual dated plan later; actual code/deploy evidence → Chapter 6; Test Plan and results → Chapter 7; real objective evaluation → Chapter 8.
Remaining report evidence: literature review, 3–5 competitor study, ethical consent/user research, annotated Rich Picture and genuine UML use-case diagram, rendered wireframes, dated Gantt/backlog/retrospectives, test execution ledger, SUS and references. This baseline does not fabricate these. Template examples about UniConnect/Firebase are examples, not Danang TourGuide requirements.
