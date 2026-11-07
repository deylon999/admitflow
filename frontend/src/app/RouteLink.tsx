import type { AnchorHTMLAttributes, ReactNode } from 'react';

type Props = AnchorHTMLAttributes<HTMLAnchorElement> & {
  to: string;
  children: ReactNode;
};

/** The global router intercepts these plain links; they also work in offline previews. */
export function RouteLink({ to, children, ...props }: Props) {
  return (
    <a href={to} {...props}>
      {children}
    </a>
  );
}
