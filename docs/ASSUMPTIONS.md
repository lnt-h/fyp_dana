# Working assumptions — Danang TourGuide v0.1

Replace these when you provide official values. Every generated doc inherits this list.

| ID | Topic | Assumed value | Impact if wrong |
|----|--------|---------------|-----------------|
| A-01 | Owner | Single graduation developer (Software Engineering + AI) | Stakeholder names, RACI |
| A-02 | Timeline | 8 months in the supplied product spec; earlier project discussions mentioned 3–4 months. **Decision pending.** The current plan assumes 8 months. | If 3–4 months is final, reduce P0 and revise every milestone/test gate before implementation. |
| A-03 | Auth | Email/password + Google OAuth; guest mode for Visual Taste | API and UX |
| A-04 | Cloud region | AWS `ap-southeast-1` | Latency, data residency |
| A-05 | Maps | Google Maps SDK + Routes API | Cost, ToS, fallback |
| A-06 | Weather | OpenWeatherMap One Call (or equivalent) | Weather module |
| A-07 | Vision/LLM | Google Gemini Vision + Gemini LLM | Prompts, cost, privacy |
| A-08 | Embeddings | `gemini-embedding-2` multimodal for image vectors and text RAG vectors, configured to **768 dimensions**; pin model ID, dimension and task configuration. Validate image and text calls in a spike before ingest. | pgvector schema, ranking and re-embedding migration |
| A-09 | TTS | Cloud TTS (Google Cloud TTS or equivalent) | Audio Guide |
| A-10 | Image storage | AWS S3 + CloudFront; originals + WebP variants | Media module |
| A-11 | Languages | `vi`, `en`; device locale default | i18n |
| A-12 | POI corpus V1 | 100–150 POIs, ~6 images each | Ingestion, vectors |
| A-13 | Concurrent users (demo) | Tens, not tens of thousands | NFR targets for thesis vs production |
| A-14 | PII | User photos stored; GDPR-like deletion on request | Retention, S3 lifecycle |
| A-15 | Explainability | Six Degrees is a **path of matched features**, max 6 nodes, not a social graph | RAG vs rec engine |
| A-16 | Camera scan | P2 in the supplied product spec, although earlier project discussions treated it as central. Keep it out of the committed V1 until scope/timeline is decided. | UX, vision endpoint, test plan |
| A-17 | Location | Foreground location permission and manual “I’m here” fallback for V1; no promise of reliable background geofencing. | Arrival API and mobile UX |
| A-18 | Voice | P0 audio narration and typed Ask AI. Full duplex voice conversation is outside the supplied V1 scope. | Speech-to-text and live audio architecture |

These are working choices, not facts supplied by an external provider. Resolve A-02 and A-16 before freezing the graduation scope. Model availability, quotas and AWS extension support must be checked in the chosen account/region during the technical spike.
