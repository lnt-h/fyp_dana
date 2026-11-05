import { Image } from 'expo-image';
import { memo, useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Marker } from 'react-native-maps';

import { Icon, categoryIcon } from '../../../components/ui';
import type { Place } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';

const SIZE = 48;
const SELECTED_SIZE = 58;

type Props = {
  place: Place;
  selected: boolean;
  onPress: (placeId: string) => void;
};

/** Round photo marker with a white border and pointer; the selected marker grows and shows its name (SCR-008). */
export const PlaceMarker = memo(function PlaceMarker({ place, selected, onPress }: Props) {
  const image = resolveImage(place.thumbnail, { height: SELECTED_SIZE, width: SELECTED_SIZE });
  const [loaded, setLoaded] = useState(!image);
  // Custom marker views are snapshotted; track view changes only until the photo loads or the selection settles.
  const [tracking, setTracking] = useState(true);

  useEffect(() => {
    setTracking(true);
    if (!loaded) return;
    const timer = setTimeout(() => setTracking(false), 400);
    return () => clearTimeout(timer);
  }, [loaded, selected]);

  const size = selected ? SELECTED_SIZE : SIZE;

  return (
    <Marker
      accessibilityLabel={place.name}
      anchor={{ x: 0.5, y: 1 }}
      coordinate={place.location}
      identifier={place.id}
      onPress={() => onPress(place.id)}
      tracksViewChanges={tracking}
      zIndex={selected ? 2 : 1}
    >
      <View style={styles.wrap}>
        {selected ? (
          <View style={styles.label}>
            <Text numberOfLines={1} style={styles.labelText}>{place.name}</Text>
          </View>
        ) : null}
        <View style={[styles.bubble, { borderRadius: size / 2, height: size, width: size }, selected && styles.bubbleSelected]}>
          {image ? (
            <Image
              contentFit="cover"
              onError={() => setLoaded(true)}
              onLoad={() => setLoaded(true)}
              placeholder={image.placeholder}
              source={image.source}
              style={StyleSheet.absoluteFill}
            />
          ) : (
            <Icon color={colors.tealText} name={categoryIcon(place.category_code)} size={22} />
          )}
        </View>
        <View style={[styles.pointer, selected && styles.pointerSelected]} />
      </View>
    </Marker>
  );
});

const styles = StyleSheet.create({
  bubble: {
    alignItems: 'center',
    backgroundColor: colors.surfaceTint,
    borderColor: colors.white,
    borderWidth: 3,
    justifyContent: 'center',
    overflow: 'hidden',
  },
  bubbleSelected: { borderColor: colors.deepOcean },
  label: {
    backgroundColor: colors.deepOcean,
    borderRadius: 6,
    marginBottom: 4,
    maxWidth: 160,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  labelText: { color: colors.white, fontFamily: fonts.bold, fontSize: 12, lineHeight: 16 },
  pointer: {
    borderLeftColor: 'transparent',
    borderLeftWidth: 6,
    borderRightColor: 'transparent',
    borderRightWidth: 6,
    borderTopColor: colors.white,
    borderTopWidth: 8,
    height: 0,
    marginTop: -1,
    width: 0,
  },
  pointerSelected: { borderTopColor: colors.deepOcean },
  wrap: {
    alignItems: 'center',
    paddingHorizontal: 4,
    paddingTop: 4,
    shadowColor: colors.ink,
    shadowOffset: { height: 3, width: 0 },
    shadowOpacity: 0.22,
    shadowRadius: 5,
  },
});
