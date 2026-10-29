import { useState } from 'react';
import { Keyboard, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useAccount } from '../features/account/AccountContext';
import { AccountShell, a } from '../features/account/AccountUI';
import { Action, Field, TextLink } from '../features/auth/components/AuthUI';

export default function EditProfileScreen() {
  const { profile, updateProfile, isPreviewProfile } = useAccount();
  const [name, setName] = useState(profile.name);
  const [email, setEmail] = useState(profile.email);
  function close() { Keyboard.dismiss(); router.canGoBack() ? router.back() : router.replace('/profile'); }
  return <AccountShell title="Edit profile">
    <Text style={[a.body, { marginBottom: 24 }]}>A familiar name for your next adventure.</Text>
    {isPreviewProfile ? <View style={[a.card, a.padded]}>
      <Field label="Full name" placeholder="Your name" value={name} onChangeText={setName} autoComplete="name" autoCapitalize="words" />
      <Field label="Email address" placeholder="you@example.com" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} />
      <Action title="Save changes" onPress={() => { updateProfile({ name: name.trim(), email: email.trim() }); close(); }} />
      <TextLink title="Cancel" onPress={close} />
    </View> : <Action title="Create an account" onPress={() => router.push('/register')} />}
    <Text style={a.note}>These details belong to your preview profile. No account or email address is verified.</Text>
  </AccountShell>;
}
