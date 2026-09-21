"""The runtime of IMPLEMENTATION_PLAN.md section 1.2, pinned.

The plan fixed the interpreter at CPython 3.9.6 from ``/usr/bin/python3``
because it was the only interpreter on this machine with a working
``_tkinter``.  **AMEND-6 moved it** to CPython 3.14 from Homebrew, with
``python-tk@3.14``, because the Tk that 3.9.6 binds — 8.5.9, Apple's — maps
windows on this macOS without painting them.  Every window test passed on it
and the two that photograph the screen did not: a plain Tk canvas with no
project code in it came back blank.  So the constraint that chose 3.9.6 has
inverted, and the reason for the pin has not: a developer with a different
Python on their path writes against a different Tk, and nothing complains
until somebody looks at the screen.

So the plan says: *"WI-0 pins the interpreter so a developer finds this out
from a failing suite and not from a user."*  These are that pin.
"""

from __future__ import annotations

import sys

import pytest


def test_the_interpreter_is_python_314() -> None:
    """3.14, not 3.9 — and the difference is which Tk comes with it.

    The interpreter is not chosen for the language it offers.  It is chosen
    for the ``_tkinter`` bound to it, and 3.9.6 on this machine brings a Tk
    that does not draw.  Pinning the version is how that stays chosen.
    """
    assert sys.version_info[0] == 3
    assert sys.version_info[1] == 14, (
        "the plan fixes CPython 3.14 (section 1.2, as amended by AMEND-6) and "
        "this interpreter is {}.{}.{} at {}. Rebuild the environment: "
        "/opt/homebrew/bin/python3.14 -m venv .venv".format(
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

    This is the single measurement that distinguishes a venv built from the
    Homebrew python *with* ``python-tk@3.14`` installed from one built from
    the same python without it, which has no ``_tkinter`` at all.  Getting it
    wrong costs a developer an afternoon in WI-5 or WI-6; here it costs a red
    line at WI-0.

    Importing the binding constructs no ``Tk()`` and therefore puts nothing on
    the user's screen — which is why the version can be read at all in a suite
    bound by section 1.6.
    """
    try:
        import _tkinter
    except ImportError as exc:  # pragma: no cover - only on a wrongly built venv
        pytest.fail(
            "_tkinter is missing from {}, so this environment cannot open a "
            "window and candidate 2 cannot run on it. The Homebrew python has "
            "it only once `brew install python-tk@3.14` has been run; see "
            "README.md. ({})".format(sys.executable, exc)
        )

    assert _tkinter.TK_VERSION.split(".")[0] == "9", (
        "expected a Tk 9.x binding, which is what AMEND-6 measured the font "
        "and the exact-grid ceiling against; this one reports Tk {} / Tcl {}. "
        "Tk 8.5.9 in particular maps windows on this macOS without painting "
        "them, which the whole suite passes and only "
        "tests/test_pixels_reach_the_screen.py catches.".format(
            _tkinter.TK_VERSION, _tkinter.TCL_VERSION
        )
    )
