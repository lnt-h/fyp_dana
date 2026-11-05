import { Image } from 'expo-image';
import { router, useFocusEffect } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Alert, Pressable, RefreshControl, ScrollView, SectionList, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';

import { Icon, PrimaryButton, SectionHeader, type IconName } from '../../components/ui';
import { useAccount } from '../account/AccountContext';
import { SignInGate } from '../auth/SignInGate';
import { useTabBarClearance } from '../home/components/HomeTabBar';
import { ApiError, getTrip, listCities, listTrips } from '../../lib/api/source';
import type { City, CityCode, Trip } from '../../lib/api/types';
import { CITY_IMAGES } from '../../lib/images/cityImages';
import { resolveImage } from '../../lib/images/imagekit';
import { colors } from '../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { TripCard, TripCardSkeleton } from './TripCard';
import { formatTripDates, isPastTrip, isTripToday, todayInVietnam } from './tripDates';

const MAX_WIDTH = 480;
const GUTTER = spacing.xl;
/** Error text on white (6.1:1). */
const errorText = colors.danger;

/**
 * Trips deleted this session. Fixture-only: there is no `deleteTrip` (API-016) in the data source yet, so a deleted
 * row is hidden locally until the app restarts.
 */
const deletedTripIds = new Set<string>();

type Load = 'idle' | 'loading' | 'ready' | 'error';
type Section = { key: 'upcoming' | 'past'; data: Trip[] };

/** Compact ink pill for the header "+ New trip" action (44 pt). */
function NewTripButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable accessibilityLabel={label} accessibilityRole="button" hitSlop={4} onPress={onPress} style={({ pressed }) => [styles.newTrip, pressed && styles.newTripPressed]}>
      <Svg aria-hidden={true} height={18} viewBox="0 0 24 24" width={18}>
        <Path d="M12 5v14M5 12h14" stroke={colors.white} strokeLinecap="round" strokeWidth={2.4} />
      </Svg>
      <Text numberOfLines={1} style={styles.newTripText}>{label}</Text>
    </Pressable>
  );
}

/** Photo-topped panel used by the empty and guest states. */
function PhotoPanel({ code, title, body, action, onAction, icon }: { code: CityCode; title: string; body: string; action: string; onAction: () => void; icon: IconName }) {
  const photo = resolveImage(CITY_IMAGES[code], { height: 168, width: 432 });
  return (
    <View style={styles.panel}>
      <View style={styles.panelPhoto}>
        {photo ? <Image contentFit="cover" placeholder={photo.placeholder} source={photo.source} style={StyleSheet.absoluteFill} transition={200} /> : null}
        <LinearGradient colors={['rgba(7,21,30,0)', 'rgba(7,21,30,0.45)']} style={StyleSheet.absoluteFill} />
        <View style={styles.panelIcon}>
          <Icon color={colors.tealText} name={icon} size={26} />
        </View>
      </View>
      <View style={styles.panelBodyWrap}>
        <Text accessibilityRole="header" style={styles.panelTitle}>{title}</Text>
        <Text style={styles.panelBody}>{body}</Text>
        <PrimaryButton label={action} onPress={onAction} style={styles.panelAction} />
      </View>
    </View>
  );
}

