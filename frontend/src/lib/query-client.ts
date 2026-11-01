import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query';
import { SessionChangedError, SessionExpiredError } from './api';
import { clearDraft } from './draft';

export const sessionAccessKey = ['session-access'] as const;
export type SessionAccess = 'active' | 'expired' | 'changed';

export function createQueryClient() {
  const client: QueryClient = new QueryClient({
    queryCache: new QueryCache({ onError: error => markSessionFailure(client, error) }),
    mutationCache: new MutationCache({ onError: error => markSessionFailure(client, error) }),
    defaultOptions: {
      queries: { retry: (failures, error) => !(error instanceof SessionExpiredError) && !(error instanceof SessionChangedError) && failures < 1, staleTime: 30_000, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
  return client;
}

function markSessionFailure(client: QueryClient, error: unknown) {
  if (error instanceof SessionExpiredError) { clearDraft(); client.setQueryData<SessionAccess>(sessionAccessKey, 'expired'); }
}
