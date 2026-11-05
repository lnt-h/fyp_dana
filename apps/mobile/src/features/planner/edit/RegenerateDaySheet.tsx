/**
 * SCR-030 Regenerate day (FEATURE_REGENERATION): confirm (other days and locked stops kept) → stage progress (API-021
 * stream) → new DAY_REGENERATED revision. A failure leaves the head revision, locks and edits unchanged (US-042 AC4).
 */
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { PrimaryButton } from '../../../components/ui';
import { currentLocale } from '../../../i18n';
import { getPreviewHead, newIdempotencyKey, streamRegenerateDay } from '../../../lib/api/sourcePlanning';
import type { PlanPreview, PlanningStage, Uuid } from '../../../lib/api/types';
import { colors } from '../../../theme/colors';
import { radii, spacing } from '../../../theme/spacing';
import { fonts, typography } from '../../../theme/typography';
import { palette } from '../../auth/components/AuthUI';
import { PlannerIcon } from '../timeline/icons';
import type { NumberedDay } from '../timeline/model';
import { InlineBanner, LinkButton, PillButton, editTokens } from './EditUI';
import { editErrorCopy } from './errorCopy';
import { Sheet } from './Sheet';

const STAGES: PlanningStage[] = ['VALIDATING_REQUEST', 'SELECTING_PLACES', 'ROUTING', 'SCHEDULING', 'CHECKING_HEALTH'];
const NOTE_MAX = 500;

type Props = {
  dayIndex: number | null;
  days: NumberedDay[];
  previewId: Uuid;
  revision: number | null;
  offline: boolean;
  /** Shows the new revision; the sheet closes after it resolves. */
  onDone: (preview: PlanPreview) => Promise<void>;
  onClose: () => void;
  /** True while the regeneration runs (the proposal shows "Recalculating" and disables Save and edits). */
  onRunningChange?: (running: boolean) => void;
};

type Phase = { kind: 'confirm' } | { kind: 'progress'; stage: PlanningStage | null } | { kind: 'error'; code: string };

export function RegenerateDaySheet({ dayIndex, days, previewId, revision, offline, onDone, onClose, onRunningChange }: Props) {
  const { t } = useTranslation();
  const [phase, setPhase] = useState<Phase>({ kind: 'confirm' });
  const [note, setNote] = useState('');
  const abort = useRef<AbortController | null>(null);
  const key = useRef<string | null>(null);

  useEffect(() => {
    if (dayIndex == null) { setPhase({ kind: 'confirm' }); setNote(''); key.current = null; }
  }, [dayIndex]);
  useEffect(() => () => abort.current?.abort(), []);

  const day = days.find(item => item.day_index === dayIndex);
  const others = days.filter(item => item.day_index !== dayIndex).map(item => item.day_index);
  const locked = day?.stops.filter(stop => stop.is_locked) ?? [];
  const running = phase.kind === 'progress';
  useEffect(() => { onRunningChange?.(running); }, [onRunningChange, running]);

  async function start() {
    if (!day || revision == null) return;
    const controller = new AbortController();
    abort.current = controller;
    key.current = key.current ?? newIdempotencyKey();
    setPhase({ kind: 'progress', stage: null });
    const result: { failed: string | null; ready: boolean } = { failed: null, ready: false };
    try {
      await streamRegenerateDay(previewId, {
        day_index: day.day_index,
        expected_revision: revision,
        instruction: note.trim() || null,
        locale: currentLocale(),
        locked_stop_ids: locked.map(stop => stop.id),
      }, key.current, event => {
        if (event.type === 'progress') setPhase({ kind: 'progress', stage: event.stage });
        else if (event.type === 'error') result.failed = event.error.code;
        else if (event.type === 'preview_ready') result.ready = true;
      }, controller.signal);
      if (controller.signal.aborted) return;
      if (result.failed || !result.ready) { setPhase({ kind: 'error', code: result.failed ?? 'internal_error' }); return; }
      const head = await getPreviewHead(previewId);
      await onDone(head);
      key.current = null;
      onClose();
    } catch {
      if (!controller.signal.aborted) setPhase({ kind: 'error', code: 'network' });
    }
  }

  const othersText = others.length > 1 ? `${others.slice(0, -1).join(', ')} ${t('proposal.regen.and')} ${others[others.length - 1]}` : String(others[0] ?? '');
  const stageIndex = phase.kind === 'progress' && phase.stage ? STAGES.indexOf(phase.stage) : -1;

  return <Sheet
    accessibilityLabel={dayIndex ? t('proposal.regen.title', { day: dayIndex }) : ''}
    dismissible={!running}
    onClose={onClose}
    role="alertdialog"
    visible={dayIndex != null && !!day}
  >
    {day ? <ScrollView contentContainerStyle={g.pad} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
      <View style={g.icon}><PlannerIcon color={colors.tealText} name="refresh" size={26} /></View>

      {phase.kind === 'progress' ? <>
        <Text accessibilityRole="header" style={g.title}>{t('proposal.regen.progressTitle', { day: day.day_index })}</Text>
        <Text style={g.body}>{t('proposal.regen.progressBody')}</Text>
        <View accessibilityLiveRegion="polite" style={g.stages}>
          {STAGES.map((stage, index) => {
            const done = index < stageIndex;
            const active = index === stageIndex || (stageIndex === -1 && index === 0);
            return <View key={stage} accessible accessibilityLabel={`${t(`proposal.regen.stage.${stage}`)}, ${done ? t('proposal.regen.stageDone') : active ? t('proposal.regen.stageActive') : ''}`} style={g.stage}>
              <View style={[g.dot, done && g.dotDone, active && g.dotActive]}>
                {done ? <PlannerIcon color={colors.white} name="check" size={14} /> : active ? <ActivityIndicator color={colors.tealText} size="small" /> : null}
              </View>
              <Text style={[g.stageText, (done || active) && g.stageTextOn]}>{t(`proposal.regen.stage.${stage}`)}</Text>
            </View>;
          })}
        </View>
      </> : <>
        <Text accessibilityRole="header" style={g.title}>{t('proposal.regen.title', { day: day.day_index })}</Text>
        {phase.kind === 'error' ? <InlineBanner body={t('proposal.regen.failed')} style={g.banner} title={editErrorCopy(t, phase.code)} tone="error" /> : null}
        {others.length ? <Bullet text={t('proposal.regen.others', { days: othersText })} /> : null}
        <Bullet text={locked.length ? t('proposal.regen.locked') : t('proposal.regen.noLocked')} />
        {locked.length ? <View style={g.locked}>
          {locked.map(stop => <View key={stop.id} style={g.lockedRow}>
            <PlannerIcon color={colors.tealText} name="lock" size={16} />
            <Text style={g.lockedName}>{`#${stop.number} ${stop.name}`}</Text>
          </View>)}
        </View> : null}
        <Bullet text={t('proposal.regen.draftNote')} />
        <Text style={g.label}>{t('proposal.regen.note')}</Text>
        <TextInput
          accessibilityLabel={t('proposal.regen.note')}
          maxLength={NOTE_MAX}
          onChangeText={setNote}
          placeholder={t('proposal.regen.notePlaceholder')}
          placeholderTextColor={colors.textMuted}
          returnKeyType="done"
          style={g.input}
          value={note}
        />
        {offline ? <Text style={g.offline}>{t('proposal.edit.saveOffline')}</Text> : null}
        <View style={g.actions}>
          {/* Cancel first: the primary action is destructive to the draft day and is not the default focus. */}
          <LinkButton label={phase.kind === 'error' ? t('proposal.regen.close') : t('proposal.regen.cancel')} onPress={onClose} tone="muted" />
          {phase.kind === 'error'
            ? <PillButton disabled={offline} icon="refresh" label={t('proposal.regen.retry')} onPress={start} style={g.primary} tone="primary" />
            : <PrimaryButton disabled={offline || revision == null} icon="sparkle" label={t('proposal.regen.confirm', { day: day.day_index })} onPress={start} style={g.primary} variant="gradient" />}
        </View>
      </>}
    </ScrollView> : null}
  </Sheet>;
}

