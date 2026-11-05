import { useAuth, useSSO } from '@clerk/expo';
import type { SetActiveNavigate } from '@clerk/shared/types';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { useEffect, useRef, useState, type ComponentRef } from 'react';
import { useTranslation } from 'react-i18next';
import { AccessibilityInfo, ActivityIndicator, Animated, Easing, Modal, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Icon, type IconName } from '../../components/ui';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { colors } from '../../theme/colors';
import { fonts } from '../../theme/typography';
import { useIsOffline } from '../home/useNetwork';
import { authErrorMessage } from './authErrors';
import { ProviderIcon } from './components/AuthIcons';
import { Action, TextLink, palette } from './components/AuthUI';

export type GateFeature = 'trips' | 'guide' | 'plan' | 'search';

type Provider = 'oauth_google' | 'oauth_apple';

const ART: Record<GateFeature, IconName> = { guide: 'lantern', plan: 'sparkle', search: 'search', trips: 'calendar' };
const ENTER_MS = 220;

/**
 * After social sign-in the guest stays where they were (SCR-040: "the app returns to the feature that was tapped");
 * only a pending Clerk session task (e.g. accept terms) leaves the screen.
 */
const stayOnScreen: SetActiveNavigate = async ({ session }) => {
  if (session?.currentTask) router.push('/auth-task');
};

type Props = {
  /** Feature the guest tapped; `null` hides the gate. */
  feature: GateFeature | null;
  onClose: () => void;
  /** Called once a session becomes active while the gate is open (before `onClose`), e.g. to continue into the feature. */
  onSignedIn?: () => void;
};

/**
 * SCR-040 sign-in gate: modal sheet shown when a guest taps a private feature (S-3). Email goes to register (or the
 * sign-in link to login); Google/Apple run Clerk SSO in place and close the gate on success.
 */
