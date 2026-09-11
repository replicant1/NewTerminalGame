"""The real game, played to a finish — WI-9.

Every other file in this suite tests one layer. This one tests that the
layers are **wired to each other**: the real loop, driven by a fake screen and
a fake clock, calling the real ``rules.move_player``, the real
``rules.move_ghost`` and the real ``view.render``. Nothing here is a stand-in
and nothing here is a stub; the only fakes are the screen and the clock, and
they are fakes because a test cannot press a key or wait a seventh of a
second.

What that buys is that a requirement can be asserted *of the running game*
rather than of one function. A game is played to a win, a game is played to a
loss twice over — once because the player walked into the ghost and once
because the ghost walked into the player — and then, after each ending, the
keys and the ticks keep coming and nothing changes.

The boards are hand-written, small, and chosen so that the answer is obvious
by reading them. They deliberately break rules that only ever bind a
*generated* maze: the win board has two disconnected halves (MAZE-6 is a
promise about ``maze.generate``, not about ``maze.from_text``), which is what
lets the ghost roam for real while the player finishes the board in peace. A
scripted game in which the ghost's every step had to be predicted to avoid an
accidental collision would be a test of arithmetic, not of wiring.
"""

import contextlib
import io
import random
import unittest

from termgame import loop, maze as mazelib, rules, theme, view
from termgame.model import (
    MAZE_COLS,
    MAZE_ROWS,
    SCREEN_COLS,
    SCREEN_ROWS,
    GameState,
    Outcome,
    LEFT,
    Position,
    RIGHT,
)
from termgame.controls import KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_UP

QUIT = ord("q")


# --------------------------------------------------------------------------
# The two fakes
# --------------------------------------------------------------------------


class FakeClock(object):
    """Seconds, as a number the screen moves on."""

    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeScreen(object):
    """Hands out scripted keys and keeps every picture it was painted.

    Reading a key advances the clock by the whole of the timeout, which is
    what a real ``getch`` that times out does, so a scripted ``None`` is
    exactly one tick of waiting. A ``(key, seconds)`` pair is a key that
    arrived early.
    """

    def __init__(self, keys, clock):
        self.script = list(keys)
        self.clock = clock
        self.pictures = []
        self.reads = 0

    def paint(self, frame):
        self.pictures.append(frame)

    def read_key(self, timeout_ms):
        self.reads += 1
        if not self.script:
            raise AssertionError(
                "the loop read past the end of the script after %d reads; "
                "it should have returned on the q" % self.reads
            )
        item = self.script.pop(0)
        if isinstance(item, tuple):
            key, elapsed = item
        else:
            key, elapsed = item, timeout_ms / 1000.0
        self.clock.advance(elapsed)
        return key


class Played(object):
    """What one scripted game did: the final state, and every state painted."""

    def __init__(self, final, states, screen):
        self.final = final
        self.states = states          # one per paint, in order
        self.screen = screen

    def status_lines(self):
        return [picture.rows()[-1].rstrip() for picture in self.screen.pictures]

    def outcomes(self):
        return [state.outcome for state in self.states]


def play(board, keys, player, ghost, dots, ghost_dir=RIGHT, tick=1.0, seed=0):
    """Play a scripted game through the real loop and the real rules."""
    maze = mazelib.from_text(board)
    state = GameState(
        maze=maze,
        player=Position(*player),
        ghost=Position(*ghost),
        ghost_dir=ghost_dir,
        dots=frozenset(Position(*d) for d in dots),
        score=0,
        outcome=Outcome.PLAYING,
    )
    clock = FakeClock(0.0)
    screen = FakeScreen(keys, clock)
    states = []

    def recording_render(painted):
        # The real renderer, plus a note of the state it was handed. Keeping
        # the state objects themselves is what lets END-5 be asserted by
        # identity rather than by equality.
        states.append(painted)
        return view.render(painted)

    final = loop.run_loop(
        screen,
        state,
        recording_render,
        rules.move_player,
        rules.move_ghost,
        random.Random(seed),
        clock=clock,
        tick=tick,
    )
    return Played(final, states, screen)


# --------------------------------------------------------------------------
# The boards
# --------------------------------------------------------------------------

