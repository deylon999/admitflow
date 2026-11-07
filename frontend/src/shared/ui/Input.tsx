import type { ComponentProps } from 'react';

export function Input({ type, className = '', ...props }: ComponentProps<'input'>) {
  const control = type === 'checkbox' || type === 'radio' ? 'check-control' : 'form-control';
  return (
    <input
      {...props}
      type={type}
      className={`${control} ${className}`.trim()}
    />
  );
}

export function Select({ className = '', ...props }: ComponentProps<'select'>) {
  return (
    <select
      {...props}
      className={`form-control ${className}`.trim()}
    />
  );
}
