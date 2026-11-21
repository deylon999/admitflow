import { RouteLink } from '../../app/RouteLink';
import { useResource } from '../../shared/resource';
import { ResourceState } from '../../shared/ResourceState';
import { PageTitle, Surface } from '../../shared/UI';
import { coverage } from './decode';

export function LiveSources() {
    const r = useResource('coverage', coverage);
    return <><PageTitle kicker="API · ИСТОЧНИКИ" title="Источники и доступность данных" description="Каталог и свежий импорт — разные показатели. Архив не является текущей кампанией."/><ResourceState {...r} hasData={!!r.data}>{r.data && <Surface title="Подтверждённые сведения"><p>Вузов в каталоге: {r.data.catalogUniversities}</p><p>Зарегистрировано источников: {r.data.registeredSources}</p><p>Свежих групп: {r.data.freshGroups}</p><p>Архивных групп: {r.data.archiveGroups}</p><time dateTime={r.data.generatedAt}>{r.data.generatedAt}</time><p><RouteLink to="/app/coverage">Покрытие вузов России ↗</RouteLink></p></Surface>}</ResourceState></>;
}
