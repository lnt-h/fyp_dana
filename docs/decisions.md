# Gonarra — Decision log (2026-11-06)

Single source for decisions and open questions; replaces SRC-100/SRC-105/BRD §13 (tag `docs-sdlc-full`).
Owner: Lê Ngọc Tấn Hiền. Approver: trantrongminh (full name pending, OQ-001). Binding design detail lives in `docs/adr/`.

## 1. Decisions

Status key: **Accepted** = accepted by the owner (directly or under the standing delegation, §2); **Pending** = mentor confirmation still pending, at the M0 gate unless stated.

| ID | Date | Decision | Status | Supersedes / relation |
|---|---|---|---|---|
| DEC-001 | 2026-11-04 | Direction: a trustworthy planner plus a grounded assistant, for **Đà Nẵng** (rev. 1, DEC-013). Must: place search, proposal from prompt + preferences (1–3 days, one city), timeline + map, Plan Health, edits with explicit Save, place card, text Guide with sources, booking handoff links, bilingual VI/EN. Should: lock + single-day regeneration, voice Q&A, photo identification. Could: indicative stay prices. | Accepted; mentor pending | Rev. 1 by DEC-013 (was five cities) |
| DEC-002 | 2026-11-04 | Booking = handoff links to Agoda, Booking.com, Klook and 12Go (Must); indicative prices from LiteAPI runtime-only (Could); no payment or in-app booking. | Accepted; mentor pending | — |
| DEC-003 | 2026-11-04 | Cut order if late: prices → photo → voice → lock/regeneration → iOS. **Never cut** bilingual content, the Đà Nẵng catalog gate (MET-011 rev. 1) or explicit Save. | Accepted; mentor pending | Rev. 1 by DEC-019 (was "never cut five cities") |
| DEC-004 | 2026-11-04 | Won't items (in-app booking/payment, flights, social, multi-city, and now the other cities) stay on the post-FYP roadmap with extension points but no implementation. | Accepted; mentor pending | Replaces the Won't line of DEC-001/002 |
| DEC-005..007 | 2026-11-04 | Hosting, deployable separation and data sources are design-level: see ADR-002 (AWS EC2 + RDS, re-affirmed as default by DEC-018), ADR-001 (three deployables over `/v1`), ADR-006 and ADR-012 (provider data and ingestion sources). | Accepted; mentor pending | Hosting choice re-opened by OQ-129 |
| DEC-008 | 2026-11-04 | Scheduling by Google OR-Tools with a cached Google Routes matrix; the LLM only selects/ranks place IDs and writes rationales; Plan Health is deterministic code (ADR-011). | Accepted; mentor pending | Refined by DEC-011, DEC-016 |
| DEC-009 | 2026-11-04 | Ingestion by a Typer/DuckDB CLI inside `apps/api`; no workers, queues or Redis (ADR-012). | Accepted; mentor pending | — |
| DEC-010 | 2026-11-05 | Guide retrieval in two tiers (ADR-010): place-scoped questions use every approved fact and chunk of the pinned publication, no question embedding or threshold; city-scoped hybrid retrieval was Tier 2 roadmap. | Accepted; mentor pending | **Tier 2 promoted by DEC-017** |
| DEC-011 | 2026-11-05 | One multi-day OR-Tools model per proposal: days as vehicles, per-date opening windows, drop penalties from LLM ranks, locks mandatory; the LLM never assigns days, order or times. | Accepted; mentor pending | **Extended by DEC-016** |
| DEC-012 | 2026-11-05 | Chunk embeddings are computed on write by the curation API (API-035 `chunks[]`) with `embedding_model` recorded; CLI `embed` only backfills and re-embeds. | Accepted; mentor pending | — |
| DEC-013 | 2026-11-06 | FYP scope is **Đà Nẵng only**; Hội An is an area inside Đà Nẵng (2025 merger). Release gate: ≥ 100 published, reviewed, bilingual places, of which ≥ 30 in the Hội An area (MET-011 rev. 1). `cities` stays in the model; only `da-nang` is enabled. | Accepted; **mentor pending, blocks M0** | Supersedes SRC-100 A-003 |
| DEC-014 | 2026-11-06 | Agno agents inside `apps/api` (`Agent`, tools, `output_schema`, retries, `agno.eval`); no AgentOS, no LLM team leader. Orchestration is Gonarra's own deterministic async step-runner. Agno imports confined to `app/agents/` and `app/ai/`. | Accepted; mentor pending | Supersedes SRC-100 A-021 "Agno dropped"; ADR-004 option C |
| DEC-015 | 2026-11-06 | Runtime research agent (Tavily search, page fetch, Google Places existence check), **catalog-first**: runs only when the catalog pool is thin or requests are unmet. Web-found places are real, saveable stops labelled `WEB_UNVERIFIED` (source URL, fetched date); Plan Health is capped at WARNING; every such place enters the curator queue. A model may propose a candidate, never publish a place or author a displayed fact. | Accepted; **mentor pending, blocks M0** | Reverses BRD §5.2 "no runtime web search", ADR-010 option D |
| DEC-016 | 2026-11-06 | Scheduling stays deterministic (Routes → OR-Tools → Plan Health). Plan Health gains curator-reviewed **calendar rules**: weekly closures, dates, lunar dates (Hội An lantern nights, Tết), ticket validity, seasonal notices. | Accepted; mentor pending | Extends DEC-011, ADR-011 |
| DEC-017 | 2026-11-06 | Guide = **city-level chat** for Đà Nẵng: hybrid retrieval (entity → lexical → vector, rank fusion) over approved facts and chunks; deterministic web fallback labelled `WEB_UNVERIFIED`; citations validated against supplied evidence, otherwise `insufficient_evidence`. | Accepted; mentor pending | Promotes DEC-010 Tier 2 to v1 |
| DEC-018 | 2026-11-06 | **Free tier only** (Gemini, Groq, Tavily, Google Maps monthly credit). Quota ledger, Postgres caches and per-role model fallback chains are part of the design. Never send account IDs, contact data or precise location to AI or search providers. Hosting: local Docker Compose now, single VM later (OQ-129). | Accepted; mentor pending | Extends BR-046; re-affirms ADR-002 as default |
| DEC-019 | 2026-11-06 | VI and EN equal priority. Keep Expo + Clerk. Voice, photo identification and indicative prices are **not cut** and stay Should/Could; cut order per DEC-003 rev. 1. | Accepted; mentor pending | Revises DEC-003 |
| DEC-020 | 2026-11-06 | Comparative user study: each participant plans the same Đà Nẵng trip with Gonarra and with ChatGPT or Gemini; measures = errors per day (MET-014), trust rating, whether the trust label is noticed. Protocol in `docs/test-plan.md` §6. | Accepted; mentor pending | Adds MET-014 |
| DEC-021 | 2026-11-06 | Documentation re-baseline: rewrite prose, keep every ID (withdraw or supersede, never renumber), one PR `docs/re-baseline-da-nang`, mentor signs at M0. Long SDLC documents are condensed into `docs/decisions.md` and `docs/test-plan.md`; the full set is kept at tag `docs-sdlc-full`. | Accepted (facilitator, owner informed); mentor pending | — |

