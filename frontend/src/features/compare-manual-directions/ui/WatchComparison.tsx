import { Card, Input } from '@/shared/ui';
import { useState } from 'react';
import type { Watch } from '@/entities/manual-direction';

const date = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' });

export function WatchComparison({ watches }: { watches: Watch[] }) {
  const [selected, setSelected] = useState<string[]>([]);
  const active = watches.filter((watch) => selected.includes(watch.id));
  if (watches.length < 2) return null;
  function toggle(id: string) {
    setSelected((old) => {
      const current = old.filter((key) => watches.some((watch) => watch.id === key));
      return current.includes(id)
        ? current.filter((key) => key !== id)
        : current.length < 3
          ? [...current, id]
          : current;
    });
  }
  return (
    <Card
      as="details"
      className="watch-comparison"
    >
      <summary>Сравнить направления</summary>
      <fieldset>
        <legend>Выберите от двух до трёх направлений</legend>
        {watches.map((watch) => (
          <label key={watch.id}>
            <Input
              type="checkbox"
              checked={selected.includes(watch.id)}
              disabled={active.length >= 3 && !selected.includes(watch.id)}
              onChange={() => toggle(watch.id)}
            />
            {watch.university} · {watch.title}
          </label>
        ))}
      </fieldset>
      {active.length >= 2 && (
        <p className="comparison-scroll-hint small-copy">
          Прокрутите таблицу вбок, чтобы увидеть остальные направления.
        </p>
      )}
      {active.length < 2 ? (
        <p className="small-copy">Выберите ещё {2 - active.length}, чтобы показать таблицу.</p>
      ) : (
        <div
          className="history-scroll"
          tabIndex={0}
          role="region"
          aria-label="Таблица сравнения направлений"
        >
          <table>
            <caption>Сравнение ручных направлений</caption>
            <thead>
              <tr>
                <th scope="col">Показатель</th>
                {active.map((watch) => (
                  <th
                    scope="col"
                    key={watch.id}
                  >
                    {watch.university}
                    <br />
                    {watch.title}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">Номер в исходном списке</th>
                {active.map((watch) => (
                  <td key={watch.id}>{watch.latest.values.rank}</td>
                ))}
              </tr>
              <tr>
                <th scope="row">Бюджетных мест</th>
                {active.map((watch) => (
                  <td key={watch.id}>{watch.latest.values.seats}</td>
                ))}
              </tr>
              <tr>
                <th scope="row">Текущий ручной сценарий</th>
                {active.map((watch) => (
                  <td key={watch.id}>{watch.latest.calculation.place}</td>
                ))}
              </tr>
              <tr>
                <th scope="row">При согласии всех выше</th>
                {active.map((watch) => (
                  <td key={watch.id}>{watch.latest.calculation.worstPlace}</td>
                ))}
              </tr>
              <tr>
                <th scope="row">Результат сценария</th>
                {active.map((watch) => (
                  <td key={watch.id}>{watch.latest.calculation.status}</td>
                ))}
              </tr>
              <tr>
                <th scope="row">Сохранено вручную</th>
                {active.map((watch) => (
                  <td key={watch.id}>
                    <time dateTime={watch.latest.capturedAt}>
                      {date.format(new Date(watch.latest.capturedAt))}
                    </time>
                  </td>
                ))}
              </tr>
              <tr>
                <th scope="row">Источник</th>
                {active.map((watch) => (
                  <td key={watch.id}>
                    <a
                      href={watch.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Открыть список ↗
                    </a>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
      <p className="small-copy">
        Каждое направление — отдельный конкурс. Места в разных списках не образуют общий рейтинг или
        вероятность. Дата — время вашего ввода, а не обновления официального источника.
      </p>
    </Card>
  );
}
