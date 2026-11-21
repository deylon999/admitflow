import { useState } from 'react';
import { Action, EmptyMessage, PageTitle, Surface } from '../../shared/UI';
import { programs } from '../../data/demo';
import type { AppPageProps } from './types';
import { ProgramCard } from './ProgramCard';

export function Watchlist({ tracked, onToggle }: AppPageProps) {
  const items = programs.filter(item => tracked.includes(item.id));
  return (
    <>
      <PageTitle kicker="МОИ НАПРАВЛЕНИЯ" title="Один экран вместо пяти сайтов." description="Сохраняй интересующие программы и сравнивай их динамику." action={<Action to="/app/watchlist/add">+ Добавить направление</Action>} />
      {items.length ? <div className="af-program-grid">{items.map(item => <ProgramCard key={item.id} item={item} tracked onToggle={onToggle} />)}</div> : <EmptyMessage title="Пока нет направлений" description="Выбери программу из каталога или добавь её по названию." action={<Action to="/universities">К вузам ↗</Action>} />}
    </>
  );
}

export function AddWatch({ tracked, onToggle }: AppPageProps) {
  const [query, setQuery] = useState('');
  const matches = programs.filter(item => `${item.university} ${item.program}`.toLowerCase().includes(query.toLowerCase()));
  return (
    <>
      <PageTitle kicker="ДОБАВЛЕНИЕ ПРОГРАММЫ" title="Что будем отслеживать?" description="Выбери университет и направление; сохранение работает локально в браузере." />
      <Surface>
        <label className="af-field"><span>ПОИСК ПРОГРАММЫ</span><input value={query} onChange={e => setQuery(e.target.value)} placeholder="МТУСИ, программная инженерия..." /></label>
        <div className="af-program-grid af-program-grid--inside">{matches.map(item => <ProgramCard key={item.id} item={item} tracked={tracked.includes(item.id)} onToggle={onToggle} />)}</div>
      </Surface>
      <Surface tone="lime" title="Не нашёл нужный вуз?" description="В реальном AdmitFlow можно предусмотреть добавление источника вручную. Этот дизайн-кит не подключается к парсерам."><Action to="/app/sources">Статусы источников ↗</Action></Surface>
    </>
  );
}
