import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTabBarClearance } from '../home/components/HomeTabBar';
import { colors } from '../../theme/colors';

/** Placeholder body for a tab whose screen is not built yet; clears the floating tab bar. */
export function TabPlaceholder({ title, subtitle }: { title: string; subtitle: string }) {
  const insets = useSafeAreaInsets();
  const clearance = useTabBarClearance();
  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />
      <LinearGradient colors={['#D8F2FF', '#F5FAFC']} pointerEvents="none" style={styles.wash} />
      <ScrollView contentContainerStyle={[styles.content, { paddingBottom: clearance, paddingTop: insets.top + 32 }]}>
        <View style={styles.inner}>
          <Text accessibilityRole="header" style={styles.title}>{title}</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  content: { flexGrow: 1, paddingHorizontal: 24 },
  inner: { alignSelf: 'center', maxWidth: 480, width: '100%' },
  screen: { backgroundColor: '#F5FAFC', flex: 1 },
  subtitle: { color: colors.textMuted, fontFamily: 'HankenGrotesk_500Medium', fontSize: 16, lineHeight: 24, marginTop: 10 },
  title: { color: colors.deepOcean, fontFamily: 'HankenGrotesk_700Bold', fontSize: 32, letterSpacing: -1, lineHeight: 38 },
  wash: { height: 260, left: 0, position: 'absolute', right: 0, top: 0 },
});
