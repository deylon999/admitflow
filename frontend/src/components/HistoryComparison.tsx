import { compareSnapshots } from '../lib/comparison';
import type { Snapshot } from '../lib/contracts';
import { useId, useState } from 'react';

export function HistoryComparison({ snapshots }: { snapshots: Snapshot[] }) {
  const prefix = useId();
  const [afterId, setAfterId] = useState('');
  const [beforeId, setBeforeId] = useState('');
  const found = snapshots.findIndex((snapshot) => snapshot.id === afterId);
  const afterIndex = found >= 0 && found < snapshots.length - 1 ? found : 0;
  const after = snapshots[afterIndex];
  const before =
    snapshots.slice(afterIndex + 1).find((snapshot) => snapshot.id === beforeId) ??
    snapshots[afterIndex + 1];
  const comparison = after && compareSnapshots(after, before);
  if (!comparison)
    return <p className="small-copy">Сохраните ещё один снимок, чтобы сравнить изменения.</p>;
  return (
    <section
      className="history-comparison"
      aria-label="Сравнение ручных снимков"
    >
      <div className="history-choices">
        <div className="field">
          <label htmlFor={`${prefix}-after`}>Новое сохранение</label>
          <select
            id={`${prefix}-after`}
            value={after.id}
            onChange={(event) => setAfterId(event.target.value)}
          >
            {snapshots.slice(0, -1).map((snapshot, index) => (
              <option
                key={snapshot.id}
                value={snapshot.id}
              >
                #{index + 1} · {snapshot.capturedAt} · место {snapshot.calculation.place}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor={`${prefix}-before`}>Более раннее сохранение</label>
          <select
            id={`${prefix}-before`}
            value={before.id}
            onChange={(event) => setBeforeId(event.target.value)}
          >
            {snapshots.slice(afterIndex + 1).map((snapshot, index) => (
              <option
                key={snapshot.id}
                value={snapshot.id}
              >
                #{afterIndex + index + 2} · {snapshot.capturedAt} · место{' '}
                {snapshot.calculation.place}
              </option>
            ))}
          </select>
        </div>
      </div>
      <p>Сравнение выбранных ручных сохранений</p>
      <strong>
        Место: {comparison.before} → {comparison.after}
      </strong>
      <p>
        {comparison.direction === 'unchanged'
          ? 'Расчётное место не изменилось.'
          : `Место стало на ${comparison.distance} ${comparison.direction === 'improved' ? 'выше' : 'ниже'}.`}
      </p>
      {comparison.changes.length ? (
        <ul>
          {comparison.changes.map((change) => (
            <li key={change.key}>
              {change.label}: {change.before} → {change.after}
            </li>
          ))}
        </ul>
      ) : (
        <p>Введённые числа не изменились.</p>
      )}
      {comparison.boundaryChanged && (
        <p>Положение относительно границы мест изменилось: {after.calculation.status}.</p>
      )}
      <p className="small-copy">
        Сравниваются ручные записи. Причины изменений в официальном списке здесь не установлены.
      </p>
    </section>
  );
}
