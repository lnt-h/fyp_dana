import { StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import type { PlanHealth } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { palette } from '../../auth/components/AuthUI';
import { HealthGlyph } from '../timeline/icons';

/** Server-computed Plan Health as icon + word (+ counts); colour is never the only signal (S-4). */
export function HealthBadge({ health, blocking, warnings }: { health: PlanHealth; blocking: number; warnings: number }) {
  const { t } = useTranslation();
  const label = health === 'GOOD'
    ? t('proposal.health.badgeGood')
    : health === 'WARNING'
      ? t('proposal.health.badgeWarning', { count: warnings })
      : t('proposal.health.badgeBlocked', { blocking, warnings });
  return <View accessible accessibilityLabel={label} style={[b.badge, health === 'BLOCKED' && b.blocked, health === 'WARNING' && b.warning]}>
    <HealthGlyph health={health} size={16} />
    <Text style={[b.text, health === 'BLOCKED' && { color: palette.error }]}>{label}</Text>
  </View>;
}

export function SavedBadge({ saved }: { saved: boolean }) {
  const { t } = useTranslation();
  return <View style={[b.badge, saved && b.saved]}>
    <Text style={[b.text, saved && { color: colors.ok }]}>{t(saved ? 'proposal.status.saved' : 'proposal.status.unsaved')}</Text>
  </View>;
}

const b = StyleSheet.create({
  badge: { flexDirection: 'row', alignItems: 'center', gap: 6, minHeight: 32, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, backgroundColor: colors.white, borderWidth: 1, borderColor: palette.border, flexShrink: 1 },
  warning: { borderColor: colors.sun },
  blocked: { borderColor: palette.error },
  saved: { borderColor: colors.ok, backgroundColor: colors.okBg },
  text: { fontFamily: 'HankenGrotesk_700Bold', fontSize: 13, color: colors.deepOcean, flexShrink: 1 },
});
