import { memo, useState } from 'react';
import { useAuth } from '@clerk/expo';
import type { BottomTabBarProps } from 'expo-router/js-tabs';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';

import { SignInGate, type GateFeature } from '../../auth/SignInGate';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

export const tabs = ['home', 'explore', 'guide', 'trips'] as const;
export type Tab = (typeof tabs)[number];

/** Tabs that are private features: guests see the sign-in gate instead (S-3, SCR-040). */
const gatedTabs: Partial<Record<Tab, GateFeature>> = { guide: 'guide', trips: 'trips' };

const isTab = (name: string): name is Tab => (tabs as readonly string[]).includes(name);

/** Height of the bar's tappable row (icon + label), above the bottom safe-area inset. */
const BAR_HEIGHT = 58;
/** Breathing room under the labels on devices without a home indicator. */
const MIN_BOTTOM_PAD = 6;

/** Full height of the tab bar including the bottom safe-area inset. */
export function useTabBarHeight() {
  const insets = useSafeAreaInsets();
  return BAR_HEIGHT + Math.max(insets.bottom, MIN_BOTTOM_PAD);
}

/** Bottom padding a tab screen needs so the bar never covers its content. */
export function useTabBarClearance() {
  return useTabBarHeight() + spacing.md;
}

type IconProps = {
  active: boolean;
  tab: Tab;
};

/** Rendered at 26 dp from a 30-unit grid, so the 2-unit stroke lands at ~1.75 dp like `Icon`. */
const ICON = 26;

