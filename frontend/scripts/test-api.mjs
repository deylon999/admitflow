import { existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';

const backend = resolve('../backend');
const python = process.env.PYTHON ?? ['.venv/Scripts/python.exe', '.venv/bin/python']
  .map(path => resolve(backend, path)).find(path => existsSync(path)) ?? 'python';
const child = spawn(python, ['tests/catalog_runtime.py'], { cwd: backend, stdio: 'inherit' });
child.on('exit', code => process.exit(code ?? 1));
child.on('error', error => { console.error(error.message); process.exit(1); });
process.on('SIGINT', () => child.kill('SIGINT'));
process.on('SIGTERM', () => child.kill('SIGTERM'));
