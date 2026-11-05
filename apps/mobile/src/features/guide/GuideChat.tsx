import { type ComponentRef, useCallback, useEffect, useRef, useState } from 'react';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { Chip, Icon, PrimaryButton, Skeleton, categoryIcon } from '../../components/ui';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { currentLocale } from '../../i18n';
import { createGuideSession, getPlace, getPreferences, listCities, listGuideMessages, streamGuide } from '../../lib/api/source';
import type { GuideMessage, GuideSession, GuideStreamEvent, PlaceDetail } from '../../lib/api/types';
import { resolveImage } from '../../lib/images/imagekit';
import { colors } from '../../theme/colors';
import { radii } from '../../theme/spacing';
import { fonts } from '../../theme/typography';
import { ScreenMessage, isNotFound } from '../place/components/PlaceUI';
import { AssistantBubble, ErrorLine, StreamingBubble, TravelerBubble } from './components/GuideBubbles';
import { GuideAvatar, GuideHeader } from './components/GuideHeader';

export const MAX_QUESTION = 4000;
const COUNTER_FROM = 3500;

type Stage = Extract<GuideStreamEvent, { type: 'progress' }>['stage'];
type Item =
  | { kind: 'message'; message: GuideMessage }
  | { kind: 'pending'; id: string; text: string; stage?: Stage }
  | { kind: 'error'; id: string };

type Load = { state: 'loading' } | { state: 'ready' } | { state: 'notFound' } | { state: 'error' };

/** The first-use AI notice stays dismissed for this app session (acknowledging via API-005 is not wired yet). */
let noticeDismissed = false;
let localSeq = 0;
const localId = (prefix: string) => `${prefix}-${++localSeq}`;

/**
 * SCR-034 chat for one place. Questions live only in component state: never persisted, never logged.
 * One question in flight; the stream aborts on unmount, clear or place change.
 */
