import type { ReactNode } from 'react';

export function SectionHeader({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return <div className="af-section-heading"><h2>{children}</h2>{action}</div>;
}
