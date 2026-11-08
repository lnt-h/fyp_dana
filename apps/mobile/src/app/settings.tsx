import { useState } from 'react';
import { Switch } from 'react-native';
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { useAccount } from '../features/account/AccountContext';
import { AccountRow, AccountShell, ExpandableRow, GroupCard, SectionLabel, SessionConfirm } from '../features/account/AccountUI';
import { demoNoAuth } from '../lib/demoAuth';
import { colors } from '../theme/colors';

/** SCR-010 Settings: the full list (Profile SCR-009 is the hub with shortcuts). */
export default function SettingsScreen() {
  const { t, i18n } = useTranslation();
  const { reduceMotion, setReduceMotion, isSignedIn } = useAccount();
  const [confirming, setConfirming] = useState(false);
  const version = Constants.expoConfig?.version ?? '1.0.0';
  const languageName = t(`account.common.languageName.${i18n.language === 'vi' ? 'vi' : 'en'}`);
  return <AccountShell title={t('account.settings.title')} lead={t('account.settings.intro')}>
    <SectionLabel>{t('account.settings.sectionAccessibility')}</SectionLabel>
    <GroupCard>
      <AccountRow icon="motion" title={t('account.common.reduceMotion')} subtitle={t('account.common.reduceMotionSubtitle')}
        trailing={<Switch accessibilityLabel={t('account.common.reduceMotion')} value={reduceMotion} onValueChange={setReduceMotion} trackColor={{ false: colors.hairline, true: colors.audioTeal }} />} />
    </GroupCard>

    <SectionLabel>{t('account.settings.sectionPersonalization')}</SectionLabel>
    <GroupCard>
      <AccountRow icon="sliders" title={t('account.preferences.title')} subtitle={t('account.settings.preferencesSubtitle')} onPress={() => router.push('/travel-preferences')} />
    </GroupCard>

    <SectionLabel>{t('account.settings.sectionLanguage')}</SectionLabel>
    <GroupCard>
      <AccountRow icon="language" title={t('account.settings.appLanguage')} subtitle={languageName} onPress={() => router.push('/language')} />
    </GroupCard>

    <SectionLabel>{t('account.settings.sectionPrivacy')}</SectionLabel>
    <GroupCard>
      <ExpandableRow icon="info" title={t('account.common.aiData')} subtitle={t('account.common.aiDataSubtitle')} body={t('account.common.aiDataBody')} />
      <ExpandableRow icon="shield" title={t('account.settings.data')} subtitle={t('account.settings.dataSubtitle')} body={t('account.settings.dataBody')} />
      <ExpandableRow icon="doc" title={t('account.common.legal')} badge={t('account.common.legalDraft')} body={t('account.common.legalBody')} />
      <ExpandableRow icon="info" title={t('account.common.about')} subtitle={t('account.common.version', { version })} body={t('account.common.aboutBody')} />
      {isSignedIn && !demoNoAuth && <AccountRow danger icon="trash" title={t('account.profile.deleteAccount')} subtitle={t('account.common.deleteAccountSubtitle')} onPress={() => router.push('/delete-account')} />}
    </GroupCard>

    {/* Demo mode (demoAuth.ts): one shared demo user, so there is no session to end. */}
    {!demoNoAuth && <>
      <SectionLabel>{t('account.settings.sectionSession')}</SectionLabel>
      <GroupCard>
        <AccountRow icon="exit" title={t(isSignedIn ? 'account.profile.signOut' : 'account.profile.resetGuest')} subtitle={t('account.settings.sessionSubtitle')} onPress={() => setConfirming(true)} />
        {confirming && <SessionConfirm onCancel={() => setConfirming(false)} />}
      </GroupCard>
    </>}
  </AccountShell>;
}
