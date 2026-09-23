"""The suite's own guards, as a pytest plugin.  (WI-1/C2, C5, C6)

IMPLEMENTATION_PLAN.md states three rules about how the suite runs.  Each is
enforced here rather than written down, because a rule nothing re-checks is a
guard that was never exercised:

* **The pinned interpreter** (section 1.2, WI-1/C2).  At start-up the plugin
  asks :mod:`tools.runtime_pin` whether this is CPython 3.14 at
  ``/opt/homebrew/bin/python3.14`` with Tk 9, and if not, stops the run with a
  usage error that names what it found and what it wants.  No test runs, so no
  test can pass or fail for a reason unrelated to the code.

* **Desktop tests are opt-in** (section 1.2, WI-1/C5).  A test marked
  ``@pytest.mark.desktop`` opens real windows.  It runs only when the ``-m``
  expression names ``desktop``, as the desktop command
  ``.venv/bin/python -m pytest -q -m desktop`` does.  Otherwise it is
  deselected, whatever else is on the command line.

* **The default suite opens no window** (section 1.6, WI-1/C6).  Every Tk
  window starts in ``_tkinter.create`` with ``wantTk`` true, or in
  ``tkinter.Tk.loadtk`` for an interpreter made with ``tkinter.Tcl()``.  Both
  are replaced for the whole session.  Inside a test marked ``desktop`` they
  pass straight through; anywhere else (an unmarked test, its fixtures, or a
  test module being imported) they fail the test *before* the window exists,
  naming it.  A Tcl interpreter with no Tk (``tkinter.Tcl()``) is allowed
  everywhere: it has no window.

  **What this cannot see:** a window made by *another process* that a test
  starts, and a window made by evaluating ``package require Tk`` in a bare Tcl
  interpreter.  A test that launches the game as a subprocess must carry the
  ``desktop`` mark; nothing here can tell that it should.

Loaded by the repository's root ``conftest.py``.  It must stay importable by
Python 3.9, so that the interpreter check can refuse a 3.9 interpreter plainly.
"""

from __future__ import annotations

from typing import Optional

import pytest

from tools import runtime_pin

#: The marker that says "this test opens real windows".
DESKTOP = "desktop"

MARKER_HELP = (
    "desktop: opens real windows on the user's desktop. Run only by "
    "`.venv/bin/python -m pytest -q -m desktop`, never by the default suite "
    "(IMPLEMENTATION_PLAN.md sections 1.2 and 1.6). Follow the window hygiene "
    "in .claude/agents/developer.md: capture your own window, reap it on "
    "success and on failure."
)

_attempt_key = pytest.StashKey()  # type: pytest.StashKey[list]

# What pytest is doing right now, for the guard to consult.
_current_item = None  # type: Optional[pytest.Item]
_collecting = None  # type: Optional[str]
_originals = {}  # type: dict


class WindowRefused(Exception):
    """Raised in place of creating a window outside a desktop test."""


def refusal_message(where: str) -> str:
    return (
        "%s would create a toolkit window, but it is not marked desktop. "
        "The default suite never opens a window (IMPLEMENTATION_PLAN.md "
        "section 1.6). If it must open one, mark it @pytest.mark.desktop and "
        "follow the window hygiene in .claude/agents/developer.md; otherwise "
        "keep it off the toolkit." % where
    )


def _refuse() -> None:
    item = _current_item
    if item is None:
        where = "Collecting %s" % (_collecting or "the suite")
        raise WindowRefused(refusal_message(where))
    message = refusal_message(item.nodeid)
    item.stash.setdefault(_attempt_key, []).append(message)
    # Failed is a BaseException, so an ``except Exception`` in the test
    # cannot swallow it; the report hook below catches ``except BaseException``.
    pytest.fail(message, pytrace=False)


def _windows_allowed() -> bool:
    item = _current_item
    return item is not None and item.get_closest_marker(DESKTOP) is not None


def _install_window_guard() -> None:
    try:
        import _tkinter
        import tkinter
    except ImportError:
        return  # no toolkit, so no window can come from it
    real_create = _tkinter.create
    real_loadtk = tkinter.Tk.loadtk

    def create(*args, **kwargs):
        want_tk = args[5] if len(args) > 5 else kwargs.get("wantTk", True)
        if want_tk and not _windows_allowed():
            _refuse()
        return real_create(*args, **kwargs)

    def loadtk(self):
        if not _windows_allowed():
            _refuse()
        return real_loadtk(self)

    _originals["create"] = (_tkinter, real_create)
    _originals["loadtk"] = (tkinter.Tk, real_loadtk)
    _tkinter.create = create
    tkinter.Tk.loadtk = loadtk


def _remove_window_guard() -> None:
    if "create" in _originals:
        module, real = _originals.pop("create")
        module.create = real
    if "loadtk" in _originals:
        cls, real = _originals.pop("loadtk")
        cls.loadtk = real


# --------------------------------------------------------------------------
# Hooks
# --------------------------------------------------------------------------


def pytest_configure(config):
    config.addinivalue_line("markers", MARKER_HELP)
    found = runtime_pin.current_runtime()
    wrong = runtime_pin.problems(found)
    if wrong:
        raise pytest.UsageError(runtime_pin.refusal(found, wrong))
    config.stash[_runtime_key] = found
    _install_window_guard()


def pytest_unconfigure(config):
    _remove_window_guard()


_runtime_key = pytest.StashKey()  # type: pytest.StashKey[runtime_pin.Runtime]


def pytest_report_header(config):
    found = config.stash.get(_runtime_key, None)
    if found is None:
        return None
    return "runtime: %s (the pinned interpreter)" % runtime_pin.describe_found(found)


def pytest_collectstart(collector):
    global _collecting
    _collecting = collector.nodeid or str(collector.path)


def pytest_collection_modifyitems(config, items):
    expression = config.getoption("markexpr") or ""
    if DESKTOP in expression:
        return  # the -m expression speaks about desktop tests; let it decide
    kept = [item for item in items if item.get_closest_marker(DESKTOP) is None]
    if len(kept) != len(items):
        dropped = [item for item in items if item.get_closest_marker(DESKTOP) is not None]
        config.hook.pytest_deselected(items=dropped)
        items[:] = kept


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item, nextitem):
    global _current_item
    _current_item = item
    try:
        return (yield)
    finally:
        _current_item = None


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    attempts = item.stash.get(_attempt_key, None)
    if attempts and report.passed:
        # The test caught the refusal and carried on.  It still asked for a
        # window, so it still fails.
        report.outcome = "failed"
        report.longrepr = attempts[0]
    if attempts and report.failed:
        item.stash[_attempt_key] = []
    return report
