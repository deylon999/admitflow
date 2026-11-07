import { createElement } from 'react';
import type { ComponentPropsWithRef } from 'react';

type CardTag = 'div' | 'article' | 'section' | 'aside' | 'details' | 'form';

export function Card<T extends CardTag = 'div'>({
  as,
  className = '',
  ...props
}: { as?: T } & ComponentPropsWithRef<T>) {
  return createElement(as ?? 'div', { ...props, className: `surface ${className}`.trim() });
}
