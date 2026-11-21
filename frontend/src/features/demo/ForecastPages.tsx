import { useState } from 'react';
import { Action, PageTitle, Pill, ProbabilityBar, Surface } from '../../shared/UI';
import { programs } from '../../data/demo';
import { SectionHeader } from './SectionHeader';

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
