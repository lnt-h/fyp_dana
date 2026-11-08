import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Icon } from '../../../components/ui';
import type { IsoDate } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { dayMonthYear, weekdayOf } from './vnTime';

/** One trip = 1–3 days (BR, FR-020). */
export const MAX_TRIP_DAYS = 3;

type WeekdayIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6;
type MonthKey = '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | '10' | '11' | '12';
type Month = { year: number; month: number };

const pad = (value: number) => String(value).padStart(2, '0');
const iso = (year: number, month: number, day: number): IsoDate => `${year}-${pad(month)}-${pad(day)}`;
const monthOf = (date: IsoDate): Month => ({ month: Number(date.slice(5, 7)), year: Number(date.slice(0, 4)) });
const daysIn = ({ year, month }: Month) => new Date(Date.UTC(year, month, 0)).getUTCDate();
const shift = ({ year, month }: Month, by: number): Month => {
  const index = year * 12 + (month - 1) + by;
  return { month: (index % 12) + 1, year: Math.floor(index / 12) };
};
const before = (a: Month, b: Month) => a.year * 12 + a.month < b.year * 12 + b.month;

/** Whole days from `a` to `b` (calendar dates, no time zone involved). */
export function daysBetween(a: IsoDate, b: IsoDate): number {
  return Math.round((Date.parse(`${b}T00:00:00Z`) - Date.parse(`${a}T00:00:00Z`)) / 86_400_000);
}

export function addDays(date: IsoDate, days: number): IsoDate {
  return new Date(Date.parse(`${date}T00:00:00Z`) + days * 86_400_000).toISOString().slice(0, 10);
}

type Props = {
  today: IsoDate;
  startDate: IsoDate | null;
  dayCount: 1 | 2 | 3 | null;
  onChange: (range: { startDate: IsoDate; dayCount: 1 | 2 | 3 }) => void;
  /** Tapped an end date more than 3 days after the start. */
  onTooLong: () => void;
};

/**
 * Month grid for the trip dates (SCR-022 step 1): tap the start date, then the end date; at most 3 days, past dates
 * disabled. A single tap is a 1-day trip. Weeks start on Monday (Viet Nam convention). 44 pt cells, one accessibility
 * label per day with its state.
 */
