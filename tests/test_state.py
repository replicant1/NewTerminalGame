"""The opening position and the game state — START-1 to START-4, SCORE-5.

Two of these need more than one maze to test honestly.

**START-1 has a parity trap in it.** The grid centre `(9, 14)` has an even
row, so on the carving lattice it is a *connector* rather than a cell, and it
is carved only when that wall happens to be opened — measured over 200 seeds,
109 times. An implementation that assumed the centre was walkable would pass
a single-seed test on roughly every other run. So START-1 is swept, and the
sweep asserts that **both** cases actually occurred, because a sweep that only
ever saw one of them would be no better than the single seed.

**START-2 has to be shown to use the right metric.** "Furthest measured across
the grid rather than along the corridors" is only testable on a maze where the
two answers differ, so there is one, and it differs loudly: the straight-line
answer is 16 steps' walk nearer than the walking answer.
"""

from __future__ import annotations

import collections
import random
from typing import Dict, List

import pytest

from terminal_game.domain.generation import generate
from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position
from terminal_game.domain.state import (
    CENTRE,
    GameState,
    Outcome,
    distance_squared,
    furthest_corridor_from,
    nearest_corridor_to,
    new_game,
)

#: Seeds for the START-1 sweep. Enough that both sides of the parity coin
#: toss are certain to appear; the sweep asserts that they did.
SEEDS = 120

#: The two squares one step above and below the centre. Both are cells on the
#: carving lattice, so both are corridor in every maze the generator makes.
ABOVE_CENTRE = Position(CENTRE.x, CENTRE.y - 1)
BELOW_CENTRE = Position(CENTRE.x, CENTRE.y + 1)

#: A maze whose straight-line furthest square and whose walking furthest
#: square are different squares, so a test can tell which metric was used.
#:
#: From the top-left corner two arms lead away. One runs straight east: only
#: 14 steps' walk, but it ends a long way off. The other goes the whole way
#: down the grid, across, and back up a parallel column that stops one square
#: short of rejoining — 36 steps' walk to end up almost back where it started.
DISAGREEING_ARMS = ["..............."] + ["."] + [". ."] * 16 + ["..."]
ARMS_AT = (2, 2)
ARMS_START = Position(2, 2)

#: Furthest as the crow flies — what START-2 asks for.
ARMS_STRAIGHT_LINE_FURTHEST = Position(4, 20)

#: Furthest along the corridors — what START-2 explicitly does *not* ask for.
ARMS_WALKING_FURTHEST = Position(4, 4)


@pytest.fixture(scope="module")
def many_games() -> Dict[int, GameState]:
    """One opening position per seed, built once."""
    return {seed: new_game(generate(random.Random(seed))) for seed in range(SEEDS)}


@pytest.fixture
def arms(draw) -> Maze:
    return draw("\n".join(DISAGREEING_ARMS), at=ARMS_AT)


def walking_distances(maze: Maze, start: Position) -> Dict[Position, int]:
    """How many steps each corridor square is from ``start`` along corridors.

    Only the tests need this. START-2 is explicitly not about it, which is
    exactly why a test has to be able to compute it: without it there is no
    way to show that the production code did something else.
    """
    distances = {start: 0}
    queue = collections.deque([start])
    while queue:
        position = queue.popleft()
        for neighbour in maze.corridor_neighbours(position):
            if neighbour not in distances:
                distances[neighbour] = distances[position] + 1
                queue.append(neighbour)
    return distances


# --------------------------------------------------------------------------
# Straight-line distance, which both START-1 and START-2 are measured in
# --------------------------------------------------------------------------


def test_distance_to_itself_is_nothing() -> None:
    assert distance_squared(Position(4, 9), Position(4, 9)) == 0


@pytest.mark.parametrize(
    "one,other,expected",
    [
        (Position(0, 0), Position(3, 0), 9),
        (Position(0, 0), Position(0, 4), 16),
        (Position(0, 0), Position(3, 4), 25),
        (Position(3, 4), Position(0, 0), 25),
    ],
)
def test_distance_is_the_square_of_the_straight_line(one, other, expected) -> None:
    """Squared, so it is an exact integer and ordering never turns on a float."""
    assert distance_squared(one, other) == expected


def test_distance_ignores_walls_entirely() -> None:
    """It is a distance across the grid, not through it.

    START-2 says *"measured across the grid rather than along the corridors"*,
    so a wall between two squares makes no difference to this number at all.
    """
    open_ground = Maze.all_walls().with_corridors_at(
        [Position(4, 4), Position(6, 4)]
    )
    assert open_ground.is_wall(Position(5, 4))
    assert distance_squared(Position(4, 4), Position(6, 4)) == 4


# --------------------------------------------------------------------------
# START-1 — the player on the corridor square nearest the middle
# --------------------------------------------------------------------------


