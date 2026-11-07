import { Input, Select, RequestFeedback, Button } from '@/shared/ui';
import { useState } from 'react';
import { useUniversityCatalog } from '../model/useUniversityCatalog';
import type { University } from '../model/types';
import { limitCodePoints } from '@/shared/lib/text';

export function SourceUniversityFilter({
  value,
  onChange,
}: {
  value: string;
  onChange: (id: string) => void;
}) {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<University | null>(null);
  const { catalog, query } = useUniversityCatalog(search);
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
        <Input
          value={search}
          onChange={(event) => setSearch(limitCodePoints(event.target.value, 120))}
          placeholder="Название или регион"
        />
      </label>
      <label>
        Вуз
        <Select
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
        </Select>
      </label>
      {query !== search || catalog.isPending ? (
        <p
          className="small-copy"
          role="status"
        >
          Ищем вуз…
        </p>
      ) : catalog.isError ? (
        <RequestFeedback
          busy={catalog.isFetching}
          retryLabel="Повторить загрузку вузов"
          onRetry={() =>
            void (catalog.isFetchNextPageError ? catalog.fetchNextPage() : catalog.refetch())
          }
        >
          Не удалось загрузить{' '}
          {catalog.isFetchNextPageError ? 'следующие вузы' : 'справочник вузов'}. Выбор сохранён.
        </RequestFeedback>
      ) : (
        <p
          className="small-copy"
          role="status"
        >
          Найдено вузов: {catalog.data?.pages[0].total}. Показано: {items.length}.
        </p>
      )}
      {catalog.isFetching && catalog.data && !catalog.isFetchingNextPage && (
        <RequestFeedback>Обновляем список вузов…</RequestFeedback>
      )}
      {catalog.hasNextPage && !catalog.isError && (
        <Button
          variant="ghost"
          type="button"

          disabled={catalog.isFetchingNextPage}
          onClick={() => void catalog.fetchNextPage()}
        >
          {catalog.isFetchingNextPage ? 'Загружаем…' : 'Показать ещё вузы'}
        </Button>
      )}
    </div>
  );
}
