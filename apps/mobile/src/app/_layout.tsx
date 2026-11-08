import '../i18n';

import { ClerkProvider, useSession } from '@clerk/expo';
import { tokenCache } from '@clerk/expo/token-cache';
import { useFonts } from 'expo-font';
import { ActivityIndicator, View } from 'react-native';
import { HankenGrotesk_400Regular } from '@expo-google-fonts/hanken-grotesk/400Regular';
import { HankenGrotesk_500Medium } from '@expo-google-fonts/hanken-grotesk/500Medium';
import { HankenGrotesk_600SemiBold } from '@expo-google-fonts/hanken-grotesk/600SemiBold';
import { HankenGrotesk_700Bold } from '@expo-google-fonts/hanken-grotesk/700Bold';
import { Stack } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { useTranslation } from 'react-i18next';

import { colors } from '../theme/colors';
import { AccountProvider, useAccount } from '../features/account/AccountContext';
import { ConfigErrorScreen } from '../features/config/ConfigErrorScreen';
import { demoNoAuth } from '../lib/demoAuth';
import { ApiAuthBridge } from '../lib/api/ApiAuthBridge';
import { isApiConfigured } from '../lib/api/config';
import { SelectedCityProvider } from '../features/home/cityStore';
import { useReducedMotion } from '../hooks/useReducedMotion';

const publishableKey = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";

if (!publishableKey) {
  throw new Error("Missing EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY. Add your key to .env.local.\nRun: 1) clerk auth login  2) clerk link  3) clerk env pull — then restart the dev server.");
}

function AppStack() {
  const { t } = useTranslation();
  const reduceMotion = useReducedMotion();
  const { isLoaded, isSignedIn } = useAccount();
  const { session } = useSession();
  if (!isLoaded) return <View style={{ flex: 1, justifyContent: 'center' }}><ActivityIndicator accessibilityLabel={t('common.loadingSession')} /></View>;
  const pendingTask = !demoNoAuth && Boolean(session?.currentTask);
  return <Stack screenOptions={{ animation: reduceMotion ? 'none' : 'fade', contentStyle: { backgroundColor: colors.deepOcean }, headerShown: false }}>
    <Stack.Protected guard={pendingTask}><Stack.Screen name="auth-task" /></Stack.Protected>
    <Stack.Protected guard={!pendingTask}>
      <Stack.Screen name="index" />
      <Stack.Screen name="onboarding" />
      <Stack.Screen name="(auth)" />
      <Stack.Screen name="sso-callback" />
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="profile" />
      <Stack.Screen name="settings" />
      <Stack.Screen name="travel-preferences" />
      <Stack.Screen name="language" />
      <Stack.Protected guard={Boolean(isSignedIn)}>
        <Stack.Screen name="edit-profile" />
        <Stack.Screen name="delete-account" />
        <Stack.Screen name="plan/new" />
        <Stack.Screen name="plan/[previewId]/index" />
        <Stack.Screen name="plan/[previewId]/proposal" />
        <Stack.Screen name="plan/[previewId]/health" />
        <Stack.Screen name="place/[placeId]" />
        <Stack.Screen name="trip/[tripId]/today" />
        <Stack.Screen name="trip/[tripId]/book" options={{ presentation: 'modal' }} />
      </Stack.Protected>
    </Stack.Protected>
  </Stack>;
}

export default function RootLayout() {
  const { t } = useTranslation();
  const [fontsLoaded, fontError] = useFonts({ HankenGrotesk_400Regular, HankenGrotesk_500Medium, HankenGrotesk_600SemiBold, HankenGrotesk_700Bold });
  if (!fontsLoaded && !fontError) {
    return <View style={{ flex: 1, backgroundColor: colors.deepOcean, alignItems: 'center', justifyContent: 'center' }}><ActivityIndicator color={colors.white} accessibilityLabel={t('common.loadingApp')} /></View>;
  }
  // EXPO_PUBLIC_API_URL is required: there is no local data to fall back to (config.ts).
  if (!isApiConfigured()) return <ConfigErrorScreen />;
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ClerkProvider publishableKey={publishableKey} tokenCache={tokenCache}>
        <ApiAuthBridge />
        <AccountProvider>
          <SelectedCityProvider><AppStack /></SelectedCityProvider>
        </AccountProvider>
      </ClerkProvider>
    </GestureHandlerRootView>
  );
}
