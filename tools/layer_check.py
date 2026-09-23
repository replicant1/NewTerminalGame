"""The layer rule of IMPLEMENTATION_PLAN.md section 1.4, as a check that runs.

    shell  ->  presentation  ->  application  ->  domain

A layer may import from itself and from the layers below it, never from one
above.  On top of the ordering:

* only the **shell** may import ``tkinter`` or any operating-system or
  windowing API (:data:`OS_OR_WINDOWING`);
* the **application** and the **domain** read no clock (:data:`CLOCK`);
* the **domain** uses the standard library only, and no randomness it was not
  handed: no module-level ``random`` functions, no ``secrets`` or ``uuid``, and
  no ``random.Random()`` made without a seed.  ``random.Random`` itself may be
  named, for a type annotation or for a source seeded from what was passed in.

**How the tree declares its layers** is the ``[tool.terminal_game.layers]``
table in ``pyproject.toml``: one package per layer, and every module under that
package, at any depth, is in that layer.  Every module under ``terminal_game/``
must be in a declared layer, except the package's own ``__init__.py`` and
``__main__.py``, which are the program's entry and are held to the shell's
rules (they are counted as ``entry``, not as shell).

**It cannot pass vacuously** (WI-1/C4).  It counts the modules it examined in
each layer, and a declared layer in which it examined none is a failure, as is
a module it could not parse.

It reads source with :mod:`ast` and imports nothing it examines, so it can judge
a module that would open a window if it were imported.  It sees ``import``,
``from ... import`` and ``importlib.import_module``/``__import__`` called with a
literal name; a dynamic import whose name it cannot read is itself reported
outside the shell, because it cannot be checked.

Run it on its own with ``.venv/bin/python -m tools.layer_check``.
"""

from __future__ import annotations

import ast
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

#: The layers of section 1.4, top first.  A layer may import from its own
#: position and every position after it.
LAYER_ORDER = ("shell", "presentation", "application", "domain")

#: Modules directly in the root package that are allowed there.  They are the
#: program's entry, so they are judged by the shell's rules.
ENTRY_MODULES = ("__init__", "__main__")
ENTRY = "entry"

#: Tk, and anything that talks to the operating system, a window system, a
#: process or a thread.  Only the shell may import these.
OS_OR_WINDOWING = frozenset({
    # the toolkit
    "tkinter", "_tkinter", "turtle", "turtledemo", "idlelib",
    # macOS window and application APIs (PyObjC)
    "objc", "AppKit", "Foundation", "Quartz", "Cocoa", "CoreFoundation",
    "ApplicationServices", "PyObjCTools",
    # the operating system, the terminal, processes and threads
    "os", "posix", "ctypes", "_ctypes", "subprocess", "_posixsubprocess",
    "signal", "pty", "tty", "termios", "fcntl", "curses", "_curses",
    "socket", "select", "selectors", "multiprocessing", "threading", "_thread",
    "asyncio", "concurrent", "platform", "webbrowser",
})

#: Reading the time.  Ticks reach the application as calls; nothing below the
#: presentation reads a clock.
CLOCK = frozenset({"time", "datetime", "sched", "timeit"})
NO_CLOCK_LAYERS = ("application", "domain")

#: Randomness the domain did not receive.
SELF_MADE_RANDOMNESS = frozenset({"secrets", "uuid"})
RANDOM_MODULE = "random"
RANDOM_TYPE = "Random"
STDLIB_ONLY_LAYERS = ("domain",)
HANDED_RANDOMNESS_LAYERS = ("domain",)


@dataclass(frozen=True)
class Violation:
    """One thing a module does that the layer rule forbids."""

    module: str  # the dotted name of the offending module
    lineno: int
    imported: str  # what it imported or used
    rule: str  # a short stable handle
    reason: str  # a sentence for whoever reads the failure

    def describe(self) -> str:
        return "%s:%d imports %s  [%s] %s" % (
            self.module, self.lineno, self.imported, self.rule, self.reason)


@dataclass
class Report:
    """What one run of the check found."""

    examined: Dict[str, int]  # layer -> modules examined, in LAYER_ORDER, plus ENTRY
    violations: List[Violation] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)  # why the check itself cannot pass

    @property
    def ok(self) -> bool:
        return not self.violations and not self.problems

    def summary(self) -> str:
        counts = ", ".join("%s %d" % (name, n) for name, n in self.examined.items())
        lines = ["layer check examined: " + counts]
        lines.extend("PROBLEM   " + p for p in self.problems)
        lines.extend("VIOLATION " + v.describe() for v in self.violations)
        lines.append("layer check: %s (%d violation(s), %d problem(s))" % (
            "PASS" if self.ok else "FAIL", len(self.violations), len(self.problems)))
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Reading the declaration
# --------------------------------------------------------------------------


