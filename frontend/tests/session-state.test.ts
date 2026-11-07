import { afterEach, expect, it, vi } from 'vitest';
import fixture from '../../shared/manual-watch.json';

afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();
});
function setup() {
  const storage = new Map([['admitflow-session-used', '1']]);
  vi.stubGlobal('localStorage', {
    getItem: (key: string) => storage.get(key),
    setItem: (key: string, value: string) => storage.set(key, value),
    removeItem: (key: string) => storage.delete(key),
  });
  vi.stubGlobal('navigator', {});
}
const info = { expiresAt: '2026-12-02T00:00:00Z' };

function setupLocks() {
  let tail: Promise<unknown> = Promise.resolve();
  const request = vi.fn(
    (_name: string, options: { signal?: AbortSignal }, operation: () => Promise<unknown>) => {
      const pending = tail.then(() => {
        options.signal?.throwIfAborted();
        return operation();
      });
      tail = pending.catch(() => {});
      return pending;
    },
  );
  vi.stubGlobal('navigator', { locks: { request } });
  return request;
}

it('a canceled consumer settles before bootstrap while the shared session stays usable', async () => {
  setup();
  let release!: (value: Response) => void;
  const gate = new Promise<Response>((resolve) => {
    release = resolve;
  });
  const fetch = vi.fn().mockReturnValueOnce(gate).mockResolvedValueOnce(Response.json([]));
  vi.stubGlobal('fetch', fetch);
  const { sessionApi } = await import('@/shared/api');
  const { manualDirectionApi } = await import('@/entities/manual-direction');
  const controller = new AbortController();
  const canceled = manualDirectionApi.list(controller.signal);
  const failure = expect(canceled).rejects.toBeInstanceOf(DOMException);
  const other = manualDirectionApi.list();
  controller.abort();
  await failure;
  expect(fetch).toHaveBeenCalledTimes(1);
  release(Response.json(info));
  expect(await other).toEqual([]);
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(await sessionApi.session()).toEqual(info);
});

it('late bootstrap failure cannot clear a newer readonly session', async () => {
  setup();
  let release!: (response: Response) => void;
  const gate = new Promise<Response>((resolve) => {
    release = resolve;
  });
  const fetch = vi
    .fn()
    .mockImplementationOnce(() => gate)
    .mockResolvedValueOnce(Response.json(info));
  vi.stubGlobal('fetch', fetch);
  const { sessionApi, SessionChangedError } = await import('@/shared/api');
  const old = sessionApi.session().catch((error) => error);
  sessionApi.forgetSession();
  expect(await sessionApi.resumeSession()).toEqual(info);
  release(Response.json({ detail: 'old failure' }, { status: 503 }));
  expect(await old).toBeInstanceOf(SessionChangedError);
  expect(await sessionApi.session()).toEqual(info);
  expect(fetch).toHaveBeenCalledTimes(2);
});

it('private body received after access changes is never returned as current data', async () => {
  setup();
  let controller!: ReadableStreamDefaultController<Uint8Array>;
  const body = new ReadableStream<Uint8Array>({
    start(value) {
      controller = value;
    },
  });
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(Response.json(info))
    .mockResolvedValueOnce(new Response(body))
    .mockResolvedValueOnce(Response.json(info));
  vi.stubGlobal('fetch', fetch);
  const { sessionApi, SessionChangedError } = await import('@/shared/api');
  const { manualDirectionApi } = await import('@/entities/manual-direction');
  const old = manualDirectionApi.list().catch((error) => error);
  await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  sessionApi.forgetSession();
  await sessionApi.resumeSession();
  controller.enqueue(new TextEncoder().encode(JSON.stringify([fixture])));
  controller.close();
  expect(await old).toBeInstanceOf(SessionChangedError);
});

it('unauthorized responses cancel unread bodies', async () => {
  setup();
  const cancel = vi.fn();
  const body = new ReadableStream<Uint8Array>({ cancel });
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValueOnce(Response.json(info))
      .mockResolvedValueOnce(new Response(body, { status: 401 })),
  );
  const { SessionExpiredError } = await import('@/shared/api');
  const { manualDirectionApi } = await import('@/entities/manual-direction');
  await expect(manualDirectionApi.list()).rejects.toBeInstanceOf(SessionExpiredError);
  expect(cancel).toHaveBeenCalledTimes(1);
});

it('stale response headers cancel their unread body', async () => {
  setup();
  let release!: (value: Response) => void;
  const cancel = vi.fn();
  vi.stubGlobal(
    'fetch',
    vi.fn().mockReturnValueOnce(
      new Promise<Response>((resolve) => {
        release = resolve;
      }),
    ),
  );
  const { sessionApi, SessionChangedError } = await import('@/shared/api');
  const result = sessionApi.session();
  const failure = expect(result).rejects.toBeInstanceOf(SessionChangedError);
  sessionApi.forgetSession();
  release(new Response(new ReadableStream<Uint8Array>({ cancel })));
  await failure;
  expect(cancel).toHaveBeenCalledTimes(1);
});

