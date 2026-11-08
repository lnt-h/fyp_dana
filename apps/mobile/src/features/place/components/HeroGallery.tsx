import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Image } from 'expo-image';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { PhotoHero, type IconName } from '../../../components/ui';
import type { Media } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

const MAX_THUMBS = 4;
const THUMB = 52;
/** How far the thumbnails hang below the hero's bottom edge. */
const GALLERY_OVERHANG = THUMB / 2;

type Props = {
  name: string;
  /** The place thumbnail first, then its other media (duplicates dropped). */
  thumbnail: Media | null | undefined;
  media: Media[] | null | undefined;
  height: number;
  fallbackIcon: IconName;
  topLeft: ReactNode;
  topRight: ReactNode;
  kicker?: string;
  title: string;
  children?: ReactNode;
};

/** Ordered, de-duplicated photos of a place: thumbnail first. */
export function galleryPhotos(thumbnail: Media | null | undefined, media: Media[] | null | undefined): Media[] {
  const list = [thumbnail, ...(media ?? [])].filter((item): item is Media => !!item);
  const seen = new Set<string>();
  return list.filter(item => (seen.has(item.media_asset_id) ? false : (seen.add(item.media_asset_id), true)));
}

/**
 * Place hero with a thumbnail gallery (`02-place-detail.png`): up to 4 squares overlapping the hero's lower-right edge;
 * tapping one swaps the hero. The credit line always names the photo currently shown, with its licence (Wikimedia
 * Commons terms). No photo: the category illustration, no thumbnails.
 */
export function HeroGallery({ name, thumbnail, media, height, fallbackIcon, topLeft, topRight, kicker, title, children }: Props) {
  const { t } = useTranslation();
  const photos = useMemo(() => galleryPhotos(thumbnail, media), [thumbnail, media]);
  const [index, setIndex] = useState(0);
  useEffect(() => { setIndex(0); }, [photos]);
  const current = photos[index] ?? null;
  const thumbs = photos.slice(0, MAX_THUMBS);
  const credit = current?.attribution_text
    ? current.license_code
      ? t('place.gallery.credit', { credit: current.attribution_text, license: current.license_code })
      : t('place.photoBy', { text: current.attribution_text })
    : null;

  const gallery = thumbs.length > 1;
  return <View>
    <PhotoHero
      accessibilityLabel={current?.alt_text ?? (current ? t('place.gallery.thumbA11y', { index: index + 1, name, total: photos.length }) : undefined)}
      // With thumbnails the credit moves under the hero (the thumbs sit on its lower-right edge).
      arch={!gallery}
      attribution={gallery ? null : credit}
      fallbackIcon={fallbackIcon}
      height={height}
      image={current}
      kicker={kicker}
      style={gallery ? g.straight : undefined}
      title={title}
      topLeft={topLeft}
      topRight={topRight}
    >
      {children}
    </PhotoHero>
    {gallery ? <View style={g.row}>
      {thumbs.map((photo, position) => {
        const resolved = resolveImage(photo, { height: THUMB, width: THUMB });
        const selected = position === index;
        return <Pressable
          key={photo.media_asset_id}
          accessibilityLabel={t('place.gallery.thumbA11y', { index: position + 1, name, total: thumbs.length })}
          accessibilityRole="imagebutton"
          accessibilityState={{ selected }}
          onPress={() => setIndex(position)}
          style={({ pressed }) => [g.thumb, selected && g.thumbSelected, pressed && { opacity: 0.8 }]}
        >
          {resolved
            ? <Image contentFit="cover" placeholder={resolved.placeholder} source={resolved.source} style={g.image} transition={150} />
            : <View style={[g.image, { backgroundColor: colors.surfaceTint }]} />}
        </Pressable>;
      })}
    </View> : null}
    {gallery ? <View style={g.creditRow}>
      {credit ? <Text accessibilityLiveRegion="polite" numberOfLines={2} style={g.credit}>{credit}</Text> : null}
    </View> : null}
  </View>;
}

const g = StyleSheet.create({
  straight: { borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  creditRow: { minHeight: GALLERY_OVERHANG + spacing.xs, paddingTop: GALLERY_OVERHANG + spacing.xs, paddingHorizontal: spacing.lg },
  credit: { fontFamily: fonts.medium, fontSize: 12, lineHeight: 16, color: colors.textMuted },
  row: { position: 'absolute', right: spacing.lg, bottom: -GALLERY_OVERHANG, flexDirection: 'row', gap: spacing.xs },
  thumb: { width: THUMB, height: THUMB, borderRadius: 12, borderWidth: 2, borderColor: colors.white, overflow: 'hidden', backgroundColor: colors.white },
  thumbSelected: { borderColor: colors.audioTeal, borderWidth: 3 },
  image: { width: '100%', height: '100%' },
});
