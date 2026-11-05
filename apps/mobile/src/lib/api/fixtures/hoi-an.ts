/**
 * FIXTURE DATA — NOT CATALOG DATA.
 *
 * Hand-made sample responses for building UI before the API exists (EXPO_PUBLIC_USE_FIXTURES=1). Places are well-known
 * Hội An landmarks with approximate coordinates; times, distances, durations, hours, prices, addresses and citations are
 * rough illustrations, not Google Routes output and not reviewed facts. Nothing here may be imported into the catalog,
 * shown as verified or used as evidence. IDs are fixed fake UUIDs. Category codes are fixture codes (no seed exists yet).
 *
 * Covers: Home/Explore (cities, categories, places), SCR-022 (preferences), SCR-023 (stream, see source.ts),
 * SCR-024/025 (preview, two variants), SCR-031 (trips), SCR-033 (place detail + place card), SCR-034 (Guide session,
 * history, cited answer, insufficient evidence).
 */
import type {
  Category,
  Citation,
  City,
  Day,
  GuideMessage,
  GuideSession,
  Leg,
  Locale,
  Media,
  Place,
  PlaceCard,
  PlaceDetail,
  PlaceFact,
  PlanPreview,
  Preferences,
  Stop,
  Trip,
  TripDetail,
  Uuid,
} from '../types';

const id = (n: number) => `00000000-0000-4000-8000-${n.toString(16).padStart(12, '0')}`;
const byLocale = (locale: Locale, vi: string, en: string) => (locale === 'vi' ? vi : en);

/* ---------------------------------------------------------------- Cities and categories */

/** Names match the schema.sql reference seed. */
export const fixtureCities: City[] = [
  { code: 'ha-noi', id: id(0x101), name_en: 'Ha Noi', name_vi: 'Hà Nội', time_zone: 'Asia/Ho_Chi_Minh' },
  { code: 'ho-chi-minh-city', id: id(0x102), name_en: 'Ho Chi Minh City', name_vi: 'Thành phố Hồ Chí Minh', time_zone: 'Asia/Ho_Chi_Minh' },
  { code: 'da-nang', id: id(0x103), name_en: 'Da Nang', name_vi: 'Đà Nẵng', time_zone: 'Asia/Ho_Chi_Minh' },
  { code: 'hoi-an', id: id(0x104), name_en: 'Hoi An', name_vi: 'Hội An', time_zone: 'Asia/Ho_Chi_Minh' },
  { code: 'hue', id: id(0x105), name_en: 'Hue', name_vi: 'Huế', time_zone: 'Asia/Ho_Chi_Minh' },
];

/** Default city until the city picker (SCR-020) exists; Hội An is built end to end first. */
export const defaultCity = fixtureCities[3];

export const cityById = (cityId: Uuid) => fixtureCities.find(city => city.id === cityId);

export const fixtureCategories: Category[] = [
  { code: 'heritage', name_en: 'Heritage', name_vi: 'Di sản', sort_order: 1 },
  { code: 'market', name_en: 'Markets & food', name_vi: 'Chợ & ẩm thực', sort_order: 2 },
  { code: 'nature', name_en: 'Nature', name_vi: 'Thiên nhiên', sort_order: 3 },
  { code: 'beach', name_en: 'Beaches', name_vi: 'Biển', sort_order: 4 },
  { code: 'evening', name_en: 'Evening walks', name_vi: 'Dạo buổi tối', sort_order: 5 },
];

/* ---------------------------------------------------------------- Places */

type FixturePlace = {
  pid: number;
  slug: string;
  category_code: string;
  name_vi: string;
  name_en: string;
  short_vi: string;
  short_en: string;
  latitude: number;
  longitude: number;
  visit: number;
};

