import type { ComponentRef } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../../components/ui';
import type { Uuid } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { formatTime } from './format';
import { HealthGlyph } from './icons';
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
};

/**
 * One day of the itinerary as an accordion card: numbered day badge, date and stop count, the server's issue counts
 * for that day (listed, not computed), then the stops joined by measured legs.
 */
export function DayCard({ day, date, cityName, open, active, places, selectedStopId, reducedMotion, onToggle, onSelectStop, onOpenPlace, registerRow }: Props) {
  const { t } = useTranslation();
  const conflicts = [...day.stops.flatMap(stop => stop.conflicts ?? []), ...day.legs.flatMap(leg => leg.conflicts ?? [])];
  const blocking = conflicts.filter(conflict => conflict.severity === 'BLOCKING').length;
  const warnings = conflicts.length - blocking;
  const first = formatTime(day.stops[0]?.planned_arrival);
  const last = formatTime(day.stops[day.stops.length - 1]?.planned_departure);
  const summary = [date, t('proposal.day.stops', { count: day.stops.length }), first && last ? `${first} – ${last}` : null].filter(Boolean).join(' · ');
  const title = t('proposal.day.title', { day: day.day_index });

  return <View style={[c.card, elevation.sm, active && c.cardActive]}>
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
          <Text style={c.emptyTitle}>{t('proposal.day.empty', { day: day.day_index })}</Text>
          <Text style={c.emptyBody}>{t('proposal.day.emptyBody', { city: cityName })}</Text>
        </View>
        : day.stops.map((stop, index) => {
          const leg = index < day.stops.length - 1 ? outgoingLeg(day, stop.id) : undefined;
          return <View key={stop.id}>
            <StopCard
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
    </View>}
  </View>;
}

const c = StyleSheet.create({
  card: { borderRadius: radii.card, backgroundColor: colors.white, borderWidth: 1, borderColor: '#E4EDF2' },
  cardActive: { borderColor: '#BFE0E7' },
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
  chevron: { width: 32, height: 32, borderRadius: 16, backgroundColor: colors.skyWash, alignItems: 'center', justifyContent: 'center', transform: [{ rotate: '90deg' }] },
  chevronOpen: { transform: [{ rotate: '-90deg' }] },
  body: { paddingHorizontal: spacing.xxs, paddingBottom: spacing.xs, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: '#DCE8EE', paddingTop: spacing.xs },
  gap: { height: spacing.xs },
  empty: { alignItems: 'center', padding: spacing.lg },
  emptyTitle: { fontFamily: fonts.bold, fontSize: 16, color: colors.ink, textAlign: 'center' },
  emptyBody: { fontFamily: fonts.medium, fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center', marginTop: 4 },
});
