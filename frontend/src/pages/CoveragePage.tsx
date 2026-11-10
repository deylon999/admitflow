import { useState } from 'react';
import { nationalCoverage, type CoverageLayer, type NationalCoverage } from '../shared/dto';
import { useResource } from '../shared/resource';
import { ResourceState } from '../shared/ResourceState';
import { PageTitle, Pill, Surface } from '../shared/UI';
import { RouteLink } from '../app/RouteLink';

const percent = (value: number | null) => value === null ? 'Нет данных' : `${(value * 100).toFixed(1).replace('.', ',')}%`;
const day = (iso: string) => new Intl.DateTimeFormat('ru-RU', { timeZone: 'UTC' }).format(new Date(iso));
const stateName: Record<string, string> = {
  fresh: 'Свежие', archived: 'Архив', stale: 'Устарели', source_error: 'Ошибка источника', quarantined: 'Карантин',
  never_checked: 'Не проверялись', disabled: 'Отключены', unsupported: 'Без адаптера', unknown: 'Неизвестно',
};

function LayerCard({ layer, target }: { layer: CoverageLayer; target: number }) {
  const width = Math.round((layer.share ?? 0) * 1000) / 10;
  return <Surface className="af-coverage-layer">
    <div className="af-coverage-layer__head">
      <h3>{layer.title}</h3>
      <Pill tone={layer.targetMet ? 'lime' : 'gray'}>{layer.targetMet ? 'Порог достигнут' : 'Ниже порога'}</Pill>
    </div>
    <strong className="af-big-number">{percent(layer.share)}</strong>
    <p className="af-coverage-layer__count">{layer.covered} из {layer.total} головных вузов</p>
    <div className="af-coverage-bar" role="img" aria-label={`${percent(layer.share)} при пороге ${percent(target)}`}>
      <span style={{ width: `${width}%` }} />
      <i style={{ left: `${target * 100}%` }} />
    </div>
    <p className="af-caption">{layer.note}</p>
  </Surface>;
}

