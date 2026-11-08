import { useTranslation } from 'react-i18next';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';

import { Chip, Icon, categoryIcon } from '../../../components/ui';
import type { Category } from '../../../lib/api/types';
import { categoryColor, colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { MAX_QUERY } from '../useExploreData';

export type ResultView = 'grid' | 'list';

/** Large title, city pill (Đà Nẵng only since 2026-11-08: a label, not a picker) and the subtitle. */
export function ExploreTitle({ cityName }: { cityName: string | null }) {
  const { t } = useTranslation();
  return (
    <View style={styles.titleBlock}>
      <View style={styles.titleRow}>
        <Text accessibilityRole="header" style={styles.title}>{t('explore.title')}</Text>
        <View
          accessibilityLabel={cityName ? t('explore.city.label', { city: cityName }) : t('explore.city.loading')}
          accessibilityRole="text"
          style={styles.cityPill}
        >
          <Icon color={colors.primary} name="map-pin" size={18} />
          <Text numberOfLines={1} style={styles.cityText}>{cityName ?? '…'}</Text>
        </View>
      </View>
      {cityName ? <Text style={styles.subtitle}>{t('explore.subtitle', { city: cityName })}</Text> : null}
    </View>
  );
}

type SearchProps = {
  value: string;
  onChange: (q: string) => void;
  cityName: string;
  /** Guest: the field is a button that opens SCR-040 (search is a private feature, S-3). */
  guest: boolean;
  onGuestPress: () => void;
  offline: boolean;
  view: ResultView;
  onChangeView: (view: ResultView) => void;
};

/** Search field (clear 44 pt) plus the grid/list switch. */
export function ExploreSearchBar({ value, onChange, cityName, guest, onGuestPress, offline, view, onChangeView }: SearchProps) {
  const { t } = useTranslation();
  const placeholder = offline ? t('explore.search.offline') : t('explore.search.placeholder', { city: cityName });
  return (
    <View style={styles.searchRow}>
      {guest ? (
        <Pressable
          accessibilityHint={t('explore.search.guest')}
          accessibilityLabel={t('explore.search.label', { city: cityName })}
          accessibilityRole="search"
          accessibilityState={{ disabled: offline }}
          disabled={offline}
          onPress={onGuestPress}
          style={({ pressed }) => [styles.field, offline && styles.fieldOff, pressed && styles.pressed]}
        >
          <Icon color={colors.textMuted} name="search" size={20} />
          <Text numberOfLines={1} style={styles.fakeInput}>{placeholder}</Text>
        </Pressable>
      ) : (
        <View style={[styles.field, offline && styles.fieldOff]}>
          <Icon color={colors.textMuted} name="search" size={20} />
          <TextInput
            accessibilityLabel={t('explore.search.label', { city: cityName })}
            autoCapitalize="none"
            autoCorrect={false}
            clearButtonMode="never"
            editable={!offline}
            maxLength={MAX_QUERY}
            onChangeText={onChange}
            placeholder={placeholder}
            placeholderTextColor={colors.textMuted}
            returnKeyType="search"
            style={styles.input}
            value={value}
          />
          {value ? (
            <Pressable accessibilityLabel={t('explore.search.clear')} accessibilityRole="button" onPress={() => onChange('')} style={styles.clear}>
              <View style={styles.clearDot}><Text style={styles.clearGlyph}>×</Text></View>
            </Pressable>
          ) : null}
        </View>
      )}
      <ViewToggle onChange={onChangeView} value={view} />
    </View>
  );
}

function ViewToggle({ value, onChange }: { value: ResultView; onChange: (view: ResultView) => void }) {
  const { t } = useTranslation();
  return (
    <View accessibilityLabel={t('explore.view.label')} accessibilityRole="radiogroup" style={styles.toggle}>
      {(['grid', 'list'] as const).map(option => {
        const selected = option === value;
        const color = selected ? colors.ink : colors.textMuted;
        return (
          <Pressable
            accessibilityLabel={t(`explore.view.${option}`)}
            accessibilityRole="radio"
            accessibilityState={{ checked: selected }}
            key={option}
            onPress={() => onChange(option)}
            style={[styles.toggleItem, selected && styles.toggleOn]}
          >
            <Svg height={20} viewBox="0 0 24 24" width={20}>
              {option === 'grid' ? (
                <>
                  <Rect fill="none" height={7} rx={2} stroke={color} strokeWidth={1.8} width={7} x={3.5} y={3.5} />
                  <Rect fill="none" height={7} rx={2} stroke={color} strokeWidth={1.8} width={7} x={13.5} y={3.5} />
                  <Rect fill="none" height={7} rx={2} stroke={color} strokeWidth={1.8} width={7} x={3.5} y={13.5} />
                  <Rect fill="none" height={7} rx={2} stroke={color} strokeWidth={1.8} width={7} x={13.5} y={13.5} />
                </>
              ) : (
                <Path d="M9 6h11.5M9 12h11.5M9 18h11.5M4 6h.01M4 12h.01M4 18h.01" fill="none" stroke={color} strokeLinecap="round" strokeWidth={2} />
              )}
            </Svg>
          </Pressable>
        );
      })}
    </View>
  );
}

/** Category chips (API-009, only categories with places) in their category colours, plus "All"; single choice. */
export function CategoryRow({ categories, value, onChange, gutter }: {
  categories: Category[];
  value: string | null;
  onChange: (code: string | null) => void;
  gutter: number;
}) {
  const { t, i18n } = useTranslation();
  const vi = i18n.resolvedLanguage === 'vi';
  if (categories.length === 0) return null;
  return (
    <ScrollView
      accessibilityLabel={t('explore.categories.label')}
      contentContainerStyle={[styles.chips, { paddingHorizontal: gutter }]}
      horizontal
      keyboardShouldPersistTaps="handled"
      showsHorizontalScrollIndicator={false}
    >
      <Chip label={t('explore.categories.all')} onPress={() => onChange(null)} selected={value === null} />
      {categories.map(category => (
        <Chip
          icon={categoryIcon(category.code)}
          key={category.code}
          label={vi ? category.name_vi : category.name_en}
          onPress={() => onChange(value === category.code ? null : category.code)}
          selected={value === category.code}
          tone={categoryColor(category.code)}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  chips: { gap: spacing.xs, paddingVertical: 2 },
  cityPill: {
    alignItems: 'center',
    backgroundColor: colors.primarySoft,
    borderRadius: radii.pill,
    flexDirection: 'row',
    flexShrink: 1,
    gap: 6,
    minHeight: MIN_TOUCH,
    paddingHorizontal: 14,
  },
  cityText: { color: colors.ink, flexShrink: 1, fontFamily: fonts.bold, fontSize: 15 },
  clear: { alignItems: 'center', height: MIN_TOUCH, justifyContent: 'center', width: MIN_TOUCH },
  clearDot: { alignItems: 'center', backgroundColor: colors.textMuted, borderRadius: 10, height: 20, justifyContent: 'center', width: 20 },
  clearGlyph: { color: colors.white, fontFamily: fonts.bold, fontSize: 15, lineHeight: 18 },
  fakeInput: { color: colors.textMuted, flex: 1, fontFamily: fonts.medium, fontSize: 16, marginLeft: 10 },
  field: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radii.pill,
    flex: 1,
    flexDirection: 'row',
    minHeight: 52,
    paddingLeft: 14,
  },
  fieldOff: { opacity: 0.6 },
  input: { color: colors.ink, flex: 1, fontFamily: fonts.medium, fontSize: 16, marginLeft: 10, minHeight: 48, paddingVertical: 0 },
  pressed: { opacity: 0.8 },
  searchRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.xs },
  subtitle: { ...typography.body, color: colors.textSecondary, marginTop: 2 },
  title: { ...typography.display, color: colors.ink, flexShrink: 0 },
  titleBlock: { gap: 2 },
  titleRow: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, justifyContent: 'space-between' },
  toggle: { backgroundColor: colors.surface, borderRadius: radii.inset, flexDirection: 'row', gap: 2, padding: 4 },
  toggleItem: { alignItems: 'center', borderRadius: 12, height: MIN_TOUCH, justifyContent: 'center', width: MIN_TOUCH },
  toggleOn: { backgroundColor: colors.white },
});
