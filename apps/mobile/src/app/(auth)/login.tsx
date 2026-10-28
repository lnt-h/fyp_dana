import { useState } from 'react';
import { Text, View } from 'react-native';
import { router } from 'expo-router';
import { Action, AuthShell, BrandSymbol, Field, Heading, PreviewNote, TextLink, s } from '../../features/auth/components/AuthUI';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [notice, setNotice] = useState('');
  function submit() { router.replace('/home'); }
  return <AuthShell back={() => router.canGoBack() ? router.back() : router.replace('/welcome')}>
    <BrandSymbol /><Heading title="Welcome back" subtitle="Sign in to continue your journey." />
    <Field label="Email address" placeholder="you@example.com" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" />
    <Field label="Password" placeholder="Enter your password" value={password} onChangeText={setPassword} password autoCapitalize="none" autoComplete="current-password" onSubmitEditing={submit} />
    <View style={{ alignItems: 'flex-end' }}><TextLink title="Forgot password?" onPress={() => setNotice('Password recovery will be available when account services are connected.')} /></View>
    <Action title="Sign In" onPress={submit} />
    {notice !== '' && <Text accessibilityLiveRegion="polite" style={s.note}>{notice}</Text>}
    <PreviewNote />
    <TextLink title="Don’t have an account? Sign up" onPress={() => router.replace('/register')} />
    <TextLink title="Explore as a guest →" onPress={() => router.replace('/home')} />
  </AuthShell>;
}
