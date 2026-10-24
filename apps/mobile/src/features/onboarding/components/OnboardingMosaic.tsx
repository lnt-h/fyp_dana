import { LinearGradient } from 'expo-linear-gradient';
import { Image, ImageSourcePropType, StyleSheet, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { colors } from '../../../theme/colors';

const images = {
  beach: require('../../../../assets/onboarding/beach.png'),
  chamSculpture: require('../../../../assets/onboarding/cham-sculpture.png'),
  cityBridge: require('../../../../assets/onboarding/city-bridge.png'),
  cyclo: require('../../../../assets/onboarding/cyclo.png'),
  dragonBridge: require('../../../../assets/onboarding/dragon-bridge.png'),
  marbleMountains: require('../../../../assets/onboarding/marble-mountains.png'),
} satisfies Record<string, ImageSourcePropType>;

type Props = {
  height: number;
  width: number;
};

type TileProps = {
  height: number;
  radius: number;
  source: ImageSourcePropType;
  top: number;
  width: number;
};

function Tile({ height, radius, source, top, width }: TileProps) {
  return (
    <View style={[styles.tile, { borderRadius: radius, height, top, width }]}>
      <Image resizeMode="cover" source={source} style={styles.image} />
    </View>
  );
}

function AudioMark({ size }: { size: number }) {
  return (
    <LinearGradient
      colors={[colors.sun, colors.teal]}
      end={{ x: 1, y: 1 }}
      start={{ x: 0, y: 0 }}
      style={[styles.audioRing, { borderRadius: size / 2, height: size, width: size }]}
    >
      <View style={[styles.audioCore, { borderRadius: (size - 8) / 2 }]}>
        <Svg height={size * 0.46} viewBox="0 0 58 58" width={size * 0.46}>
          <Path
            d="M14 31V27M21.5 38V20M29 43V15M36.5 37V21M44 33V25"
            fill="none"
            stroke={colors.white}
            strokeLinecap="round"
            strokeWidth={3.2}
          />
        </Svg>
      </View>
    </LinearGradient>
  );
}

export function OnboardingMosaic({ height, width }: Props) {
  const horizontalPadding = 16;
  const gap = 12;
  const availableWidth = width - horizontalPadding * 2 - gap * 2;
  const unit = availableWidth / 384;
  const narrow = 109 * unit;
  const wide = 166 * unit;
  const verticalScale = Math.max(0.82, Math.min(width / 440, 1.05));
  const radiusNarrow = narrow / 2;
  const radiusWide = wide / 2;

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <View style={[styles.column, { left: horizontalPadding, width: narrow }]}>
        <Tile height={215 * verticalScale} radius={radiusNarrow} source={images.marbleMountains} top={0} width={narrow} />
        <Tile height={367 * verticalScale} radius={radiusNarrow} source={images.chamSculpture} top={227 * verticalScale} width={narrow} />
        <Tile height={261 * verticalScale} radius={radiusNarrow} source={images.marbleMountains} top={606 * verticalScale} width={narrow} />
      </View>

      <View style={[styles.column, { left: horizontalPadding + narrow + gap, width: wide }]}>
        <Tile height={344 * verticalScale} radius={radiusWide} source={images.dragonBridge} top={-25 * verticalScale} width={wide} />
        <View style={[styles.audioMark, { height: 94 * verticalScale, top: 349 * verticalScale, width: wide }]}>
          <AudioMark size={94 * verticalScale} />
        </View>
        <Tile height={344 * verticalScale} radius={radiusWide} source={images.beach} top={473 * verticalScale} width={wide} />
      </View>

      <View style={[styles.column, { left: horizontalPadding + narrow + gap + wide + gap, width: narrow }]}>
        <Tile height={215 * verticalScale} radius={radiusNarrow} source={images.cyclo} top={0} width={narrow} />
        <Tile height={371 * verticalScale} radius={radiusNarrow} source={images.cityBridge} top={227 * verticalScale} width={narrow} />
        <Tile height={215 * verticalScale} radius={radiusNarrow} source={images.beach} top={610 * verticalScale} width={narrow} />
      </View>

      <LinearGradient
        colors={['rgba(255,255,255,0)', 'rgba(255,255,255,0.92)', colors.white]}
        locations={[0, 0.29, 0.56]}
        style={[styles.fade, { height: height * 0.68, top: height * 0.31 }]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  column: {
    bottom: 0,
    position: 'absolute',
    top: 0,
  },
  tile: {
    backgroundColor: colors.skyWash,
    left: 0,
    overflow: 'hidden',
    position: 'absolute',
  },
  image: {
    height: '100%',
    width: '100%',
  },
  audioMark: {
    alignItems: 'center',
    justifyContent: 'center',
    left: 0,
    position: 'absolute',
  },
  audioRing: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 4,
  },
  audioCore: {
    alignItems: 'center',
    backgroundColor: colors.teal,
    flex: 1,
    justifyContent: 'center',
    width: '100%',
  },
  fade: {
    left: 0,
    position: 'absolute',
    right: 0,
  },
});
