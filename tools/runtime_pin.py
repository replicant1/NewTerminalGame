"""Is this the interpreter the project is pinned to?  (WI-1/C2)

IMPLEMENTATION_PLAN.md section 1.2 pins the runtime to CPython 3.14 at
``/opt/homebrew/bin/python3.14``, with Tk 9.  Two other interpreters are on
this machine and both look plausible: ``/usr/bin/python3`` is 3.9 with Apple's
deprecated Tk 8.5, and Homebrew's own 3.14 shipped without ``_tkinter`` as
recently as 17 September 2026.  A suite run under either would pass or fail
for reasons that have nothing to do with the code under test.

This module answers the question and words the answer.  The pytest plugin in
:mod:`tools.pytest_guards` asks it at start-up and refuses to run the suite
when the answer is no.

**It must stay importable by Python 3.9**, because refusing a 3.9 interpreter
plainly is half of its job: no syntax or standard-library call newer than 3.9.

What "a working Tk 9" means here, and its limit: ``tkinter`` imports, reports
Tk 9, and can build a Tcl interpreter that reports Tcl 9.  Tk itself is *not*
initialised, because initialising Tk creates a window and the default suite
must never open one (section 1.6).  Whether Tk really draws is the desktop
tests' question, not this one.
"""

from __future__ import annotations

import os
import platform
import sys
from typing import List, NamedTuple, Optional

#: The interpreter section 1.2 pins.
PINNED_INTERPRETER = "/opt/homebrew/bin/python3.14"
PINNED_IMPLEMENTATION = "CPython"
PINNED_VERSION = (3, 14)
PINNED_TK_MAJOR = 9

#: The command that builds the environment, from section 1.2 and the README.
REBUILD_COMMAND = (
    "rm -rf .venv && /opt/homebrew/bin/python3.14 -m venv .venv"
    " && .venv/bin/python -m pip install -r requirements.txt"
)


class Runtime(NamedTuple):
    """What an interpreter says about itself, gathered once."""

    implementation: str  # "CPython"
    version: tuple  # (3, 14, 7)
    executable: str  # the resolved path of the base interpreter
    tk_version: Optional[str]  # "9.0", or None when tkinter would not load
    tcl_patchlevel: Optional[str]  # "9.0.4", or None
    tk_error: Optional[str]  # why tkinter would not load or run, or None


def base_executable() -> str:
    """The real file of the interpreter behind this one, through any venv.

    A venv's ``bin/python`` is a symlink to the interpreter it was made from.
    Python 3.11 and later also record that interpreter as
    ``sys._base_executable``; 3.9 records the venv's own path there, which the
    symlink resolution then follows.  Either way this ends at the real file.
    """
    candidate = getattr(sys, "_base_executable", None) or sys.executable
    return os.path.realpath(candidate)


def current_runtime() -> Runtime:
    """Describe the running interpreter.  Opens no window."""
    tk_version = None
    tcl_patchlevel = None
    tk_error = None
    try:
        import tkinter

        tk_version = str(tkinter.TkVersion)
        # Tcl() is Tk(useTk=False): an interpreter with no window at all.
        interp = tkinter.Tcl()
        tcl_patchlevel = str(interp.call("info", "patchlevel"))
    except Exception as exc:  # ImportError, TclError: both mean "no working Tk"
        tk_error = "%s: %s" % (type(exc).__name__, exc)
    return Runtime(
        implementation=platform.python_implementation(),
        version=tuple(sys.version_info[:3]),
        executable=base_executable(),
        tk_version=tk_version,
        tcl_patchlevel=tcl_patchlevel,
        tk_error=tk_error,
    )


def _major(version: Optional[str]) -> Optional[int]:
    try:
        return int(str(version).split(".")[0])
    except (TypeError, ValueError):
        return None


def problems(found: Runtime, pinned_path: Optional[str] = None) -> List[str]:
    """Every way ``found`` differs from the pin.  Empty means it is the pin.

    ``pinned_path`` is the resolved pinned interpreter; by default the real
    file behind :data:`PINNED_INTERPRETER`, looked up now.
    """
    if pinned_path is None:
        pinned_path = os.path.realpath(PINNED_INTERPRETER)
    wrong = []
    if found.implementation != PINNED_IMPLEMENTATION:
        wrong.append("the implementation is %s, not %s"
                     % (found.implementation, PINNED_IMPLEMENTATION))
    if tuple(found.version[:2]) != PINNED_VERSION:
        wrong.append("the version is %s, not %s"
                     % (_dotted(found.version), _dotted(PINNED_VERSION)))
    if found.executable != pinned_path:
        wrong.append("the interpreter is %s, not %s (which is %s)"
                     % (found.executable, PINNED_INTERPRETER, pinned_path))
    if found.tk_error is not None:
        wrong.append("Tk does not work here (%s)" % found.tk_error)
    else:
        if _major(found.tk_version) != PINNED_TK_MAJOR:
            wrong.append("Tk is %s, not %d" % (found.tk_version, PINNED_TK_MAJOR))
        if _major(found.tcl_patchlevel) != PINNED_TK_MAJOR:
            wrong.append("Tcl is %s, not %d" % (found.tcl_patchlevel, PINNED_TK_MAJOR))
    return wrong


def _dotted(version) -> str:
    return ".".join(str(part) for part in version)


def describe_found(found: Runtime) -> str:
    if found.tk_error is not None:
        tk = "no working Tk (%s)" % found.tk_error
    else:
        tk = "Tk %s (Tcl %s)" % (found.tk_version, found.tcl_patchlevel)
    return "%s %s at %s, %s" % (found.implementation, _dotted(found.version),
                                found.executable, tk)


def describe_wanted() -> str:
    return "%s %s at %s, Tk %d" % (PINNED_IMPLEMENTATION, _dotted(PINNED_VERSION),
                                   PINNED_INTERPRETER, PINNED_TK_MAJOR)


def refusal(found: Runtime, wrong: List[str]) -> str:
    """The message the suite stops with.  Names what it found and what it wants."""
    lines = [
        "The suite will not run: this is not the pinned interpreter with a "
        "working Tk 9 (IMPLEMENTATION_PLAN.md section 1.2).",
        "  found:  " + describe_found(found),
        "  wanted: " + describe_wanted(),
    ]
    lines.extend("  - " + reason for reason in wrong)
    lines.append("Rebuild the environment from the repository root:")
    lines.append("  " + REBUILD_COMMAND)
    return "\n".join(lines)
