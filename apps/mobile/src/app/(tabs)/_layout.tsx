import { memo, useState } from 'react';
import { Tabs, type BottomTabBarProps } from 'expo-router/js-tabs';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Icon, type IconName } from '../../components/ui';
import { useAccount } from '../../features/account/AccountContext';
import { SignInGate, type GateFeature } from '../../features/auth/SignInGate';
import { useTabBarHeight } from '../../features/home/components/HomeTabBar';
import { colors } from '../../theme/colors';
import { elevation } from '../../theme/elevation';
import { MIN_TOUCH, radii, spacing } from '../../theme/spacing';
import { fonts } from '../../theme/typography';

const tabs = ['home', 'explore', 'guide', 'trips'] as const;
type Tab = (typeof tabs)[number];
const isTab = (name: string): name is Tab => (tabs as readonly string[]).includes(name);

/** Tabs that are private features: guests see the sign-in gate instead (S-3, SCR-040). */
const gatedTabs: Partial<Record<Tab, GateFeature>> = { guide: 'guide', trips: 'trips' };
const TAB_ICONS: Record<Tab, IconName> = { explore: 'compass', guide: 'chats', home: 'home', trips: 'suitcase' };

/**
 * Same outer geometry as the previous floating pill (72 tall + gap + safe area), so `useTabBarHeight` /
 * `useTabBarClearance` in features/home/components/HomeTabBar stay correct for every tab screen.
 */
const PILL_HEIGHT = 72;
const PILL_PADDING = 6;

/**
 * Floating white tab bar (visual refresh 2026-11-09): icon + always-visible label per tab; the active tab is primary
 * teal with a filled icon and a soft teal pill behind it, so state is never colour-only. Labels scale up to 1.3×.
 */
const AppTabBar = memo(function AppTabBar({ emitter, navigateToTab, state }: BottomTabBarProps) {
  const { t } = useTranslation();
  const { isSignedIn } = useAccount();
  const insets = useSafeAreaInsets();
  const total = useTabBarHeight();
  const bottom = total - PILL_HEIGHT;
  const [gate, setGate] = useState<GateFeature | null>(null);
  const activeName = state.routes[state.index]?.name;

  function press(routeKey: string, tab: Tab, active: boolean) {
    const gated = gatedTabs[tab];
    if (gated && !isSignedIn) { setGate(gated); return; }
    const event = emitter.emit({ canPreventDefault: true, target: routeKey, type: 'tabPress' });
    if (!active && !event.defaultPrevented) navigateToTab(routeKey);
  }

  return <View pointerEvents="box-none" style={[styles.bar, { bottom: Math.max(bottom, insets.bottom) }]}>
    <View accessibilityLabel={t('tabs.navigation')} accessibilityRole="tablist" style={styles.pill}>
      {state.routes.map(route => {
        if (!isTab(route.name)) return null;
        const tab = route.name;
        const active = activeName === tab;
        const tint = active ? colors.primary : colors.textSecondary;
        return <Pressable
          accessibilityLabel={t(`tabs.${tab}`)}
          accessibilityRole="tab"
          accessibilityState={{ selected: active }}
          key={route.key}
          onPress={() => press(route.key, tab, active)}
          style={({ pressed }) => [styles.tab, pressed && styles.pressed]}
        >
          <View style={[styles.iconWrap, active && styles.iconWrapActive]}>
            <Icon color={tint} filled={active} name={TAB_ICONS[tab]} size={22} strokeWidth={active ? 2 : 1.8} />
          </View>
          <Text maxFontSizeMultiplier={1.3} numberOfLines={1} style={[styles.label, { color: tint }, active && styles.labelActive]}>{t(`tabs.${tab}`)}</Text>
        </Pressable>;
      })}
    </View>
    <SignInGate feature={gate} onClose={() => setGate(null)} />
  </View>;
});

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{ headerShown: false }} tabBar={props => <AppTabBar {...props} />}>
      <Tabs.Screen name="home" />
      <Tabs.Screen name="explore" />
      <Tabs.Screen name="guide" />
      <Tabs.Screen name="trips" />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  bar: { alignItems: 'center', left: 0, paddingHorizontal: spacing.md, position: 'absolute', right: 0 },
  iconWrap: { alignItems: 'center', borderRadius: radii.pill, height: 30, justifyContent: 'center', width: 52 },
  iconWrapActive: { backgroundColor: colors.primarySoft },
  label: { fontFamily: fonts.medium, fontSize: 12, lineHeight: 15, marginTop: 2 },
  labelActive: { fontFamily: fonts.bold },
  pill: {
    ...elevation.floating,
    alignItems: 'center',
    backgroundColor: colors.white,
    borderColor: colors.hairline,
    borderRadius: radii.pill,
    borderWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    height: PILL_HEIGHT,
    maxWidth: 420,
    paddingHorizontal: PILL_PADDING,
    width: '100%',
  },
  pressed: { opacity: 0.7 },
  tab: { alignItems: 'center', flex: 1, justifyContent: 'center', minHeight: MIN_TOUCH, minWidth: MIN_TOUCH, paddingVertical: 6 },
});
