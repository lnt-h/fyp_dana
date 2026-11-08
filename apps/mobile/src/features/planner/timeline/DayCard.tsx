import type { ComponentRef } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../../components/ui';
import type { Uuid } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { DayTimeline, type DayEditControls } from './DayTimeline';
import { formatTime } from './format';
import { HealthGlyph } from './icons';
import type { NumberedDay } from './model';
import { dayHasEstimate, EstimateNotice } from './TimeRail';
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

export type { DayEditControls };

/**
 * One day of the itinerary as an accordion card: numbered day badge, date and stop count, the server's issue counts
 * for that day (listed, not computed), then the day's stops on the time rail. Used for the saved, read-only itinerary.
 */
export function DayCard({ day, date, cityName, open, active, places, selectedStopId, reducedMotion, onToggle, onSelectStop, onOpenPlace, registerRow, edit }: Props) {
  const { t } = useTranslation();
  const conflicts = [...day.stops.flatMap(stop => stop.conflicts ?? []), ...day.legs.flatMap(leg => leg.conflicts ?? [])];
  const blocking = conflicts.filter(conflict => conflict.severity === 'BLOCKING').length;
  // INFO notices (e.g. estimated legs) are not warnings and are not counted here.
  const warnings = conflicts.filter(conflict => conflict.severity === 'WARNING').length;
  const first = formatTime(day.stops[0]?.planned_arrival);
  const last = formatTime(day.stops[day.stops.length - 1]?.planned_departure);
  const summary = [date, t('proposal.day.stops', { count: day.stops.length }), first && last ? `${first} – ${last}` : null].filter(Boolean).join(' · ');
  const title = t('proposal.day.title', { day: day.day_index });
  const estimated = dayHasEstimate(day);

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
      {estimated ? <EstimateNotice style={c.notice} /> : null}
      <DayTimeline
        cityName={cityName}
        day={day}
        edit={edit}
        onOpenPlace={onOpenPlace}
        onSelectStop={onSelectStop}
        places={places}
        reducedMotion={reducedMotion}
        registerRow={registerRow}
        selectedStopId={selectedStopId}
      />
    </View>}
  </View>;
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
  body: { paddingRight: spacing.sm, paddingBottom: spacing.sm, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.hairline, paddingTop: spacing.xs, backgroundColor: colors.canvas, borderBottomLeftRadius: radii.card, borderBottomRightRadius: radii.card },
  notice: { marginLeft: spacing.sm, marginBottom: spacing.xs },
});
