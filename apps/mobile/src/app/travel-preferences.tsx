import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { PrimaryButton } from '../components/ui';
import { interestCategoryCode, useAccount } from '../features/account/AccountContext';
import { AccountShell, a } from '../features/account/AccountUI';
import { MAX_INTEREST_CODES, TravelPreferences } from '../features/account/TravelPreferences';
import { authErrorMessage } from '../features/auth/authErrors';
import { useIsOffline } from '../features/home/useNetwork';
import { ApiError } from '../lib/api/errors';
import { fetchPreferences, savePreferences, toPreferencesWrite } from '../lib/api/sourceAccount';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';

export default function TravelPreferencesScreen() {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const offline = useIsOffline();
  const { profile, updateProfile } = useAccount();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  // Interests from GET /v1/me/preferences may arrive after the screen opened: the legacy four
  // profile interests seed the code selection until the traveller edits.
  const seeded = profile.interests.map(interest => interestCategoryCode[interest]);
  const seededKey = seeded.join(',');
  const [selected, setSelectedState] = useState<string[]>(seeded);
  const touched = useRef(false);
  const setSelected = (next: string[]) => { touched.current = true; setSelectedState(next); };
  useEffect(() => { if (!touched.current) setSelectedState(seeded); }, [seededKey]); // eslint-disable-line react-hooks/exhaustive-deps
  const [travelType, setTravelType] = useState(profile.travelType);
  function close() { router.canGoBack() ? router.back() : router.replace('/profile'); }
  async function save() {
    if (busy || offline) return;
    setBusy(true); setNotice('');
    try {
      // Full replace on the current server preferences: pace, modes and day window are kept,
      // the code selection (≤ 20) replaces the interest codes.
      const current = await fetchPreferences();
      await savePreferences(toPreferencesWrite(current, { interest_category_codes: selected.slice(0, MAX_INTEREST_CODES) }));
      await updateProfile({ travelType });
      close();
    }
    // API errors (PUT /v1/me/preferences) get the preferences copy; Clerk errors keep their own message.
    catch (error) { setNotice(error instanceof ApiError || error instanceof TypeError ? t('account.preferences.saveFailed') : authErrorMessage(error)); }
    finally { setBusy(false); }
  }
  return <View style={s.screen}>
    <View style={s.body}>
      <AccountShell title={t('account.preferences.title')} lead={t('account.preferences.intro')}>
        <TravelPreferences selected={selected} onSelect={setSelected} travelType={travelType} onTravelType={setTravelType} />
        {!!notice && <Text accessibilityLiveRegion="polite" style={a.error}>{notice}</Text>}
        {/* Spacer for the sticky footer below. */}
        <View style={{ height: 120 }} />
      </AccountShell>
    </View>
    <View style={[s.footer, { paddingBottom: Math.max(insets.bottom, spacing.sm) + spacing.xs }]}>
      {offline ? <Text accessibilityLiveRegion="polite" style={s.offline}>{t('common.loadError.offline')}</Text> : null}
      <PrimaryButton disabled={offline} label={t('account.preferences.save')} loading={busy} onPress={() => void save()} />
      <Pressable accessibilityRole="button" onPress={close} style={({ pressed }) => [a.textButton, pressed && a.pressed]}>
        <Text style={a.textButtonLabel}>{t('common.cancel')}</Text>
      </Pressable>
    </View>
  </View>;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.canvas },
  body: { flex: 1 },
  footer: {
    backgroundColor: colors.canvas,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.hairline,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
  },
  offline: { fontSize: 13, lineHeight: 18, color: colors.danger, textAlign: 'center', marginBottom: spacing.xs },
});
