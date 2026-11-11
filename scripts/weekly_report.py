"""Draft of the weekly team report (KAN-24).

Collects facts for one ISO week from git and docs/TASKS.json:
- done: commits that reached the main branch during the week;
- on review: commits of the week that are not in main yet (open PR);
- blocked: roadmap tasks with status "blocked" and their reason;
- in progress: roadmap tasks with status "todo" or "review".

Every row carries evidence (commit or evidence file) and an owner (commit
author). Deadlines are not stored anywhere in the repository, so the column is
left empty for the team to fill in; the script never invents a date.

Usage:
    python scripts/weekly_report.py --week 2026-W46 [--main origin/main] [--output docs/reports/2026-W46.md]
"""
import argparse
from collections import OrderedDict
from datetime import date, timedelta
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = 'https://github.com/deylon999/admitflow'
KAN = re.compile(r'\bKAN-\d+\b')
COLUMNS = ('Задача', 'Что', 'Статус', 'Срок', 'Доказательства', 'Ответственный')


def week_range(value):
    match = re.fullmatch(r'(\d{4})-W(\d{2})', value)
    if not match:
        raise ValueError('week must look like 2026-W46')
    start = date.fromisocalendar(int(match[1]), int(match[2]), 1)
    return start, start + timedelta(days=7)


def git(*args):
    return subprocess.run(('git', *args), cwd=ROOT, check=True, capture_output=True, text=True).stdout


def commits(start, end, main):
    """Non-merge commits authored in [start, end) on any local or remote branch."""
    out = git('log', '--all', '--no-merges', f'--since={start.isoformat()}T00:00:00', f'--until={end.isoformat()}T00:00:00',
              '--format=%H%x1f%an%x1f%ad%x1f%s', '--date=short')
    merged = set(git('rev-list', main).split()) if main else set()
    rows = []
    for line in out.splitlines():
        sha, author, day, subject = line.split('\x1f')
        rows.append(dict(sha=sha, author=author, day=day, subject=subject, keys=KAN.findall(subject), merged=sha in merged))
    return rows


def cell(value):
    return (value or '').replace('|', '\\|').replace('\n', ' ').strip()


def table(rows):
    lines = ['| ' + ' | '.join(COLUMNS) + ' |', '|' + '---|' * len(COLUMNS)]
    lines += ['| ' + ' | '.join(cell(row.get(c)) for c in COLUMNS) + ' |' for row in rows]
    return '\n'.join(lines) if rows else '_Нет записей._'


def grouped(items):
    """One row per Jira key (or per commit without a key), newest commit first."""
    groups = OrderedDict()
    for item in items:
        key = ', '.join(item['keys']) or item['sha'][:7]
        groups.setdefault(key, []).append(item)
    rows = []
    for key, group in groups.items():
        evidence = ', '.join(f"[{c['sha'][:7]}]({REPO_URL}/commit/{c['sha']})" for c in group)
        owners = ', '.join(sorted({c['author'] for c in group}))
        rows.append({'Задача': key if key.startswith('KAN-') else '—', 'Что': group[0]['subject'], 'Доказательства': evidence,
                     'Ответственный': owners})
    return rows


def tasks(path=ROOT/'docs'/'TASKS.json'):
    return json.loads(path.read_text(encoding='utf-8'))['tasks']


def roadmap_rows(task_list, statuses, status_name):
    rows = []
    for task in task_list:
        if task['status'] not in statuses:
            continue
        keys = KAN.findall(task['title'])
        evidence = ', '.join(e['path'] for e in task.get('evidence', [])) or '—'
        what = task['title'] if not task.get('blockedReason') else f"{task['title']}. Причина: {task['blockedReason']}"
        rows.append({'Задача': ', '.join(keys) or task['id'], 'Что': what, 'Статус': status_name,
                     'Доказательства': evidence, 'Ответственный': task.get('owner') or ''})
    return rows


def build(week, *, main='origin/main', commit_rows=None, task_list=None):
    start, end = week_range(week)
    commit_rows = commits(start, end, main) if commit_rows is None else commit_rows
    task_list = tasks() if task_list is None else task_list
    done = [dict(r, **{'Статус': 'Done, в main'}) for r in grouped([c for c in commit_rows if c['merged']])]
    review = [dict(r, **{'Статус': 'In Review, PR открыт'}) for r in grouped([c for c in commit_rows if not c['merged']])]
    blocked = roadmap_rows(task_list, {'blocked'}, 'Blocked')
    progress = roadmap_rows(task_list, {'todo', 'review'}, 'В работе')
    last = end - timedelta(days=1)
    return '\n'.join([
        f'# Еженедельный отчёт AdmitFlow, {week} ({start:%d.%m}–{last:%d.%m.%Y})', '',
        'Черновик собран `scripts/weekly_report.py` из git и docs/TASKS.json. Срок заполняет ответственный; '
        'Done ставится только после review и слияния в main.', '',
        '## Сделано', '', table(done), '',
        '## На проверке', '', table(review), '',
        '## В работе', '', table(progress), '',
        '## Заблокировано', '', table(blocked), '',
        '## Риски и решения, которые нужны от команды', '', '- ', '',
    ])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--week', required=True, help='ISO week, e.g. 2026-W46')
    parser.add_argument('--main', default='origin/main', help='Branch that counts as done')
    parser.add_argument('--output', help='Write Markdown here instead of stdout')
    args = parser.parse_args(argv)
    body = build(args.week, main=args.main)
    if args.output:
        Path(args.output).write_text(body, encoding='utf-8')
    else:
        print(body, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
