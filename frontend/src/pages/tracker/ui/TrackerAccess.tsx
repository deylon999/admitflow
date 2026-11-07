import { DeleteConfirmation, Button, Alert, Card } from '@/shared/ui';
import { SessionExpiredError } from '@/shared/api';
import type { TrackerModel } from '../model/useTrackerModel';

function errorText(error: unknown) {
  return error instanceof Error ? error.message : 'Не удалось выполнить действие.';
}

export function TrackerAccess({ model }: { model: TrackerModel }) {
  const {
    resetButton,
    expired,
    busy,
    watches,
    count,
    directionTotal,
    download,
    setConfirmReset,
    confirmReset,
    privateVisible,
    reset,
    resetting,
    changed,
    synchronize,
    refreshDirections,
  } = model;
  return (
    <>
      <div className="tracker-data-actions">
        <Button
          variant="ghost"

          type="button"
          disabled={expired || busy || watches.isFetching}
          onClick={() => void refreshDirections()}
        >
          {watches.isFetching ? 'Обновляем…' : 'Обновить направления'}
        </Button>
        <Button
          variant="ghost"

          type="button"
          disabled={busy || !count}
          onClick={() => download.mutate()}
        >
          {download.isPending ? 'Готовим файл…' : 'Скачать данные (JSON)'}
        </Button>
        {directionTotal > 0 && (
          <Button
            variant="ghost"
            ref={resetButton}
            className="delete-link"
            type="button"
            disabled={busy}
            onClick={() => setConfirmReset(true)}
          >
            Удалить все мои данные
          </Button>
        )}
      </div>
      {privateVisible && download.isError && (
        <Alert
          as="p"
          className="form-error"
          role="alert"
        >
          {errorText(download.error)}
        </Alert>
      )}
      {confirmReset && privateVisible && (
        <DeleteConfirmation
          text="Удалить все направления и историю в этом браузере? Отменить удаление нельзя."
          label="Удалить всё"
          disabled={busy}
          onCancel={() => {
            setConfirmReset(false);
            requestAnimationFrame(() => resetButton.current?.focus());
          }}
          onConfirm={() => reset.mutate()}
        />
      )}
      {resetting && <p role="status">Обновляем гостевой доступ…</p>}
      {expired && !resetting && (
        <Card className="empty-state">
          <h2>{changed ? 'Гостевой доступ изменён' : 'Срок гостевой сессии истёк'}</h2>
          <p>
            {changed
              ? 'Старые карточки и черновик скрыты. Синхронизируйте доступ, чтобы увидеть текущую сессию.'
              : 'Доступ к прежним направлениям завершён или cookies были удалены. Для дальнейшей работы начните новую сессию.'}
          </p>
          <Button
            variant="primary"

            type="button"
            disabled={reset.isPending || synchronize.isPending}
            onClick={() => (changed ? synchronize.mutate() : reset.mutate())}
          >
            {changed
              ? 'Синхронизировать доступ'
              : reset.isPending
                ? 'Создаём…'
                : 'Начать новую сессию'}
          </Button>
        </Card>
      )}
      {synchronize.isError && (
        <Alert
          as="p"
          className="form-error"
          role="alert"
        >
          {changed && synchronize.error instanceof SessionExpiredError
            ? 'Доступ ещё обновляется или временно недоступен. Повторите синхронизацию.'
            : errorText(synchronize.error)}
        </Alert>
      )}
      {reset.isError && (
        <Alert
          as="p"
          className="form-error"
          role="alert"
        >
          {errorText(reset.error)}
        </Alert>
      )}
    </>
  );
}
