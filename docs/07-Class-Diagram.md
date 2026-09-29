# Class Diagram — Danang TourGuide (domain)

Static structure for the **domain / persistence** layer (Nest entities). Not every DTO.

```mermaid
classDiagram
  class User {
    +id: UUID
    +email: string
    +googleSub: string
    +language: vi|en
    +createdAt: Date
  }

  class GuestSession {
    +id: UUID
    +deviceId: string
    +expiresAt: Date
  }

  class MediaAsset {
    +id: UUID
    +ownerUserId: UUID
    +s3Key: string
    +kind: user_ref|poi
    +status: uploaded|ready|failed
    +guestId: UUID
  }

  class ImageAnalysis {
    +mediaId: UUID
    +tags: json
    +embedding: vector
  }

  class PreferenceProfile {
    +userId: UUID
    +guestId: UUID
    +attributes: json
    +confirmedAt: Date
    +version: int
  }

  class Place {
    +id: UUID
    +name: string
    +category: string
    +description: string
    +location: Point
    +openingHours: json
    +avgDurationMin: int
    +priceLevel: int
    +attributes: json
    +experience: json
    +contextFlags: json
  }

  class PlaceImage {
    +id: UUID
    +placeId: UUID
    +s3Key: string
    +embedding: vector
    +isHero: bool
  }

  class KnowledgeChunk {
    +id: UUID
    +placeId: UUID
    +text: string
    +source: string
    +sourceUrl: string
    +verifiedAt: Date
    +embedding: vector
  }

  class SavedPlace {
    +userId: UUID
    +placeId: UUID
    +collectionId: UUID
  }

  class Collection {
    +id: UUID
    +userId: UUID
    +name: string
  }

  class Trip {
    +id: UUID
    +userId: UUID
    +startDate: Date
    +endDate: Date
    +pace: enum
    +budgetLevel: int
    +status: enum
  }

  class TripDay {
    +id: UUID
    +tripId: UUID
    +dayIndex: int
    +date: Date
  }

  class TripStop {
    +id: UUID
    +dayId: UUID
    +placeId: UUID
    +seq: int
    +arrival: time
    +departure: time
    +durationMin: int
    +travelToNextMin: int
    +status: upcoming|current|completed|skipped
    +routeStatus: fresh|estimated|stale
  }

  class RecommendationRun {
    +id: UUID
    +userId: UUID
    +createdAt: Date
  }

  class MatchEvidence {
    +runId: UUID
    +placeId: UUID
    +pathNodes: json
    +scores: json
  }

  class VisitFeedback {
    +userId: UUID
    +placeId: UUID
    +rating: loved|okay|not_for_me
    +reasons: string[]
  }

  class ArrivalEvent {
    +id: UUID
    +tripStopId: UUID
    +method: gps|manual|simulated
    +detectedAt: Date
  }

  class TasteJob {
    +id: UUID
    +status: queued|processing|succeeded|failed
  }

  User "1" --> "0..1" PreferenceProfile
  User "1" --> "*" MediaAsset
  User "1" --> "*" Trip
  User "1" --> "*" SavedPlace
  GuestSession "0..1" --> "0..1" PreferenceProfile : pending merge
  MediaAsset "1" --> "0..1" ImageAnalysis
  Place "1" --> "*" PlaceImage
  Place "1" --> "*" KnowledgeChunk
  Collection "1" --> "*" SavedPlace
  Trip "1" --> "*" TripDay
  TripDay "1" --> "*" TripStop
  TripStop "*" --> "1" Place
  TripStop "1" --> "0..1" ArrivalEvent
  RecommendationRun "1" --> "*" MatchEvidence
  MatchEvidence "*" --> "1" Place
  User "1" --> "*" VisitFeedback
  MediaAsset "1" --> "0..*" TasteJob : input
```

## Relationships (cardinality)

| From | To | Type |
|------|-----|------|
| User | Trip | 0..* |
| Trip | TripDay | 0..* composition while draft |
| TripDay | TripStop | 0..* composition while draft |
| TripStop | Place | *..1 |
| Place | PlaceImage | 1..* |
| User | PreferenceProfile | 1..0..1 |
| RecommendationRun | MatchEvidence | 1..* |

The diagram is a domain overview. SQL owns exact nullability and foreign keys; `routeStatus` may be computed in the API rather than persisted. Guest and user owners are mutually exclusive in the SQL schema. `TasteJob` ↔ media is logically many-to-many input membership and needs an association table or JSON snapshot if implemented as persistent references.

## Services (stereotypes, not all drawn)

`RecommendationService`, `ItineraryBuilder`, `RagService`, `TasteAnalyzer` as `<<service>>` depending on repositories.
