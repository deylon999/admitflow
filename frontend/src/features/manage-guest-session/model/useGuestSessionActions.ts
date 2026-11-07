import { useMutation, useQueryClient } from '@tanstack/react-query';
import { manualDirectionApi } from '@/entities/manual-direction';
import { sessionApi, sessionAccessKey } from '@/shared/api';
import type { SessionAccess, SessionInfo } from '@/shared/api';

export const privateQueryFamilies = [
  'watches',
  'history',
  'session-info',
  'archive-directions',
  'direction-budget',
  'archive-history',
  'scenario',
  'scenario-history',
  'scenario-detail',
  'changes',
];

export function useGuestSessionActions({
  beforeReset,
  onSynchronized,
  onResetSettled,
  onResetSuccess,
  onResetError,
}: {
  beforeReset: () => void;
  onSynchronized: () => void;
  onResetSettled: () => void;
  onResetSuccess: (info: SessionInfo) => void;
  onResetError: () => void;
}) {
  const client = useQueryClient();
  async function clearPrivateQueries() {
    await Promise.all(privateQueryFamilies.map((key) => client.cancelQueries({ queryKey: [key] })));
    for (const key of privateQueryFamilies) client.removeQueries({ queryKey: [key] });
  }
  const synchronize = useMutation({
    mutationFn: async () => {
      const info = await sessionApi.resumeSession();
      await client.fetchQuery({
        queryKey: ['watches'],
        queryFn: ({ signal }) => manualDirectionApi.list(signal),
        staleTime: 0,
      });
      return info;
    },
    onSuccess: (info) => {
      client.setQueryData(['session-info'], info);
      for (const key of privateQueryFamilies) {
        if (key !== 'watches' && key !== 'session-info') {
          client.removeQueries({ queryKey: [key] });
        }
      }
      client.setQueryData<SessionAccess>(sessionAccessKey, 'active');
      onSynchronized();
    },
  });
  const reset = useMutation({
    mutationKey: ['session-reset'],
    mutationFn: async () => {
      for (const key of privateQueryFamilies) {
        await client.cancelQueries({ queryKey: [key] });
      }
      beforeReset();
      return sessionApi.resetSession();
    },
    onSuccess: async (info) => {
      await clearPrivateQueries();
      onResetSettled();
      if (client.getQueryData<SessionAccess>(sessionAccessKey) === 'changed') return;
      client.setQueryData(['session-info'], info);
      client.setQueryData<SessionAccess>(sessionAccessKey, 'active');
      onResetSuccess(info);
    },
    onError: async () => {
      await clearPrivateQueries();
      onResetError();
      onResetSettled();
    },
  });
  return { synchronize, reset };
}
