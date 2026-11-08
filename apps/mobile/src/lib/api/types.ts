/**
 * App-facing domain types. Field names are the contract's snake_case names. The raw contract types are generated into
 * `schema.d.ts` (`npm run gen:api`, openapi-typescript) from docs/04-design/api/openapi.yaml (1.0.0). Most types here
 * are aliases of the generated schemas; app-level types remain only where the app needs a narrower shape (city codes,
 * 1–3 day counts, fact value shapes, discriminated stream events, scoped Guide session bodies).
 */
import type { components } from './schema';

type Schemas = components['schemas'];

/** UUID string. */
export type Uuid = string;
/** ISO 8601 date, e.g. `2027-01-16`. */
export type IsoDate = string;
/** ISO 8601 date-time with offset, e.g. `2027-01-16T08:00:00+07:00`. */
export type IsoDateTime = string;
/** `HH:MM`, 24-hour (LocalTime). */
export type LocalTime = Schemas['LocalTime'];

export type Locale = Schemas['Locale'];
export type TravelMode = Schemas['TravelMode'];
export type Pace = Schemas['Pace'];
export type TripStatus = Schemas['TripStatus'];
export type PlanHealth = Schemas['PlanHealth'];
export type KnowledgeState = Schemas['KnowledgeState'];
/** STALE when verified_at is more than 180 days before today (ASM-008). */
export type Freshness = Schemas['Freshness'];

/**
 * City `code` (openapi 1.0.3 `City.code` enum). Gonarra covers Đà Nẵng only (owner 2026-11-08); Hội An is an area of
 * Đà Nẵng (2025 merger), not a city.
 */
export type CityCode = Schemas['City']['code'];

/** The city the app opens on and falls back to. */
export const DEFAULT_CITY_CODE: CityCode = 'da-nang';

/**
 * Trust label on stops, places and citations (architecture §5, FR-098, DEC-022). `VERIFIED` = passed Gonarra's
 * automated source checks ("Source-checked"); `WEB_UNVERIFIED` = found on the web by the research agent, not
 * source-checked. There is no human review.
 */
export type TrustLevel = Schemas['TrustLevel'];

/** Provenance of a `WEB_UNVERIFIED` stop. */
export type WebSource = Schemas['WebSource'];

export type PageInfo = Schemas['PageInfo'];
export type Money = Schemas['Money'];
export type Attribution = Schemas['Attribution'];
export type GeoPoint = Schemas['GeoPoint'];
export type Media = Schemas['Media'];
/** Named area of a city (e.g. Hội An inside Đà Nẵng). */
export type Area = Schemas['Area'];
export type ClosureRule = Schemas['ClosureRule'];

/** `City`, narrowed to the known city codes and the single time zone. */
export type City = Omit<Schemas['City'], 'code' | 'time_zone'> & {
  code: CityCode;
  time_zone: 'Asia/Ho_Chi_Minh';
};

/**
 * Category codes (schema.sql seed; API returns UPPER_CASE). `category_code` stays `string` on places so a new server
 * category does not break parsing; screens map unknown codes to a generic icon/label.
 */
export type CategoryCode =
  | 'HERITAGE'
  | 'MUSEUM'
  | 'RELIGIOUS_SITE'
  | 'BEACH'
  | 'NATURE'
  | 'VIEWPOINT'
  | 'MARKET'
  | 'FOOD'
  | 'CAFE'
  | 'NIGHTLIFE'
  | 'THEME_PARK'
  | 'CRAFT_VILLAGE';

export const CATEGORY_CODES: readonly CategoryCode[] = [
  'HERITAGE', 'MUSEUM', 'RELIGIOUS_SITE', 'BEACH', 'NATURE', 'VIEWPOINT', 'MARKET', 'FOOD', 'CAFE', 'NIGHTLIFE', 'THEME_PARK', 'CRAFT_VILLAGE',
];

export const isCategoryCode = (code: string | null | undefined): code is CategoryCode =>
  !!code && (CATEGORY_CODES as readonly string[]).includes(code);

/** `PlaceSummary` in the contract (API-010 items). */
export type Place = Schemas['PlaceSummary'];
export type PlaceSummaryPage = Schemas['PlaceSummaryPage'];
export type Category = Schemas['Category'];

/** `fact_fields.code` seed (schema.sql). */
export type FactFieldCode =
  | 'OPENING_HOURS'
  | 'ADMISSION_PRICE'
  | 'ADDRESS_VI'
  | 'ENTRANCE_LOCATION'
  | 'PAYMENT_METHODS'
  | 'DRESS_CODE'
  | 'ACCESS_RULES';

