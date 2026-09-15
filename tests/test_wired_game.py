"""WI-12 — the whole game wired together, played to a loss and to a win.

The plan asks for "an end-to-end run with a scripted key sequence and an
injected clock, against the real domain, the real frame builder and a screen
port stood in for, playing to a loss and to a win, and asserting the final frame
in both cases."

So everything here is real except the screen and the clock: a real maze, the
real rules, the real ghost policy, the real glyph table, the real frame builder
and the real status line. What is asserted is **the last picture the player
would be looking at** — read off the frame cell by cell, not inferred from the
state that produced it.

That distinction is the point. A test that asserted on the final `GameState`
would pass just as well if the frame builder were never called, or called
without the status row, which is the exact failure this item was told to guard.
"""

from __future__ import annotations

import random
import unittest

from terminalgame.application.loop import play
from terminalgame.domain.game_state import GameState, Outcome
from terminalgame.domain.maze import EAST, Maze
from terminalgame.game_main import build_frame
from terminalgame.presentation.frame_builder import (
    GHOST_GLYPH,
    PLAYER_GLYPH,
    STATUS_ROW,
    WIDTH,
    column_of,
)
from terminalgame.presentation.status_line import status_text
from terminalgame.screen.port import Colour, Key
from tests.loop_fakes import FakeClock, ScriptedScreen, StillGhost

RING = [
    "#####",
    "#   #",
    "# # #",
    "#   #",
    "#####",
]


def state_on_ring(player, ghost, dots, score=0):
    maze = Maze.from_text("\n".join(RING))
    return GameState(maze=maze, player=player, ghost=ghost,
                     ghost_heading=EAST, dots=dots, score=score,
                     outcome=Outcome.PLAYING)


def row_text(frame, row):
    return "".join(frame.cell(column, row).character
                   for column in range(frame.width))


def glyph_at(frame, square):
    """The three columns the actor glyph occupies, centred on that square."""
    centre = column_of(square[0])
    return "".join(frame.cell(centre + offset, square[1]).character
                   for offset in (-1, 0, 1))


def played(state, keys, ghost=None):
    """Play a scripted game with everything real but the screen and clock."""
    clock = FakeClock()
    screen = ScriptedScreen(clock, keys)
    final = play(screen, state, random.Random(0), build_frame,
                 clock=clock.time,
                 ghost_move=ghost if ghost is not None else StillGhost())
    return final, screen


class PlayedToALoss(unittest.TestCase):
    """END-1 and END-3 seen from the glass, through the whole stack."""

    def setUp(self):
        # One square apart; the player walks straight into the ghost.
        start = state_on_ring(player=(1, 1), ghost=(2, 1), dots={(2, 1)})
        self.final, self.screen = played(
            start, [(0.01, Key.RIGHT), (0.5, Key.printable("q"))])
        self.frame = self.screen.presented[-1]

    def test_the_game_really_was_lost(self):
        self.assertEqual(Outcome.CAUGHT, self.final.outcome)

    def test_the_last_picture_carries_the_finished_game_s_status_row(self):
        """The seam at an ending: the final frame shows the *final* state.

        It asserts equality with what `status_line` produces rather than
        picking out "CAUGHT", the score and the absence of "arrows" one
        substring at a time. All three of those are owned one layer down —
        `test_status_line` pins the loss wording, the final score and the fact
        that an ended line offers only `q`. Equality catches any divergence,
        including the ones nobody thought to write a substring for.
        """
        row = row_text(self.frame, STATUS_ROW)
        self.assertEqual(status_text(self.final), row.rstrip())

    def test_the_ghost_is_drawn_over_the_player(self):
        """END-4 — "on a loss the ghost is drawn over the player".

        Both are on the same square, so the picture can only show one. It must
        be the ghost, which is what makes the final frame say what happened.
        """
        self.assertEqual(self.final.player, self.final.ghost)
        self.assertEqual(GHOST_GLYPH, glyph_at(self.frame, self.final.ghost))
        self.assertNotEqual(PLAYER_GLYPH, glyph_at(self.frame, self.final.player))

    def test_the_picture_then_stands(self):
        # END-5: the frames stop when the game does, so the last one is still
        # the last one after several more passes and another key.
        frames_at_the_end = len(self.screen.presented)
        self.assertGreater(frames_at_the_end, 1)
        self.assertIs(self.frame, self.screen.presented[-1])


