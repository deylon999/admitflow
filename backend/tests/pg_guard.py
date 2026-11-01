"""Explicit CI mode must execute every selected native PostgreSQL test."""
import os
import pytest
from pg_support import disposable_postgres_url

STATE = pytest.StashKey[dict]()


def pytest_addoption(parser):
    parser.addoption('--require-postgres', action='store_true', help='Fail if native PostgreSQL checks are absent, skipped or unsuccessful')


def pytest_configure(config):
    config.addinivalue_line('markers', 'postgres: requires actual disposable PostgreSQL execution')
    config.stash[STATE] = {'selected': set(), 'passed': set(), 'incomplete': set()}


def pytest_sessionstart(session):
    if session.config.getoption('--require-postgres'):
        try:
            disposable_postgres_url(os.getenv('TEST_DATABASE_URL', ''))
        except ValueError:
            raise pytest.UsageError('--require-postgres needs a disposable PostgreSQL TEST_DATABASE_URL (admitflow_test*)') from None


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    # Remember the native cases before -k/-m deselection can hide one of them.
    config.stash[STATE]['selected'] = {item.nodeid for item in items if item.get_closest_marker('postgres')}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()
    if report.when == 'call' and report.passed and item.get_closest_marker('postgres'):
        item.config.stash[STATE]['passed'].add(item.nodeid)
    if (report.failed or report.skipped) and item.get_closest_marker('postgres'):
        item.config.stash[STATE]['incomplete'].add(item.nodeid)


def pytest_sessionfinish(session, exitstatus):
    if not session.config.getoption('--require-postgres') or exitstatus != 0:
        return
    state = session.config.stash[STATE]
    if not state['selected'] or state['passed'] != state['selected'] or state['incomplete']:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        reporter = session.config.pluginmanager.get_plugin('terminalreporter')
        if reporter:
            reporter.write_line('Required PostgreSQL checks were absent, skipped or incomplete.', red=True)
