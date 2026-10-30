import { ActivityIndicator, Text, View } from 'react-native';
import { useAuth } from '@clerk/expo';
import { Redirect } from 'expo-router';

// ClerkProvider completes the browser auth session; the originating screen
// activates the returned session. Do not start a second OAuth attempt here.
export default function SSOCallback() {
  const { isLoaded, isSignedIn } = useAuth();
  if (isLoaded && isSignedIn) return <Redirect href="/home" />;
  return <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16 }}>
    <ActivityIndicator accessibilityLabel="Completing sign-in" />
    <Text>Completing sign-in. You can return to the app.</Text>
  </View>;
}
