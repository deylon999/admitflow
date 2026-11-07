import { useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { manualDirectionApi } from '@/entities/manual-direction';

export function useDeleteManualDirection({
  id,
  beforeDelete,
  onRemoved,
}: {
  id: string;
  beforeDelete: () => boolean;
  onRemoved: () => void;
}) {
  const button = useRef<HTMLButtonElement>(null);
  const [confirming, setConfirming] = useState(false);
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => manualDirectionApi.remove(id),
    onSuccess: async () => {
      onRemoved();
      await client.invalidateQueries({ queryKey: ['watches'] });
      await client.invalidateQueries({ queryKey: ['direction-budget'] });
    },
  });
  function cancel() {
    setConfirming(false);
    requestAnimationFrame(() => button.current?.focus());
  }
  function confirm() {
    if (beforeDelete()) mutation.mutate();
  }
  return {
    button,
    confirming,
    mutation,
    toggle: () => setConfirming(!confirming),
    cancel,
    confirm,
  };
}

export type ManualDirectionDeletion = ReturnType<typeof useDeleteManualDirection>;
