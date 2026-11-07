import { Card, Alert, Button } from '@/shared/ui';
import { Link } from 'react-router';
import { useChangeFeed } from '../model/useChangeFeed';

export function ChangeFeed() {
  const { access, feed, seen, refreshChanges, loadMoreChanges, markSeen } = useChangeFeed();
  if (access !== 'active') return null;
  return (
    <Card
      as="section"
      className="change-feed"
      aria-labelledby="changes-title"
    >
      <h3 id="changes-title">Изменения в ваших списках</h3>
      <p>
        Изменения сохранённых условных сценариев. Архивные данные не описывают текущую приёмную
        кампанию.
      </p>
      {feed.isPending && <p role="status">Загружаем изменения…</p>}
      {feed.isError && (
        <Alert
          as="p"
          role="alert"
        >
          Не удалось перечитать изменения.{' '}
          <Button
            variant="secondary"
            type="button"
            onClick={refreshChanges}
          >
            Повторить изменения
          </Button>
        </Alert>
      )}
      {feed.data && (
        <p role="status">
          Непрочитанных: {feed.data.pages[0].unreadCount} · всего: {feed.data.pages[0].total}
        </p>
      )}
      {feed.data?.items.length === 0 && (
        <p>Новых изменений пока нет. При первом сохранении записи уведомление не создаётся.</p>
      )}
      <Button
        variant="ghost"
        type="button"

        disabled={feed.isFetching}
        onClick={refreshChanges}
      >
        Перечитать изменения
      </Button>
      {seen.isError && (
        <Alert
          as="p"
          role="alert"
        >
          {seen.error.message} Повторите отметку прочтения явно.
        </Alert>
      )}
      <ol>
        {feed.data?.items.map((item) => (
          <li key={item.id}>
            <h4>{item.title}</h4>
            <p>{item.scenario.explanation?.summary}</p>
            <ul>
              {item.scenario.explanation?.changes.map((text, index) => (
                <li key={index}>{text}</li>
              ))}
            </ul>
            <p className="small-copy">
              Снимок получен: {item.scenario.fetchedAt}. Изменение обработано: {item.createdAt}.
            </p>
            <Link
              to={`/tracker?direction=${encodeURIComponent(item.scenario.subscriptionId)}&assessment=${encodeURIComponent(item.scenario.id!)}`}
            >
              Сравнить сохранённые версии
            </Link>
            {item.seenAt ? (
              <p className="small-copy">Прочитано: {item.seenAt}</p>
            ) : (
              <Button
                variant="ghost"
                type="button"

                disabled={seen.isPending}
                onClick={() => markSeen(item.id)}
              >
                Отметить прочитанным
              </Button>
            )}
          </li>
        ))}
      </ol>
      {feed.hasNextPage && (
        <Button
          variant="secondary"
          type="button"
          disabled={feed.isFetchingNextPage}
          onClick={loadMoreChanges}
        >
          Ещё изменения
        </Button>
      )}
    </Card>
  );
}
