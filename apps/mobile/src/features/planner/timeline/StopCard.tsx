import { useEffect, useRef, useState, type ComponentRef, type Ref } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { AiMark, Icon, Photo, categoryIcon } from '../../../components/ui';
import { categoryColor, colors, dayColor } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { isProblem } from '../health/reasons';
import { formatTime } from './format';
import { PlannerIcon } from './icons';
import { isStopBlocked, type NumberedStop } from './model';
import type { StopPlace } from './useProposal';

export const THUMB = 64;

type Props = {
  stop: NumberedStop;
  place: StopPlace | undefined;
  /** Localized category name (API-009); omitted when unknown. */
  categoryName?: string | null;
  selected: boolean;
  reducedMotion: boolean;
  onSelect: () => void;
  /** Opens the place page; omitted for a WEB_UNVERIFIED stop (no catalog place). */
  onOpenDetails?: () => void;
  rowRef?: Ref<ComponentRef<typeof View>>;
  /** Editable draft in edit mode: ⋯ opens the Edit stop sheet (SCR-027) and Move up/down are shown (no drag-only path). */
  edit?: StopEditControls;
  /** FEATURE_REGENERATION: show the lock badge on locked stops. */
  showLock?: boolean;
};

export type StopEditControls = {
  onMore: () => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  reorder: boolean;
  disabled: boolean;
};

/**
 * One stop (SCR-024 `StopCard`): photo, name, category colour + name, server times (Asia/Ho_Chi_Minh), chips only for
 * real problems on this stop (WARNING/BLOCKING), the outlined "From the web" chip for a WEB_UNVERIFIED stop, and the
 * AI-written rationale in 1–2 lines beside the violet sparkle. Selecting it selects the same pin on the map.
 */
