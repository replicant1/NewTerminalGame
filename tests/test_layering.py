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

**WI-12 closed the last two gaps.** `ApplicationLayerTest` covers the loop —
what it may import, and that nothing below it depends on it. `LauncherTest`
walks `launcher/`, which nothing here did until now, so the launcher half of
the layer rule — that the launcher shares no code with the game — is guarded
by the suite rather than by hand.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import unittest

import terminalgame

PACKAGE_ROOT = os.path.dirname(os.path.abspath(terminalgame.__file__))

#: The repository root — the parent of the game package, and the directory the
#: launcher lives beside.
REPOSITORY_ROOT = os.path.dirname(PACKAGE_ROOT)

#: The one module in the whole game process allowed to know curses exists.
THE_ADAPTER = os.path.join("screen", "curses_adapter.py")

#: The Domain, which is pure. Everything under here obeys `FORBIDDEN_IN_DOMAIN`.
THE_DOMAIN = "domain"

#: What "pure" means, spelt out (implementation plan §3). `sys` is on the list
#: because `sys.stdout` is; a module that cannot import `sys` cannot write to
#: it, and cannot reach `sys.argv` or the interpreter either.
FORBIDDEN_IN_DOMAIN = ("curses", "subprocess", "os", "sys", "time")

#: The Presentation layer, added by WI-5a. It turns a domain state into
#: characters and colours: "It never reads a key, never writes to a terminal,
#: never sleeps" (plan §3).
THE_PRESENTATION = "presentation"

#: Presentation is not pure in the Domain's sense — it is allowed to know what
#: a screen is — but it does no I/O and no waiting, so the same list applies.
FORBIDDEN_IN_PRESENTATION = ("curses", "subprocess", "os", "sys", "time")

#: What Presentation may import from the rest of the game. The Domain, whose
#: state it renders, and the screen **port**, whose `Colour` names are the
#: vocabulary it renders into — but never the terminal adapter behind that
#: port, and never the Application above it.
#:
#: The port entry is a judgement and it is recorded here rather than left
#: implicit: plan §3 says "Presentation depends on Domain, and on nothing
#: else" and in the same breath says Presentation produces "a grid of
#: characters and colours", which it cannot name without the port. The port's
#: own docstring has said since WI-2 that "Presentation asks for
#: `Colour.WALL`". See the WI-5a PR summary — this needs a ruling, and if it
#: goes the other way it is this tuple that changes.
#:
#: `terminalgame.presentation` is on the list because **a layer may import
#: itself**. WI-5a wrote this tuple when Presentation had exactly one module,
#: so nothing in it had anything to import from a sibling and the omission
#: could not show. WI-5b's frame builder imports the wall-glyph table, and the
#: rule failed on a case it should always have allowed. Recorded rather than
#: quietly widened: the hole was in the guard, not in the code it guards.
PRESENTATION_MAY_IMPORT = ("terminalgame.domain", "terminalgame.screen.port",
                           "terminalgame.presentation")


def python_files():
    for directory, _, filenames in os.walk(PACKAGE_ROOT):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                path = os.path.join(directory, filename)
                yield os.path.relpath(path, PACKAGE_ROOT), path


def files_under(layer):
    """The Python files of one layer, by their name within the package."""
    return [(name, path) for name, path in python_files()
            if name.split(os.sep)[0] == layer]


def domain_files():
    """The Python files of the Domain, by their name within the package."""
    return files_under(THE_DOMAIN)


def presentation_files():
    """The Python files of the Presentation layer."""
    return files_under(THE_PRESENTATION)


#: The Application layer — the loop, and nothing else. Added by WI-12.
THE_APPLICATION = "application"

#: Application may know the clock; it is the only layer that legitimately does.
#: It may not know curses, and it may not drive the desktop (caution C11).
FORBIDDEN_IN_APPLICATION = ("curses", "subprocess")

