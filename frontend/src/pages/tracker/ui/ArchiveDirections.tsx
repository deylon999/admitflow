import { useRef } from 'react';
import { ArchiveScenario } from '@/features/review-source-scenario';
import { ArchiveHistory } from '@/features/review-archive-history';
import { SourceProvenance } from '@/entities/admission-source';
import { DeleteConfirmation, Alert, Button, Card, Badge } from '@/shared/ui';
import { useArchiveDirections } from '../model/useArchiveDirections';

export function ArchiveDirections() {
  const refresh = useRef<HTMLButtonElement>(null);
  const focusAfterDelete = () =>
    requestAnimationFrame(() =>
      (refresh.current ?? document.querySelector<HTMLElement>('main h1'))?.focus(),
    );
  const { deleting, setDeleting, download, remove, access, records, sourceReads, refreshFacts } =
    useArchiveDirections(focusAfterDelete);
  if (access !== 'active') return null;
  if (records.isPending) return <p role="status">Загружаем архивные направления…</p>;
  if (!records.data?.length && !records.isError) return null;
  return (
    <section
      className="archive-directions"
      aria-labelledby="archive-directions-title"
    >
      <h2 id="archive-directions-title">Сохранённые записи источников</h2>
      <p className="small-copy">
        Здесь факты архивных списков. Ручной JSON и печатный отчёт ниже относятся только к ручным
        направлениям.
      </p>
      {records.isError && (
        <Alert
          as="p"
          role="alert"
        >
          Не удалось перечитать архивные направления.{' '}
          {records.data ? 'Показаны ранее загруженные датированные записи.' : ''}
        </Alert>
      )}
      <Button
        variant="ghost"
        ref={refresh}
        type="button"

        disabled={sourceReads > 0 || refreshFacts.isPending}
        onClick={() => refreshFacts.mutate()}
      >
        Перечитать сохранённые факты
      </Button>
      {refreshFacts.isError && sourceReads === 0 && (
        <Alert
          as="p"
          role="alert"
        >
          Не удалось перечитать все сохранённые факты. Ранее загруженные записи сохраняют свои даты;
          повторите обновление.
        </Alert>
      )}
      <Button
        variant="ghost"
        type="button"

        disabled={download.isPending || !records.data?.length}
        onClick={() => download.mutate()}
      >
        Скачать текущие архивные факты (JSON)
      </Button>
      <p className="small-copy">
        Архивный файл содержит текущие датированные факты ваших записей. История доступна в
        карточках. Файл не восстанавливает гостевой доступ и не импортируется как ручной расчёт.
      </p>
      {download.isError && (
        <Alert
          as="p"
          role="alert"
        >
          {download.error.message}
        </Alert>
      )}
      <div className="source-catalog-list">
        {records.data?.map((item) => (
          <Card
            as="article"
            className="source-catalog-card archive-direction-card"
            key={item.id}
          >
            <Badge>Архив · {item.group.year}</Badge>
            <h3>{item.group.title}</h3>
            <p>{item.group.universityName}</p>
            {item.candidate ? (
              <>
                <p>
                  Строка официального списка: <strong>{item.candidate.officialRank}</strong> ·
                  баллы: {item.candidate.score ?? 'неизвестно'}
                </p>
                <p>
                  Согласие в источнике:{' '}
                  {item.candidate.consent === null
                    ? 'неизвестно'
                    : item.candidate.consent
                      ? 'да'
                      : 'нет'}{' '}
                  · приоритет: {item.candidate.priority ?? 'неизвестно'}
                </p>
              </>
            ) : (
              <p>{item.notice}</p>
            )}
            <SourceProvenance group={item.group} />
            <p className="small-copy">
              Архив не является текущей кампанией. Вероятность и официальный результат зачисления не
              рассчитываются.
            </p>
            <ArchiveScenario
              id={item.id}
              group={item.group}
            />
            <ArchiveHistory id={item.id} />
            <Button
              variant="ghost"
              id={`delete-archive-${item.id}`}
              type="button"
              className="delete-link"
              disabled={remove.isPending}
              onClick={() => {
                remove.reset();
                setDeleting(item.id);
              }}
            >
              Удалить архивную запись
            </Button>
            {deleting === item.id && (
              <DeleteConfirmation
                text="Удалить эту архивную запись и её личную историю? Общий снимок источника останется."
                label="Да, удалить архивную запись"
                disabled={remove.isPending}
                onCancel={() => {
                  setDeleting(null);
                  requestAnimationFrame(() =>
                    document.getElementById(`delete-archive-${item.id}`)?.focus(),
                  );
                }}
                onConfirm={() => remove.mutate(item.id)}
              />
            )}
            {deleting === item.id && remove.isError && (
              <Alert
                as="p"
                role="alert"
              >
                {remove.error.message}
              </Alert>
            )}
          </Card>
        ))}
      </div>
    </section>
  );
}
