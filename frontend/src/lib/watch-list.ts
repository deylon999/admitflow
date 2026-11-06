import type { Watch } from './contracts';
import { instantMicros } from './time';

export type WatchOrder = 'updated' | 'university' | 'created';
export function selectWatches(
  watches: Watch[],
  query: string,
  state: string,
  order: WatchOrder,
): Watch[] {
  const words = query.trim().toLocaleLowerCase('ru').split(/\s+/).filter(Boolean);
  return watches
    .filter((watch) => {
      const name = `${watch.university} ${watch.title}`.toLocaleLowerCase('ru');
      return (
        words.every((word) => name.includes(word)) &&
        (state === 'all' || watch.latest.calculation.state === state)
      );
    })
    .sort((a, b) => {
      if (order === 'university')
        return (
          a.university.localeCompare(b.university, 'ru') ||
          a.title.localeCompare(b.title, 'ru') ||
          a.id.localeCompare(b.id)
        );
      const time = (watch: Watch) =>
        instantMicros(order === 'created' ? watch.createdAt : watch.latest.capturedAt);
      return time(a) === time(b) ? a.id.localeCompare(b.id) : time(a) > time(b) ? -1 : 1;
    });
}
