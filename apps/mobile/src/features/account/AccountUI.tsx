import type { ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import Svg, { Path } from 'react-native-svg';
import { ArrowIcon } from '../auth/components/AuthIcons';
import { palette } from '../auth/components/AuthUI';

const paths = {
  person: 'M8 7a4 4 0 1 0 8 0a4 4 0 1 0-8 0M4 21v-2a8 7 0 0 1 16 0v2',
  compass: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20M16 8l-2 6-6 2 2-6Z',
  settings: 'M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1ZM12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8',
  shield: 'M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6ZM8 12l3 3 5-6',
  info: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20M12 11v6M12 7v.1',
  motion: 'M2 8h5M2 12h3M2 16h5M15 5a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 8v4l3 2',
  exit: 'M9 3H4v18h5M9 12h12M16 7l5 5-5 5',
};
export type AccountIconName = keyof typeof paths;
export function AccountIcon({ name }: { name: AccountIconName }) {
  return <Svg width={23} height={23} viewBox="0 0 24 24" aria-hidden={true}><Path d={paths[name]} fill="none" stroke={palette.audioTeal} strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" /></Svg>;
}
export function AccountShell({ title, children, fallback = '/profile' }: { title: string; children: ReactNode; fallback?: '/profile' | '/home' }) {
  const insets = useSafeAreaInsets();
  const { t } = useTranslation();
  return <KeyboardAvoidingView style={a.screen} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
    <StatusBar style="dark" />
    <View style={[a.header, { paddingTop: insets.top + 8 }]}>
      <Pressable accessibilityLabel={t('common.goBack')} accessibilityRole="button" onPress={() => router.canGoBack() ? router.back() : router.replace(fallback)} style={a.touch}><ArrowIcon back color={palette.deepOcean} /></Pressable>
      <Text accessibilityRole="header" style={a.headerTitle}>{title}</Text><View style={a.touch} />
    </View>
    <ScrollView keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" contentContainerStyle={[a.content, { paddingBottom: insets.bottom + 28 }]}>
      <View style={a.inner}>{children}</View>
    </ScrollView>
  </KeyboardAvoidingView>;
}
export function AccountRow({ icon, title, subtitle, onPress, trailing }: { icon: AccountIconName; title: string; subtitle?: string; onPress?: () => void; trailing?: ReactNode }) {
  const content = <><View style={a.icon}><AccountIcon name={icon} /></View><View style={a.rowCopy}><Text style={a.rowTitle}>{title}</Text>{subtitle && <Text style={a.body}>{subtitle}</Text>}</View>{trailing ?? (onPress && <Text style={a.chevron}>›</Text>)}</>;
  return onPress ? <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [a.row, pressed && { opacity: 0.65 }]}>{content}</Pressable> : <View style={a.row}>{content}</View>;
}
export const a = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#F5FAFC' },
  header: { backgroundColor: '#F5FAFC', flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, paddingBottom: 12 },
  touch: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { flex: 1, textAlign: 'center', fontFamily: 'HankenGrotesk_700Bold', fontSize: 20, color: palette.deepOcean },
  content: { paddingHorizontal: 22, paddingTop: 12 }, inner: { width: '100%', maxWidth: 480, alignSelf: 'center' },
  card: { borderRadius: 24, backgroundColor: palette.white, borderWidth: 1, borderColor: '#E4EDF2', overflow: 'hidden', marginBottom: 18 },
  padded: { padding: 22 },
  section: { fontFamily: 'HankenGrotesk_700Bold', color: palette.muted, fontSize: 11, letterSpacing: 1.8, marginTop: 10, marginBottom: 12, marginLeft: 4 },
  title: { fontFamily: 'HankenGrotesk_700Bold', fontSize: 28, lineHeight: 34, color: palette.deepOcean },
  body: { color: palette.muted, fontFamily: 'HankenGrotesk_500Medium', fontSize: 14, lineHeight: 21, marginTop: 4 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 14, padding: 18, minHeight: 80 },
  icon: { width: 42, height: 42, borderRadius: 14, backgroundColor: palette.skyWash, alignItems: 'center', justifyContent: 'center' },
  rowCopy: { flex: 1 }, rowTitle: { fontFamily: 'HankenGrotesk_700Bold', fontSize: 16, color: palette.deepOcean },
  chevron: { color: palette.muted, fontSize: 28 }, divider: { height: 1, backgroundColor: '#ECF2F5', marginHorizontal: 18 },
  note: { color: palette.muted, fontSize: 12, lineHeight: 18, textAlign: 'center', paddingHorizontal: 16, marginVertical: 12 },
});
