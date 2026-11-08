import { useCallback, useEffect, useRef, useState, type ComponentRef } from 'react';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useTranslation } from 'react-i18next';
import { Linking, Platform, Pressable, ScrollView, Share, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { CategoryBadge, CircleButton, GlassBadge, Icon, Photo, PrimaryButton, SecondaryButton, SectionHeader, Skeleton, usePhotoFailed } from '../../components/ui';
import { currentLocale } from '../../i18n';
import { ApiError, getPlace, listCategories, loadErrorKind, type LoadErrorKind } from '../../lib/api/source';
import type { Category, Citation, DescriptionSource, GeoPoint, Media, PlaceDetail, PlaceFact } from '../../lib/api/types';
import { colors } from '../../theme/colors';
import { elevation } from '../../theme/elevation';
import { radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { FactIcon, factIcon, type FactIconName } from './components/FactIcon';
import { HeroGallery } from './components/HeroGallery';
import { ScreenMessage, isNotFound } from './components/PlaceUI';
import { SourceLine, StaleBadge } from './components/SourceLine';
import { factPoint, formatFactValue, isStaleFact, type FactLabels } from './format';

type Load = { state: 'loading' } | { state: 'ready'; place: PlaceDetail } | { state: 'notFound' } | { state: 'error'; kind: LoadErrorKind };

/** Facts shown as tiles, only when KNOWN (anti-noise rule 1); ADDRESS_VI lives in the driver card. */
const tileFacts = ['OPENING_HOURS', 'ADMISSION_PRICE', 'ENTRANCE_LOCATION', 'PAYMENT_METHODS', 'DRESS_CODE', 'ACCESS_RULES'] as const;
/** Facts named once in the quiet "Not listed yet: …" line when UNKNOWN (unknown stays unknown, never invented). */
const missingFacts = ['OPENING_HOURS', 'ADMISSION_PRICE', 'ADDRESS_VI'] as const;

const HERO_HEIGHT = 380;
/** Height of the bottom action bar above the safe-area inset (scroll padding so nothing hides under it). */
const ACTION_BAR = 52 + spacing.sm * 2;

/** A place id the server rejects as malformed (422 on the path) is a place that does not exist for the user. */
const isMissingPlace = (error: unknown) => isNotFound(error) || (error instanceof ApiError && error.status === 422);

function directionsUrls({ latitude, longitude }: GeoPoint) {
  return {
    apple: `https://maps.apple.com/?daddr=${latitude},${longitude}`,
    google: `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`,
  };
}

/** SCR-033 Place card for a place opened outside a trip (API-011 only; no live status, no activities). */
export function PlaceScreen({ placeId }: { placeId: string }) {
  const { t, i18n } = useTranslation();
  const insets = useSafeAreaInsets();
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [categories, setCategories] = useState<Category[]>([]);
  const [mapsFailed, setMapsFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const language = i18n.resolvedLanguage;
  const scrollRef = useRef<ComponentRef<typeof ScrollView>>(null);

  useEffect(() => {
    let alive = true;
    setLoad({ state: 'loading' });
    getPlace(placeId)
      .then(place => { if (alive) setLoad({ place, state: 'ready' }); })
      .catch((error: unknown) => { if (alive) setLoad(isMissingPlace(error) ? { state: 'notFound' } : { kind: loadErrorKind(error), state: 'error' }); });
    listCategories().then(items => { if (alive) setCategories(items); }).catch(() => undefined);
    return () => { alive = false; };
  }, [placeId, attempt, language]);

  const goBack = useCallback(() => (router.canGoBack() ? router.back() : router.replace('/home')), []);
  const backButton = <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={goBack} />;

  if (load.state === 'loading') {
    return <View style={s.screen}>
      <StatusBar style="light" />
      <View accessibilityLabel={t('place.loading')} accessibilityLiveRegion="polite" accessible style={s.fill}>
        <Skeleton height={HERO_HEIGHT} radius={0} />
        <View style={s.skeletonBody}>
          <Skeleton height={24} width="45%" />
          <View style={s.tiles}>
            {[0, 1, 2, 3].map(index => <View key={index} style={s.skeletonTile}><Skeleton height={104} radius={radii.card} /></View>)}
          </View>
          <Skeleton height={132} radius={radii.card} />
        </View>
      </View>
      <View style={[s.floatingBack, { top: insets.top + spacing.xs }]}>{backButton}</View>
    </View>;
  }

  if (load.state !== 'ready') {
    return <View style={[s.screen, s.plain]}>
      <StatusBar style="dark" />
      <View style={[s.plainHeader, { paddingTop: insets.top + spacing.xs }]}>
        <CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={goBack} tone="tint" />
      </View>
      {load.state === 'notFound' && <ScreenMessage title={t('place.notFoundTitle')} body={t('place.notFoundBody')}>
        <PrimaryButton label={t('common.goBack')} onPress={goBack} />
      </ScreenMessage>}
      {load.state === 'error' && <ScreenMessage body={t(`common.loadError.${load.kind}`)} title={t('place.errorTitle')}>
        <PrimaryButton label={t('place.retry')} onPress={() => setAttempt(n => n + 1)} />
      </ScreenMessage>}
    </View>;
  }

  const { place } = load;
  const locale = currentLocale();
  const category = categories.find(item => item.code === place.category_code);
  const categoryName = category ? (locale === 'vi' ? category.name_vi : category.name_en) : undefined;
  const otherName = locale === 'vi' ? place.name_en : place.name_vi;
  const facts = new Map(place.facts.map(fact => [fact.field_code, fact]));
  const labels: FactLabels = {
    allDay: t('place.hours.allDay'),
    child: price => t('place.facts.childPrice', { price }),
    closed: days => t('place.hours.closed', { days }),
    everyDay: t('place.hours.everyDay'),
    free: t('place.facts.free'),
  };
  const knownValue = (fact: PlaceFact | undefined) => (fact?.knowledge_state === 'KNOWN' ? formatFactValue(fact.value, locale, labels) : null);
  const address = facts.get('ADDRESS_VI');
  const addressText = knownValue(address);
  const entrancePoint = place.entrance_location ?? factPoint(facts.get('ENTRANCE_LOCATION'));
  const target = entrancePoint ?? place.location;

  // Known facts only, as tiles (anti-noise rule 1). Unknown ones are named once, quietly, below the tiles.
  const tiles: FactTile[] = [];
  for (const code of tileFacts) {
    const fact = facts.get(code);
    if (fact?.knowledge_state !== 'KNOWN') continue;
    const value = code === 'ENTRANCE_LOCATION' ? (entrancePoint ? t('place.facts.entrancePinned') : null) : knownValue(fact);
    if (value) tiles.push({ code, icon: factIcon(code), label: t(`place.facts.${code}`), stale: isStaleFact(fact), value });
  }
  if (place.visit_minutes_suggested) {
    tiles.splice(Math.min(1, tiles.length), 0, { code: 'VISIT', icon: 'walk', label: t('place.quick.visit'), value: t('place.visitAbout', { count: place.visit_minutes_suggested }) });
  }
  const missing = missingFacts.filter(code => (facts.get(code)?.knowledge_state ?? 'UNKNOWN') === 'UNKNOWN').map(code => t(`place.missing.${code}`));

  const photos = place.media?.filter(media => media.media_asset_id !== place.thumbnail?.media_asset_id) ?? [];
  // Short area name for the hero chip: "Hội An beaches and islands (An Bàng, …)" → "Hội An beaches and islands".
  const areaName = place.area ? (locale === 'vi' ? place.area.name_vi : place.area.name_en).replace(/\s*\(.*\)\s*$/, '') : null;
  const sources = uniqueSources(place.facts);

  async function openDirections() {
    setMapsFailed(false);
    const urls = directionsUrls(target);
    const order = Platform.OS === 'ios' ? [urls.apple, urls.google] : [urls.google, urls.apple];
    for (const url of order) {
      try { await Linking.openURL(url); return; } catch { /* try the next maps app */ }
    }
    setMapsFailed(true);
  }

  function share() {
    const lines = [place.name_vi, addressText, directionsUrls(place.location).google].filter(Boolean);
    Share.share({ message: lines.join('\n') }).catch(() => undefined);
  }

  const hasSources = sources.length > 0 || place.attributions.length > 0;

  return <View style={s.screen}>
    <StatusBar style="light" />
    <ScrollView ref={scrollRef} contentContainerStyle={[s.scroll, { paddingBottom: ACTION_BAR + insets.bottom + spacing.lg }]} showsVerticalScrollIndicator={false}>
      <HeroGallery
        categoryCode={place.category_code}
        height={HERO_HEIGHT}
        media={place.media}
        name={place.name}
        thumbnail={place.thumbnail}
        title={place.name}
        topLeft={backButton}
        topRight={<CircleButton accessibilityLabel={t('place.share')} icon="share" onPress={share} />}
      >
        {otherName !== place.name && <Text numberOfLines={2} style={s.otherName}>{otherName}</Text>}
        {/* EN only: the English name is the Vietnamese proper name because no source gives an English one (never translated). */}
        {locale === 'en' && place.name_is_source_fallback ? <Text numberOfLines={2} style={s.nameNote}>{t('place.nameSourceFallback')}</Text> : null}
        {categoryName || areaName ? <View style={s.tags}>
          {categoryName ? <CategoryBadge code={place.category_code} label={categoryName} variant="chip" /> : null}
          {areaName ? <GlassBadge icon="map-pin" label={areaName} /> : null}
        </View> : null}
      </HeroGallery>

      <View style={s.inner}>
        {tiles.length > 0 || missing.length > 0 ? <>
          <SectionHeader style={s.firstSection} title={t('place.facts.title')} />
          {tiles.length > 0 ? <View style={s.tiles}>
            {tiles.map(tile => <View
              accessibilityLabel={`${tile.label}: ${tile.value}`}
              accessible
              key={tile.code}
              style={[s.tile, tile.value.length > 24 && s.tileWide]}
            >
              <View style={s.tileHead}>
                <View style={[s.tileIcon, { backgroundColor: tone.bg }]}><FactIcon color={tone.fg} name={tile.icon} size={18} /></View>
              </View>
              <Text maxFontSizeMultiplier={1.4} style={s.tileLabel}>{tile.label}</Text>
              <Text maxFontSizeMultiplier={1.4} selectable style={s.tileValue}>{tile.value}</Text>
              {tile.stale ? <StaleBadge /> : null}
            </View>)}
          </View> : null}
          {missing.length > 0 ? <Text style={s.missing}>{t('place.missing.line', { items: missing.join(', ') })}</Text> : null}
        </> : null}

        <View accessibilityLabel={addressText ? t('place.driver.a11y', { address: addressText, name: place.name_vi }) : t('place.driver.a11yName', { name: place.name_vi })} accessible style={s.driver}>
          <View style={s.driverHead}>
            <View style={s.driverIcon}><Icon color={colors.white} name="car" size={18} /></View>
            <Text style={s.driverCap}>{t('place.driver.cap')}</Text>
          </View>
          <Text style={s.driverName}>{place.name_vi}</Text>
          {addressText ? <Text style={s.driverAddress}>{addressText}</Text> : null}
          {address && addressText && isStaleFact(address) ? <StaleBadge onDark /> : null}
        </View>

        <SectionHeader style={s.section} title={t('place.description.title')} />
        {place.description
          ? <Text style={s.body}>{place.description}</Text>
          : <Text style={s.noDescription}>{t('place.description.none')}</Text>}
        {place.description_source ? <DescriptionCredit source={place.description_source} /> : null}

        {photos.length > 0 && <>
          <SectionHeader style={s.section} title={t('place.media.title')} />
          <ScrollView contentContainerStyle={s.mediaRow} horizontal showsHorizontalScrollIndicator={false} style={s.mediaScroll}>
            {photos.map(media => <MediaItem key={media.media_asset_id} categoryCode={place.category_code} media={media} name={place.name} />)}
          </ScrollView>
        </>}

        {hasSources && <View>
          <SectionHeader style={s.section} title={t('place.attributions.title')} />
          <View style={s.credits}>
            {sources.map((source, index) => <SourceLine citation={source} key={`${source.source_revision_id}-${index}`} />)}
            {place.attributions.map(item => <Attribution item={item} key={`${item.publisher}-${item.attribution_text}`} />)}
          </View>
        </View>}
      </View>
    </ScrollView>

    <View style={[s.actionBar, elevation.floating, { paddingBottom: insets.bottom + spacing.sm }]}>
      <View style={s.barInner}>
        {mapsFailed && <Text accessibilityRole="alert" style={s.error}>{t('place.directionsFailed')}</Text>}
        <View style={s.actions}>
          <SecondaryButton icon="chat-text" label={t('place.askGuide')} onPress={() => router.push({ params: { placeId: place.id }, pathname: '/guide' })} style={s.action} />
          <PrimaryButton accessibilityHint={t('place.directionsHint')} icon="navigation" label={t('place.directions')} onPress={() => void openDirections()} style={s.action} />
        </View>
      </View>
    </View>
  </View>;
}

type FactTile = { code: string; icon: FactIconName; label: string; value: string; stale?: boolean };

/** Every distinct source cited by the place's facts, newest first per source revision. */
function uniqueSources(facts: PlaceFact[]): Citation[] {
  const seen = new Set<string>();
  const out: Citation[] = [];
  for (const fact of facts) {
    for (const source of fact.sources) {
      const key = source.source_revision_id ?? `${source.publisher}|${source.locator ?? ''}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(source);
    }
  }
  return out;
}

/**
 * 1.0.5 (DEC-031/DEC-032): one line under a description naming where it came from, e.g.
 * "From Wikivoyage (en) · CC BY-SA 4.0", linking the source page. An owner-written description is
 * attributed to Gonarra. The text itself is verbatim, never model-written.
 */
function DescriptionCredit({ source }: { source: DescriptionSource }) {
  const { t } = useTranslation();
  const label = source.provider === 'OWNER'
    ? t('place.description.owner')
    : t('place.description.source', { license: source.license_code, publisher: source.publisher });
  const url = [source.url, source.license_url].find((value): value is string => typeof value === 'string' && /^https?:\/\//i.test(value.trim()));
  if (!url) return <Text style={s.descriptionCredit}>{label}</Text>;
  return <Pressable
    accessibilityHint={t('place.source.openLinkHint')}
    accessibilityLabel={label}
    accessibilityRole="link"
    hitSlop={{ bottom: 6, top: 6 }}
    onPress={() => { Linking.openURL(url).catch(() => undefined); }}
    style={({ pressed }) => [s.descriptionCreditLink, pressed && { opacity: 0.6 }]}
  >
    <Text style={[s.descriptionCredit, s.linkText]}>{label}</Text>
    <Icon color={colors.primary} name="share" size={12} />
  </Pressable>;
}

/** Licence credit; the publisher's homepage opens in the browser when it has one. */
function Attribution({ item }: { item: PlaceDetail['attributions'][number] }) {
  const { t } = useTranslation();
  const text = `${item.publisher} — ${item.attribution_text}${item.license_code ? ` (${item.license_code})` : ''}`;
  const url = item.homepage_url && /^https?:\/\//i.test(item.homepage_url) ? item.homepage_url : null;
  if (!url) return <Text style={s.attribution}>{text}</Text>;
  return <Pressable
    accessibilityHint={t('place.source.openLinkHint')}
    accessibilityLabel={text}
    accessibilityRole="link"
    onPress={() => { Linking.openURL(url).catch(() => undefined); }}
    style={({ pressed }) => [s.attributionLink, pressed && { opacity: 0.6 }]}
  >
    <Text style={[s.attribution, s.linkText]}>{text}</Text>
    <Icon color={colors.primary} name="share" size={14} />
  </Pressable>;
}

/** One extra photo with its credit; a photo that fails to load shows the category tile and drops the credit. */
function MediaItem({ media, name, categoryCode }: { media: Media; name: string; categoryCode: string }) {
  const [failed, onError] = usePhotoFailed(media);
  return <View style={s.mediaItem}>
    <View style={s.mediaImage}>
      <Photo accessibilityLabel={media.alt_text ?? name} categoryCode={categoryCode} height={140} image={media} name={name} onError={onError} width={200} />
    </View>
    {failed ? null : <Text numberOfLines={2} style={s.caption}>{media.attribution_text}</Text>}
  </View>;
}

const tone = { bg: colors.primarySoft, fg: colors.primary };

const s = StyleSheet.create({
  action: { flex: 1, paddingHorizontal: spacing.sm },
  actionBar: { backgroundColor: colors.white, bottom: 0, left: 0, paddingHorizontal: spacing.md, paddingTop: spacing.sm, position: 'absolute', right: 0 },
  actions: { flexDirection: 'row', gap: spacing.xs },
  attribution: { ...typography.caption, color: colors.textSecondary },
  attributionLink: { alignItems: 'center', flexDirection: 'row', gap: 6, minHeight: 44 },
  barInner: { alignSelf: 'center', maxWidth: 480, width: '100%' },
  body: { ...typography.body, color: colors.ink, fontSize: 17, lineHeight: 26 },
  descriptionCredit: { ...typography.caption, color: colors.textSecondary, marginTop: spacing.xs },
  descriptionCreditLink: { alignItems: 'center', alignSelf: 'flex-start', flexDirection: 'row', gap: 4, minHeight: 32 },
  noDescription: { ...typography.body, color: colors.textSecondary },
  caption: { ...typography.caption, fontSize: 12, marginTop: 6 },
  credits: { backgroundColor: colors.surface, borderRadius: radii.card, gap: 2, paddingHorizontal: spacing.md, paddingVertical: spacing.xs },
  driver: { backgroundColor: colors.primary, borderRadius: radii.card, gap: 4, marginTop: spacing.xl, padding: spacing.lg },
  driverAddress: { color: colors.white, fontFamily: fonts.medium, fontSize: 20, lineHeight: 28 },
  driverCap: { color: 'rgba(255,255,255,0.92)', flexShrink: 1, fontFamily: fonts.semibold, fontSize: 15, lineHeight: 20 },
  driverHead: { alignItems: 'center', flexDirection: 'row', gap: 10, marginBottom: 4 },
  driverIcon: { alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.18)', borderRadius: 16, height: 32, justifyContent: 'center', width: 32 },
  driverName: { color: colors.white, fontFamily: fonts.bold, fontSize: 28, letterSpacing: -0.4, lineHeight: 34 },
  error: { color: colors.danger, fontFamily: fonts.medium, fontSize: 14, marginBottom: 8, textAlign: 'center' },
  fill: { flex: 1 },
  firstSection: { marginBottom: spacing.sm, marginTop: spacing.lg },
  floatingBack: { left: spacing.md, position: 'absolute' },
  inner: { alignSelf: 'center', maxWidth: 480, paddingHorizontal: spacing.lg, width: '100%' },
  linkText: { color: colors.primary, flexShrink: 1 },
  mediaImage: { borderRadius: radii.photo, height: 140, overflow: 'hidden', width: 200 },
  mediaItem: { width: 200 },
  mediaRow: { gap: spacing.sm, paddingHorizontal: spacing.lg },
  mediaScroll: { marginHorizontal: -spacing.lg },
  missing: { ...typography.caption, color: colors.textSecondary, marginTop: spacing.xs },
  nameNote: { color: 'rgba(255,255,255,0.86)', fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, marginTop: 2 },
  otherName: { color: 'rgba(255,255,255,0.92)', fontFamily: fonts.medium, fontSize: 17, lineHeight: 22, marginTop: 2 },
  plain: { backgroundColor: colors.canvas },
  plainHeader: { paddingHorizontal: spacing.md },
  screen: { backgroundColor: colors.canvas, flex: 1 },
  scroll: { paddingBottom: spacing.xxl },
  section: { marginBottom: spacing.sm, marginTop: spacing.xl },
  skeletonBody: { gap: spacing.md, padding: spacing.lg },
  skeletonTile: { flexBasis: '47%', flexGrow: 1 },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: spacing.xs },
  tile: { backgroundColor: colors.surface, borderRadius: radii.card, flexBasis: '47%', flexGrow: 1, gap: 2, minHeight: 104, padding: spacing.sm },
  tileWide: { flexBasis: '100%' },
  tileHead: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  tileIcon: { alignItems: 'center', borderRadius: radii.iconTile, height: 36, justifyContent: 'center', width: 36 },
  tileLabel: { ...typography.micro, color: colors.textSecondary },
  tileValue: { color: colors.ink, fontFamily: fonts.semibold, fontSize: 15, lineHeight: 20 },
  tiles: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
});
