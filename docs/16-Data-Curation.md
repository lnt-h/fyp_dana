# POI, source, audio and RAG curation

Version 1.2 | 2026-10-12 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Data gate

BIZ-01/03/04; FR-POI-01, FR-TRV-03, FR-AI-01. Development corpus: five complete POIs and 2–3 human recordings; final corpus: 30–50 POIs/10–15 audio flagship places. These are targets; no real dataset or media is shipped in this docs package.

## Record checklist

POI: UUID/slug, Vietnamese name/description, optional English, taxonomy tags, verified coordinate and arrival access point, estimated visit duration labelled as estimate, facts/hours/price with source/date/status, licensed images with alt text/attribution. Source: title/publisher/URL or document reference/access/review date/version/rights. Audio: locale/file key/duration/transcript/narrator permission/review/version. Chunk: place/source/source revision/locale/heading/text/review/corpus revision/embedding config.

## Workflow

1. Select places spanning proposed categories: culture, beach, nature, food, urban. Confirm taxonomy with research; category is controlled vocabulary, tags bounded strings.
2. Collect from trusted licensed/authorised sources. Record source access and factual verification separately; do not scrape content assuming reuse permission.
3. Deduplicate names/coordinates; check entrance accessibility and GPS target. Record unknown/conflicting operational facts.
4. Draft factual narratives only from cited material; review each claim. Record human narration after content/permissions approval.
5. Validate bytes/MIME/duration/transcript/media manifest; upload versioned object keys.
6. Create semantic text chunks with source revision. Trial 300–500 tokens with modest overlap; evaluate rather than fix blindly.
7. Embed approved chunks with pinned configuration; exclude stale/unreviewed versions.
8. Import drafts, run validation, review and publish. Publication fails without required source/rights/coordinates.
9. Re-review when facts/source/media change; create a new reviewed source ID/revision for material edits, preserve old evidence metadata, mark replaced chunks stale, reembed and version corpus. Review cadence and operational fact expiry policy TBD before external pilot.

## Ledger fields and evidence

Track place ID/name, content owner, source IDs/revisions, known/unknown facts, media rights reference, audio review state, last checked date, validation errors and publication state. Initial ledger below intentionally contains no fabricated places:

| Place ID | Name | Source/rights | Coordinates | Audio review | Publication |
|---|---|---|---|---|---|
| Not yet collected | — | Pending | Pending | Pending | Draft only |

## Rejection cases

No source; unlicensed image/narration; out-of-range coordinate; duplicate slug; price treated as free when unknown; expired/conflicting hours; mismatch chunk/source revision; wrong embedding dimension/model; unreviewed audio. Log row-level reason without secrets or personal content.

## Ownership and operations

Developer is curator/owner; independent factual/narration reviewer name TBD. Restricted CLI replaces admin UI for P0. Any later public editing workflow is a new scope/security decision. Restore must verify all DB media keys exist in versioned manifest.

## Source authority and publication invariants

For operational values prefer the venue/operator's dated information; for historical statements use identified credible primary or scholarly sources. Conflicting sources are recorded instead of selecting a convenient value. Authority, factual correctness and permission to reproduce text/image/audio are separate checks. Cite a source for each reviewed claim; a link to a general homepage is insufficient when it does not support the claim.
Reject publication until name/description/taxonomy, reviewed coordinates, source association and authorised image are complete. Unknown hours/prices may remain unknown; they block claims of feasibility, not POI publication. Missing audio is allowed for nonflagship POIs and remains unavailable. Exclude stale/conflicting/expired evidence from affirmative operational answers. A fact/source recheck policy is agreed before pilot and recorded in Decisions.
Maintain an internal content manifest with source/fact/media versions and row-level review evidence. Reviewed human transcripts have claim-to-source references; audio/imagery permission evidence is retained outside public repository when it contains personal data. A real collection and permissions are future work; no example place or licence is counted toward the final corpus.
