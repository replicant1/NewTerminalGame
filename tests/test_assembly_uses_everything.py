"""Does the assembled game actually *use* everything that was built for it?

WI-15 shipped complete, tested and dead: `placement.py` was finished, its
tests passed, and **nothing ever called it**. The game placed its window
nowhere. No test caught it, and no test could have — `test_placement.py`
checks the arithmetic, `test_window_placement.py` checks the join through a
window a test built, and **neither can know whether the assembled game ever
asks.**

**An absent call site is invisible to every test that examines the things on
either side of it.** This file is the one that looks at the site itself.

Why seven
---------

The root cause was in the dependency graph, not in anybody's code: **WI-15's
only outgoing edge went to a verification item, and a verification item
consumes nothing** — so WI-15 produced a capability no item was ever told to
use. The technical lead ran that question across the whole graph and found
**seven capabilities whose only possible consumer is the assembly**. WI-15 is
the one that failed. WI-9 survived by luck, because the session needed a ghost
to tick and consumed it on the way past.

So this file names all seven and checks each, rather than trusting that the
load-bearing ones are obviously fine — *guessing which are safe is exactly how
WI-15 was missed.*

How it checks
-------------

By reading the source of everything reachable from the entry point, with
``ast``. Same technique as ``tools/layer_rule.py``, and for the reason that
module already gives: *a sentence remembers what was true once and nothing
re-runs it.* Being reachable is necessary but not sufficient — a module can be
imported and its one useful function never called — so each row also names the
call that has to happen.

`TestTheDetectorWorks` keeps the whole file from passing vacuously.
"""

from __future__ import annotations

import ast
import os
from collections import deque

import pytest

ROOT = "terminal_game"

#: The module the assembled game is entered through.
ENTRY = "terminal_game.shell.game"

#: The seven, as ``code: (module, the call that must happen)``. If a capability
#: is ever moved or renamed, this table is the one place to change — and a
#: failure here says which requirement went quiet, not merely which import
#: went missing.
SEVEN = {
    "WI-2 maze generation": ("terminal_game.domain.generation", "generate"),
    "WI-9 ghost policy": ("terminal_game.domain.ghost", "next_ghost_move"),
    "WI-11 session controller": ("terminal_game.application.session", "Session"),
    "WI-12 status line": ("terminal_game.presentation.status", "status_cells"),
    "WI-13 input translation": ("terminal_game.presentation.keys", "intent_for"),
    "WI-15 window placement": ("terminal_game.shell.placement", "placement_for"),
}

#: The seventh. WI-7's walking skeleton is **deliberately** not reachable from
#: the assembled game: section 7 says *"WI-7 builds it with fixtures to prove
#: the slice; WI-14 supersedes those fixtures and owns it thereafter."* It is
#: a proven scaffold with its own tests, not a dead capability, and the test
#: below records that so nobody "fixes" it by wiring it back in.
SUPERSEDED = "terminal_game.shell.skeleton"


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _module_file(dotted):
    return os.path.join(_repo_root(), *dotted.split(".")) + ".py"


def _imports_of(source):
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            for alias in node.names:
                names.add("{}.{}".format(node.module, alias.name))
    return {name for name in names if name.startswith(ROOT)}


def reachable_sources():
    """Every module reachable from the entry point, with its source."""
    found = {}
    queue = deque([ENTRY])
    while queue:
        dotted = queue.popleft()
        if dotted in found:
            continue
        path = _module_file(dotted)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        found[dotted] = source
        for name in _imports_of(source):
            if name not in found:
                queue.append(name)
    return found


def callers_of(name, sources):
    """Which reachable modules call ``name``, however it was imported."""
    calling = set()
    for dotted, source in sources.items():
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = getattr(func, "id", None) or getattr(func, "attr", None)
            if called == name:
                calling.add(dotted)
                break
    return calling


@pytest.fixture(scope="module")
def sources():
    return reachable_sources()


class TestTheAssemblyReachesEveryCapability:
    """Necessary: the module is imported somewhere the entry point can get to."""

    @pytest.mark.parametrize("code", sorted(SEVEN))
    def test_the_capability_is_reachable_from_the_entry_point(self, code, sources):
        module, _ = SEVEN[code]
        assert module in sources, (
            "{} is not reachable from {}: it can be complete and tested and "
            "still never run, which is exactly what WI-15 shipped".format(
                code, ENTRY
            )
        )


class TestTheAssemblyActuallyCallsEveryCapability:
    """Sufficient: something in that reachable set calls the thing.

    Reachability alone is not enough — ``placement`` was imported by
    ``window.py`` for a type the whole time it was never used for a decision.
    """

    @pytest.mark.parametrize("code", sorted(SEVEN))
    def test_the_capability_is_called(self, code, sources):
        _, call = SEVEN[code]
        calling = callers_of(call, sources)
        assert calling, (
            "nothing the assembled game can reach calls {}(), so {} is dead "
            "code however well tested it is".format(call, code)
        )


class TestTheSupersededOneStaysSuperseded:
    """WI-7's skeleton is meant to be unreachable, and that is not a defect."""

    def test_the_skeleton_is_not_wired_into_the_game(self, sources):
        # Section 7: WI-14 supersedes WI-7's fixtures and owns the entry
        # point thereafter. Two live entry points would be two things to keep
        # in step, and only one of them would ever be played.
        assert SUPERSEDED not in sources

    def test_the_skeleton_still_exists_and_is_still_tested(self):
        # It proved the vertical slice and its tests still run; this is not
        # an argument for deleting it, only for not calling it.
        assert os.path.exists(_module_file(SUPERSEDED))
        assert os.path.exists(
            os.path.join(_repo_root(), "tests", "test_skeleton.py")
        )


class TestTheDetectorWorks:
    """Without these, every test above could be passing on an empty result."""

    def test_the_entry_point_is_found_at_all(self, sources):
        assert ENTRY in sources

    def test_it_reaches_a_useful_number_of_modules(self, sources):
        # If the walk broke, `sources` would be one module and every
        # "reachable" assertion above would fail rather than pass — but a
        # detector that silently found everything would be worse, so pin the
        # shape: more than a handful, fewer than the whole world.
        assert 8 <= len(sources) <= 40

    def test_it_reaches_all_four_layers(self, sources):
        layers = {name.split(".")[1] for name in sources if name.count(".") >= 2}
        assert {"domain", "application", "presentation", "shell"} <= layers

    def test_a_call_that_is_not_made_is_not_reported(self, sources):
        # The control. A name nothing calls must come back with no callers,
        # otherwise `callers_of` is matching something it should not and
        # every "is called" assertion above is worthless.
        assert callers_of("no_such_function_anywhere", sources) == set()

    def test_a_call_that_is_made_is_reported(self, sources):
        # And the other direction, on something unmistakably called.
        assert callers_of("compose_frame", sources)

    def test_a_module_that_is_not_imported_is_not_reachable(self, sources):
        assert "terminal_game.does.not.exist" not in sources
