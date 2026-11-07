import { DeleteConfirmation } from '@/shared/ui';
import type { ManualDirectionDeletion } from '../model/useDeleteManualDirection';

export function DeleteManualDirectionFeedback({
  deletion,
  disabled,
}: {
  deletion: ManualDirectionDeletion;
  disabled: boolean;
}) {
  return (
    <>
      {deletion.confirming && (
        <DeleteConfirmation
          text="Удалить направление и всю его историю?"
          label="Да, удалить"
          disabled={disabled || deletion.mutation.isPending}
          onCancel={deletion.cancel}
          onConfirm={deletion.confirm}
        />
      )}
      {deletion.mutation.isError && (
        <p
          className="form-error"
          role="alert"
        >
          {deletion.mutation.error instanceof Error
            ? deletion.mutation.error.message
            : 'Не удалось выполнить действие.'}
        </p>
      )}
    </>
  );
}
