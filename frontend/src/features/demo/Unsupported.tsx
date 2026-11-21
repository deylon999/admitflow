import type { ReactNode } from 'react';
import { Action, Surface } from '../../shared/UI';

export function Unsupported({ children }: {
    children: ReactNode;
}) {
    const demo = new URLSearchParams(location.search).get('mode') === 'demo';
    const params = new URLSearchParams(location.search);
    params.set('mode', demo ? 'live' : 'demo');
    return <><Surface tone="soft" title={demo ? 'Демонстрация интерфейса' : 'Функция пока не подключена'} description={demo ? 'Все цифры и действия ниже — примеры. Они не являются ответом API; данные не сохраняются на сервере.' : 'Для этой функции пока нет продуктового API. Реальные прогнозы и успешные операции не имитируются.'}><Action to={location.pathname + '?' + params.toString() + location.hash}>{demo ? 'Выйти из демо' : 'Посмотреть демо интерфейса'}</Action><Action to="/programs" variant="outline">Реальный каталог ↗</Action></Surface>{demo && children}</>;
}
