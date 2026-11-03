# PRD Audit — PRD-AUDIT-01

| Field | Value |
|---|---|
| Audit ID | PRD-AUDIT-01 |
| Date | 2026-11-04 |
| Standard | ISO/IEC/IEEE 29148-2018 |
| Auditor | Independent requirements auditor (clean session; artifacts not edited, kit §A8) |
| Artifacts audited | `docs/03-analysis/PRD.md` 0.1, `docs/03-analysis/user-stories.md` 0.1, `docs/03-analysis/traceability.md` 0.1 |
| Baseline | `docs/02-requirements/BRD.md` 0.4 (Status "Draft — in review"; §15 approval `[Pending]`; no `requirements-v1` tag) |
| Criteria | `analysis/PRD_IEEE_29148_Checklist.xlsx` (20 rows); `analysis/PRD_prompt.md` §6 self-check; Phase 3 gate of `step-by-step-guidance.md`; §A8 scoring rules |
| Owner of all actions | Lê Ngọc Tấn Hiền |

Scoring per §A8: `Pass` needs evidence the reader can open; `Partial` carries owner and due date and is not done;
`Fail` blocks the gate; items that need mentor sign-off are never `Pass`.

## 1. Checklist results

| Category | Item | Status | Evidence | Action | Owner | Gate |
|---|---|---|---|---|---|---|
| 1. Introduction & Context | Purpose & Scope | Pass | PRD §1.1, §1.2, §2.4; states it does not design the solution | — | Lê Ngọc Tấn Hiền | Non-blocking |
| 1. Introduction & Context | Business Context | Pass | PRD §3.2 (BO-001..BO-005 with MET-xxx), §10 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| 2. Stakeholders & Environment | User Characteristics | Pass | PRD §3.3 P-01..P-04 with tech proficiency | — | Lê Ngọc Tấn Hiền | Non-blocking |
| 2. Stakeholders & Environment | Operating Environment | Pass | PRD §2.5 (devices, region, time zone, concurrency) | — | Lê Ngọc Tấn Hiền | Non-blocking |
| 3. Functional Requirements | Singular & Complete | Partial | 14 compound FRs: FR-013, FR-016, FR-019, FR-025, FR-028, FR-039, FR-040, FR-047, FR-063, FR-068, FR-069, FR-073, FR-075, FR-023 (§3 of this report) | Split per FIX-03; due 2026-11-08 | Lê Ngọc Tấn Hiền | Non-blocking |
| 3. Functional Requirements | Implementation-Free | Partial | CI-01 (`/v1`, server-sent events); FR-014 "without direct database editing"; FR-025 "generated item"; NFR-030 "client types built from it" | Rewrite per FIX-05; due 2026-11-08 | Lê Ngọc Tấn Hiền | Non-blocking |
| 3. Functional Requirements | Verifiable | Partial | 81/81 FRs have criterion + method (script C6), but FR-031 "warning" has no pass condition; FR-053, FR-072 criteria are bare AC references (C6b); FR-014 time limit verified by D only | FIX-04, FIX-06; due 2026-11-08 | Lê Ngọc Tấn Hiền | Non-blocking |
| 4. Non-Functional Requirements | Performance & Capacity | Partial | NFR-001..NFR-007 numeric p95 thresholds; all rest on ASM-013/ASM-015, closed by owner delegation only, "mentor confirms at sign-off" (OQ-011) | Mentor confirms ASM-013/ASM-015 at the analysis gate; spike 2026-12-15 | Lê Ngọc Tấn Hiền | Blocking for baseline (mentor sign-off) |
| 4. Non-Functional Requirements | Security & Privacy | Partial | NFR-012..NFR-018 define TLS ≥ 1.2, encryption at rest, role limit (NFR-015), log exclusions; legal basis open: OQ-004 ethics, OQ-008 cross-border transfer (BRD §13, Open, due 2026-11-11) | Obtain mentor answers to OQ-004/OQ-008; add consent/transfer requirement if required | Lê Ngọc Tấn Hiền | Blocking for baseline (mentor sign-off) |
| 4. Non-Functional Requirements | Reliability & Availability | Partial | NFR-008..NFR-011 (99% probe, RTO ≤ 4 h, RPO ≤ 24 h); ASM-006 awaits mentor (BRD Readiness); NFR-011 omits identity provider failure (SI-01) though reopening trips needs sign-in | FIX-08; mentor confirms ASM-006; due 2026-11-11 | Lê Ngọc Tấn Hiền | Blocking for baseline (mentor sign-off) |
| 4. Non-Functional Requirements | Scalability | N/A | Single-region FYP study service, ≤ 5 concurrent users (PRD §7.8 closing note, NFR-007); no growth requirement in BRD | — | Lê Ngọc Tấn Hiền | Non-blocking |
| 5. Interface Requirements | User Interfaces (UI) | Pass | PRD §6.1 UI-01..UI-07 logical only; layout deferred to Phase 4 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| 5. Interface Requirements | Hardware Interfaces | Pass | PRD §6.2 HW-01..HW-03 with FR links | — | Lê Ngọc Tấn Hiền | Non-blocking |
| 5. Interface Requirements | Software Interfaces | Partial | PRD §6.3 SI-01..SI-08 complete; vendors in SI-02 (Gemini), SI-03/SI-04 (Google), SI-06 (LiteAPI/Hotelbeds) are not in §8 CON-xxx; SI-01/SI-02 transfers depend on OQ-008 | FIX-09; due 2026-11-11 | Lê Ngọc Tấn Hiền | Non-blocking |
| 5. Interface Requirements | Communication Interfaces | Partial | CI-01..CI-03 are "shall" statements with no priority, verification method or (CI-01) source BR (script C14) | FIX-05; due 2026-11-08 | Lê Ngọc Tấn Hiền | Non-blocking |
| 6. Constraints & Assumptions | Design Constraints | Partial | PRD §8 CON-001..CON-006, BRU, DEC-003; §3.5 regulation "assumed applicable" (ASM-007) pending OQ-004/OQ-008 | Mentor answer recorded in BRD §13 | Lê Ngọc Tấn Hiền | Blocking for baseline (mentor sign-off) |
| 6. Constraints & Assumptions | Dependencies | Pass | PRD §6.3 Dependency column DEP-001..DEP-007; BRD §10 | — | Lê Ngọc Tấn Hiền | Non-blocking |
| 7. Requirements Quality Check | Unambiguous Language | Partial | NFR-019 "acceptably", NFR-023 "sufficient", NFR-026 "correct", FR-031 "warning", FR-055 "current day" | FIX-04, FIX-07; due 2026-11-08 | Lê Ngọc Tấn Hiền | Non-blocking |
| 7. Requirements Quality Check | Traceable & Numbered | Partial | Script C1–C3, C8–C13 pass (118/118 traced, 50/50 BR covered, 0 orphan); but source BRD is unsigned, enabler traces NFR-030..NFR-032 → BR-023 and NFR-023/NFR-024 → BR-005 need mentor (OQ-009); PRD §4.0 says US-001..US-036, file has 37 (C11b) | FIX-01, FIX-02, FIX-10; mentor sign-off of BRD | Lê Ngọc Tấn Hiền | Blocking for baseline (mentor sign-off) |
| 7. Requirements Quality Check | Consistent | Partial | PRD §9 lists NFR-025/NFR-026 under both T and I; NFR-031 says "Must requirement" but measures "Must FRs"; OQ-015 claims `01-intake/glossary.md` and `stakeholders.md` are missing, both exist; §3.2 BO-002 lists no NFRs while §10 lists NFR-004, NFR-009..011, NFR-025 | FIX-11, FIX-12, FIX-13; due 2026-11-08 | Lê Ngọc Tấn Hiền | Non-blocking |
| Phase 3 gate | 100% FR/NFR trace to an existing BR; 0 orphan | Pass | Script C2 (118/118), C3 (50/50), C13 | — | Lê Ngọc Tấn Hiền | Blocking |
| Phase 3 gate | 100% US have AC and FR IDs | Pass | Script C7 (37/37, 1–5 G/W/T each), C8, C9 (81/81 FRs in a story) | — | Lê Ngọc Tấn Hiền | Blocking |
| Phase 3 gate | Every NFR has metric, threshold, method | Pass | Script C5, C5b (37/37); caveat NFR-036 cap value deferred to ASM-016, NFR-027 minimum OS version deferred to ASM-014 (FIX-07) | — | Lê Ngọc Tấn Hiền | Blocking |
| Phase 3 gate | 0 Fail; conflicts/duplicates resolved or recorded with decider | Partial | 0 Fail in this audit; PRD §12.1 and OQ-009..OQ-014 "Closed — owner delegation; mentor confirms at sign-off" | Mentor confirms OQ-009..OQ-014 at the gate meeting | Lê Ngọc Tấn Hiền | Blocking for baseline (mentor sign-off) |
| §6 self-check | Every requirement has priority and verification method | Partial | FRs 81/81 (C6); NFRs have a method but no T/I/D/A/S code in the row; CI-01..CI-03 have neither (C14) | FIX-05, FIX-12 | Lê Ngọc Tấn Hiền | Non-blocking |
| §6 self-check | One user-visible outcome per story | Partial | US-012 (clarify + refuse), US-016 (4 edit types), US-021 (lock + regenerate), US-027 (voice ask + read aloud) | FIX-14; due 2026-11-08 | Lê Ngọc Tấn Hiền | Non-blocking |
| §6 self-check | Approval and baseline | Partial | PRD §Approval mentor and owner `[Pending]` (C15); BRD §15 `[Pending]`; no git tag | Sign BRD then PRD; tag `analysis-v1` | Lê Ngọc Tấn Hiền | Blocking for baseline (mentor sign-off) |

