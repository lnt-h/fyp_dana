import { useCallback, useEffect, useRef, useState, type ComponentRef } from 'react';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useTranslation } from 'react-i18next';
import { Linking, Platform, Pressable, ScrollView, Share, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { CircleButton, GlassBadge, Icon, type IconName, categoryIcon, PrimaryButton, SecondaryButton, SectionHeader, Skeleton } from '../../components/ui';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { currentLocale, type AppLocale } from '../../i18n';
import { getPlace, listCategories } from '../../lib/api/source';
import type { Category, GeoPoint, PlaceDetail, PlaceFact } from '../../lib/api/types';
import { resolveImage } from '../../lib/images/imagekit';
import { colors } from '../../theme/colors';
import { elevation } from '../../theme/elevation';
import { radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { FactIcon, factIcon, type FactIconName } from './components/FactIcon';
import { HeroGallery } from './components/HeroGallery';
import { ScreenMessage, isNotFound } from './components/PlaceUI';
import { SourceLine, StaleBadge, UnknownBadge } from './components/SourceLine';
import { factPoint, formatFactValue, isStaleFact } from './format';

type Load = { state: 'loading' } | { state: 'ready'; place: PlaceDetail } | { state: 'notFound' } | { state: 'error' };

/** Facts always listed (UNKNOWN shown as *chưa rõ*); ADDRESS_VI lives in the driver panel. */
const coreFacts = ['OPENING_HOURS', 'ADMISSION_PRICE', 'ENTRANCE_LOCATION'] as const;
/** Other operational facts, listed only when KNOWN (SCR-033). */
const optionalFacts = ['PAYMENT_METHODS', 'DRESS_CODE', 'ACCESS_RULES'] as const;

const HERO_HEIGHT = 380;
const surfaceBorder = colors.hairline;

const unknownFact = (field_code: string): PlaceFact => ({ field_code, freshness: 'CURRENT', knowledge_state: 'UNKNOWN', sources: [], value: null });

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
  const language = i18n.language;
  const reducedMotion = useReducedMotion();
  const scrollRef = useRef<ComponentRef<typeof ScrollView>>(null);
  // Layout offsets for the "Sources: …" link: the inner column inside the scroll, then the credits inside the column.
  const innerY = useRef(0);
  const attributionsY = useRef(0);

  useEffect(() => {
    let alive = true;
    setLoad({ state: 'loading' });
    getPlace(placeId)
      .then(place => { if (alive) setLoad({ place, state: 'ready' }); })
      .catch((error: unknown) => { if (alive) setLoad({ state: isNotFound(error) ? 'notFound' : 'error' }); });
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
          <Skeleton height={56} radius={radii.inset} />
          <Skeleton height={150} radius={radii.card} />
          <Skeleton height={220} radius={radii.card} />
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
      {load.state === 'error' && <ScreenMessage title={t('place.errorTitle')}>
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
  const address = facts.get('ADDRESS_VI') ?? unknownFact('ADDRESS_VI');
  const addressText = address.knowledge_state === 'KNOWN' ? formatFactValue(address.value, locale) : null;
  const entrancePoint = place.entrance_location ?? factPoint(facts.get('ENTRANCE_LOCATION'));
  const target = entrancePoint ?? place.location;
  const listed: PlaceFact[] = [
    ...coreFacts.map(code => facts.get(code) ?? unknownFact(code)),
    ...optionalFacts.flatMap(code => { const fact = facts.get(code); return fact?.knowledge_state === 'KNOWN' ? [fact] : []; }),
  ];
  const quickValue = (code: string) => {
    const fact = facts.get(code);
    return fact?.knowledge_state === 'KNOWN' ? formatFactValue(fact.value, locale) : null;
  };
  const quick: { key: string; icon: FactIconName; label: string; value: string | null }[] = [
    { icon: 'clock', key: 'hours', label: t('place.quick.hours'), value: quickValue('OPENING_HOURS') },
    { icon: 'walk', key: 'visit', label: t('place.quick.visit'), value: place.visit_minutes_suggested ? t('place.visitAbout', { count: place.visit_minutes_suggested }) : null },
    { icon: 'ticket', key: 'price', label: t('place.quick.price'), value: quickValue('ADMISSION_PRICE') },
  ];
  const photos = place.media?.filter(media => media.media_asset_id !== place.thumbnail?.media_asset_id) ?? [];
  const areaName = place.area ? (locale === 'vi' ? place.area.name_vi : place.area.name_en) : null;
  const publishers = [...new Set(place.attributions.map(item => item.publisher).filter(Boolean))];
  const tags: { key: string; label: string; icon: IconName }[] = [
    ...(categoryName ? [{ icon: 'heritage' as const, key: 'category', label: categoryName }] : []),
    ...(areaName ? [{ icon: 'map-pin' as const, key: 'area', label: areaName }] : []),
    ...(place.trust_level === 'VERIFIED' ? [{ icon: 'shield' as const, key: 'trust', label: t('place.tags.verified') }] : []),
  ];

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

  return <View style={s.screen}>
    <StatusBar style="light" />
    <ScrollView ref={scrollRef} contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>
      <HeroGallery
        fallbackIcon={categoryIcon(place.category_code)}
        height={HERO_HEIGHT}
        media={place.media}
        name={place.name}
        thumbnail={place.thumbnail}
        title={place.name}
        topLeft={backButton}
        topRight={<CircleButton accessibilityLabel={t('place.share')} icon="share" onPress={share} />}
      >
        {otherName !== place.name && <Text numberOfLines={1} style={s.otherName}>{otherName}</Text>}
        {tags.length ? <View style={s.tags}>
          {tags.map(tag => <GlassBadge icon={tag.key === 'category' ? categoryIcon(place.category_code) : tag.icon} key={tag.key} label={tag.label} />)}
        </View> : null}
      </HeroGallery>

      <View onLayout={event => { innerY.current = event.nativeEvent.layout.y; }} style={s.inner}>
        <View style={s.quickRow}>
          {quick.map(item => <View accessibilityLabel={`${item.label}: ${item.value ?? t('place.unknown')}`} accessible key={item.key} style={s.quick}>
            <View style={s.quickIcon}><FactIcon name={item.icon} size={18} /></View>
            <Text numberOfLines={1} style={s.quickLabel}>{item.label}</Text>
            <Text numberOfLines={2} style={[s.quickValue, !item.value && s.muted]}>{item.value ?? t('place.unknown')}</Text>
          </View>)}
        </View>
        {publishers.length ? <Pressable
          accessibilityHint={t('place.sources.hint')}
          accessibilityRole="link"
          onPress={() => scrollRef.current?.scrollTo({ animated: !reducedMotion, y: Math.max(0, innerY.current + attributionsY.current - spacing.xxxl - spacing.md) })}
          style={({ pressed }) => [s.sourcesLine, pressed && { opacity: 0.6 }]}
        >
          <Icon color={colors.tealText} name="doc" size={16} />
          <Text numberOfLines={2} style={s.sourcesText}>{t('place.sources.line', { publishers: publishers.join(', ') })}</Text>
          <Icon color={colors.tealText} name="chevron-down" size={16} />
        </Pressable> : null}

        <View accessibilityLabel={t('place.driver.a11y', { address: addressText ?? t('place.driver.addressUnknown'), name: place.name_vi })} accessible style={s.driver}>
          <View style={s.driverHead}>
            <View style={s.driverIcon}><Icon color={colors.white} name="car" size={20} /></View>
            <Text style={s.driverCap}>{t('place.driver.cap')}</Text>
          </View>
          <Text style={s.driverName}>{place.name_vi}</Text>
          <Text style={[s.driverAddress, !addressText && s.driverUnknown]}>{addressText ?? t('place.driver.addressUnknown')}</Text>
          {address.knowledge_state === 'KNOWN' && isStaleFact(address) && <StaleBadge onDark />}
        </View>
        {address.sources[0] && <View style={s.driverSource}><SourceLine citation={address.sources[0]} stale={isStaleFact(address)} /></View>}

        <SectionHeader style={s.section} title={t('place.facts.title')} />
        <View style={s.card}>
          {listed.map((fact, index) => <FactRow fact={fact} first={index === 0} key={fact.field_code} locale={locale} />)}
        </View>

        {!!place.description && <>
          <SectionHeader style={s.section} title={t('place.description.title')} />
          <Text style={s.body}>{place.description}</Text>
          <Text style={s.note}>{t('place.description.note')}</Text>
        </>}

        {photos.length > 0 && <>
          <SectionHeader style={s.section} title={t('place.media.title')} />
          <ScrollView contentContainerStyle={s.mediaRow} horizontal showsHorizontalScrollIndicator={false} style={s.mediaScroll}>
            {photos.map(media => {
              const resolved = resolveImage(media, { height: 140, width: 200 });
              return <View key={media.media_asset_id} style={s.mediaItem}>
                {resolved
                  ? <Image accessibilityLabel={media.alt_text ?? place.name} contentFit="cover" placeholder={resolved.placeholder} source={resolved.source} style={s.mediaImage} transition={200} />
                  : <View style={[s.mediaImage, s.mediaEmpty]} />}
                <Text numberOfLines={2} style={s.caption}>{media.attribution_text}</Text>
              </View>;
            })}
          </ScrollView>
        </>}

        {place.attributions.length > 0 && <>
          <SectionHeader style={s.section} title={t('place.attributions.title')} />
          <View onLayout={event => { attributionsY.current = event.nativeEvent.layout.y; }} style={s.credits}>
            {place.attributions.map(item => <Text key={`${item.publisher}-${item.attribution_text}`} style={s.attribution}>
              {item.publisher} — {item.attribution_text}{item.license_code ? ` (${item.license_code})` : ''}
            </Text>)}
          </View>
        </>}
      </View>
    </ScrollView>

    <View style={[s.actionBar, elevation.lg, { paddingBottom: insets.bottom + spacing.sm }]}>
      <View style={s.barInner}>
        {mapsFailed && <Text accessibilityRole="alert" style={s.error}>{t('place.directionsFailed')}</Text>}
        <View style={s.actions}>
          <PrimaryButton accessibilityHint={t('place.directionsHint')} icon="navigation" label={t('place.directions')} onPress={() => void openDirections()} style={s.actionPrimary} />
          <SecondaryButton icon="lantern" label={t('place.askGuide')} onPress={() => router.push({ params: { placeId: place.id }, pathname: '/guide' })} style={s.actionSecondary} />
        </View>
      </View>
    </View>
  </View>;
}

function FactRow({ fact, first, locale }: { fact: PlaceFact; first: boolean; locale: AppLocale }) {
  const { t } = useTranslation();
  const label = t(`place.facts.${fact.field_code}`, { defaultValue: t('place.facts.other') });
  const known = fact.knowledge_state === 'KNOWN' ? formatFactValue(fact.value, locale) : null;
  const notApplicable = fact.knowledge_state === 'NOT_APPLICABLE';
  const stale = fact.knowledge_state === 'KNOWN' && isStaleFact(fact);
  return <View style={[s.factRow, !first && s.divider]}>
    <View style={s.factIcon}><FactIcon name={factIcon(fact.field_code)} /></View>
    <View style={s.factCopy}>
      <Text style={s.factLabel}>{label}</Text>
      {known
        ? <Text selectable style={s.factValue}>{known}</Text>
        : notApplicable
          ? <Text style={[s.factValue, s.muted]}>{t('place.notApplicable')}</Text>
          : <UnknownBadge />}
      {fact.knowledge_state === 'KNOWN' && (fact.sources.length
        ? fact.sources.map((source, index) => <SourceLine citation={source} key={`${source.source_revision_id}-${index}`} stale={stale || undefined} />)
        : <Text style={s.note}>{t('place.source.none')}</Text>)}
    </View>
  </View>;
}

const s = StyleSheet.create({
  actionBar: { backgroundColor: colors.white, borderTopLeftRadius: radii.card, borderTopRightRadius: radii.card, paddingHorizontal: spacing.lg, paddingTop: spacing.md },
  actionPrimary: { paddingHorizontal: spacing.sm },
  actionSecondary: { paddingHorizontal: spacing.sm },
  /** Stacked so "Hỏi về nơi này" / "Ask about this place" never truncates beside Directions. */
  actions: { gap: spacing.xs },
  attribution: { ...typography.caption, marginBottom: 4 },
  barInner: { alignSelf: 'center', maxWidth: 480, width: '100%' },
  body: { ...typography.body, color: colors.ink, fontSize: 17, lineHeight: 26 },
  caption: { ...typography.caption, fontSize: 12, marginTop: 6 },
  card: { backgroundColor: colors.white, borderColor: surfaceBorder, borderRadius: radii.card, borderWidth: 1 },
  credits: { backgroundColor: colors.surfaceTint, borderRadius: radii.card, padding: spacing.md },
  divider: { borderTopColor: colors.hairline, borderTopWidth: 1 },
  driver: { backgroundColor: colors.deepOcean, borderRadius: radii.card, gap: 6, marginTop: spacing.lg, padding: 22 },
  driverAddress: { color: colors.white, fontFamily: fonts.medium, fontSize: 22, lineHeight: 30 },
  driverCap: { color: colors.white, flexShrink: 1, fontFamily: fonts.bold, fontSize: 18, lineHeight: 24 },
  driverHead: { alignItems: 'center', flexDirection: 'row', gap: 10, marginBottom: 6 },
  driverIcon: { alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.14)', borderRadius: 18, height: 36, justifyContent: 'center', width: 36 },
  driverName: { color: colors.white, fontFamily: fonts.bold, fontSize: 30, letterSpacing: -0.5, lineHeight: 36 },
  driverSource: { paddingHorizontal: 4 },
  driverUnknown: { color: colors.hairline },
  error: { color: colors.danger, fontFamily: fonts.medium, fontSize: 14, marginBottom: 8, textAlign: 'center' },
  factCopy: { flex: 1, gap: 2 },
  factIcon: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: radii.iconTile, height: 40, justifyContent: 'center', width: 40 },
  factLabel: { color: colors.textMuted, fontFamily: fonts.bold, fontSize: 13, letterSpacing: 0.2, lineHeight: 18 },
  factRow: { alignItems: 'flex-start', flexDirection: 'row', gap: 14, paddingHorizontal: spacing.md, paddingVertical: spacing.md },
  factValue: { color: colors.ink, fontFamily: fonts.bold, fontSize: 17, lineHeight: 24 },
  fill: { flex: 1 },
  floatingBack: { left: spacing.md, position: 'absolute' },
  inner: { alignSelf: 'center', maxWidth: 480, paddingHorizontal: spacing.lg, width: '100%' },
  mediaEmpty: { backgroundColor: colors.surfaceTint },
  mediaImage: { borderRadius: radii.inset, height: 140, width: 200 },
  mediaItem: { width: 200 },
  mediaRow: { gap: spacing.sm, paddingHorizontal: spacing.lg },
  mediaScroll: { marginHorizontal: -spacing.lg },
  muted: { color: colors.textMuted },
  note: { ...typography.caption, marginTop: spacing.xs },
  otherName: { color: 'rgba(255,255,255,0.9)', fontFamily: fonts.medium, fontSize: 17, marginTop: 2 },
  plain: { backgroundColor: colors.canvas },
  plainHeader: { paddingHorizontal: spacing.md },
  quick: { backgroundColor: colors.white, borderColor: surfaceBorder, borderRadius: radii.card, borderWidth: 1, flex: 1, gap: 4, minHeight: 104, minWidth: 0, padding: spacing.sm },
  quickIcon: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: 12, height: 36, justifyContent: 'center', width: 36 },
  quickLabel: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 12, lineHeight: 16 },
  quickRow: { flexDirection: 'row', gap: spacing.xs, marginTop: spacing.md },
  sourcesLine: { alignItems: 'center', flexDirection: 'row', gap: 6, minHeight: 44, marginTop: spacing.xs },
  sourcesText: { color: colors.tealText, flex: 1, fontFamily: fonts.bold, fontSize: 13, lineHeight: 18 },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: spacing.xs },
  quickValue: { color: colors.ink, fontFamily: fonts.bold, fontSize: 15, lineHeight: 20 },
  screen: { backgroundColor: colors.canvas, flex: 1 },
  scroll: { paddingBottom: spacing.xxl },
  section: { marginBottom: spacing.sm, marginTop: spacing.xxl },
  skeletonBody: { gap: spacing.md, padding: spacing.lg },
});
