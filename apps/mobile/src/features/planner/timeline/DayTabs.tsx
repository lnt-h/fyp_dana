import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { colors } from '../../../theme/colors';
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
 * Date chips (Vietdetour pattern): one 44 pt pill per day, `T6 16/01` / `Fri 16 Jan`, the selected one filled in
 * deepOcean with white text. Without a start date the chip falls back to `Day n`. Same active day as the map.
 */
export function DateChips({ days, activeDay, dateOf, weekdayOf, onChange }: Props) {
  const { t } = useTranslation();
  return <ScrollView
    accessibilityRole="tablist"
    contentContainerStyle={d.row}
    horizontal
    showsHorizontalScrollIndicator={false}
  >
    {days.map(day => {
      const active = day.day_index === activeDay;
      const date = dateOf(day.day_index);
      const weekday = weekdayOf(day.day_index);
      const label = date && weekday != null
        ? t('proposal.day.chip', { date, weekday: t(`planner.weekday.${weekday as WeekdayIndex}`) })
        : t('proposal.day.title', { day: day.day_index });
      return <Pressable
        key={day.day_index}
        accessibilityLabel={t('proposal.day.chipA11y', { count: day.stops.length, date: date || label, day: day.day_index })}
        accessibilityRole="tab"
        accessibilityState={{ selected: active }}
        onPress={() => onChange(day.day_index)}
        style={({ pressed }) => [d.chip, active && d.active, pressed && !active && { opacity: 0.7 }]}
      >
        <Text style={[d.dayNo, active && d.activeSub]}>{day.day_index}</Text>
        <View style={[d.sep, active && d.activeSep]} />
        <Text numberOfLines={1} style={[d.label, active && d.activeText]}>{label}</Text>
      </Pressable>;
    })}
  </ScrollView>;
}

/** Kept for existing call sites. */
export const DayTabs = DateChips;

const d = StyleSheet.create({
  row: { flexDirection: 'row', gap: spacing.xs, paddingHorizontal: spacing.lg },
  chip: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, minHeight: MIN_TOUCH, paddingHorizontal: spacing.md, borderRadius: radii.chip, backgroundColor: colors.white, borderWidth: 1.5, borderColor: colors.hairline },
  active: { backgroundColor: colors.deepOcean, borderColor: colors.deepOcean },
  dayNo: { fontFamily: fonts.bold, fontSize: 13, color: colors.textMuted },
  sep: { width: 1, height: 14, backgroundColor: colors.hairline },
  activeSep: { backgroundColor: 'rgba(255,255,255,0.4)' },
  label: { fontFamily: fonts.bold, fontSize: 15, lineHeight: 20, color: colors.deepOcean },
  activeText: { color: colors.white },
  activeSub: { color: colors.white },
});