export function StopCard({ stop, place, categoryName, selected, reducedMotion, onSelect, onOpenDetails, rowRef, edit, showLock = false }: Props) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const highlight = useRef(new Animated.Value(selected ? 1 : 0)).current;

  useEffect(() => {
    if (reducedMotion) { highlight.setValue(selected ? 1 : 0); return; }
    Animated.timing(highlight, { duration: 200, toValue: selected ? 1 : 0, useNativeDriver: true }).start();
  }, [highlight, reducedMotion, selected]);

  const arrival = formatTime(stop.planned_arrival);
  const departure = formatTime(stop.planned_departure);
  const blocked = isStopBlocked(stop);
  const web = stop.trust_level === 'WEB_UNVERIFIED';
  // Chips only for real problems that concern this stop; the web label has its own chip (rule 7, 9).
  const problems = (stop.conflicts ?? []).filter(conflict => isProblem(conflict) && conflict.type !== 'WEB_PLACE_UNVERIFIED');
  const status = [web ? t('proposal.stop.web') : null, ...problems.map(conflict => t(`proposal.conflict.${conflict.type}`))].filter(Boolean).join(', ') || t('proposal.stop.statusOk');
  const minutes = t('proposal.stop.minutes', { count: stop.visit_minutes });
  const time = arrival && departure ? `${arrival} – ${departure}` : null;
  const timeLine = [time, minutes].filter(Boolean).join(' · ');
  const tone = categoryColor(place?.categoryCode);
  // `name` is in the request locale; the Vietnamese name joins the category line when it differs (FR-076).
  const subline = [categoryName, stop.name !== stop.name_vi ? stop.name_vi : null].filter(Boolean).join(' · ');
  const editing = !!edit?.reorder;
  const ring = blocked ? colors.danger : dayColor(stop.dayIndex - 1);

  return <View ref={rowRef} style={[c.root, blocked && c.rootBlocked]}>
    <Animated.View pointerEvents="none" style={[c.highlight, { borderColor: ring, opacity: highlight }]} />
    <View style={c.mainRow}>
      <Pressable
        accessibilityHint={t('proposal.stop.selectHint')}
        accessibilityLabel={time
          ? t('proposal.stop.a11y', { arrival, departure, name: stop.name, number: stop.number, status })
          : t('proposal.stop.a11yNoTime', { name: stop.name, number: stop.number, status, unknown: t('proposal.stop.timeUnknown') })}
        accessibilityRole="button"
        accessibilityState={{ selected }}
        onPress={onSelect}
        style={({ pressed }) => [c.main, pressed && c.pressed]}
      >
        <View style={c.thumb}>
          <Photo categoryCode={place?.categoryCode} height={THUMB} iconSize={26} image={place?.thumbnail} name={stop.name} transition={150} variant="thumb" width={THUMB} />
        </View>
        <View style={c.copy}>
          <View style={c.timeRow}>
            <Text numberOfLines={1} style={c.time}>{timeLine}</Text>
            {showLock && stop.is_locked ? <View style={c.lock}>
              <PlannerIcon color={colors.textSecondary} name="lock" size={12} />
              <Text style={c.lockText}>{t('proposal.edit.locked')}</Text>
            </View> : null}
          </View>
          <Text numberOfLines={2} style={c.name}>{stop.name}</Text>
          {subline ? <View style={c.metaRow}>
            <Icon color={tone.fg} name={categoryIcon(place?.categoryCode)} size={14} strokeWidth={2} />
            <Text numberOfLines={1} style={c.meta}>{subline}</Text>
          </View> : null}
          {web || problems.length ? <View style={c.chips}>
            {web ? <View style={c.webChip}><Text style={c.webText}>{t('proposal.stop.web')}</Text></View> : null}
            {problems.map((conflict, index) => {
              const blocking = conflict.severity === 'BLOCKING';
              return <View key={`${conflict.type}-${index}`} style={[c.chip, { backgroundColor: blocking ? colors.dangerBg : colors.warningBg }]}>
                <Icon color={blocking ? colors.danger : colors.warning} name={blocking ? 'blocked' : 'warning'} size={12} strokeWidth={2.2} />
                <Text style={[c.chipText, { color: blocking ? colors.danger : colors.warning }]}>{t(`proposal.conflict.${conflict.type}`)}</Text>
              </View>;
            })}
          </View> : null}
        </View>
      </Pressable>
      {editing ? <Pressable
        accessibilityLabel={t('proposal.edit.moreA11y', { name: stop.name, number: stop.number })}
        accessibilityRole="button"
        accessibilityState={{ disabled: edit.disabled }}
        disabled={edit.disabled}
        onPress={edit.onMore}
        style={({ pressed }) => [c.side, edit.disabled && c.disabled, pressed && c.pressed]}
      >
        <Icon color={colors.ink} name="more" size={22} />
      </Pressable> : onOpenDetails ? <Pressable
        accessibilityLabel={t('proposal.stop.detailsA11y', { name: stop.name })}
        accessibilityRole="button"
        onPress={onOpenDetails}
        style={({ pressed }) => [c.side, pressed && c.pressed]}
      >
        <Icon color={colors.textMuted} name="chevron-right" size={20} strokeWidth={2} />
      </Pressable> : null}
    </View>
    {stop.rationale ? <Pressable
      accessibilityHint={t(expanded ? 'proposal.stop.whyHide' : 'proposal.stop.whyMore')}
      accessibilityRole="button"
      accessibilityState={{ expanded }}
      onPress={() => setExpanded(value => !value)}
      style={c.why}
    >
      <View style={c.aiMark}><AiMark size={14} /></View>
      <Text numberOfLines={expanded ? undefined : 2} style={c.whyText}>{stop.rationale}</Text>
    </Pressable> : null}
    {editing ? <View style={c.reorder}>
      <ReorderButton accessibilityLabel={t('proposal.edit.moveUpA11y', { name: stop.name })} disabled={edit.disabled || !edit.onMoveUp} icon="arrowUp" label={t('proposal.edit.moveUp')} onPress={edit.onMoveUp} />
      <ReorderButton accessibilityLabel={t('proposal.edit.moveDownA11y', { name: stop.name })} disabled={edit.disabled || !edit.onMoveDown} icon="arrowDown" label={t('proposal.edit.moveDown')} onPress={edit.onMoveDown} />
      <ReorderButton disabled={edit.disabled} icon="edit" label={t('proposal.edit.more')} onPress={edit.onMore} />
    </View> : null}
  </View>;
}

