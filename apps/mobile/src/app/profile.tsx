import { StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { useAccount } from '../features/account/AccountContext';
import { AccountIcon, AccountRow, AccountShell, a } from '../features/account/AccountUI';
import { Action, palette } from '../features/auth/components/AuthUI';

export default function ProfileScreen() {
  const { t } = useTranslation();
  const { profile, isSignedIn } = useAccount();
  const initials = profile.name.trim().split(/\s+/).filter(Boolean).slice(0, 2).map(word => word[0]).join('').toUpperCase();
  return <AccountShell title={t('account.profile.title')} fallback="/home">
    <View style={a.card}>
      <LinearGradient colors={['#DBF3F5', '#EDF7FD']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.cover}>
        <View style={styles.orbit} /><Text style={styles.kicker}>{t('account.profile.kicker')}</Text>
        <Text style={styles.coverTitle}>{t('account.profile.coverTitle')}</Text>
      </LinearGradient>
      <View style={styles.identity}>
        <View style={styles.avatar}>{initials ? <Text style={styles.initials}>{initials}</Text> : <AccountIcon name="person" />}</View>
        <View style={styles.badge}><Text style={styles.badgeText}>{t(isSignedIn ? 'account.profile.badgeAccount' : 'account.profile.badgeGuest')}</Text></View>
        <Text style={a.title}>{profile.name || t(isSignedIn ? 'account.profile.fallbackName' : 'account.profile.guestName')}</Text>
        <Text style={a.body}>{isSignedIn ? profile.email || t('account.profile.fallbackEmail') : t('account.profile.guestBody')}</Text>
        <Action secondary={isSignedIn} title={t(isSignedIn ? 'account.profile.edit' : 'account.profile.create')} onPress={() => router.push(isSignedIn ? '/edit-profile' : '/register')} />
      </View>
    </View>
    <Text style={a.section}>{t('account.profile.sectionExplore')}</Text>
    <View style={a.card}>
      <AccountRow icon="compass" title={t('account.profile.preferences')} subtitle={profile.interests.length ? profile.interests.map(value => t(`account.preferences.interests.${value}`)).join(' · ') : t('account.profile.preferencesEmpty')} onPress={() => router.push('/travel-preferences')} />
      <View style={styles.tags}><View style={styles.tag}><Text style={styles.tagText}>{profile.travelType ? t(`account.preferences.travelTypes.${profile.travelType}`) : t('account.profile.travelTypeEmpty')}</Text></View></View>
    </View>
    <Text style={a.section}>{t('account.profile.sectionHome')}</Text>
    <View style={a.card}>
      <AccountRow icon="settings" title={t('account.profile.settings')} subtitle={t('account.profile.settingsSubtitle')} onPress={() => router.push('/settings')} />
    </View>
    <Text style={a.note}>{t(isSignedIn ? 'account.profile.noteAccount' : 'account.profile.noteGuest')}</Text>
  </AccountShell>;
}
const styles = StyleSheet.create({
  cover: { padding: 24, paddingBottom: 45, overflow: 'hidden' },
  orbit: { width: 160, height: 160, borderRadius: 80, borderWidth: 26, borderColor: '#FFFFFF70', position: 'absolute', right: -40, top: -54 },
  kicker: { fontSize: 10, fontFamily: 'HankenGrotesk_700Bold', letterSpacing: 2, color: palette.tealText },
  coverTitle: { fontSize: 24, fontFamily: 'HankenGrotesk_700Bold', color: palette.deepOcean, marginTop: 9 },
  identity: { padding: 22, paddingTop: 42 },
  avatar: { position: 'absolute', left: 22, top: -30, width: 60, height: 60, borderRadius: 22, backgroundColor: palette.skyWash, borderWidth: 4, borderColor: palette.white, alignItems: 'center', justifyContent: 'center' },
  initials: { fontSize: 21, fontFamily: 'HankenGrotesk_700Bold', color: palette.tealText },
  badge: { alignSelf: 'flex-end', marginBottom: 12 }, badgeText: { fontSize: 9, letterSpacing: 1.4, color: palette.tealText, fontFamily: 'HankenGrotesk_700Bold' },
  tags: { paddingHorizontal: 18, paddingBottom: 18, flexDirection: 'row' },
  tag: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 10, backgroundColor: '#FFF5E4' },
  tagText: { color: '#845717', fontSize: 12, fontFamily: 'HankenGrotesk_700Bold' },
});
