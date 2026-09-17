"""WI-9 — GHOST-2, GHOST-3 and GHOST-4.

Three requirements about one function, and each of them is awkward in its own
way:

* **GHOST-2** is easy to pass by accident. A policy that turned at random
  would still go straight sometimes, so the tests here take straight ahead
  away from the random source entirely — by running the same junction through
  a chooser that always takes the first candidate and one that always takes
  the last, and requiring the same answer from both.
* **GHOST-3**'s reverse clause **cannot happen in a real game** (ruling C-3):
  MAZE-5 forbids dead ends, so the non-reversing set is never empty. Its test
  therefore uses a hand-built dead end, and a second test walks a
  structurally sound maze five thousand steps to show the clause really is
  unreachable there.
* **GHOST-4** is met by the signature — the player is not a parameter — so it
  is pinned by an architecture guard on the signature rather than by trying
  to prove a negative about behaviour.

The maze's own structure is WI-1's and is not re-asserted here.
"""

from __future__ import annotations

import inspect
import random
from collections import Counter
from typing import Callable, List, Sequence, Set

import pytest

from terminal_game.domain.ghost import (
    GhostMove,
    candidate_directions,
    next_ghost_move,
)
from terminal_game.domain.maze import Direction, Maze, Position
from terminal_game.domain.structure import check, dead_ends

#: One fixed seed, so a failure is reproducible rather than occasional.
SEED = 20260917


class Chooser:
    """A stand-in for ``random.Random`` that picks by rule instead of chance.

    A seeded ``Random`` is the right tool for *"uniformly at random"*; this is
    the right tool for *"the random source was not what decided this"*, which
    is a different question and the one GHOST-2 turns on.
    """

    def __init__(self, pick: Callable[[Sequence[Direction]], Direction]) -> None:
        self._pick = pick
        self.offered = []  # type: List[List[Direction]]

    def choice(self, seq: Sequence[Direction]) -> Direction:
        self.offered.append(list(seq))
        return self._pick(seq)


def first_choice() -> Chooser:
    return Chooser(lambda seq: seq[0])


def last_choice() -> Chooser:
    return Chooser(lambda seq: seq[-1])


def corridors_at(*squares: Position) -> Maze:
    """An all-wall maze with exactly those squares carved.

    Used where a shape is easier to state as a handful of coordinates than as
    a picture — a junction is three or four squares and a picture of one is
    mostly blank.
    """
    return Maze.all_walls().with_corridors_at(squares)


#: A T-junction at (8, 10) opening north, south and west. Straight on to the
#: east is wall, so a ghost heading east has to choose.
T_JUNCTION = corridors_at(
    Position(8, 10), Position(8, 9), Position(8, 11), Position(7, 10)
)

#: A crossroads at (8, 10) with all four ways open.
CROSSROADS = corridors_at(
    Position(8, 10),
    Position(8, 9),
    Position(8, 11),
    Position(7, 10),
    Position(9, 10),
)

#: A corridor that stops dead at (8, 10). MAZE-5 forbids this shape; ruling
#: C-3 is that the reverse clause can only ever be seen in one.
DEAD_END = corridors_at(Position(8, 10), Position(7, 10), Position(6, 10))


# --------------------------------------------------------------------------
# GHOST-2 — straight on for as long as the corridor allows
# --------------------------------------------------------------------------


def test_a_straight_corridor_is_followed_without_deviation() -> None:
    """GHOST-2 over a run, not over one step.

    A policy that chose at random would go straight some of the time, so the
    consequence worth asserting is the whole walk: eight steps down a
    ten-square corridor and the ghost is at the far end still heading east.
    """
    maze = corridors_at(*[Position(x, 10) for x in range(4, 14)])
    square, heading = Position(4, 10), Direction.EAST
    rng = random.Random(SEED)

    walk = []  # type: List[Position]
    for _ in range(9):
        move = next_ghost_move(maze, square, heading, rng)
        square, heading = move.square, move.direction
        walk.append(square)

    assert walk == [Position(x, 10) for x in range(5, 14)]
    assert heading is Direction.EAST


def test_straight_ahead_is_not_the_random_sources_doing() -> None:
    """GHOST-2 at a crossroads, where every other way is available too.

    Run through a chooser that always takes the first candidate and one that
    always takes the last. Both give east, which they could not if the choice
    had gone through them at all — and neither was offered anything, which is
    the same fact seen from the other side.
    """
    for chooser in (first_choice(), last_choice()):
        move = next_ghost_move(
            CROSSROADS, Position(8, 10), Direction.EAST, chooser
        )
        assert move == GhostMove(Direction.EAST, Position(9, 10))
        assert chooser.offered == []