#: What Application may import from the rest of the game. Plan §3: "Application
#: depends on Presentation, Domain and the Screen port."
APPLICATION_MAY_IMPORT = ("terminalgame.domain", "terminalgame.presentation",
                          "terminalgame.screen.port")

#: The launcher process, which is not part of the game package at all.
LAUNCHER_ROOT = os.path.join(REPOSITORY_ROOT, "launcher")

#: The smoke test, which is part of neither and drives both from outside.
SMOKETEST_ROOT = os.path.join(REPOSITORY_ROOT, "smoketest")

#: What the smoke test may import. The launcher, because it starts the game
#: the way a player does — and **nothing from the game**, ruled in WI-14a for
#: the reason that is the whole point of it: *a check that reaches inside the
#: game can pass while the thing the player runs is broken.* Import
#: `terminalgame` and it could assert against the frame builder's own output
#: instead of against what reached the screen.
#:
#: `needs_a_person` is here because `__main__` prints a closing line counting
#: the codes only a person can settle. That is a register of strings and
#: imports nothing itself, so it cannot carry the game in behind it.
SMOKETEST_MAY_IMPORT = ("smoketest", "launcher", "needs_a_person")


def application_files():
    """The Python files of the Application layer."""
    return files_under(THE_APPLICATION)


def launcher_files():
    """The Python files of the launcher, by their name within it."""
    found = []
    for directory, _, filenames in os.walk(LAUNCHER_ROOT):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                path = os.path.join(directory, filename)
                found.append((os.path.relpath(path, LAUNCHER_ROOT), path))
    return found


def smoketest_files():
    """The Python files of the smoke test, by their name within it."""
    found = []
    for directory, _, filenames in os.walk(SMOKETEST_ROOT):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                path = os.path.join(directory, filename)
                found.append((os.path.relpath(path, SMOKETEST_ROOT), path))
    return found


def top_level_imports(source, package=None):
    """Every top-level module name this source imports, read with `ast`.

    `ast` rather than the line scanning the rest of this file uses, because the
    launcher question is different in kind: the other tests ask "does this
    mention that name", where this one must enumerate **everything** a module
    imports and judge each. A scan that missed one would be the whole failure.

    `package` is the package a **relative** import resolves within — "launcher"
    for a launcher module, "terminalgame" for a game one. It has to be told:
    `from . import script` names no package in the source, and guessing one
    would report the game's own relative imports as somebody else's. Left out,
    a relative import is reported as `"."`, which belongs to nothing and so is
    never mistaken for a real dependency.
    """
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                names.add(package if package is not None else ".")
            elif node.module:
                names.add(node.module.split(".")[0])
    return names


def is_in_this_repository(module_name):
    """Is that top-level name one of this project's own packages?

    Answered from the tree rather than from a list of standard-library names,
    which 3.9 does not offer and which would go stale anyway. Anything the
    repository does not define is something the interpreter brought.
    """
    package = os.path.join(REPOSITORY_ROOT, module_name)
    return os.path.isdir(package) or os.path.isfile(package + ".py")


def is_standard_library(module_name):
    """Is that importable, and from outside this repository?"""
    if is_in_this_repository(module_name):
        return False
    try:
        spec = importlib.util.find_spec(module_name)
    except (ImportError, ValueError):
        return False
    if spec is None:
        return False
    origin = getattr(spec, "origin", None)
    if origin in (None, "built-in", "frozen"):
        return True
    return not os.path.abspath(origin).startswith(REPOSITORY_ROOT + os.sep)


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


