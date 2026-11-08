# ADR-007 — On-device speech-to-text and text-to-speech for voice

| Field | Value |
|---|---|
| Status | Proposed (mentor approval at M0). Re-affirmed 2026-11-06 (DEC-019, DEC-021) |
| Date | 2026-11-04 (1.0: 2026-11-06) |
| Version | 1.0 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | BR-016, BR-039, AGENTS.md voice rules |

## Context

Voice questions and read-aloud answers are Should features, third in the cut order, started only after the text
Guide passes its acceptance test. Rules: transcript preview and edit, explicit Send, TTS reads only completed
visible text, never persist audio, native builds required for STT. Free-tier AI data use is a risk.

## Decision

- On-device STT (Expo speech-recognition module) produces an editable transcript; the user sends it explicitly to
  the same Guide endpoint as text (`input_mode = VOICE_TRANSCRIPT`).
- On-device TTS (`expo-speech`) reads the completed answer only. No audio is uploaded or stored.
- Voice never accepts, saves or overwrites a trip. Text input remains available when recognition fails.
- Behind `FEATURE_VOICE`; Vietnamese recognition quality is verified in a spike on development builds.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. On-device STT and TTS, transcript as normal Guide text | **Chosen** | No audio leaves the device; no AI cost; reuses the text pipeline |
| B. Gemini Live streaming audio | Deferred | Audio to a free-tier AI service; new streaming path |
| C. Cloud STT/TTS | Rejected | Cost; audio leaves the device; extra provider |

## Consequences

- Positive: privacy by design; no server change beyond the Guide.
- Negative: device variance; Expo Go cannot validate STT.

## Drivers

BR-016, BR-039, BR-046, DC-007, CON-001, RSK-002, RSK-033.
