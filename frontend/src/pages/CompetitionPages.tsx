import { competition, competitionGroups, competitionRows, competitionSummary } from '../shared/dto';
import { useResource } from '../shared/resource';
import { ResourceState } from '../shared/ResourceState';
import { Action, EmptyMessage, Metric, PageTitle, Pill, Surface } from '../shared/UI';
import { RouteLink } from '../app/RouteLink';
import { useCatalogFilters } from '../catalog/state';

const day = (iso: string) => new Intl.DateTimeFormat('ru-RU', { timeZone: 'Europe/Moscow', dateStyle: 'short', timeStyle: 'short' }).format(new Date(iso));
const unknown = 'Нет данных';
const warningText: Record<string, string> = {
  archive: 'Архивный список прошлой кампании, не текущая ситуация.',
  incomplete_list: 'Список неполный: позиции могут быть неточными.',
  priorities_not_published: 'Источник не публикует приоритеты, поэтому они не показаны и не учитываются.',
  consent_unknown_rows: 'У части строк неизвестно согласие на зачисление.',
  rules_not_modelled: 'Для этого типа конкурса правила согласий и мест не моделируются: только факты списка.',
  seats_unknown: 'Источник не указал число мест.',
  source_stale: 'Источник давно не обновлялся.',
  source_source_error: 'Последняя загрузка источника завершилась ошибкой; показан последний корректный снимок.',
  source_quarantined: 'Новый снимок источника отклонён проверкой; показан последний корректный.',
};
const consentName = (value: boolean | null) => value === null ? unknown : value ? 'Есть' : 'Нет';
const participationName: Record<string, string> = { unknown: unknown, active: 'Участвует', withdrawn: 'Отозвал', enrolled: 'Зачислен' };

function Warnings({ codes }: { codes: string[] }) {
  if (!codes.length) return null;
  return <Surface tone="soft" title="Что важно знать об этом списке" className="af-competition-warnings">
    <ul>{codes.map(code => <li key={code}>{warningText[code] ?? code}</li>)}</ul>
  </Surface>;
}

export function CompetitionsIndex() {
  const { params, update } = useCatalogFilters();
  const cursor = params.get('after') ?? '';
  const r = useResource('groups?' + new URLSearchParams({ limit: '50', after: cursor }), competitionGroups);
  const lists = r.data?.items.filter(g => g.coverage === 'archive' || g.coverage === 'automatic') ?? [];
  return <>
    <PageTitle kicker="КОНКУРСНЫЕ СПИСКИ" title="Импортированные конкурсные списки"
      description="Официальный порядок списка без кодов поступающих. Свою строку видно после подтверждения записи в «Мои направления»."
      action={<Action to="/app/watchlist" variant="outline">Мои направления ↗</Action>} />
    <ResourceState {...r} hasData={!!r.data}>
      {r.data && (lists.length ? <div className="af-program-grid">{lists.map(g => <article className="af-program-card af-catalog-card" key={g.id}>
        <div className="af-program-card__logo af-program-card__logo--blue">{g.universityName.slice(0, 2)}</div>
        <div className="af-program-card__main">
          <div className="af-program-card__university">{g.universityName}</div>
          <h3><RouteLink to={`/app/competitions/${encodeURIComponent(g.id)}`}>{g.title}</RouteLink></h3>
          <p>{g.year} · {g.coverage === 'archive' ? 'Архив' : 'Автоматическое обновление'} · Мест: {g.seats ?? unknown}</p>
        </div>
        <div className="af-program-card__actions"><RouteLink to={`/app/competitions/${encodeURIComponent(g.id)}`} className="af-small-link">Список ↗</RouteLink></div>
      </article>)}</div> : <EmptyMessage title="На этой странице списков нет" description="Здесь нет импортированных списков. Проверьте следующую страницу, если она доступна." />)}
      {r.data && <nav className="af-catalog-pagination" aria-label="Страницы конкурсов">
        <button type="button" className="af-action af-action--outline" disabled={!cursor || r.loading} onClick={() => update('after', '')}>В начало</button>
        <button type="button" className="af-action af-action--outline" disabled={!r.data.nextCursor || r.loading} onClick={() => update('after', r.data!.nextCursor!)}>Далее</button>
      </nav>}
    </ResourceState>
  </>;
}