def test_straight_on_wins_even_where_the_ghost_could_turn() -> None:
    """GHOST-2 reads *"for as long as the corridor lets it"*, not "unless busy".

    At the crossroads all four ways are open; the ghost takes none of the
    three turns on offer, whichever way it is heading.
    """
    rng = random.Random(SEED)
    for heading, expected in (
        (Direction.NORTH, Position(8, 9)),
        (Direction.SOUTH, Position(8, 11)),
        (Direction.EAST, Position(9, 10)),
        (Direction.WEST, Position(7, 10)),
    ):
        move = next_ghost_move(CROSSROADS, Position(8, 10), heading, rng)
        assert move == GhostMove(heading, expected)


# --------------------------------------------------------------------------
# GHOST-3 — the choice at a junction
# --------------------------------------------------------------------------


def test_the_candidates_are_every_way_on_but_the_one_it_came_from() -> None:
    """GHOST-3's *"the other ways on"*, named.

    Heading east into the wall at the T-junction, the ghost came from the
    west, so west is excluded and north and south remain.
    """
    candidates = candidate_directions(T_JUNCTION, Position(8, 10), Direction.EAST)
    assert candidates == [Direction.NORTH, Direction.SOUTH]
    assert Direction.WEST not in candidates


def test_over_a_seeded_run_both_ways_are_taken_and_the_reverse_never_is() -> None:
    """GHOST-3's two halves at once: *"at random"* and *"only when there is no
    other choice"*.

    Four thousand draws at the same T-junction. North and south must both
    come up, west must never, and the split must be even enough to be called
    uniform — 2000 ± 300 is nine standard deviations wide, so it says
    something about the distribution without being fragile.
    """
    rng = random.Random(SEED)
    taken = Counter()  # type: Counter
    for _ in range(4000):
        move = next_ghost_move(T_JUNCTION, Position(8, 10), Direction.EAST, rng)
        taken[move.direction] += 1

    assert set(taken) == {Direction.NORTH, Direction.SOUTH}
    assert taken[Direction.WEST] == 0
    assert 1700 <= taken[Direction.NORTH] <= 2300
    assert 1700 <= taken[Direction.SOUTH] <= 2300
    assert taken[Direction.NORTH] + taken[Direction.SOUTH] == 4000


def test_the_move_lands_where_the_direction_says() -> None:
    """The square and the direction returned must agree with each other.

    Returning both is a convenience for the caller; it is only a convenience
    if they cannot disagree.
    """
    for chooser, expected in (
        (first_choice(), GhostMove(Direction.NORTH, Position(8, 9))),
        (last_choice(), GhostMove(Direction.SOUTH, Position(8, 11))),
    ):
        move = next_ghost_move(T_JUNCTION, Position(8, 10), Direction.EAST, chooser)
        assert move == expected
        assert move.square == Position(8, 10).step(move.direction)


def test_the_same_seed_walks_the_same_maze_twice(specimen) -> None:
    """The candidate order is part of the contract, not an accident.

    ``choice`` over a list is only repeatable if the list is; if candidates
    came out of a set or a dict in whatever order they happened to be in, the
    same seed would give a different walk and WI-16's seeded playthroughs
    would be worthless.
    """

    def walk(seed: int) -> List[Position]:
        square, heading = specimen.ghost, Direction.EAST
        rng = random.Random(seed)
        path = []  # type: List[Position]
        for _ in range(500):
            move = next_ghost_move(specimen.maze, square, heading, rng)
            square, heading = move.square, move.direction
            path.append(square)
        return path

    assert walk(SEED) == walk(SEED)
    assert walk(SEED) != walk(SEED + 1)


def test_candidates_come_in_direction_declaration_order() -> None:
    """What "repeatable order" means, stated so the next reader can rely on it.

    ``Direction`` is declared north, west, east, south, and the candidates
    come out in that order with the way it came from removed — here the ghost
    is heading south, so it came from the north.

    This calls the helper directly. In play the policy would never get here
    with south open: GHOST-2 would already have taken it, which is why a real
    game never sees three candidates.
    """
    assert candidate_directions(
        CROSSROADS, Position(8, 10), Direction.SOUTH
    ) == [Direction.WEST, Direction.EAST, Direction.SOUTH]


# --------------------------------------------------------------------------
# GHOST-3's reverse clause, and ruling C-3
# --------------------------------------------------------------------------


def test_at_a_dead_end_the_ghost_turns_back() -> None:
    """The last clause of GHOST-3, on the only shape that can reach it.

    MAZE-5 forbids this maze, so no generated game will ever produce it —
    which is exactly why the clause needs a hand-built one (ruling C-3).
    """
    chooser = first_choice()
    move = next_ghost_move(DEAD_END, Position(8, 10), Direction.EAST, chooser)

    assert move == GhostMove(Direction.WEST, Position(7, 10))
    assert chooser.offered == [], "a reversal is not a choice; nothing to pick from"


def test_the_hand_built_dead_end_really_is_one() -> None:
    """The guard on the test above: it must be testing the shape it claims.

    A maze that was accidentally sound would make the reversal test pass for
    the wrong reason, or not reach the clause at all.
    """
    assert check(DEAD_END).has_no_dead_ends is False
    # A three-square stub is a dead end at *both* ends; the test above walks
    # into the eastern one.
    assert set(dead_ends(DEAD_END)) == {Position(8, 10), Position(6, 10)}


