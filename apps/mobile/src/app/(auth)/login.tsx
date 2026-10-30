import { useState } from 'react';
import { Text, View } from 'react-native';
import { router } from 'expo-router';
import { useAuth, useSignIn } from '@clerk/expo';
import { Action, AuthShell, BrandSymbol, Field, Heading, SocialActions, TextLink, s } from '../../features/auth/components/AuthUI';
import { authErrorMessage } from '../../features/auth/authErrors';
import { finishAuth } from '../../features/auth/finishAuth';

type Step = 'password' | 'email-code' | 'totp' | 'reset-code' | 'new-password';
export default function LoginScreen() {
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
      } else setNotice('This account requires a verification method that is not supported here yet.');
    } else if (signIn.status === 'needs_new_password') {
      setPassword(''); setStep('new-password');
    } else setNotice('Sign-in is not complete. Please try again.');
  }
  function submit() { void run(async () => {
    if (step === 'password') {
      if (!email.trim() || !password) { setNotice('Enter your email address and password.'); return; }
      const { error } = await signIn.password({ emailAddress: email.trim(), password });
      if (error) throw error;
    } else if (step === 'new-password') {
      const { error } = await signIn.resetPasswordEmailCode.submitPassword({ password, signOutOfOtherSessions: true });
      if (error) throw error;
    } else {
      if (!code.trim()) { setNotice('Enter your verification code.'); return; }
      const { error } = step === 'reset-code'
        ? await signIn.resetPasswordEmailCode.verifyCode({ code: code.trim() })
        : step === 'totp' ? await signIn.mfa.verifyTOTP({ code: code.trim() })
        : await signIn.mfa.verifyEmailCode({ code: code.trim() });
      if (error) throw error;
    }
    await advance();
  }); }
  function resetPassword() { void run(async () => {
    if (!email.trim()) { setNotice('Enter your email address first.'); return; }
    const attempt = await signIn.create({ identifier: email.trim() });
    if (attempt.error) throw attempt.error;
    const { error } = await signIn.resetPasswordEmailCode.sendCode();
    if (error) throw error;
    setPassword(''); setCode(''); setStep('reset-code');
  }); }
  function resend() { void run(async () => {
    const { error } = step === 'reset-code' ? await signIn.resetPasswordEmailCode.sendCode() : await signIn.mfa.sendEmailCode();
    if (error) throw error;
    setNotice('A new verification code has been sent.');
  }); }
  return <AuthShell back={() => router.canGoBack() ? router.back() : router.replace('/welcome')}>
    <BrandSymbol /><Heading title={step === 'password' ? 'Welcome back' : step === 'new-password' ? 'Choose a new password' : 'Verify your identity'} subtitle={step === 'password' ? 'Sign in to continue your journey.' : step === 'totp' ? 'Enter the code from your authenticator app.' : step === 'new-password' ? 'Use a strong, unique password.' : 'Enter the verification code sent to your email.'} />
    {step === 'password' && <Field label="Email address" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" editable={!disabled} />}
    {(step === 'password' || step === 'new-password') ? <Field label={step === 'new-password' ? 'New password' : 'Password'} value={password} onChangeText={setPassword} password autoCapitalize="none" autoCorrect={false} autoComplete={step === 'new-password' ? 'new-password' : 'current-password'} onSubmitEditing={submit} editable={!disabled} /> : <Field label="Verification code" value={code} onChangeText={setCode} keyboardType="number-pad" autoComplete="one-time-code" onSubmitEditing={submit} editable={!disabled} />}
    {step === 'password' && <View style={{ alignItems: 'flex-end' }}><TextLink title="Forgot password?" onPress={resetPassword} /></View>}
    {!!notice && <Text accessibilityLiveRegion="polite" style={s.error}>{notice}</Text>}
    <Action title={disabled ? 'Please wait…' : step === 'password' ? 'Sign in' : step === 'new-password' ? 'Update password' : 'Verify'} disabled={disabled} onPress={submit} />
    {(step === 'email-code' || step === 'reset-code') && <TextLink title="Resend code" onPress={resend} />}
    {step !== 'password' && <TextLink title="Start again" onPress={() => void run(async () => { await signIn.reset(); setCode(''); setPassword(''); setStep('password'); })} />}
    {step === 'password' && <><SocialActions divider /><TextLink title="Don’t have an account? Sign up" onPress={() => router.replace('/register')} /></>}
    <TextLink title="Explore without an account →" onPress={() => router.replace('/home')} />
  </AuthShell>;
}
