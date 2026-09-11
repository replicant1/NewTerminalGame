"""The pure core stays pure — implementation plan §2.4.

Two guards, because one alone is not enough:

* a **dynamic** one, which removes ``curses`` and ``subprocess`` from
  ``sys.modules``, poisons them so any import raises, and then imports every
  pure module from scratch. It catches a transitive import.
* a **static** one, which parses every pure module and refuses a direct import
  of anything that reads a file, a clock, a terminal, an environment variable
  or a window. It catches ``os`` and ``time``, which are already imported by
  the test runner and so cannot be poisoned.

Both discover the pure modules by listing ``termgame/`` and subtracting the
three modules the architecture declares impure, so a module added by a later
work item is covered the moment it lands.
"""

import ast
import importlib
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(ROOT, "termgame")
sys.path.insert(0, ROOT)

#: The three modules of the impure shell (architecture §3). Everything else
#: in the package is core and must stay pure.
IMPURE_MODULES = frozenset({"screen", "loop", "window"})

#: Nothing in the core may import these, directly or transitively.
BANNED_IN_CORE = frozenset(
    {
        "curses",
        "time",
        "subprocess",
        "os",
        "sys",
        "pathlib",
        "shutil",
        "socket",
        "tempfile",
        "termios",
        "tty",
        "select",
        "signal",
        "threading",
    }
)

#: The two that can actually be poisoned: everything else on the list above
#: is already in ``sys.modules`` before the test runner starts.
POISONED = ("curses", "subprocess")


def pure_module_names():
    """Every core module in the package, by bare name."""
    names = []
    for entry in sorted(os.listdir(PACKAGE_DIR)):
        if not entry.endswith(".py"):
            continue
        stem = entry[:-3]
        if stem == "__init__" or stem in IMPURE_MODULES:
            continue
        names.append(stem)
    return names


def all_module_names():
    return sorted(
        entry[:-3]
        for entry in os.listdir(PACKAGE_DIR)
        if entry.endswith(".py") and entry != "__init__.py"
    )


def parse(name):
    path = os.path.join(PACKAGE_DIR, name + ".py")
    with io.open(path, encoding="utf-8") as handle:
        return ast.parse(handle.read(), filename=path)


def direct_imports(tree):
    """The top-level package names this module imports directly."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # a relative import stays inside the package
                continue
            if node.module:
                found.add(node.module.split(".")[0])
    return found


class _Poison(object):
    """A meta-path finder that refuses the named modules outright."""

    def __init__(self, names):
        self.names = frozenset(names)

    def find_module(self, fullname, path=None):  # Python 2/3 legacy hook
        return self if fullname.split(".")[0] in self.names else None

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in self.names:
            raise ImportError("%s is poisoned for this test" % fullname)
        return None

    def load_module(self, fullname):
        raise ImportError("%s is poisoned for this test" % fullname)


class TestTheCoreImportsCleanlyWithoutTheShell(unittest.TestCase):
    def setUp(self):
        self.saved_modules = dict(sys.modules)
        self.saved_meta_path = list(sys.meta_path)

    def tearDown(self):
        sys.meta_path[:] = self.saved_meta_path
        for name in list(sys.modules):
            if name not in self.saved_modules:
                del sys.modules[name]
        sys.modules.update(self.saved_modules)

    def _import_core_with_poison(self):
        for name in POISONED:
            sys.modules.pop(name, None)
        for name in list(sys.modules):
            if name == "termgame" or name.startswith("termgame."):
                del sys.modules[name]
        sys.meta_path.insert(0, _Poison(POISONED))
        imported = []
        for name in pure_module_names():
            imported.append(importlib.import_module("termgame." + name))
        return imported

    def test_the_poison_really_bites(self):
        # If it did not, the test below would prove nothing at all.
        sys.modules.pop("curses", None)
        sys.meta_path.insert(0, _Poison(POISONED))
        with self.assertRaises(ImportError):
            importlib.import_module("curses")
        with self.assertRaises(ImportError):
            importlib.import_module("subprocess")

    def test_every_core_module_imports_with_curses_and_subprocess_gone(self):
        modules = self._import_core_with_poison()
        self.assertTrue(modules, "no core modules were found to import")
        for module in modules:
            self.assertTrue(hasattr(module, "__name__"))

    def test_the_core_still_generates_a_maze_with_curses_and_subprocess_gone(self):
        # Importing is not enough: the work has to be doable without them.
        self._import_core_with_poison()
        import random

        mazelib = importlib.import_module("termgame.maze")
        maze = mazelib.generate(random.Random(0))
        self.assertEqual((maze.height, maze.width), (29, 19))
        self.assertEqual(mazelib.check(maze), ())

    def test_the_pure_modules_are_the_ones_the_architecture_says(self):
        self.assertIn("model", pure_module_names())
        self.assertIn("maze", pure_module_names())
        for impure in IMPURE_MODULES:
            self.assertNotIn(impure, pure_module_names())


class TestNoCoreModuleImportsAnythingImpure(unittest.TestCase):
    def test_no_direct_import_of_a_banned_module(self):
        for name in pure_module_names():
            offenders = direct_imports(parse(name)) & BANNED_IN_CORE
            self.assertEqual(
                offenders,
                set(),
                "termgame/%s.py imports %s" % (name, sorted(offenders)),
            )

    def test_the_package_init_is_pure_too(self):
        offenders = direct_imports(parse("__init__")) & BANNED_IN_CORE
        self.assertEqual(offenders, set())

    def test_the_core_never_imports_the_shell(self):
        # Arrows point inward only.
        for name in pure_module_names():
            tree = parse(name)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    parts = node.module.split(".")
                    if parts[0] == "termgame" and len(parts) > 1:
                        self.assertNotIn(parts[1], IMPURE_MODULES, name)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        parts = alias.name.split(".")
                        if parts[0] == "termgame" and len(parts) > 1:
                            self.assertNotIn(parts[1], IMPURE_MODULES, name)

    def test_at_most_one_module_in_the_package_imports_curses(self):
        importers = [
            name for name in all_module_names() if "curses" in direct_imports(parse(name))
        ]
        self.assertLessEqual(len(importers), 1, "curses imported by %s" % importers)

    def test_at_most_one_module_in_the_package_imports_subprocess(self):
        importers = [
            name
            for name in all_module_names()
            if "subprocess" in direct_imports(parse(name))
        ]
        self.assertLessEqual(len(importers), 1, "subprocess imported by %s" % importers)

    def test_no_module_in_the_package_both_imports_curses_and_shells_out(self):
        for name in all_module_names():
            imports = direct_imports(parse(name))
            self.assertFalse(
                "curses" in imports and "subprocess" in imports,
                "termgame/%s.py does both" % name,
            )


class TestRandomnessIsAlwaysAParameter(unittest.TestCase):
    """Architecture C7 — the only reason seeded tests are reproducible."""

    def test_no_core_module_calls_the_random_module_itself(self):
        for name in pure_module_names():
            tree = parse(name)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "random"
                ):
                    self.fail(
                        "termgame/%s.py line %d calls random.%s(); randomness "
                        "must arrive as a random.Random parameter"
                        % (name, node.lineno, func.attr)
                    )

    def test_no_core_module_imports_names_out_of_random(self):
        # `from random import shuffle` would sidestep the check above.
        for name in pure_module_names():
            for node in ast.walk(parse(name)):
                if isinstance(node, ast.ImportFrom) and node.module == "random":
                    self.fail(
                        "termgame/%s.py does `from random import %s`"
                        % (name, ", ".join(a.name for a in node.names))
                    )


if __name__ == "__main__":
    unittest.main()
