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

import { CircleButton, Icon, type IconName, PhotoFallback } from '../../../components/ui';
import { useReducedMotion } from '../../../hooks/useReducedMotion';
import type { City } from '../../../lib/api/types';
import { CITY_IMAGES } from '../../../lib/images/cityImages';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors, type CategoryTone } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { VN_TIME_ZONE } from './vnTime';

/** Planner surface tokens (local; shared theme has no border/error tokens yet). */
export const tone = {
  border: colors.hairline,
  hairline: colors.hairline,
  error: colors.danger,
  surface: colors.white,
} as const;

const GUTTER = 22;

/**
 * Planner screen frame: circle back button + centred title, an optional sub-header (wizard progress), scrolling body
 * and an optional sticky footer. `scrollKey` scrolls the body back to the top when it changes (wizard step).
 */
export function PlannerShell({ title, children, footer, onBack, centered = false, subheader, scrollKey }: {
  title: string; children: ReactNode; footer?: ReactNode; onBack?: () => void; centered?: boolean; subheader?: ReactNode; scrollKey?: string | number;
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
    {subheader ? <View style={p.subheader}><View style={p.inner}>{subheader}</View></View> : null}
    {/* No top over-scroll: dragging down while typing must not pull the form away and reveal blank space. */}
    <ScrollView key={scrollKey} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" bounces={false} overScrollMode="never"
      contentContainerStyle={[p.content, centered && p.contentCentered, { paddingBottom: footer ? spacing.xl : insets.bottom + spacing.xxl }]}>
      <View style={p.inner}>{children}</View>
    </ScrollView>
    {footer && <View style={[p.footer, { paddingBottom: Math.max(insets.bottom, spacing.md) + 4 }]}><View style={p.inner}>{footer}</View></View>}
  </KeyboardAvoidingView>;
}

/** Flat assistant avatar: warm tile with the lantern mark. Decorative. */
export function AssistantAvatar({ size = 46 }: { size?: number }) {
  return <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
    style={[p.avatar, { borderRadius: size / 2, height: size, width: size }]}>
    <Icon name="lantern" size={Math.round(size * 0.55)} color={colors.accentText} />
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

/**
 * Selectable chip with an optional leading icon. Plain chips: selected = primary fill + white text + trailing check.
 * Category chips (`tone` from `categoryColor`): the icon always carries the category colour; selected = category soft
 * fill with a category-coloured ring and a check, so the state never depends on colour alone.
 */
export function Chip({ label, selected, onPress, kind, icon, disabled = false, grow = false, tone: category }: {
  label: string; selected: boolean; onPress: () => void; kind: 'radio' | 'checkbox'; icon?: IconName; disabled?: boolean; grow?: boolean;
  tone?: CategoryTone;
}) {
  const fg = selected && !category ? colors.white : colors.ink;
  const iconColor = category ? category.fg : selected ? colors.white : colors.primary;
  return <Pressable accessibilityRole={kind} accessibilityLabel={label} accessibilityState={{ checked: selected, disabled }} disabled={disabled} onPress={onPress}
    style={({ pressed }) => [p.chip, grow && p.flex, selected && (category ? [p.chipCategory, { backgroundColor: category.bg, borderColor: category.fg }] : p.chipSelected), (pressed || disabled) && { opacity: 0.6 }]}>
    {icon && <Icon name={icon} size={18} color={iconColor} strokeWidth={2} />}
    <Text maxFontSizeMultiplier={1.4} numberOfLines={1} style={[p.chipText, { color: fg }]}>{label}</Text>
    {selected && <Icon name="check" size={16} strokeWidth={2.4} color={category ? colors.ink : colors.white} />}
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
        onPress={() => onSelect(city)} style={({ pressed }) => [p.tile, selected && p.tileSelected, pressed && { transform: [{ scale: 0.97 }] }]}>
        <View style={p.tileClip}>
          {image
            ? <Image source={image.source} placeholder={image.placeholder} placeholderContentFit="cover" contentFit="cover" transition={200} style={StyleSheet.absoluteFill} />
            : <PhotoFallback tone="dark" icon="map-pin" />}
          <LinearGradient pointerEvents="none" colors={['rgba(7,21,30,0)', 'rgba(7,21,30,0.78)']} locations={[0.35, 1]} style={StyleSheet.absoluteFill} />
          {selected && <View style={p.tileBadge}><Icon name="check" size={16} strokeWidth={2.6} color={colors.white} /></View>}
          <Text numberOfLines={2} style={p.tileName}>{nameOf(city)}</Text>
        </View>
      </Pressable>;
    })}
  </ScrollView>;
}

