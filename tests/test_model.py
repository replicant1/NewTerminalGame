"""The shared value vocabulary — GAME-1, GAME-3, and the picture type."""

import dataclasses
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from termgame import maze as mazelib  # noqa: E402
from termgame.model import (  # noqa: E402
    DIRECTIONS,
    DIRECTION_BY_NAME,
    DOWN,
    GAME_STATE_FIELDS,
    LEFT,
    MAZE_COLS,
    MAZE_ROWS,
    RIGHT,
    SCREEN_COLS,
    SCREEN_ROWS,
    STYLE_DEFAULT,
    UP,
    Cell,
    Direction,
    Frame,
    FrameBuilder,
    GameState,
    Maze,
    Outcome,
    Position,
    frame_from_rows,
)

# A three-corridor plus-shape with a solid border, small enough to reason
# about by hand.
TINY = """\
#####
##.##
#...#
##.##
#####"""


def tiny_state():
    maze = mazelib.from_text(TINY)
    return GameState(
        maze=maze,
        player=Position(2, 2),
        ghost=Position(1, 2),
        ghost_dir=UP,
        dots=frozenset({Position(2, 1), Position(2, 3), Position(3, 2)}),
        score=0,
        outcome=Outcome.PLAYING,
    )


class TestPosition(unittest.TestCase):
    def test_a_position_is_a_plain_row_col_tuple(self):
        # Other work items may write (r, c) or Position(r, c); both must be
        # the same value, or a dots frozenset built one way stops answering
        # questions asked the other way.
        self.assertEqual(Position(3, 4), (3, 4))
        self.assertEqual(hash(Position(3, 4)), hash((3, 4)))
        self.assertIn((3, 4), frozenset({Position(3, 4)}))
        self.assertEqual(Position(3, 4).row, 3)
        self.assertEqual(Position(3, 4).col, 4)

    def test_shifted_moves_one_square(self):
        self.assertEqual(Position(5, 5).shifted(UP), Position(4, 5))
        self.assertEqual(Position(5, 5).shifted(DOWN), Position(6, 5))
        self.assertEqual(Position(5, 5).shifted(LEFT), Position(5, 4))
        self.assertEqual(Position(5, 5).shifted(RIGHT), Position(5, 6))


