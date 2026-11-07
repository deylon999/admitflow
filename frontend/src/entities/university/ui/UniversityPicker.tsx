import { Input, Alert, Button } from '@/shared/ui';
import { useRef, useState } from 'react';
import { useUniversityCatalog } from '../model/useUniversityCatalog';
import type { University } from '../model/types';
import { limitCodePoints } from '@/shared/lib/text';

export function UniversityPicker({
  value,
  onChange,
  onSelect,
  error,
}: {
  value: string;
  onChange: (value: string) => void;
  onSelect: (university: University) => void;
  error?: string;
}) {
  const [open, setOpen] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const search = limitCodePoints(value, 120);
  const { catalog, query } = useUniversityCatalog(search, open);
  const universities = catalog.data?.pages.flatMap((page) => page.items) ?? [];
  return (
    <div
      className="field university-picker"
      onKeyDown={(event) => {
        if (event.key === 'Escape' && open) {
          event.preventDefault();
          event.stopPropagation();
          input.current?.focus();
          setOpen(false);
        }
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
          const options = Array.from(
            event.currentTarget.querySelectorAll<HTMLButtonElement>('.catalog-option'),
          );
          const current = options.indexOf(document.activeElement as HTMLButtonElement);
          if (document.activeElement !== input.current && current < 0) return;
          event.preventDefault();
          setOpen(true);
          if (!options.length) return;
          if (current === 0 && event.key === 'ArrowUp') input.current?.focus();
          else
            options[
              current < 0
                ? event.key === 'ArrowDown'
                  ? 0
                  : options.length - 1
                : Math.min(options.length - 1, current + (event.key === 'ArrowDown' ? 1 : -1))
            ].focus();
        }
      }}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <label htmlFor="university">Вуз</label>
      <Input
        ref={input}
        id="university"
        value={value}
        required
        autoComplete="off"
        placeholder="Например: СПбГУ или вуз в Казани"
        aria-invalid={Boolean(error) || undefined}
        aria-describedby={error ? 'catalog-note university-error' : 'catalog-note'}
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          onChange(event.target.value);
          setOpen(true);
        }}
      />
      <p
        className="form-note"
        id="catalog-note"
      >
        Введите название или выберите подсказку. Можно указать свой вуз.
      </p>
      {error && (
        <Alert
          as="p"
          className="form-error"
          id="university-error"
          role="alert"
        >
          Введите название вуза в одну строку, до 160 символов.
        </Alert>
      )}
      {open && (
        <div
          className="catalog-results"
          tabIndex={-1}
        >
          {query !== search || catalog.isPending ? (
            <p
              className="small-copy"
              role="status"
            >
              Ищем вуз…
            </p>
          ) : catalog.isError ? (
            <p className="small-copy">Справочник недоступен. Название можно ввести вручную.</p>
          ) : universities.length === 0 ? (
            <p className="small-copy">
              Вуз пока не добавлен в справочник. Продолжайте с ручным вводом.
            </p>
          ) : (
            <>
              <p className="small-copy">
                Найдено: {catalog.data?.pages[0].total}. Показано: {universities.length}.
              </p>
              <ul>
                {universities.map((university) => (
                  <li key={university.id}>
                    <Button
                      variant="option"
                      className="catalog-option"
                      type="button"
                      onClick={() => {
                        onSelect(university);
                        input.current?.focus();
                        setOpen(false);
                      }}
                    >
                      <span title={university.legalName}>
                        {university.catalogOrigin === 'operator'
                          ? university.name
                          : (university.legalName ?? university.name)}
                      </span>
                      <small>
                        {university.region}
                        {university.isBranch ? ' · Филиал' : ''} · Ручной режим
                      </small>
                    </Button>
                    <a
                      href={university.provenanceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {university.catalogOrigin === 'monitoring'
                        ? 'Карточка в официальном перечне ↗'
                        : 'Официальный источник ↗'}
                    </a>
                    {university.catalogOrigin === 'monitoring' && (
                      <small>
                        Списки и автоматическое обновление ещё не подключены; ссылку на список нужно
                        указать самостоятельно.
                      </small>
                    )}
                  </li>
                ))}
              </ul>
              {catalog.hasNextPage && (
                <Button
                  variant="ghost"
                  type="button"

                  disabled={catalog.isFetchingNextPage}
                  onClick={() => {
                    input.current?.focus();
                    void catalog.fetchNextPage();
                  }}
                >
                  {catalog.isFetchingNextPage ? 'Загружаем…' : 'Показать ещё вузы'}
                </Button>
              )}
            </>
          )}
        </div>
      )}
      <details className="form-help">
        <summary>О подсказках вузов</summary>
        <p>
          Можно просто написать название. Подсказки помогают заполнить форму, но не подключают
          автоматическое обновление. После выбора проверьте ссылку: она должна вести на нужный
          конкурсный список.
        </p>
        <p>Стрелки ↑ и ↓ переходят к вариантам, Enter выбирает, Escape закрывает подсказки.</p>
        {catalog.data?.pages[0].registryEdition && (
          <p>
            В справочнике используется перечень мониторинга {catalog.data.pages[0].registryEdition}.
            Он охватывает не все вузы и не подтверждает действующий приём.
          </p>
        )}
      </details>
    </div>
  );
}