/** Banner: `info` (neutral note), `warning` (refusal), `error` (role alert). */
export function Banner({ tone: kind, title, children, action }: { tone: 'info' | 'warning' | 'error'; title?: string; children?: ReactNode; action?: ReactNode }) {
  const iconColor = kind === 'error' ? tone.error : kind === 'warning' ? colors.deepOcean : colors.tealText;
  return <View accessibilityRole={kind === 'error' ? 'alert' : undefined} accessibilityLiveRegion={kind === 'error' ? 'assertive' : 'polite'}
    style={[p.banner, kind === 'warning' && p.bannerWarning, kind === 'error' && p.bannerError]}>
    <View style={[p.bannerIcon, kind === 'warning' && { backgroundColor: colors.warnBg }, kind === 'error' && { backgroundColor: colors.dangerBg }]}>
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
      style={({ pressed }) => [p.field, !!error && p.invalid, pressed && { backgroundColor: colors.surfaceTint }]}>
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
  screen: { flex: 1, backgroundColor: colors.canvas },
  header: { backgroundColor: colors.white, flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingBottom: spacing.sm },
  headerTitle: { ...typography.headline, flex: 1, textAlign: 'center', fontSize: 19, paddingHorizontal: spacing.xs },
  headerSpacer: { width: 44, height: 44 },
  subheader: { backgroundColor: colors.white, paddingHorizontal: GUTTER, paddingBottom: spacing.sm, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.hairline },
  touch: { minWidth: MIN_TOUCH, minHeight: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
  content: { paddingHorizontal: GUTTER, paddingTop: spacing.xs },
  contentCentered: { flexGrow: 1, justifyContent: 'center' },
  inner: { width: '100%', maxWidth: 480, alignSelf: 'center' },
  footer: { backgroundColor: colors.white, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.hairline, paddingHorizontal: GUTTER, paddingTop: spacing.sm },

  avatar: { alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surfaceTint },
  intro: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm, marginBottom: spacing.xl },
  bubble: { flex: 1, backgroundColor: colors.white, borderRadius: radii.card, borderTopLeftRadius: 8, borderWidth: 1, borderColor: tone.hairline, paddingHorizontal: 18, paddingVertical: 16 },
  introLabel: { ...typography.eyebrow, marginBottom: 6 },
  introBody: { fontFamily: fonts.regular, fontSize: 16, lineHeight: 23, color: colors.ink },
  userBubble: { alignSelf: 'flex-end', maxWidth: '85%', backgroundColor: colors.primary, borderRadius: radii.card, borderBottomRightRadius: 8, paddingHorizontal: 18, paddingVertical: 13, marginBottom: spacing.md },
  userBubbleText: { fontFamily: fonts.regular, fontSize: 15, lineHeight: 22, color: colors.white },

  sectionBlock: { marginTop: 28, marginBottom: spacing.sm },
  sectionRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm },
  section: { fontFamily: fonts.bold, fontSize: 19, lineHeight: 25, letterSpacing: -0.3, color: colors.ink, flexShrink: 1 },
  hint: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.textMuted, marginTop: 4 },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  chip: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 16, minHeight: 46, borderRadius: radii.chip, borderWidth: 1, borderColor: tone.border, backgroundColor: colors.white },
  chipSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipCategory: { borderWidth: 2, paddingHorizontal: 15 },
  chipText: { fontFamily: fonts.semibold, fontSize: 15, color: colors.ink, textAlign: 'center' },
  chipTextSelected: { color: colors.white },
  chipTick: { color: colors.white, fontSize: 15, fontWeight: '700' },

  segmented: { flexDirection: 'row', backgroundColor: colors.surfaceTint, borderRadius: radii.button, padding: 4, borderWidth: 1, borderColor: 'transparent' },
  segment: { flex: 1, flexDirection: 'row', gap: 6, minHeight: 46, borderRadius: 18, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8 },
  segmentSelected: { backgroundColor: colors.white, borderColor: colors.hairline, borderWidth: 1 },
  segmentText: { fontFamily: fonts.bold, fontSize: 15, color: colors.textMuted, textAlign: 'center' },
  segmentTextSelected: { color: colors.ink },
  invalid: { borderColor: tone.error, borderWidth: 1.5 },

  tileScroll: { marginHorizontal: -GUTTER },
  tileRow: { paddingHorizontal: GUTTER, paddingVertical: 6, gap: spacing.sm },
  tile: { width: TILE_W, height: TILE_H, borderRadius: radii.photoCard, backgroundColor: colors.white, borderWidth: 3, borderColor: colors.white },
  tileSelected: { borderColor: colors.audioTeal },
  tileClip: { flex: 1, borderRadius: radii.photoCard - 3, overflow: 'hidden', justifyContent: 'flex-end', padding: spacing.sm },
  tileBadge: { position: 'absolute', top: 10, right: 10, width: 28, height: 28, borderRadius: 14, backgroundColor: colors.audioTeal, borderWidth: 2, borderColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  tileName: { fontFamily: fonts.bold, fontSize: 16, lineHeight: 20, color: colors.white, letterSpacing: -0.2 },

  banner: { flexDirection: 'row', gap: spacing.sm, borderRadius: radii.card, backgroundColor: colors.surfaceTint, padding: spacing.md, marginBottom: 14 },
  bannerWarning: { backgroundColor: colors.warningBg },
  bannerError: { backgroundColor: colors.dangerBg },
  bannerIcon: { width: 36, height: 36, borderRadius: radii.iconTile, backgroundColor: colors.white, alignItems: 'center', justifyContent: 'center' },
  bannerTitle: { fontFamily: fonts.bold, fontSize: 15, color: colors.ink, marginBottom: 3 },
  bannerBody: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 21, color: colors.ink },

  fieldBlock: { marginBottom: 4 },
  label: { fontFamily: fonts.semibold, fontSize: 14, color: colors.ink, marginBottom: spacing.xs },
  field: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, minHeight: 58, borderWidth: 1, borderColor: tone.border, borderRadius: radii.field, backgroundColor: colors.white, paddingLeft: 8, paddingRight: 14 },
  fieldIcon: { width: 40, height: 40, borderRadius: 13, backgroundColor: colors.surfaceTint, alignItems: 'center', justifyContent: 'center' },
  fieldText: { flex: 1, fontFamily: fonts.bold, fontSize: 16, color: colors.ink },
  errorRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.xs },
  error: { flex: 1, fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: tone.error },
  link: { color: colors.tealText, fontFamily: fonts.bold, fontSize: 16 },

  backdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(7,21,30,0.35)' },
  sheet: { backgroundColor: colors.white, borderTopLeftRadius: radii.sheet, borderTopRightRadius: radii.sheet, paddingHorizontal: spacing.lg, paddingTop: 10 },
  grabber: { alignSelf: 'center', width: 40, height: 5, borderRadius: 3, backgroundColor: colors.hairline, marginBottom: 6 },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 },
  sheetTitle: { flex: 1, fontFamily: fonts.bold, fontSize: 19, color: colors.ink, letterSpacing: -0.3 },
});