class TestDirection(unittest.TestCase):
    def test_the_four_directions_carry_their_deltas(self):
        self.assertEqual((UP.dr, UP.dc), (-1, 0))
        self.assertEqual((DOWN.dr, DOWN.dc), (1, 0))
        self.assertEqual((LEFT.dr, LEFT.dc), (0, -1))
        self.assertEqual((RIGHT.dr, RIGHT.dc), (0, 1))

    def test_directions_is_a_fixed_order(self):
        # A seeded choice over open directions is only reproducible if this
        # order never changes. WI-7's ghost depends on it.
        self.assertEqual(DIRECTIONS, (UP, DOWN, LEFT, RIGHT))

    def test_opposite_undoes_the_step(self):
        for direction in DIRECTIONS:
            back = direction.opposite()
            self.assertEqual(
                Position(9, 9).shifted(direction).shifted(back), Position(9, 9)
            )
            self.assertIsNot(back, direction)

    def test_a_direction_is_frozen(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            UP.dr = 99

    def test_lookup_by_name(self):
        self.assertIs(DIRECTION_BY_NAME["LEFT"], LEFT)


class TestOutcome(unittest.TestCase):
    def test_there_are_exactly_three_outcomes(self):
        self.assertEqual(
            [o.name for o in Outcome], ["PLAYING", "CAUGHT", "CLEARED"]
        )


class TestMazeValue(unittest.TestCase):
    def test_a_maze_is_frozen(self):
        maze = mazelib.from_text(TINY)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            maze.cells = ()

    def test_two_mazes_with_the_same_cells_are_equal_and_hash_alike(self):
        a = mazelib.from_text(TINY)
        b = mazelib.from_text(TINY)
        self.assertEqual(a, b)
        self.assertEqual(len({a, b}), 1)

    def test_a_ragged_grid_is_refused(self):
        with self.assertRaises(ValueError):
            Maze(((True, True), (True,)))

    def test_shape_is_reported(self):
        maze = mazelib.from_text(TINY)
        self.assertEqual((maze.height, maze.width), (5, 5))


class TestNeighbourQuery(unittest.TestCase):
    """The one non-obvious obligation: WI-6 and WI-7 both ask this."""

    def setUp(self):
        self.maze = mazelib.from_text(TINY)

    def test_is_corridor_and_is_wall_agree_with_the_written_board(self):
        for row, line in enumerate(TINY.split("\n")):
            for col, ch in enumerate(line):
                expected = ch == "."
                self.assertEqual(
                    self.maze.is_corridor((row, col)),
                    expected,
                    "cell (%d, %d) is %r" % (row, col, ch),
                )
                self.assertEqual(self.maze.is_wall((row, col)), not expected)

    def test_off_the_grid_is_wall_not_an_error(self):
        # Callers must never need a bounds check of their own.
        self.assertFalse(self.maze.is_corridor((-1, 2)))
        self.assertFalse(self.maze.is_corridor((2, 99)))
        self.assertTrue(self.maze.is_wall((-1, -1)))
        self.assertEqual(self.maze.open_directions((-5, -5)), ())

    def test_open_directions_agrees_with_a_naive_recount(self):
        lines = TINY.split("\n")

        def naively_open(row, col):
            found = []
            for direction in DIRECTIONS:
                nr, nc = row + direction.dr, col + direction.dc
                if 0 <= nr < len(lines) and 0 <= nc < len(lines[0]):
                    if lines[nr][nc] == ".":
                        found.append(direction)
            return tuple(found)

        for row in range(len(lines)):
            for col in range(len(lines[0])):
                if lines[row][col] != ".":
                    continue
                self.assertEqual(
                    self.maze.open_directions((row, col)),
                    naively_open(row, col),
                    "at (%d, %d)" % (row, col),
                )

    def test_the_centre_of_the_plus_has_all_four_ways_on(self):
        self.assertEqual(
            self.maze.open_directions((2, 2)), (UP, DOWN, LEFT, RIGHT)
        )
        self.assertEqual(self.maze.corridor_degree((2, 2)), 4)

    def test_a_tip_of_the_plus_has_exactly_one_way_on(self):
        self.assertEqual(self.maze.open_directions((1, 2)), (DOWN,))
        self.assertEqual(self.maze.corridor_degree((1, 2)), 1)

    def test_open_neighbours_are_the_positions_those_directions_reach(self):
        self.assertEqual(
            self.maze.open_neighbours((2, 2)),
            (Position(1, 2), Position(3, 2), Position(2, 1), Position(2, 3)),
        )

    def test_is_open_answers_one_direction_at_a_time(self):
        self.assertTrue(self.maze.is_open((2, 2), UP))
        self.assertFalse(self.maze.is_open((1, 2), UP))
        self.assertFalse(self.maze.is_open((0, 0), RIGHT))

    def test_open_directions_is_returned_in_directions_order(self):
        # Not merely "the same set": a seeded rng.choice over this tuple has
        # to land on the same direction on every run.
        for cell in sorted(self.maze.corridors()):
            found = self.maze.open_directions(cell)
            self.assertEqual(
                list(found), [d for d in DIRECTIONS if d in found], "at %r" % (cell,)
            )

    def test_corridors_is_every_corridor_cell(self):
        self.assertEqual(
            self.maze.corridors(),
            frozenset(
                {
                    Position(1, 2),
                    Position(2, 1),
                    Position(2, 2),
                    Position(2, 3),
                    Position(3, 2),
                }
            ),
        )

    def test_rows_round_trips_through_the_loader(self):
        self.assertEqual(mazelib.from_text("\n".join(self.maze.rows())), self.maze)


class TestGameState(unittest.TestCase):
    def test_the_state_carries_a_player_a_ghost_dots_and_a_maze(self):
        # GAME-1.
        state = tiny_state()
        self.assertEqual(state.player, Position(2, 2))
        self.assertEqual(state.ghost, Position(1, 2))
        self.assertEqual(len(state.dots), 3)
        self.assertTrue(state.maze.is_corridor(state.player))

    def test_game_3_holds_by_there_being_nothing_there(self):
        # There is no lives field, no level, no timer, no power-up, no pause
        # and no restart, and nothing may add one.
        self.assertEqual(
            GAME_STATE_FIELDS,
            ("maze", "player", "ghost", "ghost_dir", "dots", "score", "outcome"),
        )

    def test_the_state_is_frozen(self):
        state = tiny_state()
        for name, value in (
            ("score", 1),
            ("player", Position(0, 0)),
            ("outcome", Outcome.CAUGHT),
            ("dots", frozenset()),
        ):
            with self.assertRaises(dataclasses.FrozenInstanceError):
                setattr(state, name, value)

    def test_a_transition_returns_a_new_state_and_leaves_the_old_one_alone(self):
        state = tiny_state()
        moved = dataclasses.replace(state, player=Position(2, 3), score=1)
        self.assertEqual(moved.player, Position(2, 3))
        self.assertEqual(moved.score, 1)
        self.assertEqual(state.player, Position(2, 2))
        self.assertEqual(state.score, 0)

    def test_dots_are_positions_however_they_were_handed_in(self):
        state = dataclasses.replace(tiny_state(), dots=frozenset({(2, 1), (2, 3)}))
        self.assertEqual(state.dots, frozenset({Position(2, 1), Position(2, 3)}))
        self.assertIn(Position(2, 1), state.dots)

    def test_the_state_is_hashable(self):
        self.assertEqual(len({tiny_state(), tiny_state()}), 1)


class TestFrame(unittest.TestCase):
    def test_the_default_picture_is_thirty_rows_of_forty_columns(self):
        frame = FrameBuilder().build()
        self.assertEqual((SCREEN_ROWS, SCREEN_COLS), (30, 40))
        self.assertEqual(frame.height, 30)
        self.assertEqual(frame.width, 40)
        self.assertEqual(len(frame.rows()), 30)
        self.assertEqual(set(len(r) for r in frame.rows()), {40})

    def test_a_frame_reads_back_as_plain_strings(self):
        builder = FrameBuilder(height=2, width=5)
        builder.put_text(0, 0, "ab", style="wall")
        builder.put(1, 4, "z", style="dot")
        frame = builder.build()
        self.assertEqual(frame.rows(), ("ab   ", "    z"))
        self.assertEqual(frame.text(), "ab   \n    z")

    def test_a_frame_carries_a_style_identifier_per_cell(self):
        frame = FrameBuilder(height=1, width=3).put(0, 1, "X", "player").build()
        self.assertEqual(frame.cell(0, 1), Cell("X", "player"))
        self.assertEqual(frame.char_at(0, 1), "X")
        self.assertEqual(frame.style_at(0, 1), "player")
        self.assertEqual(frame.style_at(0, 0), STYLE_DEFAULT)
        self.assertEqual(frame.styles(), ((STYLE_DEFAULT, "player", STYLE_DEFAULT),))

    def test_a_frame_is_frozen(self):
        frame = FrameBuilder(height=1, width=1).build()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            frame.cells = ()

    def test_equal_frames_compare_equal(self):
        self.assertEqual(
            FrameBuilder(height=1, width=2).put(0, 0, "a").build(),
            FrameBuilder(height=1, width=2).put(0, 0, "a").build(),
        )
        self.assertNotEqual(
            FrameBuilder(height=1, width=2).put(0, 0, "a", "wall").build(),
            FrameBuilder(height=1, width=2).put(0, 0, "a", "dot").build(),
        )

    def test_a_cell_holds_exactly_one_character(self):
        with self.assertRaises(ValueError):
            Frame(((Cell("ab", STYLE_DEFAULT),),))
        with self.assertRaises(ValueError):
            FrameBuilder(height=1, width=2).put(0, 0, "ab")

    def test_writing_off_the_frame_raises_rather_than_clipping(self):
        builder = FrameBuilder(height=2, width=4)
        with self.assertRaises(IndexError):
            builder.put(2, 0, "x")
        with self.assertRaises(IndexError):
            builder.put(0, 4, "x")
        with self.assertRaises(IndexError):
            builder.put_text(0, 2, "xyz")
        # and nothing was half-written
        self.assertEqual(builder.build().rows(), ("    ", "    "))

    def test_three_wide_entity_spills_into_both_joiner_columns(self):
        # The player is drawn as three characters centred on an even column.
        # WI-3 relies on being able to do that in one call.
        frame = FrameBuilder(height=1, width=7).put_text(0, 1, "▐█▌", "player").build()
        self.assertEqual(frame.rows(), (" ▐█▌   ",))
        self.assertEqual(
            frame.styles()[0][1:4], ("player", "player", "player")
        )

    def test_frame_from_rows_builds_a_picture_from_text(self):
        frame = frame_from_rows(["ab", "cd"], style="wall")
        self.assertEqual(frame.rows(), ("ab", "cd"))
        self.assertEqual(frame.style_at(1, 1), "wall")

    def test_frame_from_rows_can_carry_a_style_grid(self):
        frame = frame_from_rows(["ab"], styles=[["wall", "dot"]])
        self.assertEqual(frame.styles(), (("wall", "dot"),))

    def test_a_ragged_picture_is_refused(self):
        with self.assertRaises(ValueError):
            frame_from_rows(["abc", "de"])


class TestGeometryConstants(unittest.TestCase):
    def test_the_maze_is_twenty_nine_deep_and_nineteen_across(self):
        self.assertEqual((MAZE_ROWS, MAZE_COLS), (29, 19))

    def test_the_window_is_thirty_rows_of_forty_columns(self):
        self.assertEqual((SCREEN_ROWS, SCREEN_COLS), (30, 40))

    def test_the_maze_leaves_a_blank_margin_down_the_right_hand_edge(self):
        # MAZE-1: maze column c occupies screen column 2c, so the maze ends
        # at screen column 36 and columns 37..39 are the margin.
        self.assertEqual(SCREEN_COLS - (2 * (MAZE_COLS - 1) + 1), 3)


if __name__ == "__main__":
    unittest.main()
