/** Small building blocks shared by the edit sheet, picker, regenerate sheet and Plan Health detail. */
import { useState, type ReactNode } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { Icon } from '../../../components/ui/Icon';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import { HealthGlyph, PlannerIcon, type PlannerIconName } from '../timeline/icons';

export const editTokens = {
  border: colors.hairline,
  cardBorder: colors.hairline,
  canvas: colors.canvas,
  errorBg: colors.dangerBg,
  warnBg: colors.warnBg,
  /** Warning text on warnBg (contrast ≥ 4.5:1). */
  warnText: colors.warn,
} as const;

type Tone = 'default' | 'primary' | 'danger';

/** 44-pt pill action with icon + word (S-4: every action has a text label). */
export function PillButton({ label, icon, onPress, tone = 'default', disabled, selected, accessibilityLabel, accessibilityHint, style }: {
  label: string;
  icon?: PlannerIconName;
  onPress: () => void;
  tone?: Tone;
  disabled?: boolean;
  selected?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  style?: StyleProp<ViewStyle>;
}) {
  const fg = selected || tone === 'primary' ? colors.white : tone === 'danger' ? colors.danger : colors.ink;
  return <Pressable
    accessibilityHint={accessibilityHint}
    accessibilityLabel={accessibilityLabel ?? label}
    accessibilityRole="button"
    accessibilityState={{ disabled: !!disabled, selected: selected || undefined }}
    disabled={disabled}
    hitSlop={2}
    onPress={onPress}
    style={({ pressed }) => [
      u.pill,
      tone === 'primary' && u.pillPrimary,
      tone === 'danger' && u.pillDanger,
      selected && u.pillSelected,
      disabled && u.disabled,
      pressed && u.pressed,
      style,
    ]}
  >
    {icon ? <PlannerIcon color={fg} name={icon} size={18} /> : null}
    <Text numberOfLines={1} style={[u.pillText, { color: fg }]}>{label}</Text>
  </Pressable>;
}

/** Overflow menu: one trigger row (more icon + label) expanding to stacked actions. */
export function OverflowMenu({ label, hint, children, style }: {
  label: string;
  hint?: string;
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  const [open, setOpen] = useState(false);
  return <View style={style}>
    <Pressable
      accessibilityHint={hint}
      accessibilityLabel={label}
      accessibilityRole="button"
      accessibilityState={{ expanded: open }}
      onPress={() => setOpen(value => !value)}
      style={({ pressed }) => [u.menuTrigger, pressed && u.pressed]}
    >
      <Icon color={colors.ink} name="more" size={20} strokeWidth={2} />
      <Text numberOfLines={1} style={u.menuTriggerText}>{label}</Text>
      <PlannerIcon color={colors.textMuted} name={open ? 'chevronUp' : 'chevronDown'} size={18} />
    </Pressable>
    {open ? <View style={u.menuBody}>{children}</View> : null}
  </View>;
}

export function SectionLabel({ children, trailing }: { children: string; trailing?: ReactNode }) {
  return <View style={u.labelRow}>
    <Text accessibilityRole="header" style={u.label}>{children}</Text>
    {trailing}
  </View>;
}

/** Inline banner: error (alert), warning, info or progress (polite). Icon + words, never colour alone. */
export function InlineBanner({ tone, title, body, actions, style }: {
  tone: 'error' | 'warning' | 'info' | 'progress';
  title: string;
  body?: string;
  actions?: ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  const isError = tone === 'error';
  return <View
    accessibilityLiveRegion={isError ? 'assertive' : 'polite'}
    accessibilityRole={isError ? 'alert' : 'summary'}
    style={[u.banner, tone === 'error' && u.bannerError, tone === 'warning' && u.bannerWarning, style]}
  >
    <View style={u.bannerRow}>
      <View style={u.bannerIcon}>
        {tone === 'progress'
          ? <ActivityIndicator color={colors.tealText} size="small" />
          : tone === 'info'
            ? <PlannerIcon color={colors.tealText} name="refresh" size={18} />
            : <HealthGlyph health={isError ? 'BLOCKED' : 'WARNING'} size={18} />}
      </View>
      <View style={u.bannerCopy}>
        <Text style={[u.bannerTitle, isError && { color: colors.danger }]}>{title}</Text>
        {body ? <Text style={u.bannerBody}>{body}</Text> : null}
      </View>
    </View>
    {actions ? <View style={u.bannerActions}>{actions}</View> : null}
  </View>;
}

/** Text link action ≥ 44 pt tall. */
export function LinkButton({ label, onPress, disabled, accessibilityLabel, tone = 'teal' }: { label: string; onPress: () => void; disabled?: boolean; accessibilityLabel?: string; tone?: 'teal' | 'muted' }) {
  return <Pressable
    accessibilityLabel={accessibilityLabel ?? label}
    accessibilityRole="button"
    accessibilityState={{ disabled: !!disabled }}
    disabled={disabled}
    onPress={onPress}
    style={({ pressed }) => [u.link, disabled && u.disabled, pressed && u.pressed]}
  >
    <Text style={[u.linkText, tone === 'muted' && { color: colors.textMuted }]}>{label}</Text>
  </Pressable>;
}

export const u = StyleSheet.create({
  pill: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, minHeight: MIN_TOUCH, paddingHorizontal: 14, borderRadius: radii.button, borderWidth: 1, borderColor: editTokens.border, backgroundColor: colors.white },
  pillPrimary: { backgroundColor: colors.primary, borderColor: colors.primary },
  pillDanger: { borderColor: colors.dangerBg, backgroundColor: colors.dangerBg },
  pillSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  pillText: { fontFamily: fonts.semibold, fontSize: 14, lineHeight: 19, flexShrink: 1 },
  disabled: { opacity: 0.45 },
  pressed: { opacity: 0.8 },
  labelRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.xs },
  label: { fontFamily: fonts.semibold, fontSize: 13, lineHeight: 18, color: colors.textSecondary },
  menuTrigger: { flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: MIN_TOUCH, paddingHorizontal: 14, borderRadius: radii.button, borderWidth: 1, borderColor: editTokens.border, backgroundColor: colors.white },
  menuTriggerText: { fontFamily: fonts.semibold, fontSize: 14, lineHeight: 19, color: colors.ink, flex: 1 },
  menuBody: { gap: spacing.xs, marginTop: spacing.xs },
  banner: { borderRadius: radii.card, padding: spacing.sm, backgroundColor: colors.surface },
  bannerError: { backgroundColor: editTokens.errorBg },
  bannerWarning: { backgroundColor: editTokens.warnBg },
  bannerRow: { flexDirection: 'row', gap: 10, alignItems: 'flex-start' },
  bannerIcon: { width: 22, height: 22, alignItems: 'center', justifyContent: 'center', marginTop: 1 },
  bannerCopy: { flex: 1, minWidth: 0 },
  bannerTitle: { fontFamily: fonts.semibold, fontSize: 14, lineHeight: 20, color: colors.ink },
  bannerBody: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 19, color: colors.ink, marginTop: 2 },
  bannerActions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginTop: spacing.xs, paddingLeft: 32 },
  link: { minHeight: MIN_TOUCH, justifyContent: 'center', paddingHorizontal: spacing.xs },
  linkText: { fontFamily: fonts.bold, fontSize: 14, color: colors.tealText },
});
