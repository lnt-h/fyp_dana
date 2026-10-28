import { Image, StyleSheet, View } from 'react-native';
import Svg, { Circle, G, Path } from 'react-native-svg';
import { colors } from '../../../theme/colors';

export function TripReadyIllustration() {
  return <View style={styles.scene} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
    <Svg width="100%" height="100%" viewBox="0 0 440 440">
      <Circle cx={88} cy={200} r={86} fill={colors.skyWash} /><Circle cx={359} cy={232} r={78} fill="#EDF7FC" />
      <G transform="rotate(-8 220 280)">
        <Path d="M60 174H380V392H60Z" fill="#DDF1F5" /><Path d="M60 277L176 244L253 300L380 252V392H60Z" fill="#D8EFDC" />
        <Path d="M60 219L180 174H244L60 318ZM236 174H282L380 236V290Z" fill="#BCE6EF" />
        <Path d="M114 174L146 392M218 174L246 392M316 174L338 392M60 241L380 328M60 355L380 219" stroke="white" strokeWidth={10} />
        <Path d="M99 324C123 270 169 346 205 291S241 230 272 244S309 286 345 255" fill="none" stroke={colors.audioTeal} strokeWidth={6} strokeLinecap="round" strokeDasharray="2 12" />
        {[{ x: 99, y: 324 }, { x: 205, y: 291 }, { x: 345, y: 255 }].map(p => <Circle key={p.x} cx={p.x} cy={p.y} r={9} fill={colors.audioTeal} stroke="white" strokeWidth={4} />)}
      </G>
      <Path d="M220 48C185 48 160 74 160 107C160 149 220 213 220 213C220 213 280 149 280 107C280 74 255 48 220 48Z" fill={colors.audioTeal} /><Circle cx={220} cy={108} r={22} fill="white" />
      <Path d="M351 56L358 76L378 83L358 90L351 110L344 90L324 83L344 76ZM384 119L388 131L400 135L388 139L384 151L380 139L368 135L380 131Z" fill={colors.sun} />
    </Svg>
    <Image source={require('../../../../assets/images/places/cham-sculpture.png')} style={[styles.photo, { left: '1%', top: '43%', transform: [{ rotate: '-10deg' }] }]} />
    <Image source={require('../../../../assets/images/places/beach.png')} style={[styles.photo, { right: '0%', top: '63%', transform: [{ rotate: '9deg' }] }]} />
  </View>;
}
const styles = StyleSheet.create({ scene: { width: '100%', aspectRatio: 1, marginVertical: 22 }, photo: { position: 'absolute', width: '25%', height: '25%', borderRadius: 18, borderWidth: 5, borderColor: 'white' } });
