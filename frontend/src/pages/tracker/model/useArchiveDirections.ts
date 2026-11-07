import { useState } from 'react';
import { useIsFetching, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { sourceApi } from '@/entities/admission-source';
import { downloadJson } from '@/shared/lib/download';
import { useSessionAccess } from '@/shared/api';

const mutableSourceFamilies = ['archive-history', 'scenario', 'scenario-history'];

export function useArchiveDirections(onRemoved: () => void) {
  const [deleting, setDeleting] = useState<string | null>(null);
  const client = useQueryClient();
  const download = useMutation({
    mutationFn: sourceApi.exportArchive,
    onSuccess: (value) =>
      downloadJson(value, `admitflow-archive-${value.exportedAt.slice(0, 10)}.json`),
  });
  const remove = useMutation({
    mutationFn: (id: string) => sourceApi.removeSubscription(id),
    onSuccess: async () => {
      setDeleting(null);
      await client.invalidateQueries({ queryKey: ['changes'] });
      for (const key of ['archive-history', 'scenario', 'scenario-history', 'scenario-detail']) {
        client.removeQueries({ queryKey: [key] });
      }
      await client.invalidateQueries({ queryKey: ['archive-directions'] });
      await client.invalidateQueries({ queryKey: ['direction-budget'] });
      onRemoved();
    },
    onError: async (_error, id) => {
      // Reconcile a possibly committed DELETE by read; never repeat it implicitly.
      const current = await client
        .fetchQuery({
          queryKey: ['archive-directions'],
          queryFn: ({ signal }) => sourceApi.subscriptions(signal),
          staleTime: 0,
        })
        .catch(() => null);
      if (current && !current.some((item) => item.id === id)) {
        setDeleting(null);
        await client.invalidateQueries({ queryKey: ['changes'] });
        for (const key of ['archive-history', 'scenario', 'scenario-history', 'scenario-detail']) {
          client.removeQueries({ queryKey: [key, id] });
        }
        await client.invalidateQueries({ queryKey: ['direction-budget'] });
        onRemoved();
      }
    },
  });
  const access = useSessionAccess();
  const records = useQuery({
    queryKey: ['archive-directions'],
    queryFn: ({ signal }) => sourceApi.subscriptions(signal),
    enabled: access.data === 'active',
  });
  const sourceReads = useIsFetching({
    predicate: ({ queryKey }) =>
      queryKey[0] === 'archive-directions' ||
      queryKey[0] === 'changes' ||
      (typeof queryKey[0] === 'string' &&
        mutableSourceFamilies.includes(queryKey[0]) &&
        !!records.data?.some(({ id }) => queryKey[1] === id)),
  });
  const refreshFacts = useMutation({
    mutationFn: async () => {
      const keys = [
        ['archive-directions'],
        ['changes'],
        ...(records.data ?? []).flatMap(({ id }) => mutableSourceFamilies.map((key) => [key, id])),
      ];
      // Details identify immutable assessments; current facts/history indexes refresh.
      const results = await Promise.allSettled(
        keys.map((queryKey) => client.invalidateQueries({ queryKey }, { throwOnError: true })),
      );
      const failures = results.filter((result) => result.status === 'rejected');
      if (failures.length) {
        throw new AggregateError(
          failures.map((result) => result.reason),
          'Some saved source facts could not be refreshed.',
        );
      }
    },
  });

  return {
    deleting,
    setDeleting,
    download,
    remove,
    access: access.data,
    records,
    sourceReads,
    refreshFacts,
  };
}
