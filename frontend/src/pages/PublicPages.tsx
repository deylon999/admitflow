import { useState } from 'react';
import { Action, EmptyMessage, PageTitle, Pill, ProgramCard, Surface } from '../shared/UI';
import { programs, examDistributionBySubject } from '../data/demo';
import type { Program } from '../data/demo';

export function UniversityCatalog({ tracked, onToggle }: { tracked: string[]; onToggle: (id: string) => void }) {
  const [search, setSearch] = useState('');
  const [city, setCity] = useState('Все города');
  const filtered = programs.filter(item => {
    const q = search.toLowerCase();
    return (item.universityFull + item.university + item.program + item.code).toLowerCase().includes(q) && (city === 'Все города' || item.city === city);
  });

  return (
    <>
      <PageTitle kicker="КАТАЛОГ ВУЗОВ" title="Найди место, где тебе понравится учиться." description="Вузы, конкурсные программы и прогнозные данные — на одном экране." />
      <div className="af-search-panel">
        <label className="af-field af-field--grow">
          <span>НАЙТИ ВУЗ ИЛИ НАПРАВЛЕНИЕ</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Например, программная инженерия" />
        </label>
        <label className="af-field">
          <span>ГОРОД</span>
          <select value={city} onChange={e => setCity(e.target.value)}>
            <option>Все города</option>
            <option>Москва</option>
            <option>Санкт-Петербург</option>
          </select>
        </label>
        <Action to="/app/compare">Сравнить →</Action>
      </div>
      <div className="af-section-heading"><h2>Направления по твоему запросу</h2><Pill tone="lime">{filtered.length} программ</Pill></div>
      {filtered.length ? (
        <div className="af-program-grid">
          {filtered.map(item => <ProgramCard key={item.id} item={item} tracked={tracked.includes(item.id)} onToggle={onToggle} />)}
        </div>
      ) : <EmptyMessage title="Ничего не нашлось" description="Измени поисковый запрос или выбери другой город." />}
    </>
  );
}

export function ProgramsCatalog({ tracked, onToggle }: { tracked: string[]; onToggle: (id: string) => void }) {
  const [subject, setSubject] = useState('Все предметы');
  const [query, setQuery] = useState('');
  const matches = programs.filter(p => (subject === 'Все предметы' || p.subject === subject) && (p.program + p.university).toLowerCase().includes(query.toLowerCase()));
  return (
    <>
      <PageTitle kicker="ПОДБОР ПРОГРАММ" title="Направление сначала. Вуз — следом." description="Выбирай специальность и сравнивай прогнозные проходные." />
      <div className="af-search-panel">
        <label className="af-field af-field--grow"><span>НАПРАВЛЕНИЕ</span><input placeholder="Поиск по названию или коду" value={query} onChange={e => setQuery(e.target.value)} /></label>
        <label className="af-field"><span>ПРЕДМЕТ</span><select value={subject} onChange={e => setSubject(e.target.value)}><option>Все предметы</option><option>Информатика</option></select></label>
      </div>
      <div className="af-program-grid">{matches.map(item => <ProgramCard item={item} key={item.id} onToggle={onToggle} tracked={tracked.includes(item.id)} />)}</div>
    </>
  );
}

export function UniversityPage() {
  const items = programs.filter(p => p.university === 'МТУСИ');
  return (
    <>
      <div className="af-profile-hero">
        <div><span>УНИВЕРСИТЕТ · МОСКВА</span><h1>МТУСИ</h1><p>Московский технический университет связи и информатики</p><Action to="/app/forecast" variant="lime">Оценить поступление ↗</Action></div>
        <div className="af-profile-hero__circle">М</div>
      </div>
      <div className="af-grid-metrics">
        <Surface tone="lime"><strong className="af-big-number">IT</strong><p>Профиль программ</p></Surface>
        <Surface><strong className="af-big-number">2027</strong><p>Приёмная кампания</p></Surface>
        <Surface><strong className="af-big-number">2027</strong><p>Год поступления</p></Surface>
      </div>
      <div className="af-section-heading"><h2>Программы университета</h2><Pill tone="blue">{items.length} направления</Pill></div>
      <div className="af-program-grid">{items.map(p => <ProgramCard key={p.id} item={p} />)}</div>

    </>
  );
}

