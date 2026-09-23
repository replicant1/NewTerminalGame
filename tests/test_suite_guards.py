"""WI-1/C2, C5, C6: the suite's guards, run through the repository's real config.

Each test builds a throwaway project with pytest's ``pytester``, copies this
repository's own ``pyproject.toml`` and ``conftest.py`` into it, adds a few test
files, and runs ``python -m pytest`` in a subprocess there.  So what is run is
the default command (``-q``) or the desktop command (``-q -m desktop``) under
the configuration this repository ships, not a stand-in for it.

**No test here can open a window, even if the guard is broken.**  The
throwaway project's ``tests/conftest.py`` replaces ``_tkinter.create`` and
``tkinter.Tk.loadtk`` with sentinels *before* the guard wraps them.  A request
for a Tcl interpreter without Tk passes through to the real thing; a request
for a window raises ``RuntimeError("SENTINEL ...")`` instead of making one.  If
the guard works, the sentinel is never reached for an unmarked test.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SENTINEL_CONFTEST = '''
import _tkinter
import tkinter

_real_create = _tkinter.create


def _create(*args, **kwargs):
    want_tk = args[5] if len(args) > 5 else kwargs.get("wantTk", True)
    if want_tk:
        print("SENTINEL-REACHED create")
        raise RuntimeError("SENTINEL: a real Tk window would have been created here")
    return _real_create(*args, **kwargs)


def _loadtk(self):
    print("SENTINEL-REACHED loadtk")
    raise RuntimeError("SENTINEL: Tk would have been loaded into a Tcl interpreter here")


_tkinter.create = _create
tkinter.Tk.loadtk = _loadtk
'''


@pytest.fixture
def project(pytester, monkeypatch):
    """A throwaway project carrying this repository's real suite configuration."""
    shutil.copy(ROOT / "pyproject.toml", pytester.path / "pyproject.toml")
    shutil.copy(ROOT / "conftest.py", pytester.path / "conftest.py")
    (pytester.path / "tests").mkdir()
    (pytester.path / "tests" / "conftest.py").write_text(SENTINEL_CONFTEST)
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    return pytester


def _write(project, name, source):
    (project.path / "tests" / name).write_text(source)


# --------------------------------------------------------------------------
# The seam: this very run loaded the guards
# --------------------------------------------------------------------------


def test_the_real_suite_loads_the_guards(request):
    assert request.config.pluginmanager.hasplugin("tools.pytest_guards")


def test_the_header_names_the_runtime_the_suite_is_running_under(project):
    """WI-1/A5: a passing run says which interpreter and Tk it accepted."""
    _write(project, "test_ordinary.py", "def test_ordinary():\n    pass\n")
    result = project.runpytest_subprocess()
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([
        "runtime: CPython 3.14.* at *python3.14, Tk 9.* (Tcl 9.*) (the pinned interpreter)"])


# --------------------------------------------------------------------------
# WI-1/C5: desktop tests run only under the desktop command
# --------------------------------------------------------------------------

TWO_KINDS = '''
import pytest

def test_ordinary():
    pass

@pytest.mark.desktop
def test_on_the_desktop():
    pass
'''


def test_the_default_command_does_not_run_a_desktop_test(project):
    _write(project, "test_two_kinds.py", TWO_KINDS)
    result = project.runpytest_subprocess("-q", "-rA")
    result.assert_outcomes(passed=1, deselected=1)
    result.stdout.fnmatch_lines(["PASSED tests/test_two_kinds.py::test_ordinary"])
    result.stdout.no_fnmatch_line("*test_on_the_desktop*")


def test_the_desktop_command_runs_the_desktop_test(project):
    _write(project, "test_two_kinds.py", TWO_KINDS)
    result = project.runpytest_subprocess("-q", "-rA", "-m", "desktop")
    result.assert_outcomes(passed=1, deselected=1)
    result.stdout.fnmatch_lines(["PASSED tests/test_two_kinds.py::test_on_the_desktop"])
    result.stdout.no_fnmatch_line("*test_ordinary*")


def test_another_mark_expression_still_leaves_desktop_tests_out(project):
    """WI-1/A1: ``-m`` that does not name ``desktop`` cannot let one in."""
    _write(project, "test_two_kinds.py", TWO_KINDS)
    result = project.runpytest_subprocess("-q", "-rA", "-m", "not slow")
    result.assert_outcomes(passed=1, deselected=1)
    result.stdout.no_fnmatch_line("*test_on_the_desktop*")


def test_naming_a_desktop_test_directly_does_not_run_it(project):
    """WI-1/A1: a node id on the command line is not the desktop command."""
    _write(project, "test_two_kinds.py", TWO_KINDS)
    result = project.runpytest_subprocess(
        "-q", "-rA", "tests/test_two_kinds.py::test_on_the_desktop")
    result.assert_outcomes(deselected=1)


def test_a_misspelt_desktop_mark_is_an_error_not_an_ordinary_test(project):
    """WI-1/A2: ``--strict-markers`` from the real config."""
    _write(project, "test_typo.py", "import pytest\n\n@pytest.mark.dekstop\ndef test_x():\n    pass\n")
    result = project.runpytest_subprocess("-q")
    assert result.ret != 0
    result.stdout.fnmatch_lines(["*'dekstop' not found in `markers` configuration option*"])


