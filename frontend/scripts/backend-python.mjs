import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

export function backendPython(backend) {
  return process.env.PYTHON ?? ['.venv/Scripts/python.exe', '.venv/bin/python']
    .map(path => resolve(backend, path)).find(path => existsSync(path)) ?? 'python';
}