#: Two corridors with a wall between them. The player clears the left half;
#: the ghost bounces up and down the right half for real, and cannot reach
#: the player. Disconnected on purpose — see the module docstring.
WIN_BOARD = "\n".join(
    [
        "#########",
        "#...#...#",
        "#########",
    ]
)

#: One corridor. Whoever walks first meets the other.
CORRIDOR = "\n".join(
    [
        "#######",
        "#.....#",
        "#######",
    ]
)


# --------------------------------------------------------------------------
# A game played to a win
# --------------------------------------------------------------------------


class AGamePlayedToAWinTest(unittest.TestCase):
    """END-2, SCORE-1..3, CTRL-1, STAT-3, and the wiring that carries them.

    The player stands at (1, 1) with dots at (1, 2) and (1, 3). Two presses
    of the right arrow eat both, and the board is clear. The ghost is loose
    in the other half of the board throughout — it really moves, on the real
    ticks, through the real ``rules.move_ghost``.
    """

    def setUp(self):
        # right, right, then four idle ticks and a q against the won game.
        self.played = play(
            WIN_BOARD,
            [KEY_RIGHT, KEY_RIGHT] + [None] * 4 + [QUIT],
            player=(1, 1),
            ghost=(1, 5),
            dots=[(1, 2), (1, 3)],
        )

    def test_the_game_was_won(self):
        self.assertEqual(Outcome.CLEARED, self.played.final.outcome)

    def test_every_dot_was_eaten_and_each_scored_exactly_one(self):
        self.assertEqual(frozenset(), self.played.final.dots)
        self.assertEqual(2, self.played.final.score)

    def test_the_player_walked_the_two_squares_it_was_sent(self):
        self.assertEqual(Position(1, 3), self.played.final.player)

    def test_the_status_line_says_which_ending_and_the_final_score(self):
        # STAT-3, off the real picture rather than off theme.status_text.
        self.assertEqual(
            " CLEARED  score 2  q quits", self.played.status_lines()[-1]
        )

    def test_the_status_line_kept_the_score_up_to_date_while_playing(self):
        # STAT-2. The first picture is the starting position, then one per
        # turn: after the first press, after the second, then the idle ticks.
        self.assertEqual(
            [
                " score 0    arrows, q quits",
                " score 1    arrows, q quits",
            ],
            self.played.status_lines()[:2],
        )

    def test_the_ghost_really_moved_on_the_ticks(self):
        # GHOST-1 end to end: the player pressed two keys and then stopped,
        # and the ghost went on moving anyway. Its square must have changed
        # at least once across the run, and it must have stayed on corridor.
        squares = [state.ghost for state in self.played.states]
        self.assertGreater(
            len(set(squares)),
            1,
            "the ghost never moved across %d painted frames" % len(squares),
        )
        maze = self.played.final.maze
        for square in squares:
            self.assertTrue(maze.is_corridor(square), square)

    def test_the_ghost_never_reached_the_player(self):
        # The wall at (1, 4) is what keeps this test about the ending it is
        # named for. If it ever fails, the board has stopped being two halves.
        self.assertNotIn(Position(1, 4), self.played.final.maze.corridors())

    def test_the_picture_is_the_size_of_the_window_throughout(self):
        for picture in self.played.screen.pictures:
            self.assertEqual(SCREEN_ROWS, picture.height)
            self.assertEqual(SCREEN_COLS, picture.width)


# --------------------------------------------------------------------------
# A game played to a loss, twice over
# --------------------------------------------------------------------------


