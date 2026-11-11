"""Weekly report: facts only, Done only after merge, no invented deadlines, PDF not kept in the project."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from scripts import weekly_report


def commit(sha, subject, merged, author='zarbondo'):
    return dict(sha=sha * 40, author=author, day='2026-11-11', subject=subject, keys=weekly_report.KAN.findall(subject), merged=merged)


ROWS = [commit('a', 'feat: coverage (KAN-221)', False), commit('b', 'fix: coverage layout (KAN-221)', False),
        commit('c', 'docs: concept (KAN-18)', True, 'Teammate'), commit('d', 'chore: tidy', True)]
TASKS = [dict(id='T046', title='HTTPS staging', status='blocked', blockedReason='нет сервера', evidence=[]),
         dict(id='T300', title='KAN-219: требования ЕГЭ', status='todo', evidence=[dict(path='docs/x.md')]),
         dict(id='T001', title='old', status='done', evidence=[])]


def report(**kwargs):
    return weekly_report.collect('2026-W46', commit_rows=kwargs.pop('rows', ROWS), task_list=kwargs.pop('tasks', TASKS), **kwargs)


class WeeklyReportTest(unittest.TestCase):
    def test_week_range_is_iso_monday_to_monday(self):
        start, end = weekly_report.week_range('2026-W46')
        self.assertEqual((start.isoformat(), end.isoformat()), ('2026-11-09', '2026-11-16'))
        with self.assertRaises(ValueError):
            weekly_report.week_range('2026-46')

    def test_sections_split_by_merge_state_and_roadmap_status(self):
        sections = report()['sections']
        self.assertEqual([r['task'] for r in sections['done']], ['KAN-18', '—'])
        self.assertEqual(sections['done'][0]['owner'], 'Teammate')
        self.assertEqual(len(sections['review']), 1)  # one row per card, both commits as evidence
        self.assertIn('aaaaaaa', sections['review'][0]['evidence'])
        self.assertIn('bbbbbbb', sections['review'][0]['evidence'])
        self.assertEqual(sections['review'][0]['what'], 'feat: coverage (KAN-221)')
        self.assertEqual([(r['task'], r['evidence']) for r in sections['progress']], [('KAN-219', 'docs/x.md')])
        self.assertIn('нет сервера', sections['blocked'][0]['what'])
        self.assertNotIn('T001', json.dumps(sections, ensure_ascii=False))

    def test_deadline_is_never_filled_by_the_script(self):
        sections = report()['sections']
        self.assertTrue(all(row['deadline'] == '' for rows in sections.values() for row in rows))

    def test_extra_rows_and_risks_are_validated(self):
        with tempfile.TemporaryDirectory() as folder:
            good = Path(folder)/'good.json'
            good.write_text(json.dumps({'rows': [{'section': 'progress', 'task': 'KAN-218', 'what': 'x', 'status': 'В работе', 'owner': 'zarbondo'}],
                                        'risks': ['нет сервера']}), encoding='utf-8')
            rows, risks = weekly_report.read_extra(good)
            merged = report(extra_rows=rows, risks=risks)
            self.assertEqual(merged['sections']['progress'][-1]['task'], 'KAN-218')
            self.assertEqual(merged['risks'], ['нет сервера'])
            for bad in ({'rows': [{'section': 'later', 'task': 'x'}]}, {'rows': [{'section': 'done', 'task': 1}]}, {'risks': ['']}, {'notes': []}):
                path = Path(folder)/'bad.json'
                path.write_text(json.dumps(bad), encoding='utf-8')
                with self.assertRaises(ValueError):
                    weekly_report.read_extra(path)

    def test_markdown_escapes_pipes(self):
        body = weekly_report.to_markdown(report(rows=[commit('f', 'fix: a | b (KAN-2)', True)], tasks=[]))
        row = next(line for line in body.splitlines() if line.startswith('| KAN-2 |'))
        self.assertIn('a \\| b', row)
        self.assertEqual(len(row.replace('\\|', '').split('|')), len(weekly_report.COLUMNS) + 2)

    def test_pdf_has_every_section_and_clickable_commits(self):
        try:
            from pypdf import PdfReader
            weekly_report.find_font()
        except (ImportError, FileNotFoundError) as error:
            self.skipTest(str(error))
        if importlib.util.find_spec('reportlab') is None:
            self.skipTest('reportlab is not installed')
        with tempfile.TemporaryDirectory() as folder:
            path = weekly_report.to_pdf(report(risks=['нужен сервер']), Path(folder)/'r.pdf')
            reader = PdfReader(path)
            text = ' '.join(page.extract_text() for page in reader.pages)
            for expected in ('Еженедельный отчёт AdmitFlow, 2026-W46', 'Сделано', 'На проверке', 'В работе', 'Заблокировано', 'KAN-221', 'нужен сервер'):
                self.assertIn(expected, text)
            links = [a.get_object()['/A']['/URI'] for page in reader.pages for a in page.get('/Annots', [])]
            self.assertIn(weekly_report.REPO_URL + '/commit/' + 'a' * 40, links)

    def test_default_output_is_outside_the_project(self):
        self.assertFalse(weekly_report.ROOT in Path(tempfile.gettempdir()).resolve().parents)


if __name__ == '__main__':
    unittest.main()