function Bullet({ text }: { text: string }) {
  return <View style={g.bullet}>
    <View style={g.bulletDot} />
    <Text style={g.bulletText}>{text}</Text>
  </View>;
}

const g = StyleSheet.create({
  pad: { paddingHorizontal: spacing.lg, paddingBottom: spacing.md, paddingTop: spacing.xs },
  icon: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.skyWash, alignItems: 'center', justifyContent: 'center', alignSelf: 'center' },
  title: { ...typography.headline, textAlign: 'center', marginTop: spacing.sm, marginBottom: spacing.sm },
  body: { ...typography.caption, fontSize: 14, textAlign: 'center' },
  banner: { marginBottom: spacing.sm },
  bullet: { flexDirection: 'row', gap: 10, marginTop: spacing.xs },
  bulletDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.audioTeal, marginTop: 8 },
  bulletText: { flex: 1, fontFamily: fonts.medium, fontSize: 15, lineHeight: 22, color: colors.ink },
  locked: { marginTop: spacing.xs, marginLeft: 16, borderRadius: 16, backgroundColor: editTokens.canvas, padding: spacing.sm, gap: 6 },
  lockedRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  lockedName: { flex: 1, fontFamily: fonts.bold, fontSize: 14, lineHeight: 20, color: colors.deepOcean },
  label: { fontFamily: fonts.bold, fontSize: 13, color: colors.deepOcean, marginTop: spacing.md, marginBottom: 6 },
  input: { minHeight: 52, borderRadius: radii.field, borderWidth: 1.5, borderColor: editTokens.border, paddingHorizontal: spacing.md, fontFamily: fonts.medium, fontSize: 16, color: colors.deepOcean },
  offline: { fontFamily: fonts.medium, fontSize: 13, color: palette.error, marginTop: spacing.xs },
  actions: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.lg },
  primary: { flex: 1, height: 56 },
  stages: { marginTop: spacing.lg, gap: spacing.sm },
  stage: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, minHeight: 32 },
  dot: { width: 28, height: 28, borderRadius: 14, borderWidth: 1.5, borderColor: editTokens.border, alignItems: 'center', justifyContent: 'center' },
  dotDone: { backgroundColor: colors.tealText, borderColor: colors.tealText },
  dotActive: { borderColor: colors.audioTeal },
  stageText: { fontFamily: fonts.medium, fontSize: 15, color: colors.textMuted },
  stageTextOn: { fontFamily: fonts.bold, color: colors.ink },
});
