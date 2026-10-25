import { memo } from 'react';
import { Image, ImageSourcePropType, StyleSheet, View } from 'react-native';
import Svg, {
  Defs,
  Ellipse,
  FeGaussianBlur,
  Filter,
  G,
  LinearGradient,
  Mask,
  Rect,
  Stop,
} from 'react-native-svg';

const planningHero = require('../../../../assets/onboarding/planning-hero.png') as ImageSourcePropType;
const patternCells = Array.from({ length: 100 }, (_, index) => index);

const designFrame = {
  height: 956,
  width: 440,
} as const;

const exportedHero = {
  height: 400,
  left: 11,
  top: 160,
  width: 419,
} as const;

const designPattern = {
  cell: 90.2076,
  cornerRadius: 16.0611,
  left: -290.5,
  step: 96.0322,
  top: 31,
} as const;

const designAmbientGlow = {
  centerX: 219.5,
  centerY: 715,
  radiusX: 378.5,
  radiusY: 377,
} as const;

const lowerFade = {
  height: 493,
  top: 463,
} as const;

type Props = {
  height: number;
  width: number;
};

type BackgroundProps = {
  height: number;
  left: number;
  width: number;
};

function PlanningBackground({ height, left, width }: BackgroundProps) {
  return (
    <Svg
      height={height}
      style={[styles.background, { left }]}
      viewBox={`0 0 ${designFrame.width} ${designFrame.height}`}
      width={width}
    >
      <Defs>
        <LinearGradient id="planningAmbient" x1="0" x2="0" y1="0" y2="1">
          <Stop offset="0" stopColor="#BBE9FF" />
          <Stop offset="0.5" stopColor="#4383B6" />
          <Stop offset="1" stopColor="#C7CFD1" />
        </LinearGradient>
        <LinearGradient id="planningVeil" x1="0" x2="0" y1="0" y2="1">
          <Stop offset="0" stopColor="#BBE9FF" />
          <Stop offset="1" stopColor="#FFFFFF" stopOpacity={0} />
        </LinearGradient>
        <LinearGradient id="planningLowerFade" x1="0" x2="0" y1="0" y2="1">
          <Stop offset="0" stopColor="#FFFFFF" stopOpacity={0} />
          <Stop offset="0.12545185" stopColor="#FFFFFF" stopOpacity={0.25} />
          <Stop offset="0.27795538" stopColor="#FFFFFF" stopOpacity={0.5} />
          <Stop offset="0.5940541" stopColor="#FFFFFF" stopOpacity={1} />
          <Stop offset="1" stopColor="#FFFFFF" stopOpacity={1} />
        </LinearGradient>
        <LinearGradient id="patternSideVisibility" x1="0" x2="1" y1="0" y2="0">
          <Stop offset="0" stopColor="#FFFFFF" stopOpacity={0.75} />
          <Stop offset="0.23" stopColor="#FFFFFF" stopOpacity={0.5} />
          <Stop offset="0.38" stopColor="#FFFFFF" stopOpacity={0.08} />
          <Stop offset="0.5" stopColor="#FFFFFF" stopOpacity={0} />
          <Stop offset="0.62" stopColor="#FFFFFF" stopOpacity={0.08} />
          <Stop offset="0.77" stopColor="#FFFFFF" stopOpacity={0.5} />
          <Stop offset="1" stopColor="#FFFFFF" stopOpacity={0.75} />
        </LinearGradient>
        <Mask id="patternSideMask">
          <Rect fill="url(#patternSideVisibility)" height={designFrame.height} width={designFrame.width} />
        </Mask>
        <Filter height="160%" id="ambientBlur" width="160%" x="-30%" y="-30%">
          <FeGaussianBlur stdDeviation={50} />
        </Filter>
        <Filter height="120%" id="patternBlur" width="120%" x="-10%" y="-10%">
          <FeGaussianBlur stdDeviation={1} />
        </Filter>
        <Filter height="120%" id="lowerFadeBlur" width="120%" x="-10%" y="-10%">
          <FeGaussianBlur stdDeviation={10} />
        </Filter>
      </Defs>

      <Ellipse
        cx={designAmbientGlow.centerX}
        cy={designAmbientGlow.centerY}
        fill="url(#planningAmbient)"
        filter="url(#ambientBlur)"
        rx={designAmbientGlow.radiusX}
        ry={designAmbientGlow.radiusY}
      />

      <G filter="url(#patternBlur)" mask="url(#patternSideMask)">
        {patternCells.map((cell) => (
          <Rect
            fill="#FFFFFF"
            fillOpacity={0.2}
            height={designPattern.cell}
            key={cell}
            rx={designPattern.cornerRadius}
            width={designPattern.cell}
            x={designPattern.left + (cell % 10) * designPattern.step}
            y={designPattern.top + Math.floor(cell / 10) * designPattern.step}
          />
        ))}
      </G>

      <Rect fill="url(#planningVeil)" height={designFrame.height} width={designFrame.width} />
      <Rect
        fill="url(#planningLowerFade)"
        filter="url(#lowerFadeBlur)"
        height={lowerFade.height}
        width={designFrame.width}
        y={lowerFade.top}
      />
    </Svg>
  );
}

export const PlanningOnboardingScene = memo(function PlanningOnboardingScene({ height, width }: Props) {
  const scale = Math.min(width / designFrame.width, height / designFrame.height);
  const canvasWidth = designFrame.width * scale;
  const canvasHeight = designFrame.height * scale;
  const canvasLeft = (width - canvasWidth) / 2;

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <PlanningBackground height={canvasHeight} left={canvasLeft} width={canvasWidth} />
      <Image
        accessibilityIgnoresInvertColors
        resizeMode="contain"
        source={planningHero}
        style={[
          styles.preview,
          {
            height: exportedHero.height * scale,
            left: canvasLeft + exportedHero.left * scale,
            top: exportedHero.top * scale,
            width: exportedHero.width * scale,
          },
        ]}
      />
    </View>
  );
});

const styles = StyleSheet.create({
  background: {
    position: 'absolute',
    top: 0,
  },
  preview: {
    position: 'absolute',
  },
});
