import { type ReactNode, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '../../../components/ui';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import { currentLocale } from '../../../i18n';
import type { Citation, GuideMessage, GuideStreamEvent } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { CitationDetail, UnverifiedBadge, isWebUnverified } from '../../place/components/SourceLine';
import { formatDate, hostOf, isStaleDate, isWebSourceStale } from '../../place/format';
import { GuideAvatar, washMuted } from './GuideHeader';

type Stage = Extract<GuideStreamEvent, { type: 'progress' }>['stage'];

/** Domain rule: an answer counts only with ≥ 1 citation; anything else renders as insufficient evidence. */
export const isCitedAnswer = (message: GuideMessage) =>
  (message.answer_status === 'ANSWERED' || message.answer_status === 'ANSWERED_WEB_UNVERIFIED') && (message.citations?.length ?? 0) > 0;

/** Web-fallback answer (ADR-010): evidence came from web pages that are not source-checked. */
const isWebAnswer = (message: GuideMessage) => message.answer_status === 'ANSWERED_WEB_UNVERIFIED';

export function TravelerBubble({ content }: { content: string }) {
  const { t } = useTranslation();
  return <View accessibilityLabel={`${t('guide.you')}: ${content}`} accessible style={[b.bubble, b.traveler]}>
    <Text style={b.travelerText}>{content}</Text>
  </View>;
}

/** Assistant row: small avatar + bubble. */
function AssistantRow({ children }: { children: ReactNode }) {
  return <View style={b.assistantRow}>
    <View style={b.avatarSlot}><GuideAvatar size={26} /></View>
    {children}
  </View>;
}

/** Final assistant message: cited answer with sources, or the insufficient-evidence bubble (no answer text). */
export function AssistantBubble({ message, onOpenPlace }: { message: GuideMessage; onOpenPlace?: () => void }) {
  const { t } = useTranslation();
  if (!isCitedAnswer(message)) return <InsufficientBubble />;
  return <AssistantRow>
    <View style={[b.bubble, b.assistant]}>
      {isWebAnswer(message) && <UnverifiedBadge compact />}
      <Text accessibilityLabel={`${t('guide.assistant')}: ${message.content}`} selectable style={b.body}>{message.content}</Text>
      <SourceChips citations={message.citations ?? []} onOpenPlace={onOpenPlace} />
      <View style={b.aiRow}>
        <Icon color={washMuted} name="info" size={13} />
        <Text style={b.aiLabel}>{t(isWebAnswer(message) ? 'guide.aiLabelWeb' : 'guide.aiLabel')}</Text>
      </View>
    </View>
  </AssistantRow>;
}

/** "Not enough evidence" bubble: no answer text at all, never a guess (ADR-010, `insufficient_evidence`). */
export function InsufficientBubble() {
  const { t } = useTranslation();
  return <AssistantRow>
    <View accessibilityLabel={`${t('guide.assistant')}: ${t('guide.insufficient.title')}. ${t('guide.insufficient.body')}`} accessible style={[b.bubble, b.assistant, b.insufficient]}>
      <View style={b.insufficientHead}>
        <View style={b.sunIcon}><Icon color={colors.warn} name="info" size={16} /></View>
        <Text style={b.insufficientTitle}>{t('guide.insufficient.title')}</Text>
      </View>
      <Text style={b.body}>{t('guide.insufficient.body')}</Text>
    </View>
  </AssistantRow>;
}

/** Compact numbered source chips; tapping one expands its detail (publisher, section, locator, verified date). */
function SourceChips({ citations, onOpenPlace }: { citations: Citation[]; onOpenPlace?: () => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState<number | null>(null);
  const locale = currentLocale();
  const selected = open === null ? null : citations[open];
  return <View style={b.sources}>
    <Text style={b.sourcesTitle}>{t('guide.sources', { count: citations.length })}</Text>
    <View style={b.chips}>
      {citations.map((citation, index) => {
        const web = isWebUnverified(citation);
        const stale = web ? isWebSourceStale(citation.fetched_at) : isStaleDate(citation.verified_at);
        const active = open === index;
        const verified = web
          ? `${t('place.trust.unverified')}, ${hostOf(citation.url ?? citation.locator) ?? t('place.trust.webSourceUnknown')}`
          : citation.verified_at ? t('place.source.verified', { date: formatDate(citation.verified_at, locale) }) : null;
        return <Pressable
          accessibilityHint={t(active ? 'place.source.collapseHint' : 'place.source.expandHint')}
          accessibilityLabel={[`${index + 1}. ${citation.publisher}`, citation.title, verified, stale ? t('place.stale') : null].filter(Boolean).join(', ')}
          accessibilityRole="button"
          accessibilityState={{ expanded: active }}
          hitSlop={{ bottom: 4, top: 4 }}
          key={`${citation.source_revision_id}-${citation.knowledge_chunk_id ?? citation.place_fact_id ?? index}`}
          onPress={() => setOpen(active ? null : index)}
          style={({ pressed }) => [b.chip, active && b.chipActive, pressed && { opacity: 0.75 }]}
        >
          <View style={[b.chipIndex, active && b.chipIndexActive]}>
            <Text style={[b.chipIndexText, active && { color: colors.deepOcean }]}>{index + 1}</Text>
          </View>
          <Text numberOfLines={1} style={[b.chipText, active && { color: colors.white }]}>{citation.publisher}</Text>
          {web && <Icon color={active ? colors.white : colors.accentText} name="info" size={14} />}
          {stale && <Icon color={active ? colors.sun : colors.warn} name="warning" size={14} />}
        </Pressable>;
      })}
    </View>
    {selected && <View style={b.detail}><CitationDetail citation={selected} onOpen={onOpenPlace} /></View>}
  </View>;
}

/** In-flight assistant bubble: typing dots until the first text delta, then streamed text and *Adding sources…*. */
export function StreamingBubble({ text, stage }: { text: string; stage?: Stage }) {
  const { t } = useTranslation();
  if (!text) {
    return <AssistantRow>
      <View accessibilityLabel={t('guide.typing')} accessible style={[b.bubble, b.assistant]}>
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

/** Why a question failed: no connection, quota reached, AI service down, or anything else. */
export type GuideErrorKind = 'offline' | 'quota' | 'busy' | 'generic';

/** Failed question. The question itself is put back in the composer, so Send retries it. */
export function ErrorLine({ reason = 'generic' }: { reason?: GuideErrorKind }) {
  const { t } = useTranslation();
  return <View accessibilityRole="alert" style={b.error}>
    <Icon color={colors.danger} name="warning" size={16} />
    <Text style={b.errorText}>{reason === 'generic' ? t('guide.error') : t(`guide.errors.${reason}`)}</Text>
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
  aiLabel: { color: washMuted, flexShrink: 1, fontFamily: fonts.medium, fontSize: 12, lineHeight: 16 },
  aiRow: { alignItems: 'center', flexDirection: 'row', gap: 5, marginTop: 10 },
  assistant: { backgroundColor: colors.surfaceTint, borderBottomLeftRadius: 6, flexShrink: 1 },
  assistantRow: { alignItems: 'flex-end', flexDirection: 'row', gap: 8, marginBottom: 14, maxWidth: '92%' },
  avatarSlot: { marginBottom: 2 },
  body: { color: colors.ink, fontFamily: fonts.regular, fontSize: 16, lineHeight: 24 },
  bubble: { borderRadius: radii.card, paddingHorizontal: 16, paddingVertical: 12 },
  chip: { alignItems: 'center', backgroundColor: colors.white, borderColor: colors.hairline, borderRadius: 16, borderWidth: 1, flexDirection: 'row', gap: 6, maxWidth: '100%', minHeight: 36, paddingLeft: 4, paddingRight: 12 },
  chipActive: { backgroundColor: colors.deepOcean, borderColor: colors.deepOcean },
  chipIndex: { alignItems: 'center', backgroundColor: colors.surfaceTint, borderRadius: 13, height: 26, justifyContent: 'center', width: 26 },
  chipIndexActive: { backgroundColor: colors.white },
  chipIndexText: { color: colors.ink, fontFamily: fonts.bold, fontSize: 13 },
  chipText: { color: colors.ink, flexShrink: 1, fontFamily: fonts.bold, fontSize: 13 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  cursor: { color: colors.audioTeal },
  detail: { marginTop: 8 },
  dot: { backgroundColor: colors.audioTeal, borderRadius: 4, height: 8, width: 8 },
  dots: { flexDirection: 'row', gap: 6, paddingVertical: 8 },
  error: { alignItems: 'center', alignSelf: 'center', backgroundColor: colors.dangerBg, borderRadius: 16, flexDirection: 'row', gap: 8, marginBottom: 14, maxWidth: '100%', paddingHorizontal: 14, paddingVertical: 10 },
  errorText: { color: colors.danger, flexShrink: 1, fontFamily: fonts.regular, fontSize: 14, lineHeight: 20 },
  insufficient: { backgroundColor: colors.warnBg, borderColor: colors.sun, borderLeftWidth: 4 },
  insufficientHead: { alignItems: 'center', flexDirection: 'row', gap: 8, marginBottom: 6 },
  insufficientTitle: { color: colors.ink, flexShrink: 1, fontFamily: fonts.bold, fontSize: 16, lineHeight: 22 },
  meta: { color: washMuted, fontFamily: fonts.medium, fontSize: 13, marginTop: 6 },
  sources: { borderTopColor: 'rgba(11,48,69,0.1)', borderTopWidth: 1, gap: 8, marginTop: 12, paddingTop: 10 },
  sourcesTitle: { color: washMuted, fontFamily: fonts.bold, fontSize: 12, letterSpacing: 0.6 },
  sunIcon: { alignItems: 'center', backgroundColor: colors.warnBg, borderRadius: 14, height: 28, justifyContent: 'center', width: 28 },
  traveler: { alignSelf: 'flex-end', backgroundColor: colors.deepOcean, borderBottomRightRadius: 6, marginBottom: 14, maxWidth: '82%' },
  travelerText: { color: colors.white, fontFamily: fonts.regular, fontSize: 16, lineHeight: 24 },
});
