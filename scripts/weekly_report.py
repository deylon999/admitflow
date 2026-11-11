"""Weekly team report as a PDF (KAN-24).

Collects facts for one ISO week from git and docs/TASKS.json:
- done: commits that reached the main branch during the week;
- on review: commits of the week that are not in main yet (open PR);
- in progress and blocked: roadmap tasks with these statuses.

Every row carries evidence (commit or evidence file) and an owner (commit
author). Deadlines are not stored in the repository, so the script never fills
them; rows and risks the repository does not know about come from --extra.

The report is not kept in the project: by default the PDF is written to the
system temp folder and its path is printed, ready to be sent to the team chat.

Usage:
    python scripts/weekly_report.py --week 2026-W46 [--extra notes.json] [--output report.pdf] [--format md]

notes.json:
    {"rows": [{"section": "progress", "task": "KAN-218", "what": "...", "status": "В работе",
               "deadline": "", "evidence": "...", "owner": "..."}],
     "risks": ["..."]}
Sections: done, review, progress, blocked.

Needs reportlab (pip install -r scripts/requirements-report.txt) and a TTF font
with Cyrillic: DejaVu Sans, Arial or Liberation Sans are found automatically,
another one can be given with --font.
"""
import argparse
from collections import OrderedDict
from datetime import date, timedelta
from html import escape
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = 'https://github.com/deylon999/admitflow'
KAN = re.compile(r'\bKAN-\d+\b')
COLUMNS = ('Задача', 'Что', 'Статус', 'Срок', 'Доказательства', 'Ответственный')
FIELDS = ('task', 'what', 'status', 'deadline', 'evidence', 'owner')
SECTIONS = (('done', 'Сделано'), ('review', 'На проверке'), ('progress', 'В работе'), ('blocked', 'Заблокировано'))
FONTS = (
    ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf'),
    ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'),
    ('/Library/Fonts/Arial.ttf', '/Library/Fonts/Arial Bold.ttf'),
    ('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'),
)
LINK = re.compile(r'\[([^\]]+)\]\((https://[^)\s]+)\)')


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


def grouped(items, status):
    """One row per Jira key (or per commit without a key), newest commit first."""
    groups = OrderedDict()
    for item in items:
        key = ', '.join(item['keys']) or item['sha'][:7]
        groups.setdefault(key, []).append(item)
    return [dict(task=key if key.startswith('KAN-') else '—', what=group[0]['subject'], status=status, deadline='',
                 evidence=', '.join(f"[{c['sha'][:7]}]({REPO_URL}/commit/{c['sha']})" for c in group),
                 owner=', '.join(sorted({c['author'] for c in group})))
            for key, group in groups.items()]


def tasks(path=ROOT/'docs'/'TASKS.json'):
    return json.loads(path.read_text(encoding='utf-8'))['tasks']


def roadmap_rows(task_list, statuses, status_name):
    rows = []
    for task in task_list:
        if task['status'] not in statuses:
            continue
        what = task['title'] if not task.get('blockedReason') else f"{task['title']}. Причина: {task['blockedReason']}"
        rows.append(dict(task=', '.join(KAN.findall(task['title'])) or task['id'], what=what, status=status_name, deadline='',
                         evidence=', '.join(e['path'] for e in task.get('evidence', [])) or '—', owner=task.get('owner') or ''))
    return rows


