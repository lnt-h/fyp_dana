# Vector Database Design — Danang TourGuide (pgvector)

Same PostgreSQL as [11-Database-SQL.md](./11-Database-SQL.md). No separate vector SaaS in V1.

---

## 1. Business requirements

- Image ↔ POI image similarity (Explore by Image, per-photo rec)
- Preference ↔ place semantic similarity (DNA vs `place_embedding` / tags)
- RAG: question embedding ↔ `knowledge_chunks.embedding` filtered by `place_id` / locale

---

## 2. Vector characteristics

| Item | V1 assumption (A-08 — confirm) |
|------|--------------------------------|
| Dimension | 768, explicitly requested in the embedding call and validated at ingest |
| Model | `gemini-embedding-2` multimodal for photos and text; pin model ID and verify account availability |
| Type | `vector(768)` float32 |
| Count | < 5,000 |
| Update | POI: batch ingest; user images: on taste job |
| Metric | Cosine (`vector_cosine_ops`) |

Google documents image and text inputs and configurable 768-dimensional output for this model. The model ID and dimension are an implementation assumption until a real image/text spike passes. If a fallback uses distinct image and text models, keep their vector spaces separate; never compare them across models. Re-embed all relevant rows when changing model or dimension.

---

## 3. Collections (tables)

| Table | Vector | Metadata filters |
|-------|--------|------------------|
| `place_images.embedding` | POI photo | `place_id`, published join |
| `image_analyses.embedding` | User photo | `media_id`, owner |
| `places.place_embedding` | Mean/centroid of images + tags | category, attributes JSON |
| `knowledge_chunks.embedding` | Passage | `place_id`, `locale` |

---

## 4. Indexes

Small V1 corpus: start with exact search and B-tree filters; record `EXPLAIN ANALYZE` and recall/latency results. Add HNSW only if measured latency warrants it. An ANN scan can filter **after** candidate retrieval and under-return rows for a narrow `place_id`/locale filter; use exact filtered RAG queries for V1.

```sql
-- Optional growth migration, not required for initial V1 deployment.
CREATE INDEX idx_place_images_hnsw
  ON place_images
  USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_chunks_hnsw
  ON knowledge_chunks
  USING hnsw (embedding vector_cosine_ops);

-- User photos are looked up by owner/job, not nearest-neighbor queried as a corpus.
```

**Query pattern (place images):**

```sql
SELECT pi.place_id, 1 - (pi.embedding <=> $1) AS sim
FROM place_images pi
JOIN places p ON p.id = pi.place_id AND p.is_published
WHERE pi.embedding IS NOT NULL
ORDER BY pi.embedding <=> $1
LIMIT 20;
```

**RAG:**

```sql
SELECT id, body, source, 1 - (embedding <=> $1) AS sim
FROM knowledge_chunks
WHERE place_id = $2 AND locale = $3 AND embedding IS NOT NULL
ORDER BY embedding <=> $1
LIMIT 8;
```

Always scope RAG by an authorized `place_id` and locale so the LLM cannot cite another POI’s history. Place-only filters are insufficient for trip-wide questions; those must use an explicit allowlist of the trip's place IDs. Apply a measured relevance threshold, remove duplicate chunks and validate source metadata. A low-score hit is not evidence merely because it is top-K.

---

## 5. Aggregation (multi-photo)

For each user image, take top-M POIs. Aggregate per-place hits (e.g. capped max/mean across images), combine with confirmed attribute match and context weights, and persist the component scores and weight/version in `match_evidence.scores`. Calibrate a 0–100 display score against a labeled small evaluation set; cosine similarity itself is not a probability.

---

## 6. Metadata

- Structured: ids, locale, category, published flag  
- Semi-structured: `pref_attributes`, `path_nodes`  
- Do not store raw embedding in Redis except short-lived taste job cache

---

## 7. Ops

- Re-embed on model change (batch job), keeping old and new columns/indexes separate during migration.
- Store `embedding_model` in config/table `ai_models` if you need dual-running (optional V1).
- Monitor: p95 query time, recall@K on a labeled mini-set of 20 queries (thesis experiment).

---

## 8. Quality rules

- Rec engine uses vectors + rules; LLM does not pick POI IDs.
- Empty RAG → `refusedFact: true`, no historical invention.

## 9. Evidence and evaluation

- For a curated set of image–POI pairs, measure recall@K and manually inspect false matches across beach, temple, food and nightlife categories.
- For RAG, evaluate Vietnamese and English questions, wrong-POI retrieval, conflicting sources and no-answer cases. Citations in API responses point to source-backed chunk IDs, not model-generated URLs.
- Record the provider, model ID, output dimension, preprocessing version and corpus snapshot for reproducible results. Never mix image and text vectors produced by incompatible configurations.

References: [Gemini Embedding 2 model](https://ai.google.dev/gemini-api/docs/models/gemini-embedding-2), [pgvector indexing and filtering](https://github.com/pgvector/pgvector#filtering). Verify provider terms and the chosen AWS engine version during the implementation spike.
