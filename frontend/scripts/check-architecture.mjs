import { readdirSync, readFileSync } from 'node:fs';
import { basename, extname, relative, resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';
import ts from 'typescript';

const layers = ['app', 'pages', 'widgets', 'features', 'entities', 'shared'];

function location(file) {
  if (file === 'main.tsx') return { layer: 'entry', root: 'entry', rank: -1 };
  const [layer, slice] = file.split('/');
  if (!layers.includes(layer)) return null;
  if (['app', 'shared'].includes(layer)) {
    if (layer === 'shared' && !file.includes('/', 7)) return null;
    return { layer, root: layer, rank: layers.indexOf(layer) };
  }
  if (!slice || slice.includes('.') || file.split('/').length < 3) return null;
  return { layer, root: `${layer}/${slice}`, slice, rank: layers.indexOf(layer) };
}

// Paths are relative to src and include the resolved target, so aliases and
// relative imports are subject to the same rules. Type-only edges also count.
export function analyzeGraph(files, edges) {
  const errors = new Set();
  const graph = new Map(files.map((file) => [file, []]));
  for (const file of files) {
    if (!location(file)) errors.add(`Invalid source layout: ${file}`);
  }
  for (const { from, to } of edges) {
    graph.get(from)?.push(to);
    const source = location(from);
    const target = location(to);
    if (!source || !target) continue;
    const crossEntity =
      source.layer === 'entities' &&
      target.layer === 'entities' &&
      to === `${target.root}/@x/${source.slice}.ts`;
    if (source.rank > target.rank) errors.add(`Upward dependency: ${from} -> ${to}`);
    if (source.rank === target.rank && source.root !== target.root && !crossEntity) {
      errors.add(`Sibling slice dependency: ${from} -> ${to}`);
    }
    if (source.root === target.root) {
      if (from !== `${source.root}/index.ts` && to === `${source.root}/index.ts`) {
        errors.add(`Slice imports its own public barrel: ${from} -> ${to}`);
      }
      continue;
    }
    const publicTarget =
      crossEntity ||
      (target.layer === 'shared' ? basename(to) === 'index.ts' : to === `${target.root}/index.ts`);
    if (!publicTarget) errors.add(`External deep import: ${from} -> ${to}`);
  }
  const visiting = new Set();
  const visited = new Set();
  const stack = [];
  function visit(file) {
    if (visiting.has(file)) {
      errors.add(`Dependency cycle: ${[...stack.slice(stack.indexOf(file)), file].join(' -> ')}`);
      return;
    }
    if (visited.has(file)) return;
    visiting.add(file);
    stack.push(file);
    for (const target of graph.get(file) ?? []) visit(target);
    stack.pop();
    visiting.delete(file);
    visited.add(file);
  }
  for (const file of files) visit(file);
  return [...errors];
}

function sourceFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = resolve(directory, entry.name);
    return entry.isDirectory() ? sourceFiles(path) : /\.[cm]?[jt]sx?$/.test(path) ? [path] : [];
  });
}

function collectGraph(root) {
  const configPath = ts.findConfigFile(root, ts.sys.fileExists, 'tsconfig.json');
  if (!configPath) throw new Error('TypeScript configuration not found');
  const config = ts.readConfigFile(configPath, ts.sys.readFile);
  if (config.error)
    throw new Error(ts.flattenDiagnosticMessageText(config.error.messageText, '\n'));
  const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys, root);
  const src = resolve(root, 'src');
  const paths = sourceFiles(src);
  const canonical = (path) =>
    process.platform === 'win32' ? resolve(path).toLowerCase() : resolve(path);
  const names = new Map(
    paths.map((path) => [canonical(path), relative(src, path).split(sep).join('/')]),
  );
  const files = [...names.values()];
  const edges = [];
  const errors = [];
  const cache = ts.createModuleResolutionCache(root, canonical, parsed.options);
  for (const path of paths) {
    const from = names.get(canonical(path));
    const source = ts.createSourceFile(
      path,
      readFileSync(path, 'utf8'),
      ts.ScriptTarget.Latest,
      true,
    );
    function dependency(specifier) {
      const resolved = ts.resolveModuleName(
        specifier,
        path,
        parsed.options,
        ts.sys,
        cache,
      ).resolvedModule;
      const to = resolved && names.get(canonical(resolved.resolvedFileName));
      if (to) edges.push({ from, to });
      else if (!resolved && (specifier.startsWith('.') || specifier.startsWith('@/'))) {
        if (!['.css', '.svg', '.png', '.jpg', '.woff2'].includes(extname(specifier))) {
          errors.push(`Unresolved internal dependency: ${from} -> ${specifier}`);
        }
      }
    }
    function inspect(node) {
      if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier) {
        if (ts.isStringLiteral(node.moduleSpecifier)) dependency(node.moduleSpecifier.text);
      } else if (
        ts.isCallExpression(node) &&
        node.expression.kind === ts.SyntaxKind.ImportKeyword &&
        node.arguments.length &&
        ts.isStringLiteral(node.arguments[0])
      )
        dependency(node.arguments[0].text);
      else if (
        ts.isImportTypeNode(node) &&
        ts.isLiteralTypeNode(node.argument) &&
        ts.isStringLiteral(node.argument.literal)
      ) {
        dependency(node.argument.literal.text);
      }
      if (ts.isExportDeclaration(node) && node.moduleSpecifier && !node.exportClause) {
        errors.push(`Wildcard public export: ${from}`);
      }
      ts.forEachChild(node, inspect);
    }
    inspect(source);
  }
  for (const entry of readdirSync(src, { withFileTypes: true })) {
    if (entry.isDirectory() ? !layers.includes(entry.name) : entry.name !== 'main.tsx') {
      errors.push(`Unexpected src root entry: ${entry.name}`);
    }
  }
  return { files, edges, errors: [...errors, ...analyzeGraph(files, edges)] };
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  const result = collectGraph(process.cwd());
  if (result.errors.length) {
    process.stderr.write(`${result.errors.join('\n')}\n`);
    process.exitCode = 1;
  } else {
    process.stdout.write(
      `FSD architecture valid: ${result.files.length} modules, ${result.edges.length} dependencies; no cycles.\n`,
    );
  }
}