export function ProgramDetail({ item = programs[0] }: { item?: Program }) {
  return (
    <>
      <PageTitle kicker={`${item.university} / ${item.code}`} title={item.program} description={`${item.city} · Очная форма · Бюджет · ${item.budget} мест`} action={<Action to="/app/forecast">Проверить мои шансы ↗</Action>} />
      <div className="af-split-grid">
        <Surface tone="blue" className="af-spotlight">
          <span className="af-eyebrow">ПРОГНОЗ ПРОХОДНОГО</span>
          <strong>{item.expected[0]}–{item.expected[1]}</strong>
          <p>Диапазон сценарного прогноза в выбранном конкурсе</p>
        </Surface>
        <Surface title="Параметры приёма">
          <div className="af-info-row"><span>Проходной за 2025 год</span><b>{item.score2025}</b></div>
          <div className="af-info-row"><span>Бюджетных мест</span><b>{item.budget}</b></div>
          <div className="af-info-row"><span>Форма обучения</span><b>Очная</b></div>
          <div className="af-info-row"><span>Конкурс</span><b>Общий</b></div>
        </Surface>
      </div>
      <div className="af-section-heading"><h2>Какие экзамены учитывать</h2></div>
      <div className="af-card-grid-3">
        {['Профильная математика', 'Информатика', 'Русский язык'].map((name, i) => (
          <Surface key={name} tone={i === 1 ? 'lime' : 'soft'}><h3>{name}</h3><p>Минимальные требования уточняются по правилам вуза.</p></Surface>
        ))}
      </div>
      <Surface title="Важно о прогнозах" description="Сложность экзамена влияет на распределение баллов, но итоговый проходной зависит ещё от числа мест и спроса на направление."><Action to="/ege-analytics">Посмотреть аналитику ЕГЭ ↗</Action></Surface>
    </>
  );
}