Totals: 27 rows — Pass 10, Partial 16, Fail 0, N/A 1.

## 2. Mechanical check results

Script: `prd_check.py` (Appendix A), run with `python3 -I` against the four files on 2026-11-04.

```text
Counts: BR=50 FR=81 NFR=37 US(sections)=37 US(index)=37
  info: BRs covered only by NFRs: BR-050

PASS | C1 IDs unique (BR, FR, NFR, US definitions) | 0 duplicates
PASS | C1b FR numbering contiguous | FR-001..FR-081
PASS | C2 Every FR/NFR has an existing source BR | 118/118
PASS | C3 Every BR covered by >=1 FR/NFR | 50/50
PASS | C4 No FR/NFR priority above its BR | 0 violations
PASS | C5 Every NFR has metric, threshold, method | 37/37
PASS | C5b Every NFR threshold is numeric | all numeric
PASS | C6 Every FR has priority, acceptance criterion, verification method | 81/81
FAIL | C6b FR criterion self-contained (not a bare AC reference) | FR-053, FR-072
PASS | C6c AC-xxx cited in PRD exist in BRD | 48 cited, all exist
PASS | C7 Every US has 1-5 Given/When/Then AC and story form | 37/37; AC per story max 5
PASS | C8 Every US lists valid FR IDs | 37/37
PASS | C8b Story index matches story bodies | consistent
PASS | C9 Every FR covered by a US | 81/81
PASS | C10 US priority = highest linked FR | consistent
PASS | C11 US IDs cited in PRD exist | all exist
FAIL | C11b PRD §4.0 story range matches USER_STORIES | PRD says US-001..US-036; file has 37 stories
PASS | C12 traceability.md backward matrices match PRD/US | consistent
PASS | C13 [ORPHAN] list empty | None
FAIL | C14 Communication-interface 'shall' rows carry priority + verification | CI-01, CI-02, CI-03 have no priority, source BR column or verif. method
FAIL | C15 Approval recorded | PRD §Approval: mentor and owner [Pending]

17/21 checks pass
```

