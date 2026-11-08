import { memo, useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Marker } from 'react-native-maps';
import { useTranslation } from 'react-i18next';

import { colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';
import type { LatLng } from './cluster';

/** Terracotta badge; white text on it is 4.85:1 (WCAG AA for 15 pt bold). */
/** Cluster badge in the brand teal (white count 5.18:1). */
const TERRACOTTA = colors.primary;
const SIZE = 48;

type Props = {
  id: string;
  coordinate: LatLng;
  count: number;
  onPress: (id: string) => void;
};

/** Round count badge for markers sharing a grid cell; tapping zooms to fit its members. */
export const ClusterMarker = memo(function ClusterMarker({ id, coordinate, count, onPress }: Props) {
  const { t } = useTranslation();
  // Plain view (no images): snapshot once after layout, then stop tracking.
  const [tracking, setTracking] = useState(true);

  useEffect(() => {
    setTracking(true);
    const timer = setTimeout(() => setTracking(false), 300);
    return () => clearTimeout(timer);
  }, [count]);

  return (
    <Marker
      accessibilityLabel={t('home.map.cluster', { count })}
      accessibilityRole="button"
      anchor={{ x: 0.5, y: 0.5 }}
      coordinate={coordinate}
      identifier={`cluster:${id}`}
      onPress={() => onPress(id)}
      tracksViewChanges={tracking}
      zIndex={0}
    >
      <View style={styles.wrap}>
        <View style={styles.badge}>
          <Text allowFontScaling={false} style={styles.count}>{count}</Text>
        </View>
      </View>
    </Marker>
  );
});

const styles = StyleSheet.create({
  badge: {
    alignItems: 'center',
    backgroundColor: TERRACOTTA,
    borderColor: colors.white,
    borderRadius: SIZE / 2,
    borderWidth: 3,
    height: SIZE,
    justifyContent: 'center',
    width: SIZE,
  },
  count: { color: colors.white, fontFamily: fonts.bold, fontSize: 17, lineHeight: 22 },
  wrap: {
    padding: 4,
    shadowColor: colors.ink,
    shadowOffset: { height: 3, width: 0 },
    shadowOpacity: 0.22,
    shadowRadius: 5,
  },
});
