import type { ReactNode } from 'react';
import { Button } from './Button';

/** Compact, local request feedback. Blocking page errors use Alert instead. */
export function RequestFeedback({
  children,
  onRetry,
  busy = false,
  retryLabel = 'Повторить',
}: {
  children: ReactNode;
  onRetry?: () => void;
  busy?: boolean;
  retryLabel?: string;
}) {
  return (
    <p
      className="request-feedback"
      role="status"
      aria-atomic="true"
    >
      <span>{children}</span>
      {onRetry && (
        <Button
          variant="ghost"
          type="button"
          disabled={busy}
          onClick={onRetry}
        >
          {busy ? 'Повторяем…' : retryLabel}
        </Button>
      )}
    </p>
  );
}
