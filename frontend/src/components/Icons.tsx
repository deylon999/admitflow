import type { ReactNode, SVGProps } from 'react';

type Name = 'cap' | 'layers' | 'bolt' | 'help' | 'chart' | 'users' | 'list' | 'check' | 'arrow' | 'menu' | 'sparkle';
export function Icon({ name, size = 21, ...props }: SVGProps<SVGSVGElement> & { name: Name; size?: number }) {
  const common = { stroke: 'currentColor', strokeWidth: 2.4, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  const content: Record<Name, ReactNode> = {
    cap: <><path d="m2 10 10-6 10 6-10 6-10-6Z"/><path d="M6 12.5v5c3 3 9 3 12 0v-5M22 10v7"/></>,
    layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/></>,
    bolt: <path d="m13 2-9 11h7l-1 9 10-12h-7l0-8Z"/>,
    help: <><path d="M9.5 9a2.75 2.75 0 1 1 4.6 2c-1.2 1-2.1 1.4-2.1 3"/><path d="M12 18v.2"/><circle cx="12" cy="12" r="10"/></>,
    chart: <><rect x="3" y="14" width="4" height="7" rx="1"/><rect x="10" y="9" width="4" height="12" rx="1"/><rect x="17" y="3" width="4" height="18" rx="1"/></>,
    users: <><circle cx="9" cy="8" r="3"/><path d="M2 20v-2c0-4 14-4 14 0v2H2Z"/><circle cx="18" cy="8" r="2.5"/><path d="M18 15c3 0 4.5 2 4.5 4v1H19"/></>,
    list: <><path d="M8 5h13M8 12h13M8 19h13"/><circle cx="3.5" cy="5" r="1"/><circle cx="3.5" cy="12" r="1"/><circle cx="3.5" cy="19" r="1"/></>,
    check: <path d="m4 12 5 5 11-11"/>,
    arrow: <><path d="M3 12h17m-7-7 7 7-7 7"/></>,
    menu: <path d="M3 6h18M3 12h18M3 18h18"/>,
    sparkle: <><path d="m12 2 2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4L12 2Z"/></>,
  };
  return <svg {...common} width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>{content[name]}</svg>;
}
