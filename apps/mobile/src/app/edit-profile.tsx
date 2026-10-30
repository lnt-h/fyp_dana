import { useState } from 'react';
import { Keyboard, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useAccount } from '../features/account/AccountContext';
import { AccountShell, a } from '../features/account/AccountUI';
import { Action, Field, TextLink, s } from '../features/auth/components/AuthUI';
import { authErrorMessage } from '../features/auth/authErrors';

export default function EditProfileScreen() {
  const { profile, updateProfile, isSignedIn } = useAccount();
  const [name, setName] = useState(profile.name);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  function close() { Keyboard.dismiss(); router.canGoBack() ? router.back() : router.replace('/profile'); }
  async function save() {
    if (busy) return;
    if (!name.trim()) { setNotice('Enter your name.'); return; }
    setBusy(true); setNotice('');
    try { await updateProfile({ name: name.trim() }); close(); }
    catch (error) { setNotice(authErrorMessage(error)); }
    finally { setBusy(false); }
  }
  return <AccountShell title="Edit profile">
    <Text style={[a.body, { marginBottom: 24 }]}>A familiar name for your next adventure.</Text>
    {isSignedIn ? <View style={[a.card, a.padded]}>
      <Field label="Full name" value={name} onChangeText={setName} autoComplete="name" autoCapitalize="words" editable={!busy} />
      <Text style={a.body}>{profile.email}</Text>
      <Text style={a.note}>Your sign-in email is shown here for reference.</Text>
      {!!notice && <Text accessibilityLiveRegion="polite" style={s.error}>{notice}</Text>}
      <Action title={busy ? 'Saving…' : 'Save changes'} disabled={busy} onPress={() => void save()} />
      <TextLink title="Cancel" onPress={close} />
    </View> : <Action title="Create an account" onPress={() => router.push('/register')} />}
  </AccountShell>;
}
