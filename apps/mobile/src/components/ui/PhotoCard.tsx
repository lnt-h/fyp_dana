import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import type { Media } from '../../lib/api/types';
import { resolveImage } from '../../lib/images/imagekit';
import { colors } from '../../theme/colors';
import { radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { GlassBadge } from './GlassBadge';
import { Icon, type IconName } from './Icon';
import { PhotoFallback } from './PhotoFallback';

export type PhotoCardProps = {
  image: Pick<Media, 'url'> | null | undefined;
  title: string;
  subtitle?: string;
  /** Icon before the subtitle (default map-pin). */
  subtitleIcon?: IconName;
  /** Top-right glass badge text, e.g. "2 ngày". */
  badge?: string;
  badgeIcon?: IconName;
  /** Card width in dp (default fills parent); used to size the ImageKit request. */
  width?: number;
  /** Photo area height (default 200). */
  imageHeight?: number;
  /** Optional white footer row under the photo (e.g. "Xem ›"). */
  footer?: ReactNode;
  /** Small credit line inside the photo, bottom-right. */
  attribution?: string | null;
  onPress?: () => void;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  style?: StyleProp<ViewStyle>;
};

export function PhotoCard({
  image,
  title,
  subtitle,
  subtitleIcon = 'map-pin',
  badge,
  badgeIcon,
  width,
  imageHeight = 200,
  footer,
  attribution,
  onPress,
  accessibilityLabel,
  accessibilityHint,
  style,
}: PhotoCardProps) {
  const resolved = resolveImage(image, { height: imageHeight, width: width ?? 360 });
  const label = accessibilityLabel ?? [title, subtitle, badge].filter(Boolean).join(', ');

  return (
    <Pressable
      accessibilityHint={accessibilityHint}
      accessibilityLabel={label}
      accessibilityRole={onPress ? 'button' : undefined}
      disabled={!onPress}
      onPress={onPress}
      style={({ pressed }) => [styles.shadow, width ? { width } : null, pressed && styles.pressed, style]}
    >
      <View style={styles.clip}>
        <View style={{ height: imageHeight }}>
          {resolved ? (
            <Image contentFit="cover" placeholder={resolved.placeholder} placeholderContentFit="cover" source={resolved.source} style={StyleSheet.absoluteFill} transition={200} />
          ) : (
            <PhotoFallback tone="dark" icon="map-pin" />
          )}
          <LinearGradient colors={['rgba(7,21,30,0)', 'rgba(7,21,30,0.72)']} locations={[0.4, 1]} style={StyleSheet.absoluteFill} />
          {badge ? <GlassBadge icon={badgeIcon} label={badge} style={styles.badge} /> : null}
          <View style={styles.overlay}>
            <Text numberOfLines={2} style={styles.title}>{title}</Text>
            {subtitle ? (
              <View style={styles.subtitleRow}>
                <Icon color={colors.white} name={subtitleIcon} size={16} />
                <Text numberOfLines={1} style={styles.subtitle}>{subtitle}</Text>
              </View>
            ) : null}
            {resolved && attribution ? <Text numberOfLines={1} style={styles.attribution}>{attribution}</Text> : null}
          </View>
        </View>
        {footer ? <View style={styles.footer}>{footer}</View> : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  attribution: { color: 'rgba(255,255,255,0.82)', fontFamily: fonts.medium, fontSize: 11, marginTop: 4 },
  badge: { position: 'absolute', right: spacing.sm, top: spacing.sm },
  clip: { backgroundColor: colors.white, borderColor: colors.hairline, borderRadius: radii.photoCard, borderWidth: StyleSheet.hairlineWidth, overflow: 'hidden' },
  footer: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', minHeight: 56, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  overlay: { bottom: 0, left: 0, padding: spacing.md, position: 'absolute', right: 0 },
  pressed: { opacity: 0.94, transform: [{ scale: 0.99 }] },
  shadow: { backgroundColor: colors.white, borderRadius: radii.photoCard },
  subtitle: { color: colors.white, flexShrink: 1, fontFamily: fonts.medium, fontSize: 15 },
  subtitleRow: { alignItems: 'center', flexDirection: 'row', gap: 5, marginTop: 4 },
  title: { ...typography.headline, color: colors.white, fontSize: 22, lineHeight: 28 },
});