class AGameLostByWalkingIntoTheGhostTest(unittest.TestCase):
    """END-1, the player's half: they walked into it.

    Three dots ahead and the ghost on the third square. The board is not
    cleared by the last press — a dot is left at (1, 4) — so this is END-1
    plainly and not the END-3 ordering case, which is next.
    """

    def setUp(self):
        self.played = play(
            CORRIDOR,
            [KEY_RIGHT, KEY_RIGHT] + [None] * 3 + [QUIT],
            player=(1, 1),
            ghost=(1, 3),
            dots=[(1, 2), (1, 3), (1, 4)],
            tick=1000.0,   # far away: this ending is the player's doing
        )

    def test_the_game_was_lost(self):
        self.assertEqual(Outcome.CAUGHT, self.played.final.outcome)

    def test_the_player_is_standing_on_the_ghost(self):
        self.assertEqual(self.played.final.ghost, self.played.final.player)

    def test_the_dots_eaten_on_the_way_still_scored(self):
        self.assertEqual(2, self.played.final.score)

    def test_a_dot_was_left_so_this_is_not_the_cleared_board_case(self):
        self.assertEqual(
            frozenset([Position(1, 4)]), self.played.final.dots
        )

    def test_the_status_line_says_caught_and_the_final_score(self):
        self.assertEqual(
            " CAUGHT  score 2   q quits", self.played.status_lines()[-1]
        )


class TheLastDotOnTheGhostsSquareTest(unittest.TestCase):
    """END-3, played rather than reasoned about.

    One dot left, and it is under the ghost. Eating it clears the board and
    meets the ghost in the same move, and the answer is CAUGHT. If the two
    branches in ``rules.move_player`` were ever swapped, this game would come
    back CLEARED and the status line would say so.
    """

    def setUp(self):
        self.played = play(
            CORRIDOR,
            [KEY_RIGHT, None, QUIT],
            player=(1, 1),
            ghost=(1, 2),
            dots=[(1, 2)],
            tick=1000.0,
        )

    def test_eating_the_last_dot_on_the_ghost_is_a_loss(self):
        self.assertEqual(Outcome.CAUGHT, self.played.final.outcome)

    def test_the_board_really_was_cleared_by_that_move(self):
        # Both conditions held at once, which is the whole of END-3. Without
        # this the test would pass on a game that simply never cleared.
        self.assertEqual(frozenset(), self.played.final.dots)

    def test_the_dot_still_scored(self):
        self.assertEqual(1, self.played.final.score)

    def test_the_status_line_says_caught_and_not_cleared(self):
        self.assertEqual(
            " CAUGHT  score 1   q quits", self.played.status_lines()[-1]
        )


class AGameLostBecauseTheGhostWalkedInTest(unittest.TestCase):
    """END-1, the ghost's half, and GHOST-1 with nobody pressing anything.

    The player never presses an arrow at all. The ghost starts at (1, 3)
    heading west along an open corridor, carries straight on (GHOST-2) and
    reaches the player at (1, 1) two ticks later. Everything that happens
    here happens because time passed.
    """

    def setUp(self):
        self.played = play(
            CORRIDOR,
            [None] * 4 + [QUIT],
            player=(1, 1),
            ghost=(1, 3),
            dots=[(1, 2), (1, 4)],
            ghost_dir=LEFT,
        )

    def test_the_game_was_lost_without_a_single_key_press(self):
        self.assertEqual(Outcome.CAUGHT, self.played.final.outcome)

    def test_the_ghost_came_to_the_player_and_not_the_other_way(self):
        self.assertEqual(Position(1, 1), self.played.final.player)
        self.assertEqual(Position(1, 1), self.played.final.ghost)

    def test_the_score_is_still_zero_because_nothing_was_eaten(self):
        self.assertEqual(0, self.played.final.score)

    def test_the_ghost_did_not_eat_the_dot_it_walked_over(self):
        # SCORE-4, end to end. The ghost crossed (1, 2) on its way; the dot
        # there is still on the board.
        self.assertIn(Position(1, 2), self.played.final.dots)

    def test_the_status_line_says_caught_with_a_score_of_zero(self):
        self.assertEqual(
            " CAUGHT  score 0   q quits", self.played.status_lines()[-1]
        )


# --------------------------------------------------------------------------
# After the ending — END-5, END-6, STAT-3
# --------------------------------------------------------------------------


