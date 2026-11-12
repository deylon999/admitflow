import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { routeHref } from './navigation';

type Props = AnchorHTMLAttributes<HTMLAnchorElement> & {
  to: string;
  children: ReactNode;
};

/** The global router intercepts these plain links; they also work in offline previews. */
export function RouteLink({ to, children, ...props }: Props) {
  return (
    <a href={routeHref(to)} {...props}>
      {children}
    </a>
  );
}
