"""Weekly report draft: facts only, Done only after merge, no invented deadlines."""
import unittest

from scripts import weekly_report


def commit(sha, subject, merged, author='zarbondo'):
    return dict(sha=sha * 40, author=author, day='2026-11-11', subject=subject, keys=weekly_report.KAN.findall(subject), merged=merged)


class WeeklyReportTest(unittest.TestCase):
    def test_week_range_is_iso_monday_to_monday(self):
        start, end = weekly_report.week_range('2026-W46')
        self.assertEqual((start.isoformat(), end.isoformat()), ('2026-11-09', '2026-11-16'))
        with self.assertRaises(ValueError):
            weekly_report.week_range('2026-46')

    def test_sections_split_by_merge_state_and_roadmap_status(self):
        rows = [commit('a', 'feat: coverage (KAN-221)', False), commit('b', 'fix: coverage | layout (KAN-221)', False),
                commit('c', 'docs: concept (KAN-18)', True, 'Teammate'), commit('d', 'chore: tidy', True)]
        task_list = [dict(id='T046', title='HTTPS staging', status='blocked', blockedReason='нет сервера', evidence=[]),
                     dict(id='T300', title='KAN-219: требования ЕГЭ', status='todo', evidence=[dict(path='docs/x.md')]),
                     dict(id='T001', title='old', status='done', evidence=[])]
        body = weekly_report.build('2026-W46', commit_rows=rows, task_list=task_list)
        done, rest = body.split('## На проверке')
        review, rest = rest.split('## В работе')
        progress, blocked = rest.split('## Заблокировано')
        self.assertIn('KAN-18', done)
        self.assertIn('Done, в main', done)
        self.assertNotIn('KAN-221', done)
        self.assertEqual(review.count('| KAN-221 |'), 1)  # one row per card, both commits as evidence
        self.assertIn('aaaaaaa', review)
        self.assertIn('bbbbbbb', review)
        self.assertIn('| feat: coverage (KAN-221) |', review)  # newest commit names the row
        self.assertIn('KAN-219', progress)
        self.assertIn('docs/x.md', progress)
        self.assertIn('нет сервера', blocked)
        self.assertNotIn('T001', body)
        self.assertIn('Teammate', done)

    def test_pipes_in_subjects_do_not_break_the_table(self):
        body = weekly_report.build('2026-W46', commit_rows=[commit('f', 'fix: a | b (KAN-2)', True)], task_list=[])
        row = next(line for line in body.splitlines() if line.startswith('| KAN-2 |'))
        self.assertIn('a \\| b', row)
        self.assertEqual(len(row.replace('\\|', '').split('|')), len(weekly_report.COLUMNS) + 2)

    def test_deadline_column_is_never_filled_by_the_script(self):
        body = weekly_report.build('2026-W46', commit_rows=[commit('e', 'feat (KAN-1)', True)], task_list=[])
        row = next(line for line in body.splitlines() if line.startswith('| KAN-1 |'))
        self.assertEqual(row.split('|')[4].strip(), '')


if __name__ == '__main__':
    unittest.main()
