import { useRef } from 'react';
import { useSearchParams } from 'react-router';
import { ArchiveScenario } from '@/features/review-source-scenario';
import { ArchiveHistory } from '@/features/review-archive-history';
import { SourceProvenance } from '@/entities/admission-source';
import { DeleteConfirmation, Alert, Button, Card, Badge, RequestFeedback } from '@/shared/ui';
import { requestErrorText } from '@/shared/api';
import { useArchiveDirections } from '../model/useArchiveDirections';

export function ArchiveDirections({
  suppressLoadError = false,
  suppressLoading = false,
  onNotice,
}: {
  suppressLoadError?: boolean;
  suppressLoading?: boolean;
  onNotice?: (notice: string) => void;
}) {
  const [params] = useSearchParams();
  const refresh = useRef<HTMLButtonElement>(null);
  const focusAfterDelete = () => {
    onNotice?.('Архивное направление удалено.');
    requestAnimationFrame(() => document.querySelector<HTMLElement>('main h1')?.focus());
  };
  const { deleting, setDeleting, download, remove, access, records, sourceReads, refreshFacts } =
    useArchiveDirections(focusAfterDelete);
  if (access !== 'active') return null;
  if (records.isPending)
    return suppressLoading ? null : (
      <RequestFeedback>Загружаем архивные направления…</RequestFeedback>
    );
  if (suppressLoadError && records.isError && !records.data?.length) return null;
  if (!records.data?.length && !records.isError) return null;
  return (
    <section
      className="archive-directions"
      aria-labelledby="archive-directions-title"
    >
      <h2 id="archive-directions-title">Архивные направления</h2>
      <p className="small-copy">
        Сохранённые списки прошлых кампаний. Они не показывают ваше текущее место.
      </p>
      {records.isFetching && records.data && (
        <RequestFeedback>Обновляем архивные направления…</RequestFeedback>
      )}
      {records.isError && !suppressLoadError && (
        <RequestFeedback
          busy={records.isFetching}
          onRetry={() => void records.refetch()}
        >
          Не удалось загрузить архивные направления.{' '}
          {records.data
            ? 'Показаны ранее загруженные данные.'
            : 'Ручные направления доступны выше.'}
        </RequestFeedback>
      )}
      <details className="tracker-disclosure archive-tools">
        <summary>Инструменты архива</summary>
        <Button
          variant="ghost"
          ref={refresh}
          type="button"

          disabled={sourceReads > 0 || refreshFacts.isPending}
          onClick={() =>
            refreshFacts.mutate(undefined, {
              onSuccess: () => onNotice?.('Архивные данные обновлены.'),
            })
          }
        >
          {refreshFacts.isPending ? 'Обновляем архив…' : 'Перечитать сохранённые факты'}
        </Button>
        <Button
          variant="ghost"
          type="button"

          disabled={download.isPending || !records.data?.length}
          onClick={() =>
            download.mutate(undefined, {
              onSuccess: () => onNotice?.('Файл архива подготовлен для скачивания.'),
            })
          }
        >
          {download.isPending ? 'Готовим файл…' : 'Скачать текущие архивные факты (JSON)'}
        </Button>
        <p className="small-copy">
          Архивный файл содержит текущие датированные факты ваших записей. История доступна в
          карточках. Файл не восстанавливает гостевой доступ и не импортируется как ручной расчёт.
        </p>
      </details>
      {refreshFacts.isError && !records.isError && sourceReads === 0 && (
        <RequestFeedback
          onRetry={() => refreshFacts.mutate()}
          busy={refreshFacts.isPending}
        >
          Не удалось перечитать все сохранённые факты. Показаны прежние данные с исходными датами.
          Повторите обновление в инструментах архива.
        </RequestFeedback>
      )}
      {download.isError && (
        <Alert
          as="p"
          role="alert"
        >
          Не удалось подготовить файл. {requestErrorText(download.error)}
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
            <p className="small-copy">
              Бюджетных мест в архиве: {item.group.seats ?? 'неизвестно'}
            </p>
            <p className="small-copy">
              Дата архивного снимка:{' '}
              {item.group.fetchedAt ? (
                <time dateTime={item.group.fetchedAt}>
                  {new Intl.DateTimeFormat('ru-RU', {
                    dateStyle: 'short',
                    timeStyle: 'short',
                  }).format(new Date(item.group.fetchedAt))}
                </time>
              ) : (
                'неизвестна'
              )}
            </p>
            <details className="direction-details">
              <summary>Данные списка и источник</summary>
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
                Архив не является текущей кампанией. Вероятность и официальный результат зачисления
                не рассчитываются.
              </p>
            </details>
            <details
              className="direction-details"
              open={params.get('direction') === item.id || undefined}
            >
              <summary>Расчёт и история архива</summary>
              <ArchiveScenario
                id={item.id}
                group={item.group}
              />
              <ArchiveHistory id={item.id} />
            </details>
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