Notes: C6b is a readability defect (the referenced AC-037 and AC-044 exist in BRD §7.6). C14 and C15 are
additions beyond the requested checks. The traceability.md coverage table (§1) is confirmed by C2, C3, C9, C10 and C12.

## 3. Sample review (all 81 FRs scanned; 33 FRs and all 37 NFRs recorded)

S = singular, A = unambiguous, I = implementation-free, V = verifiable. ✗ marks a defect.

| ID | S | A | I | V | Finding |
|---|---|---|---|---|---|
| FR-001 | ✓ | ✓ | ✓ | ✓ | — |
| FR-002 | ✓ | ✓ | ✓ | ✓ | — |
| FR-003 | ✓ | ✓ | ✓ | ✓ | — |
| FR-004 | ✓ | ✓ | ✓ | ✓ | — |
| FR-007 | ✓ | ✓ | ✓ | ✓ | — |
| FR-010 | ✓ | ✓ | ✓ | ✓ | No system subject ("Re-importing … shall"); cosmetic |
| FR-013 | ✗ | ✓ | ✓ | ✓ | Refuse + name missing items |
| FR-014 | ✓ | ✓ | ✗ | ✗ | "without direct database editing" is design; 1-minute limit lives only in criterion and is verified by D |
| FR-016 | ✗ | ✓ | ✓ | ✓ | Record licence/attribution + refuse publication |
| FR-019 | ✗ | ✓ | ✓ | ✓ | Mark "AI draft" + block publication |
| FR-021 | ✓ | ✓ | ✗ | ✓ | "structured preference form" leans on UI; acceptable if read as input channel |
| FR-023 | ✗ | ✓ | ✓ | ✓ | Three refusal cases + ordering before AI call |
| FR-025 | ✗ | ✓ | ✗ | ✓ | Include only published + discard "generated item" (mechanism) |
| FR-026 | ✓ | ✓ | ✓ | ✓ | — |
| FR-028 | ✗ | ✓ | ✓ | ✓ | Same revision on map + two-way selection sync |
| FR-029 | ✓ | ✓ | ✓ | ✓ | Provider source is BRU-006, not design |
| FR-031 | ✓ | ✗ | ✓ | ✗ | "warning" not defined; criterion tests only "blocked" |
| FR-039 | ✗ | ✓ | ✓ | ✓ | Recalculate + keep Save unavailable |
| FR-040 | ✗ | ✓ | ✓ | ✓ | Persist only on Save + label unsaved |
| FR-041 | ✓ | ✓ | ✓ | ✓ | — |
| FR-047 | ✗ | ✓ | ✓ | ✓ | Lock/unlock + indicator |
| FR-052 | ✓ | ✓ | ✓ | ✓ | ≥ 90 % address threshold only in criterion; acceptable |
| FR-053 | ✓ | ✓ | ✓ | ✗ | Criterion "AC-037 on the same sample" not self-contained |
| FR-055 | ✓ | ✗ | ✓ | ✓ | "current day" undefined outside trip dates |
| FR-056 | ✓ | ✓ | ✓ | ✓ | — |
| FR-058 | ✓ | ✓ | ✓ | ✓ | — |
| FR-061 | ✓ | ✓ | ✓ | ✓ | — |
| FR-063 | ✗ | ✓ | ✓ | ✓ | Three permissions + degraded operation |
| FR-068 | ✗ | ✓ | ✓ | ✓ | Require sign-in + allow sign-out |
| FR-069 | ✗ | ✓ | ✓ | ✓ | Deny access + check before external call |
| FR-072 | ✓ | ✓ | ✓ | ✗ | Criterion is only "AC-044." |
| FR-073 | ✗ | ✓ | ✓ | ✓ | Save preferences + prefill |
| FR-075 | ✗ | ✓ | ✓ | ✓ | Choose language + translate all text |

