import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router';
import { api } from '../lib/api';
import { assertChangeOrder } from '../lib/change-contracts';
import { sessionAccessKey } from '../lib/query-client';
import type { SessionAccess } from '../lib/query-client';
export function ChangeFeed() {
  const client = useQueryClient();
  const access = useQuery<SessionAccess>({
    queryKey: sessionAccessKey,
    queryFn: async (): Promise<SessionAccess> => 'active',
    enabled: false,
    initialData: 'active',
  });
  const feed = useInfiniteQuery({
    queryKey: ['changes'],
    initialPageParam: null as string | null,
    enabled: access.data === 'active',
    queryFn: ({ pageParam, signal }) => api.changes(pageParam, signal),
    getNextPageParam: (page) => page.nextCursor ?? undefined,
    select: (data) => {
      const items = data.pages.flatMap((page) => page.items);
      assertChangeOrder(items);
      return { ...data, items };
    },
  });
  const seen = useMutation({
    mutationFn: api.seeChange,
    onSuccess: () => client.invalidateQueries({ queryKey: ['changes'] }),
  });
  if (access.data !== 'active') return null;
  return (
    <section
      className="surface change-feed"
      aria-labelledby="changes-title"
    >
      <h2 id="changes-title">Изменения в ваших списках</h2>
      <p>
        Изменения сохранённых условных сценариев. Архивные данные не описывают текущую приёмную
        кампанию.
      </p>
      {feed.isPending && <p role="status">Загружаем изменения…</p>}
      {feed.isError && (
        <p role="alert">
          Не удалось перечитать изменения.{' '}
          <button
            type="button"
            onClick={() => void feed.refetch()}
          >
            Повторить изменения
          </button>
        </p>
      )}
      {feed.data && (
        <p role="status">
          Непрочитанных: {feed.data.pages[0].unreadCount} · всего: {feed.data.pages[0].total}
        </p>
      )}
      {feed.data?.items.length === 0 && (
        <p>Новых изменений пока нет. При первом сохранении записи уведомление не создаётся.</p>
      )}
      <button
        type="button"
        className="text-button"
        disabled={feed.isFetching}
        onClick={() => void feed.refetch()}
      >
        Перечитать изменения
      </button>
      {seen.isError && <p role="alert">{seen.error.message} Повторите отметку прочтения явно.</p>}
      <ol>
        {feed.data?.items.map((item) => (
          <li key={item.id}>
            <h3>{item.title}</h3>
            <p>{item.scenario.explanation?.summary}</p>
            <ul>
              {item.scenario.explanation?.changes.map((text, index) => (
                <li key={index}>{text}</li>
              ))}
            </ul>
            <p className="small-copy">
              Снимок получен: {item.scenario.fetchedAt}. Изменение обработано: {item.createdAt}.
            </p>
            <Link
              to={`/tracker?direction=${encodeURIComponent(item.scenario.subscriptionId)}&assessment=${encodeURIComponent(item.scenario.id!)}`}
            >
              Сравнить сохранённые версии
            </Link>
            {item.seenAt ? (
              <p className="small-copy">Прочитано: {item.seenAt}</p>
            ) : (
              <button
                type="button"
                className="text-button"
                disabled={seen.isPending}
                onClick={() => seen.mutate(item.id)}
              >
                Отметить прочитанным
              </button>
            )}
          </li>
        ))}
      </ol>
      {feed.hasNextPage && (
        <button
          type="button"
          disabled={feed.isFetchingNextPage}
          onClick={() => void feed.fetchNextPage()}
        >
          Ещё изменения
        </button>
      )}
    </section>
  );
}
