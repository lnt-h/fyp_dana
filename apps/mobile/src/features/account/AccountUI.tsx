import { Children, Fragment, useState, type ReactNode } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, LayoutAnimation, Platform, Pressable, ScrollView, StyleSheet, Text, View, type AccessibilityRole } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import Svg, { Path } from 'react-native-svg';
import { CircleButton } from '../../components/ui';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { colors } from '../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../theme/spacing';
import { fonts, typography } from '../../theme/typography';
import { useAccount } from './AccountContext';

/** AA error red (6.1:1 on white); same value as the auth palette. */
export const errorColor = colors.danger;
const hairline = colors.hairline;
const screenBg = colors.canvas;

const c = (cx: number, cy: number, r: number) => `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0`;
const paths = {
  person: 'M8 7a4 4 0 1 0 8 0a4 4 0 1 0-8 0M4 21v-2a8 7 0 0 1 16 0v2',
  edit: 'M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4',
  sliders: `M4 7h9M17 7h3M4 17h3M11 17h9${c(15, 7, 2)}${c(9, 17, 2)}`,
  settings: 'M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1ZM12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8',
  language: 'M3.5 5.5h9M8 3.5v2M10.5 5.5c0 4-2.8 7-6.5 8.5M5.8 9c1.2 2.2 3.3 3.8 6.2 4.6M12.5 20.5l4-9 4 9M14 17.5h5',
  motion: 'M2 8h5M2 12h3M2 16h5M15 5a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 8v4l3 2',
  shield: 'M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6ZM8 12l3 3 5-6',
  doc: 'M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6',
  info: `${c(12, 12, 9)}M12 11v5.5M12 7.8h.01`,
  exit: 'M9 3H4v18h5M9 12h12M16 7l5 5-5 5',
  trash: 'M4.5 7h15M9.5 7V4.5h5V7M6.5 7l1 13h9l1-13M10 11v5M14 11v5',
  device: 'M8 2.5h8a1.5 1.5 0 0 1 1.5 1.5v16a1.5 1.5 0 0 1-1.5 1.5H8A1.5 1.5 0 0 1 6.5 20V4A1.5 1.5 0 0 1 8 2.5zM11 18.5h2',
  warning: 'M10.3 4.5a2 2 0 0 1 3.4 0l7.6 13a2 2 0 0 1-1.7 3H4.4a2 2 0 0 1-1.7-3zM12 9.5V14M12 17.2h.01',
  check: 'M5 12.5l4.5 4.5L19 7.5',
  chevron: 'M9 5l7 7-7 7',
  chevronDown: 'M5 9l7 7 7-7',
};
export type AccountIconName = keyof typeof paths;

export function AccountIcon({ name, color = colors.deepOcean, size = 22 }: { name: AccountIconName; color?: string; size?: number }) {
  return <Svg width={size} height={size} viewBox="0 0 24 24" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
    <Path d={paths[name]} fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
  </Svg>;
}

type Fallback = '/profile' | '/home' | '/settings';

/** Screen frame: back button row, large title (Triply-style) and optional lead copy, then scrolling content. */
export function AccountShell({ title, lead, children, fallback = '/profile' }: { title: string; lead?: string; children: ReactNode; fallback?: Fallback }) {
  const insets = useSafeAreaInsets();
  const { t } = useTranslation();
  return <KeyboardAvoidingView style={a.screen} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
    <StatusBar style="dark" />
    <View style={[a.header, { paddingTop: insets.top + spacing.xs }]}>
      <CircleButton icon="back" tone="tint" size={44} accessibilityLabel={t('common.goBack')} onPress={() => router.canGoBack() ? router.back() : router.replace(fallback)} />
    </View>
    <ScrollView keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" contentContainerStyle={[a.content, { paddingBottom: insets.bottom + spacing.xxxl }]}>
      <View style={a.inner}>
        <Text accessibilityRole="header" style={a.largeTitle}>{title}</Text>
        {lead ? <Text style={a.lead}>{lead}</Text> : null}
        {children}
      </View>
    </ScrollView>
  </KeyboardAvoidingView>;
}

export function SectionLabel({ children }: { children: string }) {
  return <Text accessibilityRole="header" style={a.section}>{children}</Text>;
}

/** White grouped card; direct children are separated by inset hairlines. */
export function GroupCard({ children, accessibilityRole }: { children: ReactNode; accessibilityRole?: AccessibilityRole }) {
  const items = Children.toArray(children);
  return <View accessibilityRole={accessibilityRole} style={a.card}>
    {items.map((child, index) => <Fragment key={index}>{index > 0 && <View style={a.divider} />}{child}</Fragment>)}
  </View>;
}

