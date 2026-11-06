import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router';
import { api } from '../lib/api';
import { InvalidResponseError } from '../lib/contracts';
import type { SourceGroup } from '../lib/source-contracts';
export function ScenarioComparison({ id, group }: { id: string; group: SourceGroup }) {
  const [params] = useSearchParams(),
    heading = useRef<HTMLHeadingElement>(null);
  const target = params.get('direction') === id ? params.get('assessment') : null;
  const detail = useQuery({
    queryKey: ['scenario-detail', id, target],
    enabled: !!target,
    queryFn: async ({ signal }) => {
      const value = await api.scenarioDetail(id, target!, signal);
      if (
        value.subscriptionId !== id ||
        value.groupId !== group.id ||
        value.sourceId !== group.sourceId ||
        value.id !== target
      )
        throw new InvalidResponseError();
      return value;
    },
  });
  const previousId = detail.data?.previousId;
  const previous = useQuery({
    queryKey: ['scenario-detail', id, previousId],
    enabled: !!target && !!previousId,
    queryFn: async ({ signal }) => {
      const value = await api.scenarioDetail(id, previousId!, signal);
      if (
        value.subscriptionId !== id ||
        value.id !== previousId ||
        value.groupId !== group.id ||
        value.sourceId !== group.sourceId
      )
        throw new InvalidResponseError();
      return value;
    },
  });
  useEffect(() => {
    if (target && detail.data) heading.current?.focus();
  }, [target, detail.data]);
  if (!target) return null;
  return (
    <section
      className="scenario-comparison"
      aria-label="Сравнение сохранённых сценариев"
    >
      <h4
        ref={heading}
        tabIndex={-1}
      >
        Сравнение сохранённых версий
      </h4>
      {(detail.isPending || (previousId && previous.isPending)) && (
        <p role="status">Загружаем выбранные версии…</p>
      )}
      {(detail.isError || previous.isError) && (
        <p role="alert">
          Не удалось загрузить сравнение.{' '}
          <button
            type="button"
            onClick={() => {
              void detail.refetch();
              if (previousId) void previous.refetch();
            }}
          >
            Повторить сравнение
          </button>
        </p>
      )}
      {detail.data && (
        <>
          <p>
            Это сохранённые результаты для двух конкретных снимков. Они не пересчитываются при
            чтении.
          </p>
          {previous.data && (
            <div>
              <h5>До изменения</h5>
              <p>{previous.data.explanation?.summary}</p>
              <p className="small-copy">
                Снимок {previous.data.snapshotId} · {previous.data.fetchedAt}
              </p>
            </div>
          )}
          {!previousId && <p>Предыдущей версии нет.</p>}
          <div>
            <h5>После изменения</h5>
            <p>{detail.data.explanation?.summary}</p>
            <p className="small-copy">
              Снимок {detail.data.snapshotId} · {detail.data.fetchedAt}
            </p>
          </div>
          <ul>
            {detail.data.explanation?.changes.map((text, index) => (
              <li key={index}>{text}</li>
            ))}
          </ul>
          <p>
            Версия модели: {detail.data.result?.modelVersion}. Официальный результат не
            рассчитывается.
          </p>
        </>
      )}
    </section>
  );
}
