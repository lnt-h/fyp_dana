import { LinearGradient } from 'expo-linear-gradient';
import type { ReactNode } from 'react';
import { StyleSheet, Text, useWindowDimensions, View, type StyleProp, type ViewStyle } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';
import type { Media } from '../../lib/api/types';
import { colors } from '../../theme/colors';
import { spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { Icon, type IconName } from './Icon';
import { Photo, usePhotoFailed } from './Photo';

const SCRIM = ['rgba(22,33,43,0)', 'rgba(22,33,43,0.25)', 'rgba(22,33,43,0.72)'] as const;
const ARCH_HEIGHT = 36;

export type PhotoHeroProps = {
  image: Pick<Media, 'url'> | null | undefined;
  /** Icon on the fallback tile when there is no photo; default = the category icon, or lantern without a category. */
  fallbackIcon?: IconName;
  /** Category of the place shown: colours the fallback tile. */
  fallbackCategory?: string | null;
  /** Place name whose initial is drawn on the fallback tile (places only; omit for cities and trips). */
  fallbackName?: string | null;
  /** Total height including the status-bar inset (default 360). */
  height?: number;
  title?: string;
  /** Small line above the title (e.g. city name); shown with a map-pin. */
  kicker?: string;
  /** Photo credit, e.g. Media.attribution_text. Required by licence whenever a photo is shown. */
  attribution?: string | null;
  /** Curved canvas-coloured (white) bottom edge that the page content tucks under (default true). */
  arch?: boolean;
  /** Floating controls over the photo (e.g. CircleButtons), placed below the safe-area top inset. */
  topLeft?: ReactNode;
  topRight?: ReactNode;
  /** Extra content under the title inside the scrim (chips, badges). */
  children?: ReactNode;
  /** Alt text; omit for decorative heroes whose title already names the place. */
  accessibilityLabel?: string;
  style?: StyleProp<ViewStyle>;
};


export function PhotoHero({ image, fallbackIcon, fallbackCategory, fallbackName, height = 360, title, kicker, attribution, arch = true, topLeft, topRight, children, accessibilityLabel, style }: PhotoHeroProps) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const [photoFailed, onPhotoError] = usePhotoFailed(image);
  const showCredit = !!image?.url && !photoFailed && !!attribution;
  const bottomPad = (arch ? ARCH_HEIGHT : 0) + spacing.md;

  return (
    <View style={[styles.root, { height }, style]}>
      <Photo
        accessibilityLabel={accessibilityLabel}
        categoryCode={fallbackCategory}
        height={height}
        icon={fallbackIcon ?? (fallbackCategory ? undefined : 'lantern')}
        iconSize={56}
        image={image}
        name={fallbackName}
        onError={onPhotoError}
        transition={250}
        width={width}
      />
      <LinearGradient colors={SCRIM} locations={[0.35, 0.6, 1]} pointerEvents="none" style={StyleSheet.absoluteFill} />
      {/* Top fade so floating controls and the status bar stay legible on bright skies. */}
      <LinearGradient colors={['rgba(22,33,43,0.35)', 'rgba(22,33,43,0)']} pointerEvents="none" style={[styles.topFade, { height: insets.top + 80 }]} />

      {topLeft || topRight ? (
        <View pointerEvents="box-none" style={[styles.controls, { top: insets.top + spacing.xs }]}>
          <View>{topLeft}</View>
          <View>{topRight}</View>
        </View>
      ) : null}

      <View pointerEvents="box-none" style={[styles.body, { paddingBottom: bottomPad }]}>
        {kicker ? (
          <View style={styles.kickerRow}>
            <Icon color={colors.white} name="map-pin" size={18} />
            <Text numberOfLines={1} style={styles.kicker}>{kicker}</Text>
          </View>
        ) : null}
        {title ? <Text accessibilityRole="header" numberOfLines={3} style={styles.title}>{title}</Text> : null}
        {children}
        {showCredit ? <Text numberOfLines={1} style={styles.attribution}>{attribution}</Text> : null}
      </View>

      {arch ? (
        <Svg height={ARCH_HEIGHT} preserveAspectRatio="none" style={styles.arch} viewBox="0 0 100 10" width="100%">
          <Path d="M0 0Q50 20 100 0V10H0Z" fill={colors.canvas} />
        </Svg>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  arch: { bottom: -1, left: 0, position: 'absolute', right: 0 },
  attribution: { color: 'rgba(255,255,255,0.86)', fontFamily: fonts.medium, fontSize: 12, marginTop: spacing.xs, textAlign: 'right' },
  body: { bottom: 0, left: 0, paddingHorizontal: spacing.lg, position: 'absolute', right: 0 },
  controls: { flexDirection: 'row', justifyContent: 'space-between', left: spacing.md, position: 'absolute', right: spacing.md },
  kicker: { color: colors.white, flexShrink: 1, fontFamily: fonts.bold, fontSize: 17 },
  kickerRow: { alignItems: 'center', flexDirection: 'row', gap: 6, marginBottom: 4 },
  root: { backgroundColor: colors.surface, overflow: 'hidden', width: '100%' },
  title: { ...typography.display, color: colors.white },
  topFade: { left: 0, position: 'absolute', right: 0, top: 0 },
});
