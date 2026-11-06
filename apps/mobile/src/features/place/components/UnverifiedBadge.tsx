import { useTranslation } from 'react-i18next';
import { StyleSheet, Text, View } from 'react-native';

import { Icon } from '../../../components/ui';
import { currentLocale } from '../../../i18n';
import type { Citation, Stop, TrustLevel } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { fonts } from '../../../theme/typography';
import { formatDate, hostOf, isWebSourceStale } from '../format';

type Props = {
  /** Source page URL; its host is shown, never the full URL. */
  url?: string | null;
  /** When the page was fetched; shown as a date, and "may be out of date" after 7 days. */
  fetchedAt?: string | null;
  /** Pill only (timeline rows, map callouts); the source line is shown elsewhere. */
  compact?: boolean;
  /** On a dark or photo background. */
  onDark?: boolean;
};

/**
 * Trust label for `WEB_UNVERIFIED` content (architecture §5, FR-098, DEC-022): *Chưa đối chiếu nguồn / Not source-checked* pill (word + icon,
 * never colour alone), then the source host and fetched date, and a stale badge once the fetch is older than 7 days.
 */
export function UnverifiedBadge({ url, fetchedAt, compact = false, onDark = false }: Props) {
  const { t } = useTranslation();
  const locale = currentLocale();
  const host = hostOf(url) ?? t('place.trust.webSourceUnknown');
  const source = fetchedAt ? t('place.trust.webSource', { date: formatDate(fetchedAt, locale), host }) : host;
  const stale = isWebSourceStale(fetchedAt);
  const label = [t('place.trust.unverified'), t('place.trust.unverifiedHint'), compact ? null : source, stale ? t('place.stale') : null].filter(Boolean).join('. ');
  return <View accessible accessibilityLabel={label} style={st.wrap}>
    <View style={[st.pill, onDark && st.pillDark]}>
      <Icon color={onDark ? colors.white : colors.accentText} name="info" size={14} />
      <Text style={[st.pillText, onDark && { color: colors.white }]}>{t('place.trust.unverified')}</Text>
    </View>
    {!compact && <Text style={[st.source, onDark && { color: colors.white }]}>{source}</Text>}
    {!compact && stale && <View style={[st.pill, st.stale]}>
      <Icon color={colors.warn} name="warning" size={14} />
      <Text style={[st.pillText, { color: colors.warn }]}>{t('place.stale')}</Text>
    </View>}
  </View>;
}

/** Badge for a stop when it is a web candidate; null for a VERIFIED stop. */
export function StopTrustBadge({ stop, compact, onDark }: { stop: Pick<Stop, 'trust_level' | 'web_source'>; compact?: boolean; onDark?: boolean }) {
  if (stop.trust_level !== 'WEB_UNVERIFIED') return null;
  return <UnverifiedBadge compact={compact} fetchedAt={stop.web_source?.fetched_at} onDark={onDark} url={stop.web_source?.url} />;
}

export const isWebUnverified = (item: { trust_level?: TrustLevel | null }) => item.trust_level === 'WEB_UNVERIFIED';

/** Badge for a citation when it is web evidence; null otherwise. */
export function CitationTrustBadge({ citation, compact }: { citation: Citation; compact?: boolean }) {
  if (!isWebUnverified(citation)) return null;
  return <UnverifiedBadge compact={compact} fetchedAt={citation.fetched_at} url={citation.url ?? citation.locator} />;
}

const st = StyleSheet.create({
  pill: { alignItems: 'center', alignSelf: 'flex-start', backgroundColor: colors.surfaceTint, borderColor: colors.accentText, borderRadius: 16, borderStyle: 'dashed', borderWidth: 1, flexDirection: 'row', gap: 5, minHeight: 26, paddingHorizontal: 10, paddingVertical: 3 },
  pillDark: { backgroundColor: 'rgba(7,21,30,0.55)', borderColor: 'rgba(255,255,255,0.6)' },
  pillText: { color: colors.accentText, fontFamily: fonts.bold, fontSize: 12, lineHeight: 16 },
  source: { color: colors.textMuted, fontFamily: fonts.regular, fontSize: 13, lineHeight: 19 },
  stale: { backgroundColor: colors.warnBg, borderColor: colors.sun, borderStyle: 'solid' },
  wrap: { alignItems: 'flex-start', gap: 4, marginTop: 4 },
});
