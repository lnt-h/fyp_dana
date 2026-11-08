import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '../../../components/ui';
import { currentLocale } from '../../../i18n';
import type { Citation } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';
import { formatDate, isStaleDate } from '../format';
import { CitationTrustBadge, isWebUnverified } from './UnverifiedBadge';

export { CitationTrustBadge, StopTrustBadge, UnverifiedBadge, isWebUnverified } from './UnverifiedBadge';

/** *Có thể đã cũ / May be out of date* badge: word + icon, never colour alone (S-4). */
export function StaleBadge({ onDark = false }: { onDark?: boolean }) {
  const { t } = useTranslation();
  return <View style={[st.badge, st.stale, onDark && st.staleDark]}>
    <Icon color={onDark ? colors.white : colors.warning} name="warning" size={14} />
    <Text style={[st.badgeText, { color: onDark ? colors.white : colors.warning }]}>{t('place.stale')}</Text>
  </View>;
}

/** The citation's web address when it has one (`url`, or a locator that is an http(s) URL); otherwise null. */
export function citationUrl(citation: Citation): string | null {
  const candidates = [citation.url, citation.locator];
  return candidates.find((value): value is string => typeof value === 'string' && /^https?:\/\/\S+$/i.test(value.trim()))?.trim() ?? null;
}

const openUrl = (url: string) => { Linking.openURL(url).catch(() => undefined); };

/** Content of an expanded citation (title, section, locator, verified date). Shared with the Guide source chips. */
export function CitationDetail({ citation, onOpen }: { citation: Citation; onOpen?: () => void }) {
  const { t } = useTranslation();
  const locale = currentLocale();
  return <View style={st.detail}>
    <Text style={st.detailStrong}>{citation.publisher}</Text>
    {!!citation.title && <Text style={st.detailText}>{t('place.source.titleLabel')}: {citation.title}</Text>}
    <Text style={st.detailText}>
      {t('place.source.sectionLabel')}: {citation.section ? t(`place.sections.${citation.section}`) : t('place.sections.FACT')}
    </Text>
    {!!citation.locator && (citationUrl(citation) === citation.locator.trim()
      ? <Pressable
          accessibilityHint={t('place.source.openLinkHint')}
          accessibilityRole="link"
          onPress={() => openUrl(citation.locator as string)}
          style={({ pressed }) => [st.locatorLink, pressed && { opacity: 0.6 }]}
        >
          <Text style={st.detailText}>{t('place.source.locatorLabel')}: <Text style={st.urlText}>{citation.locator}</Text></Text>
        </Pressable>
      : <Text selectable style={st.detailText}>{t('place.source.locatorLabel')}: {citation.locator}</Text>)}
    {isWebUnverified(citation)
      ? <CitationTrustBadge citation={citation} />
      : <>
        {!!citation.verified_at && <Text style={st.detailText}>{t('place.source.verifiedLong', { date: formatDate(citation.verified_at, locale) })}</Text>}
        {isStaleDate(citation.verified_at) && <StaleBadge />}
      </>}
    {onOpen && <Pressable accessibilityRole="link" onPress={onOpen} style={({ pressed }) => [st.openLink, pressed && { opacity: 0.6 }]}>
      <Text style={st.link}>{t('place.source.openPlace')}</Text>
      <Icon color={colors.ink} name="chevron-right" size={16} />
    </Pressable>}
  </View>;
}

/**
 * One source: `ⓘ {publisher}, {title} · Source-checked · {date}` + stale badge (DEC-022: automated source checks, no human review). Tapping expands the title, section and locator.
 * A `WEB_UNVERIFIED` source shows the *Not source-checked* badge with host + fetched date instead (stale after 7 days).
 * `onOpen` adds an "open place card" link inside the expanded block (Guide → SCR-033).
 */
