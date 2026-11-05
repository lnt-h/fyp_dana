import Svg, { Path } from 'react-native-svg';
import { colors } from '../../theme/colors';

/** Circle as a path segment (keeps every icon a list of paths). */
const c = (cx: number, cy: number, r: number) => `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0`;

/**
 * One drawn shape. `sw` overrides the stroke width (dots); `fill` paints the shape solid with an
 * even-odd rule, so inner sub-paths become holes. Filled shapes keep the same stroke, so holes are
 * drawn ~0.9 unit larger on each side than their visible size.
 */
type Shape = { d: string; sw?: number; fill?: true };
type Glyph = { line: Shape[]; filled?: Shape[] };

const pin = 'M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z';
const chevronRight = 'M9 5l7 7-7 7';
const calendar = 'M6.5 5h11a3 3 0 0 1 3 3v9.5a3 3 0 0 1-3 3h-11a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3zM3.5 10h17M8 3v4M16 3v4';
const bubble = 'M5.5 4h13A1.5 1.5 0 0 1 20 5.5v10a1.5 1.5 0 0 1-1.5 1.5h-8L6 20.5V17h-.5A1.5 1.5 0 0 1 4 15.5v-10A1.5 1.5 0 0 1 5.5 4z';
const suitcaseBody = 'M4.5 8h15A1.5 1.5 0 0 1 21 9.5v9a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18.5v-9A1.5 1.5 0 0 1 4.5 8z';
const suitcaseHandle = 'M9 8V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V8';
const shackleLocked = 'M7.5 11V8a4.5 4.5 0 0 1 9 0v3';
const lockBody = 'M6.5 11h11a1 1 0 0 1 1 1v7.5a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1V12a1 1 0 0 1 1-1zM12 14.5v2.5';

const line = (...ds: string[]): Glyph => ({ line: ds.map((d) => ({ d })) });

/**
 * Gonarra's single icon family: 24-unit grid, 1.75 stroke, round caps and joins.
 * Line style by default; `filled` variants exist for active states (tabs, map pin).
 */
