import { StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useAccount } from '../features/account/AccountContext';
import { AccountIcon, AccountRow, AccountShell, a } from '../features/account/AccountUI';
import { Action, palette } from '../features/auth/components/AuthUI';

export default function ProfileScreen() {
  const { profile, isSignedIn } = useAccount();
  const initials = profile.name.trim().split(/\s+/).filter(Boolean).slice(0, 2).map(word => word[0]).join('').toUpperCase();
  return <AccountShell title="Profile" fallback="/home">
    <View style={a.card}>
      <LinearGradient colors={['#DBF3F5', '#EDF7FD']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.cover}>
        <View style={styles.orbit} /><Text style={styles.kicker}>YOUR NEXT CHAPTER</Text>
        <Text style={styles.coverTitle}>A little more you.</Text>
      </LinearGradient>
      <View style={styles.identity}>
        <View style={styles.avatar}>{initials ? <Text style={styles.initials}>{initials}</Text> : <AccountIcon name="person" />}</View>
        <View style={styles.badge}><Text style={styles.badgeText}>{isSignedIn ? 'YOUR ACCOUNT' : 'EXPLORER'}</Text></View>
        <Text style={a.title}>{profile.name || (isSignedIn ? 'Your profile' : 'Hello, explorer')}</Text>
        <Text style={a.body}>{isSignedIn ? profile.email || 'Add your details to make it yours.' : 'Your Da Nang story is just beginning.'}</Text>
        <Action secondary={isSignedIn} title={isSignedIn ? 'Edit profile' : 'Create an account'} onPress={() => router.push(isSignedIn ? '/edit-profile' : '/register')} />
      </View>
    </View>
    <Text style={a.section}>YOUR WAY TO EXPLORE</Text>
    <View style={a.card}>
      <AccountRow icon="compass" title="Travel preferences" subtitle={profile.interests.length ? profile.interests.join(' · ') : 'Choose the things you love'} onPress={() => router.push('/travel-preferences')} />
      <View style={styles.tags}><View style={styles.tag}><Text style={styles.tagText}>{profile.travelType || 'Travel type not set'}</Text></View></View>
    </View>
    <Text style={a.section}>MAKE YOURSELF AT HOME</Text>
    <View style={a.card}>
      <AccountRow icon="settings" title="Settings" subtitle="Accessibility, privacy and app information" onPress={() => router.push('/settings')} />
    </View>
    <Text style={a.note}>{isSignedIn ? 'Your profile and preferences are saved to your account.' : 'Guest preferences are kept for this session only.'}</Text>
  </AccountShell>;
}
const styles = StyleSheet.create({
  cover: { padding: 24, paddingBottom: 45, overflow: 'hidden' },
  orbit: { width: 160, height: 160, borderRadius: 80, borderWidth: 26, borderColor: '#FFFFFF70', position: 'absolute', right: -40, top: -54 },
  kicker: { fontSize: 10, fontFamily: 'HankenGrotesk_700Bold', letterSpacing: 2, color: palette.audioTeal },
  coverTitle: { fontSize: 24, fontFamily: 'HankenGrotesk_700Bold', color: palette.deepOcean, marginTop: 9 },
  identity: { padding: 22, paddingTop: 42 },
  avatar: { position: 'absolute', left: 22, top: -30, width: 60, height: 60, borderRadius: 22, backgroundColor: palette.skyWash, borderWidth: 4, borderColor: palette.white, alignItems: 'center', justifyContent: 'center' },
  initials: { fontSize: 21, fontFamily: 'HankenGrotesk_700Bold', color: palette.audioTeal },
  badge: { alignSelf: 'flex-end', marginBottom: 12 }, badgeText: { fontSize: 9, letterSpacing: 1.4, color: palette.audioTeal, fontFamily: 'HankenGrotesk_700Bold' },
  tags: { paddingHorizontal: 18, paddingBottom: 18, flexDirection: 'row' },
  tag: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 10, backgroundColor: '#FFF5E4' },
  tagText: { color: '#845717', fontSize: 12, fontFamily: 'HankenGrotesk_700Bold' },
});
