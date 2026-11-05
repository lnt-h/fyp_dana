import { useState } from 'react';
import { Switch, Text, View } from 'react-native';
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { useAccount } from '../features/account/AccountContext';
import { AccountRow, AccountShell, a } from '../features/account/AccountUI';
import { Action, TextLink, palette } from '../features/auth/components/AuthUI';

export default function SettingsScreen() {
  const { t } = useTranslation();
  const { reduceMotion, setReduceMotion, clearSession, isSignedIn } = useAccount();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  function toggle(key: string) { setExpanded(expanded === key ? null : key); }
  return <AccountShell title={t('account.settings.title')}>
    <Text style={[a.title, { marginBottom: 8 }]}>{t('account.settings.heading')}</Text>
    <Text style={[a.body, { marginBottom: 26 }]}>{t('account.settings.intro')}</Text>
    <Text style={a.section}>{t('account.settings.sectionAccessibility')}</Text>
    <View style={a.card}>
      <AccountRow icon="motion" title={t('account.settings.reduceMotion')} subtitle={t('account.settings.reduceMotionSubtitle')}
        trailing={<Switch accessibilityLabel={t('account.settings.reduceMotion')} value={reduceMotion} onValueChange={setReduceMotion} trackColor={{ false: '#D7E3EA', true: palette.audioTeal }} />} />
    </View>
    <Text style={a.section}>{t('account.settings.sectionPersonalization')}</Text>
    <View style={a.card}>
      <AccountRow icon="compass" title={t('account.settings.preferences')} subtitle={t('account.settings.preferencesSubtitle')} onPress={() => router.push('/travel-preferences')} />
    </View>
    <Text style={a.section}>{t('account.settings.sectionPrivacy')}</Text>
    <View style={a.card}>
      <AccountRow icon="shield" title={t('account.settings.data')} subtitle={t('account.settings.dataSubtitle')} onPress={() => toggle('data')} />
      {expanded === 'data' && <Text style={[a.body, { paddingHorizontal: 20, paddingBottom: 20 }]}>{t('account.settings.dataBody')}</Text>}
      <View style={a.divider} />
      <AccountRow icon="shield" title={t('account.settings.legal')} onPress={() => toggle('legal')} />
      {expanded === 'legal' && <Text style={[a.body, { paddingHorizontal: 20, paddingBottom: 20 }]}>{t('account.settings.legalBody')}</Text>}
      <View style={a.divider} />
      <AccountRow icon="info" title={t('account.settings.about')} subtitle={t('account.settings.version', { version: Constants.expoConfig?.version ?? '1.0.0' })} onPress={() => toggle('about')} />
      {expanded === 'about' && <Text style={[a.body, { paddingHorizontal: 20, paddingBottom: 20 }]}>{t('account.settings.aboutBody')}</Text>}
    </View>
    <Text style={a.section}>{t('account.settings.sectionSession')}</Text>
    <View style={a.card}>
      <AccountRow icon="exit" title={t(isSignedIn ? 'account.settings.signOut' : 'account.settings.resetGuest')} subtitle={t('account.settings.sessionSubtitle')} onPress={() => setConfirmReset(true)} />
      {confirmReset && <View style={{ paddingHorizontal: 20, paddingBottom: 16 }}>
        <Text style={a.body}>{t('account.settings.confirmBody')}</Text>
        {!!notice && <Text accessibilityLiveRegion="polite" style={a.body}>{notice}</Text>}
        <Action title={t(busy ? 'common.pleaseWait' : 'account.settings.confirm')} disabled={busy} onPress={async () => {
          if (busy) return;
          setBusy(true); setNotice('');
          try { await clearSession(); router.dismissAll(); router.replace('/welcome'); }
          catch { setNotice(t('account.settings.sessionFailed')); }
          finally { setBusy(false); }
        }} />
        <TextLink title={t('account.settings.keepExploring')} onPress={() => setConfirmReset(false)} />
      </View>}
    </View>
  </AccountShell>;
}
