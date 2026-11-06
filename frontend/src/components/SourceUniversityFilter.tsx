import { useDeferredValue, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { University } from '../lib/api';
import { limitCodePoints } from '../lib/direction';

export function SourceUniversityFilter({
  value,
  onChange,
}: {
  value: string;
  onChange: (id: string) => void;
}) {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<University | null>(null);
  const query = useDeferredValue(search);
  const catalog = useInfiniteQuery({
    queryKey: ['universities', query],
    initialPageParam: 0,
    queryFn: ({ signal, pageParam }) => api.universities(query, signal, pageParam),
    getNextPageParam: (page) => page.nextOffset ?? undefined,
    staleTime: 300_000,
  });
  const items = [
    ...new Map(
      catalog.data?.pages.flatMap((page) => page.items).map((item) => [item.id, item]) ?? [],
    ).values(),
  ];
  const retained =
    selected?.id === value && !items.some((item) => item.id === value) ? selected : null;
  return (
    <div className="source-university-filter">
      <label>
        Поиск вуза
        <input
          value={search}
          onChange={(event) => setSearch(limitCodePoints(event.target.value, 120))}
          placeholder="Название или регион"
        />
      </label>
      <label>
        Вуз
        <select
          aria-label="Вуз"
          value={value}
          onChange={(event) => {
            const id = event.target.value;
            setSelected(
              items.find((item) => item.id === id) ?? (retained?.id === id ? retained : null),
            );
            onChange(id);
          }}
        >
          <option value="">Все вузы каталога</option>
          {retained && <option value={retained.id}>{retained.name}</option>}
          {items.map((item) => (
            <option
              key={item.id}
              value={item.id}
            >
              {item.name}
            </option>
          ))}
        </select>
      </label>
      {query !== search || catalog.isPending ? (
        <p
          className="small-copy"
          role="status"
        >
          Ищем вуз…
        </p>
      ) : catalog.isError ? (
        <div
          role="alert"
          className="small-copy"
        >
          <p>
            Не удалось загрузить {items.length ? 'следующие вузы' : 'справочник вузов'}. Выбор
            сохранён.
          </p>
          <button
            type="button"
            onClick={() => void (items.length ? catalog.fetchNextPage() : catalog.refetch())}
          >
            Повторить загрузку вузов
          </button>
        </div>
      ) : (
        <p
          className="small-copy"
          role="status"
        >
          Найдено вузов: {catalog.data?.pages[0].total}. Показано: {items.length}.
        </p>
      )}
      {catalog.hasNextPage && !catalog.isError && (
        <button
          type="button"
          className="text-button"
          disabled={catalog.isFetchingNextPage}
          onClick={() => void catalog.fetchNextPage()}
        >
          {catalog.isFetchingNextPage ? 'Загружаем…' : 'Показать ещё вузы'}
        </button>
      )}
    </div>
  );
}
