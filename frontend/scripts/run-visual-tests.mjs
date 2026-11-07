import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
if(!existsSync('../..'+'/admitflow-frontend-v3-main/src/App.tsx'))throw Error('The original sibling React project is required for live comparison.');
const result=spawnSync(process.execPath,['scripts/test.mjs','--visual'],{stdio:'inherit'});
process.exit(result.status ?? 1);
