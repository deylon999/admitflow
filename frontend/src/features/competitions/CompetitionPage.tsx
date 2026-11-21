import { ResourceState } from '../../shared/ResourceState';
import { Action, EmptyMessage, Metric, PageTitle, Pill, Surface } from '../../shared/UI';
import { consentName, day, participationName, unknown } from './format';
import { useCompetitionRows } from './resources';
import { Warnings } from './Warnings';

const FILTERS = [['', 'Все'], ['yes', 'Согласие есть'], ['no', 'Без согласия'], ['unknown', 'Согласие неизвестно']] as const;

export function CompetitionPage({ id }: { id: string }) {
  const { info, consent, priority, offset, rankFrom, update, rows } = useCompetitionRows(id);
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
