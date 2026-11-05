import { useState } from 'react';
import { Text, View } from 'react-native';
import { router } from 'expo-router';
import { useAuth, useSignIn } from '@clerk/expo';
import { useTranslation } from 'react-i18next';
import { Action, AuthShell, BrandSymbol, Field, Heading, SocialActions, TextLink, s } from '../../features/auth/components/AuthUI';
import { authErrorMessage } from '../../features/auth/authErrors';
import { finishAuth } from '../../features/auth/finishAuth';

type Step = 'password' | 'email-code' | 'totp' | 'reset-code' | 'new-password';
export default function LoginScreen() {
  const { t } = useTranslation();
  const { isLoaded } = useAuth();
  const { signIn, fetchStatus } = useSignIn();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState<Step>('password');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const disabled = !isLoaded || busy || fetchStatus === 'fetching';
  async function run(action: () => Promise<void>) {
    if (disabled) return;
    setBusy(true); setNotice('');
    try { await action(); } catch (error) { setNotice(authErrorMessage(error)); }
    finally { setBusy(false); }
  }
  async function advance() {
    if (signIn.status === 'complete') {
      setPassword('');
      const { error } = await signIn.finalize({ navigate: finishAuth });
      if (error) throw error;
    } else if (signIn.status === 'needs_client_trust' || signIn.status === 'needs_second_factor') {
      if (signIn.supportedSecondFactors?.some(f => f.strategy === 'email_code')) {
        const { error } = await signIn.mfa.sendEmailCode();
        if (error) throw error;
        setCode(''); setStep('email-code');
      } else if (signIn.supportedSecondFactors?.some(f => f.strategy === 'totp')) {
        setCode(''); setStep('totp');
      } else setNotice(t('auth.login.notice.unsupportedFactor'));
    } else if (signIn.status === 'needs_new_password') {
      setPassword(''); setStep('new-password');
    } else setNotice(t('auth.login.notice.incomplete'));
  }
  function submit() { void run(async () => {
    if (step === 'password') {
      if (!email.trim() || !password) { setNotice(t('auth.login.notice.missingCredentials')); return; }
      const { error } = await signIn.password({ emailAddress: email.trim(), password });
      if (error) throw error;
    } else if (step === 'new-password') {
      const { error } = await signIn.resetPasswordEmailCode.submitPassword({ password, signOutOfOtherSessions: true });
      if (error) throw error;
    } else {
      if (!code.trim()) { setNotice(t('auth.login.notice.missingCode')); return; }
      const { error } = step === 'reset-code'
        ? await signIn.resetPasswordEmailCode.verifyCode({ code: code.trim() })
        : step === 'totp' ? await signIn.mfa.verifyTOTP({ code: code.trim() })
        : await signIn.mfa.verifyEmailCode({ code: code.trim() });
      if (error) throw error;
    }
    await advance();
  }); }
  function resetPassword() { void run(async () => {
    if (!email.trim()) { setNotice(t('auth.login.notice.missingEmail')); return; }
    const attempt = await signIn.create({ identifier: email.trim() });
    if (attempt.error) throw attempt.error;
    const { error } = await signIn.resetPasswordEmailCode.sendCode();
    if (error) throw error;
    setPassword(''); setCode(''); setStep('reset-code');
  }); }
  function resend() { void run(async () => {
    const { error } = step === 'reset-code' ? await signIn.resetPasswordEmailCode.sendCode() : await signIn.mfa.sendEmailCode();
    if (error) throw error;
    setNotice(t('auth.login.notice.codeSent'));
  }); }
  return <AuthShell back={() => router.canGoBack() ? router.back() : router.replace('/welcome')}>
    <BrandSymbol /><Heading title={t(step === 'password' ? 'auth.login.title.password' : step === 'new-password' ? 'auth.login.title.newPassword' : 'auth.login.title.verify')} subtitle={t(step === 'password' ? 'auth.login.subtitle.password' : step === 'totp' ? 'auth.login.subtitle.totp' : step === 'new-password' ? 'auth.login.subtitle.newPassword' : 'auth.login.subtitle.emailCode')} />
    {step === 'password' && <Field label={t('auth.login.email')} value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" editable={!disabled} />}
    {(step === 'password' || step === 'new-password') ? <Field label={t(step === 'new-password' ? 'auth.login.newPassword' : 'auth.login.password')} value={password} onChangeText={setPassword} password autoCapitalize="none" autoCorrect={false} autoComplete={step === 'new-password' ? 'new-password' : 'current-password'} onSubmitEditing={submit} editable={!disabled} /> : <Field label={t('auth.login.code')} value={code} onChangeText={setCode} keyboardType="number-pad" autoComplete="one-time-code" onSubmitEditing={submit} editable={!disabled} />}
    {step === 'password' && <View style={{ alignItems: 'flex-end' }}><TextLink title={t('auth.login.forgot')} onPress={resetPassword} /></View>}
    {!!notice && <Text accessibilityLiveRegion="polite" style={s.error}>{notice}</Text>}
    <Action title={t(disabled ? 'common.pleaseWait' : step === 'password' ? 'auth.login.submit.password' : step === 'new-password' ? 'auth.login.submit.newPassword' : 'auth.login.submit.verify')} disabled={disabled} onPress={submit} />
    {(step === 'email-code' || step === 'reset-code') && <TextLink title={t('auth.login.resend')} onPress={resend} />}
    {step !== 'password' && <TextLink title={t('auth.login.startAgain')} onPress={() => void run(async () => { await signIn.reset(); setCode(''); setPassword(''); setStep('password'); })} />}
    {step === 'password' && <><SocialActions divider /><TextLink title={t('auth.login.signUp')} onPress={() => router.replace('/register')} /></>}
    <TextLink title={t('auth.login.explore')} onPress={() => router.replace('/home')} />
  </AuthShell>;
}
