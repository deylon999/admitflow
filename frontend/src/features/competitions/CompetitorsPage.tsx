import { ResourceState } from '../../shared/ResourceState';
import { Action, PageTitle, Surface } from '../../shared/UI';
import { unknown } from './format';
import { useCompetitionSummary } from './resources';
import { Warnings } from './Warnings';

export function CompetitorsPage({ id }: { id: string }) {
  const { info, summary } = useCompetitionSummary(id);
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
