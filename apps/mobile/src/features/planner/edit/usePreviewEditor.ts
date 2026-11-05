/**
 * Sends proposal edits (API-020) and keeps them safe until the server answers (ADR-009, US-019 AC2). The client only
 * builds the op list; the server re-routes, re-schedules and recomputes Plan Health, and its revision is rendered.
 */
import { useCallback, useEffect, useRef } from 'react';
import { ApiError } from '../../../lib/api/source';
import { editPreview, getPreviewHead, newIdempotencyKey, type PreviewEditOperation } from '../../../lib/api/sourcePlanning';
import type { PlanPreview, Uuid } from '../../../lib/api/types';
import { clearPending, getPending, setPending, updatePending, usePendingEdit, type PendingEdit, type PendingStatus } from './draftStore';

export type EditOutcome = { ok: true; preview: PlanPreview } | { ok: false; status: PendingStatus; code: string };

function classify(error: unknown): { status: PendingStatus; code: string } {
  if (error instanceof ApiError) {
    const { code } = error.error;
    if (code === 'revision_conflict') return { code, status: 'conflict' };
    if (code === 'preview_expired' || code === 'preview_closed') return { code, status: 'expired' };
    return { code, status: 'failed' };
  }
  return { code: 'network', status: 'failed' };
}

type Options = {
  previewId: Uuid;
  revision: number | null;
  /** Renders a new revision (await so the screen shows it before the pending edit is cleared). */
  onPreview: (preview: PlanPreview) => Promise<void>;
};

export function usePreviewEditor({ previewId, revision, onPreview }: Options) {
  const pending = usePendingEdit(previewId);
  const onPreviewRef = useRef(onPreview);
  useEffect(() => { onPreviewRef.current = onPreview; }, [onPreview]);

  const send = useCallback(async (edit: PendingEdit): Promise<EditOutcome> => {
    setPending({ ...edit, errorCode: undefined, status: 'applying' });
    try {
      const preview = await editPreview(edit.previewId, { edits: edit.edits, expected_revision: edit.baseRevision }, edit.idempotencyKey);
      await onPreviewRef.current(preview);
      clearPending(edit.previewId, edit.idempotencyKey);
      return { ok: true, preview };
    } catch (error) {
      const { code, status } = classify(error);
      updatePending(edit.previewId, { errorCode: code, status });
      return { code, ok: false, status };
    }
  }, []);

  /** Applies a new op list built against the shown revision. Refused while another edit is unresolved. */
  const apply = useCallback(async (edits: PreviewEditOperation[]): Promise<EditOutcome | null> => {
    if (revision == null || !edits.length || getPending(previewId)) return null;
    return send({ baseRevision: revision, edits, idempotencyKey: newIdempotencyKey(), previewId, status: 'applying' });
  }, [previewId, revision, send]);

  /** 409: load the head revision, show it, then offer the same ops again against it (new key: new request). */
  const reloadAndReapply = useCallback(async (): Promise<EditOutcome | null> => {
    const current = getPending(previewId);
    if (!current) return null;
    updatePending(previewId, { status: 'applying' });
    try {
      const head = await getPreviewHead(previewId);
      await onPreviewRef.current(head);
      return send({ ...current, baseRevision: head.preview_revision, idempotencyKey: newIdempotencyKey() });
    } catch (error) {
      const { code, status } = classify(error);
      updatePending(previewId, { errorCode: code, status: status === 'conflict' ? 'conflict' : status });
      return { code, ok: false, status };
    }
  }, [previewId, send]);

  /** Same request again with the same `Idempotency-Key` (safe if the first one did land). */
  const retry = useCallback(async () => {
    const current = getPending(previewId);
    if (!current || current.status === 'applying') return null;
    if (current.status === 'conflict') return reloadAndReapply();
    return send(current);
  }, [previewId, reloadAndReapply, send]);

  /** Drops the pending ops; the shown (last acknowledged) revision stays. */
  const discard = useCallback(() => clearPending(previewId), [previewId]);

  return { apply, discard, pending, reloadAndReapply, retry };
}