def read_declaration(pyproject: Path) -> Dict[str, str]:
    """``{layer: package}`` from ``[tool.terminal_game.layers]``."""
    import tomllib  # 3.11+; the pinned interpreter is 3.14

    with open(pyproject, "rb") as handle:
        data = tomllib.load(handle)
    try:
        table = data["tool"]["terminal_game"]["layers"]
    except KeyError:
        raise ValueError("%s has no [tool.terminal_game.layers] table" % pyproject)
    unknown = sorted(set(table) - set(LAYER_ORDER))
    missing = [name for name in LAYER_ORDER if name not in table]
    if unknown or missing:
        raise ValueError(
            "%s must declare exactly the layers %s; unknown %s, missing %s"
            % (pyproject, ", ".join(LAYER_ORDER), unknown, missing))
    packages = {name: str(table[name]) for name in LAYER_ORDER}
    roots = {package.split(".")[0] for package in packages.values()}
    if len(roots) != 1:
        raise ValueError("every layer must sit in one root package; found %s"
                         % sorted(roots))
    return packages


# --------------------------------------------------------------------------
# Finding modules
# --------------------------------------------------------------------------


def _modules(root: Path, package: str) -> Iterator[Tuple[str, Path]]:
    """Every ``.py`` under ``root/<package>``, as (dotted name, path)."""
    base = root.joinpath(*package.split("."))
    if not base.is_dir():
        return
    for path in sorted(base.rglob("*.py")):
        relative = path.relative_to(root).with_suffix("")
        yield ".".join(relative.parts), path


def _layer_of(module: str, packages: Dict[str, str], root_package: str) -> Optional[str]:
    """Which layer a dotted module name belongs to, or None if it is outside."""
    for name in LAYER_ORDER:
        package = packages[name]
        if module == package or module.startswith(package + "."):
            return name
    if module == root_package or (
            module.startswith(root_package + ".")
            and module[len(root_package) + 1:] in ENTRY_MODULES):
        return ENTRY
    return None


def _rules_layer(layer: str) -> str:
    """The layer whose rules apply: the entry is held to the shell's."""
    return LAYER_ORDER[0] if layer == ENTRY else layer


# --------------------------------------------------------------------------
# Reading one module
# --------------------------------------------------------------------------


def _resolve_relative(module: str, is_package: bool, level: int, name: Optional[str]) -> str:
    parts = module.split(".")
    package_parts = parts if is_package else parts[:-1]
    if level - 1 > len(package_parts):
        return "." * level + (name or "")
    base = package_parts[: len(package_parts) - (level - 1)]
    if name:
        base = base + name.split(".")
    return ".".join(base)


@dataclass(frozen=True)
class _Use:
    target: str  # a dotted module name, or a best guess at one
    lineno: int
    alternatives: Tuple[str, ...] = ()  # other readings of the same name
    unreadable: bool = False  # a dynamic import whose name is not a literal


