"""The game as a set of facts: what is where, what has been eaten, how it ends.

This is the vocabulary the rest of the game speaks. WI-8 moves the player
through it, WI-9 moves the ghost, WI-10 reads an outcome out of it, WI-6 counts
its dots and WI-5b draws it — so the names here are the ones that cost the most
to change later, and they are deliberately plain.

**A state is immutable.** Every field is fixed at construction and the dots are
a `frozenset`; changing anything means asking for a new state with
:meth:`GameState.with_changes`. That is not ceremony. It makes "a move into a
wall changes **nothing at all**" (WI-8) checkable as equality against the state
you started with, rather than as the absence of a mutation nobody can see; and
it means the ghost's policy cannot quietly alter a state it was only asked to
look at.

**It is pure.** No `curses`, no `os`, no `sys`, no `time`, and no screen
geometry: a square is a square, and that two terminal columns are spent drawing
one of them is Presentation's business (architecture caution C5). Randomness
enters only as a seed or a random source handed in, so every opening position
can be reproduced exactly.

**One game per process (GAME-3).** There is no lives count, no level, no timer,
no pause flag and no way to restart — not because they are set to zero, but
because there is nowhere to put them. A test pins the field list for that
reason.

## Where the two actors start

START-1 puts the player on the corridor square nearest the middle. START-2 puts
the ghost on the corridor square furthest from the player, "measured across the
grid rather than along the corridors".

**The metric is straight-line — Euclidean — distance across the grid, and it is
an assumption rather than a ruling.** The user has not answered the question.
Architecture assumption A6 says "straight-line grid distance", and straight-line
is what Euclidean means; but Manhattan (`|dx| + |dy|`) and Chebyshev
(`max(|dx|, |dy|)`) both satisfy the words of START-2 just as well, and all three
would keep the actors "well apart". If the user wants one of the others,
:func:`squared_distance` is the only place it is decided and
:data:`DISTANCE_METRIC` is the only sentence that has to change.

Distances are compared **squared**, never square-rooted. Ordering by `d²` is the
same as ordering by `d` for non-negative distances, and it keeps the whole
calculation in exact integers, so two squares that are genuinely equidistant tie
exactly instead of tying or not according to floating-point error.
"""

from __future__ import annotations

import random

from terminalgame.domain.maze import DIRECTIONS
from terminalgame.domain.maze_generator import generate_maze_with

#: How START-2 is measured. Stated here so that "which metric?" has one answer
#: in the system and it is written down next to the code that applies it.
DISTANCE_METRIC = "straight-line (Euclidean) distance across the grid"


class Outcome:
    """How the game stands: still on, lost, or won.

    Three cases and no fourth. `PLAYING` is not "not yet decided" — it is a
    positive statement that the game is under way, which is what START-5 asks
    for from the first instant.
    """

    PLAYING = "playing"
    CAUGHT = "caught"
    CLEARED = "cleared"

    #: Every case, for a test that wants to check there are exactly three.
    ALL = (PLAYING, CAUGHT, CLEARED)


class NoCorridorToStartOn(ValueError):
    """A maze with no corridor square, or only one, cannot open a game.

    Plan §11.8 — where an argument makes a requirement unsatisfiable, refuse and
    say which requirement. With no corridor square START-1 has nowhere to put
    the player; with exactly one, START-2 has nowhere to put the ghost that is
    not the player's own square.
    """


def squared_distance(a, b):
    """The squared straight-line distance between two squares.

    Squared on purpose — see the module docstring. This is the only place the
    metric of START-2 is decided.
    """
    ax, ay = a
    bx, by = b
    return (ax - bx) ** 2 + (ay - by) ** 2


class GameState:
    """Everything true of a game at one moment."""

    __slots__ = ("maze", "player", "ghost", "ghost_heading", "dots", "score",
                 "outcome")

    #: The whole vocabulary, in one place. GAME-3 is the statement that this
    #: list has no lives, no level, no timer, no pause and no restart on it.
    FIELDS = __slots__

    def __init__(self, maze, player, ghost, ghost_heading, dots, score=0,
                 outcome=Outcome.PLAYING):
        object.__setattr__(self, "maze", maze)
        object.__setattr__(self, "player", tuple(player))
        object.__setattr__(self, "ghost", tuple(ghost))
        object.__setattr__(self, "ghost_heading", ghost_heading)
        object.__setattr__(self, "dots", frozenset(dots))
        object.__setattr__(self, "score", score)
        object.__setattr__(self, "outcome", outcome)

    # -- immutability ------------------------------------------------------

    def __setattr__(self, name, value):
        raise AttributeError(
            "a GameState is immutable; ask for a new one with with_changes() "
            "rather than assigning to %r" % (name,))

    def __delattr__(self, name):
        raise AttributeError("a GameState is immutable; cannot delete %r"
                             % (name,))

    def with_changes(self, **changes):
        """A new state, the same as this one but for the fields named.

        The only way anything changes. Every field is settable through it
        because WI-8, WI-9 and WI-10 between them move all of them; what they
        cannot do is change a state somebody else is holding.
        """
        unknown = sorted(set(changes) - set(self.FIELDS))
        if unknown:
            raise TypeError(
                "no such field on a GameState: %s (the state carries %s, and "
                "GAME-3 is the reason there is nothing else)"
                % (", ".join(unknown), ", ".join(self.FIELDS)))
        values = {name: getattr(self, name) for name in self.FIELDS}
        values.update(changes)
        return GameState(**values)

    # -- questions worth asking often --------------------------------------

    def dot_at(self, square):
        """Is there still a dot on that square?"""
        return tuple(square) in self.dots

    @property
    def dots_remaining(self):
        """How many dots are left. WI-10 wins the game when this reaches nil."""
        return len(self.dots)

    @property
    def is_over(self):
        return self.outcome != Outcome.PLAYING

    # -- value semantics ---------------------------------------------------

    def __eq__(self, other):
        if not isinstance(other, GameState):
            return NotImplemented
        return all(getattr(self, name) == getattr(other, name)
                   for name in self.FIELDS)

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self):
        return hash(tuple(getattr(self, name) for name in self.FIELDS))

    def __repr__(self):
        return ("GameState(player={0!r}, ghost={1!r}, heading={2!r}, "
                "dots={3}, score={4}, outcome={5!r})"
                .format(self.player, self.ghost, self.ghost_heading,
                        self.dots_remaining, self.score, self.outcome))