const places = {
  coveredBridge: { pid: 0x401, slug: 'chua-cau', category_code: 'heritage', name_vi: 'Chùa Cầu', name_en: 'Japanese Covered Bridge', short_vi: 'Cây cầu có mái che, biểu tượng của phố cổ.', short_en: 'The roofed bridge that symbolises the old town.', latitude: 15.87702, longitude: 108.32601, visit: 40 },
  tanKy: { pid: 0x402, slug: 'nha-co-tan-ky', category_code: 'heritage', name_vi: 'Nhà cổ Tấn Ký', name_en: 'Tan Ky Ancient House', short_vi: 'Nhà buôn cổ bằng gỗ trên phố Nguyễn Thái Học.', short_en: 'A wooden merchant house on Nguyen Thai Hoc street.', latitude: 15.87668, longitude: 108.32808, visit: 40 },
  phucKien: { pid: 0x403, slug: 'hoi-quan-phuc-kien', category_code: 'heritage', name_vi: 'Hội quán Phúc Kiến', name_en: 'Fujian Assembly Hall', short_vi: 'Hội quán của cộng đồng người Hoa Phúc Kiến.', short_en: 'The assembly hall of the Fujian Chinese community.', latitude: 15.87745, longitude: 108.33075, visit: 45 },
  market: { pid: 0x404, slug: 'cho-hoi-an', category_code: 'market', name_vi: 'Chợ Hội An', name_en: 'Hoi An Central Market', short_vi: 'Chợ trung tâm bên sông Hoài, nhiều món ăn địa phương.', short_en: 'The central market by the Hoai River, full of local food.', latitude: 15.87692, longitude: 108.33186, visit: 70 },
  hoaiRiver: { pid: 0x405, slug: 'pho-den-long-song-hoai', category_code: 'evening', name_vi: 'Phố đèn lồng ven sông Hoài', name_en: 'Hoai River lantern quarter', short_vi: 'Bờ sông rực đèn lồng khi trời tối.', short_en: 'The riverbank lit by lanterns after dark.', latitude: 15.87628, longitude: 108.32705, visit: 90 },
  coconutForest: { pid: 0x406, slug: 'rung-dua-bay-mau', category_code: 'nature', name_vi: 'Rừng dừa Bảy Mẫu', name_en: 'Bay Mau Coconut Forest', short_vi: 'Rừng dừa nước, đi thuyền thúng.', short_en: 'Water coconut palms explored by basket boat.', latitude: 15.88570, longitude: 108.36830, visit: 90 },
  anBang: { pid: 0x407, slug: 'bien-an-bang', category_code: 'beach', name_vi: 'Biển An Bàng', name_en: 'An Bang Beach', short_vi: 'Bãi biển gần phố cổ, nhiều quán ven biển.', short_en: 'A beach near the old town with seaside cafés.', latitude: 15.91390, longitude: 108.34050, visit: 130 },
} satisfies Record<string, FixturePlace>;

const placeList: FixturePlace[] = Object.values(places);
const PUBLICATION_ID = id(0x301);

export const placeIdOf = (place: FixturePlace) => id(place.pid);
export const PLACE_IDS = {
  anBang: placeIdOf(places.anBang),
  coconutForest: placeIdOf(places.coconutForest),
  coveredBridge: placeIdOf(places.coveredBridge),
  hoaiRiver: placeIdOf(places.hoaiRiver),
  market: placeIdOf(places.market),
  phucKien: placeIdOf(places.phucKien),
  tanKy: placeIdOf(places.tanKy),
} as const;

/** Fixture photos (Wikimedia Commons; assets/images/fixtures/attribution.json). `url` is the ImageKit path. */
const photo = (n: number, file: string, width_px: number, height_px: number, creator: string, license: string, license_code: string): Media => ({
  alt_text: null,
  attribution_text: `${creator} · ${license} · Wikimedia Commons`,
  creator,
  height_px,
  license_code,
  media_asset_id: id(0xa10 + n),
  url: `gonarra/fixtures/${file}`,
  width_px,
});

