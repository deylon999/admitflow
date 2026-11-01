export class RequestTimeoutError extends Error {
  constructor() { super('Сервер не ответил вовремя. Проверьте историю перед повторным сохранением или повторите загрузку.'); }
}

// Covers both response headers and body. Mutations are never retried here.
export async function withRequestTimeout<T>(operation: (signal: AbortSignal) => Promise<T>, external?: AbortSignal | null, timeout = 15_000): Promise<T> {
  const controller = new AbortController();
  const abort = () => controller.abort(external?.reason);
  external?.addEventListener('abort', abort, { once: true });
  if (external?.aborted) abort();
  let rejectAbort!: (reason: unknown) => void;
  const aborted = new Promise<never>((_, reject) => { rejectAbort = reject; });
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