type RowProps = {
  icon: AccountIconName;
  title: string;
  subtitle?: string;
  /** Short current value shown before the chevron (e.g. "Tiếng Việt"). */
  value?: string;
  onPress?: () => void;
  trailing?: ReactNode;
  danger?: boolean;
  expanded?: boolean;
  /** Radio rows (SCR-039): role radio, check mark instead of chevron. */
  checked?: boolean;
  busy?: boolean;
  /** Spoken label override (e.g. the language name in its own language). */
  accessibilityLabel?: string;
  accessibilityHint?: string;
};

/** 56 pt list row: icon, title, optional subtitle and value, chevron. */
export function AccountRow({ icon, title, subtitle, value, onPress, trailing, danger, expanded, checked, busy, accessibilityLabel, accessibilityHint }: RowProps) {
  const radio = checked !== undefined;
  const tint = danger ? errorColor : colors.deepOcean;
  const end = trailing ?? (busy ? <ActivityIndicator color={colors.tealText} />
    : radio ? (checked ? <AccountIcon name="check" color={colors.tealText} /> : <View style={a.radioSpacer} />)
    : onPress ? <AccountIcon name={expanded === undefined ? 'chevron' : 'chevronDown'} color={colors.textMuted} size={18} /> : null);
  const content = <>
    <AccountIcon name={icon} color={tint} />
    <View style={a.rowCopy}>
      <Text style={[a.rowTitle, danger && { color: errorColor }]}>{title}</Text>
      {subtitle ? <Text numberOfLines={2} style={a.rowSubtitle}>{subtitle}</Text> : null}
    </View>
    {value ? <Text numberOfLines={1} style={a.rowValue}>{value}</Text> : null}
    {end}
  </>;
  const label = accessibilityLabel ?? [title, value, subtitle].filter(Boolean).join(', ');
  if (!onPress) return <View accessible accessibilityLabel={label} style={a.row}>{content}</View>;
  return <Pressable
    accessibilityRole={radio ? 'radio' : 'button'}
    accessibilityLabel={label}
    accessibilityHint={accessibilityHint}
    accessibilityState={{ expanded, checked: radio ? checked : undefined, busy }}
    onPress={onPress}
    style={({ pressed }) => [a.row, pressed && a.pressed]}>
    {content}
  </Pressable>;
}

/** Row that reveals body text in place (no new screen); announces expanded state. */
export function ExpandableRow({ icon, title, subtitle, body, badge }: { icon: AccountIconName; title: string; subtitle?: string; body: string; badge?: string }) {
  const { t } = useTranslation();
  const reduced = useReducedMotion();
  const [open, setOpen] = useState(false);
  return <View>
    <AccountRow icon={icon} title={title} subtitle={subtitle} value={badge} expanded={open} accessibilityHint={t('account.common.expandHint')}
      onPress={() => { if (!reduced) LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut); setOpen(!open); }} />
    {open ? <Text style={a.expandBody}>{body}</Text> : null}
  </View>;
}

/** Destructive pill (SCR-038). */
export function DangerButton({ label, onPress, disabled }: { label: string; onPress: () => void; disabled?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled: !!disabled }} disabled={disabled} onPress={onPress}
    style={({ pressed }) => [a.danger, disabled && a.dangerDisabled, pressed && a.pressed]}>
    <AccountIcon name="trash" color={colors.white} size={20} />
    <Text style={a.dangerText}>{label}</Text>
  </Pressable>;
}

/** Sign out (account) or reset guest session, shared by Profile and Settings. */
export function useEndSession() {
  const { t } = useTranslation();
  const { clearSession } = useAccount();
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  async function end() {
    if (busy) return;
    setBusy(true); setNotice('');
    try { await clearSession(); router.dismissAll(); router.replace('/welcome'); }
    catch { setNotice(t('account.common.sessionFailed')); }
    finally { setBusy(false); }
  }
  return { busy, notice, end };
}