function TabIcon({ active, tab }: IconProps) {
  const stroke = colors.textMuted;

  if (active) {
    const activePaths: Record<Tab, string[]> = {
      home: [
        'M26.0375 10.0125L17.85 3.46252C16.25 2.18752 13.75 2.17502 12.1625 3.45002L3.97495 10.0125C2.79995 10.95 2.08745 12.825 2.33745 14.3L3.91245 23.725C4.27495 25.8375 6.23745 27.5 8.37495 27.5H21.625C23.7375 27.5 25.7375 25.8 26.1 23.7125L27.675 14.2875C27.9 12.825 27.1875 10.95 26.0375 10.0125ZM15.9375 22.5C15.9375 23.0125 15.5125 23.4375 15 23.4375C14.4875 23.4375 14.0625 23.0125 14.0625 22.5V18.75C14.0625 18.2375 14.4875 17.8125 15 17.8125C15.5125 17.8125 15.9375 18.2375 15.9375 18.75V22.5Z',
      ],
      explore: [
        'M9.53755 4.46248C9.76178 4.34017 10 4.52833 10 4.78374V21.8228C10 22.0461 9.84889 22.2362 9.6471 22.3317C9.6096 22.3495 9.57316 22.3681 9.53755 22.3875L6.60005 24.0625C4.55005 25.2375 2.86255 24.2625 2.86255 21.8875V9.72498C2.86255 8.93748 3.42505 7.96248 4.12505 7.56248L9.53755 4.46248Z',
        'M18.4719 7.66232C18.6422 7.74668 18.75 7.92031 18.75 8.11039V24.8284C18.75 25.1969 18.365 25.4388 18.033 25.2788L12.4705 22.5989C12.2975 22.5155 12.1875 22.3405 12.1875 22.1484V5.35562C12.1875 4.98477 12.5771 4.74297 12.9094 4.90756L18.4719 7.66232Z',
        'M27.5 8.11252V20.275C27.5 21.0625 26.9375 22.0375 26.2375 22.4375L21.6861 25.046C21.3528 25.237 20.9375 24.9964 20.9375 24.6122V7.84034C20.9375 7.66083 21.0337 7.49509 21.1896 7.4061L23.7625 5.93752C25.8125 4.76252 27.5 5.73752 27.5 8.11252Z',
      ],
      guide: [
        'M16.4875 7.5H8.4875C8.1625 7.5 7.85 7.5125 7.55 7.55C4.1875 7.8375 2.5 9.825 2.5 13.4875V18.4875C2.5 23.4875 4.5 24.475 8.4875 24.475H8.9875C9.2625 24.475 9.625 24.6625 9.7875 24.875L11.2875 26.875C11.95 27.7625 13.025 27.7625 13.6875 26.875L15.1875 24.875C15.375 24.625 15.675 24.475 15.9875 24.475H16.4875C20.15 24.475 22.1375 22.8 22.425 19.425C22.4625 19.125 22.475 18.8125 22.475 18.4875V13.4875C22.475 9.5 20.475 7.5 16.4875 7.5ZM8.125 17.5C7.425 17.5 6.875 16.9375 6.875 16.25C6.875 15.5625 7.4375 15 8.125 15C8.8125 15 9.375 15.5625 9.375 16.25C9.375 16.9375 8.8125 17.5 8.125 17.5ZM12.4875 17.5C11.7875 17.5 11.2375 16.9375 11.2375 16.25C11.2375 15.5625 11.8 15 12.4875 15C13.175 15 13.7375 15.5625 13.7375 16.25C13.7375 16.9375 13.1875 17.5 12.4875 17.5ZM16.8625 17.5C16.1625 17.5 15.6125 16.9375 15.6125 16.25C15.6125 15.5625 16.175 15 16.8625 15C17.55 15 18.1125 15.5625 18.1125 16.25C18.1125 16.9375 17.55 17.5 16.8625 17.5Z',
        'M27.4751 8.4875V13.4875C27.4751 15.9875 26.7001 17.6875 25.1501 18.625C24.7751 18.85 24.3376 18.55 24.3376 18.1125L24.3501 13.4875C24.3501 8.4875 21.4876 5.625 16.4876 5.625L8.87506 5.6375C8.43756 5.6375 8.13756 5.2 8.36256 4.825C9.30006 3.275 11.0001 2.5 13.4876 2.5H21.4876C25.4751 2.5 27.4751 4.5 27.4751 8.4875Z',
      ],
      trips: [
        'M16.1125 7.34998H6.3875C4.25 7.34998 2.5 9.09998 2.5 11.2375V25.4375C2.5 27.25 3.8 28.025 5.3875 27.1375L10.3 24.4C10.825 24.1125 11.675 24.1125 12.1875 24.4L17.1 27.1375C18.7 28.0125 20 27.25 20 25.4375V11.2375C20 9.09998 18.25 7.34998 16.1125 7.34998Z',
        'M27.5 6.3875V20.5875C27.5 22.4 26.2 23.1625 24.6125 22.2875L22.2 20.9375C22 20.825 21.875 20.6125 21.875 20.3875V11.2375C21.875 8.0625 19.2875 5.475 16.1125 5.475H11.025C10.5625 5.475 10.2375 4.9875 10.45 4.5875C11.1 3.35 12.4 2.5 13.8875 2.5H23.6125C25.75 2.5 27.5 4.25 27.5 6.3875Z',
      ],
    };

    return (
      <Svg height={ICON} viewBox="0 0 30 30" width={ICON}>
        {activePaths[tab].map((path) => (
          <Path d={path} fill={colors.ink} key={path} />
        ))}
      </Svg>
    );
  }

  const linePaths: Record<Tab, string[]> = {
    home: [
      'M15 22.5V18.75',
      'M12.5878 3.52475L3.92533 10.4623C2.95033 11.2373 2.32533 12.8748 2.53783 14.0998L4.20033 24.0498C4.50033 25.8248 6.20033 27.2622 8.00033 27.2622H22.0003C23.7878 27.2622 25.5003 25.8123 25.8003 24.0498L27.4628 14.0998C27.6628 12.8748 27.0378 11.2373 26.0753 10.4623L17.4128 3.53725C16.0753 2.46225 13.9128 2.46225 12.5878 3.52475Z',
    ],
    explore: [
      'M2.86255 9.72497V21.8875C2.86255 24.2625 4.55005 25.2375 6.60005 24.0625L9.53755 22.3875C10.175 22.025 11.2375 21.9875 11.9 22.325L18.4625 25.6125C19.125 25.9375 20.1875 25.9125 20.825 25.55L26.2375 22.45C26.925 22.05 27.5 21.075 27.5 20.275V8.11247C27.5 5.73747 25.8126 4.76247 23.7626 5.93747L20.825 7.61247C20.1875 7.97497 19.125 8.01247 18.4625 7.67497L11.9 4.39997C11.2375 4.07497 10.175 4.09997 9.53755 4.46247L4.12505 7.56247C3.42505 7.96247 2.86255 8.93747 2.86255 9.72497Z',
      'M10.7 5V21.25',
      'M19.6626 8.27502V25',
    ],
    guide: [
      'M22.475 13.4875V18.4875C22.475 18.8125 22.4625 19.125 22.425 19.425C22.1375 22.8 20.15 24.475 16.4875 24.475H15.9875C15.675 24.475 15.375 24.625 15.1875 24.875L13.6875 26.875C13.025 27.7625 11.95 27.7625 11.2875 26.875L9.78748 24.875C9.62498 24.6625 9.2625 24.475 8.9875 24.475H8.48751C4.50001 24.475 2.5 23.4875 2.5 18.4875V13.4875C2.5 9.82501 4.18751 7.83751 7.55001 7.55001C7.85001 7.51251 8.16251 7.5 8.48751 7.5H16.4875C20.475 7.5 22.475 9.50001 22.475 13.4875Z',
      'M27.4751 8.48751V13.4875C27.4751 17.1625 25.7875 19.1375 22.425 19.425C22.4625 19.125 22.4751 18.8125 22.4751 18.4875V13.4875C22.4751 9.50001 20.475 7.5 16.4875 7.5H8.48755C8.16255 7.5 7.85005 7.51251 7.55005 7.55001C7.83755 4.18751 9.82505 2.5 13.4875 2.5H21.4875C25.475 2.5 27.4751 4.50001 27.4751 8.48751Z',
      'M16.8694 16.5625H16.8806',
      'M12.4944 16.5625H12.5056',
      'M8.11937 16.5625H8.13062',
    ],
    trips: [
      'M16.1125 7.34998H6.38748C4.24998 7.34998 2.5 9.09996 2.5 11.2375V25.4375C2.5 27.25 3.8 28.025 5.3875 27.1375L10.3 24.4C10.825 24.1125 11.675 24.1125 12.1875 24.4L17.1 27.1375C18.6875 28.025 19.9875 27.25 19.9875 25.4375V11.2375C20 9.09996 18.25 7.34998 16.1125 7.34998Z',
      'M20 11.2375V25.4375C20 27.25 18.7 28.0125 17.1125 27.1375L12.2 24.4C11.675 24.1125 10.825 24.1125 10.3 24.4L5.3875 27.1375C3.8 28.0125 2.5 27.25 2.5 25.4375V11.2375C2.5 9.09996 4.24998 7.34998 6.38748 7.34998H16.1125C18.25 7.34998 20 9.09996 20 11.2375Z',
      'M27.5 6.38748V20.5875C27.5 22.4 26.2 23.1625 24.6125 22.2875L20 19.7125V11.2375C20 9.09999 18.25 7.35001 16.1125 7.35001H10V6.38748C10 4.24998 11.75 2.5 13.8875 2.5H23.6125C25.75 2.5 27.5 4.24998 27.5 6.38748Z',
    ],
  };

  return (
    <Svg height={ICON} viewBox="0 0 30 30" width={ICON}>
      {linePaths[tab].map((path) => (
        <Path
          d={path}
          fill="none"
          key={path}
          stroke={stroke}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
        />
      ))}
    </Svg>
  );
}

