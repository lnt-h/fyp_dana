import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, Photo, categoryIcon } from '../../../components/ui';
import type { Place } from '../../../lib/api/types';
import { categoryColor, colors } from '../../../theme/colors';
import { radii } from '../../../theme/spacing';
import { elevation } from '../../../theme/elevation';
import { fonts } from '../../../theme/typography';

type Props = {
  place: Place;
  onOpen: (placeId: string) => void;
};

/** Small floating card for the tapped marker; tap opens the place card (SCR-033). */
export function PlacePreviewCard({ place, onOpen }: Props) {
  const { t } = useTranslation();
  const minutes = place.visit_minutes_suggested;

  return (
    <Pressable
      accessibilityLabel={t('home.map.openPlace', { name: place.name })}
      accessibilityRole="button"
      onPress={() => onOpen(place.id)}
      style={({ pressed }) => [styles.card, elevation.md, pressed && styles.pressed]}
    >
      <View style={styles.photo}>
        <Photo categoryCode={place.category_code} height={56} iconSize={24} image={place.thumbnail} name={place.name} variant="thumb" width={56} />
      </View>
      <View style={styles.body}>
        <Text numberOfLines={1} style={styles.name}>{place.name}</Text>
        <View style={styles.meta}>
          <Icon color={categoryColor(place.category_code).fg} name={categoryIcon(place.category_code)} size={16} />
          {minutes ? (
            <>
              <Icon color={colors.textMuted} name="clock" size={16} />
              <Text style={styles.metaText}>{t('home.map.visitMinutes', { count: minutes })}</Text>
            </>
          ) : null}
        </View>
      </View>
      <Icon color={colors.ink} name="chevron-right" size={20} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  body: { flex: 1, gap: 4 },
  card: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderRadius: radii.card,
    flexDirection: 'row',
    gap: 12,
    minHeight: 72,
    padding: 8,
    paddingRight: 14,
  },
  meta: { alignItems: 'center', flexDirection: 'row', gap: 6 },
  metaText: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18 },
  name: { color: colors.ink, fontFamily: fonts.bold, fontSize: 16, lineHeight: 22 },
  photo: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: 14,
    height: 56,
    justifyContent: 'center',
    overflow: 'hidden',
    width: 56,
  },
  pressed: { opacity: 0.9 },
});
