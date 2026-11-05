/**
 * App-facing domain types. Field names are the contract's snake_case names. The raw contract types are generated into
 * `schema.d.ts` (`npm run gen:api`, openapi-typescript) from docs/04-design/api/openapi.yaml; this file narrows them
 * (string enums, per-op unions) and adds the architecture 1.0 trust-label fields (`trust_level`, `web_source`, new
 * stream stages) that the 0.4 contract file does not carry yet. Marked "1.0 (not yet in openapi.yaml)" below.
 */

/** UUID string. */
export type Uuid = string;
/** ISO 8601 date, e.g. `2027-01-16`. */
export type IsoDate = string;
/** ISO 8601 date-time with offset, e.g. `2027-01-16T08:00:00+07:00`. */
export type IsoDateTime = string;
/** `HH:MM`, 24-hour (LocalTime). */
export type LocalTime = string;

export type Locale = 'vi' | 'en';
export type TravelMode = 'WALK' | 'DRIVE';
export type Pace = 'RELAXED' | 'BALANCED' | 'PACKED';
export type TripStatus = 'DRAFT' | 'SAVED';
export type PlanHealth = 'GOOD' | 'WARNING' | 'BLOCKED';

/**
 * City `code` values (schema.sql `ck_cities_code_format`, kebab-case). The FYP release enables Đà Nẵng only; Hội An is
 * an area of Đà Nẵng (2025 merger), not a city. Hà Nội, TP.HCM and Huế are roadmap.
 */
export type CityCode = 'da-nang' | 'ha-noi' | 'ho-chi-minh-city' | 'hue';

/** The city the app opens on and falls back to. */
export const DEFAULT_CITY_CODE: CityCode = 'da-nang';

/**
 * 1.0 (not yet in openapi.yaml): trust label on stops, places and citations (architecture §5, FR-098). `VERIFIED` =
 * published catalog place / reviewed source; `WEB_UNVERIFIED` = found on the web by the research agent, not reviewed.
 */
export type TrustLevel = 'VERIFIED' | 'WEB_UNVERIFIED';

/** 1.0 (not yet in openapi.yaml): provenance of a `WEB_UNVERIFIED` stop. */
export type WebSource = {
  url: string;
  fetched_at: IsoDateTime;
  candidate_id: Uuid;
};

export type KnowledgeState = 'KNOWN' | 'UNKNOWN' | 'NOT_APPLICABLE';
/** STALE when verified_at is more than 180 days before today (ASM-008). */
export type Freshness = 'CURRENT' | 'STALE';

export type PageInfo = {
  /** Null on the last page. */
  next_cursor: string | null;
};

export type Money = {
  /** Decimal string, e.g. `120000`. */
  amount: string;
  /** ISO 4217, e.g. `VND`. */
  currency: string;
};

export type Attribution = {
  publisher: string;
  attribution_text: string;
  license_code?: string | null;
  homepage_url?: string | null;
};

export type City = {
  id: Uuid;
  code: CityCode;
  name_vi: string;
  name_en: string;
  time_zone: 'Asia/Ho_Chi_Minh';
  /** Map centre for a view with no stops (OQ-109); null when no boundary is recorded. */
  centre?: GeoPoint | null;
};

export type GeoPoint = {
  latitude: number;
  longitude: number;
};

export type Media = {
  media_asset_id: Uuid;
  url: string;
  width_px?: number | null;
  height_px?: number | null;
  alt_text?: string | null;
  creator?: string | null;
  license_code: string;
  attribution_text: string;
};

/** `PlaceSummary` in the contract (API-010 items). */
export type Place = {
  id: Uuid;
  city_id: Uuid;
  slug: string;
  category_code: string;
  /** Vietnamese name, always present (FR-076). */
  name_vi: string;
  /** Name in the requested locale. */
  name: string;
  short_description?: string | null;
  location: GeoPoint;
  visit_minutes_suggested?: number | null;
  catalog_publication_id: Uuid;
  thumbnail: Media | null;
  /** 1.0: always `VERIFIED` for a published place; absent from 0.4 servers. */
  trust_level?: TrustLevel;
};

export type PlaceSummaryPage = PageInfo & { items: Place[] };

