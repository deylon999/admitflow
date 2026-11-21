import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import ts from 'typescript';

const directory = 'src/features/demo';
const locations = {
  Dashboard: 'Dashboard.tsx',
  ForecastForm: 'ForecastPages.tsx', ForecastResult: 'ForecastPages.tsx', ForecastMethod: 'ForecastPages.tsx',
  Watchlist: 'WatchlistPages.tsx', AddWatch: 'WatchlistPages.tsx',
  CompetitionList: 'CompetitionPages.tsx', Competitors: 'CompetitionPages.tsx',
  Compare: 'Compare.tsx',
  ProfilePage: 'PreferencesPages.tsx', SettingsPage: 'PreferencesPages.tsx',
  HistoryPage: 'ReferencePages.tsx', NotificationsPage: 'ReferencePages.tsx', SourcesPage: 'ReferencePages.tsx',
  StatusPage: 'StatusPage.tsx', SectionHeader: 'SectionHeader.tsx', AppPageProps: 'types.ts',
};
const allowedImports = new Set(['react', '../../shared/UI', '../../data/demo', '../../app/RouteLink', './SectionHeader', './types']);
const canonical = text => text.replaceAll('\r\n', '\n');

function source(text, path) {
  const parsed = ts.createSourceFile(path, canonical(text), ts.ScriptTarget.Latest, true);
  if (parsed.parseDiagnostics.length) throw Error(`Invalid source: ${path}`);
  return parsed;
}

function declarations(parsed, checkImports = false) {
  const result = new Map();
  for (const node of parsed.statements) {
    if (ts.isImportDeclaration(node)) {
      if (checkImports && (!node.importClause || !allowedImports.has(node.moduleSpecifier.text))) {
        throw Error(`Unexpected Demo import: ${node.getText(parsed)}`);
      }
      continue;
    }
    if (!(ts.isFunctionDeclaration(node) || ts.isTypeAliasDeclaration(node)) || !node.name || result.has(node.name.text)) {
      throw Error(`Unexpected declaration in ${parsed.fileName}: ${node.getText(parsed)}`);
    }
    result.set(node.name.text, node.getText(parsed));
  }
  return result;
}

// The historical exact-source verifier still checks every page declaration.
// Only import boundaries and SectionHeader's module-local export are new.
export async function verifyAppPageModules(expectedText, frontend = '.') {
  const path = 'src/pages/AppPages.tsx';
  const expected = declarations(source(expectedText, path));
  if (expected.size !== Object.keys(locations).length || Object.keys(locations).some(name => !expected.has(name))) {
    throw Error('Unexpected declaration inventory in the reference AppPages module');
  }
  const facadeText = await readFile(resolve(frontend, path), 'utf8');
  const facade = source(facadeText, path);
  const exports = new Set();
  for (const node of facade.statements) {
    if (!ts.isExportDeclaration(node) || !node.exportClause || !ts.isNamedExports(node.exportClause) || !node.moduleSpecifier) {
      throw Error('AppPages must contain explicit re-exports only');
    }
    for (const item of node.exportClause.elements) {
      const name = item.name.text;
      const file = locations[name];
      if (!file || name === 'SectionHeader' || item.propertyName || item.isTypeOnly || exports.has(name) ||
        node.isTypeOnly !== (name === 'AppPageProps') || node.moduleSpecifier.text !== `../features/demo/${file.replace(/\.tsx?$/, '')}`) {
        throw Error(`Unexpected AppPages re-export: ${name}`);
      }
      exports.add(name);
    }
  }
  if (exports.size !== expected.size - 1) throw Error('AppPages re-export set changed');

  const modules = [];
  const hash = createHash('sha256').update(facadeText);
  for (const file of new Set(Object.values(locations))) {
    const modulePath = `${directory}/${file}`;
    const text = await readFile(resolve(frontend, modulePath), 'utf8');
    const actual = declarations(source(text, modulePath), true);
    const names = Object.keys(locations).filter(name => locations[name] === file);
    if (actual.size !== names.length) throw Error(`Unexpected declaration inventory: ${modulePath}`);
    for (const name of names) {
      const original = (name === 'SectionHeader' ? 'export ' : '') + expected.get(name);
      if (actual.get(name) !== original) throw Error(`Unexpected source change: ${modulePath} (${name})`);
    }
    hash.update(modulePath).update(text);
    modules.push({ path: modulePath, declarations: names });
  }
  return { modules, sha256: hash.digest('hex') };
}
