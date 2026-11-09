import { Image, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { Wordmark } from '../../components/brand/BrandMarks';
import { Action, AuthShell, SocialActions, TextLink, palette } from '../../features/auth/components/AuthUI';
import { ProviderIcon } from '../../features/auth/components/AuthIcons';
import { useAuth } from '@clerk/expo';
import { demoNoAuth } from '../../lib/demoAuth';
import { Redirect } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { fonts } from '../../theme/typography';

export default function WelcomeScreen() {
  const { t } = useTranslation();
  const { isSignedIn } = useAuth();
  const { height } = useWindowDimensions();
  const compact = height < 750;
  const heroHeight = Math.max(120, Math.min(180, height * 0.2));
  if (demoNoAuth || isSignedIn) return <Redirect href="/home" />;
  return (
    <AuthShell>
      <View style={styles.brand}>
        <Wordmark width={176} />
        <Text style={styles.tagline}>{t('auth.welcome.tagline')}</Text>
      </View>
      <View style={styles.destination} accessibilityElementsHidden aria-hidden importantForAccessibility="no-hide-descendants">
        <View style={[styles.heroFrame, { height: heroHeight }]}>
          <Image source={require('../../../assets/images/welcome/dragon-bridge-detail.png')} resizeMode="cover" style={styles.hero} />
          <LinearGradient colors={['transparent', 'rgba(22, 33, 43, 0.82)']} style={styles.heroShade} />
          <View style={styles.destinationCopy}>
            <Text style={styles.eyebrow}>{t('auth.welcome.heroEyebrow')}</Text>
            <Text style={styles.destinationName}>{t('auth.welcome.heroCity')}</Text>
            <View style={styles.accent} />
          </View>
        </View>
        <View style={styles.detailFrame}>
          <Image source={require('../../../assets/images/welcome/cathedral.png')} resizeMode="cover" style={styles.detailPhoto} />
        </View>
      </View>
      <Text accessibilityRole="header" style={[styles.title, compact && styles.compactTitle]}>
        {t('auth.welcome.title')}<Text style={styles.period}>.</Text>
      </Text>
      <Text style={styles.subtitle}>{t('auth.welcome.subtitle')}</Text>
      <Action title={t('auth.welcome.signUpEmail')} icon={<ProviderIcon provider="email" />} onPress={() => router.push('/register')} />
      <SocialActions />
      <View style={styles.footer}>
        <Pressable accessibilityRole="link" accessibilityLabel={t('auth.welcome.signInLabel')} onPress={() => router.push('/login')} style={({ pressed }) => [styles.signIn, pressed && { opacity: 0.7 }]}>
          <Text style={styles.accountPrompt}>{t('auth.welcome.accountPrompt')} <Text style={styles.signInText}>{t('auth.welcome.signIn')}</Text></Text>
        </Pressable>
        <TextLink title={t('auth.welcome.explore')} onPress={() => router.replace('/home')} />
      </View>
    </AuthShell>
  );
}

const styles = StyleSheet.create({
  brand: { marginTop: 4, gap: 10 },
  tagline: { fontSize: 13, fontFamily: fonts.medium, color: palette.textSecondary },
  destination: { marginTop: 20, marginBottom: 20, paddingBottom: 12 },
  heroFrame: { width: '100%', borderRadius: 16, overflow: 'hidden', backgroundColor: palette.skyWash },
  hero: { position: 'absolute', width: '100%', height: '100%', borderRadius: 16 },
  heroShade: { position: 'absolute', bottom: 0, left: 0, right: 0, height: '65%' },
  destinationCopy: { position: 'absolute', bottom: 22, left: 22, right: 120 },
  eyebrow: { color: palette.white, fontFamily: fonts.semibold, fontSize: 13 },
  destinationName: { color: palette.white, fontFamily: fonts.bold, fontSize: 30, lineHeight: 36, marginTop: 4 },
  accent: { width: 32, height: 4, borderRadius: 2, backgroundColor: palette.coral, marginTop: 10 },
  detailFrame: { position: 'absolute', bottom: 0, right: 18, width: 96, height: 120, borderRadius: 18, borderWidth: 5, borderColor: palette.white, backgroundColor: palette.white, shadowColor: palette.ink, shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.16, shadowRadius: 10, elevation: 4 },
  detailPhoto: { width: '100%', height: '100%', borderRadius: 13 },
  title: { fontSize: 32, lineHeight: 38, fontFamily: fonts.bold, letterSpacing: -1, color: palette.ink },
  compactTitle: { fontSize: 28, lineHeight: 34 },
  period: { color: palette.coral },
  subtitle: { fontSize: 16, lineHeight: 24, color: palette.muted, marginTop: 8, marginBottom: 8 },
  footer: { marginTop: 12, paddingBottom: 8 },
  signIn: { minHeight: 48, paddingVertical: 12, justifyContent: 'center', alignItems: 'center' },
  accountPrompt: { color: palette.muted, fontSize: 15, lineHeight: 22, textAlign: 'center' },
  signInText: { color: palette.tealText, fontFamily: fonts.bold },
});
