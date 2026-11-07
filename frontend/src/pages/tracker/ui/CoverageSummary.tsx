import { useQuery } from '@tanstack/react-query';
import { sourceApi } from '@/entities/admission-source';

export function CoverageSummary() {
  const query = useQuery({ queryKey: ['coverage'], queryFn: sourceApi.coverage });
  return (
    <section
      className="coverage-summary surface"
      aria-labelledby="coverage-heading"
    >
      <h2 id="coverage-heading">Покрытие источников</h2>
      {query.isPending ? (
        <p
          className="small-copy"
          role="status"
        >
          Проверяем покрытие…
        </p>
      ) : query.isError ? (
        <p
          className="small-copy"
          role="alert"
        >
          Не удалось проверить покрытие.{' '}
          <button
            className="text-button"
            type="button"
            onClick={() => void query.refetch()}
          >
            Повторить проверку покрытия
          </button>
        </p>
      ) : (
        <>
          <dl className="coverage-numbers">
            <div>
              <dt>Вузов в справочнике</dt>
              <dd>{query.data.catalogUniversities}</dd>
            </div>
            <div>
              <dt>Источников с автоматическим режимом</dt>
              <dd>{query.data.automaticSources}</dd>
            </div>
            <div>
              <dt>Групп со снимками</dt>
              <dd>{query.data.publishedGroups}</dd>
            </div>
          </dl>
          <dl className="coverage-numbers">
            <div>
              <dt>Проверенных включённых источников</dt>
              <dd>{query.data.reviewedSources}</dd>
            </div>
            <div>
              <dt>Групп с проверенным импортом</dt>
              <dd>{query.data.importedGroups}</dd>
            </div>
            <div>
              <dt>Вузов с импортом</dt>
              <dd>{query.data.importedUniversities}</dd>
            </div>
            <div>
              <dt>Групп с условным сценарием</dt>
              <dd>{query.data.conditionalGroups}</dd>
            </div>
          </dl>
          <p className="small-copy">
            Зарегистрировано источников: {query.data.registeredSources}. Опубликовано импортов:{' '}
            {query.data.importedSources}; строк в их текущих снимках: {query.data.importedRows};
            архивных групп: {query.data.archiveImportedGroups}. Условный сценарий не является
            официальным результатом зачисления.
          </p>
          <p className="small-copy">
            Последний импорт получен: {query.data.lastImportedAt ?? 'ещё не было'}. Отчёт
            сформирован: {query.data.generatedAt}. Повторная проверка не меняет дату получения
            прежнего снимка.
          </p>
          <p className="small-copy">
            Свежих групп: {query.data.freshGroups}; архивных: {query.data.archiveGroups}. Справочник
            включает опорный перечень участников мониторинга, включая филиалы; часть организаций в
            него не входит. Наличие в справочнике не означает подключение списков. Это не полный
            автоматический охват вузов России.
          </p>
        </>
      )}
    </section>
  );
}
