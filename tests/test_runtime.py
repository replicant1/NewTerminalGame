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

import ast
import pathlib
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


class TestTheSourceStaysAtThreeNine:
    """The interpreter is 3.14 and the source is 3.9.  This is the seam.

    Before AMEND-6 the interpreter *was* 3.9, so a ``match`` statement failed
    the suite by failing to parse.  The interpreter moved for the Tk bound to
    it, the source did not move with it, and that protection went with the
    interpreter — the review that raised this said so, and it was right.

    ``ast.parse(..., feature_version=(3, 9))`` puts it back without an
    interpreter to run it: CPython's own parser, told to accept only what 3.9
    accepted.

    **What this cannot see.** Syntax only.  ``functools.cache`` is an
    attribute access and ``itertools.pairwise`` is a name — both parse
    perfectly at every version, and no parser will ever catch them.  The
    3.10+ *library* half of section 1.2's list is enforced by review and by
    nothing else, which is stated here so that a green suite is not read as
    saying more than it does.
    """

    LANGUAGE_LEVEL = (3, 9)

    def _sources(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        for package in ("terminal_game", "tests", "tools"):
            for path in sorted((root / package).rglob("*.py")):
                yield path

    def test_every_module_parses_at_the_language_level(self) -> None:
        refused = {}
        for path in self._sources():
            source = path.read_text(encoding="utf-8")
            try:
                ast.parse(source, filename=str(path),
                          feature_version=self.LANGUAGE_LEVEL)
            except SyntaxError as problem:
                refused[path.name] = "line {}: {}".format(
                    problem.lineno, problem.msg)
        assert refused == {}, (
            "these modules use syntax newer than Python {}.{}, which this "
            "interpreter accepts and the language level does not: {}".format(
                self.LANGUAGE_LEVEL[0], self.LANGUAGE_LEVEL[1], refused
            )
        )

    def test_the_check_refuses_syntax_from_above_the_level(self) -> None:
        """The control, without which the test above passes on an empty sweep.

        A parser told to accept 3.9 must actually refuse 3.10.  If this ever
        stops raising, the test above is measuring nothing and says so here
        rather than staying quietly green for years.
        """
        with pytest.raises(SyntaxError):
            ast.parse("match x:\n    case 1:\n        pass\n",
                      feature_version=self.LANGUAGE_LEVEL)

    def test_the_sweep_is_not_empty(self) -> None:
        """And that it found the codebase, rather than an empty directory."""
        found = list(self._sources())
        assert len(found) > 40, (
            "only {} modules found; the sweep is looking in the wrong "
            "place".format(len(found))
        )
