import { Image } from 'expo-image';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, categoryIcon } from '../../../components/ui';
import type { Place } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { fonts } from '../../../theme/typography';

type Props = {
  place: Place;
  onOpen: (placeId: string) => void;
};

/** Small floating card for the tapped marker; tap opens the place card (SCR-033). */
export function PlacePreviewCard({ place, onOpen }: Props) {
  const { t } = useTranslation();
  const image = resolveImage(place.thumbnail, { height: 56, width: 56 });
  const minutes = place.visit_minutes_suggested;

  return (
    <Pressable
      accessibilityLabel={t('home.map.openPlace', { name: place.name })}
      accessibilityRole="button"
      onPress={() => onOpen(place.id)}
      style={({ pressed }) => [styles.card, elevation.md, pressed && styles.pressed]}
    >
      <View style={styles.photo}>
        {image ? (
          <Image contentFit="cover" placeholder={image.placeholder} source={image.source} style={StyleSheet.absoluteFill} />
        ) : (
          <Icon color={colors.tealText} name={categoryIcon(place.category_code)} size={24} />
        )}
      </View>
      <View style={styles.body}>
        <Text numberOfLines={1} style={styles.name}>{place.name}</Text>
        <View style={styles.meta}>
          <Icon color={colors.tealText} name={categoryIcon(place.category_code)} size={16} />
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
    borderRadius: 20,
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
    backgroundColor: colors.skyWash,
    borderRadius: 14,
    height: 56,
    justifyContent: 'center',
    overflow: 'hidden',
    width: 56,
  },
  pressed: { opacity: 0.9 },
});
