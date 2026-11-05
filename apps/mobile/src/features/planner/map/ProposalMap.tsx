import { useEffect, useMemo, useRef } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { Marker, Polyline, type LatLng } from 'react-native-maps';
import { Image } from 'expo-image';
import { useTranslation } from 'react-i18next';
import { CircleButton, Icon, categoryIcon } from '../../../components/ui';
import type { Uuid } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { formatTime } from '../timeline/format';
import { isMeasured, isStopBlocked, type NumberedDay } from '../timeline/model';
import type { StopPlace } from '../timeline/useProposal';

type Props = {
  day: NumberedDay;
  places: Record<Uuid, StopPlace>;
  selectedStopId: Uuid | null;
  onSelect: (stopId: Uuid) => void;
  onOpenPlace: (placeId: Uuid) => void;
  reducedMotion: boolean;
};

const EDGE = { top: 64, right: 56, bottom: 48, left: 56 };
const FOCUS_DELTA = 0.008;

/**
 * SCR-025 map for one day. Default provider (Apple Maps on iOS, Google on Android). Pins use the same continuous
 * numbers as the timeline. Legs: the API has no leg geometry in v1, so a measured leg is a straight visual connector
 * with no length label; an unavailable leg is a dashed red connector, also unlabelled. Under the map, the selected
 * stop with Previous/Next gives a non-gesture path through the day.
 */
export function ProposalMap({ day, places, selectedStopId, onSelect, onOpenPlace, reducedMotion }: Props) {
  const { t } = useTranslation();
  const mapRef = useRef<MapView>(null);
  const coordinates = useMemo<LatLng[]>(() => day.stops.map(stop => stop.location), [day]);
  const selectedIndex = day.stops.findIndex(stop => stop.id === selectedStopId);
  const selected = selectedIndex >= 0 ? day.stops[selectedIndex] : undefined;
  const hasUnavailableLeg = day.legs.some(leg => !isMeasured(leg.availability));

  const initialRegion = useMemo(() => regionFor(coordinates), [coordinates]);

  function fitAll() {
    if (coordinates.length > 1) mapRef.current?.fitToCoordinates(coordinates, { animated: !reducedMotion, edgePadding: EDGE });
    else if (coordinates[0]) mapRef.current?.animateToRegion({ ...coordinates[0], latitudeDelta: FOCUS_DELTA, longitudeDelta: FOCUS_DELTA }, reducedMotion ? 0 : 220);
  }

  // New day: frame all of its pins.
  useEffect(() => {
    const timer = setTimeout(fitAll, 50);
    return () => clearTimeout(timer);
  }, [day.day_index]);

  // Selection from either the map or the timeline: bring the stop into view.
  useEffect(() => {
    if (!selected) return;
    mapRef.current?.animateCamera({ center: selected.location }, { duration: reducedMotion ? 0 : 260 });
  }, [selected, reducedMotion]);

  function step(offset: number) {
    const next = day.stops[selectedIndex + offset];
    if (next) onSelect(next.id);
  }

  const atStart = selectedIndex <= 0;
  const atEnd = selectedIndex < 0 || selectedIndex >= day.stops.length - 1;
  const selectedImage = selected ? resolveImage(places[selected.place_id]?.thumbnail, { height: 48, width: 48 }) : null;
  const selectedTime = selected ? [formatTime(selected.planned_arrival), formatTime(selected.planned_departure)] : [];

  return <View>
    <View style={[m.shadow, elevation.md]}>
      <View style={m.card}>
        {initialRegion ? <MapView
          ref={mapRef}
          accessibilityLabel={t('proposal.map.a11y', { day: day.day_index })}
          initialRegion={initialRegion}
          onMapReady={fitAll}
          pitchEnabled={false}
          rotateEnabled={false}
          showsPointsOfInterests={false}
          style={StyleSheet.absoluteFill}
          toolbarEnabled={false}
        >
          {day.legs.map(leg => {
            const from = day.stops.find(stop => stop.id === leg.from_stop_id);
            const to = day.stops.find(stop => stop.id === leg.to_stop_id);
            if (!from || !to) return null;
            const measured = isMeasured(leg.availability);
            return <Polyline
              key={`${leg.from_stop_id}-${leg.to_stop_id}-${leg.availability}`}
              coordinates={[from.location, to.location]}
              lineDashPattern={measured ? undefined : [10, 8]}
              strokeColor={measured ? colors.deepOcean : palette.error}
              strokeWidth={3}
            />;
          })}
          {day.stops.map(stop => {
            const isSelected = stop.id === selectedStopId;
            const blocked = isStopBlocked(stop);
            const fill = blocked ? palette.error : isSelected ? colors.tealText : colors.deepOcean;
            return <Marker
              key={stop.id}
              accessibilityLabel={t('proposal.map.pin', { name: stop.name, number: stop.number, time: formatTime(stop.planned_arrival) ?? t('proposal.stop.timeUnknown') })}
              accessibilityRole="button"
              anchor={{ x: 0.5, y: 1 }}
              coordinate={stop.location}
              onPress={() => onSelect(stop.id)}
              zIndex={isSelected ? 10 : 1}
            >
              <View style={m.pinWrap}>
                <View style={[m.pin, isSelected && m.pinSelected, { backgroundColor: fill }]}>
                  <Text style={[m.pinText, isSelected && m.pinTextSelected]}>{stop.number}</Text>
                </View>
                <View style={[m.tail, { borderTopColor: fill }]} />
              </View>
            </Marker>;
          })}
        </MapView> : <View style={m.empty}>
          <Icon color={colors.tealText} name="map-pin" size={28} />
          <Text style={m.emptyText}>{t('proposal.map.noStops')}</Text>
        </View>}
        {initialRegion && <CircleButton accessibilityLabel={t('proposal.map.recenter')} icon="navigation" onPress={fitAll} size={44} style={m.recenter} />}
        <View pointerEvents="none" style={m.attribution}>
          <Text style={m.attributionText}>{t(Platform.OS === 'android' ? 'proposal.map.attributionGoogle' : 'proposal.map.attributionApple')}</Text>
        </View>
      </View>
    </View>
    {hasUnavailableLeg && <View style={m.legend}>
      <View style={m.legendLine}>{[0, 1, 2].map(index => <View key={index} style={m.legendDash} />)}</View>
      <Text style={m.legendText}>{t('proposal.map.legendUnavailable')}</Text>
    </View>}
    {selected && <View style={m.controls}>
      <CircleButton accessibilityLabel={t('proposal.map.previousA11y')} disabled={atStart} icon="back" onPress={() => step(-1)} size={44} tone="tint" />
      <Pressable
        accessibilityHint={t('proposal.stop.detailsA11y', { name: selected.name })}
        accessibilityLiveRegion="polite"
        accessibilityRole="button"
        onPress={() => onOpenPlace(selected.place_id)}
        style={({ pressed }) => [m.current, pressed && { opacity: 0.75 }]}
      >
        <View style={m.currentThumb}>
          {selectedImage
            ? <Image contentFit="cover" placeholder={selectedImage.placeholder} source={selectedImage.source} style={StyleSheet.absoluteFill} transition={150} />
            : <Icon color={colors.tealText} name={categoryIcon(places[selected.place_id]?.categoryCode)} size={22} />}
        </View>
        <View style={m.currentCopy}>
          <Text numberOfLines={1} style={m.currentName}>{t('proposal.map.position', { name: selected.name, number: selected.number })}</Text>
          <Text numberOfLines={1} style={m.currentTime}>
            {selectedTime[0] && selectedTime[1] ? `${selectedTime[0]} – ${selectedTime[1]}` : t('proposal.stop.timeUnknown')}
          </Text>
        </View>
        <Icon color={colors.tealText} name="chevron-right" size={18} strokeWidth={2.2} />
      </Pressable>
      <CircleButton accessibilityLabel={t('proposal.map.nextA11y')} disabled={atEnd} icon="chevron-right" onPress={() => step(1)} size={44} tone="tint" />
    </View>}
  </View>;
}

