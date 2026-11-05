/**
 * SCR-027 Edit stop sheet: duration, travel mode (incoming leg), position, replace, lock (flag) and remove in one place.
 * The sheet only builds an op list (≤ 20 ops) for API-020; times, routes and Plan Health come back from the server.
 */
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';
import { CircleButton, Icon, PrimaryButton, categoryIcon } from '../../../components/ui';
import type { PreviewEditOperation } from '../../../lib/api/sourcePlanning';
import { MAX_EDITS_PER_REQUEST } from '../../../lib/api/sourcePlanning';
import type { Leg, TravelMode } from '../../../lib/api/types';
import { resolveImage } from '../../../lib/images/imagekit';
import { colors } from '../../../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { formatTime } from '../timeline/format';
import { PlannerIcon } from '../timeline/icons';
import type { NumberedDay, NumberedStop } from '../timeline/model';
import type { StopPlace } from '../timeline/useProposal';
import type { EditFocus, PendingEdit } from './draftStore';
import { InlineBanner, PillButton, SectionLabel, editTokens } from './EditUI';
import { editErrorCopy } from './errorCopy';
import { VISIT_MAX, VISIT_MIN, VISIT_STEP, regenerationEnabled } from './flags';
import { Sheet } from './Sheet';
import type { EditOutcome } from './usePreviewEditor';

export type EditTarget = { stopId: string; focus?: EditFocus; moveToStart?: boolean };

type Props = {
  target: EditTarget | null;
  days: NumberedDay[];
  places: Record<string, StopPlace>;
  allowedModes: TravelMode[];
  pending: PendingEdit | undefined;
  offline: boolean;
  onApply: (edits: PreviewEditOperation[]) => Promise<EditOutcome | null>;
  onRetry: () => void;
  onDiscardPending: () => void;
  onReplace: (stop: NumberedStop) => void;
  onClose: () => void;
};

type Position = { dayIndex: number; ordinal: number };

const stepDown = (value: number) => Math.max(VISIT_MIN, value % VISIT_STEP === 0 ? value - VISIT_STEP : Math.floor(value / VISIT_STEP) * VISIT_STEP);
const stepUp = (value: number) => Math.min(VISIT_MAX, Math.floor(value / VISIT_STEP) * VISIT_STEP + VISIT_STEP);

export function EditStopSheet(props: Props) {
  const { target, days } = props;
  const found = useMemo(() => {
    if (!target) return null;
    for (const day of days) {
      const index = day.stops.findIndex(stop => stop.id === target.stopId);
      if (index >= 0) return { day, index, stop: day.stops[index] };
    }
    return null;
  }, [days, target]);
  const { t } = useTranslation();
  return <Sheet
    accessibilityLabel={found ? found.stop.name : t('proposal.edit.more')}
    dismissible={props.pending?.status !== 'applying'}
    onClose={props.onClose}
    visible={!!target && !!found}
  >
    {found && target ? <EditStopBody key={`${found.stop.id}:${target.focus ?? ''}:${target.moveToStart ? 1 : 0}`} {...props} day={found.day} index={found.index} stop={found.stop} target={target} /> : null}
  </Sheet>;
}

