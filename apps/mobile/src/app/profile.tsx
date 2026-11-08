import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Chip, PrimaryButton, SecondaryButton } from '../components/ui';
import { useAccount } from '../features/account/AccountContext';
import { AccountIcon, AccountRow, AccountShell, GroupCard, SectionLabel, SessionConfirm, a, errorColor } from '../features/account/AccountUI';
import { demoNoAuth } from '../lib/demoAuth';
import { colors } from '../theme/colors';
import { elevation } from '../theme/elevation';
import { MIN_TOUCH, radii, spacing } from '../theme/spacing';
import { fonts, typography } from '../theme/typography';

/** SCR-009 Profile: identity, travel preferences, language and the account hub (privacy, legal and motion live in SCR-010 Settings). */
export default function ProfileScreen() {
  const { t, i18n } = useTranslation();
  const { profile, isSignedIn } = useAccount();
  const [confirming, setConfirming] = useState(false);
  const version = Constants.expoConfig?.version ?? '1.0.0';
  const name = isSignedIn ? profile.name || t('account.profile.fallbackName') : t('account.profile.guestName');
  const initial = (isSignedIn ? profile.name.trim() || profile.email : '').charAt(0).toUpperCase();
  const interests = profile.interests.map(value => t(`account.preferences.interests.${value}`));
  const travelType = profile.travelType ? t(`account.preferences.travelTypes.${profile.travelType}`) : null;
  const preferenceSummary = [...interests, ...(travelType ? [travelType] : [])].join(', ');
  const languageName = t(`account.common.languageName.${i18n.language === 'vi' ? 'vi' : 'en'}`);

  return <AccountShell title={t('account.profile.title')} fallback="/home">
    <View style={[a.card, styles.identity]}>
      <View style={styles.avatar} accessible accessibilityRole="image" accessibilityLabel={t('account.profile.avatarLabel', { name })}>
        {initial ? <Text style={styles.initial}>{initial}</Text> : <AccountIcon name="person" color={colors.ink} size={30} />}
      </View>
      <View style={styles.identityCopy}>
        <Text numberOfLines={1} style={styles.name}>{name}</Text>
        <Text numberOfLines={isSignedIn ? 1 : 3} style={styles.email}>{isSignedIn ? profile.email : t('account.profile.guestBody')}</Text>
      </View>
    </View>
    {!isSignedIn && <PrimaryButton label={t('account.profile.create')} onPress={() => router.push('/register')} style={styles.create} />}

    <Pressable accessibilityRole="button" accessibilityLabel={`${t('account.profile.preferences')}. ${preferenceSummary || t('account.profile.preferencesEmpty')}`}
      accessibilityHint={t('account.profile.preferencesHint')} onPress={() => router.push('/travel-preferences')}
      style={({ pressed }) => [a.card, styles.prefs, pressed && a.pressed]}>
      <View style={styles.prefsHeader}>
        <AccountIcon name="sliders" />
        <Text style={styles.prefsTitle}>{t('account.profile.preferences')}</Text>
        <AccountIcon name="chevron" color={colors.textMuted} size={18} />
      </View>
      {interests.length || travelType ? <View style={styles.chips}>
        {interests.map(label => <Chip key={label} label={label} tone="tint" />)}
        {travelType ? <Chip icon="navigation" label={travelType} /> : null}
      </View> : <Text style={styles.prefsEmpty}>{t('account.profile.preferencesEmpty')}</Text>}
    </Pressable>

    {isSignedIn && <GroupCard>
      <AccountRow icon="edit" title={t('account.profile.editProfile')} onPress={() => router.push('/edit-profile')} />
    </GroupCard>}

    <SectionLabel>{t('account.profile.sectionOptions')}</SectionLabel>
    <GroupCard>
      <AccountRow icon="language" title={t('account.common.language')} value={languageName} onPress={() => router.push('/language')} />
      <AccountRow icon="settings" title={t('account.profile.settings')} subtitle={t('account.profile.settingsSubtitle')} onPress={() => router.push('/settings')} />
    </GroupCard>

    {/* Demo mode (demoAuth.ts): no sign-out or account deletion for the shared demo user. */}
    {demoNoAuth ? null : confirming ? <View style={a.card}><SessionConfirm onCancel={() => setConfirming(false)} /></View>
      : <SecondaryButton label={t(isSignedIn ? 'account.profile.signOut' : 'account.profile.resetGuest')} onPress={() => setConfirming(true)} style={styles.signOut} />}
    {isSignedIn && !demoNoAuth && <Pressable accessibilityRole="button" accessibilityLabel={t('account.profile.deleteAccount')} onPress={() => router.push('/delete-account')}
      style={({ pressed }) => [styles.delete, pressed && a.pressed]}>
      <AccountIcon name="trash" color={errorColor} size={20} />
      <Text style={styles.deleteText}>{t('account.profile.deleteAccount')}</Text>
    </Pressable>}
    <Text style={a.note}>{t('account.profile.versionCaption', { version })}</Text>
  </AccountShell>;
}

const styles = StyleSheet.create({
  identity: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.lg },
  // Solid sun with ink initial: 10.1:1 contrast.
  avatar: { width: 64, height: 64, borderRadius: 32, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.sun },
  initial: { fontFamily: fonts.bold, fontSize: 28, color: colors.ink },
  identityCopy: { flex: 1 },
  name: { ...typography.headline, color: colors.ink },
  email: { ...typography.caption, fontSize: 15, lineHeight: 21, marginTop: 2 },
  create: { marginTop: -spacing.xs, marginBottom: spacing.lg },
  prefs: { padding: spacing.lg, gap: spacing.sm, minHeight: MIN_TOUCH },
  prefsHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, minHeight: MIN_TOUCH - 12 },
  prefsTitle: { flex: 1, fontFamily: fonts.bold, fontSize: 17, lineHeight: 22, color: colors.ink },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  prefsEmpty: { ...typography.caption, fontSize: 15, lineHeight: 21 },
  signOut: { height: 52, borderRadius: radii.button, marginTop: spacing.xs, ...elevation.none },
  delete: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.xs, minHeight: MIN_TOUCH + 4, marginTop: spacing.sm, borderRadius: radii.button },
  deleteText: { fontFamily: fonts.bold, fontSize: 16, color: errorColor },
});
