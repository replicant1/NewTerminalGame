# -*- coding: utf-8 -*-
"""WI-10 — the rules of the house, as something a machine can check.

Six rules, restated by amendment 2 of the implementation plan, each one a
function that walks the tree and reports where it is broken.  The test module
next door runs them over this repository and over small planted trees.

Why this exists at all
----------------------
Every rule here is one a careful person would keep anyway.  The reason to
spend a day writing them down is that **in M0 two spellings of the root
package landed on ``main`` within hours of each other and the suite stayed
green**, because neither imported the other.  A rule nobody can violate by
accident is worth a line of code; this is the class of mistake nobody
notices.

Why the checks read the syntax tree and not the text
-----------------------------------------------------
``terminal_game/shell/grid_surface.py``'s own docstring says, in as many
words, *"do not add ``create_image``, ``create_bitmap``,
``create_rectangle``…"*.  A grep for those names would fail the file whose
documentation is the thing keeping the rule.  Every check below parses with
:mod:`ast` and looks at **calls and imports**, so a name written in prose
costs nothing and a name actually invoked is caught.

What each rule does not cover, stated rather than hidden
--------------------------------------------------------
``create_window`` is **not** in rule 3's forbidden set.  On a Tk canvas that
method embeds a widget, but in this project it is the name of the toolkit
seam's own method for making the game's window — ``Toolkit.create_window`` —
and it is called by the window owner on every run.  Forbidding it would fail
honest work; so rule 3 forbids the seven canvas drawing primitives and the
two image classes, and the stronger property that *the only canvas item the
surface ever creates is a ``create_text``* is owned by WI-2's own tests
against the recording double, which assert the recorded item kinds are
exactly ``{"text"}``.

Deliberately not named ``test_*``: this is apparatus, not a test case.
"""

from __future__ import annotations

import ast
import os
from typing import Dict, Iterable, List, NamedTuple, Optional, Sequence, Tuple

__all__ = [
    "REPOSITORY_ROOT",
    "Violation",
    "Report",
    "TEST_PACKAGE",
    "SCRIPT_PACKAGE",
    "python_files",
    "imports_of",
    "no_toolkit_below_the_shell",
    "domain_names_nothing_above_it",
    "nothing_draws_an_image",
    "exactly_one_root_package",
    "no_tk_interpreter_constructed",
    "nothing_but_tests_depends_on_tests",
    "TREE_RULES",
]


#: The repository this file lives in: ``tests/`` is one level down.
REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The suite.  Not the application, and allowed to reach anywhere.
TEST_PACKAGE = "tests"

#: Scripts a person runs deliberately.  Not the application either, but they
#: are not tests, so rules 3 and 6 apply to them.
SCRIPT_PACKAGE = "tools"

#: The name of the windowing toolkit, and anything under it.
TOOLKIT = "tkinter"

#: Canvas methods that put something other than a character on the screen
#: (caution C5, the price candidate 2 pays for SCRN-2).
DRAWING_PRIMITIVES = frozenset(
    (
        "create_image",
        "create_bitmap",
        "create_rectangle",
        "create_line",
        "create_oval",
        "create_polygon",
        "create_arc",
    )
)

#: Classes that are an image however they are drawn.
IMAGE_CLASSES = frozenset(("PhotoImage", "BitmapImage"))

#: Modules that tell the time.  The Domain is handed a cadence; it does not
#: go and look at a clock.
CLOCK_MODULES = frozenset(("time", "datetime", "calendar"))

#: ``random.Random`` as a type is fine — the Domain is *handed* one of those.
#: Reaching for the module's own global generator is not.
GLOBAL_RANDOM_FUNCTIONS = frozenset(
    (
        "random",
        "randint",
        "randrange",
        "choice",
        "choices",
        "shuffle",
        "sample",
        "seed",
        "uniform",
        "getrandbits",
    )
)


class Violation(NamedTuple):
    """One place a rule is broken, named well enough to go and fix it."""

    path: str
    line: int
    detail: str

    def __str__(self) -> str:
        return "{0}:{1}: {2}".format(self.path, self.line, self.detail)


def _vacuous(rule: str) -> Violation:
    """A rule that found nothing to look at has not passed; it was skipped."""
    return Violation(
        ".",
        0,
        "inspected no files at all, so this rule proves nothing; a guard "
        "that can pass over an empty set is worse than no guard",
    )


