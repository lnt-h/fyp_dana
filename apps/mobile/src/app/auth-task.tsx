import { useState } from 'react';
import { useClerk } from '@clerk/expo';
import { router } from 'expo-router';
import { Text } from 'react-native';
import { Action, AuthShell, Heading, s } from '../features/auth/components/AuthUI';

export default function AuthTaskScreen() {
  const { signOut } = useClerk();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  return <AuthShell>
    <Heading title="One more step is needed" subtitle="Your account requires an additional setup step that this app does not support yet. Please contact support before continuing." />
    {!!notice && <Text accessibilityLiveRegion="polite" style={s.error}>{notice}</Text>}
    <Action title="Sign out and return" disabled={busy} onPress={async () => {
      setBusy(true);
      try { await signOut(); router.replace('/welcome'); }
      catch { setNotice('Could not sign out. Please try again.'); }
      finally { setBusy(false); }
    }} />
  </AuthShell>;
}
