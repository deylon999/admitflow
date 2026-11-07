import { Link } from 'react-router';
import { useSourceCatalog } from '../model/useSourceCatalog';
import { SourceCatalogFilters } from './SourceCatalogFilters';
import { SourceGroupCard } from './SourceGroupCard';

export function SourcesPage() {
  const { filters, setFilters, selected, setSelected, catalog, items, facets } = useSourceCatalog();
  return (
    <main
      id="top"
      className="container tracker-page"
    >
      <p className="eyebrow">Проверяемые источники</p>
      <h1>Вузы и конкурсные группы</h1>
      <p className="section-description">
        Каталог и автоматический сбор — разные вещи. Архив сохраняет свой сезон. По данным источника
        не рассчитывается вероятность или гарантия зачисления.
      </p>
      <SourceCatalogFilters
        filters={filters}
        onChange={setFilters}
        facets={facets}
      />
      {catalog.isPending && <p role="status">Загружаем конкурсные группы…</p>}
      {catalog.isError && (
        <div
          role="alert"
          className="surface source-catalog-card"
        >
          <p>Не удалось загрузить группы.</p>
          <button
            type="button"
            onClick={() => void catalog.refetch()}
          >
            Повторить загрузку групп
          </button>
        </div>
      )}
      {catalog.isSuccess && items.length === 0 && (
        <p className="notice">
          Подходящих подключённых групп пока нет. Направление можно сохранить вручную.
        </p>
      )}
      <div className="source-catalog-list">
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
      {catalog.hasNextPage && (
        <button
          type="button"
          className="button button-secondary"
          disabled={catalog.isFetchingNextPage}
          onClick={() => void catalog.fetchNextPage()}
        >
          {catalog.isFetchingNextPage ? 'Загружаем…' : 'Загрузить ещё группы'}
        </button>
      )}
      <div className="direction-actions">
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
      <p className="small-copy">
        Для предложения нужны официальный адрес, сезон, конкурсная группа и образец списка без
        персональных данных. Предложение не включает источник автоматически.
      </p>
    </main>
  );
}
