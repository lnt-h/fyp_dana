import { Stack } from 'expo-router';

import { colors } from '../theme/colors';

export default function RootLayout() {
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
