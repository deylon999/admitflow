import { useState } from 'react';
import { Action, Metric, PageTitle, Pill, Surface } from '../../shared/UI';
import { applicantRows } from '../../data/demo';

export function CompetitionList() {
  const [filter, setFilter] = useState('Все');
  const [search, setSearch] = useState('');
  const rows = applicantRows.filter(row => (filter === 'Все' || (filter === 'Ваше заявление' ? row.id === 'ВЫ' : row.status === 'Есть подтверждение')) && row.id.toLowerCase().includes(search.toLowerCase()));
  return (
    <>
      <PageTitle kicker="КОНКУРСНЫЕ СПИСКИ" title="Видишь не только своё место." description="МТУСИ · Программная инженерия · Общий конкурс · Демо" action={<Action to="/app/competitions/mtuci-se/competitors" variant="outline">Анализ конкурентов ↗</Action>} />
      <div className="af-grid-metrics">
        <Metric label="Твоя позиция" value="90" hint="сейчас в списке" tone="lime" />
        <Metric label="Бюджетных мест" value="90" hint="условный сценарий" />
        <Metric label="Участников" value="128" hint="в опубликованной модели" />
        <Metric label="Обновлено" value="11:20" hint="время обновления" />
      </div>
      <Surface title="Участники конкурса">
        <div className="af-table-toolbar">
          <div className="af-tabs">{['Все', 'Ваше заявление', 'Есть подтверждение'].map(tab => <button type="button" className={tab === filter ? 'is-active' : ''} key={tab} onClick={() => setFilter(tab)}>{tab}</button>)}</div>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Найти код" aria-label="Поиск кода абитуриента" />
        </div>
        <div className="af-table-scroll"><table className="af-table"><thead><tr><th>№</th><th>Код поступающего</th><th>Баллы</th><th>Приоритет</th><th>Статус</th></tr></thead><tbody>{rows.map(row => <tr key={row.position} className={row.id === 'ВЫ' ? 'is-me' : ''}><td>{row.position}</td><td>{row.id}</td><td>{row.score}</td><td>{row.priority}</td><td><Pill tone={row.id === 'ВЫ' ? 'blue' : 'gray'}>{row.status}</Pill></td></tr>)}</tbody></table></div>
        <p className="af-caption">Список и статусы в этом интерфейсе вымышлены. Участие в конкурсе не означает окончательный выбор вуза.</p>
      </Surface>
    </>
  );
}

export function Competitors() {
  return (
    <>
      <PageTitle kicker="АНАЛИЗ КОНКУРЕНЦИИ" title="Кто выше — и что действительно известно." description="Прогноз не должен автоматически удалять людей из конкурса из-за отсутствия согласия." />
      <div className="af-split-grid">
        <Surface tone="blue" className="af-spotlight"><span className="af-eyebrow">ПОЗИЦИЙ ВЫШЕ</span><strong>89</strong><p>Условный срез конкурсного списка.</p></Surface>
        <Surface title="Почему это не 89 гарантированных конкурентов">
          <div className="af-info-row"><span>Опубликованные приоритеты</span><b>Частично</b></div>
          <div className="af-info-row"><span>Сведения из других вузов</span><b>Ограниченно</b></div>
          <div className="af-info-row"><span>Поведение людей</span><b>Неизвестно</b></div>
          <div className="af-info-row"><span>Итоговое зачисление</span><b>Не наступило</b></div>
        </Surface>
      </div>
      <div className="af-card-grid-3">
        <Surface tone="lime"><h3>Приоритеты</h3><p>Публичный приоритет — полезный сигнал, но не гарантия выбора.</p></Surface>
        <Surface tone="soft"><h3>Подтверждения</h3><p>Статусы могут измениться до контрольного времени.</p></Surface>
        <Surface tone="orange"><h3>Другие заявления</h3><p>Показываем только законно доступные данные, без персональных досье.</p></Surface>
      </div>
      <Action to="/app/competitions/mtuci-se">Вернуться к списку ↗</Action>
    </>
  );
}
