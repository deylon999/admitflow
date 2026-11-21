import { RouteLink } from '../../app/RouteLink';
import type { Program } from '../../data/demo';

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
        <span>ШАНСЫ · ДЕМО</span>
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