/*
 * Fact `value` shapes per value_kind. The contract only says "object, shape depends on fact_fields.value_kind"; these
 * shapes are PROVISIONAL (used by the UI) until the API defines them. Confirm before relying on them.
 */
export type HoursValue = { intervals: { open: LocalTime; close: LocalTime }[] };
export type MoneyValue = Money;
export type TextValue = { text: string };
export type LocationValue = GeoPoint;
/** ADMISSION_PRICE from the pipeline (1.0.4, DEC-028): free entry, or VND adult/child prices (`amount` = adult). */
export type PriceValue = { free: boolean; currency?: string; adult?: number; child?: number; amount?: string };
export type FactValue = HoursValue | MoneyValue | TextValue | LocationValue | PriceValue;

/**
 * One operational fact. UNKNOWN is never collapsed into an empty value (FR-006); `value` only when KNOWN. Narrows the
 * contract's untyped `value` to the provisional shapes above.
 */
export type PlaceFact = Omit<Schemas['PlaceFact'], 'field_code' | 'value'> & {
  field_code: FactFieldCode | (string & {});
  value?: FactValue | string | null;
};

/** `PlaceDetail` (API-011 `GET /v1/places/{place_id}`). */
export type PlaceDetail = Omit<Schemas['PlaceDetail'], 'facts'> & { facts: PlaceFact[] };

/** `PlaceCard` (API-017, a stop of a trip). */
export type PlaceCard = Omit<Schemas['PlaceCard'], 'address_vi' | 'entrance'> & {
  /** Vietnamese address for a driver, or UNKNOWN (FR-052). */
  address_vi: PlaceFact;
  /** Source-checked entrance location, or UNKNOWN (FR-053). */
  entrance: PlaceFact;
};

/**
 * Plan Health conflict (13 health types plus the INFO notice `LEG_ESTIMATED`, contract 1.0.2; calendar rules carry
 * `rule_id`/`date`, web stops carry `stop_ids`). Severity INFO is a notice and never a warning.
 */
export type Conflict = Schemas['Conflict'];
export type ConflictType = Conflict['type'];

export const CONFLICT_TYPES: readonly ConflictType[] = [
  'CLOSED_AT_PLANNED_TIME', 'LEG_UNAVAILABLE', 'DAY_WINDOW_EXCEEDED', 'OPENING_HOURS_UNKNOWN', 'FACT_STALE', 'MUST_SEE_NOT_INCLUDED',
  'CLOSED_ON_DATE', 'LEG_MODE_RESTRICTED', 'LUNAR_EVENT_CONFLICT', 'TICKET_VALIDITY', 'SEASONAL_WARNING', 'WEB_PLACE_UNVERIFIED',
  'WEB_PLACE_UNRESOLVED', 'LEG_ESTIMATED',
];

/** Itinerary stop; `place_id`/`catalog_publication_id` are null for a `WEB_UNVERIFIED` stop. */
export type Stop = Schemas['Stop'];
export type Leg = Schemas['Leg'];
export type LegAvailability = Leg['availability'];

type DayIndex = 1 | 2 | 3;

/** `ItineraryDay` in the contract; `day_index` narrowed to 1–3 (one trip = 1–3 days). */
export type Day = Omit<Schemas['ItineraryDay'], 'day_index'> & { day_index: DayIndex };

export type PlanningPreferences = Schemas['PlanningPreferences'];

/** API-004 `GET /v1/me/preferences`. */
export type Preferences = Schemas['Preferences'];

/** API-012 `POST /v1/trips` body. */
export type TripCreate = Omit<Schemas['TripCreate'], 'day_count'> & { day_count: DayIndex };

export type Trip = Omit<Schemas['Trip'], 'day_count'> & { day_count: DayIndex };

export type TripPage = PageInfo & { items: Trip[] };

export type TripDetail = Trip & Omit<Schemas['TripDetail'], keyof Schemas['Trip'] | 'days'> & {
  /** Saved itinerary; empty for a DRAFT trip. */
  days: Day[];
};

export type PlanPreviewCreate = Schemas['PlanPreviewCreate'];
export type ClarificationRequired = Schemas['ClarificationRequired'];

export type PlanPreview = Omit<Schemas['PlanPreview'], 'days'> & { days: Day[] };

