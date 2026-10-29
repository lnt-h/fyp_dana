import { useState } from 'react';
import { Switch, Text, View } from 'react-native';
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { useAccount } from '../features/account/AccountContext';
import { AccountRow, AccountShell, a } from '../features/account/AccountUI';
import { Action, TextLink, palette } from '../features/auth/components/AuthUI';

export default function SettingsScreen() {
  const { reduceMotion, setReduceMotion, clearSession, isPreviewProfile } = useAccount();
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
      <AccountRow icon="shield" title="Your data" subtitle="How this preview handles your details" onPress={() => toggle('data')} />
      {expanded === 'data' && <Text style={[a.body, { paddingHorizontal: 20, paddingBottom: 20 }]}>Profile details and preferences stay in memory for this session. They are not sent to an account service and are cleared when the app restarts. Passwords are not added to your profile. No account has been created; account deletion is not available in this preview.</Text>}
      <View style={a.divider} />
      <AccountRow icon="shield" title="Terms & privacy" onPress={() => toggle('legal')} />
      {expanded === 'legal' && <Text style={[a.body, { paddingHorizontal: 20, paddingBottom: 20 }]}>Terms of Service and Privacy Policy have not been published yet. They will be available before real account registration opens.</Text>}
      <View style={a.divider} />
      <AccountRow icon="info" title="About Gonarra" subtitle={`Version ${Constants.expoConfig?.version ?? '1.0.0'}`} onPress={() => toggle('about')} />
      {expanded === 'about' && <Text style={[a.body, { paddingHorizontal: 20, paddingBottom: 20 }]}>Explore, plan and experience Da Nang. Gonarra brings local stories and travel inspiration together. You’re using an interactive preview.</Text>}
    </View>
    <Text style={a.section}>THIS SESSION</Text>
    <View style={a.card}>
      <AccountRow icon="exit" title={isPreviewProfile ? 'End preview session' : 'Reset preview'} subtitle="Clear profile details and preferences" onPress={() => setConfirmReset(true)} />
      {confirmReset && <View style={{ paddingHorizontal: 20, paddingBottom: 16 }}>
        <Text style={a.body}>Clear this session and return to Welcome? Your current profile and preferences will be removed from this preview.</Text>
        <Action title="Clear and return to Welcome" onPress={() => { clearSession(); router.dismissAll(); router.replace('/welcome'); }} />
        <TextLink title="Keep exploring" onPress={() => setConfirmReset(false)} />
      </View>}
    </View>
  </AccountShell>;
}
