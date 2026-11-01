import { compareSnapshots } from '../lib/comparison';
import type { Snapshot } from '../lib/contracts';

export function HistoryComparison({ snapshots }: { snapshots: Snapshot[] }) {
  const comparison = snapshots[0] && compareSnapshots(snapshots[0], snapshots[1]);
  if (!comparison) return <p className="small-copy">Сохраните ещё один снимок, чтобы сравнить изменения.</p>;
  return <section className="history-comparison" aria-label="Сравнение ручных снимков">
    <p>Два последних сохранения</p>
    <strong>Место: {comparison.before} → {comparison.after}</strong>
    <p>{comparison.direction === 'unchanged' ? 'Расчётное место не изменилось.'
      : `Место стало на ${comparison.distance} ${comparison.direction === 'improved' ? 'выше' : 'ниже'}.`}</p>
    {comparison.changes.length ? <ul>{comparison.changes.map(change => <li key={change.key}>{change.label}: {change.before} → {change.after}</li>)}</ul>
      : <p>Введённые числа не изменились.</p>}
    {comparison.boundaryChanged && <p>Положение относительно границы мест изменилось: {snapshots[0].calculation.status}.</p>}
    <p className="small-copy">Сравниваются ручные записи. Причины изменений в официальном списке здесь не установлены.</p>
  </section>;
}
