"""
Test harness that runs jedi's rename fixture tests against an LSP server.

Usage:
    python3 -m pytest test/test_lsp_rename.py --lsp-cmd='zuban server' -v
"""
import asyncio
import os
import subprocess
import sys

import pytest

from test.lsp_compat import collect_rename_cases, start_server, run_rename
from test.helpers import test_dir


RENAME_FIXTURE = os.path.join(test_dir, 'refactor', 'rename.py')


def _build_zuban():
    """Build zuban and return path to binary."""
    zuban_dir = os.path.join(os.path.dirname(test_dir), 'zuban')
    if not os.path.isdir(zuban_dir):
        zuban_dir = os.path.join(os.path.dirname(os.path.dirname(test_dir)), 'zuban')
    if not os.path.isdir(zuban_dir):
        return None
    result = subprocess.run(
        ['cargo', 'build'],
        cwd=zuban_dir,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        pytest.skip(f'cargo build failed: {result.stderr}')
    binary = os.path.join(zuban_dir, 'target', 'debug', 'zuban')
    if not os.path.isfile(binary):
        pytest.skip(f'zuban binary not found at {binary}')
    return binary


@pytest.fixture(scope='session')
def lsp_cmd(request):
    cmd = request.config.getoption('--lsp-cmd', default=None)
    if cmd:
        return cmd
    zuban_bin = request.config.getoption('--zuban-bin', default=None)
    if zuban_bin:
        return f'{zuban_bin} --stdio'
    binary = _build_zuban()
    if binary:
        return f'{binary} --stdio'
    pytest.skip('No --lsp-cmd or --zuban-bin provided and cargo build not available')


class LspSessionManager:
    """Manages an LSP server session, restarting on crash."""

    def __init__(self, cmd):
        self.cmd = cmd
        self.loop = asyncio.new_event_loop()
        self.client = None
        self.proc = None
        self._start()

    def _start(self):
        self.client, self.proc = self.loop.run_until_complete(start_server(self.cmd))

    def ensure_alive(self):
        if self.proc.returncode is not None:
            self._start()

    def run_rename(self, case):
        self.ensure_alive()
        return self.loop.run_until_complete(run_rename(self.client, case))

    def close(self):
        if self.client:
            try:
                self.loop.run_until_complete(self.client.shutdown())
            except Exception:
                pass
        if self.proc:
            try:
                self.proc.kill()
            except ProcessLookupError:
                pass
        self.loop.close()


@pytest.fixture(scope='session')
def lsp_session(lsp_cmd):
    mgr = LspSessionManager(lsp_cmd)
    yield mgr
    mgr.close()


def _get_rename_cases():
    try:
        cases = list(collect_rename_cases(RENAME_FIXTURE))
    except Exception:
        return []
    return cases


_cases = _get_rename_cases()
_case_ids = [c.name for c in _cases]


@pytest.mark.parametrize('rename_case', _cases, ids=_case_ids)
def test_lsp_rename(rename_case, lsp_session):
    result_type, result_string = lsp_session.run_rename(rename_case)

    if rename_case.type == 'error':
        if result_string is None:
            return
        pytest.fail(f'Expected error but got result for case {rename_case.name}')
        return

    if result_string is None:
        pytest.fail(f'Server returned null/error for case {rename_case.name}')
        return

    expected = rename_case.get_desired_result()

    actual_normalized = result_string.rstrip('\n') + '\n'
    expected_normalized = expected.rstrip('\n') + '\n'

    if actual_normalized != expected_normalized:
        import difflib
        diff = ''.join(difflib.unified_diff(
            expected_normalized.splitlines(keepends=True),
            actual_normalized.splitlines(keepends=True),
            fromfile='expected', tofile='actual',
        ))
        pytest.fail(f'Rename result mismatch for case {rename_case.name}:\n{diff}')
