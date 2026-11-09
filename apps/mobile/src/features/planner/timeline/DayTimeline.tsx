import type { ComponentRef } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../../components/ui';
import type { Uuid } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { PlannerIcon } from './icons';
import { outgoingLeg, type NumberedDay } from './model';
import { StopCard } from './StopCard';
import { RAIL_WIDTH, RailGap, RailLeg, RailStop } from './TimeRail';
import type { StopPlace } from './useProposal';

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

export type DayTimelineProps = {
  day: NumberedDay;
  cityName: string;
  places: Record<Uuid, StopPlace>;
  /** Localized category names by code (display only). */
  categoryNames?: Record<string, string>;
  selectedStopId: Uuid | null;
  reducedMotion: boolean;
  onSelectStop: (stopId: Uuid) => void;
  onOpenPlace: (placeId: Uuid) => void;
  registerRow: (stopId: Uuid, view: ComponentRef<typeof View> | null) => void;
  /** Editable draft controls (absent for a saved, read-only itinerary). */
  edit?: DayEditControls;
};

/**
 * One day's stops on the rail (Wanderlog pattern): numbered pin in the day colour, stop card, then the quiet leg row to
 * the next stop with the server's duration and distance. Pins share number and colour with the map.
 */
export function DayTimeline({ day, cityName, places, categoryNames = {}, selectedStopId, reducedMotion, onSelectStop, onOpenPlace, registerRow, edit }: DayTimelineProps) {
  const { t } = useTranslation();
  const place = (placeId: Uuid | null | undefined) => (placeId ? places[placeId] : undefined);
  return <View>
    {day.stops.length === 0
      ? <View style={s.empty}>
        <View style={s.emptyArt}><Icon color={colors.primary} name="map-pin" size={26} /></View>
        <Text style={s.emptyTitle}>{t('proposal.day.empty', { day: day.day_index })}</Text>
        <Text style={s.emptyBody}>{t('proposal.day.emptyBody', { city: cityName })}</Text>
      </View>
      : day.stops.map((stop, index) => {
        const last = index === day.stops.length - 1;
        const leg = last ? undefined : outgoingLeg(day, stop.id);
        // Per-day numbering (Wave 6 P2): the rail restarts at 1 each day; `stop.number` stays continuous for health/a11y copy.
        const displayNumber = index + 1;
        return <View key={stop.id}>
          <RailStop dayIndex={day.day_index} last={last} number={displayNumber}>
            <StopCard
              categoryName={categoryNames[place(stop.place_id)?.categoryCode ?? ''] ?? null}
              edit={edit ? {
                disabled: edit.disabled,
                onMore: () => edit.onEditStop(stop.id),
                onMoveDown: !last ? () => edit.onMoveStop(stop.id, 1) : undefined,
                onMoveUp: index > 0 ? () => edit.onMoveStop(stop.id, -1) : undefined,
                reorder: edit.editing,
              } : undefined}
              showLock={edit?.showLock}
              onOpenDetails={stop.place_id ? () => onOpenPlace(stop.place_id as string) : undefined}
              onSelect={() => onSelectStop(stop.id)}
              place={place(stop.place_id)}
              reducedMotion={reducedMotion}
              rowRef={view => registerRow(stop.id, view)}
              selected={stop.id === selectedStopId}
              stop={{ ...stop, number: displayNumber }}
            />
          </RailStop>
          {last ? null : leg ? <RailLeg leg={leg} /> : <RailGap />}
        </View>;
      })}
    {edit && (edit.editing || day.stops.length === 0) ? <View style={[s.editRow, day.stops.length > 0 && s.editRowIndent]}>
      <DayAction disabled={edit.disabled} icon="plus" label={t('proposal.edit.addStop')} accessibilityLabel={t('proposal.edit.addStopA11y', { day: day.day_index })} onPress={edit.onAddStop} primary />
      {edit.onRegenerate ? <DayAction disabled={edit.disabled} icon="refresh" label={t('proposal.edit.regenerate')} accessibilityLabel={t('proposal.edit.regenerateA11y', { day: day.day_index })} onPress={edit.onRegenerate} /> : null}
    </View> : null}
  </View>;
}

function DayAction({ label, icon, onPress, disabled, primary, accessibilityLabel }: { label: string; icon: 'plus' | 'refresh'; onPress: () => void; disabled: boolean; primary?: boolean; accessibilityLabel: string }) {
  return <Pressable
    accessibilityLabel={accessibilityLabel}
    accessibilityRole="button"
    accessibilityState={{ disabled }}
    disabled={disabled}
    onPress={onPress}
    style={({ pressed }) => [s.dayAction, primary && s.dayActionPrimary, disabled && { opacity: 0.4 }, pressed && { opacity: 0.75 }]}
  >
    <PlannerIcon color={primary ? colors.primary : colors.ink} name={icon} size={18} />
    <Text style={[s.dayActionText, primary && { color: colors.primary }]}>{label}</Text>
  </Pressable>;
}

const s = StyleSheet.create({
  empty: { alignItems: 'center', padding: spacing.lg, borderRadius: radii.card, backgroundColor: colors.surface },
  emptyArt: { width: 52, height: 52, borderRadius: 26, backgroundColor: colors.primarySoft, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm },
  emptyTitle: { fontFamily: fonts.semibold, fontSize: 16, color: colors.ink, textAlign: 'center' },
  emptyBody: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center', marginTop: 4 },
  editRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, paddingTop: spacing.sm, paddingBottom: spacing.xs },
  editRowIndent: { paddingLeft: RAIL_WIDTH + spacing.xs },
  dayAction: { flexGrow: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, minHeight: Math.max(MIN_TOUCH, 48), paddingHorizontal: 14, borderRadius: radii.button, backgroundColor: colors.surface },
  dayActionPrimary: { backgroundColor: colors.primarySoft },
  dayActionText: { fontFamily: fonts.semibold, fontSize: 14, color: colors.ink },
});