def read_extra(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or set(data) - {'rows', 'risks'}:
        raise ValueError('extra must have only "rows" and "risks"')
    rows = data.get('rows', [])
    for row in rows:
        if row.get('section') not in dict(SECTIONS) or set(row) - {'section', *FIELDS} or not all(isinstance(row.get(f, ''), str) for f in FIELDS):
            raise ValueError('every extra row needs a known section and text fields')
    risks = data.get('risks', [])
    if not all(isinstance(r, str) and r.strip() for r in risks):
        raise ValueError('risks must be non-empty strings')
    return rows, risks


def collect(week, *, main='origin/main', commit_rows=None, task_list=None, extra_rows=(), risks=()):
    start, end = week_range(week)
    commit_rows = commits(start, end, main) if commit_rows is None else commit_rows
    task_list = tasks() if task_list is None else task_list
    sections = {
        'done': grouped([c for c in commit_rows if c['merged']], 'Done, в main'),
        'review': grouped([c for c in commit_rows if not c['merged']], 'In Review, PR открыт'),
        'progress': roadmap_rows(task_list, {'todo', 'review'}, 'В работе'),
        'blocked': roadmap_rows(task_list, {'blocked'}, 'Blocked'),
    }
    for row in extra_rows:
        sections[row['section']].append({f: row.get(f, '') for f in FIELDS})
    return dict(week=week, start=start, last=end - timedelta(days=1), sections=sections, risks=list(risks))


def title(report):
    return f"Еженедельный отчёт AdmitFlow, {report['week']} ({report['start']:%d.%m}–{report['last']:%d.%m.%Y})"


NOTE = 'Собрано scripts/weekly_report.py из git и docs/TASKS.json. Срок заполняет ответственный; Done ставится только после review и слияния в main.'


def to_markdown(report):
    def cell(value):
        return (value or '').replace('|', '\\|').replace('\n', ' ').strip()
    lines = [f'# {title(report)}', '', NOTE, '']
    for key, name in SECTIONS:
        rows = report['sections'][key]
        lines += [f'## {name}', '']
        if rows:
            lines += ['| ' + ' | '.join(COLUMNS) + ' |', '|' + '---|' * len(COLUMNS)]
            lines += ['| ' + ' | '.join(cell(r[f]) for f in FIELDS) + ' |' for r in rows]
        else:
            lines.append('_Нет записей._')
        lines.append('')
    lines += ['## Риски и решения, которые нужны от команды', '']
    lines += [f'- {r}' for r in report['risks']] or ['_Нет записей._']
    return '\n'.join(lines) + '\n'


def find_font(path=None):
    if path:
        return Path(path), Path(path)
    for regular, bold in FONTS:
        if Path(regular).exists():
            return Path(regular), Path(bold) if Path(bold).exists() else Path(regular)
    raise FileNotFoundError('no TTF font with Cyrillic found; pass --font path/to/font.ttf')


def rich(value):
    """Escape text for a reportlab Paragraph and keep markdown links clickable."""
    out, last = [], 0
    for match in LINK.finditer(value or ''):
        out.append(escape(value[last:match.start()]))
        out.append(f'<link href="{escape(match[2])}" color="#1f4fd8">{escape(match[1])}</link>')
        last = match.end()
    out.append(escape((value or '')[last:]))
    return ''.join(out)


def to_pdf(report, output, *, font=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    regular, bold = find_font(font)
    pdfmetrics.registerFont(TTFont('ReportSans', str(regular)))
    pdfmetrics.registerFont(TTFont('ReportSans-Bold', str(bold)))
    pdfmetrics.registerFontFamily('ReportSans', normal='ReportSans', bold='ReportSans-Bold')
    ink, muted, line, head = colors.HexColor('#16181d'), colors.HexColor('#5b6170'), colors.HexColor('#d9dde6'), colors.HexColor('#eef1f6')
    h1 = ParagraphStyle('h1', fontName='ReportSans-Bold', fontSize=16, leading=20, textColor=ink, spaceAfter=4)
    h2 = ParagraphStyle('h2', fontName='ReportSans-Bold', fontSize=11.5, leading=15, textColor=ink, spaceBefore=10, spaceAfter=5, keepWithNext=1)
    body = ParagraphStyle('body', fontName='ReportSans', fontSize=8.5, leading=11, textColor=ink)
    small = ParagraphStyle('small', parent=body, fontSize=8, textColor=muted)
    risk = ParagraphStyle('risk', parent=body, fontSize=9, leading=12, spaceAfter=4, leftIndent=9, bulletIndent=0)
    cellhead = ParagraphStyle('cellhead', parent=body, fontName='ReportSans-Bold')

    page = landscape(A4)
    margin = 14*mm
    widths = [x*mm for x in (24, 112, 28, 18, 52, 35)]
    doc = SimpleDocTemplate(str(output), pagesize=page, leftMargin=margin, rightMargin=margin, topMargin=12*mm, bottomMargin=12*mm,
                            title=title(report), author='AdmitFlow')

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont('ReportSans', 7.5)
        canvas.setFillColor(muted)
        canvas.drawString(margin, 7*mm, title(report))
        canvas.drawRightString(page[0] - margin, 7*mm, f'стр. {document.page}')
        canvas.restoreState()

    counts = ' · '.join(f"{name} {len(report['sections'][key])}" for key, name in SECTIONS)
    story = [Paragraph(escape(title(report)), h1), Paragraph(escape(counts), body), Paragraph(escape(NOTE), small), Spacer(1, 4)]
    for key, name in SECTIONS:
        rows = report['sections'][key]
        heading = Paragraph(f'{escape(name)} · {len(rows)}', h2)
        if not rows:
            story += [heading, Paragraph('Нет записей.', small)]
            continue
        data = [[Paragraph(c, cellhead) for c in COLUMNS]] + [[Paragraph(rich(r[f]), body) for f in FIELDS] for r in rows]
        table = Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), head), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, -1), 0.4, line), ('BOX', (0, 0), (-1, -1), 0.4, line),
            ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        # The heading stays with the table; a long table breaks across pages and repeats its header row.
        story += [heading, table]
    risks = [Paragraph(escape(r), risk, bulletText='•') for r in report['risks']] or [Paragraph('Нет записей.', small)]
    story.append(KeepTogether([Paragraph('Риски и решения, которые нужны от команды', h2), *risks]))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return Path(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--week', required=True, help='ISO week, e.g. 2026-W46')
    parser.add_argument('--main', default='origin/main', help='Branch that counts as done')
    parser.add_argument('--extra', help='JSON with extra rows and risks the repository does not know')
    parser.add_argument('--format', choices=('pdf', 'md'), default='pdf', help='pdf (default) or Markdown to stdout')
    parser.add_argument('--output', help='PDF path; default: system temp folder')
    parser.add_argument('--font', help='TTF font with Cyrillic, if none is found automatically')
    args = parser.parse_args(argv)
    extra_rows, risks = read_extra(args.extra) if args.extra else ((), ())
    report = collect(args.week, main=args.main, extra_rows=extra_rows, risks=risks)
    if args.format == 'md':
        print(to_markdown(report), end='')
        return 0
    output = Path(args.output) if args.output else Path(tempfile.gettempdir())/f'admitflow-weekly-{args.week}.pdf'
    print(to_pdf(report, output, font=args.font))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