function EditStopBody({ target, day, index, stop, days, places, allowedModes, pending, offline, onApply, onRetry, onDiscardPending, onReplace, onClose }: Props & {
  target: EditTarget; day: NumberedDay; index: number; stop: NumberedStop;
}) {
  const { t } = useTranslation();
  const incoming: Leg | undefined = index > 0 ? day.legs.find(leg => leg.to_stop_id === stop.id) : undefined;
  const previous = index > 0 ? day.stops[index - 1] : undefined;
  const original: Position = { dayIndex: day.day_index, ordinal: index + 1 };

  const [minutes, setMinutes] = useState(stop.visit_minutes);
  const [mode, setMode] = useState<TravelMode | null>(incoming?.travel_mode ?? null);
  const [position, setPosition] = useState<Position>(target.moveToStart ? { dayIndex: day.day_index, ordinal: 1 } : original);
  const [locked, setLocked] = useState(stop.is_locked);
  const [confirmRemove, setConfirmRemove] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const applying = pending?.status === 'applying';
  const blockedByPending = !!pending && !applying;
  useEffect(() => { if (!pending) setError(null); }, [pending]);

  const targetDay = days.find(item => item.day_index === position.dayIndex) ?? day;
  const sameDay = position.dayIndex === day.day_index;
  const maxOrdinal = sameDay ? day.stops.length : targetDay.stops.length + 1;
  const moved = position.dayIndex !== original.dayIndex || position.ordinal !== original.ordinal;
  const lockChanged = regenerationEnabled && locked !== stop.is_locked;

  const modeOptions = useMemo(() => {
    const options = [...allowedModes];
    if (incoming && !options.includes(incoming.travel_mode)) options.unshift(incoming.travel_mode);
    return options;
  }, [allowedModes, incoming]);
  const showMode = !!incoming && modeOptions.length > 1;

  const edits = useMemo<PreviewEditOperation[]>(() => {
    const list: PreviewEditOperation[] = [];
    if (lockChanged && !locked) list.push({ op: 'UNLOCK_STOP', stop_id: stop.id });
    if (minutes !== stop.visit_minutes) list.push({ op: 'SET_VISIT_MINUTES', stop_id: stop.id, visit_minutes: minutes });
    if (incoming && mode && mode !== incoming.travel_mode) {
      list.push({ from_stop_id: incoming.from_stop_id, op: 'SET_LEG_MODE', to_stop_id: stop.id, travel_mode: mode });
    }
    if (moved) list.push({ day_index: position.dayIndex, op: 'MOVE_STOP', stop_id: stop.id, to_ordinal: position.ordinal });
    if (lockChanged && locked) list.push({ op: 'LOCK_STOP', stop_id: stop.id });
    return list.slice(0, MAX_EDITS_PER_REQUEST);
  }, [incoming, lockChanged, locked, minutes, mode, moved, position, stop]);

  async function submit(ops: PreviewEditOperation[]) {
    setError(null);
    const outcome = await onApply(ops);
    if (!outcome) return;
    if (outcome.ok) { onClose(); return; }
    setError(outcome.status === 'conflict' ? t('proposal.edit.conflictTitle') : editErrorCopy(t, outcome.code));
  }

  const arrival = formatTime(stop.planned_arrival);
  const departure = formatTime(stop.planned_departure);
  const subtitle = arrival && departure
    ? t('proposal.sheet.subtitle', { day: day.day_index, number: index + 1, time: `${arrival} – ${departure}` })
    : t('proposal.sheet.subtitleNoTime', { day: day.day_index, number: index + 1 });
  const place = places[stop.place_id];
  const image = resolveImage(place?.thumbnail, { height: 72, width: 72 });
  const otherDays = days.filter(item => item.day_index !== day.day_index);
  const disabled = offline || applying || blockedByPending;

  const header = <View style={e.header}>
    <View style={e.photo}>
      {image
        ? <Image accessibilityLabel={t('proposal.sheet.photo', { name: stop.name })} contentFit="cover" placeholder={image.placeholder} source={image.source} style={StyleSheet.absoluteFill} />
        : <LinearGradient colors={[colors.deepOcean, colors.tealDark]} end={{ x: 1, y: 1 }} start={{ x: 0, y: 0 }} style={[StyleSheet.absoluteFill, e.photoFallback]}>
          <Icon color={colors.white} name={categoryIcon(place?.categoryCode)} size={28} />
        </LinearGradient>}
    </View>
    <View style={e.headerCopy}>
      <Text accessibilityRole="header" numberOfLines={2} style={e.title}>{stop.name}</Text>
      {stop.name !== stop.name_vi ? <Text numberOfLines={1} style={e.secondary}>{stop.name_vi}</Text> : null}
      <Text style={e.subtitle}>{subtitle}</Text>
    </View>
    <CircleButton accessibilityLabel={t('proposal.sheet.close')} disabled={applying} icon="back" onPress={onClose} size={44} style={e.close} tone="tint" />
  </View>;

  if (confirmRemove) {
    return <View style={e.pad}>
      {header}
      <View accessibilityRole="alert" style={e.confirm}>
        <View style={e.confirmIcon}><Icon color={palette.error} name="trash" size={24} /></View>
        <Text accessibilityRole="header" style={e.confirmTitle}>{t('proposal.sheet.removeTitle')}</Text>
        <Text style={e.confirmBody}>{t('proposal.sheet.removeBody', { name: stop.name })}</Text>
      </View>
      {error ? <InlineBanner body={t('proposal.edit.kept')} style={e.banner} title={error} tone="error" /> : null}
      <View style={e.confirmActions}>
        {/* "Keep" first: the destructive action is never the default focus (SCR-027). */}
        <PillButton label={t('proposal.sheet.keep')} onPress={() => setConfirmRemove(false)} style={e.flex} />
        <PillButton disabled={disabled} icon="close" label={applying ? t('proposal.sheet.applying') : t('proposal.sheet.removeConfirm')} onPress={() => submit([{ op: 'REMOVE_STOP', stop_id: stop.id }])} style={[e.flex, e.removeConfirm]} tone="primary" />
      </View>
    </View>;
  }

  const footer = <View>
    {offline
      ? <Text accessibilityLiveRegion="polite" style={e.reason}>{t('proposal.edit.saveOffline')}</Text>
      : blockedByPending
        ? <Text style={e.reason}>{t('proposal.edit.busy')}</Text>
        : <Text accessibilityLiveRegion="polite" style={e.note}>{applying ? t('proposal.sheet.applying') : edits.length ? t('proposal.sheet.recalcNote') : t('proposal.sheet.noChange')}</Text>}
    <PrimaryButton
      disabled={!edits.length || offline || blockedByPending}
      label={edits.length ? t('proposal.sheet.applyCount', { count: edits.length }) : t('proposal.sheet.apply')}
      loading={applying}
      onPress={() => submit(edits)}
      style={e.apply}
      variant="gradient"
    />
  </View>;

  return <View style={e.root}>
    <ScrollView contentContainerStyle={e.pad} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
      {header}

      {blockedByPending && pending ? <InlineBanner
        actions={<>
          <PillButton icon="refresh" label={pending.status === 'conflict' ? t('proposal.edit.reloadReapply') : t('proposal.edit.retry')} onPress={onRetry} tone="primary" />
          <PillButton label={t('proposal.edit.discard')} onPress={onDiscardPending} />
        </>}
        body={t('proposal.edit.kept')}
        style={e.banner}
        title={pending.status === 'conflict' ? t('proposal.edit.conflictTitle') : editErrorCopy(t, pending.errorCode)}
        tone="error"
      /> : error ? <InlineBanner body={t('proposal.edit.kept')} style={e.banner} title={error} tone="error" /> : null}

      <View style={[e.section, target.focus === 'duration' && e.focused]}>
        <SectionLabel>{t('proposal.sheet.duration')}</SectionLabel>
        <View style={e.stepper}>
          <CircleButtonIcon accessibilityLabel={t('proposal.sheet.decrease')} disabled={disabled || minutes <= VISIT_MIN} icon="minus" onPress={() => setMinutes(stepDown)} />
          <View accessible accessibilityLabel={t('proposal.sheet.durationA11y', { count: minutes })} accessibilityLiveRegion="polite" style={e.stepValue}>
            <Text style={e.stepNumber}>{minutes}</Text>
            <Text style={e.stepUnit}>{t('proposal.sheet.minutesUnit')}</Text>
          </View>
          <CircleButtonIcon accessibilityLabel={t('proposal.sheet.increase')} disabled={disabled || minutes >= VISIT_MAX} icon="plus" onPress={() => setMinutes(stepUp)} />
        </View>
        <Text style={e.hint}>{t('proposal.sheet.durationRange')}</Text>
      </View>

      {showMode && incoming && previous ? <View style={[e.section, target.focus === 'mode' && e.focused]}>
        <SectionLabel>{t('proposal.sheet.mode')}</SectionLabel>
        <Text style={e.hintTop}>{t('proposal.sheet.modeFrom', { name: previous.name })}</Text>
        <View accessibilityRole="radiogroup" style={e.segment}>
          {modeOptions.map(option => {
            const selected = mode === option;
            return <PillButtonRadio key={option} disabled={disabled} icon={option === 'WALK' ? 'walk' : 'drive'} label={t(`proposal.sheet.mode${option}`)} onPress={() => setMode(option)} selected={selected} />;
          })}
        </View>
      </View> : null}

      <View style={[e.section, target.focus === 'move' && e.focused]}>
        <SectionLabel trailing={<Text style={e.positionNow}>{t('proposal.sheet.positionNow', { day: original.dayIndex, number: original.ordinal })}</Text>}>{t('proposal.sheet.position')}</SectionLabel>
        <View style={e.wrap}>
          <PillButton accessibilityLabel={t('proposal.edit.moveUpA11y', { name: stop.name })} disabled={disabled || position.ordinal <= 1} icon="arrowUp" label={t('proposal.edit.moveUp')} onPress={() => setPosition(current => ({ ...current, ordinal: current.ordinal - 1 }))} />
          <PillButton accessibilityLabel={t('proposal.edit.moveDownA11y', { name: stop.name })} disabled={disabled || position.ordinal >= maxOrdinal} icon="arrowDown" label={t('proposal.edit.moveDown')} onPress={() => setPosition(current => ({ ...current, ordinal: current.ordinal + 1 }))} />
          <PillButton disabled={disabled || position.ordinal === 1} icon="toStart" label={t('proposal.sheet.moveStart')} onPress={() => setPosition(current => ({ ...current, ordinal: 1 }))} />
          {otherDays.map(other => <PillButton
            key={other.day_index}
            disabled={disabled || locked}
            icon="calendarMove"
            label={t('proposal.sheet.moveDay', { day: other.day_index })}
            onPress={() => setPosition({ dayIndex: other.day_index, ordinal: other.stops.length + 1 })}
            selected={position.dayIndex === other.day_index}
          />)}
          {position.dayIndex !== day.day_index ? <PillButton label={t('proposal.sheet.positionNow', { day: day.day_index, number: original.ordinal })} onPress={() => setPosition(original)} /> : null}
        </View>
        {moved ? <Text accessibilityLiveRegion="polite" style={e.positionNew}>{t('proposal.sheet.positionNew', { day: position.dayIndex, number: position.ordinal })}</Text> : null}
        {locked && otherDays.length ? <Text style={e.hint}>{t('proposal.sheet.lockedMove')}</Text> : null}
      </View>

      <View style={[e.section, target.focus === 'replace' && e.focused]}>
        <SectionLabel>{t('proposal.sheet.actions')}</SectionLabel>
        <View style={e.wrap}>
          <PillButton disabled={disabled} icon="swap" label={t('proposal.sheet.replace')} onPress={() => onReplace(stop)} />
          {regenerationEnabled ? <PillButton
            accessibilityHint={t('proposal.sheet.lockHint')}
            disabled={disabled}
            icon={locked ? 'unlock' : 'lock'}
            label={locked ? t('proposal.sheet.unlock') : t('proposal.sheet.lock')}
            onPress={() => setLocked(value => !value)}
            selected={locked !== stop.is_locked}
          /> : null}
          <PillButton disabled={disabled || stop.is_locked} icon="close" label={t('proposal.sheet.remove')} onPress={() => setConfirmRemove(true)} tone="danger" />
        </View>
        {regenerationEnabled ? <Text style={e.hint}>{t('proposal.sheet.lockHint')}</Text> : null}
        {stop.is_locked ? <Text style={e.hint}>{t('proposal.sheet.lockedRemove')}</Text> : null}
      </View>
    </ScrollView>
    <View style={e.footer}>{footer}</View>
  </View>;
}

