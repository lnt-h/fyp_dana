/**
 * SCR-024 edit states above the itinerary: recalculating (polite), error with the edit kept (US-019 AC2), 409
 * revision conflict, 410 expired, and offline. Copy follows S-1/S-2.
 */
import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { fixtureFaults, fixtureNextFault, setFixtureNextFault, type FixtureFault } from '../../../lib/api/sourcePlanning';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { fonts } from '../../../theme/typography';
import type { PendingEdit } from './draftStore';
import { InlineBanner, PillButton } from './EditUI';
import { editErrorCopy } from './errorCopy';

type Props = {
  pending: PendingEdit | undefined;
  regenerating: boolean;
  offline: boolean;
  onRetry: () => void;
  onDiscard: () => void;
  onCreateAgain: () => void;
};

export function EditStatusBanner({ pending, regenerating, offline, onRetry, onDiscard, onCreateAgain }: Props) {
  const { t } = useTranslation();
  if (offline) return <InlineBanner title={t('proposal.edit.offline')} tone="warning" />;
  if (regenerating || pending?.status === 'applying') {
    return <InlineBanner
      body={pending ? t('proposal.edit.saveWhileRecalculating') : undefined}
      title={t('proposal.edit.recalculating')}
      tone="progress"
    />;
  }
  if (!pending) return null;
  const count = t('proposal.edit.pending', { count: pending.edits.length });
  if (pending.status === 'expired') {
    return <InlineBanner
      actions={<>
        <PillButton icon="refresh" label={t('proposal.edit.createAgain')} onPress={onCreateAgain} tone="primary" />
        <PillButton label={t('proposal.edit.discard')} onPress={onDiscard} />
      </>}
      body={t('proposal.edit.expiredBody')}
      title={t('proposal.edit.expiredTitle')}
      tone="error"
    />;
  }
  if (pending.status === 'conflict') {
    return <InlineBanner
      actions={<>
        <PillButton icon="refresh" label={t('proposal.edit.reloadReapply')} onPress={onRetry} tone="primary" />
        <PillButton label={t('proposal.edit.discard')} onPress={onDiscard} />
      </>}
      body={`${t('proposal.edit.conflictBody')} ${count}.`}
      title={t('proposal.edit.conflictTitle')}
      tone="warning"
    />;
  }
  return <InlineBanner
    actions={<>
      <PillButton icon="refresh" label={t('proposal.edit.retry')} onPress={onRetry} tone="primary" />
      <PillButton label={t('proposal.edit.discard')} onPress={onDiscard} />
    </>}
    body={`${t('proposal.edit.kept')} ${count}.`}
    title={editErrorCopy(t, pending.errorCode)}
    tone="error"
  />;
}

/** Dev-only (fixtures in a dev build): make the next edit/regeneration fail once, to exercise the states above. */
export function FixtureFaultPicker() {
  const { t } = useTranslation();
  // Read on every render: the fault is consumed by the next call, and the proposal re-renders when that call settles.
  const [, bump] = useState(0);
  const fault = fixtureNextFault();
  const choose = (next: FixtureFault | null) => { setFixtureNextFault(next); bump(value => value + 1); };
  return <View style={d.root}>
    <Text style={d.label}>{t('proposal.dev.label')}</Text>
    <ScrollView contentContainerStyle={d.row} horizontal showsHorizontalScrollIndicator={false}>
      <PillButton label={t('proposal.dev.none')} onPress={() => choose(null)} selected={fault === null} />
      {fixtureFaults.map(item => <PillButton key={item} label={t(`proposal.dev.${item}`)} onPress={() => choose(item)} selected={fault === item} />)}
    </ScrollView>
  </View>;
}

const d = StyleSheet.create({
  root: { marginTop: spacing.sm, borderRadius: 16, borderWidth: 1, borderStyle: 'dashed', borderColor: colors.mutedDot, padding: spacing.xs },
  label: { fontFamily: fonts.bold, fontSize: 11, letterSpacing: 1.2, textTransform: 'uppercase', color: colors.textMuted, marginBottom: 4, marginLeft: 4 },
  row: { gap: 6 },
});
