import { Button, Card } from '@/shared/ui';
import { Link } from 'react-router';
import { RequestFeedback } from '@/shared/ui';
import { useState } from 'react';
import { ChangeFeed } from '@/features/review-source-changes';
import { ImportData } from '@/features/import-manual-directions';
import { WatchComparison } from '@/features/compare-manual-directions';
import { ManualReport } from '@/features/print-manual-directions';
import { useTrackerModel } from '../model/useTrackerModel';
import { ArchiveDirections } from './ArchiveDirections';
import { CoverageSummary } from './CoverageSummary';
import { TrackerHeading } from './TrackerHeading';
import { TrackerAccess } from './TrackerAccess';
import { TrackerFeedback } from './TrackerFeedback';
import { TrackerFilters } from './TrackerFilters';
import { ManualDirectionsPanel } from './ManualDirectionsPanel';

export default function TrackerPage() {
  const model = useTrackerModel();
  const [panels, setPanels] = useState({ changes: false, coverage: false });
  const {
    privateVisible,
    watches,
    budget,
    directionTotal,
    busy,
    count,
    visible,
    report,
    sessionInfo,
  } = model;
  return (
    <main
      className="container tracker-page"
      id="top"
    >
      <TrackerHeading model={model} />
      <TrackerAccess model={model} />
      <TrackerFeedback model={model} />
      {privateVisible && (
        <div className="tracker-list-heading">
          <div>
            <h2>Сохранённые направления</h2>
            <p className="small-copy">
              {model.directionsError
                ? 'Часть направлений недоступна'
                : budget.isError
                  ? 'Количество направлений временно недоступно'
                  : budget.data && watches.data
                    ? `${directionTotal} из 20`
                    : 'Проверяем сохранённые направления'}{' '}
              · Цифры ручного ввода обновляете вы.
            </p>
          </div>
          <Button
            variant="ghost"
            type="button"
            disabled={busy || watches.isFetching || model.archive.isFetching || budget.isFetching}
            onClick={() => void model.refreshDirections()}
          >
            {watches.isFetching || model.archive.isFetching || budget.isFetching
              ? 'Обновляем…'
              : 'Обновить направления'}
          </Button>
        </div>
      )}
      {privateVisible && !model.directionsError && !model.directionsLoading && budget.isError && (
        <RequestFeedback
          busy={budget.isFetching}
          onRetry={() => void budget.refetch()}
        >
          Не удалось проверить число сохранённых направлений. Добавление и импорт пока недоступны.
        </RequestFeedback>
      )}
      <TrackerFilters model={model} />
      <ManualDirectionsPanel model={model} />
      {privateVisible && (
        <ArchiveDirections
          suppressLoading={model.directionsLoading}
          suppressLoadError={model.directionsError || model.refreshError}
          onNotice={model.setNotice}
        />
      )}
      <p className="tracker-disclaimer">
        Расчёт описывает положение по введённым данным в одной конкурсной группе. Он не учитывает
        все правила и приоритеты конкретного вуза и не гарантирует зачисление.
      </p>
      {privateVisible && (
        <section
          className="tracker-section"
          aria-labelledby="tracker-history-title"
        >
          <h2 id="tracker-history-title">История и сравнение</h2>
          <p className="small-copy">
            История места — в карточке направления. Здесь можно сравнить направления и изменения
            списков.
          </p>
          {watches.data && <WatchComparison watches={watches.data} />}
          <Card
            as="details"
            className="tracker-disclosure"
            onToggle={(event) => {
              if (event.currentTarget.open) setPanels((current) => ({ ...current, changes: true }));
            }}
          >
            <summary>Изменения сохранённых списков</summary>
            {panels.changes && <ChangeFeed />}
          </Card>
        </section>
      )}
      <section
        className="tracker-section"
        aria-labelledby="tracker-tools-title"
      >
        <h2 id="tracker-tools-title">Дополнительные инструменты</h2>
        <p className="small-copy">Сохранение данных, печать и сведения об источниках.</p>
        {privateVisible && (
          <>
            <Card
              as="details"
              className="tracker-disclosure"
            >
              <summary>Скачать данные и распечатать</summary>
              <p className="small-copy">
                Выгрузка и печать включают ручные направления. Архивные записи скачиваются отдельно
                в своём разделе.
              </p>
              <div className="tracker-data-actions">
                <Button
                  type="button"
                  disabled={busy || !count}
                  onClick={() => {
                    model.setNotice('');
                    model.download.mutate(undefined, {
                      onSuccess: () =>
                        model.setNotice('Файл с направлениями подготовлен для скачивания.'),
                    });
                  }}
                >
                  {model.download.isPending ? 'Готовим файл…' : 'Скачать данные (JSON)'}
                </Button>
                <Button
                  variant="ghost"
                  className="print-action"
                  type="button"
                  disabled={visible.length === 0 || busy}
                  onClick={report.print}
                >
                  Распечатать выбранный список ({visible.length})
                </Button>
              </div>
            </Card>
            <ImportData
              count={directionTotal}
              disabled={
                busy || watches.isPending || watches.isError || budget.isPending || budget.isError
              }
              onDone={(result) =>
                model.setNotice(
                  result.replayed
                    ? 'Этот файл уже импортирован. Повтор не создаёт копий и не восстанавливает удалённое.'
                    : `Импортировано направлений: ${result.importedCount}; сохранений: ${result.snapshotCount}.`,
                )
              }
            />
            <Card
              as="details"
              className="tracker-disclosure"
            >
              <summary>Доступ и удаление данных</summary>
              <p className="small-copy">
                Гостевой доступ действует 30 дней. Очистка cookies удалит доступ. Открытие страницы
                не продлевает срок.
              </p>
              {sessionInfo.data && (
                <p className="small-copy session-deadline">
                  Гостевой доступ до{' '}
                  <time dateTime={sessionInfo.data.expiresAt}>
                    {new Intl.DateTimeFormat('ru-RU', {
                      dateStyle: 'long',
                      timeStyle: 'short',
                    }).format(new Date(sessionInfo.data.expiresAt))}
                  </time>
                  .
                </p>
              )}
              {sessionInfo.isError && !model.directionsError && (
                <RequestFeedback
                  busy={sessionInfo.isFetching}
                  onRetry={() => void sessionInfo.refetch()}
                >
                  Не удалось проверить срок доступа.
                </RequestFeedback>
              )}
              <TrackerAccess
                model={model}
                tools
              />
            </Card>
          </>
        )}
        <Card
          as="details"
          className="tracker-disclosure"
          onToggle={(event) => {
            if (event.currentTarget.open) setPanels((current) => ({ ...current, coverage: true }));
          }}
        >
          <summary>Источники и охват вузов</summary>
          <Link
            className="button button-secondary"
            to="/sources"
          >
            Найти направление в каталоге →
          </Link>
          {panels.coverage && <CoverageSummary />}
        </Card>
      </section>
      {privateVisible && (
        <ManualReport
          watches={visible}
          generatedAt={report.generatedAt}
        />
      )}
    </main>
  );
}
