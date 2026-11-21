"""Report sizes, SHA-256 duplicates and known evidence references in a Git tree."""

import argparse
from collections import defaultdict
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = 'docs/evidence'
BASELINES = f'{EVIDENCE}/visual-baselines.sha256'
REQUIRED = {
    f'{EVIDENCE}/regression.md': 'backend/tests/test_domain_regression.py',
    f'{EVIDENCE}/kan-214-controls.json': 'scripts/check_auth_acceptance.py',
    f'{EVIDENCE}/frontend-v3-exact/source-manifest.json': 'frontend/scripts/verify-source.mjs',
}
WIDTHS = (390, 768, 1024, 1280, 1440)
CATALOG_PAGES = ('universities', 'university', 'programs', 'program')
LINKS = re.compile(r'''\]\(\s*<?([^>\s)]+)>?|\b(?:href|src)=["']([^"']+)["']''')


def tree(ref):
    output = subprocess.check_output(
        ['git', 'ls-tree', '-r', '-z', '-l', '--end-of-options', ref], cwd=ROOT,
    )
    files = {}
    for entry in output.split(b'\0'):
        if not entry:
            continue
        metadata, path = entry.split(b'\t', 1)
        _, kind, oid, size = metadata.decode('ascii').split()
        if kind == 'blob':
            files[path.decode('utf-8')] = (oid, int(size))
    return files


@contextmanager
def read_blobs():
    with subprocess.Popen(
        ['git', 'cat-file', '--batch'], cwd=ROOT,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    ) as git:
        def read(oid):
            git.stdin.write(f'{oid}\n'.encode('ascii'))
            git.stdin.flush()
            _, kind, size = git.stdout.readline().split()
            if kind != b'blob':
                raise ValueError(f'Expected blob {oid}, found {kind!r}')
            data = git.stdout.read(int(size))
            if git.stdout.read(1) != b'\n':
                raise ValueError(f'Incomplete blob {oid}')
            return data

        try:
            yield read
        finally:
            git.stdin.close()


def evidence_links(source, content):
    for line_number, line in enumerate(content.splitlines(), 1):
        for match in LINKS.finditer(line):
            href = match.group(1) or match.group(2)
            # The catalog gallery builds its URLs in JS. Check its 20 inputs above.
            if '${' in href:
                continue
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            href = unquote(url.path)
            target = posixpath.normpath(
                href.lstrip('/') if href.startswith('/')
                else posixpath.join(posixpath.dirname(source), href),
            )
            if target == EVIDENCE or target.startswith(f'{EVIDENCE}/'):
                yield line_number, target


def check_references(files, digests, read):
    required = dict(REQUIRED)
    required.update({
        f'{EVIDENCE}/catalog-vertical-slice/{width}/{page}.png': 'frontend/tests/catalog.spec.ts'
        for width in WIDTHS for page in CATALOG_PAGES
    })
    problems = [f'{consumer} -> missing {path}' for path, consumer in required.items() if path not in files]

    # The manifest was introduced after some refs this utility can audit.
    if BASELINES in files:
        for line in read(files[BASELINES][0]).decode('ascii').splitlines():
            digest, separator, path = line.partition('  ')
            if not separator or not re.fullmatch('[0-9a-f]{64}', digest):
                problems.append(f'{BASELINES}: invalid SHA-256 entry {line!r}')
            elif digests.get(path) != digest:
                problems.append(f'{BASELINES}: absent or changed PNG {path}')

    directories = {str(parent) for path in files for parent in PurePosixPath(path).parents}
    link_count = 0
    for source, (oid, _) in files.items():
        if not source.endswith(('.md', '.html')):
            continue
        content = read(oid).decode('utf-8', errors='replace')
        for line_number, target in evidence_links(source, content):
            link_count += 1
            if target not in files and target not in directories:
                problems.append(f'{source}:{line_number} -> missing {target}')
    print(f'Checked {link_count} local Markdown/HTML evidence links and {len(required)} known test inputs.')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='HEAD', help='commit, tag or tree to inspect (default: HEAD)')
    args = parser.parse_args()
    files = tree(args.ref)
    evidence = {path: item for path, item in files.items() if path.startswith(f'{EVIDENCE}/')}
    print(f'Repository: {len(files):,} files, {sum(size for _, size in files.values()):,} bytes')
    print(f'Evidence:   {len(evidence):,} files, {sum(size for _, size in evidence.values()):,} bytes')
    print('Largest tracked evidence files (manual review):')
    for path, (_, size) in sorted(evidence.items(), key=lambda item: -item[1][1])[:10]:
        print(f'  {size:>10,} bytes  {path}')

    digests = {}
    groups = defaultdict(list)
    with read_blobs() as read:
        for path, (oid, _) in evidence.items():
            digest = sha256(read(oid)).hexdigest()
            digests[path] = digest
            groups[digest].append(path)
        duplicates = [(digest, paths) for digest, paths in groups.items() if len(paths) > 1]
        extra_files = sum(len(paths) - 1 for _, paths in duplicates)
        extra_bytes = sum((len(paths) - 1) * evidence[paths[0]][1] for _, paths in duplicates)
        print(f'{len(duplicates):,} duplicate groups, {extra_files:,} additional paths, '
              f'{extra_bytes:,} repeated bytes in the tree (manual review):')
        for digest, paths in duplicates:
            print(f'  {digest} ({evidence[paths[0]][1]:,} bytes each)')
            for path in paths:
                print(f'    {path}')

        generated = [path for path in files if {'test-results', 'playwright-report'} & set(path.split('/')[:-1])]
        print(f'{len(generated):,} tracked test output paths (manual review):')
        for path in generated:
            print(f'  {path}')

        problems = check_references(files, digests, read)
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
