import { Platform, type ViewStyle } from 'react-native';
import { colors } from './colors';

/** Soft shadow presets. iOS uses shadow*, Android uses elevation (tinted with shadowColor on API 28+). */
const make = (offsetY: number, radius: number, opacity: number, elevation: number): ViewStyle =>
  Platform.select<ViewStyle>({
    android: { elevation, shadowColor: colors.ink },
    default: {
      shadowColor: colors.ink,
      shadowOffset: { height: offsetY, width: 0 },
      shadowOpacity: opacity,
      shadowRadius: radius,
    },
  }) ?? {};

/**
 * Cards carry no border and no shadow on white (visual refresh 2026-11-09). Elevation is only for things floating
 * over the map or a sheet: use `floating` (y 4, blur 16, opacity 0.08).
 */
export const elevation = {
  none: {} as ViewStyle,
  floating: make(4, 16, 0.08, 4),
  sm: make(2, 6, 0.08, 2),
  md: make(8, 18, 0.1, 5),
  lg: make(16, 32, 0.14, 10),
} as const;

export type ElevationToken = keyof typeof elevation;
