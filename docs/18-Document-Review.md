# DaNavi — Documentation Review Record

Version 1.3 | 2026-10-19 | Status: documentation baseline ready for stakeholder review. Document ownership and navigation: [Index](00-INDEX.md).

## Purpose and review scope

This record reports only checks actually performed on the v1.3 documentation set. It is an internal engineering review, not a claim of institutional approval, standards certification, implemented functionality or production readiness. Runtime, database, provider, store and native-device evidence remain separate delivery gates.

## Changes reviewed in v1.3

- Reframed DaNavi for English-first, first-time international visitors to Da Nang and bounded the core experience to one-day planning.
- Defined a guest-first model: Explore, Place Detail and audio preview remain public; Generate, Save and Ask AI require authentication while preserving the in-progress form across sign-in.
- Standardized start-point capture as a map pin, current location or a small preset list; P0 transport is car/ride-hailing only.
- Made external Google/Apple Maps handoff the navigation path. “I’ve arrived” is primary; foreground GPS fix and dwell are secondary confirmation.
- Added read-only trip essentials cache, active-trip restoration, minimum supported app/API version handling and a complete account-deletion slice.
- Reduced the content target to 15–20 curated POIs across Culture, Beach, Food and Nature, with at least five flagship English audio guides.
- Kept Ask AI authenticated and single-turn at the server boundary; client-side history is device-only. Added English alias search and translation provenance.
- Consolidated product UI into 15 primary screens plus supporting authentication, deletion and P1 camera/voice screens. Retired duplicate UI specifications without reusing retired IDs.
- Updated API, data model, security, curation, test, traceability, plan, research and diagrams to the same scope.

## Current review results

| Check | Result actually observed | Limit |
|---|---|---|
| Markdown structure | 21 Markdown files checked; 130 local links resolved; checked tables have consistent columns | Structural check only; external URLs and factual claims require source review |
| Requirements and traceability | 20 canonical FRs are present in the RTM: 17 P0 and three P1 | Traceability is planned coverage, not execution evidence |
| Cases and tasks | 45 unique test IDs and 29 task outputs: 41 active P0/quality tests, three deferred P1 tests and one retired test | No test case or task is marked executed by this review |
| OpenAPI | JSON parsed; 24 paths, 28 operations, 40 schemas and 249 local `$ref` uses resolved; operation IDs are unique and path parameters are required | No live endpoint or external full OpenAPI conformance run |
| Targeted API contracts | Version 1.3, account deletion, typed `426`, one-day planning, three start-point options, car-only transport, four categories, English Ask locale and cache metadata were asserted | Assertions cover the v1.3 decisions, not every possible schema branch |
| Wireframes | 17 unique editable HTML screen frames at 393×852; static scan found no obvious Vietnamese app copy | Browser/native visual render, interaction and screen-reader review were not executed |
| Color tokens | Ten recorded text/background pairs range from 4.76:1 to 17.85:1 and meet the stated normal-text threshold | Arithmetic token check only; photography, maps, scaling and native states still need device checks |
| Diagrams | Ten Draw.io sources and ten SVG previews are well-formed; source cell IDs are unique and references resolve | Full-size visual inspection and Draw.io re-import were not executed |
| Database definition | 19 tables plus the v1.3 locale, alias, translation, transport, deletion and provenance fields passed static checks | SQL was not executed against PostgreSQL/PostGIS/pgvector |
| Research/source support | Competitor and store-policy claims were bounded to official pages inspected on 2026-10-19; no novelty or superiority conclusion was inserted | No comparative usability benchmark, participant study or supervisor validation yet |
| Evidence integrity | No participant responses, measured model scores, real content rights, runtime results or store acceptance were fabricated | These remain explicit external evidence gates |

## Repository checklist applicability

The retained checklist workbooks are review aids. Their filenames do not prove IEEE/UML compliance, and this review does not assert that every workbook row passes.

| Checklist area | Canonical v1.3 artifacts | Remaining evidence |
|---|---|---|
| Product/requirements | 01-PRD.md; 10-BRD.md; 11-User-Stories.md; 14-Traceability.md | Approved objectives, rubric and stakeholder sign-off |
| Architecture/design | 02-SAD.md; 09-Project-Decisions.md; 12-Blueprint.md; diagrams/ | Provider trials, pinned versions and visual import review |
| API/database | 05-Database-Design.md; 06-API-Design.md; database.sql; openapi.json | PostgreSQL migration trial, live contract and load evidence |
| UI/UX | 07-UI-UX-Design.md; UI_UX_design/wireframes.html | Native build, accessibility, map/photo contrast and interaction review |
| Verification | 08-Test-Plan.md; 13-Development-Plan.md; 14-Traceability.md | Executed cases, defects, retests and acceptance records |
| Security/content/research | 15-Security-Privacy.md; 16-Data-Curation.md; 17-Research-and-Academic-Plan.md | Rights, translation/narration QA, consent, recruitment and empirical results |

## Unresolved gates before implementation acceptance

| Gate | Required evidence / owner |
|---|---|
| Academic alignment | Approved objectives, report template and rubric; student and supervisor |
| Technical feasibility | Native shell, database/extensions, routes provider, location foreground behavior and model trials; developer |
| Store readiness | Public privacy policy, Google Play external account-deletion resource, data declarations and selected test distribution channel; product/developer |
| Content readiness | 15–20 verified POIs, English review, image/audio rights, five completed audio guides and offline-use permission; curator/narrator |
| Visual/native review | Full-size diagram review, wireframe review, native text scaling, VoiceOver/TalkBack and target-device checks; designer/developer |
| Implementation acceptance | Builds, migrations, P0 tests, failure/retest history, crash reporting, active-trip recovery and old-version blocking; developer/reviewer |
| Research/evaluation | Participant consent, international-visitor recruitment, held-out RAG evaluation, field GPS checks and UAT; researcher |

## Review outcome

The v1.3 documents are internally aligned as a reviewable product specification for the agreed DaNavi direction. This means the written scope, flow, identifiers and contracts are consistent enough for stakeholder review; it does not mean the app has been implemented or validated. Commit and push are intentionally deferred until the stakeholder approves this documentation review.
