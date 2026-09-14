"""The layer rule, stated as a test rather than as a paragraph.

Implementation plan §3: "The Screen port is an interface; the terminal
adapter is the only thing behind it that knows `curses` exists. Nothing above
the port imports `curses`."

That rule is easy to keep while the tree is four files and easy to lose once
it is forty. This is the cheapest possible guard on it: if a second module
ever imports curses, the next person to run the suite finds out.

It is a standing obligation rather than a one-off, so each work item that
adds a layer adds its cases here. **WI-4 added the domain-purity cases**
(`DomainPurityTest`): the Domain imports nothing impure and depends on
nothing above it, which is the other half of plan §3 and of architecture
caution C5.

Still uncovered, and owned by WI-12 rather than by this file's current
authors: nothing here walks `launcher/`, so the launcher half of the layer
rule — that the launcher shares no code with the game — is not guarded yet.
"""

from __future__ import annotations

import os
import re
import unittest

import terminalgame

PACKAGE_ROOT = os.path.dirname(os.path.abspath(terminalgame.__file__))

#: The one module in the whole game process allowed to know curses exists.
THE_ADAPTER = os.path.join("screen", "curses_adapter.py")

#: The Domain, which is pure. Everything under here obeys `FORBIDDEN_IN_DOMAIN`.
THE_DOMAIN = "domain"

#: What "pure" means, spelt out (implementation plan §3). `sys` is on the list
#: because `sys.stdout` is; a module that cannot import `sys` cannot write to
#: it, and cannot reach `sys.argv` or the interpreter either.
FORBIDDEN_IN_DOMAIN = ("curses", "subprocess", "os", "sys", "time")


def python_files():
    for directory, _, filenames in os.walk(PACKAGE_ROOT):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                path = os.path.join(directory, filename)
                yield os.path.relpath(path, PACKAGE_ROOT), path


def domain_files():
    """The Python files of the Domain, by their name within the package."""
    return [(name, path) for name, path in python_files()
            if name.split(os.sep)[0] == THE_DOMAIN]


def source_of(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def imported_game_modules(source):
    """Which `terminalgame.…` modules this source imports, as dotted names.

    `imports` above answers "does it import this top-level module", which
    cannot tell `terminalgame.domain.maze` from `terminalgame.screen.port`.
    The Domain depends on nothing above it, so that distinction is the whole
    question here.
    """
    found = []
    for line in source.splitlines():
        stripped = line.strip()
        words = stripped.replace(",", " ").split()
        if stripped.startswith("from ") and len(words) > 1:
            candidates = [words[1]]
        elif stripped.startswith("import "):
            candidates = words[1:]
        else:
            continue
        for word in candidates:
            if word == "terminalgame" or word.startswith("terminalgame."):
                found.append(word)
    return found


def uses_global_random(source):
    """Which interpreter-wide `random` functions this source reaches for.

    `random.Random(...)` builds a generator of its own and is how the Domain is
    meant to work — a caller hands one in, or names one with a seed. But
    `random.choice(...)`, `random.shuffle(...)` and the rest of the module-level
    functions share one generator belonging to the interpreter, which no test
    can seed. A maze or an opening position built on those could not be
    reproduced, and plan §3 is explicit that "randomness enters it only through
    a seed or a random source passed in, so any maze or ghost behaviour can be
    reproduced in a test".

    `random_source.choice(...)` — a generator that was handed in — is not this
    and does not match: the name before the dot has to be exactly `random`.
    """
    found = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for match in re.finditer(r"(?<![\w.])random\.([A-Za-z_]\w*)", line):
            if match.group(1) != "Random":
                found.append(match.group(1))
        if stripped.startswith("from random import "):
            imported = stripped[len("from random import "):]
            for name in imported.replace(",", " ").split():
                if name != "Random":
                    found.append(name)
    return found


def imports(source, module_name):
    """Does this source actually import that module?

    Crude on purpose — it looks at import statements only, so the word
    appearing in a comment or a docstring does not count.
    """
    for line in source.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ")
                or stripped.startswith("from ")):
            continue
        words = stripped.replace(",", " ").split()
        if module_name in words:
            return True
        for word in words:
            if word.split(".")[0] == module_name and word not in ("from", "import"):
                return True
    return False