def test_the_centre_of_the_grid_is_its_middle_square() -> None:
    assert CENTRE == Position(9, 14)
    assert CENTRE.x == WIDTH // 2
    assert CENTRE.y == HEIGHT // 2


def test_the_player_starts_on_the_centre_when_the_centre_is_corridor(draw) -> None:
    maze = draw("...", at=(CENTRE.x - 1, CENTRE.y))
    assert new_game(maze).player == CENTRE


def test_the_player_starts_on_the_nearest_corridor_when_the_centre_is_wall(draw) -> None:
    maze = draw(".", at=(CENTRE.x, CENTRE.y - 3))
    assert new_game(maze).player == Position(CENTRE.x, CENTRE.y - 3)


def test_the_player_always_starts_on_a_corridor_square(many_games) -> None:
    for seed, game in many_games.items():
        assert game.maze.is_corridor(game.player), "seed {}".format(seed)


def test_the_player_starts_on_the_centre_exactly_when_it_is_carved(many_games) -> None:
    """START-1's parity trap, swept.

    The centre is corridor in about half of real mazes. This asserts the rule
    that holds in both halves: if the centre is carved the player is on it,
    and if it is not, the player is on the nearest square that is.
    """
    for seed, game in many_games.items():
        expected = CENTRE if game.maze.is_corridor(CENTRE) else ABOVE_CENTRE
        assert game.player == expected, "seed {}".format(seed)


def test_the_sweep_actually_saw_both_halves_of_the_parity_coin_toss(many_games) -> None:
    """Otherwise the test above would be a single-seed test wearing a sweep.

    A sweep that happened to draw only mazes with a carved centre would pass
    while saying nothing at all about the other half.
    """
    on_centre = sum(1 for game in many_games.values() if game.player == CENTRE)
    assert 0 < on_centre < SEEDS


def test_the_player_never_starts_further_than_one_square_from_the_centre(many_games) -> None:
    """The two squares above and below the centre are always carved, so there
    is never a reason to start further away than that."""
    for seed, game in many_games.items():
        assert distance_squared(game.player, CENTRE) <= 1, "seed {}".format(seed)


def test_the_squares_above_and_below_the_centre_are_always_corridor(many_games) -> None:
    """Which is what makes the sentence above true. Both are cells on the
    carving lattice — odd column, odd row — and every cell is always carved."""
    for seed, game in many_games.items():
        assert game.maze.is_corridor(ABOVE_CENTRE), "seed {}".format(seed)
        assert game.maze.is_corridor(BELOW_CENTRE), "seed {}".format(seed)


def test_the_nearest_corridor_ties_are_broken_in_reading_order(draw) -> None:
    """Topmost, then leftmost. The tie above and below the centre is the one
    that fires in real games, so it is the one pinned here."""
    maze = draw(".\n \n.", at=(CENTRE.x, CENTRE.y - 1))
    assert maze.is_corridor(ABOVE_CENTRE)
    assert maze.is_corridor(BELOW_CENTRE)
    assert nearest_corridor_to(maze, CENTRE) == ABOVE_CENTRE


def test_a_tie_between_two_rows_is_broken_by_the_upper_row(draw) -> None:
    maze = Maze.all_walls().with_corridors_at(
        [Position(CENTRE.x + 1, CENTRE.y), BELOW_CENTRE]
    )
    assert nearest_corridor_to(maze, CENTRE) == Position(CENTRE.x + 1, CENTRE.y)


def test_a_maze_with_nowhere_to_stand_is_refused() -> None:
    with pytest.raises(ValueError):
        new_game(Maze.all_walls())


# --------------------------------------------------------------------------
# START-2 — the ghost furthest away, across the grid and not along it
# --------------------------------------------------------------------------


def test_the_two_metrics_really_do_disagree_on_this_maze(arms) -> None:
    """The fixture is only worth anything if it discriminates, so check it does.

    Without this, a later edit could quietly flatten the maze into one where
    both metrics agree, and the test below would keep passing while proving
    nothing.
    """
    walk = walking_distances(arms, ARMS_START)
    straight = {p: distance_squared(p, ARMS_START) for p in arms.corridors()}

    assert max(straight, key=lambda p: straight[p]) == ARMS_STRAIGHT_LINE_FURTHEST
    assert max(walk, key=lambda p: walk[p]) == ARMS_WALKING_FURTHEST
    assert ARMS_STRAIGHT_LINE_FURTHEST != ARMS_WALKING_FURTHEST


def test_the_ghost_starts_at_the_straight_line_furthest_square(arms) -> None:
    """START-2, on the maze where the wrong metric gives a visibly wrong answer."""
    assert furthest_corridor_from(arms, ARMS_START) == ARMS_STRAIGHT_LINE_FURTHEST


