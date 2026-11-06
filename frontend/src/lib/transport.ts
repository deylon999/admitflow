import { InvalidResponseError } from './contracts';

export const MAX_RESPONSE_BYTES = 10 * 1024 * 1024;

export async function readJsonResponse(
  response: Response,
  signal: AbortSignal,
  limit = MAX_RESPONSE_BYTES,
): Promise<unknown> {
  const length = response.headers.get('content-length');
  const type = response.headers.get('content-type')?.split(';')[0].trim().toLowerCase();
  if (
    (length !== null && (!/^\d+$/.test(length) || Number(length) > limit)) ||
    (type && type !== 'application/json')
  ) {
    void response.body?.cancel().catch(() => {});
    throw new InvalidResponseError();
  }
  const reader = response.body?.getReader();
  if (!reader) throw new InvalidResponseError();
  const cancel = () => {
    void reader.cancel(signal.reason).catch(() => {});
  };
  signal.addEventListener('abort', cancel, { once: true });
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    signal.throwIfAborted();
    while (true) {
      const result = await reader.read();
      signal.throwIfAborted();
      if (result.done) break;
      size += result.value.byteLength;
      if (size > limit) throw new InvalidResponseError();
      chunks.push(result.value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    try {
      return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
    } catch {
      throw new InvalidResponseError();
    }
  } finally {
    signal.removeEventListener('abort', cancel);
    void reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export class RequestTimeoutError extends Error {
  constructor() {
    super(
      'Сервер не ответил вовремя. Проверьте историю перед повторным сохранением или повторите загрузку.',
    );
  }
}

// Covers both response headers and body. Mutations are never retried here.
export async function withRequestTimeout<T>(
  operation: (signal: AbortSignal) => Promise<T>,
  external?: AbortSignal | null,
  timeout = 15_000,
): Promise<T> {
  const controller = new AbortController();
  const abort = () => controller.abort(external?.reason);
  external?.addEventListener('abort', abort, { once: true });
  if (external?.aborted) abort();
  let rejectAbort!: (reason: unknown) => void;
  const aborted = new Promise<never>((_, reject) => {
    rejectAbort = reject;
  });
  const reject = () => rejectAbort(controller.signal.reason);
  controller.signal.addEventListener('abort', reject, { once: true });
  const timer = setTimeout(() => controller.abort(new RequestTimeoutError()), timeout);
  try {
    controller.signal.throwIfAborted();
    return await Promise.race([operation(controller.signal), aborted]);
  } finally {
    clearTimeout(timer);
    external?.removeEventListener('abort', abort);
    controller.signal.removeEventListener('abort', reject);
  }
}
