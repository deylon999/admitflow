import { Action, PageTitle, Surface } from '../../shared/UI';

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