/** API-022 body. `acknowledge_web_unverified` must be true when the plan holds a WEB_UNVERIFIED stop (OQ-128). */
export type AcceptPreviewRequest = Schemas['AcceptPreviewRequest'];

export type ErrorDetail = Schemas['ErrorDetail'];
export type ErrorResponse = Schemas['ErrorResponse'];

type PlanningStreamSchema = Schemas['PlanningStreamEvent'];

/**
 * Planning stream stages in order (architecture §5). RESEARCHING runs only when the catalog pool is thin; WRITING only
 * when an AI key is configured (it writes rationales). VERIFYING_WEB_PLACES stays in the contract but is not emitted.
 */
export type PlanningStage = NonNullable<PlanningStreamSchema['stage']>;

export const PLANNING_STAGES: readonly PlanningStage[] = [
  'VALIDATING_REQUEST', 'SELECTING_PLACES', 'RESEARCHING', 'VERIFYING_WEB_PLACES', 'ROUTING', 'SCHEDULING', 'CHECKING_HEALTH', 'WRITING',
];

/** Stages that appear only when the server reports them (research path, AI rationales); screens show them once seen. */
export const OPTIONAL_PLANNING_STAGES: readonly PlanningStage[] = ['RESEARCHING', 'VERIFYING_WEB_PLACES', 'WRITING'];

/** Agent role reporting a stage (`selector`, `researcher`, `grounded_writer`). */
export type PlanningAgent = NonNullable<PlanningStreamSchema['agent']>;

/** Progress `detail` (counts only; no place names or user text). */
export type StageDetail = NonNullable<PlanningStreamSchema['detail']>;

/**
 * One SSE `data:` payload of the planning stream; terminal: preview_ready, clarification_required, error. The contract
 * schema is one flat object with optional fields; this is the discriminated union the app parses into.
 */
export type PlanningStreamEvent =
  | { type: 'progress'; stage: PlanningStage; agent?: PlanningAgent | null; detail?: StageDetail | null }
  | { type: 'clarification_required'; clarification: ClarificationRequired }
  | { type: 'preview_ready'; preview_id: Uuid; preview_revision: number; plan_health: PlanHealth }
  | { type: 'error'; error: ErrorDetail };

export type Citation = Schemas['Citation'];
export type CitationSection = NonNullable<Citation['section']>;
/** ADR-010: kind of evidence a citation points to. */
export type EvidenceKind = Citation['evidence_kind'];

export type GuideMessage = Schemas['GuideMessage'];
export type GuideAnswerStatus = NonNullable<GuideMessage['answer_status']>;
export type GuideMessagePage = Schemas['GuideMessagePage'];

/**
 * API-026 body. Contract `GuideSessionCreate` narrowed per scope: the Guide tab opens a city session (`CITY` +
 * `city_code`), a place card opens a place session (`PLACE` + `place_id`).
 */
export type GuideSessionCreate =
  | { scope: 'CITY'; city_code: CityCode; place_id?: null; trip_id?: Uuid | null; locale: Locale }
  | { scope: 'PLACE'; place_id: Uuid; city_code?: CityCode | null; trip_id?: Uuid | null; locale: Locale };

export type GuideSession = Schemas['GuideSession'];
export type GuideQuestion = Schemas['GuideQuestion'];

/** Guide stream stages in order (architecture §5); SEARCHING_WEB runs only for the web fallback. */
export type GuideStage = NonNullable<Schemas['GuideStreamEvent']['stage']>;

/** One SSE `data:` payload of the Guide stream; `text` carries a delta; `result` and `error` are terminal. */
export type GuideStreamEvent =
  | { type: 'progress'; stage: GuideStage }
  | { type: 'text'; delta: string }
  | { type: 'result'; message: GuideMessage }
  | { type: 'error'; error: ErrorDetail };

export type HandoffKind = Schemas['HandoffKind'];
/** STAY: agoda | booking_com; ACTIVITY: klook; TRANSPORT: twelve_go. */
export type HandoffLink = Schemas['HandoffLink'];
export type HandoffPartner = HandoffLink['partner_key'];

/** `StayPrice` (API-031 item). Runtime only; never cached or stored (FR-081). */
export type StayPrice = Schemas['StayPrice'];
/** `StayPricePage` (API-031). */
export type StayPricePage = Schemas['StayPricePage'];

/** API-003 `GET /v1/me`. */
export type Identity = Schemas['IdentityResponse'];