/** Region framing all points (display only); null when the day has no stops. */
function regionFor(points: LatLng[]) {
  if (!points.length) return null;
  const lats = points.map(point => point.latitude);
  const lngs = points.map(point => point.longitude);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats), minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  return {
    latitude: (minLat + maxLat) / 2,
    latitudeDelta: Math.max(FOCUS_DELTA, (maxLat - minLat) * 1.6),
    longitude: (minLng + maxLng) / 2,
    longitudeDelta: Math.max(FOCUS_DELTA, (maxLng - minLng) * 1.6),
  };
}

const m = StyleSheet.create({
  shadow: { borderRadius: radii.card, backgroundColor: colors.white },
  card: { height: 260, borderRadius: radii.card, overflow: 'hidden', backgroundColor: colors.skyWash },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.xs, padding: spacing.xl },
  emptyText: { fontFamily: fonts.bold, fontSize: 15, color: colors.deepOcean, textAlign: 'center' },
  pinWrap: { alignItems: 'center', paddingHorizontal: 4, paddingTop: 4 },
  pin: { minWidth: 32, height: 32, borderRadius: 16, paddingHorizontal: 6, alignItems: 'center', justifyContent: 'center', borderWidth: 2.5, borderColor: colors.white },
  pinSelected: { minWidth: 42, height: 42, borderRadius: 21, borderWidth: 3 },
  pinText: { color: colors.white, fontFamily: fonts.bold, fontSize: 14 },
  pinTextSelected: { fontSize: 17 },
  tail: { width: 0, height: 0, marginTop: -1, borderLeftWidth: 6, borderRightWidth: 6, borderTopWidth: 8, borderLeftColor: 'transparent', borderRightColor: 'transparent' },
  recenter: { position: 'absolute', top: spacing.sm, right: spacing.sm },
  attribution: { position: 'absolute', left: 10, bottom: 8, backgroundColor: 'rgba(255,255,255,0.88)', borderRadius: 8, paddingHorizontal: 6, paddingVertical: 2, maxWidth: '70%' },
  attributionText: { fontFamily: fonts.medium, fontSize: 11, color: colors.ink },
  legend: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: spacing.sm, paddingHorizontal: spacing.xxs },
  legendLine: { flexDirection: 'row', gap: 3 },
  legendDash: { width: 7, height: 3, borderRadius: 1.5, backgroundColor: palette.error },
  legendText: { flex: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 19, color: colors.textMuted },
  controls: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, marginTop: spacing.sm },
  current: { flex: 1, minWidth: 0, minHeight: MIN_TOUCH + 12, flexDirection: 'row', alignItems: 'center', gap: 10, paddingLeft: 6, paddingRight: 10, borderRadius: radii.chip + 4, backgroundColor: colors.white, borderWidth: 1, borderColor: '#DCE8EE' },
  currentThumb: { width: 44, height: 44, borderRadius: 12, overflow: 'hidden', backgroundColor: colors.skyWash, alignItems: 'center', justifyContent: 'center' },
  currentCopy: { flex: 1, minWidth: 0 },
  currentName: { fontFamily: fonts.bold, fontSize: 14, lineHeight: 19, color: colors.ink },
  currentTime: { fontFamily: fonts.bold, fontSize: 12, lineHeight: 16, color: colors.tealText },
});