def test_the_ghost_does_not_start_at_the_walking_furthest_square(arms) -> None:
    """Said separately because it is the failure this fixture exists to catch.

    The walking furthest square is 36 steps away and almost on top of the
    player; the straight-line furthest is 20 steps away and across the grid.
    An implementation measuring along the corridors would put the ghost two
    squares from the player at the start of every game.
    """
    walk = walking_distances(arms, ARMS_START)
    chosen = furthest_corridor_from(arms, ARMS_START)

    assert chosen != ARMS_WALKING_FURTHEST
    assert walk[chosen] < walk[ARMS_WALKING_FURTHEST]


def test_the_ghost_starts_further_from_the_player_than_any_other_corridor(many_games) -> None:
    for seed, game in many_games.items():
        furthest = distance_squared(game.ghost, game.player)
        for corridor in game.maze.corridors():
            assert distance_squared(corridor, game.player) <= furthest, (
                "seed {}".format(seed)
            )


def test_the_ghost_always_starts_on_a_corridor_square(many_games) -> None:
    for seed, game in many_games.items():
        assert game.maze.is_corridor(game.ghost), "seed {}".format(seed)


def test_the_ghost_never_starts_on_top_of_the_player(many_games) -> None:
    """The game would be over before it began — END-1."""
    for seed, game in many_games.items():
        assert game.ghost != game.player, "seed {}".format(seed)


def test_the_furthest_corridor_ties_are_broken_in_reading_order() -> None:
    """Assumption P7: the tie is mine to break, so long as a test pins it."""
    maze = Maze.all_walls().with_corridors_at(
        [Position(1, 1), Position(17, 1), Position(1, 27)]
    )
    # From (1, 27): (17, 1) is 256 + 676 = 932 away; (1, 1) is 676 away.
    assert furthest_corridor_from(maze, Position(1, 27)) == Position(17, 1)
    # From (9, 14) both corners are equidistant, so reading order decides.
    tied = Maze.all_walls().with_corridors_at([Position(1, 1), Position(17, 27)])
    assert distance_squared(Position(1, 1), CENTRE) == distance_squared(
        Position(17, 27), CENTRE
    )
    assert furthest_corridor_from(tied, CENTRE) == Position(1, 1)


def test_a_maze_with_nowhere_to_put_the_ghost_is_refused() -> None:
    with pytest.raises(ValueError):
        furthest_corridor_from(Maze.all_walls(), CENTRE)


# --------------------------------------------------------------------------
# START-3 — a dot on every corridor square except the player's
# --------------------------------------------------------------------------


def test_every_corridor_square_holds_a_dot_except_the_players(many_games) -> None:
    for seed, game in many_games.items():
        expected = frozenset(game.maze.corridors()) - {game.player}
        assert game.dots == expected, "seed {}".format(seed)


def test_the_player_starts_on_an_empty_square(many_games) -> None:
    for seed, game in many_games.items():
        assert not game.has_dot_at(game.player), "seed {}".format(seed)


def test_the_ghost_starts_on_a_square_that_still_has_its_dot(many_games) -> None:
    """SCORE-4: *"a dot under the ghost is still there to be taken."*

    START-3 excepts the player's square and only the player's.
    """
    for seed, game in many_games.items():
        assert game.has_dot_at(game.ghost), "seed {}".format(seed)


def test_no_dot_is_ever_placed_on_a_wall(many_games) -> None:
    for seed, game in many_games.items():
        for dot in game.dots:
            assert game.maze.is_corridor(dot), "seed {}".format(seed)


def test_there_is_one_fewer_dot_than_there_are_corridor_squares(many_games) -> None:
    for seed, game in many_games.items():
        assert game.dots_remaining == len(game.maze.corridors()) - 1


# --------------------------------------------------------------------------
# START-4 — the score starts at zero and the game is undecided
# --------------------------------------------------------------------------


def test_the_score_starts_at_zero(many_games) -> None:
    assert {game.score for game in many_games.values()} == {0}


def test_a_new_game_is_undecided_and_not_over(many_games) -> None:
    for game in many_games.values():
        assert game.outcome is Outcome.UNDECIDED
        assert not game.is_over


# --------------------------------------------------------------------------
# The outcome vocabulary, which WI-10 sets and WI-12 renders
# --------------------------------------------------------------------------


def test_there_are_exactly_three_outcomes() -> None:
    assert set(Outcome) == {Outcome.UNDECIDED, Outcome.CAUGHT, Outcome.CLEARED}
    assert len(Outcome) == 3


@pytest.mark.parametrize("outcome", [Outcome.CAUGHT, Outcome.CLEARED])
def test_a_decided_game_is_over(arms, outcome) -> None:
    game = new_game(arms).decided(outcome)
    assert game.outcome is outcome
    assert game.is_over


