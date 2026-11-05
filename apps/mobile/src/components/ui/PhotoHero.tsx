import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import type { ReactNode } from 'react';
import { StyleSheet, Text, useWindowDimensions, View, type StyleProp, type ViewStyle } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Path } from 'react-native-svg';
import type { Media } from '../../lib/api/types';
import { resolveImage } from '../../lib/images/imagekit';
import { colors } from '../../theme/colors';
import { spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { Icon } from './Icon';

const SCRIM = ['rgba(7,21,30,0)', 'rgba(7,21,30,0.25)', 'rgba(7,21,30,0.72)'] as const;
const ARCH_HEIGHT = 36;

export type PhotoHeroProps = {
  image: Pick<Media, 'url'> | null | undefined;
  /** Total height including the status-bar inset (default 360). */
  height?: number;
  title?: string;
  /** Small line above the title (e.g. city name); shown with a map-pin. */
  kicker?: string;
  /** Photo credit, e.g. Media.attribution_text. Required by licence whenever a photo is shown. */
  attribution?: string | null;
  /** Curved white bottom edge that the page content tucks under (default true). */
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

/** Fallback when no photo: deepOcean→tealDark with a faint lantern-ring pattern. */
function FallbackArt() {
  return (
    <>
      <LinearGradient colors={[colors.deepOcean, colors.tealDark]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={StyleSheet.absoluteFill} />
      <Svg height="100%" preserveAspectRatio="xMidYMid slice" style={StyleSheet.absoluteFill} viewBox="0 0 200 200" width="100%">
        {[0, 1, 2, 3].map(i => (
          <Circle cx={170} cy={30} fill="none" key={`a${i}`} r={22 + i * 22} stroke={colors.white} strokeOpacity={0.07} strokeWidth={1.2} />
        ))}
        {[0, 1, 2].map(i => (
          <Circle cx={20} cy={180} fill="none" key={`b${i}`} r={18 + i * 20} stroke={colors.white} strokeOpacity={0.06} strokeWidth={1.2} />
        ))}
      </Svg>
    </>
  );
}

export function PhotoHero({ image, height = 360, title, kicker, attribution, arch = true, topLeft, topRight, children, accessibilityLabel, style }: PhotoHeroProps) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const resolved = resolveImage(image, { height, width });
  const bottomPad = (arch ? ARCH_HEIGHT : 0) + spacing.md;

  return (
    <View style={[styles.root, { height }, style]}>
      {resolved ? (
        <Image
          accessibilityLabel={accessibilityLabel}
          accessible={!!accessibilityLabel}
          contentFit="cover"
          placeholder={resolved.placeholder}
          placeholderContentFit="cover"
          source={resolved.source}
          style={StyleSheet.absoluteFill}
          transition={250}
        />
      ) : (
        <FallbackArt />
      )}
      <LinearGradient colors={SCRIM} locations={[0.35, 0.6, 1]} pointerEvents="none" style={StyleSheet.absoluteFill} />
      {/* Top fade so floating controls and the status bar stay legible on bright skies. */}
      <LinearGradient colors={['rgba(7,21,30,0.35)', 'rgba(7,21,30,0)']} pointerEvents="none" style={[styles.topFade, { height: insets.top + 80 }]} />

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
        {resolved && attribution ? <Text numberOfLines={1} style={styles.attribution}>{attribution}</Text> : null}
      </View>

      {arch ? (
        <Svg height={ARCH_HEIGHT} preserveAspectRatio="none" style={styles.arch} viewBox="0 0 100 10" width="100%">
          <Path d="M0 0Q50 20 100 0V10H0Z" fill={colors.white} />
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
  root: { backgroundColor: colors.deepOcean, overflow: 'hidden', width: '100%' },
  title: { ...typography.display, color: colors.white },
  topFade: { left: 0, position: 'absolute', right: 0, top: 0 },
});
