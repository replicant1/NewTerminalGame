"""The dependency rule between layers, as something that runs.

IMPLEMENTATION_PLAN.md section 1.3 states the rule in prose and then says why
it is a test and not a sentence: *"a sentence remembers what was true once and
nothing re-runs it."*  This module is the part that re-runs it.  It reads the
source of every module under a package with ``ast``, works out what each one
imports, and reports every import that the rule forbids.

The rule, with the arrow reading "may import":

    shell -> presentation -> application -> domain

and on top of the ordering:

* **Domain** may name nothing impure — no windowing toolkit, no clock, no
  filesystem, no environment, no process, and no module-level random source.
  Randomness arrives as an argument.
* **Application** may name no toolkit and no clock.  A tick arrives as a call.
* **Presentation** may name the toolkit from exactly one module, the one that
  actually paints: :data:`PAINTING_MODULE`.
* **Shell** may name anything.  It owns the window and the event loop.

Nothing here imports the game, and nothing in the game imports this.  It works
on source text, so it can judge a module that would open a window if it were
imported — which is the whole reason it reads rather than imports.
"""

from __future__ import annotations

import ast
import os
from typing import Dict, FrozenSet, Iterable, List, NamedTuple, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# The layers, lowest first.  A layer may import itself and anything below it.
# --------------------------------------------------------------------------

LAYERS = ("domain", "application", "presentation", "shell")  # type: Tuple[str, ...]

#: The one module inside Presentation allowed to name the windowing toolkit —
#: the character grid surface, which is WI-5's responsibility.  WI-5 may rename
#: it, and this is the single place that has to change when it does.  The test
#: suite pins that there is exactly one such module, so that the exception
#: cannot be widened quietly.
PAINTING_MODULE = "terminal_game.presentation.surface"

# --------------------------------------------------------------------------
# What "impure" means, spelled out.  Each set answers one clause of the rule,
# so that a violation can say which clause it broke rather than just "no".
# --------------------------------------------------------------------------

#: The windowing toolkit.  Only Shell and :data:`PAINTING_MODULE` may name it.
TOOLKIT_MODULES = frozenset(
    {"tkinter", "_tkinter", "Tkinter", "turtle", "idlelib"}
)  # type: FrozenSet[str]

#: Reading the time.  A tick arrives as a call; it is never read from a clock.
CLOCK_MODULES = frozenset(
    {"time", "datetime", "sched", "timeit", "zoneinfo"}
)  # type: FrozenSet[str]

#: A module-level source of randomness.  Randomness arrives as an argument.
RANDOM_MODULES = frozenset({"random", "secrets", "uuid"})  # type: FrozenSet[str]

#: Touching the filesystem.
FILESYSTEM_MODULES = frozenset(
    {
        "fileinput",
        "glob",
        "io",
        "os",
        "pathlib",
        "shelve",
        "shutil",
        "sqlite3",
        "tempfile",
    }
)  # type: FrozenSet[str]

#: Reading the environment the process was started in.
ENVIRONMENT_MODULES = frozenset(
    {"argparse", "getpass", "os", "platform", "site", "sys", "sysconfig"}
)  # type: FrozenSet[str]

#: Starting, signalling or talking to another process or thread.
PROCESS_MODULES = frozenset(
    {
        "asyncio",
        "atexit",
        "concurrent",
        "ctypes",
        "ftplib",
        "http",
        "multiprocessing",
        "queue",
        "select",
        "selectors",
        "signal",
        "smtplib",
        "socket",
        "socketserver",
        "subprocess",
        "threading",
        "urllib",
        "webbrowser",
    }
)  # type: FrozenSet[str]

#: Category name -> the modules in it, in the order a violation prefers to
#: report them.  ``os`` is both filesystem and environment; the first match
#: wins and either answer is true, so the order only affects the wording.
IMPURITY = (
    ("a windowing toolkit", TOOLKIT_MODULES),
    ("a clock", CLOCK_MODULES),
    ("a module-level random source", RANDOM_MODULES),
    ("the filesystem", FILESYSTEM_MODULES),
    ("the environment", ENVIRONMENT_MODULES),
    ("a process or thread", PROCESS_MODULES),
)  # type: Tuple[Tuple[str, FrozenSet[str]], ...]


class ImportSite(NamedTuple):
    """One name imported by one module, and where it was written."""

    module: str  # the dotted name of the module doing the importing
    imported: str  # the dotted name it imports
    lineno: int
    kind: str  # "import", "from", or "dynamic"

    def describe(self) -> str:
        return "{}:{} imports {} ({})".format(
            self.module, self.lineno, self.imported, self.kind
        )


class Violation(NamedTuple):
    """One import that the rule forbids, and why."""

    site: ImportSite
    rule: str  # a short, stable handle, e.g. "layer-order"
    reason: str  # a sentence for a human reading a failure

    def describe(self) -> str:
        return "{}\n    [{}] {}".format(self.site.describe(), self.rule, self.reason)


