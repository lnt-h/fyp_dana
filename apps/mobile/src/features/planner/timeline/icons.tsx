import Svg, { Circle, Path } from 'react-native-svg';
import { colors } from '../../../theme/colors';
import { palette } from '../../auth/components/AuthUI';

const paths = {
  walk: 'M13 4.5a1.5 1.5 0 1 0 0-.01M10 21l2-6 3 3v3M9 12l2-4 3 1 2 3h3M11 8l-3 2v3',
  drive: 'M5 16V11l2-5h10l2 5v5ZM5 16v2M19 16v2M5 11h14M8 13.5h.01M16 13.5h.01',
  recenter: 'M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5',
  previous: 'M15 5l-7 7 7 7',
  next: 'M9 5l7 7-7 7',
  chevronDown: 'M6 9l6 6 6-6',
  chevronUp: 'M6 15l6-6 6 6',
  sparkle: 'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8Z',
  card: 'M4 5h16v14H4ZM8 9h8M8 13h5',
  check: 'M5 12.5l4.5 4.5L19 7',
  close: 'M6 6l12 12M18 6L6 18',
} as const;

export type PlannerIconName = keyof typeof paths;

export function PlannerIcon({ name, color = colors.deepOcean, size = 20 }: { name: PlannerIconName; color?: string; size?: number }) {
  return <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden={true}>
    <Path d={paths[name]} fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
  </Svg>;
}

/** Plan Health glyphs: never the only signal, always shown next to a word. */
export function HealthGlyph({ health, size = 18 }: { health: 'GOOD' | 'WARNING' | 'BLOCKED'; size?: number }) {
  if (health === 'GOOD') {
    return <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden={true}>
      <Circle cx={12} cy={12} r={10} fill={colors.audioTeal} />
      <Path d="M7 12.5l3.2 3.2L17 9" fill="none" stroke={colors.white} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
    </Svg>;
  }
  if (health === 'WARNING') {
    return <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden={true}>
      <Path d="M12 2.5L22.5 21h-21Z" fill={colors.sun} stroke={colors.sun} strokeWidth={1.5} strokeLinejoin="round" />
      <Path d="M12 9v5.5M12 17.5v.1" stroke={colors.ink} strokeWidth={2.2} strokeLinecap="round" />
    </Svg>;
  }
  return <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden={true}>
    <Circle cx={12} cy={12} r={10} fill={palette.error} />
    <Path d="M7 12h10" stroke={colors.white} strokeWidth={2.6} strokeLinecap="round" />
  </Svg>;
}
