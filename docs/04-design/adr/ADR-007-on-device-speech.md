# ADR-007 — On-device speech-to-text and text-to-speech for voice

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | Agent brief (voice), BR-016, BR-039, AGENTS.md voice rules |

## Context

Voice questions (BR-016) and read-aloud answers (BR-039) are Should features, third in the cut order (DEC-003), to
start only after the text Guide passes AC-015 (BRD §5.2). AGENTS.md: transcript preview/edit and explicit Send; TTS
reads only completed, visible text; never persist audio; native builds required for STT. Free-tier AI data use is a
risk (RSK-002).

## Drivers

BR-016, BR-039, BR-046, DC-007, CON-001, RSK-002, AC-016, AC-039.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. On-device STT (Expo speech-recognition module) and TTS (`expo-speech`); transcript sent as normal Guide text | No audio leaves the device; no AI cost; reuses text Guide pipeline | Recognition quality depends on device/OS (RSK-033) | **Chosen** |
| B. Gemini Live (streaming audio) | Natural conversation | Audio to a free-tier AI service; new streaming path; cost/quota; later option | Deferred (future ADR) |
| C. Cloud STT/TTS service | Consistent quality | Cost; audio leaves device; extra provider | Rejected |

## Decision

Mobile CMP-021 records with on-device recognition, shows an editable transcript and sends it only on explicit
Send to the same Guide endpoint as text; TTS reads the completed answer. No audio is uploaded or stored. The
feature is behind `FEATURE_VOICE`. Module choice and Vietnamese support are verified in a spike (OQ-037).

## Consequences

- Positive: privacy by design; no server changes beyond the Guide.
- Negative: device variance; Expo Go cannot validate STT (development builds needed).