const placePhotos: Record<string, Media> = {
  'bien-an-bang': photo(7, 'an-bang.jpg', 1400, 933, 'Alexkom000', 'CC BY 4.0', 'CC-BY-4.0'),
  'cho-hoi-an': photo(4, 'cho-hoi-an.jpg', 1400, 933, 'Gary Todd', 'CC0', 'CC0-1.0'),
  'chua-cau': photo(1, 'chua-cau.jpg', 1400, 1050, 'Chainwit.', 'CC BY 4.0', 'CC-BY-4.0'),
  'hoi-quan-phuc-kien': photo(3, 'phuc-kien.jpg', 1400, 1050, 'Chainwit.', 'CC BY 4.0', 'CC-BY-4.0'),
  'nha-co-tan-ky': photo(2, 'tan-ky.jpg', 1400, 929, 'P. Hughes', 'CC BY 4.0', 'CC-BY-4.0'),
  'pho-den-long-song-hoai': photo(5, 'pho-den-long.jpg', 1400, 933, 'lumoplank', 'CC0', 'CC0-1.0'),
  'rung-dua-bay-mau': photo(6, 'rung-dua-bay-mau.jpg', 1400, 935, 'Chester Ho', 'CC0', 'CC0-1.0'),
};

function summary(place: FixturePlace, locale: Locale): Place {
  return {
    catalog_publication_id: PUBLICATION_ID,
    category_code: place.category_code,
    city_id: defaultCity.id,
    id: placeIdOf(place),
    location: { latitude: place.latitude, longitude: place.longitude },
    name: byLocale(locale, place.name_vi, place.name_en),
    name_vi: place.name_vi,
    short_description: byLocale(locale, place.short_vi, place.short_en),
    slug: place.slug,
    thumbnail: placePhotos[place.slug] ?? null,
    visit_minutes_suggested: place.visit,
  };
}

/** API-010 `GET /v1/places?city_id&q` (Hội An only). `q` matches either name, accent-insensitively. */
export function fixturePlaces(locale: Locale, q?: string): Place[] {
  const fold = (value: string) => value.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
  const query = q?.trim() ? fold(q) : '';
  return placeList
    .filter(place => !query || fold(place.name_vi).includes(query) || fold(place.name_en).includes(query))
    .map(place => summary(place, locale));
}

/* ---------------------------------------------------------------- Place detail and card (SCR-033) */

const SOURCE_HERITAGE = id(0x802);
const heritageCitation: Citation = {
  knowledge_chunk_id: null, locator: null, place_fact_id: null, publisher: 'Trung tâm Quản lý Bảo tồn Di sản Văn hóa Hội An',
  section: null, source_revision_id: SOURCE_HERITAGE, title: null, verified_at: '2026-09-15',
};

function fact(n: number, field_code: PlaceFact['field_code'], partial: Omit<PlaceFact, 'field_code' | 'place_fact_id' | 'sources'>): PlaceFact {
  const place_fact_id = id(n);
  return {
    field_code,
    place_fact_id,
    sources: partial.knowledge_state === 'KNOWN' ? [{ ...heritageCitation, place_fact_id, verified_at: partial.verified_at ?? heritageCitation.verified_at }] : [],
    ...partial,
  };
}

/**
 * Facts for one place. Chùa Cầu shows every state: KNOWN + CURRENT hours, KNOWN + STALE price, KNOWN address,
 * UNKNOWN entrance. Other places: KNOWN address, UNKNOWN hours (never blank).
 */