class LayerRuleTest(unittest.TestCase):

    def test_only_the_terminal_adapter_knows_that_curses_exists(self):
        offenders = [name for name, path in python_files()
                     if name != THE_ADAPTER and imports(source_of(path), "curses")]
        self.assertEqual([], offenders,
                         "curses has leaked above the screen port; only {0} "
                         "may import it (implementation plan §3)"
                         .format(THE_ADAPTER))

    def test_the_adapter_is_where_it_is_said_to_be(self):
        # If the adapter is moved or renamed, the test above would quietly
        # start permitting nothing at all rather than permitting the wrong
        # thing. This is what stops that going unnoticed.
        names = [name for name, _ in python_files()]
        self.assertIn(THE_ADAPTER, names)
        self.assertTrue(imports(source_of(os.path.join(PACKAGE_ROOT, THE_ADAPTER)),
                                "curses"))

    def test_the_game_process_never_touches_the_desktop(self):
        """Caution C11 — only the launcher drives windows.

        `subprocess` is how the desktop gets driven, by `osascript`. The game
        process has no business with it at all.
        """
        offenders = [name for name, path in python_files()
                     if imports(source_of(path), "subprocess")]
        self.assertEqual([], offenders,
                         "the game process must not shell out; moving, "
                         "titling and closing windows belongs to the "
                         "launcher alone (caution C11)")


