import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query';
import { SessionChangedError, SessionExpiredError } from '@/shared/api';
import { clearDraft } from '@/features/edit-manual-direction';

import { sessionAccessKey } from '@/shared/api';
import type { SessionAccess } from '@/shared/api';

export function createQueryClient() {
  const client: QueryClient = new QueryClient({
    queryCache: new QueryCache({ onError: (error) => markSessionFailure(client, error) }),
    mutationCache: new MutationCache({ onError: (error) => markSessionFailure(client, error) }),
    defaultOptions: {
      queries: {
        retry: (failures, error) =>
          !(error instanceof SessionExpiredError) &&
          !(error instanceof SessionChangedError) &&
          failures < 1,
        staleTime: 30_000,
        refetchOnWindowFocus: false,
      },
      mutations: { retry: false },
    },
  });
  return client;
}

function markSessionFailure(client: QueryClient, error: unknown) {
  if (error instanceof SessionExpiredError) {
    clearDraft();
    client.setQueryData<SessionAccess>(sessionAccessKey, (current) =>
      current === 'changed' ? current : 'expired',
    );
  }
}

export const queryClient = createQueryClient();
