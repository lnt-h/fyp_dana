import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';
import { useTranslation } from 'react-i18next';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import type { NumberedDay } from './model';

/** Day switcher for the map (1–3 days). Same active day as the open itinerary card. */
export function DayTabs({ days, activeDay, dateOf, onChange }: { days: NumberedDay[]; activeDay: number; dateOf: (dayIndex: number) => string; onChange: (dayIndex: number) => void }) {
  const { t } = useTranslation();
  return <ScrollView accessibilityRole="tablist" contentContainerStyle={d.row} horizontal showsHorizontalScrollIndicator={false}>
    {days.map(day => {
      const active = day.day_index === activeDay;
      const date = dateOf(day.day_index);
      return <Pressable
        key={day.day_index}
        accessibilityLabel={t('proposal.day.tabA11y', { count: day.stops.length, date, day: day.day_index })}
        accessibilityRole="tab"
        accessibilityState={{ selected: active }}
        onPress={() => onChange(day.day_index)}
        style={({ pressed }) => [d.tab, active && d.active, pressed && { opacity: 0.75 }]}
      >
        <Text style={[d.text, active && d.activeText]}>{date ? t('proposal.day.tab', { date, day: day.day_index }) : t('proposal.day.title', { day: day.day_index })}</Text>
      </Pressable>;
    })}
  </ScrollView>;
}

const d = StyleSheet.create({
  row: { gap: spacing.xs, paddingHorizontal: spacing.lg },
  tab: { minHeight: MIN_TOUCH, paddingHorizontal: spacing.md, borderRadius: radii.chip, backgroundColor: colors.surfaceTint, justifyContent: 'center' },
  active: { backgroundColor: colors.deepOcean },
  text: { fontFamily: fonts.bold, fontSize: 14, color: colors.deepOcean },
  activeText: { color: colors.white },
});