export function SignInGate({ feature, onClose, onSignedIn }: Props) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const reduceMotion = useReducedMotion();
  const offline = useIsOffline();
  const { isLoaded, isSignedIn } = useAuth();
  const { startSSOFlow } = useSSO();
  const [busy, setBusy] = useState<Provider | null>(null);
  const [notice, setNotice] = useState('');
  // Keep the last feature while the sheet animates out so the title never blanks.
  const [shown, setShown] = useState<GateFeature>(feature ?? 'search');
  const titleRef = useRef<ComponentRef<typeof Text>>(null);
  const enter = useRef(new Animated.Value(0)).current;
  const visible = feature !== null;

  useEffect(() => {
    if (feature) setShown(feature);
  }, [feature]);

  // Fresh state per opening; slide/fade in (≤ 220 ms, none under reduced motion); move screen-reader focus to the title.
  useEffect(() => {
    if (!visible) return;
    setNotice('');
    setBusy(null);
    enter.setValue(reduceMotion ? 1 : 0);
    if (!reduceMotion) {
      Animated.timing(enter, { duration: ENTER_MS, easing: Easing.out(Easing.cubic), toValue: 1, useNativeDriver: true }).start();
    }
    const timer = setTimeout(() => {
      if (titleRef.current) AccessibilityInfo.sendAccessibilityEvent(titleRef.current, 'focus');
    }, ENTER_MS + 30);
    return () => clearTimeout(timer);
  }, [enter, reduceMotion, visible]);

  // Signed in (SSO here, or a session that appeared meanwhile): close and let the caller continue.
  const callbacks = useRef({ onClose, onSignedIn });
  callbacks.current = { onClose, onSignedIn };
  useEffect(() => {
    if (visible && isSignedIn) {
      callbacks.current.onSignedIn?.();
      callbacks.current.onClose();
    }
  }, [isSignedIn, visible]);

  const disabled = offline || !isLoaded || busy !== null;

  async function social(strategy: Provider) {
    if (disabled) return;
    setBusy(strategy);
    setNotice('');
    try {
      const result = await startSSOFlow({ strategy });
      if (result.createdSessionId && result.setActive) {
        await result.setActive({ navigate: stayOnScreen, session: result.createdSessionId });
      } else if (result.signUp?.status === 'missing_requirements') {
        setNotice(t('auth.social.missingRequirements'));
      } else if (result.authSessionResult?.type === 'success') {
        setNotice(t('auth.social.verificationRequired'));
      }
    } catch (error) {
      setNotice(authErrorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  function go(path: '/register' | '/login') {
    onClose();
    router.push(path);
  }

  const sheetMotion = {
    opacity: enter,
    transform: [{ translateY: enter.interpolate({ inputRange: [0, 1], outputRange: [48, 0] }) }],
  };
  const spinner = <ActivityIndicator color={colors.deepOcean} />;

  return (
    <Modal animationType={reduceMotion ? 'none' : 'fade'} onRequestClose={onClose} statusBarTranslucent transparent visible={visible}>
      <View style={styles.backdrop}>
        <Pressable accessibilityElementsHidden importantForAccessibility="no" onPress={onClose} style={StyleSheet.absoluteFill} />
        <Animated.View
          accessibilityViewIsModal
          style={[styles.sheet, { paddingBottom: insets.bottom + 16 }, sheetMotion]}
        >
          <View style={styles.handle} />
          <GateArt icon={ART[shown]} />
          <Text accessibilityRole="header" ref={titleRef} style={styles.title}>{t(`auth.gate.title.${shown}`)}</Text>
          <View style={styles.privacy}>
            <Icon color={colors.tealText} name="check" size={18} />
            <Text style={styles.body}>{t('auth.gate.body')}</Text>
          </View>

          {offline ? (
            <View accessibilityLiveRegion="polite" accessibilityRole="alert" style={styles.offline}>
              <Icon color={colors.ink} name="info" size={20} />
              <Text style={styles.offlineText}>{t('auth.gate.offline')}</Text>
            </View>
          ) : null}

          <Action
            disabled={disabled}
            icon={<ProviderIcon provider="email" />}
            onPress={() => go('/register')}
            title={t('auth.gate.email')}
          />
          <Action
            disabled={disabled}
            icon={busy === 'oauth_google' ? spinner : <ProviderIcon provider="google" />}
            onPress={() => void social('oauth_google')}
            secondary
            title={busy === 'oauth_google' ? t('auth.gate.busy') : t('auth.social.google')}
          />
          {Platform.OS === 'ios' ? (
            <Action
              disabled={disabled}
              icon={busy === 'oauth_apple' ? spinner : <ProviderIcon provider="apple" />}
              onPress={() => void social('oauth_apple')}
              secondary
              title={busy === 'oauth_apple' ? t('auth.gate.busy') : t('auth.social.apple')}
            />
          ) : null}
          {notice ? <Text accessibilityLiveRegion="polite" accessibilityRole="alert" style={styles.error}>{notice}</Text> : null}

          <View style={styles.links}>
            <TextLink onPress={() => go('/login')} title={t('auth.gate.haveAccount')} />
            <Pressable accessibilityRole="button" onPress={onClose} style={styles.notNow}>
              <Text style={styles.notNowText}>{t('auth.gate.notNow')}</Text>
            </Pressable>
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
}

/** Feature glyph on a skyWash disc with the brand sun dot. Decorative. */
function GateArt({ icon }: { icon: IconName }) {
  return (
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.art}>
      <LinearGradient colors={[colors.skyWash, colors.white]} end={{ x: 0.8, y: 1 }} start={{ x: 0.2, y: 0 }} style={styles.artDisc}>
        <View style={styles.artInner}>
          <Icon color={colors.tealText} name={icon} size={34} strokeWidth={1.7} />
        </View>
      </LinearGradient>
      <View style={styles.sun} />
    </View>
  );
}

const styles = StyleSheet.create({
  art: { alignSelf: 'center', height: 96, marginBottom: 14, width: 96 },
  artDisc: { alignItems: 'center', borderRadius: 48, height: 96, justifyContent: 'center', width: 96 },
  artInner: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderColor: palette.border,
    borderRadius: 32,
    borderWidth: 1,
    height: 64,
    justifyContent: 'center',
    width: 64,
  },
  backdrop: { backgroundColor: 'rgba(7,21,30,0.45)', flex: 1, justifyContent: 'flex-end' },
  body: { color: colors.textMuted, flexShrink: 1, fontFamily: fonts.medium, fontSize: 15, lineHeight: 22 },
  error: { color: palette.error, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20, marginTop: 10, textAlign: 'center' },
  handle: { alignSelf: 'center', backgroundColor: colors.mutedDot, borderRadius: 3, height: 5, marginBottom: 18, width: 56 },
  links: { alignItems: 'center', marginTop: 6 },
  notNow: { alignItems: 'center', justifyContent: 'center', minHeight: 44, minWidth: 120, paddingHorizontal: 16 },
  notNowText: { color: colors.textMuted, fontFamily: fonts.bold, fontSize: 15 },
  offline: {
    alignItems: 'center',
    backgroundColor: colors.skyWash,
    borderRadius: 16,
    flexDirection: 'row',
    gap: 10,
    marginTop: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  offlineText: { color: colors.ink, flex: 1, fontFamily: fonts.medium, fontSize: 14, lineHeight: 20 },
  privacy: { alignItems: 'flex-start', alignSelf: 'center', flexDirection: 'row', gap: 8, marginBottom: 6, marginTop: 10, maxWidth: 360 },
  sheet: {
    alignSelf: 'center',
    backgroundColor: colors.white,
    borderTopLeftRadius: 40,
    borderTopRightRadius: 40,
    maxWidth: 520,
    paddingHorizontal: 24,
    paddingTop: 10,
    width: '100%',
  },
  sun: { backgroundColor: colors.sun, borderColor: colors.white, borderRadius: 9, borderWidth: 3, height: 18, position: 'absolute', right: 8, top: 6, width: 18 },
  title: { color: colors.deepOcean, fontFamily: fonts.bold, fontSize: 26, letterSpacing: -0.8, lineHeight: 31, textAlign: 'center' },
});
