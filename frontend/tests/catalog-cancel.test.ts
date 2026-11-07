import { afterEach, expect, it, vi } from 'vitest';
import { QueryObserver } from '@tanstack/react-query';
import { universityApi } from '@/entities/university';
import { createQueryClient } from '@/app/providers/query-client';

afterEach(() => vi.unstubAllGlobals());
it('cancels an abandoned catalog request while a subsequent search succeeds', async () => {
  let oldSignal: AbortSignal | undefined;
  const fetch = vi
    .fn()
    .mockImplementationOnce((_url, init: RequestInit) => {
      oldSignal = init.signal as AbortSignal;
      return new Promise<Response>((_resolve, reject) =>
        oldSignal!.addEventListener('abort', () => reject(oldSignal!.reason), { once: true }),
      );
    })
    .mockResolvedValueOnce(Response.json({ items: [], total: 0 }));
  vi.stubGlobal('fetch', fetch);
  const client = createQueryClient();
  const observer = new QueryObserver(client, {
    queryKey: ['universities', 'old'],
    queryFn: ({ signal }) => universityApi.universities('old', signal),
  });
  const unsubscribe = observer.subscribe(() => {});
  expect(oldSignal?.aborted).toBe(false);
  unsubscribe();
  expect(oldSignal?.aborted).toBe(true);
  expect(
    await client.fetchQuery({
      queryKey: ['universities', 'new'],
      queryFn: ({ signal }) => universityApi.universities('new', signal),
    }),
  ).toEqual({ items: [], total: 0, nextOffset: null });
  expect(fetch).toHaveBeenCalledTimes(2);
  client.clear();
});
