import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { backendPython } from './backend-python.mjs';

const backend = resolve('../backend');
const python = backendPython(backend);
const child = spawn(python, ['tests/catalog_runtime.py'], { cwd: backend, stdio: 'inherit' });
child.on('exit', code => process.exit(code ?? 1));
child.on('error', error => { console.error(error.message); process.exit(1); });
process.on('SIGINT', () => child.kill('SIGINT'));
process.on('SIGTERM', () => child.kill('SIGTERM'));
