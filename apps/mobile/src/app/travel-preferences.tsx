import { useState } from 'react';
import { Text } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { useAccount } from '../features/account/AccountContext';
import { AccountShell, a } from '../features/account/AccountUI';
import { TravelPreferences } from '../features/account/TravelPreferences';
import { authErrorMessage } from '../features/auth/authErrors';
import { Action, TextLink } from '../features/auth/components/AuthUI';

export default function TravelPreferencesScreen() {
  const { t } = useTranslation();
  const { profile, updateProfile } = useAccount();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [selected, setSelected] = useState(profile.interests);
  const [travelType, setTravelType] = useState(profile.travelType);
  function close() { router.canGoBack() ? router.back() : router.replace('/profile'); }
  async function save() {
    if (busy) return;
    setBusy(true); setNotice('');
    try { await updateProfile({ interests: selected, travelType }); close(); }
    catch (error) { setNotice(authErrorMessage(error)); }
    finally { setBusy(false); }
  }
  return <AccountShell title={t('account.preferences.title')}>
    <Text style={[a.body, { marginBottom: 20 }]}>{t('account.preferences.intro')}</Text>
    <TravelPreferences selected={selected} onSelect={setSelected} travelType={travelType} onTravelType={setTravelType} />
    {!!notice && <Text accessibilityLiveRegion="polite" style={a.body}>{notice}</Text>}
    <Action title={t(busy ? 'common.saving' : 'account.preferences.save')} disabled={busy} onPress={() => void save()} />
    <TextLink title={t('common.cancel')} onPress={close} />
  </AccountShell>;
}
