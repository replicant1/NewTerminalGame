"""The rules of the game: **starting** a game, and what a **move** does.

START-1..5 say where everything begins; :func:`move_player` says what one
press of an arrow key changes.

It is part of the pure core: it imports nothing impure, reads no file, reads
no clock, and takes every scrap of randomness it needs as a
``random.Random`` **parameter** (implementation plan §2.4). Hand it the same
seed twice and you get the identical starting position twice, which is what
makes every other test in this project reproducible.

The two placement rules, in one sentence each, so that they can be read off
the code without running it:

===========  ==============================================================
START-1      the player starts on the corridor square **nearest the middle
             of the grid**, ties broken by lowest ``(row, col)``
START-2      the ghost starts on the corridor square **furthest from the
             player measured across the grid** — squared Euclidean distance
             over ``(row, col)``, *not* distance along the corridors — ties
             broken the same way
START-3      every corridor square holds a dot **except** the player's
START-4      the score starts at zero, and the outcome is ``PLAYING``
START-5      (the state half) the game is under way the moment a state
             exists: :func:`new_game` takes a random source and nothing
             else. There is no title screen, no "press any key", and no
             argument by which one could be introduced
===========  ==============================================================

**Assumption A2 — not a ruling.** The specification's START-2 says "measured
across the grid rather than along the corridors". That rules out path
distance but does not say *which* straight-line metric. This module proceeds
on the plan's recorded assumption (§9, A2): **squared Euclidean on
``(row, col)``**, ties broken by lowest ``(row, col)``. If the user answers
otherwise, exactly one expression changes here — :func:`squared_distance`
where :func:`starting_ghost` calls it — and one test changes with it.

Squared Euclidean is used rather than the square root of it because the two
order the candidates identically and the squared form is exact integer
arithmetic, so ties are ties and never a floating-point near-miss.

The player's move, in one sentence each
---------------------------------------

===========  ==============================================================
END-5        once the game has ended the arrow keys do nothing: the state
             comes back **unchanged**
CTRL-1       an arrow moves the player one square up, down, left or right
CTRL-2       one square per press and then a stop — this function moves
             exactly one square and holds no repeat, drift or momentum
             anywhere for a caller to wind up
CTRL-3       a press towards a wall does **nothing at all**: the very same
             state comes back, not a fresh one that happens to compare
             equal, and certainly not one with a changed score
SCORE-1      a dot on the square moved onto is eaten and gone from the
             state for the rest of the game
SCORE-2      each dot eaten adds exactly one to the score
SCORE-3      moving onto a square whose dot has already gone scores nothing
SCORE-5      nothing here ever subtracts from the score
END-1        walking onto the ghost's square loses the game
END-2        eating the last dot wins it
END-3        and **in that order** — see below
GAME-2       so the two ways a game ends are eating every dot and meeting
             the ghost, and there is no third
===========  ==============================================================

**END-3 is an ordering, not a special case.** "Eating the last dot on the
square the ghost is standing on is a loss, not a win: meeting the ghost is
decided first." In :func:`move_player` that is the ``if`` before the
``elif``: the collision test is evaluated first, so when both conditions hold
at once the game is :data:`Outcome.CAUGHT`. Swap those two branches and the
game silently starts *winning* that position. Nothing else in the function
would change, no other test would notice, and the board it goes wrong on is
rare. Both branches are kept adjacent and in that order for that reason, and
``tests/test_rules_player.py`` names a test after this requirement so that
the position is checked on purpose rather than by luck.
"""

import random
from typing import Callable, FrozenSet, Iterable, Tuple

from termgame import maze as mazelib
from termgame.model import (
    Direction,
    GameState,
    Maze,
    Outcome,
    Position,
)

__all__ = [
    "centre_of",
    "squared_distance",
    "starting_player",
    "starting_ghost",
    "starting_dots",
    "starting_heading",
    "starting_state",
    "new_game",
    "move_player",
]


# --------------------------------------------------------------------------
# Measuring across the grid
# --------------------------------------------------------------------------


