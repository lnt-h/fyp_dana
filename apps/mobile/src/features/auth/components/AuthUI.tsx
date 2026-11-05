import type { ReactNode } from 'react';
import { useState } from 'react';
import { useAuth, useSSO } from '@clerk/expo';
import { authErrorMessage } from '../authErrors';
import { finishAuth } from '../finishAuth';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { useTranslation } from 'react-i18next';
import Svg, { Circle, Path } from 'react-native-svg';
import { colors } from '../../../theme/colors';
import { ArrowIcon, ProviderIcon } from './AuthIcons';

export const palette = { ...colors, muted: colors.textMuted, border: '#DCE8EE', error: '#AF3434' };
export function AuthShell({ children, back, step, skip }: { children: ReactNode; back?: () => void; step?: number; skip?: () => void }) {
  const insets = useSafeAreaInsets();
  const { t } = useTranslation();
  return <KeyboardAvoidingView style={s.fill} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
    <StatusBar style="dark" />
    <View pointerEvents="none" style={s.background}>
      <LinearGradient colors={['#D8F2FF', '#F8FCFD']} style={StyleSheet.absoluteFill} />
      <Svg width="100%" height={70} viewBox="0 0 440 70" preserveAspectRatio="none" style={{ position: 'absolute', bottom: -1 }}>
        <Path d="M0 40C100 0 160 5 230 32C315 65 360 62 440 30V70H0Z" fill="white" />
      </Svg>
    </View>
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={[s.content, { paddingTop: insets.top + 12, paddingBottom: insets.bottom + 24 }]}>
      <View style={s.inner}>
        {back && <View style={s.nav}>
          <Pressable accessibilityRole="button" accessibilityLabel={t('common.goBack')} onPress={back} style={s.touch}><ArrowIcon back color={colors.deepOcean} /></Pressable>
          {step && <View accessibilityLabel={t('auth.shell.step', { step, total: 3 })} style={s.steps}>{[1, 2, 3].map(n => <View key={n} style={[s.step, n <= step && { backgroundColor: colors.audioTeal }]} />)}</View>}
          {skip ? <Pressable accessibilityRole="button" onPress={skip} style={s.touch}><Text style={s.link}>{t('auth.shell.skip')}</Text></Pressable> : <View style={s.touch} />}
        </View>}
        {children}
      </View>
    </ScrollView>
  </KeyboardAvoidingView>;
}
export function BrandSymbol() {
  return <View style={s.symbol} aria-hidden={true}><Svg width={64} height={76} viewBox="0 0 80 94"><Path d="M57 36a23 23 0 1 1-46 0a23 23 0 1 1 46 0M57 25v38c0 27-26 32-43 19" fill="none" stroke={colors.deepOcean} strokeWidth={13} strokeLinecap="round" /><Circle cx={72} cy={9} r={7} fill={colors.sun} /></Svg></View>;
}
export function Heading({ title, subtitle, left = false }: { title: string; subtitle: string; left?: boolean }) {
  return <View style={s.heading}><Text accessibilityRole="header" style={[s.title, left && { textAlign: 'left' }]}>{title}</Text><Text style={[s.subtitle, left && { textAlign: 'left' }]}>{subtitle}</Text></View>;
}
export function Action({ title, onPress, secondary = false, icon, arrow = false, disabled = false }: { title: string; onPress: () => void; secondary?: boolean; icon?: ReactNode; arrow?: boolean; disabled?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={onPress} style={({ pressed }) => [s.action, secondary && s.secondary, (pressed || disabled) && { opacity: 0.55 }]}>
    {!secondary && <LinearGradient colors={[colors.deepOcean, '#105B70']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />}
    <View style={s.actionContent}>{icon}<Text style={[s.actionText, secondary && { color: colors.deepOcean }]}>{title}</Text>{arrow && <ArrowIcon color={secondary ? colors.deepOcean : colors.white} />}</View>
  </Pressable>;
}
export function SocialActions({ divider = false }: { divider?: boolean }) {
  const { t } = useTranslation();
  const { isLoaded } = useAuth();
  const { startSSOFlow } = useSSO();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  async function authenticate(strategy: 'oauth_google' | 'oauth_apple') {
    if (busy || !isLoaded) return;
    setBusy(true); setNotice('');
    try {
      const result = await startSSOFlow({ strategy });
      if (result.createdSessionId && result.setActive) {
        await result.setActive({ session: result.createdSessionId, navigate: finishAuth });
      } else if (result.signUp?.status === 'missing_requirements') {
        setNotice(t('auth.social.missingRequirements'));
      } else if (result.authSessionResult?.type === 'success') {
        setNotice(t('auth.social.verificationRequired'));
      }
    } catch (error) { setNotice(authErrorMessage(error)); }
    finally { setBusy(false); }
  }
  return <>
    {divider && <View style={s.divider}><View style={s.dividerLine} /><Text style={s.note}>{t('auth.social.divider')}</Text><View style={s.dividerLine} /></View>}
    <Action secondary disabled={busy || !isLoaded} title={t('auth.social.google')} icon={<ProviderIcon provider="google" />} onPress={() => void authenticate('oauth_google')} />
    <Action secondary disabled={busy || !isLoaded} title={t('auth.social.apple')} icon={<ProviderIcon provider="apple" />} onPress={() => void authenticate('oauth_apple')} />
    {!!notice && <Text accessibilityLiveRegion="polite" style={s.error}>{notice}</Text>}
  </>;
}
function FieldIcon({ kind }: { kind: 'email' | 'password' | 'person' }) {
  const paths = {
    email: 'M3 5h18v14H3ZM3 6l9 7 9-7',
    password: 'M6 10h12v11H6ZM8 10V6a4 4 0 0 1 8 0v4',
    person: 'M8 7a4 4 0 1 0 8 0a4 4 0 1 0-8 0M4 22v-4a8 6 0 0 1 16 0v4',
  };
  return <Svg width={21} height={24} viewBox="0 0 24 24" aria-hidden={true}><Path d={paths[kind]} fill="none" stroke={colors.deepOcean} strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" /></Svg>;
}

export function Field({ label, error, password, placeholder, ...props }: TextInputProps & { label: string; error?: string; password?: boolean }) {
  const { t } = useTranslation();
  const [visible, setVisible] = useState(false);
  return <View style={s.fieldBlock}><Text style={s.label}>{label}</Text><View style={[s.field, !!error && { borderColor: palette.error }]}>
    <FieldIcon kind={password ? 'password' : props.keyboardType === 'email-address' ? 'email' : 'person'} />
    <TextInput {...props} accessibilityLabel={label} secureTextEntry={password && !visible} placeholder={placeholder ?? label} placeholderTextColor={palette.muted} style={s.input} />
    {password && <Pressable accessibilityRole="button" accessibilityLabel={t(visible ? 'auth.field.hidePassword' : 'auth.field.showPassword')} onPress={() => setVisible(!visible)} style={s.touch}><Svg width={23} height={23} viewBox="0 0 24 24" aria-hidden={true}>
      <Path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z" fill="none" stroke={colors.deepOcean} strokeWidth={1.7} />
      <Circle cx={12} cy={12} r={3} fill="none" stroke={colors.deepOcean} strokeWidth={1.7} />
      {visible && <Path d="M3 3l18 18" stroke={colors.deepOcean} strokeWidth={1.7} />}
    </Svg></Pressable>}
  </View>{error && <Text accessibilityLiveRegion="polite" style={s.error}>{error}</Text>}</View>;
}
export function TextLink({ title, onPress }: { title: string; onPress: () => void }) {
  return <Pressable accessibilityRole="button" onPress={onPress} style={s.textLink}><Text style={s.link}>{title}</Text></Pressable>;
}
export const s = StyleSheet.create({
  fill: { flex: 1, backgroundColor: 'white' }, background: { position: 'absolute', top: 0, left: 0, right: 0, height: 350 },
  content: { flexGrow: 1, paddingHorizontal: 24 }, inner: { width: '100%', maxWidth: 480, alignSelf: 'center', flex: 1 },
  nav: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }, touch: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' }, back: { fontSize: 42, color: colors.deepOcean, lineHeight: 44 },
  steps: { flexDirection: 'row', gap: 8 }, step: { width: 42, height: 5, borderRadius: 5, backgroundColor: palette.border },
  symbol: { alignItems: 'center', marginTop: 12, marginBottom: 20 }, heading: { marginBottom: 24 }, title: { color: colors.deepOcean, fontSize: 30, lineHeight: 35, fontFamily: 'HankenGrotesk_700Bold', textAlign: 'center', letterSpacing: -0.8 }, subtitle: { color: palette.muted, fontSize: 16, lineHeight: 24, fontFamily: 'HankenGrotesk_500Medium', textAlign: 'center', marginTop: 10 },
  actionContent: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12, width: '100%' },
  divider: { flexDirection: 'row', alignItems: 'baseline', gap: 14, marginBottom: 4 }, dividerLine: { height: 1, backgroundColor: palette.border, flex: 1 },
  action: { minHeight: 56, borderRadius: 22, overflow: 'hidden', justifyContent: 'center', alignItems: 'center', marginTop: 12, padding: 16 }, actionText: { color: 'white', fontSize: 17, fontFamily: 'HankenGrotesk_700Bold', textAlign: 'center', flexShrink: 1 }, secondary: { borderWidth: 1.5, borderColor: palette.border, backgroundColor: 'white' },
  fieldBlock: { marginBottom: 16 }, label: { fontSize: 13, fontWeight: '600', color: colors.deepOcean, marginBottom: 7 }, field: { flexDirection: 'row', alignItems: 'center', minHeight: 58, borderWidth: 1.5, borderColor: palette.border, borderRadius: 17, backgroundColor: 'white', paddingHorizontal: 16 }, input: { flex: 1, minWidth: 0, marginLeft: 12, fontSize: 16, color: colors.deepOcean, paddingVertical: 16 }, error: { fontSize: 13, color: palette.error, marginTop: 6 },
  link: { color: colors.tealText, fontWeight: '700', fontSize: 15 }, textLink: { minHeight: 44, justifyContent: 'center', alignItems: 'center', paddingVertical: 10 }, note: { color: palette.muted, fontSize: 12, lineHeight: 18, textAlign: 'center', marginTop: 18 },
});
