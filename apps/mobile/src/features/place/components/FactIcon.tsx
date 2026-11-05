import Svg, { Path } from 'react-native-svg';

import { Icon, type IconName } from '../../../components/ui';
import { colors } from '../../../theme/colors';

/** Extra 24×24 line icons for place facts (same 1.8 stroke style as `components/ui/Icon`). */
const LOCAL = {
  ticket: ['M4 7.5a1.5 1.5 0 0 1 1.5-1.5h13A1.5 1.5 0 0 1 20 7.5V10a2 2 0 0 0 0 4v2.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 16.5V14a2 2 0 0 0 0-4z', 'M14.5 6.5v2M14.5 11v2M14.5 15.5v2'],
  door: ['M6 20.5V5a1.5 1.5 0 0 1 1.5-1.5h9A1.5 1.5 0 0 1 18 5v15.5M3.5 20.5h17M14.5 12h.01'],
  card: ['M4.5 6h15A1.5 1.5 0 0 1 21 7.5v9a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 16.5v-9A1.5 1.5 0 0 1 4.5 6zM3 10h18M7 14.5h3'],
  shirt: ['M9 4l3 2 3-2 5 3-2 4-2-1v10H8V10l-2 1-2-4z'],
  rules: ['M7 3.5h10A1.5 1.5 0 0 1 18.5 5v14.5A1.5 1.5 0 0 1 17 21H7a1.5 1.5 0 0 1-1.5-1.5V5A1.5 1.5 0 0 1 7 3.5zM9 8.5h6M9 12.5h6M9 16.5h3.5'],
} as const;

export type FactIconName = keyof typeof LOCAL | IconName;

export function FactIcon({ name, size = 20, color = colors.tealText }: { name: FactIconName; size?: number; color?: string }) {
  if (!(name in LOCAL)) return <Icon color={color} name={name as IconName} size={size} />;
  return <Svg accessibilityElementsHidden fill="none" height={size} importantForAccessibility="no-hide-descendants" viewBox="0 0 24 24" width={size}>
    {LOCAL[name as keyof typeof LOCAL].map(d => <Path d={d} key={d} stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} />)}
  </Svg>;
}

/** Fact field → icon. */
export function factIcon(code: string): FactIconName {
  switch (code) {
    case 'OPENING_HOURS': return 'clock';
    case 'ADMISSION_PRICE': return 'ticket';
    case 'ENTRANCE_LOCATION': return 'door';
    case 'ADDRESS_VI': return 'map-pin';
    case 'PAYMENT_METHODS': return 'card';
    case 'DRESS_CODE': return 'shirt';
    case 'ACCESS_RULES': return 'rules';
    default: return 'info';
  }
}