it('readonly resume waits for a reset to finish and never creates or deletes a session', async () => {
  setup();
  const lock = setupLocks();
  let release!: (response: Response) => void;
  const pendingCreation = new Promise<Response>((resolve) => {
    release = resolve;
  });
  const methods: string[] = [];
  const fetch = vi.fn((_url: string, options: RequestInit) => {
    const method = options.method ?? 'GET';
    methods.push(method);
    if (method === 'POST') return pendingCreation;
    return Promise.resolve(
      method === 'DELETE' ? new Response(null, { status: 204 }) : Response.json(info),
    );
  });
  vi.stubGlobal('fetch', fetch);
  const { sessionApi } = await import('@/shared/api');
  const reset = sessionApi.resetSession();
  await vi.waitFor(() => expect(methods).toEqual(['DELETE', 'POST']));
  const resume = sessionApi.resumeSession();
  await Promise.resolve();
  expect(lock).toHaveBeenCalledTimes(2);
  expect(methods).toEqual(['DELETE', 'POST']);

  release(new Response(null, { status: 204 }));
  expect(await reset).toEqual(info);
  expect(await resume).toEqual(info);
  expect(methods).toEqual(['DELETE', 'POST', 'GET', 'GET']);
  expect(await sessionApi.session()).toEqual(info);
  expect(fetch).toHaveBeenCalledTimes(4);
});

it('queued resume rejects an access change before issuing its readonly request', async () => {
  setup();
  const lock = setupLocks();
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const held = lock('admitflow-guest-session', {}, () => gate);
  const fetch = vi.fn();
  vi.stubGlobal('fetch', fetch);
  const { sessionApi, SessionChangedError } = await import('@/shared/api');
  const resume = sessionApi.resumeSession();
  const rejected = expect(resume).rejects.toBeInstanceOf(SessionChangedError);
  sessionApi.forgetSession();
  release();
  await held;
  await rejected;
  expect(fetch).not.toHaveBeenCalled();
});

it('queued reset cannot delete the replacement session after an access change', async () => {
  setup();
  const lock = setupLocks();
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const held = lock('admitflow-guest-session', {}, () => gate);
  const fetch = vi.fn();
  vi.stubGlobal('fetch', fetch);
  const { sessionApi, SessionChangedError } = await import('@/shared/api');
  const reset = sessionApi.resetSession();
  const rejected = expect(reset).rejects.toBeInstanceOf(SessionChangedError);
  sessionApi.forgetSession();
  release();
  await held;
  await rejected;
  expect(fetch).not.toHaveBeenCalled();
});

it('resume cannot cache private session data received after the access epoch changes', async () => {
  setup();
  setupLocks();
  let controller!: ReadableStreamDefaultController<Uint8Array>;
  const body = new ReadableStream<Uint8Array>({
    start(value) {
      controller = value;
    },
  });
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response(body))
    .mockResolvedValueOnce(Response.json(info));
  vi.stubGlobal('fetch', fetch);
  const { sessionApi, SessionChangedError } = await import('@/shared/api');
  const resume = sessionApi.resumeSession();
  const rejected = expect(resume).rejects.toBeInstanceOf(SessionChangedError);
  await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  sessionApi.forgetSession();
  controller.enqueue(new TextEncoder().encode(JSON.stringify(info)));
  controller.close();
  await rejected;
  expect(await sessionApi.session()).toEqual(info);
  expect(fetch).toHaveBeenCalledTimes(2);
});

it('a failed reset releases the guest lock for a readonly resume without another write', async () => {
  setup();
  setupLocks();
  const methods: string[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn((_url: string, options: RequestInit) => {
      const method = options.method ?? 'GET';
      methods.push(method);
      if (method === 'DELETE') return Promise.resolve(new Response(null, { status: 204 }));
      return Promise.resolve(
        Response.json({ detail: 'Synthetic failure' }, { status: method === 'POST' ? 503 : 401 }),
      );
    }),
  );
  const { sessionApi, SessionExpiredError } = await import('@/shared/api');
  await expect(sessionApi.resetSession()).rejects.toThrow('Synthetic failure');
  await expect(sessionApi.resumeSession()).rejects.toBeInstanceOf(SessionExpiredError);
  expect(methods).toEqual(['DELETE', 'POST', 'GET']);
});

it('readonly resume keeps genuine expiration semantics when Web Locks are unavailable', async () => {
  setup();
  const fetch = vi.fn().mockResolvedValue(Response.json({}, { status: 401 }));
  vi.stubGlobal('fetch', fetch);
  const { sessionApi, SessionExpiredError } = await import('@/shared/api');
  await expect(sessionApi.resumeSession()).rejects.toBeInstanceOf(SessionExpiredError);
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch.mock.calls[0][1].method).toBeUndefined();
});