class PresentationLayerTest(unittest.TestCase):
    """Plan §3 — Presentation renders the Domain and does no I/O.

    Added by WI-5a, which created the layer. The Domain half above says
    nothing may point *down* into the Domain's dependencies; this says
    Presentation may not point *up* or sideways.
    """

    def test_the_presentation_layer_is_where_it_is_said_to_be(self):
        names = [name for name, _ in presentation_files()]
        self.assertNotEqual([], names,
                            "no Presentation layer found under {0}{1}{2}; the "
                            "tests below would be checking nothing"
                            .format(PACKAGE_ROOT, os.sep, THE_PRESENTATION))
        self.assertIn(os.path.join(THE_PRESENTATION, "wall_glyphs.py"), names)

    def test_presentation_reads_no_key_writes_no_terminal_and_never_sleeps(self):
        offenders = []
        for name, path in presentation_files():
            source = source_of(path)
            for forbidden in FORBIDDEN_IN_PRESENTATION:
                if imports(source, forbidden):
                    offenders.append((name, forbidden))
        self.assertEqual([], offenders,
                         "Presentation turns a state into characters and "
                         "colours and does nothing else: no {0} "
                         "(implementation plan §3)"
                         .format(", ".join(FORBIDDEN_IN_PRESENTATION)))

    def test_presentation_imports_only_the_domain_and_the_screen_port(self):
        offenders = []
        for name, path in presentation_files():
            for imported in imported_game_modules(source_of(path)):
                if not any(imported == allowed or imported.startswith(allowed + ".")
                           for allowed in PRESENTATION_MAY_IMPORT):
                    offenders.append((name, imported))
        self.assertEqual([], offenders,
                         "Presentation may import {0} and nothing else in the "
                         "game — in particular never the terminal adapter, "
                         "which is what keeps curses below the port"
                         .format(" or ".join(PRESENTATION_MAY_IMPORT)))

    def test_presentation_never_reaches_for_the_terminal_adapter(self):
        # Implied by the test above, and stated separately because it is the
        # one that would actually break the layer rule rather than merely
        # blur it: the adapter is the only module that knows curses exists.
        offenders = [name for name, path in presentation_files()
                     if "curses_adapter" in source_of(path)]
        self.assertEqual([], offenders)

    def test_the_domain_does_not_import_the_presentation_layer(self):
        # The other direction, and the one that would be a real inversion.
        # Covered by `test_the_domain_depends_on_nothing_above_it`; named here
        # too because the Presentation layer now exists to be imported and a
        # reader of this class should see the pair.
        offenders = []
        for name, path in domain_files():
            for imported in imported_game_modules(source_of(path)):
                if imported.startswith("terminalgame." + THE_PRESENTATION):
                    offenders.append((name, imported))
        self.assertEqual([], offenders,
                         "dependencies point inward only: Presentation → "
                         "Domain, never the other way")


class ApplicationLayerTest(unittest.TestCase):
    """Plan §3 — "Application depends on Presentation, Domain and the Screen
    port. Nothing depends on Application."

    Added by WI-12, which is where the layer stopped being hypothetical.
    """

    def test_the_application_layer_is_where_it_is_said_to_be(self):
        names = [name for name, _ in application_files()]
        self.assertIn(os.path.join(THE_APPLICATION, "loop.py"), names,
                      "no Application found; the tests below would be "
                      "checking an empty list of files")

    def test_it_imports_nothing_it_has_no_business_with(self):
        offenders = []
        for name, path in application_files():
            source = source_of(path)
            for forbidden in FORBIDDEN_IN_APPLICATION:
                if imports(source, forbidden):
                    offenders.append((name, forbidden))
        self.assertEqual([], offenders,
                         "the loop drives the screen through the port and the "
                         "desktop not at all (plan §3, caution C11)")

    def test_it_reaches_only_for_the_layers_beneath_it(self):
        offenders = []
        for name, path in application_files():
            for imported in imported_game_modules(source_of(path)):
                if not imported.startswith(APPLICATION_MAY_IMPORT):
                    offenders.append((name, imported))
        self.assertEqual([], offenders,
                         "Application may import the Domain, Presentation and "
                         "the screen port, and nothing else")

    def test_it_never_reaches_for_the_terminal_adapter(self):
        # The port is an interface; the adapter behind it is the screen's
        # business and not the loop's.
        for name, path in application_files():
            self.assertNotIn("curses_adapter", source_of(path), name)

    def test_nothing_beneath_it_depends_on_the_application_layer(self):
        """"Nothing depends on Application" — the half that is easy to lose.

        The Domain, Presentation and the screen port must all be usable with
        no loop anywhere, which is what lets them be tested by the thousand.
        """
        offenders = []
        beneath = domain_files() + presentation_files() + files_under("screen")
        for name, path in beneath:
            for imported in imported_game_modules(source_of(path)):
                if imported.startswith("terminalgame." + THE_APPLICATION):
                    offenders.append((name, imported))
        self.assertEqual([], offenders,
                         "something below the loop imported it; nothing "
                         "depends on Application (plan §3)")


