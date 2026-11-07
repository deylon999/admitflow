import { useCallback, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { manualDirectionApi, calculatePlace } from '@/entities/manual-direction';
import type { Watch, CalculationForm, CalculationValues } from '@/entities/manual-direction';
import type { SessionInfo } from '@/shared/api';
import { clearDraft, storeDraft } from './draft-store';
import type { SaveIntent, StoredDraft } from './draft-store';
import { draftSignature, validateDirection } from './direction';
import { useUnsavedDirectionGuard } from './useUnsavedDirectionGuard';

export type DirectionFormProps = {
  watch?: Watch;
  sessionInfo?: SessionInfo;
  restored?: StoredDraft | null;
  focusRequest: number;
  disabled: boolean;
  onDone: () => void;
  onCancel: () => void;
  onDirtyChange: (dirty: boolean) => void;
};

const emptyValues: CalculationForm = { rank: '', seats: '', excluded: '0', noConsent: '0' };

export function useDirectionForm({
  watch,
  sessionInfo,
  restored,
  focusRequest,
  disabled,
  onDone,
  onDirtyChange,
}: DirectionFormProps) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, [focusRequest]);
  const [values, setValues] = useState<CalculationForm>(
    restored?.draft.values ?? watch?.latest.values ?? emptyValues,
  );
  const [university, setUniversity] = useState(
    restored?.draft.university ?? watch?.university ?? '',
  );
  const [title, setTitle] = useState(restored?.draft.title ?? watch?.title ?? '');
  const [sourceUrl, setSourceUrl] = useState(restored?.draft.sourceUrl ?? watch?.sourceUrl ?? '');
  const [submitted, setSubmitted] = useState(false);
  const currentDraft = draftSignature({ university, title, sourceUrl, values });
  const initialDraft = useRef(
    draftSignature({
      university: watch?.university ?? '',
      title: watch?.title ?? '',
      sourceUrl: watch?.sourceUrl ?? '',
      values: watch?.latest.values ?? emptyValues,
    }),
  );
  const dirty = currentDraft !== initialDraft.current;
  useEffect(() => {
    onDirtyChange(dirty);
    return () => onDirtyChange(false);
  }, [dirty, onDirtyChange]);
  const intent = useRef<SaveIntent | null>(restored?.intent ?? null);
  const baseSnapshotId = useRef(restored?.baseSnapshotId ?? watch?.latest.id ?? null);
  const [localSaved, setLocalSaved] = useState<boolean | 'clear-failed' | null>(
    restored ? true : null,
  );
  const [localExpiry, setLocalExpiry] = useState<number | null>(restored?.expiresAt ?? null);
  const scope = sessionInfo?.draftScope,
    deadline = sessionInfo?.expiresAt;
  const previousDraft = useRef({ signature: currentDraft, scope, deadline });
  const persist = useCallback(() => {
    const record =
      scope && deadline
        ? storeDraft(scope, deadline, {
            draft: { university, title, sourceUrl, values },
            watchId: watch?.id ?? null,
            baseSnapshotId: baseSnapshotId.current,
            intent: intent.current,
          })
        : null;
    setLocalSaved(Boolean(record));
    setLocalExpiry(record?.expiresAt ?? null);
    return record;
  }, [scope, deadline, university, title, sourceUrl, values, watch?.id]);
  useEffect(() => {
    // Only field/access changes refresh storage; retain a restored draft's original expiry.
    const previous = previousDraft.current;
    previousDraft.current = { signature: currentDraft, scope, deadline };
    if (
      previous.signature === currentDraft &&
      previous.scope === scope &&
      previous.deadline === deadline
    )
      return;
    if (dirty || intent.current) {
      persist();
      return;
    }
    if (clearDraft()) {
      setLocalSaved(null);
      setLocalExpiry(null);
    } else {
      // Replace reverted values if writes still work while removal is unavailable.
      persist();
      setLocalSaved('clear-failed');
    }
  }, [currentDraft, scope, deadline, persist, dirty]);
  useEffect(() => {
    if (localExpiry === null) return;
    const timer = setTimeout(
      () => {
        clearDraft();
        setLocalSaved(false);
        setLocalExpiry(null);
      },
      Math.max(0, localExpiry - Date.now()),
    );
    return () => clearTimeout(timer);
  }, [localExpiry]);
  const result = calculatePlace(values);
  const validation = validateDirection({ university, title, sourceUrl, values }, Boolean(watch));
  const error = validation.calculation;
  const metadata = submitted ? validation.metadata : {};
  const queryClient = useQueryClient();
  const save = useMutation({
    mutationFn: async () => {
      const numeric = Object.fromEntries(
        Object.entries(values).map(([key, value]) => [key, Number(value)]),
      ) as CalculationValues;
      const body = {
        university: university.trim(),
        title: title.trim(),
        sourceUrl: sourceUrl.trim(),
        values: numeric,
      };
      const fingerprint = JSON.stringify({ watchId: watch?.id, ...body });
      if (intent.current?.fingerprint !== fingerprint)
        intent.current = { fingerprint, key: crypto.randomUUID() };
      persist(); // Save the retry key before the request can commit or lose its response.
      if (watch)
        await manualDirectionApi.update(
          watch.id,
          numeric,
          intent.current.key,
          baseSnapshotId.current ?? undefined,
        );
      else await manualDirectionApi.create(body, intent.current.key);
    },
    onSuccess: async () => {
      clearDraft();
      await queryClient.invalidateQueries({ queryKey: ['watches'] });
      await queryClient.invalidateQueries({ queryKey: ['history'] });
      await queryClient.invalidateQueries({ queryKey: ['direction-budget'] });
      onDone();
    },
  });
  useUnsavedDirectionGuard(dirty, currentDraft, save.isPending);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true);
    if (save.isPending || disabled) return;
    if (validation.firstInvalidId) document.getElementById(validation.firstInvalidId)?.focus();
    else save.mutate();
  }
  return {
    heading,
    values,
    setValues,
    university,
    setUniversity,
    title,
    setTitle,
    sourceUrl,
    setSourceUrl,
    submitted,
    result,
    error,
    metadata,
    save,
    localSaved,
    submit,
  };
}