def _uses(tree: ast.AST, module: str, is_package: bool) -> Iterator[_Use]:
    import_module_names = {"__import__"}
    importlib_aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    importlib_aliases.add(alias.asname or "importlib")
                yield _Use(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = _resolve_relative(module, is_package, node.level, node.module)
            else:
                base = node.module or ""
            if base == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_names.add(alias.asname or "import_module")
            for alias in node.names:
                if alias.name == "*":
                    yield _Use(base, node.lineno)
                else:
                    yield _Use(base, node.lineno, alternatives=(base + "." + alias.name,))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        dynamic = (
            (isinstance(func, ast.Name) and func.id in import_module_names)
            or (isinstance(func, ast.Attribute) and func.attr == "import_module"
                and isinstance(func.value, ast.Name) and func.value.id in importlib_aliases)
        )
        if not dynamic:
            continue
        first = node.args[0] if node.args else None
        if isinstance(first, ast.Constant) and isinstance(first.value, str) \
                and not first.value.startswith("."):
            yield _Use(first.value, node.lineno)
        else:
            yield _Use("<dynamic import>", node.lineno, unreadable=True)


def _randomness(tree: ast.AST) -> Iterator[Tuple[int, str]]:
    """Every place a module draws randomness it was not handed."""
    module_aliases = set()
    type_aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == RANDOM_MODULE:
                    module_aliases.add(alias.asname or RANDOM_MODULE)
        elif isinstance(node, ast.ImportFrom) and node.module == RANDOM_MODULE and not node.level:
            for alias in node.names:
                if alias.name == RANDOM_TYPE:
                    type_aliases.add(alias.asname or RANDOM_TYPE)
                else:
                    yield node.lineno, "random.%s" % alias.name
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                and node.value.id in module_aliases and node.attr != RANDOM_TYPE:
            yield node.lineno, "random.%s" % node.attr
        if isinstance(node, ast.Call) and not node.args and not node.keywords:
            func = node.func
            unseeded = (
                (isinstance(func, ast.Name) and func.id in type_aliases)
                or (isinstance(func, ast.Attribute) and func.attr == RANDOM_TYPE
                    and isinstance(func.value, ast.Name) and func.value.id in module_aliases)
            )
            if unseeded:
                yield node.lineno, "random.Random() with no seed"


def _check_module(module: str, path: Path, layer: str, packages: Dict[str, str],
                  root_package: str, report: Report) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        report.problems.append("could not read %s (%s), so it was not checked" % (path, exc))
        return
    rules = _rules_layer(layer)
    position = LAYER_ORDER.index(rules)
    is_package = path.name == "__init__.py"
    add = report.violations.append

    for use in _uses(tree, module, is_package):
        if use.unreadable:
            if rules != LAYER_ORDER[0]:
                add(Violation(module, use.lineno, use.target, "dynamic-import",
                              "an import whose name is not a literal cannot be checked; "
                              "only the shell may do that"))
            continue
        # Inside the project: the ordering rule.
        target_layer = None
        for candidate in use.alternatives + (use.target,):
            target_layer = _layer_of(candidate, packages, root_package)
            if target_layer is not None:
                shown = candidate
                break
        if target_layer is not None:
            if LAYER_ORDER.index(_rules_layer(target_layer)) < position:
                add(Violation(module, use.lineno, shown, "upward",
                              "%s may not import from %s, which is above it"
                              % (rules, target_layer)))
            continue
        top = use.target.split(".")[0]
        if not top or top.startswith("."):
            add(Violation(module, use.lineno, use.target, "unresolvable",
                          "a relative import that climbs out of the package"))
            continue
        if top == root_package:
            add(Violation(module, use.lineno, use.target, "undeclared",
                          "%s is in no declared layer" % use.target))
            continue
        # Outside the project.
        if top in OS_OR_WINDOWING and rules != LAYER_ORDER[0]:
            add(Violation(module, use.lineno, use.target, "toolkit-or-os",
                          "only the shell may import tkinter or any operating-system "
                          "or windowing API"))
        elif top in CLOCK and rules in NO_CLOCK_LAYERS:
            add(Violation(module, use.lineno, use.target, "clock",
                          "the %s reads no clock; ticks arrive as calls" % rules))
        elif top in SELF_MADE_RANDOMNESS and rules in HANDED_RANDOMNESS_LAYERS:
            add(Violation(module, use.lineno, use.target, "randomness",
                          "the domain uses no randomness it was not handed"))
        elif rules in STDLIB_ONLY_LAYERS and top not in sys.stdlib_module_names:
            add(Violation(module, use.lineno, use.target, "stdlib-only",
                          "the domain uses the standard library only"))

    if rules in HANDED_RANDOMNESS_LAYERS:
        for lineno, what in _randomness(tree):
            add(Violation(module, lineno, what, "randomness",
                          "the domain uses no randomness it was not handed; "
                          "take a random source as an argument"))


# --------------------------------------------------------------------------
# The check
# --------------------------------------------------------------------------


def check(root: Path, packages: Dict[str, str]) -> Report:
    """Check every module under the root package against the layer rule."""
    root = Path(root)
    root_package = next(iter(packages.values())).split(".")[0]
    report = Report(examined={name: 0 for name in LAYER_ORDER + (ENTRY,)})
    for module, path in _modules(root, root_package):
        layer = _layer_of(module, packages, root_package)
        if layer is None:
            report.violations.append(Violation(
                module, 1, "(nothing)", "undeclared",
                "%s is in no declared layer; move it into one of %s"
                % (module, ", ".join(packages[name] for name in LAYER_ORDER))))
            continue
        report.examined[layer] += 1
        _check_module(module, path, layer, packages, root_package, report)
    for name in LAYER_ORDER:
        if report.examined[name] == 0:
            report.problems.append(
                "examined no module in the %s layer (%s), which the tree declares; "
                "a check that examined nothing proves nothing" % (name, packages[name]))
    return report


def check_repository(root: Path) -> Report:
    root = Path(root)
    return check(root, read_declaration(root / "pyproject.toml"))


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]) if argv else Path(__file__).resolve().parents[1]
    report = check_repository(root)
    print(report.summary())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
