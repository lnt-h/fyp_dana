import { useState } from 'react';
import { useClerk } from '@clerk/expo';
import { router } from 'expo-router';
import { Text } from 'react-native';
import { useTranslation } from 'react-i18next';
import { Action, AuthShell, Heading, s } from '../features/auth/components/AuthUI';

export default function AuthTaskScreen() {
  const { t } = useTranslation();
  const { signOut } = useClerk();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  return <AuthShell>
    <Heading title={t('auth.task.title')} subtitle={t('auth.task.subtitle')} />
    {!!notice && <Text accessibilityLiveRegion="polite" style={s.error}>{notice}</Text>}
    <Action title={t('auth.task.signOut')} disabled={busy} onPress={async () => {
      setBusy(true);
      try { await signOut(); router.replace('/welcome'); }
      catch { setNotice(t('auth.task.signOutFailed')); }
      finally { setBusy(false); }
    }} />
  </AuthShell>;
}
