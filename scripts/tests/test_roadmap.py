"""Regression tests for selective documentation reading and generated handoff."""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import documentation_archive, roadmap


class DocumentationToolsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = roadmap.read_json('TASKS.json')
        cls.state = roadmap.read_json('STATE.json')

    def test_card_contains_acceptance_and_evidence(self):
        task = next(task for task in self.data['tasks'] if task['id'] == 'T017')
        output = roadmap.render_task(self.data, 'T017')
        for item in task['acceptance']:
            self.assertIn(item, output)
        for item in task['evidence']:
            self.assertIn(roadmap.evidence_location(item['path']), output)
        self.assertIn('T014 [done]', output)
        self.assertNotIn('T231 [', output)

    def test_dependencies_are_direct_without_recursive_history(self):
        data = copy.deepcopy(self.data)
        data['tasks'] = data['tasks'][:3]
        for index, task in enumerate(data['tasks']):
            task['dependsOn'] = [data['tasks'][index - 1]['id']] if index else []
        output = roadmap.render_task(data, 'T003')
        self.assertIn('T002 [', output)
        self.assertNotIn('T001 [', output)

    def test_unknown_task_is_an_error(self):
        with self.assertRaisesRegex(ValueError, 'Unknown task'):
            roadmap.render_task(self.data, 'T999')

    def test_archived_evidence_has_an_immutable_location(self):
        archived_path = 'docs/archive/api-before-foundation.md'
        self.assertEqual(
            roadmap.evidence_location(archived_path),
            f'{roadmap.ARCHIVE_URL}/{archived_path}',
        )
        self.assertEqual(roadmap.evidence_location('docs/not-a-real-document.md'), 'docs/not-a-real-document.md')
        data = copy.deepcopy(self.data)
        task = next(task for task in data['tasks'] if task['id'] == 'T017')
        task['evidence'] = [{'path': archived_path, 'note': 'Historical contract'}]
        self.assertFalse(roadmap.validate(data, self.state))
        task['evidence'][0]['path'] = 'docs/not-a-real-document.md'
        self.assertIn('T017: missing evidence file or note', roadmap.validate(data, self.state))

    def test_archived_inventory_uses_original_bytes_and_allows_local_override(self):
        archived_path = 'docs/sources/national-inventory.json'
        ref = f'{documentation_archive.ARCHIVE_REF}:{archived_path}'
        original = documentation_archive.archive_git('show', ref)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            default_path = root / archived_path
            with patch.object(documentation_archive, 'ROOT', root), \
                    patch.object(documentation_archive, 'archive_git', return_value=original) as archive:
                self.assertEqual(documentation_archive.read_input(default_path, archived_path), original)
                archive.assert_called_once_with('show', ref)
                default_path.parent.mkdir(parents=True)
                default_path.write_bytes(b'{"local": true}')
                self.assertEqual(documentation_archive.read_input(default_path, archived_path), b'{"local": true}')
                archive.assert_called_once()

    def test_readers_do_not_mutate_registry_or_state(self):
        before = copy.deepcopy((self.data, self.state))
        roadmap.render_task(self.data, 'T017')
        self.assertEqual(before, (self.data, self.state))

    def test_log_handles_headed_and_unheaded_sessions(self):
        text = '# Log\n\n## S001 — old\nT017 checked.\n\nS002: new\nT018 checked.\n'
        self.assertEqual(roadmap.select_log(text, count=1), 'S002: new\nT018 checked.\n')
        self.assertIn('T017 checked.', roadmap.select_log(text, 'S001'))
        self.assertNotIn('T018', roadmap.select_log(text, 'S001'))

    def test_log_uses_exact_task_identifier(self):
        text = '## S001\nT017 result\n## S002\nT0170 different\n'
        self.assertNotIn('S002', roadmap.select_log(text, 'T017'))
        with self.assertRaisesRegex(ValueError, 'No log entries'):
            roadmap.select_log(text, 'T999')

    def test_context_prefers_current_then_next_and_explicit_task(self):
        for current, explicit, expected in [(None, None, 'T057'),
                                             ('T017', None, 'T017'),
                                             ('T017', 'T018', 'T018')]:
            state = dict(self.state, currentTask=current, nextTask='T057')
            argv = ['roadmap.py', '--context'] + (['--task', explicit] if explicit else [])
            with patch.object(sys, 'argv', argv), patch.object(roadmap, 'validate', return_value=[]), \
                    patch.object(roadmap, 'read_json', side_effect=[self.data, state]), \
                    patch.object(roadmap, 'render_task', return_value='card') as render, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(roadmap.main(), 0)
                render.assert_called_once_with(self.data, expected)

    def test_cli_rejects_invalid_log_count(self):
        with patch.object(sys, 'argv', ['roadmap.py', '--log', '--entries', '0']), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            roadmap.main()
        self.assertEqual(error.exception.code, 2)

    def test_render_and_check_detect_stale_checklist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / 'docs'
            docs.mkdir()
            (docs / 'TASKS.json').write_text(json.dumps(self.data), encoding='utf-8')
            (docs / 'STATE.json').write_text(json.dumps(self.state), encoding='utf-8')
            with patch.object(roadmap, 'ROOT', root), patch.object(roadmap, 'DOCS', docs), \
                    patch.object(roadmap, 'validate', return_value=[]), \
                    patch.object(roadmap, 'check_links', return_value=[]), \
                    patch.object(roadmap, 'read_log', return_value=self.state['lastSession']), \
                    contextlib.redirect_stdout(io.StringIO()):
                with patch.object(sys, 'argv', ['roadmap.py', '--render', '--check']):
                    self.assertEqual(roadmap.main(), 0)
                (root / 'CHECKLIST.md').write_text('stale', encoding='utf-8')
                with patch.object(sys, 'argv', ['roadmap.py', '--check']):
                    self.assertEqual(roadmap.main(), 1)


if __name__ == '__main__':
    unittest.main()
