import { type ComponentRef, useCallback, useEffect, useRef, useState } from 'react';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { AiMark, Icon, Photo, PrimaryButton, Skeleton, type IconName } from '../../components/ui';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { currentLocale } from '../../i18n';
import { SIGN_IN_AGAIN_ROUTE, isAuthError } from '../../lib/api/errors';
import { ApiError, getPlace, listCategories, listCities, loadErrorKind, streamGuide, type LoadErrorKind } from '../../lib/api/source';
import { fetchPreferences, savePreferences, toPreferencesWrite } from '../../lib/api/sourceAccount';
import type { Category, CityCode, ErrorDetail, GuideMessage, GuideSession, GuideSessionCreate, GuideStreamEvent, Locale, Place, PlaceDetail } from '../../lib/api/types';
import { categoryColor, colors, type CategoryTone } from '../../theme/colors';
import { radii } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { ScreenMessage, isNotFound } from '../place/components/PlaceUI';
import { AssistantBubble, ErrorLine, InsufficientBubble, StreamingBubble, TravelerBubble, type GuideErrorKind } from './components/GuideBubbles';
import { GuideAvatar, GuideHeader } from './components/GuideHeader';
import { forgetGuideSession, listAllGuideMessages, loadCityPlaces, openGuideSession, placesMentioned, storedAnswerFor } from './guideApi';

export const MAX_QUESTION = 4000;
const COUNTER_FROM = 3500;

type Stage = Extract<GuideStreamEvent, { type: 'progress' }>['stage'];
type Item =
  | { kind: 'message'; message: GuideMessage }
  | { kind: 'pending'; id: string; text: string; stage?: Stage }
  | { kind: 'error'; id: string; reason: GuideErrorKind }
  /** The server refused to answer without evidence (`insufficient_evidence` stream error): shown like the answer status. */
  | { kind: 'insufficient'; id: string };

/**
 * `notFound` = the place of a PLACE session is gone (API-011 404). `unavailable` = the Guide endpoints answered 404/501
 * (not deployed on this server). `error` = anything else, with the reason for the body line.
 */
type Load = { state: 'loading' } | { state: 'ready' } | { state: 'notFound' } | { state: 'unavailable' } | { state: 'error'; kind: LoadErrorKind };

/** Guide endpoints missing on this server (older API build): 404 on session create, or 501. */
const isGuideMissing = (error: unknown) => error instanceof ApiError && (error.status === 404 || error.status === 501);

/** Reason line for a failed question: a stream `error` event or a thrown request error. */
function guideErrorKind(error: ErrorDetail | unknown): GuideErrorKind {
  if (isAuthError(error)) return 'auth';
  const code = error instanceof ApiError ? error.code : (error as Partial<ErrorDetail> | null)?.code;
  if (code === 'authentication_required') return 'auth';
  if (code === 'quota_exceeded') return 'quota';
  if (code === 'network' || (!code && error instanceof TypeError)) return 'offline';
  if (error instanceof ApiError || typeof code === 'string') {
    return code && (code.endsWith('_unavailable') || code === 'feature_disabled') ? 'busy' : 'generic';
  }
  return 'generic';
}

/** What a Guide session is about: the whole city (Guide tab) or one place (place card / picker). */
export type GuideScope = { kind: 'CITY'; cityCode: CityCode } | { kind: 'PLACE'; placeId: string };

export const scopeKey = (scope: GuideScope) => (scope.kind === 'CITY' ? `city:${scope.cityCode}` : `place:${scope.placeId}`);

/** API-024 body for a scope: `CITY` + `city_code`, or `PLACE` + `place_id` (contract 1.0). */
export function sessionBody(scope: GuideScope, locale: Locale): GuideSessionCreate {
  return scope.kind === 'CITY'
    ? { city_code: scope.cityCode, locale, scope: 'CITY' }
    : { locale, place_id: scope.placeId, scope: 'PLACE' };
}

/** The AI data notice (FR-074) stays dismissed for this app session even if API-005 could not record it. */
let noticeDismissed = false;
let localSeq = 0;
const localId = (prefix: string) => `${prefix}-${++localSeq}`;