function factsFor(place: FixturePlace): PlaceFact[] {
  const base = place.pid * 0x10;
  if (place === places.coveredBridge) {
    return [
      fact(base + 1, 'OPENING_HOURS', { freshness: 'CURRENT', knowledge_state: 'KNOWN', value: { intervals: [{ close: '21:30', open: '07:00' }] }, verified_at: '2026-09-15' }),
      fact(base + 2, 'ADMISSION_PRICE', { freshness: 'STALE', knowledge_state: 'KNOWN', value: { amount: '120000', currency: 'VND' }, verified_at: '2026-03-01' }),
      fact(base + 3, 'ADDRESS_VI', { freshness: 'CURRENT', knowledge_state: 'KNOWN', value: { text: 'Đường Nguyễn Thị Minh Khai, phố cổ Hội An' }, verified_at: '2026-09-15' }),
      fact(base + 4, 'ENTRANCE_LOCATION', { freshness: 'CURRENT', knowledge_state: 'UNKNOWN', value: null, verified_at: null }),
    ];
  }
  return [
    fact(base + 1, 'OPENING_HOURS', { freshness: 'CURRENT', knowledge_state: 'UNKNOWN', value: null, verified_at: null }),
    fact(base + 3, 'ADDRESS_VI', { freshness: 'CURRENT', knowledge_state: 'KNOWN', value: { text: `${place.name_vi}, Hội An` }, verified_at: '2026-09-15' }),
  ];
}

/** API-011 `GET /v1/places/{place_id}`; undefined for an unknown id (→ 404 `not_found`). */
export function fixturePlaceDetail(placeId: Uuid, locale: Locale): PlaceDetail | undefined {
  const place = placeList.find(item => placeIdOf(item) === placeId);
  if (!place) return undefined;
  return {
    ...summary(place, locale),
    attributions: [{ attribution_text: '© Fixture data — not reviewed', homepage_url: null, license_code: null, publisher: 'Gonarra fixtures' },
      ...(placePhotos[place.slug] ? [{ attribution_text: placePhotos[place.slug].attribution_text, homepage_url: null, license_code: placePhotos[place.slug].license_code, publisher: 'Wikimedia Commons' }] : [])],
    description: byLocale(locale, place.short_vi, place.short_en),
    entrance_location: null,
    facts: factsFor(place),
    media: placePhotos[place.slug] ? [placePhotos[place.slug]] : [],
    name_en: place.name_en,
    publication_revision: 1,
    published_at: '2026-10-01T09:00:00+07:00',
    visit_minutes_max: place.visit + 20,
    visit_minutes_min: Math.max(15, place.visit - 20),
  };
}

const mapsUrls = (place: FixturePlace) => ({
  apple_maps_url: `https://maps.apple.com/?daddr=${place.latitude},${place.longitude}`,
  google_maps_url: `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`,
});

/** API-017 place card for a stop of the fixture trip; undefined for an unknown stop. */
export function fixturePlaceCard(stopId: Uuid): PlaceCard | undefined {
  const entry = Object.entries(STOP_IDS).find(([, value]) => value === stopId);
  if (!entry) return undefined;
  const place = places[entry[0] as keyof typeof places];
  const facts = factsFor(place);
  const unknown = (field_code: PlaceFact['field_code']): PlaceFact => ({ field_code, freshness: 'CURRENT', knowledge_state: 'UNKNOWN', sources: [], value: null });
  return {
    address_vi: facts.find(item => item.field_code === 'ADDRESS_VI') ?? unknown('ADDRESS_VI'),
    catalog_publication_id: PUBLICATION_ID,
    directions: { target: 'PLACE_POSITION', ...mapsUrls(place) },
    entrance: facts.find(item => item.field_code === 'ENTRANCE_LOCATION') ?? unknown('ENTRANCE_LOCATION'),
    name_en: place.name_en,
    name_vi: place.name_vi,
    place_id: placeIdOf(place),
    stop_id: stopId,
    // live_status deliberately omitted: runtime-only provider data is never faked (ADR-006).
  };
}

/* ---------------------------------------------------------------- Preview (SCR-024/025) */

/** Stable stop ids, one per place (each place appears once in the fixture trip). */
const STOP_IDS: Record<keyof typeof places, Uuid> = {
  anBang: id(0x207),
  coconutForest: id(0x206),
  coveredBridge: id(0x201),
  hoaiRiver: id(0x205),
  market: id(0x204),
  phucKien: id(0x203),
  tanKy: id(0x202),
};

const at = (date: string, time: string) => `${date}T${time}:00+07:00`;
const MEASURED_AT = '2027-01-10T09:00:00+07:00';

