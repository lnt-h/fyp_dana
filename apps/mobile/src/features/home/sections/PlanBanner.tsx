import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, PhotoFallback } from '../../../components/ui';
import type { CityCode } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

const HEIGHT = 208;

/**
 * SCR-008 Plan entry: the city photo under a legibility wash, title, one-line promise and a white "Start planning"
 * pill (primary text 4.82:1). The whole card is one button; offline it is disabled with a hint.
 */
export function PlanBanner({ cityCode, cityName, offline, onStart }: { cityCode: CityCode | null; cityName: string; offline: boolean; onStart: () => void }) {
  const { t } = useTranslation();
  const media = cityCode ? CITY_IMAGES[cityCode] : null;
  const photo = resolveImage(media, { height: HEIGHT, width: 400 });
  const title = t('homeSheet.plan.title', { city: cityName });
  return (
    <View>
      <Pressable
        accessibilityHint={offline ? t('homeSheet.plan.offlineHint') : t('homeSheet.plan.a11yHint')}
        accessibilityLabel={`${title}. ${t('homeSheet.plan.subtitle')}. ${t('homeSheet.plan.action')}`}
        accessibilityRole="button"
        accessibilityState={{ disabled: offline }}
        disabled={offline}
        onPress={onStart}
        style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      >
        <View style={styles.clip}>
          {photo ? (
            <Image contentFit="cover" placeholder={photo.placeholder} placeholderContentFit="cover" source={photo.source} style={StyleSheet.absoluteFill} transition={200} />
          ) : (
            <PhotoFallback tone="dark" icon="map-pin" />
          )}
          {/* Teal wash, strongest behind the text, keeps white text ≥4.5:1 on any photo. */}
          <LinearGradient
            colors={['rgba(7,78,75,0.94)', 'rgba(11,122,117,0.78)', 'rgba(11,122,117,0.12)']}
            end={{ x: 1, y: 0.2 }}
            locations={[0, 0.5, 1]}
            start={{ x: 0, y: 1 }}
            style={StyleSheet.absoluteFill}
          />
          <View style={styles.body}>
            <View style={styles.badge}>
              <Icon color={colors.white} name="calendar" size={16} />
              <Text numberOfLines={1} style={styles.badgeText}>{t('homeSheet.plan.kicker')}</Text>
            </View>
            <View>
              <Text numberOfLines={2} style={styles.title}>{title}</Text>
              <Text numberOfLines={2} style={styles.subtitle}>{t('homeSheet.plan.subtitle')}</Text>
              <View style={styles.row}>
                <View style={[styles.pill, offline && styles.pillDisabled]}>
                  <Text style={styles.pillText}>{t('homeSheet.plan.action')}</Text>
                  <Icon color={colors.primary} name="chevron-right" size={18} />
                </View>
                {media && photo ? <Text numberOfLines={1} style={styles.credit}>{media.attribution_text}</Text> : null}
              </View>
            </View>
          </View>
        </View>
      </Pressable>
      {offline ? <Text style={styles.hint}>{t('homeSheet.plan.offlineHint')}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { alignItems: 'center', alignSelf: 'flex-start', backgroundColor: 'rgba(255,255,255,0.18)', borderRadius: radii.pill, flexDirection: 'row', gap: 6, paddingHorizontal: 10, paddingVertical: 4 },
  badgeText: { color: colors.white, fontFamily: fonts.semibold, fontSize: 13, lineHeight: 18 },
  body: { flex: 1, justifyContent: 'space-between', padding: spacing.lg },
  card: { backgroundColor: colors.primary, borderRadius: radii.card },
  clip: { borderRadius: radii.card, height: HEIGHT, overflow: 'hidden' },
  credit: { color: 'rgba(255,255,255,0.85)', flexShrink: 1, fontFamily: fonts.medium, fontSize: 10, marginLeft: spacing.sm, textAlign: 'right' },
  hint: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, marginTop: spacing.xs },
  pill: { alignItems: 'center', backgroundColor: colors.white, borderRadius: radii.pill, flexDirection: 'row', gap: 4, minHeight: MIN_TOUCH, paddingLeft: 18, paddingRight: 12 },
  pillDisabled: { opacity: 0.6 },
  pillText: { color: colors.primary, fontFamily: fonts.bold, fontSize: 16 },
  pressed: { opacity: 0.94 },
  row: { alignItems: 'flex-end', flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.md },
  subtitle: { color: 'rgba(255,255,255,0.94)', fontFamily: fonts.regular, fontSize: 15, lineHeight: 20, marginTop: 4 },
  title: { color: colors.white, fontFamily: fonts.bold, fontSize: 24, letterSpacing: -0.4, lineHeight: 30 },
});
