"""
Thin LSP adapter that drives rename operations against a stdio LSP server
using jedi's fixture format. Reuses _collect_file_tests from test/refactor.py.
"""
import asyncio
import difflib
import json
import os
import shlex
import shutil
import tempfile
from pathlib import Path

from test.refactor import _collect_file_tests, RefactoringCase


def collect_rename_cases(fixture_path):
    """Parse a jedi fixture file and yield RefactoringCase objects for rename tests."""
    fixture_dir = os.path.dirname(os.path.abspath(fixture_path))
    get_tmpdir(fixture_dir=fixture_dir)
    with open(fixture_path, newline='') as f:
        code = f.read()
    yield from _collect_file_tests(code, fixture_path, lines_to_execute=[])


class LspClient:
    """Minimal async stdio LSP client."""

    def __init__(self, proc):
        self._proc = proc
        self._req_id = 0
        self._pending = {}
        self._reader_task = None

    async def start(self):
        self._reader_task = asyncio.ensure_future(self._read_loop())

    async def _read_loop(self):
        try:
            while True:
                msg = await self._read_message()
                if msg is None:
                    break
                msg_id = msg.get('id')
                if msg_id is not None and msg_id in self._pending:
                    self._pending[msg_id].set_result(msg)
        except (asyncio.CancelledError, ConnectionError):
            pass

    async def _read_message(self):
        headers = {}
        while True:
            line = await self._proc.stdout.readline()
            if not line:
                return None
            line = line.decode('utf-8')
            if line == '\r\n' or line == '\n':
                break
            if ':' in line:
                key, val = line.split(':', 1)
                headers[key.strip().lower()] = val.strip()
        content_length = int(headers.get('content-length', 0))
        if content_length == 0:
            return None
        body = await self._proc.stdout.readexactly(content_length)
        return json.loads(body.decode('utf-8'))

    def _send(self, msg):
        body = json.dumps(msg).encode('utf-8')
        header = f'Content-Length: {len(body)}\r\n\r\n'.encode('utf-8')
        self._proc.stdin.write(header + body)

    async def request(self, method, params):
        self._req_id += 1
        rid = self._req_id
        msg = {'jsonrpc': '2.0', 'id': rid, 'method': method, 'params': params}
        fut = asyncio.get_event_loop().create_future()
        self._pending[rid] = fut
        self._send(msg)
        await self._proc.stdin.drain()
        return await asyncio.wait_for(fut, timeout=30)

    def notify(self, method, params):
        msg = {'jsonrpc': '2.0', 'method': method, 'params': params}
        self._send(msg)

    async def shutdown(self):
        try:
            await self.request('shutdown', None)
        except Exception:
            pass
        try:
            self.notify('exit', None)
        except Exception:
            pass
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass


# Shared temp directory for all cases in a session
_tmpdir = None
_fixture_dir = None


def get_tmpdir(fixture_dir=None):
    global _tmpdir, _fixture_dir
    if _tmpdir is None:
        _tmpdir = tempfile.mkdtemp(prefix='lsp_compat_')
        with open(os.path.join(_tmpdir, 'pyproject.toml'), 'w') as f:
            f.write('[tool.zuban]\n')
    if fixture_dir is not None and fixture_dir != _fixture_dir:
        _fixture_dir = fixture_dir
        _copy_fixture_aux_files(fixture_dir, _tmpdir)
    return _tmpdir


def _copy_fixture_aux_files(fixture_dir, tmpdir):
    """Copy auxiliary files from the fixture directory into the temp workspace.

    This makes cross-file rename cases work: e.g. cases that reference
    import_tree/ need those files present so the LSP server can resolve imports.
    rename.py is excluded because the adapter manages that file itself.
    """
    for entry in os.scandir(fixture_dir):
        if entry.name == 'rename.py':
            continue
        dst = os.path.join(tmpdir, entry.name)
        if entry.is_dir():
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(entry.path, dst)
        else:
            shutil.copy2(entry.path, dst)


async def start_server(cmd):
    """Launch an LSP server subprocess and complete the initialize handshake."""
    args = shlex.split(cmd)
    tmpdir = get_tmpdir()
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    client = LspClient(proc)
    await client.start()

    resp = await client.request('initialize', {
        'processId': os.getpid(),
        'capabilities': {},
        'rootUri': 'file://' + tmpdir,
        'workspaceFolders': [{'uri': 'file://' + tmpdir, 'name': 'test'}],
    })
    client.notify('initialized', {})
    # Give server time to initialize
    await asyncio.sleep(1)
    return client, proc