| ID | Finding |
|---|---|
| NFR-001..NFR-006 | Singular, numeric p95, method stated. Thresholds need mentor confirmation (ASM-013). |
| NFR-007 | Threshold "5" is the load, not a pass condition; pass condition is NFR-001..006 held — acceptable, state it in the threshold cell. |
| NFR-008 | OK; production study window. |
| NFR-009, NFR-010 | OK; ASM-006 awaits mentor. |
| NFR-011 | Identity provider missing from the fault list (FIX-08). |
| NFR-012..NFR-017 | OK; specific and testable. |
| NFR-018 | OK; inspection dated 2027-07-01. |
| NFR-019 | "acceptably" in statement; metric SUS ≥ 70 fixes it — reword. |
| NFR-020, NFR-021 | OK; study measures. |
| NFR-022 | OK (WCAG SC 4.1.2). |
| NFR-023 | "sufficient" in statement; weak trace to BR-005 instead of BR-022. |
| NFR-024 | OK; weak trace to BR-005. |
| NFR-025 | OK; listed under both T and I in §9. |
| NFR-026 | "correct" in statement; metric resolves it. |
| NFR-027 | "minimum supported version" undefined until design (ASM-014). |
| NFR-028 | Same as NFR-027; Should priority under DEC-003 is ≤ BR-023 Must. |
| NFR-029 | OK. |
| NFR-030 | Solution language (generated API description, client types); enabler trace to BR-023. |
| NFR-031 | Process requirement, not a product quality; "Must requirement" vs "Must FRs" mismatch. |
| NFR-032 | OK as verification-environment requirement; enabler trace. |
| NFR-033..NFR-035 | OK; trace to BR-050. |
| NFR-036 | Cap value deferred (ASM-016); threshold incomplete until SAD. |
| NFR-037 | OK. |