/** Stepper button: 48 pt circle with a stroked glyph. */
function CircleButtonIcon({ icon, onPress, disabled, accessibilityLabel }: { icon: 'plus' | 'minus'; onPress: () => void; disabled?: boolean; accessibilityLabel: string }) {
  return <PillButtonBase accessibilityLabel={accessibilityLabel} disabled={disabled} onPress={onPress} style={e.stepButton}>
    <PlannerIcon color={colors.deepOcean} name={icon} size={22} />
  </PillButtonBase>;
}

function PillButtonRadio({ label, icon, onPress, selected, disabled }: { label: string; icon: 'walk' | 'drive'; onPress: () => void; selected: boolean; disabled?: boolean }) {
  return <PillButtonBase accessibilityLabel={label} accessibilityRole="radio" disabled={disabled} onPress={onPress} selected={selected} style={[e.segmentItem, selected && e.segmentSelected]}>
    <PlannerIcon color={selected ? colors.white : colors.deepOcean} name={icon} size={18} />
    <Text style={[e.segmentText, selected && { color: colors.white }]}>{label}</Text>
  </PillButtonBase>;
}

function PillButtonBase({ children, onPress, disabled, selected, accessibilityLabel, accessibilityRole = 'button', style }: {
  children: ReactNode; onPress: () => void; disabled?: boolean; selected?: boolean; accessibilityLabel: string; accessibilityRole?: 'button' | 'radio'; style?: StyleProp<ViewStyle>;
}) {
  return <Pressable
    accessibilityLabel={accessibilityLabel}
    accessibilityRole={accessibilityRole}
    accessibilityState={{ checked: accessibilityRole === 'radio' ? selected : undefined, disabled: !!disabled }}
    disabled={disabled}
    onPress={onPress}
    style={({ pressed }) => [style, disabled && { opacity: 0.4 }, pressed && { opacity: 0.75 }]}
  >
    {children}
  </Pressable>;
}

