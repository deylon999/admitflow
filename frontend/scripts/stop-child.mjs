// Bound teardown even when a test API ignores stdin or SIGTERM.
function waitForExit(child, milliseconds) {
  if (child.exitCode !== null || child.signalCode !== null) return Promise.resolve(true);
  return new Promise(done => {
    const finish = exited => {
      clearTimeout(timer);
      child.off('exit', onExit);
      done(exited);
    };
    const onExit = () => finish(true);
    const timer = setTimeout(() => finish(false), milliseconds);
    child.once('exit', onExit);
  });
}

export async function stopChild(child, { gracefulMs = 5000, signalMs = 2000 } = {}) {
  if (!child?.pid || child.exitCode !== null || child.signalCode !== null) return;
  // A child exiting concurrently may close stdin before the control line lands.
  child.stdin?.on('error', () => {});
  child.stdin?.end('stop\n');
  if (await waitForExit(child, gracefulMs)) return;
  child.kill('SIGTERM');
  if (await waitForExit(child, signalMs)) return;
  child.kill('SIGKILL');
  if (!await waitForExit(child, signalMs)) throw Error('Test API did not exit after SIGKILL.');
}
