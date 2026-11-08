import type { CityCode, Media } from '../api/types';

/**
 * City cover photos bundled with the app (UI chrome, not catalog data). The contract `City` has no image field, so covers
 * live here keyed by `CityCode`; resolve them with `resolveImage`, which serves the bundled file for a `bundled:` URL.
 * Source, author and licence of each file: assets/images/cities/attribution.json.
 */
export const BUNDLED_IMAGES: Record<string, number> = {
  'bundled:cities/city-da-nang.jpg': require('../../../assets/images/cities/city-da-nang.jpg'),
};

const cover = (n: number, file: string, width: number, height: number, attribution_text: string, license_code: string): Media => ({
  attribution_text,
  height_px: height,
  license_code,
  media_asset_id: `00000000-0000-4000-8000-${(0xa00 + n).toString(16).padStart(12, '0')}`,
  url: `bundled:cities/${file}`,
  width_px: width,
});

export const CITY_IMAGES: Record<CityCode, Media> = {
  'da-nang': cover(4, 'city-da-nang.jpg', 1400, 1054, 'Shenzybaby · CC0 · Wikimedia Commons', 'CC0-1.0'),
};