export type Category = {
  code: string;
  name_vi: string;
  name_en: string;
  sort_order: number;
};

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
 * shapes are PROVISIONAL (used by fixtures and UI) until the API defines them. Confirm before relying on them.
 */
export type HoursValue = { intervals: { open: LocalTime; close: LocalTime }[] };
export type MoneyValue = Money;
export type TextValue = { text: string };
export type LocationValue = GeoPoint;
export type FactValue = HoursValue | MoneyValue | TextValue | LocationValue;

/** One operational fact. UNKNOWN is never collapsed into an empty value (FR-006); `value` only when KNOWN. */
export type PlaceFact = {
  place_fact_id?: Uuid;
  field_code: FactFieldCode | (string & {});
  knowledge_state: KnowledgeState;
  value?: FactValue | string | null;
  verified_at?: IsoDate | null;
  valid_until?: IsoDate | null;
  freshness: Freshness;
  sources: Citation[];
};

/** `PlaceDetail` (API-011 `GET /v1/places/{place_id}`). */
export type PlaceDetail = Place & {
  name_en: string;
  description?: string | null;
  visit_minutes_min?: number | null;
  visit_minutes_max?: number | null;
  entrance_location?: GeoPoint | null;
  publication_revision: number;
  published_at?: IsoDateTime;
  facts: PlaceFact[];
  media?: Media[];
  /** Every source whose data is shown (FR-008). */
  attributions: Attribution[];
};

/** `PlaceCard` (API-017, a stop of a trip). */
export type PlaceCard = {
  stop_id: Uuid;
  place_id: Uuid;
  catalog_publication_id?: Uuid;
  name_vi: string;
  name_en: string;
  /** Vietnamese address for a driver, or UNKNOWN (FR-052). */
  address_vi: PlaceFact;
  /** Verified entrance location, or UNKNOWN (FR-053). */
  entrance: PlaceFact;
  directions: {
    target: 'ENTRANCE' | 'PLACE_POSITION';
    google_maps_url: string;
    apple_maps_url: string;
  };
  /** Runtime-only Google Places data; omitted when unavailable (ADR-006). Never stored. */
  live_status?: {
    open_now?: boolean | null;
    retrieved_at: IsoDateTime;
    attribution_text: string;
  };
  attributions?: Attribution[];
};

export type ConflictType =
  | 'CLOSED_AT_PLANNED_TIME'
  | 'LEG_UNAVAILABLE'
  | 'DAY_WINDOW_EXCEEDED'
  | 'OPENING_HOURS_UNKNOWN'
  | 'FACT_STALE'
  | 'MUST_SEE_NOT_INCLUDED';

export type Conflict = {
  type: ConflictType;
  severity: 'BLOCKING' | 'WARNING';
  message?: string;
};

export type Stop = {
  /** Stable across preview revisions and into the saved trip_stops row. */
  id: Uuid;
  /** Published place; null for a `WEB_UNVERIFIED` stop (1.0). */
  place_id: Uuid | null;
  /** Null for a `WEB_UNVERIFIED` stop (1.0). */
  catalog_publication_id: Uuid | null;
  /** 1.0 (not yet in openapi.yaml). */
  trust_level: TrustLevel;
  /** 1.0: present only when `trust_level` is `WEB_UNVERIFIED`. */
  web_source?: WebSource | null;
  ordinal: number;
  planned_arrival?: IsoDateTime | null;
  planned_departure?: IsoDateTime | null;
  visit_minutes: number;
  is_locked: boolean;
  name_vi: string;
  name: string;
  location: GeoPoint;
  /** AI-written reason for the selection (preview only). */
  rationale?: string | null;
  conflicts?: Conflict[];
};

export type LegAvailability = 'AVAILABLE' | 'UNAVAILABLE' | 'EXPIRED';

export type Leg = {
  from_stop_id: Uuid;
  to_stop_id: Uuid;
  travel_mode: TravelMode;
  availability: LegAvailability;
  /** Google Routes only; null when unavailable. */
  distance_m?: number | null;
  duration_s?: number | null;
  measured_at?: IsoDateTime | null;
  conflicts?: Conflict[];
};

