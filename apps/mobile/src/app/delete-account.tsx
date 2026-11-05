import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { AccountIcon, AccountShell, DangerButton, a, errorColor } from '../features/account/AccountUI';
import { colors } from '../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../theme/spacing';
import { fonts, typography } from '../theme/typography';

const items = ['itemTrips', 'itemPreferences', 'itemQuestions', 'itemAccount'] as const;

/** SCR-038 Account deletion (confirm step). Signed-in only (route guard in `_layout.tsx`). */
export default function DeleteAccountScreen() {
  const { t } = useTranslation();
  const [typed, setTyped] = useState('');
  const [notice, setNotice] = useState('');
  const word = t('account.deleteAccount.confirmWord');
  const accepted = [word, t('account.deleteAccount.confirmWordAlt')].map(value => value.normalize('NFC'));
  const confirmed = accepted.includes(typed.trim().toUpperCase().normalize('NFC'));

  function submit() {
    if (!confirmed) return;
    // TODO(SCR-038): call API-006 `POST /v1/me/deletion` {confirm: true} with an Idempotency-Key, then show the status
    // screen (API-007). The deletion job removes the Clerk user server-side; the app never calls Clerk delete itself.
    setNotice(t('account.deleteAccount.notConnected'));
  }
  function keep() { router.canGoBack() ? router.back() : router.replace('/settings'); }

  return <AccountShell title={t('account.deleteAccount.title')} fallback="/settings">
    <View style={[a.card, a.padded]}>
      <View style={styles.badge}><AccountIcon name="warning" color={errorColor} size={26} /></View>
      <Text accessibilityRole="header" style={styles.heading}>{t('account.deleteAccount.heading')}</Text>
      <Text style={styles.lead}>{t('account.deleteAccount.lead')}</Text>
      <View accessibilityRole="list">
        {items.map(item => <View key={item} accessibilityRole="text" style={styles.item}>
          <View style={styles.bullet} /><Text style={styles.itemText}>{t(`account.deleteAccount.${item}`)}</Text>
        </View>)}
      </View>
      <Text style={styles.warning}>{t('account.deleteAccount.warning')}</Text>
    </View>

    <Text nativeID="delete-confirm-label" style={styles.label}>{t('account.deleteAccount.confirmLabel', { word })}</Text>
    <TextInput
      accessibilityLabel={t('account.deleteAccount.confirmLabel', { word })}
      accessibilityLabelledBy="delete-confirm-label"
      autoCapitalize="characters"
      autoComplete="off"
      autoCorrect={false}
      onChangeText={value => { setTyped(value); setNotice(''); }}
      placeholder={word}
      placeholderTextColor={colors.textMuted}
      style={[styles.input, confirmed && styles.inputReady]}
      value={typed}
    />
    <Text style={styles.helper}>{t('account.deleteAccount.confirmHelper')}</Text>

    {notice ? <View accessibilityLiveRegion="polite" accessibilityRole="alert" style={styles.notice}>
      <AccountIcon name="info" color={colors.tealText} size={20} />
      <Text style={styles.noticeText}>{notice}</Text>
    </View> : null}

    <DangerButton label={t('account.deleteAccount.submit')} disabled={!confirmed} onPress={submit} />
    <Pressable accessibilityRole="button" onPress={keep} style={({ pressed }) => [styles.keep, pressed && a.pressed]}>
      <Text style={styles.keepText}>{t('account.deleteAccount.keep')}</Text>
    </Pressable>
  </AccountShell>;
}

const styles = StyleSheet.create({
  badge: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#FBECEC', alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm },
  heading: { ...typography.headline, color: colors.ink },
  lead: { ...typography.body, color: colors.ink, marginTop: spacing.sm, marginBottom: spacing.xs },
  item: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm, paddingVertical: spacing.xxs },
  bullet: { width: 6, height: 6, borderRadius: 3, backgroundColor: errorColor, marginTop: 9 },
  itemText: { ...typography.body, fontSize: 15, lineHeight: 22, color: colors.ink, flex: 1 },
  warning: { ...typography.caption, fontSize: 14, lineHeight: 21, marginTop: spacing.md },
  label: { ...typography.label, marginBottom: spacing.xs, marginLeft: spacing.xxs },
  input: { minHeight: 54, borderRadius: radii.field, borderWidth: 1.5, borderColor: '#DCE8EE', backgroundColor: colors.white, paddingHorizontal: spacing.md, fontFamily: fonts.bold, fontSize: 17, letterSpacing: 1, color: colors.ink },
  inputReady: { borderColor: errorColor },
  helper: { ...typography.caption, marginTop: spacing.xs, marginBottom: spacing.lg, marginLeft: spacing.xxs },
  notice: { flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start', backgroundColor: colors.skyWash, borderRadius: radii.chip, padding: spacing.md, marginBottom: spacing.lg },
  noticeText: { ...typography.caption, fontSize: 14, lineHeight: 21, color: colors.ink, flex: 1 },
  keep: { minHeight: MIN_TOUCH + 4, alignItems: 'center', justifyContent: 'center', marginTop: spacing.sm },
  keepText: { fontFamily: fonts.bold, fontSize: 16, color: colors.tealText },
});
