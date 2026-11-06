import { useCallback, useEffect, useRef, useState } from 'react';
import { useBlocker } from 'react-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CalculationInputs } from './Calculator';
import { UniversityPicker } from './UniversityPicker';
import { api } from '../lib/api';
import type { Watch } from '../lib/api';
import type { SessionInfo } from '../lib/contracts';
import { clearDraft, storeDraft } from '../lib/draft';
import type { SaveIntent, StoredDraft } from '../lib/draft';
import { calculatePlace } from '../lib/calculator';
import type { CalculationForm, CalculationValues } from '../lib/calculator';
import { draftSignature, validateDirection } from '../lib/direction';
const emptyValues: CalculationForm = { rank: '', seats: '', excluded: '0', noConsent: '0' };
function errorText(error: unknown) {
  return error instanceof Error ? error.message : 'Не удалось выполнить действие.';
}

export function DirectionForm({
  watch,
  sessionInfo,
  restored,
  focusRequest,
  disabled,
  onDone,
  onCancel,
  onDirtyChange,
}: {
  watch?: Watch;
  sessionInfo?: SessionInfo;
  restored?: StoredDraft | null;
  focusRequest: number;
  disabled: boolean;
  onDone: () => void;
  onCancel: () => void;
  onDirtyChange: (dirty: boolean) => void;
}) {
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
  const [localSaved, setLocalSaved] = useState<boolean | null>(restored ? true : null);
  const [localExpiry, setLocalExpiry] = useState<number | null>(restored?.expiresAt ?? null);
  const scope = sessionInfo?.draftScope,
    deadline = sessionInfo?.expiresAt;
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
    if (dirty) persist();
    // Persist only when fields or access change, never refresh the TTL by rendering.
  }, [persist, dirty]);
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
        await api.update(
          watch.id,
          numeric,
          intent.current.key,
          baseSnapshotId.current ?? undefined,
        );
      else await api.create(body, intent.current.key);
    },
    onSuccess: async () => {
      clearDraft();
      await queryClient.invalidateQueries({ queryKey: ['watches'] });
      await queryClient.invalidateQueries({ queryKey: ['history'] });
      await queryClient.invalidateQueries({ queryKey: ['direction-budget'] });
      onDone();
    },
  });
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      (dirty || save.isPending) &&
      (currentLocation.pathname !== nextLocation.pathname ||
        currentLocation.search !== nextLocation.search),
  );
  useEffect(() => {
    if (blocker.state !== 'blocked') return;
    if (save.isPending) blocker.reset();
    else if (window.confirm('Покинуть форму с несохранёнными изменениями?')) blocker.proceed();
    else blocker.reset();
  }, [blocker, save.isPending]);
  useEffect(() => {
    if (!dirty && !save.isPending) return;
    let acceptedLink = false;
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (save.isPending || !acceptedLink) {
        event.preventDefault();
        event.returnValue = '';
      }
    };
    const guardLink = (event: MouseEvent) => {
      const link =
        event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('a[href]') : null;
      if (
        !link ||
        link.target === '_blank' ||
        link.hasAttribute('download') ||
        link.hasAttribute('data-router-link') ||
        event.button !== 0 ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey ||
        event.altKey
      )
        return;
      const target = new URL(link.href, location.href);
      if (
        target.origin === location.origin &&
        target.pathname === location.pathname &&
        target.search === location.search
      )
        return;
      if (save.isPending) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      if (!window.confirm('Удалить несохранённые изменения формы и перейти?')) {
        event.preventDefault();
        event.stopPropagation();
      } else acceptedLink = true;
    };
    window.addEventListener('beforeunload', beforeUnload);
    document.addEventListener('click', guardLink, true);
    return () => {
      window.removeEventListener('beforeunload', beforeUnload);
      document.removeEventListener('click', guardLink, true);
    };
  }, [dirty, currentDraft, save.isPending]);
  return (
    <form
      className="direction-form surface"
      noValidate
      aria-labelledby="direction-form-heading"
      onKeyDown={(event) => {
        if (event.key === 'Escape' && !event.defaultPrevented && !save.isPending) {
          event.preventDefault();
          onCancel();
        }
      }}
      onSubmit={(event) => {
        event.preventDefault();
        setSubmitted(true);
        if (save.isPending || disabled) return;
        if (validation.firstInvalidId) document.getElementById(validation.firstInvalidId)?.focus();
        else save.mutate();
      }}
    >
      <div className="tracker-form-heading">
        <h2
          id="direction-form-heading"
          ref={heading}
          tabIndex={-1}
        >
          {watch ? 'Обновить цифры' : 'Добавить направление'}
        </h2>
        <button
          className="text-button"
          type="button"
          onClick={onCancel}
          aria-label="Закрыть форму"
          disabled={save.isPending}
        >
          ✕
        </button>
      </div>
      <fieldset
        className="direction-fields"
        disabled={save.isPending || disabled}
      >
        <legend className="visually-hidden">Данные направления</legend>
        {watch ? (
          <p className="small-copy">
            {watch.university} · {watch.title}
          </p>
        ) : (
          <>
            <UniversityPicker
              value={university}
              onChange={setUniversity}
              error={metadata.university}
              onSelect={(item) => {
                setUniversity(item.name);
                setSourceUrl(item.catalogOrigin === 'monitoring' ? '' : item.provenanceUrl);
              }}
            />
            <div className="field">
              <label htmlFor="direction-title">Направление и конкурсная группа</label>
              <input
                id="direction-title"
                value={title}
                required
                aria-invalid={Boolean(metadata.title) || undefined}
                aria-describedby={metadata.title ? 'direction-title-error' : undefined}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Например: информатика, общий конкурс"
              />
              {metadata.title && (
                <p
                  id="direction-title-error"
                  className="form-error"
                  role="alert"
                >
                  {metadata.title}
                </p>
              )}
            </div>
            <div className="field">
              <label htmlFor="source-url">Ссылка на конкурсный список</label>
              <input
                id="source-url"
                type="url"
                value={sourceUrl}
                maxLength={2048}
                required
                aria-invalid={Boolean(metadata.sourceUrl) || undefined}
                aria-describedby={metadata.sourceUrl ? 'source-url-error' : undefined}
                onChange={(event) => setSourceUrl(event.target.value)}
                placeholder="https://…"
              />
              {metadata.sourceUrl && (
                <p
                  id="source-url-error"
                  className="form-error"
                  role="alert"
                >
                  {metadata.sourceUrl}
                </p>
              )}
            </div>
          </>
        )}
        <div className="tracker-number-fields">
          <CalculationInputs
            values={values}
            onChange={setValues}
            error={submitted ? error : undefined}
            prefix="tracker-"
          />
        </div>
      </fieldset>
      <p className="form-note">
        Берите данные одной конкурсной группы. Каждый человек выше вас учитывается только в одной из
        двух вычитаемых групп.
      </p>
      {!('error' in result) && (
        <div className="tracker-preview">
          <span>Место по введённым данным</span>
          <strong>
            {result.place} <small>из {result.seats}</small>
          </strong>
        </div>
      )}
      {submitted && error && (
        <p
          className="form-error"
          id="tracker-calculation-error"
          role="alert"
        >
          {error.error}
        </p>
      )}
      {save.isError && (
        <p
          className="form-error"
          role="alert"
        >
          {errorText(save.error)}
        </p>
      )}
      {save.isPending && (
        <p role="status">Дождитесь результата сохранения перед переходом на другую страницу.</p>
      )}
      {disabled && !save.isPending && (
        <p role="status">Дождитесь завершения текущей операции. Поля формы сохранены.</p>
      )}
      {localSaved === true && (
        <p
          className="form-note"
          role="status"
        >
          Черновик сохранён в этой вкладке на 30 минут, не дольше гостевого доступа. Это не
          подтверждение сохранения направления на сервере.
        </p>
      )}
      {localSaved === false && (
        <p
          className="form-error"
          role="status"
        >
          Не удалось сохранить черновик в этой вкладке. Сохраните направление перед уходом.
        </p>
      )}
      <button
        className="button button-primary"
        type="submit"
        disabled={save.isPending || disabled}
      >
        {save.isPending ? 'Сохраняем…' : watch ? 'Сохранить обновление' : 'Сохранить направление'}
      </button>
      <p className="form-note">
        Числа сохраняются вручную. Сервис не запрашивает список по указанной ссылке.
      </p>
    </form>
  );
}
