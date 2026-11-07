import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// The copied source inventory remains authoritative, including /not-found.
export const routes = Array.from(readFileSync(resolve('SCREEN_INVENTORY.md'),'utf8').matchAll(/^\|[^\n]*?\|\s*`(\/[^`]*)`\s*\|/gm), match => match[1]);
export const widths = [390,768,1024,1280,1440];
export const slug = (route:string) => route === '/' ? 'landing' : route.slice(1).replaceAll('/','__');