class LauncherTest(unittest.TestCase):
    """The launcher half of the layer rule — the gap open since M0.

    Plan §3: "The Launcher process shares no code with the game's Domain,
    Presentation or Application. It knows nothing about mazes."

    Until WI-12 nothing walked `launcher/` and this was checked by hand, which
    is to say it was checked once. It is the suite's now.
    """

    def test_there_is_a_launcher_to_look_at(self):
        # The same guard the other layers carry: a scan of nothing passes.
        names = [name for name, _ in launcher_files()]
        self.assertIn("game.py", names)
        self.assertIn("lifecycle.py", names)
        self.assertGreater(len(names), 4)

    def test_the_launcher_imports_nothing_from_the_game(self):
        offenders = []
        for name, path in launcher_files():
            for imported in top_level_imports(source_of(path), "launcher"):
                if imported == "terminalgame":
                    offenders.append(name)
        self.assertEqual([], offenders,
                         "the launcher process shares no code with the game "
                         "(plan §3); it names the game as a string and starts "
                         "it as a subprocess")

    def test_every_launcher_import_is_the_standard_library_or_itself(self):
        """The stronger form, and the one that catches what nobody predicted.

        Not "does it avoid the game" but "what *does* it import" — enumerated
        with `ast` and each one judged. A new dependency on anything at all
        shows up here.
        """
        offenders = []
        for name, path in launcher_files():
            for imported in top_level_imports(source_of(path), "launcher"):
                if imported == "launcher":
                    continue
                if not is_standard_library(imported):
                    offenders.append((name, imported))
        self.assertEqual([], offenders,
                         "the launcher runs on the standard library and its "
                         "own modules, and nothing else")

    def test_the_game_never_imports_the_launcher_either(self):
        offenders = []
        for name, path in python_files():
            if "launcher" in top_level_imports(source_of(path), "terminalgame"):
                offenders.append(name)
        self.assertEqual([], offenders,
                         "the game process must not know the launcher exists "
                         "(caution C11)")

    def test_the_import_scan_sees_what_it_is_looking_for(self):
        # A guard that enumerated nothing would pass every test above.
        self.assertEqual({"os"}, top_level_imports("import os"))
        self.assertEqual({"os"}, top_level_imports("import os.path"))
        self.assertEqual({"os", "sys"}, top_level_imports("import os, sys"))
        self.assertEqual({"terminalgame"},
                         top_level_imports("from terminalgame.domain import x"))
        self.assertEqual({"launcher"},
                         top_level_imports("from . import script", "launcher"))
        # The same line in the game resolves to the game, not the launcher.
        self.assertEqual({"terminalgame"},
                         top_level_imports("from .screen import port", "terminalgame"))
        self.assertEqual({"."}, top_level_imports("from . import script"))
        self.assertEqual({"launcher"},
                         top_level_imports("from launcher.script import x"))
        # Prose and comments are not imports, and `ast` cannot be fooled by
        # them the way a line scan could.
        self.assertEqual(set(), top_level_imports('"""import os."""'))
        self.assertEqual(set(), top_level_imports("# import terminalgame"))

    def test_the_standard_library_check_can_tell_the_difference(self):
        self.assertTrue(is_standard_library("subprocess"))
        self.assertTrue(is_standard_library("os"))
        self.assertFalse(is_standard_library("terminalgame"))
        self.assertFalse(is_standard_library("launcher"))
        self.assertFalse(is_standard_library("tests"))
        self.assertFalse(is_standard_library("no_such_module_anywhere"))


