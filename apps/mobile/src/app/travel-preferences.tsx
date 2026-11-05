import { useState } from 'react';
import { Pressable, Text } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { PrimaryButton } from '../components/ui';
import { useAccount } from '../features/account/AccountContext';
import { AccountShell, a } from '../features/account/AccountUI';
import { TravelPreferences } from '../features/account/TravelPreferences';
import { authErrorMessage } from '../features/auth/authErrors';

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
  return <AccountShell title={t('account.preferences.title')} lead={t('account.preferences.intro')}>
    <TravelPreferences selected={selected} onSelect={setSelected} travelType={travelType} onTravelType={setTravelType} />
    {!!notice && <Text accessibilityLiveRegion="polite" style={a.error}>{notice}</Text>}
    <PrimaryButton label={t('account.preferences.save')} loading={busy} onPress={() => void save()} style={{ marginTop: 8 }} />
    <Pressable accessibilityRole="button" onPress={close} style={({ pressed }) => [a.textButton, pressed && a.pressed]}>
      <Text style={a.textButtonLabel}>{t('common.cancel')}</Text>
    </Pressable>
  </AccountShell>;
}
