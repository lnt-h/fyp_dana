import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { useAccount } from '../../features/account/AccountContext';
import { AccountIcon } from '../../features/account/AccountUI';
import { Image, ImageSourcePropType, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';

import { Wordmark } from '../../components/brand/BrandMarks';
import { HomeMapBackdrop } from '../../features/home/components/HomeMapBackdrop';
import { AudioMark } from '../../features/onboarding/components/OnboardingMosaic';
import { PlanCard } from '../../features/planner/input/PlanCard';
import { defaultCity } from '../../lib/api/fixtures/hoi-an';
import { colors } from '../../theme/colors';

const designFrame = {
  height: 956,
  width: 440,
} as const;

const images = {
  beach: require('../../../assets/images/places/beach.png'),
  museum: require('../../../assets/images/places/cham-sculpture.png'),
} satisfies Record<string, ImageSourcePropType>;

function LocationIcon({ size }: { size: number }) {
  return (
    <Svg height={size} viewBox="0 0 20 20" width={size}>
      <Path d="M17.1834 7.04171C16.3084 3.19171 12.9501 1.45837 10.0001 1.45837C7.05008 1.45837 3.68341 3.18337 2.80841 7.03337C1.83341 11.3334 4.46675 14.975 6.85008 17.2667C8.61675 18.9667 11.3834 18.9667 13.1417 17.2667C15.5251 14.975 18.1584 11.3417 17.1834 7.04171ZM10.0001 11.2167C8.55008 11.2167 7.37508 10.0417 7.37508 8.59171C7.37508 7.14171 8.55008 5.96671 10.0001 5.96671C11.4501 5.96671 12.6251 7.14171 12.6251 8.59171C12.6251 10.0417 11.4501 11.2167 10.0001 11.2167Z" fill={colors.ink} />
    </Svg>
  );
}

function SearchIcon({ size }: { size: number }) {
  return (
    <Svg height={size} viewBox="0 0 20 20" width={size}>
      <Path d="M17.5001 9.58329C17.5001 13.9555 13.9557 17.5 9.58342 17.5C5.21116 17.5 1.66675 13.9555 1.66675 9.58329C1.66675 5.21104 5.21116 1.66663 9.58342 1.66663C13.9557 1.66663 17.5001 5.21104 17.5001 9.58329Z" fill="none" stroke="#292D32" strokeLinecap="round" strokeLinejoin="round" strokeOpacity={0.5} strokeWidth={1.5} />
      <Path d="M18.3334 18.3333L16.6667 16.6666" fill="none" stroke="#292D32" strokeLinecap="round" strokeOpacity={0.5} strokeWidth={1.5} />
    </Svg>
  );
}

function GpsIcon({ size }: { size: number }) {
  return (
    <Svg height={size} viewBox="0 0 30 30" width={size}>
      <Circle cx={15} cy={15} fill="none" r={9.375} stroke="#292D32" strokeWidth={2} />
      <Circle cx={15} cy={15} fill="none" r={3.75} stroke="#292D32" strokeWidth={2} />
      <Path d="M15 5V2.5M5 15H2.5M15 25V27.5M25 15H27.5" fill="none" stroke="#292D32" strokeLinecap="round" strokeWidth={2} />
    </Svg>
  );
}

type MarkerProps = {
  height: number;
  left: number;
  scale: number;
  source: ImageSourcePropType;
  top: number;
  width: number;
};

function MapMarker({ height, left, scale, source, top, width }: MarkerProps) {
  return (
    <View
      style={[
        styles.marker,
        {
          borderRadius: 12 * scale,
          borderWidth: 2 * scale,
          height: height * scale,
          left: left * scale,
          top: top * scale,
          width: width * scale,
        },
      ]}
    >
      <Image resizeMode="cover" source={source} style={StyleSheet.absoluteFill} />
    </View>
  );
}

export default function HomeScreen() {
  const { t, i18n } = useTranslation();
  const { profile } = useAccount();
  const cityName = i18n.resolvedLanguage === 'vi' ? defaultCity.name_vi : defaultCity.name_en;
  const { height, width } = useWindowDimensions();
  const scale = Math.min(width / designFrame.width, height / designFrame.height);
  const canvasWidth = designFrame.width * scale;
  const canvasLeft = (width - canvasWidth) / 2;

  return (
    <View style={styles.screen}>
      <StatusBar style="dark" />

      <View style={[styles.canvas, { height: designFrame.height * scale, left: canvasLeft, width: canvasWidth }]}>
        <View style={[styles.map, { height: 458 * scale, width: canvasWidth }]}>
          <HomeMapBackdrop height={458 * scale} width={canvasWidth} />
        </View>

        <View style={[styles.wordmark, { left: 20 * scale, top: 84 * scale }]}>
          <Wordmark width={128 * scale} />
        </View>

        <View style={[styles.location, { left: 20 * scale, top: 148 * scale }]}>
          <LocationIcon size={20 * scale} />
          <Text style={[styles.locationText, { fontSize: 14 * scale, lineHeight: 20 * scale }]}>
            {t('home.location', { city: cityName, country: t('common.country') })}
          </Text>
        </View>

        <Pressable
          accessibilityLabel={t('home.profile')}
          accessibilityRole="button"
          onPress={() => router.push('/profile')}
          style={[
            styles.avatar,
            {
              borderRadius: 26 * scale,
              height: 52 * scale,
              left: 372 * scale,
              top: 77 * scale,
              width: 52 * scale,
            },
          ]}
        >
          <LinearGradient colors={['#BDEBFF', '#75C8DD']} style={StyleSheet.absoluteFill} />
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>{profile.name.trim() ? <Text style={{ color: colors.deepOcean, fontFamily: 'HankenGrotesk_700Bold', fontSize: 20 }}>{profile.name.trim()[0].toUpperCase()}</Text> : <AccountIcon name="person" />}</View>
        </Pressable>

        <Pressable
          accessibilityLabel={t('home.searchLabel')}
          accessibilityRole="button"
          style={[
            styles.search,
            {
              borderRadius: 26 * scale,
              height: 52 * scale,
              left: 16 * scale,
              paddingLeft: 10 * scale,
              top: 176 * scale,
              width: 408 * scale,
            },
          ]}
        >
          <SearchIcon size={20 * scale} />
          <Text
            numberOfLines={1}
            style={[
              styles.searchPlaceholder,
              { fontSize: 14 * scale, lineHeight: 20 * scale, marginLeft: 10 * scale },
            ]}
          >
            {t('home.searchPlaceholder')}
          </Text>
          <View
            style={[
              styles.searchAudio,
              {
                height: 40 * scale,
                right: 5 * scale,
                top: 5 * scale,
                width: 40 * scale,
              },
            ]}
          >
            <AudioMark size={40 * scale} />
          </View>
        </Pressable>

        <MapMarker height={58} left={58} scale={scale} source={images.beach} top={289} width={58} />
        <MapMarker height={62} left={305} scale={scale} source={images.museum} top={251} width={58} />
        <View
          style={[
            styles.markerLabel,
            {
              borderRadius: 4 * scale,
              height: 25 * scale,
              left: 293 * scale,
              top: 313 * scale,
              width: 83 * scale,
            },
          ]}
        >
          <Text style={[styles.markerLabelText, { fontSize: 10 * scale }]}>{t('home.sampleMarker')}</Text>
        </View>

        <Pressable
          accessibilityLabel={t('home.gps')}
          accessibilityRole="button"
          style={[
            styles.gps,
            {
              borderRadius: 24 * scale,
              height: 48 * scale,
              left: 376 * scale,
              top: 360 * scale,
              width: 48 * scale,
            },
          ]}
        >
          <GpsIcon size={30 * scale} />
        </Pressable>

        <View
          style={[
            styles.sheet,
            {
              borderTopLeftRadius: 40 * scale,
              borderTopRightRadius: 40 * scale,
              height: 515 * scale,
              top: 441 * scale,
              width: canvasWidth,
            },
          ]}
        >
          <View
            style={[
              styles.sheetHandle,
              {
                borderRadius: 2 * scale,
                height: 4 * scale,
                top: 10 * scale,
                width: 68 * scale,
              },
            ]}
          />
          <PlanCard cityName={cityName} scale={scale} onPress={() => router.push('/plan/new')} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  avatar: {
    borderColor: colors.white,
    borderWidth: 2,
    overflow: 'hidden',
    position: 'absolute',
    shadowColor: colors.ink,
    shadowOffset: { height: 3, width: 0 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
  },
  canvas: {
    overflow: 'hidden',
    position: 'absolute',
    top: 0,
  },
  gps: {
    alignItems: 'center',
    backgroundColor: colors.white,
    justifyContent: 'center',
    position: 'absolute',
    shadowColor: colors.ink,
    shadowOffset: { height: 4, width: 0 },
    shadowOpacity: 0.14,
    shadowRadius: 12,
  },
  location: {
    alignItems: 'center',
    flexDirection: 'row',
    position: 'absolute',
  },
  locationText: {
    color: colors.ink,
  },
  map: {
    left: 0,
    position: 'absolute',
    top: 0,
  },
  marker: {
    backgroundColor: colors.skyWash,
    borderColor: colors.white,
    overflow: 'hidden',
    position: 'absolute',
    shadowColor: colors.ink,
    shadowOffset: { height: 4, width: 0 },
    shadowOpacity: 0.2,
    shadowRadius: 7,
  },
  markerLabel: {
    alignItems: 'center',
    backgroundColor: colors.deepOcean,
    justifyContent: 'center',
    position: 'absolute',
    shadowColor: colors.audioTeal,
    shadowOffset: { height: 2, width: 0 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
  },
  markerLabelText: {
    color: colors.white,
  },
  screen: {
    backgroundColor: colors.white,
    flex: 1,
    overflow: 'hidden',
  },
  search: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderColor: '#A9D6DE',
    borderWidth: 1,
    flexDirection: 'row',
    position: 'absolute',
    shadowColor: colors.ink,
    shadowOffset: { height: 2, width: 0 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
  },
  searchAudio: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
  },
  searchPlaceholder: {
    color: colors.textMuted,
    paddingRight: 54,
  },
  sheet: {
    backgroundColor: colors.white,
    left: 0,
    position: 'absolute',
    shadowColor: colors.ink,
    shadowOffset: { height: -4, width: 0 },
    shadowOpacity: 0.06,
    shadowRadius: 14,
  },
  sheetHandle: {
    alignSelf: 'center',
    backgroundColor: '#C9C9C9',
    position: 'absolute',
  },
  wordmark: {
    position: 'absolute',
  },
});
