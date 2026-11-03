import { useState } from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { Link } from 'react-router';
import { api } from '../lib/api';
import { limitCodePoints } from '../lib/direction';
import { SourceLookup } from '../components/SourceLookup';
import { SourceProvenance } from '../components/SourceProvenance';

const modes = { manual: 'Ручной режим', archive: 'Архив', automatic: 'Сбор данных', unsupported: 'Источник не подключён' };
export default function SourcesPage() {
  const [filters, setFilters] = useState({ q: '', universityId: '', branchId: '', year: '' });
  const [selected, setSelected] = useState<string | null>(null);
  const catalog = useInfiniteQuery({ queryKey: ['group-catalog', filters], queryFn: ({ pageParam, signal }) => api.groups(filters, pageParam, signal), initialPageParam: null as string | null, getNextPageParam: page => page.nextCursor ?? undefined });
  const universities = useQuery({ queryKey: ['universities', ''], queryFn: ({ signal }) => api.universities('', signal) });
  const items = [...new Map(catalog.data?.pages.flatMap(page => page.items).map(item => [item.id, item]) ?? []).values()];
  const facets = catalog.data?.pages[0].facets;
  return <main id="top" className="container tracker-page">
    <p className="eyebrow">Проверяемые источники</p><h1>Вузы и конкурсные группы</h1>
    <p className="section-description">Каталог и автоматический сбор — разные вещи. Архив сохраняет свой сезон. По данным источника не рассчитывается вероятность или гарантия зачисления.</p>
    <div className="source-catalog-filters surface">
      <label>Группа или направление<input value={filters.q} onChange={event => setFilters({ ...filters, q: limitCodePoints(event.target.value, 120) })} placeholder="Название или код направления" /></label>
      <label>Вуз<select aria-label="Вуз" value={filters.universityId} onChange={event => setFilters({ ...filters, universityId: event.target.value, branchId: '' })}><option value="">Все вузы каталога</option>{universities.data?.items.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Подразделение<select aria-label="Подразделение" value={filters.branchId} onChange={event => setFilters({ ...filters, branchId: event.target.value })}><option value="">Все подразделения</option><option value="main">Головной вуз</option>{facets?.branches.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Сезон<select aria-label="Сезон" value={filters.year} onChange={event => setFilters({ ...filters, year: event.target.value })}><option value="">Все сезоны</option>{facets?.years.map(year => <option key={year}>{year}</option>)}</select></label>
    </div>
    {catalog.isPending && <p role="status">Загружаем конкурсные группы…</p>}
    {catalog.isError && <div role="alert" className="surface source-catalog-card"><p>Не удалось загрузить группы.</p><button type="button" onClick={() => void catalog.refetch()}>Повторить загрузку групп</button></div>}
    {!catalog.isPending && items.length === 0 && <p className="notice">Подходящих подключённых групп пока нет. Направление можно сохранить вручную.</p>}
    <div className="source-catalog-list">{items.map(group => <article key={group.id} className="surface source-catalog-card">
      <span className="tag">{modes[group.coverage]} · {group.year}</span><h2>{group.title}</h2><p>{group.universityName}{group.parentUniversityId ? ' · филиал' : ' · головной вуз'}</p>
      <p>{group.studyForm === 'full-time' ? 'Очная форма' : group.studyForm} · {group.funding === 'budget' ? 'Бюджет' : group.funding === 'contract' ? 'Платное обучение' : group.funding} · {group.seats === null ? 'Число мест не подтверждено' : `${group.seats} мест в этой группе`}</p>
      {(group.dataKind === 'archive' || group.coverage === 'archive') && <p>Архив {group.year} года. Это не текущая приёмная кампания.</p>}
      {group.fetchedAt ? <p>Снимок получен: <time dateTime={group.fetchedAt}>{new Date(group.fetchedAt).toLocaleString('ru-RU')}</time>. Строк: {group.rowCount ?? 'не подтверждено'}.</p> : <p>Проверенный снимок ещё не получен.</p>}
      {group.sourceUpdatedAt === null && <p className="small-copy">Дата обновления самим источником не подтверждена.</p>}
      {['source_error', 'quarantined', 'disabled'].includes(group.sourceState ?? '') && <p role="status">Последняя проверка источника недоступна. Дата сохранённого снимка указана отдельно.</p>}
      <p className="small-copy">{group.scenarioAvailable ? 'После сохранения доступен условный сценарий по согласиям.' : 'Для этой группы числовой сценарий не подключён.'} Официальный результат зачисления не рассчитывается.</p>
      {group.lookupAvailable && <button id={`lookup-${group.id}`} className="button button-secondary" type="button" aria-expanded={selected === group.id} onClick={() => setSelected(group.id)}>Найти свою запись</button>}
      {selected === group.id && <SourceLookup key={group.id} group={group} onClose={() => { setSelected(null); requestAnimationFrame(() => document.getElementById(`lookup-${group.id}`)?.focus()); }} />}
      <SourceProvenance group={group} />
    </article>)}</div>
    {catalog.hasNextPage && <button type="button" className="button button-secondary" disabled={catalog.isFetchingNextPage} onClick={() => void catalog.fetchNextPage()}>{catalog.isFetchingNextPage ? 'Загружаем…' : 'Загрузить ещё группы'}</button>}
    <div className="direction-actions"><Link data-router-link className="button button-primary" to="/tracker">Сохранить направление вручную</Link><a className="button button-secondary" href="https://github.com/deylon999/admitflow/issues/new" target="_blank" rel="noopener noreferrer">Предложить источник на GitHub ↗</a></div>
    <p className="small-copy">Для предложения нужны официальный адрес, сезон, конкурсная группа и образец списка без персональных данных. Предложение не включает источник автоматически.</p>
  </main>;
}
