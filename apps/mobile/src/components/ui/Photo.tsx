import { Image } from 'expo-image';
import { useState } from 'react';
import { StyleSheet } from 'react-native';
import type { Media } from '../../lib/api/types';
import { resolveImage } from '../../lib/images/imagekit';
import type { IconName } from './Icon';
import { PhotoFallback, type PhotoFallbackProps } from './PhotoFallback';

/** Contract photo plus the optional small variant (API `Media.thumb_url`, 330px Commons). */
export type PhotoImage = Pick<Media, 'url'> & { thumb_url?: string | null };

/** Layouts at or below this size (dp, both axes) take `thumb_url` when present. */
const THUMB_MAX_DP = 160;

export type PhotoProps = {
  image: PhotoImage | null | undefined;
  /** Layout size in dp, used to size the ImageKit request. */
  width: number;
  height?: number;
  /**
   * Prefer `thumb_url` (small variant for markers/lists). Default is automatic: layouts with
   * width and height at or below `THUMB_MAX_DP` use the thumb when the contract provides one;
   * heroes always use the full URL. Pass false to force the full photo.
   */
  preferThumb?: boolean;
  /** Fallback tile: category colour and icon, the place's initial (see `PhotoFallback`). */
  categoryCode?: string | null;
  name?: string | null;
  icon?: IconName;
  iconSize?: number;
  tone?: PhotoFallbackProps['tone'];
  variant?: PhotoFallbackProps['variant'];
  transition?: number;
  /** Alt text; omit for decorative photos whose card already names the place. */
  accessibilityLabel?: string;
  onLoad?: () => void;
  /** Called once when the remote photo fails (the fallback tile is then shown instead). */
  onError?: () => void;
};

/**
 * A place, city or trip photo that never leaves a blank or broken box. Fills its parent (give the parent a size and
 * `overflow: 'hidden'`). No photo → the category fallback tile. While a remote photo (e.g. Wikimedia Commons) loads, a
 * bare gradient of the same colour sits underneath; if it fails, the full fallback tile replaces it.
 */
export function Photo({ image, width, height, preferThumb, categoryCode, name, icon, iconSize, tone, variant, transition = 200, accessibilityLabel, onLoad, onError }: PhotoProps) {
  const thumb = image?.thumb_url?.trim() || null;
  const autoThumb = width <= THUMB_MAX_DP && (height ?? 0) <= THUMB_MAX_DP;
  const wantThumb = preferThumb ?? autoThumb;
  const chosen = wantThumb && thumb ? { ...image, url: thumb } : image;
  const shownUrl = chosen?.url?.trim() || null;
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const resolved = resolveImage(chosen, { height, width });
  const fallback = { categoryCode, icon, iconSize, tone, variant };

  if (!resolved || (shownUrl !== null && failedUrl === shownUrl)) return <PhotoFallback {...fallback} />;
  return <>
    <PhotoFallback {...fallback} bare />
    <Image
      accessibilityLabel={accessibilityLabel}
      accessible={!!accessibilityLabel}
      contentFit="cover"
      onError={() => { setFailedUrl(shownUrl); onError?.(); }}
      onLoad={onLoad}
      placeholder={resolved.placeholder}
      placeholderContentFit="cover"
      recyclingKey={shownUrl}
      source={resolved.source}
      style={StyleSheet.absoluteFill}
      transition={transition}
    />
  </>;
}

/** Tracks whether the current photo failed, so a credit line is shown only over a photo that actually loaded. */
export function usePhotoFailed(image: PhotoImage | null | undefined): [boolean, () => void] {
  const urls = [image?.url?.trim() || null, image?.thumb_url?.trim() || null];
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  return [
    failedUrl !== null && urls.includes(failedUrl),
    () => setFailedUrl(image?.url?.trim() || null),
  ];
}
