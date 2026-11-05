import { Tabs } from 'expo-router/js-tabs';

import { HomeTabBar } from '../../features/home/components/HomeTabBar';

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{ headerShown: false }} tabBar={props => <HomeTabBar {...props} />}>
      <Tabs.Screen name="home" />
      <Tabs.Screen name="explore" />
      <Tabs.Screen name="guide" />
      <Tabs.Screen name="trips" />
    </Tabs>
  );
}
