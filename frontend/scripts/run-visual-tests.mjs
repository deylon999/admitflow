import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
if(!existsSync('../..'+'/admitflow-frontend-v3-main/src/App.tsx'))throw Error('The original sibling React project is required for live comparison.');
const result=spawnSync(process.execPath,['node_modules/@playwright/test/cli.js','test'],{stdio:'inherit',env:{...process.env,COMPARE_REFERENCE:'1'}});
process.exit(result.status ?? 1);
