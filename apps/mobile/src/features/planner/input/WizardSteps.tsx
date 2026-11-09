import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { Icon, PhotoFallback, PrimaryButton, SecondaryButton, type IconName } from '../../../components/ui';
import type { Media } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';

export const WIZARD_STEPS = 4;

/** One colour per step (teal, coral, indigo, green): the bar fills with colour as the traveller moves on. */
const STEP_COLORS = [colors.primary, colors.coral, '#4F46E5', colors.success] as const;

/** Segmented progress under the header (`Unknown-7/8.jpg`): one bar per step, done and current filled. */
export function StepProgress({ current, total = WIZARD_STEPS }: { current: number; total?: number }) {
  const { t } = useTranslation();
  const label = t('planner.wizard.step', { current, total });
  return <View
    accessibilityLabel={label}
    accessibilityRole="progressbar"
    accessibilityValue={{ max: total, min: 1, now: current, text: label }}
    style={w.progress}
  >
    <View style={w.bars}>
      {Array.from({ length: total }, (_, index) => <View key={index} style={[w.bar, index < current && { backgroundColor: STEP_COLORS[index % STEP_COLORS.length] }]} />)}
    </View>
    <Text style={w.stepText}>{label}</Text>
  </View>;
}

/** Fixed destination for the FYP release: city photo (credited), `Đà Nẵng`, `Including the Hội An area`. */
export function DestinationCard({ name, subtitle, image, credit }: { name: string; subtitle: string; image: Media | null; credit: string | null }) {
  const resolved = resolveImage(image, { height: 140, width: 360 });
  return <View accessible accessibilityLabel={`${name}, ${subtitle}`} style={w.destination}>
    <View style={w.destinationClip}>
      {resolved
        ? <Image contentFit="cover" placeholder={resolved.placeholder} source={resolved.source} style={StyleSheet.absoluteFill} transition={200} />
        : <PhotoFallback icon="map-pin" tone="dark" />}
      <LinearGradient colors={['rgba(7,21,30,0)', 'rgba(7,21,30,0.8)']} locations={[0.2, 1]} pointerEvents="none" style={StyleSheet.absoluteFill} />
      <View style={w.destinationCopy}>
        <View style={w.destinationPin}><Icon color={colors.white} name="map-pin" size={16} /></View>
        <View style={w.flex}>
          <Text style={w.destinationName}>{name}</Text>
          <Text style={w.destinationSub}>{subtitle}</Text>
        </View>
      </View>
    </View>
    {credit ? <Text numberOfLines={1} style={w.credit}>{credit}</Text> : null}
  </View>;
}

/** A review summary card; tapping it jumps back to its step. */
export function ReviewCard({ title, icon, lines, onPress, editLabel }: { title: string; icon: IconName; lines: string[]; onPress: () => void; editLabel: string }) {
  return <Pressable
    accessibilityHint={editLabel}
    accessibilityLabel={[title, ...lines].join(', ')}
    accessibilityRole="button"
    onPress={onPress}
    style={({ pressed }) => [w.review, pressed && { backgroundColor: colors.surfaceTint }]}
  >
    <View style={w.reviewIcon}><Icon color={colors.tealText} name={icon} size={20} /></View>
    <View style={w.flex}>
      <Text style={w.reviewTitle}>{title}</Text>
      {lines.map((line, index) => <Text key={index} style={w.reviewLine}>{line}</Text>)}
    </View>
    <Icon color={colors.textMuted} name="edit" size={18} />
  </Pressable>;
}

