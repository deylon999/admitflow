import { Link } from 'react-router';
import type { TrackerModel } from '../model/useTrackerModel';

export function TrackerHeading({ model }: { model: TrackerModel }) {
  const { expired, directionTotal, busy, privateVisible, sessionInfo, editor } = model;
  const { addButton, pageHeading, openForm } = editor;
  return (
    <>
      <div className="tracker-page-heading">
        <div>
          <p className="eyebrow">Ваша приёмная кампания</p>
          <h1
            ref={pageHeading}
            tabIndex={-1}
          >
            Мои направления
          </h1>
          <p className="section-description">
            Сравнивайте место и сохраняйте изменения в одном окне.
          </p>
          <Link
            data-router-link
            to="/sources"
          >
            Посмотреть источники и архивные группы →
          </Link>
        </div>
        <button
          ref={addButton}
          className="button button-primary"
          type="button"
          disabled={expired || directionTotal >= 20 || busy}
          onClick={(event) => openForm('new', event.currentTarget)}
        >
          Добавить направление
        </button>
      </div>
      <div className="tracker-info">
        <span className="tag">Ручной режим</span>
        <p>
          Направления доступны в этом браузере 30 дней с начала сессии. Очистка cookies удалит
          доступ. Автоматическое обновление вузов ещё не подключено.
        </p>
      </div>
      {privateVisible && sessionInfo.data && (
        <p className="small-copy session-deadline">
          Гостевой доступ до{' '}
          <time
            dateTime={sessionInfo.data.expiresAt}
            title={sessionInfo.data.expiresAt}
          >
            {new Intl.DateTimeFormat('ru-RU', { dateStyle: 'long', timeStyle: 'short' }).format(
              new Date(sessionInfo.data.expiresAt),
            )}
          </time>
          . Открытие страницы не продлевает срок.
        </p>
      )}
      {privateVisible && sessionInfo.isError && (
        <p className="small-copy">Не удалось проверить точную дату окончания доступа.</p>
      )}
    </>
  );
}