/** `ItineraryDay` in the contract. */
export type Day = {
  /** Null inside a preview snapshot. */
  trip_day_id?: Uuid | null;
  day_index: 1 | 2 | 3;
  day_window_start?: LocalTime;
  day_window_end?: LocalTime;
  stops: Stop[];
  legs: Leg[];
};

export type PlanningPreferences = {
  pace?: Pace;
  interest_category_codes?: string[];
  allowed_modes?: TravelMode[];
  day_start_time?: LocalTime;
  day_end_time?: LocalTime;
  must_see_place_ids?: Uuid[];
};

/** API-004 `GET /v1/me/preferences`. */
export type Preferences = {
  locale: Locale;
  pace?: Pace | null;
  interest_category_codes: string[];
  allowed_modes: TravelMode[];
  day_start_time?: LocalTime | null;
  day_end_time?: LocalTime | null;
  ai_notice_acknowledged_at?: IsoDateTime | null;
  updated_at?: IsoDateTime | null;
};

/** API-012 `POST /v1/trips` body. */
export type TripCreate = {
  city_id: Uuid;
  title?: string | null;
  start_date: IsoDate;
  day_count: 1 | 2 | 3;
};

export type Trip = {
  id: Uuid;
  city_id: Uuid;
  title?: string | null;
  start_date: IsoDate;
  day_count: 1 | 2 | 3;
  status: TripStatus;
  revision: number;
  saved_at?: IsoDateTime | null;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
};

export type TripPage = PageInfo & { items: Trip[] };

export type TripDetail = Trip & {
  planning_preferences?: PlanningPreferences | null;
  /** Saved itinerary; empty for a DRAFT trip. */
  days: Day[];
  active_preview_id?: Uuid | null;
};

export type PlanPreviewCreate = {
  source: 'GENERATE' | 'SAVED_ITINERARY';
  expected_trip_revision: number;
  locale: Locale;
  request_text?: string | null;
  preferences?: PlanningPreferences;
};

export type ClarificationRequired = {
  outcome: 'CLARIFICATION_REQUIRED';
  missing_fields: ('city' | 'start_date' | 'day_count')[];
  message: string;
};

export type PlanPreview = {
  id: Uuid;
  trip_id: Uuid;
  base_trip_revision: number;
  head_revision: number;
  /** Revision represented by this body. */
  preview_revision: number;
  parent_revision?: number | null;
  status: 'ACTIVE' | 'SAVED' | 'DISCARDED' | 'EXPIRED';
  origin: 'GENERATED' | 'MANUAL_EDIT' | 'DAY_REGENERATED' | 'REPAIRED';
  plan_health: PlanHealth;
  health_reasons?: Conflict[];
  expires_at: IsoDateTime;
  days: Day[];
  assumptions?: string[];
  model_version?: string | null;
  prompt_version?: string | null;
  corpus_revision?: number | null;
  created_at?: IsoDateTime;
};

export type ErrorDetail = {
  code: string;
  message: string;
  retryable?: boolean;
  request_id?: string | null;
  context?: Record<string, unknown>;
};

export type ErrorResponse = { error: ErrorDetail };

/**
 * Planning stream stages in order (architecture §5). RESEARCHING and VERIFYING_WEB_PLACES run only when the catalog pool
 * is thin; WRITING writes rationales. 1.0: those three are not yet in openapi.yaml.
 */
export type PlanningStage =
  | 'VALIDATING_REQUEST'
  | 'SELECTING_PLACES'
  | 'RESEARCHING'
  | 'VERIFYING_WEB_PLACES'
  | 'ROUTING'
  | 'SCHEDULING'
  | 'CHECKING_HEALTH'
  | 'WRITING';

export const PLANNING_STAGES: readonly PlanningStage[] = [
  'VALIDATING_REQUEST', 'SELECTING_PLACES', 'RESEARCHING', 'VERIFYING_WEB_PLACES', 'ROUTING', 'SCHEDULING', 'CHECKING_HEALTH', 'WRITING',
];

/** Stages that appear only when the research path runs; screens show them once reported. */
export const OPTIONAL_PLANNING_STAGES: readonly PlanningStage[] = ['RESEARCHING', 'VERIFYING_WEB_PLACES'];

/** 1.0: progress `detail` (counts only; no place names or user text). */
export type StageDetail = { catalog_candidates?: number; web_candidates?: number; verified?: number };

