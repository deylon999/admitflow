import { InvalidResponseError } from './contracts';
import { parseScenario } from './scenario-contracts';
import { sourceObject, sourceText, sourceTime, sourceInt } from './source-contracts';
import { instantMicros, compareOpaqueIds } from './time';
export function parseChange(value: unknown) {
  const o = sourceObject(value),
    scenario = parseScenario(o.scenario);
  if (!scenario.available || !scenario.previousId || !scenario.changes.length)
    throw new InvalidResponseError();
  return {
    id: sourceText(o.id, 36),
    title: sourceText(o.title, 500),
    createdAt: sourceTime(o.createdAt),
    seenAt: o.seenAt === null ? null : sourceTime(o.seenAt),
    scenario,
  };
}
export type SourceChange = ReturnType<typeof parseChange>;
export function assertChangeOrder(items: SourceChange[]) {
  const ids = new Set<string>();
  items.forEach((item, index) => {
    const previous = items[index - 1];
    if (
      ids.has(item.id) ||
      (previous &&
        (instantMicros(previous.createdAt) < instantMicros(item.createdAt) ||
          (instantMicros(previous.createdAt) === instantMicros(item.createdAt) &&
            compareOpaqueIds(previous.id, item.id) <= 0)))
    )
      throw new InvalidResponseError();
    ids.add(item.id);
  });
}
export function parseChanges(value: unknown) {
  const o = sourceObject(value);
  if (!Array.isArray(o.items) || o.items.length > 50) throw new InvalidResponseError();
  const items = o.items.map(parseChange),
    total = sourceInt(o.total),
    unreadCount = sourceInt(o.unreadCount),
    nextCursor = o.nextCursor === null ? null : sourceText(o.nextCursor, 36);
  assertChangeOrder(items);
  if (
    total < items.length ||
    unreadCount > total ||
    (nextCursor !== null && nextCursor !== items.at(-1)?.id)
  )
    throw new InvalidResponseError();
  return { items, total, unreadCount, nextCursor };
}
