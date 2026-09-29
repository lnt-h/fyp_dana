# Component Diagram — Danang TourGuide

UML 2.0. Internal components inside **Danang TourGuide API**; app and externals outside.

```mermaid
flowchart LR
  subgraph Device["Mobile App (Expo)"]
    UI[Screens + Expo Router]
  end

  subgraph API["NestJS Modular Monolith"]
    Auth[Auth]
    User[User]
    Media[Media]
    Pref[Preference]
    Place[Place]
    Search[Search]
    Rec[Recommendation]
    Saved[Saved]
    Trip[Trip]
    Itin[Itinerary]
    Route[Routing]
    Loc[Location]
    Ctx[Context]
    Guide[Guide]
    RAG[RAG]
    AI[AI Facade]
    Wx[Weather]
    Ntf[Notification]
  end

  subgraph Data["Data plane"]
    PG[(PostgreSQL PostGIS pgvector)]
    RD[(Redis)]
    S3[S3]
  end

  subgraph Ext["External"]
    Gem[Gemini]
    Maps[Google Maps/Routes]
    WAPI[Weather API]
    TTS[TTS]
    GO[Google OAuth]
  end

  UI -->|REST JWT| Auth
  UI --> Media
  UI --> Pref
  UI --> Rec
  UI --> Place
  UI --> Search
  UI --> Saved
  UI --> Trip
  UI --> Loc
  UI --> Guide
  UI --> Ctx

  Pref --> AI
  Rec --> AI
  Rec --> Place
  Rec --> Wx
  Itin --> Route
  Itin --> Place
  Trip --> Itin
  Guide --> TTS
  Guide --> RAG
  Ctx --> RAG
  RAG --> AI
  AI --> Gem
  Route --> Maps
  Wx --> WAPI
  Auth --> GO
  Media --> S3
  Auth --> PG
  Place --> PG
  Rec --> PG
  Pref --> PG
  Rec --> RD
  Wx --> RD
  Route --> RD
```

## Provided / required interfaces (logical)

| Component | Provides | Requires |
|-----------|----------|----------|
| Auth | `IAuth` login, JWT | Google, User store |
| Media | `IMedia` signed upload | S3 |
| Preference | `ITaste` jobs, DNA CRUD | Media, AI, PG |
| Recommendation | `IForYou`, `IExplain` | PG vectors, Place, Weather, Location |
| Itinerary | `IBuild`, `IMutateStops` | Place, Routing |
| RAG | `IRetrieve` | pgvector chunks, AI |
| Guide | `INarrative`, `IAudio` | RAG/DB text, TTS |
| Routing | `ILegCost` | Maps + Redis |

## Design rule

Mobile **does not** call Gemini. All AI behind `AI Facade` for keys, timeouts, and logging.

The app calls `/ai/ask` through the Context module; RAG is an internal interface. For the small V1 corpus, Recommendation and RAG use exact pgvector queries; HNSW is a measured growth option. Auth and owner checks protect all user/guest records, including evidence and media. External TTS failure returns narrative text. Async taste/TTS jobs have database-backed status and bounded retry rather than an implied fire-and-forget call.