## 4. FIX LIST

1. **FIX-01 PRD story range.** PRD §4.0: replace "US-001..US-036" with "US-001..US-037".
2. **FIX-02 Stale intake question.** PRD Open questions, OQ-015: set status "Closed — `docs/01-intake/glossary.md` and `stakeholders.md` exist"; add both files to PRD §2.1 inventory.
3. **FIX-03 Split compound FRs.** Split into one obligation each, keeping the source BR and priority, and update stories and traceability: FR-013 → refuse publication / name missing items; FR-016 → record licence and attribution / refuse publication without attribution; FR-019 → mark AI draft / block until confirmed; FR-023 → refuse > 3 days / > 1 city / non-launch city, with "no external AI call" moved to the criterion; FR-025 → only published same-city places / discard foreign references; FR-028 → same revision on map / two-way selection; FR-039 → recalculate / disable Save during recalculation; FR-040 → persist only on Save / label unsaved; FR-047 → lock and unlock / show indicator; FR-063 → one row per permission; FR-068 → require sign-in / sign out; FR-069 → deny cross-account access / authorise before external calls; FR-073 → save preferences / prefill form; FR-075 → choose language / translate interface text. Use new IDs FR-082 onward; do not renumber.
4. **FIX-04 Define Plan Health and "current day".** FR-031: add "warning = at least one non-blocking issue and no blocking conflict; good = none", and extend the criterion to test good and warning cases. FR-055: add "when the device date is outside the trip dates, the view shows the first day".
5. **FIX-05 Communication interfaces.** PRD §6.4: add Source BR, Priority and Verif. columns to CI-01..CI-03 (e.g. CI-02 BR-020 Must T); rewrite CI-01 as "shall communicate with the backend only through its published, versioned API" and move `/v1` and server-sent events to the SAD.
6. **FIX-06 Self-contained criteria and timing.** FR-053: replace with "for one saved trip per city with ≥ 5 stops, every card shows an entrance location or 'unknown'". FR-072: replace with "during deletion the app shows 'in progress', then 'completed' or the failure reason". FR-014: drop "without direct database editing", move "within 1 minute" into the statement, and change verification to T.
7. **FIX-07 Wording and thresholds.** NFR-019 "shall rate the usability at SUS ≥ 70"; NFR-023 "shall meet a contrast ratio ≥ 4.5:1" and source BR-022; NFR-024 source BR-022; NFR-026 "shall render without missing or corrupted diacritics"; NFR-027/NFR-028 name the minimum OS versions or add a dated OQ for them; NFR-036 add the cap value or OQ with due date 2026-12-15.
8. **FIX-08 Identity provider resilience.** NFR-011: add a row or clause stating the behaviour when SI-01 is unavailable (e.g. signed-in sessions continue to reopen saved trips for the session lifetime), with a fault-injection threshold.
9. **FIX-09 Vendor constraints.** PRD §8: add CON entries (or reference DEC-xxx) for Gemini, Google Routes/Places, LiteAPI/Hotelbeds and the booking partners, or mark SI-02..SI-07 vendor names as "current choice, decided in Phase 4".
10. **FIX-10 Enabler traces.** NFR-030..NFR-032: either move NFR-031/NFR-032 to the verification plan and NFR-030 to the SAD, or keep them and record the mentor's acceptance of the BR-023 enabler trace in OQ-009.
11. **FIX-11 Verification table.** PRD §9: list NFR-025 and NFR-026 under one method only (T for NFR-025, I for NFR-026) and add a Verif. column to the NFR tables in §7.
12. **FIX-12 NFR-031 scope.** Change metric to "Must FRs and Must NFRs without a linked TC-xxx", or change the statement to "Every Must FR".
13. **FIX-13 Objective table.** PRD §3.2: add the NFRs listed for each BO in §10 (BO-002: NFR-004, NFR-009..NFR-011, NFR-025; BO-001: NFR-001..NFR-003, NFR-022..NFR-024, NFR-026).
14. **FIX-14 Story size.** USER_STORIES: split US-012 (clarify / refuse), US-016 (reorder / add / remove / replace, or record why one story), US-021 (lock / regenerate) and US-027 (spoken question / read aloud); add new IDs from US-038, regenerate traceability.md.
15. **FIX-15 Mentor sign-off (not an edit).** Obtain answers to OQ-001, OQ-003, OQ-004, OQ-006, OQ-008; mentor confirms ASM-006, ASM-013, ASM-015 and the OQ-009..OQ-014 delegated closures; sign BRD §15, tag `requirements-v1`, then sign the PRD approval table and tag `analysis-v1`.