# --------------------------------------------------------------------------
# WI-1/C6: an unmarked test that would create a window fails, naming itself
# --------------------------------------------------------------------------

REFUSAL = "would create a toolkit window, but it is not marked desktop"


def test_an_unmarked_test_creating_a_tk_window_fails_naming_itself(project):
    _write(project, "test_window.py",
           "import tkinter\n\ndef test_opens_a_window():\n    tkinter.Tk()\n")
    result = project.runpytest_subprocess("-q")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*tests/test_window.py::test_opens_a_window " + REFUSAL + "*"])
    result.stdout.no_fnmatch_line("*SENTINEL*")


def test_a_toplevel_without_a_root_is_refused_too(project):
    _write(project, "test_toplevel.py",
           "import tkinter\n\ndef test_toplevel():\n    tkinter.Toplevel()\n")
    result = project.runpytest_subprocess("-q")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*tests/test_toplevel.py::test_toplevel " + REFUSAL + "*"])
    result.stdout.no_fnmatch_line("*SENTINEL*")


def test_loading_tk_into_a_tcl_interpreter_is_refused(project):
    _write(project, "test_loadtk.py",
           "import tkinter\n\ndef test_loadtk():\n    tkinter.Tcl().loadtk()\n")
    result = project.runpytest_subprocess("-q")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*tests/test_loadtk.py::test_loadtk " + REFUSAL + "*"])
    result.stdout.no_fnmatch_line("*SENTINEL*")


def test_a_test_that_swallows_the_refusal_still_fails(project):
    _write(project, "test_swallow.py", (
        "import tkinter\n\n"
        "def test_swallows():\n"
        "    try:\n"
        "        tkinter.Tk()\n"
        "    except BaseException:\n"
        "        pass\n"))
    result = project.runpytest_subprocess("-q")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*tests/test_swallow.py::test_swallows " + REFUSAL + "*"])
    result.stdout.no_fnmatch_line("*SENTINEL*")


def test_a_fixture_creating_a_window_fails_the_test_that_uses_it(project):
    _write(project, "test_fixture.py", (
        "import pytest, tkinter\n\n"
        "@pytest.fixture(scope='session')\n"
        "def root():\n"
        "    return tkinter.Tk()\n\n"
        "def test_uses_root(root):\n"
        "    pass\n"))
    result = project.runpytest_subprocess("-q")
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*tests/test_fixture.py::test_uses_root " + REFUSAL + "*"])
    result.stdout.no_fnmatch_line("*SENTINEL*")


def test_a_module_creating_a_window_on_import_fails_naming_the_module(project):
    _write(project, "test_import_time.py",
           "import tkinter\nROOT = tkinter.Tk()\n\ndef test_x():\n    pass\n")
    result = project.runpytest_subprocess("-q")
    assert result.ret != 0
    result.stdout.fnmatch_lines(["*Collecting tests/test_import_time.py " + REFUSAL + "*"])
    result.stdout.no_fnmatch_line("*SENTINEL*")


def test_a_tcl_interpreter_without_tk_is_allowed(project):
    _write(project, "test_tcl.py", (
        "import tkinter\n\n"
        "def test_tcl():\n"
        "    assert tkinter.Tcl().call('expr', '6 * 7') == 42\n"))
    result = project.runpytest_subprocess("-q")
    result.assert_outcomes(passed=1)


def test_a_desktop_test_under_the_desktop_command_reaches_the_toolkit(project):
    """The guard steps aside for a marked test: its call reaches Tk (here, the sentinel)."""
    _write(project, "test_desktop_window.py", (
        "import pytest, tkinter\n\n"
        "@pytest.mark.desktop\n"
        "def test_desktop_window():\n"
        "    with pytest.raises(RuntimeError, match='SENTINEL'):\n"
        "        tkinter.Tk()\n"))
    result = project.runpytest_subprocess("-q", "-s", "-m", "desktop")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["SENTINEL-REACHED create*"])


# --------------------------------------------------------------------------
# WI-1/C2, the seam: the real suite stops with the message
# --------------------------------------------------------------------------


def test_the_pinned_interpreter_without_tkinter_stops_the_suite_plainly(project, monkeypatch, tmp_path):
    """A ``_tkinter.py`` early on the path hides the real one, as Homebrew's
    3.14 once shipped.  The suite must stop and say so, running nothing."""
    hide = tmp_path / "no_tk"
    hide.mkdir()
    (hide / "_tkinter.py").write_text(
        "raise ImportError('simulated: this interpreter has no _tkinter')\n")
    monkeypatch.setenv("PYTHONPATH", "%s:%s" % (hide, ROOT))
    (project.path / "tests" / "conftest.py").unlink()  # the sentinel needs a real _tkinter
    _write(project, "test_ordinary.py", "def test_ordinary():\n    pass\n")
    result = project.runpytest_subprocess("-q")
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    output = result.stderr.str()
    assert "This is not the interpreter the project is pinned to" in output
    assert "no working Tk (ImportError: simulated: this interpreter has no _tkinter)" in output
    assert "  wanted: CPython 3.14 at /opt/homebrew/bin/python3.14, Tk 9" in output
    assert "passed" not in result.stdout.str()