/** One SSE `data:` payload of the planning stream; terminal: preview_ready, clarification_required, error. */
export type PlanningStreamEvent =
  | { type: 'progress'; stage: PlanningStage; agent?: string | null; detail?: StageDetail | null }
  | { type: 'clarification_required'; clarification: ClarificationRequired }
  | { type: 'preview_ready'; preview_id: Uuid; preview_revision: number; plan_health: PlanHealth }
  | { type: 'error'; error: ErrorDetail };

export type CitationSection = 'OVERVIEW' | 'HISTORY' | 'HIGHLIGHTS' | 'VISIT_TIPS' | 'ETIQUETTE' | 'ACCESS';

/** 1.0 (ADR-010): kind of evidence a citation points to. */
export type EvidenceKind = 'FACT' | 'CHUNK' | 'WEB';

export type Citation = {
  source_revision_id: Uuid;
  knowledge_chunk_id?: Uuid | null;
  /** Section of the cited chunk; null for a fact citation. */
  section?: CitationSection | null;
  place_fact_id?: Uuid | null;
  publisher: string;
  title?: string | null;
  locator?: string | null;
  /** Reviewed date; null for a `WEB_UNVERIFIED` citation (1.0). */
  verified_at: IsoDate | null;
  /** 1.0 (not yet in openapi.yaml). */
  trust_level: TrustLevel;
  /** 1.0: FACT, CHUNK or WEB. */
  evidence_kind?: EvidenceKind | null;
  /** 1.0: source page URL of a WEB citation. */
  url?: string | null;
  /** 1.0: when a WEB citation's page was fetched. */
  fetched_at?: IsoDateTime | null;
};

/** `ANSWERED_WEB_UNVERIFIED` is 1.0 (ADR-010 web fallback), not yet in openapi.yaml. */
export type GuideAnswerStatus = 'ANSWERED' | 'ANSWERED_WEB_UNVERIFIED' | 'INSUFFICIENT_EVIDENCE' | 'NOT_RECOGNISED';

export type GuideMessage = {
  id: Uuid;
  seq: number;
  role: 'TRAVELER' | 'ASSISTANT';
  input_mode?: 'TEXT' | 'VOICE_TRANSCRIPT' | 'PHOTO' | null;
  content: string;
  answer_status?: GuideAnswerStatus | null;
  citations?: Citation[];
  created_at: IsoDateTime;
};

export type GuideMessagePage = PageInfo & { items: GuideMessage[] };

export type GuideSessionCreate = {
  place_id: Uuid;
  trip_id?: Uuid | null;
  locale: Locale;
};

export type GuideSession = {
  id: Uuid;
  trip_id?: Uuid | null;
  place_id: Uuid;
  locale: Locale;
  expires_at?: IsoDateTime | null;
  created_at: IsoDateTime;
};

export type GuideQuestion = {
  content: string;
  input_mode: 'TEXT' | 'VOICE_TRANSCRIPT';
};

/** Guide stream stages in order (architecture §5); SEARCHING_WEB runs only for the web fallback. VALIDATING and SEARCHING_WEB are 1.0. */
export type GuideStage = 'VALIDATING' | 'RETRIEVING' | 'SEARCHING_WEB' | 'ANSWERING';

/** One SSE `data:` payload of the Guide stream; `text` carries a delta; `result` and `error` are terminal. */
export type GuideStreamEvent =
  | { type: 'progress'; stage: GuideStage }
  | { type: 'text'; delta: string }
  | { type: 'result'; message: GuideMessage }
  | { type: 'error'; error: ErrorDetail };

export type HandoffKind = 'STAY' | 'ACTIVITY' | 'TRANSPORT';

export type HandoffLink = {
  kind: HandoffKind;
  /** STAY: agoda | booking_com; ACTIVITY: klook; TRANSPORT: twelve_go. */
  partner_key: 'agoda' | 'booking_com' | 'klook' | 'twelve_go';
  partner_display_name: string;
  url: string;
  city_id?: Uuid;
  start_date?: IsoDate;
  end_date?: IsoDate;
};

/** API-003 `GET /v1/me` (generated from openapi.yaml; unchanged since 0.1). */
export type Identity = import('./schema').components['schemas']['IdentityResponse'];
