import { afterEach, expect, it, vi } from 'vitest';
import { SessionExpiredError, sessionAccessKey } from '@/shared/api';
import { createQueryClient } from '@/app/providers/query-client';
import type { SessionAccess } from '@/shared/api';

afterEach(() => {
  vi.unstubAllGlobals();
});

for (const source of ['query', 'mutation']) {
  for (const state of ['active', 'changed'] as const) {
    it(`${source}401 keeps ${state === 'changed' ? 'changed access retryable' : 'real expiration visible'}`, async () => {
      const removeItem = vi.fn();
      vi.stubGlobal('sessionStorage', { removeItem });
      const client = createQueryClient();
      client.setQueryData<SessionAccess>(sessionAccessKey, state);
      const failure = new SessionExpiredError();
      const operation = () => Promise.reject(failure);
      try {
        const request =
          source === 'query'
            ? client.fetchQuery({ queryKey: ['synthetic-private-read'], queryFn: operation })
            : client.getMutationCache().build(client, { mutationFn: operation }).execute(undefined);
        await expect(request).rejects.toBe(failure);
        expect(client.getQueryData(sessionAccessKey)).toBe(
          state === 'changed' ? 'changed' : 'expired',
        );
        expect(removeItem).toHaveBeenCalledWith('admitflow-draft-v1');
      } finally {
        client.clear();
      }
    });
  }
}
