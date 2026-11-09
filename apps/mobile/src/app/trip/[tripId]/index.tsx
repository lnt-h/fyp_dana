import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { CircleButton, Skeleton } from '../../../components/ui';
import { ScreenMessage } from '../../../features/place/components/PlaceUI';
import { getTrip } from '../../../lib/api/source';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';

/**
 * Route handler for `/trip/[tripId]`: redirects to the saved proposal view or draft preview.
 */
export default function TripIndexRoute() {
  const { tripId } = useLocalSearchParams<{ tripId: string }>();
  const { t } = useTranslation();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tripId) return;
    let alive = true;
    getTrip(tripId)
      .then(detail => {
        if (!alive) return;
        const previewId = detail.active_preview_id ?? detail.id;
        router.replace({
          params: { mode: detail.active_preview_id ? 'draft' : 'saved', previewId, tripId: detail.id },
          pathname: '/plan/[previewId]/proposal',
        });
      })
      .catch(err => {
        if (!alive) return;
        setError(err?.message || t('common.loadError.server'));
      });
    return () => {
      alive = false;
    };
  }, [tripId, t]);

  if (error) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={() => router.replace('/trips')} size={44} />
        </View>
        <ScreenMessage body={error} title={t('place.errorTitle')} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Skeleton height={200} radius={0} width="100%" />
      <View style={styles.body}>
        <Skeleton height={24} width={220} />
        <Skeleton height={16} width={140} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  body: { gap: spacing.md, padding: spacing.lg },
  container: { backgroundColor: colors.white, flex: 1 },
  header: { padding: spacing.md },
});
