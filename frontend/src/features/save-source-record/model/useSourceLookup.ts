import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { sourceApi } from '@/entities/admission-source';
import type { LookupResult, SourceGroup } from '@/entities/admission-source';
import { useSessionAccess } from '@/shared/api';

export function useSourceLookup(group: SourceGroup, onSaved: () => void) {
  const [code, setCode] = useState('');
  const [preview, setPreview] = useState<LookupResult | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [attempted, setAttempted] = useState(false);
  const [expired, setExpired] = useState(false);
  const [saved, setSaved] = useState(false);
  const queryClient = useQueryClient();
  const access = useSessionAccess();
  const lookup = useMutation({
    mutationFn: async () => {
      const value = await sourceApi.lookup(group.sourceId!, code.trim());
      if (
        value.group.id !== group.id ||
        value.group.year !== group.year ||
        value.group.universityId !== group.universityId
      ) {
        throw new Error('Ответ относится к другой группе. Повторите поиск в каталоге.');
      }
      return value;
    },
    onSuccess: (value) => {
      setPreview(value);
      setAcknowledged(false);
      setAttempted(false);
      setExpired(false);
    },
  });
  const save = useMutation({
    mutationFn: () => sourceApi.subscribe(preview!.confirmationToken!),
    onSuccess: async () => {
      setCode('');
      setPreview(null);
      setSaved(true);
      await queryClient.invalidateQueries({ queryKey: ['archive-directions'] });
      await queryClient.invalidateQueries({ queryKey: ['direction-budget'] });
      onSaved();
    },
  });
  useEffect(() => {
    if (access.data !== 'active') {
      setCode('');
      setPreview(null);
      setAcknowledged(false);
    }
  }, [access.data]);
  useEffect(() => {
    if (!preview?.expiresAt) return;
    const timer = setTimeout(
      () => setExpired(true),
      Math.max(0, Date.parse(preview.expiresAt) - Date.now()),
    );
    return () => clearTimeout(timer);
  }, [preview]);
  const busy = lookup.isPending || save.isPending;
  const validCode = /^[A-Za-z0-9-]{1,64}$/.test(code.trim());

  function changeCode(value: string) {
    setCode(value);
    setPreview(null);
    setAcknowledged(false);
    save.reset();
  }

  function findRecord() {
    if (busy || !validCode) return;
    setSaved(false);
    setPreview(null);
    lookup.mutate();
  }

  function saveRecord() {
    if (!preview) return;
    if (!attempted && (!preview.expiresAt || Date.now() >= Date.parse(preview.expiresAt))) {
      setExpired(true);
      return;
    }
    setAttempted(true);
    save.mutate();
  }

  return {
    code,
    preview,
    acknowledged,
    setAcknowledged,
    attempted,
    expired,
    saved,
    access: access.data,
    lookup,
    save,
    busy,
    validCode,
    changeCode,
    findRecord,
    saveRecord,
  };
}
