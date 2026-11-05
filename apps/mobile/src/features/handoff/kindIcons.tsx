import Svg, { Path } from 'react-native-svg';

import type { HandoffKind } from '../../lib/api/types';
import { colors } from '../../theme/colors';

/** Same 24-grid line style as components/ui/Icon (1.8 stroke, round caps); local because the shared set has no bed/ticket/bus. */
const PATHS = {
  STAY: ['M3 18.5V6.5M3 14h18v4.5M21 14v-2.5a3 3 0 0 0-3-3h-7V14', 'M5.3 11.2a1.7 1.7 0 1 0 3.4 0a1.7 1.7 0 1 0 -3.4 0'],
  ACTIVITY: ['M4 7.5A1.5 1.5 0 0 1 5.5 6h13A1.5 1.5 0 0 1 20 7.5V10a2 2 0 0 0 0 4v2.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 16.5V14a2 2 0 0 0 0-4z', 'M14 6.5v2M14 11v2M14 15.5v2'],
  TRANSPORT: ['M6.5 4h11A2.5 2.5 0 0 1 20 6.5V17H4V6.5A2.5 2.5 0 0 1 6.5 4zM4 12h16M8 17v2.5M16 17v2.5', 'M7.5 14.5h.01M16.5 14.5h.01'],
  external: ['M14 4.5h5.5V10M19.5 4.5L11 13', 'M17 13.5v4A2 2 0 0 1 15 19.5H6.5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h4'],
} as const;

export type HandoffIconName = HandoffKind | 'external';

export function HandoffIcon({ name, size = 24, color = colors.ink }: { name: HandoffIconName; size?: number; color?: string }) {
  return (
    <Svg accessibilityElementsHidden fill="none" height={size} importantForAccessibility="no-hide-descendants" viewBox="0 0 24 24" width={size}>
      {PATHS[name].map((d, index) => (
        <Path d={d} key={index} stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth={d.includes('.01') ? 3 : 1.8} />
      ))}
    </Svg>
  );
}
