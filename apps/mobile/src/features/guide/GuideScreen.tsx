import { useEffect, useState } from 'react';
import { LinearGradient } from 'expo-linear-gradient';
import { router, useLocalSearchParams } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Keyboard, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTabBarClearance } from '../home/components/HomeTabBar';
import { colors } from '../../theme/colors';
import { GuideChat } from './GuideChat';
import { GuideHeader } from './components/GuideHeader';
import { GuidePlacePicker } from './components/GuidePlacePicker';

function useKeyboardOpen() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const show = Keyboard.addListener(showEvent, () => setOpen(true));
    const hide = Keyboard.addListener(hideEvent, () => setOpen(false));
    return () => { show.remove(); hide.remove(); };
  }, []);
  return open;
}

/** SCR-034 Guide tab: place chooser without `placeId`, otherwise a chat scoped to that place. */
export function GuideScreen() {
  const insets = useSafeAreaInsets();
  const clearance = useTabBarClearance();
  const keyboardOpen = useKeyboardOpen();
  const params = useLocalSearchParams<{ placeId?: string }>();
  // The `placeId` param is the only selection state, so "Ask the Guide" on a place card always switches the session.
  const placeId = params.placeId || null;
  const choose = (id: string) => router.setParams({ placeId: id });

  return <View style={g.screen}>
    <StatusBar style="dark" />
    <LinearGradient colors={[colors.skyWash, colors.white]} pointerEvents="none" style={g.wash} />
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={g.fill}>
      {placeId
        ? <View style={[g.chat, { paddingBottom: keyboardOpen ? 8 : clearance, paddingTop: insets.top + 8 }]}>
          <View style={[g.inner, g.fill]}>
            <GuideChat key={placeId} keyboardOpen={keyboardOpen} onChangePlace={() => choose('')} placeId={placeId} />
          </View>
        </View>
        : <ScrollView contentContainerStyle={[g.content, { paddingBottom: clearance, paddingTop: insets.top + 8 }]} showsVerticalScrollIndicator={false}>
          <View style={g.inner}>
            <GuideHeader />
            <GuidePlacePicker onPick={choose} />
          </View>
        </ScrollView>}
    </KeyboardAvoidingView>
  </View>;
}

const g = StyleSheet.create({
  chat: { flex: 1, paddingHorizontal: 20 },
  content: { flexGrow: 1, paddingHorizontal: 20 },
  fill: { flex: 1 },
  inner: { alignSelf: 'center', maxWidth: 480, width: '100%' },
  screen: { backgroundColor: colors.white, flex: 1 },
  wash: { height: 220, left: 0, position: 'absolute', right: 0, top: 0 },
});
