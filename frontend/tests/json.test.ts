import { expect, it } from 'vitest';
import { parseStrictJson } from '../src/lib/json';
import { parseImportText } from '../src/lib/import';

it('rejects duplicate decoded keys before parsing discards them', () => {
  for (const text of ['{"a":1,"a":2}', '{"a":1,"\\u0061":2}', '{"a":[{"x":1,"x":2}]}']) expect(() => parseStrictJson(text)).toThrow();
  expect(() => parseImportText('{"formatVersion":"other","formatVersion":"manual-export-v1","watches":[]}')).toThrow('корректную выгрузку');
});
it('bounds nesting and rejects nonfinite and malformed tokens', () => {
  for (const text of ['[NaN]', '[Infinity]', '[1e999]', '[01]', '[1,]', '{"x":1,}', 'true false', '['.repeat(65) + '0' + ']'.repeat(65)]) expect(() => parseStrictJson(text)).toThrow();
  expect(parseStrictJson('['.repeat(64) + '0' + ']'.repeat(64))).toBeDefined();
});
it('preserves ordinary JSON values, escaped strings and prototype keys', () => {
  const text = '{"text":"[\\\"{}]","__proto__":{"ok":true},"a":[null,-1.5e2,false],"nested":{"text":"independent"}}';
  expect(parseStrictJson(text)).toEqual(JSON.parse(text));
});
