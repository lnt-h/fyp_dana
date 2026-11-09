import { useState } from 'react';
import { Text, View } from 'react-native';
import { router } from 'expo-router';
import { useAuth, useSignUp } from '@clerk/expo';
import { useTranslation } from 'react-i18next';
import { Action, AuthShell, BrandSymbol, Field, Heading, SocialActions, TextLink, s } from '../../features/auth/components/AuthUI';
import { authErrorMessage } from '../../features/auth/authErrors';
import { authDestination } from '../../features/auth/finishAuth';

export default function RegisterScreen() {
  const { t } = useTranslation();
  const { isLoaded } = useAuth();
  const { signUp, fetchStatus } = useSignUp();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const disabled = !isLoaded || busy || fetchStatus === 'fetching';
  async function run(action: () => Promise<void>) {
    if (disabled) return;
    setBusy(true); setNotice('');
    try { await action(); } catch (error) { setNotice(authErrorMessage(error)); }
    finally { setBusy(false); }
  }
  async function complete() {
    if (signUp.status !== 'complete') {
      setNotice(t('auth.register.notice.incomplete')); return;
    }
    setPassword('');
    const { error } = await signUp.finalize({ navigate: authDestination('/travel-preferences') });
    if (error) throw error;
  }
  function submit() { void run(async () => {
    if (verifying) {
      if (!code.trim()) { setNotice(t('auth.register.notice.missingCode')); return; }
      const { error } = await signUp.verifications.verifyEmailCode({ code: code.trim() });
      if (error) throw error;
      await complete();
    } else {
      if (!name.trim() || !email.trim() || !password) { setNotice(t('auth.register.notice.missingFields')); return; }
      const [firstName, ...lastName] = name.trim().split(/\s+/);
      const { error } = await signUp.password({ firstName, lastName: lastName.join(' '), emailAddress: email.trim(), password });
      if (error) throw error;
      if (signUp.status === 'complete') { await complete(); return; }
      setPassword(''); setVerifying(true);
      const sent = await signUp.verifications.sendEmailCode();
      if (sent.error) throw sent.error;
    }
  }); }
  return <AuthShell back={() => router.canGoBack() ? router.back() : router.replace('/welcome')} fitViewport>
    <BrandSymbol /><Heading title={t(verifying ? 'auth.register.titleVerify' : 'auth.register.title')} subtitle={verifying ? t('auth.register.subtitleVerify', { email: email.trim() }) : t('auth.register.subtitle')} />
    {verifying ? <Field label={t('auth.register.code')} value={code} onChangeText={setCode} keyboardType="number-pad" autoComplete="one-time-code" onSubmitEditing={submit} editable={!disabled} /> : <>
      <Field label={t('auth.register.name')} value={name} onChangeText={setName} autoComplete="name" autoCapitalize="words" editable={!disabled} />
      <Field label={t('auth.register.email')} value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" editable={!disabled} />
      <Field label={t('auth.register.password')} value={password} onChangeText={setPassword} password autoCapitalize="none" autoCorrect={false} autoComplete="new-password" onSubmitEditing={submit} editable={!disabled} />
      <Text style={s.note}>{t('auth.register.passwordHint')}</Text>
    </>}
    <View nativeID="clerk-captcha" />
    {!!notice && <Text accessibilityLiveRegion="polite" style={s.error}>{notice}</Text>}
    <Action title={t(disabled ? 'common.pleaseWait' : verifying ? 'auth.register.submitVerify' : 'auth.register.submit')} disabled={disabled} onPress={submit} />
    {verifying ? <>
      <TextLink title={t('auth.register.resend')} onPress={() => void run(async () => { const { error } = await signUp.verifications.sendEmailCode(); if (error) throw error; setNotice(t('auth.register.notice.codeSent')); })} />
      <TextLink title={t('auth.register.differentEmail')} onPress={() => void run(async () => { await signUp.reset(); setVerifying(false); setCode(''); })} />
    </> : <SocialActions divider />}
    <TextLink title={t('auth.register.signIn')} onPress={() => router.replace('/login')} />
  </AuthShell>;
}