export const HomeTabBar = memo(function HomeTabBar({ emitter, navigateToTab, state }: BottomTabBarProps) {
  const { t } = useTranslation();
  const { isSignedIn } = useAuth();
  const insets = useSafeAreaInsets();
  const [gate, setGate] = useState<GateFeature | null>(null);
  const activeName = state.routes[state.index]?.name;

  function press(routeKey: string, tab: Tab, active: boolean) {
    const gated = gatedTabs[tab];
    if (gated && !isSignedIn) { setGate(gated); return; }
    const event = emitter.emit({ canPreventDefault: true, target: routeKey, type: 'tabPress' });
    if (!active && !event.defaultPrevented) navigateToTab(routeKey);
  }

  return (
    <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, MIN_BOTTOM_PAD) }]}>
      <View accessibilityLabel={t('tabs.navigation')} accessibilityRole="tablist" style={styles.row}>
        {state.routes.map((route) => {
          if (!isTab(route.name)) return null;
          const tab = route.name;
          const active = activeName === tab;

          return (
            <Pressable
              accessibilityLabel={t(`tabs.${tab}`)}
              accessibilityRole="tab"
              accessibilityState={{ selected: active }}
              key={route.key}
              onPress={() => press(route.key, tab, active)}
              style={({ pressed }) => [styles.tab, pressed && styles.pressed]}
            >
              {/* Sun dot marks the active tab together with the filled icon and ink label (never colour alone). */}
              <View style={[styles.dot, active && styles.dotActive]} />
              <TabIcon active={active} tab={tab} />
              <Text maxFontSizeMultiplier={1.3} numberOfLines={1} style={[styles.label, active && styles.labelActive]}>
                {t(`tabs.${tab}`)}
              </Text>
            </Pressable>
          );
        })}
      </View>
      <SignInGate feature={gate} onClose={() => setGate(null)} />
    </View>
  );
});

const styles = StyleSheet.create({
  bar: {
    backgroundColor: 'rgba(251,247,240,0.96)',
    borderTopColor: colors.hairline,
    borderTopWidth: StyleSheet.hairlineWidth,
    bottom: 0,
    left: 0,
    position: 'absolute',
    right: 0,
    shadowColor: colors.ink,
    shadowOffset: { height: -2, width: 0 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 8,
  },
  dot: { backgroundColor: 'transparent', borderRadius: 2, height: 4, marginBottom: 3, width: 4 },
  dotActive: { backgroundColor: colors.sun },
  label: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 11, lineHeight: 14, marginTop: 2 },
  labelActive: { color: colors.ink, fontFamily: fonts.semibold },
  pressed: { opacity: 0.7 },
  row: { flexDirection: 'row', height: BAR_HEIGHT },
  tab: { alignItems: 'center', flex: 1, justifyContent: 'center', minHeight: 44, paddingHorizontal: 2 },
});
