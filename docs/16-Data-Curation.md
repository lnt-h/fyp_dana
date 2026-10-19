# POI, source, audio and RAG curation

Version 1.3 | 2026-10-19 | Status: design baseline for review. Document control and evidence status: [Index](00-INDEX.md).

## Data gate

BIZ-01/03/04; FR-POI-01, FR-TRV-03, FR-OFF-01, FR-AI-01. Development corpus: five complete English-first POIs and 2–3 human English recordings; final P0 corpus: 15–20 POIs and exactly five flagship human English audio guides. Categories are Culture, Beach, Food and Nature; urban landmarks use Culture plus bounded tags. These are targets; no real dataset or media is shipped in this docs package.

## Record checklist

POI: UUID/slug, required reviewed English name/description, Vietnamese local name, aliases/romanisations, four-category value and bounded tags, verified coordinate and reviewed entrance/arrival point, estimated visit duration labelled as estimate, facts/hours/price with source/date/status, licensed images with English alt text/attribution. Source: title/publisher/URL or document reference, `source_language`, access/review date, version and reuse rights. English translation: origin source IDs, translator/editor identity or process, human review status/date and claim links. Audio: `en` locale, file key, bytes/duration/transcript, narrator permission, publication rights, offline-cache permission, review/version. Chunk: place/source/source revision/source language/translation provenance/heading/text/review/corpus revision/embedding config.

## Workflow

1. Select 15–20 places spanning Culture, Beach, Food and Nature, with flagship coverage for the five audio guides. Category is controlled vocabulary; urban traits are tags rather than a fifth category.
2. Collect from trusted licensed/authorised sources. Record source access and factual verification separately; do not scrape content assuming reuse permission.
3. Deduplicate names/coordinates; check entrance accessibility and GPS target. Record unknown/conflicting operational facts.
4. Draft English factual narratives only from cited material. If a source is Vietnamese, preserve `source_language`, link the English translation to the origin and complete human review before publication. Review each claim; never label raw machine translation as reviewed.
5. Record human English narration after script/source/narrator approval. Validate bytes/MIME/duration/transcript/media manifest and both playback and offline-cache rights; upload versioned object keys.
6. Create semantic text chunks with source revision. Trial 300–500 tokens with modest overlap; evaluate rather than fix blindly.
7. Embed approved chunks with pinned configuration; exclude stale/unreviewed versions.
8. Import drafts, run validation, review and publish. Publication fails without required English content, local-name alias, source language/origin links, rights, entrance coordinates or translation review.
9. Re-review when facts/source/media change; create a new reviewed source ID/revision for material edits, preserve old evidence metadata, mark replaced chunks stale, reembed and version corpus. Review cadence and operational fact expiry policy TBD before external pilot.

## Ledger fields and evidence

Track place ID/English and local names/aliases, category/tags, content owner, source IDs/revisions/languages, translation origin/reviewer, known/unknown facts, image/audio rights including offline use, audio review state, last checked date, validation errors and publication state. Initial ledger below intentionally contains no fabricated places:

| Place ID | English/local names | Source language/translation | Source/rights | Entrance | Audio/offline right | Publication |
|---|---|---|---|---|---|---|
| Not yet collected | — | Pending | Pending | Pending | Pending | Draft only |

## Rejection cases

No source; missing source language or translation-origin link; unreviewed English; unlicensed image/narration/offline caching; out-of-range coordinate or unreviewed entrance; duplicate slug/alias collision; unsupported fifth category; price treated as free when unknown; expired/conflicting hours; mismatch chunk/source revision; wrong embedding dimension/model; unreviewed audio. Log row-level reason without secrets or personal content.

## Ownership and operations

Developer is curator/owner; independent factual/narration reviewer name TBD. Restricted CLI replaces admin UI for P0. Any later public editing workflow is a new scope/security decision. Restore must verify all DB media keys exist in versioned manifest.

## Source authority and publication invariants

For operational values prefer the venue/operator's dated information; for historical statements use identified credible primary or scholarly sources. Conflicting sources are recorded instead of selecting a convenient value. Authority, factual correctness and permission to reproduce text/image/audio are separate checks. Cite a source for each reviewed claim; a link to a general homepage is insufficient when it does not support the claim.
Reject publication until reviewed English name/description, Vietnamese local name plus aliases, four-category taxonomy, entrance coordinates, source-language/translation provenance, source association and authorised image are complete. Unknown hours/prices may remain unknown; they block claims of feasibility, not POI publication. Missing audio is allowed outside the five flagship POIs and remains unavailable; audio without offline permission may stream but never appear cached. Exclude stale/conflicting/expired evidence from affirmative operational answers. A fact/source recheck policy is agreed before pilot and recorded in Decisions.
Maintain an internal content manifest with source/fact/media versions and row-level review evidence. Reviewed human transcripts have claim-to-source references; audio/imagery permission evidence is retained outside public repository when it contains personal data. A real collection and permissions are future work; no example place or licence is counted toward the final corpus.

## Small-corpus evaluation guard

The held-out English set includes answerable facts, unknown hours/prices, distractor chunks, cross-POI questions, ambiguous aliases, adversarial instructions and correct-refusal cases. Near-duplicate passages from the same source/revision cannot be split across tuning and held-out sets. Report coverage by POI/category and both false-refusal and unsupported-claim rates; a high score on five repeated flagship facts is not evidence of general accuracy.
