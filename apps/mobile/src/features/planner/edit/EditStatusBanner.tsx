/**
 * SCR-024 edit states above the itinerary: recalculating (polite), error with the edit kept (US-019 AC2), 409
 * revision conflict, 410 expired, and offline. Copy follows S-1/S-2.
 */
import { useTranslation } from 'react-i18next';
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
  if (pending.status === 'rejected') {
    return <InlineBanner
      actions={<PillButton label={t('proposal.edit.discard')} onPress={onDiscard} tone="primary" />}
      body={t('proposal.edit.rejectedBody')}
      title={editErrorCopy(t, pending.errorCode)}
      tone="error"
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
