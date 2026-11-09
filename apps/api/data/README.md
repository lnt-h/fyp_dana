# Content pipeline data (DEC-022)

Gonarra publishes catalog content **without human review**: importers stage DRAFT places and a
deterministic gate in code (`app/curation/auto_publish.py`) approves and publishes what passes.
The owner maintains the files in this folder and runs the CLI from `apps/api`.

## Commands

```sh
uv run python -m app.cli seed                          # reference data + system account
uv run python -m app.cli policy list                   # provider policies (default deny)
uv run python -m app.cli policy activate wikidata  --terms-version "CC0 checked 2026-11-07"
uv run python -m app.cli policy activate wikipedia --terms-version "CC BY-SA 4.0 + ToU checked 2026-11-07"
uv run python -m app.cli policy activate gonarra_sheet --terms-version "owner sheet v1"
uv run python -m app.cli policy activate wikivoyage --terms-version "CC BY-SA 4.0 checked 2026-11-09"
uv run python -m app.cli pipeline run [--sheet data/sheet/da-nang.csv] [--dry-run] [--no-embed] [-v]
uv run python -m app.cli publish auto
uv run python -m app.cli publish summary               # published total, by area, Hội An area
uv run python -m app.cli publish audit-sample [--fraction 0.1] [--seed 7] [--out audit.csv]
uv run python -m app.cli caches sweep                  # provider-cache retention
```

`pipeline run` = `areas load` → `ingest wikidata` → `ingest wikidata-link` → `ingest wikipedia` →
`ingest osm` → `ingest wikivoyage` → `ingest commons` → `ingest sheet <csv>` (when given, or when
`data/sheet/da-nang.csv` exists) → `web-candidates promote` → `publish auto` → `closure-rules load`
→ `caches sweep`. Each step also runs alone. An importer whose provider policy
is not ACTIVE refuses to run (ADR-006); `pipeline run` reports it and continues.
`publish auto --dry-run` runs the gate and writes nothing. Chunk embeddings need `GEMINI_API_KEY`;
without it, places still publish and their Guide OVERVIEW chunks stay pending until a later run.

Re-running is safe: an unchanged release is skipped, places are keyed by external identity
(`external_place_identities`), approved rows are reused while unchanged, and a place is
re-published only when its publication snapshot would change.

## Automated publication gate

A place is published only when all of these hold (codes appear in the CLI report):

| Code | Rule |
|---|---|
| `NO_SOURCE` | at least one staged record with a recorded source revision |
| `OUTSIDE_CITY` | location inside `cities.boundary` |
| `MISSING_CATEGORY` | category from the sheet or a mapped Wikidata class |
| `MISSING_AREA` | sheet `area_code`, or the location falls inside an `areas/<city>.yaml` polygon |
| `MISSING_NAME:<locale>` | a VI **and** an EN name (sheet, else Wikidata label, else OSM `name:en`); never machine-translated. Proper-name fallback: see below |
| `MISSING_DESCRIPTION:<locale>` | only when `REQUIRE_DESCRIPTION` is on (DEC-033 option B); under option A a place without a human-written description publishes and the card says "No description yet" |
| `AI_CONTENT` | no localization with `translation_origin` `AI_SUMMARY`/`AI_DRAFT` and no fact with `origin = AI_EXTRACTED` (DEC-031) |
| `GENERIC_NAME`, `VI_NAME_NOT_VIETNAMESE`, `NAME_FORMAT` | name quality: not a bare class word, a VI name with Vietnamese diacritics or an allow-listed brand, Latin/Vietnamese script only |
| `NOT_A_STOP` | hotels, banks, tailors, offices, supermarkets and malls are not travel stops |
| `DUPLICATE_OF:<slug>`, `PART_OF:<slug>` | the place is another candidate (same item/QID/OSM element, or similar name within the category radius) or a sub-part of an existing place |
| `MISSING_LICENCE:<publisher>` | every source behind shown text, facts or chunks has a licence and attribution text |
| `FACT_WITHOUT_SOURCE:<field>` | every KNOWN fact cites an attributed source revision |
| `SQL_GATE:<violation>` | `fn_publication_gate_violations` (re-checked inside `fn_publish_place`) |

Facts without a sourced value are written as `UNKNOWN` (required fields only), citing the place's
primary record with the claim "No value … shown as unknown" — values are never invented.
`has_no_media` is set unless licensed (CLEARED) media is attached. Visit minutes come from the
sheet or a per-category default (`app/ingestion/categories.py`). Everything is approved and
published as the system account `system:gonarra-pipeline`.

If a published place stops passing the gate, the pipeline withdraws it (reason
`auto-gate: …`) and re-publishes it when it passes again. A place the owner unpublished
(`POST /v1/admin/places/{place_id}/unpublish`) is never re-published automatically; use
`publish auto --include-withdrawn` to bring it back.

Research web candidates are promoted to DRAFT places only when the Google Places check says
`EXISTS_OPERATIONAL` and the location is inside the city boundary; they then face the same gate.

### English name fallback (proper names)

When no source gives an English name, the EN name is the original Vietnamese name, unchanged
(`place_localizations.name_is_source_fallback = true`): always for FOOD, CAFE, MARKET,
RELIGIOUS_SITE and CRAFT_VILLAGE, and for other categories only when the name does not start with
a generic place word such as "Núi", "Bãi biển" or "Bảo tàng" (`app/curation/names.py`). Names are
never machine-translated.

### Descriptions and facts (human-written only, DEC-031)

