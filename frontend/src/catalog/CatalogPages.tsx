import { EmptyMessage, PageTitle, Pill } from '../shared/UI';
import { CatalogCard, Pagination, ResourceState } from './parts';
import { useCatalog, useCatalogFilters, useDebounced } from './state';
import type { ProgramResults, UniversityResults } from './types';

export function SortField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <label className="af-field"><span>СОРТИРОВКА</span><select value={value} onChange={e => onChange(e.target.value)}>
    <option value="name">По названию А–Я</option><option value="name-desc">По названию Я–А</option>
  </select></label>;
}

export function YearField({ value, years, onChange }: { value: string; years: number[]; onChange: (value: string) => void }) {
  const options = [...new Set([...years.map(String), ...(value ? [value] : [])])].sort().reverse();
  return <label className="af-field"><span>ГОД ПОСТУПЛЕНИЯ</span><select value={value} onChange={e => onChange(e.target.value)}>
    <option value="">Все годы</option>{options.map(year => <option key={year}>{year}</option>)}
  </select></label>;
}

export function UniversityCatalog() {
  const { params, update } = useCatalogFilters();
  const search = params.get('q') ?? '';
  const region = params.get('region') ?? '';
  const sort = params.get('sort') ?? 'name';
  const offset = Number(params.get('offset') ?? 0);
  const query = new URLSearchParams({ q: search, region, sort, offset: String(offset) });
  const requestKey = useDebounced(query.toString());
  const resource = useCatalog<UniversityResults>(`universities?${requestKey}`);
  return <>
    <PageTitle kicker="КАТАЛОГ ВУЗОВ" title="Найди место, где тебе понравится учиться." description="Вузы и подтверждённые конкурсные программы — на одном экране." />
    <div className="af-search-panel af-catalog-controls">
      <label className="af-field af-field--grow"><span>НАЙТИ ВУЗ ИЛИ НАПРАВЛЕНИЕ</span>
        <input value={search} maxLength={120} onChange={e => update('q', e.target.value)} placeholder="Например, программная инженерия" />
      </label>
      <label className="af-field"><span>РЕГИОН</span><select aria-label="РЕГИОН" value={region} onChange={e => update('region', e.target.value)}>
        <option value="">Все регионы</option>
        {(resource.data?.regions ?? (region ? [region] : [])).map(name => <option key={name}>{name}</option>)}
      </select></label>
      <SortField value={sort} onChange={value => update('sort', value)} />
    </div>
    <ResourceState {...resource} loading={resource.loading || requestKey !== query.toString()}>
      {resource.data && <>
        <div className="af-section-heading"><h2>Университеты по твоему запросу</h2><Pill tone="lime">{resource.data.total} вузов</Pill></div>
        {resource.data.items.length ? <div className="af-program-grid">{resource.data.items.map(item => <CatalogCard key={item.id} university={item} />)}</div>
          : <EmptyMessage title="Ничего не нашлось" description="Измени поисковый запрос или выбери другой регион." />}
        <Pagination page={resource.data} offset={offset} onOffset={value => update('offset', String(value))} />
      </>}
    </ResourceState>
  </>;
}

export function ProgramsCatalog() {
  const { params, update } = useCatalogFilters();
  const query = params.get('q') ?? '';
  const subject = params.get('subject') ?? '';
  const year = params.get('year') ?? '';
  const sort = params.get('sort') ?? 'name';
  const offset = Number(params.get('offset') ?? 0);
  const request = new URLSearchParams({ q: query, subject, sort, offset: String(offset) });
  if (year) request.set('year', year);
  const universityId = params.get('universityId');
  if (universityId) request.set('universityId', universityId);
  const requestKey = useDebounced(request.toString());
  const resource = useCatalog<ProgramResults>(`programs?${requestKey}`);
  return <>
    <PageTitle kicker="ПОДБОР ПРОГРАММ" title="Направление сначала. Вуз — следом." description="Выбирай специальность и проверяй параметры приёма." />
    <div className="af-search-panel af-catalog-controls">
      <label className="af-field af-field--grow"><span>НАПРАВЛЕНИЕ</span><input placeholder="Поиск по названию или коду" maxLength={120} value={query} onChange={e => update('q', e.target.value)} /></label>
      <label className="af-field"><span>ПРЕДМЕТ</span><select value={subject} onChange={e => update('subject', e.target.value)}>
        <option value="">Все предметы</option>{[...new Set([...(resource.data?.subjects ?? []), ...(subject ? [subject] : [])])].map(name => <option key={name}>{name}</option>)}
      </select></label>
      <YearField value={year} years={resource.data?.years ?? []} onChange={value => update('year', value)} />
      <SortField value={sort} onChange={value => update('sort', value)} />
    </div>
    <ResourceState {...resource} loading={resource.loading || requestKey !== request.toString()}>
      {resource.data && <>
        <div className="af-program-grid">{resource.data.items.map(item => <CatalogCard program={item} key={item.id} />)}</div>
        {!resource.data.items.length && <EmptyMessage title="Ничего не нашлось" description="Подтверждённых программ по выбранным условиям пока нет." />}
        <Pagination page={resource.data} offset={offset} onOffset={value => update('offset', String(value))} />
      </>}
    </ResourceState>
  </>;
}
