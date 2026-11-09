import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { useAuth, useSSO } from '@clerk/expo';
import { authErrorMessage } from '../authErrors';
import { finishAuth } from '../finishAuth';
import { Keyboard, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useTranslation } from 'react-i18next';
import Svg, { Circle, Path } from 'react-native-svg';
import { colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';
import { CircleButton, PrimaryButton } from '../../../components/ui';
import { ArrowIcon, ProviderIcon } from './AuthIcons';

export const palette = { ...colors, muted: colors.textSecondary, border: colors.hairline, error: colors.danger };

export function AuthShell({ children, back, step, skip, fitViewport = false }: { children: ReactNode; back?: () => void; step?: number; skip?: () => void; /** Fit one viewport at rest; the form scrolls only while the keyboard is open. */ fitViewport?: boolean }) {
  const insets = useSafeAreaInsets();
  const { t } = useTranslation();
  const [keyboardOpen, setKeyboardOpen] = useState(false);
  useEffect(() => {
    if (!fitViewport) return;
    const show = Keyboard.addListener('keyboardDidShow', () => setKeyboardOpen(true));
    const hide = Keyboard.addListener('keyboardDidHide', () => setKeyboardOpen(false));
    return () => { show.remove(); hide.remove(); };
  }, [fitViewport]);
  return (
    <KeyboardAvoidingView style={s.fill} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <StatusBar style="dark" />
      <ScrollView
        alwaysBounceVertical={false}
        bounces={false}
        scrollEnabled={!fitViewport || keyboardOpen}
        keyboardDismissMode={Platform.OS === 'ios' ? 'interactive' : 'on-drag'}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={[s.content, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 16 }]}
      >
        <View style={s.inner}>
          {back ? (
            <View style={s.nav}>
              <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={back} size={44} />
              {step ? (
                <View accessibilityLabel={t('auth.shell.step', { step, total: 3 })} style={s.steps}>
                  {[1, 2, 3].map(n => (
                    <View key={n} style={[s.step, n <= step && { backgroundColor: colors.primary }]} />
                  ))}
                </View>
              ) : null}
              {skip ? (
                <Pressable accessibilityRole="button" onPress={skip} style={s.touch}>
                  <Text style={s.link}>{t('auth.shell.skip')}</Text>
                </Pressable>
              ) : <View style={s.spacer} />}
            </View>
          ) : null}
          {children}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

export function BrandSymbol() {
  return null;
}

export function Heading({ title, subtitle, left = true }: { title: string; subtitle: string; left?: boolean }) {
  return (
    <View style={s.heading}>
      <Text accessibilityRole="header" style={[s.title, left && { textAlign: 'left' }]}>
        {title}
      </Text>
      <Text style={[s.subtitle, left && { textAlign: 'left' }]}>{subtitle}</Text>
    </View>
  );
}

export function Action({
  title,
  onPress,
  secondary = false,
  icon,
  arrow = false,
  disabled = false,
}: {
  title: string;
  onPress: () => void;
  secondary?: boolean;
  icon?: ReactNode;
  arrow?: boolean;
  disabled?: boolean;
}) {
  if (!secondary) {
    return (
      <View style={s.actionWrap}>
        <PrimaryButton disabled={disabled} label={title} onPress={onPress} />
      </View>
    );
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [s.action, s.secondary, (pressed || disabled) && { opacity: 0.65 }]}
    >
      <View style={s.actionContent}>
        {icon}
        <Text style={[s.actionText, { color: colors.ink }]}>{title}</Text>
        {arrow ? <ArrowIcon color={colors.ink} /> : null}
      </View>
    </Pressable>
  );
}

export function SocialActions({ divider = false }: { divider?: boolean }) {
  const { t } = useTranslation();
  const { isLoaded } = useAuth();
  const { startSSOFlow } = useSSO();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');

  async function authenticate(strategy: 'oauth_google' | 'oauth_apple') {
    if (busy || !isLoaded) return;
    setBusy(true);
    setNotice('');
    try {
      const result = await startSSOFlow({ strategy });
      if (result.createdSessionId && result.setActive) {
        await result.setActive({ session: result.createdSessionId, navigate: finishAuth });
      } else if (result.signUp?.status === 'missing_requirements') {
        setNotice(t('auth.social.missingRequirements'));
      } else if (result.authSessionResult?.type === 'success') {
        setNotice(t('auth.social.verificationRequired'));
      }
    } catch (error) {
      setNotice(authErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {divider ? (
        <View style={s.divider}>
          <View style={s.dividerLine} />
          <Text style={s.note}>{t('auth.social.divider')}</Text>
          <View style={s.dividerLine} />
        </View>
      ) : null}
      <Action
        disabled={busy || !isLoaded}
        icon={<ProviderIcon provider="apple" />}
        onPress={() => void authenticate('oauth_apple')}
        secondary
        title={t('auth.social.apple')}
      />
      <Action
        disabled={busy || !isLoaded}
        icon={<ProviderIcon provider="google" />}
        onPress={() => void authenticate('oauth_google')}
        secondary
        title={t('auth.social.google')}
      />
      {notice ? (
        <Text accessibilityLiveRegion="polite" style={s.error}>
          {notice}
        </Text>
      ) : null}
    </>
  );
}

function FieldIcon({ kind }: { kind: 'email' | 'password' | 'person' }) {
  const paths = {
    email: 'M3 5h18v14H3ZM3 6l9 7 9-7',
    password: 'M6 10h12v11H6ZM8 10V6a4 4 0 0 1 8 0v4',
    person: 'M8 7a4 4 0 1 0 8 0a4 4 0 1 0-8 0M4 22v-4a8 6 0 0 1 16 0v4',
  };
  return (
    <Svg aria-hidden={true} height={20} viewBox="0 0 24 24" width={20}>
      <Path
        d={paths[kind]}
        fill="none"
        stroke={colors.textSecondary}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.8}
      />
    </Svg>
  );
}

export function Field({
  label,
  error,
  password,
  placeholder,
  ...props
}: TextInputProps & { label: string; error?: string; password?: boolean }) {
  const { t } = useTranslation();
  const [visible, setVisible] = useState(false);
  return (
    <View style={s.fieldBlock}>
      <Text style={s.label}>{label}</Text>
      <View style={[s.field, !!error && { borderColor: colors.danger }]}>
        <FieldIcon kind={password ? 'password' : props.keyboardType === 'email-address' ? 'email' : 'person'} />
        <TextInput
          {...props}
          accessibilityLabel={label}
          autoComplete={props.autoComplete}
          placeholder={placeholder ?? label}
          placeholderTextColor={colors.textSecondary}
          secureTextEntry={password && !visible}
          style={s.input}
        />
        {password ? (
          <Pressable
            accessibilityLabel={t(visible ? 'auth.field.hidePassword' : 'auth.field.showPassword')}
            accessibilityRole="button"
            onPress={() => setVisible(!visible)}
            style={s.touch}
          >
            <Svg aria-hidden={true} height={20} viewBox="0 0 24 24" width={20}>
              <Path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z" fill="none" stroke={colors.textSecondary} strokeWidth={1.8} />
              <Circle cx={12} cy={12} fill="none" r={3} stroke={colors.textSecondary} strokeWidth={1.8} />
              {visible ? <Path d="M3 3l18 18" stroke={colors.textSecondary} strokeWidth={1.8} /> : null}
            </Svg>
          </Pressable>
        ) : null}
      </View>
      {error ? (
        <Text accessibilityLiveRegion="polite" style={s.error}>
          {error}
        </Text>
      ) : null}
    </View>
  );
}

export function TextLink({ title, onPress }: { title: string; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={s.textLink}>
      <Text style={s.link}>{title}</Text>
    </Pressable>
  );
}

export const s = StyleSheet.create({
  action: {
    alignItems: 'center',
    borderRadius: 14,
    justifyContent: 'center',
    marginTop: 10,
    minHeight: 52,
    overflow: 'hidden',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  actionContent: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 12,
    justifyContent: 'center',
    width: '100%',
  },
  actionText: {
    color: 'white',
    fontFamily: fonts.bold,
    fontSize: 16,
    lineHeight: 22,
    textAlign: 'center',
  },
  actionWrap: {
    marginTop: 12,
  },
  back: { color: colors.ink, fontSize: 36, lineHeight: 40 },
  content: { flexGrow: 1, paddingHorizontal: 24 },
  divider: { alignItems: 'center', flexDirection: 'row', gap: 14, marginVertical: 14 },
  dividerLine: { backgroundColor: colors.hairline, flex: 1, height: 1 },
  error: { color: colors.danger, fontFamily: fonts.regular, fontSize: 13, marginTop: 6 },
  field: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.hairline,
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    minHeight: 50,
    paddingHorizontal: 14,
  },
  fieldBlock: { marginBottom: 14 },
  fill: { backgroundColor: colors.white, flex: 1 },
  heading: { marginBottom: 20 },
  inner: { alignSelf: 'center', flex: 1, maxWidth: 460, width: '100%' },
  input: {
    color: colors.ink,
    flex: 1,
    fontFamily: fonts.medium,
    fontSize: 16,
    marginLeft: 10,
    minWidth: 0,
    paddingVertical: 12,
  },
  label: { color: colors.ink, fontFamily: fonts.semibold, fontSize: 13, marginBottom: 6 },
  link: { color: colors.primary, fontFamily: fonts.bold, fontSize: 15 },
  nav: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', marginBottom: 14 },
  note: { color: colors.textSecondary, fontFamily: fonts.regular, fontSize: 12, lineHeight: 18, textAlign: 'center' },
  secondary: { backgroundColor: colors.white, borderColor: colors.hairline, borderWidth: 1 },
  spacer: { height: 44, width: 44 },
  step: { backgroundColor: colors.hairline, borderRadius: 3, height: 4, width: 36 },
  steps: { flexDirection: 'row', gap: 6 },
  subtitle: {
    color: colors.textSecondary,
    fontFamily: fonts.regular,
    fontSize: 15,
    lineHeight: 22,
    marginTop: 6,
    textAlign: 'left',
  },
  textLink: { alignItems: 'center', justifyContent: 'center', minHeight: 44, paddingVertical: 8 },
  title: {
    color: colors.ink,
    fontFamily: fonts.bold,
    fontSize: 26,
    letterSpacing: -0.5,
    lineHeight: 32,
    textAlign: 'left',
  },
  touch: { alignItems: 'center', justifyContent: 'center', minHeight: 44, minWidth: 44 },
});
