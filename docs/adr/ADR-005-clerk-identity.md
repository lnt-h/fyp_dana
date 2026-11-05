# ADR-005 — Clerk identity; API verifies JWT and maps to an internal account

| Field | Value |
|---|---|
| Status | Proposed (mentor approval at M0). Re-affirmed 2026-11-06 (DEC-019, DEC-021) |
| Date | 2026-11-04 (1.0: 2026-11-06) |
| Version | 1.0 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | CON-005, DEP-006; implemented in `apps/api/app/security/clerk.py` |

## Context

Travelers and the curator sign in on mobile and web. The foundation already verifies Clerk RS256 JWTs and maps
the subject to an internal account UUID (`GET /v1/me`). Private data is owner-scoped and must be deletable within
24 h. Contact details must never reach AI, search or page-fetch providers.

## Decision

- Clerk manages credentials and sessions; tokens are kept in SecureStore on mobile.
- The API verifies signature, issuer, exp/nbf/iat, subject and audience/authorized party; the internal account UUID
  is the owner key on every private row; client-supplied owner IDs never authorize.
- The curator role is checked server-side on every `/v1/admin` route.
- Account deletion deletes private rows in one transaction, revokes sessions and deletes the Clerk user last; a
  failed step is retried by the jobs runner until done within 24 h.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. Clerk SDKs + server-side JWKS verification + internal UUID | **Chosen** | Already built; hosted UI; free plan covers the study |
| B. Amazon Cognito | Rejected | Rework of the foundation; weaker Expo experience |
| C. Self-built auth | Rejected | Security burden for one developer |

## Consequences

- Positive: no credential storage in Gonarra; contact details stay in Clerk, which helps BR-046.
- Negative: a Clerk outage blocks sign-in; JWKS is cached to reduce calls.

## Drivers

CON-005, BR-020, BR-021, BR-044, BR-046, DEP-006, QAS-04, QAS-10.
