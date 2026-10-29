import { Image, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { Wordmark } from '../../components/brand/BrandMarks';
import { Action, AuthShell, SocialActions, TextLink, palette } from '../../features/auth/components/AuthUI';
import { ProviderIcon } from '../../features/auth/components/AuthIcons';
import { useAccount } from '../../features/account/AccountContext';

export default function WelcomeScreen() {
  const { clearSession } = useAccount();
  return (
    <AuthShell>
      <View style={styles.brand}>
        <Wordmark width={176} />
        <Text style={styles.tagline}>EXPLORE · PLAN · EXPERIENCE</Text>
      </View>
      <View style={styles.destination} accessibilityElementsHidden aria-hidden importantForAccessibility="no-hide-descendants">
        <View style={styles.heroFrame}>
          <Image source={require('../../../assets/images/welcome/dragon-bridge-detail.png')} resizeMode="cover" style={styles.hero} />
          <LinearGradient colors={['transparent', 'rgba(3, 45, 63, 0.85)']} style={styles.heroShade} />
          <View style={styles.destinationCopy}>
            <Text style={styles.eyebrow}>VIETNAM</Text>
            <Text style={styles.destinationName}>Da Nang</Text>
            <View style={styles.accent} />
          </View>
        </View>
        <View style={styles.detailFrame}>
          <Image source={require('../../../assets/images/welcome/cathedral.png')} resizeMode="cover" style={styles.detailPhoto} />
        </View>
      </View>
      <Text accessibilityRole="header" style={styles.title}>
        Your Da Nang{'\n'}story starts here<Text style={styles.period}>.</Text>
      </Text>
      <Text style={styles.subtitle}>Discover local stories. Make the day yours.</Text>
      <Action title="Continue with Email" icon={<ProviderIcon provider="email" />} onPress={() => router.push('/register')} />
      <SocialActions />
      <TextLink title="Sign in" onPress={() => router.push('/login')} />
      <TextLink title="Explore without an account  →" onPress={() => { clearSession(); router.replace('/home'); }} />
    </AuthShell>
  );
}

const styles = StyleSheet.create({
  brand: { marginTop: 14, gap: 12 },
  tagline: { fontSize: 10, letterSpacing: 2.6, color: palette.muted },
  destination: { marginTop: 28, marginBottom: 32, paddingBottom: 16 },
  heroFrame: { width: '100%', aspectRatio: 1.35, borderRadius: 24, overflow: 'hidden', backgroundColor: palette.skyWash },
  hero: { position: 'absolute', width: '100%', height: '100%', borderRadius: 24 },
  heroShade: { position: 'absolute', bottom: 0, left: 0, right: 0, height: '65%' },
  destinationCopy: { position: 'absolute', bottom: 22, left: 22, right: 120 },
  eyebrow: { color: palette.white, fontFamily: 'HankenGrotesk_700Bold', fontSize: 10, letterSpacing: 3 },
  destinationName: { color: palette.white, fontFamily: 'HankenGrotesk_700Bold', fontSize: 30, lineHeight: 36, marginTop: 4 },
  accent: { width: 32, height: 4, borderRadius: 2, backgroundColor: palette.sun, marginTop: 10 },
  detailFrame: { position: 'absolute', bottom: 0, right: 18, width: 96, height: 120, borderRadius: 18, borderWidth: 5, borderColor: palette.white, backgroundColor: palette.white, shadowColor: palette.deepOcean, shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.16, shadowRadius: 10, elevation: 4 },
  detailPhoto: { width: '100%', height: '100%', borderRadius: 13 },
  title: { fontSize: 34, lineHeight: 40, fontFamily: 'HankenGrotesk_700Bold', letterSpacing: -1, color: palette.deepOcean },
  period: { color: palette.sun },
  subtitle: { fontSize: 16, lineHeight: 24, color: palette.muted, marginTop: 12, marginBottom: 18 },
});
