/**
 * Hand-written mirror of docs/04-design/api/openapi.yaml; replace with openapi-typescript output (ADR-001) when the
 * API lands. Field names are the contract's snake_case names. Only the schemas UI steps 1–5 need are mirrored.
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

/** City `code` values of the five launch cities (schema.sql `ck_cities_code_format`, kebab-case). */
export type CityCode = 'ha-noi' | 'ho-chi-minh-city' | 'da-nang' | 'hoi-an' | 'hue';

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
  place_id: Uuid;
  catalog_publication_id: Uuid;
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

export type PlanningStage = 'VALIDATING_REQUEST' | 'SELECTING_PLACES' | 'ROUTING' | 'SCHEDULING' | 'CHECKING_HEALTH';

/** One SSE `data:` payload of the planning stream; terminal: preview_ready, clarification_required, error. */
export type PlanningStreamEvent =
  | { type: 'progress'; stage: PlanningStage }
  | { type: 'clarification_required'; clarification: ClarificationRequired }
  | { type: 'preview_ready'; preview_id: Uuid; preview_revision: number; plan_health: PlanHealth }
  | { type: 'error'; error: ErrorDetail };

export type CitationSection = 'OVERVIEW' | 'HISTORY' | 'HIGHLIGHTS' | 'VISIT_TIPS' | 'ETIQUETTE' | 'ACCESS';

export type Citation = {
  source_revision_id: Uuid;
  knowledge_chunk_id?: Uuid | null;
  /** Section of the cited chunk; null for a fact citation. */
  section?: CitationSection | null;
  place_fact_id?: Uuid | null;
  publisher: string;
  title?: string | null;
  locator?: string | null;
  verified_at: IsoDate;
};

export type GuideAnswerStatus = 'ANSWERED' | 'INSUFFICIENT_EVIDENCE' | 'NOT_RECOGNISED';

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

/** One SSE `data:` payload of the Guide stream; `text` carries a delta; `result` and `error` are terminal. */
export type GuideStreamEvent =
  | { type: 'progress'; stage: 'RETRIEVING' | 'ANSWERING' }
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
