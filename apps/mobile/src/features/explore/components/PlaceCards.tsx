import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { GlassBadge, Icon, Photo, PhotoCard, Skeleton, categoryIcon, usePhotoFailed } from '../../../components/ui';
import type { Place } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

export const LIST_THUMB = 64;
export const FEATURED_WIDTH = 264;
export const FEATURED_HEIGHT = 300;
const border = colors.hairline;

function useMinutes(place: Place) {
  const { t } = useTranslation();
  return place.visit_minutes_suggested ? t('explore.minutes', { count: place.visit_minutes_suggested }) : null;
}

/** `name` is in the UI language and `name_vi` always present: the other-language name exists only in English UI. */
function otherName(place: Place) {
  return place.name_vi !== place.name ? place.name_vi : null;
}

type CardProps = { place: Place; categoryLabel: string; onPress: () => void };

/** Grid tile: photo with scrim, glass minutes badge, name and category. Height scales with width (4:5). */
export function PlaceGridCard({ place, categoryLabel, onPress, width }: CardProps & { width: number }) {
  const { t } = useTranslation();
  const minutes = useMinutes(place);
  const height = Math.round(width * 1.25);
  const [photoFailed, onPhotoError] = usePhotoFailed(place.thumbnail);
  return (
    <Pressable
      accessibilityHint={t('explore.openHint')}
      accessibilityLabel={[place.name, otherName(place), categoryLabel, minutes].filter(Boolean).join(', ')}
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.gridCard, { height, width }, pressed && styles.pressed]}
    >
      <View style={styles.clip}>
        <Photo categoryCode={place.category_code} height={height} image={place.thumbnail} name={place.name} onError={onPhotoError} tone="dark" width={width} />
        <LinearGradient colors={['rgba(7,21,30,0)', 'rgba(7,21,30,0.8)']} locations={[0.35, 1]} style={StyleSheet.absoluteFill} />
        {minutes ? <GlassBadge icon="clock" label={minutes} style={styles.badge} /> : null}
        <View style={styles.overlay}>
          <Text numberOfLines={2} style={styles.gridName}>{place.name}</Text>
          <View style={styles.gridMeta}>
            <Icon color={colors.white} name={categoryIcon(place.category_code)} size={15} />
            {categoryLabel ? <Text numberOfLines={1} style={styles.gridMetaText}>{categoryLabel}</Text> : null}
          </View>
          {!photoFailed && place.thumbnail?.attribution_text ? <Text numberOfLines={1} style={styles.credit}>{place.thumbnail.attribution_text}</Text> : null}
        </View>
      </View>
    </Pressable>
  );
}

/** List row: 64 pt photo, both names, category and visit time; chevron. Names wrap to two lines, never cut short. */
export function PlaceListRow({ place, categoryLabel, onPress }: CardProps) {
  const { t } = useTranslation();
  const minutes = useMinutes(place);
  const secondary = otherName(place);
  return (
    <Pressable
      accessibilityHint={t('explore.openHint')}
      accessibilityLabel={[place.name, secondary, categoryLabel, minutes].filter(Boolean).join(', ')}
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.row, pressed && styles.rowPressed]}
    >
      <View style={styles.thumb}>
        <Photo categoryCode={place.category_code} height={LIST_THUMB} iconSize={26} image={place.thumbnail} name={place.name} transition={150} variant="thumb" width={LIST_THUMB} />
      </View>
      <View style={styles.rowBody}>
        <Text numberOfLines={2} style={styles.rowName}>{place.name}</Text>
        {secondary ? <Text numberOfLines={2} style={styles.rowSecondary}>{secondary}</Text> : null}
        <View style={styles.rowMeta}>
          <Icon color={colors.tealText} name={categoryIcon(place.category_code)} size={15} />
          <Text numberOfLines={1} style={styles.rowMetaText}>{[categoryLabel, minutes].filter(Boolean).join(' · ')}</Text>
        </View>
      </View>
      <Icon color={colors.textMuted} name="chevron-right" size={20} />
    </Pressable>
  );
}

