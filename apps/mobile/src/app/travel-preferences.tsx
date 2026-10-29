import { useState } from 'react';
import { Text } from 'react-native';
import { router } from 'expo-router';
import { useAccount } from '../features/account/AccountContext';
import { AccountShell, a } from '../features/account/AccountUI';
import { TravelPreferences } from '../features/account/TravelPreferences';
import { Action, TextLink } from '../features/auth/components/AuthUI';

export default function TravelPreferencesScreen() {
  const { profile, updateProfile } = useAccount();
  const [selected, setSelected] = useState(profile.interests);
  const [travelType, setTravelType] = useState(profile.travelType);
  function close() { router.canGoBack() ? router.back() : router.replace('/profile'); }
  return <AccountShell title="Travel preferences">
    <Text style={[a.body, { marginBottom: 20 }]}>There’s no one way to explore. Find yours.</Text>
    <TravelPreferences selected={selected} onSelect={setSelected} travelType={travelType} onTravelType={setTravelType} />
    <Action title="Save preferences" onPress={() => { updateProfile({ interests: selected, travelType }); close(); }} />
    <TextLink title="Cancel" onPress={close} />
  </AccountShell>;
}