def test_a_structurally_sound_maze_never_reaches_the_reverse_clause(specimen) -> None:
    """Ruling C-3, demonstrated rather than asserted.

    Five thousand steps around the specimen maze — which the structural
    checker says is sound: solid border, no dead ends, fully connected — and
    the ghost never once turns back the way it came. This is what the plan
    means by *"the clause is unreachable in any maze this game generates"*,
    and it is why nobody should be puzzled to find it uncovered by a
    generated-maze test.
    """
    assert check(specimen.maze).is_sound

    square, heading = specimen.ghost, Direction.EAST
    rng = random.Random(SEED)
    visited = set()  # type: Set[Position]
    for step in range(5000):
        came_from = heading.opposite()
        move = next_ghost_move(specimen.maze, square, heading, rng)
        assert move.direction is not came_from, (
            "reversed at {} on step {}, in a maze with no dead ends".format(
                square, step
            )
        )
        square, heading = move.square, move.direction
        visited.add(square)

    assert len(visited) > 100, "the ghost hardly moved; the walk proves little"


def test_a_junction_never_offers_more_than_two_ways_to_turn(specimen) -> None:
    """A consequence of the four-way grid, measured so that "uniform" is simple.

    Straight ahead must be blocked before a choice happens, which leaves at
    most three exits; one of those is the way the ghost came, so there are
    only ever one or two to pick between. Worth knowing: *"picks one of the
    other ways on at random"* is a coin flip and never anything richer.
    """
    widest = 0
    square, heading = specimen.ghost, Direction.EAST
    rng = random.Random(SEED)
    for _ in range(2000):
        if heading not in specimen.maze.ways_on_from(square):
            widest = max(
                widest,
                len(candidate_directions(specimen.maze, square, heading)),
            )
        move = next_ghost_move(specimen.maze, square, heading, rng)
        square, heading = move.square, move.direction

    assert widest == 2


# --------------------------------------------------------------------------
# GHOST-4 — the player is not a parameter
# --------------------------------------------------------------------------


def test_the_policy_takes_no_player_parameter() -> None:
    """GHOST-4, met by the signature rather than by behaviour.

    *"The ghost does not hunt the player and takes no notice of where they
    are."*  The strongest form of that is a function that could not read the
    player's position if it wanted to, and the only way to pin it is to look
    at what the function accepts. An architecture guard, not a duplicate of
    anything.
    """
    parameters = list(inspect.signature(next_ghost_move).parameters)
    assert parameters == ["maze", "square", "heading", "random_source"]
    assert not [name for name in parameters if "player" in name]


def test_the_same_inputs_always_give_the_same_move() -> None:
    """GHOST-4's other half: nothing outside the arguments can change the answer.

    Called a hundred times with the same maze, square, heading and a chooser
    that does not vary, the move is the same every time — so there is no
    hidden state, no clock and nothing about a player in play.
    """
    moves = {
        next_ghost_move(T_JUNCTION, Position(8, 10), Direction.EAST, first_choice())
        for _ in range(100)
    }
    assert moves == {GhostMove(Direction.NORTH, Position(8, 9))}


# --------------------------------------------------------------------------
# States that are not legal, and say so
# --------------------------------------------------------------------------


def test_a_ghost_standing_on_a_wall_is_refused() -> None:
    """A wall is not somewhere a ghost can be; silently walking on would hide it."""
    with pytest.raises(ValueError):
        next_ghost_move(
            T_JUNCTION, Position(0, 0), Direction.EAST, first_choice()
        )


def test_a_ghost_off_the_grid_is_refused() -> None:
    """MAZE-3: nothing leaves the maze, so nothing outside it is a position."""
    with pytest.raises(ValueError):
        next_ghost_move(
            T_JUNCTION, Position(-1, 10), Direction.EAST, first_choice()
        )


def test_a_corridor_square_with_no_way_on_at_all_is_refused() -> None:
    """MAZE-6 makes an isolated square impossible; it is a broken maze, not a rule."""
    isolated = corridors_at(Position(8, 10))
    with pytest.raises(ValueError):
        next_ghost_move(isolated, Position(8, 10), Direction.EAST, first_choice())


def test_a_random_source_that_answers_with_something_it_was_not_offered() -> None:
    """The one thing an injected dependency can do that the policy cannot check
    for in advance.

    A source that returns west at the T-junction would reverse the ghost in a
    maze where it had a choice — a GHOST-3 violation arriving from outside.
    Better a named error than a wrong move.
    """
    rogue = Chooser(lambda seq: Direction.WEST)
    with pytest.raises(ValueError):
        next_ghost_move(T_JUNCTION, Position(8, 10), Direction.EAST, rogue)
