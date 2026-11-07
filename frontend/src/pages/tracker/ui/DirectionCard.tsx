import { Button } from '@/shared/ui';
import { useState } from 'react';
import { ManualDirectionCard } from '@/entities/manual-direction';
import type { Watch } from '@/entities/manual-direction';
import {
  useDeleteManualDirection,
  DeleteManualDirectionFeedback,
} from '@/features/delete-manual-direction';
import { ManualDirectionHistory, PositionChange } from '@/features/review-manual-history';

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
    <ManualDirectionCard
      watch={watch}
      positionChange={<PositionChange watch={watch} />}
    >
      <div className="direction-actions">
        <Button
          variant="secondary"

          type="button"
          disabled={disabled}
          onClick={(event) => onEdit(event.currentTarget)}
        >
          Обновить цифры
        </Button>
        <Button
          variant="ghost"

          type="button"
          aria-expanded={showHistory}
          onClick={() => setShowHistory(!showHistory)}
        >
          История
        </Button>
        <Button
          variant="ghost"
          ref={deletion.button}
          className="delete-link"
          type="button"
          disabled={disabled}
          onClick={deletion.toggle}
        >
          Удалить
        </Button>
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
