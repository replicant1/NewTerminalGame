"""WI-10: the frame composer (SCRN-1, SCRN-4, SCRN-5, MAZE-1, END-4, SCORE-4)."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import Optional

import pytest

import specimen
from terminal_game.domain.maze import Maze
from terminal_game.domain.maze_generator import generate_maze
from terminal_game.presentation import roles
from terminal_game.presentation.frame_composer import compose
from terminal_game.presentation.status_line import LOST, PLAYING, WON, status_row

#: From the plan's WI-4/C1 table, not from the code under test.
WALL_CHARACTERS = set("■═║╔╗╚╝╠╣╦╩╬")
BLANK = (" ", roles.BACKGROUND)


@dataclass(frozen=True)
class State:
    """The attributes the composer reads; WI-7's GameState has the same ones."""

    maze: Maze
    player: tuple
    ghost: tuple
    dots: frozenset
    score: int = 0
    outcome: Optional[str] = PLAYING


def _text(frame):
    return ["".join(character for character, _ in row) for row in frame]


# --------------------------------------------------------------------------
# The specimen, turned back into a state
# --------------------------------------------------------------------------


def _specimen_state():
    maze_rows = specimen.maze_rows()
    walls, dots, player, ghost = [], set(), None, None
    for r, line in enumerate(maze_rows):
        row = []
        for c in range(specimen.MAZE_WIDTH):
            ch = line[2 * c]
            row.append("#" if ch in WALL_CHARACTERS else ".")
            if ch == "▪":
                dots.add((c, r))
            if ch == "█":
                sprite = line[2 * c - 1:2 * c + 2]
                if sprite == "▐█▌":
                    player = (c, r)
                elif sprite == "▗█▖":
                    ghost = (c, r)
        walls.append("".join(row))
    return State(Maze.from_rows(walls), player, ghost, frozenset(dots), 0, PLAYING)


def test_the_specimen_reads_back_as_the_positions_it_shows():
    state = _specimen_state()
    assert (state.player, state.ghost) == ((10, 13), (1, 27))
    assert len(state.dots) == 264 - 2  # every corridor square but the player's and the ghost's


def test_c1_the_specimen_state_composes_to_the_specimen_character_for_character():
    got = _text(compose(_specimen_state()))
    want = [row.ljust(40) for row in specimen.rows()]
    assert len(got) == 30
    for r, (g, w) in enumerate(zip(got, want)):
        assert g == w, "row %d\n got %r\nwant %r" % (r, g, w)


# --------------------------------------------------------------------------
# Generated states for the structural claims
# --------------------------------------------------------------------------


def _generated(seed, score=0, outcome=PLAYING):
    maze = generate_maze(random.Random(seed))
    corridors = maze.corridor_squares()
    player, ghost = corridors[0], corridors[-1]
    dots = frozenset(sq for sq in corridors[::2] if sq != player)
    return State(maze, player, ghost, dots, score, outcome)


def _sprite_cells(state):
    cells = set()
    for col, row in (state.player, state.ghost):
        cells |= {(row, 2 * col - 1), (row, 2 * col), (row, 2 * col + 1)}
    return cells


SEEDS = range(50)


@pytest.mark.parametrize("score, outcome", [(0, PLAYING), (37, LOST), (274, WON), (459, PLAYING)])
def test_c2_the_frame_is_40_by_30_and_row_29_is_exactly_the_status_line(score, outcome):
    for seed in SEEDS:
        frame = compose(_generated(seed, score, outcome))
        assert len(frame) == 30 and all(len(row) == 40 for row in frame)
        assert frame[29] == status_row(score, outcome)


def test_c2_nothing_from_the_maze_reaches_row_29_even_with_both_on_the_bottom_corridor():
    maze = generate_maze(random.Random(1))
    bottom = [sq for sq in maze.corridor_squares() if sq[1] == 27]
    state = State(maze, bottom[0], bottom[-1], frozenset(bottom[1:-1]))
    assert compose(state)[29] == status_row(0, PLAYING)


def test_c3_square_n_is_cell_2n_its_joining_cell_is_2n_plus_1_and_cells_37_to_39_are_blank():
    for seed in SEEDS:
        state = _generated(seed)
        frame = compose(state)
        hidden = _sprite_cells(state)
        for r in range(29):
            for n in range(19):
                if (r, 2 * n) not in hidden:
                    assert (frame[r][2 * n][0] in WALL_CHARACTERS) == state.maze.is_wall((n, r)), (seed, r, n)
                if n < 18 and (r, 2 * n + 1) not in hidden:
                    both = state.maze.is_wall((n, r)) and state.maze.is_wall((n + 1, r))
                    assert frame[r][2 * n + 1] == (("═", roles.WALL) if both else BLANK), (seed, r, n)
            assert frame[r][37:] == [BLANK, BLANK, BLANK], (seed, r)


def test_c4_a_dotted_corridor_square_is_a_gold_dot_and_an_eaten_one_is_blank():
    for seed in SEEDS:
        state = _generated(seed)
        frame = compose(state)
        hidden = _sprite_cells(state)
        for col, row in state.maze.corridor_squares():
            if (row, 2 * col) in hidden:
                continue
            want = ("▪", roles.DOT) if (col, row) in state.dots else BLANK
            assert frame[row][2 * col] == want, (seed, col, row)


def _adjacent_corridor_pair(maze):
    for col, row in maze.corridor_squares():
        if maze.is_corridor((col + 1, row)):
            return (col, row), (col + 1, row)
    raise AssertionError("no horizontally adjacent corridor squares")


