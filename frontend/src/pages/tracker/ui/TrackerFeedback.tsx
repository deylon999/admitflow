import { Alert, Button } from '@/shared/ui';
import { DraftRecovery } from '@/features/edit-manual-direction';
import type { TrackerModel } from '../model/useTrackerModel';

function errorText(error: unknown) {
  return error instanceof Error ? error.message : 'Не удалось выполнить действие.';
}

export function TrackerFeedback({ model }: { model: TrackerModel }) {
  const { notice, privateVisible, watches, busy, editor } = model;
  const { restore, form, recovery, recoveryBlocked, discardRecovery } = editor;
  return (
    <>
      <p
        className="tracker-notice"
        role="status"
      >
        {notice}
      </p>
      {restore.isError && privateVisible && (
        <Alert
          as="p"
          className="form-error"
          role="alert"
        >
          Не удалось проверить доступ перед восстановлением. {errorText(restore.error)}
        </Alert>
      )}
      {privateVisible && !form && recovery && (
        <DraftRecovery
          record={recovery}
          blockedReason={recoveryBlocked}
          disabled={busy || watches.isFetching || watches.isError}
          onRestore={() => restore.mutate()}
          onDiscard={discardRecovery}
        />
      )}
      {privateVisible && watches.isError && watches.data && (
        <Alert
          tone="warning"
          className="surface stale-warning"
          role="alert"
        >
          <p>
            Не удалось обновить направления. Показаны последние загруженные сохранения с их
            исходными датами.
          </p>
          <p>{errorText(watches.error)}</p>
          <Button
            variant="ghost"

            type="button"
            disabled={watches.isFetching}
            onClick={() => void watches.refetch()}
          >
            Повторить обновление
          </Button>
        </Alert>
      )}
    </>
  );
}