# -- opening a game --------------------------------------------------------


def nearest_to_centre(maze):
    """The corridor square nearest the middle of the maze (START-1).

    The centre of a grid `width` squares across sits at `(width - 1) / 2`, which
    is a half-square when the width is even. Rather than round it — and have to
    justify rounding one way — both the centre and each square are doubled, so
    `dx = 2x - (width - 1)` is an exact integer for every grid. Doubling scales
    every distance by the same factor, so it cannot change which square is
    nearest.

    Ties go to the first square in reading order: smallest `y`, then smallest
    `x`. Stated in the key rather than relying on the order
    `corridor_squares()` happens to return, so it stays true if that order ever
    changes.
    """
    corridors = maze.corridor_squares()
    _refuse_if_too_few(corridors, need=1, requirement="START-1")
    centre_x, centre_y = maze.width - 1, maze.height - 1
    return min(
        corridors,
        key=lambda square: (
            squared_distance((2 * square[0], 2 * square[1]),
                             (centre_x, centre_y)),
            square[1],
            square[0],
        ),
    )


def furthest_from(maze, square):
    """The corridor square furthest from `square` (START-2).

    Furthest under :data:`DISTANCE_METRIC` — across the grid, not along the
    corridors, so the two need not be far apart as the player walks. Ties go to
    the first in reading order, as in :func:`nearest_to_centre`.
    """
    corridors = maze.corridor_squares()
    _refuse_if_too_few(corridors, need=2, requirement="START-2")
    return max(
        corridors,
        key=lambda other: (
            squared_distance(other, square),
            -other[1],
            -other[0],
        ),
    )


def new_game(seed=None, width=None, height=None):
    """A fresh game: a new maze, both actors placed, every dot laid.

    `seed` names the whole game — the maze and both placements — so any opening
    position can be reproduced exactly. With no seed the game is different every
    time, which is MAZE-4.
    """
    return new_game_with(random.Random(seed), width=width, height=height)


def new_game_with(random_source, width=None, height=None):
    """The same, for a caller that owns the whole game's randomness.

    One source for the maze and for the ghost's opening heading, so a caller
    threading a single `Random` through the game gets a reproducible whole.
    """
    sizing = {}
    if width is not None:
        sizing["width"] = width
    if height is not None:
        sizing["height"] = height
    maze = generate_maze_with(random_source, **sizing)
    return open_game_on(maze, random_source)


def open_game_on(maze, random_source):
    """Place the actors and lay the dots on a maze that already exists.

    Separate from :func:`new_game_with` so that a test — or WI-10 — can open a
    game on a maze it wrote out by hand, without going through the generator.
    """
    player = nearest_to_centre(maze)
    ghost = furthest_from(maze, player)
    # START-3: every corridor square holds a dot except the one the player
    # starts on. The ghost's square is NOT excepted, so the last dot of a game
    # can sit underneath the ghost — which is the situation END-3 is about.
    dots = frozenset(maze.corridor_squares()) - {player}
    return GameState(
        maze=maze,
        player=player,
        ghost=ghost,
        ghost_heading=opening_heading(maze, ghost, random_source),
        dots=dots,
        score=0,                  # START-4
        outcome=Outcome.PLAYING,  # START-5: under way from the first instant
    )


def opening_heading(maze, square, random_source):
    """Which way the ghost is already going (START-5).

    "The game is under way the moment the window opens: the ghost is already
    moving" — so the ghost has a heading before anything has been pressed, and
    it is one it can actually travel. Chosen from the ways on rather than fixed,
    because a fixed heading would point into a wall on most mazes and the ghost
    would spend its first move turning round instead of moving.

    MAZE-5 guarantees a corridor square has at least two ways on, so the choice
    is never empty for a square the generator produced. A square with none at
    all — constructible by hand — falls back to a fixed direction rather than
    failing, because a ghost that cannot move is not a broken opening position,
    it is a maze with nowhere to go.
    """
    ways_on = [direction for direction, _, _ in maze.open_neighbours(*square)]
    if not ways_on:
        return DIRECTIONS[0]
    return random_source.choice(ways_on)


def _refuse_if_too_few(corridors, need, requirement):
    if len(corridors) < need:
        raise NoCorridorToStartOn(
            "%s needs at least %d corridor square%s and this maze has %d"
            % (requirement, need, "" if need == 1 else "s", len(corridors)))
