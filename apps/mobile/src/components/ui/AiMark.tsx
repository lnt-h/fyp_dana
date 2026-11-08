import { useTranslation } from 'react-i18next';
import { colors } from '../../theme/colors';
import { Icon } from './Icon';

export type AiMarkProps = {
  /** Icon size in dp (default 14; the brief allows 14–16). */
  size?: number;
  /** Hide from screen readers when an adjacent caption already says the text is AI-written. */
  decorative?: boolean;
};

/**
 * The only AI marker in the app: a small violet sparkle beside AI-written text ("Written by AI" / "Do AI viết").
 * No uppercase "AI" labels or per-item banners (visual refresh anti-noise rule 3).
 */
export function AiMark({ size = 14, decorative = false }: AiMarkProps) {
  const { t } = useTranslation();
  return <Icon accessibilityLabel={decorative ? undefined : t('common.aiMark')} color={colors.ai} name="sparkle" size={size} strokeWidth={2} />;
}
