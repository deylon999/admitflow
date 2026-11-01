import { expect, it, vi } from 'vitest';
import { readJsonResponse } from '../src/lib/transport';

it('decodes split UTF8 chunks without losing characters', async () => {
  const bytes = new TextEncoder().encode('{"value":"😀"}');
  const body = new ReadableStream<Uint8Array>({ start(controller) { for (const byte of bytes) controller.enqueue(new Uint8Array([byte])); controller.close(); } });
  expect(await readJsonResponse(new Response(body), new AbortController().signal)).toEqual({ value: '😀' });
});

it('cancels oversized chunks instead of consuming the rest', async () => {
  const cancel = vi.fn();
  const body = new ReadableStream<Uint8Array>({ start(controller) { controller.enqueue(new Uint8Array(17)); }, cancel });
  await expect(readJsonResponse(new Response(body), new AbortController().signal, 16)).rejects.toThrow();
  expect(cancel).toHaveBeenCalledOnce();
});

it('rejects declared oversize and malformed UTF8', async () => {
  await expect(readJsonResponse(new Response('{}', { headers: { 'Content-Length': '999', 'Content-Type': 'application/json' } }), new AbortController().signal, 16)).rejects.toThrow();
  await expect(readJsonResponse(new Response('{}', { headers: { 'Content-Type': 'text/html' } }), new AbortController().signal)).rejects.toThrow();
  await expect(readJsonResponse(new Response(new Uint8Array([0xc0, 0xaf])), new AbortController().signal)).rejects.toThrow();
});

it('abort cancels a body stalled before completion', async () => {
  const controller = new AbortController();
  const cancel = vi.fn();
  const body = new ReadableStream<Uint8Array>({ cancel });
  const result = readJsonResponse(new Response(body), controller.signal);
  controller.abort(new Error('cancelled'));
  await expect(result).rejects.toThrow('cancelled');
  expect(cancel).toHaveBeenCalled();
});
