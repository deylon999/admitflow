import type { ComponentProps } from 'react';

type ButtonProps = ComponentProps<'button'> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'option';
};

export function Button({ variant = 'secondary', className = '', ...props }: ButtonProps) {
  return (
    <button
      {...props}
      className={`button button-${variant} ${variant === 'ghost' ? 'text-button' : ''} ${className}`.trim()}
    />
  );
}