type Suggestion = { key: string; icon: IconName; tone: CategoryTone };
const SUGGESTIONS: Suggestion[] = [
  { icon: 'clock', key: 'hours', tone: categoryColor('MUSEUM') },
  { icon: 'card', key: 'ticket', tone: categoryColor('FOOD') },
  { icon: 'heritage', key: 'history', tone: categoryColor('HERITAGE') },
  { icon: 'map-pin', key: 'entrance', tone: categoryColor('NATURE') },
];
const CITY_SUGGESTIONS: Suggestion[] = [
  { icon: 'heritage', key: 'cityHistory', tone: categoryColor('HERITAGE') },
  { icon: 'lantern', key: 'cityHoiAn', tone: categoryColor('CRAFT_VILLAGE') },
  { icon: 'beach', key: 'cityBeaches', tone: categoryColor('BEACH') },
  { icon: 'person', key: 'cityEtiquette', tone: categoryColor('RELIGIOUS_SITE') },
];

/**
 * SCR-034 chat for the city (Guide tab) or one place. Questions live only in component state: never persisted, never
 * logged. The session id is reused per scope for this app session (guideApi.ts), so history survives switching scope.
 * One question in flight; the stream aborts on unmount, clear or scope change.
 */
export function GuideChat({ scope, onChangePlace, keyboardOpen }: { scope: GuideScope; onChangePlace: () => void; keyboardOpen: boolean }) {
  const { t } = useTranslation();
  const reduceMotion = useReducedMotion();
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [place, setPlace] = useState<PlaceDetail | null>(null);
  const [cityName, setCityName] = useState<string | null>(null);
  const [cityPlaces, setCityPlaces] = useState<Place[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [session, setSession] = useState<GuideSession | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [showNotice, setShowNotice] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<ComponentRef<typeof ScrollView>>(null);
  const freshRef = useRef(false);

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    let alive = true;
    const locale = currentLocale();
    const fresh = freshRef.current;
    freshRef.current = false;
    setLoad({ state: 'loading' });
    (async () => {
      // Each step fails differently: a gone place is "not found", a missing Guide endpoint is "unavailable".
      let detail: PlaceDetail | null = null;
      if (scope.kind === 'PLACE') {
        try { detail = await getPlace(scope.placeId); } catch (error) {
          const failure: Load = isNotFound(error) ? { state: 'notFound' } : { kind: loadErrorKind(error), state: 'error' };
          return { failure, ok: false as const };
        }
      }
      try {
        const opened = await openGuideSession(scopeKey(scope), sessionBody(scope, locale), fresh);
        return { ...opened, detail, ok: true as const };
      } catch (error) {
        const failure: Load = isGuideMissing(error) ? { state: 'unavailable' } : { kind: loadErrorKind(error), state: 'error' };
        return { failure, ok: false as const };
      }
    })()
      .then(result => {
        if (!alive) return;
        if (!result.ok) { setLoad(result.failure); return; }
        const { session: opened, detail, history } = result;
        setPlace(detail);
        listCities()
          .then(cities => {
            const city = cities.find(item => (detail ? item.id === detail.city_id : item.code === opened.city_code));
            if (!alive || !city) return;
            setCityName(locale === 'vi' ? city.name_vi : city.name_en);
            // Catalog list for inline place cards in answers (cached for the app session).
            loadCityPlaces(city.id, locale).then(places => { if (alive) setCityPlaces(places); }).catch(() => undefined);
          })
          .catch(() => undefined);
        listCategories().then(list => { if (alive) setCategories(list); }).catch(() => undefined);
        setSession(opened);
        setItems(history.map(message => ({ kind: 'message', message })));
        setLoad({ state: 'ready' });
      });
    if (!noticeDismissed) fetchPreferences().then(prefs => { if (alive) setShowNotice(!prefs.ai_notice_acknowledged_at); }).catch(() => undefined);
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scopeKey(scope), attempt]);

  const hasItems = items.length > 0;
  // The empty state (starter questions) reads from the top; a thread follows its newest message.
  const scrollToEnd = useCallback(() => { if (hasItems) scrollRef.current?.scrollToEnd({ animated: !reduceMotion }); }, [hasItems, reduceMotion]);
  // Keep the newest message right above the composer when the keyboard opens.
  useEffect(() => { if (keyboardOpen) scrollToEnd(); }, [keyboardOpen, scrollToEnd]);

  async function send(raw: string) {
    const content = raw.trim();
    if (!content || busy || !session || content.length > MAX_QUESTION) return;
    const pendingId = localId('pending');
    const traveler: GuideMessage = { content, created_at: new Date().toISOString(), id: localId('traveler'), input_mode: 'TEXT', role: 'TRAVELER', seq: 0 };
    setItems(current => [...current.filter(item => item.kind !== 'error'), { kind: 'message', message: traveler }, { id: pendingId, kind: 'pending', text: '' }]);
    setInput('');
    setBusy(true);
    const controller = new AbortController();
    abortRef.current = controller;
    const update = (fn: (item: Extract<Item, { kind: 'pending' }>) => Item) =>
      setItems(current => current.map(item => (item.kind === 'pending' && item.id === pendingId ? fn(item) : item)));
    const fail = (reason: GuideErrorKind) => {
      setItems(current => current.map(item => (item.kind === 'pending' && item.id === pendingId ? { id: localId('error'), kind: 'error', reason } : item)));
      setInput(previous => previous || content); // the question is kept in the composer
    };
    // Not a failure: the Guide declined to answer without evidence (ADR-010), so the question is not put back.
    const insufficient = () => update(() => ({ id: localId('insufficient'), kind: 'insufficient' }));
    let finished = false;
    try {
      await streamGuide(session.id, { content, input_mode: 'TEXT' }, event => {
        if (controller.signal.aborted) return;
        if (event.type === 'progress') update(item => ({ ...item, stage: event.stage }));
        else if (event.type === 'text') update(item => ({ ...item, text: item.text + event.delta }));
        else if (event.type === 'result') { finished = true; update(() => ({ kind: 'message', message: event.message })); }
        else {
          finished = true;
          if (event.error.code === 'insufficient_evidence') insufficient();
          else fail(guideErrorKind(event.error));
        }
      }, controller.signal);
      if (!finished && !controller.signal.aborted) {
        // Stream dropped without a terminal event: re-fetch the stored result (all pages, so the newest is included),
        // never POST again. Only an answer stored after this question counts; an older answer is never shown.
        const answer = storedAnswerFor(await listAllGuideMessages(session.id), content);
        if (answer) update(() => ({ kind: 'message', message: answer }));
        else fail('generic');
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        if (error instanceof ApiError && error.code === 'insufficient_evidence') insufficient();
        else fail(guideErrorKind(error));
      }
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  function confirmClear() {
    Alert.alert(t('guide.clearConfirmTitle'), t('guide.clearConfirmBody'), [
      { style: 'cancel', text: t('common.cancel') },
      {
        onPress: () => {
          abortRef.current?.abort();
          abortRef.current = null;
          setBusy(false);
          setItems([]);
          // API-026 delete is not wired; forget the cached session and start a fresh one without history.
          forgetGuideSession(scopeKey(scope), currentLocale());
          freshRef.current = true;
          setAttempt(n => n + 1);
        },
        style: 'destructive',
        text: t('guide.clearConfirm'),
      },
    ]);
  }

  function acknowledgeNotice() {
    noticeDismissed = true;
    setShowNotice(false);
    // FR-074: API-005 stamps ai_notice_acknowledged_at; failures keep it dismissed for this app session only.
    fetchPreferences().then(prefs => savePreferences(toPreferencesWrite(prefs, { ai_notice_acknowledged: true }))).catch(() => undefined);
  }

  const isCity = scope.kind === 'CITY';
  /** Subject of the chat: the place name, or the city name for a city session. */
  const placeName = (isCity ? cityName : place?.name) ?? '';
  const openPlace = scope.kind === 'PLACE' ? () => router.push({ params: { placeId: scope.placeId }, pathname: '/place/[placeId]' }) : undefined;
  const openMentioned = (placeId: string) => router.push({ params: { placeId }, pathname: '/place/[placeId]' });
  const signIn = () => router.push(SIGN_IN_AGAIN_ROUTE);
  const ready = load.state === 'ready' && !!session;
  const remaining = input.length >= COUNTER_FROM;
  const canSend = ready && !busy && input.trim().length > 0 && input.length <= MAX_QUESTION;
  const changePlace = () => { abortRef.current?.abort(); onChangePlace(); };
  const suggestions = isCity ? CITY_SUGGESTIONS : SUGGESTIONS;
  const excludeId = scope.kind === 'PLACE' ? scope.placeId : null;

  return <View style={c.fill}>
    <GuideHeader clearDisabled={!ready || items.length === 0} onClear={confirmClear} />
    <Pressable
      accessibilityHint={t(isCity ? 'guide.context.cityHint' : 'guide.context.hint')}
      accessibilityLabel={isCity ? t('guide.context.cityA11y', { name: placeName }) : t('guide.context.a11y', { name: [placeName, cityName].filter(Boolean).join(', ') })}
      accessibilityRole="button"
      onPress={changePlace}
      style={({ pressed }) => [c.context, pressed && c.pressed]}
    >
      <View style={c.contextThumb}>
        {isCity
          ? <Icon color={colors.primary} name="map-pin" size={18} />
          : <Photo categoryCode={place?.category_code} height={32} iconSize={16} image={place?.thumbnail} name={place?.name} variant="thumb" width={32} />}
      </View>
      <Text numberOfLines={1} style={c.contextName}>{placeName || '…'}</Text>
      <Text numberOfLines={1} style={c.contextChange}>{t(isCity ? 'guide.context.pickPlace' : 'guide.context.change')}</Text>
      <Icon color={colors.primary} name="chevron-down" size={16} />
    </Pressable>

    {load.state === 'loading' && <View accessibilityLabel={t('guide.session.loading')} accessibilityLiveRegion="polite" accessible style={c.skeleton}>
      <Skeleton height={72} radius={20} width="78%" />
      <Skeleton height={44} radius={20} style={c.skeletonRight} width="55%" />
      <Skeleton height={110} radius={20} width="85%" />
    </View>}
    {load.state === 'notFound' && <ScreenMessage title={t('guide.session.notFound')}>
      <PrimaryButton label={t('guide.picker.choose')} onPress={onChangePlace} />
    </ScreenMessage>}
    {load.state === 'unavailable' && <ScreenMessage body={t('guide.session.unavailableBody')} title={t('guide.session.unavailable')}>
      <PrimaryButton label={t('guide.picker.retry')} onPress={() => setAttempt(n => n + 1)} />
    </ScreenMessage>}
    {load.state === 'error' && <ScreenMessage body={t(`common.loadError.${load.kind}`)} title={t('guide.session.error')}>
      {load.kind === 'auth'
        ? <PrimaryButton label={t('common.signInAgain')} onPress={signIn} />
        : <PrimaryButton label={t('guide.picker.retry')} onPress={() => setAttempt(n => n + 1)} />}
    </ScreenMessage>}

    {ready && <ScrollView
      alwaysBounceVertical={false}
      bounces={hasItems}
      contentContainerStyle={c.thread}
      keyboardDismissMode="interactive"
      keyboardShouldPersistTaps="handled"
      onContentSizeChange={scrollToEnd}
      ref={scrollRef}
      showsVerticalScrollIndicator={false}
      style={c.fill}
    >
      {items.length === 0 && <View style={c.empty}>
        <GuideAvatar size={56} />
        <Text style={c.emptyTitle}>{t('guide.empty.title', { place: placeName })}</Text>
        <Text style={c.emptyBody}>{t('guide.empty.body')}</Text>
        <View style={c.starters}>
          {suggestions.map(item => <Pressable
            accessibilityLabel={t(`guide.suggest.${item.key}.question` as 'guide.suggest.hours.question')}
            accessibilityRole="button"
            key={item.key}
            onPress={() => void send(t(`guide.suggest.${item.key}.question` as 'guide.suggest.hours.question'))}
            style={({ pressed }) => [c.starter, pressed && c.pressed]}
          >
            <View style={[c.starterIcon, { backgroundColor: item.tone.bg }]}><Icon color={item.tone.fg} name={item.icon} size={18} /></View>
            <Text numberOfLines={2} style={c.starterText}>{t(`guide.suggest.${item.key}.question` as 'guide.suggest.hours.question')}</Text>
            <Icon color={colors.textMuted} name="arrow-up" size={16} />
          </Pressable>)}
        </View>
      </View>}
      <View accessibilityLiveRegion="polite">
        {items.map(item => {
          if (item.kind === 'error') return <ErrorLine key={item.id} onSignIn={signIn} reason={item.reason} />;
          if (item.kind === 'insufficient') return <InsufficientBubble key={item.id} />;
          if (item.kind === 'pending') return <StreamingBubble key={item.id} stage={item.stage} text={item.text} />;
          return item.message.role === 'TRAVELER'
            ? <TravelerBubble content={item.message.content} key={item.message.id} />
            : <AssistantBubble
              key={item.message.id}
              mentioned={{ categories, onOpen: openMentioned, places: placesMentioned(item.message.content, cityPlaces, excludeId) }}
              message={item.message}
              onOpenPlace={openPlace}
            />;
        })}
      </View>
    </ScrollView>}

    {ready && <View style={[c.composerWrap, keyboardOpen && c.composerKeyboard]}>
      {showNotice && <View accessibilityRole="summary" style={c.notice}>
        <Icon color={colors.info} name="info" size={18} />
        <View style={c.fill}>
          <Text style={c.noticeTitle}>{t('guide.notice.title')}</Text>
          <Text style={c.noticeBody}>{t('guide.notice.body')}</Text>
        </View>
        <Pressable accessibilityRole="button" hitSlop={8} onPress={acknowledgeNotice} style={c.noticeAction}>
          <Text style={c.link}>{t('guide.notice.dismiss')}</Text>
        </Pressable>
      </View>}
      {!busy && !input && items.length > 0 && <ScrollView contentContainerStyle={c.suggestions} horizontal keyboardShouldPersistTaps="handled" showsHorizontalScrollIndicator={false} style={c.suggestionScroll}>
        {suggestions.map(item => <Pressable
          accessibilityLabel={t(`guide.suggest.${item.key}.question` as 'guide.suggest.hours.question')}
          accessibilityRole="button"
          key={item.key}
          onPress={() => void send(t(`guide.suggest.${item.key}.question` as 'guide.suggest.hours.question'))}
          style={({ pressed }) => [c.chip, { backgroundColor: item.tone.bg }, pressed && c.pressed]}
        >
          <Icon color={item.tone.fg} name={item.icon} size={16} />
          <Text numberOfLines={1} style={c.chipText}>{t(`guide.suggest.${item.key}.label` as 'guide.suggest.hours.label')}</Text>
        </Pressable>)}
      </ScrollView>}
      <View style={c.composer}>
        <TextInput
          accessibilityLabel={t('guide.composer.label')}
          maxLength={MAX_QUESTION}
          multiline
          onChangeText={setInput}
          placeholder={t('guide.composer.placeholder', { place: placeName })}
          placeholderTextColor={colors.textMuted}
          style={c.input}
          value={input}
        />
        <Pressable
          accessibilityHint={busy ? t('guide.composer.busy') : undefined}
          accessibilityLabel={t('guide.composer.send')}
          accessibilityRole="button"
          accessibilityState={{ busy, disabled: !canSend }}
          disabled={!canSend}
          onPress={() => void send(input)}
          style={({ pressed }) => [c.send, !canSend && c.sendDisabled, pressed && { opacity: 0.85, transform: [{ scale: 0.96 }] }]}
        >
          {busy ? <ActivityIndicator color={colors.white} /> : <Icon color={colors.white} name="arrow-up" size={22} strokeWidth={2.4} />}
        </Pressable>
      </View>
      <View style={c.footer}>
        <AiMark decorative size={12} />
        <Text style={c.footerText}>{t('guide.composer.disclaimer')}</Text>
        {remaining && <Text accessibilityLiveRegion="polite" style={c.counter}>{t('guide.composer.counter', { count: input.length, max: MAX_QUESTION })}</Text>}
      </View>
    </View>}
  </View>;
}

const c = StyleSheet.create({
  chip: { alignItems: 'center', borderRadius: radii.pill, flexDirection: 'row', gap: 6, minHeight: 44, paddingHorizontal: 12 },
  chipText: { color: colors.ink, fontFamily: fonts.semibold, fontSize: 14 },
  composer: { alignItems: 'flex-end', backgroundColor: colors.surface, borderRadius: 26, flexDirection: 'row', gap: 8, minHeight: 56, paddingLeft: 18, paddingRight: 6, paddingVertical: 6 },
  composerKeyboard: { paddingBottom: 8 },
  composerWrap: { paddingTop: 8 },
  context: { alignItems: 'center', alignSelf: 'flex-start', backgroundColor: colors.surface, borderRadius: radii.pill, flexDirection: 'row', gap: 8, marginBottom: 8, maxWidth: '100%', minHeight: 44, paddingLeft: 6, paddingRight: 12 },
  contextChange: { color: colors.primary, fontFamily: fonts.semibold, fontSize: 14 },
  contextName: { color: colors.ink, flexShrink: 1, fontFamily: fonts.semibold, fontSize: 15 },
  contextThumb: { alignItems: 'center', backgroundColor: colors.white, borderRadius: 16, height: 32, justifyContent: 'center', overflow: 'hidden', width: 32 },
  counter: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 12, marginLeft: 'auto' },
  empty: { alignItems: 'center', gap: 8, paddingBottom: 12, paddingTop: 20 },
  emptyBody: { ...typography.body, color: colors.textSecondary, fontSize: 15, lineHeight: 22, paddingHorizontal: 12, textAlign: 'center' },
  emptyTitle: { ...typography.headline, fontFamily: fonts.bold, fontSize: 21, lineHeight: 27, marginTop: 6, paddingHorizontal: 12, textAlign: 'center' },
  fill: { flex: 1 },
  footer: { alignItems: 'center', flexDirection: 'row', gap: 5, justifyContent: 'center', marginTop: 6, paddingHorizontal: 6 },
  footerText: { ...typography.micro, flexShrink: 1 },
  input: { color: colors.ink, flex: 1, fontFamily: fonts.regular, fontSize: 16, maxHeight: 120, minHeight: 44, paddingBottom: 11, paddingTop: 12 },
  link: { color: colors.primary, fontFamily: fonts.bold, fontSize: 14 },
  notice: { alignItems: 'flex-start', backgroundColor: colors.infoBg, borderRadius: radii.inset, flexDirection: 'row', gap: 10, marginBottom: 8, padding: 12 },
  noticeAction: { alignSelf: 'center', justifyContent: 'center', minHeight: 44, paddingHorizontal: 4 },
  noticeBody: { ...typography.caption, color: colors.ink, marginTop: 2 },
  noticeTitle: { color: colors.ink, fontFamily: fonts.semibold, fontSize: 14 },
  pressed: { opacity: 0.8 },
  send: { alignItems: 'center', backgroundColor: colors.primary, borderRadius: 22, height: 44, justifyContent: 'center', width: 44 },
  sendDisabled: { backgroundColor: colors.disabledButton },
  skeleton: { flex: 1, gap: 14, paddingTop: 12 },
  skeletonRight: { alignSelf: 'flex-end' },
  starter: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.hairline, borderRadius: radii.card, borderWidth: 1, flexDirection: 'row', gap: 12, minHeight: 56, paddingHorizontal: 12, paddingVertical: 8 },
  starterIcon: { alignItems: 'center', borderRadius: radii.iconTile, height: 36, justifyContent: 'center', width: 36 },
  starterText: { ...typography.label, flex: 1 },
  starters: { alignSelf: 'stretch', gap: 8, marginTop: 16 },
  suggestionScroll: { flexGrow: 0, marginBottom: 8, marginHorizontal: -20 },
  suggestions: { gap: 8, paddingHorizontal: 20 },
  thread: { flexGrow: 1, paddingTop: 12 },
});
