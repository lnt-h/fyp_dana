# ADR-006 — Runtime-only provider data policy (Google Places, LiteAPI prices)

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | BRU-004, BRU-005, DATA.md (SRC-007), SRC-104 |

## Context

Live hours/status come from Google Places, whose terms restrict caching and storage; indicative stay prices come
from LiteAPI (fallback Hotelbeds evaluation), shown only at viewing time and never stored with a trip (BRU-005,
AC-043). Attribution must be shown wherever provider or open data appears (BR-047). Logs must not become a shadow
cache (SRC-003).

## Drivers

BRU-004, BRU-005, BR-043, BR-047, CON-006, QAS-12, C-010.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Provider policy registry with default-deny persistence; runtime adapters return typed DTOs with retrieval time and attribution; only permitted identifiers persisted | Terms-compliant by construction; auditable | Each provider needs a policy record | **Chosen** |
| B. Prefetch Places details into the catalog | Faster, fewer calls | Breaches terms; restricted data becomes "fact" | Rejected |
| C. Store prices with trips for comparison | Nice UX | Violates BRU-005; misleading prices | Rejected |
| D. Call providers directly from the mobile app | Fewer server calls | Exposes keys; bypasses quotas and redaction | Rejected |

## Decision

Every provider call goes through an adapter in CMP-013 that classifies each field as CANONICAL, EPHEMERAL,
IDENTIFIER_ONLY or DENY under an active policy record; unknown fields are denied. Google Places: only place ID may
be retained (subject to OQ-031); live hours/status are fetched when a place card is opened and shown with
"retrieved at" and Google attribution; failure hides only that enrichment. LiteAPI/Hotelbeds: prices are fetched
per stays-panel view and shown with retrieval time and the partner-confirmation notice; nothing is persisted; the
feature is behind `FEATURE_STAY_PRICES` (first in cut order). Raw provider bodies are never logged.

## Consequences

- Positive: compliance is testable (0 restricted fields persisted; 0 prices stored).
- Negative: a call per card view uses quota (RSK-003); offline place cards show catalog facts only.
- Follow-up: OQ-031 (Google terms), DEP-005/SPK-001 (LiteAPI coverage and terms).
