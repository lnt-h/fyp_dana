import { Image } from 'expo-image';
import { useState } from 'react';
import { StyleSheet } from 'react-native';
import type { Media } from '../../lib/api/types';
import { resolveImage } from '../../lib/images/imagekit';
import type { IconName } from './Icon';
import { PhotoFallback, type PhotoFallbackProps } from './PhotoFallback';

export type PhotoProps = {
  image: Pick<Media, 'url'> | null | undefined;
  /** Layout size in dp, used to size the ImageKit request. */
  width: number;
  height?: number;
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
export function Photo({ image, width, height, categoryCode, name, icon, iconSize, tone, variant, transition = 200, accessibilityLabel, onLoad, onError }: PhotoProps) {
  const url = image?.url?.trim() || null;
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const resolved = resolveImage(image, { height, width });
  const fallback = { categoryCode, icon, iconSize, name, tone, variant };

  if (!resolved || (url !== null && failedUrl === url)) return <PhotoFallback {...fallback} />;
  return <>
    <PhotoFallback {...fallback} bare />
    <Image
      accessibilityLabel={accessibilityLabel}
      accessible={!!accessibilityLabel}
      contentFit="cover"
      onError={() => { setFailedUrl(url); onError?.(); }}
      onLoad={onLoad}
      placeholder={resolved.placeholder}
      placeholderContentFit="cover"
      recyclingKey={url}
      source={resolved.source}
      style={StyleSheet.absoluteFill}
      transition={transition}
    />
  </>;
}

/** Tracks whether the current photo failed, so a credit line is shown only over a photo that actually loaded. */
export function usePhotoFailed(image: Pick<Media, 'url'> | null | undefined): [boolean, () => void] {
  const url = image?.url?.trim() || null;
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  return [url !== null && failedUrl === url, () => setFailedUrl(url)];
}
