import { memo } from 'react';
import { Image, ImageSourcePropType, StyleSheet, View } from 'react-native';
import Svg, { Circle, Defs, G, Path, RadialGradient, Stop } from 'react-native-svg';

import { colors } from '../../../theme/colors';
import {
  OnboardingLowerFade,
  OnboardingPatternBackdrop,
} from './OnboardingPatternBackground';

const images = {
  beach: require('../../../../assets/images/places/beach.png'),
  chamSculpture: require('../../../../assets/images/places/cham-sculpture.png'),
  cityBridge: require('../../../../assets/images/places/city-bridge.png'),
  cyclo: require('../../../../assets/images/places/cyclo.png'),
  dragonBridge: require('../../../../assets/images/places/dragon-bridge.png'),
  linhUngPagoda: require('../../../../assets/images/places/linh-ung-pagoda.png'),
  marbleMountains: require('../../../../assets/images/places/marble-mountains.png'),
  miQuang: require('../../../../assets/images/places/mi-quang.png'),
} satisfies Record<string, ImageSourcePropType>;

const designFrame = {
  height: 956,
  width: 440,
} as const;

const imageCrops = {
  beach: { height: 1, width: 0.643545, x: 0.178227, y: 0 },
  chamSculpture: { height: 1, width: 0.216295, x: 0.360357, y: 0 },
  cityBridge: { height: 1, width: 0.210829, x: 0.175304, y: 0 },
  cyclo: { height: 1, width: 0.633721, x: 0.18314, y: 0 },
  dragonBridge: { height: 0.777172, width: 0.461913, x: 0.141856, y: -0.070704 },
  linhUngPagoda: { height: 1, width: 0.271312, x: 0.364344, y: 0 },
  marbleMountains: { height: 1, width: 0.339024, x: 0.330488, y: 0 },
  miQuang: { height: 1, width: 0.556644, x: 0.169572, y: 0 },
} as const;

type Props = {
  height: number;
  width: number;
};

type TileProps = {
  crop: {
    height: number;
    width: number;
    x: number;
    y: number;
  };
  height: number;
  radius: number;
  source: ImageSourcePropType;
  top: number;
  width: number;
};

function Tile({ crop, height, radius, source, top, width }: TileProps) {
  const imageHeight = height / crop.height;
  const imageWidth = width / crop.width;

  return (
    <View style={[styles.tile, { borderRadius: radius, height, top, width }]}>
      <Image
        resizeMode="cover"
        source={source}
        style={[
          styles.image,
          {
            height: imageHeight,
            left: -crop.x * imageWidth,
            top: -crop.y * imageHeight,
            width: imageWidth,
          },
        ]}
      />
    </View>
  );
}

export function AudioMark({ size }: { size: number }) {
  return (
    <Svg height={size} viewBox="0 0 94 94" width={size}>
      <Defs>
        <RadialGradient cx="50%" cy="50%" id="audioGlow" r="50%">
          <Stop offset="0%" stopColor={colors.audioTeal} />
          <Stop offset="62%" stopColor={colors.audioTeal} />
          <Stop offset="100%" stopColor={colors.sun} stopOpacity={0.72} />
        </RadialGradient>
      </Defs>
      <Circle
        cx={47}
        cy={47}
        fill="url(#audioGlow)"
        r={46.5}
        stroke={colors.audioTeal}
        strokeOpacity={0.4}
      />
      <G transform="translate(18 18)">
        <Path
          d="M14 31V27M21.5 38V20M29 43V15M36.5 37V21M44 33V25"
          fill="none"
          stroke={colors.white}
          strokeLinecap="round"
          strokeWidth={3.2}
        />
      </G>
    </Svg>
  );
}

export const OnboardingMosaic = memo(function OnboardingMosaic({ height, width }: Props) {
  const scale = Math.min(width / designFrame.width, height / designFrame.height);
  const canvasLeft = (width - designFrame.width * scale) / 2;
  const narrow = 109 * scale;
  const wide = 166 * scale;
  const radiusNarrow = narrow / 2;
  const radiusWide = wide / 2;

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <OnboardingPatternBackdrop height={height} variant="discover" width={width} />
      <View style={[styles.column, { left: canvasLeft + 16 * scale, width: narrow }]}>
        <Tile
          crop={imageCrops.marbleMountains}
          height={215 * scale}
          radius={radiusNarrow}
          source={images.marbleMountains}
          top={0}
          width={narrow}
        />
        <Tile
          crop={imageCrops.chamSculpture}
          height={367 * scale}
          radius={radiusNarrow}
          source={images.chamSculpture}
          top={227 * scale}
          width={narrow}
        />
        <Tile
          crop={imageCrops.miQuang}
          height={261 * scale}
          radius={radiusNarrow}
          source={images.miQuang}
          top={606 * scale}
          width={narrow}
        />
      </View>

      <View style={[styles.column, { left: canvasLeft + 137 * scale, width: wide }]}>
        <Tile
          crop={imageCrops.dragonBridge}
          height={344 * scale}
          radius={radiusWide}
          source={images.dragonBridge}
          top={-25 * scale}
          width={wide}
        />
        <View style={[styles.audioMark, { height: 94 * scale, top: 349 * scale, width: wide }]}>
          <AudioMark size={94 * scale} />
        </View>
        <Tile
          crop={imageCrops.beach}
          height={344 * scale}
          radius={radiusWide}
          source={images.beach}
          top={473 * scale}
          width={wide}
        />
      </View>

      <View style={[styles.column, { left: canvasLeft + 315 * scale, width: narrow }]}>
        <Tile
          crop={imageCrops.cyclo}
          height={215 * scale}
          radius={radiusNarrow}
          source={images.cyclo}
          top={0}
          width={narrow}
        />
        <Tile
          crop={imageCrops.cityBridge}
          height={371 * scale}
          radius={radiusNarrow}
          source={images.cityBridge}
          top={227 * scale}
          width={narrow}
        />
        <Tile
          crop={imageCrops.linhUngPagoda}
          height={215 * scale}
          radius={radiusNarrow}
          source={images.linhUngPagoda}
          top={610 * scale}
          width={narrow}
        />
      </View>

      <OnboardingLowerFade height={height} variant="discover" width={width} />
    </View>
  );
});

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
    position: 'absolute',
  },
  audioMark: {
    alignItems: 'center',
    justifyContent: 'center',
    left: 0,
    position: 'absolute',
  },
});
