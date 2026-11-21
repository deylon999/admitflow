from pathlib import Path

from scripts.check_doc_links import check


def documents(root, paths):
    for name, body in paths.items():
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding='utf-8')
    return [Path(name) for name in paths]


def test_relative_paths_anchors_and_reference_definitions(tmp_path):
    paths = documents(tmp_path, {
        'README.md': '[A](docs/Guide.md#раздел)\n[B](docs/Guide.md#раздел-1)\n'
            '[Old][history]\n[history]: <docs/old (v1).md> "Read for context"\n'
            '<a href="docs/Guide.md#old-id">C</a>\n![](docs/picture.png)\n[folder](docs/)\n',
        'docs/Guide.md': '# Раздел\n\n## Раздел\n\n<a id="old-id"></a>\n[Self](#old-id)\n',
        'docs/old (v1).md': 'Dated notes\n',
        'docs/picture.png': 'fixture',
    })
    assert check(tmp_path, paths) == (3, 7, [])


def test_bad_destination_and_missing_markdown_heading_are_reported(tmp_path):
    paths = documents(tmp_path, {
        'README.md': '[one](docs/missing.md)\n[two](docs/Guide.md#missing)\n'
            '[external worktree](../sibling/file.md)\n'
            '[untracked](docs/local.md)\n',
        'docs/Guide.md': '# Existing\n',
    })
    (tmp_path/'docs/local.md').write_text('A local file', encoding='utf-8')
    _, _, issues = check(tmp_path, paths)
    assert issues == [
        'README.md:1: missing path: docs/missing.md',
        'README.md:2: missing heading or anchor: docs/Guide.md#missing',
        'README.md:3: outside repository: ../sibling/file.md',
        'README.md:4: missing path: docs/local.md',
    ]


def test_old_pinned_urls_and_code_examples_do_not_fail_link_check(tmp_path):
    paths = documents(tmp_path, {
        'docs/archive/old.md': '''# Archive

````md
```
[obsolete](../retired.md)
```
````

`[inline example](no.md)`

    [indented](another.md)

<!-- [commented](ignore.md) -->

[old commit](https://github.com/owner/repo/blob/abc/old.md)
''',
    })
    assert check(tmp_path, paths) == (1, 0, [])
