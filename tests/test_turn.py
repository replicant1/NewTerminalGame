"""The turn resolver — CTRL-1/2/3, SCORE-1/2/3, END-1/2/3, GAME-2, MAZE-3.

**END-3 is the reason this file exists in the shape it does.** The plan's
section 1.6 names it as the project's single fragility: *"eating the last dot
on the square the ghost is standing on is a loss, not a win"* lived in the
order of two statements, and **both orderings end the game**, so a test that
observed "the game ended" would pass either way.

So the END-3 tests here are built on a board where the two orderings give
**different answers**, and they assert three consequences rather than one —
the outcome, the score, and whether the dot is still on the board — so that a
resolver with the win tested first fails on all three and says so loudly.

Alongside them is a control showing that ``CLEARED`` **is** reachable. Without
it, "the outcome is caught" could be satisfied by a resolver that never says
anything else.

Nothing here was checked by breaking working code. The boards are built to
discriminate; the production code was never altered to watch a test fail.
"""

from __future__ import annotations

import random
from typing import List

import pytest

from terminal_game.application.turn import (
    Intent,
    outcome_of,
    resolve_ghost_move,
    resolve_player_intent,
    resolve_player_move,
)
from terminal_game.domain.generation import generate
from terminal_game.domain.maze import Direction, Maze, Position
from terminal_game.domain.state import GameState, Outcome, new_game


def corridor(*squares: Position) -> Maze:
    """A maze that is wall everywhere except the squares named."""
    return Maze.all_walls().with_corridors_at(list(squares))


#: A three-square corridor used by most of the boards below.
WEST = Position(5, 5)
MIDDLE = Position(6, 5)
EAST = Position(7, 5)
ROW = corridor(WEST, MIDDLE, EAST)


def game(
    maze: Maze,
    player: Position,
    ghost: Position,
    dots: List[Position],
    score: int = 0,
    outcome: Outcome = Outcome.UNDECIDED,
) -> GameState:
    return GameState(maze, dots, player, ghost, score, outcome)


# --------------------------------------------------------------------------
# outcome_of — END-1, END-2 and END-3 as one total function
# --------------------------------------------------------------------------


def test_a_game_with_dots_left_and_no_collision_is_undecided() -> None:
    assert outcome_of(game(ROW, WEST, EAST, [MIDDLE])) is Outcome.UNDECIDED


def test_the_player_and_the_ghost_on_one_square_is_a_loss() -> None:
    """END-1."""
    assert outcome_of(game(ROW, MIDDLE, MIDDLE, [WEST])) is Outcome.CAUGHT


def test_no_dots_left_is_a_win() -> None:
    """END-2, GAME-2."""
    assert outcome_of(game(ROW, WEST, EAST, [])) is Outcome.CLEARED


def test_both_at_once_is_the_loss() -> None:
    """END-3, at the level where it is decided.

    No dots left *and* the player on the ghost's square. A function testing
    the win first would answer ``CLEARED``; this one cannot reach that branch.
    """
    assert outcome_of(game(ROW, MIDDLE, MIDDLE, [])) is Outcome.CAUGHT


def test_the_outcome_does_not_depend_on_how_the_state_was_reached() -> None:
    """It is a function of the state, which is what makes it unbreakable by
    reordering statements elsewhere — there are no statements elsewhere."""
    one = game(ROW, MIDDLE, MIDDLE, [], score=3)
    other = game(ROW, MIDDLE, MIDDLE, [], score=99, outcome=Outcome.CLEARED)
    assert outcome_of(one) is outcome_of(other) is Outcome.CAUGHT


# --------------------------------------------------------------------------
# END-3 through the resolver, on a board where the orderings disagree
# --------------------------------------------------------------------------
#
# The player is one step west of the ghost, and the ghost is standing on the
# last dot in the maze.  The player moves east, onto both.
#
#   resolver as written     : move, eat, read the outcome -> CAUGHT
#   resolver with win first : move, eat, "no dots left"   -> CLEARED
#
# Both end the game.  Only one of them is END-3.


