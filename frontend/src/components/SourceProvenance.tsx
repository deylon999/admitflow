import type { SourceGroup } from '../lib/source-contracts';

const states: Record<string, string> = {
  archived: 'Архивный снимок', fresh: 'Проверка источника актуальна', stale: 'Проверка источника устарела',
  source_error: 'Последняя проверка завершилась ошибкой. Сохранённые факты имеют прежнюю дату.',
  quarantined: 'Новый ответ источника отклонён проверкой качества. Показан прежний проверенный снимок.',
  disabled: 'Сбор источника отключён. Сохранённый снимок остаётся архивом.',
  unsupported: 'Формат источника не поддержан', unknown: 'Состояние проверки не подтверждено',
};
function Time({ value }: { value: string | null }) {
  return value ? <time dateTime={value} title={value}>{new Date(value).toLocaleString('ru-RU')} ({value})</time> : <>неизвестно</>;
}
export function SourceProvenance({ group }: { group: SourceGroup }) {
  return <div className="source-provenance">
    <p role="status">{states[group.sourceState ?? 'unknown'] ?? states.unknown}</p>
    <dl><dt>Снимок</dt><dd>{group.snapshotId ?? 'ещё не получен'}</dd>
      <dt>Получен сервисом</dt><dd><Time value={group.fetchedAt} /></dd>
      <dt>Обновление самим источником</dt><dd><Time value={group.sourceUpdatedAt} /></dd>
      <dt>Последняя проверка источника</dt><dd><Time value={group.lastCheckedAt} /></dd></dl>
    {group.sourceUrl && <a href={group.sourceUrl} target="_blank" rel="noopener noreferrer">Официальный список ↗</a>}
    <p className="small-copy">Проверка доступности не меняет дату снимка. Неизвестная дата источника не заменяется временем загрузки.</p>
  </div>;
}
