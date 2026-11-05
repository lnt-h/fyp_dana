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

export const elevation = {
  none: {} as ViewStyle,
  sm: make(2, 6, 0.08, 2),
  md: make(8, 18, 0.1, 5),
  lg: make(16, 32, 0.14, 10),
} as const;

export type ElevationToken = keyof typeof elevation;