const FILTERS = [['', 'Все'], ['yes', 'Согласие есть'], ['no', 'Без согласия'], ['unknown', 'Согласие неизвестно']] as const;

export function CompetitionPage({ id }: { id: string }) {
  const base = `competitions/${encodeURIComponent(id)}`;
  const info = useResource(base, competition);
  const { params, update } = useCatalogFilters();
  const consent = params.get('consent') ?? '';
  const priority = params.get('priority') ?? '';
  const offset = Number(params.get('offset') ?? 0);
  const rankFrom = params.get('rankFrom') ?? '';
  const query = new URLSearchParams({ offset: String(offset) });
  if (consent) query.set('consent', consent);
  if (priority) query.set('priority', priority);
  if (rankFrom) query.set('rankFrom', rankFrom);
  const rows = useResource(`${base}/rows?${query}`, competitionRows);
  const data = info.data;
  return <ResourceState {...info} hasData={!!data}>
    {data && <>
      <PageTitle kicker={`КОНКУРСНЫЙ СПИСОК · ${data.year}`} title={data.title} description={`${data.universityName} · ${data.funding === 'budget' ? 'Бюджет' : data.funding === 'contract' ? 'Платное' : data.funding}`}
        action={<Action to={`/app/competitions/${encodeURIComponent(id)}/competitors`} variant="outline">Анализ конкуренции ↗</Action>} />
      <div className="af-grid-metrics">
        <Metric label="Ваша позиция" value={data.myRank ?? '—'} hint={data.myRank ? 'по официальному порядку' : 'подтвердите запись в «Мои направления»'} tone="lime" />
        <Metric label="Мест" value={data.snapshot.seats ?? unknown} hint="по данным источника" />
        <Metric label="Строк в списке" value={data.snapshot.rowCount} hint={data.snapshot.complete ? 'список полный' : 'список неполный'} />
        <Metric label="Снимок" value={day(data.snapshot.fetchedAt).split(',')[0]} hint={data.snapshot.kind === 'archive' ? 'архив' : 'загружен'} />
      </div>
      <Warnings codes={data.warnings} />
      <Surface title="Участники конкурса">
        <div className="af-table-toolbar">
          <div className="af-tabs">{FILTERS.map(([value, label]) => <button type="button" key={value} className={consent === value ? 'is-active' : ''} onClick={() => update('consent', value)}>{label}</button>)}</div>
          <div className="af-competition-controls">
            {data.prioritiesPublished && <select aria-label="Приоритет" value={priority} onChange={e => update('priority', e.target.value)}>
              <option value="">Любой приоритет</option><option value="first">Только приоритет 1</option><option value="known">Приоритет указан</option><option value="unknown">Приоритет не указан</option>
            </select>}
            <input inputMode="numeric" aria-label="Перейти к месту" placeholder="Перейти к месту" value={rankFrom} onChange={e => update('rankFrom', e.target.value.replace(/\D/g, '').slice(0, 6))} />
          </div>
        </div>
        <ResourceState {...rows} hasData={!!rows.data}>
          {rows.data && (rows.data.items.length ? <>
            <div className="af-table-scroll"><table className="af-table af-competition-table"><thead><tr><th>№</th><th>Баллы</th><th>Согласие</th>{data.prioritiesPublished && <th>Приоритет</th>}<th>Участие</th></tr></thead>
              <tbody>{rows.data.items.map(row => <tr key={row.officialRank} className={row.mine ? 'is-me' : ''}>
                <td>{row.officialRank}{row.mine && <Pill tone="lime">Вы</Pill>}</td><td>{row.score ?? unknown}</td><td>{consentName(row.consent)}</td>
                {data.prioritiesPublished && <td>{row.priority ?? unknown}</td>}<td>{participationName[row.participation] ?? row.participation}</td>
              </tr>)}</tbody></table></div>
            <nav className="af-catalog-pagination" aria-label="Страницы списка">
              <button type="button" className="af-action af-action--outline" disabled={offset === 0 || rows.loading} onClick={() => update('offset', String(Math.max(0, offset - 50)))}>Назад</button>
              <span aria-live="polite">{offset + 1}–{offset + rows.data.items.length} из {rows.data.total}</span>
              <button type="button" className="af-action af-action--outline" disabled={rows.data.nextOffset === null || rows.loading} onClick={() => update('offset', String(rows.data!.nextOffset!))}>Далее</button>
            </nav>
          </> : <EmptyMessage title="Нет строк" description="Под выбранные условия в этом снимке строк нет." />)}
        </ResourceState>
        <p className="af-caption">Порядок — официальный порядок источника: он уже учитывает равные баллы и дополнительные основания. Сортировки по баллам нет намеренно. Коды поступающих не показываются.</p>
      </Surface>
      <Surface title="Источник и обновления">
        {data.snapshot.sourceUrl && <p><a href={data.snapshot.sourceUrl} target="_blank" rel="noreferrer">Официальный список ↗</a></p>}
        <p>Снимок получен <time dateTime={data.snapshot.fetchedAt}>{day(data.snapshot.fetchedAt)}</time>{data.snapshot.sourceUpdatedAt && <>, источник обновлён <time dateTime={data.snapshot.sourceUpdatedAt}>{day(data.snapshot.sourceUpdatedAt)}</time></>}.</p>
        {data.history.map(h => <div className="af-info-row" key={h.id}><span>{day(h.fetchedAt)}{h.published ? ' · показан' : ''}</span><b>{h.rowCount} строк · мест {h.seats ?? unknown}</b></div>)}
      </Surface>
    </>}
  </ResourceState>;
}

