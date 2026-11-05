import type { ReactNode } from 'react';
import { useState } from 'react';
import { KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { CircleButton, Icon, PrimaryButton as UiPrimaryButton, type IconName } from '../../../components/ui';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import type { City } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { elevation } from '../../../theme/elevation';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { VN_TIME_ZONE } from './vnTime';

/** Planner surface tokens (local; shared theme has no border/error tokens yet). */
export const tone = {
  border: '#DCE8EE',
  hairline: '#E4EDF2',
  error: '#AF3434',
  surface: colors.white,
} as const;

const GUTTER = 22;

/** Planner screen frame: circle back button + centred title, scrolling body and an optional sticky footer. */
export function PlannerShell({ title, children, footer, onBack, centered = false }: {
  title: string; children: ReactNode; footer?: ReactNode; onBack?: () => void; centered?: boolean;
}) {
  const insets = useSafeAreaInsets();
  const { t } = useTranslation();
  const back = onBack ?? (() => (router.canGoBack() ? router.back() : router.replace('/home')));
  return <KeyboardAvoidingView style={p.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
    <StatusBar style="dark" />
    <View style={[p.header, { paddingTop: insets.top + spacing.xs }]}>
      <CircleButton icon="back" tone="tint" size={44} accessibilityLabel={t('common.goBack')} onPress={back} />
      <Text accessibilityRole="header" numberOfLines={1} style={p.headerTitle}>{title}</Text>
      <View style={p.headerSpacer} />
    </View>
    <ScrollView keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag"
      contentContainerStyle={[p.content, centered && p.contentCentered, { paddingBottom: footer ? spacing.xl : insets.bottom + spacing.xxl }]}>
      <View style={p.inner}>{children}</View>
    </ScrollView>
    {footer && <View style={[p.footer, { paddingBottom: Math.max(insets.bottom, spacing.md) + 4 }]}><View style={p.inner}>{footer}</View></View>}
  </KeyboardAvoidingView>;
}

export function SparkleIcon({ size = 22, color = colors.audioTeal }: { size?: number; color?: string }) {
  return <Icon name="sparkle" size={size} color={color} />;
}

/** Gradient assistant avatar with the sparkle mark. */
export function AssistantAvatar({ size = 46 }: { size?: number }) {
  return <View style={[p.avatarShadow, { borderRadius: size / 2, height: size, width: size }]}>
    <LinearGradient colors={[colors.audioTeal, colors.deepOcean]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
      style={[StyleSheet.absoluteFill, { borderRadius: size / 2 }]} />
    <Icon name="sparkle" size={Math.round(size * 0.5)} color={colors.white} />
  </View>;
}

/** Assistant intro: avatar + speech bubble. */
export function IntroCard({ label, body }: { label: string; body: string }) {
  return <View style={p.intro}>
    <AssistantAvatar />
    <View style={p.bubble}>
      <Text style={p.introLabel}>{label}</Text>
      <Text style={p.introBody}>{body}</Text>
    </View>
  </View>;
}

/** The user's own words, echoed as a right-aligned bubble. */
export function UserBubble({ text }: { text: string }) {
  return <View style={p.userBubble}><Text style={p.userBubbleText}>{text}</Text></View>;
}

export function SectionLabel({ children, hint, trailing }: { children: string; hint?: string; trailing?: ReactNode }) {
  return <View style={p.sectionBlock}>
    <View style={p.sectionRow}>
      <Text accessibilityRole="header" style={p.section}>{children}</Text>
      {trailing}
    </View>
    {hint && <Text style={p.hint}>{hint}</Text>}
  </View>;
}

export function FieldError({ children, style }: { children?: string; style?: object }) {
  if (!children) return null;
  return <View accessibilityLiveRegion="polite" style={[p.errorRow, style]}>
    <Icon name="warning" size={16} color={tone.error} />
    <Text style={p.error}>{children}</Text>
  </View>;
}

/**
 * Pill segmented control. `tab` semantics for view switches (Form / Describe), `radio` for value choices (days, pace).
 * The selected segment is lifted on white with bold ink text, so the state never depends on colour alone.
 */
export function Segmented<T extends string | number>({ label, options, value, onChange, role = 'tab', invalid = false }: {
  label: string; options: { value: T; label: string; icon?: IconName }[]; value: T | null; onChange: (value: T) => void;
  role?: 'tab' | 'radio'; invalid?: boolean;
}) {
  return <View accessibilityRole={role === 'tab' ? 'tablist' : 'radiogroup'} accessibilityLabel={label} style={[p.segmented, invalid && p.invalid]}>
    {options.map(option => {
      const selected = option.value === value;
      return <Pressable key={String(option.value)} accessibilityRole={role} accessibilityLabel={option.label}
        accessibilityState={role === 'tab' ? { selected } : { checked: selected }} onPress={() => onChange(option.value)}
        style={({ pressed }) => [p.segment, selected && p.segmentSelected, pressed && !selected && { opacity: 0.7 }]}>
        {option.icon && <Icon name={option.icon} size={18} color={selected ? colors.ink : colors.textMuted} />}
        <Text numberOfLines={1} style={[p.segmentText, selected && p.segmentTextSelected]}>{option.label}</Text>
      </Pressable>;
    })}
  </View>;
}

/** Selectable chip with an optional leading icon; selected = deepOcean fill + trailing check (not colour alone). */
export function Chip({ label, selected, onPress, kind, icon, disabled = false, grow = false }: {
  label: string; selected: boolean; onPress: () => void; kind: 'radio' | 'checkbox'; icon?: IconName; disabled?: boolean; grow?: boolean;
}) {
  const fg = selected ? colors.white : colors.ink;
  return <Pressable accessibilityRole={kind} accessibilityLabel={label} accessibilityState={{ checked: selected, disabled }} disabled={disabled} onPress={onPress}
    style={({ pressed }) => [p.chip, grow && p.flex, selected && p.chipSelected, (pressed || disabled) && { opacity: 0.6 }]}>
    {icon && <Icon name={icon} size={18} color={selected ? colors.white : colors.tealText} />}
    <Text numberOfLines={1} style={[p.chipText, { color: fg }]}>{label}</Text>
    {selected && <Icon name="check" size={16} strokeWidth={2.4} color={colors.white} />}
  </Pressable>;
}

export function ChipRow({ children }: { children: ReactNode }) {
  return <View style={p.chipRow}>{children}</View>;
}

const TILE_W = 128;
const TILE_H = 164;

/** Photo-led single-choice city picker: horizontal row of city tiles with a scrim, name and a check badge. */
export function CityTiles({ cities, selectedId, onSelect, label, nameOf }: {
  cities: City[]; selectedId: string | null; onSelect: (city: City) => void; label: string; nameOf: (city: City) => string;
}) {
  return <ScrollView horizontal showsHorizontalScrollIndicator={false} accessibilityRole="radiogroup" accessibilityLabel={label}
    style={p.tileScroll} contentContainerStyle={p.tileRow}>
    {cities.map(city => {
      const selected = city.id === selectedId;
      const image = resolveImage(CITY_IMAGES[city.code], { height: TILE_H, width: TILE_W });
      return <Pressable key={city.id} accessibilityRole="radio" accessibilityLabel={nameOf(city)} accessibilityState={{ checked: selected }}
        onPress={() => onSelect(city)} style={({ pressed }) => [p.tile, selected ? p.tileSelected : elevation.sm, pressed && { transform: [{ scale: 0.97 }] }]}>
        <View style={p.tileClip}>
          {image
            ? <Image source={image.source} placeholder={image.placeholder} placeholderContentFit="cover" contentFit="cover" transition={200} style={StyleSheet.absoluteFill} />
            : <LinearGradient colors={[colors.deepOcean, colors.tealDark]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />}
          <LinearGradient pointerEvents="none" colors={['rgba(7,21,30,0)', 'rgba(7,21,30,0.78)']} locations={[0.35, 1]} style={StyleSheet.absoluteFill} />
          {selected && <View style={p.tileBadge}><Icon name="check" size={16} strokeWidth={2.6} color={colors.white} /></View>}
          <Text numberOfLines={2} style={p.tileName}>{nameOf(city)}</Text>
        </View>
      </Pressable>;
    })}
  </ScrollView>;
}

/** Sticky CTA: shared gradient pill with the sparkle; disabled renders the light grey fill. */
export function PrimaryButton({ label, onPress, disabled = false, busy = false, hint, icon = 'sparkle' }: {
  label: string; onPress: () => void; disabled?: boolean; busy?: boolean; hint?: string; icon?: IconName;
}) {
  return <UiPrimaryButton variant="gradient" icon={icon} label={label} onPress={onPress} disabled={disabled} loading={busy} accessibilityHint={hint} />;
}

/** Banner: `info` (neutral note), `warning` (refusal), `error` (role alert). */
export function Banner({ tone: kind, title, children, action }: { tone: 'info' | 'warning' | 'error'; title?: string; children?: ReactNode; action?: ReactNode }) {
  const iconColor = kind === 'error' ? tone.error : kind === 'warning' ? colors.deepOcean : colors.tealText;
  return <View accessibilityRole={kind === 'error' ? 'alert' : undefined} accessibilityLiveRegion={kind === 'error' ? 'assertive' : 'polite'}
    style={[p.banner, kind === 'warning' && p.bannerWarning, kind === 'error' && p.bannerError]}>
    <View style={[p.bannerIcon, kind === 'warning' && { backgroundColor: '#FDF1DC' }, kind === 'error' && { backgroundColor: '#F8E6E6' }]}>
      <Icon name={kind === 'info' ? 'info' : 'warning'} size={20} color={iconColor} />
    </View>
    <View style={p.flex}>
      {title && <Text style={[p.bannerTitle, kind === 'error' && { color: tone.error }]}>{title}</Text>}
      {typeof children === 'string' ? <Text style={p.bannerBody}>{children}</Text> : children}
      {action}
    </View>
  </View>;
}

/**
 * Date or 24 h time field backed by the native picker, always in Asia/Ho_Chi_Minh. Android opens the system dialog;
 * iOS shows the picker in a bottom sheet with Done.
 */
export function PickerField({ label, text, placeholder, mode, value, onChange, minimumDate, error, pickerTitle, locale, hideLabel = false }: {
  label: string; text: string | null; placeholder?: string; mode: 'date' | 'time'; value: Date; onChange: (value: Date) => void;
  minimumDate?: Date; error?: string; pickerTitle: string; locale: string; hideLabel?: boolean;
}) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const reduceMotion = useReducedMotion();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(value);
  const show = () => { setDraft(value); setOpen(true); };
  return <View style={p.fieldBlock}>
    {!hideLabel && <Text style={p.label}>{label}</Text>}
    <Pressable accessibilityRole="button" accessibilityLabel={`${label}, ${text ?? placeholder ?? ''}`} accessibilityHint={pickerTitle} onPress={show}
      style={({ pressed }) => [p.field, !!error && p.invalid, pressed && { backgroundColor: colors.skyWash }]}>
      <View style={p.fieldIcon}><Icon name={mode === 'date' ? 'calendar' : 'clock'} size={20} color={colors.tealText} /></View>
      <Text numberOfLines={1} style={[p.fieldText, !text && { color: colors.textMuted }]}>{text ?? placeholder}</Text>
      {mode === 'date' && <Icon name="chevron-right" size={18} color={colors.textMuted} />}
    </Pressable>
    <FieldError>{error}</FieldError>
    {open && Platform.OS === 'android' && <DateTimePicker value={value} mode={mode} is24Hour minimumDate={minimumDate} timeZoneName={VN_TIME_ZONE}
      onValueChange={(_event, date) => { setOpen(false); onChange(date); }} onDismiss={() => setOpen(false)} />}
    {Platform.OS !== 'android' && <Modal transparent visible={open} animationType={reduceMotion ? 'none' : 'slide'} onRequestClose={() => setOpen(false)}>
      <View style={p.backdrop}>
        <Pressable accessibilityElementsHidden importantForAccessibility="no" onPress={() => setOpen(false)} style={StyleSheet.absoluteFill} />
        <View accessibilityViewIsModal style={[p.sheet, { paddingBottom: insets.bottom + spacing.md }]}>
          <View style={p.grabber} />
          <View style={p.sheetHeader}>
            <Text accessibilityRole="header" style={p.sheetTitle}>{pickerTitle}</Text>
            <Pressable accessibilityRole="button" accessibilityLabel={t('planner.date.done')} onPress={() => { setOpen(false); onChange(draft); }} style={p.touch}>
              <Text style={p.link}>{t('planner.date.done')}</Text>
            </Pressable>
          </View>
          <DateTimePicker value={draft} mode={mode} display={mode === 'date' ? 'inline' : 'spinner'} is24Hour locale={locale} minimumDate={minimumDate}
            timeZoneName={VN_TIME_ZONE} accentColor={colors.audioTeal} textColor={colors.deepOcean} themeVariant="light" minuteInterval={mode === 'time' ? 5 : undefined}
            onValueChange={(_event, date) => setDraft(date)} />
        </View>
      </View>
    </Modal>}
  </View>;
}

export const p = StyleSheet.create({
  flex: { flex: 1 },
  screen: { flex: 1, backgroundColor: colors.white },
  header: { backgroundColor: colors.white, flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingBottom: spacing.sm },
  headerTitle: { ...typography.headline, flex: 1, textAlign: 'center', fontSize: 19, paddingHorizontal: spacing.xs },
  headerSpacer: { width: 44, height: 44 },
  touch: { minWidth: MIN_TOUCH, minHeight: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
  content: { paddingHorizontal: GUTTER, paddingTop: spacing.xs },
  contentCentered: { flexGrow: 1, justifyContent: 'center' },
  inner: { width: '100%', maxWidth: 480, alignSelf: 'center' },
  footer: { backgroundColor: colors.white, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: '#C9D9E1', paddingHorizontal: GUTTER, paddingTop: spacing.sm },

  avatarShadow: { alignItems: 'center', justifyContent: 'center', backgroundColor: colors.audioTeal, ...elevation.sm },
  intro: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm, marginBottom: spacing.xl },
  bubble: { flex: 1, backgroundColor: colors.white, borderRadius: radii.card, borderTopLeftRadius: 8, borderWidth: 1, borderColor: tone.hairline, paddingHorizontal: 18, paddingVertical: 16, ...elevation.sm },
  introLabel: { fontFamily: fonts.bold, fontSize: 13, letterSpacing: 0.2, color: colors.tealText, marginBottom: 4 },
  introBody: { fontFamily: fonts.medium, fontSize: 16, lineHeight: 23, color: colors.ink },
  userBubble: { alignSelf: 'flex-end', maxWidth: '85%', backgroundColor: colors.deepOcean, borderRadius: radii.card, borderBottomRightRadius: 8, paddingHorizontal: 18, paddingVertical: 13, marginBottom: spacing.md },
  userBubbleText: { fontFamily: fonts.medium, fontSize: 15, lineHeight: 22, color: colors.white },

  sectionBlock: { marginTop: 28, marginBottom: spacing.sm },
  sectionRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm },
  section: { fontFamily: fonts.bold, fontSize: 19, lineHeight: 25, letterSpacing: -0.3, color: colors.ink, flexShrink: 1 },
  hint: { fontFamily: fonts.medium, fontSize: 14, lineHeight: 20, color: colors.textMuted, marginTop: 4 },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  chip: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 16, minHeight: 46, borderRadius: radii.chip, borderWidth: 1, borderColor: tone.border, backgroundColor: colors.white },
  chipSelected: { backgroundColor: colors.deepOcean, borderColor: colors.deepOcean },
  chipText: { fontFamily: fonts.bold, fontSize: 15, color: colors.ink, textAlign: 'center' },
  chipTextSelected: { color: colors.white },
  chipTick: { color: colors.white, fontSize: 15, fontWeight: '700' },

  segmented: { flexDirection: 'row', backgroundColor: colors.skyWash, borderRadius: radii.action, padding: 4, borderWidth: 1, borderColor: 'transparent' },
  segment: { flex: 1, flexDirection: 'row', gap: 6, minHeight: 46, borderRadius: 18, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8 },
  segmentSelected: { backgroundColor: colors.white, ...elevation.sm },
  segmentText: { fontFamily: fonts.bold, fontSize: 15, color: colors.textMuted, textAlign: 'center' },
  segmentTextSelected: { color: colors.ink },
  invalid: { borderColor: tone.error, borderWidth: 1.5 },

  tileScroll: { marginHorizontal: -GUTTER },
  tileRow: { paddingHorizontal: GUTTER, paddingVertical: 6, gap: spacing.sm },
  tile: { width: TILE_W, height: TILE_H, borderRadius: 22, backgroundColor: colors.white, borderWidth: 3, borderColor: colors.white },
  tileSelected: { borderColor: colors.audioTeal, ...elevation.md },
  tileClip: { flex: 1, borderRadius: 19, overflow: 'hidden', justifyContent: 'flex-end', padding: spacing.sm },
  tileBadge: { position: 'absolute', top: 10, right: 10, width: 28, height: 28, borderRadius: 14, backgroundColor: colors.audioTeal, borderWidth: 2, borderColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  tileName: { fontFamily: fonts.bold, fontSize: 16, lineHeight: 20, color: colors.white, letterSpacing: -0.2 },

  banner: { flexDirection: 'row', gap: spacing.sm, borderRadius: radii.card, backgroundColor: colors.skyWash, padding: spacing.md, marginBottom: 14 },
  bannerWarning: { backgroundColor: colors.white, borderWidth: 1.5, borderColor: colors.sun },
  bannerError: { backgroundColor: colors.white, borderWidth: 1.5, borderColor: tone.error },
  bannerIcon: { width: 36, height: 36, borderRadius: radii.iconTile, backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  bannerTitle: { fontFamily: fonts.bold, fontSize: 15, color: colors.ink, marginBottom: 3 },
  bannerBody: { fontFamily: fonts.medium, fontSize: 14, lineHeight: 21, color: colors.deepOcean },

  fieldBlock: { marginBottom: 4 },
  label: { fontFamily: fonts.bold, fontSize: 14, color: colors.deepOcean, marginBottom: spacing.xs },
  field: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, minHeight: 58, borderWidth: 1, borderColor: tone.border, borderRadius: radii.field, backgroundColor: colors.white, paddingLeft: 8, paddingRight: 14 },
  fieldIcon: { width: 40, height: 40, borderRadius: 13, backgroundColor: colors.skyWash, alignItems: 'center', justifyContent: 'center' },
  fieldText: { flex: 1, fontFamily: fonts.bold, fontSize: 16, color: colors.ink },
  errorRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.xs },
  error: { flex: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: tone.error },
  link: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 16 },

  backdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(7,21,30,0.35)' },
  sheet: { backgroundColor: colors.white, borderTopLeftRadius: radii.sheet, borderTopRightRadius: radii.sheet, paddingHorizontal: spacing.lg, paddingTop: 10 },
  grabber: { alignSelf: 'center', width: 40, height: 5, borderRadius: 3, backgroundColor: '#D4E0E5', marginBottom: 6 },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 },
  sheetTitle: { flex: 1, fontFamily: fonts.bold, fontSize: 19, color: colors.ink, letterSpacing: -0.3 },
});
