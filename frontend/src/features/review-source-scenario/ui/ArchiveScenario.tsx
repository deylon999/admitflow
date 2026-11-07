import { Alert, Button } from '@/shared/ui';
import type { SourceGroup } from '@/entities/admission-source';
import { ScenarioComparison } from './ScenarioComparison';
import { useArchiveScenario } from '../model/useArchiveScenario';

export function ArchiveScenario({ id, group }: { id: string; group: SourceGroup }) {
  const {
    showHistory,
    toggleHistory,
    current,
    history,
    refreshDirection,
    retryHistory,
    loadMoreHistory,
  } = useArchiveScenario(id, group);
  const value = current.data;
  const result = value?.result;
  const explanation = value?.explanation;
  return (
    <section
      className="archive-scenario"
      aria-label="Условный сценарий по списку"
    >
      <h4>Условный сценарий по согласиям</h4>
      <ScenarioComparison
        id={id}
        group={group}
      />
      {current.isPending && <p role="status">Загружаем сохранённый сценарий…</p>}
      {current.isError && (
        <Alert
          as="p"
          role="alert"
        >
          Не удалось перечитать сценарий.{' '}
          {value ? 'Ниже показан ранее загруженный результат с его датой.' : ''}{' '}
          <Button
            variant="ghost"

            type="button"
            onClick={() => void current.refetch()}
          >
            Повторить сценарий
          </Button>
        </Alert>
      )}
      {value && !value.available && <p>{value.notice}</p>}
      {value?.available && value.snapshotId !== group.snapshotId ? (
        <p role="status">
          На сервере появился другой снимок.{' '}
          <Button
            variant="ghost"

            type="button"
            onClick={refreshDirection}
          >
            Перечитать карточку направления
          </Button>
        </p>
      ) : (
        result &&
        explanation && (
          <>
            <p
              className="scenario-summary"
              data-state={result.state}
            >
              {explanation.summary}
            </p>
            <p>
              <b>Условия:</b> ваше согласие, неизменный состав списка и число мест. Приоритеты между
              группами не учтены. Официальный результат не рассчитывается.
            </p>
            {result.numbers && (
              <dl className="scenario-numbers">
                <dt>При текущих согласиях</dt>
                <dd>
                  {result.numbers.currentLower === result.numbers.currentUpper
                    ? result.numbers.currentLower
                    : `${result.numbers.currentLower}–${result.numbers.currentUpper}`}
                </dd>
                <dt>Если все выше подадут согласие</dt>
                <dd>{result.numbers.allConsentPlace}</dd>
                <dt>Мест в этой группе</dt>
                <dd>{result.numbers.seats}</dd>
              </dl>
            )}
            <p className="small-copy">
              Снимок {value!.snapshotId} · получен {value!.fetchedAt} · архив {group.year}.
              Обновление самим источником: {value!.sourceUpdatedAt ?? 'неизвестно'}.
            </p>
            {explanation.changes.length > 0 && (
              <div className="scenario-changes">
                <h5>Что изменилось с прошлого расчёта</h5>
                <ul>
                  {explanation.changes.map((text, index) => (
                    <li key={index}>{text}</li>
                  ))}
                </ul>
              </div>
            )}
            <details>
              <summary>Основания и ограничения сценария</summary>
              {explanation.basis.length > 0 && (
                <ul>
                  {explanation.basis.map((text) => (
                    <li key={text}>{text}</li>
                  ))}
                </ul>
              )}
              <ul>
                {explanation.limitations.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ul>
              <p className="small-copy">
                Версия: {result.modelVersion} · объяснение: {explanation.version} · обработано:{' '}
                {value!.assessedAt}.
              </p>
            </details>
          </>
        )
      )}
      {value?.available && (
        <>
          <Button
            variant="ghost"

            type="button"
            aria-expanded={showHistory}
            onClick={toggleHistory}
          >
            История условных сценариев
          </Button>
          {showHistory && (
            <div className="scenario-history">
              {history.isPending && <p role="status">Загружаем версии сценария…</p>}
              {history.isError && (
                <Alert
                  as="p"
                  role="alert"
                >
                  Не удалось загрузить версии.{' '}
                  <Button
                    variant="ghost"

                    type="button"
                    onClick={retryHistory}
                  >
                    Повторить версии сценария
                  </Button>
                </Alert>
              )}
              {history.data && (
                <p className="small-copy">
                  Сохранено версий: {history.data.pages[0].total}. Прошлые результаты не
                  пересчитываются при чтении.
                </p>
              )}
              <ol>
                {history.data?.items.map((item) => (
                  <li
                    key={item.id}
                    id={`scenario-${item.id}`}
                  >
                    <p>
                      <time dateTime={item.fetchedAt!}>{item.fetchedAt}</time> · снимок{' '}
                      {item.snapshotId}
                    </p>
                    <p>{item.explanation?.summary}</p>
                    <p className="small-copy">
                      {item.result?.modelVersion} · обработано {item.assessedAt}
                    </p>
                  </li>
                ))}
              </ol>
              {history.hasNextPage && (
                <Button
                  variant="ghost"

                  type="button"
                  disabled={history.isFetchingNextPage}
                  onClick={loadMoreHistory}
                >
                  Ещё версии сценария
                </Button>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}
