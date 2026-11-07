import type { ReactNode } from 'react';
import { RouteLink } from '../app/RouteLink';
import type { Program } from '../data/demo';

type BoxProps = {
  title?: string;
  description?: string;
  tone?: 'white' | 'soft' | 'blue' | 'lime' | 'orange' | 'violet';
  className?: string;
  children?: ReactNode;
};

export function Surface({ title, description, children, tone = 'white', className = '' }: BoxProps) {
  return (
    <section className={`af-surface af-surface--${tone} ${className}`.trim()}>
      {(title || description) && (
        <header className="af-surface__header">
          {title && <h2>{title}</h2>}
          {description && <p>{description}</p>}
        </header>
      )}
      {children}
    </section>
  );
}

export function PageTitle({ kicker, title, description, action }: {
  kicker?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="af-page-heading">
      <div>
        {kicker && <div className="af-eyebrow">{kicker}</div>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action && <div className="af-page-heading__action">{action}</div>}
    </div>
  );
}

export function Pill({ children, tone = 'blue' }: { children: ReactNode; tone?: 'blue' | 'lime' | 'gray' | 'red' | 'purple' }) {
  return <span className={`af-pill af-pill--${tone}`}>{children}</span>;
}

export function Action({ to, children, variant = 'primary' }: {
  to: string;
  children: ReactNode;
  variant?: 'primary' | 'light' | 'lime' | 'outline';
}) {
  return <RouteLink className={`af-action af-action--${variant}`} to={to}>{children}</RouteLink>;
}

export function Metric({ label, value, hint, tone = 'white' }: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: 'white' | 'blue' | 'lime';
}) {
  return (
    <div className={`af-metric af-metric--${tone}`}>
      <span className="af-metric__label">{label}</span>
      <strong className="af-metric__value">{value}</strong>
      {hint && <span className="af-metric__hint">{hint}</span>}
    </div>
  );
}

export function ProbabilityBar({ value }: { value: number }) {
  return (
    <div className="af-probability" role="img" aria-label={`Оценка: ${value}%`}>
      <span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

export function ProgramCard({ item, onToggle, tracked = false }: {
  item: Program;
  tracked?: boolean;
  onToggle?: (id: string) => void;
}) {
  return (
    <article className="af-program-card">
      <div className={`af-program-card__logo af-program-card__logo--${item.color}`}>
        {item.university.slice(0, 2)}
      </div>
      <div className="af-program-card__main">
        <div className="af-program-card__university">{item.university} <span>· {item.city}</span></div>
        <h3>{item.program}</h3>
        <p>{item.code} · Бюджет · {item.budget} мест</p>
      </div>
      <div className="af-program-card__stats">
        <span>ОЦЕНКА ШАНСОВ</span>
        <strong>{item.chance}%</strong>
        <small>Проходной: {item.expected[0]}–{item.expected[1]}</small>
      </div>
      <div className="af-program-card__actions">
        <RouteLink to="/app/forecast/example" className="af-small-link">Прогноз ↗</RouteLink>
        {onToggle && <button className="af-track-button" type="button" onClick={() => onToggle(item.id)}>{tracked ? '✓ Сохранено' : '+ Следить'}</button>}
      </div>
    </article>
  );
}


export function EmptyMessage({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <Surface tone="soft" className="af-empty">
      <span className="af-empty__symbol" aria-hidden="true">◎</span>
      <h2>{title}</h2>
      <p>{description}</p>
      {action}
    </Surface>
  );
}