@pytest.fixture
def last_dot_under_the_ghost() -> GameState:
    return game(ROW, player=WEST, ghost=MIDDLE, dots=[MIDDLE])


def test_eating_the_last_dot_on_the_ghosts_square_is_a_loss(
    last_dot_under_the_ghost,
) -> None:
    """END-3. The whole requirement, on the board that can tell the difference."""
    after = resolve_player_move(last_dot_under_the_ghost, Direction.EAST)

    assert after.outcome is Outcome.CAUGHT
    assert after.outcome is not Outcome.CLEARED


def test_that_board_really_would_read_as_a_win_if_the_win_were_tested_first(
    last_dot_under_the_ghost,
) -> None:
    """The test above is only worth anything if the board discriminates.

    This says so without touching the resolver: after the move, the state
    satisfies *both* end conditions at once. A resolver that asked "are there
    dots left?" before "are they on the same square?" would answer ``CLEARED``
    on exactly this state.
    """
    after = resolve_player_move(last_dot_under_the_ghost, Direction.EAST)

    assert after.player == after.ghost
    assert after.dots_remaining == 0


def test_the_last_dot_is_still_eaten_and_scored_on_that_fatal_step(
    last_dot_under_the_ghost,
) -> None:
    """SCORE-1 and SCORE-2 do not stop applying because the step was fatal.

    The player moved onto a square that still had a dot, so the dot is eaten
    and the score goes up. The game is lost all the same. Recorded as a test
    because STAT-3 puts the score on screen, so this is visible to a player.
    """
    after = resolve_player_move(last_dot_under_the_ghost, Direction.EAST)

    assert after.score == 1
    assert after.dots_remaining == 0


def test_eating_the_last_dot_away_from_the_ghost_is_a_win() -> None:
    """The control for END-3: ``CLEARED`` really is reachable.

    Without this, "the outcome is caught" would be satisfied by a resolver
    that never said anything else.
    """
    board = game(ROW, player=WEST, ghost=EAST, dots=[MIDDLE])
    after = resolve_player_move(board, Direction.EAST)

    assert after.outcome is Outcome.CLEARED
    assert after.score == 1


def test_walking_into_the_ghost_with_dots_left_is_a_loss() -> None:
    """END-1 on its own, so the loss is not an artefact of the dots running out."""
    board = game(ROW, player=WEST, ghost=MIDDLE, dots=[WEST, EAST])
    after = resolve_player_move(board, Direction.EAST)

    assert after.outcome is Outcome.CAUGHT
    assert after.dots_remaining == 2


# --------------------------------------------------------------------------
# CTRL-1 and CTRL-2 — one intent, exactly one square
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "direction,expected",
    [
        (Direction.EAST, Position(6, 5)),
        (Direction.WEST, Position(4, 5)),
        (Direction.NORTH, Position(5, 4)),
        (Direction.SOUTH, Position(5, 6)),
    ],
)
def test_a_move_goes_exactly_one_square_in_that_direction(direction, expected) -> None:
    open_ground = corridor(
        Position(4, 5), Position(5, 5), Position(6, 5), Position(5, 4), Position(5, 6)
    )
    board = game(open_ground, player=Position(5, 5), ghost=Position(4, 5), dots=[EAST])

    assert resolve_player_move(board, direction).player == expected


def test_the_player_stops_after_one_square_and_does_not_drift() -> None:
    """CTRL-2: resolving once moves once. Nothing carries into the next call."""
    long_row = corridor(*[Position(x, 5) for x in range(2, 12)])
    board = game(long_row, player=Position(2, 5), ghost=Position(11, 5), dots=[Position(9, 5)])

    once = resolve_player_move(board, Direction.EAST)
    assert once.player == Position(3, 5)

    twice = resolve_player_move(once, Direction.EAST)
    assert twice.player == Position(4, 5)


# --------------------------------------------------------------------------
# CTRL-3 — a blocked move changes nothing at all
# --------------------------------------------------------------------------


