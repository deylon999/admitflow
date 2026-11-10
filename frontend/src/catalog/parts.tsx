import { RouteLink } from '../app/RouteLink';
import { Surface } from '../shared/UI';
import type { CatalogPage, CatalogProgram, Provenance, University } from './types';

export const unknown = 'Нет данных';
export const formName = (value: string) => ({ 'full-time': 'Очная', 'part-time': 'Очно-заочная', mixed: 'Смешанная' }[value] ?? unknown);
export const fundingName = (value: string) => ({ budget: 'Бюджет', contract: 'Платное' }[value] ?? unknown);
export const universityPath = (id: string) => `/universities/${encodeURIComponent(id)}`;
export const programPath = (id: string) => `/programs/${encodeURIComponent(id)}`;

export function SourceNote({ source }: { source: Provenance }) {
  const date = new Intl.DateTimeFormat('ru-RU', { timeZone: 'UTC' }).format(new Date(source.verifiedAt));
  return <p className="af-caption af-catalog-source">
    <a href={source.url} target="_blank" rel="noreferrer">Источник ↗</a>
    {' · '}{source.kind === 'archive' ? 'Архив' : `Мониторинг ${source.edition}`}
    {' · '}Проверено: <time dateTime={source.verifiedAt}>{date}</time>
  </p>;
}

export { ResourceState } from '../shared/ResourceState';

export function CatalogCard({ university, program }: { university?: University; program?: CatalogProgram }) {
  const name = program?.universityName ?? university?.name ?? '';
  const href = program ? programPath(program.id) : universityPath(university!.id);
  return <article className="af-program-card af-catalog-card">
    <div className="af-program-card__logo af-program-card__logo--blue">{name.slice(0, 2)}</div>
    <div className="af-program-card__main">
      <div className="af-program-card__university">
        {program ? <RouteLink to={universityPath(program.universityId)}>{name}</RouteLink> : 'Университет'}
        <span> · {program?.region ?? university?.region}</span>
      </div>
      <h3><RouteLink to={href}>{program?.title ?? name}</RouteLink></h3>
      <p>{program ? `${program.code ?? unknown} · ${fundingName(program.funding)} · ${program.seats ?? unknown} мест` : university?.isBranch ? 'Филиал' : 'Образовательная организация'}</p>
    </div>
    <div className="af-program-card__stats">
      <span>{program ? 'КАМПАНИЯ' : 'РЕДАКЦИЯ'}</span>
      <strong>{program?.year ?? university?.provenance.edition}</strong>
      <small>{program ? formName(program.studyForm) : 'Мониторинг'}</small>
    </div>
    <div className="af-program-card__actions">
      <RouteLink to={href} className="af-small-link">{program ? 'Направление ↗' : 'Университет ↗'}</RouteLink>
    </div>
  </article>;
}

export function Pagination({ page, offset, onOffset }: {
  page: CatalogPage<unknown>; offset: number; onOffset: (value: number) => void;
}) {
  if (page.total <= 12 && offset === 0) return null;
  return <nav className="af-catalog-pagination" aria-label="Страницы каталога">
    <button type="button" className="af-action af-action--outline" disabled={offset === 0} onClick={() => onOffset(Math.max(0, offset - 12))}>Назад</button>
    <span aria-live="polite">{Math.min(offset + 1, page.total)}–{Math.min(offset + page.items.length, page.total)} из {page.total}</span>
    <button type="button" className="af-action af-action--outline" disabled={page.nextOffset === null} onClick={() => onOffset(page.nextOffset!)}>Далее</button>
  </nav>;
}

export function MissingExams() {
  return <Surface tone="soft"><h3>{unknown}</h3><p>Подтверждённые требования ЕГЭ для этой кампании ещё не добавлены.</p></Surface>;
}
