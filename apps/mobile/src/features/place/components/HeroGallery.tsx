import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { LinearGradient } from 'expo-linear-gradient';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Photo, PhotoFallback, PhotoHero } from '../../../components/ui';
import type { Media } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';

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
  /** Category of the place: colours and labels the fallback tile when there is no photo (or it fails). */
  categoryCode: string;
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
export function HeroGallery({ name, thumbnail, media, height, categoryCode, topLeft, topRight, kicker, title, children }: Props) {
  const { t } = useTranslation();
  const photos = useMemo(() => galleryPhotos(thumbnail, media), [thumbnail, media]);
  const [index, setIndex] = useState(0);
  useEffect(() => { setIndex(0); }, [photos]);
  const current = photos[index] ?? null;
  // The gallery shows the other photos (Wave 6 P2): the hero never repeats itself in the row below.
  const thumbs = photos.map((photo, position) => ({ index: position, photo })).filter(item => item.index !== index).slice(0, MAX_THUMBS);
  const credit = current?.attribution_text
    ? current.license_code
      ? t('place.gallery.credit', { credit: current.attribution_text, license: current.license_code })
      : t('place.photoBy', { text: current.attribution_text })
    : null;

  const insets = useSafeAreaInsets();
  const gallery = photos.length > 1;
  if (!current) {
    // No photo: the strong category gradient with a large category icon (never a brown or grey box), white title.
    return <View style={[g.fallback, { height }]}>
      <PhotoFallback categoryCode={categoryCode} iconSize={64} tone="dark" />
      <LinearGradient colors={['rgba(22,33,43,0)', 'rgba(22,33,43,0.45)']} locations={[0.45, 1]} pointerEvents="none" style={StyleSheet.absoluteFill} />
      <View pointerEvents="box-none" style={[g.controls, { top: insets.top + spacing.xs }]}>
        <View>{topLeft}</View>
        <View>{topRight}</View>
      </View>
      <View pointerEvents="box-none" style={g.body}>
        <Text accessibilityRole="header" numberOfLines={3} style={g.title}>{title}</Text>
        {children}
      </View>
    </View>;
  }
  return <View>
    <PhotoHero
      accessibilityLabel={current?.alt_text ?? (current ? t('place.gallery.thumbA11y', { index: index + 1, name, total: photos.length }) : undefined)}
      // With thumbnails the credit moves under the hero (the thumbs sit on its lower-right edge).
      arch={!gallery}
      attribution={gallery ? null : credit}
      fallbackCategory={categoryCode}
      fallbackName={name}
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
      {thumbs.map(item => {
        const photo = item.photo;
        return <Pressable
          key={photo.media_asset_id}
          accessibilityLabel={t('place.gallery.thumbA11y', { index: item.index + 1, name, total: photos.length })}
          accessibilityRole="imagebutton"
          onPress={() => setIndex(item.index)}
          style={({ pressed }) => [g.thumb, pressed && { opacity: 0.8 }]}
        >
          <Photo categoryCode={categoryCode} height={THUMB} iconSize={20} image={photo} name={name} transition={150} variant="thumb" width={THUMB} />
        </Pressable>;
      })}
    </View> : null}
    {/* The credit sits left of the overhanging thumbnails, never under them. */}
    {gallery ? <View style={[g.creditRow, { paddingRight: spacing.lg + thumbs.length * (THUMB + spacing.xs) }]}>
      {credit ? <Text accessibilityLiveRegion="polite" numberOfLines={2} style={g.credit}>{credit}</Text> : null}
    </View> : null}
  </View>;
}

const g = StyleSheet.create({
  body: { bottom: 0, left: 0, paddingBottom: spacing.lg, paddingHorizontal: spacing.lg, position: 'absolute', right: 0 },
  controls: { flexDirection: 'row', justifyContent: 'space-between', left: spacing.md, position: 'absolute', right: spacing.md },
  fallback: { borderBottomLeftRadius: 28, borderBottomRightRadius: 28, overflow: 'hidden', width: '100%' },
  title: { ...typography.display, color: colors.white },
  straight: { borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  creditRow: { minHeight: GALLERY_OVERHANG + spacing.xs, paddingLeft: spacing.lg, paddingTop: spacing.xs },
  credit: { fontFamily: fonts.medium, fontSize: 12, lineHeight: 16, color: colors.textMuted },
  row: { position: 'absolute', right: spacing.lg, bottom: -GALLERY_OVERHANG, flexDirection: 'row', gap: spacing.xs },
  thumb: { width: THUMB, height: THUMB, borderRadius: 12, borderWidth: 2, borderColor: colors.white, overflow: 'hidden', backgroundColor: colors.white },
});