export function GuideChat({ placeId, onChangePlace, keyboardOpen }: { placeId: string; onChangePlace: () => void; keyboardOpen: boolean }) {
  const { t } = useTranslation();
  const reduceMotion = useReducedMotion();
  const [load, setLoad] = useState<Load>({ state: 'loading' });
  const [place, setPlace] = useState<PlaceDetail | null>(null);
  const [cityName, setCityName] = useState<string | null>(null);
  const [session, setSession] = useState<GuideSession | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [showNotice, setShowNotice] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<ComponentRef<typeof ScrollView>>(null);
  const withHistory = useRef(true);

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    let alive = true;
    const locale = currentLocale();
    setLoad({ state: 'loading' });
    (async () => {
      const detail = await getPlace(placeId);
      const created = await createGuideSession({ locale, place_id: placeId });
      const history = withHistory.current ? await listGuideMessages(created.id) : [];
      return { created, detail, history };
    })()
      .then(({ created, detail, history }) => {
        if (!alive) return;
        setPlace(detail);
        listCities()
          .then(cities => {
            const city = cities.find(item => item.id === detail.city_id);
            if (alive) setCityName(city ? (locale === 'vi' ? city.name_vi : city.name_en) : null);
          })
          .catch(() => undefined);
        setSession(created);
        setItems(history.map(message => ({ kind: 'message', message })));
        setLoad({ state: 'ready' });
      })
      .catch((error: unknown) => { if (alive) setLoad({ state: isNotFound(error) ? 'notFound' : 'error' }); });
    if (!noticeDismissed) getPreferences().then(prefs => { if (alive) setShowNotice(!prefs.ai_notice_acknowledged_at); }).catch(() => undefined);
    return () => { alive = false; };
  }, [placeId, attempt]);

  const scrollToEnd = useCallback(() => scrollRef.current?.scrollToEnd({ animated: !reduceMotion }), [reduceMotion]);

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
    const fail = () => {
      setItems(current => current.map(item => (item.kind === 'pending' && item.id === pendingId ? { id: localId('error'), kind: 'error' } : item)));
      setInput(previous => previous || content); // the question is kept in the composer
    };
    let finished = false;
    try {
      await streamGuide(session.id, { content, input_mode: 'TEXT' }, event => {
        if (controller.signal.aborted) return;
        if (event.type === 'progress') update(item => ({ ...item, stage: event.stage }));
        else if (event.type === 'text') update(item => ({ ...item, text: item.text + event.delta }));
        else if (event.type === 'result') { finished = true; update(() => ({ kind: 'message', message: event.message })); }
        else { finished = true; fail(); }
      }, controller.signal);
      if (!finished && !controller.signal.aborted) {
        // Stream dropped without a terminal event: re-fetch the stored result, never POST again.
        const stored = await listGuideMessages(session.id);
        const last = stored[stored.length - 1];
        if (last?.role === 'ASSISTANT') update(() => ({ kind: 'message', message: last }));
        else fail();
      }
    } catch {
      if (!controller.signal.aborted) fail();
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
          withHistory.current = false; // API-026 delete is not wired; start a fresh session without history
          setAttempt(n => n + 1);
        },
        style: 'destructive',
        text: t('guide.clearConfirm'),
      },
    ]);
  }


  const placeName = place?.name ?? '';
  const ready = load.state === 'ready' && !!session;
  const remaining = input.length >= COUNTER_FROM;
  const canSend = ready && !busy && input.trim().length > 0 && input.length <= MAX_QUESTION;
  const thumb = resolveImage(place?.thumbnail, { height: 44, width: 44 });
  const changePlace = () => { abortRef.current?.abort(); onChangePlace(); };

  return <View style={c.fill}>
    <GuideHeader clearDisabled={!ready} onClear={confirmClear} />
    <Pressable
      accessibilityHint={t('guide.context.hint')}
      accessibilityLabel={t('guide.context.a11y', { name: [placeName, cityName].filter(Boolean).join(', ') })}
      accessibilityRole="button"
      onPress={changePlace}
      style={({ pressed }) => [c.context, pressed && { opacity: 0.8 }]}
    >
      <View style={c.contextThumb}>
        {thumb
          ? <Image contentFit="cover" placeholder={thumb.placeholder} source={thumb.source} style={StyleSheet.absoluteFill} />
          : <Icon color={colors.tealText} name={categoryIcon(place?.category_code)} size={22} />}
      </View>
      <View style={c.contextCopy}>
        <Text numberOfLines={1} style={c.contextName}>{placeName || '…'}</Text>
        <Text numberOfLines={1} style={c.contextMeta}>{[cityName, t('guide.context.change')].filter(Boolean).join(' · ')}</Text>
      </View>
      <Icon color={colors.deepOcean} name="chevron-right" size={20} />
    </Pressable>

    {load.state === 'loading' && <View accessibilityLabel={t('guide.session.loading')} accessibilityLiveRegion="polite" accessible style={c.skeleton}>
      <Skeleton height={72} radius={22} width="78%" />
      <Skeleton height={44} radius={22} style={c.skeletonRight} width="55%" />
      <Skeleton height={110} radius={22} width="85%" />
    </View>}
    {load.state === 'notFound' && <ScreenMessage title={t('guide.session.notFound')}>
      <PrimaryButton label={t('guide.picker.choose')} onPress={onChangePlace} />
    </ScreenMessage>}
    {load.state === 'error' && <ScreenMessage title={t('guide.session.error')}>
      <PrimaryButton label={t('guide.picker.retry')} onPress={() => setAttempt(n => n + 1)} />
    </ScreenMessage>}

    {ready && <ScrollView
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
      </View>}
      <View accessibilityLiveRegion="polite">
        {items.map(item => {
          if (item.kind === 'error') return <ErrorLine key={item.id} />;
          if (item.kind === 'pending') return <StreamingBubble key={item.id} stage={item.stage} text={item.text} />;
          return item.message.role === 'TRAVELER'
            ? <TravelerBubble content={item.message.content} key={item.message.id} />
            : <AssistantBubble key={item.message.id} message={item.message} onOpenPlace={() => router.push({ params: { placeId }, pathname: '/place/[placeId]' })} />;
        })}
      </View>
    </ScrollView>}

    {ready && <View style={[c.composerWrap, keyboardOpen && c.composerKeyboard]}>
      {showNotice && <View accessibilityRole="summary" style={c.notice}>
        <View style={c.noticeIcon}><Icon color={colors.tealText} name="info" size={18} /></View>
        <View style={c.fill}>
          <Text style={c.noticeTitle}>{t('guide.notice.title')}</Text>
          <Text style={c.noticeBody}>{t('guide.notice.body')}</Text>
          <Pressable accessibilityRole="button" onPress={() => { noticeDismissed = true; setShowNotice(false); }} style={c.noticeAction}>
            <Text style={c.link}>{t('guide.notice.dismiss')}</Text>
          </Pressable>
        </View>
      </View>}
      {!busy && !input && <ScrollView contentContainerStyle={c.suggestions} horizontal keyboardShouldPersistTaps="handled" showsHorizontalScrollIndicator={false} style={c.suggestionScroll}>
        {SUGGESTIONS.map(key => <Chip
          accessibilityLabel={t(`guide.suggest.${key}.question`)}
          key={key}
          label={t(`guide.suggest.${key}.label`)}
          onPress={() => void send(t(`guide.suggest.${key}.question`))}
          tone="tint"
        />)}
      </ScrollView>}
      <View style={c.composer}>
        <View style={c.inputPill}>
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
        </View>
        <Pressable
          accessibilityHint={busy ? t('guide.composer.busy') : undefined}
          accessibilityLabel={t('guide.composer.send')}
          accessibilityRole="button"
          accessibilityState={{ busy, disabled: !canSend }}
          disabled={!canSend}
          onPress={() => void send(input)}
          style={({ pressed }) => [c.send, !canSend && c.sendDisabled, pressed && { opacity: 0.8, transform: [{ scale: 0.96 }] }]}
        >
          {busy ? <ActivityIndicator color={colors.white} /> : <Icon color={colors.white} name="send" size={22} />}
        </Pressable>
      </View>
      <View style={c.footer}>
        <Icon color={colors.textMuted} name="info" size={12} />
        <Text style={c.footerText}>{t('guide.composer.disclaimer')}</Text>
        {remaining && <Text accessibilityLiveRegion="polite" style={c.counter}>{t('guide.composer.counter', { count: input.length, max: MAX_QUESTION })}</Text>}
      </View>
    </View>}
  </View>;
}

