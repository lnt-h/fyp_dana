import { useState } from 'react';
import { Keyboard, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { useAccount } from '../features/account/AccountContext';
import { AccountShell, a } from '../features/account/AccountUI';
import { Action, Field, TextLink, s } from '../features/auth/components/AuthUI';
import { authErrorMessage } from '../features/auth/authErrors';

export default function EditProfileScreen() {
  const { t } = useTranslation();
  const { profile, updateProfile, isSignedIn } = useAccount();
  const [name, setName] = useState(profile.name);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  function close() { Keyboard.dismiss(); router.canGoBack() ? router.back() : router.replace('/profile'); }
  async function save() {
    if (busy) return;
    if (!name.trim()) { setNotice(t('account.editProfile.missingName')); return; }
    setBusy(true); setNotice('');
    try { await updateProfile({ name: name.trim() }); close(); }
    catch (error) { setNotice(authErrorMessage(error)); }
    finally { setBusy(false); }
  }
  return <AccountShell title={t('account.editProfile.title')}>
    <Text style={[a.body, { marginBottom: 24 }]}>{t('account.editProfile.intro')}</Text>
    {isSignedIn ? <View style={[a.card, a.padded]}>
      <Field label={t('account.editProfile.name')} value={name} onChangeText={setName} autoComplete="name" autoCapitalize="words" editable={!busy} />
      <Text style={a.body}>{profile.email}</Text>
      <Text style={a.note}>{t('account.editProfile.emailNote')}</Text>
      {!!notice && <Text accessibilityLiveRegion="polite" style={s.error}>{notice}</Text>}
      <Action title={t(busy ? 'common.saving' : 'account.editProfile.save')} disabled={busy} onPress={() => void save()} />
      <TextLink title={t('common.cancel')} onPress={close} />
    </View> : <Action title={t('account.editProfile.create')} onPress={() => router.push('/register')} />}
  </AccountShell>;
}
