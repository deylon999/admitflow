import { useState } from 'react';
import { ManualDirectionCard } from '@/entities/manual-direction';
import type { Watch } from '@/entities/manual-direction';
import {
  useDeleteManualDirection,
  DeleteManualDirectionFeedback,
} from '@/features/delete-manual-direction';
import { ManualDirectionHistory } from '@/features/review-manual-history';

export function DirectionCard({
  watch,
  onEdit,
  disabled,
  beforeDelete,
  onRemoved,
}: {
  watch: Watch;
  onEdit: (button: HTMLButtonElement) => void;
  disabled: boolean;
  beforeDelete: () => boolean;
  onRemoved: () => void;
}) {
  const [showHistory, setShowHistory] = useState(false);
  const deletion = useDeleteManualDirection({ id: watch.id, beforeDelete, onRemoved });
  return (
    <ManualDirectionCard watch={watch}>
      <div className="direction-actions">
        <button
          className="button button-secondary"
          type="button"
          disabled={disabled}
          onClick={(event) => onEdit(event.currentTarget)}
        >
          Обновить цифры
        </button>
        <button
          className="text-button"
          type="button"
          aria-expanded={showHistory}
          onClick={() => setShowHistory(!showHistory)}
        >
          История
        </button>
        <button
          ref={deletion.button}
          className="text-button delete-link"
          type="button"
          disabled={disabled}
          onClick={deletion.toggle}
        >
          Удалить
        </button>
      </div>
      <DeleteManualDirectionFeedback
        deletion={deletion}
        disabled={disabled}
      />
      <ManualDirectionHistory
        watch={watch}
        show={showHistory}
      />
    </ManualDirectionCard>
  );
}
