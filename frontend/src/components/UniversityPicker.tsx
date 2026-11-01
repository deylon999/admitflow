import { useDeferredValue, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { University } from '../lib/api';
import { limitCodePoints } from '../lib/direction';

export function UniversityPicker({ value, onChange, onSelect, error }: {
  value: string;
  onChange: (value: string) => void;
  onSelect: (university: University) => void;
  error?: string;
}) {
  const [open, setOpen] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const query = useDeferredValue(limitCodePoints(value, 120));
  const catalog = useQuery({ queryKey: ['universities', query], queryFn: ({ signal }) => api.universities(query, signal), enabled: open, staleTime: 300_000 });
  return <div className="field university-picker" onKeyDown={event => {
    if (event.key === 'Escape' && open) { event.preventDefault(); event.stopPropagation(); input.current?.focus(); setOpen(false); }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      const options = Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('.catalog-option'));
      const current = options.indexOf(document.activeElement as HTMLButtonElement);
      if (document.activeElement !== input.current && current < 0) return;
      event.preventDefault();
      setOpen(true);
      if (!options.length) return;
      if (current === 0 && event.key === 'ArrowUp') input.current?.focus();
      else options[current < 0 ? (event.key === 'ArrowDown' ? 0 : options.length - 1) : Math.min(options.length - 1, current + (event.key === 'ArrowDown' ? 1 : -1))].focus();
    }
  }} onBlur={event => {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
  }}>
    <label htmlFor="university">Вуз</label>
    <input ref={input} id="university" value={value} required autoComplete="off"
      placeholder="Название вуза" aria-invalid={Boolean(error) || undefined} aria-describedby={error ? 'catalog-note university-error' : 'catalog-note'}
      onFocus={() => setOpen(true)}
      onChange={event => { onChange(event.target.value); setOpen(true); }} />
    <p className="form-note" id="catalog-note">Можно выбрать из небольшого справочника или ввести любой вуз вручную. Стрелки ↑ и ↓ переходят к вариантам, Escape закрывает их.</p>
    {error && <p className="form-error" id="university-error" role="alert">{error}</p>}
    {open && <div className="catalog-results">
      {catalog.isPending ? <p className="small-copy" role="status">Ищем вуз…</p>
        : catalog.isError ? <p className="small-copy">Справочник недоступен. Название можно ввести вручную.</p>
          : catalog.data.items.length === 0 ? <p className="small-copy">Вуз пока не добавлен в справочник. Продолжайте с ручным вводом.</p>
            : <ul>{catalog.data.items.map(university => <li key={university.id}>
              <button className="catalog-option" type="button" onClick={() => { onSelect(university); input.current?.focus(); setOpen(false); }}>
                <span>{university.name}</span><small>Ручной режим · автоматическое обновление не подключено</small>
              </button>
              <a href={university.provenanceUrl} target="_blank" rel="noopener noreferrer">Официальный список ↗</a>
            </li>)}</ul>}
    </div>}
  </div>;
}
