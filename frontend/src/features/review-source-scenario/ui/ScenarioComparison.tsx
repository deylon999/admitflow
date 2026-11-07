import { Alert, Button } from '@/shared/ui';
import { useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router';
import type { SourceGroup } from '@/entities/admission-source';
import { useScenarioComparison } from '../model/useScenarioComparison';

export function ScenarioComparison({ id, group }: { id: string; group: SourceGroup }) {
  const [params] = useSearchParams();
  const heading = useRef<HTMLHeadingElement>(null);
  const target = params.get('direction') === id ? params.get('assessment') : null;
  const { detail, previous, previousId, retryComparison } = useScenarioComparison(
    id,
    group,
    target,
  );
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
        <Alert
          as="p"
          role="alert"
        >
          Не удалось загрузить сравнение.{' '}
          <Button
            variant="secondary"
            type="button"
            onClick={retryComparison}
          >
            Повторить сравнение
          </Button>
        </Alert>
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
