import { type ReactNode, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Animated, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { AiMark, Icon, Photo } from '../../../components/ui';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import { currentLocale } from '../../../i18n';
import type { Category, Citation, GuideMessage, GuideStreamEvent, Place } from '../../../lib/api/types';
import { categoryColor, colors } from '../../../theme/colors';
import { radii } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { CitationDetail, isWebUnverified } from '../../place/components/SourceLine';
import { formatDate, hostOf, isStaleDate, isWebSourceStale } from '../../place/format';
import { GuideAvatar } from './GuideHeader';

type Stage = Extract<GuideStreamEvent, { type: 'progress' }>['stage'];

/** Domain rule: an answer counts only with ≥ 1 citation; anything else renders as insufficient evidence. */
export const isCitedAnswer = (message: GuideMessage) =>
  (message.answer_status === 'ANSWERED' || message.answer_status === 'ANSWERED_WEB_UNVERIFIED') && (message.citations?.length ?? 0) > 0;

/** Web-fallback answer (ADR-010): evidence came from web pages that are not source-checked. */
const isWebAnswer = (message: GuideMessage) => message.answer_status === 'ANSWERED_WEB_UNVERIFIED';

/** Traveller bubble: primary fill, white text (5.18:1), right aligned. */
export function TravelerBubble({ content }: { content: string }) {
  const { t } = useTranslation();
  return <View accessibilityLabel={`${t('guide.you')}: ${content}`} accessible style={[b.bubble, b.traveler]}>
    <Text style={b.travelerText}>{content}</Text>
  </View>;
}

/** Assistant row: small Gonarra avatar + content column. */
function AssistantRow({ children }: { children: ReactNode }) {
  return <View style={b.assistantRow}>
    <View style={b.avatarSlot}><GuideAvatar size={28} /></View>
    <View style={b.assistantColumn}>{children}</View>
  </View>;
}

export type MentionedPlaces = { places: Place[]; categories: Category[]; onOpen: (placeId: string) => void };

/** Final assistant message: answer text, inline place cards for catalog places it names, compact numbered sources. */
export function AssistantBubble({ message, onOpenPlace, mentioned }: { message: GuideMessage; onOpenPlace?: () => void; mentioned?: MentionedPlaces }) {
  const { t } = useTranslation();
  if (!isCitedAnswer(message)) return <InsufficientBubble />;
  const web = isWebAnswer(message);
  return <AssistantRow>
    <View style={[b.bubble, b.assistant]}>
      {web && <View accessible accessibilityLabel={t('guide.webAnswerA11y')} style={b.webChip}>
        <Icon color={colors.warning} name="info" size={14} />
        <Text style={b.webChipText}>{t('guide.webAnswer')}</Text>
      </View>}
      <Text accessibilityLabel={`${t('guide.assistant')}: ${message.content}`} selectable style={b.body}>{message.content}</Text>
    </View>
    {mentioned && mentioned.places.length > 0 && <PlaceCards {...mentioned} />}
    <SourceChips citations={message.citations ?? []} onOpenPlace={onOpenPlace} />
  </AssistantRow>;
}

/** Source chips shown before "+N"; the rest open on tap. */
const MAX_CHIPS = 4;
const CARD_WIDTH = 188;
const CARD_PHOTO = 104;

/** Inline photo cards (Mindtrip-style) for published places the answer names; tapping opens the place screen. */
function PlaceCards({ places, categories, onOpen }: MentionedPlaces) {
  const { t } = useTranslation();
  const locale = currentLocale();
  return <ScrollView contentContainerStyle={b.cards} horizontal showsHorizontalScrollIndicator={false} style={b.cardScroll}>
    {places.map(place => {
      const category = categories.find(item => item.code === place.category_code);
      const categoryName = category ? (locale === 'vi' ? category.name_vi : category.name_en) : null;
      const tone = categoryColor(place.category_code);
      return <Pressable
        accessibilityHint={t('guide.placeCardHint')}
        accessibilityLabel={[place.name, categoryName].filter(Boolean).join(', ')}
        accessibilityRole="button"
        key={place.id}
        onPress={() => onOpen(place.id)}
        style={({ pressed }) => [b.card, pressed && b.pressed]}
      >
        <View style={b.cardPhoto}>
          <Photo categoryCode={place.category_code} height={CARD_PHOTO} image={place.thumbnail} name={place.name} width={CARD_WIDTH} />
        </View>
        <View style={b.cardBody}>
          <Text numberOfLines={1} style={b.cardTitle}>{place.name}</Text>
          {!!categoryName && <View style={b.cardMeta}>
            <View style={[b.cardDot, { backgroundColor: tone.fg }]} />
            <Text numberOfLines={1} style={b.cardMetaText}>{categoryName}</Text>
          </View>}
        </View>
      </Pressable>;
    })}
  </ScrollView>;
}

/** "Not enough evidence" bubble: no answer text at all, never a guess (ADR-010, `insufficient_evidence`). */
export function InsufficientBubble() {
  const { t } = useTranslation();
  return <AssistantRow>
    <View accessibilityLabel={`${t('guide.assistant')}: ${t('guide.insufficient.title')}. ${t('guide.insufficient.body')}`} accessible style={[b.bubble, b.assistant]}>
      <View style={b.insufficientHead}>
        <Icon color={colors.warning} name="info" size={18} />
        <Text style={b.insufficientTitle}>{t('guide.insufficient.title')}</Text>
      </View>
      <Text style={b.bodySecondary}>{t('guide.insufficient.body')}</Text>
    </View>
  </AssistantRow>;
}

/** Compact numbered source chips under the bubble; tapping one expands its detail (publisher, section, verified date). */
function SourceChips({ citations, onOpenPlace }: { citations: Citation[]; onOpenPlace?: () => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState<number | null>(null);
  const [all, setAll] = useState(false);
  const locale = currentLocale();
  const selected = open === null ? null : citations[open];
  const shown = all ? citations : citations.slice(0, MAX_CHIPS);
  const hidden = citations.length - shown.length;
  return <View style={b.sources}>
    <View style={b.chips}>
      <View accessible accessibilityLabel={`${t('common.aiMark')}. ${t('guide.sources', { count: citations.length })}`} style={b.sourcesLabel}>
        <AiMark decorative size={14} />
        <Text style={b.sourcesTitle}>{t('guide.sources', { count: citations.length })}</Text>
      </View>
      {shown.map((citation, index) => {
        const web = isWebUnverified(citation);
        const stale = web ? isWebSourceStale(citation.fetched_at) : isStaleDate(citation.verified_at);
        const active = open === index;
        const verified = web
          ? `${t('guide.webAnswer')}, ${hostOf(citation.url ?? citation.locator) ?? ''}`
          : citation.verified_at ? t('place.source.verified', { date: formatDate(citation.verified_at, locale) }) : null;
        return <Pressable
          accessibilityHint={t(active ? 'place.source.collapseHint' : 'place.source.expandHint')}
          accessibilityLabel={[`${index + 1}. ${citation.publisher}`, citation.title, verified, stale ? t('place.stale') : null].filter(Boolean).join(', ')}
          accessibilityRole="button"
          accessibilityState={{ expanded: active }}
          hitSlop={{ bottom: 8, left: 2, right: 2, top: 8 }}
          key={`${citation.source_revision_id}-${citation.knowledge_chunk_id ?? citation.place_fact_id ?? index}`}
          onPress={() => setOpen(active ? null : index)}
          style={({ pressed }) => [b.chip, active && b.chipActive, pressed && b.pressed]}
        >
          <Text style={[b.chipIndex, active && b.chipTextActive]}>{index + 1}</Text>
          <Text numberOfLines={1} style={[b.chipText, active && b.chipTextActive]}>{citation.publisher}</Text>
          {(web || stale) && <Icon color={active ? colors.primary : colors.warning} name={stale ? 'warning' : 'info'} size={13} />}
        </Pressable>;
      })}
      {hidden > 0 && <Pressable
        accessibilityLabel={t('guide.moreSources', { count: hidden })}
        accessibilityRole="button"
        hitSlop={{ bottom: 8, left: 2, right: 2, top: 8 }}
        onPress={() => setAll(true)}
        style={({ pressed }) => [b.chip, b.moreChip, pressed && b.pressed]}
      >
        <Text style={[b.chipText, b.moreChipText]}>{t('guide.moreSourcesShort', { count: hidden })}</Text>
      </Pressable>}
    </View>
    {selected && <View style={b.detail}><CitationDetail citation={selected} onOpen={onOpenPlace} /></View>}
  </View>;
}

/** In-flight assistant bubble: typing dots until the first text delta, then streamed text and *Adding sources…*. */
export function StreamingBubble({ text, stage }: { text: string; stage?: Stage }) {
  const { t } = useTranslation();
  if (!text) {
    return <AssistantRow>
      <View accessibilityLabel={t('guide.typing')} accessible style={[b.bubble, b.assistant, b.typing]}>
        <TypingDots />
        {stage && <Text style={b.meta}>{t(`guide.stage.${stage}`)}</Text>}
      </View>
    </AssistantRow>;
  }
  return <AssistantRow>
    <View style={[b.bubble, b.assistant]}>
      <Text style={b.body}>{text}<Text style={b.cursor}>▍</Text></Text>
      <Text style={b.meta}>{t('guide.addingSources')}</Text>
    </View>
  </AssistantRow>;
}

/** Why a question failed: no connection, quota reached, AI service down, session ended, or anything else. */
export type GuideErrorKind = 'offline' | 'quota' | 'busy' | 'auth' | 'generic';

/** Failed question. The question itself is put back in the composer, so Send retries it. */
export function ErrorLine({ reason = 'generic', onSignIn }: { reason?: GuideErrorKind; onSignIn?: () => void }) {
  const { t } = useTranslation();
  return <View accessibilityRole="alert" style={b.error}>
    <Icon color={colors.danger} name="warning" size={16} />
    <Text style={b.errorText}>{reason === 'generic' ? t('guide.error') : reason === 'auth' ? t('common.loadError.auth') : t(`guide.errors.${reason}`)}</Text>
    {reason === 'auth' && onSignIn && <Pressable accessibilityRole="button" hitSlop={8} onPress={onSignIn}>
      <Text style={b.errorAction}>{t('common.signInAgain')}</Text>
    </Pressable>}
  </View>;
}

function TypingDots() {
  const reduceMotion = useReducedMotion();
  const values = useRef([0, 1, 2].map(() => new Animated.Value(0.35))).current;
  useEffect(() => {
    if (reduceMotion) return;
    const loop = Animated.loop(Animated.stagger(180, values.map(value => Animated.sequence([
      Animated.timing(value, { duration: 260, toValue: 1, useNativeDriver: true }),
      Animated.timing(value, { duration: 260, toValue: 0.35, useNativeDriver: true }),
    ]))));
    loop.start();
    return () => loop.stop();
  }, [reduceMotion, values]);
  return <View style={b.dots}>
    {values.map((value, index) => <Animated.View key={index} style={[b.dot, {
      opacity: reduceMotion ? 0.6 : value,
      transform: reduceMotion ? [] : [{ translateY: value.interpolate({ inputRange: [0.35, 1], outputRange: [0, -3] }) }],
    }]} />)}
  </View>;
}

const b = StyleSheet.create({
  assistant: { alignSelf: 'flex-start', backgroundColor: colors.surface, borderTopLeftRadius: 6 },
  assistantColumn: { flex: 1, gap: 8, minWidth: 0 },
  assistantRow: { alignItems: 'flex-start', flexDirection: 'row', gap: 10, marginBottom: 18, paddingRight: 12 },
  avatarSlot: { marginTop: 2 },
  body: { ...typography.body, color: colors.ink },
  bodySecondary: { ...typography.body, color: colors.textSecondary, fontSize: 15, lineHeight: 22 },
  bubble: { borderRadius: 20, paddingHorizontal: 16, paddingVertical: 12 },
  card: { backgroundColor: colors.white, borderRadius: radii.card, overflow: 'hidden', shadowColor: colors.ink, shadowOffset: { height: 2, width: 0 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 2, width: CARD_WIDTH },
  cardBody: { gap: 3, paddingHorizontal: 12, paddingVertical: 10 },
  cardDot: { borderRadius: 4, height: 8, width: 8 },
  cardMeta: { alignItems: 'center', flexDirection: 'row', gap: 6 },
  cardMetaText: { ...typography.micro, color: colors.textSecondary, flexShrink: 1 },
  cardPhoto: { backgroundColor: colors.surface, height: CARD_PHOTO, overflow: 'hidden' },
  cardScroll: { flexGrow: 0, marginRight: -32 },
  cardTitle: { ...typography.label, fontFamily: fonts.semibold },
  cards: { gap: 10, paddingBottom: 6, paddingRight: 32, paddingTop: 2 },
  chip: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.hairline, borderRadius: radii.pill, borderWidth: 1, flexDirection: 'row', gap: 5, maxWidth: 200, minHeight: 32, paddingHorizontal: 10 },
  chipActive: { backgroundColor: colors.primarySoft, borderColor: colors.primarySoft },
  chipIndex: { color: colors.textSecondary, fontFamily: fonts.bold, fontSize: 12 },
  chipText: { color: colors.ink, flexShrink: 1, fontFamily: fonts.medium, fontSize: 12 },
  chipTextActive: { color: colors.primary },
  chips: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  cursor: { color: colors.primary },
  moreChip: { backgroundColor: colors.surface, borderColor: colors.surface },
  moreChipText: { color: colors.primary, fontFamily: fonts.semibold },
  detail: { backgroundColor: colors.surface, borderRadius: radii.inset, marginTop: 8, paddingHorizontal: 12, paddingVertical: 4 },
  dot: { backgroundColor: colors.primary, borderRadius: 4, height: 8, width: 8 },
  dots: { flexDirection: 'row', gap: 6, paddingVertical: 8 },
  error: { alignItems: 'center', alignSelf: 'center', backgroundColor: colors.dangerBg, borderRadius: 16, flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16, maxWidth: '100%', paddingHorizontal: 14, paddingVertical: 10 },
  errorAction: { color: colors.danger, fontFamily: fonts.bold, fontSize: 14, textDecorationLine: 'underline' },
  errorText: { color: colors.danger, flexShrink: 1, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20 },
  insufficientHead: { alignItems: 'center', flexDirection: 'row', gap: 8, marginBottom: 4 },
  insufficientTitle: { ...typography.bodyStrong, flexShrink: 1 },
  meta: { ...typography.caption, marginTop: 4 },
  pressed: { opacity: 0.8 },
  sources: { marginTop: 0 },
  sourcesLabel: { alignItems: 'center', flexDirection: 'row', gap: 4, marginRight: 2, minHeight: 30 },
  sourcesTitle: { ...typography.micro, color: colors.textSecondary },
  traveler: { alignSelf: 'flex-end', backgroundColor: colors.primary, borderTopRightRadius: 6, marginBottom: 18, maxWidth: '82%' },
  travelerText: { ...typography.body, color: colors.white },
  typing: { paddingVertical: 8 },
  webChip: { alignItems: 'center', alignSelf: 'flex-start', borderColor: colors.warning, borderRadius: radii.pill, borderWidth: 1, flexDirection: 'row', gap: 4, marginBottom: 8, paddingHorizontal: 8, paddingVertical: 2 },
  webChipText: { color: colors.warning, fontFamily: fonts.semibold, fontSize: 12, lineHeight: 16 },
});
