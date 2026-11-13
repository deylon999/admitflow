import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_auth_acceptance import validate


class AuthAcceptanceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.junit = self.root/'backend.xml'
        self.junit.write_text('<testsuite><testcase classname="tests.test_control" name="test_security"/></testsuite>')
        self.matrix = {'minimumBackendTests': 1, 'minimumBrowserTests': 1,
                       'automated': [{'id': 'security', 'tests': ['backend/tests/test_control.py::test_security']}],
                       'externalGates': [{'id': 'delivery', 'status': 'not_verified'}]}
        for engine in ('chromium', 'firefox', 'webkit'):
            path = self.root/engine
            path.mkdir()
            (path/'results.json').write_text(json.dumps({'stats': {'expected': 1, 'unexpected': 0, 'flaky': 0, 'skipped': 0}, 'errors': []}))

    def test_successful_automated_evidence_cannot_accept_external_gates(self):
        result = validate(self.matrix, self.junit, self.root)
        self.assertFalse(result['productionReady'])
        self.assertEqual(result['externalGates'], [{'id': 'delivery', 'status': 'not_verified'}])
        self.assertEqual(set(result['browsers']), {'chromium', 'firefox', 'webkit'})

    def test_failed_skipped_missing_or_truncated_backend_is_rejected(self):
        for body in ['<testcase classname="tests.test_control" name="test_security"><failure/></testcase>',
                     '<testcase classname="tests.test_control" name="test_security"><skipped/></testcase>',
                     '<testcase classname="tests.test_control" name="unrelated"/>', '']:
            with self.subTest(body=body):
                self.junit.write_text('<testsuite>'+body+'</testsuite>')
                with self.assertRaises(ValueError): validate(self.matrix, self.junit, self.root)

    def test_missing_failed_or_skipped_browser_evidence_is_rejected(self):
        path = self.root/'webkit'/'results.json'
        for stats in [{'expected': 0}, {'expected': 1, 'unexpected': 1}, {'expected': 1, 'skipped': 1}, {'expected': 1, 'flaky': 1}]:
            with self.subTest(stats=stats):
                path.write_text(json.dumps({'stats': stats}))
                with self.assertRaises(ValueError): validate(self.matrix, self.junit, self.root)
        path.unlink()
        with self.assertRaises(FileNotFoundError): validate(self.matrix, self.junit, self.root)
