import Svg, { Circle, Path } from 'react-native-svg';
import { Icon, type IconName } from '../../../components/ui/Icon';
import { colors } from '../../../theme/colors';
import { palette } from '../../auth/components/AuthUI';

/** Planner glyph names → the shared Icon family (kept so call sites stay unchanged). */
const plannerIcons = {
  walk: 'walk',
  drive: 'car',
  recenter: 'recenter',
  previous: 'back',
  next: 'chevron-right',
  chevronDown: 'chevron-down',
  chevronUp: 'chevron-up',
  sparkle: 'sparkle',
  card: 'card',
  check: 'check',
  close: 'close',
  lock: 'lock',
  unlock: 'unlock',
  plus: 'plus',
  minus: 'minus',
  arrowUp: 'arrow-up',
  arrowDown: 'arrow-down',
  toStart: 'to-start',
  swap: 'swap',
  refresh: 'refresh',
  edit: 'edit',
  calendarMove: 'calendar-move',
} as const satisfies Record<string, IconName>;

export type PlannerIconName = keyof typeof plannerIcons;

export function PlannerIcon({ name, color = colors.deepOcean, size = 20 }: { name: PlannerIconName; color?: string; size?: number }) {
  return <Icon color={color} name={plannerIcons[name]} size={size} />;
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
