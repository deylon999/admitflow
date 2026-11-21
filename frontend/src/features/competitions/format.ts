export const day = (iso: string) => new Intl.DateTimeFormat('ru-RU', { timeZone: 'Europe/Moscow', dateStyle: 'short', timeStyle: 'short' }).format(new Date(iso));
export const unknown = 'Нет данных';
export const consentName = (value: boolean | null) => value === null ? unknown : value ? 'Есть' : 'Нет';
export const participationName: Record<string, string> = { unknown: unknown, active: 'Участвует', withdrawn: 'Отозвал', enrolled: 'Зачислен' };
