import { useDeferredValue, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { University } from '../lib/api';

export function UniversityPicker({ value, onChange, onSelect }: {
  value: string;
  onChange: (value: string) => void;
  onSelect: (university: University) => void;
}) {
  const [open, setOpen] = useState(false);
  const query = useDeferredValue(value.slice(0, 120));
  const catalog = useQuery({ queryKey: ['universities', query], queryFn: () => api.universities(query), enabled: open, staleTime: 300_000 });
  return <div className="field university-picker" onBlur={event => {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
  }}>
    <label htmlFor="university">Вуз</label>
    <input id="university" value={value} maxLength={160} required autoComplete="off"
      placeholder="Название вуза" aria-describedby="catalog-note"
      onFocus={() => setOpen(true)} onKeyDown={event => { if (event.key === 'Escape') setOpen(false); }}
      onChange={event => { onChange(event.target.value); setOpen(true); }} />
    <p className="form-note" id="catalog-note">Можно выбрать из небольшого справочника или ввести любой вуз вручную.</p>
    {open && <div className="catalog-results">
      {catalog.isPending ? <p className="small-copy" role="status">Ищем вуз…</p>
        : catalog.isError ? <p className="small-copy">Справочник недоступен. Название можно ввести вручную.</p>
          : catalog.data.items.length === 0 ? <p className="small-copy">Вуз пока не добавлен в справочник. Продолжайте с ручным вводом.</p>
            : <ul>{catalog.data.items.map(university => <li key={university.id}>
              <button className="catalog-option" type="button" onClick={() => { onSelect(university); setOpen(false); }}>
                <span>{university.name}</span><small>Ручной режим · автоматическое обновление не подключено</small>
              </button>
              <a href={university.provenanceUrl} target="_blank" rel="noopener noreferrer">Официальный список ↗</a>
            </li>)}</ul>}
    </div>}
  </div>;
}
