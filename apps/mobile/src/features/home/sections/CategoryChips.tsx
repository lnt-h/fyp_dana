import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';

import { Chip, Skeleton, categoryIcon } from '../../../components/ui';
import type { Category } from '../../../lib/api/types';
import { radii, spacing } from '../../../theme/spacing';

/** Horizontal category filter: "Tất cả" + API categories. Shared with the map markers through `home.tsx`. */
export function CategoryChips({ categories, loading, selected, onChange, gutter }: {
  categories: Category[];
  loading: boolean;
  selected: string | null;
  onChange: (code: string | null) => void;
  gutter: number;
}) {
  const { t, i18n } = useTranslation();
  const isVi = i18n.resolvedLanguage === 'vi';
  const content = [styles.row, { paddingHorizontal: gutter }];

  if (loading) {
    return (
      <View accessibilityElementsHidden style={content}>
        {[72, 96, 84, 70].map((width, index) => <Skeleton height={44} key={index} radius={radii.chip} width={width} />)}
      </View>
    );
  }

  return (
    <ScrollView
      accessibilityLabel={t('homeSheet.categories.label')}
      contentContainerStyle={content}
      horizontal
      showsHorizontalScrollIndicator={false}
    >
      <Chip label={t('homeSheet.categories.all')} onPress={() => onChange(null)} selected={selected === null} style={styles.chip} />
      {[...categories].sort((a, b) => a.sort_order - b.sort_order).map(category => (
        <Chip
          icon={categoryIcon(category.code)}
          key={category.code}
          label={isVi ? category.name_vi : category.name_en}
          onPress={() => onChange(selected === category.code ? null : category.code)}
          selected={selected === category.code}
          style={styles.chip}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  chip: { minHeight: 44 },
  row: { flexDirection: 'row', gap: spacing.xs },
});
