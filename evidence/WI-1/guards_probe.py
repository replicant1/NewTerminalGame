"""WI-1/C5 and C6 against the real commands, on a commit's real tree.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-1/guards_probe.py                   # HEAD
    .venv/bin/python evidence/WI-1/guards_probe.py --commit 8bc9496  # control: the base

It exports the commit into a scratch directory, adds three probe files to its
``tests/`` (they are test files; no production file is touched), and runs the
default command ``python -m pytest -q`` and the desktop command
``python -m pytest -q -m desktop`` there, with ``-rA`` so each test's outcome
is printed by name.  Then it prints one verdict line per claim.

The probes:

* ``test_wi1_probe_desktop.py``: one test marked ``desktop`` that opens nothing.
* ``test_wi1_probe_window.py``: one unmarked test that calls ``tkinter.Tk()``.
* ``conftest.py``: replaces ``_tkinter.create`` with a sentinel that raises
  instead of creating a window, so **no window can open on any commit**, with or
  without a guard.  If the unmarked test reaches it, it prints
  ``WI1-PROBE-WINDOW-WOULD-OPEN``: on a tree without the guard, that is where a real window
  would have appeared.

On HEAD both verdicts should read HOLDS; on the base both should read DOES NOT
HOLD, failing on the claim's own assertion (the desktop test runs by default;
the window request is not refused).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exporting  # noqa: E402

SENTINEL = '''
import _tkinter

_real_create = _tkinter.create


def _create(*args, **kwargs):
    want_tk = args[5] if len(args) > 5 else kwargs.get("wantTk", True)
    if want_tk:
        print("WI1-PROBE-WINDOW-WOULD-OPEN: a real Tk window would have been created here")
        raise RuntimeError("WI1-PROBE-WINDOW-WOULD-OPEN")
    return _real_create(*args, **kwargs)


_tkinter.create = _create
'''

DESKTOP_PROBE = '''
import pytest


@pytest.mark.desktop
def test_probe_marked_desktop():
    pass
'''

WINDOW_PROBE = '''
import tkinter


def test_probe_unmarked_window():
    tkinter.Tk()
'''

DESKTOP_ID = "tests/test_wi1_probe_desktop.py::test_probe_marked_desktop"
WINDOW_ID = "tests/test_wi1_probe_window.py::test_probe_unmarked_window"
REFUSAL = "%s would create a toolkit window, but it is not marked desktop" % WINDOW_ID


def outcome(output: str, nodeid: str) -> str:
    """PASSED / FAILED / ERROR for ``nodeid`` in ``-rA`` output, or 'not run'."""
    match = re.search(r"^(PASSED|FAILED|ERROR|SKIPPED) %s\b" % re.escape(nodeid), output, re.M)
    return match.group(1) if match else "not run"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", default="HEAD")
    commit = parser.parse_args().commit
    tree = exporting.export(commit)
    tests = tree / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "conftest.py").write_text(SENTINEL)
    (tests / "test_wi1_probe_desktop.py").write_text(DESKTOP_PROBE)
    (tests / "test_wi1_probe_window.py").write_text(WINDOW_PROBE)
    print("commit %s exported to %s; probes added under tests/" % (exporting.resolve(commit), tree))

    default = [sys.executable, "-m", "pytest", "-q", "-rA", "-p", "no:cacheprovider"]
    desktop = default + ["-m", "desktop"]
    status_d, out_d = exporting.run(default, tree)
    exporting.show("default command", default, status_d, out_d)
    status_k, out_k = exporting.run(desktop, tree)
    exporting.show("desktop command", desktop, status_k, out_k)

    in_default = outcome(out_d, DESKTOP_ID)
    in_desktop = outcome(out_k, DESKTOP_ID)
    c5 = in_default == "not run" and in_desktop == "PASSED"
    print()
    print("WI-1/C5 %s: the desktop-marked probe under the default command: %s; "
          "under the desktop command: %s"
          % ("HOLDS" if c5 else "DOES NOT HOLD", in_default, in_desktop))

    window = outcome(out_d, WINDOW_ID)
    named = REFUSAL in out_d
    reached = "WI1-PROBE-WINDOW-WOULD-OPEN" in out_d
    c6 = window == "FAILED" and named and not reached
    print("WI-1/C6 %s: the unmarked window probe under the default command: %s; "
          "refusal naming it printed: %s; reached the point a window is created: %s"
          % ("HOLDS" if c6 else "DOES NOT HOLD", window, "yes" if named else "no",
             "YES" if reached else "no"))
    return 0 if (c5 and c6) else 1


if __name__ == "__main__":
    sys.exit(main())
