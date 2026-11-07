import { Card, Input, Select, Button } from '@/shared/ui';
import type { WatchOrder } from '@/entities/manual-direction';
import type { TrackerModel } from '../model/useTrackerModel';

export function TrackerFilters({ model }: { model: TrackerModel }) {
  const {
    privateVisible,
    count,
    search,
    setSearch,
    scenario,
    setScenario,
    order,
    setOrder,
    visible,
    clearFilters,
  } = model;
  return (
    <>
      {privateVisible && count > 0 && (
        <Card
          as="section"
          className="watch-filters"
          aria-label="Поиск направлений"
        >
          <div className="field">
            <label htmlFor="watch-search">Поиск по вузу и направлению</label>
            <Input
              id="watch-search"
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="watch-state">Ручной сценарий</label>
            <Select
              id="watch-state"
              value={scenario}
              onChange={(event) => setScenario(event.target.value)}
            >
              <option value="all">Все сценарии</option>
              <option value="safe">В пределах в обоих сценариях</option>
              <option value="conditional">В пределах только при текущих согласиях</option>
              <option value="out">За границей мест</option>
            </Select>
          </div>
          <div className="field">
            <label htmlFor="watch-order">Порядок направлений</label>
            <Select
              id="watch-order"
              value={order}
              onChange={(event) => setOrder(event.target.value as WatchOrder)}
            >
              <option value="updated">Недавно сохранённые</option>
              <option value="university">По вузу и названию</option>
              <option value="created">Недавно добавленные</option>
            </Select>
          </div>
          <p role="status">
            Показано {visible.length} из {count}
          </p>
          <Button
            variant="ghost"

            type="button"
            onClick={clearFilters}
          >
            Сбросить поиск и фильтры
          </Button>
        </Card>
      )}
    </>
  );
}
