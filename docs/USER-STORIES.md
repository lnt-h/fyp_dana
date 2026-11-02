# User stories and acceptance criteria

Each story is a V1 delivery slice. Given/When/Then examples define observable behavior and trace to the [use cases](USE-CASES.md) and [product requirements](PRD.md).

| Story | User need | Given / When / Then |
|---|---|---|
| US-00 · UC-00 · FR-00 | As a curator, I want imported POIs to remain unpublished until their identity, evidence, bilingual content and rights are reviewed. | Given an approved provider release, when I import it twice, then staging is idempotent and the current catalog is unchanged. A candidate with a disallowed provider field, ambiguous identity, unsupported claim or missing media rights cannot publish. |
| US-01 · UC-01 · FR-01 | As a traveler, I want local and translated place names so I can find the same destination in either language. | Given a reviewed alias, when I search the selected city, then the published POI appears with the correct entrance and source. An unpublished match stays hidden. |
| US-02 · UC-02 · FR-02 | As a first-time visitor, I want a proposal that fits my dates and pace. | Given an incomplete request, when I generate, then I can supply the required details. A valid response contains only IDs from the selected city's published manifest; injected or model-created place/fact values are rejected. |
| US-03 · UC-02 · FR-03 | As a traveler on foot, I want to see whether my day fits. | Given a required WALK leg without a route, when I inspect the day, then both views identify the issue, leave travel measurements unknown and block Save. |
| US-04 · UC-03 · FR-04 | As a traveler with a must-see stop, I want to keep it while changing my afternoon. | Given the HA-02 baseline, when I lock the stop and regenerate day two, then its identity, day, duration and relative lock order survive and day one is unchanged. |
| US-05 · UC-03 · FR-05 | As the trip owner, I want to decide which edits become final. | Given a valid preview, when I leave before Save or regeneration fails, then the accepted trip remains intact. When I explicitly Save and retry that request, only one revision is accepted. |
| US-06 · UC-04 · FR-05/06 | As a traveler at my destination, I want a usable local address. | Given a saved stop, when I open its card, then I can show the driver a reviewed address or open external directions. Missing prices stay unknown. |
| US-07 · UC-05 · FR-06 | As a visitor, I want to know where a Guide answer comes from. | Given a scoped question, when reviewed evidence supports it, then I receive an answer and sources in my locale. Otherwise I see insufficient_evidence. |
| US-08 · UC-06 · FR-07 | As an account holder, I want control over my private trips. | Given another owner's trip ID, when a user requests it, then access is denied before provider calls. Given my own account, when I confirm deletion after reauthentication, then sessions are revoked and cleanup status is shown. |

A story is ready for acceptance when its positive and exception paths can be exercised against named fixtures. Record build, locale, environment, provider mode and observed result. Use [test coverage](TESTING.md) for release evidence.
