import { useState } from 'react';
import { Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import Constants from 'expo-constants';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { PrimaryButton, SecondaryButton, Skeleton, StatCircle } from '../components/ui';
import { useAccount } from '../features/account/AccountContext';
import { AccountIcon, AccountRow, AccountShell, ExpandableRow, GroupCard, SectionLabel, SessionConfirm, a, errorColor } from '../features/account/AccountUI';
import { useTripStats } from '../features/account/useTripStats';
import { colors } from '../theme/colors';
import { elevation } from '../theme/elevation';
import { MIN_TOUCH, radii, spacing } from '../theme/spacing';
import { fonts, typography } from '../theme/typography';

/** SCR-009 Profile: identity, saved-trip stats and the account hub (fuller list lives in SCR-010 Settings). */
export default function ProfileScreen() {
  const { t, i18n } = useTranslation();
  const { profile, isSignedIn, reduceMotion, setReduceMotion } = useAccount();
  const stats = useTripStats(isSignedIn);
  const [confirming, setConfirming] = useState(false);
  const version = Constants.expoConfig?.version ?? '1.0.0';
  const name = isSignedIn ? profile.name || t('account.profile.fallbackName') : t('account.profile.guestName');
  const initial = (isSignedIn ? profile.name.trim() || profile.email : '').charAt(0).toUpperCase();
  const preferenceSummary = [
    ...profile.interests.map(value => t(`account.preferences.interests.${value}`)),
    ...(profile.travelType ? [t(`account.preferences.travelTypes.${profile.travelType}`)] : []),
  ].join(' · ');
  const languageName = t(`account.common.languageName.${i18n.language === 'vi' ? 'vi' : 'en'}`);

  return <AccountShell title={t('account.profile.title')} fallback="/home">
    <View style={[a.card, styles.identity]}>
      <LinearGradient colors={[colors.deepOcean, colors.tealDark]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.avatar}
        accessible accessibilityRole="image" accessibilityLabel={t('account.profile.avatarLabel', { name })}>
        {initial ? <Text style={styles.initial}>{initial}</Text> : <AccountIcon name="person" color={colors.white} size={30} />}
      </LinearGradient>
      <View style={styles.identityCopy}>
        <Text numberOfLines={1} style={styles.name}>{name}</Text>
        <Text numberOfLines={isSignedIn ? 1 : 3} style={styles.email}>{isSignedIn ? profile.email : t('account.profile.guestBody')}</Text>
      </View>
    </View>
    {!isSignedIn && <PrimaryButton label={t('account.profile.create')} variant="gradient" onPress={() => router.push('/register')} style={styles.create} />}

    {isSignedIn && <View accessibilityLabel={t('account.profile.statsLabel')} style={[a.card, styles.stats]}>
      {stats.status === 'ready' ? <View accessible accessibilityLabel={t('account.profile.statsA11y', stats.stats)} style={styles.statsRow}>
        <StatCircle icon="navigation" size={44} value={String(stats.stats.trips)} label={t('account.profile.statTrips')} style={styles.stat} />
        <View style={styles.statRule} />
        <StatCircle icon="map-pin" size={44} value={String(stats.stats.cities)} label={t('account.profile.statCities')} style={styles.stat} />
        <View style={styles.statRule} />
        <StatCircle icon="calendar" size={44} value={String(stats.stats.days)} label={t('account.profile.statDays')} style={styles.stat} />
      </View>
      : stats.status === 'error' ? <Text accessibilityLiveRegion="polite" style={[a.note, styles.statsError]}>{t('account.profile.statsUnavailable')}</Text>
      : <View style={styles.statsRow}>{[0, 1, 2].map(key => <View key={key} style={styles.statSkeleton}>
        <Skeleton width={44} height={44} radius={22} /><Skeleton width={36} height={22} radius={8} /><Skeleton width={64} height={12} radius={6} />
      </View>)}</View>}
    </View>}

    <SectionLabel>{t('account.profile.sectionAccount')}</SectionLabel>
    <GroupCard>
      {isSignedIn && <AccountRow icon="edit" title={t('account.profile.editProfile')} onPress={() => router.push('/edit-profile')} />}
      <AccountRow icon="sliders" title={t('account.profile.preferences')} subtitle={preferenceSummary || t('account.profile.preferencesEmpty')} onPress={() => router.push('/travel-preferences')} />
    </GroupCard>

    <SectionLabel>{t('account.profile.sectionOptions')}</SectionLabel>
    <GroupCard>
      <AccountRow icon="language" title={t('account.common.language')} value={languageName} onPress={() => router.push('/language')} />
      <AccountRow icon="motion" title={t('account.common.reduceMotion')}
        trailing={<Switch accessibilityLabel={t('account.common.reduceMotion')} value={reduceMotion} onValueChange={setReduceMotion} trackColor={{ false: '#D7E3EA', true: colors.audioTeal }} />} />
      <AccountRow icon="settings" title={t('account.profile.settings')} subtitle={t('account.profile.settingsSubtitle')} onPress={() => router.push('/settings')} />
    </GroupCard>

    <SectionLabel>{t('account.profile.sectionSupport')}</SectionLabel>
    <GroupCard>
      <ExpandableRow icon="sparkle" title={t('account.common.aiData')} body={t('account.common.aiDataBody')} />
      <ExpandableRow icon="doc" title={t('account.common.legal')} badge={t('account.common.legalDraft')} body={t('account.common.legalBody')} />
      <ExpandableRow icon="info" title={t('account.common.about')} subtitle={t('account.common.version', { version })} body={t('account.common.aboutBody')} />
    </GroupCard>

    {confirming ? <View style={a.card}><SessionConfirm onCancel={() => setConfirming(false)} /></View>
      : <SecondaryButton label={t(isSignedIn ? 'account.profile.signOut' : 'account.profile.resetGuest')} onPress={() => setConfirming(true)} style={styles.signOut} />}
    {isSignedIn && <Pressable accessibilityRole="button" accessibilityLabel={t('account.profile.deleteAccount')} onPress={() => router.push('/delete-account')}
      style={({ pressed }) => [styles.delete, pressed && a.pressed]}>
      <AccountIcon name="trash" color={errorColor} size={20} />
      <Text style={styles.deleteText}>{t('account.profile.deleteAccount')}</Text>
    </Pressable>}
    <Text style={a.note}>{t('account.profile.versionCaption', { version })}</Text>
  </AccountShell>;
}

const styles = StyleSheet.create({
  identity: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.lg },
  avatar: { width: 64, height: 64, borderRadius: 32, alignItems: 'center', justifyContent: 'center' },
  initial: { fontFamily: fonts.bold, fontSize: 28, color: colors.white },
  identityCopy: { flex: 1 },
  name: { ...typography.headline, color: colors.ink },
  email: { ...typography.caption, fontSize: 15, lineHeight: 21, marginTop: 2 },
  create: { marginTop: -spacing.xs, marginBottom: spacing.lg },
  stats: { paddingVertical: spacing.lg, paddingHorizontal: spacing.xs },
  statsRow: { flexDirection: 'row', alignItems: 'stretch' },
  stat: { flex: 1 },
  statRule: { width: StyleSheet.hairlineWidth, backgroundColor: '#D9E5EB', marginVertical: spacing.xs },
  statSkeleton: { flex: 1, alignItems: 'center', gap: spacing.xs },
  statsError: { marginVertical: 0 },
  signOut: { height: 56, borderRadius: radii.action, marginTop: spacing.xs, ...elevation.none },
  delete: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.xs, minHeight: MIN_TOUCH + 4, marginTop: spacing.sm, borderRadius: radii.action },
  deleteText: { fontFamily: fonts.bold, fontSize: 16, color: errorColor },
});