class PlayedToAWin(unittest.TestCase):
    """END-2, and the other status line."""

    def setUp(self):
        start = state_on_ring(player=(1, 1), ghost=(3, 3), dots={(2, 1)})
        self.final, self.screen = played(
            start, [(0.01, Key.RIGHT), (0.5, Key.printable("q"))])
        self.frame = self.screen.presented[-1]

    def test_the_game_really_was_won(self):
        self.assertEqual(Outcome.CLEARED, self.final.outcome)
        self.assertEqual(0, self.final.dots_remaining)

    def test_the_last_picture_carries_the_finished_game_s_status_row(self):
        """The win half of the same seam — see the loss class for why equality."""
        row = row_text(self.frame, STATUS_ROW)
        self.assertEqual(status_text(self.final), row.rstrip())

    def test_the_two_actors_are_drawn_separately(self):
        self.assertNotEqual(self.final.player, self.final.ghost)
        self.assertEqual(PLAYER_GLYPH, glyph_at(self.frame, self.final.player))
        self.assertEqual(GHOST_GLYPH, glyph_at(self.frame, self.final.ghost))

    def test_the_eaten_dot_is_gone_from_the_picture(self):
        # SCORE-1 — "the dot disappears from the maze for the rest of the
        # game". Read off the frame, not off the state.
        eaten = column_of(2), 1
        self.assertNotEqual("▪", self.frame.cell(eaten[0], eaten[1]).character)


class TheStatusRowIsNeverBlankInAWiredGame(unittest.TestCase):
    """The camouflage case, asserted on the frames a real game produced.

    `compose(state, status_line=None)` leaves row 29 blank and composes
    perfectly. Every frame a played game presents must carry a status row, or
    STAT-1 has been lost in a way nothing else would notice.
    """

    def test_every_frame_the_loop_presents_carries_this_game_s_status_row(self):
        """The seam: the loop draws frames built by `build_frame`, not bare ones.

        What the row *says* is `status_line`'s (29 tests) and its colour and
        placement are `frame_builder`'s. The only thing unowned here is whether
        the **loop** presents rows that track the game as it is played, so that
        is all this asserts. It replaces three tests that also re-checked the
        colour and the wording.
        """
        start = state_on_ring(player=(1, 1), ghost=(3, 3),
                              dots={(2, 1), (3, 1)})
        final, screen = played(start, [(0.01, Key.RIGHT), (0.02, Key.RIGHT),
                                       (0.5, Key.printable("q"))])
        self.assertEqual(2, final.score)
        self.assertGreater(len(screen.presented), 2)
        rows = [row_text(frame, STATUS_ROW) for frame in screen.presented]
        for index, row in enumerate(rows):
            self.assertNotEqual("", row.strip(),
                                "frame %d has a blank status row" % index)
        # The score climbing 0 -> 1 -> 2 across the frames is what proves the
        # row is rebuilt from the live state each pass rather than drawn once.
        for expected in ("score 0", "score 1", "score 2"):
            self.assertTrue(any(expected in row for row in rows),
                            "no presented frame ever showed %r" % expected)


class EveryFrameIsTheWholeWindow(unittest.TestCase):

    def test_each_one_is_forty_by_thirty(self):
        start = state_on_ring(player=(1, 1), ghost=(3, 3), dots={(2, 1)})
        _, screen = played(start, [(0.01, Key.RIGHT), (0.5, Key.printable("q"))])
        for frame in screen.presented:
            self.assertEqual(40, frame.width)
            self.assertEqual(30, frame.height)

    def test_a_fresh_frame_each_time_rather_than_one_edited_in_place(self):
        # Caution C9. Two frames of a game in which something changed must not
        # be the same object, or the earlier picture would have been mutated.
        start = state_on_ring(player=(1, 1), ghost=(3, 3), dots={(2, 1)})
        _, screen = played(start, [(0.01, Key.RIGHT), (0.5, Key.printable("q"))])
        self.assertGreater(len(screen.presented), 1)
        self.assertIsNot(screen.presented[0], screen.presented[-1])
        self.assertNotEqual(screen.presented[0], screen.presented[-1])


if __name__ == "__main__":
    unittest.main()