def test_a_move_into_a_wall_returns_the_very_same_state() -> None:
    """CTRL-3: *"a press towards a wall does nothing at all."*"""
    board = game(ROW, player=MIDDLE, ghost=EAST, dots=[WEST])
    assert resolve_player_move(board, Direction.NORTH) is board


def test_a_blocked_move_changes_neither_score_nor_dots_nor_outcome() -> None:
    """Said as consequences, because "nothing at all" is four separate claims."""
    board = game(ROW, player=MIDDLE, ghost=EAST, dots=[WEST], score=7)
    after = resolve_player_move(board, Direction.SOUTH)

    assert after.player == board.player
    assert after.score == 7
    assert after.dots == board.dots
    assert after.outcome is Outcome.UNDECIDED


def test_a_blocked_move_next_to_the_ghost_does_not_end_the_game() -> None:
    """The dangerous case: standing beside the ghost and pressing into a wall.

    A resolver that moved first and checked legality afterwards would have the
    player briefly on the ghost's square.
    """
    board = game(ROW, player=MIDDLE, ghost=EAST, dots=[WEST])
    after = resolve_player_move(board, Direction.NORTH)

    assert after.outcome is Outcome.UNDECIDED
    assert not after.is_over


# --------------------------------------------------------------------------
# MAZE-3 — a move at the grid edge cannot leave it
# --------------------------------------------------------------------------


def test_a_move_off_the_edge_of_the_grid_is_simply_not_a_way_on() -> None:
    """MAZE-3 is satisfied by there being no way on, not by handling an error.

    The square north of row 0 does not exist. The resolver never asks about
    it: it asks the maze which ways on the player has, and that square is not
    among them.
    """
    edge = corridor(Position(9, 0), Position(9, 1))
    board = game(edge, player=Position(9, 0), ghost=Position(9, 1), dots=[Position(9, 1)])

    assert resolve_player_move(board, Direction.NORTH) is board


def test_movement_never_wraps_around_the_grid() -> None:
    """A wrapped square is not adjacent, so it can never be a way on.

    MAZE-3: *"there are no tunnels through the sides."*
    """
    both_edges = corridor(Position(0, 14), Position(18, 14), Position(1, 14))
    board = game(
        both_edges, player=Position(0, 14), ghost=Position(18, 14), dots=[Position(18, 14)]
    )

    after = resolve_player_move(board, Direction.WEST)
    assert after is board
    assert after.player == Position(0, 14)


def test_the_border_ring_stops_the_player_in_a_real_maze() -> None:
    """In a generated maze the player can never even reach the edge.

    MAZE-3's solid border is what makes the grid's edge unreachable, so the
    bounds question never arises in play. Swept, because it is a claim about
    every maze rather than one.
    """
    for seed in range(25):
        maze = generate(random.Random(seed))
        for square in maze.corridors():
            assert 0 < square.x < maze.width - 1, "seed {}".format(seed)
            assert 0 < square.y < maze.height - 1, "seed {}".format(seed)
            # And therefore every way on from it also lands well inside.
            for onward in maze.ways_on_from(square).values():
                assert maze.contains(onward)
                assert maze.is_corridor(onward)


# --------------------------------------------------------------------------
# SCORE-1, SCORE-2, SCORE-3
# --------------------------------------------------------------------------


def test_moving_onto_a_dot_eats_it_and_it_stays_eaten() -> None:
    """SCORE-1: *"the dot disappears from the maze for the rest of the game."*"""
    board = game(ROW, player=WEST, ghost=EAST, dots=[MIDDLE, EAST])
    after = resolve_player_move(board, Direction.EAST)

    assert not after.has_dot_at(MIDDLE)
    back_again = resolve_player_move(
        resolve_player_move(after, Direction.WEST), Direction.EAST
    )
    assert not back_again.has_dot_at(MIDDLE)


