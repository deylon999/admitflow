// A loopback-only HTTP driver for the disposable catalogue benchmark.
import http from 'node:http';
import { performance } from 'node:perf_hooks';

const [origin, search, count, duration, warm] = process.argv.slice(2);
const url = new URL('/api/v1/catalog/programs', origin);
if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1') {
  throw new Error('Expected an owned loopback server');
}
url.search = new URLSearchParams(JSON.parse(search));
const concurrency = Number(count);
const seconds = Number(duration);
if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 50 || !Number.isFinite(seconds) || seconds < 1 || seconds > 60) {
  throw new Error('Unexpected benchmark dimensions');
}
const agent = new http.Agent({ keepAlive: true, maxSockets: concurrency, maxFreeSockets: concurrency });

function request() {
  const start = performance.now();
  return new Promise((resolve) => {
    const req = http.get(url, { agent, timeout: 10000 }, (res) => {
      const parts = [];
      res.on('data', (chunk) => parts.push(chunk));
      res.on('error', (error) => resolve({ ms: performance.now() - start, status: null, transportError: error.code }));
      res.on('end', () => {
        const ms = performance.now() - start;
        try {
          const total = res.statusCode === 200 ? JSON.parse(Buffer.concat(parts)).total : null;
          resolve({ ms, status: res.statusCode, total });
        } catch {
          resolve({ ms, status: null, transportError: 'invalid_json' });
        }
      });
    });
    req.on('timeout', () => req.destroy(new Error('request_timeout')));
    req.on('error', (error) => resolve({ ms: performance.now() - start, status: null, transportError: error.code ?? error.message }));
  });
}

async function phase(seconds) {
  const started = performance.now();
  const deadline = started + seconds * 1000;
  const minSamples = Math.max(2, Math.ceil(50 / concurrency));
  const workers = Array.from({ length: concurrency }, async () => {
    const samples = [];
    while (samples.length < minSamples || performance.now() < deadline) samples.push(await request());
    return samples;
  });
  const samples = (await Promise.all(workers)).flat();
  return { seconds: (performance.now() - started) / 1000, samples };
}

try {
  for (let i = 0; i < 10; i++) {
    const response = await request();
    if (response.status !== 200) throw new Error(`Warmup failed: ${JSON.stringify(response)}`);
  }
  const concurrentWarmup = warm === '1' ? (await phase(2)).samples : null;
  const measured = await phase(seconds);
  if (concurrentWarmup) measured.concurrentWarmup = concurrentWarmup;
  console.log(JSON.stringify(measured));
} finally {
  agent.destroy();
}