function stop(key: keyof typeof places, locale: Locale, ordinal: number, date: string, arrive: string, depart: string, rationale: string): Stop {
  const place = places[key];
  return {
    catalog_publication_id: PUBLICATION_ID,
    conflicts: [],
    id: STOP_IDS[key],
    is_locked: false,
    location: { latitude: place.latitude, longitude: place.longitude },
    name: byLocale(locale, place.name_vi, place.name_en),
    name_vi: place.name_vi,
    ordinal,
    place_id: placeIdOf(place),
    planned_arrival: at(date, arrive),
    planned_departure: at(date, depart),
    rationale,
    visit_minutes: place.visit,
  };
}

function walk(from: Stop, to: Stop, distance_m: number, duration_s: number): Leg {
  return { availability: 'AVAILABLE', conflicts: [], distance_m, duration_s, from_stop_id: from.id, measured_at: MEASURED_AT, to_stop_id: to.id, travel_mode: 'WALK' };
}

export const HOI_AN_TRIP_ID = id(0x601);
export const HUE_TRIP_ID = id(0x602);
export const HOI_AN_PREVIEW_ID = id(0x501);
/** Variant whose day-2 leg has no route: an unavailable leg makes the plan Blocked (screen-specs SCR-025). */
export const HOI_AN_PREVIEW_ROUTE_UNAVAILABLE_ID = id(0x502);
export const HOI_AN_START_DATE = '2027-01-16';

function hoiAnDays(locale: Locale, routeUnavailable: boolean): Day[] {
  const d1 = HOI_AN_START_DATE;
  const d2 = '2027-01-17';
  const s1 = [
    stop('coveredBridge', locale, 1, d1, '08:00', '08:40', byLocale(locale, 'Biểu tượng của phố cổ, nên đến sớm khi còn vắng.', 'The old town’s landmark; best early, before the crowds.')),
    stop('tanKy', locale, 2, d1, '08:45', '09:25', byLocale(locale, 'Nhà cổ gần cầu, hợp với sở thích văn hoá.', 'A short walk from the bridge and fits your culture interest.')),
    stop('phucKien', locale, 3, d1, '09:30', '10:15', byLocale(locale, 'Hội quán tiêu biểu của người Hoa ở phố cổ.', 'A well-known Chinese assembly hall in the old town.')),
    stop('market', locale, 4, d1, '10:20', '11:30', byLocale(locale, 'Ăn trưa sớm với món địa phương.', 'An early lunch of local dishes.')),
    stop('hoaiRiver', locale, 5, d1, '17:30', '19:00', byLocale(locale, 'Ngắm đèn lồng ven sông khi trời tối.', 'Lanterns along the river after dark.')),
  ];
  const s2 = [
    stop('coconutForest', locale, 1, d2, '08:30', '10:00', byLocale(locale, 'Đi thuyền thúng trong rừng dừa nước.', 'A basket-boat ride through the water coconut palms.')),
    stop('anBang', locale, 2, d2, '10:20', '12:30', byLocale(locale, 'Nghỉ ngơi ở biển sau buổi sáng.', 'Beach time to round off the trip.')),
  ];
  s2[0].conflicts = [{ message: byLocale(locale, 'Giờ mở cửa: chưa rõ', 'Opening hours: unknown'), severity: 'WARNING', type: 'OPENING_HOURS_UNKNOWN' }];

  const day2Leg: Leg = routeUnavailable
    ? { availability: 'UNAVAILABLE', conflicts: [{ severity: 'BLOCKING', type: 'LEG_UNAVAILABLE' }], distance_m: null, duration_s: null, from_stop_id: s2[0].id, measured_at: null, to_stop_id: s2[1].id, travel_mode: 'DRIVE' }
    : { availability: 'AVAILABLE', conflicts: [], distance_m: 6800, duration_s: 960, from_stop_id: s2[0].id, measured_at: MEASURED_AT, to_stop_id: s2[1].id, travel_mode: 'DRIVE' };

  return [
    {
      day_index: 1, day_window_end: '20:00', day_window_start: '08:00', trip_day_id: null, stops: s1,
      legs: [walk(s1[0], s1[1], 250, 240), walk(s1[1], s1[2], 300, 270), walk(s1[2], s1[3], 200, 180), walk(s1[3], s1[4], 650, 540)],
    },
    { day_index: 2, day_window_end: '18:00', day_window_start: '08:00', trip_day_id: null, stops: s2, legs: [day2Leg] },
  ];
}

