import { useEffect, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { importKey, MAX_IMPORT_FILE_BYTES, parseImportText } from '../lib/import';
import type { DataExport, ImportResult } from '../lib/contracts';

export function ImportData({ count, disabled, onDone }: { count: number; disabled: boolean; onDone: (result: ImportResult) => void }) {
  const [prepared, setPrepared] = useState<{ bundle: DataExport; key: string } | null>(null);
  const [reading, setReading] = useState(false);
  const [error, setError] = useState('');
  const input = useRef<HTMLInputElement>(null);
  const summary = useRef<HTMLElement>(null);
  const selection = useRef(0);
  const client = useQueryClient();
  useEffect(() => () => { selection.current++; }, []);
  const mutation = useMutation({ mutationFn: () => api.importData(prepared!.bundle, prepared!.key), onSuccess: async result => {
    await client.invalidateQueries({ queryKey: ['watches'] });
    await client.invalidateQueries({ queryKey: ['history'] });
    clear();
    onDone(result);
    summary.current?.focus();
  } });
  function clear() {
    selection.current++;
    setPrepared(null);
    setError('');
    if (input.current) input.current.value = '';
  }
  async function select(file?: File) {
    const version = ++selection.current;
    setPrepared(null);
    setError('');
    mutation.reset();
    if (!file) return;
    if (file.size > MAX_IMPORT_FILE_BYTES) { setError('Файл больше 8 МБ. Выберите выгрузку меньшего размера.'); return; }
    setReading(true);
    try {
      const bundle = parseImportText(await file.text());
      const key = await importKey(bundle);
      if (selection.current === version) setPrepared({ bundle, key });
    } catch (error) {
      if (selection.current === version) setError(error instanceof Error ? error.message : 'Не удалось прочитать файл.');
    } finally { if (selection.current === version) setReading(false); }
  }
  const added = prepared?.bundle.watches.length ?? 0;
  const tooMany = count + added > 20;
  return <details className="import-data surface">
    <summary ref={summary}>Восстановить из JSON</summary>
    <p id="import-note" className="small-copy">Выберите свой файл, скачанный из AdmitFlow. Направления добавятся к этой сессии с исходными датами ручного ввода. Данные вузов автоматически не обновятся.</p>
    <div className="field"><label htmlFor="manual-import-file">Файл выгрузки, до 8 МБ</label><input ref={input} id="manual-import-file" type="file" accept="application/json,.json" aria-describedby="import-note" disabled={disabled || reading} onChange={event => void select(event.target.files?.[0])} /></div>
    {reading && <p role="status">Проверяем файл…</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
    {prepared && <div>
      <p role="status">Найдено направлений: {added}; сохранений: {prepared.bundle.watches.reduce((total,watch) => total + watch.history.length,0)}.</p>
      <p className="small-copy">Существующие записи сохранятся. Повтор этого же файла в той же сессии не создаёт новые копии и не восстанавливает удалённые записи.</p>
      {tooMany && <p className="form-error" role="alert">После импорта будет больше 20 направлений. Сначала освободите место.</p>}
      <div className="direction-actions"><button className="button button-primary" type="button" disabled={disabled || tooMany} onClick={() => mutation.mutate()}>{mutation.isPending ? 'Импортируем…' : 'Импортировать файл'}</button><button className="text-button" type="button" disabled={disabled} onClick={clear}>Отменить импорт</button></div>
    </div>}
    {mutation.isError && <p className="form-error" role="alert">{mutation.error instanceof Error ? mutation.error.message : 'Не удалось импортировать файл.'} Повтор использует тот же ключ операции.</p>}
  </details>;
}
