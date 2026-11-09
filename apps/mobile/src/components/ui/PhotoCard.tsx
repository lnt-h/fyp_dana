import { LinearGradient } from 'expo-linear-gradient';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors } from '../../theme/colors';
import { radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { GlassBadge } from './GlassBadge';
import { Icon, type IconName } from './Icon';
import { Photo, usePhotoFailed, type PhotoImage } from './Photo';

export type PhotoCardProps = {
  image: PhotoImage | null | undefined;
  /** Icon on the fallback tile when there is no photo; default = the category icon, or the map pin. */
  fallbackIcon?: IconName;
  /** Category of the place shown: colours the fallback tile. */
  fallbackCategory?: string | null;
  /** Place name whose initial is drawn on the fallback tile (places only; omit for cities and trips). */
  fallbackName?: string | null;
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
  fallbackIcon,
  fallbackCategory,
  fallbackName,
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
  const [photoFailed, onPhotoError] = usePhotoFailed(image);
  const showCredit = !!image?.url && !photoFailed && !!attribution;
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
          <Photo
            categoryCode={fallbackCategory}
            height={imageHeight}
            icon={fallbackIcon}
            image={image}
            name={fallbackName}
            iconSize={40}
            onError={onPhotoError}
            width={width ?? 360}
          />
          <LinearGradient colors={['rgba(22,33,43,0)', 'rgba(22,33,43,0.72)']} locations={[0.4, 1]} style={StyleSheet.absoluteFill} />
          {badge ? <GlassBadge icon={badgeIcon} label={badge} style={styles.badge} /> : null}
          <View style={styles.overlay}>
            <Text numberOfLines={2} style={styles.title}>{title}</Text>
            {subtitle ? (
              <View style={styles.subtitleRow}>
                <Icon color={colors.white} name={subtitleIcon} size={16} />
                <Text numberOfLines={1} style={styles.subtitle}>{subtitle}</Text>
              </View>
            ) : null}
            {showCredit ? <Text numberOfLines={1} style={styles.attribution}>{attribution}</Text> : null}
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
  clip: { backgroundColor: colors.white, borderRadius: radii.photoCard, overflow: 'hidden' },
  footer: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', minHeight: 56, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  overlay: { bottom: 0, left: 0, padding: spacing.md, position: 'absolute', right: 0 },
  pressed: { opacity: 0.94, transform: [{ scale: 0.99 }] },
  shadow: { backgroundColor: colors.white, borderRadius: radii.photoCard },
  subtitle: { color: colors.white, flexShrink: 1, fontFamily: fonts.medium, fontSize: 15 },
  subtitleRow: { alignItems: 'center', flexDirection: 'row', gap: 5, marginTop: 4 },
  title: { ...typography.headline, color: colors.white, fontSize: 22, lineHeight: 28 },
});
