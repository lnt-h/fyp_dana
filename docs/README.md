# Documentation index

The [BRD](BRD.md) defines business outcomes and release gates. The [PRD](PRD.md) owns V1 scope and functional requirements. For implementation status see the [repository overview](../README.md).

| Question | Contract owner |
|---|---|
| How does each actor complete a task or recover from failure? | [Use cases](USE-CASES.md) |
| What can the delivery team accept for each user need? | [User stories](USER-STORIES.md) |
| Which relations, keys and transactions preserve trip integrity? | [Database design](DATABASE-DESIGN.md) |
| Where does each component run, how does trusted data enter the system, and how does planning reach explicit Save? | [Architecture and Mermaid workflows](ARCHITECTURE.md) |
| What can mobile send, receive, retry and Save? | [API](API.md) |
| Where does POI data come from, what may be stored and what makes a place publishable? | [Data supply, provenance and publication](DATA.md) |
| Who can access data, and what happens on deletion? | [Security and privacy](SECURITY.md) |
| Which scenario demonstrates each requirement? | [Testing and traceability](TESTING.md) |
| How do I run the current app and build future releases? | [Development](DEVELOPMENT.md) |
| How will the FYP evaluate usefulness and trust? | [Research](RESEARCH.md) |

When a contract changes, update its owner document, affected acceptance cases and the evidence tracker in the same change. HA-02 is the shared planner acceptance case.
