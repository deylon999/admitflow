import { useState, type ReactNode } from 'react';
import { ApiError, request } from './api';
import { Action, EmptyMessage } from './UI';
export function ResourceState({ loading, error, retry, children, data, hasData = data !== undefined }: {
    loading: boolean;
    error?: Error;
    retry: () => void;
    children: ReactNode;
    data?: unknown;
    hasData?: boolean;
}) {
    const [starting, setStarting] = useState(false);
    const [failure, setFailure] = useState('');
    const expired = error instanceof ApiError && error.status === 401 && error.requiresSession;
    async function start() {
        setStarting(true);
        setFailure('');
        try {
            await request('session', () => null, { method: 'POST' });
        }
        catch (e) {
            setFailure(e instanceof Error ? e.message : 'Не удалось начать сессию.');
        }
        finally {
            setStarting(false);
        }
    }
    if (expired || (!hasData && error))
        return <div role="alert"><EmptyMessage title={expired ? 'Нужен гостевой доступ' : error instanceof ApiError && error.status === 404 ? 'Запись не найдена' : 'Не удалось загрузить данные'} description={error!.message} action={<><button type="button" className="af-action af-action--primary" disabled={starting} onClick={() => void (expired ? start() : retry())}>{starting ? 'Создаём доступ…' : expired ? 'Начать гостевую сессию' : 'Повторить'}</button>{error instanceof ApiError && error.status === 404 && <Action to="/universities">Каталог ↗</Action>}</>}/>{failure && <p>{failure}</p>}</div>;
    if (loading && !hasData)
        return <div role="status"><EmptyMessage title="Загрузка данных" description="Получаем сведения с сервера."/></div>;
    return <>{loading && <p role="status">Обновляем данные…</p>}{error && <p role="alert">Не удалось обновить данные. Показаны предыдущие сведения. <button type="button" className="af-action af-action--outline" onClick={retry}>Повторить</button></p>}{children}</>;
}
