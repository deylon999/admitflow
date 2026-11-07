/**
 * Dependency-free static previews of EVERY route from the real React tree.
 * This file is not bundled into production. It uses installed global TypeScript
 * to transpile and a minimal JSX renderer only for exporting view snapshots.
 * Application interactions work when running Vite; offline HTML is for inspection.
 */
const fs = require('fs');
const path = require('path');
let ts;
try { ts = require('typescript'); }
catch (_) { ts = require('/opt/nvm/versions/node/v22.16.0/lib/node_modules/typescript'); }

const base = path.resolve(__dirname, '..');
const cache = new Map();
const runtime = {
  jsx: (type, props) => ({ type, props: props || {} }),
  jsxs: (type, props) => ({ type, props: props || {} }),
  Fragment: Symbol.for('react.fragment'),
};
const react = {
  useState(initial) { return [typeof initial === 'function' ? initial() : initial, () => {}]; },
  useEffect() {},
  useMemo(getValue) { return getValue(); },
  useCallback(fn) { return fn; },
  StrictMode: runtime.Fragment,
};

function loader(from, request) {
  if (request === 'react') return react;
  if (request === 'react/jsx-runtime') return runtime;
  if (request.endsWith('.css')) return {};
  if (!request.startsWith('.')) throw new Error('Unknown require: ' + request);
  const target = path.resolve(path.dirname(from), request);
  return run(target.endsWith('.tsx') || target.endsWith('.ts') ? target : target + (fs.existsSync(target + '.tsx') ? '.tsx' : '.ts'));
}
function run(filepath) {
  if (cache.has(filepath)) return cache.get(filepath).exports;
  const source = fs.readFileSync(filepath, 'utf8');
  const result = ts.transpileModule(source, {
    fileName: filepath,
    reportDiagnostics: true,
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
  });
  const errors = (result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error);
  if (errors.length) throw new Error(filepath + ': ' + errors.map(e => ts.flattenDiagnosticMessageText(e.messageText, '\n')).join('; '));
  const module = { exports: {} };
  cache.set(filepath, module);
  new Function('require', 'exports', 'module', result.outputText)(request => loader(filepath, request), module.exports, module);
  return module.exports;
}
const esc = value => String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const voids = new Set(['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']);
const routes = Object.keys(run(path.join(base, 'src/data/demo.ts')).routeLabels);
const routeFile = route => route === '/' ? 'index.html' : route.slice(1).replace(/\//g, '__') + '.html';
function staticHref(value) {
  const [pathPart, hash] = value.split('#');
  if (!value.startsWith('/')) return value;
  return './' + routeFile(pathPart || '/') + (hash ? '#' + hash : '');
}
function html(el) {
  if (el === null || typeof el === 'undefined' || typeof el === 'boolean') return '';
  if (Array.isArray(el)) return el.map(html).join('');
  if (typeof el === 'string' || typeof el === 'number') return esc(el);
  if (typeof el.type === 'function') return html(el.type(el.props));
  if (el.type === runtime.Fragment) return html(el.props.children);
  if (typeof el.type !== 'string') throw new Error('Unexpected JSX type: ' + String(el.type));
  let attrs = '';
  const p = el.props || {};
  for (let [key, value] of Object.entries(p)) {
    if (['children','key','ref','dangerouslySetInnerHTML'].includes(key) || key.startsWith('on') || value == null || typeof value === 'function') continue;
    if (key === 'className') key = 'class';
    if (key === 'htmlFor') key = 'for';
    if (key === 'defaultValue') key = 'value';
    if (key === 'defaultChecked') key = 'checked';
    if (key === 'href' && typeof value === 'string') value = staticHref(value);
    if (typeof value === 'boolean') { if (value) attrs += ' ' + key; continue; }
    if (key === 'style' && typeof value === 'object') {
      const css = Object.entries(value).map(([k,v]) => k.replace(/[A-Z]/g, x=>'-'+x.toLowerCase())+':'+(typeof v==='number' && k !== 'opacity' && k !== 'zIndex' ? v + 'px' : v)).join(';');
      attrs += ' style="' + esc(css) + '"';
      continue;
    }
    attrs += ' ' + key + '="' + esc(value) + '"';
  }
  if (voids.has(el.type)) return `<${el.type}${attrs}>`;
  return `<${el.type}${attrs}>${html(p.children)}</${el.type}>`;
}
const App = run(path.join(base, 'src/App.tsx')).default;
const dir = path.join(base, 'preview');
fs.mkdirSync(dir, { recursive: true });
let count = 0;
for (const route of routes) {
  global.window = {
    location: { pathname: route, href: 'http://localhost:5173' + route, origin: 'http://localhost:5173' },
    localStorage: { getItem() { return null; }, setItem() {} },
  };
  const rendered = html({ type: App, props: {} });
  const document = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(route)} — AdmitFlow</title><link rel="stylesheet" href="../src/styles.css"><link rel="stylesheet" href="../src/internal.css"></head><body>${rendered}${route === '/' ? '<script src="./interactions.js"></script>' : ''}</body></html>`;
  fs.writeFileSync(path.join(dir, routeFile(route)), document, 'utf8');
  count++;
}
const labels = run(path.join(base, 'src/data/demo.ts')).routeLabels;
const links = routes.map((route, i) => `<a href="./${routeFile(route)}"><span>${String(i+1).padStart(2,'0')}</span><b>${esc(labels[route])}</b><small>${esc(route)}</small><strong>↗</strong></a>`).join('\n');
const listing = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Все страницы AdmitFlow</title><style>body{margin:0;background:#f6f8ff;color:#10131f;font:15px Inter,Arial,sans-serif}.wrap{max-width:1100px;padding:44px 24px;margin:auto}h1{font-size:clamp(35px,5vw,66px);letter-spacing:-.05em;line-height:1;margin:20px 0 14px}p{color:#6c7488;line-height:1.5;margin-bottom:32px}.pill{display:inline-block;border-radius:99px;background:#b8f500;font-size:12px;font-weight:800;padding:9px 13px}nav{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}nav a{display:grid;grid-template-columns:38px 1fr auto;gap:8px 13px;padding:20px;border-radius:16px;background:#fff;text-decoration:none;color:inherit;box-shadow:0 1px 0 #dce2f1}nav a span{color:#2147ff;font-weight:900}nav a b{font-size:17px}nav a small{grid-column:2;font-size:12px;color:#768095}nav a strong{grid-column:3;grid-row:1/3;font-size:21px;color:#2147ff}@media(max-width:650px){nav{grid-template-columns:1fr}.wrap{padding:25px 15px}}</style></head><body><div class="wrap"><span class="pill">29 страниц · Desktop + Mobile</span><h1>AdmitFlow.<br>Весь дизайн-кит.</h1><p>Выбери любую страницу. Офлайн-превью без npm — ссылки работают между HTML файлами. Числа демонстрационные.</p><nav>${links}</nav></div></body></html>`;
fs.writeFileSync(path.join(dir,'all-pages.html'),listing,'utf8');
console.log(`Created ${count} offline pages + navigator in ${dir}`);
