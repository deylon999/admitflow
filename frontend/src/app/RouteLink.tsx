import type { AnchorHTMLAttributes, ReactNode } from 'react';

type Props = AnchorHTMLAttributes<HTMLAnchorElement> & {
  to: string;
  children: ReactNode;
};

/** The global router intercepts these plain links; they also work in offline previews. */
export function RouteLink({ to, children, ...props }: Props) {
  return (
    <a href={typeof window !== 'undefined' && new URLSearchParams(location.search).get('mode')==='demo' && to.startsWith('/') && !to.includes('?') && !to.startsWith('/universities') && !to.startsWith('/programs') ? to+'?mode=demo' : to} {...props}>
      {children}
    </a>
  );
}
