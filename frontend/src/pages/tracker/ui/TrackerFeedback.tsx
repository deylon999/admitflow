import { Alert, Button } from '@/shared/ui';
import { DraftRecovery } from '@/features/edit-manual-direction';
import { requestErrorText } from '@/shared/api';
import type { TrackerModel } from '../model/useTrackerModel';

export function TrackerFeedback({ model }: { model: TrackerModel }) {
  const { notice, privateVisible, watches, archive, busy, editor, refreshError } = model;
  const { restore, form, recovery, recoveryBlocked, discardRecovery } = editor;
  return (
    <>
      <p
        className={`tracker-notice${notice ? ' tracker-success' : ''}`}
        role="status"
        aria-atomic="true"
      >
        {notice}
      </p>
      {restore.isError && privateVisible && (
        <Alert
          as="p"
          className="form-error"
          role="alert"
        >
          Не удалось восстановить черновик. {requestErrorText(restore.error)}
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
      {privateVisible && refreshError && (
        <Alert
          tone="warning"
          className="surface stale-warning"
          role="alert"
        >
          <p>
            {watches.data?.length === 0 && archive.data?.length === 0
              ? 'При последней успешной загрузке направлений не было. Сейчас обновить список не удалось.'
              : 'Не удалось обновить направления. Показаны ранее загруженные данные с исходными датами.'}
          </p>
          <Button
            variant="ghost"

            type="button"
            disabled={watches.isFetching || archive.isFetching}
            onClick={() => void model.refreshDirections()}
          >
            {watches.isFetching || archive.isFetching ? 'Обновляем…' : 'Повторить обновление'}
          </Button>
        </Alert>
      )}
    </>
  );
}
