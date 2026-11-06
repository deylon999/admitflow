import { useEffect, useRef } from 'react';

export function DeleteConfirmation({
  text,
  label,
  disabled,
  onCancel,
  onConfirm,
}: {
  text: string;
  label: string;
  disabled: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    cancel.current?.focus();
  }, []);
  return (
    <div
      className="delete-confirm surface"
      role="region"
      aria-label="Подтверждение удаления"
      onKeyDown={(event) => {
        if (event.key === 'Escape' && !disabled) {
          event.preventDefault();
          event.stopPropagation();
          onCancel();
        }
      }}
    >
      <p>{text}</p>
      <div>
        <button
          ref={cancel}
          className="button button-secondary"
          type="button"
          disabled={disabled}
          onClick={onCancel}
        >
          Отмена
        </button>
        <button
          className="button danger-button"
          type="button"
          disabled={disabled}
          onClick={onConfirm}
        >
          {disabled ? 'Подождите…' : label}
        </button>
      </div>
    </div>
  );
}
