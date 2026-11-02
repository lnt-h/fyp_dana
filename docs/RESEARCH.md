# FYP research and evaluation

## Design rationale

The supplied Vietdetour screens illustrate city discovery, a map and a preference wizard. The Hội An example displays a newly created three-day trip with zero activities. The prototype should test whether receiving an editable first proposal helps users get to a usable trip. This observation applies to the supplied screen, not every workflow in that app.

Use Mindtrip as the visual trip-planning comparison, Tripomatic for AI editing of an existing itinerary and Roadtrippers for refining part of a trip. Compare effort, retained choices and visibility of changes on the same task. Treat competitive features as design references rather than evidence of user benefit. [Mindtrip](https://mindtrip.ai/) · [Tripomatic planner](https://tripomatic.com/en/features/ai-trip-planner) · [Roadtrippers trip enhancement](https://support.roadtrippers.com/hc/en-us/articles/31569473913620-Using-Autopilot-to-Enhance-a-Trip)

## Questions and method

- Can Vietnamese- and English-speaking travelers create a feasible short trip and recognize closures, excessive walking and missing evidence using Plan Health?
- How much editing is needed to change one day while preserving valued stops? Observe HA-02, identify unintended changes and ask users to explain the difference between preview and Save.
- Can a traveler use the execution card to find an entrance, show a driver the address and distinguish verified from stale information? Evaluate contextual answers at claim level.

Use interviews to refine assumptions. Compare planning outcomes against a deterministic scheduler given identical candidates, facts, modes and daily windows. Freeze tuning and held-out sets separately by source/revision to prevent near-duplicates. Include multiple cities, both locales, unknown facts, distractors, adversarial instructions and correct refusals. Record model, embedding, prompt, decoding settings, corpus revision and device/network conditions.

Report task completion, time, critical errors, edit effort, perceived trust and the standard ten-item System Usability Scale separately. For model evaluation report schema/ID validity, feasible plan rate, lock violations, supported claims, answerable coverage, correct and false refusals, latency, provider failures and cost. Human reviewers check whether each citation supports the actual claim.

## Ethics and evidence

Agree recruitment criteria, sample size, thresholds, consent, retention and withdrawal with the supervisor before recruitment. Use voluntary participation, synthetic accounts and non-sensitive scenarios. De-identify observations and obtain permission before publishing quotes or images. Separate prototype, fixture, live-provider and physical-device results. Report failed tasks, small-sample limitations, prior travel knowledge and language/device effects. Version the evaluation report with its fixtures and build identifier. Retain identifiable participant evidence only in approved research storage.