class Report(NamedTuple):
    """What one rule found, and what it looked at.

    ``inspected`` is what makes the guard unable to pass vacuously, and the
    rules do not leave that to the caller: a report built by :func:`_report`
    with nothing inspected carries a violation saying so.  A green run of
    this guard therefore means the rules were applied to real files, not that
    a path went stale and quietly matched nothing.
    """

    rule: str
    inspected: Tuple[str, ...]
    violations: Tuple[Violation, ...]

    @property
    def clean(self) -> bool:
        return not self.violations

    def describe(self) -> str:
        if not self.inspected:
            return "{0}: INSPECTED NOTHING".format(self.rule)
        if self.clean:
            return "{0}: clean over {1} files".format(
                self.rule, len(self.inspected)
            )
        return "{0}: {1} violation(s) over {2} files\n  {3}".format(
            self.rule,
            len(self.violations),
            len(self.inspected),
            "\n  ".join(str(violation) for violation in self.violations),
        )


def _report(
    rule: str, inspected: Sequence[str], violations: Sequence[Violation]
) -> Report:
    """Build a report, failing it outright if it inspected nothing."""
    found = list(violations)
    if not inspected:
        found.insert(0, _vacuous(rule))
    return Report(rule, tuple(inspected), tuple(found))


# ---------------------------------------------------------------------------
# Walking the tree
# ---------------------------------------------------------------------------


def python_files(root: str, within: Optional[str] = None) -> Tuple[str, ...]:
    """Every ``.py`` file under *root*, as paths relative to *root*.

    *within* restricts to one subtree, given as a relative path.  Hidden
    directories and ``__pycache__`` are skipped; nothing else is.
    """
    base = root if within is None else os.path.join(root, within)
    found: List[str] = []
    for directory, subdirectories, filenames in os.walk(base):
        subdirectories[:] = sorted(
            name
            for name in subdirectories
            if not name.startswith(".") and name != "__pycache__"
        )
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                found.append(
                    os.path.relpath(os.path.join(directory, filename), root)
                )
    return tuple(sorted(found))


def top_level_packages(root: str) -> Tuple[str, ...]:
    """Directories directly under *root* that are Python packages."""
    return tuple(
        sorted(
            name
            for name in os.listdir(root)
            if os.path.isdir(os.path.join(root, name))
            and not name.startswith(".")
            and os.path.isfile(os.path.join(root, name, "__init__.py"))
        )
    )


def _top_level_directories_holding_python(root: str) -> set:
    """Top-level directories that contain Python at any depth.

    A second root package does not need an ``__init__.py`` to be importable,
    so rule 4's import half looks wider than its directory half does.
    """
    found = set()
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if not os.path.isdir(path) or name.startswith("."):
            continue
        if python_files(root, name):
            found.add(name)
    return found


def _parse(root: str, relative_path: str) -> ast.Module:
    with open(os.path.join(root, relative_path), "r", encoding="utf-8") as handle:
        return ast.parse(handle.read(), filename=relative_path)


def _package_of(relative_path: str) -> List[str]:
    """The dotted package a module at *relative_path* sits in, as parts."""
    parts = relative_path.replace(os.sep, "/").split("/")
    if parts[-1] == "__init__.py":
        return parts[:-1]
    return parts[:-1]


