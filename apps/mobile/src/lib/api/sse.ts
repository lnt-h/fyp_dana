/**
 * Server-Sent Events over `expo/fetch` (SDK 58), which exposes `response.body` as a ReadableStream on iOS, Android and
 * web; React Native's global `fetch` buffers the whole body, and EventSource cannot POST a JSON body or set headers.
 * The parser follows the WHATWG event-stream rules that Gonarra uses: `event:`, `data:` (multi-line, joined with
 * `\n`), `id:`, comment lines (`:` keep-alives), LF/CRLF/CR line endings, dispatch on a blank line. `retry:` is
 * ignored: there is no reconnection, a dropped stream is resumed with a GET of the persisted resource (architecture §5).
 */
import { fetch as expoFetch } from 'expo/fetch';

import { buildHeaders, buildUrl, throwIfNotOk, type RequestOptions } from './client';

export type SseMessage = {
  /** `event:` field; `message` when absent. */
  event: string;
  /** `data:` lines joined with `\n`. */
  data: string;
  id: string | null;
};

/** Incremental parser: feed decoded text chunks of any size; complete events are returned as they finish. */
export class SseParser {
  private buffer = '';
  private eventName = '';
  private dataLines: string[] = [];
  private lastId: string | null = null;
  /** A chunk ended in `\r`; a leading `\n` of the next chunk belongs to that line ending. */
  private pendingCr = false;

  feed(chunk: string): SseMessage[] {
    let text = chunk;
    if (this.pendingCr && text.startsWith('\n')) text = text.slice(1);
    this.pendingCr = false;
    this.buffer += text;
    const out: SseMessage[] = [];
    let start = 0;
    for (let i = 0; i < this.buffer.length; i++) {
      const ch = this.buffer[i];
      if (ch !== '\n' && ch !== '\r') continue;
      const line = this.buffer.slice(start, i);
      if (ch === '\r') {
        if (i + 1 < this.buffer.length) {
          if (this.buffer[i + 1] === '\n') i++;
        } else {
          this.pendingCr = true;
        }
      }
      start = i + 1;
      const message = this.processLine(line);
      if (message) out.push(message);
    }
    this.buffer = this.buffer.slice(start);
    return out;
  }

  /** End of stream: an event without its trailing blank line is discarded (per spec). */
  end(): void {
    this.buffer = '';
    this.eventName = '';
    this.dataLines = [];
  }

  private processLine(line: string): SseMessage | null {
    if (line === '') return this.dispatch();
    if (line.startsWith(':')) return null; // comment / keep-alive
    const colon = line.indexOf(':');
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? '' : line.slice(colon + 1);
    if (value.startsWith(' ')) value = value.slice(1);
    switch (field) {
      case 'event': this.eventName = value; break;
      case 'data': this.dataLines.push(value); break;
      case 'id': if (!value.includes('\0')) this.lastId = value; break;
      default: break; // `retry` and unknown fields are ignored
    }
    return null;
  }

  private dispatch(): SseMessage | null {
    const hasData = this.dataLines.length > 0;
    const message: SseMessage = { data: this.dataLines.join('\n'), event: this.eventName || 'message', id: this.lastId };
    this.eventName = '';
    this.dataLines = [];
    return hasData ? message : null;
  }
}

export type SseRequestOptions = Omit<RequestOptions, 'accept'>;

/**
 * POSTs (or GETs) with `Accept: text/event-stream` and calls `onMessage` per event until the stream ends, `onMessage`
 * returns `'stop'`, or `signal` aborts (resolves quietly). Non-2xx throws `ApiError`; a lost connection rejects with
 * `TypeError`.
 */
export async function streamSse(path: string, options: SseRequestOptions, onMessage: (message: SseMessage) => 'stop' | void): Promise<void> {
  const signal = options.signal;
  let response;
  try {
    response = await expoFetch(buildUrl(path, options.query), {
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      headers: await buildHeaders({ ...options, accept: 'text/event-stream' }),
      method: options.method ?? 'POST',
      signal,
    });
  } catch (error) {
    if (signal?.aborted) return;
    throw error;
  }
  await throwIfNotOk(response);

  const parser = new SseParser();
  const deliver = (messages: SseMessage[]): boolean => {
    for (const message of messages) {
      if (signal?.aborted) return true;
      if (onMessage(message) === 'stop') return true;
    }
    return false;
  };

  const body = response.body;
  if (!body) {
    // No streaming body on this platform: parse the buffered text once.
    const text = await response.text();
    deliver(parser.feed(`${text}\n\n`));
    return;
  }

  const reader = body.getReader();
  const decoder = new TextDecoder();
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      if (deliver(parser.feed(decoder.decode(value, { stream: true })))) return;
    }
    deliver(parser.feed(`${decoder.decode()}\n`));
    parser.end();
  } catch (error) {
    if (signal?.aborted) return;
    throw error;
  } finally {
    reader.cancel().catch(() => undefined);
  }
}

/** Parses an event's JSON `data`; the SSE `event:` name equals the payload `type` in the Gonarra contract. */
export function parseEventData(message: SseMessage): Record<string, unknown> | null {
  try {
    const value: unknown = JSON.parse(message.data);
    if (typeof value !== 'object' || value === null) return null;
    const record = value as Record<string, unknown>;
    if (typeof record.type !== 'string' && message.event !== 'message') record.type = message.event;
    return typeof record.type === 'string' ? record : null;
  } catch {
    return null;
  }
}
