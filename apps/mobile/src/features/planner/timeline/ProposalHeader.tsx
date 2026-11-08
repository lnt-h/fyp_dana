import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { CircleButton, GlassBadge, PhotoHero } from '../../../components/ui';
import type { Media } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

/** Visible photo height below the status bar; the hero never drops under 240 pt in total. */
const HERO_BODY = 196;
const HERO_MIN = 240;
export const HERO_RADIUS = 0;

type Props = {
  title: string;
  /** Display date range (e.g. `16–17/01`); null when the plan has no start date. */
  dateRange: string | null;
  /** First stop's photo, else the city photo; null shows the hero's gradient art. */
  image: Media | null;
  imageLabel: string;
  dayCount: number;
  stopCount: number;
  /** Small glass badge over the photo (e.g. "Saved", "Draft"). */
  badge?: { label: string; icon?: 'check' } | null;
  /** Plan Health pill (preview only) and anything else that belongs on the cover row. */
  status?: ReactNode;
  onBack: () => void;
};

/** Hero height for a given top inset (shared with the loading skeleton). */
export function proposalHeroHeight(topInset: number) {
  return Math.max(HERO_MIN, topInset + HERO_BODY);
}

/**
 * Trip cover (Wanderlog pattern): full-bleed photo with the title on it (photo credit kept visible, FR-008), then one
 * meta line `21–22 Nov · 2 days · 11 stops` and the cover row with the single Plan Health pill.
 */
export function ProposalHeader({ title, dateRange, image, imageLabel, dayCount, stopCount, badge, status, onBack }: Props) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const days = t('proposal.stats.daysValue', { count: dayCount });
  const stops = t('proposal.stats.stopsValue', { count: stopCount });
  const meta = [dateRange, days, stops].filter(Boolean).join(' · ');
  return <View>
    <PhotoHero
      accessibilityLabel={image ? imageLabel : undefined}
      arch={false}
      attribution={image ? t('proposal.cover.credit', { credit: image.attribution_text }) : null}
      fallbackIcon="map"
      height={proposalHeroHeight(insets.top)}
      image={image}
      title={title}
      topLeft={<CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={onBack} size={44} />}
      topRight={badge ? <GlassBadge icon={badge.icon} label={badge.label} style={h.badge} /> : undefined}
    />
    <View style={h.cover}>
      <Text accessibilityLabel={meta} style={h.meta}>{meta}</Text>
      {status ? <View style={h.status}>{status}</View> : null}
    </View>
  </View>;
}

const h = StyleSheet.create({
  badge: { marginTop: 7 },
  cover: { paddingHorizontal: spacing.lg, paddingTop: spacing.md, gap: spacing.sm },
  meta: { fontFamily: fonts.semibold, fontSize: 15, lineHeight: 20, color: colors.textSecondary },
  status: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: spacing.xs },
});
