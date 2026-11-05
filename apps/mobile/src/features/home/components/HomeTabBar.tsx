import { memo, useState } from 'react';
import { useAuth } from '@clerk/expo';
import type { BottomTabBarProps } from 'expo-router/js-tabs';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Icon, type IconName } from '../../../components/ui';

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

const ICON = 26;
const TAB_ICONS: Record<Tab, IconName> = { explore: 'compass', guide: 'chat-text', home: 'home', trips: 'suitcase' };

/** Shared Icon family: line when idle, filled ink when active (fill + label + dot, never colour alone). */
function TabIcon({ active, tab }: IconProps) {
  return <Icon color={active ? colors.ink : colors.textMuted} filled={active} name={TAB_ICONS[tab]} size={ICON} />;
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
