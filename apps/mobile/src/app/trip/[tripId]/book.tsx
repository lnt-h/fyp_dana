import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { SecondaryButton } from '../../../components/ui';
import { HandoffPanel } from '../../../features/handoff/HandoffPanel';
import type { HandoffKind } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';

const KINDS: HandoffKind[] = ['STAY', 'ACTIVITY', 'TRANSPORT'];

/**
 * SCR-037 Booking handoff as a route (`/trip/[tripId]/book?kind=STAY|ACTIVITY|TRANSPORT&stopId=`), presented as a
 * native form sheet. Use it from screens that cannot host `HandoffSheet` (e.g. a Trips row ⋯); omit `kind` for all.
 */
export default function BookRoute() {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const { tripId, kind, stopId } = useLocalSearchParams<{ tripId: string; kind?: string; stopId?: string }>();
  const kinds = kind ? KINDS.filter(item => kind.split(',').includes(item)) : KINDS;
  const close = () => (router.canGoBack() ? router.back() : router.replace('/(tabs)/trips'));
  return (
    <View style={styles.screen}>
      <Stack.Screen options={{ contentStyle: { backgroundColor: colors.white }, presentation: 'modal' }} />
      <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.handle} />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <HandoffPanel kinds={kinds.length ? kinds : KINDS} stopId={stopId} tripId={tripId} />
      </ScrollView>
      <View style={[styles.footer, { paddingBottom: Math.max(insets.bottom, spacing.md) }]}>
        <SecondaryButton label={t('save.handoff.close')} onPress={close} style={styles.button} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  button: { height: 56 },
  content: { paddingHorizontal: spacing.lg, paddingVertical: spacing.sm },
  footer: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm },
  handle: { alignSelf: 'center', backgroundColor: colors.mutedDot, borderRadius: 3, height: 5, marginTop: spacing.sm, width: 44 },
  screen: { backgroundColor: colors.white, borderTopLeftRadius: radii.sheet, borderTopRightRadius: radii.sheet, flex: 1 },
});
