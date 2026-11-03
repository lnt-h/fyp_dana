# ADR-005 — Clerk identity; API verifies JWT and maps to an internal account

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | CON-005, DEP-006; implemented in `apps/api/app/security/clerk.py` |

## Context

Travelers and the curator need sign-in on mobile and web. The foundation already verifies Clerk RS256 JWTs and maps
the subject to an internal account UUID (`GET /v1/me`) (SRC-009). Private data must be owner-scoped (BR-020) and
deletable within 24 h (BR-021).

## Drivers

CON-005, BR-020, BR-021, BR-044, DEP-006, QAS-04, QAS-10.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Clerk (Expo + React SDKs), API verifies JWT via JWKS, internal account UUID | Already built; social sign-in; hosted UI; free plan covers study size (DEP-006) | External dependency; user deletion must be coordinated | **Chosen** |
| B. Amazon Cognito | Same cloud as hosting | Rework of built foundation; weaker Expo DX | Rejected |
| C. Self-built auth (passwords, sessions) | No vendor | Security burden for one developer; time | Rejected |

## Decision

Clerk manages credentials and sessions; tokens are kept in SecureStore on mobile. The API verifies signature,
issuer, exp/nbf/iat, subject, audience/authorized party; internal account UUID is the owner key on every private
row; client-supplied owner IDs never authorize. The curator role is checked server-side (mechanism: OQ-036).
Account deletion deletes private rows, revokes sessions and deletes the Clerk user, retried by the jobs runner.

## Consequences

- Positive: no credential storage in Gonarra; contact details stay in Clerk (helps BR-046).
- Negative: Clerk outage blocks sign-in (DEP-006); JWKS cached to reduce calls.
