import { useEffect, useMemo, useRef } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { Marker, Polyline, type LatLng } from 'react-native-maps';
import { useTranslation } from 'react-i18next';
import { CircleButton, Icon, NumberPin, Photo } from '../../../components/ui';
import type { Uuid } from '../../../lib/api/types';
import { colors, dayColor } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { formatTime } from '../timeline/format';
import { isMeasured, isStopBlocked, type NumberedDay } from '../timeline/model';
import { dayHasEstimate } from '../timeline/TimeRail';
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
 * SCR-025 map for one day. Default provider (Apple Maps on iOS, Google on Android). Pins are the timeline's numbered
 * pins in the day colour; the route line is the day colour too, dashed when the leg is a demo estimate. The API has no
 * leg geometry in v1, so lines join stops directly; an unavailable leg is a red dashed connector. Under the map, the
 * selected stop with Previous/Next gives a non-gesture path through the day.
 */
export function ProposalMap({ day, places, selectedStopId, onSelect, onOpenPlace, reducedMotion }: Props) {
  const { t } = useTranslation();
  const mapRef = useRef<MapView>(null);
  const coordinates = useMemo<LatLng[]>(() => day.stops.map(stop => stop.location), [day]);
  const selectedIndex = day.stops.findIndex(stop => stop.id === selectedStopId);
  const selected = selectedIndex >= 0 ? day.stops[selectedIndex] : undefined;
  const hasUnavailableLeg = day.legs.some(leg => !isMeasured(leg.availability));
  const routeColor = dayColor(day.day_index - 1);
  // Refit whenever the day's stop list changes (new day, or an edit added/moved/removed a stop), not only on day change.
  const stopKey = day.stops.map(stop => stop.id).join('|');

  const initialRegion = useMemo(() => regionFor(coordinates), [coordinates]);

  function fitAll() {
    if (coordinates.length > 1) mapRef.current?.fitToCoordinates(coordinates, { animated: !reducedMotion, edgePadding: EDGE });
    else if (coordinates[0]) mapRef.current?.animateToRegion({ ...coordinates[0], latitudeDelta: FOCUS_DELTA, longitudeDelta: FOCUS_DELTA }, reducedMotion ? 0 : 220);
  }

  // New day or a changed stop list: frame all of its pins.
  useEffect(() => {
    const timer = setTimeout(fitAll, 50);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [day.day_index, stopKey]);

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
  const selectedPlace = selected?.place_id ? places[selected.place_id] : undefined;
  const selectedTime = selected ? [formatTime(selected.planned_arrival), formatTime(selected.planned_departure)] : [];

  return <View>
    <View style={m.shadow}>
      <View style={m.card}>
        {initialRegion ? <MapView
          ref={mapRef}
          accessibilityLabel={t('proposal.map.a11y', { day: day.day_index })}
          initialRegion={initialRegion}
          onMapReady={fitAll}
          pitchEnabled={false}
          rotateEnabled={false}
          // The map sits inside the page scroll: it never captures vertical drags (Wave 6 P2). Pins stay
          // tappable and pinch-zoom still works; the recenter button returns to the day's bounds.
          scrollEnabled={false}
          showsPointsOfInterests={false}
          style={StyleSheet.absoluteFill}
          toolbarEnabled={false}
        >
          {day.legs.map(leg => {
            const from = day.stops.find(stop => stop.id === leg.from_stop_id);
            const to = day.stops.find(stop => stop.id === leg.to_stop_id);
            if (!from || !to) return null;
            const measured = isMeasured(leg.availability);
            const dashed = !measured || !!leg.estimated;
            return <Polyline
              key={`${leg.from_stop_id}-${leg.to_stop_id}-${leg.availability}-${leg.estimated ? 1 : 0}`}
              coordinates={[from.location, to.location]}
              lineDashPattern={dashed ? [8, 6] : undefined}
              strokeColor={measured ? routeColor : colors.danger}
              strokeWidth={3}
            />;
          })}
          {day.stops.map((stop, index) => {
            const isSelected = stop.id === selectedStopId;
            const blocked = isStopBlocked(stop);
            const web = stop.trust_level === 'WEB_UNVERIFIED';
            // Per-day numbering (Wave 6 P2): pins restart at 1 each day, matching the timeline rail.
            const displayNumber = index + 1;
            return <Marker
              key={stop.id}
              accessibilityLabel={[t('proposal.map.pin', { name: stop.name, number: displayNumber, time: formatTime(stop.planned_arrival) ?? t('proposal.stop.timeUnknown') }), web ? t('proposal.stop.web') : null].filter(Boolean).join(', ')}
              accessibilityRole="button"
              anchor={{ x: 0.5, y: 0.5 }}
              coordinate={stop.location}
              onPress={() => onSelect(stop.id)}
              zIndex={isSelected ? 10 : 1}
            >
              <View style={[m.pinWrap, isSelected && { borderColor: blocked ? colors.danger : routeColor }, !isSelected && blocked && m.pinBlocked, web && m.pinWeb]}>
                <NumberPin dayIndex={day.day_index - 1} number={displayNumber} size={28} />
              </View>
            </Marker>;
          })}
        </MapView> : <View style={m.empty}>
          <Icon color={colors.primary} name="map-pin" size={28} />
          <Text style={m.emptyText}>{t('proposal.map.noStops')}</Text>
        </View>}
        {initialRegion && <CircleButton accessibilityLabel={t('proposal.map.recenter')} icon="navigation" onPress={fitAll} size={44} style={m.recenter} />}
        <View pointerEvents="none" style={m.attribution}>
          <Text style={m.attributionText}>{t(Platform.OS === 'android' ? 'proposal.map.attributionGoogle' : 'proposal.map.attributionApple')}</Text>
        </View>
      </View>
    </View>
    {day.stops.length > 1 && !dayHasEstimate(day) && !hasUnavailableLeg ? <Text style={m.legendText}>{t('proposal.map.legendStraight')}</Text> : null}
    {hasUnavailableLeg && <View style={m.legend}>
      <View style={m.legendLine}>{[0, 1, 2].map(index => <View key={index} style={m.legendDash} />)}</View>
      <Text style={[m.legendText, m.flex]}>{t('proposal.map.legendUnavailable')}</Text>
    </View>}
    {selected && <View style={m.controls}>
      <CircleButton accessibilityLabel={t('proposal.map.previousA11y')} disabled={atStart} icon="back" onPress={() => step(-1)} size={44} tone="tint" />
      <Pressable
        accessibilityHint={t('proposal.stop.detailsA11y', { name: selected.name })}
        accessibilityLiveRegion="polite"
        accessibilityRole="button"
        disabled={!selected.place_id}
        onPress={() => { if (selected.place_id) onOpenPlace(selected.place_id); }}
        style={({ pressed }) => [m.current, pressed && { opacity: 0.75 }]}
      >
        <View style={m.currentThumb}>
          <View style={m.currentClip}>
            <Photo categoryCode={selectedPlace?.categoryCode} height={44} iconSize={22} image={selectedPlace?.thumbnail} name={selected.name} transition={150} variant="thumb" width={44} />
          </View>
          <NumberPin dayIndex={day.day_index - 1} number={selectedIndex + 1} size={24} style={m.currentPin} />
        </View>
        <View style={m.currentCopy}>
          <Text numberOfLines={1} style={m.currentName}>{selected.name}</Text>
          {selectedTime[0] && selectedTime[1] ? <Text numberOfLines={1} style={m.currentTime}>{`${selectedTime[0]} – ${selectedTime[1]}`}</Text> : null}
          {selected.trust_level === 'WEB_UNVERIFIED' ? <Text numberOfLines={1} style={m.currentWeb}>{t('proposal.stop.web')}</Text> : null}
        </View>
        {selected.place_id ? <Icon color={colors.textMuted} name="chevron-right" size={18} strokeWidth={2} /> : null}
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
  flex: { flex: 1 },
  shadow: { borderRadius: radii.card, backgroundColor: colors.white },
  card: { height: 260, borderRadius: radii.card, overflow: 'hidden', backgroundColor: colors.surface },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.xs, padding: spacing.xl },
  emptyText: { fontFamily: fonts.semibold, fontSize: 15, color: colors.ink, textAlign: 'center' },
  /** Selection ring (day colour), blocked ring (danger) or web ring (dashed warning) around the shared NumberPin. */
  pinWrap: { padding: 2, borderRadius: 18, borderWidth: 2, borderColor: 'transparent' },
  pinBlocked: { borderColor: colors.danger },
  pinWeb: { borderColor: colors.warning, borderStyle: 'dashed' },
  recenter: { position: 'absolute', top: spacing.sm, right: spacing.sm },
  attribution: { position: 'absolute', left: 10, bottom: 8, backgroundColor: 'rgba(255,255,255,0.88)', borderRadius: 8, paddingHorizontal: 6, paddingVertical: 2, maxWidth: '70%' },
  attributionText: { fontFamily: fonts.medium, fontSize: 11, color: colors.ink },
  legend: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: spacing.xs },
  legendLine: { flexDirection: 'row', gap: 3 },
  legendDash: { width: 7, height: 3, borderRadius: 1.5, backgroundColor: colors.danger },
  legendText: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 18, color: colors.textMuted, marginTop: spacing.xs },
  controls: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, marginTop: spacing.sm },
  current: { flex: 1, minWidth: 0, minHeight: MIN_TOUCH + 12, flexDirection: 'row', alignItems: 'center', gap: 10, paddingLeft: 6, paddingRight: 10, borderRadius: radii.card, backgroundColor: colors.white, ...elevation.floating },
  currentThumb: { width: 44, height: 44, borderRadius: radii.photo, backgroundColor: colors.surface },
  currentClip: { width: 44, height: 44, borderRadius: radii.photo, overflow: 'hidden' },
  currentPin: { position: 'absolute', top: -6, left: -6 },
  currentCopy: { flex: 1, minWidth: 0 },
  currentName: { fontFamily: fonts.semibold, fontSize: 15, lineHeight: 20, color: colors.ink },
  currentTime: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 17, color: colors.textSecondary },
  currentWeb: { fontFamily: fonts.semibold, fontSize: 12, lineHeight: 16, color: colors.warning },
});