def test_each_dot_eaten_adds_one_to_the_score() -> None:
    """SCORE-2."""
    long_row = corridor(*[Position(x, 5) for x in range(2, 9)])
    board = game(
        long_row,
        player=Position(2, 5),
        ghost=Position(8, 5),
        dots=[Position(3, 5), Position(4, 5), Position(5, 5)],
    )

    scores = []
    state = board
    for _ in range(3):
        state = resolve_player_move(state, Direction.EAST)
        scores.append(state.score)
    assert scores == [1, 2, 3]


def test_moving_onto_an_empty_square_scores_nothing() -> None:
    """SCORE-3."""
    board = game(ROW, player=WEST, ghost=EAST, dots=[EAST], score=4)
    after = resolve_player_move(board, Direction.EAST)

    assert after.score == 4
    assert after.player == MIDDLE


def test_walking_back_over_an_eaten_square_scores_nothing() -> None:
    """SCORE-3 the way it actually happens in play."""
    board = game(ROW, player=WEST, ghost=Position(9, 9), dots=[MIDDLE, EAST])
    once = resolve_player_move(board, Direction.EAST)
    back = resolve_player_move(once, Direction.WEST)
    again = resolve_player_move(back, Direction.EAST)

    assert once.score == 1
    assert again.score == 1


# --------------------------------------------------------------------------
# The ghost's arm of the turn
# --------------------------------------------------------------------------


def test_the_ghost_walking_into_the_player_is_a_loss() -> None:
    """END-1's other arm, *"whether the player walked into the ghost or the
    ghost walked into the player."*"""
    board = game(ROW, player=MIDDLE, ghost=EAST, dots=[WEST])
    after = resolve_ghost_move(board, MIDDLE)

    assert after.outcome is Outcome.CAUGHT
    assert after.ghost == MIDDLE


def test_the_same_function_decides_both_arms_of_end_one() -> None:
    """So the two arms cannot drift apart. Same board, same collision, reached
    from the two different directions."""
    by_player = resolve_player_move(
        game(ROW, player=WEST, ghost=MIDDLE, dots=[EAST]), Direction.EAST
    )
    by_ghost = resolve_ghost_move(
        game(ROW, player=MIDDLE, ghost=EAST, dots=[WEST]), MIDDLE
    )

    assert by_player.outcome is by_ghost.outcome is Outcome.CAUGHT


def test_the_ghost_moving_onto_a_dot_neither_eats_it_nor_scores() -> None:
    """SCORE-4: *"a dot under the ghost is still there to be taken."*"""
    board = game(ROW, player=WEST, ghost=EAST, dots=[MIDDLE], score=5)
    after = resolve_ghost_move(board, MIDDLE)

    assert after.has_dot_at(MIDDLE)
    assert after.dots_remaining == 1
    assert after.score == 5
    assert after.outcome is Outcome.UNDECIDED


def test_a_ghost_move_onto_a_wall_is_refused_as_a_fault_in_the_policy() -> None:
    board = game(ROW, player=WEST, ghost=MIDDLE, dots=[EAST])
    with pytest.raises(ValueError) as raised:
        resolve_ghost_move(board, Position(6, 6))
    assert "not a corridor square" in str(raised.value)


def test_a_ghost_move_off_the_grid_is_refused() -> None:
    board = game(ROW, player=WEST, ghost=MIDDLE, dots=[EAST])
    with pytest.raises(ValueError):
        resolve_ghost_move(board, Position(19, 5))


def test_the_ghost_can_move_onto_a_square_the_player_has_cleared() -> None:
    board = game(ROW, player=WEST, ghost=EAST, dots=[WEST])
    after = resolve_ghost_move(board, MIDDLE)

    assert after.ghost == MIDDLE
    assert after.outcome is Outcome.UNDECIDED


# --------------------------------------------------------------------------
# A decided game does not move (END-5's half that lives here)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("outcome", [Outcome.CAUGHT, Outcome.CLEARED])
def test_a_decided_game_ignores_a_player_move(outcome) -> None:
    board = game(ROW, player=WEST, ghost=EAST, dots=[MIDDLE], outcome=outcome)
    assert resolve_player_move(board, Direction.EAST) is board


