import { PageTitle, Pill, Surface } from '../../shared/UI';
import { reviews } from '../../data/demo';

export function HistoryPage() {
  return (
    <>
      <PageTitle kicker="ИСТОРИЯ" title="Как меняется ситуация." description="Причины обновлений и динамика по выбранным направлениям." />
      <div className="af-split-grid">
        <Surface title="Последние изменения">
          <div className="af-timeline">{reviews.map(event => <div className="af-timeline__item" key={event.at}><span className="af-timeline__dot" /><div><small>{event.at}</small><h3>{event.title}</h3><p>{event.detail}</p></div></div>)}</div>
        </Surface>
        <Surface title="Иллюстрация динамики" description="Проходной и изменение оценки по датам, вымышленные значения.">
          <div className="af-history-chart">{[58, 64, 60, 74, 69, 83, 79, 88].map((v, i) => <div key={i}><span style={{ height: `${v}%` }} /><small>{i + 1}</small></div>)}</div>
          <p className="af-caption">Реальный график строится только на сохранённых срезах с датой и источником.</p>
        </Surface>
      </div>
    </>
  );
}

export function NotificationsPage() {
  const items = [
    ['Конкурсный список обновился', 'Изменилось положение в очереди', 'Сегодня, 11:20', 'lime'],
    ['Новые заявления', 'Появились участники с высокими баллами', 'Вчера, 19:40', 'white'],
    ['Прогноз пересчитан', 'Оценка изменилась', '3 дня назад', 'white'],
    ['Источник временно недоступен', 'Последняя удачная проверка была вчера', '5 дней назад', 'orange'],
  ];
  return (
    <>
      <PageTitle kicker="УВЕДОМЛЕНИЯ" title="Ничего важного не пропускай." description="Все события по интересующим направлениям в одном месте." />
      <div className="af-notification-list">{items.map(([title, description, date, tone]) => <Surface tone={tone as 'lime'|'white'|'orange'} key={title}><span>{date}</span><h3>{title}</h3><p>{description}</p></Surface>)}</div>
    </>
  );
}

export function SourcesPage() {
  const sources = [
    ['Конкурсные списки', 'Приёмная комиссия университета', 'Источники вузов'],
    ['Статистика ЕГЭ', 'Рособрнадзор / официальные публикации', 'Годовые отчёты'],
    ['Исторический проходной', 'Приказы о зачислении и архивы вузов', 'Несколько кампаний'],
    ['Ввод абитуриента', 'Баллы и сохранённые направления', 'Локальный источник'],
  ];
  return (
    <>
      <PageTitle kicker="ДАННЫЕ И ДОСТОВЕРНОСТЬ" title="Откуда берутся числа?" description="В рабочем интерфейсе каждый прогноз должен ссылаться на проверенный источник." />
      <div className="af-source-list">{sources.map(([name, body, type], i) => <Surface key={name}><div className="af-source-index">0{i + 1}</div><h3>{name}</h3><p>{body}</p><Pill tone="gray">{type}</Pill></Surface>)}</div>

    </>
  );
}
