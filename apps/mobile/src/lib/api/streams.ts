/**
 * Typed planning and Guide streams over SSE (remote mode). Each SSE `data:` is one JSON event whose `type` equals the
 * SSE `event:` name. Unknown event types are skipped (forward compatible); a malformed payload is reported as a terminal
 * `error` event. A stream that ends before a terminal event: the planning stream reports `error` (code `network`; the
 * preview id is unknown, so there is nothing to GET), the Guide stream returns quietly so the caller resumes with
 * API-027 (GuideChat already does).
 */
import type { ErrorDetail, GuideStreamEvent, PlanningStreamEvent } from './types';
import { parseEventData, streamSse, type SseRequestOptions } from './sse';

const PLANNING_TERMINAL = new Set(['clarification_required', 'preview_ready', 'error']);
const GUIDE_TERMINAL = new Set(['result', 'error']);

const streamEnded: ErrorDetail = { code: 'network', message: 'The stream ended before a result', retryable: true };
const badPayload: ErrorDetail = { code: 'internal_error', message: 'Unreadable stream event', retryable: true };

const isPlanningEvent = (value: Record<string, unknown>): boolean => {
  switch (value.type) {
    case 'progress': return typeof value.stage === 'string';
    case 'preview_ready': return typeof value.preview_id === 'string';
    case 'clarification_required': return typeof value.clarification === 'object' && value.clarification !== null;
    case 'error': return typeof value.error === 'object' && value.error !== null;
    default: return false;
  }
};

const isGuideEvent = (value: Record<string, unknown>): boolean => {
  switch (value.type) {
    case 'progress': return typeof value.stage === 'string';
    case 'text': return typeof value.delta === 'string';
    case 'result': return typeof value.message === 'object' && value.message !== null;
    case 'error': return typeof value.error === 'object' && value.error !== null;
    default: return false;
  }
};

async function runTypedStream<E extends { type: string }>(
  path: string,
  options: SseRequestOptions,
  known: Set<string>,
  terminal: Set<string>,
  isValid: (value: Record<string, unknown>) => boolean,
  onEvent: (event: E) => void,
  errorOnDrop: boolean,
): Promise<void> {
  let finished = false;
  await streamSse(path, options, message => {
    const data = parseEventData(message);
    if (!data) {
      finished = true;
      onEvent({ error: badPayload, type: 'error' } as unknown as E);
      return 'stop';
    }
    if (!known.has(data.type as string)) return; // unknown event type: ignore
    if (!isValid(data)) {
      finished = true;
      onEvent({ error: badPayload, type: 'error' } as unknown as E);
      return 'stop';
    }
    onEvent(data as unknown as E);
    if (terminal.has(data.type as string)) {
      finished = true;
      return 'stop';
    }
  });
  if (errorOnDrop && !finished && !options.signal?.aborted) onEvent({ error: streamEnded, type: 'error' } as unknown as E);
}

export function runPlanningStream(path: string, options: SseRequestOptions, onEvent: (event: PlanningStreamEvent) => void): Promise<void> {
  return runTypedStream(path, options, new Set(['progress', ...PLANNING_TERMINAL]), PLANNING_TERMINAL, isPlanningEvent, onEvent, true);
}

export function runGuideStream(path: string, options: SseRequestOptions, onEvent: (event: GuideStreamEvent) => void): Promise<void> {
  return runTypedStream(path, options, new Set(['progress', 'text', ...GUIDE_TERMINAL]), GUIDE_TERMINAL, isGuideEvent, onEvent, false);
}
