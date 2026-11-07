import { SourceUniversityFilter } from '@/entities/university';
import type { GroupCatalog } from '@/entities/admission-source';
import { limitCodePoints } from '@/shared/lib/text';
import type { SourceFilters } from '../model/useSourceCatalog';

type Props = {
  filters: SourceFilters;
  onChange: (filters: SourceFilters) => void;
  facets?: GroupCatalog['facets'];
};

export function SourceCatalogFilters({ filters, onChange, facets }: Props) {
  return (
    <div className="source-catalog-filters surface">
      <label>
        Группа или направление
        <input
          value={filters.q}
          onChange={(event) =>
            onChange({ ...filters, q: limitCodePoints(event.target.value, 120) })
          }
          placeholder="Название или код направления"
        />
      </label>
      <SourceUniversityFilter
        value={filters.universityId}
        onChange={(universityId) => onChange({ ...filters, universityId, branchId: '' })}
      />
      <label>
        Подразделение
        <select
          aria-label="Подразделение"
          value={filters.branchId}
          onChange={(event) => onChange({ ...filters, branchId: event.target.value })}
        >
          <option value="">Все подразделения</option>
          <option value="main">Головной вуз</option>
          {facets?.branches.map((item) => (
            <option
              key={item.id}
              value={item.id}
            >
              {item.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Сезон
        <select
          aria-label="Сезон"
          value={filters.year}
          onChange={(event) => onChange({ ...filters, year: event.target.value })}
        >
          <option value="">Все сезоны</option>
          {facets?.years.map((year) => (
            <option key={year}>{year}</option>
          ))}
        </select>
      </label>
    </div>
  );
}
