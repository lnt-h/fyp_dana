# Security, privacy and threat assessment

Version 1.3 | 2026-10-19 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Assets and trust boundaries

Private accounts/session secrets, trip preferences/start point, saved places, device-only Ask history, cached trip content and optional transient P1 camera/microphone media; published POI facts/images/audio; provider keys and cloud credentials. Phone and external map apps are separate trust boundaries; the API establishes ownership. Curator is privileged but ingestion is restricted CLI. Provider passages/model outputs are untrusted data. Public media must be intentionally published; offline audio needs an explicit right separate from streaming/publication; private P1 uploads never share public permissions.

## Threat-control matrix

| Threat | Control | Evidence / gate |
|---|---|---|
| Cross-user nested ID access | JWT subject + ownership + parent membership on every private path/Ask context | TC-25 before core release |
| Anonymous AI abuse or private writes | Guest access only to Explore/Detail/audio preview; server authentication and owner/IP quotas for Generate, Save and Ask | TC-43; distributed limiter selected before external pilot |
| Session takeover | Salted adaptive password hash; hashed rotating refresh tokens and session-state checks; TLS; secure device token storage; bounded login quota | TC-24; hash parameters/library TBD after spike |
| SQL/payload injection | Parameterized repository queries; DTO allowlists; UUID/size/range validation | API negative cases and query review |
| Prompt injection/false sources | No model tools with mutation; server context/citation allowlists; refusal; claim review | TC-19..21; held-out adversarial set |
| Quota exhaustion | Owner/IP auth and AI quotas; total deadline; request/image/audio limits | TC-22; measured quota configuration before deployment |
| GPS spoof/replay | Manual arrival is primary; fresh foreground-only plausibility checks, unique stop event, current-stop state; disclose client GPS cannot prove presence | TC-14..16, TC-30, TC-39, TC-44 |
| Malicious upload P1 | Private scoped upload, MIME signature/size check, random key, expiry cleanup, no automatic public publication | TC-31/32; P1 gate |
| Media rights/fact errors | Reviewed source/licence/narrator permission; per-record publication gate | TC-01; content audit |
| Secret leakage | Server-only provider credentials; environment secret storage; log redaction; restricted client Maps key | configuration review; no credentials in docs |
| Cloud/database exposure | Private DB; restricted security groups; TLS ingress; scoped IAM; controlled migration principal | release review; restore rehearsal |
| Lost backup/media mismatch | DB backup plus versioned media manifest; tested restore | TASK-24; report actual RPO/RTO |
| Account-deletion misuse or incomplete purge | Password re-authentication, explicit confirmation, transaction/cascade, session revocation and retention disclosure | TC-38; deletion matrix review |
| Stale or tampered local cache | Revision-bound manifest, integrity/size checks, read-only use, no secrets in cache and explicit partial state | TC-40, TC-44 |
| External map deep-link manipulation | Build destination from reviewed coordinates only; fixed HTTPS allowlist; never accept model/user URL | TC-39; mobile review |
| Old incompatible client | Minimum-app/API version headers and typed 426 update gate | TC-45; release checklist |

## Session design

JWT verifies issuer/audience/signature/expiry and carries subject/session identifier. Every protected request checks session ownership, expiry and revocation in PostgreSQL; logout invalidates the selected session even if its JWT has not reached expiry. Proposed lifetimes and password bounds are centralized in [Decisions](09-Project-Decisions.md); hash algorithm/parameters remain trial-dependent. Rotate the stored refresh hash atomically using the old hash as a condition; concurrent refresh replay cannot mint two valid replacements. Never store plaintext refresh tokens. Login/refresh errors do not reveal account details. Logout is idempotent and does not disclose whether a well-formed token was known.
P1 Google identity/account linking requires a separate reviewed contract; verified email alone never proves linking ownership. No mandatory password recovery/email verification workflow is committed in P0; document that pilot limitation rather than implying such controls exist.