class NothingHappensAfterTheEndingTest(unittest.TestCase):
    """END-5 and END-6, asserted of the running game rather than of a rule.

    The game is won on the second press. Then eight more arrow keys in all
    four directions and eight more ticks arrive, and a picture is painted for
    every one of them. Not one of them changes anything.
    """

    def setUp(self):
        arrows = [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]
        self.played = play(
            WIN_BOARD,
            [KEY_RIGHT, KEY_RIGHT] + arrows + [None] * 8 + arrows + [QUIT],
            player=(1, 1),
            ghost=(1, 5),
            dots=[(1, 2), (1, 3)],
        )
        outcomes = self.played.outcomes()
        self.first_ended = outcomes.index(Outcome.CLEARED)
        self.after = self.played.states[self.first_ended:]

    def test_the_game_really_did_end_partway_through_the_script(self):
        # Otherwise every assertion below would be about an empty list.
        self.assertGreater(len(self.after), 8)

    def test_every_state_after_the_ending_is_the_very_same_object(self):
        # The strongest form of "nothing changed": not a fresh state that
        # compares equal, the identical one. That is what the loop relies on
        # when it declines to test the outcome itself.
        for state in self.after:
            self.assertIs(self.after[0], state)

    def test_the_arrow_keys_did_nothing(self):
        self.assertEqual(Position(1, 3), self.played.final.player)
        self.assertEqual(2, self.played.final.score)

    def test_the_ghost_stood_still(self):
        squares = set(state.ghost for state in self.after)
        self.assertEqual(1, len(squares), squares)

    def test_a_picture_was_still_painted_every_turn(self):
        # END-5's "the last picture stays on screen", made true by painting
        # rather than by not painting. One paint before the first read, then
        # one per turn.
        # One before the first read, then one per turn -- except the last
        # turn, which returns on the q before it would have painted. So the
        # picture count equals the read count exactly.
        self.assertEqual(
            self.played.screen.reads, len(self.played.screen.pictures)
        )

    def test_every_picture_after_the_ending_is_identical(self):
        rows = [
            picture.rows()
            for picture in self.played.screen.pictures[self.first_ended:]
        ]
        for picture in rows:
            self.assertEqual(rows[0], picture)

    def test_the_status_line_went_on_saying_which_ending_happened(self):
        for line in self.played.status_lines()[self.first_ended:]:
            self.assertEqual(" CLEARED  score 2  q quits", line)

    def test_only_the_quit_returned_from_the_loop(self):
        # END-6. The script holds sixteen keys and ticks after the ending --
        # eight arrows and eight ticks -- and the loop read every one of them
        # before the q. Had an ending been a way out, the fake screen would
        # have raised on the first key it was never asked for.
        self.assertEqual(19, self.played.screen.reads)


# --------------------------------------------------------------------------
# The entry point the `Terminal Game` executable calls
# --------------------------------------------------------------------------


class NotATerminal(object):
    """A stream that is certainly not a tty."""

    def fileno(self):
        raise ValueError("I/O operation on closed file")


@contextlib.contextmanager
def a_screen(keys):
    """A ``session()``-shaped context manager over a fake screen."""
    clock = FakeClock(0.0)
    yield FakeScreen(keys, clock)


