import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '../../../components/ui';
import { colors } from '../../../theme/colors';
import { radii } from '../../../theme/spacing';
import { elevation } from '../../../theme/elevation';
import { fonts } from '../../../theme/typography';
import { AudioMark } from '../../onboarding/components/OnboardingMosaic';

const voiceEnabled = process.env.EXPO_PUBLIC_FEATURE_VOICE === '1';

type Props = {
  cityName: string;
  disabled: boolean;
  onPress: () => void;
  onVoice?: () => void;
};

/** Search pill over the map (SCR-008 → SCR-021). The mic shows only with FEATURE_VOICE (SCR-035). */
export function SearchPill({ cityName, disabled, onPress, onVoice }: Props) {
  const { t } = useTranslation();
  return (
    <View style={[styles.pill, elevation.sm, disabled && styles.disabled]}>
      <Pressable
        accessibilityLabel={t('home.search.pillLabel', { city: cityName })}
        accessibilityRole="search"
        accessibilityState={{ disabled }}
        disabled={disabled}
        onPress={onPress}
        style={styles.main}
      >
        <Icon color={colors.textMuted} name="search" size={20} />
        <Text numberOfLines={1} style={styles.placeholder}>{t('home.search.placeholder', { city: cityName })}</Text>
      </Pressable>
      {voiceEnabled && onVoice ? (
        <Pressable accessibilityLabel={t('home.search.voice')} accessibilityRole="button" disabled={disabled} hitSlop={4} onPress={onVoice} style={styles.mic}>
          <AudioMark size={40} />
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  disabled: { opacity: 0.6 },
  main: { alignItems: 'center', flex: 1, flexDirection: 'row', gap: 10, height: '100%', paddingLeft: 16, paddingRight: 8 },
  mic: { alignItems: 'center', height: 44, justifyContent: 'center', marginRight: 4, width: 44 },
  pill: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderColor: colors.hairline,
    borderRadius: radii.field,
    borderWidth: 1,
    flexDirection: 'row',
    height: 52,
  },
  placeholder: { color: colors.textMuted, flex: 1, fontFamily: fonts.regular, fontSize: 15, lineHeight: 20 },
});