## 2. Standing rules

- The owner's standing delegation ("best choice") lets the facilitator decide; the decision is recorded here as Accepted and the mentor confirms it at the next gate.
- Planning, documentation and direction work runs on Fable; code tasks run on Opus 5.5 at medium effort, as parallel subagents with disjoint files.
- The facilitator drafts and never approves; every approval row stays `[Pending]` until the mentor signs.
- IDs are never renumbered or reused; a changed item is revised ("rev. 1"), withdrawn or superseded, with the successor named.
- Code may not differ from an accepted ADR, `docs/api/openapi.yaml` or `docs/data/schema.sql` without updating the contract in the same change.
- Facts, coordinates, hours, prices, distances and durations never come from a model; unknown IDs or fields in model output are validation failures.
- Nothing is reported as verified on real providers, devices or bilingual content when only mocks or static checks ran.
- Dates are written `YYYY-MM-DD`; this log is the only place where decisions and open questions are maintained.

## 3. Open questions

OQ-005 (AWS account) and OQ-007 (`plan.md` amendment) are closed. OQ-117..120 are the former screen-specs OQ-110..113, closed by SRC-100 A-029; TEST_PLAN keeps OQ-110..113.

| ID | Question | Blocks | Owner | Needed by | Recommendation |
|---|---|---|---|---|---|
| OQ-001 | Mentor's full name and title | Validity of every approval | Lê Ngọc Tấn Hiền | 2026-11-11 | Ask at the M0 meeting; update the approver rows |
| OQ-002 | Exact FYP submission date | Schedule, ASM-002 | Lê Ngọc Tấn Hiền | 2026-11-11 | Confirm with the faculty; plan on 2027-02-01 until then |
| OQ-003 | What the examiners assess (demo, report, study) | Weight of MET-001..014 | Lê Ngọc Tấn Hiền | 2026-11-11 | Ask the mentor; assume demo + report + study |
| OQ-004 | Is ethics approval or a consent template required for the study? | Study start, consent forms, OQ-113, OQ-128, OQ-130 | Lê Ngọc Tấn Hiền (ask mentor) | 2026-11-11 | Ask now; prepare the EN/VI consent forms either way |
| OQ-006 | Measure participants' manual planning time as a baseline pre-task? | BO-001 baseline | Lê Ngọc Tấn Hiền | 2026-11-15 | Drop the pre-task; the ChatGPT/Gemini arm (DEC-020) is the comparison |
| OQ-008 | Obligations for transferring traveller and study data outside Vietnam (AWS Singapore, Google, Groq, Tavily, Clerk) | Consent form, provider policies | Lê Ngọc Tấn Hiền (ask mentor) | 2026-11-30 | Disclose every provider in the consent form; no personal data leaves the account store |
| OQ-031 | Google Maps Platform terms: which Routes/Places fields may be retained and for how long; attribution placement | ADR-006, `routes_matrix_cache`, `places_lookup_cache` | Lê Ngọc Tấn Hiền | 2026-11-25 | Handle together with OQ-124; default deny until read |
| OQ-032 | Gemini model pins, quotas and data-use terms; Tier 2 retrieval calibration for Vietnamese | RSK-002, ADR-010, ASM-019 | Lê Ngọc Tấn Hiền | 2026-11-30 | Pins via OQ-126; calibrate on the Guide golden sets (`docs/test-plan.md` §4) |
| OQ-110 | Is there a separate staging environment? | Performance and failure-injection runs, cost | Lê Ngọc Tấn Hiền | 2026-12-08 | Second Compose project and database on the same host chosen in OQ-129; no extra cloud resources |
| OQ-111 | Who gives the independent second judgement on the MET-007 citation sample and the EN content review? | MET-007, one-person team | trantrongminh | 2026-12-08 | Mentor or a fellow student reviews a 20% random sample |
| OQ-112 | Which physical devices for the Android minimum/latest and iPhone checks? | Device verification, iOS cut decision | Lê Ngọc Tấn Hiền | 2026-12-15 | Owner's phone as latest plus one borrowed older Android |
| OQ-113 | How are participants recruited, and is compensation offered? | Study protocol | Lê Ngọc Tấn Hiền (confirm under OQ-004) | 2026-12-15 | Adults ≥ 18 from university and personal networks; no payment |
| OQ-121 | Authoritative post-merger Đà Nẵng boundary and the travel-area list (incl. Hội An Old Town, beaches/islands) | DEC-013 gate, `areas` seed, `OUTSIDE_CITY` | Lê Ngọc Tấn Hiền | 2026-12-09 | Travel areas, not wards; boundary from an open dataset with licence recorded |
| OQ-122 | Tavily terms: may results and page text be cached 7 days? Monthly credit confirmed? | DEP-010, `research_cache` policy | Lê Ngọc Tấn Hiền | 2026-12-08 | Record in `provider_policies` before the first call |
| OQ-123 | Groq free-tier terms and data use | DEP-011, BR-046 | Lê Ngọc Tấn Hiền | 2026-12-08 | Read terms; same redaction as Gemini |
| OQ-124 | Google Places (New) field SKUs for status/hours; may lat/lng be cached ≤ 30 days? | Research check cost, `places_lookup_cache` | Lê Ngọc Tấn Hiền | 2026-12-08 | Minimal field masks; store only `place_id` canonically |
| OQ-125 | Lunar-calendar algorithm for VN (UTC+7), test vectors (Tết 2026-02-17, 2027-02-06), official lantern-night day (lunar 14th vs owner's "1st/15th") | DEC-016 calendar rules | Lê Ngọc Tấn Hiền | 2026-12-22 | Pure-Python algorithm with golden tests; verify on the Hội An heritage office site |
| OQ-126 | Agno version and Gemini/Groq model IDs to pin; embedding model at 768 dims | DEP-012, ADR-012 | Lê Ngọc Tấn Hiền | 2026-11-20 | Pin `agno==3.1.12` (spike 2026-11-06); keep `vector(768)`; verify live structured output once keys exist |
| OQ-127 | Threshold for "catalog pool is thin" and per-plan caps on Tavily/Places calls | DEC-015 | Lê Ngọc Tấn Hiền | 2026-12-08 | Set from SPK-004 numbers |
| OQ-128 | May `WEB_UNVERIFIED` stops appear in study sessions; must the traveller acknowledge before saving such a plan? | DEC-020 protocol, consent | Lê Ngọc Tấn Hiền (ask mentor) | 2027-01-06 | Yes with acknowledgement; it is the measured variable |
| OQ-129 | Hosting: AWS EC2 + RDS (ADR-002) or one VM with Docker Compose | DEC-018, M2 | Lê Ngọc Tấn Hiền | 2026-12-09 | Single VM for the study; ADR-002 stays the default on paper |
| OQ-130 | ChatGPT/Gemini baseline protocol: accounts, model versions, prompt parity, ethics | DEC-020, `docs/test-plan.md` §6 | Lê Ngọc Tấn Hiền (ask mentor) | 2027-01-06 | Same prompt text, pinned dates, screenshots archived |

## 4. Live assumptions and risks

| ID | Statement | Impact if wrong | Validation / response | Needed by |
|---|---|---|---|---|
| ASM-002 | Submission date is 2027-02-01 | Schedule wrong | Confirm with faculty (OQ-002) | 2026-11-11 |
| ASM-004 | ≥ 15 places reviewed per week from 2026-11-16 | MET-011 rev. 1 missed | Weekly count in `progress.md`; < 10/week for two weeks triggers the DEC-003 cut order | Weekly |
| ASM-017 | The Hội An area holds ≥ 30 publishable places within the gate | Gate missed | Count after 4 weeks of curation | 2026-12-15 |
| ASM-018 / RSK-013 | Tavily free tier (≈ 1 000 credits/month) covers development and study; no free quota (Tavily, Groq, Gemini) is exhausted during the study | Research agent or planner degraded near the study | Daily and monthly ceilings in adapters; 300 Tavily credits reserved; sessions spread over ≥ 2 days (OQ-122) | 2026-12-08 |
| ASM-019 | `pg_trgm` + pgvector hybrid retrieval gives acceptable Vietnamese recall without `unaccent`/tsvector | Guide answers miss evidence | Retrieval spike on the Guide golden sets (OQ-032) | 2027-01-06 |
| ASM-020 | Groq free-tier models extract facts from VI/EN pages well enough for `WEB_UNVERIFIED` candidates | Research precision too low | SPK-004 manual count | 2026-12-08 |
| ASM-021 | Agno agents run in-process in FastAPI, no workers, within a 2 GiB host | Architecture change | Day-1 Agno spike; load test before the study | 2026-11-20 |
| ASM-022 / RSK-015 | The post-merger Đà Nẵng boundary and Hội An area can be defined from a licensed open dataset; boundary ambiguity is low | `OUTSIDE_CITY` rejects Hội An places | Travel-area list instead of wards; boundary optional for the gate (OQ-121) | 2026-12-09 |
| RSK-001 | One curator → fewer than 100 Đà Nẵng / 30 Hội An-area places | High | Hội An area first; AI drafts with mandatory human review; curator queue; weekly tracking. Contingency: cut Should features, never the gate | Weekly |
| RSK-002 | Free-tier terms let providers use inputs → exposure of traveller content | High | BR-046 redactor (fails closed); disclose in consent; verify terms (OQ-008, OQ-123). Contingency: paid-tier trial credit | 2026-11-30 |
| RSK-012 | Web-found places are wrong and travellers follow them | High | `WEB_UNVERIFIED` label on every surface; Places existence check; WARNING cap; curator queue; MET-014 measures the rate. Contingency: research agent behind a flag, off for the study if precision is below threshold (OQ-128) | Before study |
| RSK-014 | Agno API churn breaks agents mid-project | Medium | Exact pin `agno==3.1.12`; imports isolated in two modules; spike before coding | 2026-11-20 |

## 5. Change history

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-11-06 | Lê Ngọc Tấn Hiền (drafted with Claude Code) | Created from SRC-100, SRC-105, BRD §13 and the governance "fixed decisions"; DEC-001 and DEC-003 restated in revised form; those sources retired at tag `docs-sdlc-full` |
