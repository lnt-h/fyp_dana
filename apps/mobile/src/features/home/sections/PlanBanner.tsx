import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '../../../components/ui';
import type { CityCode } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

const HEIGHT = 196;

/**
 * SCR-008 Plan entry (replaces the old PlanCard): city photo with a dark scrim, kicker, title, reviewed-places line and
 * a white "Bắt đầu →" pill. The whole banner is one button; offline it is disabled with a hint.
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
        style={({ pressed }) => [styles.card, elevation.md, pressed && styles.pressed]}
      >
        <View style={styles.clip}>
          {photo ? (
            <Image contentFit="cover" placeholder={photo.placeholder} placeholderContentFit="cover" source={photo.source} style={StyleSheet.absoluteFill} transition={200} />
          ) : (
            <LinearGradient colors={[colors.deepOcean, colors.tealDark]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={StyleSheet.absoluteFill} />
          )}
          {/* Strong scrim on the left/bottom keeps white text ≥4.5:1 on any photo. */}
          <LinearGradient colors={['rgba(7,21,30,0.88)', 'rgba(7,21,30,0.72)', 'rgba(7,21,30,0.35)']} end={{ x: 1, y: 0.5 }} locations={[0, 0.55, 1]} start={{ x: 0, y: 0.5 }} style={StyleSheet.absoluteFill} />
          <View style={styles.body}>
            <View style={styles.kicker}>
              <Icon color={colors.sun} name="sparkle" size={16} />
              <Text numberOfLines={1} style={styles.kickerText}>{t('homeSheet.plan.kicker')}</Text>
            </View>
            <Text numberOfLines={2} style={styles.title}>{title}</Text>
            <Text numberOfLines={1} style={styles.subtitle}>{t('homeSheet.plan.subtitle')}</Text>
            <View style={styles.row}>
              <View style={[styles.pill, offline && styles.pillDisabled]}>
                <Text style={styles.pillText}>{t('homeSheet.plan.action')}</Text>
                <Icon color={colors.ink} name="chevron-right" size={18} />
              </View>
              {media && photo ? <Text numberOfLines={1} style={styles.credit}>{media.attribution_text}</Text> : null}
            </View>
          </View>
        </View>
      </Pressable>
      {offline ? <Text style={styles.hint}>{t('homeSheet.plan.offlineHint')}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  body: { flex: 1, justifyContent: 'flex-end', padding: spacing.lg },
  card: { backgroundColor: colors.deepOcean, borderRadius: radii.card },
  clip: { borderRadius: radii.card, height: HEIGHT, overflow: 'hidden' },
  credit: { color: 'rgba(255,255,255,0.85)', flexShrink: 1, fontFamily: fonts.medium, fontSize: 10, marginLeft: spacing.sm, textAlign: 'right' },
  hint: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, marginTop: spacing.xs },
  kicker: { alignItems: 'center', flexDirection: 'row', gap: 6 },
  kickerText: { color: colors.white, fontFamily: fonts.bold, fontSize: 13, letterSpacing: 0.2 },
  pill: { alignItems: 'center', backgroundColor: colors.white, borderRadius: radii.pill, flexDirection: 'row', gap: 4, minHeight: MIN_TOUCH, paddingLeft: 18, paddingRight: 12 },
  pillDisabled: { opacity: 0.6 },
  pillText: { color: colors.ink, fontFamily: fonts.bold, fontSize: 15 },
  pressed: { opacity: 0.94 },
  row: { alignItems: 'flex-end', flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.sm },
  subtitle: { color: 'rgba(255,255,255,0.92)', fontFamily: fonts.medium, fontSize: 14, lineHeight: 19, marginTop: 2 },
  title: { color: colors.white, fontFamily: fonts.bold, fontSize: 22, letterSpacing: -0.3, lineHeight: 27, marginTop: 6 },
});
