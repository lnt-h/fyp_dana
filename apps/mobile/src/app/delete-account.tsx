import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { PrimaryButton } from '../components/ui';
import { AccountIcon, AccountShell, DangerButton, a, errorColor, useEndSession } from '../features/account/AccountUI';
import { loadErrorKind } from '../lib/api/errors';
import { newIdempotencyKey } from '../lib/api/source';
import { getAccountDeletionStatus, requestAccountDeletion, type AccountDeletionStatus } from '../lib/api/sourceAccount';
import { demoNoAuth } from '../lib/demoAuth';
import { colors } from '../theme/colors';
import { MIN_TOUCH, radii, spacing } from '../theme/spacing';
import { fonts, typography } from '../theme/typography';

const items = ['itemTrips', 'itemPreferences', 'itemQuestions', 'itemAccount'] as const;
/** Status poll while a job is open (API-007). The purge runs in the jobs runner, so this is a light poll. */
const POLL_MS = 5000;
/** Seconds the done state stays before the app signs out on its own. */
const DONE_SIGN_OUT_MS = 2500;

type Phase =
  | { kind: 'checking' }
  | { kind: 'confirm' }
  | { kind: 'running'; status: AccountDeletionStatus }
  | { kind: 'done' };

/**
 * SCR-038 Account deletion. Confirm step → API-006 `POST /v1/me/deletion` `{confirm: true}` (Idempotency-Key reused on
 * retry) → status from API-007 until COMPLETED → sign out. An open job found on entry resumes the status view. After
 * the job is accepted every other `/v1` route answers 409 `deletion_in_progress`, so the traveller can only sign out.
 * Demo mode (shared demo user): deletion is not offered; the screen only explains that and returns Home.
 */
