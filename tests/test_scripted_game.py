# -*- coding: utf-8 -*-
"""WI-19 — a whole game, played headless, asserted as pictures.

This is the whole-application test. **It never opens a window**, it builds
no clock (amendment 5 — there is nothing to consume and nothing to build),
and it does not assemble the shell, which is WI-18's.

A game here is a loop over three calls: ``tick()`` for the ghost's turn,
``move()`` for a key, ``quit()`` to end it.

**No status-line string is authored in this file.** A7 forbids writing one
outside WI-13; an expected picture's row 29 is composed from WI-13's own
function by :func:`tests.scripted.expected_picture` and joined onto the maze
rows typed here. If the user ever rules on contradictions C-3 or C-4 these
tests follow WI-13 rather than having to be retyped.
"""

from __future__ import annotations

import hashlib
import os
import random
import subprocess
import sys
import unittest

from terminal_game.application.session import Phase
from terminal_game.domain.game_state import Outcome
from terminal_game.domain.maze import Direction, Maze, Square
from terminal_game.domain.maze_generator import generate_maze
from terminal_game.domain.opening_position import opening_position
from terminal_game.presentation.frame_composer import GHOST_MOTIF, PLAYER_MOTIF

from tests.scripted import (
    ScriptedGame,
    eat_everything,
    expected_picture,
    state_over,
)

N, S, E, W = (
    Direction.NORTH,
    Direction.SOUTH,
    Direction.EAST,
    Direction.WEST,
)

#: A ring of eight corridor squares round one lone wall.  Small enough to
#: read as a picture, and — because every square of a ring has exactly two
#: corridor neighbours — a maze in which **every** ghost choice is forced:
#: straight on where it can, and the single non-reverse exit at each corner.
#: So the whole walk is deterministic and the win path needs no lucky seed.
RING = Maze.from_text(
    """
#####
#...#
#.#.#
#...#
#####
"""
)

#: Three corridor squares in a line.  The player at one end, the ghost at
#: the other, and one dot in between.
CORRIDOR = Maze.from_text(
    """
#####
#...#
#####
"""
)

#: Five corridor squares in a line — long enough that a collision can
#: happen with dots still on the board.
LONG_CORRIDOR = Maze.from_text(
    """
#######
#.....#
#######
"""
)

#: The seed whose full-size game the planner clears.  Fixed, so the score
#: below is a fact about a particular game rather than a lucky run.
CLEARING_SEED = 4


def a_ring_game():
    """The player at the top-left of the ring, the ghost one square ahead."""
    return ScriptedGame(
        state_over(RING, Square(1, 1), Square(2, 1), ghost_heading=E)
    )


#: Tick, then move — seven times round the ring.  The ghost stays one square
#: ahead the whole way and the player eats up behind it.
WIN_SCRIPT = [
    step
    for direction in (E, E, S, S, W, W, N)
    for step in (("tick", None), ("move", direction))
]


