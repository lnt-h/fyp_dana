# SRC-105 — Re-baseline session: Đà Nẵng scope, multi-agent planner, trust labels (Gonarra)

> **Kit prompt:** `analysis/BRD_Elicitation_Prompt_IEEE_standard.md` (SDLC-Prompt-Checklist @ 6996dae), §7.3 change-request triage
> **Interviewee (owner):** Lê Ngọc Tấn Hiền, project author
> **Facilitator:** Claude Code (agent; drafts only, never approves)
> **Started:** 2026-11-06 · **Status:** closed 2026-11-06, mentor confirmation pending at the M0 gate
> **Supersedes in part:** SRC-100 (A-003 five-city scope; A-021 "Agno/AgentOS dropped"; DEC-003 "never cut five cities"; DEC-010 Tier 2 "roadmap")
> **Numbering note:** SRC-101..SRC-104 are desk-research sources already issued inside SRC-100, so this record is SRC-105. Answers continue from A-029 (SRC-100, PR #7). Decisions continue from DEC-012. Open questions continue from OQ-120 (see "OQ renumbering" below).

## Source register used for this session

| ID | Source | Notes |
|---|---|---|
| SRC-003 | `AGENTS.md` (2026-11-04) | Hard rules in force before this session |
| SRC-009 | `apps/api`, `apps/mobile` at `14e0efc` | Code baseline (api: accounts + Clerk only; mobile: all screens on Hội An fixtures, no HTTP calls) |
| SRC-106 | MonkeyTravel, "Best AI trip planners 2026 compared" (updated 2026-10-28); independent 2026 reviews (Savvy Jetsetter, aitravel.tools, Travel Anywhere) | Market scan; vendor blog, self-promotional; cross-checked |
| SRC-107 | Agoda 2026 Travel Outlook (VN: 81% intend to use AI; 28% trust, 59% neutral); VTV 2026-11-04 (63% of VN travellers used AI) | Adoption and trust figures, secondary reporting |
| SRC-108 | Greetwell / Simon-Kucher 2026 surveys; AirGuide and Wyoming News reports of AI itinerary errors; MonkeyEatingMango 356-trip study | Accuracy problem (closed venues, wrong hours, non-existent places); vendor figures treated as directional only |
| SRC-109 | Visit Vietnam platform at ITB Asia 2026 (Sun Group, with VNAT); Vie Travel AI launch 2026-01; Agoda AI Assistant beta 2026-09 | Competitor landscape in Việt Nam |
| SRC-110 | Google "Ask Maps" rollout (US/India, English) and Vietnamese tech press on Google Maps 26.11 in VN; Apple Maps iOS 27 | Local-assistant competition; Vietnamese-language gap |
| SRC-111 | Hội An Old Town ticket (120 000 ₫, same day), Tết 2026 ticket suspension, lantern nights (lunar calendar), 2025 Quảng Nam–Đà Nẵng merger | Calendar and ticket facts that motivate calendar rules; to be re-verified on official sources (OQ-125) |
| SRC-112 | Provider limits checked 2026-11-06 (secondary): Gemini Flash free ≈ 10 RPM / 250 RPD (sources conflict); Tavily free 1 000 credits/month; Groq free ≈ 30 RPM / 1 000 RPD; Agno current release **3.1.12** verified in a scratch spike 2026-11-06 (`agno.agent.Agent` with `output_schema`, `tools`, `tool_call_limit`, `retries`; `agno.models.google.Gemini` native structured output; `agno.models.groq.Groq` JSON mode only; `agno.eval.accuracy.AccuracyEval`; `agno.eval.suite.Case`); no live model call made | Feeds DEC-018 quota design; must be re-read on the official pages on coding day |

## Round 0 — findings presented to the owner (2026-11-06)

- F-010: "Prompt → itinerary" is commoditised (8+ free tools; general assistants and OTAs own breadth and booking) [SRC-106].
- F-011: The one universally reported, unsolved problem is wrong place information; no reviewed product exposes a trust or verification signal [SRC-106, SRC-108].
- F-012: Vietnamese travellers lead Asia in AI-planning intent but trust is low; Gemini Ask Maps is not available in Vietnamese or in Việt Nam [SRC-107, SRC-110].
- F-013: A state-backed competitor (Visit Vietnam) is launching an AI trip planner with far greater distribution [SRC-109].
- F-014: Facilitator recommendation: position Gonarra as a *verified local layer* (every place, hour, ticket and answer carries a source and a verification date) rather than as another itinerary generator; make the "Today" view and the Guide the primary in-trip surfaces.

## Round log

### Round 1 — direction (2026-11-06)
- A-030 → scope: Owner: "chốt làm thiên về Đà Nẵng thôi". **FYP scope = Đà Nẵng only**, including the Hội An area (part of Đà Nẵng city since the 2025 merger). Hà Nội, TP. Hồ Chí Minh and Huế stay on the roadmap (DEC-004 vision kept). → DEC-013.
- A-031 → orchestration: Owner: mentor allows **Agno**; owner wants a **multi-agent** planner with a research/crawler agent and explicitly **accepts the information weakness** of web-sourced content ("chấp nhận điểm yếu thông tin"). → DEC-014, DEC-015.
- A-032 → target users and language: **VI and EN equal** ("cả hai ngang nhau"). → DEC-019.
- A-033 → budget: **free tier only** ("chỉ free tier"). → DEC-018.
- A-034 → research policy: delegated ("best choice"). Facilitator recommendation adopted: **catalog-first; web only when the catalog pool is thin or the request has unmet asks**; web-found places labelled and queued for curation. → DEC-015.
- A-035 → scheduling: **code (OR-Tools + Plan Health)** assigns days, order and times; LLM selects and writes only. → DEC-016.
- A-036 → Guide depth: **city-level chat** ("hỏi bất kỳ gì về Đà Nẵng"). → DEC-017.
- A-037 → platform and scope cuts: keep **Expo + Clerk**; host later on one VM with Docker Compose; **nothing is cut** from the FYP scope now ("không cắt, cũng như hiện tại chưa cần hạ tầng nên để sau") — voice, photo and prices remain Should/Could. → DEC-018, DEC-019.
- A-038 → evaluation: **Gonarra vs ChatGPT/Gemini on the same prompts**, errors per day. → DEC-020.

### Round 2 — tech-lead delegations (2026-11-06)
- A-039 → web-found places in itineraries: delegated ("as a techlead choose a best choice for ui/ux user and logic for development"). Facilitator decision: **web-found places are real stops, saveable, always labelled `WEB_UNVERIFIED`** with source URL and fetched date; a plan containing one is capped at Plan Health WARNING. Rationale: a suggestion-only panel makes the research agent cosmetic; "preview-only, cannot Save" blocks the traveller at the worst moment. → DEC-015.
- A-040 → LLM team leader: delegated ("giữa agno và ko dùng agno choose best choice"). Facilitator decision: **use Agno for the agents (`Agent`, tools, `output_schema`, retries, `agno.eval`); no Agno Team leader; orchestration is Gonarra's own deterministic async step-runner**. Rationale: the spine is deterministic, a leader adds one Gemini call per request under a ~250 RPD free quota and removes reproducibility; Agno `Team`/`Workflow` add unverified API surface. → DEC-014.
- A-041 → process: code tasks are delegated to Opus 5.5 (medium effort) subagents; documentation is written by the facilitator. PR #7 merged on owner instruction (`14e0efc`). Re-baseline delivered as one PR `docs/re-baseline-da-nang`. → DEC-021.

## Decisions (adopted under the owner's standing delegation; mentor confirms at M0)

| ID | Decision | Date | Decision maker | Rationale / source |
|---|---|---|---|---|
| DEC-013 | FYP scope is **Đà Nẵng only**; Hội An is an *area* within Đà Nẵng; Hà Nội, TP.HCM, Huế move to the roadmap. Release gate: ≥ 100 published, reviewed, bilingual places in Đà Nẵng, of which ≥ 30 in the Hội An area (MET-011 rev. 1). `cities` stays in the data model; only `da-nang` is enabled. | 2026-11-06 | Lê Ngọc Tấn Hiền (A-030) | Depth over breadth [F-011, F-013]; one curator (CON-002) |
| DEC-014 | **Agno agents inside `apps/api`**, no AgentOS service, no workers/queues/Redis. **No LLM team leader**: orchestration is deterministic Gonarra code; Agno provides `Agent` (tools, structured output, retries) and `agno.eval`. All Agno imports confined to `app/agents/` and `app/ai/`. Supersedes SRC-100 A-021 "Agno dropped" and ADR-004 option C. | 2026-11-06 | Owner (A-031) + facilitator (A-040) | Mentor allows Agno; quota and reproducibility |
| DEC-015 | **Runtime research agent** (Tavily search, page fetch, Google Places existence/status check) is in scope. Policy **catalog-first**. Web-found places are **real, saveable stops labelled `WEB_UNVERIFIED`** (source URL, fetched date); Plan Health capped at WARNING for such plans; every web-found place enters a **curator queue**. Reverses BRD §5.2 "runtime web search out of scope" and ADR-010 option D. | 2026-11-06 | Owner (A-031, A-034) + facilitator (A-039) | Owner accepts and wants to *measure* the information weakness [F-011] |
| DEC-016 | **Scheduling stays deterministic**: Google Routes → one OR-Tools multi-day model → Plan Health (code). LLM never assigns days, order or times. Plan Health gains **calendar rules** (weekly closures, dates, lunar dates incl. Hội An lantern nights and Tết, ticket validity, seasonal notices) as curator-reviewed data. Extends DEC-011 and ADR-011. | 2026-11-06 | Lê Ngọc Tấn Hiền (A-035) | Explainable, reproducible; calendar errors are the most common competitor fault [SRC-108, SRC-111] |
| DEC-017 | **Guide = city-level chat** for Đà Nẵng: hybrid retrieval (entity → lexical → vector, rank fusion) over approved facts and chunks; deterministic web fallback labelled `WEB_UNVERIFIED`; citations validated against supplied evidence; otherwise `insufficient_evidence`. Promotes DEC-010 Tier 2 from roadmap to v1. | 2026-11-06 | Lê Ngọc Tấn Hiền (A-036) | Vietnamese-language local assistant gap [F-012] |
| DEC-018 | **Free tier only**: Gemini free, Groq free, Tavily free, Google Maps Platform monthly credit. Quota ledger, Postgres caches and per-role model fallback chains are part of the design. Never send account IDs, contact data or precise location to AI or search providers (BR-046 extended). Hosting decision deferred: local Docker Compose now; single VM later (OQ-129); DEC-005/ADR-002 re-affirmed as default. | 2026-11-06 | Lê Ngọc Tấn Hiền (A-033, A-037) | CON-001; free-tier data terms (RSK-002) |
| DEC-019 | VI and EN equal priority. Keep Expo + Clerk (CON-005). Voice, photo identification and indicative prices are **not cut**; they stay Should/Could. Cut order (DEC-003 rev. 1): prices → photo → voice → lock/regeneration → iOS; **never cut** bilingual content, the Đà Nẵng catalog gate (MET-011 rev. 1) or explicit Save. | 2026-11-06 | Lê Ngọc Tấn Hiền (A-032, A-037) | Protect Must scope under the new gate |
| DEC-020 | **Comparative user study**: each participant plans the same Đà Nẵng trip with Gonarra and with ChatGPT or Gemini; metrics = errors per day (closed place, wrong hours, non-existent place), trust rating, and whether the trust label is noticed (new MET-014). | 2026-11-06 | Lê Ngọc Tấn Hiền (A-038) | Hard evidence for the thesis claim [F-011] |
| DEC-021 | Documentation **re-baseline**: rewrite prose, keep every existing ID (withdraw or supersede, never renumber), versions → 1.0, delivered as one PR `docs/re-baseline-da-nang` for mentor sign-off at M0; traceability and RTM regenerated by a committed script. | 2026-11-06 | Facilitator (A-041), owner informed | SDP §4.6: scope and gate changes need mentor approval as one coherent diff |

## Assumptions, dependencies, risks raised

| ID | Type | Statement | Impact if wrong | Owner | Validation | Needed by |
|---|---|---|---|---|---|---|
| ASM-017 | Assumption | The Hội An area contains ≥ 30 publishable places reachable within the catalog gate | MET-011 rev. 1 missed | Lê Ngọc Tấn Hiền | Count after 4 weeks of curation | 2026-12-15 |
| ASM-018 | Assumption | Tavily free tier (≈ 1 000 credits/month) covers development + study with per-day caps | Research agent disabled near the study | Lê Ngọc Tấn Hiền | Ledger in `ai_quota_ledger`; OQ-122 | 2026-12-08 |
| ASM-019 | Assumption | Hybrid retrieval with `pg_trgm` + pgvector gives acceptable recall for Vietnamese without `unaccent`/tsvector | Guide answers miss evidence | Lê Ngọc Tấn Hiền | Retrieval spike on the Guide golden set; OQ-125 | 2027-01-06 |
| ASM-020 | Assumption | Groq free-tier Llama models extract facts from VI/EN web pages well enough for `WEB_UNVERIFIED` candidates | Research precision too low | Lê Ngọc Tấn Hiền | SPK-004 manual count | 2026-12-08 |
| ASM-021 | Assumption | Agno agents run in-process in FastAPI without workers and within the 2 GiB host | Architecture change | Lê Ngọc Tấn Hiền | Day-1 Agno spike; load test before study | 2026-11-20 |
| ASM-022 | Assumption | Post-merger Đà Nẵng boundary and the Hội An area can be defined from a licensed open dataset | `OUTSIDE_CITY` gate rejects Hội An places | Lê Ngọc Tấn Hiền | OQ-121 | 2026-12-09 |
| DEP-010 | Dependency | Tavily Search API (free) | Research agent unavailable | Lê Ngọc Tấn Hiền | Key + terms read (OQ-122) | 2026-12-08 |
| DEP-011 | Dependency | Groq API (free) as extraction model and fallback | Fallback chain shorter; Gemini quota pressure | Lê Ngọc Tấn Hiền | Key + terms read (OQ-123) | 2026-12-08 |
| DEP-012 | Dependency | Agno library pinned at `agno==3.1.12` (SRC-112) | Agent code rewrite | Lê Ngọc Tấn Hiền | Pin from day-1 spike (OQ-126) | 2026-11-20 |
| DEP-013 | Dependency | Vietnamese lunar-calendar algorithm/data and official festival dates | Calendar rules wrong | Lê Ngọc Tấn Hiền | OQ-125 | 2026-12-22 |
| RSK-012 | Risk | Web-found places are wrong (closed, misplaced, non-existent) and travellers follow them | High | Lê Ngọc Tấn Hiền | `WEB_UNVERIFIED` label on every surface; Places existence check; Plan Health WARNING cap; curator queue; MET-014 measures the rate. Contingency: research agent behind a flag, off for the study if precision < threshold (OQ-128) | Before study |
| RSK-013 | Risk | A third free-tier quota (Tavily, Groq) is exhausted during the study | Medium | Lê Ngọc Tấn Hiền | Daily/monthly ceilings in adapters; 300 Tavily credits reserved; study sessions spread over ≥ 2 days | Before study |
| RSK-014 | Risk | Agno API churn breaks agents mid-project | Medium | Lê Ngọc Tấn Hiền | Exact pin; imports isolated in two modules; spike before coding | 2026-11-20 |
| RSK-015 | Risk | Ambiguous Đà Nẵng/Hội An boundary after the 2025 merger | Low | Lê Ngọc Tấn Hiền | Travel-area list instead of administrative wards; boundary optional for the gate | 2026-12-09 |

## Open questions

OQ renumbering: OQ-110..OQ-113 were issued twice (TEST_PLAN.md and screen-specs.md). TEST_PLAN keeps OQ-110..113 (issued first, still open). The screen-specs set becomes **OQ-117..OQ-120** ("formerly OQ-110..113, screen-specs 0.1, closed by A-029"). New questions start at OQ-121.

| ID | Question | Blocks | Owner | Needed by | Recommendation |
|---|---|---|---|---|---|
| OQ-121 | Authoritative post-merger Đà Nẵng boundary and the travel-area list (incl. Hội An Old Town, Hội An beaches/islands) | DEC-013 gate, `areas` seed, `OUTSIDE_CITY` | Lê Ngọc Tấn Hiền | 2026-12-09 | Travel areas, not wards; boundary from an open dataset with licence recorded |
| OQ-122 | Tavily terms: may results and extracted page text be cached 7 days? Monthly credit confirmed? | DEP-010, `research_cache` policy | Lê Ngọc Tấn Hiền | 2026-12-08 | Record in `provider_policies` before first call |
| OQ-123 | Groq free-tier terms and data use | DEP-011, BR-046 | Lê Ngọc Tấn Hiền | 2026-12-08 | Read terms; same redaction as Gemini |
| OQ-124 | Google Places (New) field SKUs for `businessStatus`/`regularOpeningHours`; may lat/lng be cached ≤ 30 days (Service Specific Terms)? | Research check cost; `places_lookup_cache` | Lê Ngọc Tấn Hiền | 2026-12-08 | Minimal field masks; store only `place_id` canonically |
| OQ-125 | Lunar-calendar algorithm/library for VN (UTC+7), test vectors (Tết 2026-02-17, 2027-02-06), and the official Hội An lantern-night day (lunar 14th vs owner's "1st/15th") | DEC-016 calendar rules | Lê Ngọc Tấn Hiền | 2026-12-22 | Pure-Python algorithm with golden tests; verify on the Hội An heritage office site |
| OQ-126 | Agno exact version and Gemini/Groq model IDs to pin; embedding model (`gemini-embedding-001` at 768 dims vs `vector(768)`) | DEP-012, ADR-012 | Lê Ngọc Tấn Hiền | 2026-11-20 | Pin `agno==3.1.12` (spike 2026-11-06; re-run if a newer minor is chosen); keep `vector(768)`; live structured-output calls still to verify once API keys exist |
| OQ-127 | Threshold for "catalog pool is thin" that triggers research, and per-plan caps on Tavily/Places calls | DEC-015 | Lê Ngọc Tấn Hiền | 2026-12-08 | Set from SPK-004 numbers |
| OQ-128 | May `WEB_UNVERIFIED` stops appear in study sessions, and must the traveller acknowledge before saving a plan that contains one? | DEC-020 protocol, consent | Lê Ngọc Tấn Hiền (ask mentor) | 2027-01-06 | Yes with acknowledgement; it is the measured variable |
| OQ-129 | Hosting: AWS EC2+RDS (ADR-002) vs one VM with Docker Compose | DEC-018, M2 | Lê Ngọc Tấn Hiền | 2026-12-09 | Single VM for the study; ADR-002 stays default on paper |
| OQ-130 | ChatGPT/Gemini baseline protocol: accounts, model versions, prompt parity, ethics (OQ-004) | DEC-020, RESEARCH_PROTOCOL | Lê Ngọc Tấn Hiền (ask mentor) | 2027-01-06 | Same prompt text, pinned dates, screenshots archived |

## Contradictions resolved by this session

- C-010: SRC-003 `AGENTS.md` "Orchestration: no Agno/AgentOS" vs mentor allowing Agno → DEC-014.
- C-011: BRD §5.2 "Runtime web search — out of scope" and ADR-010 option D vs owner's research agent → DEC-015.
- C-012: BRD DEC-003 "never cut five cities" / BRU-007 / schema `cities` seed with a separate `hoi-an` row vs Đà Nẵng-only scope and the 2025 merger → DEC-013, DEC-019.
- C-013: BRU-002 "AI output may not create a place" vs web-found candidates → reworded: a model may *propose* a `WEB_UNVERIFIED` candidate for the curator queue; it may never publish a place or author a displayed fact (DEC-015).
- C-014: DEC-010 Tier 2 "roadmap" vs city-level Guide → DEC-017.

## Session close (2026-11-06)

All topics closed as decisions or carried as OQ/ASM with owners. Blocking for the M0 gate: mentor confirmation of DEC-013 (scope and gate change, SDP §4.6) and DEC-015 (web content in a trust-labelled product). Next steps: apply DEC-013..021 to governance files, BRD 1.0, PRD 1.0, design (ADR-013, ADR-014, revisions), verification and development plans in the same PR; run the day-1 Agno spike (ASM-021, OQ-126) in parallel.
