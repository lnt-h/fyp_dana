# Danang TourGuide — Decisions and open inputs

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Decision categories

Selected scope records the user's product choice. Working design records the approach specified by this documentation and its rationale, pending technical review. Trial-dependent values are explicitly proposed and become fixed only after documented evidence. Academic approval is separate and has not been supplied.

## Decision register

| ID | Decision | Status | Rationale / alternative / consequence |
|---|---|---|---|
| D-01 | Explore → editable AI plan → foreground arrival/audio/RAG | Selected scope | Continuous core journey; photo personalization is Future |
| D-02 | Expo/React Native + NestJS modular monolith | Working design | One developer, one API deployable; verify native integrations before version pinning |
| D-03 | PostgreSQL + PostGIS + pgvector; no initial Redis | Working design | Relational state, geography and retrieval in one consistency boundary; benchmark before extra stores |
| D-04 | Reviewed human narration; versioned object storage | Working design | Explicit factual/media review; TTS excluded |
| D-05 | Auto-play default off, opt-in per travel session | Working design | User controls playback; no microphone permission for listening |
| D-06 | Foreground GPS with manual fallback | Selected scope | Field-testable scope; background tracking excluded |
| D-07 | Validated preview then explicit acceptance | Working design | Model output cannot silently overwrite an accepted itinerary |
| D-08 | Reviewed-source RAG plus structured operational facts | Working design | Evidence/provenance required; semantic correctness still evaluated manually |
| D-09 | Text-only embeddings; exact filtered search initially | Working design | Small corpus; image embeddings/ANN deferred |
| D-10 | Final corpus 30–50 POIs and 10–15 audio guides | Proposed target | Supports category/field/evaluation coverage; confirm production effort through five-POI slice |
| D-11 | Email/password sessions and owner-scoped persistence | Working design | Private trips/saves; Google optional |
| D-12 | Vietnamese P0; English only when reviewed content exists | Working design | No invented translation coverage; fallback identified explicitly |
| D-13 | AWS physical deployment option | Conditional design | Budget, extension support and networking trial required; cloud release not required for drafting docs |
| D-14 | Camera/STT/Google only after P0 gate | Optional backlog | Not included in mandatory delivery, P0 OpenAPI or P0 pass denominator |
| D-15 | Exclude TTS/voice agent/microservices/booking/social/weather | Scope boundary | Keeps one coherent core; changes require requirement and impact review |
| D-16 | Keep existing docs filenames; consolidate task/risk/evidence sections | Selected organization | User requested direct overwrite; documented exception to SOP phase-folder layout |
| D-17 | Versioned REST contract under /api/v1 | Working design | OpenAPI owns field shapes; API design owns semantic rules |
| D-18 | Revision checks, durable idempotency, short transactions | Working design | Protects user edits and retry safety; no external calls inside trip transactions |
| D-19 | Explicit start-to-first-stop leg per day | Working design | Travel from start must count in schedule; no assumed hotel or overnight position |
| D-20 | Versioned immutable embedding-space identity | Working design | Never mix model/dimension/task; re-embed into new space before switch |
| D-21 | HTML wireframes plus editable draw.io sources | Working design | Reviewable docs artifacts; native behavior must be evaluated later |
| D-22 | JWT session identifier checked against session state | Working design | Logout invalidates the selected session for protected requests; avoid false immediate-revocation claims from token expiry alone |

## Proposed configuration register

Values below are design proposals, not measured performance or external requirements. Record the selected value and trial evidence before its dependent implementation is baselined.
| Key | Proposed value / unresolved value | Verification / owner |
|---|---|---|
| Pagination | default 20, maximum 50 | API/UI trial; developer |
| Build total deadline | 60 seconds including retries | Provider latency/cost trial; developer |
| Ask total deadline | 30 seconds including embedding/retries | Retrieval/generation trial; developer |
| Retry / repair | At most one transient retry or schema repair within remaining deadline; no retry for invalid ownership/input | Failure tests; developer |
| Proposal expiry | 30 minutes from creation | UX/version-conflict tests; developer |
| Idempotency retention | 24 hours; do not expire a live in-progress operation | Replay/recovery tests; developer |
| Session policy | Access 15 minutes; refresh session absolute lifetime 7 days; rotate refresh hash atomically | Security trial; developer/reviewer |
| Password policy | 12–128 characters, no truncation; adaptive hash parameters TBD | Library/performance/security review |
| Planner limits | One-day/walking feasibility slice; final maximum days/stops/modes and duration bounds TBD | Routes/device/cost trial; O-04 |
| Arrival parameters | Radius, maximum accuracy, dwell and allowed report age TBD; per-POI entrance overrides reviewed | Real field trials; O-09 |
| Retrieval | Trial chunks 300–500 tokens; overlap, K, score threshold and dimension TBD | Separate tuning set; O-03 |
| Freshness | Route maximum age and operational-fact expiry by type TBD | Provider terms and curation review; O-08 |
| Quotas / sizes | Auth/AI/IP quotas, body/media size, maximum pending requests TBD | Abuse/failure tests; O-11 |
| Research sampling | Five discovery interviews proposed; optional survey only if it answers a defined question; ≥5 independent UAT participants proposed | Supervisor method review; O-06 |
| Evaluation | 40–60 held-out RAG questions; ≥20 planning scenarios proposed | Coverage-driven test design; Test Plan |

## Open inputs and blocking gates

| ID | Topic | Owner | Required before |
|---|---|---|---|
| O-01 | Deadline, weekly capacity, review/defense dates | Student | Dated schedule commitment |
| O-02 | Budget, cloud region, provider consumption ceiling | Student/developer | Paid integrations or deployment |
| O-03 | LLM, embedding model/dimension/task, retrieval settings | Developer | Embedding/model integration baseline |
| O-04 | Day/mode/stop/time bounds and start-leg policy verification | Developer/product owner | Planner configuration baseline |
| O-05 | Narrator permission, image/source rights and language coverage | Curator | Content publication |
| O-06 | Approved proposal, objectives, rubric, research sampling | Student/supervisor | Academic baseline and participant recruitment |
| O-07 | ORM, DB extension/engine and Expo native version compatibility | Developer | Versioned migrations/native integration |
| O-08 | Fact/route freshness, consent, retention, deletion/export, backups | Student/developer/reviewer | Research collection or external pilot, as applicable |
| O-09 | Field arrival thresholds, report age and entrance coordinates | Developer | GPS acceptance configuration |
| O-10 | Optional STT/vision/upload lifecycle | Developer | P1 activation only |
| O-11 | Password parameters, session/quota/request-size policies | Developer/reviewer | Authentication/AI external pilot |
| O-12 | Deployment resources/networking, recovery objectives | Student/developer | Release readiness |

## Change and review record

2026-10-12, v1.2: retain selected P0; clarify optional backlog; fix unsupported academic sample-size attribution; separate source findings from project proposals; specify state/replay/freshness behavior; consolidate repeated administration. No implementation, approval, research participant response or runtime result is recorded by this change.
For a later decision record date, owner/reviewer, exact artifact version, evidence, alternative considered, decision and affected IDs. A pending item is not silently treated as resolved. Review identities and academic confirmation remain open.
