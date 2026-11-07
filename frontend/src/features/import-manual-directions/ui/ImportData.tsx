import type { ImportResult } from '@/entities/manual-direction';
import { useManualImport } from '../model/useManualImport';

export function ImportData({
  count,
  disabled,
  onDone,
}: {
  count: number;
  disabled: boolean;
  onDone: (result: ImportResult) => void;
}) {
  const { prepared, reading, error, input, summary, mutation, clear, select, added, tooMany } =
    useManualImport(count, onDone);
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
          disabled={disabled || reading || mutation.isPending}
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
              disabled={disabled || mutation.isPending}
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
