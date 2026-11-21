import { useState } from 'react';
import { EmptyMessage, PageTitle } from '../../shared/UI';
import { programs } from '../../data/demo';

export function Compare() {
  const [selected, setSelected] = useState<string[]>(programs.slice(0, 3).map(item => item.id));
  const list = programs.filter(p => selected.includes(p.id));
  function toggle(id: string) { setSelected(p => p.includes(id) ? p.filter(x => x !== id) : p.length < 4 ? [...p, id] : p); }
  return (
    <>
      <PageTitle kicker="СРАВНЕНИЕ" title="Куда лучше подавать документы?" description="Сравнивай несколько направлений по проходным, местам и условному прогнозу." />
      <div className="af-choice-row">{programs.map(p => <label key={p.id}><input type="checkbox" checked={selected.includes(p.id)} onChange={() => toggle(p.id)} />{p.university}</label>)}</div>
      {list.length ? <div className="af-compare-scroll"><div className="af-compare-grid">
        <div className="af-compare-labels"><b>Университет</b><b>Направление</b><b>Оценка шанса</b><b>Прогноз проходного</b><b>Мест</b><b>Прошлогодний</b><b>Город</b></div>
        {list.map(item => <div key={item.id} className={`af-compare-col ${item.chance > 85 ? 'is-highlighted' : ''}`}><strong>{item.university}</strong><span>{item.program}</span><b className="af-compare-chance">{item.chance}%</b><b>{item.expected[0]}–{item.expected[1]}</b><b>{item.budget}</b><b>{item.score2025}</b><span>{item.city}</span></div>)}
      </div></div> : <EmptyMessage title="Выбери направления" description="Можно сравнить до четырёх вариантов." />}

    </>
  );
}