async def run_rename(client, case: RefactoringCase):
    """
    Send a rename request for a single case.
    Returns (result_type, result_string) or (result_type, None) for errors.
    """
    code = case._code
    new_name = case._kwargs.get('new_name', 'renamed')

    # Write code to a temp file so the server can find it
    tmpdir = get_tmpdir()
    tmpfile = os.path.join(tmpdir, 'rename.py')
    with open(tmpfile, 'w') as f:
        f.write(code)
    uri = 'file://' + tmpfile

    # Position: lsp_line = case._line_nr - 1, lsp_character = case._index
    lsp_line = case._line_nr - 1
    lsp_character = case._index

    # Open document
    client.notify('textDocument/didOpen', {
        'textDocument': {
            'uri': uri,
            'languageId': 'python',
            'version': 1,
            'text': code,
        }
    })

    # Give server time to process the document
    await asyncio.sleep(0.5)

    # Check if server is still alive
    if client._proc.returncode is not None:
        return case.type, None

    # Send rename
    try:
        response = await client.request('textDocument/rename', {
            'textDocument': {'uri': uri},
            'position': {'line': lsp_line, 'character': lsp_character},
            'newName': new_name,
        })
    except (asyncio.TimeoutError, ConnectionError):
        return case.type, None

    # Close document
    try:
        client.notify('textDocument/didClose', {
            'textDocument': {'uri': uri}
        })
    except Exception:
        pass

    # Handle error response
    if 'error' in response:
        return case.type, None

    result = response.get('result')
    if result is None:
        return case.type, None

    # Collect edits per URI from the response (handle both formats)
    edits_by_uri = {}
    document_changes = result.get('documentChanges', [])
    changes = result.get('changes', {})

    if document_changes:
        for change in document_changes:
            if 'textDocument' in change and 'edits' in change:
                change_uri = change['textDocument'].get('uri', '')
                edits_by_uri.setdefault(change_uri, []).extend(change['edits'])
    elif changes:
        edits_by_uri = dict(changes)

    if not edits_by_uri:
        if case.type == 'error':
            return 'error', None
        return case.type, None

    if case.type == 'diff':
        # Produce per-file diffs: definition files first, rename.py last
        tmpdir = get_tmpdir()
        uri_prefix = 'file://' + tmpdir + '/'

        def uri_sort_key(u):
            return (1 if u == uri else 0, u)

        diff_parts = []
        for file_uri in sorted(edits_by_uri.keys(), key=uri_sort_key):
            file_edits = edits_by_uri[file_uri]
            if file_uri.startswith(uri_prefix):
                rel_path = file_uri[len(uri_prefix):]
            elif file_uri == 'file://' + tmpdir:
                rel_path = ''
            else:
                rel_path = file_uri

            abs_path = os.path.join(tmpdir, rel_path)
            try:
                with open(abs_path, 'r') as f:
                    orig_text = f.read()
            except (IOError, OSError):
                orig_text = ''

            new_text = apply_edits(orig_text, file_edits)
            diff = make_diff(orig_text, new_text, rel_path)
            if diff:
                diff_parts.append(diff)

        if not diff_parts:
            return case.type, None
        return 'diff', ''.join(diff_parts)
    else:
        # For text/error types, use only the rename.py edits
        edits_for_uri = edits_by_uri.get(uri, [])
        if not edits_for_uri:
            if case.type == 'error':
                return 'error', None
            return case.type, None
        new_text = apply_edits(code, edits_for_uri)
        if case.type == 'text':
            return 'text', new_text
        elif case.type == 'error':
            return 'error', new_text
        return case.type, new_text


def apply_edits(text, edits):
    """Apply LSP text edits to source text, end-to-start to avoid offset drift."""
    lines = text.split('\n')

    def sort_key(edit):
        r = edit['range']
        return (r['start']['line'], r['start']['character'])

    sorted_edits = sorted(edits, key=sort_key, reverse=True)

    for edit in sorted_edits:
        start = edit['range']['start']
        end = edit['range']['end']
        new = edit['newText']

        start_offset = _pos_to_offset(lines, start['line'], start['character'])
        end_offset = _pos_to_offset(lines, end['line'], end['character'])

        flat = '\n'.join(lines)
        flat = flat[:start_offset] + new + flat[end_offset:]
        lines = flat.split('\n')

    return '\n'.join(lines)


def _pos_to_offset(lines, line, character):
    """Convert LSP position to flat string offset."""
    offset = 0
    for i in range(min(line, len(lines))):
        offset += len(lines[i]) + 1
    offset += min(character, len(lines[line]) if line < len(lines) else 0)
    return offset


def make_diff(old_text, new_text, filename):
    """Produce unified diff matching jedi's expected format."""
    old_lines = [l + '\n' for l in old_text.split('\n')]
    new_lines = [l + '\n' for l in new_text.split('\n')]

    diff_lines = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile=filename, tofile=filename,
    ))
    # Remove trailing context-only lines that are just whitespace
    while diff_lines and diff_lines[-1].strip() == '':
        diff_lines.pop()
    return ''.join(diff_lines)