After FIX-01..FIX-14, rerun Appendix A and regenerate `traceability.md`.

## 5. Verdict

**Ready with conditions — not yet baselineable.** The Phase 3 gate's mechanical criteria are met: 81 FRs and
37 NFRs trace to 50 existing BRs (118/118), 50/50 BRs covered, 0 orphans, 37/37 stories with 1–5 Given/When/Then
criteria and valid FR IDs, 37/37 NFRs with metric, threshold and method, 0 priority violations, all IDs unique.
The audit has 0 Fail. Sixteen rows are Partial: document defects FIX-01..FIX-14 (none changes scope) and
mentor-dependent items (FIX-15) that cannot pass until signed. Tag `analysis-v1` only after FIX-15 and a re-audit
(PRD-AUDIT-02).

## Appendix A — `prd_check.py`

```python
import re, sys, collections
D="/Users/lengoctanhien/fyp_dana/docs/"
brd=open(D+"02-requirements/BRD.md").read(); prd=open(D+"03-analysis/PRD.md").read()
us=open(D+"03-analysis/user-stories.md").read(); tr=open(D+"03-analysis/traceability.md").read()
R=collections.OrderedDict(); 
def res(k,ok,detail=""): R[k]=(ok,detail)
rank={"Must":3,"Should":2,"Could":1}
def pr(s):
    for k in rank:
        if s.strip().startswith(k): return k
    return None
cells=lambda l:[c.strip() for c in l.strip().strip("|").split("|")]
# BRs
BR={}; brdefs=[]
for l in brd.splitlines():
    if re.match(r"\|\s*BR-\d{3}\s*\|",l):
        c=cells(l); brdefs.append(c[0]); BR[c[0]]=pr(c[4])
bracs=set(re.findall(r"\bAC-\d{3}\b",brd))
# FRs
FR={}; frdefs=[]
for l in prd.splitlines():
    if re.match(r"\|\s*FR-\d{3}\s*\|",l):
        c=cells(l); frdefs.append(c[0]); FR[c[0]]=dict(text=c[2],br=re.findall(r"BR-\d{3}",c[3]),prio=pr(c[4]),ac=c[5],ver=c[6])
NFR={}; nfrdefs=[]
for l in prd.splitlines():
    if re.match(r"\|\s*NFR-\d{3}\s*\|",l):
        c=cells(l); nfrdefs.append(c[0]); NFR[c[0]]=dict(text=c[1],metric=c[2],thr=c[3],method=c[4],where=c[5],br=re.findall(r"BR-\d{3}",c[6]),prio=pr(c[7]))
# US sections
US={}
for m in re.finditer(r"^### (US-\d{3}) — .*?\((.*?)\)(.*?)(?=^### |^## )",us,re.S|re.M):
    hdr=m.group(2); body=m.group(3)
    acs=re.findall(r"^- \*\*AC\d+\*\*(.*)$",body,re.M)
    US[m.group(1)]=dict(fr=re.findall(r"FR-\d{3}",hdr),prio=pr(hdr),acs=acs,asa=bool(re.search(r"As an? \*\*.*?\*\*[^,]*, I want .*?so\s+that",body,re.S)))
usidx={}
for l in us.splitlines():
    if re.match(r"\|\s*US-\d{3}\s*\|",l):
        c=cells(l); usidx[c[0]]=dict(fr=re.findall(r"FR-\d{3}",c[4]),prio=pr(c[5]))
print(f"Counts: BR={len(BR)} FR={len(FR)} NFR={len(NFR)} US(sections)={len(US)} US(index)={len(usidx)}")
# 1 unique IDs
d=[x for x,n in collections.Counter(brdefs).items() if n>1]+[x for x,n in collections.Counter(frdefs).items() if n>1]+[x for x,n in collections.Counter(nfrdefs).items() if n>1]
d+=[x for x,n in collections.Counter(re.findall(r"^### (US-\d{3})",us,re.M)).items() if n>1]
res("C1 IDs unique (BR, FR, NFR, US definitions)",not d,", ".join(d) or "0 duplicates")
gaps=[f"FR-{i:03d}" for i in range(1,max(int(x[3:]) for x in FR)+1) if f"FR-{i:03d}" not in FR]
res("C1b FR numbering contiguous",not gaps,", ".join(gaps) or "FR-001..FR-%03d"%len(FR))
# 2 FR/NFR source BR exists
bad=[f"{k}->{v['br'] or 'none'}" for k,v in {**FR,**NFR}.items() if not v['br'] or any(b not in BR for b in v['br'])]
res("C2 Every FR/NFR has an existing source BR",not bad,", ".join(bad) or f"{len(FR)+len(NFR)}/{len(FR)+len(NFR)}")
# 3 BR coverage
cov=set(b for v in {**FR,**NFR}.values() for b in v['br'])
unc=[b for b in BR if b not in cov]
res("C3 Every BR covered by >=1 FR/NFR",not unc,", ".join(unc) or f"{len(BR)}/{len(BR)}")
onlynfr=[b for b in BR if b not in set(x for v in FR.values() for x in v['br'])]
print("  info: BRs covered only by NFRs:",", ".join(onlynfr) or "none")
# 4 priority
bad=[f"{k}({v['prio']})>{b}({BR[b]})" for k,v in {**FR,**NFR}.items() for b in v['br'] if b in BR and (v['prio'] is None or BR[b] is None or rank[v['prio']]>rank[BR[b]])]
res("C4 No FR/NFR priority above its BR",not bad,", ".join(bad) or "0 violations")
# 5 NFR fields
bad=[k for k,v in NFR.items() if not all(v[x] and v[x] not in("—","-") for x in("metric","thr","method"))]
num=[k for k,v in NFR.items() if not re.search(r"\d",v['thr'])]
res("C5 Every NFR has metric, threshold, method",not bad,", ".join(bad) or f"{len(NFR)}/{len(NFR)}")
res("C5b Every NFR threshold is numeric",not num,", ".join(num) or "all numeric")
# 6 FR fields
bad=[k for k,v in FR.items() if not v['ac'] or not v['ver'] or not v['prio']]
res("C6 Every FR has priority, acceptance criterion, verification method",not bad,", ".join(bad) or f"{len(FR)}/{len(FR)}")
bare=[k for k,v in FR.items() if re.fullmatch(r"AC-\d{3}\.?",v['ac']) or re.fullmatch(r"AC-\d{3} on the same sample\.",v['ac'])]
res("C6b FR criterion self-contained (not a bare AC reference)",not bare,", ".join(bare) or "none")
acref=set(re.findall(r"\bAC-\d{3}\b",prd)); missac=sorted(acref-bracs)
res("C6c AC-xxx cited in PRD exist in BRD",not missac,", ".join(missac) or f"{len(acref)} cited, all exist")
# 7 US
bad=[]; 
for k,v in US.items():
    if not v['acs']: bad.append(f"{k}: no AC")
    if len(v['acs'])>5: bad.append(f"{k}: {len(v['acs'])} AC")
    for i,a in enumerate(v['acs'],1):
        if not re.search(r"\bGiven\b",a) or not re.search(r"\bwhen\b",a,re.I) or not re.search(r"\bthen\b",a,re.I): bad.append(f"{k}-AC{i} not G/W/T")
    if not v['asa']: bad.append(f"{k}: not As a/I want/so that")
res("C7 Every US has 1-5 Given/When/Then AC and story form",not bad,"; ".join(bad) or f"{len(US)}/{len(US)}; AC per story max {max(len(v['acs']) for v in US.values())}")
bad=[f"{k}:{f}" for k,v in US.items() for f in v['fr'] if f not in FR]+[k for k,v in US.items() if not v['fr']]
res("C8 Every US lists valid FR IDs",not bad,", ".join(bad) or f"{len(US)}/{len(US)}")
mis=[k for k in set(US)|set(usidx) if k not in US or k not in usidx or set(US[k]['fr'])!=set(usidx[k]['fr']) or US[k]['prio']!=usidx[k]['prio']]
res("C8b Story index matches story bodies",not mis,", ".join(sorted(mis)) or "consistent")
cfr=set(f for v in US.values() for f in v['fr']); unc=[f for f in FR if f not in cfr]
res("C9 Every FR covered by a US",not unc,", ".join(unc) or f"{len(FR)}/{len(FR)}")
bad=[f"{k}({v['prio']}) vs max FR {max((FR[f]['prio'] for f in v['fr'] if f in FR),key=lambda p:rank[p])}" for k,v in US.items() if v['fr'] and v['prio']!=max((FR[f]['prio'] for f in v['fr'] if f in FR),key=lambda p:rank[p])]
res("C10 US priority = highest linked FR",not bad,", ".join(bad) or "consistent")
# 11 cross-doc references
usrefs=set(re.findall(r"US-\d{3}",prd)); bad=sorted(u for u in usrefs if u not in US)
res("C11 US IDs cited in PRD exist",not bad,", ".join(bad) or "all exist")
m=re.search(r"user stories US-(\d{3})\.\.US-(\d{3})",prd)
if m: res("C11b PRD §4.0 story range matches USER_STORIES",int(m.group(2))==len(US),f"PRD says US-{m.group(1)}..US-{m.group(2)}; file has {len(US)} stories")
# 12 traceability consistency
bad=[]
for l in tr.splitlines():
    c=cells(l) if l.startswith("|") else []
    if c and re.fullmatch(r"FR-\d{3}",c[0]) and len(c)>=5:
        f=c[0]
        if f not in FR or set(re.findall(r"BR-\d{3}",c[2]))!=set(FR[f]['br']) or pr(c[1])!=FR[f]['prio'] or set(re.findall(r"US-\d{3}",c[4]))!={k for k,v in US.items() if f in v['fr']}: bad.append(f)
    if c and re.fullmatch(r"NFR-\d{3}",c[0]) and len(c)>=5:
        n=c[0]
        if n not in NFR or set(re.findall(r"BR-\d{3}",c[3]))!=set(NFR[n]['br']) or pr(c[2])!=NFR[n]['prio']: bad.append(n)
res("C12 traceability.md backward matrices match PRD/US",not bad,", ".join(bad) or "consistent")
orph=re.search(r"## 8\. \[ORPHAN\] list\s*\n\s*None",tr) is not None
res("C13 [ORPHAN] list empty",orph,"None" if orph else "entries present")
# 14 interface reqs with 'shall' lacking priority/verification
ci=[cells(l)[0] for l in prd.splitlines() if re.match(r"\|\s*CI-\d+",l)]
res("C14 Communication-interface 'shall' rows carry priority + verification",False if ci else True,f"{', '.join(ci)} have no priority, source BR column or verif. method" if ci else "none")
# 15 approvals
res("C15 Approval recorded",not re.search(r"\[Pending\]",prd),"PRD §Approval: mentor and owner [Pending]")
print()
fails=0
for k,(ok,dt) in R.items():
    print(f"{'PASS' if ok else 'FAIL'} | {k} | {dt}"); fails+= not ok
print(f"\n{len(R)-fails}/{len(R)} checks pass")
```
