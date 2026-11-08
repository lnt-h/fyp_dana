/**
 * Plan Health as ONE status pill (visual refresh rule 6): "Looks good" / "N to check" / "Needs changes". The status is
 * the server's `plan_health`; N counts the real problems the server listed (never unknown hours or estimates, DEC-030).
 * Tapping opens the health detail (SCR-026). Icon + words, never colour alone.
 */
import { useTranslation } from 'react-i18next';
import type { StyleProp, ViewStyle } from 'react-native';
import { StatusPill, type StatusTone } from '../../../components/ui';
import type { PlanHealth } from '../../../lib/api/types';

export type HealthLook = { tone: StatusTone; label: string };

/** Pill tone and localized label for a server status plus the number of real problems. */
export function useHealthLook() {
  const { t } = useTranslation();
  return (health: PlanHealth, problems: number): HealthLook => {
    if (health === 'BLOCKED') return { label: t('proposal.health.pill.blocked'), tone: 'danger' };
    if (health === 'WARNING' && problems > 0) return { label: t('proposal.health.pill.check', { count: problems }), tone: 'warning' };
    return { label: t('proposal.health.pill.good'), tone: 'success' };
  };
}

export function HealthPill({ health, problems, updating = false, onPress, style }: {
  health: PlanHealth;
  problems: number;
  /** An edit or regeneration is recalculating: the last result stays, labelled as being checked. */
  updating?: boolean;
  onPress?: () => void;
  style?: StyleProp<ViewStyle>;
}) {
  const { t } = useTranslation();
  const look = useHealthLook()(health, problems);
  const label = updating ? t('proposal.health.pill.updating') : look.label;
  return <StatusPill
    accessibilityHint={onPress ? t('proposal.health.pill.hint') : undefined}
    accessibilityLabel={t('proposal.health.pill.a11y', { status: label })}
    icon={updating ? 'refresh' : undefined}
    label={label}
    onPress={onPress}
    style={style}
    tone={updating ? 'neutral' : look.tone}
  />;
}
