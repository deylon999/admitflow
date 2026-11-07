import { useQuery } from '@tanstack/react-query';
import { sessionAccessKey } from './session-contract';
import type { SessionAccess } from './session-contract';

export function useSessionAccess() {
  return useQuery<SessionAccess>({
    queryKey: sessionAccessKey,
    queryFn: async (): Promise<SessionAccess> => 'active',
    enabled: false,
    initialData: 'active',
  });
}
