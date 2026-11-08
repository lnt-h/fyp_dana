# Gonarra catalog — DATASET REBUILD spec (no AI-generated catalog data)

Status: executed 2026-11-09 · author: data-quality subagent
Owner direction (2026-11-09): catalog data must not be AI-generated. AI-summarised descriptions
(DEC-025, `translation_origin = AI_SUMMARY`) and AI-extracted facts (DEC-028, `origin = AI_EXTRACTED`)
are dropped. Rebuild the dataset "like a real app" from human-written, openly licensed sources.

**Result (2026-11-09):** `pipeline run` published **173 places, 63 in the Hội An area** (gate met: ≥ 100 / ≥ 30),
with 60 publishable FOOD/CAFE/MARKET places; 5 published areas carry `is_area` and are never planner stops;
21/173 places have both VI and EN human-written descriptions (descriptions optional, DEC-033 option A). The
baseline and yield figures below are the pre-run measurements that drove the spec, not the final counts.

---------------------------------------------------------------------------------------------------

## 0. Measured baseline (dev DB `gonarra`, 2026-11-09)

| Metric | Value |
|---|---|
| Published before this task | 110 (Hội An area 52) |
| Taken down in this task (`publish takedown`, retired) | 8: art-gallery, nha-tho-toc, chua-quan-the-am-2, non-nuoc-beach, quan-am, my-son-group-a, da-nang-bay, nha-bia |
| Published now | **102 (Hội An area 50)** |
| Of the 102, VI **and** EN description human-written (Wikipedia/Wikidata, `ORIGINAL`) | **31** (Hội An area 11). 8 of these are one-line Wikidata stubs ("bridge in Vietnam", "Beach in Da Nang") |
| One locale human, other AI | 2 |
| Both locales AI_SUMMARY | **69** (Hội An area 39) |
| Published facts: OPENING_HOURS KNOWN (OSM) | 7 / 102; ADDRESS_VI, ADMISSION_PRICE, ENTRANCE_LOCATION all UNKNOWN |
| Staged but **unpublished** AI facts (`import_records` `ai-facts:*`) | 58 records, 62 facts (32 ADDRESS_VI, 14 OPENING_HOURS, 16 ADMISSION_PRICE), all flagged STRONG. They would go live on the next `publish auto` (dry run: "would publish = 102"). **Do not run `publish auto` before step 2 below.** |
| Published places without Guide chunks | 71 / 102; city-scope chunks: 0 (55 PLACE chunks total) |
| en.wikivoyage listings matched to the 110 places (QID or name ≥ 0.8 within 400 m) | 18, of which 15 have content text (≥ 100 chars: 14); hours 1, price 3 |
| vi.wikivoyage | Đà Nẵng / Hội An / Mỹ Sơn pages use `{{địa điểm|tên=|địa chỉ=|điện thoại=}}` only: names and addresses, **no coordinates, no descriptions** — unusable for descriptions |
| vi.wikipedia exact-title probe on the 69 AI-described places | 10 hits, **4 wrong entities** (Hồ Chí Minh Museum → Hà Nội museum Q1055897; Chùa Linh Ứng ×2 → Bãi Bụt Q18277260; Bãi Cát Vàng → Paracel Islands Q274388). Usable new VI: ~5 (Pháp Lâm, Hải Tạng, Phước Lâm, Chiên Đàn, Khương Mỹ) |

**Consequence (must be decided, see §9):** from open human-written sources alone, a realistic
bilingual catalog is **~35–40 places, ~13–16 in the Hội An area**, far below MET-011 (≥ 100 / ≥ 30).
The VI side is the bottleneck: vi.wikivoyage has no listing text, and vi.wikipedia covers mainly
places that already have a QID. Wikivoyage helps EN only.

---------------------------------------------------------------------------------------------------

## 1. New decision required (facilitator to record; IDs are proposals)

