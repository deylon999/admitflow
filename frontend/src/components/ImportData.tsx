import { useEffect, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import {
  decodeImportBytes,
  importKey,
  MAX_IMPORT_FILE_BYTES,
  parseImportText,
} from '../lib/import';
import type { DataExport, ImportResult } from '../lib/contracts';

export function ImportData({
  count,
  disabled,
  onDone,
}: {
  count: number;
  disabled: boolean;
  onDone: (result: ImportResult) => void;
}) {
  const [prepared, setPrepared] = useState<{ bundle: DataExport; key: string } | null>(null);
  const [reading, setReading] = useState(false);
  const [error, setError] = useState('');
  const input = useRef<HTMLInputElement>(null);
  const summary = useRef<HTMLElement>(null);
  const selection = useRef(0);
  const client = useQueryClient();
  useEffect(
    () => () => {
      selection.current++;
    },
    [],
  );
  const mutation = useMutation({
    mutationFn: () => api.importData(prepared!.bundle, prepared!.key),
    onSuccess: async (result) => {
      await client.invalidateQueries({ queryKey: ['watches'] });
      await client.invalidateQueries({ queryKey: ['history'] });
      await client.invalidateQueries({ queryKey: ['direction-budget'] });
      clear();
      onDone(result);
      summary.current?.focus();
    },
  });
  function clear() {
    selection.current++;
    setReading(false);
    setPrepared(null);
    setError('');
    if (input.current) input.current.value = '';
  }
  async function select(file?: File) {
    const version = ++selection.current;
    setPrepared(null);
    setError('');
    mutation.reset();
    setReading(false);
    if (!file) return;
    if (file.size > MAX_IMPORT_FILE_BYTES) {
      setError('Файл больше 8 МБ. Выберите выгрузку меньшего размера.');
      return;
    }
    setReading(true);
    try {
      const bytes = await file.arrayBuffer();
      if (selection.current !== version) return;
      const bundle = parseImportText(decodeImportBytes(bytes));
      const key = await importKey(bundle);
      if (selection.current === version) setPrepared({ bundle, key });
    } catch (error) {
      if (selection.current === version)
        setError(error instanceof Error ? error.message : 'Не удалось прочитать файл.');
    } finally {
      if (selection.current === version) setReading(false);
    }
  }
  const added = prepared?.bundle.watches.length ?? 0;
  const tooMany = count + added > 20;
  return (
    <details className="import-data surface">
      <summary ref={summary}>Восстановить из JSON</summary>
      <p
        id="import-note"
        className="small-copy"
      >
        Выберите свой файл, скачанный из AdmitFlow. Направления добавятся к этой сессии с исходными
        датами ручного ввода. Данные вузов автоматически не обновятся.
      </p>
      <div className="field">
        <label htmlFor="manual-import-file">Файл выгрузки, до 8 МБ</label>
        <input
          ref={input}
          id="manual-import-file"
          type="file"
          accept="application/json,.json"
          aria-describedby="import-note"
          disabled={disabled || reading}
          onChange={(event) => void select(event.target.files?.[0])}
        />
      </div>
      {reading && (
        <>
          <p role="status">Проверяем файл…</p>
          <button
            className="text-button"
            type="button"
            onClick={clear}
          >
            Отменить чтение
          </button>
        </>
      )}
      {error && (
        <p
          className="form-error"
          role="alert"
        >
          {error}
        </p>
      )}
      {prepared && (
        <div>
          <p role="status">
            Найдено направлений: {added}; сохранений:{' '}
            {prepared.bundle.watches.reduce((total, watch) => total + watch.history.length, 0)}.
          </p>
          <ul
            className="import-preview"
            aria-label="Направления из выбранного файла"
          >
            {prepared.bundle.watches.map((watch) => (
              <li key={watch.id}>
                <strong>
                  {watch.university} · {watch.title}
                </strong>
                <p>
                  Сохранений: {watch.history.length}. Последний ручной ввод:{' '}
                  <time dateTime={watch.latest.capturedAt}>{watch.latest.capturedAt}</time>.
                </p>
                <p>Источник: {watch.sourceUrl}</p>
              </li>
            ))}
          </ul>
          <p className="small-copy">
            Существующие записи сохранятся. Повтор этого же файла в той же сессии не создаёт новые
            копии и не восстанавливает удалённые записи.
          </p>
          {tooMany && (
            <p
              className="small-copy"
              id="import-quota-note"
              role="status"
            >
              Для новых направлений недостаточно места. Можно проверить повтор уже выполненного
              импорта: сервер не добавит записи сверх лимита 20.
            </p>
          )}
          <div className="direction-actions">
            <button
              className="button button-primary"
              type="button"
              disabled={disabled || mutation.isPending}
              aria-describedby={tooMany ? 'import-quota-note' : undefined}
              onClick={() => {
                if (!mutation.isPending) mutation.mutate();
              }}
            >
              {mutation.isPending
                ? 'Импортируем…'
                : tooMany
                  ? 'Проверить повтор импорта'
                  : 'Импортировать файл'}
            </button>
            <button
              className="text-button"
              type="button"
              disabled={disabled}
              onClick={clear}
            >
              Отменить импорт
            </button>
          </div>
        </div>
      )}
      {mutation.isError && (
        <p
          className="form-error"
          role="alert"
        >
          {mutation.error instanceof Error
            ? mutation.error.message
            : 'Не удалось импортировать файл.'}{' '}
          Повтор использует тот же ключ операции.
        </p>
      )}
    </details>
  );
}
