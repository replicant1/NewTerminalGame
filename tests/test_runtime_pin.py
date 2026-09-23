"""WI-1/C2: under any interpreter but the pinned one, the suite says so plainly.

The pure half (:mod:`tools.runtime_pin`) is driven with made-up interpreters
here.  The seam, that the suite really stops with that message, is driven for
real in ``tests/test_suite_guards.py``, and against a real 3.9 interpreter by
``evidence/WI-1/runtime_probe.py``.
"""

from __future__ import annotations

import os

from tools import runtime_pin
from tools.runtime_pin import Runtime

PINNED_FILE = "/opt/homebrew/Cellar/python@3.14/3.14.7/Frameworks/Python.framework/Versions/3.14/bin/python3.14"
APPLE_39 = "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9"


def _runtime(**changes) -> Runtime:
    good = Runtime(implementation="CPython", version=(3, 14, 7), executable=PINNED_FILE,
                   tk_version="9.0", tcl_patchlevel="9.0.4", tk_error=None)
    return good._replace(**changes)


def test_the_pinned_interpreter_has_no_problems():
    assert runtime_pin.problems(_runtime(), pinned_path=PINNED_FILE) == []


def test_apples_39_with_tk_85_is_refused_on_every_count():
    found = _runtime(version=(3, 9, 6), executable=APPLE_39,
                     tk_version="8.5", tcl_patchlevel="8.5.9")
    wrong = runtime_pin.problems(found, pinned_path=PINNED_FILE)
    assert wrong == [
        "the version is 3.9.6, not 3.14",
        "the interpreter is %s, not /opt/homebrew/bin/python3.14 (which is %s)"
        % (APPLE_39, PINNED_FILE),
        "Tk is 8.5, not 9",
        "Tcl is 8.5.9, not 9",
    ]


def test_the_refusal_names_what_it_found_and_what_it_wants():
    found = _runtime(version=(3, 9, 6), executable=APPLE_39,
                     tk_version="8.5", tcl_patchlevel="8.5.9")
    message = runtime_pin.refusal(found, runtime_pin.problems(found, pinned_path=PINNED_FILE))
    lines = message.splitlines()
    assert lines[1] == "  found:  CPython 3.9.6 at %s, Tk 8.5 (Tcl 8.5.9)" % APPLE_39
    assert lines[2] == "  wanted: CPython 3.14 at /opt/homebrew/bin/python3.14, Tk 9"
    assert lines[-1] == "  " + runtime_pin.REBUILD_COMMAND


def test_the_pinned_path_without_a_tkinter_is_refused_for_its_tk():
    found = _runtime(tk_version=None, tcl_patchlevel=None,
                     tk_error="ModuleNotFoundError: No module named '_tkinter'")
    wrong = runtime_pin.problems(found, pinned_path=PINNED_FILE)
    assert wrong == ["Tk does not work here (ModuleNotFoundError: No module named '_tkinter')"]
    found_line = runtime_pin.refusal(found, wrong).splitlines()[1]
    assert found_line == ("  found:  CPython 3.14.7 at %s, no working Tk "
                          "(ModuleNotFoundError: No module named '_tkinter')" % PINNED_FILE)


def test_a_tk_86_build_of_the_right_version_elsewhere_is_refused():
    elsewhere = "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14"
    found = _runtime(executable=elsewhere, tk_version="8.6", tcl_patchlevel="8.6.16")
    wrong = runtime_pin.problems(found, pinned_path=PINNED_FILE)
    assert wrong == [
        "the interpreter is %s, not /opt/homebrew/bin/python3.14 (which is %s)"
        % (elsewhere, PINNED_FILE),
        "Tk is 8.6, not 9",
        "Tcl is 8.6.16, not 9",
    ]


def test_another_implementation_is_refused():
    wrong = runtime_pin.problems(_runtime(implementation="PyPy"), pinned_path=PINNED_FILE)
    assert wrong == ["the implementation is PyPy, not CPython"]


def test_by_default_the_pin_is_the_file_behind_the_homebrew_path():
    found = _runtime(executable=os.path.realpath(runtime_pin.PINNED_INTERPRETER))
    assert runtime_pin.problems(found) == []


def test_this_run_is_under_the_pinned_interpreter_with_tk_9():
    """What the suite measured about itself at start-up: the thing C2 protects."""
    found = runtime_pin.current_runtime()
    assert runtime_pin.problems(found) == [], runtime_pin.refusal(found, runtime_pin.problems(found))
    assert found.tk_version.startswith("9.")
