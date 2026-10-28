import { useState } from 'react';
import { BackHandler, Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { useCallback } from 'react';
import { Action, AuthShell, BrandSymbol, Field, Heading, PreviewNote, TextLink, palette, s } from '../../features/auth/components/AuthUI';
import { TripReadyIllustration } from '../../features/auth/components/TripReadyIllustration';

const interests = [
  { label: 'Culture', image: require('../../../assets/images/places/cham-sculpture.png') },
  { label: 'Beach', image: require('../../../assets/images/places/beach.png') },
  { label: 'Food', image: require('../../../assets/images/places/mi-quang.png') },
  { label: 'Nature', image: require('../../../assets/images/places/linh-ung-pagoda.png') },
] as const;
export default function RegisterScreen() {
  const [step, setStep] = useState(1);
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [accepted, setAccepted] = useState(false);
  const [selected, setSelected] = useState<string[]>([]); const [travelType, setTravelType] = useState<string>();
  const [notice, setNotice] = useState('');
  const back = useCallback(() => { if (step > 1) setStep(step - 1); else if (router.canGoBack()) router.back(); else router.replace('/welcome'); }, [step]);
  useFocusEffect(useCallback(() => { const subscription = BackHandler.addEventListener('hardwareBackPress', () => { back(); return true; }); return () => subscription.remove(); }, [back]));
  function next() { setNotice(''); setStep(2); }
  return <AuthShell key={step} back={back} step={step} skip={step === 2 ? () => { setSelected([]); setTravelType(undefined); setStep(3); } : undefined}>
    {step === 1 && <>
      <BrandSymbol /><Heading title={'Create your\nGonarra account'} subtitle="Start exploring Da Nang your way." />
      <Field label="Full name" placeholder="Your name" value={name} onChangeText={setName} autoComplete="name" />
      <Field label="Email address" placeholder="you@example.com" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} autoComplete="email" />
      <Field label="Password" placeholder="At least 8 characters" value={password} onChangeText={setPassword} password autoCapitalize="none" autoComplete="new-password" />
      <View style={styles.consent}>
        <Pressable accessibilityRole="checkbox" accessibilityLabel="Agree to terms and privacy policy (preview)" accessibilityState={{ checked: accepted }} onPress={() => setAccepted(!accepted)} style={styles.checkboxTouch}>
          <View style={[styles.checkbox, accepted && { backgroundColor: palette.audioTeal, borderColor: palette.audioTeal }]}><Text style={{ color: 'white' }}>{accepted ? '✓' : ''}</Text></View>
        </Pressable>
        <Text style={styles.consentText}>I agree to the <Text accessibilityRole="link" style={s.link} onPress={() => setNotice('Terms of Service are not published yet.')}>Terms of Service</Text> and <Text accessibilityRole="link" style={s.link} onPress={() => setNotice('Privacy Policy is not published yet.')}>Privacy Policy</Text></Text>
      </View>
      {notice !== '' && <Text accessibilityLiveRegion="polite" style={s.note}>{notice}</Text>}
      <Action title="Next →" onPress={next} /><PreviewNote />
      <TextLink title="Already have an account? Sign in" onPress={() => router.replace('/login')} />
    </>}
    {step === 2 && <>
      <Heading title="Tell us about your travel style" subtitle="Choose what you love. You can skip this step." left />
      <Text style={styles.section}>I’m interested in</Text>
      <View style={styles.grid}>{interests.map(item => { const checked = selected.includes(item.label); return <Pressable key={item.label} accessibilityRole="checkbox" accessibilityLabel={item.label} accessibilityState={{ checked }} onPress={() => setSelected(checked ? selected.filter(x => x !== item.label) : [...selected, item.label])} style={styles.tile}><View style={[styles.imageFrame, checked && { borderColor: palette.audioTeal }]}><Image source={item.image} resizeMode="cover" style={styles.image} />{checked && <View style={styles.check}><Text style={styles.tick}>✓</Text></View>}</View><Text style={styles.tileLabel}>{item.label}</Text></Pressable>; })}</View>
      <Text style={styles.section}>Travel type</Text><View style={styles.types}>{['Solo', 'Couple', 'Family', 'Friends'].map(type => <Pressable key={type} accessibilityRole="radio" accessibilityState={{ checked: type === travelType }} onPress={() => setTravelType(type)} style={[styles.chip, type === travelType && { backgroundColor: palette.audioTeal, borderColor: palette.audioTeal }]}><Text style={[styles.chipText, type === travelType && { color: 'white' }]}>{type}</Text></Pressable>)}</View>
      <Action title="Next →" onPress={() => setStep(3)} />
    </>}
    {step === 3 && <>
      <TripReadyIllustration /><Heading title="You’re all set!" subtitle="Let’s start exploring Da Nang together." />
      <Action title="Start Exploring →" onPress={() => { setPassword(''); router.replace('/home'); }} />
      <Text style={s.note}>UI preview</Text>
    </>}
  </AuthShell>;
}
const styles = StyleSheet.create({
  consent: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 48 }, checkbox: { width: 25, height: 25, borderRadius: 7, borderWidth: 1.5, borderColor: palette.muted, alignItems: 'center', justifyContent: 'center' }, consentText: { flex: 1, fontSize: 13, lineHeight: 20, color: palette.deepOcean }, checkboxTouch: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  section: { fontSize: 19, color: palette.deepOcean, fontWeight: '700', marginBottom: 16, marginTop: 12 }, grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 14 }, tile: { width: '47%', marginBottom: 10 }, imageFrame: { width: '100%', aspectRatio: 1.15, borderRadius: 22, borderWidth: 3, borderColor: 'transparent', overflow: 'hidden' }, image: { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', borderRadius: 19 }, tileLabel: { fontSize: 16, fontWeight: '700', textAlign: 'center', color: palette.deepOcean, marginTop: 9 }, check: { position: 'absolute', right: 10, top: 10, backgroundColor: palette.audioTeal, borderRadius: 18, width: 30, height: 30, alignItems: 'center', justifyContent: 'center' }, tick: { color: 'white', fontSize: 21, fontWeight: '700' }, types: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 24 }, chip: { paddingHorizontal: 16, minHeight: 48, borderWidth: 1.5, borderColor: palette.border, borderRadius: 18, justifyContent: 'center' }, chipText: { color: palette.deepOcean, fontWeight: '700', fontSize: 14 },
});
