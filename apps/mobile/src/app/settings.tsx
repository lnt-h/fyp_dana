import { useState } from 'react';
import { Switch, Text, View } from 'react-native';
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { useAccount } from '../features/account/AccountContext';
import { AccountRow, AccountShell, a } from '../features/account/AccountUI';
import { Action, TextLink, palette } from '../features/auth/components/AuthUI';

export default function SettingsScreen() {
  const { reduceMotion, setReduceMotion, clearSession, isSignedIn } = useAccount();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  function toggle(key: string) { setExpanded(expanded === key ? null : key); }
  return <AccountShell title="Settings">
    <Text style={[a.title, { marginBottom: 8 }]}>Feel at home.</Text>
    <Text style={[a.body, { marginBottom: 26 }]}>Small adjustments for a better journey.</Text>
    <Text style={a.section}>ACCESSIBILITY</Text>
    <View style={a.card}>
      <AccountRow icon="motion" title="Reduce motion" subtitle="Use simpler screen transitions. Your device’s accessibility preference is also respected."
        trailing={<Switch accessibilityLabel="Reduce motion" value={reduceMotion} onValueChange={setReduceMotion} trackColor={{ false: '#D7E3EA', true: palette.audioTeal }} />} />
    </View>
    <Text style={a.section}>PERSONALIZATION</Text>
    <View style={a.card}>
      <AccountRow icon="compass" title="Travel preferences" subtitle="Interests and travel type" onPress={() => router.push('/travel-preferences')} />
    </View>
    <Text style={a.section}>PRIVACY & ABOUT</Text>
    <View style={a.card}>
      <AccountRow icon="shield" title="Your data" subtitle="How your account details are stored" onPress={() => toggle('data')} />
      {expanded === 'data' && <Text style={[a.body, { paddingHorizontal: 20, paddingBottom: 20 }]}>Clerk manages account identity and authentication. Signed-in profile details and travel preferences are saved to your account. Guest preferences stay in memory until the app restarts. Account deletion is not available in this app yet.</Text>}
      <View style={a.divider} />
      <AccountRow icon="shield" title="Terms & privacy" onPress={() => toggle('legal')} />
      {expanded === 'legal' && <Text style={[a.body, { paddingHorizontal: 20, paddingBottom: 20 }]}>Terms of Service and Privacy Policy have not been published yet. This development version is for testing only.</Text>}
      <View style={a.divider} />
      <AccountRow icon="info" title="About Gonarra" subtitle={`Version ${Constants.expoConfig?.version ?? '1.0.0'}`} onPress={() => toggle('about')} />
      {expanded === 'about' && <Text style={[a.body, { paddingHorizontal: 20, paddingBottom: 20 }]}>Explore, plan and experience Da Nang. Gonarra brings local stories and travel inspiration together. You’re using a development version.</Text>}
    </View>
    <Text style={a.section}>THIS SESSION</Text>
    <View style={a.card}>
      <AccountRow icon="exit" title={isSignedIn ? 'Sign out' : 'Reset guest session'} subtitle="End this session on this device" onPress={() => setConfirmReset(true)} />
      {confirmReset && <View style={{ paddingHorizontal: 20, paddingBottom: 16 }}>
        <Text style={a.body}>Return to Welcome? Your saved account details will be kept. Guest preferences on this device will be cleared.</Text>
        {!!notice && <Text accessibilityLiveRegion="polite" style={a.body}>{notice}</Text>}
        <Action title={busy ? 'Please wait…' : 'Confirm and return to Welcome'} disabled={busy} onPress={async () => {
          if (busy) return;
          setBusy(true); setNotice('');
          try { await clearSession(); router.dismissAll(); router.replace('/welcome'); }
          catch { setNotice('Could not end the session. Please try again.'); }
          finally { setBusy(false); }
        }} />
        <TextLink title="Keep exploring" onPress={() => setConfirmReset(false)} />
      </View>}
    </View>
  </AccountShell>;
}
