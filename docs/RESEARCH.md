# FYP research and evaluation

## Design rationale

The supplied Vietdetour screens illustrate city discovery, a map and a preference wizard. The Hội An example displays a newly created three-day trip with zero activities. The prototype should test whether receiving an editable first proposal helps users get to a usable trip. This observation applies to the supplied screen, not every workflow in that app.

Use Mindtrip as the visual trip-planning comparison, Tripomatic for AI editing of an existing itinerary and Roadtrippers for refining part of a trip. Compare effort, retained choices and visibility of changes on the same task. Treat competitive features as design references rather than evidence of user benefit. [Mindtrip](https://mindtrip.ai/) · [Tripomatic planner](https://tripomatic.com/en/features/ai-trip-planner) · [Roadtrippers trip enhancement](https://support.roadtrippers.com/hc/en-us/articles/31569473913620-Using-Autopilot-to-Enhance-a-Trip)

## Data-provider research baseline

Research reviewed on 2026-11-02 supports a hybrid catalog, not model-generated POI data and not a permanent copy of one commercial API:

- [Overture Places](https://docs.overturemaps.org/guides/places/) publishes downloadable, versioned place data with record sources and permissive/Apache/CC0 licenses. Use geographically bounded releases to seed candidates and retain the applicable notices.
- [Foursquare Open Source Places](https://docs.foursquare.com/data-products/docs/fsq-places-open-source) provides an Apache-2.0 open dataset with stable IDs, categories and core place attributes. Rich hours and quality fields belong to separately licensed products; open and paid schemas must not be conflated.
- [Wikidata](https://www.wikidata.org/wiki/Wikidata:REST_API) provides CC0 structured identity/heritage facts. Wikimedia Commons media is reusable only under each file's actual license and attribution requirements.
- [VietMap](https://maps.vietmap.vn/docs/), [Goong](https://document.goong.io/tutorial-Places.html) and [Map4D](https://api.map4d.vn/sdk/docs/index.html) expose Vietnam-oriented place, geocoding and routing APIs. Public documentation establishes capability, not Gonarra's right to retain/redistribute every response; commercial/legal approval and a measured benchmark are required.
- [Google Places policy](https://developers.google.com/maps/documentation/places/web-service/policies) generally prohibits prefetching/caching/storing Places content outside stated exceptions while allowing place IDs to be retained. Treat it as attributed runtime enrichment, not the canonical catalog.
- [Google Routes](https://developers.google.com/maps/documentation/routes/reference/rest) supplies route/matrix measurements. Route values remain provider observations with mode/time/freshness, not model facts.

For provider selection, sample at least 100 POIs and 100 routes across the launch cities. Score canonical match, public-entrance accuracy, address quality after administrative changes, closed/duplicate rate, walking/car/two-wheeler coverage where applicable, latency, failure rate, attribution, storage rights, refresh mechanics and projected cost. Keep raw benchmark evidence separate from published catalog content. Re-run before a material contract/API version change.

## Questions and method

- Can Vietnamese- and English-speaking travelers create a feasible short trip and recognize closures, excessive walking and missing evidence using Plan Health?
- How much editing is needed to change one day while preserving valued stops? Observe HA-02, identify unintended changes and ask users to explain the difference between preview and Save.
- Can a traveler use the execution card to find an entrance, show a driver the address and distinguish verified from stale information? Evaluate contextual answers at claim level.

Use interviews to refine assumptions. Compare planning outcomes against a deterministic scheduler given identical candidates, facts, modes and daily windows. Freeze tuning and held-out sets separately by provider release, source and publication revision to prevent near-duplicates. Include multiple cities, both locales, unknown facts, source conflicts, stale/closed candidates, distractors, adversarial instructions and correct refusals. Record model, embedding, prompt, decoding settings, catalog manifest, provider configuration and device/network conditions.

Report task completion, time, critical errors, edit effort, perceived trust and the standard ten-item System Usability Scale separately. For data/model evaluation report import rejection/duplicate rates, source/freshness coverage, schema/ID validity, fabricated-field rate, feasible plan rate, lock violations, supported claims, answerable coverage, correct and false refusals, latency, provider failures and cost. Human reviewers check whether each citation supports the actual field or claim.

## Ethics and evidence

Agree recruitment criteria, sample size, thresholds, consent, retention and withdrawal with the supervisor before recruitment. Use voluntary participation, synthetic accounts and non-sensitive scenarios. De-identify observations and obtain permission before publishing quotes or images. Separate prototype, fixture, live-provider and physical-device results. Report failed tasks, small-sample limitations, prior travel knowledge and language/device effects. Version the evaluation report with its fixtures and build identifier. Retain identifiable participant evidence only in approved research storage.
