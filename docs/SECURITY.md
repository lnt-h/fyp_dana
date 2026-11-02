# Security and privacy contract

| Boundary | Required control and evidence |
|---|---|
| Identity | Clerk manages credentials and sessions. Verify signature, issuer, expiry and configured audience/authorized parties server-side. Derive the owner from verified identity. Test invalid, expired and foreign credentials. |
| Private resources | Check owner plus parent membership before data retrieval, agent invocation or provider spend. Test foreign trip, session, preview, lock and stop IDs. Parameterize queries and validate DTO ranges. |
| AI, routing and external links | Treat prompts and retrieved passages as untrusted data. Allowlist published IDs, sources and typed read tools. Use fixed external map targets and verified coordinates. Provider failure leaves accepted state intact. |
| Abuse and concurrency | Bound payloads, per-owner and service quotas, deadlines, retries and repair cost. Verify idempotency, revision checks and quota enforcement across deployed instances before pilot. |
| Credentials and infrastructure | SecureStore for client tokens, restricted mobile Maps key, server-only Clerk secret, Gemini, Routes and DB credentials in Secret Manager. Scope IAM, use TLS, isolate DB access and audit release/migration principals. |
| Logs and consent | Record request IDs, timings, version and outcome. Redact tokens, prompts, questions, transcripts and precise locations from logs, traces and crash reports. Request only permissions required by released features. |

## Deletion and recovery

Trips, drafts, previews, saved places, preferences and Guide history are private. Provide session/trip deletion and reauthenticated, confirmed account deletion. Revoke Clerk sessions, purge owner records including idempotency entries and clear private device state. Coordinate identity and database deletion with a retryable workflow. Report pending or failed cleanup accurately. Other devices clear local state on session revocation.

Define and disclose retention periods for chats, minimal abuse logs and backup expiry before the pilot. Reapply deletions after restore. Separate research consent, withdrawal and retention from product account deletion. Verify data-use declarations against actual network traffic, SDKs and device permissions before distribution. Rotate exposed credentials and block release on cross-owner leakage.
