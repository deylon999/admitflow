import { readdir, readFile, writeFile } from 'node:fs/promises';
const files=await readdir('test-results/exact-metrics');
const cases=await Promise.all(files.filter(file=>file.endsWith('.json')).map(async file=>JSON.parse(await readFile('test-results/exact-metrics/'+file,'utf8'))));
if(cases.length!==145||cases.some(row=>row.pixelDiff!==0||row.overflow!==0||!row.textEqual))throw Error(`Incomplete/failed visual matrix: ${cases.length}/145`);
cases.sort((a,b)=>a.width-b.width||a.route.localeCompare(b.route));
const summary={routes:29,widths:[390,768,1024,1280,1440],comparisons:cases.length,maxDiffPixels:0,maxColorThreshold:0,passed:true,cases};
await writeFile('../docs/evidence/frontend-v3-exact/visual-results.json',JSON.stringify(summary,null,2)+'\n');
console.log('145/145 live React comparisons passed; 0 different pixels, identical text and no page overflow.');
