import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon, travelModeIcon } from '../../../components/ui';
import { currentLocale } from '../../../i18n';
import type { Leg } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { formatApprox, formatDistance, splitDuration } from './format';
import { isMeasured, type NumberedDay } from './model';

/** Fixed rail column left of the stop cards (ui-research 2026-11-08 §3.4). */
export const RAIL_WIDTH = 64;
const LINE = 2;

/** True when any leg of the day carries a demo estimate (`Leg.estimated`, contract 1.0.2). */
export function dayHasEstimate(day: Pick<NumberedDay, 'legs'>): boolean {
  return day.legs.some(leg => leg.estimated && isMeasured(leg.availability));
}

/**
 * One stop on the rail: the arrival time chip (server `planned_arrival`, HH:mm) above a solid line, the card on the
 * right. The rail is decorative for screen readers: the card's own label already reads the times.
 */
export function RailStop({ time, last, children }: { time: string | null; last: boolean; children: ReactNode }) {
  return <View style={r.row}>
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={r.rail}>
      <View style={r.chip}><Text style={r.chipText}>{time ?? '—'}</Text></View>
      {last ? null : <View style={r.line} />}
    </View>
    <View style={r.card}>{children}</View>
  </View>;
}

/** Plain rail segment between two stops when the server supplied no leg (e.g. a stop just added). */
export function RailGap() {
  return <View style={r.legRow}><View style={r.rail}><View style={[r.line, r.gap]} /></View></View>;
}

/** Display duration of a leg in the `proposal.leg.*` copy. */
function useLegDuration() {
  const { t } = useTranslation();
  return (seconds: number) => {
    const { hours, minutes } = splitDuration(seconds);
    return hours === 0
      ? t('proposal.leg.minutes', { count: minutes })
      : minutes === 0 ? t('proposal.leg.hours', { hours }) : t('proposal.leg.hoursMinutes', { hours, minutes });
  };
}

/**
 * One leg on the rail: ≈ distance, mode icon, ≈ duration, centred on the line. Values are the server's; an estimated
 * leg (`Leg.estimated`) is prefixed with ≈ and says "estimated" to screen readers. An unavailable or expired leg draws
 * a dashed red line and shows no numbers (BRU-006).
 */
export function RailLeg({ leg }: { leg: Leg }) {
  const { t } = useTranslation();
  const durationOf = useLegDuration();
  const mode = t(`proposal.leg.${leg.travel_mode}`);
  const measured = isMeasured(leg.availability) && leg.distance_m != null && leg.duration_s != null;

  if (!measured) {
    return <View accessible accessibilityLabel={t('proposal.leg.unavailableA11y', { mode })} style={r.legRow}>
      <View style={r.rail}>
        <Dashes count={3} />
        <View style={r.legStack}>
          <Icon color={palette.error} name={travelModeIcon(leg.travel_mode)} size={16} strokeWidth={2} />
          <Text style={[r.legText, { color: palette.error }]}>{t('proposal.leg.unavailableShort')}</Text>
        </View>
        <Dashes count={3} />
      </View>
    </View>;
  }

  const distance = formatDistance(leg.distance_m ?? 0, currentLocale());
  const duration = durationOf(leg.duration_s ?? 0);
  const show = (value: string) => (leg.estimated ? formatApprox(t, value) : value);
  const label = leg.estimated
    ? t('proposal.leg.estimatedA11y', { distance, duration, mode })
    : t('proposal.leg.a11y', { distance, duration, mode });
  return <View accessible accessibilityLabel={label} style={r.legRow}>
    <View style={r.rail}>
      <View style={[r.line, r.legLine]} />
      <View style={r.legStack}>
        <Text style={r.legText}>{show(distance)}</Text>
        <Icon color={colors.tealText} name={travelModeIcon(leg.travel_mode)} size={16} strokeWidth={2} />
        <Text style={r.legText}>{show(duration)}</Text>
      </View>
      <View style={[r.line, r.legLine]} />
    </View>
  </View>;
}

function Dashes({ count }: { count: number }) {
  return <View style={r.dashes}>{Array.from({ length: count }, (_, index) => <View key={index} style={r.dash} />)}</View>;
}

/** One-line notice under the day chips when any leg of the day is a demo estimate. */
export function EstimateNotice({ style }: { style?: object }) {
  const { t } = useTranslation();
  return <View accessible accessibilityRole="text" style={[r.notice, style]}>
    <Icon color={colors.tealText} name="info" size={16} />
    <Text style={r.noticeText}>{t('proposal.leg.estimateNotice')}</Text>
  </View>;
}

const r = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'stretch' },
  rail: { width: RAIL_WIDTH, alignItems: 'center' },
  chip: { minWidth: 52, paddingHorizontal: 6, paddingVertical: 4, borderRadius: radii.chip, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.hairline, alignItems: 'center', marginTop: spacing.sm },
  chipText: { fontFamily: fonts.bold, fontSize: 13, lineHeight: 17, color: colors.ink, textAlign: 'center' },
  line: { flex: 1, width: LINE, minHeight: spacing.xs, backgroundColor: colors.mutedDot, marginTop: spacing.xxs },
  gap: { minHeight: spacing.md, marginTop: 0 },
  card: { flex: 1, minWidth: 0 },
  legRow: { flexDirection: 'row', minHeight: 72 },
  legLine: { marginTop: 0, minHeight: 6 },
  legStack: { alignItems: 'center', gap: 2, paddingVertical: 4, paddingHorizontal: 2 },
  legText: { fontFamily: fonts.bold, fontSize: 12, lineHeight: 15, color: colors.deepOcean, textAlign: 'center' },
  dashes: { flex: 1, minHeight: 10, justifyContent: 'space-evenly', alignItems: 'center' },
  dash: { width: LINE, height: 4, borderRadius: 1, backgroundColor: palette.error },
  notice: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.xs, paddingVertical: spacing.xs, paddingHorizontal: spacing.sm, borderRadius: radii.inset, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.hairline },
  noticeText: { flex: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted },
});
