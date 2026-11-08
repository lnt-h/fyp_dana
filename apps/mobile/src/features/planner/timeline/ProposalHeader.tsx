import { StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { CircleButton, GlassBadge, Icon, PhotoHero } from '../../../components/ui';
import type { Media } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

/** Visible photo height below the status bar; the hero never drops under 220 pt in total. */
const HERO_BODY = 168;
const HERO_MIN = 220;
export const HERO_RADIUS = 28;

type Props = {
  title: string;
  cityName: string | null;
  /** Display date range (e.g. `16–17/01`); null when the plan has no start date. */
  dateRange: string | null;
  /** First stop's photo, else the city photo; null shows the hero's gradient art. */
  image: Media | null;
  imageLabel: string;
  dayCount: number;
  stopCount: number;
  saved: boolean;
  onBack: () => void;
};

/** Hero height for a given top inset (shared with the loading skeleton). */
export function proposalHeroHeight(topInset: number) {
  return Math.max(HERO_MIN, topInset + HERO_BODY);
}

/**
 * Compact photo hero (title, photo credit kept visible for FR-008) with a straight edge and rounded bottom corners,
 * then one cover meta line (city · dates · days · stops). Plan Health is rendered by the screen right below.
 */
export function ProposalHeader({ title, cityName, dateRange, image, imageLabel, dayCount, stopCount, saved, onBack }: Props) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const status = t(saved ? 'proposal.status.saved' : 'proposal.status.unsaved');
  const days = t('proposal.stats.daysValue', { count: dayCount });
  const stops = t('proposal.stats.stopsValue', { count: stopCount });
  // Cover meta (ui-research §3.4): `Đà Nẵng · 16–18/01 · 3 ngày · 12 điểm dừng`; parts that are unknown are left out.
  const meta = cityName && dateRange
    ? t('proposal.cover.meta', { city: cityName, dates: dateRange, days, stops })
    : [cityName, dateRange, days, stops].filter(Boolean).join(' · ');
  return <View>
    <PhotoHero
      accessibilityLabel={image ? imageLabel : undefined}
      arch={false}
      attribution={image ? t('proposal.cover.credit', { credit: image.attribution_text }) : null}
      height={proposalHeroHeight(insets.top)}
      image={image}
      style={h.hero}
      title={title}
      topLeft={<CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={onBack} size={44} />}
      topRight={<GlassBadge icon={saved ? 'check' : undefined} label={status} style={h.status} />}
    />
    <View accessible accessibilityLabel={meta} style={h.meta}>
      <Icon color={colors.textMuted} name="calendar" size={16} />
      <Text style={h.metaText}>{meta}</Text>
    </View>
  </View>;
}

const h = StyleSheet.create({
  hero: { borderBottomLeftRadius: HERO_RADIUS, borderBottomRightRadius: HERO_RADIUS },
  status: { marginTop: 7 },
  meta: { flexDirection: 'row', alignItems: 'flex-start', gap: 6, paddingHorizontal: spacing.lg, marginTop: spacing.md },
  metaText: { flex: 1, fontFamily: fonts.bold, fontSize: 15, lineHeight: 20, color: colors.ink },
});
