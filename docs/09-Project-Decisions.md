# DaNavi — Decisions and open inputs

Version 1.3 | 2026-10-19 | Status: product scope selected; technical and academic review still required. Document control and evidence status: [Index](00-INDEX.md).

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
| D-10 | Final corpus 30–50 POIs and 10–15 audio guides | Superseded by D-29 | Retained for history; the v1.3 one-developer baseline uses a smaller reviewed corpus |
| D-11 | Email/password sessions and owner-scoped persistence | Working design | Private trips/saves; Google optional |
| D-12 | Vietnamese P0; English only when reviewed content exists | Superseded by D-23 | Retained for history; v1.3 changes the primary audience and reviewed content language |
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
| D-23 | English-first P0 for an international first-time visitor to Da Nang | Selected scope | App copy and reviewed P0 content are English. Search also matches reviewed Vietnamese names and romanized aliases. Keep the locale field with `en` as the default; no unreviewed machine-translated fallback. |
| D-24 | P0 itineraries are one day only (`dayCount=1`) | Selected scope | Makes scheduling, field testing and recovery feasible for one developer. Preserve multi-day-capable schema/configuration for later versions without exposing it in P0. |
| D-25 | Guest-first access with authentication only at protected intent | Selected scope | Guests may Explore, open Detail and hear an audio preview. Save, Ask and Generate require login. A guest may fill the planning form; Generate opens the login gate, preserves the form, returns to it after login and requires a second explicit Generate tap. Never generate automatically after authentication. |
| D-26 | Start point uses a required map pin, current-location shortcut or one of 3–4 curated presets | Selected scope | Avoids a P0 geocoding/autocomplete dependency. Persist coordinates and `source` as `map_pin`, `current_location` or `preset`; presets are reviewed content/configuration. |
| D-27 | P0 transport has one mode: car/ride-hailing | Selected scope | Walking-only is not credible across Da Nang distances. Keep a one-value transport enum for contract stability. Add motorbike only after a Routes provider/device trial confirms support. |
| D-28 | External directions handoff plus explicit return reconciliation | Selected scope | Open Google Maps or Apple Maps through HTTPS using a reviewed entrance coordinate. The in-app map is a route preview, not turn-by-turn navigation. “I've arrived” is the primary path; on foreground resume the app requests a fresh fix and may run the dwell helper for the current stop. No background GPS. |
| D-29 | P0 corpus is 15–20 reviewed POIs in Culture, Beach, Food and Nature, with five flagship human audio guides | Selected scope | Urban places use Culture plus tags. The larger 30-POI/10-audio corpus is a stretch goal. Planning evaluation must expose sparse-pool and no-audio cases rather than hide them. |
| D-30 | P0-lite trip essentials cache is read-only; full offline maps/routing are excluded | Selected scope | At Start Trip, prefetch the accepted stops' text, transcript and authorised audio. Invalidate on content/itinerary revision. Enforce a measured size limit and media rights. Offline completion/skip/arrival remain visibly pending until reconciliation; the user may retry or continue without claiming a complete download. |
| D-31 | Account deletion is P0 and uses reauthentication | Selected scope | `POST /account/delete` requires password confirmation, revokes sessions and hard-deletes owner data through documented cascades. O-08 must define lawful/operational retention for security logs and backups without implying immediate physical purge from backups. Public Google Play release also requires a discoverable external deletion-request web resource and accurate Data safety answers; that release artifact is not claimed to exist yet. |
| D-32 | Ask requires authentication, is server-side single-turn and stores history only on the client | Selected scope | Reduces anonymous abuse and cost. P0 displays answer-level source cards and explicit insufficient-evidence states; claim-level citation presentation is stretch, while claim support remains an evaluation measure. |
| D-33 | Accept the proposal before editing; preview CTA is “Save & customize” | Selected scope | Preserves the proposal/accepted-trip boundary and prevents edits to an unaccepted transient proposal. |
| D-34 | Password recovery is not included in P0 | Selected scope limitation | Account deletion is available to a signed-in user who can reauthenticate. A user who forgot the password cannot recover or delete through the P0 app; document this limitation and do not imply otherwise. |

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
| Planner limits | `dayCount=1`; one transport value `car`; maximum stops and visit/time-window bounds TBD | Routes/device/cost trial; O-04 |
| Arrival parameters | Radius, maximum accuracy, dwell and allowed report age TBD; per-POI entrance overrides reviewed | Real field trials; O-09 |
| Retrieval | Trial chunks 300–500 tokens; overlap, K, score threshold and dimension TBD | Separate tuning set; O-03 |
| Freshness | Route maximum age and operational-fact expiry by type TBD | Provider terms and curation review; O-08 |
| Quotas / sizes | Auth/AI/IP quotas, body/media size, trip-cache size and maximum pending requests TBD | Abuse/failure/cache tests; O-11 |
| Research sampling | Five discovery interviews proposed; optional survey only if it answers a defined question; ≥5 independent UAT participants proposed | Supervisor method review; O-06 |
| Evaluation | 40–60 held-out RAG questions; ≥20 planning scenarios proposed | Coverage-driven test design; Test Plan |

## Open inputs and blocking gates

| ID | Topic | Owner | Required before |
|---|---|---|---|
| O-01 | Deadline, weekly capacity, review/defense dates | Student | Dated schedule commitment |
| O-02 | Budget, cloud region, provider consumption ceiling | Student/developer | Paid integrations or deployment |
| O-03 | LLM, embedding model/dimension/task, retrieval settings | Developer | Embedding/model integration baseline |
| O-04 | Maximum stops, visit/time-window bounds, route provider support and start-leg policy verification | Developer/product owner | Planner configuration baseline |
| O-05 | English narrator permission, image/source/offline rights, and English translation review by a bilingual reviewer | Curator/reviewer | Content publication or caching |
| O-06 | Approved proposal, objectives, rubric, research sampling | Student/supervisor | Academic baseline and participant recruitment |
| O-07 | ORM, DB extension/engine and Expo native version compatibility | Developer | Versioned migrations/native integration |
| O-08 | Fact/route freshness, consent, security-log retention, account deletion, backup retention/purge and any export policy | Student/developer/reviewer | Research collection or external pilot, as applicable |
| O-09 | Field arrival thresholds, report age and entrance coordinates | Developer | GPS acceptance configuration |
| O-10 | Optional STT/vision/upload lifecycle | Developer | P1 activation only |
| O-11 | Password parameters, session/quota/request-size policies | Developer/reviewer | Authentication/AI external pilot |
| O-12 | Deployment resources/networking, recovery objectives | Student/developer | Release readiness |

## Change and review record

2026-10-19, v1.3: select English-first one-day mobile scope, guest authentication gates, explicit start input, car/ride-hailing mode, external directions handoff, reduced reviewed corpus, read-only trip cache, account deletion and single-turn authenticated Ask. D-10 and D-12 are superseded, not deleted. No implementation, approval, participant response or runtime result is recorded by this documentation change.

2026-10-12, v1.2: retain selected P0; clarify optional backlog; fix unsupported academic sample-size attribution; separate source findings from project proposals; specify state/replay/freshness behavior; consolidate repeated administration. No implementation, approval, research participant response or runtime result is recorded by this change.
For a later decision record date, owner/reviewer, exact artifact version, evidence, alternative considered, decision and affected IDs. A pending item is not silently treated as resolved. Review identities and academic confirmation remain open.
