"""Check local Markdown links and headings against versioned repository files."""
import argparse
from collections import Counter
from html import unescape
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]
FENCE = re.compile(r'^\s*(?:(?:>\s*)+)?(`{3,}|~{3,})(.*)$')
INLINE_CODE = re.compile(r'(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)')
INLINE_LINK = re.compile(r'(?<!\\)\]\(\s*')
REFERENCE = re.compile(r'^\s{0,3}\[[^\]]+\]:\s*')
HTML_LINK = re.compile(r'<(?:a|img)\b[^>]*?\b(?:href|src)\s*=\s*(["\'])(.*?)\1', re.I)
EXPLICIT_ANCHOR = re.compile(r'<(?:a|h[1-6])\b[^>]*?\b(?:id|name)\s*=\s*(["\'])(.*?)\1', re.I)
ATX_HEADING = re.compile(r'^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$')
SETEXT = re.compile(r'^\s{0,3}(?:=+|-+)\s*$')


def visible_lines(text):
    """Remove fenced examples and HTML comments while preserving line numbers."""
    text = re.sub(r'<!--.*?-->', lambda match: '\n' * match[0].count('\n'), text, flags=re.S)
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = FENCE.match(line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        yield number, line


def read_destination(text):
    """Extract one destination, allowing angle paths and balanced parentheses."""
    if text.startswith('<'):
        end = text.find('>')
        return text[1:end] if end >= 0 else ''
    depth, index = 0, 0
    while index < len(text):
        char = text[index]
        if char == '\\' and index+1 < len(text) and text[index+1] in '()':
            index += 2
            continue
        if char.isspace() or (char == ')' and depth == 0):
            break
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        index += 1
    return text[:index].replace(r'\(', '(').replace(r'\)', ')')


def destinations(text):
    for number, line in visible_lines(text):
        if line.startswith(('    ', '\t')):
            continue  # indented code example
        line = INLINE_CODE.sub('', line)
        reference = REFERENCE.match(line)
        if reference:
            yield number, read_destination(line[reference.end():])
        for match in INLINE_LINK.finditer(line):
            if '[' in line[:match.start()]:
                yield number, read_destination(line[match.end():])
        for match in HTML_LINK.finditer(line):
            yield number, match[2]


def anchors(text):
    result, counts = set(), Counter()
    previous = ''
    previous_line = 0
    for number, line in visible_lines(text):
        result.update(match[2] for match in EXPLICIT_ANCHOR.finditer(line))
        heading = ATX_HEADING.match(line)
        if heading:
            title = heading[1]
        elif previous.strip() and previous_line == number-1 and SETEXT.fullmatch(line):
            title = previous.strip()
        else:
            title = None
        if title:
            title = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', title)
            title = unescape(re.sub(r'<[^>]+>', '', title)).lower()
            slug = re.sub(r'[^\w\- ]', '', title).replace(' ', '-')
            suffix = counts[slug]
            while (candidate := slug if suffix == 0 else f'{slug}-{suffix}') in result:
                suffix += 1
            result.add(candidate)
            counts[slug] = suffix+1
        previous, previous_line = line, number
    return result


def check(root, paths):
    files = set(paths)
    directories = {parent for file in files for parent in file.parents}
    documents = sorted(p for p in files if p.suffix.lower() == '.md' and (root/p).is_file())
    contents = {path: (root/path).read_text(encoding='utf-8-sig') for path in documents}
    anchor_cache = {}
    issues, checked = [], 0
    for source, body in contents.items():
        for number, raw in destinations(body):
            target = unescape(raw)
            if not target or target.startswith('//') or re.match(r'^[a-z][a-z0-9+.-]*:', target, re.I):
                continue
            checked += 1
            name, _, fragment = target.partition('#')
            name = unquote(name.split('?',1)[0])
            try:
                absolute = root/name.lstrip('/') if name.startswith('/') else root/source.parent/name if name else root/source
                path = absolute.resolve().relative_to(root.resolve())
            except (ValueError, OSError):
                issues.append(f'{source.as_posix()}:{number}: outside repository: {target}')
                continue
            where = f'{source.as_posix()}:{number}'
            if (path not in files and path not in directories) or not (root/path).exists():
                issues.append(f'{where}: missing path: {target}')
                continue
            if fragment and path in contents:
                if path not in anchor_cache:
                    anchor_cache[path] = anchors(contents[path])
                if unquote(fragment) not in anchor_cache[path]:
                    issues.append(f'{where}: missing heading or anchor: {target}')
    return len(documents), checked, issues


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    raw = subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'], cwd=ROOT)
    paths = [Path(name) for name in raw.decode('utf-8').split('\0') if name]
    count, links, issues = check(ROOT, paths)
    for issue in issues:
        print(issue)
    print(f'Checked {links} internal links in {count} Markdown files; {len(issues)} issues.')
    return int(bool(issues))


if __name__ == '__main__':
    raise SystemExit(main())