class SourceModule(NamedTuple):
    """A ``.py`` file found under the scanned package."""

    name: str  # dotted, e.g. "terminal_game.domain.maze"
    path: str
    is_package: bool  # True for an __init__.py


# --------------------------------------------------------------------------
# Reading imports out of source
# --------------------------------------------------------------------------


def _resolve_relative(module: str, is_package: bool, level: int, tail: str) -> str:
    """Turn a relative import into the absolute name it refers to.

    ``level`` is the number of leading dots.  Inside a package's own
    ``__init__.py`` one dot means the package itself; inside a plain module one
    dot means the package that contains it.
    """
    parts = module.split(".")
    if not is_package:
        parts = parts[:-1]
    if level > 1:
        parts = parts[: len(parts) - (level - 1)]
    if tail:
        parts = parts + tail.split(".")
    return ".".join(part for part in parts if part)


def _literal_string(node: ast.AST) -> Optional[str]:
    """The value of a string literal node, or ``None`` if it is not one."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _dynamic_target(node: ast.Call) -> Optional[str]:
    """The module named by ``importlib.import_module("x")`` or ``__import__("x")``.

    A dynamic import with a computed name cannot be read statically, and this
    returns ``None`` for those.  That is a known limit of the scanner and it is
    written down in the README rather than hidden here: the rule catches the
    ordinary ways of naming a module, and the obvious way of dodging it.
    """
    func = node.func
    name = None  # type: Optional[str]
    if isinstance(func, ast.Name):
        name = func.id
    elif isinstance(func, ast.Attribute):
        name = func.attr
    if name not in ("import_module", "__import__"):
        return None
    if not node.args:
        return None
    return _literal_string(node.args[0])


def imports_in_source(source: str, module: str, is_package: bool = False) -> List[ImportSite]:
    """Every module name ``source`` imports, wherever in the file it is written.

    ``from a.b import c`` yields both ``a.b`` and ``a.b.c``, because ``c`` may
    be a submodule and the rule has to judge it either way.  Imports nested
    inside a function or a ``try`` are found just the same as top-level ones —
    moving an import into a function is the first thing somebody does when a
    rule like this gets in the way.
    """
    tree = ast.parse(source)
    sites = []  # type: List[ImportSite]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                sites.append(ImportSite(module, alias.name, node.lineno, "import"))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = _resolve_relative(module, is_package, node.level, node.module or "")
            else:
                base = node.module or ""
            if base:
                sites.append(ImportSite(module, base, node.lineno, "from"))
            for alias in node.names:
                if alias.name == "*":
                    continue
                full = "{}.{}".format(base, alias.name) if base else alias.name
                sites.append(ImportSite(module, full, node.lineno, "from"))
        elif isinstance(node, ast.Call):
            target = _dynamic_target(node)
            if target:
                sites.append(ImportSite(module, target, node.lineno, "dynamic"))
    return sites


def find_modules(package_dir: str) -> List[SourceModule]:
    """Every ``.py`` file under ``package_dir``, as dotted module names.

    The dotted names are rooted at the directory's own basename, so scanning
    ``<repo>/terminal_game`` names its modules ``terminal_game.domain.maze``
    and so on.  The list is sorted, so a failure report reads the same way
    twice.
    """
    package_dir = os.path.abspath(package_dir)
    root_name = os.path.basename(package_dir)
    modules = []  # type: List[SourceModule]
    for dirpath, dirnames, filenames in os.walk(package_dir):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        rel_dir = os.path.relpath(dirpath, package_dir)
        prefix = (
            root_name
            if rel_dir == "."
            else "{}.{}".format(root_name, rel_dir.replace(os.sep, "."))
        )
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            if filename == "__init__.py":
                modules.append(SourceModule(prefix, os.path.join(dirpath, filename), True))
            else:
                name = "{}.{}".format(prefix, filename[:-3])
                modules.append(SourceModule(name, os.path.join(dirpath, filename), False))
    modules.sort()
    return modules


def scan(package_dir: str) -> Dict[SourceModule, List[ImportSite]]:
    """Read every module under ``package_dir`` and return what each imports."""
    found = {}  # type: Dict[SourceModule, List[ImportSite]]
    for module in find_modules(package_dir):
        with open(module.path, "r", encoding="utf-8") as handle:
            source = handle.read()
        found[module] = imports_in_source(source, module.name, module.is_package)
    return found


# --------------------------------------------------------------------------
# Judging what was read
# --------------------------------------------------------------------------


def layer_of(module: str, root: str) -> Optional[str]:
    """Which layer ``module`` belongs to, or ``None`` if it belongs to none."""
    parts = module.split(".")
    if len(parts) < 2 or parts[0] != root:
        return None
    return parts[1] if parts[1] in LAYERS else None


def _top_level(module: str) -> str:
    return module.split(".")[0]


def _impurity_of(imported: str) -> Optional[str]:
    top = _top_level(imported)
    for label, members in IMPURITY:
        if top in members:
            return label
    return None


def check_imports(
    imports: Iterable[ImportSite],
    modules: Iterable[SourceModule],
    root: str = "terminal_game",
    painting_module: str = PAINTING_MODULE,
) -> List[Violation]:
    """Every violation of the layer rule in the given imports.

    Separated from :func:`scan` so that the judging can be exercised on a
    fixture tree that has never existed on this machine's real source path.
    """
    violations = []  # type: List[Violation]

    for module in modules:
        if module.name == root:
            continue  # the package's own __init__ is not in a layer, by design
        if layer_of(module.name, root) is None:
            violations.append(
                Violation(
                    ImportSite(module.name, "-", 0, "placement"),
                    "unplaced-module",
                    "{} is not in one of the four layers {}; a module with no "
                    "layer is a module the rule cannot judge".format(
                        module.name, ", ".join(LAYERS)
                    ),
                )
            )

    for site in imports:
        own_layer = layer_of(site.module, root)
        if own_layer is None:
            continue  # already reported as unplaced; judging it twice adds noise
        own_rank = LAYERS.index(own_layer)

        target_layer = layer_of(site.imported, root)
        if target_layer is not None:
            if LAYERS.index(target_layer) > own_rank:
                violations.append(
                    Violation(
                        site,
                        "layer-order",
                        "{} may not import {}; the arrow runs {}".format(
                            own_layer,
                            target_layer,
                            " -> ".join(reversed(LAYERS)),
                        ),
                    )
                )
            continue  # a sibling layer import is never also an impurity

        if _top_level(site.imported) == root:
            continue  # the package itself, or a module still being placed

        impurity = _impurity_of(site.imported)
        if impurity is None:
            continue

        is_toolkit = _top_level(site.imported) in TOOLKIT_MODULES

        if own_layer == "domain":
            violations.append(
                Violation(
                    site,
                    "domain-purity",
                    "domain may not name {} ({}); the domain is pure so that "
                    "the rules can be tested with no window and no clock".format(
                        impurity, site.imported
                    ),
                )
            )
        elif own_layer == "application":
            if is_toolkit:
                violations.append(
                    Violation(
                        site,
                        "application-toolkit",
                        "application may not name a windowing toolkit ({})".format(
                            site.imported
                        ),
                    )
                )
            elif _top_level(site.imported) in CLOCK_MODULES:
                violations.append(
                    Violation(
                        site,
                        "application-clock",
                        "application may not read a clock ({}); a tick arrives "
                        "as a call".format(site.imported),
                    )
                )
        elif own_layer == "presentation":
            if is_toolkit and site.module != painting_module:
                violations.append(
                    Violation(
                        site,
                        "presentation-toolkit",
                        "only {} may name the windowing toolkit inside "
                        "presentation; everything else this layer produces is "
                        "data ({})".format(painting_module, site.imported),
                    )
                )

    return _collapse(violations)


def _collapse(violations: Sequence[Violation]) -> List[Violation]:
    """One written import line reports as one violation.

    ``from terminal_game.shell import window`` is read as two names, the
    package and the name inside it, because either could be the module.  Both
    break the same rule on the same line, and reporting it twice makes a
    failure look twice as bad as it is.  Where one violation's imported name
    is a strict dotted extension of another's, on the same line and under the
    same rule, only the shorter survives.

    ``import tkinter, time`` stays two violations: neither name extends the
    other, and they really are two separate things named.
    """
    kept = []  # type: List[Violation]
    for violation in violations:
        redundant = False
        for other in violations:
            if other is violation:
                continue
            if (other.site.module, other.site.lineno, other.rule) != (
                violation.site.module,
                violation.site.lineno,
                violation.rule,
            ):
                continue
            if violation.site.imported.startswith(other.site.imported + "."):
                redundant = True
                break
        if not redundant:
            kept.append(violation)
    return kept


def check_package(
    package_dir: str, painting_module: str = PAINTING_MODULE
) -> List[Violation]:
    """Scan ``package_dir`` and return every violation of the layer rule."""
    found = scan(package_dir)
    root = os.path.basename(os.path.abspath(package_dir))
    every_import = []  # type: List[ImportSite]
    for sites in found.values():
        every_import.extend(sites)
    every_import.sort()
    return check_imports(every_import, found.keys(), root, painting_module)


def describe(violations: Sequence[Violation]) -> str:
    """A failure message a human can act on without opening this file."""
    if not violations:
        return "no violations"
    lines = ["{} violation(s) of the layer rule:".format(len(violations))]
    for violation in violations:
        lines.append("  " + violation.describe())
    return "\n".join(lines)
