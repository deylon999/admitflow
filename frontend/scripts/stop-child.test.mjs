import { spawn } from 'node:child_process';
import { once } from 'node:events';
import assert from 'node:assert/strict';
import test from 'node:test';
import { stopChild } from './stop-child.mjs';

for (const stubborn of [false, true]) {
  test(`owned API shutdown: ${stubborn ? 'ignores stdin and SIGTERM' : 'graceful control'}`, { timeout: 10000 }, async t => {
    const script = stubborn
      ? "process.on('SIGTERM', () => {}); process.stdin.resume(); setInterval(() => {}, 1000); console.log('ready');"
      : "process.stdin.once('data', () => process.exit(0)); console.log('ready');";
    const child = spawn(process.execPath, ['-e', script], { stdio: ['pipe', 'pipe', 'inherit'] });
    t.after(() => { if (child.exitCode === null && child.signalCode === null) child.kill('SIGKILL'); });
    await once(child.stdout, 'data');
    await stopChild(child, { gracefulMs: 100, signalMs: 1000 });
    assert.ok(child.exitCode !== null || child.signalCode !== null);
    if (!stubborn) assert.equal(child.exitCode, 0);
    if (stubborn && process.platform !== 'win32') assert.equal(child.signalCode, 'SIGKILL');
  });
}

test('shutdown accepts absent or already exited child', async () => {
  await stopChild(undefined);
  await stopChild({ pid: 1, exitCode: 0, signalCode: null });
});
