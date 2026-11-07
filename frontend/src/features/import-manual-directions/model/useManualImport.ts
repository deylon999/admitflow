import { useEffect, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { manualDirectionApi } from '@/entities/manual-direction';
import type { DataExport, ImportResult } from '@/entities/manual-direction';
import { decodeImportBytes, importKey, MAX_IMPORT_FILE_BYTES, parseImportText } from './import';

export function useManualImport(count: number, onDone: (result: ImportResult) => void) {
  const [prepared, setPrepared] = useState<{ bundle: DataExport; key: string } | null>(null);
  const [reading, setReading] = useState(false);
  const [error, setError] = useState('');
  const input = useRef<HTMLInputElement>(null);
  const summary = useRef<HTMLElement>(null);
  const selection = useRef(0);
  const client = useQueryClient();
  useEffect(
    () => () => {
      selection.current++;
    },
    [],
  );
  const mutation = useMutation({
    mutationFn: () => manualDirectionApi.importData(prepared!.bundle, prepared!.key),
    onSuccess: async (result) => {
      await client.invalidateQueries({ queryKey: ['watches'] });
      await client.invalidateQueries({ queryKey: ['history'] });
      await client.invalidateQueries({ queryKey: ['direction-budget'] });
      clear();
      onDone(result);
      summary.current?.focus();
    },
  });
  function clear() {
    selection.current++;
    mutation.reset();
    setReading(false);
    setPrepared(null);
    setError('');
    if (input.current) input.current.value = '';
  }
  async function select(file?: File) {
    const version = ++selection.current;
    setPrepared(null);
    setError('');
    mutation.reset();
    setReading(false);
    if (!file) return;
    if (file.size > MAX_IMPORT_FILE_BYTES) {
      setError('Файл больше 8 МБ. Выберите выгрузку меньшего размера.');
      return;
    }
    setReading(true);
    try {
      const bytes = await file.arrayBuffer();
      if (selection.current !== version) return;
      const bundle = parseImportText(decodeImportBytes(bytes));
      const key = await importKey(bundle);
      if (selection.current === version) setPrepared({ bundle, key });
    } catch (error) {
      if (selection.current === version)
        setError(error instanceof Error ? error.message : 'Не удалось прочитать файл.');
    } finally {
      if (selection.current === version) setReading(false);
    }
  }
  const added = prepared?.bundle.watches.length ?? 0;
  const tooMany = count + added > 20;

  return { prepared, reading, error, input, summary, mutation, clear, select, added, tooMany };
}
