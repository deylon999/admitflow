import { parseExport } from './contracts';
import type { DataExport } from './contracts';
import { instantMicros } from './time';
import { parseStrictJson } from './json';

export const MAX_IMPORT_FILE_BYTES = 8 * 1024 * 1024;

export function parseImportText(text: string, nowMillis = Date.now()): DataExport {
  let data: DataExport;
  try { data = parseExport(parseStrictJson(text)); }
  catch { throw new Error('Файл не содержит корректную выгрузку AdmitFlow. Проверьте формат и расчёты.'); }
  if (!data.watches.length) throw new Error('В этом файле нет сохранённых направлений.');
  const futureLimit = BigInt(Math.trunc(nowMillis)) * 1000n + 300_000_000n;
  const earliest = instantMicros('2000-01-01T00:00:00Z');
  if (instantMicros(data.exportedAt) > futureLimit || data.watches.some(watch => instantMicros(watch.createdAt) < earliest)) {
    throw new Error('Даты файла выходят за допустимые границы. Проверьте часы: экспорт не должен опережать их более чем на 5 минут.');
  }
  return data;
}

export async function importKey(bundle: DataExport): Promise<string> {
  const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify(bundle)));
  return `import-v1-${Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('')}`;
}