class TheWinPath(unittest.TestCase):
    """Every dot eaten, CLEARED, the ghost stopped, further keys dead."""

    def setUp(self):
        self.game = a_ring_game()
        self.dots_at_the_start = self.game.dots_left
        self.assertEqual(7, self.dots_at_the_start)

    def test_the_first_picture_is_composed_before_anything_is_pressed(self):
        # START-5: the game is under way the moment the window opens.
        self.assertEqual(1, len(self.game.shown))
        self.assertEqual(
            expected_picture(
                [
                    "╔═══════╗",
                    "║▐█▗█▖▪ ║",
                    "║ ▪ ■ ▪ ║",
                    "║ ▪ ▪ ▪ ║",
                    "╚═══════╝",
                ],
                0,
                Outcome.UNDECIDED,
            ),
            self.game.picture,
        )

    def test_adjacent_actors_overlap_and_the_ghost_is_the_one_seen(self):
        # Two squares two columns apart, two three-column motifs: they share
        # a column, and END-4's draw order decides it. Hence ▐█▗█▖ and not
        # ▐█▌▗█▖ in the picture above.
        self.assertIn("▐█" + GHOST_MOTIF, self.game.maze_picture[1])

    def test_playing_the_script_clears_the_maze(self):
        self.game.play(WIN_SCRIPT)

        self.assertEqual(Outcome.CLEARED, self.game.outcome)
        self.assertEqual(Phase.DECIDED, self.game.phase)
        self.assertEqual(0, self.game.dots_left)

    def test_the_score_is_the_number_of_dots_eaten(self):
        self.game.play(WIN_SCRIPT)

        self.assertEqual(self.dots_at_the_start, self.game.score)

    def test_the_final_picture_is_this_one(self):
        self.game.play(WIN_SCRIPT)

        self.assertEqual(
            expected_picture(
                [
                    "╔═══════╗",
                    "║▗█▖    ║",
                    "║▐█▌■   ║",
                    "║       ║",
                    "╚═══════╝",
                ],
                7,
                Outcome.CLEARED,
            ),
            self.game.picture,
        )

    def test_a_picture_was_shown_for_every_turn_of_the_game(self):
        self.game.play(WIN_SCRIPT)

        # One for the opening position, then one per tick and one per move.
        self.assertEqual(1 + len(WIN_SCRIPT), len(self.game.shown))

    def test_the_ghost_stops_once_the_game_is_won(self):
        self.game.play(WIN_SCRIPT)
        ghost = self.game.session.state.ghost
        frames = len(self.game.shown)

        for _ in range(10):
            self.game.tick()

        self.assertEqual(ghost, self.game.session.state.ghost)
        self.assertEqual(frames, len(self.game.shown))

    def test_further_keys_do_nothing_once_the_game_is_won(self):
        self.game.play(WIN_SCRIPT)
        picture = self.game.picture
        player = self.game.session.state.player

        for direction in (N, S, E, W):
            self.game.move(direction)

        self.assertEqual(player, self.game.session.state.player)
        self.assertEqual(picture, self.game.picture)

    def test_the_last_picture_stays_on_screen(self):
        # END-5: nothing new is composed once the outcome is decided.
        self.game.play(WIN_SCRIPT)
        last = self.game.shown[-1]

        self.game.tick()
        self.game.move(E)

        self.assertIs(last, self.game.shown[-1])

    def test_q_is_the_only_way_out_and_it_works(self):
        self.game.play(WIN_SCRIPT)
        self.assertEqual(Phase.DECIDED, self.game.phase)

        self.game.quit()

        self.assertEqual(Phase.ENDED, self.game.phase)
        self.assertEqual(1, self.game.shut_downs)

    def test_quitting_twice_shuts_down_once(self):
        self.game.play(WIN_SCRIPT).quit().quit()

        self.assertEqual(1, self.game.shut_downs)


class TheLossPath(unittest.TestCase):
    """The ghost and the player meet, and the ghost is drawn over them."""

    def test_the_ghost_walking_into_the_player_loses_the_game(self):
        game = ScriptedGame(state_over(CORRIDOR, Square(1, 1), Square(3, 1)))

        game.move(E).tick()

        self.assertEqual(Outcome.CAUGHT, game.outcome)
        self.assertEqual(Phase.DECIDED, game.phase)
        self.assertEqual(
            game.session.state.player, game.session.state.ghost
        )

    def test_the_final_picture_shows_the_ghost_and_not_the_player(self):
        # END-4: on a loss the ghost is drawn over the player, so the last
        # picture shows what happened.
        game = ScriptedGame(state_over(CORRIDOR, Square(1, 1), Square(3, 1)))

        game.move(E).tick()

        self.assertEqual(
            expected_picture(
                ["╔═══════╗", "║  ▗█▖▪ ║", "╚═══════╝"],
                1,
                Outcome.CAUGHT,
            ),
            game.picture,
        )
        self.assertNotIn(PLAYER_MOTIF, "\n".join(game.maze_picture))

    def test_the_player_walking_into_the_ghost_loses_the_game(self):
        # END-1 is indifferent to who walked into whom. A longer corridor
        # than CORRIDOR, so that dots remain after the collision and this
        # is a plain loss rather than the END-3 precedence case below —
        # in the three-square maze, eating the middle dot is already a win.
        game = ScriptedGame(
            state_over(LONG_CORRIDOR, Square(1, 1), Square(3, 1))
        )

        game.move(E).move(E)

        self.assertEqual(Outcome.CAUGHT, game.outcome)
        self.assertGreater(game.dots_left, 0)

    def test_nothing_moves_once_the_game_is_lost(self):
        game = ScriptedGame(state_over(CORRIDOR, Square(1, 1), Square(3, 1)))
        game.move(E).tick()
        picture, frames = game.picture, len(game.shown)

        game.tick()
        game.move(W)
        game.tick()

        self.assertEqual(picture, game.picture)
        self.assertEqual(frames, len(game.shown))

    def test_q_leaves_a_finished_game(self):
        game = ScriptedGame(state_over(CORRIDOR, Square(1, 1), Square(3, 1)))
        game.move(E).tick()

        game.quit()

        self.assertEqual(Phase.ENDED, game.phase)
        self.assertEqual(1, game.shut_downs)


