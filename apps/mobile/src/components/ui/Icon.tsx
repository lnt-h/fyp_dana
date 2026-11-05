import Svg, { Path } from 'react-native-svg';
import { colors } from '../../theme/colors';

/** Circle as a path segment (keeps every icon a list of stroked paths). */
const c = (cx: number, cy: number, r: number) => `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0`;

type Stroke = { d: string; sw?: number };

/** 24×24 line icons, one stroke style (1.75, round caps and joins). */
const ICONS = {
  back: [{ d: 'M15 5l-7 7 7 7' }],
  more: [{ d: 'M5.5 12h.01M12 12h.01M18.5 12h.01', sw: 3.2 }],
  'map-pin': [{ d: 'M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z' }, { d: c(12, 9.5, 2.5) }],
  calendar: [{ d: 'M6.5 5h11a3 3 0 0 1 3 3v9.5a3 3 0 0 1-3 3h-11a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3zM3.5 10h17M8 3v4M16 3v4' }],
  clock: [{ d: c(12, 12, 8.5) }, { d: 'M12 7.5V12l3 2' }],
  walk: [{ d: c(13.5, 4.5, 1.7) }, { d: 'M9 21l2.6-6.2M12.8 21v-4.4l-2.3-2.4 1-5.2M7 12.2l2.2-3.1 3.3-.9 2.2 3.3 2.6 1.1' }],
  car: [{ d: 'M4 12l1.8-4.6A2 2 0 0 1 7.7 6h8.6a2 2 0 0 1 1.9 1.4L20 12v5H4zM4 12h16M6.5 17v2M17.5 17v2M7.5 14.5h.01M16.5 14.5h.01' }],
  bike: [{ d: c(6, 16, 3.5) }, { d: c(18, 16, 3.5) }, { d: 'M6 16l3.5-7H15l3 7M9.5 9l2.5 7 3-7M13 6h3' }],
  boat: [{ d: 'M3 14h18l-2.5 5h-13zM12 4v10M12 5l6 7h-6' }],
  sparkle: [{ d: 'M11 4l1.8 5.2L18 11l-5.2 1.8L11 18l-1.8-5.2L4 11l5.2-1.8zM18.5 3v3.5M16.75 4.75h3.5' }],
  /** Two-tier Vietnamese pagoda roof with upturned eaves (not a torii). */
  heritage: [{ d: 'M12 2.5v3M6 7.5c1.5 0 2.5-.8 3.2-2h5.6c.7 1.2 1.7 2 3.2 2M8 7.5V11h8V7.5M3 13c2 0 3.2-.8 4-2h10c.8 1.2 2 2 4 2M5.5 13v7h13v-7M10.5 20v-3.5h3V20M3 20.5h18' }],
  food: [{ d: 'M4 11h16c0 4.4-3.6 8-8 8s-8-3.6-8-8zM14.5 3L11 10M19 4l-5.5 6M9 21h6' }],
  market: [{ d: 'M4 9l1.5-5h13L20 9M4 9a2.67 2.67 0 0 0 5.33 0 2.67 2.67 0 0 0 5.34 0A2.67 2.67 0 0 0 20 9M5.5 11.5V20h13v-8.5M10 20v-5h4v5' }],
  beach: [{ d: 'M3.5 11a8.5 7 0 0 1 17 0zM12 11v6.5M3 20c1.5 0 1.5-1 3-1s1.5 1 3 1 1.5-1 3-1 1.5 1 3 1 1.5-1 3-1 1.5 1 3 1' }],
  nature: [{ d: 'M5 19C5 10 10 5 19 5c0 9-5 14-14 14zM5 19l8-8' }],
  lantern: [{ d: 'M12 2.5v2M10 4.5h4M9.5 6.5h5c2.2 2.6 2.2 8.4 0 11h-5c-2.2-2.6-2.2-8.4 0-11zM12 6.5v11M10 17.5v1.5h4v-1.5M12 19v2.5' }],
  camera: [{ d: 'M4 8h3l1.5-2.5h7L17 8h3a1 1 0 0 1 1 1v9.5a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z' }, { d: c(12, 13.5, 3.5) }],
  info: [{ d: c(12, 12, 9) }, { d: 'M12 11v5.5M12 7.8h.01' }],
  check: [{ d: 'M5 12.5l4.5 4.5L19 7.5' }],
  warning: [{ d: 'M10.3 4.5a2 2 0 0 1 3.4 0l7.6 13a2 2 0 0 1-1.7 3H4.4a2 2 0 0 1-1.7-3zM12 9.5V14M12 17.2h.01' }],
  blocked: [{ d: c(12, 12, 9) }, { d: 'M5.6 5.6l12.8 12.8' }],
  'chevron-right': [{ d: 'M9 5l7 7-7 7' }],
  search: [{ d: c(11, 11, 6.5) }, { d: 'M16 16l4.5 4.5' }],
  send: [{ d: 'M4 12L20 4l-6 16-2.5-7zM11.5 13L20 4' }],
  trash: [{ d: 'M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13M10 11v5M14 11v5' }],
  navigation: [{ d: 'M20 4L3.5 11l7 2.5L13 20.5z' }],
  share: [{ d: 'M12 3.5v11M7.5 8L12 3.5 16.5 8M5 12v7.5h14V12' }],
} satisfies Record<string, Stroke[]>;

export type IconName = keyof typeof ICONS;

export type IconProps = {
  name: IconName;
  /** Box size in dp (default 24). */
  size?: number;
  color?: string;
  /** Stroke width in the 24-unit grid (default 1.75). */
  strokeWidth?: number;
  /** Set for icons that carry meaning on their own; decorative icons stay hidden from screen readers. */
  accessibilityLabel?: string;
};

export function Icon({ name, size = 24, color = colors.ink, strokeWidth = 1.75, accessibilityLabel }: IconProps) {
  const strokes: Stroke[] = ICONS[name];
  return (
    <Svg
      accessibilityElementsHidden={!accessibilityLabel}
      accessibilityLabel={accessibilityLabel}
      accessibilityRole={accessibilityLabel ? 'image' : undefined}
      fill="none"
      height={size}
      importantForAccessibility={accessibilityLabel ? 'yes' : 'no-hide-descendants'}
      viewBox="0 0 24 24"
      width={size}
    >
      {strokes.map((stroke, index) => (
        <Path d={stroke.d} key={index} stroke={color} strokeLinecap="round" strokeLinejoin="round" strokeWidth={stroke.sw ?? strokeWidth} />
      ))}
    </Svg>
  );
}

/** Category code → icon. Evening walks use the lantern; unknown codes fall back to the map pin. */
export function categoryIcon(code: string | null | undefined): IconName {
  switch (code) {
    case 'heritage':
    case 'history':
    case 'museum':
    case 'temple':
      return 'heritage';
    case 'market':
      return 'market';
    case 'food':
    case 'cafe':
      return 'food';
    case 'nature':
      return 'nature';
    case 'beach':
      return 'beach';
    case 'evening':
    case 'nightlife':
      return 'lantern';
    default:
      return 'map-pin';
  }
}

/** Travel mode → icon (contract TravelMode plus roadmap modes). */
export function travelModeIcon(mode: 'WALK' | 'DRIVE' | 'BIKE' | 'BOAT' | string): IconName {
  if (mode === 'WALK') return 'walk';
  if (mode === 'BIKE') return 'bike';
  if (mode === 'BOAT') return 'boat';
  return 'car';
}