class DomainPurityTest(unittest.TestCase):
    """The other half of plan §3: the Domain is pure.

    "The Domain is pure. It imports nothing impure: no `curses`, no
    `subprocess`, no `os`, no `sys.stdout`, no `time`, no screen geometry.
    Randomness enters it only through a seed or a random source passed in, so
    any maze or ghost behaviour can be reproduced in a test."

    Added by WI-4 and extended by WI-7, per the technical lead's ruling that
    this file is a standing obligation rather than a one-off.
    """

    def test_the_domain_is_where_it_is_said_to_be(self):
        # Same guard as `test_the_adapter_is_where_it_is_said_to_be`: if the
        # Domain is moved or renamed, every test below would go on passing
        # while checking an empty list of files.
        names = [name for name, _ in domain_files()]
        self.assertNotEqual([], names,
                            "no Domain found under {0}{1}{2}; the purity "
                            "tests below would be checking nothing"
                            .format(PACKAGE_ROOT, os.sep, THE_DOMAIN))
        self.assertIn(os.path.join(THE_DOMAIN, "maze.py"), names)
        self.assertIn(os.path.join(THE_DOMAIN, "maze_generator.py"), names)
        # WI-7. Listed for the same reason as the two above: if the state
        # module is moved or renamed, every scan below would go on passing
        # while no longer looking at it.
        self.assertIn(os.path.join(THE_DOMAIN, "game_state.py"), names)

    def test_the_domain_imports_nothing_impure(self):
        offenders = []
        for name, path in domain_files():
            source = source_of(path)
            for forbidden in FORBIDDEN_IN_DOMAIN:
                if imports(source, forbidden):
                    offenders.append((name, forbidden))
        self.assertEqual([], offenders,
                         "the Domain is pure: it imports no {0} "
                         "(implementation plan §3)"
                         .format(", ".join(FORBIDDEN_IN_DOMAIN)))

    def test_the_scan_can_see_the_imports_it_is_looking_for(self):
        # A guard that cannot see anything passes for the wrong reason. These
        # are the forms the forbidden imports would actually take, written
        # out here as text rather than by disturbing any module in the tree.
        self.assertTrue(imports("import os", "os"))
        self.assertTrue(imports("import os.path", "os"))
        self.assertTrue(imports("from os import environ", "os"))
        self.assertTrue(imports("import sys, time", "time"))
        self.assertTrue(imports("    import curses", "curses"))
        self.assertTrue(imports("from time import monotonic", "time"))
        # And it does not fire on the word appearing in prose, which is what
        # makes a clean result meaningful rather than merely lucky.
        self.assertFalse(imports('"""No os here."""', "os"))
        self.assertFalse(imports("# import time", "time"))
        self.assertFalse(imports("import ostrich", "os"))

    def test_the_dependency_scan_can_tell_the_domain_from_the_rest(self):
        self.assertEqual(
            ["terminalgame.screen.port"],
            imported_game_modules("from terminalgame.screen.port import Frame"))
        self.assertEqual(
            ["terminalgame.domain.maze"],
            imported_game_modules("from terminalgame.domain.maze import Maze"))
        self.assertEqual(
            ["terminalgame.screen"],
            imported_game_modules("import terminalgame.screen"))
        self.assertEqual([], imported_game_modules("import random"))

    def test_the_domain_depends_on_nothing_above_it(self):
        # Presentation depends on Domain, Application on both. Nothing goes
        # the other way, so a Domain module may import from the Domain and
        # from nowhere else in the game.
        offenders = []
        for name, path in domain_files():
            for imported in imported_game_modules(source_of(path)):
                head = ".".join(imported.split(".")[:2])
                if head != "terminalgame." + THE_DOMAIN:
                    offenders.append((name, imported))
        self.assertEqual([], offenders,
                         "a Domain module imported something outside the "
                         "Domain; the Domain sits at the bottom and depends "
                         "on nothing above it (implementation plan §3)")

    def test_randomness_enters_the_domain_only_where_it_can_be_seeded(self):
        """Plan §3, the clause the other purity tests do not reach.

        "Randomness enters it only through a seed or a random source passed in,
        so any maze or ghost behaviour can be reproduced in a test." A module
        calling `random.choice` directly would still import nothing forbidden
        and depend on nothing above it — it would pass every other test in this
        class — while quietly making its output impossible to reproduce.

        Added by WI-7, which places both actors from a random source, and it
        guards WI-9's ghost policy for the same reason.
        """
        offenders = []
        for name, path in domain_files():
            for used in uses_global_random(source_of(path)):
                offenders.append((name, "random." + used))
        self.assertEqual(
            [], offenders,
            "the Domain reached for the interpreter's shared random generator; "
            "nothing can seed that from a test, so what it produces cannot be "
            "reproduced (implementation plan §3)")

    def test_the_random_scan_can_tell_a_shared_generator_from_an_owned_one(self):
        # The same guard as `test_the_scan_can_see_the_imports_it_is_looking
        # _for`: a scan that saw nothing would pass for the wrong reason.
        self.assertEqual(["choice"], uses_global_random("random.choice(xs)"))
        self.assertEqual(["shuffle"], uses_global_random("    random.shuffle(xs)"))
        self.assertEqual(["randint"], uses_global_random("from random import randint"))
        # An owned generator is the whole point and must not be flagged.
        self.assertEqual([], uses_global_random("random.Random(seed)"))
        self.assertEqual([], uses_global_random("import random"))
        self.assertEqual([], uses_global_random("from random import Random"))
        self.assertEqual([], uses_global_random("random_source.choice(xs)"))
        self.assertEqual([], uses_global_random("self.random.choice(xs)"))
        self.assertEqual([], uses_global_random("# random.choice(xs)"))

    def test_the_domain_carries_no_screen_geometry(self):
        """Caution C5, as far as a text scan can state it.

        Two columns per square, three-column actor glyphs and the 40 x 30
        frame are Presentation's. The port already names those numbers as
        `REQUIRED_WIDTH` and `REQUIRED_HEIGHT`; if either name turns up in
        the Domain, the geometry has come with it.

        This cannot catch a bare `40` written out by hand, and it is not
        claimed to. What it does catch is the Domain reaching for the screen
        port's own constants, which is how the leak would actually happen.
        """
        offenders = []
        for name, path in domain_files():
            source = source_of(path)
            for banned in ("REQUIRED_WIDTH", "REQUIRED_HEIGHT", "Frame",
                           "Colour", "Screen"):
                if banned in source:
                    offenders.append((name, banned))
        self.assertEqual([], offenders,
                         "screen vocabulary has leaked into the Domain "
                         "(architecture caution C5)")


if __name__ == "__main__":
    unittest.main()
