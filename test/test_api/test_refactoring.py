import os
import shutil
from textwrap import dedent
from pathlib import Path
import platform

import pytest

import jedi
from test.helpers import get_example_dir


@pytest.fixture()
def dir_with_content(tmpdir):
    with open(os.path.join(tmpdir.strpath, 'modx.py'), 'w', newline='') as f:
        f.write('import modx\nfoo\n')  # self reference
    return Path(tmpdir.strpath)


def test_rename_mod(Script, dir_with_content):
    script = Script(
        'import modx; modx\n',
        path=dir_with_content.joinpath('some_script.py'),
        project=jedi.Project(dir_with_content),
    )
    refactoring = script.rename(line=1, new_name='modr')
    refactoring.apply()

    p1 = dir_with_content.joinpath('modx.py')
    p2 = dir_with_content.joinpath('modr.py')
    expected_code = 'import modr\nfoo\n'
    assert not p1.exists()
    with open(p2, newline='') as f:
        assert f.read() == expected_code

    assert refactoring.get_renames() == [(p1, p2)]

    assert refactoring.get_changed_files()[p1].get_new_code() == expected_code

    assert refactoring.get_diff() == dedent('''\
        rename from modx.py
        rename to modr.py
        --- modx.py
        +++ modr.py
        @@ -1,3 +1,3 @@
        -import modx
        +import modr
         foo
        --- some_script.py
        +++ some_script.py
        @@ -1,2 +1,2 @@
        -import modx; modx
        +import modr; modr
        ''').format(dir=dir_with_content)


@pytest.mark.skipif('sys.version_info[:2] < (3, 8)', message="Python 3.8 introduces dirs_exist_ok")
def test_namespace_package(Script, tmpdir):
    origin = get_example_dir('implicit_namespace_package')
    shutil.copytree(origin, tmpdir.strpath, dirs_exist_ok=True)
    sys_path = [
        os.path.join(tmpdir.strpath, 'ns1'),
        os.path.join(tmpdir.strpath, 'ns2')
    ]
    script_path = os.path.join(tmpdir.strpath, 'script.py')
    script = Script(
        'import pkg\n',
        path=script_path,
        project=jedi.Project(os.path.join(tmpdir.strpath, 'does-not-exist'), sys_path=sys_path),
    )
    refactoring = script.rename(line=1, new_name='new_pkg')
    refactoring.apply()
    old1 = os.path.join(sys_path[0], "pkg")
    new1 = os.path.join(sys_path[0], "new_pkg")
    old2 = os.path.join(sys_path[1], "pkg")
    new2 = os.path.join(sys_path[1], "new_pkg")
    assert not os.path.exists(old1)
    assert os.path.exists(new1)
    assert not os.path.exists(old2)
    assert os.path.exists(new2)

    changed, = iter(refactoring.get_changed_files().values())
    assert changed.get_new_code() == "import new_pkg\n"

    assert refactoring.get_diff() == dedent(f'''\
        rename from {old1}
        rename to {new1}
        rename from {old2}
        rename to {new2}
        --- {script_path}
        +++ {script_path}
        @@ -1,2 +1,2 @@
        -import pkg
        +import new_pkg
        ''').format(dir=dir_with_content)


def test_rename_none_path(Script):
    refactoring = Script('foo', path=None).rename(new_name='bar')
    with pytest.raises(jedi.RefactoringError, match='on a Script with path=None'):
        refactoring.apply()
    assert refactoring


def test_diff_without_ending_newline(Script):
    refactoring = Script('a = 1\nb\na').rename(1, 0, new_name='c')
    assert refactoring.get_diff() == dedent('''\
        --- 
        +++ 
        @@ -1,3 +1,3 @@
        -a = 1
        +c = 1
         b
        -a
        +c
        ''')  # noqa: W291


def test_diff_path_outside_of_project(Script):
    if platform.system().lower() == 'windows':
        abs_path = r'D:\unknown_dir\file.py'
    else:
        abs_path = '/unknown_dir/file.py'
    script = Script(
        code='foo = 1',
        path=abs_path,
        project=jedi.get_default_project()
    )
    diff = script.rename(line=1, column=0, new_name='bar').get_diff()
    assert diff == dedent(f'''\
        --- {abs_path}
        +++ {abs_path}
        @@ -1 +1 @@
        -foo = 1
        +bar = 1
        ''')


def test_rename_updates_dunder_all_same_file(Script, tmpdir):
    """Scenario A: __all__ string in the same file as the renamed symbol is updated."""
    code = dedent('''\
        def helper(): pass
        __all__ = ['helper']
        ''')
    path = Path(tmpdir.strpath) / 'utils.py'
    path.write_text(code, encoding='utf-8')
    script = Script(code, path=path, project=jedi.Project(tmpdir.strpath))
    refactoring = script.rename(line=1, column=4, new_name='process')
    new_code = list(refactoring.get_changed_files().values())[0].get_new_code()
    assert 'def process(): pass' in new_code
    assert "'process'" in new_code
    assert "'helper'" not in new_code


def test_rename_updates_dunder_all_cross_file(Script, tmpdir):
    """Scenario B: __all__ string in a re-exporting file is updated alongside the import."""
    utils_code = 'def helper(): pass\n'
    api_code = dedent('''\
        from utils import helper
        __all__ = ['helper']
        ''')
    utils_path = Path(tmpdir.strpath) / 'utils.py'
    api_path = Path(tmpdir.strpath) / 'api.py'
    utils_path.write_text(utils_code, encoding='utf-8')
    api_path.write_text(api_code, encoding='utf-8')

    script = Script(utils_code, path=utils_path, project=jedi.Project(tmpdir.strpath))
    refactoring = script.rename(line=1, column=4, new_name='process')
    changed = {p: f.get_new_code() for p, f in refactoring.get_changed_files().items()}

    api_new = changed[api_path]
    assert 'from utils import process' in api_new
    assert "'process'" in api_new
    assert "'helper'" not in api_new


def test_rename_dunder_all_multi_element(Script, tmpdir):
    """__all__ with multiple entries: only the matching string is updated."""
    code = dedent('''\
        def helper(): pass
        def other(): pass
        __all__ = ['helper', 'other']
        ''')
    path = Path(tmpdir.strpath) / 'mod.py'
    path.write_text(code, encoding='utf-8')
    script = Script(code, path=path, project=jedi.Project(tmpdir.strpath))
    refactoring = script.rename(line=1, column=4, new_name='process')
    new_code = list(refactoring.get_changed_files().values())[0].get_new_code()
    assert "'process'" in new_code
    assert "'other'" in new_code
    assert "'helper'" not in new_code
