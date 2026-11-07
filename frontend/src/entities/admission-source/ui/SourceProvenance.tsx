import { Button, Alert } from '@/shared/ui';
import type { SourceGroup } from '../model/types';
import { useId, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { sourceApi } from '../api/source-api';

const states: Record<string, string> = {
  archived: 'Архивный снимок',
  fresh: 'Проверка источника актуальна',
  stale: 'Проверка источника устарела',
  source_error: 'Последняя проверка завершилась ошибкой. Сохранённые факты имеют прежнюю дату.',
  quarantined:
    'Новый ответ источника отклонён проверкой качества. Показан прежний проверенный снимок.',
  disabled: 'Сбор источника отключён. Сохранённый снимок остаётся архивом.',
  unsupported: 'Формат источника не поддержан',
  unknown: 'Состояние проверки не подтверждено',
};
function Time({ value }: { value: string | null }) {
  return value ? (
    <time
      dateTime={value}
      title={value}
    >
      {new Date(value).toLocaleString('ru-RU')} ({value})
    </time>
  ) : (
    <>неизвестно</>
  );
}
export function SourceProvenance({ group }: { group: SourceGroup }) {
  const [show, setShow] = useState(false),
    id = useId();
  const checks = useQuery({
    queryKey: ['source-checks', group.sourceId],
    queryFn: ({ signal }) => sourceApi.sourceChecks(group.sourceId!, signal),
    enabled: show && Boolean(group.sourceId),
  });
  return (
    <div className="source-provenance">
      <p role="status">{states[group.sourceState ?? 'unknown'] ?? states.unknown}</p>
      <dl>
        <dt>Снимок</dt>
        <dd>{group.snapshotId ?? 'ещё не получен'}</dd>
        <dt>Получен сервисом</dt>
        <dd>
          <Time value={group.fetchedAt} />
        </dd>
        <dt>Обновление самим источником</dt>
        <dd>
          <Time value={group.sourceUpdatedAt} />
        </dd>
        <dt>Последняя проверка источника</dt>
        <dd>
          <Time value={group.lastCheckedAt} />
        </dd>
      </dl>
      {group.sourceUrl && (
        <a
          href={group.sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          Официальный список ↗
        </a>
      )}
      <p className="small-copy">
        Проверка доступности не меняет дату снимка. Неизвестная дата источника не заменяется
        временем загрузки.
      </p>
      {group.sourceId && (
        <>
          <Button
            variant="ghost"

            type="button"
            aria-expanded={show}
            aria-controls={id}
            onClick={() => setShow((value) => !value)}
          >
            Последние проверки источника
          </Button>
          {show && (
            <div id={id}>
              {checks.isPending ? (
                <p role="status">Загружаем проверки…</p>
              ) : checks.isError ? (
                <Alert
                  as="p"
                  role="alert"
                >
                  Не удалось загрузить проверки.{' '}
                  <Button
                    variant="secondary"
                    type="button"
                    onClick={() => void checks.refetch()}
                  >
                    Повторить проверки
                  </Button>
                </Alert>
              ) : checks.data?.length ? (
                <ol>
                  {checks.data.map((check) => (
                    <li key={check.id}>
                      <Time value={check.checkedAt} /> —{' '}
                      {check.outcome === 'success'
                        ? 'проверка прошла'
                        : 'проверка не прошла; прежний снимок сохранён'}
                    </li>
                  ))}
                </ol>
              ) : (
                <p>
                  Завершённые проверки ещё не записаны. Старые попытки до включения журнала здесь не
                  восстановлены.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
