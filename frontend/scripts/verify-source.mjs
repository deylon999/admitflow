import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const manifest=JSON.parse(await readFile('../docs/evidence/frontend-v3-exact/source-manifest.json','utf8'));
const compared=[];
// Explicitly scoped functional integration; all other original UI remains frozen.
const integrated=['src/App.tsx','src/app/Shell.tsx','src/pages/PublicPages.tsx'];
const demoLabels={
  'src/components/ForecastCard.tsx':['МГУ · Прикладная математика</span>','МГУ · Прикладная математика · демо</span>'],
  'src/components/Calculator.tsx':['Ваш шанс поступить</strong>','Ваш шанс поступить · демо</strong>'],
  'src/shared/UI.tsx':['<span>ОЦЕНКА ШАНСОВ</span>','<span>ШАНСЫ · ДЕМО</span>'],
  'src/pages/AppPages.tsx':['kicker="РЕЗУЛЬТАТ ПРОГНОЗА"','kicker="РЕЗУЛЬТАТ ПРОГНОЗА · ДЕМО"'],
};
for(const entry of manifest.filter(entry=>(entry.path.startsWith('src/')||['index.html','tsconfig.json'].includes(entry.path))&&!integrated.includes(entry.path))) {
  const original=await readFile('../../admitflow-frontend-v3-main/'+entry.path);
  const copied=await readFile(entry.path);
  let expected=entry.path==='src/pages/AppPages.tsx'
    ? original.toString('utf8').replace('  };\r\n  const [title, description, symbol, tone]', '  } as const;\r\n  const [title, description, symbol, tone]').replace('  };\n  const [title, description, symbol, tone]', '  } as const;\n  const [title, description, symbol, tone]')
    : original.toString('utf8');
  if(demoLabels[entry.path]) expected=expected.replace(...demoLabels[entry.path]);
  // Cleanup removes only the unused offline-export route map, not demo UI data.
  if(entry.path==='src/data/demo.ts') expected=expected.split('export const routeLabels: Record<string, string> = {')[0].trimEnd()+'\n';
  if(copied.toString('utf8').replaceAll('\r\n','\n')!==expected.replaceAll('\r\n','\n'))throw Error('Unexpected source change: '+entry.path);
  compared.push({file:entry.path,exactBytes:copied.equals(original),typeOnlyCorrection:entry.path==='src/pages/AppPages.tsx',demoLabelOnly:entry.path in demoLabels,deadRouteMapRemoved:entry.path==='src/data/demo.ts',sha256:createHash('sha256').update(copied).digest('hex')});
}
const directory=process.env.QA_EVIDENCE_DIR ?? 'test-results/evidence';
await mkdir(directory,{recursive:true});
await writeFile(directory+'/design-preservation.json',JSON.stringify({compared,integrated},null,2)+'\n');
console.log(`Verified ${compared.length} UI/config files with four explicit demo labels; three integration compositions excluded.`);