class SmokeTestStaysOutsideTest(unittest.TestCase):
    """The smoke test checks the game from outside, and must stay outside.

    Ruled in WI-14a, and the reason is its whole purpose: **a check that
    reaches inside the game can pass while the thing the player runs is
    broken.** If `smoketest/` could import `terminalgame`, it could assert
    against the frame builder's own output rather than against what actually
    arrived on the screen, and it would stop being a test of the assembled
    thing at all.

    Added by WI-14b rather than left as a ruling nobody enforces — a new
    category with rules in prose only is a guard waiting to have never been
    exercised.
    """

    def test_there_is_a_smoke_test_to_look_at(self):
        # A scan of nothing passes. This is the guard on the guard.
        names = [name for name, _ in smoketest_files()]
        self.assertIn("pack.py", names)
        self.assertIn("__main__.py", names)
        self.assertGreater(len(names), 2)

    def test_the_register_is_a_separate_package_that_imports_nothing(self):
        """`needs_a_person` is a register, not an instrument.

        It was split out of the same directory as the smoke test, and the
        split only means anything while it stays inert: the moment it imports
        something it stops being a list of what a person must do and becomes
        a second thing that runs.
        """
        root = os.path.join(REPOSITORY_ROOT, "needs_a_person")
        self.assertTrue(os.path.isdir(root), "the register should be its own package")
        checks = os.path.join(root, "checks.py")
        self.assertTrue(os.path.isfile(checks))
        imported = top_level_imports(source_of(checks), "needs_a_person")
        not_stdlib = sorted(m for m in imported if not is_standard_library(m))
        self.assertEqual(
            [], not_stdlib,
            "checks.py must import nothing but the standard library; it "
            "reaches for %s" % (not_stdlib,))

    def test_the_pack_imports_nothing_from_the_game(self):
        offenders = []
        for name, path in smoketest_files():
            for imported in top_level_imports(source_of(path), "smoketest"):
                if imported == "terminalgame":
                    offenders.append(name)
        self.assertEqual([], offenders,
                         "the smoke test drives the game from outside, "
                         "the way a player does; importing it would let a "
                         "check pass while what the player runs is broken")

    def test_every_pack_import_is_the_standard_library_or_the_launcher(self):
        # The stronger form, as with the launcher: not "does it avoid the
        # game" but "what *does* it import", enumerated and each one judged.
        offenders = []
        for name, path in smoketest_files():
            for imported in top_level_imports(source_of(path), "smoketest"):
                if imported in SMOKETEST_MAY_IMPORT:
                    continue
                if not is_standard_library(imported):
                    offenders.append((name, imported))
        self.assertEqual([], offenders,
                         "the pack runs on the standard library, the launcher "
                         "and its own modules, and nothing else")

    def test_it_really_does_import_the_launcher(self):
        # Otherwise the test above passes on a pack that imports nothing and
        # therefore does nothing.
        imported = set()
        for _, path in smoketest_files():
            imported.update(top_level_imports(source_of(path), "smoketest"))
        self.assertIn("launcher", imported)

    def test_neither_the_game_nor_the_launcher_imports_the_pack(self):
        # The other direction. The pack is a harness; nothing ships depending
        # on it.
        offenders = []
        for name, path in python_files():
            if "smoketest" in top_level_imports(source_of(path), "terminalgame"):
                offenders.append(("terminalgame/" + name, "smoketest"))
        for name, path in launcher_files():
            if "smoketest" in top_level_imports(source_of(path), "launcher"):
                offenders.append(("launcher/" + name, "smoketest"))
        self.assertEqual([], offenders,
                         "nothing that ships may depend on the test harness")


if __name__ == "__main__":
    unittest.main()
