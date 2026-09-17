"""The runtime of IMPLEMENTATION_PLAN.md section 1.2, pinned.

The plan fixes the interpreter at CPython 3.9.6 from ``/usr/bin/python3``,
inside a project virtual environment, because it is the only interpreter on
this machine with a working ``_tkinter`` and candidate 2 needs a window.  That
is an uncomfortable constraint and it is easy to drift off: a developer with a
newer Python on their path writes ``match`` or ``list[int]``, and nothing
complains until somebody runs the game.

So the plan says: *"WI-0 pins the interpreter so a developer finds this out
from a failing suite and not from a user."*  These are that pin.
"""

from __future__ import annotations

import sys

import pytest


def test_the_interpreter_is_python_39() -> None:
    """3.9, not 3.10 and not 3.14.

    Being on 3.10+ is what silently makes ``match``, ``X | Y`` and
    ``functools.cache`` work here and fail for everybody else.
    """
    assert sys.version_info[0] == 3
    assert sys.version_info[1] == 9, (
        "the plan fixes CPython 3.9 (section 1.2) and this interpreter is "
        "{}.{}.{} at {}. Rebuild the environment: "
        "/usr/bin/python3 -m venv .venv".format(
            sys.version_info[0], sys.version_info[1], sys.version_info[2], sys.executable
        )
    )


def test_the_suite_runs_inside_a_virtual_environment() -> None:
    """The suite command names ``.venv/bin/python``, and this checks it got one.

    Running the suite with a system-wide pytest works right up until the
    interpreter differs from everybody else's, which is the failure this
    project cannot afford at WI-0.
    """
    assert sys.prefix != sys.base_prefix, (
        "this suite is running on {} which is not a virtual environment. The "
        "suite command is `.venv/bin/python -m pytest -q` from the repository "
        "root (section 1.2); see README.md to build the environment.".format(
            sys.executable
        )
    )


def test_the_windowing_binding_is_present() -> None:
    """``_tkinter`` is importable, and says which Tk it is bound to.

    This is the single measurement that distinguishes a venv built from
    ``/usr/bin/python3`` from one built from the Homebrew python, which has no
    ``_tkinter`` at all.  Getting it wrong costs a developer an afternoon in
    WI-5 or WI-6; here it costs a red line at WI-0.

    Importing the binding constructs no ``Tk()`` and therefore puts nothing on
    the user's screen — which is why the version can be read at all in a suite
    bound by section 1.6.
    """
    try:
        import _tkinter
    except ImportError as exc:  # pragma: no cover - only on a wrongly built venv
        pytest.fail(
            "_tkinter is missing from {}, so this environment cannot open a "
            "window and candidate 2 cannot run on it. The venv must be created "
            "from /usr/bin/python3, which has it; the Homebrew python does "
            "not. ({})".format(sys.executable, exc)
        )

    assert _tkinter.TK_VERSION.split(".")[0] == "8", (
        "expected a Tk 8.x binding, which is what section 1.2 measured and "
        "what S-1 is testing against; this one reports Tk {} / Tcl {}. If a "
        "modern Tk has been installed deliberately (section 9, human item 5) "
        "then this assertion is the one place that has to move.".format(
            _tkinter.TK_VERSION, _tkinter.TCL_VERSION
        )
    )
