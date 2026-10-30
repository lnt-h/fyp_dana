import { useState } from 'react';
import { Text, View } from 'react-native';
import { router } from 'expo-router';
import { useAuth, useSignUp } from '@clerk/expo';
import { Action, AuthShell, BrandSymbol, Field, Heading, SocialActions, TextLink, s } from '../../features/auth/components/AuthUI';
import { authErrorMessage } from '../../features/auth/authErrors';
import { authDestination } from '../../features/auth/finishAuth';

export default function RegisterScreen() {
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
      setNotice('Additional account information is required. Please check your details or try another sign-in method.'); return;
    }
    setPassword('');
    const { error } = await signUp.finalize({ navigate: authDestination('/travel-preferences') });
    if (error) throw error;
  }
  function submit() { void run(async () => {
    if (verifying) {
      if (!code.trim()) { setNotice('Enter the verification code.'); return; }
      const { error } = await signUp.verifications.verifyEmailCode({ code: code.trim() });
      if (error) throw error;
      await complete();
    } else {
      if (!name.trim() || !email.trim() || !password) { setNotice('Enter your name, email address and password.'); return; }
      const [firstName, ...lastName] = name.trim().split(/\s+/);
      const { error } = await signUp.password({ firstName, lastName: lastName.join(' '), emailAddress: email.trim(), password });
      if (error) throw error;
      if (signUp.status === 'complete') { await complete(); return; }
      setPassword(''); setVerifying(true);
      const sent = await signUp.verifications.sendEmailCode();
      if (sent.error) throw sent.error;
    }
  }); }
  return <AuthShell back={() => router.canGoBack() ? router.back() : router.replace('/welcome')}>
    <BrandSymbol /><Heading title={verifying ? 'Check your email' : 'Create your\nGonarra account'} subtitle={verifying ? `Enter the code sent to ${email.trim()}.` : 'Start exploring Da Nang your way.'} />
    {verifying ? <Field label="Verification code" value={code} onChangeText={setCode} keyboardType="number-pad" autoComplete="one-time-code" onSubmitEditing={submit} editable={!disabled} /> : <>
      <Field label="Full name" value={name} onChangeText={setName} autoComplete="name" autoCapitalize="words" editable={!disabled} />
      <Field label="Email address" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" editable={!disabled} />
      <Field label="Password" value={password} onChangeText={setPassword} password autoCapitalize="none" autoCorrect={false} autoComplete="new-password" onSubmitEditing={submit} editable={!disabled} />
      <Text style={s.note}>Use at least 15 characters for your password.</Text>
    </>}
    <View nativeID="clerk-captcha" />
    {!!notice && <Text accessibilityLiveRegion="polite" style={s.error}>{notice}</Text>}
    <Action title={disabled ? 'Please wait…' : verifying ? 'Verify email' : 'Create account'} disabled={disabled} onPress={submit} />
    {verifying ? <>
      <TextLink title="Resend code" onPress={() => void run(async () => { const { error } = await signUp.verifications.sendEmailCode(); if (error) throw error; setNotice('A new verification code has been sent.'); })} />
      <TextLink title="Use a different email" onPress={() => void run(async () => { await signUp.reset(); setVerifying(false); setCode(''); })} />
    </> : <SocialActions divider />}
    <TextLink title="Already have an account? Sign in" onPress={() => router.replace('/login')} />
  </AuthShell>;
}