const SUGGESTIONS = ['hours', 'ticket', 'history', 'entrance'] as const;

const c = StyleSheet.create({
  composer: { alignItems: 'flex-end', flexDirection: 'row', gap: 10 },
  composerKeyboard: { paddingBottom: 8 },
  composerWrap: { paddingTop: 8 },
  context: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.hairline, borderRadius: radii.card, borderWidth: 1, flexDirection: 'row', gap: 12, marginBottom: 8, minHeight: 60, padding: 8, paddingRight: 14 },
  contextCopy: { flex: 1, minWidth: 0 },
  contextMeta: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 13, lineHeight: 18 },
  contextName: { color: colors.ink, fontFamily: fonts.bold, fontSize: 16, lineHeight: 21 },
  contextThumb: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: 12, height: 44, justifyContent: 'center', overflow: 'hidden', width: 44 },
  counter: { color: colors.textMuted, fontFamily: fonts.medium, fontSize: 12, marginLeft: 'auto' },
  empty: { alignItems: 'center', gap: 8, paddingHorizontal: 16, paddingVertical: 28 },
  emptyBody: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 15, lineHeight: 22, textAlign: 'center' },
  emptyTitle: { color: colors.ink, fontFamily: fonts.bold, fontSize: 20, letterSpacing: -0.3, lineHeight: 26, marginTop: 6, textAlign: 'center' },
  fill: { flex: 1 },
  footer: { alignItems: 'center', flexDirection: 'row', gap: 5, marginTop: 6, paddingHorizontal: 6 },
  footerText: { color: colors.textMuted, flexShrink: 1, fontFamily: fonts.medium, fontSize: 12, lineHeight: 16 },
  input: { color: colors.ink, fontFamily: fonts.medium, fontSize: 16, maxHeight: 120, minHeight: 48, paddingBottom: 12, paddingTop: 13 },
  inputPill: { backgroundColor: colors.white, borderColor: colors.hairline, borderRadius: radii.field, borderWidth: 1.5, flex: 1, paddingHorizontal: 18 },
  /** Ink + underline: teal text drops to 4.45:1 on the warm notice tint. */
  link: { color: colors.ink, fontFamily: fonts.bold, fontSize: 14, textDecorationLine: 'underline' },
  notice: { alignItems: 'flex-start', backgroundColor: colors.surfaceTint, borderRadius: radii.inset, flexDirection: 'row', gap: 10, marginBottom: 8, padding: 14, paddingBottom: 4 },
  noticeAction: { alignSelf: 'flex-start', justifyContent: 'center', minHeight: 44 },
  noticeBody: { color: colors.deepOcean, fontFamily: fonts.regular, fontSize: 13, lineHeight: 19, marginTop: 2 },
  noticeIcon: { alignItems: 'center', backgroundColor: colors.white, borderRadius: 16, height: 32, justifyContent: 'center', width: 32 },
  noticeTitle: { color: colors.deepOcean, fontFamily: fonts.bold, fontSize: 14 },
  send: { alignItems: 'center', backgroundColor: colors.ink, borderRadius: radii.button, height: 48, justifyContent: 'center', width: 48 },
  sendDisabled: { backgroundColor: colors.disabledButton },
  skeleton: { flex: 1, gap: 14, paddingTop: 12 },
  skeletonRight: { alignSelf: 'flex-end' },
  suggestionScroll: { flexGrow: 0, marginBottom: 8, marginHorizontal: -20 },
  suggestions: { gap: 8, paddingHorizontal: 20 },
  thread: { flexGrow: 1, paddingTop: 12 },
});