export function ExamAnalytics() {
  const [exam, setExam] = useState('Информатика');
  const distribution = examDistributionBySubject[exam as keyof typeof examDistributionBySubject];
  const high2026 = distribution.slice(-2).reduce((total, row) => total + row.previous, 0);
  const high2027 = distribution.slice(-2).reduce((total, row) => total + row.current, 0);
  const change = high2027 - high2026;
  return (
    <>
      <PageTitle kicker="АНАЛИТИКА ЕГЭ" title="Как меняется сложность ЕГЭ?" description="Сравни распределение результатов по годам и оцени влияние на проходные баллы." />
      <div className="af-tabs" role="group" aria-label="Выбрать предмет">
        {['Информатика', 'Математика', 'Русский язык'].map(name => <button type="button" key={name} className={exam === name ? 'is-active' : ''} aria-pressed={exam === name} onClick={() => setExam(name)}>{name}</button>)}
      </div>
      <div className="af-split-grid af-split-grid--chart">
        <Surface title={`Распределение баллов · ${exam}`} description="Какая доля участников набрала баллы в каждом диапазоне">
          <div className="af-chart-meta">
            <div className="af-chart-legend" aria-label="Обозначения цветов"><span><i className="af-dot af-dot--blue" /> 2026 год</span><span><i className="af-dot af-dot--red" /> 2027 год</span></div>
            <span className="af-chart-example">Пример данных</span>
          </div>
          <div className="af-chart-unit">Доля участников, %</div>
          <div className="af-distribution-layout">
            <div className="af-distribution-y" aria-hidden="true"><span>30%</span><span>20%</span><span>10%</span><span>0%</span></div>
            <div className="af-distribution-plot">
              <div className="af-distribution-grid" aria-hidden="true"><span /><span /><span /><span /></div>
              <div className="af-distribution-groups">
                {distribution.map(row => (
                  <div className="af-distribution-group" key={row.group}>
                    <div className="af-distribution-bars">
                      <div className="af-distribution-bar af-distribution-bar--2026" style={{ height: `${row.previous / 30 * 100}%` }} title={`2026: ${row.previous}% участников получили ${row.group} баллов`} aria-label={`2026: ${row.previous}%`} />
                      <div className="af-distribution-bar af-distribution-bar--2027" style={{ height: `${row.current / 30 * 100}%` }} title={`2027: ${row.current}% участников получили ${row.group} баллов`} aria-label={`2027: ${row.current}%`} />
                    </div>
                    <span className="af-distribution-label">{row.group}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="af-chart-x-label">Баллы ЕГЭ (из 100)</div>
          <div className="af-chart-insight">Пример: в диапазоне <b>81–100 баллов</b> доля участников изменилась с <b>{high2026}%</b> до <b>{high2027}%</b> ({change > 0 ? '+' : ''}{change} п. п.).</div>
        </Surface>
        <Surface tone="blue" className="af-chart-note">
          <span className="af-eyebrow">ЧТО ПОКАЗЫВАЕТ ГРАФИК</span>
          <h2>Больше высоких баллов — не всегда выше шанс поступить.</h2>
          <p>Синие столбцы — результаты 2026 года, красные — 2027-го. Чем выше столбец, тем больше участников попало в соответствующий диапазон баллов.</p>
          <p>Проходной зависит не только от ЕГЭ, но и от популярности программы, количества бюджетных мест и состава конкурсных списков.</p>
          <Pill tone="lime">СМОТРИ НА ВСЮ КАРТИНУ</Pill>
        </Surface>
      </div>
    </>
  );
}

export function HowItWorks() {
  return (
    <>
      <PageTitle kicker="МЕТОДИКА" title="Не гадание. Данные → прогноз → решение." description="Сервис должен объяснять не только оценку, но и то, на чём она построена." />
      <div className="af-method-grid">
        {[['01', 'Анализируем ЕГЭ', 'Смотрим официальные распределения результатов и изменения между годами.', 'blue'], ['02', 'Сравниваем историю', 'Изучаем прошлые проходные и наборы на конкретные направления.', 'lime'], ['03', 'Учитываем конкурс', 'Баллы, число мест, приоритеты и изменения заявлений.', 'orange'], ['04', 'Оцениваем неопределённость', 'Не показываем точные проценты без статистической проверки.', 'violet']].map(([num, title, desc, tone]) => (
          <Surface key={num} tone={tone as 'blue' | 'lime' | 'orange' | 'violet'}>
            <div className="af-method-number">{num}</div>
            <h2>{title}</h2><p>{desc}</p>
          </Surface>
        ))}
      </div>
      <Surface title="Два этапа прогноза" description="До публикации списков — широкий прогноз проходного. По мере появления заявлений — уточнение на основе текущей конкуренции."><Action to="/app/forecast">Попробовать демо ↗</Action></Surface>
    </>
  );
}

export function FaqPage() {
  const items = [
    ['Что означает шанс поступления?', 'Это прогноз вероятности, а не гарантия. Для реальных процентов нужны достаточные данные и проверенная модель.'],
    ['Почему сложный ЕГЭ может снизить проходной?', 'Если распределение баллов сдвинулось вниз при сопоставимом спросе и числе мест, порог может снизиться, но итог не предопределён.'],
    ['Можно ли видеть заявления других абитуриентов?', 'Только сведения, законно опубликованные в доступных источниках. Не все заявления доступны, а намерения других людей нельзя считать известными.'],
    ['Когда обновится прогноз?', 'После появления проверенных данных. Если источник недоступен, система должна показывать дату последнего успешного обновления.'],
    ['Откуда берутся цифры?', 'Для полноценного прогноза нужны официальная статистика ЕГЭ, данные приёмных комиссий и информация от самого абитуриента.'],
    ['Как проверить точность прогноза?', 'Сравнить предсказания модели с фактическими зачислениями прошлых лет и проверить калибровку вероятностей.'],
  ];
  return (
    <>
      <PageTitle kicker="ПОМОЩЬ" title="Вопросы, на которые нужны ясные ответы." description="Никаких скрытых допущений или обещаний гарантированного поступления." />
      <div className="af-faq-list">
        {items.map(([question, answer]) => <details key={question}><summary>{question}</summary><p>{answer}</p></details>)}
      </div>
      <Surface tone="lime" title="Не нашёл ответ?" description="Проверь методику прогноза и ограничения данных."><Action to="/how-it-works">Как это работает ↗</Action></Surface>
    </>
  );
}