class EndThreeInAWholeGame(unittest.TestCase):
    """The last dot, on the ghost's square: a loss, not a win.

    END-3 lives in the order of two statements inside the turn resolver, and
    the resolver's own unit test asserts it directly. This asserts it again
    where it actually matters — in a game played from the opening position
    to the end — which is the strongest ordinary coverage available for a
    requirement that is a *precedence* rather than a value.
    """

    def a_game_one_move_from_both_endings(self):
        # Three corridor squares. The player eats the middle dot, and the
        # only dot left is the one under the ghost. Moving onto it would
        # empty the dot field *and* meet the ghost, both on the same turn.
        game = ScriptedGame(state_over(CORRIDOR, Square(1, 1), Square(3, 1)))
        game.move(E)
        self.assertEqual(Phase.PLAYING, game.phase)
        self.assertEqual(1, game.dots_left)
        self.assertTrue(game.session.state.dots.has_dot(Square(3, 1)))
        return game

    def test_the_last_dot_on_the_ghosts_square_is_caught_and_not_cleared(self):
        game = self.a_game_one_move_from_both_endings()

        game.move(E)

        self.assertEqual(Outcome.CAUGHT, game.outcome)
        self.assertNotEqual(Outcome.CLEARED, game.outcome)

    def test_the_dot_field_really_did_empty_on_that_same_turn(self):
        # Without this the test above could pass for the wrong reason — a
        # loss that happened before the win condition was ever in play.
        game = self.a_game_one_move_from_both_endings()

        game.move(E)

        self.assertEqual(0, game.dots_left)

    def test_the_dot_is_still_taken_and_still_scored_on_the_losing_turn(self):
        # Assumption A8: END-3's own wording presupposes the eating happens
        # and only the outcome changes.
        game = self.a_game_one_move_from_both_endings()
        before = game.score

        game.move(E)

        self.assertEqual(before + 1, game.score)

    def test_the_status_line_says_caught(self):
        game = self.a_game_one_move_from_both_endings()

        game.move(E)

        self.assertEqual(
            expected_picture(
                ["╔═══════╗", "║    ▗█▖║", "╚═══════╝"], 2, Outcome.CAUGHT
            ),
            game.picture,
        )


class AWholeSeededGame(unittest.TestCase):
    """The real thing: a generated 19 x 29 maze played to a win."""

    @classmethod
    def setUpClass(cls):
        maze = generate_maze(random.Random(CLEARING_SEED))
        opening = opening_position(maze)
        cls.game = ScriptedGame(
            state_over(maze, opening.player, opening.ghost),
            seed=CLEARING_SEED,
        )
        cls.dots_at_the_start = cls.game.dots_left
        cls.moves = eat_everything(cls.game, tick_every=1, limit=8000)

    def test_the_maze_is_the_one_the_requirements_ask_for(self):
        self.assertEqual(19, self.game.session.state.maze.width)
        self.assertEqual(29, self.game.session.state.maze.height)

    def test_the_game_is_won(self):
        self.assertEqual(Outcome.CLEARED, self.game.outcome)
        self.assertEqual(0, self.game.dots_left)

    def test_the_score_equals_the_number_of_dots_eaten(self):
        self.assertEqual(self.dots_at_the_start, self.game.score)

    def test_the_score_is_in_the_band_a_whole_game_is_worth(self):
        # A9 / contradiction C-6: measured over 200 seeded mazes, a whole
        # game is worth 259 to 271, mean 264.5.
        self.assertGreaterEqual(self.game.score, 259)
        self.assertLessEqual(self.game.score, 271)

    def test_the_score_is_not_the_number_in_the_specifications_example(self):
        # STAT-3's `CLEARED  score 274` is a *formatting* exemplar and not a
        # state this game can reach. Nothing here may assert 274.
        self.assertNotEqual(274, self.game.score)

    def test_the_status_line_reads_cleared_with_the_score_it_reached(self):
        self.assertEqual(
            expected_picture(
                self.game.maze_picture, self.game.score, Outcome.CLEARED
            ),
            self.game.picture,
        )

    def test_the_whole_picture_is_thirty_rows_of_forty_characters(self):
        lines = self.game.picture.split("\n")

        self.assertEqual(30, len(lines))
        self.assertEqual({40}, {len(line) for line in lines})

    def test_a_picture_was_shown_for_every_turn(self):
        # One for the opening position, then exactly one per turn taken —
        # counted by the harness rather than modelled from the planner,
        # which does not always tick after a move.
        self.assertEqual(1 + self.game.turns, len(self.game.shown))
        self.assertGreater(self.moves, 100)

    def test_nothing_moves_after_the_outcome_is_decided(self):
        picture, frames = self.game.picture, len(self.game.shown)

        self.game.tick()
        self.game.move(N)

        self.assertEqual(picture, self.game.picture)
        self.assertEqual(frames, len(self.game.shown))


