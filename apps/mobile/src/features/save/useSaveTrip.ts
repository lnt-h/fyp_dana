import * as Crypto from 'expo-crypto';
import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError } from '../../lib/api/source';
import { acceptPreview, type AcceptPreviewRequest } from '../../lib/api/sourceTrips';
import type { Conflict, TripDetail, Uuid } from '../../lib/api/types';

export type SaveState =
  | { status: 'idle' }
  | { status: 'saving' }
  | { status: 'success'; trip: TripDetail; replayed: boolean }
  | { status: 'blocked'; reasons: Conflict[] }
  | { status: 'conflict'; currentRevision: number }
  | { status: 'interrupted' }
  | { status: 'expired' }
  | { status: 'error' };

/**
 * Explicit Save (API-022) with ADR-009 rules: both expected revisions are always sent; one `Idempotency-Key` per attempt
 * series, reused on a retry of the same body (network loss, in-progress, retryable 5xx) so the server stores at most one
 * version; a new body (e.g. rebasing after a conflict) gets a new key. Nothing here touches the draft: every failure
 * leaves the caller's preview and unsaved edits as they were.
 */
export function useSaveTrip({ previewId, previewRevision, tripRevision }: { previewId: Uuid; previewRevision: number; tripRevision: number }) {
  const [state, setState] = useState<SaveState>({ status: 'idle' });
  const attempt = useRef<{ key: string; body: string } | null>(null);
  const inFlight = useRef(false);
  const mounted = useRef(true);
  const lastBody = useRef<AcceptPreviewRequest | null>(null);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  const run = useCallback(async (body: AcceptPreviewRequest) => {
    if (inFlight.current) return;
    inFlight.current = true;
    const serialized = JSON.stringify(body);
    if (!attempt.current || attempt.current.body !== serialized) {
      attempt.current = { body: serialized, key: Crypto.randomUUID() };
    }
    lastBody.current = body;
    const key = attempt.current.key;
    setState({ status: 'saving' });
    let next: SaveState;
    try {
      const result = await acceptPreview(previewId, body, key);
      attempt.current = null;
      next = { replayed: result.replayed, status: 'success', trip: result.trip };
    } catch (error) {
      if (!(error instanceof ApiError)) {
        // No response: the save may have committed. Keep the key so the retry is a safe replay.
        next = { status: 'interrupted' };
      } else {
        const { code, context, retryable } = error.error;
        switch (code) {
          case 'plan_blocked':
            attempt.current = null;
            next = { reasons: Array.isArray(context?.reasons) ? (context.reasons as Conflict[]) : [], status: 'blocked' };
            break;
          case 'revision_conflict':
            attempt.current = null;
            next = { currentRevision: typeof context?.current_revision === 'number' ? context.current_revision : body.expected_trip_revision + 1, status: 'conflict' };
            break;
          case 'preview_expired':
          case 'preview_closed':
            attempt.current = null;
            next = { status: 'expired' };
            break;
          case 'idempotency_in_progress':
            next = { status: 'interrupted' };
            break;
          case 'idempotency_key_reused':
            attempt.current = null;
            next = { status: 'error' };
            break;
          default:
            if (!retryable) attempt.current = null;
            next = { status: 'error' };
        }
      }
    } finally {
      inFlight.current = false;
    }
    if (mounted.current) setState(next);
  }, [previewId]);

  /** First Save (or Save again after a generic error). */
  const save = useCallback(() => run({ expected_preview_revision: previewRevision, expected_trip_revision: tripRevision }), [previewRevision, run, tripRevision]);

  /** Same body, same key: a replay never creates a second saved version (FR-041). */
  const retry = useCallback(() => run(lastBody.current ?? { expected_preview_revision: previewRevision, expected_trip_revision: tripRevision }), [previewRevision, run, tripRevision]);

  /** After the user confirms replacing the other device's save: re-send accept with the newer trip revision (SCR-029). */
  const saveReplacing = useCallback((currentRevision: number) => run({ expected_preview_revision: previewRevision, expected_trip_revision: currentRevision }), [previewRevision, run]);

  const reset = useCallback(() => setState({ status: 'idle' }), []);

  return { reset, retry, save, saveReplacing, state };
}