* **DEC-030 — No AI-generated catalog content.** Supersedes DEC-025 (1)–(5) and DEC-028 in full.
  Keep the enum values `AI_SUMMARY` / `AI_EXTRACTED` in the schema for history (no destructive
  migration), but no published row may carry them. The `grounded_writer` stays for Guide answers
  and trip rationales only (ADR-010/014 unchanged); the `FACT_EXTRACT` and description profiles are
  removed. Revert the AGENTS.md implementation-rule text added by DEC-028 ("facts may be AI-extracted
  …") to "Models never author displayed descriptions or facts".
* **DEC-031 — Description is optional at the gate; the release gate counts "complete cards".** Choose one:
  * **(A, recommended)** MET-011 rev. 4: ≥ 100 published places with **both-locale names, category,
    area, location and ≥ 1 attributed source**; a description is shown when a human-written one
    exists, otherwise the card says "No description yet" / "Chưa có mô tả" (same "unknown stays
    unknown" principle). Separate reported metric: number of places with human-written VI+EN
    descriptions (target ≥ 60, reached through the owner sheet, §4.4).
  * **(B)** Keep descriptions mandatory and have the owner write VI+EN descriptions for ~65 places in
    the owner sheet (`licence = own-work`) — ~2 sentences each, ~6–8 owner-hours. Risk RSK-001.
  * Either way: no machine translation, no AI paraphrase (NFR-026 stated exception of DEC-025 withdrawn).
* **DEC-032 — Wikivoyage as a source (CC BY-SA 4.0)**, extends DEC-024. Attribution and share-alike
  as §3.4. Official tourism sites (danangfantasticity.com, hoianworldheritage.org.vn) are **link-only**
  fact sources (owner reads them and records facts in the sheet with the URL); their text is never
  copied (their terms were not verified as open — treat as all rights reserved).
* Mentor confirmation: OQ-133 becomes moot; add OQ for DEC-031 option.

---------------------------------------------------------------------------------------------------

## 2. Retire existing AI content (reversible, no data deletion)

Goal: after this step no published localization has `translation_origin = 'AI_SUMMARY'` and no
published fact has `origin = 'AI_EXTRACTED'`; turning it back on is a policy re-activation.

1. `apps/api/app/ingestion/cli.py` — add `policy deactivate <provider_key> --reason` next to
   `policy_activate` (sets `provider_policies.status` to the non-active value already used by
   default-deny; audit event `POLICY_CHANGE`).
2. `apps/api/app/curation/auto_publish.py:gather` — load `AI_SUMMARY_PROVIDER_KEY` and
   `AI_FACTS_PROVIDER_KEY` payloads **only if their provider policy is ACTIVE** (helper
   `_policy_active(session, key)`; reuse `app.ingestion.common.require_active_policy` semantics without raising).
   With both deactivated, `compose` falls back to human sources only.
3. `auto_publish.py:compose` — remove the branches that set `loc.short_description = ai_short` and
   `loc.description = ai_text` / `translation_origin = "AI_SUMMARY"` and the `ai = _sourced_fact(ai_facts, …)`
   fallback, **or** guard them behind a module constant `ALLOW_AI_CONTENT = False` (DEC-030). Prefer
   deletion plus the guard in `gather` (belt and braces).
4. `auto_publish.py:gate_reasons` — new hard rule `AI_CONTENT` (any localization with
   `translation_origin in ('AI_SUMMARY','AI_DRAFT')` or fact with `origin == 'AI_EXTRACTED'`) → reject.
   Remove `AI_SUMMARY_UNCITED` from `GATE_RULES` (unreachable).
5. Operator run (after deploy of 1–4):
   ```sh
   cd apps/api
   docker compose exec -T db pg_dump -U gonarra -Fc gonarra > <backup>.dump
   uv run python -m app.cli policy deactivate gonarra_ai_summary --reason "DEC-030"
   uv run python -m app.cli policy deactivate gonarra_ai_facts   --reason "DEC-030"
   uv run python -m app.cli publish auto --dry-run -v   # expect withdrawn_by_gate ≈ 69 under DEC-031(B); ≈ 0 under (A)
   uv run python -m app.cli publish auto
   ```
   Places that lose their only description are **withdrawn by the gate** (`auto-gate: …`), not retired,
   so they come back automatically once a human description exists. Import records stay (audit trail).
6. CLI removal: `apps/api/app/cli.py` — delete `enrich descriptions` and `enrich facts` commands
   (`enrich_descriptions_command`, the facts command) and their policy seeds (lines ~257–281);
   delete or quarantine `app/research/enrich.py`, `app/research/fact_extract.py`,
   `app/agents/fact_validation.py`, the description/FACT_EXTRACT profiles in `app/agents/writer.py`
   and their schemas in `app/agents/schemas.py`; drop their tests. (Other agents currently edit
   `app/agents/schemas.py` — coordinate.)
7. No migration needed. Optional migration `20261110_0010_no_ai_catalog.py`: a CHECK-free trigger is
   **not** recommended; the gate rule is the control. Keep enum values for history.

Verification query (must return 0 / 0):
```sql
SELECT count(*) FROM catalog_publications cp JOIN place_localizations l
  ON l.id IN (cp.localization_vi_id, cp.localization_en_id)
 WHERE cp.state='PUBLISHED' AND l.translation_origin <> 'ORIGINAL';
SELECT count(*) FROM publication_facts pf JOIN place_facts f ON f.id = pf.place_fact_id
  JOIN catalog_publications cp ON cp.id = pf.publication_id
 WHERE cp.state='PUBLISHED' AND f.origin = 'AI_EXTRACTED';
```
(adjust column names to the actual `publication_facts` FK names.)

---------------------------------------------------------------------------------------------------

## 3. Wikivoyage listings importer (new)

### 3.1 Module and CLI
* New `apps/api/app/ingestion/wikivoyage.py` (pattern: `osm.py` / `wikipedia.py`):
  `PROVIDER_KEY = "wikivoyage"`, `IMPORTER_VERSION = "wv-1"`, `LICENSE_CODE = "CC-BY-SA-4.0"`.
  * `PAGES: dict[str, tuple[str, ...]] = {"en": ("Da Nang", "Hoi An", "My Son", "Chàm Islands", "Tam Kỳ"), "vi": ("Đà Nẵng", "Hội An", "Thánh địa Mỹ Sơn")}` (titles verified 2026-11-09; "Marble Mountains", "Ba Na Hills", "Son Tra", "Hai Van Pass" have **no** en.wikivoyage page — they are listings inside "Da Nang").
  * `async def fetch_page(client, lang, title) -> WikivoyagePage` — MediaWiki API
    `action=parse&prop=wikitext|revid&redirects=1&format=json&formatversion=2`, descriptive
    User-Agent, `maxlag=5`, **≥ 5 s between requests and retry with back-off on HTTP 429 / "too many
    requests" body** (observed rate-limiting on the 11th rapid request).
  * `def parse_listings(wikitext) -> list[Listing]` — brace-depth-aware template parser for
    `see|do|eat|drink|buy|listing` (skip `sleep|go|marker|city`), params `name, alt, address, lat, long,
    hours, price, content, url, wikidata, wikipedia, lastedit`, plus the section heading. vi:
    `{{địa điểm|tên=|địa chỉ=}}` → name/address only (no text, no coords; used only as an alias/address
    hint when matched by name to an existing place in the same page's city).
  * `def wikitext_to_plain(text) -> str` — strip `[[a|b]]`→b, `''`/`'''`, `{{…}}`, refs, HTML; collapse spaces.
  * `def category_for(listing) -> str | None` — see/do → from name keywords + matched OSM/Wikidata
    category; eat → FOOD; drink → CAFE if name/content matches `caf|coffee|cà phê|tea` else NIGHTLIFE;
    buy → MARKET only if name matches `market|chợ|night market` (tailors, banks, supermarkets,
    "Big C", "Lotte Mart", "MM Mega Market" are skipped — not stops); "village|làng" → CRAFT_VILLAGE.
  * `async def stage_listings(session, pages) -> WikivoyageReport` — matching order:
    (1) listing `wikidata=Q…` → existing place with that QID identity; (2) same normalised name
    (diacritic-folded, generic words stripped — reuse `app.ingestion.wikidata_link.match_key`) within
    the category radius of §4.1; (3) otherwise **new IMPORTED draft only if** lat/long present, inside
    the city boundary, category mapped and `content` ≥ 60 chars. Upstream id
    `"{lang}:{page}#{normalised name}"`; one `source_revisions` row per page revid
    (locator `https://{lang}.wikivoyage.org/w/index.php?title=…&oldid=<revid>`).
  * Payload: `name.en` (listing name with wiki markup stripped), `alt` as alias (often the VI name —
    e.g. "Chợ Đêm Sơn Trà", "Bãi biển Mỹ Khê"; store as `aliases.vi` **and** use as VI name only when
    it contains Vietnamese diacritics), `description.en = wikitext_to_plain(content)` verbatim,
    `facts`: OPENING_HOURS via `app.ingestion.osm.parse_osm_opening_hours`-compatible subset (else
    UNKNOWN), ADMISSION_PRICE `{"text": price}` only for see/do, ADDRESS_VI only from vi listings or
    when the `address` contains Vietnamese diacritics. **Facts are dropped when `lastedit` is missing or
    older than 2023-01-01** (prices like "US$1 (Jan 2018)" are stale); the description is kept.
* CLI: `apps/api/app/ingestion/cli.py` — `@ingest_app.command("wikivoyage")` `ingest_wikivoyage(--city-chunks/--no-city-chunks, --dry-run)`;
  add to `pipeline_run` after `ingest wikipedia`.
* Seeds: `apps/api/app/cli.py:seed_reference_data` — data provider `wikivoyage` (OPEN_DATASET) and a
  provider policy (default deny; owner activates: `policy activate wikivoyage --terms-version "CC BY-SA 4.0 checked 2026-11-xx"`).

### 3.2 City-level Guide chunks
`stage_listings` also stages sections `Understand`, `Get around`, `Stay safe`, `Respect`/`Cope`
(en "Da Nang", "Hoi An") as `knowledge_chunks` with `scope = 'CITY'`, `place_id = NULL`,
`section` = heading, split ≤ 1 200 chars, source revision = page revid. Approved by the gate step
`auto_publish._process` equivalent for city chunks (new `publish city-chunks` or inside `publish auto`).

### 3.3 Expected yield (measured 2026-11-09)
* Matches to existing places: 18 (content on 15). New EN descriptions for currently-AI places:
  tan-ky, nha-co-phung-hung, quan-cong-mieu, linh-ung-pagoda (replaces stub), my-khe-beach (replaces
  stub), hai-van-pass, son-tra-mountain ("Motorbike ride up Monkey Mountain"), bai-tam-non-nuoc-2,
  thap-khuong-my, hoi-an-museum ("Museum of Hoi An History and Culture"), hoi-quan-phuc-kien
  ("Phuc Kien Meeting Hall", 43 chars — too short).
* New drafts with text and coordinates: **FOOD (eat) 46** (Da Nang 27, Hội An 19), **drink 21**
  (cafés + bars), **MARKET**: Han Market, Son Tra Night Market, Helio Night Market, Hội An Central
  Market (both "buy" and "eat" listing), Hội An Night Market, Morning Market, Textile Market;
  **CRAFT_VILLAGE**: Thanh Ha pottery village (no coords → match to OSM/Wikidata), Hoi An Silk Village.
  Not on Wikivoyage: Làng rau Trà Quế, Làng mộc Kim Bồng → owner sheet / Wikidata.

### 3.4 Licence obligations (store per source revision; show in app)
| Source | Licence | Obligation |
|---|---|---|
| Wikivoyage text | CC BY-SA 4.0 | Attribution "Wikivoyage contributors, '<page>'" + link to page (history link satisfies author attribution per Wikivoyage reuse guide); indicate changes ("markup removed"); **share-alike**: our adapted description text stays CC BY-SA 4.0 (show licence link on the place screen) |
| Wikipedia lead extract | CC BY-SA 4.0 | Same; verbatim, no AI rewrite |
| Wikidata | CC0 | None required (credit as courtesy) |
| OSM tags | ODbL 1.0 | "© OpenStreetMap contributors" + link; derived database share-alike if redistributed as a DB |
| Commons photos | per file | Existing DEC-024 (2) rules |
| Official tourism sites | not open | Link only; owner-entered facts cite the URL |
| Google Places | ToS | Runtime only (ADR-006), `place_id` stored, never content |

---------------------------------------------------------------------------------------------------

## 4. Composition and gate rules (`apps/api/app/curation/auto_publish.py`)

### 4.1 Description and short-description priority (`compose`)
Per locale, independently, never translated:
1. owner sheet `description` / `short_description` (human, `own-work`);
2. **Wikivoyage listing `content`** (EN; VI never available today);
3. **Wikipedia lead extract** — only when the article is reached through the place's own QID
   sitelink (`wikibase_item` == place QID), never by title search;
4. none → description NULL (DEC-031 A) / gate rejects (DEC-031 B).
Wikidata `description` is allowed **only as `short_description`**, never as `description`
(today 8 published places show "bridge in Vietnam" etc. as their whole description).
`translation_origin` stays `ORIGINAL` for all of these.

### 4.2 New gate rules (add to `GATE_RULES` + `gate_reasons`; deterministic, unit-tested)
| Code | Rule | Data needed |
|---|---|---|
| `AI_CONTENT` | §2.4 | — |
| `DUPLICATE_OF:<slug>` | another candidate/published place of a compatible category within the radius and `name_similarity ≥ 0.85` (folded, generic words stripped), or same QID / same OSM element. Radius: FOOD/CAFE/NIGHTLIFE 75 m, MARKET/MUSEUM/RELIGIOUS_SITE/HERITAGE/VIEWPOINT 150 m, THEME_PARK 400 m, BEACH/NATURE/CRAFT_VILLAGE 2 000 m. Keeper = has QID > has VI name with diacritics > more sources > older `created_at`. (Would have caught non-nuoc-beach ↔ bai-tam-non-nuoc-2, 1.8 km; the pool has ba-duong ↔ ba-duong-2 and 3× "Mì Quảng Bà Mua".) | new helper `app/curation/dedupe.py:find_duplicate(desired, others)` |
| `PART_OF:<slug>` | Wikidata P361 (part of) of this place's QID equals another catalog place's QID, or the parent's P527 contains it; **or** no QID and the point lies within 120 m of a published place whose category is RELIGIOUS_SITE/HERITAGE/THEME_PARK and whose QID's P527/P361 graph links it, or the OSM element sits inside the parent's polygon (`amenity=place_of_worship`/`historic=*`/`tourism=theme_park`). The child is folded into the parent as an alias/highlight, not a stop. (Would have caught quan-am, my-son-group-a, nha-bia; still-pending drafts my-son-groups-b-c-and-d, -e-and-f, -g, tuong-phat-quan-am-chua-my-khe.) Exception: the parent is an **area** (§ AREA) — children stay stops. | `app/ingestion/wikidata.py:build_query` add `?part_of` (P361) and `?has_part` (P527) to the SPARQL; OSM: keep polygon membership (`out center` loses it — add `is_in`-style check via a second Overpass call or store way geometry bbox) |
| `GENERIC_NAME:<locale>` | name (folded, lower) equals a category word or matches the list `{nhà thờ tộc, nhà thờ, chùa, đình, miếu, lăng, nhà bia, quan âm, tượng phật, art gallery, gallery, museum, bảo tàng, café, cafe, coffee, restaurant, nhà hàng, quán ăn, chợ, market, bãi biển, beach, park, công viên, produce, fruits and vegetables}` with nothing else, or the NSI generic regexes (`^(fixme|n/a|no ?name|none|null|unknown|test)$`). Exempt when the place has a non-class QID (iD validator behaviour). | `app/curation/names.py:is_generic_name(name, locale)` |
| `VI_NAME_NOT_VIETNAMESE` | VI name has no Vietnamese diacritic **and** is not in a brand/proper-noun allow-list, or VI name == EN name in Latin without diacritics while an `alt`/alias with diacritics exists (then use the alias). Catches "Tan Ky", "Diep Dong Nguyen", "Ngoc Cam", "Thanh That Cao Dai", "Thanh That Hoi An", "Cua Dai", "Military blockhouse ruins", "Y Pha Nho cemetery …". Brand names (Art in Paradise, Hoi An Memories Land, Mini-Golf Hoi An, CSO Gallery) go in `app/curation/names.py:LATIN_BRAND_ALLOWLIST` (owner-maintained). | `names.py` |
| `NAME_FORMAT:<locale>` | name contains an address tail (`, <ward>, <town>` — e.g. "Miếu bà chúa Ngọc, Trà Quế, Cẩm Hà, Hội An"), starts lower-case ("nghĩa trang liệt sĩ …"), or has a non-Latin/Vietnamese script ("Пицца,бургер …"). Auto-fix allowed in code: strip the trailing address segment when the remaining name is non-generic; title-case the first letter. | `names.py:normalise_display_name` |
| `AREA_NOT_SCHEDULABLE` | category NATURE/HERITAGE and source tags/class say area: Wikidata P31 ∈ {bay, gulf, peninsula, island group, mountain range, historic district, old town, city district} or OSM `place=*`, `natural=bay|peninsula|water`, `boundary=*`, `landuse=*`, polygon area > 50 ha without an `entrance`/`routing:entrance` node. Not a rejection: set new column `places.is_area = true` → published for map/Guide, excluded from planner pools (`apps/api/app/planning/pool.py`), never a timeline stop. Applies to hoi-an-ancient-town, ngu-hanh-son, son-tra-mountain, cham-islands, ba-na-hills (resort; keep schedulable only if an entrance is known), hai-van-pass (keep as a "drive" stop — owner decides). Point-in-water (`ST_Intersects` with OSM water / coastline buffer) → reject outright (da-nang-bay case). | migration `20261110_0010_place_is_area.py` (`places.is_area boolean not null default false`, also on `catalog_publications`); OpenAPI `Place.is_area`; `planning/pool.py` filter |
| `DESCRIPTION_IDENTITY:<locale>` | the description's source must belong to **this** place: Wikipedia via own QID sitelink; Wikivoyage listing matched by QID or (name ≥ 0.85 and distance ≤ radius); sheet row of the place. Additionally reject when the description text names a different catalog place's VI/EN name and not this place's own name/aliases (cheap string check — would have caught art-gallery → "Art In Paradise", nha-tho-toc → "Nhà thờ tộc Trần", chua-quan-the-am-2 → "quận Ngũ Hành Sơn" ~20 km away, precious-heritage EN → biography of Réhahn). | `auto_publish.py:gate_reasons` + helper `app/curation/identity.py:description_mentions_other_place` |
| `DESCRIPTION_TOO_SHORT:<locale>` | description < 80 chars (Wikidata stubs) → treat as absent | — |
| `LOCATION_IMPLAUSIBLE` | text address district (e.g. "quận Ngũ Hành Sơn", "Sơn Trà") contradicts the area of the point (areas yaml) | optional, P2 |
| `NOT_A_STOP` | OSM tags `tourism=hotel`/`building=hotel` on the element or parent, `shop=supermarket|mall` for MARKET (malls are not markets), name matches `hotel|resort|bất động sản|ngân hàng|bank|tailor` | `categories.py:map_osm_tags` + gate |

Precious Heritage Art Gallery Museum (Q30744118) EN sitelink describes the person Réhahn: the QID
sitelink check passes but the EN article's own P31 is human (Q5) → add rule: Wikipedia extract
accepted only when the article's `wikibase_item` == place QID (not via a redirect to another item).

### 4.3 Disambiguation of shared names (display only)
Three real, distinct pagodas share "Chùa Linh Ứng / Linh Ung Pagoda" (Bãi Bụt – Sơn Trà; Non Nước –
Ngũ Hành Sơn; Bà Nà). Not duplicates. Rule in `compose`: when ≥ 2 published places share a name in a
locale, append the area short name: "Chùa Linh Ứng (Bãi Bụt)", "Linh Ung Pagoda (Marble Mountains)",
"Linh Ung Pagoda (Ba Na Hills)" — from `areas/da-nang.yaml` `name_vi/name_en` or an owner alias.
No translation is produced; area names are owner-maintained.

### 4.4 Owner sheet as the main VI source
`data/sheet/da-nang.csv` (existing importer `app/ingestion/sheet.py`) gets the VI+EN descriptions
the owner writes, `licence = own-work`, `source_kind = OWN_OBSERVATION`, `wikidata_id` or a new
optional column **`osm_id`** (e.g. `way/595299310`) so a row enriches the existing OSM place instead of
creating a duplicate (today only `wikidata_id` links; add `osm_id` matching in
`sheet.py` → `place_for_identity(provider openstreetmap, osm_id)`). Also used to fix names (§4.2
VI_NAME rules) — `name_vi` from the sheet wins.

---------------------------------------------------------------------------------------------------

## 5. Facts: sources and provenance (no AI)

| Field | Sources (priority) |
|---|---|
| OPENING_HOURS | owner sheet > OSM `opening_hours` (existing parser subset) > Wikivoyage `hours` (lastedit ≥ 2023, same parser) |
| ADMISSION_PRICE | owner sheet (from official site, URL recorded) > Wikivoyage `price` for see/do (lastedit ≥ 2023) > OSM `fee=no` → `{"free": true}` / `charge=*` |
| ADDRESS_VI | owner sheet > OSM `addr:housenumber`+`addr:street`(+`addr:subdistrict`) composed in code > Wikidata P6375 (vi) > vi.wikivoyage `địa chỉ` |
| ENTRANCE_LOCATION | owner sheet > OSM `entrance=main` / `routing:entrance` node of the polygon (new Overpass query by element id) |
| website (link only, not a fact) | OSM `website`/`contact:website`, Wikidata P856 |

Every KNOWN fact keeps one `fact_evidence` row to its source revision (existing
`FACT_WITHOUT_SOURCE` gate). `origin` = `SOURCE` or `OWNER` only.
`apps/api/app/ingestion/osm.py:build_query`/payload: also keep `addr:*`, `fee`, `charge`,
`website`, `cuisine`, `brand:wikidata`, `wikidata`, `name:vi`, `name:en`, `alt_name`.

(Former Part D (2), only relevant if AI extraction is ever revived: every number in an extracted
hours/price value must occur in the cited quote **and** the quote must occur (overlap ≥ 0.9) in the
evidence text; overlap < 0.2 drops the field instead of flagging WEAK — `app/agents/fact_validation.py:grounding`.
Today all 62 staged facts are "STRONG" yet art-gallery's address was another venue's, so quote
overlap alone does not prove identity.)

---------------------------------------------------------------------------------------------------

## 6. FOOD / CAFE / MARKET / CRAFT_VILLAGE / NIGHTLIFE coverage

### 6.1 Importer changes
* `app/ingestion/osm.py:SELECTORS` add `["amenity"~"^(bar|pub|nightclub)$"]`, `["craft"]`,
  `["place"~"^(village|hamlet)$"]["tourism"]`, `["tourism"="attraction"]["craft"]`.
* `app/ingestion/categories.py:OSM_PRIMARY_TAGS` add `("amenity","bar")→NIGHTLIFE`,
  `("amenity","pub")→NIGHTLIFE`, `("amenity","nightclub")→NIGHTLIFE`; remove `("shop","mall")→MARKET`
  (AEON Mall, Lotte Mart, GO!, MM Mega Market are not travel markets).
* Chains: skip when `brand:wikidata` is present or the name matches the chain list (Highlands,
  Starbucks, Trung Nguyên, Phúc Long, KFC, Lotteria, Jollibee, Pizza 4P's, The Coffee House, Katinat,
  Cộng Cà Phê — Cộng is a chain but iconic; owner allow-list) — `osm.py:_is_chain`.
* Quality score before staging FOOD/CAFE/NIGHTLIFE (`osm.py`, replaces the sparse filter):
  `wikidata +2, website +1, opening_hours +1, name:en or alt +1, VI name with diacritics +1, Wikivoyage
  listing match +3`; stage when ≥ 3; MARKET/CRAFT_VILLAGE when ≥ 1. Publishing still needs §4 rules.
* Wikidata (`app/ingestion/wikidata.py:build_query` / `categories.py:CLASS_LABEL_CATEGORY`): add
  classes "craft village"/"làng nghề", "traditional craft village", "marketplace", "night market".
  The QIDs of Làng gốm Thanh Hà, Làng rau Trà Quế, Làng mộc Kim Bồng were **not verified** here —
  look them up by label (`SELECT ?i WHERE { ?i rdfs:label "Làng gốm Thanh Hà"@vi }`) before adding to the sheet. vi.wikipedia has no article under the exact titles "Làng gốm Thanh Hà", "Làng rau Trà Quế", "Làng mộc Kim Bồng", "Chợ Hội An" (checked 2026-11-09).

### 6.2 Target list (≥ 20 high-quality; ids are `places.id` already in the IMPORTED pool)
Markets (all currently blocked only by `MISSING_DESCRIPTION`):

| slug | id | VI / EN | human text available |
|---|---|---|---|
| cho-han | 2ede3719-91b8-46a4-b793-a900a0a91f54 | Chợ Hàn / Han Market | Wikivoyage EN (482 chars, hours 06:00-21:00); vi.wikipedia "Chợ Hàn" = Q97163247 (verified 2026-11-09; pool record has no wikidata tag → `ingest wikidata-link` or sheet `wikidata_id`) |
| cho-con | bf4e96a9-9eaf-48bb-9a9c-b24f53f53a4b | Chợ Cồn / Con Market | vi.wikipedia "Chợ Cồn" = Q10748770 (verified); EN: owner |
| cho-hoi-an | 956805bf-0dfa-43a5-b736-1b999c3850f0 | Chợ Hội An / Hoi An Market | Wikivoyage EN ("Central Market", 275 chars) |
| cho-dem | a3094fc5-200a-4613-a8bc-4efa4b72f9c1 | Chợ Đêm / Night Market (Hội An) | Wikivoyage EN (76 chars — owner extends); rename VI "Chợ đêm Hội An" via sheet |
| cho-dem-son-tra | f6889fce-93e0-4ce4-87b4-e0743b3e6233 | Chợ Đêm Sơn Trà / Son Tra Night Market | Wikivoyage EN (90 chars) |
| cho-vai-hoi-an | 87a5b856-4ec7-40cb-b9d9-1d852e0b257d | Chợ vải Hội An / Hoi An Textile Market | Wikivoyage lists, no text → owner |
| cho-ba-le | 2d402131-ad9f-426e-9092-ff142fde2e33 | Chợ Bà Lê / Ba Le Market | owner |
| cho-cam-pho | e49ab78e-1c63-4d70-b57e-6b67a42f841e | Chợ Cẩm Phô | owner (low priority) |
| (new from Wikivoyage) | — | Helio Night Market / Chợ đêm Helio | Wikivoyage EN 115 chars |

Food (pool ids; Wikivoyage EN text where noted):

| slug | id | note |
|---|---|---|
| mi-quang-1a | f9ce2c4e-b4b5-4b3e-a939-84d34f660bcc | Wikivoyage "Mi Quang 1A" 354 chars, hours |
| quan-an-ngon-thia-go-danang-style | 32a5b7c2-95eb-475b-b56c-b2fd60bb8887 | Wikivoyage "Thìa Gỗ Restaurant" |
| banh-mi-phuong | b887b7c7-a356-4a5a-b3dc-0205f31b895f | iconic; owner text (not on WV) |
| bong-hong-trang | cd9c3fc7-0a22-4b24-988e-e272337ffe8b | White Rose — Wikivoyage 78 chars |
| vegetarian-vegan-chay-resturant | 78784194-fcd7-4ea2-ad7a-d2a6c15bde3b | = "Ba Dam Vegetarian" on Wikivoyage; fix VI name |
| morning-glory | 83ae6f2e-ca7d-4df8-9611-ff9311bc7227 | owner |
| pho-xua | 7141e886-674b-4395-b6f7-39f78bdedf2a | website + hours |
| mi-quang-ba-mua | bed8fe8b-55e7-4cc9-b116-1700aa4dbb4e | **dedupe** with my-quang-ba-mua 875b313a-… and my-quang-da-nang-ba-mua 907ec29f-… (check distances; chain of branches) |
| ba-duong-2 | 3065cb1a-735f-4738-8d47-967f0f483cbd | Bánh xèo Bà Dưỡng; **dedupe** with ba-duong 3df05875-… (keep -2: diacritics + hours) |
| com-ga-tran-tong | cd590d5e-32b7-4a85-825c-cf2e0bc8f916 | hours |
| bun-cha-ca-109 | b3152f3e-7414-4d50-a7b8-f6bca2e1d8aa | name:en |
| quan-chay-an-lac | bb6858b2-100d-41d4-9ca4-d4b312a452cf | VI typo "Quản" → "Quán" via sheet |
| (new from Wikivoyage, Hội An) | — | Madam Khanh – The Banh Mi Queen, Cao lầu Không Gian Xanh, Thiên Bảo Quán, Bale Well, Phở Tùng, Quán Cô Mai, Red Bridge Restaurant & Cooking School, Madam Kieu |
| (new from Wikivoyage, Đà Nẵng) | — | Bún Mắm Vân, Quán Dung Mỳ Quảng (802 chars), Com Nieu Nha Do (562), Memory Lounge, Cơm Nhà Linh, Bún mắm Bé Hà, Quán Thảo |

Cafés: hop-dua e0b68d2d-4f56-49c4-adc8-7841c91d7945, tiem-banh-meraki 33c03ca3-67c3-44da-925e-c5e98aac912c,
nghe-coffee-hoi-an 5924b94a-b213-47ee-a4be-f6bf47980afb, hoi-an-roastery 0a5fcf54-f72f-4147-b8be-5ed83e75bc7c,
rosie-s-cafe 5d57232d-129d-444f-a557-7f81190cca06 (Wikivoyage 265 chars), reaching-out-teahouse
e4d89b0e-d9b4-4479-91de-1fc9be0ba232, cong-ca-phe-2 161bcbee-a3ad-4fe0-affe-1fd4d323539b;
Wikivoyage Đà Nẵng drink: Long Coffee (335), Hai Quynh Café (235), Ca Fe 49 (228).
**Noise to exclude** (scored high but not stops): san-giao-dich-bat-dong-san-dat-lanh (real-estate
office), phu-kien-09 (accessories shop as MARKET), bricksstone (Cyrillic name), produce,
fruits-and-vegetables (generic), mm-mega-market-da-nang / aeon-mall-da-nang / lotte-mart / sieu-thi-go (malls).

Craft villages (not in the pool; need ingestion): Làng gốm Thanh Hà (Wikivoyage "Thanh Ha pottery
village", 543 chars, no coords → match OSM/Wikidata), Làng rau Trà Quế, Làng mộc Kim Bồng, Hoi An
Silk Village (Wikivoyage, coords + hours). Nightlife: Wikivoyage Hội An BB Lounge, Dive Bar; Đà Nẵng
Golden Pine, Bamboo Bar 2 (check `lastedit`).

---------------------------------------------------------------------------------------------------

## 7. Guide chunks
* Place chunks come from the same human texts: Wikipedia extract (existing) **plus Wikivoyage
  listing content** (new: `wikivoyage.py` stages a PLACE chunk per matched listing, section `OVERVIEW`
  or `TIPS`). No chunk from AI text (today none are — `AI summaries are not Guide chunks`).
* City chunks: §3.2. Expected ≈ 30–50 CITY chunks (EN) from "Da Nang" + "Hoi An" pages; VI city
  chunks from vi.wikivoyage "Đà Nẵng"/"Hội An" prose sections (Hiểu, Đi lại, An toàn) ≈ 10–20.
* Embedding: `GEMINI_EMBED` cap 1 000/day (ledger). Expected ≤ 250 embeddings for the whole rebuild —
  one run. Command: `uv run python -m app.cli publish auto` (embeds on publish) or the existing backfill.
* With 71/102 places lacking chunks, Guide answers for those places fall back to card fields +
  `insufficient_evidence`; that is acceptable and honest.

---------------------------------------------------------------------------------------------------

## 8. Retention sweep (ADR-006)
New CLI `apps/api/app/cli.py` → `cache sweep [--dry-run]` (module `app/providers/retention.py:sweep`):
* `research_cache`: `DELETE WHERE expires_at < now()` (571 rows now, 0 expired, TTL ≤ 7 d).
* `places_lookup_cache`: `UPDATE SET location = NULL, location_expires_at = NULL WHERE location_expires_at < now()`;
  `DELETE WHERE outcome_expires_at < now()` (0 rows now).
* `routes_matrix_cache`: `DELETE WHERE expires_at < now()` (0 rows; Google only).
* `query_embedding_cache`: `DELETE WHERE expires_at < now()`.
* Prints counts only. Run daily from cron on the VM; add to `pipeline run` as the last step.
* Tests: one integration test per table with an expired and a fresh row.

---------------------------------------------------------------------------------------------------

## 9. Pipeline order (after this spec)
```
areas load → ingest wikidata (with P361/P527) → ingest wikidata-link → ingest wikipedia
→ ingest osm (new selectors, chain filter, quality score) → ingest wikivoyage (+city chunks)
→ ingest sheet (owner VI/EN descriptions, names, facts; osm_id linking) → ingest commons
→ web-candidates promote → publish auto (gate §4) → closure-rules load → cache sweep
```
`enrich *` removed.

## 10. Expected counts vs release gate (estimates from the measurements in §0/§3.3)

| Scenario | Published | Hội An area | Both-locale human descriptions |
|---|---|---|---|
| Now (with AI text) | 102 | 50 | 31 |
| AI retired, DEC-031 **B** (description mandatory), no owner text | ~33–38 | ~12–15 | same |
| + Wikivoyage EN + vi.wikipedia via QID links | ~38–45 | ~14–17 | ~38–45 |
| **DEC-031 A** (description optional) after §4 rules, before new imports | ~95–100 (sub-parts/non-stops/no-diacritics names fixed or held) | ~46–48 | ~38–45 |
| A + new FOOD/CAFE/MARKET/CRAFT from Wikivoyage + OSM quality pass | **≥ 120** | **≥ 55** | ~60 with WV-EN only; VI side needs owner |
| B + owner writes ~65 VI+EN descriptions (sheet) | ≥ 100 | ≥ 30 | ≥ 100 |

Gate MET-011 (≥ 100 / ≥ 30, both locales) is reachable **only** with DEC-031 A (names bilingual,
description optional) or B + owner-written text. Bilingual **names** remain mandatory in both
options: FOOD/CAFE/MARKET/RELIGIOUS_SITE/CRAFT_VILLAGE keep the proper-name EN fallback (DEC-025 (5)
is a naming rule, not AI — keep it, re-home it in DEC-031).

## 11. Code changes by file (summary)

apps/api
* `app/curation/auto_publish.py`: `gather` (policy-gated AI providers), `compose` (priority §4.1,
  disambiguation §4.3, no AI branches), `gate_reasons` + `GATE_RULES` (§4.2), new `is_area` handling in `_Apply`.
* `app/curation/names.py`: `is_generic_name`, `LATIN_BRAND_ALLOWLIST`, `normalise_display_name`, VI diacritic check.
* new `app/curation/dedupe.py`, `app/curation/identity.py`.
* new `app/ingestion/wikivoyage.py`; `app/ingestion/cli.py` (`ingest wikivoyage`, `policy deactivate`, pipeline order).
* `app/ingestion/osm.py` (`SELECTORS`, payload tags, `_is_chain`, quality score), `app/ingestion/categories.py` (NIGHTLIFE, craft, drop mall).
* `app/ingestion/wikidata.py:build_query`/`parse_bindings` (P361, P527, P31 area classes).
* `app/ingestion/wikipedia.py:sitelink_requests` (only own-QID sitelinks; reject when article `wikibase_item` ≠ place QID).
* `app/ingestion/sheet.py` (`osm_id` column).
* `app/planning/pool.py` (exclude `is_area`).
* `app/catalog/places.py`, `app/schemas/catalog.py`, `app/api/routes/catalog.py`: expose `is_area`,
  description `source` {publisher, licence, url} for attribution; keep `origin`/`grounding` fields
  for compatibility but always `SOURCE`/`OWNER` / null.
* `app/cli.py`: remove `enrich` commands and AI policy seeds; add `cache sweep`; seed `wikivoyage` provider.
* `app/curation/audit_sample.py`: drop AI columns; add description source/licence.
* remove `app/research/enrich.py`, `app/research/fact_extract.py`, `app/agents/fact_validation.py`, writer profiles.
* migration `20261110_0010_place_is_area.py`.
* `docs/04-design/api/openapi.yaml` + `scripts/export_openapi.py --check`; `docs/04-design/data/schema.sql` regen.
* Tests: unit tests per new gate rule using today's real cases (fixtures: art-gallery, nha-tho-toc,
  chua-quan-the-am-2, non-nuoc-beach/bai-tam-non-nuoc-2, quan-am/linh-ung-pagoda, my-son-group-a/my-son,
  da-nang-bay, nha-bia, the 3 Linh Ứng pagodas as **non**-duplicates, nguyen-van-troi-bridge vs
  tran-thi-ly-bridge 110 m as **non**-duplicates); listing parser tests on saved wikitext fixtures.

apps/mobile
* `src/features/place/PlaceScreen.tsx`: remove the `description_origin === 'AI_SUMMARY'` block
  (lines ~212–221) and `AiExtractedLabel` (line ~292); add an attribution line under the
  description: "Theo Wikivoyage · CC BY-SA 4.0" / "From Wikivoyage · CC BY-SA 4.0" (or Wikipedia,
  or "Gonarra" for owner text) linking to the source URL; empty state "Chưa có mô tả" / "No description yet".
* `src/i18n/locales/{vi,en}/place.json`: delete `aiExtracted`, `aiSummary`, `aiSummaryHint`; add
  `description.empty`, `description.source`, `description.licence`.
* `src/lib/api/schema.d.ts`: regenerate after OpenAPI change.
* Area places (`is_area`): show on map and in Guide, "Add to trip" disabled with "Khu vực — chọn
  điểm cụ thể bên trong" / "Area — pick a place inside it".

docs: DEC-030..032 in `docs/decisions.md`; MET-011 rev. 4 in PRD; `apps/api/data/README.md` gate table;
AGENTS.md rule text (DEC-028 paragraph reverted); RSK-107 closed, RSK-001 re-rated.

## 12. Name and description fixes to apply through the owner sheet (no CLI exists to edit names)
| slug | fix |
|---|---|
| tan-ky | VI "Nhà cổ Tấn Ký" |
| diep-dong-nguyen | VI "Nhà cổ Diệp Đồng Nguyên" |
| ngoc-cam | VI "Tịnh xá Ngọc Cẩm" |
| thanh-that-cao-dai-2 / thanh-that-hoi-an | VI "Thánh thất Cao Đài …"; check whether they are two temples (1.3 km apart; both texts say "1950s, Cẩm Phô") |
| cua-dai | VI "Bãi biển Cửa Đại" |
| nghia-trang-liet-si-to-quoc-ghi-cong | VI "Nghĩa trang liệt sĩ Hội An" |
| mieu-ba-chua-ngoc-tra-que-cam-ha-hoi-an | VI "Miếu Bà Chúa Ngọc (Trà Quế)" |
| mieu-lum-ba-dang-thanh-ha-hoi-an | VI "Miếu Lùm Bà Dàng" |
| military-blockhouse-ruins | VI name from a source or hold |
| y-pha-nho-cemetery-… | VI "Nghĩa trang Y Pha Nho" |
| waterpark-365-mikazuki-hotel | VI/EN "Công viên nước 365 Mikazuki" / "Mikazuki 365 Water Park"; confirm public day tickets, else take down (hotel facility) |
| precious-heritage-art-gallery-museum | EN description is a biography of Réhahn (wrong entity) — replace (Wikivoyage/owner) |
| linh-ung-pagoda, my-khe-beach, march-29-park, nguyen-tri-phuong-bridge, hoi-an-park, cau-lau-bridge, quang-nam-provincial-museum, da-nang-cathedral | description is a Wikidata one-liner → Wikivoyage/owner text |
| tran-thi-ly-bridge | EN text describes the "Nguyễn Văn Trỗi–Trần Thị Lý Bridge"; OK but owner may clarify |
| ba-na Linh Phong complex (linh-phong-bao-thap, linh-phong-thien-tu, den-linh-chua-linh-tu, chua-linh-ung-2) | 4 places within ~900 m inside Sun World Bà Nà (ticketed resort) → PART_OF ba-na-hills candidate; owner decides whether they stay separate stops |
