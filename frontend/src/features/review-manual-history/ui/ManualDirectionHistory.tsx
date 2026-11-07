import { Alert, Button } from '@/shared/ui';
import type { Watch } from '@/entities/manual-direction';
import { HistoryComparison } from './HistoryComparison';
import { useManualHistory } from '../model/useManualHistory';

const exactDateFormat = new Intl.DateTimeFormat('ru-RU', {
  dateStyle: 'short',
  timeStyle: 'medium',
});
function exactDate(value: string) {
  return `${exactDateFormat.format(new Date(value))} (${value})`;
}
function errorText(error: unknown) {
  return error instanceof Error ? error.message : 'Не удалось выполнить действие.';
}

export function ManualDirectionHistory({ watch, show }: { watch: Watch; show: boolean }) {
  const history = useManualHistory(watch.id, show, watch.latest.id);
  const snapshots = history.data?.snapshots ?? [];
  const totalSnapshots = history.data?.pages[0]?.total;
  if (!show) return null;
  return (
    <div className="direction-history">
      <h3>История расчётов</h3>
      {totalSnapshots != null && (
        <p className="small-copy">
          Сохранено {totalSnapshots} из 500. Осталось обновлений: {500 - totalSnapshots}.
        </p>
      )}
      {history.isPending ? (
        <p role="status">Загружаем историю…</p>
      ) : (
        <>
          {history.isError && (
            <Alert
              as="p"
              className="form-error"
              role="alert"
            >
              {errorText(history.error)}{' '}
              <Button
                variant="ghost"

                type="button"
                onClick={() =>
                  void (history.isFetchNextPageError ? history.fetchNextPage() : history.refetch())
                }
              >
                Повторить загрузку истории
              </Button>
            </Alert>
          )}
          {snapshots.length > 0 && (
            <>
              <HistoryComparison snapshots={snapshots} />
              <p className="small-copy">
                Загружено {snapshots.length} сохранений. Дата — время ручного ввода.
              </p>
              <p className="small-copy">
                Таблицу можно прокручивать вбок, в том числе стрелками с клавиатуры после перехода в
                неё.
              </p>
              <div
                className="history-scroll"
                tabIndex={0}
                role="region"
                aria-label={`История ${watch.title}`}
              >
                <table>
                  <caption className="visually-hidden">
                    Сохранённые значения и рассчитанное место
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Дата и время</th>
                      <th scope="col">Номер</th>
                      <th scope="col">Вне конкурса</th>
                      <th scope="col">Без согласия</th>
                      <th scope="col">Место</th>
                      <th scope="col">При всех согласиях</th>
                      <th scope="col">Бюджет</th>
                      <th scope="col">Модель</th>
                    </tr>
                  </thead>
                  <tbody>
                    {snapshots.map((snapshot) => (
                      <tr key={snapshot.id}>
                        <td>
                          <time dateTime={snapshot.capturedAt}>
                            {exactDate(snapshot.capturedAt)}
                          </time>
                        </td>
                        <td>{snapshot.values.rank}</td>
                        <td>{snapshot.values.excluded}</td>
                        <td>{snapshot.values.noConsent}</td>
                        <td>{snapshot.calculation.place}</td>
                        <td>{snapshot.calculation.worstPlace}</td>
                        <td>{snapshot.values.seats}</td>
                        <td>{snapshot.modelVersion}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
          {history.hasNextPage && (
            <Button
              variant="ghost"

              type="button"
              disabled={history.isFetchingNextPage}
              onClick={() => void history.fetchNextPage()}
            >
              {history.isFetchingNextPage ? 'Загружаем…' : 'Загрузить ещё'}
            </Button>
          )}
        </>
      )}
    </div>
  );
}