/** SCR-031 My trips: saved trips and drafts split into Upcoming and Past, open, delete, start a new trip. */
export function TripsScreen() {
  const { t, i18n } = useTranslation();
  const insets = useSafeAreaInsets();
  const clearance = useTabBarClearance();
  const { width: windowWidth } = useWindowDimensions();
  const cardWidth = Math.min(windowWidth - GUTTER * 2, MAX_WIDTH);
  const { isLoaded, isSignedIn } = useAccount();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [state, setState] = useState<Load>('idle');
  const [refreshing, setRefreshing] = useState(false);
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [notice, setNotice] = useState('');
  const [gateOpen, setGateOpen] = useState(false);
  const loaded = useRef(false);

  const load = useCallback(async (mode: 'initial' | 'refresh' | 'silent') => {
    if (mode === 'initial') setState('loading');
    if (mode === 'refresh') setRefreshing(true);
    try {
      const [items, cityList] = await Promise.all([listTrips(), listCities()]);
      setTrips(items.filter(trip => !deletedTripIds.has(trip.id)));
      setCities(cityList);
      setState('ready');
      loaded.current = true;
    } catch {
      // A silent refresh keeps the list already shown; otherwise show the error banner (S-1).
      if (mode !== 'silent' || !loaded.current) setState('error');
    } finally {
      setRefreshing(false);
    }
  }, []);

  // Load on first focus, then refresh quietly when the tab regains focus (e.g. after Save on SCR-029).
  useFocusEffect(useCallback(() => {
    if (!isSignedIn) return;
    void load(loaded.current ? 'silent' : 'initial');
  }, [isSignedIn, load]));

  const isVi = i18n.resolvedLanguage === 'vi';
  const cityOf = useCallback((cityId: string) => cities.find(item => item.id === cityId), [cities]);
  const cityName = useCallback((cityId: string) => {
    const city = cityOf(cityId);
    return city ? (isVi ? city.name_vi : city.name_en) : '';
  }, [cityOf, isVi]);
  const tripTitle = useCallback((trip: Trip) => trip.title?.trim() || t('trips.card.title', { city: cityName(trip.city_id), count: trip.day_count }), [cityName, t]);

  const sections = useMemo<Section[]>(() => {
    const today = todayInVietnam();
    const upcoming = trips.filter(trip => !isPastTrip(trip, today)).sort((a, b) => a.start_date.localeCompare(b.start_date));
    const past = trips.filter(trip => isPastTrip(trip, today)).sort((a, b) => b.start_date.localeCompare(a.start_date));
    return ([{ data: upcoming, key: 'upcoming' }, { data: past, key: 'past' }] as Section[]).filter(section => section.data.length > 0);
  }, [trips]);

  async function openTrip(trip: Trip) {
    if (openingId) return;
    setOpeningId(trip.id); setNotice('');
    try {
      // API-014: a draft with an active preview resumes that preview; a saved trip opens SCR-024 in read mode.
      const detail = await getTrip(trip.id);
      const previewId = detail.active_preview_id ?? detail.id;
      router.push({ params: { mode: detail.active_preview_id ? 'draft' : 'saved', previewId, tripId: detail.id }, pathname: '/plan/[previewId]/proposal' });
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        deletedTripIds.add(trip.id);
        setTrips(current => current.filter(item => item.id !== trip.id));
        setNotice(t('trips.error.notFound'));
      } else {
        setNotice(t('trips.error.open'));
      }
    } finally {
      setOpeningId(null);
    }
  }

  function confirmDelete(trip: Trip) {
    Alert.alert(t('trips.delete.title', { name: tripTitle(trip) }), t('trips.delete.body'), [
      { style: 'cancel', text: t('trips.delete.keep') },
      {
        onPress: () => {
          // Fixture-only removal; API-016 `DELETE /v1/trips/{trip_id}` (204 or 404 = done) lands with the API client.
          deletedTripIds.add(trip.id);
          setTrips(current => current.filter(item => item.id !== trip.id));
          setNotice(t('trips.delete.done'));
        },
        style: 'destructive',
        text: t('trips.delete.confirm'),
      },
    ]);
  }

  const newTrip = () => router.push('/plan/new');
  const contentStyle = [styles.content, { paddingBottom: clearance + spacing.xl, paddingTop: insets.top + spacing.lg }];
  const background = (
    <>
      <StatusBar style="dark" />
    </>
  );

  // Guest via deep link (the tab bar already gates the tab, S-3).
  if (isLoaded && !isSignedIn) {
    return (
      <View style={styles.screen}>
        {background}
        <ScrollView contentContainerStyle={contentStyle}>
          <View style={styles.inner}>
            <Text accessibilityRole="header" style={styles.title}>{t('trips.title')}</Text>
            <Text style={styles.subtitle}>{t('trips.subtitleEmpty')}</Text>
            <View style={styles.stateGap}>
              <PhotoPanel action={t('trips.guest.action')} body={t('trips.guest.body')} code="hue" icon="lantern" onAction={() => setGateOpen(true)} title={t('trips.guest.title')} />
            </View>
          </View>
        </ScrollView>
        <SignInGate feature={gateOpen ? 'trips' : null} onClose={() => setGateOpen(false)} />
      </View>
    );
  }

  const showSkeleton = !isLoaded || state === 'idle' || state === 'loading';
  const hasTrips = state === 'ready' && trips.length > 0;
  const subtitle = hasTrips ? t('trips.subtitle', { count: trips.length }) : t('trips.subtitleEmpty');

  const header = (
    <View style={styles.inner}>
      <View style={styles.titleRow}>
        <Text accessibilityRole="header" numberOfLines={1} style={[styles.title, styles.titleFlex]}>{t('trips.title')}</Text>
        {hasTrips && <NewTripButton label={t('trips.newTrip')} onPress={newTrip} />}
      </View>
      <Text style={styles.subtitle}>{showSkeleton ? t('trips.loading') : subtitle}</Text>
      {state === 'error' && (
        <View accessibilityRole="alert" style={styles.banner}>
          <Icon color={errorText} name="warning" size={20} />
          <Text style={styles.bannerText}>{t('trips.error.load')}</Text>
          <Pressable accessibilityRole="button" hitSlop={4} onPress={() => void load('initial')} style={({ pressed }) => [styles.retry, pressed && { opacity: 0.7 }]}>
            <Text style={styles.link}>{t('trips.error.retry')}</Text>
          </Pressable>
        </View>
      )}
      {!!notice && (
        <View accessibilityLiveRegion="polite" style={styles.notice}>
          <Icon color={colors.tealText} name="info" size={18} />
          <Text style={styles.noticeText}>{notice}</Text>
        </View>
      )}
      {showSkeleton && (
        <View accessibilityLabel={t('trips.loading')} accessibilityRole="progressbar" style={styles.stateGap}>
          <TripCardSkeleton />
          <TripCardSkeleton />
          <TripCardSkeleton />
        </View>
      )}
    </View>
  );

  return (
    <View style={styles.screen}>
      {background}
      <SectionList
        ListEmptyComponent={state === 'ready' ? (
          <View style={[styles.inner, styles.stateGap]}>
            <PhotoPanel action={t('trips.empty.action')} body={t('trips.empty.body')} code="hoi-an" icon="map-pin" onAction={newTrip} title={t('trips.empty.title')} />
          </View>
        ) : undefined}
        ListHeaderComponent={header}
        contentContainerStyle={contentStyle}
        keyExtractor={trip => trip.id}
        refreshControl={<RefreshControl colors={[colors.audioTeal]} onRefresh={() => void load('refresh')} refreshing={refreshing} tintColor={colors.audioTeal} />}
        renderItem={({ item }) => {
          const city = cityOf(item.city_id);
          return (
            <View style={styles.inner}>
              <TripCard
                cityCode={city?.code ?? null}
                cityName={cityName(item.city_id)}
                dates={formatTripDates(t, item)}
                isToday={isTripToday(item)}
                onDelete={() => confirmDelete(item)}
                onOpen={() => isTripToday(item) ? router.push({ pathname: '/trip/[tripId]/today', params: { tripId: item.id } }) : void openTrip(item)}
                opening={openingId === item.id}
                title={tripTitle(item)}
                trip={item}
                width={cardWidth}
              />
            </View>
          );
        }}
        renderSectionHeader={({ section }) => (
          <View style={styles.inner}>
            <SectionHeader
              style={styles.section}
              subtitle={t('trips.sections.count', { count: section.data.length })}
              title={t(`trips.sections.${section.key}`)}
            />
          </View>
        )}
        sections={showSkeleton || state === 'error' ? [] : sections}
        showsVerticalScrollIndicator={false}
        stickySectionHeadersEnabled={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  banner: { alignItems: 'center', backgroundColor: colors.white, borderColor: '#F1D3D3', borderRadius: radii.inset, borderWidth: 1, flexDirection: 'row', gap: spacing.sm, marginTop: spacing.lg, paddingLeft: spacing.md },
  bannerText: { color: errorText, flex: 1, fontFamily: fonts.regular, fontSize: 15, lineHeight: 21, paddingVertical: spacing.sm },
  content: { flexGrow: 1, paddingHorizontal: GUTTER },
  inner: { alignSelf: 'center', maxWidth: MAX_WIDTH, width: '100%' },
  link: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 15 },
  newTrip: { alignItems: 'center', backgroundColor: colors.ink, borderRadius: radii.pill, flexDirection: 'row', flexShrink: 0, gap: 6, height: MIN_TOUCH, paddingHorizontal: spacing.md },
  newTripPressed: { opacity: 0.88, transform: [{ scale: 0.98 }] },
  newTripText: { color: colors.white, fontFamily: fonts.bold, fontSize: 15 },
  notice: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: radii.inset, flexDirection: 'row', gap: spacing.xs, marginTop: spacing.md, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  noticeText: { color: colors.ink, flex: 1, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20 },
  panel: { backgroundColor: colors.white, borderColor: colors.hairline, borderRadius: radii.card, borderWidth: 1 },
  panelAction: { alignSelf: 'stretch', marginTop: spacing.lg },
  panelBody: { ...typography.body, color: colors.textMuted, marginTop: spacing.xs, textAlign: 'center' },
  panelBodyWrap: { alignItems: 'center', paddingBottom: spacing.xl, paddingHorizontal: spacing.xl, paddingTop: 36 },
  panelIcon: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.surfaceTint, borderRadius: 28, borderWidth: 3, bottom: -28, height: 56, justifyContent: 'center', left: '50%', marginLeft: -28, position: 'absolute', width: 56 },
  panelPhoto: { backgroundColor: colors.surfaceTint, borderTopLeftRadius: radii.card, borderTopRightRadius: radii.card, height: 168 },
  panelTitle: { ...typography.headline, fontSize: 22, lineHeight: 28, textAlign: 'center' },
  retry: { alignItems: 'center', justifyContent: 'center', minHeight: MIN_TOUCH, paddingHorizontal: spacing.md },
  screen: { backgroundColor: colors.canvas, flex: 1 },
  section: { marginBottom: spacing.sm, marginTop: spacing.xl },
  stateGap: { marginTop: spacing.xl },
  subtitle: { ...typography.body, color: colors.textMuted, marginTop: spacing.xxs },
  title: { ...typography.display, fontSize: 36, lineHeight: 42 },
  titleFlex: { flexShrink: 1 },
  titleRow: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm, justifyContent: 'space-between' },
});