def test_an_undecided_game_is_not_over(arms) -> None:
    assert not new_game(arms).decided(Outcome.UNDECIDED).is_over


# --------------------------------------------------------------------------
# SCORE-5 — the score offers no way to fall
# --------------------------------------------------------------------------


def test_eating_a_dot_adds_exactly_one(arms) -> None:
    game = new_game(arms)
    dot = sorted(game.dots)[0]
    assert game.ate_dot_at(dot).score == game.score + 1


def test_eating_a_dot_takes_it_off_the_board(arms) -> None:
    game = new_game(arms)
    dot = sorted(game.dots)[0]
    after = game.ate_dot_at(dot)

    assert not after.has_dot_at(dot)
    assert after.dots_remaining == game.dots_remaining - 1


def test_eating_a_square_with_no_dot_changes_nothing(arms) -> None:
    """SCORE-3, so that WI-10 may call this on every move without asking first."""
    game = new_game(arms)
    assert game.ate_dot_at(game.player) is game


def test_eating_the_same_dot_twice_scores_once(arms) -> None:
    game = new_game(arms)
    dot = sorted(game.dots)[0]
    once = game.ate_dot_at(dot)
    assert once.ate_dot_at(dot).score == once.score


def test_the_score_cannot_be_assigned_to(arms) -> None:
    """There is no setter, so "never goes down" has nothing to go through."""
    game = new_game(arms)
    with pytest.raises(AttributeError):
        game.score = 99  # type: ignore[misc]


def test_no_transition_lowers_the_score(arms) -> None:
    """The whole transition surface, applied to a game with a score on it.

    This is SCORE-5 as a consequence rather than as a claim about the code:
    whatever any of these does, the number does not fall.
    """
    game = new_game(arms)
    for dot in sorted(game.dots)[:5]:
        game = game.ate_dot_at(dot)
    assert game.score == 5

    somewhere = sorted(game.maze.corridors())[0]
    transitions = [
        game.with_player_at(somewhere),
        game.with_ghost_at(somewhere),
        game.ate_dot_at(somewhere),
        game.ate_dot_at(game.player),
        game.decided(Outcome.CAUGHT),
        game.decided(Outcome.CLEARED),
    ]
    for after in transitions:
        assert after.score >= game.score


def test_a_state_cannot_be_built_with_a_negative_score(arms) -> None:
    game = new_game(arms)
    with pytest.raises(ValueError):
        GameState(game.maze, game.dots, game.player, game.ghost, score=-1)


# --------------------------------------------------------------------------
# The state is immutable, and moving does only what it says
# --------------------------------------------------------------------------


def elsewhere(game: GameState) -> Position:
    """A corridor square that is neither the player's nor the ghost's.

    Needed because a "move" onto the square an actor already occupies is not
    a move, and a test that accidentally picks one proves nothing.
    """
    for corridor in game.maze.corridors():
        if corridor not in (game.player, game.ghost):
            return corridor
    raise AssertionError("this maze is too small to move anything about in")


def test_moving_the_player_leaves_the_old_state_alone(arms) -> None:
    game = new_game(arms)
    somewhere = elsewhere(game)
    moved = game.with_player_at(somewhere)

    assert moved.player == somewhere
    assert game.player != somewhere
    assert game.player == new_game(arms).player
    assert game.dots == moved.dots
    assert game.score == moved.score


def test_moving_the_player_does_not_eat_anything(arms) -> None:
    """SCORE-1 is WI-10's: this moves, and eating is a separate decision."""
    game = new_game(arms)
    dot = sorted(game.dots)[0]
    moved = game.with_player_at(dot)

    assert moved.has_dot_at(dot)
    assert moved.score == 0


def test_moving_the_ghost_never_touches_a_dot(arms) -> None:
    """SCORE-4: the ghost neither eats dots nor hides them."""
    game = new_game(arms)
    dot = sorted(game.dots)[0]
    moved = game.with_ghost_at(dot)

    assert moved.has_dot_at(dot)
    assert moved.dots == game.dots
    assert moved.score == game.score


def test_two_states_with_the_same_contents_are_equal(arms) -> None:
    one = new_game(arms)
    other = new_game(arms)
    assert one == other
    assert len({one, other}) == 1


def test_a_state_differs_once_anything_about_it_differs(arms) -> None:
    game = new_game(arms)
    somewhere = elsewhere(game)
    assert somewhere not in (game.player, game.ghost)
    assert game != game.with_player_at(somewhere)
    assert game != game.with_ghost_at(somewhere)
    assert game != game.ate_dot_at(sorted(game.dots)[0])
    assert game != game.decided(Outcome.CAUGHT)


def test_a_state_is_not_equal_to_something_that_is_not_a_state(arms) -> None:
    assert new_game(arms) != "a game"
