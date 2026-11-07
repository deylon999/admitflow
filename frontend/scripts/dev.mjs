import { build, preview } from 'vite';
import { parseArgs } from 'node:util';

// Managed Windows prevents esbuild's dependency optimizer from reading parent
// directories. Vite's Rollup watch build avoids that optimizer, with identical UI.
const {values}=parseArgs({options:{host:{type:'string',default:'0.0.0.0'},port:{type:'string',default:'5173'},strictPort:{type:'boolean',default:true}}});
const output='node_modules/.cache/dev-dist';
const watcher=await build({configFile:false,build:{outDir:output,emptyOutDir:true,watch:{}}});
let server;
watcher.on('event',async event=>{
  if(event.code==='ERROR')console.error(event.error);
  if(event.code==='END'&&!server){
    server=await preview({configFile:false,build:{outDir:output},preview:{host:values.host,port:Number(values.port),strictPort:values.strictPort}});
    server.printUrls();
  }
});
process.on('SIGINT',async()=>{await watcher.close();server?.httpServer.close();process.exit(0);});
