import { useState } from 'react';
import type { ReactNode } from 'react';
import { Action, EmptyMessage, Metric, PageTitle, Pill, ProbabilityBar, ProgramCard, Surface } from '../shared/UI';
import { applicantRows, programs, reviews } from '../data/demo';
import { RouteLink } from '../app/RouteLink';

export type AppPageProps = {
  tracked: string[];
  onToggle: (id: string) => void;
};

function SectionHeader({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return <div className="af-section-heading"><h2>{children}</h2>{action}</div>;
}

export function Dashboard({ tracked }: Pick<AppPageProps, 'tracked'>) {
  const saved = programs.filter(p => tracked.includes(p.id));
  return (
    <>
      <PageTitle kicker="КАМПАНИЯ 2027" title="Твои варианты поступления." description="Все направления, прогнозы и изменения — на одном экране." action={<Action to="/app/forecast">Новый прогноз ↗</Action>} />
      <div className="af-grid-metrics">
        <Metric label="Сохранено программ" value={saved.length} hint="в твоём списке" />
        <Metric label="Высокие шансы" value={saved.filter(p => p.chance >= 70).length} hint="из сохранённых направлений" tone="lime" />
        <Metric label="Обновлений за неделю" value="12" hint="условные события" />
        <Metric label="Приёмная кампания" value="2027" hint="год сценария" />
      </div>
      <div className="af-split-grid">
        <div>
          <SectionHeader action={<RouteLink to="/app/watchlist" className="af-text-link">Все направления ↗</RouteLink>}>Твои направления</SectionHeader>
          <div className="af-stack">
            {saved.length ? saved.slice(0, 3).map(item => <ProgramCard key={item.id} item={item} />) : <EmptyMessage title="Список пуст" description="Добавь первое направление, чтобы видеть его здесь." action={<Action to="/app/watchlist/add">Добавить ↗</Action>} />}
          </div>
        </div>
        <div>
          <SectionHeader>Последние события</SectionHeader>
          <Surface className="af-event-list">
            {reviews.map(event => <div className="af-event-list__item" key={event.at}><span className="af-event-list__dot" /><div><small>{event.at}</small><b>{event.title}</b><p>{event.detail}</p></div></div>)}
            <RouteLink to="/app/history" className="af-text-link">Вся история ↗</RouteLink>
          </Surface>
        </div>
      </div>

    </>
  );
}

export function ForecastForm() {
  const [university, setUniversity] = useState(programs[0].id);
  const [examScores, setExamScores] = useState({ math: '91', informatics: '92', russian: '95' });
  const sum = Object.values(examScores).reduce((acc, x) => acc + (Number(x) || 0), 0);
  const setScore = (subject: keyof typeof examScores, value: string) => setExamScores(prev => ({ ...prev, [subject]: value }));

  return (
    <>
      <PageTitle kicker="ШАГ 01 / ВХОДНЫЕ ДАННЫЕ" title="Рассчитай прогноз поступления." description="Начни с собственных баллов и выбранной конкурсной группы." />
      <div className="af-split-grid af-split-grid--form">
        <Surface title="Твоя заявка" description="Выбери условия конкурса и укажи свои баллы.">
          <div className="af-form-grid">
            <label className="af-field af-field--full"><span>ВУЗ И НАПРАВЛЕНИЕ</span><select value={university} onChange={e => setUniversity(e.target.value)}>{programs.map(item => <option key={item.id} value={item.id}>{item.university} — {item.program}</option>)}</select></label>
            <label className="af-field"><span>ГОД ПОСТУПЛЕНИЯ</span><select defaultValue="2027"><option>2027</option><option>2026</option></select></label>
            <label className="af-field"><span>КОНКУРС</span><select defaultValue="Общий конкурс"><option>Общий конкурс</option><option>Отдельная квота</option><option>Целевая квота</option></select></label>
            <div className="af-form-grid__label">БАЛЛЫ ЕГЭ</div>
            {([['math', 'Профильная математика'], ['informatics', 'Информатика'], ['russian', 'Русский язык']] as const).map(([key, name]) => <label className="af-field" key={key}><span>{name}</span><input value={examScores[key]} min="0" max="100" type="number" onChange={e => setScore(key, e.target.value)} /></label>)}
          </div>
          <div className="af-form-footer"><span>Сумма: <b>{sum}</b> баллов</span><Action to="/app/forecast/example">Посмотреть прогноз ↗</Action></div>
        </Surface>
        <Surface tone="blue" className="af-form-side">
          <Pill tone="lime">НА ОСНОВЕ ДАННЫХ</Pill>
          <h2>Твои баллы — только начало.</h2>
          <p>Модель должна учитывать сложность ЕГЭ, реальные конкурсные списки, число бюджетных мест и динамику спроса.</p>
          <div className="af-form-side__graphic"><span>ЕГЭ</span><span>ВУЗ</span><span>КОНКУРС</span></div>
        </Surface>
      </div>
    </>
  );
}

export function ForecastResult() {
  const item = programs[0];
  return (
    <>
      <PageTitle kicker="РЕЗУЛЬТАТ ПРОГНОЗА · ДЕМО" title="Вот как могут выглядеть твои шансы." description={`${item.university} · ${item.program} · Общий конкурс`} action={<Action to="/app/forecast">Изменить данные ↗</Action>} />
      <div className="af-split-grid af-split-grid--result">
        <Surface tone="blue" className="af-spotlight">
          <span className="af-eyebrow">ОЦЕНКА ШАНСОВ</span>
          <strong>74%</strong>
          <p>С учётом выбранной программы и конкурсной ситуации.</p>
          <ProbabilityBar value={74} />
        </Surface>
        <Surface className="af-passing-card">
          <span className="af-eyebrow">ПРОГНОЗ ПРОХОДНОГО</span>
          <strong>{item.expected[0]}–{item.expected[1]}</strong>
          <Pill tone="lime">↓ Сдвиг относительно 2025 года</Pill>
          <div className="af-info-row"><span>Прошлый проходной</span><b>{item.score2025}</b></div>
          <div className="af-info-row"><span>Текущая позиция</span><b>{item.position} из {item.applicants}</b></div>
        </Surface>
      </div>
      <SectionHeader action={<Action to="/app/forecast/method" variant="outline">Подробно о методике ↗</Action>}>Какие факторы учитываются</SectionHeader>
      <div className="af-card-grid-3">
        <Surface tone="blue"><div className="af-feature-icon">▥</div><h3>Сложность ЕГЭ</h3><p>Сопоставляем распределения результатов.</p></Surface>
        <Surface tone="lime"><div className="af-feature-icon">◷</div><h3>Прошлые проходные</h3><p>Смотрим историю по направлению.</p></Surface>
        <Surface tone="orange"><div className="af-feature-icon">♧</div><h3>Конкуренты</h3><p>Учитываем изменения реального списка.</p></Surface>
      </div>

    </>
  );
}

export function ForecastMethod() {
  return (
    <>
      <PageTitle kicker="ПРОЗРАЧНОСТЬ" title="Почему прогноз такой?" description="Что влияет на оценку, а что мы ещё не можем знать." />
      <div className="af-method-grid">
        {[
          ['01', 'Результаты ЕГЭ', 'Сравнение распределений по годам, а не впечатление от сложности варианта.', 'blue'],
          ['02', 'Прошлые проходные', 'Данные прошлых кампаний и их различия по конкретным конкурсным группам.', 'lime'],
          ['03', 'Конкуренция', 'Число мест, участники конкурса, приоритеты и доступные изменения.', 'orange'],
          ['04', 'Уровень доверия', 'Когда данных мало, система должна отказаться от точного числового обещания.', 'violet'],
        ].map(([number, title, desc, tone]) => <Surface key={number} tone={tone as 'blue'|'lime'|'orange'|'violet'}><div className="af-method-number">{number}</div><h2>{title}</h2><p>{desc}</p></Surface>)}
      </div>
      <Surface title="Чего нельзя заключить из списков" description="Отсутствие согласия или низкий приоритет не доказывают, что конкурент уйдёт. А заявления в другие вузы не всегда публично доступны или сопоставимы."><Action to="/app/competitions/mtuci-se/competitors">Посмотреть аналитику конкуренции ↗</Action></Surface>
    </>
  );
}

export function Watchlist({ tracked, onToggle }: AppPageProps) {
  const items = programs.filter(item => tracked.includes(item.id));
  return (
    <>
      <PageTitle kicker="МОИ НАПРАВЛЕНИЯ" title="Один экран вместо пяти сайтов." description="Сохраняй интересующие программы и сравнивай их динамику." action={<Action to="/app/watchlist/add">+ Добавить направление</Action>} />
      {items.length ? <div className="af-program-grid">{items.map(item => <ProgramCard key={item.id} item={item} tracked onToggle={onToggle} />)}</div> : <EmptyMessage title="Пока нет направлений" description="Выбери программу из каталога или добавь её по названию." action={<Action to="/universities">К вузам ↗</Action>} />}
    </>
  );
}

export function AddWatch({ tracked, onToggle }: AppPageProps) {
  const [query, setQuery] = useState('');
  const matches = programs.filter(item => `${item.university} ${item.program}`.toLowerCase().includes(query.toLowerCase()));
  return (
    <>
      <PageTitle kicker="ДОБАВЛЕНИЕ ПРОГРАММЫ" title="Что будем отслеживать?" description="Выбери университет и направление; сохранение работает локально в браузере." />
      <Surface>
        <label className="af-field"><span>ПОИСК ПРОГРАММЫ</span><input value={query} onChange={e => setQuery(e.target.value)} placeholder="МТУСИ, программная инженерия..." /></label>
        <div className="af-program-grid af-program-grid--inside">{matches.map(item => <ProgramCard key={item.id} item={item} tracked={tracked.includes(item.id)} onToggle={onToggle} />)}</div>
      </Surface>
      <Surface tone="lime" title="Не нашёл нужный вуз?" description="В реальном AdmitFlow можно предусмотреть добавление источника вручную. Этот дизайн-кит не подключается к парсерам."><Action to="/app/sources">Статусы источников ↗</Action></Surface>
    </>
  );
}

export function CompetitionList() {
  const [filter, setFilter] = useState('Все');
  const [search, setSearch] = useState('');
  const rows = applicantRows.filter(row => (filter === 'Все' || (filter === 'Ваше заявление' ? row.id === 'ВЫ' : row.status === 'Есть подтверждение')) && row.id.toLowerCase().includes(search.toLowerCase()));
  return (
    <>
      <PageTitle kicker="КОНКУРСНЫЕ СПИСКИ" title="Видишь не только своё место." description="МТУСИ · Программная инженерия · Общий конкурс · Демо" action={<Action to="/app/competitions/mtuci-se/competitors" variant="outline">Анализ конкурентов ↗</Action>} />
      <div className="af-grid-metrics">
        <Metric label="Твоя позиция" value="90" hint="сейчас в списке" tone="lime" />
        <Metric label="Бюджетных мест" value="90" hint="условный сценарий" />
        <Metric label="Участников" value="128" hint="в опубликованной модели" />
        <Metric label="Обновлено" value="11:20" hint="время обновления" />
      </div>
      <Surface title="Участники конкурса">
        <div className="af-table-toolbar">
          <div className="af-tabs">{['Все', 'Ваше заявление', 'Есть подтверждение'].map(tab => <button type="button" className={tab === filter ? 'is-active' : ''} key={tab} onClick={() => setFilter(tab)}>{tab}</button>)}</div>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Найти код" aria-label="Поиск кода абитуриента" />
        </div>
        <div className="af-table-scroll"><table className="af-table"><thead><tr><th>№</th><th>Код поступающего</th><th>Баллы</th><th>Приоритет</th><th>Статус</th></tr></thead><tbody>{rows.map(row => <tr key={row.position} className={row.id === 'ВЫ' ? 'is-me' : ''}><td>{row.position}</td><td>{row.id}</td><td>{row.score}</td><td>{row.priority}</td><td><Pill tone={row.id === 'ВЫ' ? 'blue' : 'gray'}>{row.status}</Pill></td></tr>)}</tbody></table></div>
        <p className="af-caption">Список и статусы в этом интерфейсе вымышлены. Участие в конкурсе не означает окончательный выбор вуза.</p>
      </Surface>
    </>
  );
}

export function Competitors() {
  return (
    <>
      <PageTitle kicker="АНАЛИЗ КОНКУРЕНЦИИ" title="Кто выше — и что действительно известно." description="Прогноз не должен автоматически удалять людей из конкурса из-за отсутствия согласия." />
      <div className="af-split-grid">
        <Surface tone="blue" className="af-spotlight"><span className="af-eyebrow">ПОЗИЦИЙ ВЫШЕ</span><strong>89</strong><p>Условный срез конкурсного списка.</p></Surface>
        <Surface title="Почему это не 89 гарантированных конкурентов">
          <div className="af-info-row"><span>Опубликованные приоритеты</span><b>Частично</b></div>
          <div className="af-info-row"><span>Сведения из других вузов</span><b>Ограниченно</b></div>
          <div className="af-info-row"><span>Поведение людей</span><b>Неизвестно</b></div>
          <div className="af-info-row"><span>Итоговое зачисление</span><b>Не наступило</b></div>
        </Surface>
      </div>
      <div className="af-card-grid-3">
        <Surface tone="lime"><h3>Приоритеты</h3><p>Публичный приоритет — полезный сигнал, но не гарантия выбора.</p></Surface>
        <Surface tone="soft"><h3>Подтверждения</h3><p>Статусы могут измениться до контрольного времени.</p></Surface>
        <Surface tone="orange"><h3>Другие заявления</h3><p>Показываем только законно доступные данные, без персональных досье.</p></Surface>
      </div>
      <Action to="/app/competitions/mtuci-se">Вернуться к списку ↗</Action>
    </>
  );
}

export function Compare() {
  const [selected, setSelected] = useState<string[]>(programs.slice(0, 3).map(item => item.id));
  const list = programs.filter(p => selected.includes(p.id));
  function toggle(id: string) { setSelected(p => p.includes(id) ? p.filter(x => x !== id) : p.length < 4 ? [...p, id] : p); }
  return (
    <>
      <PageTitle kicker="СРАВНЕНИЕ" title="Куда лучше подавать документы?" description="Сравнивай несколько направлений по проходным, местам и условному прогнозу." />
      <div className="af-choice-row">{programs.map(p => <label key={p.id}><input type="checkbox" checked={selected.includes(p.id)} onChange={() => toggle(p.id)} />{p.university}</label>)}</div>
      {list.length ? <div className="af-compare-scroll"><div className="af-compare-grid">
        <div className="af-compare-labels"><b>Университет</b><b>Направление</b><b>Оценка шанса</b><b>Прогноз проходного</b><b>Мест</b><b>Прошлогодний</b><b>Город</b></div>
        {list.map(item => <div key={item.id} className={`af-compare-col ${item.chance > 85 ? 'is-highlighted' : ''}`}><strong>{item.university}</strong><span>{item.program}</span><b className="af-compare-chance">{item.chance}%</b><b>{item.expected[0]}–{item.expected[1]}</b><b>{item.budget}</b><b>{item.score2025}</b><span>{item.city}</span></div>)}
      </div></div> : <EmptyMessage title="Выбери направления" description="Можно сравнить до четырёх вариантов." />}

    </>
  );
}

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

export function ProfilePage() {
  const [name, setName] = useState('Абитуриент');
  const [city, setCity] = useState('Москва');
  const [saved, setSaved] = useState(false);
  return (
    <>
      <PageTitle kicker="МОИ ДАННЫЕ" title="Настрой профиль." description="Добавь актуальные данные для персонального прогноза." />
      <div className="af-split-grid af-split-grid--form">
        <Surface title="Основная информация">
          <div className="af-form-grid">
            <label className="af-field"><span>ИМЯ</span><input value={name} onChange={e => setName(e.target.value)} /></label>
            <label className="af-field"><span>ГОРОД</span><input value={city} onChange={e => setCity(e.target.value)} /></label>
            <label className="af-field"><span>ГОД ПОСТУПЛЕНИЯ</span><select defaultValue="2027"><option>2027</option><option>2026</option></select></label>
          </div>
          <button className="af-action af-action--primary" type="button" onClick={() => setSaved(true)}>Сохранить изменения</button>
          {saved && <div className="af-inline-success">Демо: изменения не сохраняются на сервере.</div>}
        </Surface>
        <Surface tone="lime" title="Твои баллы — твой выбор." description="Добавь результаты, чтобы сравнивать возможные варианты. Изменения в реальной системе должны храниться безопасно." />
      </div>
    </>
  );
}

export function SettingsPage() {
  const [theme, setTheme] = useState('Системная');
  const [notifications, setNotifications] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  return (
    <>
      <PageTitle kicker="НАСТРОЙКИ" title="Управляй своим пространством." description="Уведомления, тема и приватность." />
      <div className="af-split-grid">
        <Surface title="Внешний вид и события">
          <label className="af-field"><span>ТЕМА ИНТЕРФЕЙСА</span><select value={theme} onChange={e => setTheme(e.target.value)}><option>Системная</option><option>Светлая</option><option>Тёмная</option></select></label>
          <label className="af-check"><input type="checkbox" checked={notifications} onChange={e => setNotifications(e.target.checked)} />Показывать изменения по выбранным программам</label>
          <p className="af-caption">Переключение темы показано как UI-сценарий; полная тёмная тема не реализована в этом наборе.</p>
        </Surface>
        <Surface title="Данные и приватность">
          <p>В рабочем продукте нужны экспорт, удаление, безопасное хранение и контроль срока гостевой сессии.</p>
          <button className="af-danger-button" type="button" onClick={() => setShowConfirm(true)}>Очистить мои данные</button>
        </Surface>
      </div>
      {showConfirm && <div className="af-modal-backdrop"><div className="af-modal" role="dialog" aria-modal="true" aria-label="Подтверждение удаления"><h2>Очистить данные?</h2><p>Подтверди действие перед удалением данных.</p><div><button onClick={() => setShowConfirm(false)} type="button">Отмена</button><button onClick={() => setShowConfirm(false)} type="button">Понятно</button></div></div></div>}
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

export function StatusPage({ variant }: { variant: 'empty' | 'error' | 'success' }) {
  const map = {
    empty: ['Нет конкурсных списков', 'По выбранному направлению ещё не опубликованы данные.', '◎', 'soft' as const],
    error: ['Источник временно недоступен', 'Показываем дату последнего успешного обновления. Точный прогноз сейчас недоступен.', '!', 'orange' as const],
    success: ['Направление сохранено', 'Теперь ты можешь отслеживать программу в своём кабинете.', '✓', 'lime' as const],
  } as const;
  const [title, description, symbol, tone] = map[variant];
  return (
    <>
      <PageTitle kicker="СОСТОЯНИЕ ИНТЕРФЕЙСА" title={title} description={description} />
      <Surface tone={tone} className="af-state-panel"><div className="af-state-panel__symbol">{symbol}</div><h2>{title}</h2><p>{description}</p><Action to={variant === 'success' ? '/app/watchlist' : '/universities'}>{variant === 'success' ? 'Мои направления ↗' : 'Вернуться к каталогу ↗'}</Action></Surface>
    </>
  );
}
