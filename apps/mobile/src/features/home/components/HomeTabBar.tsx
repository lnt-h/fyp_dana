import { memo, useState } from 'react';
import type { BottomTabBarProps } from 'expo-router/js-tabs';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Icon, type IconName } from '../../../components/ui';

import { useAccount } from '../../account/AccountContext';
import { SignInGate, type GateFeature } from '../../auth/SignInGate';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';

export const tabs = ['home', 'explore', 'guide', 'trips'] as const;
export type Tab = (typeof tabs)[number];

/** Tabs that are private features: guests see the sign-in gate instead (S-3, SCR-040). */
const gatedTabs: Partial<Record<Tab, GateFeature>> = { guide: 'guide', trips: 'trips' };

const isTab = (name: string): name is Tab => (tabs as readonly string[]).includes(name);

/** Floating pill: active circle plus inner padding on each side. */
const CIRCLE = 56;
const PILL_PADDING = 8;
const PILL_HEIGHT = CIRCLE + PILL_PADDING * 2;
/** Gap between the pill and the home indicator (or the screen edge on devices without one). */
const BOTTOM_GAP = spacing.xs;
/** Colours taken from the owner's reference screenshot (local on purpose, not theme tokens). */
const PILL_BG = '#DCE1E4';
const ACTIVE_BG = '#B7D0D8';

function usePillBottom() {
  const insets = useSafeAreaInsets();
  return Math.max(insets.bottom, spacing.xs) + BOTTOM_GAP;
}

/** Vertical space the floating pill occupies from the screen bottom (pill + gap + safe-area inset). */
export function useTabBarHeight() {
  return PILL_HEIGHT + usePillBottom();
}

/** Bottom padding a tab screen needs so the bar never covers its content. */
export function useTabBarClearance() {
  return useTabBarHeight() + spacing.md;
}

type IconProps = {
  active: boolean;
  tab: Tab;
};

const ICON = 26;
const TAB_ICONS: Record<Tab, IconName> = { explore: 'map', guide: 'chats', home: 'home', trips: 'bookmarks' };

/**
 * Inactive: ink line icon. Active: filled white icon on a pale ACTIVE_BG circle, following the owner's reference
 * screenshot. White on ACTIVE_BG is only ~1.6:1 (owner's explicit choice); the state is still marked by the circle
 * shape and the filled icon, and screen readers get the tab's selected state.
 */
function TabIcon({ active, tab }: IconProps) {
  return <Icon color={active ? colors.white : colors.ink} filled={active} name={TAB_ICONS[tab]} size={ICON} />;
}

export const HomeTabBar = memo(function HomeTabBar({ emitter, navigateToTab, state }: BottomTabBarProps) {
  const { t } = useTranslation();
  const { isSignedIn } = useAccount();
  const bottom = usePillBottom();
  const [gate, setGate] = useState<GateFeature | null>(null);
  const activeName = state.routes[state.index]?.name;

  function press(routeKey: string, tab: Tab, active: boolean) {
    const gated = gatedTabs[tab];
    if (gated && !isSignedIn) { setGate(gated); return; }
    const event = emitter.emit({ canPreventDefault: true, target: routeKey, type: 'tabPress' });
    if (!active && !event.defaultPrevented) navigateToTab(routeKey);
  }

  return (
    <View pointerEvents="box-none" style={[styles.bar, { bottom }]}>
      <View accessibilityLabel={t('tabs.navigation')} accessibilityRole="tablist" style={styles.pill}>
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
              <View style={[styles.circle, active && styles.circleActive]}>
                <TabIcon active={active} tab={tab} />
              </View>
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
    alignItems: 'center',
    left: 0,
    paddingHorizontal: spacing.xl,
    position: 'absolute',
    right: 0,
  },
  circle: { alignItems: 'center', borderRadius: CIRCLE / 2, height: CIRCLE, justifyContent: 'center', width: CIRCLE },
  circleActive: { backgroundColor: ACTIVE_BG },
  pill: {
    alignItems: 'center',
    backgroundColor: PILL_BG,
    borderRadius: radii.pill,
    elevation: 10,
    flexDirection: 'row',
    height: PILL_HEIGHT,
    maxWidth: 360,
    paddingHorizontal: PILL_PADDING,
    shadowColor: colors.ink,
    shadowOffset: { height: 10, width: 0 },
    shadowOpacity: 0.1,
    shadowRadius: 28,
    width: '100%',
  },
  pressed: { opacity: 0.7 },
  tab: { alignItems: 'center', flex: 1, justifyContent: 'center', minHeight: MIN_TOUCH, minWidth: MIN_TOUCH },
});