/**
 * Two-day Hội An preview. `warning` (default): Plan Health WARNING with one reason (opening hours unknown), all legs
 * available. `routeUnavailable`: the day-2 leg is UNAVAILABLE (no distance/duration) and Plan Health is BLOCKED.
 */
export function hoiAnPreview(locale: Locale, variant: 'warning' | 'routeUnavailable' = 'warning'): PlanPreview {
  const routeUnavailable = variant === 'routeUnavailable';
  return {
    assumptions: [byLocale(locale, 'Đi bộ trong phố cổ, đi xe tới rừng dừa và biển.', 'Walking in the old town; driving to the coconut forest and the beach.')],
    base_trip_revision: 0,
    corpus_revision: 1,
    created_at: '2027-01-10T09:00:00+07:00',
    days: hoiAnDays(locale, routeUnavailable),
    expires_at: '2027-01-11T09:00:00+07:00',
    head_revision: 1,
    health_reasons: routeUnavailable
      ? [{ message: byLocale(locale, 'Không có tuyến đường', 'Route unavailable'), severity: 'BLOCKING', type: 'LEG_UNAVAILABLE' }]
      : [{ message: byLocale(locale, 'Giờ mở cửa: chưa rõ', 'Opening hours: unknown'), severity: 'WARNING', type: 'OPENING_HOURS_UNKNOWN' }],
    id: routeUnavailable ? HOI_AN_PREVIEW_ROUTE_UNAVAILABLE_ID : HOI_AN_PREVIEW_ID,
    model_version: 'fixture',
    origin: 'GENERATED',
    parent_revision: null,
    plan_health: routeUnavailable ? 'BLOCKED' : 'WARNING',
    preview_revision: 1,
    prompt_version: 'fixture',
    status: 'ACTIVE',
    trip_id: HOI_AN_TRIP_ID,
  };
}

/* ---------------------------------------------------------------- Trips (SCR-031, saved mode of SCR-024) */

/** Saved-trip summaries for the Trips list (API-013 items, newest first). */
export const fixtureTrips: Trip[] = [
  {
    city_id: defaultCity.id, created_at: '2027-01-10T09:00:00+07:00', day_count: 2, id: HOI_AN_TRIP_ID, revision: 1,
    saved_at: '2027-01-10T09:05:00+07:00', start_date: HOI_AN_START_DATE, status: 'SAVED', title: null, updated_at: '2027-01-10T09:05:00+07:00',
  },
  {
    city_id: fixtureCities[4].id, created_at: '2027-01-08T20:00:00+07:00', day_count: 1, id: HUE_TRIP_ID, revision: 1,
    saved_at: '2027-01-08T20:10:00+07:00', start_date: '2027-02-20', status: 'SAVED', title: null, updated_at: '2027-01-08T20:10:00+07:00',
  },
];

/** API-014 `GET /v1/trips/{trip_id}`: the saved Hội An trip carries the WARNING itinerary; Huế has no fixture days. */
export function fixtureTripDetail(tripId: Uuid, locale: Locale): TripDetail | undefined {
  const trip = fixtureTrips.find(item => item.id === tripId);
  if (!trip) return undefined;
  const days = tripId === HOI_AN_TRIP_ID
    ? hoiAnDays(locale, false).map(day => ({ ...day, trip_day_id: id(0x650 + day.day_index) }))
    : [];
  return { ...trip, active_preview_id: null, days, planning_preferences: { allowed_modes: ['WALK', 'DRIVE'], pace: 'BALANCED' } };
}

