import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '../../../components/ui';
import { currentLocale } from '../../../i18n';
import type { Citation } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';
import { formatDate, isStaleDate } from '../format';

/** *Có thể đã cũ / May be out of date* badge: word + icon, never colour alone (S-4). */
export function StaleBadge({ onDark = false }: { onDark?: boolean }) {
  const { t } = useTranslation();
  return <View style={[st.badge, st.stale, onDark && st.staleDark]}>
    <Icon color={onDark ? colors.sun : colors.warn} name="warning" size={14} />
    <Text style={[st.badgeText, { color: onDark ? colors.white : colors.warn }]}>{t('place.stale')}</Text>
  </View>;
}

/** *chưa rõ / unknown* badge for UNKNOWN facts. */
export function UnknownBadge({ label }: { label?: string }) {
  const { t } = useTranslation();
  return <View style={[st.badge, st.unknown]}>
    <Icon color={colors.textMuted} name="info" size={14} />
    <Text style={[st.badgeText, { color: colors.textMuted }]}>{label ?? t('place.unknown')}</Text>
  </View>;
}

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
    {!!citation.locator && <Text selectable style={st.detailText}>{t('place.source.locatorLabel')}: {citation.locator}</Text>}
    <Text style={st.detailText}>{t('place.source.verifiedLong', { date: formatDate(citation.verified_at, locale) })}</Text>
    {isStaleDate(citation.verified_at) && <StaleBadge />}
    {onOpen && <Pressable accessibilityRole="link" onPress={onOpen} style={({ pressed }) => [st.openLink, pressed && { opacity: 0.6 }]}>
      <Text style={st.link}>{t('place.source.openPlace')}</Text>
      <Icon color={colors.ink} name="chevron-right" size={16} />
    </Pressable>}
  </View>;
}

/**
 * One source: `ⓘ {publisher}, {title} · verified {date}` + stale badge. Tapping expands the title, section and locator.
 * `onOpen` adds an "open place card" link inside the expanded block (Guide → SCR-033).
 */
export function SourceLine({ citation, stale, onOpen }: { citation: Citation; stale?: boolean; onOpen?: () => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const locale = currentLocale();
  const isStale = stale ?? isStaleDate(citation.verified_at);
  const label = [citation.publisher, citation.title].filter(Boolean).join(', ');
  const verified = t('place.source.verified', { date: formatDate(citation.verified_at, locale) });
  return <View>
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ expanded: open }}
      accessibilityHint={t(open ? 'place.source.collapseHint' : 'place.source.expandHint')}
      onPress={() => setOpen(value => !value)}
      style={({ pressed }) => [st.row, pressed && { opacity: 0.6 }]}
    >
      <View style={st.line}>
        <View style={st.lineIcon}><Icon color={colors.textMuted} name="info" size={14} /></View>
        <Text style={st.text}>{label} · {verified}</Text>
      </View>
      {isStale && <StaleBadge />}
    </Pressable>
    {open && <CitationDetail citation={citation} onOpen={onOpen} />}
  </View>;
}

const st = StyleSheet.create({
  badge: { alignItems: 'center', alignSelf: 'flex-start', borderRadius: 16, borderWidth: 1, flexDirection: 'row', gap: 5, marginTop: 4, minHeight: 26, paddingHorizontal: 10, paddingVertical: 3 },
  badgeText: { fontFamily: fonts.bold, fontSize: 12, lineHeight: 16 },
  detail: { backgroundColor: colors.surfaceTint, borderRadius: 14, gap: 4, marginBottom: 6, padding: 12 },
  detailStrong: { color: colors.ink, fontFamily: fonts.bold, fontSize: 14, lineHeight: 20 },
  detailText: { color: colors.deepOcean, fontFamily: fonts.regular, fontSize: 13, lineHeight: 19 },
  line: { alignItems: 'flex-start', flexDirection: 'row', gap: 6 },
  lineIcon: { paddingTop: 2 },
  /** Ink + underline on the warm tint detail box (teal would be 4.45:1). */
  link: { color: colors.ink, fontFamily: fonts.bold, fontSize: 14, textDecorationLine: 'underline' },
  openLink: { alignItems: 'center', alignSelf: 'flex-start', flexDirection: 'row', gap: 2, minHeight: 44 },
  row: { justifyContent: 'center', minHeight: 44, paddingVertical: 6 },
  stale: { backgroundColor: colors.warnBg, borderColor: colors.sun },
  staleDark: { backgroundColor: 'rgba(246,166,35,0.16)' },
  text: { color: colors.textMuted, flexShrink: 1, fontFamily: fonts.regular, fontSize: 13, lineHeight: 19 },
  unknown: { backgroundColor: colors.surfaceTint, borderColor: colors.hairline },
});
