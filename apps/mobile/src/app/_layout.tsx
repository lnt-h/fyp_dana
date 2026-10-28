import { useFonts } from 'expo-font';
import { ActivityIndicator, View } from 'react-native';
import { HankenGrotesk_500Medium } from '@expo-google-fonts/hanken-grotesk/500Medium';
import { HankenGrotesk_700Bold } from '@expo-google-fonts/hanken-grotesk/700Bold';
import { Stack } from 'expo-router';

import { colors } from '../theme/colors';

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({ HankenGrotesk_500Medium, HankenGrotesk_700Bold });
  if (!fontsLoaded && !fontError) {
    return <View style={{ flex: 1, backgroundColor: colors.deepOcean, alignItems: 'center', justifyContent: 'center' }}><ActivityIndicator color={colors.white} accessibilityLabel="Loading Gonarra" /></View>;
  }
  return (
    <Stack
      screenOptions={{
        animation: 'fade',
        contentStyle: { backgroundColor: colors.deepOcean },
        headerShown: false,
      }}
    />
  );
}