const e = StyleSheet.create({
  root: { flexShrink: 1 },
  pad: { paddingHorizontal: spacing.lg, paddingBottom: spacing.md },
  flex: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingTop: spacing.xs, paddingBottom: spacing.md },
  photo: { width: 72, height: 72, borderRadius: 18, overflow: 'hidden', backgroundColor: colors.skyWash },
  photoFallback: { alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1, minWidth: 0 },
  title: { ...typography.headline },
  secondary: { fontFamily: fonts.medium, fontSize: 14, color: colors.textMuted, marginTop: 1 },
  subtitle: { fontFamily: fonts.bold, fontSize: 13, lineHeight: 18, color: colors.tealText, marginTop: 4 },
  close: { alignSelf: 'flex-start', transform: [{ rotate: '-90deg' }] },
  banner: { marginBottom: spacing.sm },
  section: { borderRadius: radii.card, borderWidth: 1, borderColor: editTokens.cardBorder, padding: spacing.md, marginBottom: spacing.sm },
  focused: { borderColor: colors.audioTeal, backgroundColor: '#F1F9FB' },
  stepper: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  stepButton: { width: 52, height: 52, borderRadius: 26, borderWidth: 1.5, borderColor: editTokens.border, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.white },
  stepValue: { alignItems: 'center', minWidth: 120 },
  stepNumber: { fontFamily: fonts.bold, fontSize: 34, lineHeight: 40, letterSpacing: -0.8, color: colors.ink },
  stepUnit: { fontFamily: fonts.medium, fontSize: 14, color: colors.textMuted },
  hint: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted, marginTop: spacing.xs },
  hintTop: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: colors.textMuted, marginBottom: spacing.xs },
  segment: { flexDirection: 'row', padding: 4, gap: 4, borderRadius: radii.action, backgroundColor: colors.skyWash },
  segmentItem: { flex: 1, flexDirection: 'row', gap: 6, alignItems: 'center', justifyContent: 'center', minHeight: MIN_TOUCH, borderRadius: 18 },
  segmentSelected: { backgroundColor: colors.deepOcean },
  segmentText: { fontFamily: fonts.bold, fontSize: 15, color: colors.deepOcean },
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  positionNow: { fontFamily: fonts.medium, fontSize: 12, color: colors.textMuted },
  positionNew: { fontFamily: fonts.bold, fontSize: 13, color: colors.tealText, marginTop: spacing.xs },
  footer: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: editTokens.border },
  note: { fontFamily: fonts.medium, fontSize: 12, lineHeight: 17, color: colors.textMuted, textAlign: 'center', marginBottom: spacing.xs },
  reason: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18, color: palette.error, textAlign: 'center', marginBottom: spacing.xs },
  apply: { height: 56 },
  confirm: { alignItems: 'center', paddingVertical: spacing.md },
  confirmIcon: { width: 56, height: 56, borderRadius: 28, backgroundColor: editTokens.errorBg, alignItems: 'center', justifyContent: 'center' },
  confirmTitle: { ...typography.headline, marginTop: spacing.sm, textAlign: 'center' },
  confirmBody: { ...typography.body, fontSize: 15, lineHeight: 22, color: colors.textMuted, textAlign: 'center', marginTop: spacing.xxs },
  confirmActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
  removeConfirm: { backgroundColor: palette.error, borderColor: palette.error },
});
