import { ApiError, InvalidResponseError, SessionChangedError, SessionExpiredError } from './errors';
import { parseSession } from './session-contract';
import type { SessionInfo } from './session-contract';
import { readJsonResponse, RequestTimeoutError, withRequestTimeout } from './transport';

let sessionEpoch = 0;
export async function request(
  path: string,
  init: RequestInit = {},
  access: 'public' | 'private' = 'private',
): Promise<unknown> {
  const epoch = sessionEpoch;
  const checkAccess = () => {
    if (access === 'private' && epoch !== sessionEpoch) throw new SessionChangedError();
  };
  return withRequestTimeout(async (signal) => {
    let response: Response;
    try {
      response = await fetch(`/api/v1${path}`, {
        ...init,
        signal,
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'abiturient',
          ...init.headers,
        },
      });
    } catch {
      signal.throwIfAborted();
      checkAccess();
      throw new Error(
        'Не удалось связаться с сервером. Проверьте соединение и попробуйте ещё раз.',
      );
    }
    try {
      checkAccess();
    } catch (error) {
      void response.body?.cancel().catch(() => {});
      throw error;
    }
    if (!response.ok) {
      if (response.status === 401) {
        void response.body?.cancel().catch(() => {});
        throw new SessionExpiredError();
      }
      const body = (await readJsonResponse(response, signal, 64 * 1024).catch(() => null)) as {
        detail?: unknown;
      } | null;
      checkAccess();
      const message =
        typeof body?.detail === 'string' && body.detail.length <= 500
          ? body.detail
          : response.status === 422
            ? 'Проверьте названия, ссылку и числовые значения.'
            : 'Сервис временно недоступен. Попробуйте ещё раз.';
      throw new ApiError(message, response.status);
    }
    if (response.status === 204) return undefined;
    let body: unknown;
    try {
      body = await readJsonResponse(response, signal);
    } catch {
      checkAccess();
      throw new InvalidResponseError();
    }
    checkAccess();
    return body;
  }, init.signal);
}
const sessionMarker = 'admitflow-session-used';
export const sessionChangeKey = 'admitflow-session-change';
let session: Promise<SessionInfo> | undefined;
function forgetSession() {
  sessionEpoch++;
  session = undefined;
}
function usedSession() {
  try {
    return localStorage.getItem(sessionMarker) === '1';
  } catch {
    return false;
  }
}
async function serializeSession<T>(operation: () => Promise<T>): Promise<T> {
  if (typeof navigator === 'undefined' || !navigator.locks) return operation();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new RequestTimeoutError()), 15_000);
  try {
    return await navigator.locks.request(
      'admitflow-guest-session',
      { signal: controller.signal },
      () => {
        clearTimeout(timer);
        return operation();
      },
    );
  } finally {
    clearTimeout(timer);
  }
}
async function loadSession() {
  if (!usedSession()) await request('/session', { method: 'POST' });
  const info = parseSession(await request('/session'));
  try {
    localStorage.setItem(sessionMarker, '1');
  } catch {
    /* Cookie access still works. */
  }
  return info;
}
export async function ensureSession() {
  if (!session) {
    const epoch = sessionEpoch;
    const pending = serializeSession(() => {
      if (epoch !== sessionEpoch) throw new SessionChangedError();
      return loadSession();
    }).catch((error) => {
      if (session === pending) session = undefined;
      throw error;
    });
    session = pending;
  }
  return session;
}
export async function read<T>(
  path: string,
  parse: (value: unknown) => T,
  signal?: AbortSignal,
): Promise<T> {
  signal?.throwIfAborted();
  const epoch = sessionEpoch;
  const pending = ensureSession();
  if (signal) {
    let abort!: () => void;
    const canceled = new Promise<never>((_resolve, reject) => {
      abort = () => reject(signal.reason);
    });
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) abort();
    try {
      await Promise.race([pending, canceled]);
    } finally {
      signal.removeEventListener('abort', abort);
    }
    signal.throwIfAborted();
  } else await pending;
  if (epoch !== sessionEpoch) throw new SessionChangedError();
  return parse(await request(path, { signal }));
}

export const sessionApi = {
  session: ensureSession,
  forgetSession,
  async resumeSession() {
    const epoch = sessionEpoch;
    return serializeSession(async () => {
      if (epoch !== sessionEpoch) throw new SessionChangedError();
      const info = parseSession(await request('/session'));
      if (epoch !== sessionEpoch) throw new SessionChangedError();
      session = Promise.resolve(info);
      try {
        localStorage.setItem(sessionMarker, '1');
      } catch {
        /* Cookie still works. */
      }
      return info;
    });
  },
  async resetSession() {
    const epoch = sessionEpoch;
    return serializeSession(async () => {
      if (epoch !== sessionEpoch) throw new SessionChangedError();
      forgetSession();
      const resetEpoch = sessionEpoch;
      await request('/session', { method: 'DELETE' });
      if (resetEpoch !== sessionEpoch) throw new SessionChangedError();
      try {
        localStorage.setItem(sessionChangeKey, crypto.randomUUID());
      } catch {
        /* Cross-tab notification unavailable. */
      }
      session = undefined;
      try {
        localStorage.removeItem(sessionMarker);
      } catch {
        /* Storage may be disabled. */
      }
      const info = await loadSession();
      if (resetEpoch !== sessionEpoch) throw new SessionChangedError();
      session = Promise.resolve(info);
      return info;
    });
  },
};