/** Inline confirmation panel for ending the session. */
export function SessionConfirm({ onCancel }: { onCancel: () => void }) {
  const { t } = useTranslation();
  const { isSignedIn } = useAccount();
  const { busy, notice, end } = useEndSession();
  return <View style={a.confirm}>
    <Text style={a.confirmBody}>{t(isSignedIn ? 'account.common.confirmSignOut' : 'account.common.confirmResetGuest')}</Text>
    {notice ? <Text accessibilityLiveRegion="polite" accessibilityRole="alert" style={a.error}>{notice}</Text> : null}
    <View style={a.confirmActions}>
      <Pressable accessibilityRole="button" onPress={onCancel} style={({ pressed }) => [a.ghost, pressed && a.pressed]}>
        <Text style={a.ghostText}>{t('account.common.keepExploring')}</Text>
      </Pressable>
      <Pressable accessibilityRole="button" accessibilityState={{ busy }} disabled={busy} onPress={() => void end()} style={({ pressed }) => [a.confirmButton, pressed && a.pressed]}>
        {busy ? <ActivityIndicator color={colors.white} accessibilityLabel={t('common.pleaseWait')} /> : <Text style={a.confirmText}>{t('account.common.confirmSession')}</Text>}
      </Pressable>
    </View>
  </View>;
}

export const a = StyleSheet.create({
  screen: { flex: 1, backgroundColor: screenBg },
  header: { backgroundColor: screenBg, paddingHorizontal: spacing.md, paddingBottom: spacing.xxs },
  content: { paddingHorizontal: spacing.lg, paddingTop: spacing.xs },
  inner: { width: '100%', maxWidth: 520, alignSelf: 'center' },
  largeTitle: { ...typography.display, color: colors.ink, marginBottom: spacing.lg },
  lead: { ...typography.body, color: colors.textMuted, marginTop: -spacing.sm, marginBottom: spacing.lg },
  section: { fontFamily: fonts.bold, color: colors.textMuted, fontSize: 15, marginTop: spacing.xs, marginBottom: spacing.xs, marginLeft: spacing.xxs },
  card: { borderRadius: radii.card, backgroundColor: colors.white, borderWidth: StyleSheet.hairlineWidth, borderColor: hairline, overflow: 'hidden', marginBottom: spacing.lg },
  padded: { padding: spacing.lg },
  divider: { height: StyleSheet.hairlineWidth, backgroundColor: colors.hairline, marginLeft: 58 },
  row: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, minHeight: 56 },
  pressed: { opacity: 0.7 },
  rowCopy: { flex: 1 },
  rowTitle: { fontFamily: fonts.regular, fontSize: 17, lineHeight: 22, color: colors.ink },
  rowSubtitle: { ...typography.caption, marginTop: 2 },
  rowValue: { ...typography.caption, fontSize: 15, maxWidth: 130 },
  radioSpacer: { width: 22 },
  expandBody: { ...typography.caption, fontSize: 14, lineHeight: 21, paddingLeft: 58, paddingRight: spacing.lg, paddingBottom: spacing.md },
  body: { ...typography.body, color: colors.textMuted, fontSize: 15, lineHeight: 22 },
  note: { ...typography.caption, textAlign: 'center', marginVertical: spacing.sm },
  error: { ...typography.caption, color: errorColor, marginTop: spacing.xs },
  danger: { flexDirection: 'row', gap: spacing.xs, alignItems: 'center', justifyContent: 'center', minHeight: 56, borderRadius: radii.button, backgroundColor: errorColor, paddingHorizontal: spacing.xl },
  dangerDisabled: { backgroundColor: '#C9B4B4' },
  dangerText: { fontFamily: fonts.bold, fontSize: 17, color: colors.white },
  confirm: { paddingHorizontal: spacing.lg, paddingBottom: spacing.md, paddingTop: spacing.xxs },
  confirmBody: { ...typography.caption, fontSize: 14, lineHeight: 21, color: colors.ink },
  confirmActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  ghost: { flex: 1, minHeight: MIN_TOUCH + 4, borderRadius: radii.button, borderWidth: 1.5, borderColor: colors.hairline, alignItems: 'center', justifyContent: 'center' },
  ghostText: { fontFamily: fonts.bold, fontSize: 15, color: colors.ink },
  confirmButton: { flex: 1, minHeight: MIN_TOUCH + 4, borderRadius: radii.button, backgroundColor: colors.ink, alignItems: 'center', justifyContent: 'center' },
  confirmText: { fontFamily: fonts.bold, fontSize: 15, color: colors.white },
  textButton: { minHeight: MIN_TOUCH + 4, alignItems: 'center', justifyContent: 'center', marginTop: spacing.xs },
  textButtonLabel: { fontFamily: fonts.bold, fontSize: 16, color: colors.tealText },
});