/** Large featured card (carousel). */
export function FeaturedCard({ place, categoryLabel, onPress }: CardProps) {
  const { t } = useTranslation();
  const minutes = useMinutes(place);
  return (
    <PhotoCard
      accessibilityHint={t('explore.openHint')}
      accessibilityLabel={[place.name, otherName(place), categoryLabel, minutes].filter(Boolean).join(', ')}
      attribution={place.thumbnail?.attribution_text}
      badge={minutes ?? undefined}
      badgeIcon="clock"
      fallbackCategory={place.category_code}
      fallbackName={place.name}
      image={place.thumbnail}
      imageHeight={FEATURED_HEIGHT}
      onPress={onPress}
      subtitle={categoryLabel || undefined}
      subtitleIcon={categoryIcon(place.category_code)}
      title={place.name}
      width={FEATURED_WIDTH}
    />
  );
}

/* ------------------------------------------------------------------ skeletons (same footprint as the cards) */

export function GridSkeleton({ width, count = 4 }: { width: number; count?: number }) {
  return (
    <View style={styles.gridWrap}>
      {Array.from({ length: count }, (_, i) => (
        <Skeleton height={Math.round(width * 1.25)} key={i} radius={radii.card} width={width} />
      ))}
    </View>
  );
}

export function ListSkeleton({ count = 4 }: { count?: number }) {
  return (
    <View>
      {Array.from({ length: count }, (_, i) => (
        <View key={i} style={styles.row}>
          <Skeleton height={LIST_THUMB} radius={radii.inset} width={LIST_THUMB} />
          <View style={styles.rowBody}>
            <Skeleton height={16} width="72%" />
            <Skeleton height={13} width="48%" />
            <Skeleton height={12} width="36%" />
          </View>
        </View>
      ))}
    </View>
  );
}

export function FeaturedSkeleton() {
  return (
    <View style={styles.featuredSkeleton}>
      {[0, 1].map(i => <Skeleton height={FEATURED_HEIGHT} key={i} radius={radii.card} width={FEATURED_WIDTH} />)}
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { position: 'absolute', right: spacing.xs, top: spacing.xs },
  clip: { backgroundColor: colors.deepOcean, borderColor: border, borderRadius: radii.photoCard, borderWidth: StyleSheet.hairlineWidth, flex: 1, overflow: 'hidden' },
  credit: { color: 'rgba(255,255,255,0.82)', fontFamily: fonts.medium, fontSize: 10, marginTop: 4 },
  featuredSkeleton: { flexDirection: 'row', gap: spacing.md, overflow: 'hidden' },
  gridCard: { backgroundColor: colors.white, borderRadius: radii.photoCard },
  gridMeta: { alignItems: 'center', flexDirection: 'row', gap: 5, marginTop: 4 },
  gridMetaText: { color: colors.white, flexShrink: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18 },
  gridName: { color: colors.white, fontFamily: fonts.bold, fontSize: 17, letterSpacing: -0.2, lineHeight: 22 },
  gridWrap: { columnGap: spacing.sm, flexDirection: 'row', flexWrap: 'wrap', rowGap: spacing.sm },
  overlay: { bottom: 0, left: 0, padding: spacing.sm, position: 'absolute', right: 0 },
  pressed: { opacity: 0.94, transform: [{ scale: 0.98 }] },
  row: { alignItems: 'center', borderRadius: radii.inset, flexDirection: 'row', gap: spacing.sm, minHeight: 84, paddingVertical: 10 },
  rowBody: { flex: 1, gap: 3 },
  rowMeta: { alignItems: 'center', flexDirection: 'row', gap: 5, marginTop: 2 },
  rowMetaText: { color: colors.textMuted, flexShrink: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18 },
  rowName: { color: colors.ink, fontFamily: fonts.bold, fontSize: 16, lineHeight: 22 },
  rowPressed: { backgroundColor: colors.surfaceTint },
  rowSecondary: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 14, lineHeight: 19 },
  thumb: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: radii.inset, height: LIST_THUMB, justifyContent: 'center', overflow: 'hidden', width: LIST_THUMB },
});