export function RangeCalendar({ today, startDate, dayCount, onChange, onTooLong }: Props) {
  const { t } = useTranslation();
  const [month, setMonth] = useState<Month>(() => monthOf(startDate ?? today));
  // After the first tap the next tap picks the end date; a third tap starts a new range.
  const [awaitingEnd, setAwaitingEnd] = useState(false);
  const first = monthOf(today);
  const end = startDate && dayCount ? addDays(startDate, dayCount - 1) : null;

  function tap(date: IsoDate) {
    if (awaitingEnd && startDate && date >= startDate) {
      const length = daysBetween(startDate, date) + 1;
      if (length > MAX_TRIP_DAYS) { onTooLong(); return; }
      onChange({ dayCount: length as 1 | 2 | 3, startDate });
      setAwaitingEnd(false);
      return;
    }
    onChange({ dayCount: 1, startDate: date });
    setAwaitingEnd(true);
  }

  const lead = (weekdayOf(iso(month.year, month.month, 1)) + 6) % 7;
  const cells: (IsoDate | null)[] = [
    ...Array.from({ length: lead }, () => null),
    ...Array.from({ length: daysIn(month) }, (_, index) => iso(month.year, month.month, index + 1)),
  ];
  while (cells.length % 7) cells.push(null);
  const title = t('planner.wizard.calendar.monthTitle', { month: t(`planner.wizard.calendar.month.${String(month.month) as MonthKey}`), year: month.year });
  const canGoBack = before(first, month);
  const weekdays: WeekdayIndex[] = [1, 2, 3, 4, 5, 6, 0];

  return <View style={c.wrap}>
    <View style={c.head}>
      <NavButton disabled={!canGoBack} icon="back" label={t('planner.wizard.calendar.previous')} onPress={() => setMonth(current => shift(current, -1))} />
      <Text accessibilityLiveRegion="polite" accessibilityRole="header" style={c.title}>{title}</Text>
      <NavButton icon="chevron-right" label={t('planner.wizard.calendar.next')} onPress={() => setMonth(current => shift(current, 1))} />
    </View>
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={c.row}>
      {weekdays.map(day => <Text key={day} style={c.weekday}>{t(`planner.weekday.${day}`)}</Text>)}
    </View>
    <View style={c.grid}>
      {cells.map((date, index) => {
        if (!date) return <View key={`empty-${index}`} style={c.cell} />;
        const past = date < today;
        const isStart = date === startDate;
        const isEnd = date === end;
        const inRange = !!startDate && !!end && date > startDate && date < end;
        const selected = isStart || isEnd;
        const state = past ? t('planner.wizard.calendar.unavailable')
          : isStart && isEnd ? t('planner.wizard.calendar.single')
            : isStart ? t('planner.wizard.calendar.start')
              : isEnd ? t('planner.wizard.calendar.end')
                : inRange ? t('planner.wizard.calendar.inRange') : null;
        const label = [`${t(`planner.weekday.${weekdayOf(date) as WeekdayIndex}`)}, ${dayMonthYear(date)}`, state].filter(Boolean).join(', ');
        const band = startDate && end && startDate !== end && (inRange || selected);
        return <View key={date} style={c.cell}>
          {band ? <View style={[c.band, isStart && c.bandStart, isEnd && c.bandEnd]} /> : null}
          <Pressable
            accessibilityLabel={label}
            accessibilityRole="button"
            accessibilityState={{ disabled: past, selected }}
            disabled={past}
            onPress={() => tap(date)}
            style={({ pressed }) => [c.day, selected && c.daySelected, pressed && !selected && { backgroundColor: colors.surfaceTint }]}
          >
            <Text style={[c.dayText, past && c.dayPast, selected && c.dayTextSelected, date === today && !selected && c.today]}>{Number(date.slice(8, 10))}</Text>
          </Pressable>
        </View>;
      })}
    </View>
  </View>;
}

function NavButton({ icon, label, onPress, disabled = false }: { icon: 'back' | 'chevron-right'; label: string; onPress: () => void; disabled?: boolean }) {
  return <Pressable
    accessibilityLabel={label}
    accessibilityRole="button"
    accessibilityState={{ disabled }}
    disabled={disabled}
    hitSlop={2}
    onPress={onPress}
    style={({ pressed }) => [c.nav, disabled && { opacity: 0.3 }, pressed && { opacity: 0.6 }]}
  >
    <Icon color={colors.deepOcean} name={icon} size={20} />
  </Pressable>;
}

const CELL = MIN_TOUCH;

const c = StyleSheet.create({
  wrap: { borderRadius: radii.card, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.hairline, padding: spacing.sm },
  head: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.xs },
  title: { flex: 1, textAlign: 'center', fontFamily: fonts.bold, fontSize: 16, color: colors.ink },
  nav: { width: MIN_TOUCH, height: MIN_TOUCH, borderRadius: MIN_TOUCH / 2, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surfaceTint },
  row: { flexDirection: 'row' },
  weekday: { width: `${100 / 7}%`, textAlign: 'center', fontFamily: fonts.bold, fontSize: 12, color: colors.textMuted, paddingVertical: spacing.xxs },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  cell: { width: `${100 / 7}%`, height: CELL + 4, alignItems: 'center', justifyContent: 'center' },
  band: { position: 'absolute', left: 0, right: 0, top: 2, bottom: 2, backgroundColor: colors.surfaceTint },
  bandStart: { left: '50%' },
  bandEnd: { right: '50%' },
  day: { width: CELL, height: CELL, borderRadius: CELL / 2, alignItems: 'center', justifyContent: 'center' },
  daySelected: { backgroundColor: colors.deepOcean },
  dayText: { fontFamily: fonts.semibold, fontSize: 15, color: colors.ink },
  dayTextSelected: { fontFamily: fonts.bold, color: colors.white },
  dayPast: { color: colors.disabledButton, textDecorationLine: 'line-through' },
  today: { color: colors.tealText, fontFamily: fonts.bold, textDecorationLine: 'underline' },
});
