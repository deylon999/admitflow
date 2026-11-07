import { DeleteConfirmation, Button, Alert, Card } from '@/shared/ui';
import { SessionExpiredError, requestErrorText } from '@/shared/api';
import type { TrackerModel } from '../model/useTrackerModel';

export function TrackerAccess({ model, tools = false }: { model: TrackerModel; tools?: boolean }) {
  const {
    resetButton,
    expired,
    busy,
    directionTotal,
    download,
    setConfirmReset,
    confirmReset,
    privateVisible,
    reset,
    resetting,
    changed,
    synchronize,
  } = model;
  return (
    <>
      {tools && (
        <div className="tracker-data-actions">
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
      )}
      {!tools && privateVisible && download.isError && (
        <Alert
          as="p"
          className="form-error"
          role="alert"
        >
          Не удалось подготовить файл. {requestErrorText(download.error)}
        </Alert>
      )}
      {tools && confirmReset && privateVisible && (
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
      {!tools && resetting && <p role="status">Обновляем гостевой доступ…</p>}
      {!tools && expired && !resetting && (
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
      {!tools && synchronize.isError && (
        <Alert
          as="p"
          className="form-error"
          role="alert"
        >
          {changed && synchronize.error instanceof SessionExpiredError
            ? 'Доступ ещё обновляется или временно недоступен. Повторите синхронизацию.'
            : requestErrorText(synchronize.error)}
        </Alert>
      )}
      {!tools && reset.isError && (
        <Alert
          as="p"
          className="form-error"
          role="alert"
        >
          {requestErrorText(reset.error)}
        </Alert>
      )}
    </>
  );
}
