/**
 * Draft store for proposal edits (CMP-020, ADR-009, US-019 AC2). A pending op list stays here, keyed by preview id and
 * the revision it was built on, until the server acknowledges it with a new revision. A failure, a 409 or leaving the
 * screen never drops it; only an explicit Discard or a server acknowledgement clears it.
 *
 * Also carries one-shot "open this stop" intents from SCR-026 to the proposal screen (fix shortcuts, Go to stop).
 */
import { useSyncExternalStore } from 'react';
import type { PreviewEditOperation } from '../../../lib/api/sourcePlanning';
import type { Uuid } from '../../../lib/api/types';

export type PendingStatus = 'applying' | 'failed' | 'conflict' | 'expired';

export type PendingEdit = {
  previewId: Uuid;
  /** `expected_revision` the ops were built against. */
  baseRevision: number;
  edits: PreviewEditOperation[];
  /** Reused on retry so a dropped response is not applied twice. */
  idempotencyKey: string;
  status: PendingStatus;
  /** Contract error `code` (S-1) or `network`. */
  errorCode?: string;
};

export const draftKey = (previewId: Uuid, revision: number) => `${previewId}@${revision}`;

const pending = new Map<Uuid, PendingEdit>();
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach(listener => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

export function getPending(previewId: Uuid): PendingEdit | undefined {
  return pending.get(previewId);
}

export function setPending(edit: PendingEdit) {
  pending.set(edit.previewId, edit);
  emit();
}

export function updatePending(previewId: Uuid, patch: Partial<PendingEdit>) {
  const current = pending.get(previewId);
  if (!current) return;
  pending.set(previewId, { ...current, ...patch });
  emit();
}

/** Clears the pending edit, only if it is still the one identified by `idempotencyKey` (when given). */
export function clearPending(previewId: Uuid, idempotencyKey?: string) {
  const current = pending.get(previewId);
  if (!current || (idempotencyKey && current.idempotencyKey !== idempotencyKey)) return;
  pending.delete(previewId);
  emit();
}

export function usePendingEdit(previewId: Uuid): PendingEdit | undefined {
  return useSyncExternalStore(subscribe, () => pending.get(previewId), () => pending.get(previewId));
}

/* ---------------------------------------------------------------- SCR-026 → SCR-024/027 intents */

/** Which control of the Edit stop sheet to prefill/focus. */
export type EditFocus = 'duration' | 'mode' | 'move' | 'replace';

export type StopIntent =
  | { kind: 'edit'; stopId: Uuid; focus?: EditFocus; moveToStart?: boolean }
  | { kind: 'goto'; dayIndex: number; stopId: Uuid };

const intents = new Map<Uuid, StopIntent>();

export function requestStopIntent(previewId: Uuid, intent: StopIntent) {
  intents.set(previewId, intent);
  emit();
}

/** Returns and forgets the intent for this preview. */
export function takeStopIntent(previewId: Uuid): StopIntent | undefined {
  const intent = intents.get(previewId);
  intents.delete(previewId);
  return intent;
}
