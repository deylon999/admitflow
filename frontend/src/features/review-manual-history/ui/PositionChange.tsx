import type { Watch } from '@/entities/manual-direction';
import { useManualHistory } from '../model/useManualHistory';

export function PositionChange({
  watch,
  showFailure = true,
}: {
  watch: Watch;
  showFailure?: boolean;
}) {
  const history = useManualHistory(watch.id, true, watch.latest.id);
  const snapshots = history.data?.snapshots;
  // Only compare a history that still describes the displayed latest snapshot.
  const previous = snapshots?.[0]?.id === watch.latest.id ? snapshots[1] : undefined;
  if (history.isError && !history.data)
    return showFailure ? (
      <p className="position-change">Изменение места недоступно. Повторите загрузку в «Истории».</p>
    ) : null;
  if (history.isPending)
    return (
      <p
        className="position-change"
        role="status"
      >
        Проверяем изменение места…
      </p>
    );
  if (snapshots?.length && snapshots[0]?.id !== watch.latest.id)
    return (
      <p className="position-change">
        История обновилась. Обновите направления, чтобы сравнить место.
      </p>
    );
  if (!previous)
    return <p className="position-change">Для сравнения нужно предыдущее сохранение.</p>;
  const change = previous.calculation.place - watch.latest.calculation.place;
  return (
    <p
      className="position-change"
      data-changed={change !== 0}
    >
      {change === 0
        ? 'Место не изменилось'
        : `${change > 0 ? '↑ Выше' : '↓ Ниже'} на ${Math.abs(change)}`}
      <span> · было {previous.calculation.place} при прошлом сохранении</span>
      {history.isError && showFailure && <span> · Не удалось обновить изменение.</span>}
      {history.isFetching && <span> · Обновляем…</span>}
    </p>
  );
}
