import { memo, useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Marker } from 'react-native-maps';

import { Photo } from '../../../components/ui';
import type { Place } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { categoryColor, colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';

const SIZE = 48;
const SELECTED_SIZE = 58;

type Props = {
  place: Place;
  selected: boolean;
  onPress: (placeId: string) => void;
};

/**
 * Round photo marker ringed in its category colour (icon tile when there is no photo), with a pointer in the same colour;
 * the selected marker grows and shows its name (SCR-008).
 */
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
  const tint = categoryColor(place.category_code).fg;

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
        <View style={[styles.bubble, { borderColor: tint, borderRadius: size / 2, height: size, width: size }]}>
          {/* No photo, or a photo that fails: the category tile (deep tone, icon only) so pins stay legible on the map. */}
          <Photo
            categoryCode={place.category_code}
            height={SELECTED_SIZE}
            iconSize={selected ? 24 : 20}
            image={place.thumbnail}
            onError={() => setLoaded(true)}
            onLoad={() => setLoaded(true)}
            tone="dark"
            transition={0}
            variant="thumb"
            width={SELECTED_SIZE}
          />
        </View>
        <View style={[styles.pointer, { borderTopColor: tint }]} />
      </View>
    </Marker>
  );
});

const styles = StyleSheet.create({
  bubble: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 3,
    justifyContent: 'center',
    overflow: 'hidden',
  },
  label: {
    backgroundColor: colors.ink,
    borderRadius: 8,
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
    borderTopWidth: 8,
    height: 0,
    marginTop: -1,
    width: 0,
  },
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
