import { memo } from 'react';
import Svg, { Path, Polygon, Rect } from 'react-native-svg';

type Props = {
  height: number;
  width: number;
};

/** Stylised Da Nang map rebuilt as vectors so it stays crisp at every density. */
export const HomeMapBackdrop = memo(function HomeMapBackdrop({ height, width }: Props) {
  return (
    <Svg height={height} viewBox="0 0 440 458" width={width}>
      <Rect fill="#EEE9DC" height={458} width={440} />

      <Path d="M0 0H112C80 24 38 48 0 55Z" fill="#DDF3F5" />
      <Polygon fill="#B7DB72" points="0,320 116,223 264,292 94,419 0,441" />
      <Path
        d="M51 339C76 298 111 260 151 252C172 248 198 253 209 266C197 280 174 288 151 292C125 297 104 313 89 335C76 354 62 365 51 339Z"
        fill="#55AEB5"
      />

      <Path d="M-20 89L201 89L307 -8" fill="none" stroke="#D9DDDD" strokeWidth={8} />
      <Path d="M68 39L231 145L440 187" fill="none" stroke="#D9DDDD" strokeWidth={8} />
      <Path d="M-18 206L158 130L310 238L459 186" fill="none" stroke="#D9DDDD" strokeWidth={8} />
      <Path d="M244 -15L158 130L73 234" fill="none" stroke="#D9DDDD" strokeWidth={8} />
      <Path d="M440 104L359 304L440 388" fill="none" stroke="#D9DDDD" strokeWidth={8} />
      <Path d="M267 94L354 160L315 259L438 335" fill="none" stroke="#D9DDDD" strokeWidth={8} />
      <Path d="M88 370L219 351L279 458" fill="none" stroke="#D9DDDD" strokeWidth={8} />
      <Path d="M-20 454L89 370L0 283" fill="none" stroke="#D9DDDD" strokeWidth={8} />
      <Path d="M179 458L168 398L327 390L382 458" fill="none" stroke="#D9DDDD" strokeWidth={8} />
    </Svg>
  );
});
