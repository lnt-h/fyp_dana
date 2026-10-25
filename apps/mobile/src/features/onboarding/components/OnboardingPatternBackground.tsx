import { memo } from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, {
  Defs,
  FeGaussianBlur,
  Filter,
  G,
  LinearGradient,
  Path,
  Rect,
  Stop,
} from 'react-native-svg';

const designFrame = {
  height: 956,
  width: 440,
} as const;

const designPattern = {
  cell: 90.2076,
  cornerRadius: 16.0611,
  left: -290.5,
  step: 96.0322,
  top: 31,
} as const;

const patternCells = Array.from({ length: 100 }, (_, index) => index);
const lowerFadeTop = {
  discover: 330,
  planning: 463,
} as const;

// Exact vector geometry exported from Figma node 201:214 / 115:501.
const ambientWash = {
  height: 822.7,
  left: -259,
  path: 'M765.576 100C812.557 154.459 842.948 221.149 853.173 292.226C863.398 363.303 853.033 435.81 823.295 501.218C793.558 566.627 745.685 622.217 685.309 661.449C624.933 700.682 554.564 721.925 482.48 722.68C410.395 723.434 339.594 703.67 278.403 665.711C217.212 627.752 168.176 573.177 137.065 508.405C105.953 443.634 94.0587 371.36 102.781 300.085C111.504 228.81 140.48 161.498 186.302 106.067L354.295 243.839C334.817 267.401 322.5 296.013 318.793 326.31C315.085 356.607 320.141 387.329 333.366 414.862C346.59 442.394 367.434 465.592 393.444 481.728C419.455 497.863 449.551 506.265 480.192 505.944C510.833 505.623 540.745 496.593 566.409 479.916C592.073 463.24 612.422 439.61 625.063 411.807C637.703 384.003 642.11 353.183 637.763 322.97C633.417 292.757 620.499 264.409 600.528 241.26L765.576 100Z',
  top: 369.3,
  width: 957,
} as const;

type CanvasProps = {
  height: number;
  variant: 'discover' | 'planning';
  width: number;
};

function getCanvasMetrics(height: number, width: number) {
  const scale = Math.min(width / designFrame.width, height / designFrame.height);
  const canvasWidth = designFrame.width * scale;

  return {
    canvasHeight: designFrame.height * scale,
    canvasLeft: (width - canvasWidth) / 2,
    canvasWidth,
    scale,
  };
}

export const OnboardingPatternBackdrop = memo(function OnboardingPatternBackdrop({
  height,
  variant,
  width,
}: CanvasProps) {
  const { canvasHeight, canvasLeft, canvasWidth } = getCanvasMetrics(height, width);
  const ambientBlurId = `${variant}AmbientBlur`;
  const ambientGradientId = `${variant}AmbientGradient`;
  const patternBlurId = `${variant}PatternBlur`;
  const veilId = `${variant}Veil`;
  const ambientLayer = (
    <G key="ambient" transform={`translate(${ambientWash.left} ${ambientWash.top})`}>
      <Path
        d={ambientWash.path}
        fill={`url(#${ambientGradientId})`}
        filter={`url(#${ambientBlurId})`}
      />
    </G>
  );
  const patternLayer = (
    <G filter={`url(#${patternBlurId})`} key="pattern">
      {patternCells.map((cell) => (
        <Rect
          fill="#BBE9FF"
          fillOpacity={0.2}
          height={designPattern.cell}
          key={cell}
          rx={designPattern.cornerRadius}
          stroke="#FFFFFF"
          strokeOpacity={0.24}
          strokeWidth={1}
          width={designPattern.cell}
          x={designPattern.left + (cell % 10) * designPattern.step}
          y={designPattern.top + Math.floor(cell / 10) * designPattern.step}
        />
      ))}
    </G>
  );
  const veilLayer = (
    <Rect
      fill={`url(#${veilId})`}
      height={designFrame.height}
      key="veil"
      width={designFrame.width}
    />
  );
  const layers =
    variant === 'discover'
      ? [veilLayer, ambientLayer, patternLayer]
      : [ambientLayer, veilLayer, patternLayer];

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <Svg
        height={canvasHeight}
        style={[styles.canvas, { left: canvasLeft }]}
        viewBox={`0 0 ${designFrame.width} ${designFrame.height}`}
        width={canvasWidth}
      >
        <Defs>
          <LinearGradient
            gradientUnits="userSpaceOnUse"
            id={ambientGradientId}
            x1={478.5}
            x2={478.5}
            y1={-31.2996}
            y2={722.7}
          >
            <Stop offset="0" stopColor="#BBE9FF" />
            <Stop offset="0.5" stopColor="#4383B6" />
            <Stop offset="1" stopColor="#C7CFD1" />
          </LinearGradient>
          <LinearGradient id={veilId} x1="0" x2="0" y1="0" y2="1">
            <Stop offset="0" stopColor="#BBE9FF" />
            <Stop offset="1" stopColor="#FFFFFF" stopOpacity={0} />
          </LinearGradient>
          <Filter height="120%" id={patternBlurId} width="120%" x="-10%" y="-10%">
            <FeGaussianBlur stdDeviation={1} />
          </Filter>
          <Filter height="130%" id={ambientBlurId} width="125%" x="-12%" y="-12%">
            <FeGaussianBlur stdDeviation={50} />
          </Filter>
        </Defs>

        {layers}
      </Svg>
    </View>
  );
});

export const OnboardingLowerFade = memo(function OnboardingLowerFade({
  height,
  variant,
  width,
}: CanvasProps) {
  const { canvasHeight, canvasLeft, canvasWidth } = getCanvasMetrics(height, width);
  const fadeId = `${variant}LowerFade`;
  const fadeBlurId = `${variant}LowerFadeBlur`;
  const fadeTop = lowerFadeTop[variant];

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <Svg
        height={canvasHeight}
        style={[styles.canvas, { left: canvasLeft }]}
        viewBox={`0 0 ${designFrame.width} ${designFrame.height}`}
        width={canvasWidth}
      >
        <Defs>
          <LinearGradient id={fadeId} x1="0" x2="0" y1="0" y2="1">
            <Stop offset="0" stopColor="#FFFFFF" stopOpacity={0} />
            <Stop offset="0.12545185" stopColor="#FFFFFF" stopOpacity={0.25} />
            <Stop offset="0.27795538" stopColor="#FFFFFF" stopOpacity={0.5} />
            <Stop offset="0.5940541" stopColor="#FFFFFF" stopOpacity={1} />
            <Stop offset="1" stopColor="#FFFFFF" stopOpacity={1} />
          </LinearGradient>
          <Filter height="120%" id={fadeBlurId} width="120%" x="-10%" y="-10%">
            <FeGaussianBlur stdDeviation={10} />
          </Filter>
        </Defs>
        <Rect
          fill={`url(#${fadeId})`}
          filter={`url(#${fadeBlurId})`}
          height={designFrame.height - fadeTop}
          width={designFrame.width}
          y={fadeTop}
        />
      </Svg>
    </View>
  );
});

const styles = StyleSheet.create({
  canvas: {
    position: 'absolute',
    top: 0,
  },
});