Generate, Save, Ask and all private trip actions are authenticated on both client and server. A client-side sign-in sheet is usability, not authorization. Ask is single-turn at the API: the server stores no conversation/message table. If the mobile client offers recent Ask history, it is device-only, clearable and excluded from backup where the selected platform permits; this behavior must be described in the privacy notice.

## Data minimisation and lifecycle

GPS is computed locally; arrival persists only minimal method/time/accuracy/distance evidence. Do not persist continuous history and do not describe external-map time as background tracking. Default logs omit raw GPS, start-point coordinates, images, question text, planner free text and tokens; record request ID/latency/status/model/corpus revision. P1 media expires after processing; exact cleanup/retention targets TBD before enabling uploads. Public images/audio need rights/attribution records. Store source revision and review date; do not confuse access date with factual correctness. The essentials cache contains only reviewed trip text/transcripts and rights-approved audio; it excludes credentials, raw GPS history, offline map tiles and route-provider responses, and is invalidated by trip/content revision.

## Account deletion and retention matrix

P0 uses `POST /account/delete` because the action requires a password-confirmation body. Re-authentication, confirmation and deletion occur as one controlled workflow; sessions are revoked and owner rows (trips, days, stops, legs, proposals, arrivals, saves and idempotency records) are removed through documented cascades. A partial failure returns an error and does not claim success. The app clears local session, device-only Ask history and cached private trip state after acknowledgement.

| Data class | On successful deletion | Retention boundary |
|---|---|---|
| Account, sessions and owner product rows | Hard-delete/cascade in the primary database | Immediate transaction on success |
| Device-only history/cache | Clear from the current device after acknowledgement | Other devices clear when their revoked session is observed; disclose this limitation |
| Security/abuse logs | Remove direct content and identifiers where feasible; retain the minimum approved pseudonymous record | Exact period TBD before pilot; must be stated in notice |
| Backups | Not edited in place; deleted data ages out under backup expiry and is not restored into live service without reapplying deletion controls | Exact expiry/RPO/RTO TBD before deployment |
| Research/UAT records | Governed by the separate consent/withdrawal schedule, not by the product account alone | Agreed before recruitment |

The matrix is a design contract, not proof that deletion has run. TC-38 supplies implementation evidence.

## Policy register

Owner: developer/product owner; reviewer identity TBD. Before recruitment: consent/storage/withdrawal policy and an English-speaking international-visitor sampling plan. Before external pilot: account deletion handling, device-only history/cache behavior, session policy, media retention, backup expiry, external map/provider data settings and privacy notice. Before store/internal distribution: platform data-safety/privacy declarations, crash-reporting redaction, minimum-version policy and account-deletion UI/endpoint verification; a public Google Play release additionally needs the external deletion-request web resource referenced by its policy. Before deployment: distributed quotas/budget/cloud IAM review. Regulatory applicability requires qualified assessment; this document is a technical proposal, not legal advice or compliance certification.

## Incident and review

If secrets leak, stop affected integration, revoke/rotate authorised credentials, assess exposure, preserve redacted evidence and add regression controls. If cross-user leak/unsupported facts found, block release until fixed and verified. Reviewer records decision and exact artifact version. High-risk implementation changes require qualified independent review according to repository SOP.

## Residual risk and review boundaries

GPS is client evidence and can be spoofed. RAG reference checks cannot guarantee historical claim entailment. An in-process limiter resets on restart and is not a distributed abuse control; it is insufficient for an external Ask/Generate pilot. Public media publication must be deliberate; source URLs and external map URLs are not fetched from user/model input. API outputs permit only stored reviewed links; any future server URL-fetching feature needs SSRF defenses and a separate review. Deletion cannot promise immediate removal from expired-device storage, security logs or backups beyond the approved policy. These limitations are reviewed with TC-14/21/22/25/38–45 and held-out evaluation.
Participant consent and storage policies are research-method requirements, not a declaration of legal compliance. Applicable law/institutional ethics decisions require actual project context; they are not inferred from a generic checklist.
