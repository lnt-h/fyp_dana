import { useEffect, useState } from 'react';
import { router, useLocalSearchParams } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Keyboard, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTabBarClearance } from '../home/components/HomeTabBar';
import { DEFAULT_CITY_CODE } from '../../lib/api/types';
import { colors } from '../../theme/colors';
import { GuideChat, type GuideScope } from './GuideChat';
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

/**
 * SCR-034 Guide tab. Default: a city-level chat (`scope: CITY`, Đà Nẵng, ADR-010). `placeId` scopes the chat to one
 * place (`scope: PLACE`, from a place card or the picker); `pick=1` shows the place picker.
 */
export function GuideScreen() {
  const insets = useSafeAreaInsets();
  const clearance = useTabBarClearance();
  const keyboardOpen = useKeyboardOpen();
  const params = useLocalSearchParams<{ placeId?: string; pick?: string }>();
  // The params are the only selection state, so "Ask the Guide" on a place card always switches the session.
  const placeId = params.placeId || null;
  const picking = !placeId && params.pick === '1';
  const choose = (id: string) => router.setParams({ pick: '', placeId: id });
  const openPicker = () => router.setParams({ pick: '1', placeId: '' });
  const chooseCity = () => router.setParams({ pick: '', placeId: '' });
  // FYP release: Đà Nẵng only (Hội An is an area of it).
  const scope: GuideScope = placeId ? { kind: 'PLACE', placeId } : { cityCode: DEFAULT_CITY_CODE, kind: 'CITY' };
  const key = scope.kind === 'PLACE' ? `place:${scope.placeId}` : `city:${scope.cityCode}`;

  return <View style={g.screen}>
    <StatusBar style="dark" />
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={g.fill}>
      {!picking
        ? <View style={[g.chat, { paddingBottom: keyboardOpen ? 8 : clearance, paddingTop: insets.top + 8 }]}>
          <View style={[g.inner, g.fill]}>
            <GuideChat key={key} keyboardOpen={keyboardOpen} onChangePlace={openPicker} scope={scope} />
          </View>
        </View>
        : <ScrollView contentContainerStyle={[g.content, { paddingBottom: clearance, paddingTop: insets.top + 8 }]} showsVerticalScrollIndicator={false}>
          <View style={g.inner}>
            <GuideHeader />
            <GuidePlacePicker onPick={choose} onPickCity={chooseCity} />
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
  screen: { backgroundColor: colors.canvas, flex: 1 },
});
