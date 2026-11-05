import { useState } from 'react';
import { Keyboard, Pressable, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { PrimaryButton } from '../components/ui';
import { useAccount } from '../features/account/AccountContext';
import { AccountShell, a } from '../features/account/AccountUI';
import { Field, s } from '../features/auth/components/AuthUI';
import { authErrorMessage } from '../features/auth/authErrors';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';

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
  return <AccountShell title={t('account.editProfile.title')} lead={t('account.editProfile.intro')}>
    {isSignedIn ? <>
      <View style={[a.card, a.padded]}>
        <Field label={t('account.editProfile.name')} value={name} onChangeText={setName} autoComplete="name" autoCapitalize="words" editable={!busy} />
        <Text style={s.label}>{t('account.editProfile.email')}</Text>
        <Text style={[a.body, { color: colors.ink }]}>{profile.email}</Text>
        <Text style={[a.note, { textAlign: 'left', marginBottom: 0 }]}>{t('account.editProfile.emailNote')}</Text>
      </View>
      {!!notice && <Text accessibilityLiveRegion="polite" style={[s.error, { marginBottom: spacing.sm }]}>{notice}</Text>}
      <PrimaryButton label={t('account.editProfile.save')} loading={busy} onPress={() => void save()} />
      <Pressable accessibilityRole="button" onPress={close} style={({ pressed }) => [a.textButton, pressed && a.pressed]}>
        <Text style={a.textButtonLabel}>{t('common.cancel')}</Text>
      </Pressable>
    </> : <PrimaryButton label={t('account.editProfile.create')} onPress={() => router.push('/register')} />}
  </AccountShell>;
}
