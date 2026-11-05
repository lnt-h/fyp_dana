import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useReducedMotion } from '../../hooks/useReducedMotion';
import { colors } from '../../theme/colors';
import { Action, TextLink } from './components/AuthUI';

export type GateFeature = 'trips' | 'guide' | 'plan' | 'search';

/**
 * SCR-040 sign-in gate: a modal sheet shown when a guest taps a private feature (S-3). `feature` null = hidden.
 * Simplified for now: Sign in and Not now only (the full layout adds Email/Google/Apple, see screen-specs SCR-040).
 */
export function SignInGate({ feature, onClose }: { feature: GateFeature | null; onClose: () => void }) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const reduceMotion = useReducedMotion();
  return (
    <Modal animationType={reduceMotion ? 'none' : 'slide'} onRequestClose={onClose} transparent visible={feature !== null}>
      <View style={styles.backdrop}>
        <Pressable accessibilityElementsHidden importantForAccessibility="no" onPress={onClose} style={StyleSheet.absoluteFill} />
        <View accessibilityViewIsModal style={[styles.sheet, { paddingBottom: insets.bottom + 20 }]}>
          <View style={styles.handle} />
          {feature && <Text accessibilityRole="header" style={styles.title}>{t(`auth.gate.title.${feature}`)}</Text>}
          <Text style={styles.body}>{t('auth.gate.body')}</Text>
          <Action title={t('auth.gate.signIn')} onPress={() => { onClose(); router.push('/login'); }} />
          <TextLink title={t('auth.gate.notNow')} onPress={onClose} />
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { backgroundColor: 'rgba(7,21,30,0.35)', flex: 1, justifyContent: 'flex-end' },
  body: { color: colors.textMuted, fontFamily: 'HankenGrotesk_500Medium', fontSize: 16, lineHeight: 24, marginTop: 10, textAlign: 'center' },
  handle: { alignSelf: 'center', backgroundColor: '#C9C9C9', borderRadius: 2, height: 4, marginBottom: 22, width: 68 },
  sheet: { alignSelf: 'center', backgroundColor: colors.white, borderTopLeftRadius: 40, borderTopRightRadius: 40, maxWidth: 520, paddingHorizontal: 24, paddingTop: 10, width: '100%' },
  title: { color: colors.deepOcean, fontFamily: 'HankenGrotesk_700Bold', fontSize: 26, letterSpacing: -0.8, lineHeight: 31, textAlign: 'center' },
});