export default function DeleteAccountScreen() {
  const { t } = useTranslation();
  const [phase, setPhase] = useState<Phase>(demoNoAuth ? { kind: 'confirm' } : { kind: 'checking' });
  const [typed, setTyped] = useState('');
  const [notice, setNotice] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const keyRef = useRef<string | null>(null);
  const sawRunning = useRef(false);
  const { end, busy: signingOut } = useEndSession();
  const word = t('account.deleteAccount.confirmWord');
  const accepted = [word, t('account.deleteAccount.confirmWordAlt')].map(value => value.normalize('NFC'));
  const confirmed = accepted.includes(typed.trim().toUpperCase().normalize('NFC'));

  const apply = useCallback((status: AccountDeletionStatus | null | 'gone') => {
    if (status === 'gone') { setPhase(sawRunning.current ? { kind: 'done' } : { kind: 'confirm' }); return; }
    if (!status) { setPhase({ kind: 'confirm' }); return; }
    if (status.status === 'COMPLETED') { setPhase({ kind: 'done' }); return; }
    sawRunning.current = true;
    setPhase({ kind: 'running', status });
  }, []);

  // Resume an open job (e.g. the app was closed after confirming).
  useEffect(() => {
    if (demoNoAuth) return;
    let alive = true;
    getAccountDeletionStatus()
      .then(status => { if (alive) apply(status); })
      .catch(() => { if (alive) setPhase({ kind: 'confirm' }); });
    return () => { alive = false; };
  }, [apply]);

  // Poll while running.
  const running = phase.kind === 'running';
  useEffect(() => {
    if (!running) return;
    const timer = setInterval(() => {
      getAccountDeletionStatus().then(apply).catch(() => undefined);
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [running, apply]);

  // Done: sign out shortly after showing the confirmation.
  const done = phase.kind === 'done';
  useEffect(() => {
    if (!done) return;
    const timer = setTimeout(() => void end(), DONE_SIGN_OUT_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [done]);

  async function submit() {
    if (!confirmed || submitting || demoNoAuth) return;
    setSubmitting(true); setNotice('');
    keyRef.current ??= newIdempotencyKey();
    try {
      apply(await requestAccountDeletion(keyRef.current));
    } catch (error) {
      const kind = loadErrorKind(error);
      setNotice(kind === 'offline' ? t('account.deleteAccount.failedOffline') : kind === 'auth' ? t('common.loadError.auth') : t('account.deleteAccount.failed'));
    } finally {
      setSubmitting(false);
    }
  }
  function keep() { router.canGoBack() ? router.back() : router.replace('/settings'); }

  if (demoNoAuth) {
    return <AccountShell title={t('account.deleteAccount.title')} fallback="/settings">
      <View style={[a.card, a.padded, styles.center]}>
        <View style={[styles.badge, styles.badgeInfo]}><AccountIcon name="info" color={colors.info} size={26} /></View>
        <Text accessibilityRole="header" style={styles.heading}>{t('account.deleteAccount.demoTitle')}</Text>
        <Text style={[styles.lead, styles.centerText]}>{t('account.deleteAccount.demoBody')}</Text>
      </View>
      <PrimaryButton label={t('account.deleteAccount.backHome')} onPress={() => { router.dismissAll(); router.replace('/home'); }} />
    </AccountShell>;
  }

  if (phase.kind === 'checking') {
    return <AccountShell title={t('account.deleteAccount.title')} fallback="/settings">
      <ActivityIndicator accessibilityLabel={t('common.pleaseWait')} color={colors.primary} style={styles.checking} />
    </AccountShell>;
  }

  if (phase.kind === 'running' || phase.kind === 'done') {
    const isDone = phase.kind === 'done';
    const status = phase.kind === 'running' ? phase.status.status : 'COMPLETED';
    const steps = [
      { done: true, key: 'stepRequested' },
      { done: status === 'IN_PROGRESS' || isDone, key: 'stepDeleting' },
      { done: isDone, key: 'stepDone' },
    ] as const;
    return <AccountShell title={t('account.deleteAccount.title')} fallback="/settings">
      <View accessibilityLiveRegion="polite" style={[a.card, a.padded, styles.center]}>
        <View style={[styles.badge, isDone ? styles.badgeDone : styles.badgeInfo]}>
          {isDone ? <AccountIcon name="check" color={colors.success} size={26} /> : <ActivityIndicator color={colors.info} />}
        </View>
        <Text accessibilityRole="header" style={[styles.heading, styles.centerText]}>{t(isDone ? 'account.deleteAccount.doneTitle' : 'account.deleteAccount.runningTitle')}</Text>
        <Text style={[styles.lead, styles.centerText]}>{t(isDone ? 'account.deleteAccount.doneBody' : status === 'FAILED' ? 'account.deleteAccount.retryingBody' : 'account.deleteAccount.runningBody')}</Text>
      </View>
      <View accessibilityRole="list" style={[a.card, styles.steps]}>
        {steps.map(step => <View accessibilityLabel={`${t(`account.deleteAccount.${step.key}`)}${step.done ? `, ${t('account.deleteAccount.stepComplete')}` : ''}`} accessible key={step.key} style={styles.step}>
          <View style={[styles.stepDot, step.done && styles.stepDotDone]}>
            {step.done ? <AccountIcon name="check" color={colors.white} size={14} /> : null}
          </View>
          <Text style={[styles.stepText, !step.done && styles.stepPending]}>{t(`account.deleteAccount.${step.key}`)}</Text>
        </View>)}
      </View>
      <PrimaryButton label={t(isDone ? 'account.deleteAccount.signOutDone' : 'account.deleteAccount.signOutNow')} loading={signingOut} onPress={() => void end()} />
    </AccountShell>;
  }

  return <AccountShell title={t('account.deleteAccount.title')} fallback="/settings">
    <View style={[a.card, a.padded]}>
      <View style={styles.badge}><AccountIcon name="warning" color={errorColor} size={26} /></View>
      <Text accessibilityRole="header" style={styles.heading}>{t('account.deleteAccount.heading')}</Text>
      <Text style={styles.lead}>{t('account.deleteAccount.lead')}</Text>
      <View accessibilityRole="list">
        {items.map(item => <View key={item} accessibilityRole="text" style={styles.item}>
          <View style={styles.bullet} /><Text style={styles.itemText}>{t(`account.deleteAccount.${item}`)}</Text>
        </View>)}
      </View>
      <Text style={styles.warning}>{t('account.deleteAccount.warning')}</Text>
    </View>

    <Text nativeID="delete-confirm-label" style={styles.label}>{t('account.deleteAccount.confirmLabel', { word })}</Text>
    <TextInput
      accessibilityLabel={t('account.deleteAccount.confirmLabel', { word })}
      accessibilityLabelledBy="delete-confirm-label"
      autoCapitalize="characters"
      autoComplete="off"
      autoCorrect={false}
      editable={!submitting}
      onChangeText={value => { setTyped(value); setNotice(''); }}
      placeholder={word}
      placeholderTextColor={colors.textMuted}
      style={[styles.input, confirmed && styles.inputReady]}
      value={typed}
    />
    <Text style={styles.helper}>{t('account.deleteAccount.confirmHelper')}</Text>

    {notice ? <View accessibilityLiveRegion="polite" accessibilityRole="alert" style={styles.notice}>
      <AccountIcon name="warning" color={colors.danger} size={20} />
      <Text style={styles.noticeText}>{notice}</Text>
    </View> : null}

    {submitting
      ? <View style={styles.submitting}><ActivityIndicator accessibilityLabel={t('common.pleaseWait')} color={colors.danger} /></View>
      : <DangerButton label={t('account.deleteAccount.submit')} disabled={!confirmed} onPress={() => void submit()} />}
    <Pressable accessibilityRole="button" onPress={keep} style={({ pressed }) => [styles.keep, pressed && a.pressed]}>
      <Text style={styles.keepText}>{t('account.deleteAccount.keep')}</Text>
    </Pressable>
  </AccountShell>;
}

const styles = StyleSheet.create({
  badge: { width: 48, height: 48, borderRadius: 24, backgroundColor: colors.dangerBg, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.sm },
  badgeDone: { backgroundColor: colors.successBg },
  badgeInfo: { backgroundColor: colors.infoBg },
  center: { alignItems: 'center' },
  centerText: { textAlign: 'center' },
  checking: { marginTop: spacing.xxl },
  heading: { ...typography.headline, color: colors.ink },
  lead: { ...typography.body, color: colors.ink, marginTop: spacing.sm, marginBottom: spacing.xs },
  item: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm, paddingVertical: spacing.xxs },
  bullet: { width: 6, height: 6, borderRadius: 3, backgroundColor: errorColor, marginTop: 9 },
  itemText: { ...typography.body, fontSize: 15, lineHeight: 22, color: colors.ink, flex: 1 },
  warning: { ...typography.caption, fontSize: 14, lineHeight: 21, marginTop: spacing.md },
  label: { ...typography.label, marginBottom: spacing.xs, marginLeft: spacing.xxs },
  input: { minHeight: 54, borderRadius: radii.field, borderWidth: 1.5, borderColor: colors.hairline, backgroundColor: colors.white, paddingHorizontal: spacing.md, fontFamily: fonts.bold, fontSize: 17, letterSpacing: 1, color: colors.ink },
  inputReady: { borderColor: errorColor },
  helper: { ...typography.caption, marginTop: spacing.xs, marginBottom: spacing.lg, marginLeft: spacing.xxs },
  notice: { flexDirection: 'row', gap: spacing.sm, alignItems: 'flex-start', backgroundColor: colors.dangerBg, borderRadius: radii.inset, padding: spacing.md, marginBottom: spacing.lg },
  noticeText: { ...typography.caption, fontSize: 14, lineHeight: 21, color: colors.ink, flex: 1 },
  keep: { minHeight: MIN_TOUCH + 4, alignItems: 'center', justifyContent: 'center', marginTop: spacing.sm },
  keepText: { fontFamily: fonts.bold, fontSize: 16, color: colors.primary },
  steps: { gap: spacing.sm, padding: spacing.lg },
  step: { alignItems: 'center', flexDirection: 'row', gap: spacing.sm, minHeight: 28 },
  stepDot: { alignItems: 'center', borderColor: colors.hairline, borderRadius: 12, borderWidth: 2, height: 24, justifyContent: 'center', width: 24 },
  stepDotDone: { backgroundColor: colors.success, borderColor: colors.success },
  stepText: { ...typography.label, flex: 1 },
  stepPending: { color: colors.textMuted },
  submitting: { alignItems: 'center', justifyContent: 'center', minHeight: 56 },
});
