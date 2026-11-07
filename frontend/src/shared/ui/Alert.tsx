import { createElement } from 'react';
import type { ComponentPropsWithRef } from 'react';

export function Alert<T extends 'div' | 'p' = 'div'>({
  as,
  tone = 'error',
  className = '',
  ...props
}: { as?: T; tone?: 'error' | 'info' | 'warning' } & ComponentPropsWithRef<T>) {
  return createElement(as ?? 'div', {
    ...props,
    className: `alert alert-${tone} ${className}`.trim(),
  });
}
