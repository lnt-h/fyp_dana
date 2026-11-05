import { StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon, travelModeIcon } from '../../../components/ui';
import { currentLocale } from '../../../i18n';
import type { Leg } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { formatDistance, splitDuration } from './format';
import { isMeasured } from './model';
import { THUMB } from './StopCard';

/** Rail x position: centred under the stop thumbnail. */
const RAIL_X = spacing.sm + THUMB / 2 - 1;

/**
 * Compact connector between two stops, exactly as measured by the server (Google Routes). Unavailable/expired legs
 * draw a dashed red rail and show no length or duration (BRU-006).
 */
export function LegRow({ leg }: { leg: Leg }) {
  const { t } = useTranslation();
  const mode = t(`proposal.leg.${leg.travel_mode}`);
  const measured = isMeasured(leg.availability) && leg.distance_m != null && leg.duration_s != null;
  const tone = measured ? colors.tealText : palette.error;
  const icon = <Icon color={tone} name={travelModeIcon(leg.travel_mode)} size={16} strokeWidth={2} />;

  if (!measured) {
    return <View accessible accessibilityLabel={t('proposal.leg.unavailableA11y', { mode })} style={l.row}>
      <View style={l.dashRail}>{[0, 1, 2, 3, 4, 5].map(index => <View key={index} style={l.dash} />)}</View>
      <View style={[l.pill, l.pillBlocked]}>
        {icon}
        <Text style={[l.text, { color: palette.error }]}>{`${mode} · ${t('proposal.leg.unavailable')}`}</Text>
      </View>
    </View>;
  }

  const { hours, minutes } = splitDuration(leg.duration_s ?? 0);
  const duration = hours === 0
    ? t('proposal.leg.minutes', { count: minutes })
    : minutes === 0 ? t('proposal.leg.hours', { hours }) : t('proposal.leg.hoursMinutes', { hours, minutes });
  const distance = formatDistance(leg.distance_m ?? 0, currentLocale());
  return <View accessible accessibilityLabel={t('proposal.leg.a11y', { distance, duration, mode })} style={l.row}>
    <View style={l.dotRail}>{[0, 1, 2, 3, 4].map(index => <View key={index} style={l.dot} />)}</View>
    <View style={l.pill}>
      {icon}
      <Text style={l.text}>{`${mode} · ${distance} · ${duration}`}</Text>
    </View>
  </View>;
}

const l = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', minHeight: 40, paddingLeft: spacing.sm + THUMB + spacing.sm },
  dotRail: { position: 'absolute', left: RAIL_X - 1, top: 2, bottom: 2, justifyContent: 'space-between', alignItems: 'center' },
  dot: { width: 4, height: 4, borderRadius: 2, backgroundColor: colors.mutedDot },
  dashRail: { position: 'absolute', left: RAIL_X, top: 0, bottom: 0, width: 2, justifyContent: 'space-between', paddingVertical: 2 },
  dash: { width: 2, height: 4, borderRadius: 1, backgroundColor: palette.error },
  pill: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 5, borderRadius: radii.chip, backgroundColor: colors.surfaceTint, flexShrink: 1 },
  pillBlocked: { backgroundColor: colors.white, borderWidth: 1, borderColor: palette.error },
  text: { flexShrink: 1, fontFamily: fonts.bold, fontSize: 12, lineHeight: 16, color: colors.deepOcean },
});