/* ---------------------------------------------------------------- Preferences (SCR-022 prefill) */

export function fixturePreferences(locale: Locale): Preferences {
  return {
    ai_notice_acknowledged_at: null,
    allowed_modes: ['WALK', 'DRIVE'],
    day_end_time: '20:00',
    day_start_time: '08:00',
    interest_category_codes: ['heritage', 'market'],
    locale,
    pace: 'BALANCED',
    updated_at: null,
  };
}

/* ---------------------------------------------------------------- Guide (SCR-034) */

export const GUIDE_SESSION_ID = id(0x951);

/** A Guide session about Chùa Cầu inside the saved Hội An trip. */
export function fixtureGuideSession(locale: Locale): GuideSession {
  return { created_at: '2027-01-16T08:09:00+07:00', expires_at: null, id: GUIDE_SESSION_ID, locale, place_id: PLACE_IDS.coveredBridge, trip_id: HOI_AN_TRIP_ID };
}

const guideCitations: Citation[] = [
  {
    knowledge_chunk_id: id(0x701), locator: 'whc.unesco.org/en/list/948', place_fact_id: null, publisher: 'UNESCO World Heritage Centre',
    section: 'HISTORY', source_revision_id: id(0x801), title: 'Hoi An Ancient Town', verified_at: '2026-10-01',
  },
  {
    knowledge_chunk_id: id(0x702), locator: null, place_fact_id: null, publisher: 'Trung tâm Quản lý Bảo tồn Di sản Văn hóa Hội An',
    section: 'VISIT_TIPS', source_revision_id: SOURCE_HERITAGE, title: 'Chùa Cầu', verified_at: '2026-09-15',
  },
];

/** A cited Guide answer about Chùa Cầu (two citations). */
export function guideAnswer(locale: Locale): GuideMessage {
  return {
    answer_status: 'ANSWERED',
    citations: guideCitations,
    content: byLocale(
      locale,
      'Chùa Cầu là cây cầu có mái che bắc qua một nhánh lạch nhỏ ở phố cổ Hội An, gắn với cộng đồng thương nhân Nhật Bản từ đầu thế kỷ 17. Bạn nên đến vào sáng sớm để tránh đông người.',
      'The Covered Bridge spans a small creek in Hội An’s old town and is linked to the Japanese merchant community of the early 17th century. Go early in the morning to avoid the crowds.',
    ),
    created_at: '2027-01-16T08:10:00+07:00',
    id: id(0x902),
    input_mode: null,
    role: 'ASSISTANT',
    seq: 2,
  };
}

/** A Guide reply where the sources do not support an answer (ADR-010). */
export function guideInsufficientEvidence(locale: Locale): GuideMessage {
  return {
    answer_status: 'INSUFFICIENT_EVIDENCE',
    citations: [],
    content: byLocale(locale, 'Chưa đủ nguồn để trả lời', 'Not enough evidence to answer'),
    created_at: '2027-01-16T08:12:00+07:00',
    id: id(0x904),
    input_mode: null,
    role: 'ASSISTANT',
    seq: 4,
  };
}

/** API-027 history: question → cited answer → question → insufficient evidence. */
export function fixtureGuideMessages(locale: Locale): GuideMessage[] {
  return [
    { citations: [], content: byLocale(locale, 'Chùa Cầu có lịch sử thế nào?', 'What is the history of the Covered Bridge?'), created_at: '2027-01-16T08:10:00+07:00', id: id(0x901), input_mode: 'TEXT', role: 'TRAVELER', seq: 1 },
    guideAnswer(locale),
    { citations: [], content: byLocale(locale, 'Gần cầu có chỗ gửi xe không?', 'Is there parking near the bridge?'), created_at: '2027-01-16T08:12:00+07:00', id: id(0x903), input_mode: 'TEXT', role: 'TRAVELER', seq: 3 },
    guideInsufficientEvidence(locale),
  ];
}
