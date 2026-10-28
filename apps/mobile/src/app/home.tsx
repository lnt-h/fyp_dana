import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { Image, ImageSourcePropType, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';

import { Wordmark } from '../components/brand/BrandMarks';
import { HomeMapBackdrop } from '../features/home/components/HomeMapBackdrop';
import { HomeTabBar } from '../features/home/components/HomeTabBar';
import { AudioMark } from '../features/onboarding/components/OnboardingMosaic';
import { colors } from '../theme/colors';

const designFrame = {
  height: 956,
  width: 440,
} as const;

const images = {
  avatar: require('../../assets/images/places/cyclo.png'),
  beach: require('../../assets/images/places/beach.png'),
  museum: require('../../assets/images/places/cham-sculpture.png'),
} satisfies Record<string, ImageSourcePropType>;

function NotificationIcon({ size }: { size: number }) {
  return (
    <Svg height={size} viewBox="0 0 24 24" width={size}>
      <Path d="M12.0201 2.91003C8.71009 2.91003 6.02009 5.60003 6.02009 8.91003V11.8C6.02009 12.41 5.76009 13.34 5.45009 13.86L4.30009 15.77C3.59009 16.95 4.08009 18.26 5.38009 18.7C9.69009 20.14 14.3401 20.14 18.6501 18.7C19.8601 18.3 20.3901 16.87 19.7301 15.77L18.5801 13.86C18.2801 13.34 18.0201 12.41 18.0201 11.8V8.91003C18.0201 5.61003 15.3201 2.91003 12.0201 2.91003Z" fill="none" stroke="#292D32" strokeLinecap="round" strokeWidth={2} />
      <Path d="M13.8699 3.19994C13.5599 3.10994 13.2399 3.03994 12.9099 2.99994C11.9499 2.87994 11.0299 2.94994 10.1699 3.19994C10.4599 2.45994 11.1799 1.93994 12.0199 1.93994C12.8599 1.93994 13.5799 2.45994 13.8699 3.19994Z" fill="none" stroke="#292D32" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
      <Path d="M15.02 19.0601C15.02 20.7101 13.67 22.0601 12.02 22.0601C11.2 22.0601 10.44 21.7201 9.90002 21.1801C9.36002 20.6401 9.02002 19.8801 9.02002 19.0601" fill="none" stroke="#292D32" strokeWidth={2} />
    </Svg>
  );
}

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
          <Text style={[styles.locationText, { fontSize: 14 * scale, lineHeight: 20 * scale }]}>Da Nang, Viet Nam</Text>
          <View style={[styles.weatherDot, { height: 4 * scale, width: 4 * scale }]} />
          <Text style={[styles.sun, { fontSize: 18 * scale }]}>☀</Text>
          <Text style={[styles.locationText, { fontSize: 14 * scale, lineHeight: 20 * scale }]}>26°C</Text>
        </View>

        <Pressable
          accessibilityLabel="Notifications"
          accessibilityRole="button"
          hitSlop={10}
          style={[styles.notification, { height: 24 * scale, left: 330 * scale, top: 88 * scale, width: 24 * scale }]}
        >
          <NotificationIcon size={24 * scale} />
        </Pressable>

        <Pressable
          accessibilityLabel="Profile"
          accessibilityRole="button"
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
          <Image resizeMode="cover" source={images.avatar} style={styles.avatarImage} />
        </Pressable>

        <Pressable
          accessibilityLabel="Search places, stories and activities"
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
            Places, stories and your move...
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
          <Text style={[styles.markerLabelText, { fontSize: 10 * scale }]}>Cham Museum</Text>
        </View>

        <Pressable
          accessibilityLabel="Center map on my location"
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
        </View>

        <View style={[styles.nav, { left: 56 * scale, top: 842 * scale }]}>
          <HomeTabBar scale={scale} />
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
  avatarImage: {
    height: '100%',
    opacity: 0.88,
    width: '100%',
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
  nav: {
    position: 'absolute',
    zIndex: 4,
  },
  notification: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
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
    color: 'rgba(41,45,50,0.56)',
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
  sun: {
    color: colors.ink,
    marginLeft: 6,
    marginRight: 3,
  },
  weatherDot: {
    backgroundColor: colors.ink,
    borderRadius: 2,
    marginLeft: 8,
  },
  wordmark: {
    position: 'absolute',
  },
});