class TheGameReplaysIdentically(unittest.TestCase):
    """The property every asserted picture in this file rests on.

    DEV-A measured in WI-5 that seeded maze generation is independent of
    ``PYTHONHASHSEED`` — an identical digest over 50 mazes at four hash
    seeds. That is exactly the kind of invariant a later change undoes by
    iterating a set, and the failure would look random rather than causal.
    So it is pinned here, in the item that depends on it.
    """

    def a_short_game(self, seed):
        maze = generate_maze(random.Random(seed))
        opening = opening_position(maze)
        game = ScriptedGame(
            state_over(maze, opening.player, opening.ghost), seed=seed
        )
        eat_everything(game, tick_every=1, limit=60)
        return [frame.to_text() for frame in game.shown]

    def test_the_same_seed_plays_the_same_game_twice(self):
        self.assertEqual(self.a_short_game(11), self.a_short_game(11))

    def test_two_different_seeds_play_different_games(self):
        self.assertNotEqual(self.a_short_game(11), self.a_short_game(12))

    def test_a_seeded_game_is_the_same_under_a_different_hash_seed(self):
        """The one that cannot be checked inside this process.

        ``PYTHONHASHSEED`` is fixed when the interpreter starts, so this
        runs the same seeded game in subprocesses at two different hash
        seeds and compares the digests.
        """
        digests = set()
        for hash_seed in ("0", "12345"):
            environment = dict(os.environ, PYTHONHASHSEED=hash_seed)
            result = subprocess.run(
                [sys.executable, "-c", REPLAY_PROGRAM],
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(
                0,
                result.returncode,
                result.stderr.decode("utf-8", "replace"),
            )
            digests.add(result.stdout.decode("ascii").strip())

        self.assertEqual(1, len(digests), digests)
        self.assertEqual({self.replay_digest()}, digests)

    @staticmethod
    def replay_digest():
        return _replay_digest()


def _replay_digest():
    """A digest over two seeded games' pictures.  Shared with the subprocess.

    Deliberately short — two seeds, twenty-five turns. The property being
    pinned is that a *seeded* game is reproducible at all, and a long game
    pins it no better than a short one while costing every developer the
    difference on every run.
    """
    digest = hashlib.sha256()
    for seed in (0, 1):
        maze = generate_maze(random.Random(seed))
        opening = opening_position(maze)
        game = ScriptedGame(
            state_over(maze, opening.player, opening.ghost), seed=seed
        )
        eat_everything(game, tick_every=1, limit=25)
        for frame in game.shown:
            digest.update(frame.to_text().encode("utf-8"))
    return digest.hexdigest()


#: Run in a subprocess at a chosen ``PYTHONHASHSEED``.
REPLAY_PROGRAM = (
    "import sys; sys.path.insert(0, '.')\n"
    "from tests.test_scripted_game import _replay_digest\n"
    "print(_replay_digest())\n"
)


if __name__ == "__main__":
    unittest.main()
