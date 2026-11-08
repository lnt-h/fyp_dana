import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';
import { useTranslation } from 'react-i18next';
import { DayDot } from '../../../components/ui';
import { colors, dayPinColor } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import type { NumberedDay } from './model';

type WeekdayIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6;

type Props = {
  days: NumberedDay[];
  activeDay: number;
  /** Short date label of a day (`16/01` or `16 Jan`); empty when the trip has no start date. */
  dateOf: (dayIndex: number) => string;
  /** Weekday (0 = Sunday) of a day; null when the trip has no start date. */
  weekdayOf: (dayIndex: number) => number | null;
  onChange: (dayIndex: number) => void;
};

/**
 * Day chips in the day colours (day 1 teal, day 2 coral, day 3 indigo), the same colours as the timeline pins and the
 * map: `Day 1 · Sat 21 Nov`. The selected chip is filled in its day colour (white text ≥ 4.5:1); the others carry a dot.
 */
export function DateChips({ days, activeDay, dateOf, weekdayOf, onChange }: Props) {
  const { t } = useTranslation();
  return <ScrollView accessibilityRole="tablist" contentContainerStyle={d.row} horizontal showsHorizontalScrollIndicator={false}>
    {days.map(day => {
      const active = day.day_index === activeDay;
      const date = dateOf(day.day_index);
      const weekday = weekdayOf(day.day_index);
      const when = date && weekday != null ? t('proposal.day.chip', { date, weekday: t(`planner.weekday.${weekday as WeekdayIndex}`) }) : '';
      const label = when ? t('proposal.day.chipLabel', { day: day.day_index, when }) : t('proposal.day.title', { day: day.day_index });
      const color = dayPinColor(day.day_index - 1);
      return <Pressable
        key={day.day_index}
        accessibilityLabel={t('proposal.day.chipA11y', { count: day.stops.length, date: date || label, day: day.day_index })}
        accessibilityRole="tab"
        accessibilityState={{ selected: active }}
        onPress={() => onChange(day.day_index)}
        style={({ pressed }) => [d.chip, active && { backgroundColor: color, borderColor: color }, pressed && !active && d.pressed]}
      >
        {active ? null : <DayDot dayIndex={day.day_index - 1} />}
        <Text numberOfLines={1} style={[d.label, active && d.activeText]}>{label}</Text>
      </Pressable>;
    })}
  </ScrollView>;
}

/** Kept for existing call sites. */
export const DayTabs = DateChips;

const d = StyleSheet.create({
  row: { flexDirection: 'row', gap: spacing.xs, paddingHorizontal: spacing.lg },
  chip: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, minHeight: MIN_TOUCH, paddingHorizontal: spacing.md, borderRadius: radii.pill, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.hairline },
  pressed: { backgroundColor: colors.surface },
  label: { fontFamily: fonts.semibold, fontSize: 15, lineHeight: 20, color: colors.ink },
  activeText: { color: colors.white },
});