def imports_of(root: str, relative_path: str) -> Tuple[Tuple[str, int], ...]:
    """Every module *relative_path* imports, absolute, with its line number.

    Relative imports are resolved against the file's own package, so
    ``from ..presentation.frame import Cell`` inside
    ``terminal_game/domain/x.py`` comes back as
    ``terminal_game.presentation.frame`` and can be judged by the same rule
    as an absolute one.  An import that climbs past the repository root is
    reported as it was written rather than silently dropped.
    """
    tree = _parse(root, relative_path)
    package = _package_of(relative_path)
    found: List[Tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                climbed = package[: len(package) - (node.level - 1)]
                if len(package) - (node.level - 1) < 0:
                    found.append((node.module or ".", node.lineno))
                    continue
                parts = list(climbed) + (
                    [node.module] if node.module else []
                )
                found.append((".".join(parts), node.lineno))
            elif node.module:
                found.append((node.module, node.lineno))
    return tuple(found)


def _is_within(module: str, package: str) -> bool:
    """Is *module* that package, or something inside it?"""
    return module == package or module.startswith(package + ".")


# ---------------------------------------------------------------------------
# Rule 1 — no production code below the Shell names the windowing toolkit
# ---------------------------------------------------------------------------


def no_toolkit_below_the_shell(
    root: str = REPOSITORY_ROOT, application: Optional[str] = None
) -> Report:
    """Rule 1.  **Production code only**, and only below the Shell.

    The Shell is the one place the toolkit may be named.  A *test* that
    checks the real adapter against the seam must import the toolkit and is
    right to — amendment 2 is explicit about it, and a rule written the other
    way would fail the one test keeping the adapter honest.  So the suite is
    not inspected here at all.
    """
    application = application or _sole_root_package(root)
    shell = "{0}/shell".format(application)
    inspected = tuple(
        path
        for path in python_files(root, application)
        if not path.replace(os.sep, "/").startswith(shell + "/")
    )
    violations: List[Violation] = []
    for path in inspected:
        for module, line in imports_of(root, path):
            if _is_within(module, TOOLKIT):
                violations.append(
                    Violation(
                        path,
                        line,
                        "imports {0}; only the Shell may name the windowing "
                        "toolkit".format(module),
                    )
                )
    return _report("no toolkit below the Shell", inspected, violations)


# ---------------------------------------------------------------------------
# Rule 2 — the Domain names nothing above it, no clock, no global randomness
# ---------------------------------------------------------------------------


def domain_names_nothing_above_it(
    root: str = REPOSITORY_ROOT, application: Optional[str] = None
) -> Report:
    """Rule 2.  What makes the Domain testable with no window at all.

    Three things at once, because they are one idea: the Domain is handed
    everything it needs.  It imports no layer above it, it reads no clock,
    and it never reaches for :mod:`random`'s own global generator.

    ``import random`` itself is **not** a violation: the generator and the
    ghost are handed a ``random.Random`` and name that type in their
    signatures.  What is forbidden is *calling* the module — ``random.choice``
    rather than ``random_source.choice``.
    """
    application = application or _sole_root_package(root)
    domain = "{0}/domain".format(application)
    above = tuple(
        "{0}.{1}".format(application, layer)
        for layer in ("presentation", "application", "shell")
    )
    inspected = python_files(root, domain.replace("/", os.sep))
    violations: List[Violation] = []
    for path in inspected:
        for module, line in imports_of(root, path):
            for layer in above:
                if _is_within(module, layer):
                    violations.append(
                        Violation(
                            path,
                            line,
                            "imports {0}; the Domain names nothing above "
                            "it".format(module),
                        )
                    )
            if module.split(".")[0] in CLOCK_MODULES:
                violations.append(
                    Violation(
                        path,
                        line,
                        "imports {0}; the Domain reads no clock".format(module),
                    )
                )
        violations.extend(_global_random_uses(root, path))
    return _report(
        "the Domain names nothing above it", inspected, violations
    )


#: The layers, lowest first.  A layer may name the ones below it and itself,
#: and nothing above.  `Shell -> Presentation -> Application -> Domain`, as the
#: implementation plan fixes it.
LAYERS = ("domain", "application", "presentation", "shell")


def no_layer_names_one_above_it(
    root: str = REPOSITORY_ROOT, application: Optional[str] = None
) -> Report:
    """Rule 6.  The dependency rule, for every layer and not only the Domain.

    Rule 2 guards the Domain, which is the layer it costs most to lose --
    everything about the maze, the ghost and the rules stays testable with no
    window only because nothing above it may be named there.  But the plan
    fixes the whole chain, and until this rule existed the middle of it was
    unguarded: **the Application layer could import Presentation or the Shell
    and no rule anywhere would notice.**  Measured on a temporary tree, a
    module under ``application`` importing both passed every rule in
    ``TREE_RULES``.

    That gap is the interesting kind.  The rule was written down, ruled on,
    and cited in a later ruling as the thing that had been guarded -- and the
    citation was true of the Domain and not of the rest.  A rule in prose that
    nothing re-runs is a guard waiting to have never been exercised.

    The toolkit is rule 1's business and the clock and the global random
    generator are rule 2's; this rule is only about a layer naming one above
    it.  Overlap with rule 2 on the Domain is deliberate: two rules reporting
    the same breach is cheap, and a Domain guarded twice is not a problem.
    """
    application = application or _sole_root_package(root)
    inspected: List[str] = []
    violations: List[Violation] = []
    for height, layer in enumerate(LAYERS):
        above = tuple(
            "{0}.{1}".format(application, higher) for higher in LAYERS[height + 1:]
        )
        if not above:
            continue
        within = "{0}/{1}".format(application, layer).replace("/", os.sep)
        files = python_files(root, within)
        inspected.extend(files)
        for path in files:
            for module, line in imports_of(root, path):
                for higher in above:
                    if _is_within(module, higher):
                        violations.append(
                            Violation(
                                path,
                                line,
                                "imports {0}; {1} names nothing above it".format(
                                    module, layer.capitalize()
                                ),
                            )
                        )
    return _report(
        "no layer names one above it", inspected, violations
    )


def _global_random_uses(root: str, path: str) -> List[Violation]:
    """Calls on :mod:`random` itself, rather than on a source handed in."""
    tree = _parse(root, path)
    found: List[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "random":
            for alias in node.names:
                if alias.name in GLOBAL_RANDOM_FUNCTIONS:
                    found.append(
                        Violation(
                            path,
                            node.lineno,
                            "imports random.{0}; the Domain is handed a "
                            "random source".format(alias.name),
                        )
                    )
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "random"
            and function.attr in GLOBAL_RANDOM_FUNCTIONS
        ):
            found.append(
                Violation(
                    path,
                    node.lineno,
                    "calls random.{0}(); the Domain is handed a random "
                    "source and reaches for no global one".format(
                        function.attr
                    ),
                )
            )
    return found


# ---------------------------------------------------------------------------
# Rule 3 — nothing draws an image
# ---------------------------------------------------------------------------


def nothing_draws_an_image(
    root: str = REPOSITORY_ROOT, application: Optional[str] = None
) -> Report:
    """Rule 3.  Caution C5 — everything on screen is a character in a cell.

    In candidate 1 the medium made SCRN-2 impossible to break.  On a
    graphical surface nothing stops a later developer drawing a picture, so
    it is a rule now rather than a fact.

    Inspected: the application **and** ``tools/``, because a script that
    paints the real screen is as capable of breaking SCRN-2 as the
    application is.  Not inspected: the suite, which has to name these
    methods in order to assert that nothing calls them — ``tests/doubles.py``
    implements every one of them precisely so a test can record that they
    were never used.
    """
    application = application or _sole_root_package(root)
    inspected = python_files(root, application)
    if os.path.isdir(os.path.join(root, SCRIPT_PACKAGE)):
        inspected = inspected + python_files(root, SCRIPT_PACKAGE)
    violations: List[Violation] = []
    for path in inspected:
        tree = _parse(root, path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == TOOLKIT:
                for alias in node.names:
                    if alias.name in IMAGE_CLASSES:
                        violations.append(
                            Violation(
                                path,
                                node.lineno,
                                "imports {0}; everything on screen is a "
                                "character (SCRN-2)".format(alias.name),
                            )
                        )
            if not isinstance(node, ast.Call):
                continue
            name = _called_name(node.func)
            if name in DRAWING_PRIMITIVES:
                violations.append(
                    Violation(
                        path,
                        node.lineno,
                        "calls {0}(); everything on screen is a character in "
                        "a cell (SCRN-2, caution C5)".format(name),
                    )
                )
            elif name in IMAGE_CLASSES:
                violations.append(
                    Violation(
                        path,
                        node.lineno,
                        "constructs {0}; there are no images (SCRN-2)".format(
                            name
                        ),
                    )
                )
    return _report("nothing draws an image", inspected, violations)


def _called_name(function: ast.expr) -> Optional[str]:
    if isinstance(function, ast.Attribute):
        return function.attr
    if isinstance(function, ast.Name):
        return function.id
    return None


# ---------------------------------------------------------------------------
# Rule 4 — there is exactly one root package
# ---------------------------------------------------------------------------


def exactly_one_root_package(root: str = REPOSITORY_ROOT) -> Report:
    """Rule 4.  The one that would have caught M0's real collision.

    Two spellings of the root package landed on ``main`` within hours of each
    other and the suite stayed green, because neither imported the other.
    Nothing was wrong with either file; the tree had two applications in it
    and no test could tell.

    Two things are checked, because the first alone can be dodged:

    1. **Exactly one top-level package is the application.** ``tests`` is the
       suite and ``tools`` is the deliberately-run scripts; both are named
       here explicitly, so the rule cannot be satisfied by inventing a third
       directory and calling it something else.
    2. **Every first-party import anywhere in the repository — the suite
       included — resolves to that one package.** This half looks at every
       top-level directory holding Python at all, not only the ones with an
       ``__init__.py``, so a second root spelled as a namespace package is
       caught as readily as one spelled properly. The directory listing and
       the imports are two different witnesses and a second root has to get
       past both.
    """
    packages = top_level_packages(root)
    roots = tuple(
        name for name in packages if name not in (TEST_PACKAGE, SCRIPT_PACKAGE)
    )
    inspected = python_files(root)
    violations: List[Violation] = []
    if len(roots) != 1:
        violations.append(
            Violation(
                ".",
                0,
                "expected exactly one root package, found {0} ({1}); "
                "{2!r} and {3!r} are excluded by name".format(
                    len(roots),
                    ", ".join(roots) or "none",
                    TEST_PACKAGE,
                    SCRIPT_PACKAGE,
                ),
            )
        )
        return _report("exactly one root package", inspected, violations)

    sole = roots[0]
    known = set(packages) | _top_level_directories_holding_python(root)
    for path in inspected:
        for module, line in imports_of(root, path):
            head = module.split(".")[0]
            if head in known and head not in (sole, TEST_PACKAGE, SCRIPT_PACKAGE):
                violations.append(
                    Violation(
                        path,
                        line,
                        "imports {0}, but the one root package is {1}".format(
                            module, sole
                        ),
                    )
                )
    return _report("exactly one root package", inspected, violations)


def _sole_root_package(root: str) -> str:
    """The application's package, or a clear failure if there is not one."""
    roots = [
        name
        for name in top_level_packages(root)
        if name not in (TEST_PACKAGE, SCRIPT_PACKAGE)
    ]
    if len(roots) != 1:
        raise AssertionError(
            "expected exactly one root package under {0}, found {1}".format(
                root, roots
            )
        )
    return roots[0]


# ---------------------------------------------------------------------------
# Rule 5 — the suite never constructs a Tk interpreter
# ---------------------------------------------------------------------------


def no_tk_interpreter_constructed(default_root: object) -> Report:
    """Rule 5.  Importing is harmless; **constructing** reaches the screen.

    This is the rule amendment 2 rewrote, and the reason is worth keeping in
    front of whoever reads it next.  Amendment 1 said the suite loads neither
    ``tkinter`` nor ``_tkinter``.  That was measured true on a branch at
    04:40 and became false 24 seconds later, when WI-3 landed the test that
    checks the real adapter against the seam — a test which **must** import
    the toolkit.  A guard written to the earlier wording would fail the one
    test keeping the adapter honest.

    The property that holds, and that this checks, is stronger: only
    ``tkinter.Tk()`` reaches the window server, and it is never called.  The
    argument is :data:`tkinter._default_root`, which Tk sets when an
    interpreter is created; passing it in rather than reading it here is what
    lets the check be tested without creating one.
    """
    inspected = ("tkinter._default_root",)
    if default_root is None:
        return Report("no Tk interpreter constructed", inspected, ())
    return Report(
        "no Tk interpreter constructed",
        inspected,
        (
            Violation(
                "tkinter._default_root",
                0,
                "a Tk interpreter exists ({0!r}); importing the toolkit is "
                "harmless but constructing one reaches the window "
                "server".format(default_root),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Rule 6 — nothing that is not a test depends on test code
# ---------------------------------------------------------------------------


def nothing_but_tests_depends_on_tests(
    root: str = REPOSITORY_ROOT, application: Optional[str] = None
) -> Report:
    """Rule 6.  Tests may reach anywhere; nothing may reach into them.

    Inspected: the application and ``tools/``.  A script is not a test, so a
    script that imports one has made the suite load-bearing for something
    that is not the suite.
    """
    application = application or _sole_root_package(root)
    inspected = python_files(root, application)
    if os.path.isdir(os.path.join(root, SCRIPT_PACKAGE)):
        inspected = inspected + python_files(root, SCRIPT_PACKAGE)
    violations: List[Violation] = []
    for path in inspected:
        for module, line in imports_of(root, path):
            if _is_within(module, TEST_PACKAGE):
                violations.append(
                    Violation(
                        path,
                        line,
                        "imports {0}; nothing that is not a test may depend "
                        "on test code".format(module),
                    )
                )
    return _report(
        "nothing but tests depends on test code", inspected, violations
    )


#: The five rules that are answered by walking the tree.  Rule 5 is not here
#: because it is a question about a live interpreter, not about files.
TREE_RULES = (
    no_toolkit_below_the_shell,
    domain_names_nothing_above_it,
    nothing_draws_an_image,
    exactly_one_root_package,
    nothing_but_tests_depends_on_tests,
    no_layer_names_one_above_it,
)
