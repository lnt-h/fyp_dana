# Security, privacy and threat assessment

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Assets and trust boundaries

Private accounts/session secrets, trip preferences/start point, saved places, optional transient camera/microphone media; published POI facts/images/audio; provider keys and cloud credentials. Phone is untrusted; API establishes ownership. Curator is privileged but ingestion is restricted CLI. Provider passages/model outputs are untrusted data. Public media must be intentionally published; private P1 uploads never share public permissions.

## Threat-control matrix

| Threat | Control | Evidence / gate |
|---|---|---|
| Cross-user nested ID access | JWT subject + ownership + parent membership on every private path/Ask context | TC-25 before core release |
| Session takeover | Salted adaptive password hash; hashed rotating refresh tokens and session-state checks; TLS; secure device token storage; bounded login quota | TC-24; hash parameters/library TBD after spike |
| SQL/payload injection | Parameterized repository queries; DTO allowlists; UUID/size/range validation | API negative cases and query review |
| Prompt injection/false sources | No model tools with mutation; server context/citation allowlists; refusal; claim review | TC-19..21; held-out adversarial set |
| Quota exhaustion | Owner/IP auth and AI quotas; total deadline; request/image/audio limits | TC-22; measured quota configuration before deployment |
| GPS spoof/replay | Plausibility checks, unique stop event, current-stop state; disclose client GPS cannot prove presence | TC-14..16, TC-30 |
| Malicious upload P1 | Private scoped upload, MIME signature/size check, random key, expiry cleanup, no automatic public publication | TC-31/32; P1 gate |
| Media rights/fact errors | Reviewed source/licence/narrator permission; per-record publication gate | TC-01; content audit |
| Secret leakage | Server-only provider credentials; environment secret storage; log redaction; restricted client Maps key | configuration review; no credentials in docs |
| Cloud/database exposure | Private DB; restricted security groups; TLS ingress; scoped IAM; controlled migration principal | release review; restore rehearsal |
| Lost backup/media mismatch | DB backup plus versioned media manifest; tested restore | TASK-24; report actual RPO/RTO |

## Session design

JWT verifies issuer/audience/signature/expiry and carries subject/session identifier. Every protected request checks session ownership, expiry and revocation in PostgreSQL; logout invalidates the selected session even if its JWT has not reached expiry. Proposed lifetimes and password bounds are centralized in [Decisions](09-Project-Decisions.md); hash algorithm/parameters remain trial-dependent. Rotate the stored refresh hash atomically using the old hash as a condition; concurrent refresh replay cannot mint two valid replacements. Never store plaintext refresh tokens. Login/refresh errors do not reveal account details. Logout is idempotent and does not disclose whether a well-formed token was known.
P1 Google identity/account linking requires a separate reviewed contract; verified email alone never proves linking ownership. No mandatory password recovery/email verification workflow is committed in P0; document that pilot limitation rather than implying such controls exist.

## Data minimisation and lifecycle

GPS computed locally; arrival persists only minimal method/time/accuracy/distance evidence. Do not persist continuous history. Default logs omit raw GPS/images/question text and tokens; record request ID/latency/status/model/corpus revision. P1 media expires after processing; exact cleanup/retention targets TBD before enabling uploads. Public images/audio need rights/attribution records. Store source revision and review date; do not confuse access date with factual correctness.

## Policy register

Owner: developer/product owner; reviewer identity TBD. Before recruitment: consent/storage/withdrawal policy. Before external pilot: account deletion/export handling, session policy, media retention, backup expiry, provider data settings and privacy notice. Before deployment: quotas/budget/cloud IAM review. Regulatory applicability requires qualified assessment; this document is a technical proposal, not legal advice or compliance certification.

## Incident and review

If secrets leak, stop affected integration, revoke/rotate authorised credentials, assess exposure, preserve redacted evidence and add regression controls. If cross-user leak/unsupported facts found, block release until fixed and verified. Reviewer records decision and exact artifact version. High-risk implementation changes require qualified independent review according to repository SOP.

## Residual risk and review boundaries

GPS is client evidence and can be spoofed. RAG reference checks cannot guarantee historical claim entailment. An in-process limiter resets on restart and is not a distributed abuse control. Public media publication must be deliberate; source URLs are not fetched from user/model input. API outputs permit only stored reviewed links; any future server URL-fetching feature needs SSRF defenses and a separate review. These limitations are reviewed with TC-14/21/22/25 and held-out evaluation.
Participant consent and storage policies are research-method requirements, not a declaration of legal compliance. Applicable law/institutional ethics decisions require actual project context; they are not inferred from a generic checklist.