const ICONS = {
  // Navigation and actions
  back: line('M15 5l-7 7 7 7'),
  'chevron-right': line(chevronRight),
  'chevron-down': line('M6 9l6 6 6-6'),
  'chevron-up': line('M6 15l6-6 6 6'),
  more: { line: [{ d: 'M5.5 12h.01M12 12h.01M18.5 12h.01', sw: 3.2 }] },
  close: line('M6 6l12 12M18 6L6 18'),
  plus: line('M12 5v14M5 12h14'),
  minus: line('M5 12h14'),
  'arrow-up': line('M12 19V5M6 11l6-6 6 6'),
  'arrow-down': line('M12 5v14M6 13l6 6 6-6'),
  'to-start': line('M5 5h14M12 20V9M7 14l5-5 5 5'),
  swap: line('M4 8h13M13 4l4 4-4 4M20 16H7M11 12l-4 4 4 4'),
  refresh: line('M19.5 12a7.5 7.5 0 1 1-2.2-5.3M19.5 4.5v4h-4'),
  recenter: line('M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5'),
  edit: line('M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4'),
  search: { line: [{ d: c(11, 11, 6.5) }, { d: 'M16 16l4.5 4.5' }] },
  send: line('M4 12L20 4l-6 16-2.5-7zM11.5 13L20 4'),
  share: line('M12 3.5v11M7.5 8L12 3.5 16.5 8M5 12v7.5h14V12'),
  trash: line('M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13M10 11v5M14 11v5'),
  exit: line('M9 3.5H5a1 1 0 0 0-1 1v15a1 1 0 0 0 1 1h4M9 12h11.5M16 7.5l4.5 4.5-4.5 4.5'),
  navigation: line('M20 4L3.5 11l7 2.5L13 20.5z'),

  // Tabs (line + filled)
  home: {
    line: [{ d: 'M4 10.5L12 4l8 6.5V19a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19zM9.5 20.5V15h5v5.5' }],
    filled: [{ d: 'M4 10.5L12 4l8 6.5V19a1.5 1.5 0 0 1-1.5 1.5h-4V15h-5v5.5h-4A1.5 1.5 0 0 1 4 19z', fill: true }],
  },
  compass: {
    line: [{ d: c(12, 12, 9) }, { d: 'M15.5 8.5l-2 5-5 2 2-5z' }],
    filled: [{ d: `${c(12, 12, 9)}M16.6 7.4l-2.6 6.6-6.6 2.6 2.6-6.6z`, fill: true }],
  },
  'chat-text': {
    line: [{ d: bubble }, { d: 'M8 9h8M8 12.5h5' }],
    filled: [{ d: `${bubble}M7.1 7.4h9.8v3.2H7.1zM7.1 10.9h6.8v3.2H7.1z`, fill: true }],
  },
  suitcase: {
    line: [{ d: suitcaseBody }, { d: suitcaseHandle }, { d: 'M8 8v12M16 8v12' }],
    filled: [{ d: suitcaseBody, fill: true }, { d: suitcaseHandle }],
  },
  'map-pin': {
    line: [{ d: pin }, { d: c(12, 9.5, 2.5) }],
    filled: [{ d: `${pin}${c(12, 9.5, 3)}`, fill: true }],
  },

  // Time and travel
  calendar: line(calendar),
  'calendar-move': line(calendar, 'M10 15h5M13 13l2 2-2 2'),
  clock: { line: [{ d: c(12, 12, 8.5) }, { d: 'M12 7.5V12l3 2' }] },
  walk: { line: [{ d: c(13.5, 4.5, 1.7) }, { d: 'M9 21l2.6-6.2M12.8 21v-4.4l-2.3-2.4 1-5.2M7 12.2l2.2-3.1 3.3-.9 2.2 3.3 2.6 1.1' }] },
  car: line('M4 12l1.8-4.6A2 2 0 0 1 7.7 6h8.6a2 2 0 0 1 1.9 1.4L20 12v5H4zM4 12h16M6.5 17v2M17.5 17v2M7.5 14.5h.01M16.5 14.5h.01'),
  bike: { line: [{ d: c(6, 16, 3.5) }, { d: c(18, 16, 3.5) }, { d: 'M6 16l3.5-7H15l3 7M9.5 9l2.5 7 3-7M13 6h3' }] },
  boat: line('M3 14h18l-2.5 5h-13zM12 4v10M12 5l6 7h-6'),

  // Gonarra categories: drawn to read at 16 pt
  /** Two-tier Vietnamese tile roof with upturned eaves (not a torii). */
  heritage: line(
    'M12 2.5v2',
    'M4 7.5c1.2 1.2 2.6 1.3 4 .5L10 4.5h4l2 3.5c1.4.8 2.8.7 4-.5',
    'M8.5 8.5V11M15.5 8.5V11',
    'M2.5 12c1.2 1.2 2.8 1.4 4.3.5L8 11h8l1.2 1.5c1.5.9 3.1.7 4.3-.5',
    'M6 13.5V20M18 13.5V20M10 20v-3.5h4V20M3.5 20h17',
  ),
  /** Market hall roof sheltering a stall with a scalloped awning. */
  market: line(
    'M2.5 9.5L12 4l9.5 5.5',
    'M5 8.5V20M19 8.5V20M3 20h18',
    'M8 11.5h8v1.5a2 2 0 0 1-4 0 2 2 0 0 1-4 0z',
    'M8.5 15V20M15.5 15V20M8.5 17.5h7',
  ),
  /** Bowl with chopsticks. */
  food: line('M3.5 11.5h17c0 4.4-3.8 8-8.5 8s-8.5-3.6-8.5-8z', 'M9.5 21.5h5', 'M12.5 9.5L18 3M15 10l6-5'),
  /** Round basket boat (thúng chai) with paddle, riding a wave. */
  beach: line(
    'M5 12h14c0 2.8-3.1 5-7 5s-7-2.2-7-5z',
    'M14 12l4-7.5',
    'M2.5 20.5c1.5 0 2-1 3.2-1s1.7 1 3.2 1 2-1 3.1-1 1.7 1 3.2 1 2-1 3.2-1 1.7 1 3.1 1',
  ),
  /** Water-coconut (nipa) palm: fronds rising from the water line. */
  nature: line(
    'M12 18V4',
    'M12 18c-.5-5-3-8.5-7-10.5M12 18c.5-5 3-8.5 7-10.5',
    'M12 18c-1.5-3-4.5-4.5-8.5-4M12 18c1.5-3 4.5-4.5 8.5-4',
    'M4 20.5h16',
  ),
  /** Hội An hexagonal silk lantern: caps, two visible facet ribs, tassel. */
  lantern: line(
    'M12 2v2.5M10 6.5v-2h4v2',
    'M9 6.5h6c2.2 2 3 3.8 3 5.5s-.8 3.5-3 5.5H9c-2.2-2-3-3.8-3-5.5s.8-3.5 3-5.5z',
    'M10.5 6.5C9.5 8.5 9 10.1 9 12s.5 3.5 1.5 5.5M13.5 6.5c1 2 1.5 3.6 1.5 5.5s-.5 3.5-1.5 5.5',
    'M10 17.5v1.5h4v-1.5M12 19v3',
  ),

  // Status and content
  sparkle: line('M11 4l1.8 5.2L18 11l-5.2 1.8L11 18l-1.8-5.2L4 11l5.2-1.8zM18.5 3v3.5M16.75 4.75h3.5'),
  camera: { line: [{ d: 'M4 8h3l1.5-2.5h7L17 8h3a1 1 0 0 1 1 1v9.5a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z' }, { d: c(12, 13.5, 3.5) }] },
  info: { line: [{ d: c(12, 12, 9) }, { d: 'M12 11v5.5M12 7.8h.01' }] },
  check: line('M5 12.5l4.5 4.5L19 7.5'),
  warning: line('M10.3 4.5a2 2 0 0 1 3.4 0l7.6 13a2 2 0 0 1-1.7 3H4.4a2 2 0 0 1-1.7-3zM12 9.5V14M12 17.2h.01'),
  blocked: { line: [{ d: c(12, 12, 9) }, { d: 'M5.6 5.6l12.8 12.8' }] },
  card: line('M5 5h14a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zM8 9.5h8M8 13.5h5'),
  doc: line('M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6'),
  lock: line(shackleLocked, lockBody),
  unlock: line('M7.5 11V8a4.5 4.5 0 0 1 8.7-1.6', lockBody),
  shield: line('M12 2.5l8 3.5v6c0 5-8 9.5-8 9.5S4 17 4 12V6zM8.5 12l2.5 2.5 4.5-5'),

  // Account and settings
  person: { line: [{ d: c(12, 7.5, 4) }, { d: 'M4 21v-1.5a8 7 0 0 1 16 0V21' }] },
  sliders: { line: [{ d: 'M4 7h9M17 7h3M4 17h3M11 17h9' }, { d: c(15, 7, 2) }, { d: c(9, 17, 2) }] },
  settings: { line: [{ d: 'M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1z' }, { d: c(12, 12, 3.5) }] },
  language: line('M3.5 5.5h9M8 3.5v2M10.5 5.5c0 4-2.8 7-6.5 8.5M5.8 9c1.2 2.2 3.3 3.8 6.2 4.6M12.5 20.5l4-9 4 9M14 17.5h5'),
  motion: { line: [{ d: 'M2 8h5M2 12h3M2 16h5' }, { d: c(15, 12, 7) }, { d: 'M15 8.5V12l2.5 2' }] },
  device: line('M8 2.5h8a1.5 1.5 0 0 1 1.5 1.5v16a1.5 1.5 0 0 1-1.5 1.5H8A1.5 1.5 0 0 1 6.5 20V4A1.5 1.5 0 0 1 8 2.5zM11 18.5h2'),
} satisfies Record<string, Glyph>;

export type IconName = keyof typeof ICONS;

export type IconProps = {
  name: IconName;
  /** Box size in dp (default 24). */
  size?: number;
  color?: string;
  /** Stroke width in the 24-unit grid (default 1.75). */
  strokeWidth?: number;
  /** Solid variant for active states (tabs, selected pin). Falls back to the line style when none is drawn. */
  filled?: boolean;
  /** Set for icons that carry meaning on their own; decorative icons stay hidden from screen readers. */
  accessibilityLabel?: string;
};

export function Icon({ name, size = 24, color = colors.ink, strokeWidth = 1.75, filled = false, accessibilityLabel }: IconProps) {
  const glyph: Glyph = ICONS[name];
  const shapes = (filled && glyph.filled) || glyph.line;
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
      {shapes.map((shape, index) => (
        <Path
          d={shape.d}
          fill={shape.fill ? color : 'none'}
          fillRule={shape.fill ? 'evenodd' : undefined}
          key={index}
          stroke={color}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={shape.sw ?? strokeWidth}
        />
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
