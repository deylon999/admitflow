import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const manifest=JSON.parse(await readFile('../docs/evidence/frontend-v3-exact/source-manifest.json','utf8'));
const compared=[];
for(const entry of manifest.filter(entry=>entry.path.startsWith('src/')||['index.html','tsconfig.json'].includes(entry.path))) {
  const original=await readFile('../../admitflow-frontend-v3-main/'+entry.path);
  const copied=await readFile(entry.path);
  const expected=entry.path==='src/pages/AppPages.tsx'
    ? original.toString('utf8').replace('  };\r\n  const [title, description, symbol, tone]', '  } as const;\r\n  const [title, description, symbol, tone]').replace('  };\n  const [title, description, symbol, tone]', '  } as const;\n  const [title, description, symbol, tone]')
    : original.toString('utf8');
  if(copied.toString('utf8').replaceAll('\r\n','\n')!==expected.replaceAll('\r\n','\n'))throw Error('Unexpected source change: '+entry.path);
  compared.push({file:entry.path,exactBytes:copied.equals(original),typeOnlyCorrection:entry.path==='src/pages/AppPages.tsx',sha256:createHash('sha256').update(copied).digest('hex')});
}
await writeFile('../docs/evidence/frontend-v3-exact/copied-source-check.json',JSON.stringify(compared,null,2)+'\n');
console.log(`Verified ${compared.length} UI/config files: original content with one type-only correction.`);
