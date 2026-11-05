import type { ComponentRef } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../../components/ui';
import type { Uuid } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { formatTime } from './format';
import { HealthGlyph, PlannerIcon } from './icons';
import { LegRow } from './LegRow';
import { outgoingLeg, type NumberedDay } from './model';
import { StopCard } from './StopCard';
import type { StopPlace } from './useProposal';

type Props = {
  day: NumberedDay;
  date: string;
  cityName: string;
  open: boolean;
  active: boolean;
  places: Record<Uuid, StopPlace>;
  selectedStopId: Uuid | null;
  reducedMotion: boolean;
  onToggle: () => void;
  onSelectStop: (stopId: Uuid) => void;
  onOpenPlace: (placeId: Uuid) => void;
  registerRow: (stopId: Uuid, view: ComponentRef<typeof View> | null) => void;
  /** Editable draft controls (absent for a saved, read-only itinerary). */
  edit?: DayEditControls;
};

export type DayEditControls = {
  /** Edit mode: Move up/down on each stop plus the day's Add / Regenerate actions. */
  editing: boolean;
  disabled: boolean;
  showLock: boolean;
  onEditStop: (stopId: Uuid) => void;
  onMoveStop: (stopId: Uuid, direction: -1 | 1) => void;
  onAddStop: () => void;
  /** FEATURE_REGENERATION only. */
  onRegenerate?: () => void;
};

/**
 * One day of the itinerary as an accordion card: numbered day badge, date and stop count, the server's issue counts
 * for that day (listed, not computed), then the stops joined by measured legs.
 */
export function DayCard({ day, date, cityName, open, active, places, selectedStopId, reducedMotion, onToggle, onSelectStop, onOpenPlace, registerRow, edit }: Props) {
  const { t } = useTranslation();
  const conflicts = [...day.stops.flatMap(stop => stop.conflicts ?? []), ...day.legs.flatMap(leg => leg.conflicts ?? [])];
  const blocking = conflicts.filter(conflict => conflict.severity === 'BLOCKING').length;
  const warnings = conflicts.length - blocking;
  const first = formatTime(day.stops[0]?.planned_arrival);
  const last = formatTime(day.stops[day.stops.length - 1]?.planned_departure);
  const summary = [date, t('proposal.day.stops', { count: day.stops.length }), first && last ? `${first} – ${last}` : null].filter(Boolean).join(' · ');
  const title = t('proposal.day.title', { day: day.day_index });

  return <View style={[c.card, active && c.cardActive]}>
    <Pressable
      accessibilityHint={t('proposal.day.expandHint')}
      accessibilityLabel={[title, summary].join(', ')}
      accessibilityRole="button"
      accessibilityState={{ expanded: open }}
      onPress={onToggle}
      style={({ pressed }) => [c.head, pressed && { opacity: 0.75 }]}
    >
      <View style={[c.badge, active && c.badgeActive]}>
        <Text style={c.badgeText}>{day.day_index}</Text>
      </View>
      <View style={c.headCopy}>
        <Text accessibilityRole="header" style={c.title}>{title}</Text>
        <Text numberOfLines={1} style={c.summary}>{summary}</Text>
        {(blocking > 0 || warnings > 0) && <View style={c.issues}>
          {blocking > 0 && <View style={c.issue}>
            <HealthGlyph health="BLOCKED" size={14} />
            <Text style={[c.issueText, { color: palette.error }]}>{t('proposal.day.blocking', { count: blocking })}</Text>
          </View>}
          {warnings > 0 && <View style={c.issue}>
            <HealthGlyph health="WARNING" size={14} />
            <Text style={c.issueText}>{t('proposal.day.warnings', { count: warnings })}</Text>
          </View>}
        </View>}
      </View>
      <View style={[c.chevron, open && c.chevronOpen]}>
        <Icon color={colors.deepOcean} name="chevron-right" size={18} strokeWidth={2.2} />
      </View>
    </Pressable>
    {open && <View style={c.body}>
      {day.stops.length === 0
        ? <View style={c.empty}>
          <View style={c.emptyIcon}><Icon color={colors.tealText} name="map-pin" size={24} /></View>
          <Text style={c.emptyTitle}>{t('proposal.day.empty', { day: day.day_index })}</Text>
          <Text style={c.emptyBody}>{t('proposal.day.emptyBody', { city: cityName })}</Text>
        </View>
        : day.stops.map((stop, index) => {
          const leg = index < day.stops.length - 1 ? outgoingLeg(day, stop.id) : undefined;
          return <View key={stop.id}>
            <StopCard
              edit={edit ? {
                disabled: edit.disabled,
                onMore: () => edit.onEditStop(stop.id),
                onMoveDown: index < day.stops.length - 1 ? () => edit.onMoveStop(stop.id, 1) : undefined,
                onMoveUp: index > 0 ? () => edit.onMoveStop(stop.id, -1) : undefined,
                reorder: edit.editing,
              } : undefined}
              showLock={edit?.showLock}
              onOpenDetails={() => onOpenPlace(stop.place_id)}
              onSelect={() => onSelectStop(stop.id)}
              place={places[stop.place_id]}
              reducedMotion={reducedMotion}
              rowRef={view => registerRow(stop.id, view)}
              selected={stop.id === selectedStopId}
              stop={stop}
            />
            {leg ? <LegRow leg={leg} /> : index < day.stops.length - 1 ? <View style={c.gap} /> : null}
          </View>;
        })}
      {edit && (edit.editing || day.stops.length === 0) ? <View style={c.editRow}>
        <DayAction disabled={edit.disabled} icon="plus" label={t('proposal.edit.addStop')} accessibilityLabel={t('proposal.edit.addStopA11y', { day: day.day_index })} onPress={edit.onAddStop} primary />
        {edit.onRegenerate ? <DayAction disabled={edit.disabled} icon="refresh" label={t('proposal.edit.regenerate')} accessibilityLabel={t('proposal.edit.regenerateA11y', { day: day.day_index })} onPress={edit.onRegenerate} /> : null}
      </View> : null}
    </View>}
  </View>;
}