function download(report: NationalCoverage) {
  const blob = new Blob([JSON.stringify(report, null, 2) + '\n'], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `admitflow-coverage-${report.generatedAt.slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

export function CoveragePage() {
  const r = useResource('coverage/national', nationalCoverage);
  const [allRegions, setAllRegions] = useState(false);
  const report = r.data;
  return <>
    <PageTitle kicker="ОПЕРАТОР · ПОКРЫТИЕ РФ" title="Покрытие вузов России"
      description="Каждый слой считается отдельно от одного знаменателя. Наличие вуза в справочнике не означает, что собраны его программы, требования ЕГЭ или списки."
      action={report && <button type="button" className="af-action af-action--outline" onClick={() => download(report)}>Скачать отчёт JSON</button>} />
    <ResourceState {...r} hasData={!!report}>
      {report && <>
        <Surface tone="soft" title="Знаменатель" className="af-coverage-denominator">
          <p><b>{report.denominator.total}</b> головных организаций с действующей аккредитацией бакалавриата или специалитета: гражданских {report.denominator.civil}, ведомственных {report.denominator.departmental}. Зарубежные ({report.denominator.abroadExcluded}) не входят.</p>
          <p className="af-caption">{report.denominator.rule} <a href={report.denominator.sourceUrl} target="_blank" rel="noreferrer">Реестр Рособрнадзора ↗</a> · данные на <time dateTime={report.denominator.datasetDate}>{day(report.denominator.datasetDate)}</time> · порог {percent(report.target)}</p>
        </Surface>
        <div className="af-coverage-layers">{report.layers.map(layer => <LayerCard key={layer.id} layer={layer} target={report.target} />)}</div>
        <div className="af-split-grid">
          <Surface title="По годам кампании">
            {report.byYear.length ? report.byYear.map(row => <div className="af-info-row" key={row.year}><span>{row.year}</span><b>программы у {row.programs} · ЕГЭ у {row.examRequirements}</b></div>)
              : <p>Проверенных программ нет ни за один год.</p>}
          </Surface>
          <Surface title="Пробелы">
            <div className="af-info-row"><span>Головных вузов без программ</span><b>{report.gaps.headsWithoutPrograms}</b></div>
            <div className="af-info-row"><span>Записей каталога без сопоставления с реестром</span><b>{report.gaps.unmatchedCatalogHeads}</b></div>
            <div className="af-info-row"><span>Неоднозначных сопоставлений</span><b>{report.gaps.ambiguousCatalogHeads}</b></div>
            <div className="af-info-row"><span>Только в реестре, не в мониторинге</span><b>{report.gaps.registryOnly}</b></div>
            <div className="af-info-row"><span>Программ филиалов, не засчитанных головным вузам</span><b>{report.gaps.branchProgramsNotCounted}</b></div>
          </Surface>
        </div>
        <div className="af-split-grid">
          <Surface title="Источники списков">
            <div className="af-info-row"><span>Конкурсов с импортированным списком</span><b>{report.lists.groups}</b></div>
            <div className="af-info-row"><span>Из них свежих</span><b>{report.lists.freshGroups}</b></div>
            <div className="af-info-row"><span>Из них архивных</span><b>{report.lists.archiveGroups}</b></div>
            {Object.entries(report.sources.byState).map(([state, n]) => <div className="af-info-row" key={state}><span>{stateName[state] ?? state}</span><b>{n}</b></div>)}
            {report.sources.problems.length > 0 && <div className="af-coverage-problems" role="alert">
              <b>Требуют внимания</b>
              {report.sources.problems.map(p => <p key={p.sourceId}>{p.university} · {p.group} — {stateName[p.state] ?? p.state} ({p.domain})</p>)}
            </div>}
          </Surface>
          <Surface title="Очередь обновления">
            <div className="af-info-row"><span>Состояние</span><b>{report.operations.status === 'ok' ? 'В норме' : 'Есть проблемы'}</b></div>
            <div className="af-info-row"><span>Worker</span><b>{({ alive: 'Работает', stale: 'Нет сигнала', never_seen: 'Не запускался' } as Record<string, string>)[report.operations.worker.state] ?? report.operations.worker.state}</b></div>
            <div className="af-info-row"><span>Просроченных заданий</span><b>{report.operations.jobs.overdue}</b></div>
            {Object.entries(report.operations.jobs.byState).map(([state, n]) => <div className="af-info-row" key={state}><span>Заданий: {state}</span><b>{n}</b></div>)}
          </Surface>
        </div>
        <Surface title="Регионы">
          <div className="af-table-scroll"><table className="af-table af-coverage-regions"><thead><tr><th>Регион</th><th>Вузов</th><th>В каталоге</th><th>С программами</th><th>Со списками</th></tr></thead>
            <tbody>{(allRegions ? report.regions : report.regions.slice(0, 15)).map(row => <tr key={row.region}><td>{row.region}</td><td>{row.total}</td><td>{row.catalog}</td><td>{row.programs}</td><td>{row.lists}</td></tr>)}</tbody></table></div>
          {report.regions.length > 15 && <button type="button" className="af-action af-action--outline" onClick={() => setAllRegions(v => !v)}>{allRegions ? 'Свернуть' : `Все регионы (${report.regions.length})`}</button>}
        </Surface>
        <p className="af-caption">Отчёт сформирован <time dateTime={report.generatedAt}>{new Date(report.generatedAt).toLocaleString('ru-RU')}</time>. Контрольная сумма входных данных <code>{report.inputs.checksum.slice(0, 12)}</code>. Тот же отчёт: <code>python -m app.national_coverage --output report.json</code>. <RouteLink to="/app/sources">Источники ↗</RouteLink></p>
      </>}
    </ResourceState>
  </>;
}
