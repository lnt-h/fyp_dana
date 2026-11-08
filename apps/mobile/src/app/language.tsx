import { useEffect, useState } from 'react';
import { AccessibilityInfo, Text } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { deviceLocale, loadLanguageChoice, setLanguageChoice, type LanguageChoice } from '../i18n';
import { AccountRow, AccountShell, GroupCard, a } from '../features/account/AccountUI';

/**
 * SCR-039 Language setting. Applies immediately and persists on device (`app.language`).
 * TODO(SCR-039): when the API is wired, also PUT /v1/me/preferences (API-005) with the new `locale` for signed-in users.
 */
export default function LanguageScreen() {
  const { t, i18n } = useTranslation();
  const [choice, setChoice] = useState<LanguageChoice | null>(null);
  const [pending, setPending] = useState<LanguageChoice | null>(null);
  const [notice, setNotice] = useState('');
  useEffect(() => {
    let active = true;
    void loadLanguageChoice().then(saved => { if (active) setChoice(saved); });
    return () => { active = false; };
  }, []);

  function close() { router.canGoBack() ? router.back() : router.replace('/settings'); }

  /**
   * Applies at once and returns to Settings. Tapping the language already in use also responds (it confirms the
   * choice and closes the screen) instead of being ignored, which used to look like a dead row to sighted and
   * screen-reader users alike.
   */
  async function select(next: LanguageChoice) {
    if (pending) return;
    if (next !== choice) {
      setPending(next);
      setNotice('');
      try {
        await setLanguageChoice(next);
        setChoice(next);
      } catch {
        setPending(null);
        setNotice(t('account.language.saveFailed'));
        return;
      }
      setPending(null);
    }
    const locale = next === 'device' ? deviceLocale() : next;
    AccessibilityInfo.announceForAccessibility(i18n.t('account.language.changed', { language: i18n.t(`account.common.languageName.${locale}`) }));
    close();
  }

  const device = deviceLocale();
  return <AccountShell title={t('account.language.title')} lead={t('account.language.intro')} fallback="/settings">
    <GroupCard accessibilityRole="radiogroup">
      <AccountRow icon="language" title="Tiếng Việt" subtitle={t('account.language.viSubtitle')} accessibilityLabel="Tiếng Việt"
        checked={choice === 'vi'} busy={pending === 'vi'} onPress={() => void select('vi')} />
      <AccountRow icon="language" title="English" subtitle={t('account.language.enSubtitle')} accessibilityLabel="English"
        checked={choice === 'en'} busy={pending === 'en'} onPress={() => void select('en')} />
      <AccountRow icon="device" title={t('account.language.device')} subtitle={t('account.language.deviceSubtitle', { language: t(`account.common.languageName.${device}`) })}
        checked={choice === 'device'} busy={pending === 'device'} onPress={() => void select('device')} />
    </GroupCard>
    {!!notice && <Text accessibilityLiveRegion="polite" style={a.error}>{notice}</Text>}
    <Text style={a.note}>{t('account.language.note')}</Text>
  </AccountShell>;
}
