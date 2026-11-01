import { parseExport } from './contracts';
import type { DataExport } from './contracts';

export const MAX_IMPORT_FILE_BYTES = 8 * 1024 * 1024;

export function parseImportText(text: string): DataExport {
  let data: DataExport;
  try { data = parseExport(JSON.parse(text)); }
  catch { throw new Error('Файл не содержит корректную выгрузку AdmitFlow. Проверьте формат и расчёты.'); }
  if (!data.watches.length) throw new Error('В этом файле нет сохранённых направлений.');
  return data;
}

export async function importKey(bundle: DataExport): Promise<string> {
  const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify(bundle)));
  return `import-v1-${Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('')}`;
}
