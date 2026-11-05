import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Icon, SecondaryButton, Skeleton } from '../../../components/ui';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import type { CityCode } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';
import { useSelectedCity } from '../cityStore';

const TILE_HEIGHT = 96;

type Props = {
  visible: boolean;
  onClose: () => void;
};

/**
 * SCR-020 city choice: a modal sheet with the launch cities as photo tiles (order and names from API-008, never
 * hard-coded). Tapping a tile selects it and closes; the choice is stored on the device by the city store.
 */
export function CitySheet({ visible, onClose }: Props) {
  const { t, i18n } = useTranslation();
  const insets = useSafeAreaInsets();
  const reduceMotion = useReducedMotion();
  const { city, cities, loading, error, setCity, reload } = useSelectedCity();
  const vi = i18n.resolvedLanguage === 'vi';

  function choose(code: CityCode) {
    setCity(code);
    onClose();
  }

  return (
    <Modal animationType={reduceMotion ? 'none' : 'slide'} onRequestClose={onClose} transparent visible={visible}>
      <View style={styles.backdrop}>
        <Pressable accessibilityElementsHidden importantForAccessibility="no" onPress={onClose} style={StyleSheet.absoluteFill} />
        <View accessibilityViewIsModal style={[styles.sheet, { paddingBottom: insets.bottom + 16 }]}>
          <View style={styles.handle} />
          <View style={styles.headerRow}>
            <Text accessibilityRole="header" style={styles.title}>{t('home.city.title')}</Text>
            <Pressable accessibilityLabel={t('home.city.close')} accessibilityRole="button" hitSlop={6} onPress={onClose} style={styles.close}>
              <Text style={styles.closeGlyph}>×</Text>
            </Pressable>
          </View>
          <Text style={styles.subtitle}>{t('home.city.subtitle')}</Text>

          <ScrollView accessibilityRole="radiogroup" contentContainerStyle={styles.list} showsVerticalScrollIndicator={false}>
            {loading && cities.length === 0
              ? Array.from({ length: 5 }, (_, i) => <Skeleton height={TILE_HEIGHT} key={i} radius={20} />)
              : null}
            {error && cities.length === 0 ? (
              <View accessibilityLiveRegion="polite" style={styles.error}>
                <Icon color={colors.ink} name="warning" size={20} />
                <Text style={styles.errorText}>{t('home.city.loadError')}</Text>
                <SecondaryButton label={t('home.city.retry')} onPress={reload} />
              </View>
            ) : null}
            {cities.map(item => {
              const selected = item.code === city?.code;
              const primary = vi ? item.name_vi : item.name_en;
              const secondary = vi ? item.name_en : item.name_vi;
              const image = resolveImage(CITY_IMAGES[item.code], { height: TILE_HEIGHT, width: 360 });
              return (
                <Pressable
                  accessibilityLabel={primary === secondary ? primary : `${primary} (${secondary})`}
                  accessibilityRole="radio"
                  accessibilityState={{ checked: selected }}
                  key={item.id}
                  onPress={() => choose(item.code)}
                  style={({ pressed }) => [styles.tile, selected && styles.tileSelected, pressed && styles.pressed]}
                >
                  {image ? (
                    <Image contentFit="cover" placeholder={image.placeholder} source={image.source} style={StyleSheet.absoluteFill} />
                  ) : null}
                  <LinearGradient colors={['rgba(7,21,30,0.72)', 'rgba(7,21,30,0.15)']} end={{ x: 1, y: 0.5 }} start={{ x: 0, y: 0.5 }} style={StyleSheet.absoluteFill} />
                  <View style={styles.tileText}>
                    <Text numberOfLines={1} style={styles.tileName}>{primary}</Text>
                    {primary !== secondary ? <Text numberOfLines={1} style={styles.tileSecondary}>{secondary}</Text> : null}
                  </View>
                  {selected ? (
                    <View style={styles.check}>
                      <Icon color={colors.white} name="check" size={18} strokeWidth={2.4} />
                    </View>
                  ) : null}
                </Pressable>
              );
            })}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { backgroundColor: 'rgba(7,21,30,0.35)', flex: 1, justifyContent: 'flex-end' },
  check: {
    alignItems: 'center',
    backgroundColor: colors.audioTeal,
    borderColor: colors.white,
    borderRadius: 16,
    borderWidth: 2,
    height: 32,
    justifyContent: 'center',
    marginRight: 16,
    width: 32,
  },
  close: { alignItems: 'center', height: 44, justifyContent: 'center', marginRight: -10, width: 44 },
  closeGlyph: { color: colors.ink, fontFamily: fonts.medium, fontSize: 30, lineHeight: 32 },
  error: { alignItems: 'center', gap: 10, paddingVertical: 16 },
  errorText: { color: colors.ink, fontFamily: fonts.medium, fontSize: 15, lineHeight: 22, textAlign: 'center' },
  handle: { alignSelf: 'center', backgroundColor: '#C9C9C9', borderRadius: 2, height: 4, marginBottom: 16, width: 68 },
  headerRow: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  list: { gap: 10, paddingTop: 16 },
  pressed: { opacity: 0.88 },
  sheet: {
    alignSelf: 'center',
    backgroundColor: colors.white,
    borderTopLeftRadius: 40,
    borderTopRightRadius: 40,
    maxHeight: '88%',
    maxWidth: 520,
    paddingHorizontal: 20,
    paddingTop: 10,
    width: '100%',
  },
  subtitle: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 15, lineHeight: 22, marginTop: 2 },
  tile: {
    alignItems: 'center',
    backgroundColor: colors.deepOcean,
    borderColor: 'transparent',
    borderRadius: 20,
    borderWidth: 3,
    flexDirection: 'row',
    height: TILE_HEIGHT,
    overflow: 'hidden',
  },
  tileName: { color: colors.white, fontFamily: fonts.bold, fontSize: 20, lineHeight: 26 },
  tileSecondary: { color: colors.white, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20 },
  tileSelected: { borderColor: colors.audioTeal },
  tileText: { flex: 1, paddingHorizontal: 18 },
  title: { color: colors.ink, fontFamily: fonts.bold, fontSize: 20, lineHeight: 26 },
});
