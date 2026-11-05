import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { CircleButton, GlassBadge, PhotoHero, StatCircle } from '../../../components/ui';
import type { Media, PlanHealth } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, spacing } from '../../../theme/spacing';
import { typography } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { HealthGlyph } from './icons';

const HERO_HEIGHT = 312;

type Props = {
  title: string;
  cityName: string | null;
  /** First stop's photo, else the city photo; null shows the hero's gradient art. */
  image: Media | null;
  imageLabel: string;
  dayCount: number;
  stopCount: number;
  /** Server Plan Health; null for a saved itinerary (shows the saved status instead). */
  health: PlanHealth | null;
  saved: boolean;
  onBack: () => void;
  onOpenHealth: () => void;
};

/** Full-bleed photo hero (title, city, credit) and the stat row: days, stops, Plan Health (icon + word). */
export function ProposalHeader({ title, cityName, image, imageLabel, dayCount, stopCount, health, saved, onBack, onOpenHealth }: Props) {
  const { t } = useTranslation();
  const status = t(saved ? 'proposal.status.saved' : 'proposal.status.unsaved');
  return <View>
    <PhotoHero
      accessibilityLabel={image ? imageLabel : undefined}
      attribution={image ? t('proposal.cover.credit', { credit: image.attribution_text }) : null}
      height={HERO_HEIGHT}
      image={image}
      kicker={cityName ?? undefined}
      title={title}
      topLeft={<CircleButton accessibilityLabel={t('common.goBack')} icon="back" onPress={onBack} size={44} />}
      topRight={<GlassBadge icon={saved ? 'check' : undefined} label={status} style={h.status} />}
    />
    <View style={h.stats}>
      <StatCircle icon="calendar" label={t('proposal.stats.days')} size={60} value={t('proposal.stats.daysValue', { count: dayCount })} />
      <StatCircle icon="map-pin" label={t('proposal.stats.stops')} size={60} value={t('proposal.stats.stopsValue', { count: stopCount })} />
      {health
        ? <HealthStat health={health} onPress={onOpenHealth} />
        : <StatCircle icon={saved ? 'check' : 'info'} label={t('proposal.stats.status')} size={60} value={status} />}
    </View>
  </View>;
}

const tint: Record<PlanHealth, string> = { BLOCKED: '#F8E3E3', GOOD: colors.skyWash, WARNING: '#FDF0DA' };

/** Local variant of `StatCircle`: the circle and word take the health colour, and it opens the Health card. */
function HealthStat({ health, onPress }: { health: PlanHealth; onPress: () => void }) {
  const { t } = useTranslation();
  const word = t(`proposal.health.${health}`);
  return <Pressable
    accessibilityHint={t('proposal.stats.healthHint')}
    accessibilityLabel={`${word}, ${t('proposal.stats.health')}`}
    accessibilityRole="button"
    onPress={onPress}
    style={({ pressed }) => [h.healthStat, pressed && { opacity: 0.7 }]}
  >
    <View style={[h.healthCircle, { backgroundColor: tint[health] }]}>
      <HealthGlyph health={health} size={26} />
    </View>
    <Text numberOfLines={1} style={[h.healthWord, health === 'BLOCKED' && { color: palette.error }]}>{word}</Text>
    <Text numberOfLines={2} style={h.healthLabel}>{t('proposal.stats.health')}</Text>
  </Pressable>;
}

const h = StyleSheet.create({
  status: { marginTop: 7 },
  stats: { flexDirection: 'row', gap: spacing.xs, paddingHorizontal: spacing.md, marginTop: spacing.xs },
  healthStat: { flex: 1, minWidth: 0, minHeight: MIN_TOUCH, alignItems: 'center' },
  healthCircle: { width: 60, height: 60, borderRadius: 30, alignItems: 'center', justifyContent: 'center', marginBottom: 10 },
  healthWord: { ...typography.headline, textAlign: 'center' },
  healthLabel: { ...typography.caption, fontSize: 14, textAlign: 'center' },
});
