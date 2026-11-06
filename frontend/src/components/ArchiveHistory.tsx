import { useId, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { assertArchiveOrder } from '../lib/source-contracts';
import type { ArchiveHistoryItem, CandidateFact } from '../lib/source-contracts';

function fact(value: unknown) {
  return value === null
    ? 'неизвестно'
    : value === true
      ? 'да'
      : value === false
        ? 'нет'
        : String(value);
}
const fields: [keyof CandidateFact, string][] = [
  ['officialRank', 'Строка списка'],
  ['score', 'Баллы'],
  ['consent', 'Согласие'],
  ['priority', 'Приоритет'],
];
function Difference({ after, before }: { after: ArchiveHistoryItem; before: ArchiveHistoryItem }) {
  const current = after.candidate;
  const previous = before.candidate;
  const changes =
    current && previous ? fields.filter(([key]) => current[key] !== previous[key]) : [];
  return (
    <>
      {current && previous ? (
        changes.length ? (
          <ul>
            {changes.map(([key, label]) => (
              <li key={key}>
                {label}: {fact(previous[key])} → {fact(current[key])}
              </li>
            ))}
          </ul>
        ) : (
          <p>Строка, баллы, согласие и приоритет не изменились.</p>
        )
      ) : (
        <p>
          Запись {after.present ? 'присутствует' : 'отсутствует'} в новом снимке;{' '}
          {before.present ? 'присутствует' : 'отсутствует'} в старом. Отсутствие не доказывает отзыв
          или отказ.
        </p>
      )}
      {before.group.seats !== after.group.seats && (
        <p>
          Мест в группе: {fact(before.group.seats)} → {fact(after.group.seats)}
        </p>
      )}
      {current && previous && previous.participation !== current.participation && (
        <p>
          Статус участия в источнике изменился: {previous.participation} → {current.participation}.
        </p>
      )}
    </>
  );
}
export function ArchiveHistory({ id }: { id: string }) {
  const [show, setShow] = useState(false),
    [olderId, setOlderId] = useState('');
  const prefix = useId();
  const history = useInfiniteQuery({
    queryKey: ['archive-history', id],
    initialPageParam: null as string | null,
    queryFn: ({ pageParam, signal }) => api.archiveHistory(id, pageParam, signal),
    getNextPageParam: (page) => page.nextCursor ?? undefined,
    enabled: show,
    select: (data) => {
      const items = data.pages.flatMap((page) => page.items);
      assertArchiveOrder(items);
      return { ...data, items };
    },
  });
  const items = history.data?.items ?? [],
    after = items[0],
    before = items.slice(1).find((item) => item.id === olderId) ?? items[1];
  return (
    <div className="archive-history">
      <button
        type="button"
        className="text-button"
        aria-expanded={show}
        aria-controls={prefix}
        onClick={() => setShow((value) => !value)}
      >
        История фактов
      </button>
      {show && (
        <div id={prefix}>
          <h4>Архивная история источника</h4>
          <p>
            Версии фактов из списка. Строка списка не является расчётным местом или гарантией
            зачисления.
          </p>
          {history.isPending && <p role="status">Загружаем историю фактов…</p>}
          {history.isError && (
            <p role="alert">
              Не удалось загрузить историю.{' '}
              {history.data ? 'Показаны ранее загруженные датированные записи. ' : ''}
              <button
                type="button"
                className="text-button"
                onClick={() =>
                  void (history.isFetchNextPageError ? history.fetchNextPage() : history.refetch())
                }
              >
                Повторить историю фактов
              </button>
            </p>
          )}
          {after && before && (
            <section aria-label="Сравнение архивных фактов">
              <label>
                Ранний архивный снимок
                <select
                  value={before.id}
                  onChange={(event) => setOlderId(event.target.value)}
                >
                  {items.slice(1).map((item) => (
                    <option
                      key={item.id}
                      value={item.id}
                    >
                      {item.group.fetchedAt} · {item.group.snapshotId}
                    </option>
                  ))}
                </select>
              </label>
              <p>
                Новый снимок {after.group.fetchedAt} · {after.group.snapshotId}; ранний{' '}
                {before.group.fetchedAt} · {before.group.snapshotId}.
              </p>
              <Difference
                after={after}
                before={before}
              />
              <p className="small-copy">
                Изменение факта не устанавливает причину или результат зачисления.
              </p>
            </section>
          )}
          {items.length === 1 && <p>Для сравнения нужен ещё один проверенный снимок.</p>}
          <ol className="archive-fact-list">
            {items.map((item) => (
              <li key={item.id}>
                <p>
                  Снимок {item.group.snapshotId} ·{' '}
                  <time dateTime={item.group.fetchedAt!}>{item.group.fetchedAt}</time> ·{' '}
                  {item.group.year} · архив
                </p>
                <p>
                  {item.candidate
                    ? fields
                        .map(([key, label]) => `${label}: ${fact(item.candidate![key])}`)
                        .join(' · ')
                    : 'Запись отсутствует в снимке; причина не установлена.'}
                </p>
                <p className="small-copy">
                  Обработка: {item.modelVersion} · сохранение фактов: {item.assessedAt}. Обновление
                  источника: {item.group.sourceUpdatedAt ?? 'неизвестно'}.
                </p>
                {item.group.sourceUrl && (
                  <a
                    href={item.group.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Официальный список ↗
                  </a>
                )}
              </li>
            ))}
          </ol>
          {history.hasNextPage && (
            <button
              className="text-button"
              type="button"
              disabled={history.isFetchingNextPage}
              onClick={() => void history.fetchNextPage()}
            >
              Ещё архивные снимки
            </button>
          )}
        </div>
      )}
    </div>
  );
}