def centre_of(maze: Maze) -> Position:
    """The middle square of ``maze``'s grid.

    For the real 29 x 19 board both axes are odd, so this is exactly
    ``(14, 9)`` — the true centre, with the same number of rows above it as
    below and the same number of columns either side. For a hand-written
    board with an even dimension there is no exact middle and this takes the
    higher of the two candidates.
    """
    return Position(maze.height // 2, maze.width // 2)


def squared_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Squared Euclidean distance between two squares, across the grid.

    Straight across the grid, ignoring the walls entirely — this is
    deliberately **not** distance along the corridors (START-2). Squared, so
    the arithmetic stays exact integers.
    """
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _nearest(
    corridors: Iterable[Position], score: Callable[[Position], int]
) -> Position:
    """The corridor square with the lowest ``score``, ties by lowest square.

    ``(score, row, col)`` is compared as a tuple, so the tie-break is "lowest
    row, then lowest column" and there is never a draw: no two squares share
    a ``(row, col)``.
    """
    candidates = tuple(corridors)
    if not candidates:
        raise ValueError("the maze has no corridor squares to start on")
    return min(candidates, key=lambda p: (score(p), p.row, p.col))


# --------------------------------------------------------------------------
# Where everything starts
# --------------------------------------------------------------------------


def starting_player(maze: Maze) -> Position:
    """Where the player begins — START-1.

    The corridor square **nearest the middle of the grid**, ties broken by
    lowest row and then lowest column.
    """
    centre = centre_of(maze)
    return _nearest(maze.corridors(), lambda p: squared_distance(p, centre))


def starting_ghost(maze: Maze, player: Tuple[int, int]) -> Position:
    """Where the ghost begins — START-2.

    The corridor square **furthest from the player** measured straight across
    the grid, ties broken by lowest row and then lowest column. Furthest is
    nearest to the negated distance, which is why this reads as ``-``: it is
    the one expression assumption A2 would change.
    """
    return _nearest(maze.corridors(), lambda p: -squared_distance(p, player))


def starting_dots(maze: Maze, player: Tuple[int, int]) -> FrozenSet[Position]:
    """Every corridor square holds a dot except the player's — START-3."""
    here = Position(player[0], player[1])
    return frozenset(p for p in maze.corridors() if p != here)


def starting_heading(
    maze: Maze, ghost: Tuple[int, int], rng: random.Random
) -> Direction:
    """A direction that is open from where the ghost stands.

    Drawn from the random source it is handed, so a seed reproduces the whole
    starting position and not merely the maze. The choice is over
    :meth:`Maze.open_directions`, which returns its answer in the canonical
    ``DIRECTIONS`` order, so the draw is reproducible.
    """
    options = maze.open_directions(ghost)
    if not options:
        raise ValueError(
            "the ghost's square %r has no way on, so it cannot face anywhere"
            % (Position(ghost[0], ghost[1]),)
        )
    return rng.choice(options)


def starting_state(maze: Maze, rng: random.Random) -> GameState:
    """A fresh game on the maze it is given.

    Split out from :func:`new_game` so that a test can hand in a board small
    enough to check by hand. The two placement rules live here; generating a
    maze is the only thing :func:`new_game` adds.
    """
    player = starting_player(maze)
    ghost = starting_ghost(maze, player)
    return GameState(
        maze=maze,
        player=player,
        ghost=ghost,
        ghost_dir=starting_heading(maze, ghost, rng),
        dots=starting_dots(maze, player),
        score=0,                    # START-4
        outcome=Outcome.PLAYING,    # START-4, and START-5: already under way
    )


def new_game(rng: random.Random) -> GameState:
    """A fresh game from a seeded random source, and nothing else — START-1..5.

    The maze is drawn from ``rng`` first and the ghost's heading from the same
    ``rng`` afterwards, so one seed fixes the entire starting position.

    There is no other parameter, and there is nothing to press: the game is
    under way the moment this returns (START-5).
    """
    return starting_state(mazelib.generate(rng), rng)


# --------------------------------------------------------------------------
# What a move does
# --------------------------------------------------------------------------


def move_player(state: GameState, direction: Direction) -> GameState:
    """The player presses one arrow key, once — CTRL-1..3, SCORE-1..3, END-1..3.

    A total function: every state and every direction has an answer, and it
    is always a :class:`GameState`. It reads no clock and draws no random
    number, so the same state and the same direction always give the same
    result.

    Three of the requirements are about *not* doing something, and each is
    one line here:

    * the game has already ended — the state comes back, the identical
      object, untouched (END-5);
    * the square ahead is wall, or off the grid entirely — likewise, the
      identical object (CTRL-3, "nothing at all"). Not a copy that compares
      equal: a caller that checks ``is`` must see nothing happened;
    * one square is moved and the function returns. There is no loop, so
      there is no way for a press to travel two squares (CTRL-2).

    Then the dot, and then the ending:

    * if the square moved onto still holds a dot, that dot is removed from
      ``dots`` for good and the score goes up by exactly one (SCORE-1,
      SCORE-2). If it does not, the score is carried across untouched
      (SCORE-3). The score is only ever added to (SCORE-5);
    * **the ghost's square is tested first, and the empty board second.**
      That order is END-3 and is the whole of it: eating the last dot while
      standing into the ghost is :data:`Outcome.CAUGHT`, never
      :data:`Outcome.CLEARED`. Do not reorder these two branches.
    """
    if state.outcome is not Outcome.PLAYING:
        return state                                    # END-5

    target = state.player.shifted(direction)
    if state.maze.is_wall(target):
        return state                                    # CTRL-3

    if target in state.dots:
        dots = state.dots - {target}                    # SCORE-1
        score = state.score + 1                         # SCORE-2
    else:
        dots = state.dots                               # SCORE-3
        score = state.score

    # END-3 lives in the next three lines, and in their order. Meeting the
    # ghost is decided first; the cleared board only gets a say if the ghost
    # is not standing where the player has just moved.
    if target == state.ghost:
        outcome = Outcome.CAUGHT                        # END-1
    elif not dots:
        outcome = Outcome.CLEARED                       # END-2
    else:
        outcome = Outcome.PLAYING

    return GameState(
        maze=state.maze,
        player=target,                                  # CTRL-1, CTRL-2
        ghost=state.ghost,
        ghost_dir=state.ghost_dir,
        dots=dots,
        score=score,
        outcome=outcome,
    )
