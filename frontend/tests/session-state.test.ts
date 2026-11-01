import { afterEach, expect, it, vi } from 'vitest';
import fixture from '../../shared/manual-watch.json';

afterEach(() => { vi.unstubAllGlobals(); vi.resetModules(); });
function setup() {
  const storage = new Map([['admitflow-session-used', '1']]);
  vi.stubGlobal('localStorage', { getItem: (key: string) => storage.get(key), setItem: (key: string, value: string) => storage.set(key, value), removeItem: (key: string) => storage.delete(key) });
  vi.stubGlobal('navigator', {});
}
const info = { expiresAt: '2026-12-02T00:00:00Z' };

it('late bootstrap failure cannot clear a newer readonly session', async () => {
  setup();
  let release!: (response: Response) => void;
  const gate = new Promise<Response>(resolve => { release = resolve; });
  const fetch = vi.fn().mockImplementationOnce(() => gate).mockResolvedValueOnce(Response.json(info));
  vi.stubGlobal('fetch', fetch);
  const { api, SessionChangedError } = await import('../src/lib/api');
  const old = api.session().catch(error => error);
  api.forgetSession();
  expect(await api.resumeSession()).toEqual(info);
  release(Response.json({ detail: 'old failure' }, { status: 503 }));
  expect(await old).toBeInstanceOf(SessionChangedError);
  expect(await api.session()).toEqual(info);
  expect(fetch).toHaveBeenCalledTimes(2);
});

it('private body received after access changes is never returned as current data', async () => {
  setup();
  let controller!: ReadableStreamDefaultController<Uint8Array>;
  const body = new ReadableStream<Uint8Array>({ start(value) { controller = value; } });
  const fetch = vi.fn().mockResolvedValueOnce(Response.json(info)).mockResolvedValueOnce(new Response(body)).mockResolvedValueOnce(Response.json(info));
  vi.stubGlobal('fetch', fetch);
  const { api, SessionChangedError } = await import('../src/lib/api');
  const old = api.list().catch(error => error);
  await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  api.forgetSession();
  await api.resumeSession();
  controller.enqueue(new TextEncoder().encode(JSON.stringify([fixture])));
  controller.close();
  expect(await old).toBeInstanceOf(SessionChangedError);
});
