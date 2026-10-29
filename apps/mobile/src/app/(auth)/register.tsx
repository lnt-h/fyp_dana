import { useCallback, useState } from 'react';
import { BackHandler, Keyboard, Pressable, StyleSheet, Text, View } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { Action, AuthShell, BrandSymbol, Field, Heading, PreviewNote, SocialActions, TextLink, palette, s } from '../../features/auth/components/AuthUI';
import { TripReadyIllustration } from '../../features/auth/components/TripReadyIllustration';
import { useAccount, type Interest, type TravelType } from '../../features/account/AccountContext';
import { TravelPreferences } from '../../features/account/TravelPreferences';

export default function RegisterScreen() {
  const { profile, startPreview } = useAccount();
  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [accepted, setAccepted] = useState(false);
  const [selected, setSelected] = useState<Interest[]>(profile.interests);
  const [travelType, setTravelType] = useState<TravelType | undefined>(profile.travelType);
  const [notice, setNotice] = useState('');
  const back = useCallback(() => {
    Keyboard.dismiss();
    if (step > 1) setStep(step - 1);
    else if (router.canGoBack()) router.back();
    else router.replace('/welcome');
  }, [step]);
  useFocusEffect(useCallback(() => {
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => { back(); return true; });
    return () => subscription.remove();
  }, [back]));
  function next() { Keyboard.dismiss(); setNotice(''); setStep(step + 1); }
  function finish() {
    startPreview({ name: name.trim(), email: email.trim(), interests: selected, travelType });
    setPassword(''); router.replace('/home');
  }
  return <AuthShell key={step} back={back} step={step} skip={step === 2 ? () => setStep(3) : undefined}>
    {step === 1 && <>
      <BrandSymbol /><Heading title={'Create your\nGonarra account'} subtitle="Start exploring Da Nang your way." />
      <Field label="Full name" placeholder="Your name" value={name} onChangeText={setName} autoComplete="name" autoCapitalize="words" />
      <Field label="Email address" placeholder="you@example.com" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" />
      <Field label="Password" placeholder="Create a password" value={password} onChangeText={setPassword} password autoCapitalize="none" autoCorrect={false} autoComplete="new-password" onSubmitEditing={next} returnKeyType="next" />
      <View style={styles.consent}>
        <Pressable accessibilityRole="checkbox" accessibilityLabel="Agree to terms and privacy policy (preview)" accessibilityState={{ checked: accepted }} aria-checked={accepted} onPress={() => setAccepted(!accepted)} style={styles.checkboxTouch}>
          <View style={[styles.checkbox, accepted && styles.checked]}><Text style={styles.tick}>{accepted ? '✓' : ''}</Text></View>
        </Pressable>
        <Text style={styles.consentText}>I agree to the <Text accessibilityRole="link" style={s.link} onPress={() => setNotice('Terms of Service are not published yet.')}>Terms of Service</Text> and <Text accessibilityRole="link" style={s.link} onPress={() => setNotice('Privacy Policy is not published yet.')}>Privacy Policy</Text></Text>
      </View>
      {!!notice && <Text accessibilityLiveRegion="polite" style={s.note}>{notice}</Text>}
      <Action title="Continue" arrow onPress={next} /><PreviewNote />
      <SocialActions divider />
      <TextLink title="Already have an account? Sign in" onPress={() => router.replace('/login')} />
    </>}
    {step === 2 && <>
      <Heading title={'Tell us about\nyour travel style'} subtitle="Make it yours. You can change this in Profile." left />
      <TravelPreferences selected={selected} onSelect={setSelected} travelType={travelType} onTravelType={setTravelType} />
      <Action title="Next" arrow onPress={next} />
    </>}
    {step === 3 && <View style={styles.completion}>
      <TripReadyIllustration /><Heading title="You’re all set!" subtitle="Let’s start exploring Da Nang together." />
      <Action title="Start Exploring" arrow onPress={finish} /><PreviewNote />
    </View>}
  </AuthShell>;
}
const styles = StyleSheet.create({
  completion: { flex: 1, justifyContent: 'center', paddingBottom: 12 },
  consent: { flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: 48 },
  checkbox: { width: 24, height: 24, borderRadius: 7, borderWidth: 1.5, borderColor: palette.muted, alignItems: 'center', justifyContent: 'center' },
  checked: { backgroundColor: palette.audioTeal, borderColor: palette.audioTeal }, tick: { color: palette.white },
  consentText: { flex: 1, fontSize: 13, lineHeight: 20, color: palette.deepOcean },
  checkboxTouch: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
});
