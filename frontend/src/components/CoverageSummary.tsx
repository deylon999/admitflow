import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export function CoverageSummary() {
  const query = useQuery({ queryKey: ['coverage'], queryFn: api.coverage });
  return <section className="coverage-summary surface" aria-labelledby="coverage-heading">
    <h2 id="coverage-heading">Покрытие источников</h2>
    {query.isPending ? <p className="small-copy" role="status">Проверяем покрытие…</p> : query.isError ? <p className="small-copy" role="alert">Не удалось проверить покрытие. <button className="text-button" type="button" onClick={() => void query.refetch()}>Повторить проверку покрытия</button></p> : <>
      <dl className="coverage-numbers"><div><dt>Вузов в справочнике</dt><dd>{query.data.catalogUniversities}</dd></div><div><dt>Подключённых автоисточников</dt><dd>{query.data.automaticSources}</dd></div><div><dt>Групп со снимками</dt><dd>{query.data.publishedGroups}</dd></div></dl>
      <p className="small-copy">Свежих групп: {query.data.freshGroups}; архивных: {query.data.archiveGroups}. Вуз в справочнике может работать только с ручным вводом. Это не полный охват вузов России.</p>
    </>}
  </section>;
}
