import type { ReactNode } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { ApiError } from '../../../lib/api/source';
import { colors } from '../../../theme/colors';
import { BUTTON_HEIGHT, radii } from '../../../theme/spacing';

export const border = colors.hairline;
export const screenBackground = colors.canvas;

export const isNotFound = (error: unknown) => error instanceof ApiError && (error.status === 404 || error.error.code === 'resource_not_found');

/** Button (52 pt, radius 14): `primary` is teal with white text, `secondary` is outlined. */
export function PillButton({ title, onPress, variant = 'primary', icon, disabled = false, hint }: {
  title: string; onPress: () => void; variant?: 'primary' | 'secondary'; icon?: ReactNode; disabled?: boolean; hint?: string;
}) {
  const primary = variant === 'primary';
  return <Pressable
    accessibilityHint={hint}
    accessibilityRole="button"
    accessibilityState={{ disabled }}
    disabled={disabled}
    onPress={onPress}
    style={({ pressed }) => [ui.pill, primary ? ui.pillPrimary : ui.pillSecondary, (pressed || disabled) && { opacity: 0.6 }]}
  >
    {icon}
    <Text style={[ui.pillText, { color: primary ? colors.white : colors.ink }]}>{title}</Text>
  </Pressable>;
}

/** Centered full-screen message (loading, error, not found). */
export function ScreenMessage({ title, body, busy = false, children }: { title: string; body?: string; busy?: boolean; children?: ReactNode }) {
  return <View accessibilityLiveRegion="polite" style={ui.message}>
    {busy && <ActivityIndicator color={colors.primary} size="large" />}
    <Text accessibilityRole={busy ? undefined : 'header'} style={ui.messageTitle}>{title}</Text>
    {!!body && <Text style={ui.messageBody}>{body}</Text>}
    {children && <View style={ui.messageActions}>{children}</View>}
  </View>;
}

export const ui = StyleSheet.create({
  message: { alignItems: 'center', alignSelf: 'center', flex: 1, gap: 12, justifyContent: 'center', maxWidth: 420, padding: 24, width: '100%' },
  messageActions: { alignSelf: 'stretch', gap: 12, marginTop: 8 },
  messageBody: { color: colors.textMuted, fontFamily: 'HankenGrotesk_400Regular', fontSize: 16, lineHeight: 24, textAlign: 'center' },
  messageTitle: { color: colors.ink, fontFamily: 'HankenGrotesk_700Bold', fontSize: 24, letterSpacing: -0.6, lineHeight: 30, textAlign: 'center' },
  pill: { alignItems: 'center', borderRadius: radii.button, flexDirection: 'row', gap: 10, justifyContent: 'center', minHeight: BUTTON_HEIGHT, paddingHorizontal: 20 },
  pillPrimary: { backgroundColor: colors.primary },
  pillSecondary: { backgroundColor: colors.white, borderColor: border, borderWidth: 1.5 },
  pillText: { fontFamily: 'HankenGrotesk_700Bold', fontSize: 17, flexShrink: 1, textAlign: 'center' },
  touch: { alignItems: 'center', height: 44, justifyContent: 'center', width: 44 },
});
