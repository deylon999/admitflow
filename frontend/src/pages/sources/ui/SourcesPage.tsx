import { Alert, Button, Card, RequestFeedback } from '@/shared/ui';
import { requestErrorText } from '@/shared/api';
import { Link } from 'react-router';
import { useSourceCatalog } from '../model/useSourceCatalog';
import { SourceCatalogFilters } from './SourceCatalogFilters';
import { SourceGroupCard } from './SourceGroupCard';

export function SourcesPage() {
  const { filters, setFilters, selected, setSelected, catalog, items, facets } = useSourceCatalog();
  return (
    <main
      id="top"
      className="container page-shell sources-page"
    >
      <header className="page-heading">
        <p className="eyebrow">Проверяемые источники</p>
        <h1>Вузы и конкурсные группы</h1>
        <p className="section-description">
          Каталог и автоматический сбор — разные вещи. Архив сохраняет свой сезон. По данным
          источника не рассчитывается вероятность или гарантия зачисления.
        </p>
      </header>
      <SourceCatalogFilters
        filters={filters}
        onChange={setFilters}
        facets={facets}
      />
      <h2 id="source-results-title">Конкурсные группы</h2>
      {catalog.isPending && <p role="status">Загружаем конкурсные группы…</p>}
      {catalog.isFetching && catalog.data && !catalog.isFetchingNextPage && (
        <RequestFeedback>Обновляем конкурсные группы…</RequestFeedback>
      )}
      {catalog.isError && catalog.data && (
        <RequestFeedback
          busy={catalog.isFetching}
          retryLabel="Повторить загрузку групп"
          onRetry={() =>
            void (catalog.isFetchNextPageError ? catalog.fetchNextPage() : catalog.refetch())
          }
        >
          {catalog.isFetchNextPageError
            ? 'Не удалось загрузить следующие группы.'
            : 'Не удалось обновить группы.'}{' '}
          Показаны ранее загруженные данные.
        </RequestFeedback>
      )}
      {catalog.isError && !catalog.data && (
        <Alert
          role="alert"
          className="surface source-catalog-card"
        >
          <p>Не удалось загрузить группы.</p>
          <p>{requestErrorText(catalog.error)}</p>
          <Button
            variant="secondary"
            type="button"
            disabled={catalog.isFetching}
            onClick={() => void catalog.refetch()}
          >
            {catalog.isFetching ? 'Повторяем загрузку…' : 'Повторить загрузку групп'}
          </Button>
        </Alert>
      )}
      {catalog.isSuccess && items.length === 0 && (
        <Card className="catalog-empty">
          <h3>Ничего не найдено</h3>
          <p className="small-copy">
            Подходящих подключённых групп пока нет. Направление можно сохранить вручную.
          </p>
        </Card>
      )}
      <div
        className="source-catalog-list"
        role="region"
        aria-labelledby="source-results-title"
      >
        {items.map((group) => (
          <SourceGroupCard
            key={group.id}
            group={group}
            selected={selected === group.id}
            onSelect={() => setSelected(group.id)}
            onClose={() => {
              setSelected(null);
              requestAnimationFrame(() => document.getElementById(`lookup-${group.id}`)?.focus());
            }}
          />
        ))}
      </div>
      {catalog.hasNextPage && !catalog.isFetchNextPageError && (
        <Button
          variant="secondary"
          type="button"

          disabled={catalog.isFetchingNextPage}
          onClick={() => void catalog.fetchNextPage()}
        >
          {catalog.isFetchingNextPage ? 'Загружаем…' : 'Загрузить ещё группы'}
        </Button>
      )}
      <div className="page-actions">
        <Link
          data-router-link
          className="button button-primary"
          to="/tracker"
        >
          Сохранить направление вручную
        </Link>
        <a
          className="button button-secondary"
          href="https://github.com/deylon999/admitflow/issues/new"
          target="_blank"
          rel="noopener noreferrer"
        >
          Предложить источник на GitHub ↗
        </a>
      </div>
      <p className="small-copy source-submission-note">
        Для предложения нужны официальный адрес, сезон, конкурсная группа и образец списка без
        персональных данных. Предложение не включает источник автоматически.
      </p>
    </main>
  );
}