/** Sticky footer: Back (secondary, hidden on step 1) + Next / Create (primary), with an optional reason line above. */
export function WizardFooter({ step, onBack, onNext, nextLabel, nextIcon, disabled, loading, reason, error }: {
  step: number; onBack: () => void; onNext: () => void; nextLabel: string; nextIcon?: IconName; disabled?: boolean; loading?: boolean;
  reason?: string | null; error?: string | null;
}) {
  const { t } = useTranslation();
  return <View>
    {reason ? <Text style={w.reason}>{reason}</Text> : null}
    {error ? <Text accessibilityRole="alert" style={[w.reason, { color: colors.danger }]}>{error}</Text> : null}
    <View style={w.footerRow}>
      {step > 1 ? <SecondaryButton label={t('planner.wizard.back')} onPress={onBack} style={w.back} /> : null}
      <PrimaryButton
        accessibilityHint={disabled && reason ? reason : undefined}
        disabled={disabled}
        icon={nextIcon}
        iconSize={16}
        label={nextLabel}
        loading={loading}
        onPress={onNext}
        style={w.flex}
      />
    </View>
  </View>;
}

/** Text link styled as a 44 pt row (e.g. "Or describe it in words"). */
export function LinkRow({ label, onPress, icon = 'chevron-right' }: { label: string; onPress: () => void; icon?: IconName }) {
  return <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [w.link, pressed && { opacity: 0.6 }]}>
    <Text style={w.linkText}>{label}</Text>
    <Icon color={colors.tealText} name={icon} size={16} />
  </Pressable>;
}

export function StepTitle({ children, hint }: { children: string; hint?: ReactNode }) {
  return <View style={w.stepHead}>
    <Text accessibilityRole="header" style={w.stepTitle}>{children}</Text>
    {typeof hint === 'string' ? <Text style={w.stepHint}>{hint}</Text> : hint}
  </View>;
}

const w = StyleSheet.create({
  flex: { flex: 1 },
  progress: { gap: 6, paddingTop: spacing.xs },
  bars: { flexDirection: 'row', gap: 6 },
  bar: { flex: 1, height: 6, borderRadius: 3, backgroundColor: colors.hairline },
  stepText: { fontFamily: fonts.semibold, fontSize: 13, color: colors.textSecondary },
  destination: { marginBottom: spacing.md },
  destinationClip: { height: 140, borderRadius: radii.photoCard, overflow: 'hidden', justifyContent: 'flex-end', backgroundColor: colors.surfaceTint },
  destinationCopy: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, padding: spacing.md },
  destinationPin: { width: 32, height: 32, borderRadius: 16, backgroundColor: 'rgba(255,255,255,0.22)', alignItems: 'center', justifyContent: 'center' },
  destinationName: { fontFamily: fonts.bold, fontSize: 22, lineHeight: 27, color: colors.white, letterSpacing: -0.3 },
  destinationSub: { fontFamily: fonts.medium, fontSize: 14, lineHeight: 19, color: colors.white },
  credit: { fontFamily: fonts.medium, fontSize: 12, color: colors.textMuted, marginTop: spacing.xxs },
  review: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm, minHeight: MIN_TOUCH, padding: spacing.md, borderRadius: radii.card, backgroundColor: colors.surface, marginBottom: spacing.sm },
  reviewIcon: { width: 40, height: 40, borderRadius: radii.iconTile, backgroundColor: colors.primarySoft, alignItems: 'center', justifyContent: 'center' },
  reviewTitle: { fontFamily: fonts.bold, fontSize: 16, lineHeight: 21, color: colors.ink, marginBottom: 2 },
  reviewLine: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted },
  reason: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted, textAlign: 'center', marginBottom: spacing.xs },
  footerRow: { flexDirection: 'row', gap: spacing.sm },
  back: { minWidth: 112 },
  link: { flexDirection: 'row', alignItems: 'center', gap: 2, minHeight: MIN_TOUCH, alignSelf: 'flex-start' },
  linkText: { fontFamily: fonts.bold, fontSize: 15, color: colors.tealText },
  stepHead: { marginTop: spacing.lg, marginBottom: spacing.md, gap: 4 },
  stepTitle: { fontFamily: fonts.bold, fontSize: 24, lineHeight: 30, letterSpacing: -0.4, color: colors.ink },
  stepHint: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted },
});
