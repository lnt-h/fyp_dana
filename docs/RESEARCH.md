# Gonarra Research

## Aim

Evaluate whether an English-first, source-aware mobile guide can help first-time international visitors discover, plan, and understand a day in Da Nang while keeping AI, location, and content limitations visible.

This is an academic and product hypothesis, not an existing research finding.

## Research questions

1. Does the integrated discovery-to-visit journey reduce user effort compared with switching among separate information and map tools?
2. Do reviewed local names, aliases, and source cards improve comprehension and trust?
3. Can users understand and safely edit an AI-assisted itinerary?
4. Are external directions, manual arrival, human-recorded audio, and source-grounded questions useful during a visit?
5. Do authentication, permissions, offline states, and provider failures remain understandable?

## Evidence plan

- Interview or observe eligible international visitors before finalising the problem statement.
- Use reviewed English tasks and a fixed Da Nang place corpus.
- Record task completion, critical errors, time on task, and qualitative observations.
- Use the standard ten-item System Usability Scale separately from task-success metrics.
- Evaluate itinerary validity and constraint handling against a deterministic baseline.
- Evaluate answers at claim level against the specific reviewed source supplied to the system.
- Separate fixture tests, controlled evaluations, and live-provider trials.

Proposed targets such as participant counts, task-success rates, or SUS scores require supervisor approval and must be reported with their sample limitations.

## AI and retrieval evaluation

Freeze the reporting set before tuning. Record corpus revision, embedding configuration, model, prompt, and decoding settings.

Report:

- Published-ID and schema validity.
- Constraint-valid itinerary rate.
- Source-supported claim rate.
- Appropriate refusal rate.
- False refusal and answerable-question coverage.
- End-to-end latency and provider failure rate.

A citation does not by itself prove that a claim is supported. Human review must check the cited source against the claim.

## Ethics and privacy

- Participation is voluntary and follows the institution's approved consent process.
- Do not collect minors or vulnerable participants without explicit approval.
- Use synthetic accounts and non-sensitive scenarios where possible.
- Minimise precise location, raw audio, images, and free-text retention.
- Remove direct identifiers from research records and define retention before collection.
- Do not publish participant data, media, or quotes without documented permission.
- Content, translations, photography, narration, and offline distribution require recorded rights.

## Validity and reporting

- Small convenience samples do not establish population-wide conclusions.
- Simulated GPS, route fixtures, and prototype screens are labelled.
- Provider quality, network conditions, prior travel experience, language ability, and device familiarity are possible confounders.
- Contradictory findings and failed tasks are reported rather than removed.
- Documentation coverage is not implementation or validation evidence.

## Reference starting points

- React Native accessibility guidance: <https://reactnative.dev/docs/accessibility>
- System Usability Scale reference hosted by AHRQ: <https://digital.ahrq.gov/sites/default/files/docs/survey/systemusabilityscale%2528sus%2529_comp%255B1%255D.pdf>
- The repository's Figma prototype is a design reference, not usability evidence.
