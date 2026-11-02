# Security and privacy contract

| Boundary | Required control and evidence |
|---|---|
| Identity | Clerk manages credentials and sessions. The API verifies RS256 signature, issuer, expiry/not-before, subject and configured audience/authorized party, then maps the subject to a unique internal account UUID. Test valid, invalid, expired and foreign credentials. |
| Private resources | Check owner plus parent membership before data retrieval, agent invocation or provider spend. Test foreign trip, session, preview, lock and stop IDs. Parameterize queries and validate DTO ranges. |
| AI, routing and external links | Treat prompts and retrieved passages as untrusted data. Allowlist published IDs, sources and typed read tools. Use fixed external map targets and verified coordinates. Provider failure leaves accepted state intact. |
| Data supply and licensing | Route all external data through named provider adapters and an active persistence policy. Preserve source/license/attribution and deny unknown fields by default. Never use scraping or logs as a shadow provider cache. Restrict curator/import/publish operations and retain an audit trail. |
| Abuse and concurrency | Bound payloads, per-owner and service quotas, deadlines, retries and repair cost. Verify idempotency, revision checks and quota enforcement across deployed instances before pilot. |
| Credentials and infrastructure | SecureStore for client tokens, restricted mobile Maps key, server-only Clerk secret, Gemini, Routes, local-map/provider and DB credentials in Secret Manager. Scope keys by API, environment, IP/application where supported; apply quota/budget alerts. Scope IAM, use TLS, isolate DB access and audit release/migration principals. |
| Logs and consent | Record request IDs, timings, version and outcome. Redact tokens, prompts, questions, transcripts and precise locations from logs, traces and crash reports. Request only permissions required by released features. |

## Deletion and recovery

Trips, drafts, previews, saved places, preferences and Guide history are private. Provide session/trip deletion and reauthenticated, confirmed account deletion. Revoke Clerk sessions, purge owner records including idempotency entries and clear private device state. Coordinate identity and database deletion with a retryable workflow. Report pending or failed cleanup accurately. Other devices clear local state on session revocation.

Define and disclose retention periods for chats, minimal abuse logs and backup expiry before the pilot. Reapply deletions after restore. Separate research consent, withdrawal and retention from product account deletion. Verify data-use declarations against actual network traffic, SDKs and device permissions before distribution. Rotate exposed credentials and block release on cross-owner leakage.

External provider payloads may contain personal or user-generated content. Request only fields required for the released capability, do not log raw bodies, and do not pass reviews/photos/user identifiers to Gemini unless an approved purpose, terms and privacy assessment explicitly allow it. A provider contract or policy change can disable the affected adapter without requiring deletion of Gonarra-owned catalog facts; disputed or no-longer-licensed provider content is quarantined and removed according to its policy record.
