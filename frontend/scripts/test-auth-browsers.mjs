// Each engine owns a fresh native-PG runtime/schema/mailbox/clock and evidence dir.
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { rmSync } from 'node:fs';
if (!process.env.TEST_DATABASE_URL || process.env.QA_API_TARGET) throw Error('A disposable TEST_DATABASE_URL and owned auth runtime are required.');
let unsuccessful = false;
for (const browser of ['chromium', 'firefox', 'webkit']) {
    console.log(`Native PostgreSQL auth acceptance: ${browser}`);
    const results = process.env.AUTH_BROWSER_RESULTS_ROOT ? resolve(process.env.AUTH_BROWSER_RESULTS_ROOT, browser) : resolve(`test-results/auth-${browser}`);
    // A startup failure must not leave a previous passing JSON report usable.
    rmSync(resolve(results, 'results.json'), { force: true });
    rmSync(resolve(results, 'frontend.xml'), { force: true });
    const child = spawn(process.execPath, ['scripts/test.mjs'], { stdio: 'inherit', env: {
        ...process.env, AUTH_BROWSER_E2E: '1', AUTH_TEST_BROWSER: browser,
        AUTH_TEST_RESULTS_DIR: results,
    } });
    const code = await new Promise((done, reject) => { child.once('error', reject); child.once('exit', code => done(code ?? 1)); });
    if (code !== 0) unsuccessful = true;
}
process.exitCode = unsuccessful ? 1 : 0;