function DayAction({ label, icon, onPress, disabled, primary, accessibilityLabel }: { label: string; icon: 'plus' | 'refresh'; onPress: () => void; disabled: boolean; primary?: boolean; accessibilityLabel: string }) {
  return <Pressable
    accessibilityLabel={accessibilityLabel}
    accessibilityRole="button"
    accessibilityState={{ disabled }}
    disabled={disabled}
    onPress={onPress}
    style={({ pressed }) => [c.dayAction, primary && c.dayActionPrimary, disabled && { opacity: 0.4 }, pressed && { opacity: 0.75 }]}
  >
    <PlannerIcon color={primary ? colors.tealText : colors.deepOcean} name={icon} size={18} />
    <Text style={[c.dayActionText, primary && { color: colors.tealText }]}>{label}</Text>
  </Pressable>;
}

const c = StyleSheet.create({
  card: { borderRadius: radii.card, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.hairline },
  cardActive: { borderColor: colors.audioTeal },
  head: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, minHeight: 72, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  badge: { width: 38, height: 38, borderRadius: 19, backgroundColor: colors.deepOcean, alignItems: 'center', justifyContent: 'center' },
  badgeActive: { backgroundColor: colors.tealText },
  badgeText: { color: colors.white, fontFamily: fonts.bold, fontSize: 16 },
  headCopy: { flex: 1, minWidth: 0 },
  title: { fontFamily: fonts.bold, fontSize: 18, lineHeight: 23, letterSpacing: -0.3, color: colors.ink },
  summary: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted, marginTop: 1 },
  issues: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: 4 },
  issue: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  issueText: { fontFamily: fonts.bold, fontSize: 12, color: colors.ink },
  chevron: { width: 32, height: 32, borderRadius: 16, backgroundColor: colors.surfaceTint, alignItems: 'center', justifyContent: 'center', transform: [{ rotate: '90deg' }] },
  chevronOpen: { transform: [{ rotate: '-90deg' }] },
  body: { paddingHorizontal: spacing.xxs, paddingBottom: spacing.xs, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.hairline, paddingTop: spacing.xs },
  gap: { height: spacing.xs },
  empty: { alignItems: 'center', padding: spacing.lg },
  emptyIcon: { width: 52, height: 52, borderRadius: 26, backgroundColor: colors.surfaceTint, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.xs },
  editRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, paddingHorizontal: spacing.sm, paddingTop: spacing.xs, paddingBottom: spacing.xs },
  dayAction: { flexGrow: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, minHeight: 48, paddingHorizontal: 14, borderRadius: radii.button, borderWidth: 1.5, borderColor: colors.hairline, backgroundColor: colors.white },
  dayActionPrimary: { borderStyle: 'dashed', borderColor: colors.audioTeal, backgroundColor: colors.canvas },
  dayActionText: { fontFamily: fonts.bold, fontSize: 14, color: colors.deepOcean },
  emptyTitle: { fontFamily: fonts.bold, fontSize: 16, color: colors.ink, textAlign: 'center' },
  emptyBody: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center', marginTop: 4 },
});
