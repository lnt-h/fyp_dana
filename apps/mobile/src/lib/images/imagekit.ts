import { PixelRatio } from 'react-native';
import type { ImageSource } from 'expo-image';
import type { Media } from '../api/types';
import { localFixtures } from './localFixtures';

/**
 * ImageKit URL-endpoint delivery (public endpoint only, e.g. `https://ik.imagekit.io/<id>`; the origin is the S3
 * bucket, ADR-002). No ImageKit private key ever ships in the app.
 */
const endpoint = (process.env.EXPO_PUBLIC_IMAGEKIT_URL_ENDPOINT ?? '').replace(/\/+$/, '');

export type IkTransform = {
  /** Output width in physical pixels. */
  w?: number;
  /** Output height in physical pixels. */
  h?: number;
  /** Quality 1–100 (default 75). */
  q?: number;
  /** Aspect ratio as `W-H`, e.g. `16-9`. Needs `w` or `h`. */
  ar?: string;
  /** Crop focus when cropping to `h`/`ar`: `auto` (smart) or `center`. */
  focus?: 'auto' | 'center';
  /** Gaussian blur radius 1–100 (placeholders). */
  bl?: number;
};

const isRemote = (path: string) => /^[a-z][a-z0-9+.-]*:/i.test(path);

/** Builds an ImageKit URL with a `tr=` transformation chain. Returns null when no endpoint is configured. */
export function ikUrl(path: string, t: IkTransform = {}): string | null {
  if (!endpoint || isRemote(path)) return null;
  const parts: string[] = [];
  if (t.w) parts.push(`w-${Math.round(t.w)}`);
  if (t.h) parts.push(`h-${Math.round(t.h)}`);
  if (t.ar) parts.push(`ar-${t.ar}`);
  parts.push(`q-${t.q ?? 75}`);
  if (t.bl) parts.push(`bl-${t.bl}`);
  parts.push('f-auto');
  if (t.h || t.ar) parts.push('c-maintain_ratio', `fo-${t.focus ?? 'auto'}`);
  const cleanPath = path.replace(/^\/+/, '').split('/').map(encodeURIComponent).join('/');
  return `${endpoint}/${cleanPath}?tr=${parts.join(',')}`;
}

export type ImageSize = {
  /** Layout width in dp. */
  width: number;
  /** Layout height in dp (optional; crops with smart focus when set). */
  height?: number;
};

export type ResolvedImage = {
  source: ImageSource | number;
  placeholder: ImageSource | number | null;
};

const fileName = (url: string) => url.split('?')[0].split('/').pop() ?? '';

/**
 * Resolves a contract `Media` thumbnail into expo-image props.
 * 1. ImageKit endpoint set and `url` is a relative path → density-aware ImageKit URL + 40-px blurred placeholder.
 * 2. Otherwise a bundled fixture photo matched by file name (no placeholder needed).
 * 3. Otherwise an absolute `https` URL is used as-is; anything else → null (caller shows its gradient fallback).
 */
export function resolveImage(thumbnail: Pick<Media, 'url'> | null | undefined, size: ImageSize): ResolvedImage | null {
  if (!thumbnail?.url) return null;
  const { url } = thumbnail;
  const w = PixelRatio.getPixelSizeForLayoutSize(size.width);
  const h = size.height ? PixelRatio.getPixelSizeForLayoutSize(size.height) : undefined;
  const remote = ikUrl(url, { h, w });
  if (remote) {
    const ratio = h ? { h: Math.max(1, Math.round((40 * h) / w)) } : {};
    const tiny = ikUrl(url, { bl: 10, q: 30, w: 40, ...ratio });
    return { placeholder: tiny ? { uri: tiny } : null, source: { uri: remote } };
  }
  const local = localFixtures[fileName(url)];
  if (local !== undefined) return { placeholder: null, source: local };
  if (/^https:\/\//i.test(url)) return { placeholder: null, source: { uri: url } };
  return null;
}
