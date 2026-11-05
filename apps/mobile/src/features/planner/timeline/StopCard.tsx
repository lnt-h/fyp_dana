import { useEffect, useRef, useState, type ComponentRef, type Ref } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { Icon, categoryIcon } from '../../../components/ui';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { formatTime } from './format';
import { HealthGlyph } from './icons';
import { isStopBlocked, type NumberedStop } from './model';
import type { StopPlace } from './useProposal';

export const THUMB = 64;

type Props = {
  stop: NumberedStop;
  place: StopPlace | undefined;
  selected: boolean;
  reducedMotion: boolean;
  onSelect: () => void;
  onOpenDetails: () => void;
  rowRef?: Ref<ComponentRef<typeof View>>;
};

/**
 * One stop of a day (SCR-024 `StopCard`): photo, number, server times in Asia/Ho_Chi_Minh, name, category, conflicts
 * and the AI-written rationale (labelled as AI). The selection highlight fades in and follows the map.
 */
export function StopCard({ stop, place, selected, reducedMotion, onSelect, onOpenDetails, rowRef }: Props) {
  const { t } = useTranslation();
  const [showWhy, setShowWhy] = useState(false);
  const highlight = useRef(new Animated.Value(selected ? 1 : 0)).current;

  useEffect(() => {
    if (reducedMotion) { highlight.setValue(selected ? 1 : 0); return; }
    Animated.timing(highlight, { duration: 200, toValue: selected ? 1 : 0, useNativeDriver: true }).start();
  }, [highlight, reducedMotion, selected]);

  const arrival = formatTime(stop.planned_arrival);
  const departure = formatTime(stop.planned_departure);
  const blocked = isStopBlocked(stop);
  const conflicts = stop.conflicts ?? [];
  const timeRange = arrival && departure ? `${arrival} – ${departure}` : t('proposal.stop.timeUnknown');
  const status = conflicts.length ? conflicts.map(conflict => t(`proposal.conflict.${conflict.type}`)).join(', ') : t('proposal.stop.statusOk');
  // `name` is in the request locale; show the Vietnamese name as well when they differ (FR-076).
  const secondary = [stop.name !== stop.name_vi ? stop.name_vi : null, t('proposal.stop.minutes', { count: stop.visit_minutes })].filter(Boolean).join(' · ');
  const image = resolveImage(place?.thumbnail, { height: THUMB, width: THUMB });

  return <View ref={rowRef} style={r.root}>
    <Animated.View pointerEvents="none" style={[r.highlight, blocked && r.highlightBlocked, { opacity: highlight }]} />
    {blocked && <View style={r.blockedEdge} />}
    <Pressable
      accessibilityHint={t('proposal.stop.selectHint')}
      accessibilityLabel={t('proposal.stop.a11y', { arrival: arrival ?? '—', departure: departure ?? '—', name: stop.name, number: stop.number, status })}
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={onSelect}
      style={({ pressed }) => [r.main, pressed && { opacity: 0.75 }]}
    >
      <View style={r.thumbWrap}>
        <View style={r.thumb}>
          {image
            ? <Image contentFit="cover" placeholder={image.placeholder} source={image.source} style={StyleSheet.absoluteFill} transition={150} />
            : <LinearGradient colors={[colors.deepOcean, colors.tealDark]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={[StyleSheet.absoluteFill, r.thumbFallback]}>
              <Icon color={colors.white} name={categoryIcon(place?.categoryCode)} size={26} />
            </LinearGradient>}
        </View>
        <View style={[r.number, selected && r.numberSelected, blocked && r.numberBlocked]}>
          <Text style={r.numberText}>{stop.number}</Text>
        </View>
      </View>
      <View style={r.copy}>
        <View style={r.timeRow}>
          <Icon color={colors.tealText} name="clock" size={14} strokeWidth={2.2} />
          <Text style={r.time}>{timeRange}</Text>
        </View>
        <Text numberOfLines={2} style={r.name}>{stop.name}</Text>
        <View style={r.metaRow}>
          <Icon color={colors.textMuted} name={categoryIcon(place?.categoryCode)} size={15} />
          <Text numberOfLines={1} style={r.meta}>{secondary}</Text>
        </View>
        {conflicts.map((conflict, index) => <View key={`${conflict.type}-${index}`} style={r.conflict}>
          <HealthGlyph health={conflict.severity === 'BLOCKING' ? 'BLOCKED' : 'WARNING'} size={14} />
          <Text style={[r.conflictText, conflict.severity === 'BLOCKING' && { color: palette.error }]}>{t(`proposal.conflict.${conflict.type}`)}</Text>
        </View>)}
      </View>
    </Pressable>
    <View style={r.extras}>
      {!!stop.rationale && <View style={r.why}>
        <View style={r.aiLabel}>
          <Icon color={colors.tealText} name="sparkle" size={14} strokeWidth={2} />
          <Text style={r.aiLabelText}>{t('proposal.stop.aiLabel')}</Text>
        </View>
        <Text numberOfLines={showWhy ? undefined : 2} style={r.whyText}>{stop.rationale}</Text>
      </View>}
      <View style={r.actions}>
        {!!stop.rationale && <Pressable
          accessibilityRole="button"
          accessibilityState={{ expanded: showWhy }}
          onPress={() => setShowWhy(value => !value)}
          style={({ pressed }) => [r.action, pressed && { opacity: 0.6 }]}
        >
          <Text style={r.actionText}>{t(showWhy ? 'proposal.stop.whyHide' : 'proposal.stop.why')}</Text>
        </Pressable>}
        <Pressable
          accessibilityLabel={t('proposal.stop.detailsA11y', { name: stop.name })}
          accessibilityRole="button"
          onPress={onOpenDetails}
          style={({ pressed }) => [r.action, pressed && { opacity: 0.6 }]}
        >
          <Text style={r.actionText}>{t('proposal.stop.details')}</Text>
          <Icon color={colors.tealText} name="chevron-right" size={16} strokeWidth={2.2} />
        </Pressable>
      </View>
    </View>
  </View>;
}

const r = StyleSheet.create({
  root: { borderRadius: 20, overflow: 'hidden' },
  highlight: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, backgroundColor: '#F1F9FB', borderRadius: 20, borderWidth: 1.5, borderColor: colors.audioTeal },
  highlightBlocked: { backgroundColor: '#FDF3F3', borderColor: palette.error },
  blockedEdge: { position: 'absolute', left: 0, top: 10, bottom: 10, width: 4, borderRadius: 2, backgroundColor: palette.error },
  main: { flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.sm, paddingTop: spacing.sm },
  thumbWrap: { width: THUMB, height: THUMB },
  thumb: { width: THUMB, height: THUMB, borderRadius: radii.iconTile, overflow: 'hidden', backgroundColor: colors.skyWash },
  thumbFallback: { alignItems: 'center', justifyContent: 'center' },
  number: { position: 'absolute', top: -6, left: -6, minWidth: 26, height: 26, borderRadius: 13, paddingHorizontal: 5, backgroundColor: colors.deepOcean, borderWidth: 2, borderColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  numberSelected: { backgroundColor: colors.tealText },
  numberBlocked: { backgroundColor: palette.error },
  numberText: { color: colors.white, fontFamily: fonts.bold, fontSize: 12, lineHeight: 15 },
  copy: { flex: 1, minWidth: 0 },
  timeRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  time: { fontFamily: fonts.bold, fontSize: 13, letterSpacing: 0.2, color: colors.tealText },
  name: { fontFamily: fonts.bold, fontSize: 16, lineHeight: 21, letterSpacing: -0.2, color: colors.ink, marginTop: 2 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 3 },
  meta: { flexShrink: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted },
  conflict: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 6 },
  conflictText: { flexShrink: 1, fontFamily: fonts.bold, fontSize: 13, lineHeight: 18, color: colors.ink },
  extras: { paddingLeft: spacing.sm + THUMB + spacing.sm, paddingRight: spacing.sm, paddingBottom: 2 },
  why: { marginTop: spacing.xs },
  aiLabel: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 2 },
  aiLabelText: { fontFamily: fonts.bold, fontSize: 11, letterSpacing: 0.8, textTransform: 'uppercase', color: colors.tealText },
  whyText: { fontFamily: fonts.medium, fontSize: 14, lineHeight: 20, color: colors.textMuted },
  actions: { flexDirection: 'row', flexWrap: 'wrap', columnGap: spacing.md },
  action: { flexDirection: 'row', alignItems: 'center', gap: 2, minHeight: MIN_TOUCH },
  actionText: { fontFamily: fonts.bold, fontSize: 14, color: colors.tealText },
});