export function SourceLine({ citation, stale, onOpen }: { citation: Citation; stale?: boolean; onOpen?: () => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const locale = currentLocale();
  const web = isWebUnverified(citation);
  const isStale = !web && (stale ?? isStaleDate(citation.verified_at));
  const label = [citation.publisher, citation.title].filter(Boolean).join(', ');
  const verified = !web && citation.verified_at ? t('place.source.verified', { date: formatDate(citation.verified_at, locale) }) : null;
  const url = citationUrl(citation);
  return <View>
    <View style={st.rowWrap}>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ expanded: open }}
        accessibilityHint={t(open ? 'place.source.collapseHint' : 'place.source.expandHint')}
        onPress={() => setOpen(value => !value)}
        style={({ pressed }) => [st.row, pressed && { opacity: 0.6 }]}
      >
        <View style={st.line}>
          <View style={st.lineIcon}><Icon color={colors.textMuted} name="doc" size={14} /></View>
          <Text style={st.text}>{[label, verified].filter(Boolean).join(' · ')}</Text>
        </View>
        {web && <CitationTrustBadge citation={citation} />}
        {isStale && <StaleBadge />}
      </Pressable>
      {/* The source itself, one tap away ("Summarised from sources" leads here, DEC-025/028). */}
      {url ? <Pressable
        accessibilityHint={t('place.source.openLinkHint')}
        accessibilityLabel={`${t('place.source.openLink')}: ${citation.publisher}`}
        accessibilityRole="link"
        onPress={() => openUrl(url)}
        style={({ pressed }) => [st.openSource, pressed && { opacity: 0.6 }]}
      >
        <Text style={st.openSourceText}>{t('place.source.openLink')}</Text>
        <Icon color={colors.primary} name="share" size={14} />
      </Pressable> : null}
    </View>
    {open && <CitationDetail citation={citation} onOpen={onOpen} />}
  </View>;
}

const st = StyleSheet.create({
  badge: { alignItems: 'center', alignSelf: 'flex-start', borderRadius: 16, borderWidth: 1, flexDirection: 'row', gap: 5, marginTop: 4, minHeight: 26, paddingHorizontal: 10, paddingVertical: 3 },
  badgeText: { fontFamily: fonts.bold, fontSize: 12, lineHeight: 16 },
  detail: { backgroundColor: colors.white, borderRadius: 14, gap: 4, marginBottom: 6, padding: 12 },
  detailStrong: { color: colors.ink, fontFamily: fonts.bold, fontSize: 14, lineHeight: 20 },
  detailText: { color: colors.textSecondary, fontFamily: fonts.regular, fontSize: 13, lineHeight: 19 },
  line: { alignItems: 'flex-start', flexDirection: 'row', gap: 6 },
  lineIcon: { paddingTop: 2 },
  /** Ink + underline on the warm tint detail box (teal would be 4.45:1). */
  link: { color: colors.ink, fontFamily: fonts.bold, fontSize: 14, textDecorationLine: 'underline' },
  openLink: { alignItems: 'center', alignSelf: 'flex-start', flexDirection: 'row', gap: 2, minHeight: 44 },
  locatorLink: { justifyContent: 'center', minHeight: 44 },
  openSource: { alignItems: 'center', flexDirection: 'row', gap: 4, minHeight: 44, paddingLeft: 8 },
  openSourceText: { color: colors.primary, fontFamily: fonts.semibold, fontSize: 13, lineHeight: 18 },
  row: { flex: 1, justifyContent: 'center', minHeight: 44, paddingVertical: 6 },
  rowWrap: { alignItems: 'center', flexDirection: 'row' },
  urlText: { color: colors.primary, textDecorationLine: 'underline' },
  stale: { backgroundColor: colors.warningBg, borderColor: colors.warningBg },
  staleDark: { backgroundColor: 'rgba(255,255,255,0.16)', borderColor: 'rgba(255,255,255,0.4)' },
  text: { color: colors.textMuted, flexShrink: 1, fontFamily: fonts.regular, fontSize: 13, lineHeight: 19 },
});