export function CompetitorsPage({ id }: { id: string }) {
  const info = useResource(`competitions/${encodeURIComponent(id)}`, competition);
  const summary = useResource(`competitions/${encodeURIComponent(id)}/summary`, competitionSummary);
  const s = summary.data;
  const peak = s ? Math.max(1, ...s.scoreBins.map(b => b.count)) : 1;
  return <ResourceState {...info} hasData={!!info.data}><ResourceState {...summary} hasData={!!s}>
    {s && <>
      <PageTitle kicker="АНАЛИЗ КОНКУРЕНЦИИ" title={info.data ? info.data.title : 'Состав конкурса'}
        description="Только агрегаты выбранного снимка. Отсутствие согласия или строки не означает, что человек выбыл."
        action={<Action to={`/app/competitions/${encodeURIComponent(id)}`} variant="outline">К списку ↗</Action>} />
      <div className="af-split-grid">
        <Surface tone="blue" className="af-spotlight">
          <span className="af-eyebrow">{s.aboveMe ? 'СТРОК ВЫШЕ ВАС' : 'СТРОК В СПИСКЕ'}</span>
          <strong>{s.aboveMe ? s.aboveMe.total : s.total}</strong>
          <p>{s.aboveMe ? `Ваша позиция ${s.myRank}. Мест: ${s.seats ?? unknown}.` : 'Подтвердите свою запись, чтобы увидеть, кто выше.'}</p>
        </Surface>
        <Surface title={s.aboveMe ? 'Кто выше вас' : 'Весь список'}>
          {(s.aboveMe ? [['С согласием', s.aboveMe.consentYes], ['Без согласия', s.aboveMe.consentNo], ['Согласие неизвестно', s.aboveMe.consentUnknown], ['Отозвали заявление', s.aboveMe.withdrawn], ['Приоритет 1', s.aboveMe.priorityFirst]]
            : [['С согласием', s.byConsent.yes], ['Без согласия', s.byConsent.no], ['Согласие неизвестно', s.byConsent.unknown], ['Отозвали заявление', s.byParticipation.withdrawn ?? 0], ['Приоритет 1', s.priorityFirst]])
            .map(([label, value]) => <div className="af-info-row" key={label}><span>{label}</span><b>{value}</b></div>)}
          {s.priorityKnown === 0 && <p className="af-caption">Источник не публикует приоритеты.</p>}
        </Surface>
      </div>
      <Surface title="Распределение баллов" description={`Баллы известны у ${s.scoreKnown} из ${s.total} строк.`}>
        {s.scoreBins.length ? <div className="af-score-bins" role="img" aria-label="Число строк по диапазонам баллов">
          {s.scoreBins.map(b => <div key={b.lower}><span style={{ height: `${Math.round(b.count / peak * 100)}%` }} title={`${b.count}`} /><small>{b.lower}</small><b>{b.count}</b></div>)}
        </div> : <p>{unknown}</p>}
      </Surface>
      <Warnings codes={s.warnings} />
    </>}
  </ResourceState></ResourceState>;
}
