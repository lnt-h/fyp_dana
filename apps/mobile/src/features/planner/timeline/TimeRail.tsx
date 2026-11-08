import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon, NumberPin, travelModeIcon } from '../../../components/ui';
import { currentLocale } from '../../../i18n';
import type { Leg } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { formatApprox, formatDistance, splitDuration } from './format';
import { isProblem } from '../health/reasons';
import { isMeasured, type NumberedDay } from './model';

/** Fixed rail column left of the stop cards: the numbered pin and the connector. */
export const RAIL_WIDTH = 36;
const LINE = 2;

/** True when any leg of the day carries a demo estimate (`Leg.estimated`, contract 1.0.2). */
export function dayHasEstimate(day: Pick<NumberedDay, 'legs'>): boolean {
  return day.legs.some(leg => leg.estimated && isMeasured(leg.availability));
}

/**
 * One stop on the rail: the numbered pin in the day colour (same number and colour as the map pin) above the
 * connector, the card on the right. The rail is decorative for screen readers: the card's own label reads the number.
 */
export function RailStop({ number, dayIndex, last, children }: { number: number; dayIndex: number; last: boolean; children: ReactNode }) {
  return <View style={r.row}>
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={r.rail}>
      <NumberPin dayIndex={dayIndex - 1} number={number} size={28} style={r.pin} />
      {last ? null : <View style={r.line} />}
    </View>
    <View style={r.card}>{children}</View>
  </View>;
}

/** Plain rail segment between two stops when the server supplied no leg (e.g. a stop just added). */
export function RailGap() {
  return <View style={r.legRow}><View style={r.rail}><View style={r.line} /></View></View>;
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
 * One leg between two stops: a quiet grey row `🚶 ≈ 12 min · 3 km` beside the connector. Values are the server's; an
 * estimated leg (`Leg.estimated`) is prefixed with ≈, drawn with a dashed connector and says "estimated" to screen
 * readers. An unavailable or expired leg draws a red dashed connector and shows no numbers (BRU-006).
 */
export function RailLeg({ leg }: { leg: Leg }) {
  const { t } = useTranslation();
  const durationOf = useLegDuration();
  const mode = t(`proposal.leg.${leg.travel_mode}`);
  const measured = isMeasured(leg.availability) && leg.distance_m != null && leg.duration_s != null;

  if (!measured) {
    return <View accessible accessibilityLabel={t('proposal.leg.unavailableA11y', { mode })} style={r.legRow}>
      <View style={r.rail}><Dashes color={colors.danger} /></View>
      <View style={r.legBody}><View style={r.legCopy}>
        <Icon color={colors.danger} name={travelModeIcon(leg.travel_mode)} size={16} strokeWidth={2} />
        <Text style={[r.legText, r.legDanger]}>{t('proposal.leg.unavailableShort')}</Text>
      </View></View>
    </View>;
  }

  const distance = formatDistance(leg.distance_m ?? 0, currentLocale());
  const duration = durationOf(leg.duration_s ?? 0);
  // One ≈ in front of the pair (`≈ 12 min · 3 km`, DEC-023), as in the brief.
  const show = (value: string) => (leg.estimated ? formatApprox(t, value) : value);
  const label = leg.estimated
    ? t('proposal.leg.estimatedA11y', { distance, duration, mode })
    : t('proposal.leg.a11y', { distance, duration, mode });
  // Real problems on this leg (e.g. LEG_MODE_RESTRICTED) are shown right on it (FR-030); estimates are not problems.
  const problems = (leg.conflicts ?? []).filter(isProblem);
  const problemText = problems.map(conflict => t(`proposal.conflict.${conflict.type}`));
  return <View accessible accessibilityLabel={[label, ...problemText].join(', ')} style={r.legRow}>
    <View style={r.rail}>{leg.estimated ? <Dashes color={colors.mutedDot} /> : <View style={r.line} />}</View>
    <View style={r.legBody}>
      <View style={r.legCopy}>
        <Icon color={colors.textMuted} name={travelModeIcon(leg.travel_mode)} size={16} strokeWidth={2} />
        <Text style={r.legText}>{show(`${duration} · ${distance}`)}</Text>
      </View>
      {problems.map((conflict, index) => {
        const blocking = conflict.severity === 'BLOCKING';
        return <View key={`${conflict.type}-${index}`} style={[r.legChip, { backgroundColor: blocking ? colors.dangerBg : colors.warningBg }]}>
          <Icon color={blocking ? colors.danger : colors.warning} name={blocking ? 'blocked' : 'warning'} size={12} strokeWidth={2.2} />
          <Text style={[r.legChipText, { color: blocking ? colors.danger : colors.warning }]}>{problemText[index]}</Text>
        </View>;
      })}
    </View>
  </View>;
}

/** Vertical dashed connector (RN cannot dash a single border side reliably on iOS). */
function Dashes({ color }: { color: string }) {
  return <View style={r.dashes}>{Array.from({ length: 5 }, (_, index) => <View key={index} style={[r.dash, { backgroundColor: color }]} />)}</View>;
}

/**
 * The one estimate legend per day header (DEC-023): `≈ estimated travel times`. Shown only when a leg of the day is a
 * demo estimate; the ≈ on each leg carries the rest.
 */
export function EstimateLegend({ style }: { style?: object }) {
  const { t } = useTranslation();
  return <Text accessibilityRole="text" style={[r.legend, style]}>{t('proposal.leg.legend')}</Text>;
}

const r = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'stretch' },
  rail: { width: RAIL_WIDTH, alignItems: 'center' },
  pin: { marginTop: spacing.xs },
  line: { flex: 1, width: LINE, minHeight: spacing.xs, borderRadius: 1, backgroundColor: colors.hairline, marginTop: spacing.xxs },
  card: { flex: 1, minWidth: 0, paddingLeft: spacing.xs },
  legRow: { flexDirection: 'row', minHeight: 40 },
  legBody: { flex: 1, justifyContent: 'center', gap: 4, paddingLeft: spacing.sm, paddingVertical: 6 },
  legCopy: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legChip: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', gap: 4, minHeight: 24, paddingHorizontal: 8, borderRadius: 999 },
  legChipText: { flexShrink: 1, fontFamily: fonts.semibold, fontSize: 12, lineHeight: 16 },
  legText: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted },
  legDanger: { color: colors.danger, fontFamily: fonts.semibold },
  dashes: { flex: 1, minHeight: 32, justifyContent: 'space-evenly', alignItems: 'center', paddingVertical: 2 },
  dash: { width: LINE, height: 4, borderRadius: 1 },
  legend: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 18, color: colors.textMuted },
});
