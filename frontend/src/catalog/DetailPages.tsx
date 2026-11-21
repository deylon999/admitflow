import { Action, EmptyMessage, PageTitle, Pill, Surface } from '../shared/UI';
import { RouteLink } from '../app/RouteLink';
import { YearField } from './CatalogPages';
import { AccreditationNote, branchDescription, CatalogCard, ExamRequirementsView, formName, fundingName, MissingExams, Pagination, ResourceState, seatText, SourceNote, universityPath, universityTitle, unknown } from './parts';
import { useCatalog, useCatalogFilters } from './state';
import { program, programResults, university as decodeUniversity } from './decode';

export function UniversityPage({ id }: { id: string }) {
  const university = useCatalog(`universities/${encodeURIComponent(id)}`, decodeUniversity);
  const { params, update } = useCatalogFilters();
  const year = params.get('year') ?? '';
  const offset = Number(params.get('offset') ?? 0);
  const query = new URLSearchParams({ universityId: id, offset: String(offset) });
  if (year) query.set('year', year);
  const courses = useCatalog(`programs?${query}`, programResults);
  return <div className="af-catalog-detail">
    <ResourceState {...university}>
      {university.data && <>
        <div className={`af-profile-hero ${universityTitle(university.data).length > 16 ? 'af-profile-hero--long-name' : ''}`}>
          <div><span>{university.data.isBranch ? 'ФИЛИАЛ' : 'УНИВЕРСИТЕТ'} · {university.data.region.toUpperCase()}</span><h1>{universityTitle(university.data)}</h1><p>{university.data.legalName}</p>
            {university.data.isBranch && <p>{branchDescription(university.data)}</p>}
            <Action to={`/programs?universityId=${encodeURIComponent(id)}`} variant="lime">Программы университета ↗</Action>
          </div>
          <div className="af-profile-hero__circle">{universityTitle(university.data).slice(0, 1)}</div>
        </div>
        <div className="af-grid-metrics">
          <Surface tone="lime"><strong className="af-big-number">{university.data.knownProgramCount}</strong><p>Подтверждено программ</p></Surface>
          <Surface><strong className="af-big-number">{university.data.years.join(', ') || unknown}</strong><p>Приёмная кампания</p></Surface>
          <Surface><strong className="af-big-number">{university.data.provenance.edition ?? 'Реестр'}</strong><p>{university.data.provenance.kind === 'accreditation' ? 'Источник записи' : 'Редакция справочника'}</p></Surface>
        </div>
        <SourceNote source={university.data.provenance} />
        {university.data.displayNameSource && <p className="af-caption af-catalog-source af-university-name-source">
          <a href={university.data.displayNameSource.url} target="_blank" rel="noreferrer">{({ official: 'Официальное краткое наименование', normalized: 'Название без юридической формы', manual: 'Проверенное название', original: 'Исходное наименование' })[university.data.displayNameSource.kind]} ↗</a>
          {' · '}Проверено: <time dateTime={university.data.displayNameSource.verifiedAt}>{new Intl.DateTimeFormat('ru-RU', { timeZone: 'UTC' }).format(new Date(university.data.displayNameSource.verifiedAt))}</time>
        </p>}
        {university.data.branchInfo && <p className="af-caption af-catalog-source"><a href={university.data.branchInfo.url} target="_blank" rel="noreferrer">Сведения о филиале ↗</a>{' · '}Проверено: <time dateTime={university.data.branchInfo.verifiedAt}>{new Intl.DateTimeFormat('ru-RU', { timeZone: 'UTC' }).format(new Date(university.data.branchInfo.verifiedAt))}</time></p>}
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
  const resource = useCatalog(`programs/${encodeURIComponent(id)}`, program);
  const item = resource.data;
  const form = formName(item?.studyForm ?? null);
  const archive = item?.provenance.kind === 'archive';
  return <div className="af-catalog-detail">
    <ResourceState {...resource}>
      {item && <>
        <PageTitle kicker={`${item.universityName} / ${item.code ?? unknown} / ${item.year}`} title={item.title}
          description={`${item.region} · ${form === unknown ? form : `${form} форма`} · ${fundingName(item.funding)} · ${seatText(item.seats)}`}
          action={<Action to={universityPath(item.universityId)}>Университет ↗</Action>} />
        <div className="af-split-grid">
          <Surface tone="blue" className="af-spotlight">
            <span className="af-eyebrow">ПРОГНОЗ ПРОХОДНОГО</span>
            <strong className="af-catalog-unknown">{unknown}</strong>
            <p>Проверенная прогнозная модель для этой кампании пока не подключена.</p>
          </Surface>
          <Surface title="Параметры приёма">
            <div className="af-info-row"><span>Исторический проходной</span><b>{unknown}</b></div>
            <div className="af-info-row"><span>{item.funding === 'budget' ? 'Бюджетных мест' : fundingName(item.funding) === 'Платное' ? 'Мест по договору' : 'Мест'}</span><b>{item.seats ?? unknown}</b></div>
            <div className="af-info-row"><span>Форма обучения</span><b>{form}</b></div>
            <div className="af-info-row"><span>Конкурс</span><b>{item.category === 'general' ? 'Общий' : unknown}</b></div>
            <div className="af-info-row"><span>Приёмная кампания</span><b>{item.year}{archive ? ' · Архив' : ''}</b></div>
            {!archive && item.competitionGroups.map(group => <div className="af-info-row" key={group.id}>
              <span>{group.title}</span><b>{formName(group.studyForm)} · {fundingName(group.funding)} · {seatText(group.seats)}</b>
            </div>)}
          </Surface>
        </div>
        <div className="af-section-heading"><h2>Какие экзамены учитывать</h2></div>
        {item.examRequirements ? <ExamRequirementsView exams={item.examRequirements} /> : <div className="af-card-grid-3"><MissingExams /></div>}
        <Surface title="Источник данных">
          <SourceNote source={item.provenance} />
          {archive && <p>Количество мест относится к указанному конкурсу и архивной кампании {item.year} года.</p>}
          <RouteLink className="af-small-link" to={universityPath(item.universityId)}>Все программы университета ↗</RouteLink>
        </Surface>
      </>}
    </ResourceState>
  </div>;
}
