import Svg, { Path } from 'react-native-svg';
import { colors } from '../../../theme/colors';

export function ArrowIcon({ back = false, color = colors.white }: { back?: boolean; color?: string }) {
  return <Svg width={22} height={22} viewBox="0 0 24 24" aria-hidden={true}>
    <Path d={back ? 'M19 12H5M11 6l-6 6 6 6' : 'M5 12h14M13 6l6 6-6 6'} fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
  </Svg>;
}

export function ProviderIcon({ provider }: { provider: 'email' | 'google' | 'apple' }) {
  if (provider === 'email') return <Svg width={24} height={24} viewBox="0 0 24 24" aria-hidden={true}><Path d="M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1ZM3 6l9 7 9-7" fill="none" stroke="white" strokeWidth={1.8} strokeLinejoin="round" /></Svg>;
  if (provider === 'apple') return <Svg width={24} height={24} viewBox="0 0 24 24" aria-hidden={true}><Path fill="#111820" d="M17.05 12.54c.03 3.24 2.85 4.32 2.88 4.33-.02.08-.45 1.54-1.49 3.05-.9 1.3-1.83 2.6-3.3 2.63-1.44.03-1.9-.85-3.55-.85-1.64 0-2.15.82-3.52.88-1.42.05-2.5-1.41-3.4-2.71-1.84-2.66-3.25-7.51-1.36-10.79A5.28 5.28 0 0 1 7.78 6.4c1.4-.03 2.73.95 3.59.95.86 0 2.47-1.17 4.16-1 .71.03 2.71.29 4 2.18-.1.06-2.51 1.46-2.48 4.01ZM14.34 4.56c.75-.91 1.26-2.17 1.12-3.43-1.08.04-2.39.72-3.17 1.63-.7.8-1.31 2.08-1.15 3.3 1.2.09 2.43-.61 3.2-1.5Z" /></Svg>;
  return <Svg width={24} height={24} viewBox="0 0 48 48" aria-hidden={true}>
    <Path fill="#4285F4" d="M43.61 24.46c0-1.36-.12-2.66-.35-3.92H24v7.42h11a9.4 9.4 0 0 1-4.08 6.18v5.14h6.61c3.87-3.56 6.08-8.8 6.08-14.82Z" />
    <Path fill="#34A853" d="M24 44c5.4 0 9.93-1.79 13.24-4.86l-6.62-5.14c-1.79 1.2-4.08 1.93-6.62 1.93-5.22 0-9.66-3.52-11.25-8.26H5.92v5.3A20 20 0 0 0 24 44Z" />
    <Path fill="#FBBC05" d="M12.75 27.67a12 12 0 0 1 0-7.34v-5.3H5.92a20 20 0 0 0 0 17.94l6.83-5.3Z" />
    <Path fill="#EA4335" d="M24 12.07c2.94 0 5.57 1.01 7.65 2.99l5.74-5.74A19.2 19.2 0 0 0 24 4 20 20 0 0 0 5.92 15.03l6.83 5.3C14.34 15.59 18.78 12.07 24 12.07Z" />
  </Svg>;
}