@pytest.mark.parametrize("outcome", [Outcome.CAUGHT, Outcome.CLEARED])
def test_a_decided_game_ignores_a_ghost_move(outcome) -> None:
    board = game(ROW, player=WEST, ghost=EAST, dots=[MIDDLE], outcome=outcome)
    assert resolve_ghost_move(board, MIDDLE) is board


def test_a_decided_game_is_not_validated_before_being_ignored() -> None:
    """The guard comes first, so a finished game cannot be made to raise."""
    board = game(ROW, player=WEST, ghost=EAST, dots=[], outcome=Outcome.CLEARED)
    assert resolve_ghost_move(board, Position(0, 0)) is board


# --------------------------------------------------------------------------
# The intent vocabulary, which WI-11 and WI-13 share
# --------------------------------------------------------------------------


def test_there_are_five_intents() -> None:
    """Four arrow keys (CTRL-1) and ``q`` (CTRL-4). A key that means none of
    them produces no intent at all, which is CTRL-5 and WI-13's to express."""
    assert len(Intent) == 5


@pytest.mark.parametrize(
    "intent,direction",
    [
        (Intent.MOVE_NORTH, Direction.NORTH),
        (Intent.MOVE_SOUTH, Direction.SOUTH),
        (Intent.MOVE_EAST, Direction.EAST),
        (Intent.MOVE_WEST, Direction.WEST),
    ],
)
def test_each_move_intent_names_its_direction(intent, direction) -> None:
    assert intent.direction is direction
    assert intent.is_move


def test_the_four_move_intents_cover_the_four_directions() -> None:
    assert {i.direction for i in Intent if i.is_move} == set(Direction)


def test_quitting_is_not_a_move() -> None:
    assert Intent.QUIT.direction is None
    assert not Intent.QUIT.is_move


def test_resolving_a_move_intent_moves_the_player() -> None:
    board = game(ROW, player=WEST, ghost=EAST, dots=[MIDDLE])
    assert resolve_player_intent(board, Intent.MOVE_EAST).player == MIDDLE


def test_resolving_quit_leaves_the_game_untouched() -> None:
    """Leaving is the session's business (CTRL-4), not the resolver's."""
    board = game(ROW, player=WEST, ghost=EAST, dots=[MIDDLE])
    assert resolve_player_intent(board, Intent.QUIT) is board


# --------------------------------------------------------------------------
# A whole game, played out
# --------------------------------------------------------------------------


def test_a_game_can_be_played_from_the_opening_position_to_a_win() -> None:
    """GAME-2, end to end on a real generated maze.

    Walks the player over every corridor square by brute force and checks the
    game is won exactly when the last dot goes, with the score equal to the
    number of dots there were. The ghost is parked out of the way, because
    this is about the win and not about the chase.
    """
    maze = generate(random.Random(3))
    opening = new_game(maze)
    corridors = list(maze.corridors())
    parked = max(corridors, key=lambda p: (p.y, p.x))
    state = GameState(
        maze, opening.dots - {parked}, opening.player, parked, score=0
    )
    expected_score = state.dots_remaining

    # The ghost is scenery here, so the walk never steps onto it. Its square
    # holds no dot, so the win does not depend on visiting it.
    seen = {state.player, parked}
    stack = [state.player]
    while stack and not state.is_over:
        # Walk to an unvisited neighbour, or back off along the path.
        here = state.player
        onward = [p for p in maze.corridor_neighbours(here) if p not in seen]
        if onward:
            target = onward[0]
            seen.add(target)
            stack.append(target)
        else:
            stack.pop()
            if not stack:
                break
            target = stack[-1]
        direction = next(
            d for d, square in maze.ways_on_from(here).items() if square == target
        )
        state = resolve_player_move(state, direction)

    assert state.outcome is Outcome.CLEARED
    assert state.dots_remaining == 0
    assert state.score == expected_score