class RunGameStartsARealGameTest(unittest.TestCase):
    """GAME-1, START-5 and MAZE-4 through ``loop.run_game`` itself.

    ``run_game`` takes no argument that could ask for a particular game, so
    everything here is asserted off the picture it paints.
    """

    def test_it_paints_a_picture_before_it_is_asked_for_a_key(self):
        # START-5: the game is under way the moment the window opens.
        painted = []

        class Watching(FakeScreen):
            def paint(self, frame):
                painted.append(self.reads)
                FakeScreen.paint(self, frame)

        @contextlib.contextmanager
        def opener():
            yield Watching([QUIT], FakeClock(0.0))

        loop.run_game(open_screen=opener)
        self.assertEqual(0, painted[0])

    def test_the_first_picture_is_a_whole_window_of_a_real_maze(self):
        screens = []

        @contextlib.contextmanager
        def opener():
            screen = FakeScreen([QUIT], FakeClock(0.0))
            screens.append(screen)
            yield screen

        self.assertEqual(0, loop.run_game(open_screen=opener))
        first = screens[0].pictures[0]
        self.assertEqual(SCREEN_ROWS, first.height)
        self.assertEqual(SCREEN_COLS, first.width)

    def test_the_status_line_of_a_fresh_game_reads_score_zero(self):
        # START-4 and STAT-2, off the real picture the real entry point drew.
        screens = []

        @contextlib.contextmanager
        def opener():
            screen = FakeScreen([QUIT], FakeClock(0.0))
            screens.append(screen)
            yield screen

        loop.run_game(open_screen=opener)
        self.assertEqual(
            " score 0    arrows, q quits",
            screens[0].pictures[0].rows()[-1].rstrip(),
        )

    def test_the_maze_it_starts_with_is_the_full_size_one(self):
        # MAZE-1 through the entry point: 19 columns at two picture columns
        # each occupy 0..36, so 37, 38 and 39 are the blank right margin.
        screens = []

        @contextlib.contextmanager
        def opener():
            screen = FakeScreen([QUIT], FakeClock(0.0))
            screens.append(screen)
            yield screen

        loop.run_game(open_screen=opener)
        rows = screens[0].pictures[0].rows()
        self.assertEqual(MAZE_ROWS, len(rows) - 1)
        for row in rows[:MAZE_ROWS]:
            self.assertEqual(
                "   ", row[2 * MAZE_COLS - 1:], "the right margin is not blank"
            )

    def test_two_games_in_a_row_are_not_the_same_game(self):
        # MAZE-4, end to end: run_game seeds itself from the operating system
        # and takes no argument by which the same game could be asked for.
        first = io.StringIO()
        second = io.StringIO()
        self.assertEqual(0, loop.run_game(out=first, stdin=NotATerminal()))
        self.assertEqual(0, loop.run_game(out=second, stdin=NotATerminal()))
        self.assertNotEqual(first.getvalue(), second.getvalue())

    def test_with_no_terminal_it_writes_one_whole_picture_and_returns(self):
        # Plan §2.6 rule 4: never block in a window nobody could then close.
        out = io.StringIO()
        self.assertEqual(0, loop.run_game(out=out, stdin=NotATerminal()))
        lines = out.getvalue().split("\n")
        self.assertEqual(SCREEN_ROWS, len(lines) - 1)
        self.assertEqual("", lines[-1])
        self.assertEqual(
            " score 0    arrows, q quits", lines[SCREEN_ROWS - 1].rstrip()
        )

    def test_a_game_it_starts_has_a_dot_on_every_corridor_but_the_player_s(self):
        # START-3 and GAME-1, asserted of what run_game builds rather than of
        # rules.new_game: the entry point could have built its state any way
        # at all, and this says which way it did.
        out = io.StringIO()
        loop.run_game(out=out, stdin=NotATerminal())
        picture = out.getvalue().split("\n")[:MAZE_ROWS]
        dots = sum(row.count(theme.DOT_GLYPH) for row in picture)
        # Every corridor but the player's holds a dot, and the player and the
        # ghost each cover one square, so the count is corridors - 2 at least.
        self.assertGreater(dots, 100)
        self.assertIn(theme.PLAYER_GLYPHS[1], "".join(picture))
        self.assertIn(theme.GHOST_GLYPHS[1], "".join(picture))


class RunGameIsTheOnlyThingTheChildCallsTest(unittest.TestCase):
    """The seam WI-2 built, still where it was built.

    WI-9's brief says the child executable must not need to change. It did
    not: it imports ``run_game`` from ``termgame.loop`` and calls it with no
    arguments, and that still works.
    """

    def test_run_game_takes_no_required_argument(self):
        import inspect

        signature = inspect.signature(loop.run_game)
        required = [
            name
            for name, parameter in signature.parameters.items()
            if parameter.default is inspect.Parameter.empty
        ]
        self.assertEqual([], required)

    def test_the_child_executable_still_calls_it(self):
        import os

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "Terminal Game")) as handle:
            source = handle.read()
        self.assertIn("from termgame.loop import run_game", source)
        self.assertIn("sys.exit(run_game())", source)


class TheStandInsAreGoneTest(unittest.TestCase):
    """WI-4 shipped ``termgame/standins.py`` saying WI-9 would delete it."""

    def test_the_module_cannot_be_imported(self):
        import importlib

        with self.assertRaises(ImportError):
            importlib.import_module("termgame.standins")

    def test_the_file_is_not_on_disk(self):
        import os

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertFalse(
            os.path.exists(os.path.join(root, "termgame", "standins.py"))
        )


if __name__ == "__main__":
    unittest.main()