def test_c5_the_player_is_a_yellow_bar_block_bar_and_the_ghost_a_pink_quadrant_block_quadrant():
    state = _generated(3)
    frame = compose(state)
    (pc, pr), (gc, gr) = state.player, state.ghost
    assert frame[pr][2 * pc - 1:2 * pc + 2] == [("▐", roles.PLAYER), ("█", roles.PLAYER), ("▌", roles.PLAYER)]
    assert frame[gr][2 * gc - 1:2 * gc + 2] == [("▗", roles.GHOST), ("█", roles.GHOST), ("▖", roles.GHOST)]


def test_c6_on_the_same_square_the_ghost_is_drawn_and_the_player_cannot_be_seen():
    maze = generate_maze(random.Random(5))
    square = maze.corridor_squares()[40]
    frame = compose(State(maze, square, square, frozenset()))
    col, row = square
    assert frame[row][2 * col - 1:2 * col + 2] == [("▗", roles.GHOST), ("█", roles.GHOST), ("▖", roles.GHOST)]
    assert not any(role == roles.PLAYER for line in frame for _, role in line)


def test_c7_a_dot_under_the_ghost_is_hidden_and_drawn_again_once_it_moves_off():
    maze = generate_maze(random.Random(6))
    corridors = maze.corridor_squares()
    under, elsewhere, player = corridors[30], corridors[60], corridors[0]
    dots = frozenset({under})
    col, row = under
    on_it = compose(State(maze, player, under, dots))
    assert on_it[row][2 * col] == ("█", roles.GHOST)
    assert not any(role == roles.DOT for line in on_it for _, role in line)
    moved_off = compose(State(maze, player, elsewhere, dots))
    assert moved_off[row][2 * col] == ("▪", roles.DOT)


@pytest.mark.parametrize("player_on_the_left", [True, False])
def test_c8_side_by_side_both_centre_blocks_show_each_in_its_own_colour(player_on_the_left):
    maze = generate_maze(random.Random(7))
    left, right = _adjacent_corridor_pair(maze)
    player, ghost = (left, right) if player_on_the_left else (right, left)
    frame = compose(State(maze, player, ghost, frozenset()))
    assert frame[player[1]][2 * player[0]] == ("█", roles.PLAYER)
    assert frame[ghost[1]][2 * ghost[0]] == ("█", roles.GHOST)


def test_c9_every_cell_has_the_role_its_character_calls_for():
    for seed in SEEDS:
        state = _generated(seed, 12, PLAYING)
        frame = compose(state)
        hidden = _sprite_cells(state)
        for r, line in enumerate(frame[:29]):
            for c, (character, role) in enumerate(line):
                if (r, c) in hidden:
                    continue
                if character in WALL_CHARACTERS:
                    assert role == roles.WALL, (seed, r, c)
                elif character == "▪":
                    assert role == roles.DOT, (seed, r, c)
                else:
                    assert (character, role) == BLANK, (seed, r, c)
        assert {role for _, role in frame[29]} == {roles.STATUS}


def test_c9_a_blank_cell_in_the_status_row_is_in_the_status_role_as_wi5_gives_it():
    """The status row is WI-5's to colour; its blanks are status, not background."""
    frame = compose(_generated(0))
    assert frame[29][39] == (" ", roles.STATUS)


def test_c10_composing_changes_nothing_and_gives_the_same_frame_twice():
    maze = generate_maze(random.Random(9))
    corridors = maze.corridor_squares()
    dots = set(corridors[1:])  # a mutable set, so any change would show

    @dataclass
    class Mutable:
        maze: Maze
        player: tuple
        ghost: tuple
        dots: set
        score: int
        outcome: Optional[str]

    state = Mutable(maze, corridors[0], corridors[-1], dots, 5, PLAYING)
    before = copy.deepcopy(state)
    first, second = compose(state), compose(state)
    assert first == second
    assert state == before
    first[0][0] = ("X", roles.WALL)
    assert compose(state) == second, "frames share no rows the caller could alter"


@pytest.mark.parametrize("width, height", [(20, 29), (19, 30), (20, 30)])
def test_a1_a_maze_too_big_for_the_frame_is_refused(width, height):
    big = Maze.from_rows(["#" * width] * height)
    with pytest.raises(ValueError, match="up to 19 x 29 squares, not %d x %d" % (width, height)):
        compose(State(big, (1, 1), (1, 1), frozenset()))


def test_a1_a_shorter_maze_leaves_the_rows_below_it_blank():
    short = Maze.from_rows(["#####", "#...#", "#####"])
    frame = compose(State(short, (1, 1), (3, 1), frozenset({(2, 1)})))
    assert _text(frame)[:3] == ["╔═══════╗".ljust(40), "║▐█▌▪▗█▖║".ljust(40), "╚═══════╝".ljust(40)]
    assert all(row == [BLANK] * 40 for row in frame[3:29])
    assert frame[29] == status_row(0, PLAYING)


# --------------------------------------------------------------------------
# The seam with WI-7: the domain's own GameState, as new_game makes it
# --------------------------------------------------------------------------


def test_the_composer_reads_the_domains_game_state_as_it_reads_the_stand_in():
    from terminal_game.domain.game_setup import new_game

    for seed in range(20):
        game = new_game(generate_maze(random.Random(seed)))
        stand_in = State(game.maze, game.player, game.ghost, game.dots, game.score, game.outcome)
        frame = compose(game)
        assert frame == compose(stand_in), seed
        col, row = game.player
        assert frame[row][2 * col] == ("█", roles.PLAYER), seed
