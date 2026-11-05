import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import type { NumberedDay } from './model';

const TRACK_PAD = 3;
const SEGMENT_RADIUS = 12;

/**
 * Day switcher for the map (1–3 days) as a segmented control: equal segments on one track, the active one raised.
 * Same active day as the open itinerary card.
 */
export function DayTabs({ days, activeDay, dateOf, onChange }: { days: NumberedDay[]; activeDay: number; dateOf: (dayIndex: number) => string; onChange: (dayIndex: number) => void }) {
  const { t } = useTranslation();
  return <View accessibilityRole="tablist" style={d.wrap}>
    <View style={d.track}>
      {days.map(day => {
        const active = day.day_index === activeDay;
        const date = dateOf(day.day_index);
        return <Pressable
          key={day.day_index}
          accessibilityLabel={t('proposal.day.tabA11y', { count: day.stops.length, date, day: day.day_index })}
          accessibilityRole="tab"
          accessibilityState={{ selected: active }}
          onPress={() => onChange(day.day_index)}
          style={({ pressed }) => [d.segment, active && d.active, pressed && !active && { opacity: 0.7 }]}
        >
          <Text numberOfLines={1} style={[d.day, active && d.activeText]}>{t('proposal.day.title', { day: day.day_index })}</Text>
          {date ? <Text numberOfLines={1} style={[d.date, active && d.activeDate]}>{date}</Text> : null}
        </Pressable>;
      })}
    </View>
  </View>;
}

const d = StyleSheet.create({
  wrap: { paddingHorizontal: spacing.lg },
  track: { flexDirection: 'row', padding: TRACK_PAD, borderRadius: SEGMENT_RADIUS + TRACK_PAD, backgroundColor: colors.skyWash },
  segment: { flex: 1, minWidth: 0, minHeight: MIN_TOUCH + 4, paddingHorizontal: spacing.xs, borderRadius: SEGMENT_RADIUS, alignItems: 'center', justifyContent: 'center' },
  active: {
    backgroundColor: colors.white,
    ...Platform.select({
      android: { elevation: 2 },
      default: { shadowColor: colors.ink, shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.12, shadowRadius: 3 },
    }),
  },
  // textMuted falls under 4.5:1 on skyWash, so inactive segments keep deepOcean text; the raised white fill marks the
  // active one, with the ink day label as a second, non-colour cue.
  day: { fontFamily: fonts.medium, fontSize: 14, lineHeight: 18, color: colors.deepOcean },
  activeText: { fontFamily: fonts.bold, color: colors.ink },
  date: { fontFamily: fonts.medium, fontSize: 12, lineHeight: 16, color: colors.deepOcean },
  activeDate: { color: colors.ink },
});
