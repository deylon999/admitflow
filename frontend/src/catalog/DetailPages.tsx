import { Action, EmptyMessage, PageTitle, Pill, Surface } from '../shared/UI';
import { RouteLink } from '../app/RouteLink';
import { YearField } from './CatalogPages';
import { AccreditationNote, CatalogCard, ExamRequirementsView, formName, fundingName, MissingExams, Pagination, ResourceState, SourceNote, universityPath, unknown } from './parts';
import { useCatalog, useCatalogFilters } from './state';
import type { CatalogProgram, ProgramResults, University } from './types';

export function UniversityPage({ id }: { id: string }) {
  const university = useCatalog<University>(`universities/${encodeURIComponent(id)}`);
  const { params, update } = useCatalogFilters();
  const year = params.get('year') ?? '';
  const offset = Number(params.get('offset') ?? 0);
  const query = new URLSearchParams({ universityId: id, offset: String(offset) });
  if (year) query.set('year', year);
  const courses = useCatalog<ProgramResults>(`programs?${query}`);
  return <div className="af-catalog-detail">
    <ResourceState {...university}>
      {university.data && <>
        <div className={`af-profile-hero ${university.data.name.length > 16 ? 'af-profile-hero--long-name' : ''}`}>
          <div><span>УНИВЕРСИТЕТ · {university.data.region.toUpperCase()}</span><h1>{university.data.name}</h1><p>{university.data.legalName}</p>
            <Action to={`/programs?universityId=${encodeURIComponent(id)}`} variant="lime">Программы университета ↗</Action>
          </div>
          <div className="af-profile-hero__circle">{university.data.name.slice(0, 1)}</div>
        </div>
        <div className="af-grid-metrics">
          <Surface tone="lime"><strong className="af-big-number">{university.data.knownProgramCount}</strong><p>Подтверждено программ</p></Surface>
          <Surface><strong className="af-big-number">{university.data.years.join(', ') || unknown}</strong><p>Приёмная кампания</p></Surface>
          <Surface><strong className="af-big-number">{university.data.provenance.edition ?? 'Реестр'}</strong><p>{university.data.provenance.kind === 'accreditation' ? 'Источник записи' : 'Редакция справочника'}</p></Surface>
        </div>
        <SourceNote source={university.data.provenance} />
        <AccreditationNote university={university.data} />
        {university.data.officialUrl && <a className="af-small-link" href={university.data.officialUrl} target="_blank" rel="noreferrer">Официальный сайт ↗</a>}
        <div className="af-section-heading"><h2>Программы университета</h2><Pill tone="blue">{courses.data?.total ?? '…'} направления</Pill></div>
        <div className="af-search-panel"><YearField value={year} years={university.data.years} onChange={value => update('year', value)} /></div>
        <ResourceState {...courses}>
          {courses.data && <>
            {courses.data.items.length ? <div className="af-program-grid">{courses.data.items.map(program => <CatalogCard key={program.id} program={program} />)}</div>
              : <EmptyMessage title="Нет данных" description="Подтверждённые программы выбранной кампании ещё не добавлены." />}
            <Pagination page={courses.data} offset={offset} onOffset={value => update('offset', String(value))} />
          </>}
        </ResourceState>
      </>}
    </ResourceState>
  </div>;
}

export function ProgramDetail({ id }: { id: string }) {
  const resource = useCatalog<CatalogProgram>(`programs/${encodeURIComponent(id)}`);
  const item = resource.data;
  return <div className="af-catalog-detail">
    <ResourceState {...resource}>
      {item && <>
        <PageTitle kicker={`${item.universityName} / ${item.code ?? unknown} / ${item.year}`} title={item.title}
          description={`${item.region} · ${formName(item.studyForm)} форма · ${fundingName(item.funding)} · ${item.seats ?? unknown} мест`}
          action={<Action to={universityPath(item.universityId)}>Университет ↗</Action>} />
        <div className="af-split-grid">
          <Surface tone="blue" className="af-spotlight">
            <span className="af-eyebrow">ПРОГНОЗ ПРОХОДНОГО</span>
            <strong className="af-catalog-unknown">{unknown}</strong>
            <p>Проверенная прогнозная модель для этой кампании пока не подключена.</p>
          </Surface>
          <Surface title="Параметры приёма">
            <div className="af-info-row"><span>Исторический проходной</span><b>{unknown}</b></div>
            <div className="af-info-row"><span>{item.funding === 'budget' ? 'Бюджетных мест' : 'Мест по договору'}</span><b>{item.seats ?? unknown}</b></div>
            <div className="af-info-row"><span>Форма обучения</span><b>{formName(item.studyForm)}</b></div>
            <div className="af-info-row"><span>Конкурс</span><b>{item.category === 'general' ? 'Общий' : unknown}</b></div>
            <div className="af-info-row"><span>Приёмная кампания</span><b>{item.year} · Архив</b></div>
          </Surface>
        </div>
        <div className="af-section-heading"><h2>Какие экзамены учитывать</h2></div>
        {item.examRequirements ? <ExamRequirementsView exams={item.examRequirements} /> : <div className="af-card-grid-3"><MissingExams /></div>}
        <Surface title="Источник данных">
          <SourceNote source={item.provenance} />
          <p>Количество мест относится к указанному конкурсу и архивной кампании {item.year} года.</p>
          <RouteLink className="af-small-link" to={universityPath(item.universityId)}>Все программы университета ↗</RouteLink>
        </Surface>
      </>}
    </ResourceState>
  </div>;
}
