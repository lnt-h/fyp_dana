import type { ComponentRef } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../../components/ui';
import type { Uuid } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { formatTime } from './format';
import { PlannerIcon } from './icons';
import { outgoingLeg, type NumberedDay } from './model';
import { StopCard } from './StopCard';
import { RailGap, RailLeg, RailStop } from './TimeRail';
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
  selectedStopId: Uuid | null;
  reducedMotion: boolean;
  onSelectStop: (stopId: Uuid) => void;
  onOpenPlace: (placeId: Uuid) => void;
  registerRow: (stopId: Uuid, view: ComponentRef<typeof View> | null) => void;
  /** Editable draft controls (absent for a saved, read-only itinerary). */
  edit?: DayEditControls;
};

/**
 * One day's stops on the left time rail (Vietdetour pattern): arrival chip, stop card, then the leg to the next stop
 * with its server distance and duration. Used flat under the date chips (preview) and inside the saved day accordion.
 */
export function DayTimeline({ day, cityName, places, selectedStopId, reducedMotion, onSelectStop, onOpenPlace, registerRow, edit }: DayTimelineProps) {
  const { t } = useTranslation();
  return <View>
    {day.stops.length === 0
      ? <View style={s.empty}>
        <View style={s.emptyArt}>
          <Icon color={colors.tealText} name="map-pin" size={28} />
          <View style={s.emptyDots}>{[0, 1, 2].map(index => <View key={index} style={s.emptyDot} />)}</View>
          <Icon color={colors.accentText} name="sparkle" size={20} />
        </View>
        <Text style={s.emptyTitle}>{t('proposal.day.empty', { day: day.day_index })}</Text>
        <Text style={s.emptyBody}>{t('proposal.day.emptyBody', { city: cityName })}</Text>
      </View>
      : day.stops.map((stop, index) => {
        const last = index === day.stops.length - 1;
        const leg = last ? undefined : outgoingLeg(day, stop.id);
        return <View key={stop.id}>
          <RailStop last={last} time={formatTime(stop.planned_arrival)}>
            <StopCard
              edit={edit ? {
                disabled: edit.disabled,
                onMore: () => edit.onEditStop(stop.id),
                onMoveDown: !last ? () => edit.onMoveStop(stop.id, 1) : undefined,
                onMoveUp: index > 0 ? () => edit.onMoveStop(stop.id, -1) : undefined,
                reorder: edit.editing,
              } : undefined}
              framed
              showLock={edit?.showLock}
              onOpenDetails={stop.place_id ? () => onOpenPlace(stop.place_id as string) : undefined}
              onSelect={() => onSelectStop(stop.id)}
              place={stop.place_id ? places[stop.place_id] : undefined}
              reducedMotion={reducedMotion}
              rowRef={view => registerRow(stop.id, view)}
              selected={stop.id === selectedStopId}
              stop={stop}
            />
          </RailStop>
          {last ? null : leg ? <RailLeg leg={leg} /> : <RailGap />}
        </View>;
      })}
    {edit && (edit.editing || day.stops.length === 0) ? <View style={s.editRow}>
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
    <PlannerIcon color={primary ? colors.tealText : colors.deepOcean} name={icon} size={18} />
    <Text style={[s.dayActionText, primary && { color: colors.tealText }]}>{label}</Text>
  </Pressable>;
}

const s = StyleSheet.create({
  empty: { alignItems: 'center', padding: spacing.lg, borderRadius: radii.card, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.hairline },
  emptyArt: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: radii.card, backgroundColor: colors.surfaceTint, marginBottom: spacing.sm },
  emptyDots: { flexDirection: 'row', gap: 4 },
  emptyDot: { width: 5, height: 5, borderRadius: 2.5, backgroundColor: colors.mutedDot },
  emptyTitle: { fontFamily: fonts.bold, fontSize: 16, color: colors.ink, textAlign: 'center' },
  emptyBody: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center', marginTop: 4 },
  editRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, paddingTop: spacing.sm, paddingBottom: spacing.xs },
  dayAction: { flexGrow: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, minHeight: Math.max(MIN_TOUCH, 48), paddingHorizontal: 14, borderRadius: radii.button, borderWidth: 1.5, borderColor: colors.hairline, backgroundColor: colors.white },
  dayActionPrimary: { borderStyle: 'dashed', borderColor: colors.audioTeal, backgroundColor: colors.canvas },
  dayActionText: { fontFamily: fonts.bold, fontSize: 14, color: colors.deepOcean },
});