function ReorderButton({ label, icon, onPress, disabled, accessibilityLabel }: { label: string; icon: 'arrowUp' | 'arrowDown' | 'edit'; onPress?: () => void; disabled: boolean; accessibilityLabel?: string }) {
  return <Pressable
    accessibilityLabel={accessibilityLabel ?? label}
    accessibilityRole="button"
    accessibilityState={{ disabled }}
    disabled={disabled}
    onPress={onPress}
    style={({ pressed }) => [c.reorderButton, disabled && c.disabled, pressed && c.pressed]}
  >
    <PlannerIcon color={colors.ink} name={icon} size={16} />
    <Text style={c.reorderText}>{label}</Text>
  </Pressable>;
}

const c = StyleSheet.create({
  root: { borderRadius: radii.card, backgroundColor: colors.surface, paddingBottom: spacing.sm },
  rootBlocked: { backgroundColor: colors.dangerBg },
  highlight: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, borderRadius: radii.card, borderWidth: 2 },
  mainRow: { flexDirection: 'row' },
  main: { flex: 1, flexDirection: 'row', gap: spacing.sm, paddingLeft: spacing.sm, paddingTop: spacing.sm },
  pressed: { opacity: 0.7 },
  disabled: { opacity: 0.4 },
  side: { width: MIN_TOUCH, minHeight: MIN_TOUCH, alignItems: 'center', justifyContent: 'center', marginTop: spacing.xxs },
  thumb: { width: THUMB, height: THUMB, borderRadius: radii.photo, overflow: 'hidden', backgroundColor: colors.hairline },
  copy: { flex: 1, minWidth: 0 },
  timeRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  time: { flexShrink: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textSecondary },
  lock: { flexDirection: 'row', alignItems: 'center', gap: 3, paddingHorizontal: 6, paddingVertical: 1, borderRadius: radii.pill, backgroundColor: colors.white },
  lockText: { fontFamily: fonts.semibold, fontSize: 11, color: colors.textSecondary },
  name: { fontFamily: fonts.semibold, fontSize: 16, lineHeight: 21, color: colors.ink, marginTop: 1 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 3 },
  meta: { flexShrink: 1, fontFamily: fonts.regular, fontSize: 13, lineHeight: 18, color: colors.textSecondary },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 6 },
  chip: { flexDirection: 'row', alignItems: 'center', gap: 4, minHeight: 24, paddingHorizontal: 8, borderRadius: radii.pill, maxWidth: '100%' },
  chipText: { flexShrink: 1, fontFamily: fonts.semibold, fontSize: 12, lineHeight: 16 },
  webChip: { minHeight: 24, justifyContent: 'center', paddingHorizontal: 8, borderRadius: radii.pill, borderWidth: 1, borderColor: colors.warning, backgroundColor: colors.white },
  webText: { fontFamily: fonts.semibold, fontSize: 12, lineHeight: 16, color: colors.warning },
  why: { flexDirection: 'row', alignItems: 'flex-start', gap: 6, paddingHorizontal: spacing.sm, paddingTop: spacing.xs },
  aiMark: { marginTop: 3 },
  whyText: { flex: 1, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textSecondary },
  reorder: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, paddingHorizontal: spacing.sm, paddingTop: spacing.sm },
  reorderButton: { flexDirection: 'row', alignItems: 'center', gap: 5, minHeight: MIN_TOUCH, paddingHorizontal: 12, borderRadius: radii.button, backgroundColor: colors.white },
  reorderText: { fontFamily: fonts.semibold, fontSize: 13, color: colors.ink },
});
