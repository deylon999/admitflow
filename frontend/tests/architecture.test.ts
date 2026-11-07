import { describe, expect, it } from 'vitest';
import { analyzeGraph } from '../scripts/check-architecture.mjs';

const edge = (from: string, to: string) => ({ from, to });

describe('FSD dependency boundaries', () => {
  it('allows descending imports through public APIs and internal slice modules', () => {
    const files = [
      'main.tsx',
      'app/index.ts',
      'app/ui/App.tsx',
      'pages/tracker/index.ts',
      'pages/tracker/ui/TrackerPage.tsx',
      'features/edit-direction/index.ts',
      'entities/manual-direction/index.ts',
      'shared/api/index.ts',
      'shared/api/client.ts',
      'shared/lib/time/index.ts',
    ];
    expect(
      analyzeGraph(files, [
        edge('main.tsx', 'app/index.ts'),
        edge('app/index.ts', 'app/ui/App.tsx'),
        edge('app/ui/App.tsx', 'pages/tracker/index.ts'),
        edge('pages/tracker/index.ts', 'pages/tracker/ui/TrackerPage.tsx'),
        edge('pages/tracker/ui/TrackerPage.tsx', 'features/edit-direction/index.ts'),
        edge('features/edit-direction/index.ts', 'entities/manual-direction/index.ts'),
        edge('entities/manual-direction/index.ts', 'shared/api/index.ts'),
        edge('shared/api/index.ts', 'shared/api/client.ts'),
        edge('shared/api/client.ts', 'shared/lib/time/index.ts'),
      ]),
    ).toEqual([]);
  });

  it('rejects upward dependencies even through a public API', () => {
    const files = ['shared/api/index.ts', 'features/edit-direction/index.ts'];
    expect(analyzeGraph(files, [edge(files[0], files[1])])).toContain(
      'Upward dependency: shared/api/index.ts -> features/edit-direction/index.ts',
    );
  });

  it('rejects sibling feature imports even through their public APIs', () => {
    const files = ['features/import-directions/index.ts', 'features/edit-direction/index.ts'];
    expect(analyzeGraph(files, [edge(files[0], files[1])])).toContain(
      'Sibling slice dependency: features/import-directions/index.ts -> features/edit-direction/index.ts',
    );
  });

  it('rejects external deep imports independently of whether an alias or relative path resolved them', () => {
    const files = ['pages/tracker/index.ts', 'entities/manual-direction/model/contracts.ts'];
    expect(analyzeGraph(files, [edge(files[0], files[1])])).toContain(
      'External deep import: pages/tracker/index.ts -> entities/manual-direction/model/contracts.ts',
    );
  });

  it('rejects shared infrastructure deep imports from higher layers', () => {
    const files = ['entities/manual-direction/index.ts', 'shared/api/client.ts'];
    expect(analyzeGraph(files, [edge(files[0], files[1])])).toContain(
      'External deep import: entities/manual-direction/index.ts -> shared/api/client.ts',
    );
  });

  it('permits an explicit entity cross-reference only for its named consumer', () => {
    const files = ['entities/archive/index.ts', 'entities/source/@x/archive.ts'];
    expect(analyzeGraph(files, [edge(files[0], files[1])])).toEqual([]);
    const other = 'entities/other/index.ts';
    expect(analyzeGraph([...files, other], [edge(other, files[1])])).toContain(
      'Sibling slice dependency: entities/other/index.ts -> entities/source/@x/archive.ts',
    );
  });

  it('detects an internal dependency cycle that layer ordering alone cannot catch', () => {
    const files = ['entities/source/model/facts.ts', 'entities/source/model/history.ts'];
    expect(analyzeGraph(files, [edge(files[0], files[1]), edge(files[1], files[0])])).toContain(
      'Dependency cycle: entities/source/model/facts.ts -> entities/source/model/history.ts -> entities/source/model/facts.ts',
    );
  });

  it('rejects importing a slice public barrel from its own internals', () => {
    const files = ['features/edit-direction/model/editor.ts', 'features/edit-direction/index.ts'];
    expect(analyzeGraph(files, [edge(files[0], files[1])])).toContain(
      'Slice imports its own public barrel: features/edit-direction/model/editor.ts -> features/edit-direction/index.ts',
    );
  });

  it.each(['lib/api.ts', 'components/Calculator.tsx', 'features/index.ts'])(
    'rejects the legacy or unsliced source layout %s',
    (file) => expect(analyzeGraph([file], [])).toContain(`Invalid source layout: ${file}`),
  );
});
