const stats = [
  ['1–3 недели', 'наблюдения за списками'],
  ['до 20 часов', 'ручной проверки списков'],
  ['2 из 2', 'интервью: риск ошибки'],
  ['2027', 'следующая кампания'],
];
export function StatsStrip() {return <section className="stats-strip container" aria-label="Контекст и статистика">{stats.map(([value, description])=><div className="stat" key={value}><strong>{value}</strong><span>{description}</span></div>)}</section>}