Catalog descriptions and facts come only from human-written, openly licensed sources and the
owner sheet, in this order: owner-sheet description, then the matched Wikivoyage listing
(CC BY-SA 4.0, `lastedit` ≥ 2023 for facts), then the Wikipedia lead reached through the place's
own Wikidata sitelink, else none. Wikidata descriptions are used only as short descriptions. No
model writes, translates or paraphrases catalog content (`AI_CONTENT` gate rule); the former
`enrich descriptions` / `enrich facts` commands and their providers are retired. A missing
description is a normal state (DEC-033 option A), shown as "No description yet".

`publish audit-sample` writes a CSV of a random 10 % of current publications (names, descriptions
with origin and sources, cited URLs, facts with evidence locators, image credit) with empty
`owner_accurate_yes_no` / `owner_notes` columns for the owner's manual check.

## Sources and licences

* **Wikidata** (CC0): labels, descriptions, aliases, coordinates, `P31` class → category
  (`app/ingestion/categories.py`; unmapped classes are skipped). Source revision per item URL.
* **Wikipedia** (CC BY-SA 4.0): REST summary of the VI/EN sitelinks becomes the description and
  the Guide OVERVIEW chunk; source "Wikipedia (vi|en)", locator = page URL, `content_sha256` of the
  extract, retrieved time. Displaying this text requires attribution and keeps it under
  CC BY-SA (ShareAlike).
* **Owner sheet**: every row and fact names its own source URL, publisher and licence.
* **OpenStreetMap** (ODbL): names, coordinates, opening hours. FOOD/CAFE elements with none of
  `name:en`, `website`, `opening_hours`, `cuisine` or `wikidata` are not imported (draft bloat
  filter, `skipped_sparse` in the report): they could never pass the gate.

## `areas/<city>.yaml`

Approximate travel-area polygons (`[lng, lat]`), first match wins. `areas load` writes them into
`areas.boundary` and creates or renames areas that carry `name_vi`/`name_en`. `hoi_an_area: true`
marks the "Hội An area" group of the release gate (`hoi-an-old-town`, `hoi-an-beaches-islands`,
`hoi-an-outskirts`). Real tourist clusters only (e.g. `my-son`, `tam-ky`); there is no catch-all
area. Edit and re-run the pipeline to re-assign places.

## `closure_rules/<city>.yaml`

The operator calendar (Tết, lantern nights, ticket validity, weekly events, car-free hours).
Loaded APPROVED with the source "Gonarra operator calendar" (OWN_OBSERVATION); the load is a
sync (unchanged kept, new inserted, removed RETIRED). Every rule kind accepts optional
`from`/`to` ("HH:MM") and `restricted_modes` (`WALK`, `DRIVE`, `TWO_WHEELER`). See the file
header for the per-kind `params`.

## Owner sheet (CSV, UTF-8)

Default location `data/sheet/da-nang.csv` (or pass `--sheet`). One row per place:

| Column | Required | Notes |
|---|---|---|
| `slug` | yes | `lower-kebab-case`, unique; the row's identity across imports |
| `category_code` | yes | one of HERITAGE, MUSEUM, RELIGIOUS_SITE, BEACH, NATURE, VIEWPOINT, MARKET, FOOD, CAFE, NIGHTLIFE, THEME_PARK, CRAFT_VILLAGE |
| `area_code` | no | blank = assigned from `areas/da-nang.yaml` |
| `lat`, `lng` | yes | WGS 84 decimal degrees, inside the city |
| `name_vi`, `name_en` | yes* | both needed to publish |
| `short_description_vi`, `short_description_en` | yes* | one line each |
| `description_vi`, `description_en` | no | longer text; Wikipedia wins when the place also has a sitelink |
| `source_url`, `source_publisher` | yes | where the row's text comes from |
| `licence` | yes* | e.g. `CC-BY-4.0`, `CC0-1.0`, `own-work`; blank = `UNKNOWN` → gate rejects `MISSING_LICENCE` |
| `attribution` | no | defaults to `source_publisher` when a licence is given |
| `source_kind` | no | OFFICIAL, OPEN_DATA, REFERENCE (default), OWN_OBSERVATION, WEB |
| `wikidata_id` | no | `Q…`: enrich the Wikidata place instead of creating a new one |
| `opening_hours` + `opening_hours_source_url` | no | syntax below |
| `ticket_price` + `ticket_price_source_url` | no | free text, e.g. `120.000 VND (người lớn)` → ADMISSION_PRICE `{"text": …}` |
| `address_vi` + `address_vi_source_url` | no | ADDRESS_VI `{"text": …}` |
| `payment_methods`, `dress_code`, `access_rules` (+ `_source_url`) | no | `{"text": …}` |
| `entrance_lat`, `entrance_lng` + `entrance_source_url` | no | ENTRANCE_LOCATION `{"lat", "lng"}` |
| `visit_minutes_min`, `visit_minutes_suggested`, `visit_minutes_max` | no | all three or none; 0 < min ≤ suggested ≤ max ≤ 600 |

\* the row imports without it, but the gate will not publish the place.
A fact value without its `_source_url` rejects the row (`FACT_WITHOUT_SOURCE`).

### `OPENING_HOURS` value shape

Sheet syntax: clauses separated by `;`, each `<days> <ranges>`; days `mon`..`sun`, ranges like
`mon-fri`, lists like `sat,sun`, or `daily`; ranges `HH:MM-HH:MM` separated by `,` (`24:00` allowed
as a closing time) or `closed`. Example: `mon-fri 08:00-11:30,13:30-17:00; sat closed`.

Stored fact value (what Plan Health reads):

```json
{"weekly": {"1": [["08:00", "11:30"], ["13:30", "17:00"]], "6": []}, "text": "<original sheet text>"}
```

Keys are ISO weekdays `"1"`..`"7"` (Monday = 1; readers also accept `"mon"`..`"sun"` and the map
without the `weekly` wrapper). A day mapped to `[]` is closed; a day that is absent is unknown.
